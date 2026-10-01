# muthmills

A small, tested solver for the Muth–Mills monocentric city (Brueckner 1987, as restated in
`muth_mills_revisited.tex`), with comparative statics, asset "betas" by distance, and rent-path
valuation. It turns the note's results into numbers you can shock.

## Why use it

Given a handful of city primitives (income, commuting cost, farmland rent, housing technology,
population or utility) it tells you, at every distance from the centre, the price of floor space,
land rent, building height, dwelling size and density, and how each responds to population growth,
income growth, commuting-cost changes (transit, remote work), farmland rent and zoning.

## Quick start

```python
import numpy as np
from muthmills import CobbDouglas, CobbDouglasTech, Spec, solve
from muthmills.statics import location_betas, pivots, response

spec = Spec(CobbDouglas(0.25), CobbDouglasTech(0.8), y=6e4, t=400.0, rA=1.28e5, L=1e6)
city = solve(spec)
city.xbar                                   # 33.03 miles
response(spec, {"t": 0.6}, [0, 16, 30])     # remote work: t falls 40%
location_betas(spec, [0, 10, 25], ["y", "t"])   # d ln rent / d ln shock by distance
pivots(city)                                # {'y': 6.9, 't': 13.2} miles
```

## Key ideas

- **Three city types.** `L=` closed (u adjusts), `u=` open (L adjusts), `L=, u=, migration=`
  partly open. The choice decides *which predictions exist* (an income rotation exists only when
  the city is mostly closed); see `DESIGN.md`.
- **Everything is a function of net income** `m = y - t x` and utility `u`, so the solver is one
  root-find in `u`.
- **Analytic = numeric.** `statics.analytic_closed` implements the note's theorem and is tested
  against finite differences to 1e-5.
- **Pluggable primitives.** `StoneGeary` (non-homothetic) and `CobbDouglasTech` (with a height cap)
  are the two shipped classes; the solver only uses their small method interface.

## Docs

`DESIGN.md` (quantities, relationships, investment use, roadmap) · `API.md` · `CHEATSHEET.md` ·
`workflows.md`. Run tests with `python -m pytest tests -q`.
