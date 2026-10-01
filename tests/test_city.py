import numpy as np
import pytest

from muthmills import CobbDouglas, CobbDouglasTech, Spec, StoneGeary, solve


def test_reproduces_note_baseline(cd_spec):
    c = solve(cd_spec)
    a = c.aggregates()
    assert c.xbar == pytest.approx(33.0, abs=0.05)
    assert a["commute_share_edge"] == pytest.approx(0.22, abs=0.005)
    assert a["center_rent_ratio"] == pytest.approx(145, abs=1)
    assert a["center_density"] == pytest.approx(6200, rel=0.01)
    assert c.local(c.xbar * 0.9999)["D"] == pytest.approx(55, rel=0.02)


@pytest.mark.parametrize("spec_name", ["cd_spec", "sg_spec"])
def test_rent_integral_identity_holds(spec_name, request):
    a = solve(request.getfixturevalue(spec_name)).aggregates()
    assert abs(a["rent_identity_residual"]) < 1e-8


def test_stone_geary_reduces_to_cobb_douglas(cd_spec):
    sg0 = Spec(StoneGeary(0.25, 0.0, 0.0), cd_spec.tech, cd_spec.y, cd_spec.t, cd_spec.rA, L=cd_spec.L)
    assert solve(sg0).xbar == pytest.approx(solve(cd_spec).xbar)


def test_intracity_gradients(sg_spec):
    loc = solve(sg_spec).local(np.linspace(0.1, 30, 50))
    assert np.all(np.diff(loc["p"]) < 0) and np.all(np.diff(loc["r"]) < 0)
    assert np.all(np.diff(loc["S"]) < 0) and np.all(np.diff(loc["D"]) < 0)
    assert np.all(np.diff(loc["q"]) > 0)


def test_rent_gradient_equals_commute_cost_times_density(cd_spec):
    c, x, h = solve(cd_spec), 12.0, 1e-4
    slope = (c.local(x + h)["r"] - c.local(x - h)["r"]) / (2 * h)
    assert slope == pytest.approx(-cd_spec.t * c.local(x)["D"], rel=1e-6)


def test_open_city_recovers_closed_population(cd_spec):
    c = solve(cd_spec)
    o = solve(Spec(cd_spec.prefs, cd_spec.tech, cd_spec.y, cd_spec.t, cd_spec.rA, u=c.u))
    assert o.L == pytest.approx(cd_spec.L, rel=1e-6) and o.xbar == pytest.approx(c.xbar)


def test_open_city_similarity(cd_spec):
    o = solve(Spec(cd_spec.prefs, cd_spec.tech, cd_spec.y, cd_spec.t, cd_spec.rA, u=solve(cd_spec).u))
    o2 = solve(o.spec.scaled(t=1.1))
    assert o2.xbar == pytest.approx(o.xbar / 1.1, rel=1e-9)
    assert o2.L == pytest.approx(o.L / 1.21, rel=1e-6)
    assert o2.local(5.0)["p"] == pytest.approx(o.local(5.5)["p"])      # f_lambda(x) = f(lambda x)
    d = 3000.0
    o3 = solve(o.spec.scaled(y=1 + d / o.spec.y))
    assert o3.local(10.0 + d / o.spec.t)["r"] == pytest.approx(o.local(10.0)["r"])  # translation


def test_spec_requires_exactly_one_of_L_or_u(cd_spec):
    with pytest.raises(ValueError):
        Spec(cd_spec.prefs, cd_spec.tech, 6e4, 400.0, 1.28e5)


def test_height_cap_expands_city_and_lowers_utility(cd_spec):
    free = solve(cd_spec)
    cap = 0.3 * float(free.local(0.0)["S"])
    capped = solve(Spec(cd_spec.prefs, CobbDouglasTech(0.8, S_cap=cap), L=1e6, y=6e4, t=400.0, rA=1.28e5), n=2000)
    assert capped.xbar > free.xbar and capped.u < free.u
    assert float(capped.local(0.0)["S"]) == pytest.approx(cap)
    assert abs(capped.aggregates(2000)["rent_identity_residual"]) < 1e-4


def test_non_binding_cap_changes_nothing(cd_spec):
    big = Spec(cd_spec.prefs, CobbDouglasTech(0.8, S_cap=1e30), L=1e6, y=6e4, t=400.0, rA=1.28e5)
    assert solve(big).xbar == pytest.approx(solve(cd_spec).xbar)


def test_partly_open_city_nests_closed_and_open(cd_spec):
    c = solve(cd_spec)
    ref = dict(L=cd_spec.L, u=c.u)
    part = lambda m: solve(Spec(cd_spec.prefs, cd_spec.tech, cd_spec.y * 1.1, cd_spec.t, cd_spec.rA, migration=m, **ref))
    closed = solve(cd_spec.scaled(y=1.1))
    assert part(0.0).xbar == pytest.approx(closed.xbar, rel=1e-9)
    assert part(1e4).u == pytest.approx(c.u, rel=1e-3)           # near-open: utility pinned at u_ref
    assert part(1e4).L > part(1.0).L > closed.L   # more migration, bigger city after an income gain


def test_scaled_accepts_alpha_and_i_and_rejects_missing_params(cd_spec):
    s = cd_spec.scaled(alpha=1.2, i=1.5)
    assert s.prefs.alpha == pytest.approx(0.3) and s.tech.i == 1.5
    with pytest.raises(ValueError):
        cd_spec.scaled(u=1.1)


def test_no_bracket_raises_instead_of_silently_misconverging():
    with pytest.raises(ValueError):
        CobbDouglasTech(0.99).p_bar(1.28e5)
