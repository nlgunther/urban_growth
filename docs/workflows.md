# Workflows

## 1. What does a national commuting-cost shock (remote work) do to core vs ring values?

```python
from muthmills import *
from muthmills.statics import response
spec = Spec(CobbDouglas(.25), CobbDouglasTech(.8), y=6e4, t=400, rA=1.28e5, L=1e6)
r = response(spec, {"t": 0.6}, [0, 16, 30])
r["local_pct"]["p"]     # [-17.7, -0.8, +20.6]: donut (finite crossing near 16.6 mi)
r["city_pct"]["xbar"]   # +37% radius
```
Use the **closed** city for an economy-wide shock. Add `alpha=1.1` to the factors to let remote
work also raise floor-space demand. See `API.md#response`.

## 2. Which drivers does an observed change in the price gradient point to?

```python
from muthmills.statics import location_betas
xs = [0, 8, 16, 25, 32]
B = location_betas(spec, xs, ["L", "y", "t"])
# L row ~ constant (level shift); y row rises with x; t row falls with x (rotations)
```
Regress observed `d ln rent(x)` on the columns of `B` to decompose a change into level and rotation
factors. Re-run with `migration=` set to see how openness turns the income rotation into a level shift.

## 3. Uncertainty bands for an exposure

```python
import numpy as np
from muthmills.statics import propagate
draw = lambda rng: Spec(CobbDouglas(rng.uniform(.2,.3)), CobbDouglasTech(rng.uniform(.7,.85)),
                        y=6e4, t=rng.uniform(300,500), rA=1.28e5, L=1e6)
out = propagate(draw, lambda c: c.xbar, draws=200)
np.percentile(out, [5, 50, 95])
```
Quote the band, not the point estimate.
