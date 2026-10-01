# Cheatsheet

## Build a city
```python
from muthmills import *
closed = Spec(CobbDouglas(.25), CobbDouglasTech(.8), y=6e4, t=400, rA=1.28e5, L=1e6)
open_  = Spec(CobbDouglas(.25), CobbDouglasTech(.8), y=6e4, t=400, rA=1.28e5, u=13068.4)
partly = Spec(CobbDouglas(.25), CobbDouglasTech(.8), y=6e4, t=400, rA=1.28e5, L=1e6, u=13068.4, migration=2.0)
capped = Spec(CobbDouglas(.25), CobbDouglasTech(.8, S_cap=2e7), y=6e4, t=400, rA=1.28e5, L=1e6)  # solve(capped, n=2000)
nonhom = Spec(StoneGeary(.25, c0=5000, q0=30), CobbDouglasTech(.8), y=6e4, t=400, rA=1.28e5, L=1e6)
```

## Common operations
| Want | Call |
|---|---|
| Profiles at distances | `solve(spec).local([0, 10, 25])` |
| City totals / identity check | `solve(spec).aggregates()` |
| % change after a shock | `response(spec, {"t": 0.6}, xs)` |
| Exposure by distance | `location_betas(spec, xs, ["L","y","t","rA"], asset="land")` |
| Rotation points | `pivots(solve(closed))` |
| Rent-path value | `land_value(spec, {"L": 1e6*1.02**np.arange(31)}, xs, rho=.06)` |
| Uncertainty bands | `np.percentile(propagate(draw, fn, 200), [5,50,95], axis=0)` |

## Shockable parameters
`L u y t rA theta alpha i` — `scaled(t=0.6)` multiplies. Closed cities have no `u`, open no `L`.

## Gotchas
- Pivots exist only for a mostly closed city; in an open city income raises prices everywhere.
- `x` beyond the boundary: `land_rent` returns `rA`; `local()[“r”]` is below `rA`.
- Height caps kink the integrand: pass `n=2000` to `solve`.
- `u` is not comparable across different `alpha`.
- Differential rent `r - rA` betas look huge at the edge; that is accounting (`r/(r-rA)`), not information.
- Cobb–Douglas closed city: land rent at fixed `x` is invariant to capital price `i`; rate effects on
  land value come through the capitalisation rate only.
