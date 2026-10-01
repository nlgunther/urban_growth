"""Comparative statics: numerical elasticities, the note's analytic closed-city formulas,
rotation pivots, location 'betas' and shock responses.

The analytic path (analytic_closed) implements Theorem 'closed' of the note and is used to
cross-check the finite-difference path, which works for any Spec (open, capped, Stone-Geary).
"""
import numpy as np
from loguru import logger
from scipy.optimize import brentq

from .city import City, Spec, integrate, solve

SHOCK_PARAMS = ("L", "u", "y", "t", "rA", "theta")   # those unset for the city type are skipped


def elasticity(spec: Spec, outcome, param: str, step: float = 1e-3):
    """d ln outcome(City) / d ln param by central difference; outcome returns positive numbers.

    Example:
        elasticity(spec, lambda c: c.xbar, "y")   # radius elasticity w.r.t. income
    """
    up, dn = (outcome(solve(spec.scaled(**{param: f}))) for f in (1 + step, 1 - step))
    with np.errstate(all="ignore"):
        return (np.log(up) - np.log(dn)) / (np.log(1 + step) - np.log(1 - step))


ASSETS = {   # what an investor holds: land, floor-space price, or rent per dwelling
    "land": lambda c, xs: c.land_rent(xs),
    "price": lambda c, xs: c.local(xs)["p"],
    "dwelling": lambda c, xs: (lambda d: d["p"] * d["q"])(c.local(xs)),
}


def location_betas(spec: Spec, xs, params=SHOCK_PARAMS, asset: str = "land",
                   differential: bool = False) -> dict:
    """d ln value(x) / d ln param at fixed distances xs: the spatial factor exposure of an asset.

    asset: 'land' (r), 'price' (p per unit floor space; elasticity is (1 - beta) x land's in
    Cobb-Douglas) or 'dwelling' (p q, rent per dwelling).  differential=True (land only) uses
    r - rA, the capitalised-access part of value: its elasticity is r/(r - rA) times that of r,
    so the 'leverage' near the boundary is accounting, not extra information.

    Example:
        location_betas(spec, [0, 10, 25], ["y", "t"], asset="dwelling")
    """
    xs = np.asarray(xs, float)
    value = (lambda c: c.land_rent(xs) - c.spec.rA) if differential else (lambda c: ASSETS[asset](c, xs))
    return {p: elasticity(spec, value, p) for p in params if spec.get(p) is not None}


def response(spec: Spec, factors: dict, xs) -> dict:
    """Percent changes after a permanent multiplicative shock, e.g. factors={'t': 0.6}.

    Returns local (p, q, S, r, D at xs) and city-wide (xbar, u, L, area, total rent ...) changes.
    """
    a, b = solve(spec), solve(spec.scaled(**factors))
    xs = np.asarray(xs, float)
    pct = lambda new, old: 100 * (new / old - 1)
    la, lb = a.local(xs), b.local(xs)
    out = {"local_pct": {k: pct(lb[k], la[k]) for k in la},
           "land_rent_pct": pct(b.land_rent(xs), a.land_rent(xs))}
    agg_a, agg_b = a.aggregates(), b.aggregates()
    out["city_pct"] = {k: pct(agg_b[k], agg_a[k]) for k in
                       ("L", "u", "xbar", "area", "total_land_rent", "differential_rent",
                        "floor_space", "housing_bill", "commuting_cost")}
    return out


# ---------------------------------------------------------------- analytic closed-city statics
def _weights(city: City):
    """E = int D e_u dx, int D dx and the density-weighted mean e_u_bar (eq. E in the note)."""
    s = city.spec
    eu = lambda x: s.prefs.e_u(city.local(x)["p"], city.u)
    E = integrate(lambda x: city.local(x)["D"] * eu(x), 0, city.xbar)
    ID = integrate(lambda x: city.local(x)["D"], 0, city.xbar)
    return eu, E, ID, E / ID


def analytic_closed(city: City, xs) -> dict:
    """Elasticities of u, xbar, p(x), r(x) for a closed city from the note's formulas.

    Returns {'u': {param: e}, 'xbar': {...}, 'p': {param: array}, 'r': {param: array}}.
    """
    s, th, t, L = city.spec, city.spec.theta, city.spec.t, city.L
    if s.L is None or s.u is not None:
        raise ValueError("analytic_closed needs a closed city (L set, u and migration unset)")
    eu, E, _, eu_bar = _weights(city)
    xs = np.asarray(xs, float)
    du = {"L": -t / (th * E), "rA": -city.xbar / E, "y": 1 / eu_bar,
          "t": -2 * L / (th * E), "theta": t * L / (th**2 * E)}
    direct = {"y": (1.0, 0.0), "t": (0.0, 1.0)}   # (dy, dt) per unit of the parameter

    def dp_at(x, par):
        dy, dt_ = direct.get(par, (0.0, 0.0))
        q = city.local(x)["q"]
        return (dy - x * dt_ - eu(x) * du[par]) / q

    out = {"u": {}, "xbar": {}, "p": {}, "r": {}}
    loc, lb = city.local(xs), city.local(city.xbar)
    hb = s.tech.h(s.tech.S_of_p(city.pbar))
    for par, dpar in du.items():
        val = getattr(s, par)
        out["u"][par] = val * dpar / city.u
        dpbar = 1 / hb if par == "rA" else 0.0
        out["xbar"][par] = val * lb["q"] * (dp_at(city.xbar, par) - dpbar) / t / city.xbar
        out["p"][par] = val * dp_at(xs, par) / loc["p"]
        h_p_over_r = s.tech.h(loc["S"]) * loc["p"] / loc["r"]   # elasticity of R(p) w.r.t. p
        out["r"][par] = out["p"][par] * h_p_over_r
    return out


def pivots(city: City) -> dict:
    """Rotation points: x_hat (income) and x_star (commuting cost); None if no root inside the city.

    x_hat solves e_u(x) = e_u_bar; x_star solves x / e_u(x) = 2L / (theta E).
    """
    eu, E, _, eu_bar = _weights(city)
    th, L, xb = city.spec.theta, city.L, city.xbar

    def root(g):
        return brentq(g, 1e-9, xb) if g(1e-9) * g(xb) < 0 else None

    return {"y": root(lambda x: eu(x) - eu_bar),
            "t": root(lambda x: x - eu(x) * 2 * L / (th * E))}


# ---------------------------------------------------------------- parameter uncertainty
def propagate(make_spec, outcome, draws: int = 200, seed: int = 0) -> np.ndarray:
    """Monte Carlo: make_spec(rng) -> Spec, outcome(City) -> array. Returns (draws_ok, k) array.

    Quote quantiles, not point estimates: level effects such as open-city population (and the
    rent gradient) are very sensitive to gamma = 1/(alpha (1-beta)). Draws whose city does not
    solve are dropped (and counted in the log).

    Example:
        q = np.percentile(propagate(draw, lambda c: c.xbar, 100), [5, 50, 95])
    """
    rng, rows, failed = np.random.default_rng(seed), [], 0
    for _ in range(draws):
        try:
            rows.append(np.atleast_1d(outcome(solve(make_spec(rng)))))
        except (ValueError, RuntimeError):
            failed += 1
    logger.info("propagate: {} ok, {} failed", len(rows), failed)
    if not rows:
        raise RuntimeError("every draw failed to solve")
    return np.array(rows)
