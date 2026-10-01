"""Closed- and open-city equilibrium of the Muth-Mills model.

Closed city: L given, solve for (u, xbar).  Open city: u given, solve for (xbar, L).
Units are whatever the caller uses consistently (the note: miles, $/year, $/sq-mile/year).

Example:
    spec = Spec(CobbDouglas(0.25), CobbDouglasTech(0.8), y=6e4, t=400, rA=1.28e5, L=1e6)
    city = solve(spec)
    city.xbar            # ~33.0 miles
    city.local([0, 10])  # dict of p, q, S, r, D at 0 and 10 miles
"""
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np
from loguru import logger
from scipy.optimize import brentq

from .primitives import CobbDouglasTech, StoneGeary

NODES = 400   # Gauss-Legendre nodes; integrands are smooth unless a height cap binds
SHOCKABLE = ("L", "u", "y", "t", "rA", "theta", "alpha", "i")


@lru_cache(maxsize=None)
def _gl(n: int):
    return np.polynomial.legendre.leggauss(n)


def integrate(f, a: float, b: float, n: int = NODES) -> float:
    """Gauss-Legendre integral of a vectorised f on [a, b]."""
    z, w = _gl(n)
    x = 0.5 * (b - a) * z + 0.5 * (b + a)
    return 0.5 * (b - a) * float(np.sum(w * f(x)))


@dataclass(frozen=True)
class Spec:
    """Everything that defines a city.

    Closed city: L set.  Open city: u set.  Partly open city: L, u and migration all set, with
    L(u) = L * (u / u_ref)^migration, where (L, u) is the reference point and migration >= 0 is
    the population elasticity to utility (0 -> closed, large -> open).
    """
    prefs: StoneGeary
    tech: CobbDouglasTech
    y: float
    t: float
    rA: float
    theta: float = np.pi
    L: float | None = None
    u: float | None = None
    migration: float | None = None

    def __post_init__(self):
        if self.migration is not None:
            if self.L is None or self.u is None or self.migration < 0:
                raise ValueError("partly open city needs L, u and migration >= 0")
        elif (self.L is None) == (self.u is None):
            raise ValueError("set exactly one of L (closed city) or u (open city)")

    def get(self, name: str):
        """Value of a shockable parameter (alpha and i live in prefs / tech); None if unset."""
        return getattr({"alpha": self.prefs, "i": self.tech}.get(name, self), name)

    def scaled(self, **factors: float) -> "Spec":
        """Multiply named parameters: spec.scaled(t=0.6) is a 40% fall in commuting cost.

        Also accepts alpha (housing budget share) and i (capital price, the interest-rate channel).
        """
        bad = set(factors) - set(SHOCKABLE)
        if bad:
            raise ValueError(f"unknown parameters {bad}")
        changes = {}
        for k, f in factors.items():
            if self.get(k) is None:
                raise ValueError(f"{k} is not a parameter of this city (closed cities have no u, open no L)")
            changes[k] = self.get(k) * f
        return replace(self, **{k: v for k, v in changes.items() if k not in ("alpha", "i")},
                       **({"prefs": replace(self.prefs, alpha=changes["alpha"])} if "alpha" in changes else {}),
                       **({"tech": replace(self.tech, i=changes["i"])} if "i" in changes else {}))


@dataclass(frozen=True)
class City:
    """Solved equilibrium. Profiles are evaluated on demand from net income m = y - t x."""
    spec: Spec
    u: float
    xbar: float
    L: float
    pbar: float

    def local(self, x) -> dict:
        """p, q, S, r, D at distance x < y/t (r < rA beyond the boundary, where land is farmed)."""
        s = self.spec
        x = np.asarray(x, float)
        if np.any(s.y - s.t * x <= 0):
            raise ValueError("net income y - t x must be positive")
        p = s.prefs.bid_price(s.y - s.t * x, self.u)
        q = s.prefs.hicksian_q(p, self.u)
        S = s.tech.S_of_p(p)
        return dict(p=p, q=q, S=S, r=s.tech.R(p), D=s.tech.h(S) / q)

    def land_rent(self, x):
        """Rent per unit land: urban inside xbar, agricultural rA outside."""
        return np.maximum(self.local(x)["r"], self.spec.rA)

    def aggregates(self, n: int = NODES) -> dict:
        """City-wide totals (integrals over the disc) plus the rent-integral identity check."""
        s, th = self.spec, self.spec.theta

        def ring(key_fn):
            return th * integrate(lambda x: x * key_fn(x, self.local(x)), 0.0, self.xbar, n)

        area = th * self.xbar**2 / 2
        total_rent = ring(lambda x, d: d["r"])
        per_ray = integrate(lambda x: self.local(x)["r"] - s.rA, 0.0, self.xbar, n)
        return dict(
            L=self.L, u=self.u, xbar=self.xbar, area=area,
            total_land_rent=total_rent, differential_rent=total_rent - s.rA * area,
            floor_space=ring(lambda x, d: s.tech.h(d["S"])),
            housing_bill=ring(lambda x, d: d["p"] * s.tech.h(d["S"])),
            commuting_cost=ring(lambda x, d: s.t * x * d["D"]),
            center_density=float(self.local(0.0)["D"]),
            center_rent_ratio=float(self.local(0.0)["r"] / s.rA),
            commute_share_edge=s.t * self.xbar / s.y,
            rent_identity_residual=per_ray / (s.t * self.L / th) - 1,
        )


def _density(spec: Spec, u: float, x):
    p = spec.prefs.bid_price(spec.y - spec.t * np.asarray(x, float), u)
    return spec.tech.h(spec.tech.S_of_p(p)) / spec.prefs.hicksian_q(p, u)


def _boundary(spec: Spec, u: float) -> tuple[float, float]:
    pbar = spec.tech.p_bar(spec.rA)
    return pbar, (spec.y - spec.prefs.expenditure(pbar, u)) / spec.t


def _population(spec: Spec, u: float, n: int) -> tuple[float, float]:
    _, xbar = _boundary(spec, u)
    if xbar <= 0:
        return 0.0, xbar
    return spec.theta * integrate(lambda x: x * _density(spec, u, x), 0.0, xbar, n), xbar


def _solve_u(spec: Spec, n: int) -> float:
    pbar = spec.tech.p_bar(spec.rA)
    u_hi = spec.prefs.utility(spec.y, pbar)   # u at which the city has zero radius
    if u_hi <= 0:
        raise ValueError("income is below subsistence at the boundary price: no city")
    u_lo = 0.5 * u_hi
    # Closed: target population is L. Partly open: it grows with utility, L (u / u_ref)^migration.
    # Logs avoid overflow for a near-open city (huge migration elasticity).
    log_target = lambda u: np.log(spec.L) + (0.0 if spec.migration is None else spec.migration * np.log(u / spec.u))
    f = lambda u: np.log(max(_population(spec, u, n)[0], 1e-300)) - log_target(u)
    for _ in range(60):   # population explodes as u falls, so halving finds a bracket
        if f(u_lo) > 0:
            break
        u_lo *= 0.5
    else:
        raise RuntimeError("could not bracket closed-city utility")
    return brentq(f, u_lo, u_hi * (1 - 1e-12), xtol=1e-14 * u_hi, rtol=1e-13)


def solve(spec: Spec, n: int = NODES) -> City:
    """Solve the equilibrium of a closed (L), open (u) or partly open (L, u, migration) city."""
    u = _solve_u(spec, n) if spec.L is not None else spec.u
    pbar, xbar = _boundary(spec, u)
    if xbar <= 0:
        raise ValueError("u is too high: no city is viable at this utility level")
    L = spec.L if spec.u is None else _population(spec, u, n)[0]
    logger.debug("solved: u={:.6g} xbar={:.4f} L={:.6g}", u, xbar, L)
    return City(spec, u, xbar, L, pbar)
