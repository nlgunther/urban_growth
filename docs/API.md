# API reference

Units are whatever you use consistently. The note uses miles, dollars per year, and rents per
square mile per year. Utility `u` is ordinal: do not compare it across different `alpha`.

## muthmills.primitives

### StoneGeary(alpha, c0=0.0, q0=0.0)
`v = (c - c0)^(1-alpha) (q - q0)^alpha`; `c0 = q0 = 0` is Cobb–Douglas (`CobbDouglas(alpha)`).
Methods (vectorised): `expenditure(p,u)`, `hicksian_q(p,u)`, `e_u(p,u)`, `utility(m,p)`,
`bid_price(m,u)` (closed form for Cobb–Douglas, log-bisection otherwise).

### CobbDouglasTech(beta, i=1.0, S_cap=inf)
`h(S) = S^beta`. Methods: `S_of_p(p)` (capped), `h(S)`, `R(p)` (land-rent function),
`p_bar(rA)` (boundary price). **Raises** `ValueError` if no price bracket exists (extreme `beta`).

### solve_increasing(f, shape, lo, hi, iters)
Elementwise log-bisection for increasing `f`. **Raises** `ValueError` without a sign change.

## muthmills.city

### Spec(prefs, tech, y, t, rA, theta=pi, L=None, u=None, migration=None)
Closed: `L`. Open: `u`. Partly open: `L`, `u`, `migration` with `L(u) = L (u/u_ref)^migration`.
**Raises** `ValueError` for any other combination.
- `get(name)` – value of `L,u,y,t,rA,theta,alpha,i` (None if unset).
- `scaled(**factors)` – multiply parameters: `spec.scaled(t=0.6)`. **Raises** `ValueError` for
  unknown or unset parameters.

### solve(spec, n=400) -> City
Equilibrium. `n` = Gauss–Legendre nodes (use ~2000 when a height cap binds).
**Raises** `ValueError` if no city is viable, `RuntimeError` if the utility bracket fails.

### City
Fields `spec, u, xbar, L, pbar`.
- `local(x)` -> dict `p, q, S, r, D` (needs `y - t x > 0`).
- `land_rent(x)` -> `max(r, rA)`.
- `aggregates()` -> `area, total_land_rent, differential_rent, floor_space, housing_bill,
  commuting_cost, center_density, center_rent_ratio, commute_share_edge,
  rent_identity_residual` (should be ~0: the note's rent-integral identity).

## muthmills.statics

- `elasticity(spec, outcome, param, step=1e-3)` – d ln outcome / d ln param.
- `location_betas(spec, xs, params=SHOCK_PARAMS, asset="land"|"price"|"dwelling", differential=False)`
  -> `{param: array over xs}`.
- `response(spec, factors, xs)` -> `{"local_pct", "land_rent_pct", "city_pct"}` after a permanent shock.
- `analytic_closed(city, xs)` -> `{"u","xbar","p","r": {param: elasticity}}`, closed city only
  (**raises** `ValueError` otherwise).
- `pivots(city)` -> `{"y": x_hat, "t": x_star}` infinitesimal rotation points; `None` if absent.
- `propagate(make_spec, outcome, draws=200, seed=0)` -> Monte Carlo array; **raises**
  `RuntimeError` if every draw fails.

## muthmills.valuation

- `path_specs(spec, paths)` – Spec per year from absolute parameter paths.
- `land_value(spec, paths, xs, rho)` -> `value, static_value, growth_premium`: PV of rent along the
  path (perfect foresight, rents flat after the last year, no conversion cost).

## Logging
Silent by default. `from loguru import logger; logger.enable("muthmills")` for solver debug output.
