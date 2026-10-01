import numpy as np
import pytest

from muthmills import solve
from muthmills.statics import analytic_closed, elasticity, location_betas, pivots, propagate, response

XS = np.array([0.0, 5.0, 15.0, 25.0, 32.0])


@pytest.mark.parametrize("spec_name", ["cd_spec", "sg_spec"])
def test_analytic_matches_finite_difference(spec_name, request):
    spec = request.getfixturevalue(spec_name)
    city = solve(spec)
    xs = city.xbar * np.array([0.0, 0.15, 0.45, 0.75, 0.97])   # inside the boundary: beyond it r is rA
    a = analytic_closed(city, xs)
    for par in ("L", "rA", "y", "t", "theta"):
        assert a["u"][par] == pytest.approx(elasticity(spec, lambda c: c.u, par), abs=1e-5)
        assert a["xbar"][par] == pytest.approx(elasticity(spec, lambda c: c.xbar, par), abs=1e-5)
        assert a["r"][par] == pytest.approx(elasticity(spec, lambda c: c.land_rent(xs), par), abs=1e-4)


def test_theorem_signs(cd_spec):
    city, a = solve(cd_spec), analytic_closed(solve(cd_spec), XS)
    assert all(a["u"][p] < 0 for p in ("L", "rA", "t")) and a["u"]["y"] > 0
    assert a["xbar"]["L"] > 0 and a["xbar"]["y"] > 0 and a["xbar"]["rA"] < 0 and a["xbar"]["t"] < 0
    assert np.all(a["r"]["L"] > 0) and np.all(a["r"]["rA"] > 0)
    assert np.all(np.diff(np.sign(a["r"]["y"])) >= 0)    # income rotates counter-clockwise
    assert np.all(np.diff(np.sign(a["r"]["t"])) <= 0)    # commuting cost rotates clockwise
    piv = pivots(city)
    assert 0 < piv["y"] < piv["t"] < city.xbar


def test_pivot_is_zero_of_analytic_beta(cd_spec):
    city = solve(cd_spec)
    piv = pivots(city)
    for par in ("y", "t"):
        assert analytic_closed(city, [piv[par]])["r"][par][0] == pytest.approx(0, abs=1e-6)


def test_location_betas_uniform_for_population_in_cd(cd_spec):
    b = location_betas(cd_spec, XS, ["L"])["L"]
    assert np.allclose(b, b[0], rtol=1e-4)            # Cobb-Douglas: L shifts ln p uniformly


def test_differential_rent_is_levered_near_the_edge(cd_spec):
    b = location_betas(cd_spec, [5.0, 31.0], ["L"], differential=True)["L"]
    assert b[1] > 2 * b[0]


def test_wfh_shock_matches_note(cd_spec):
    r = response(cd_spec, {"t": 0.6}, [0.0, 30.0])
    assert r["city_pct"]["xbar"] == pytest.approx(37, abs=1)
    assert r["city_pct"]["u"] == pytest.approx(5, abs=0.5)
    assert r["local_pct"]["p"][0] == pytest.approx(-18, abs=1) and r["local_pct"]["p"][1] > 0


def test_propagate_drops_failures_and_returns_array(cd_spec):
    out = propagate(lambda rng: cd_spec.scaled(L=rng.uniform(0.5, 2)), lambda c: c.xbar, draws=10)
    assert out.shape == (10, 1) and np.all(out > 0)


def test_land_population_elasticity_is_pinned_near_one_independent_of_gamma(cd_spec):
    # Reviewer's identity (Cobb-Douglas): eps = 1 - rA xbar / int r dx; gamma cancels.
    from muthmills.city import integrate
    for beta in (0.6, 0.8, 0.9):
        spec = type(cd_spec)(cd_spec.prefs, type(cd_spec.tech)(beta), cd_spec.y, cd_spec.t, cd_spec.rA, L=1e6)
        c = solve(spec)
        closed_form = 1 - spec.rA * c.xbar / integrate(lambda x: c.local(x)["r"], 0, c.xbar)
        assert location_betas(spec, [5.0], ["L"])["L"][0] == pytest.approx(closed_form, abs=1e-4)


def test_differential_beta_for_rA_uses_shocked_rA(cd_spec):
    b = location_betas(cd_spec, [5.0, 31.0], ["rA"], differential=True)["rA"]
    assert b[1] < 0          # near the edge, a higher farmland rent shrinks differential rent


def test_asset_betas_scale_with_beta_in_cobb_douglas(cd_spec):
    land = location_betas(cd_spec, [5.0], ["L"], asset="land")["L"]
    price = location_betas(cd_spec, [5.0], ["L"], asset="price")["L"]
    assert price == pytest.approx(land * (1 - cd_spec.tech.beta), rel=1e-4)


def test_partly_open_has_no_analytic_pivot_formulas(cd_spec):
    from muthmills import Spec
    spec = Spec(cd_spec.prefs, cd_spec.tech, cd_spec.y, cd_spec.t, cd_spec.rA, L=1e6, u=solve(cd_spec).u, migration=1.0)
    with pytest.raises(ValueError):
        analytic_closed(solve(spec), [1.0])
