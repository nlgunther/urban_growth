"""From equilibrium rents to asset values under a scenario path of the city's drivers.

Perfect-foresight, frictionless-adjustment approximation: value at x is the PV of the
model rent r(x, k) along the path. The excess over the static perpetuity is a
Capozza-Helsley-style growth premium (no conversion cost, no uncertainty/option value).
"""
from typing import Mapping, Sequence

import numpy as np

from .city import Spec, solve


def path_specs(spec: Spec, paths: Mapping[str, Sequence[float]]) -> list[Spec]:
    """Spec at each year k from absolute parameter paths; all paths must have equal length."""
    lengths = {len(v) for v in paths.values()}
    if len(lengths) != 1:
        raise ValueError("all paths must have the same length")
    return [spec.scaled(**{p: v[k] / getattr(spec, p) for p, v in paths.items()})
            for k in range(lengths.pop())]


def land_value(spec: Spec, paths: Mapping[str, Sequence[float]], xs, rho: float) -> dict:
    """PV of land rent at distances xs along the path (years 0..T), plus terminal perpetuity.

    Returns {'value', 'static_value', 'growth_premium'}: static_value capitalises today's rent,
    r0 (1 + rho) / rho, and growth_premium = value / static_value - 1.  Rents are held flat after
    year T (conservative).  Land beyond today's boundary has static value = farmland value, so
    its premium is pure conversion value; there is no conversion cost or option value (v2).
    The premium is uniform inside the city for pure population growth only because
    Cobb-Douglas shifts ln p uniformly; do not expect that in general.

    Example:
        land_value(spec, {"L": 1e6 * 1.02 ** np.arange(31)}, [5, 15, 25, 32], rho=0.06)
    """
    xs = np.asarray(xs, float)
    rents = np.array([solve(s).land_rent(xs) for s in path_specs(spec, paths)])   # (T+1, len(xs))
    T = len(rents) - 1
    disc = (1 + rho) ** -np.arange(T + 1)
    value = disc @ rents + rents[-1] / rho * (1 + rho) ** -T   # rents after year T stay at r_T
    static = rents[0] * (1 + rho) / rho
    return {"value": value, "static_value": static, "growth_premium": value / static - 1}
