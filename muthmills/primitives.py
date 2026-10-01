"""Preferences and housing technology for the Muth-Mills city.

Notation follows muth_mills_revisited.tex (and Brueckner 1987):
expenditure function e(p, u), land-rent function R(p), building height S.
All functions are vectorised over numpy arrays.
"""
from dataclasses import dataclass

import numpy as np

P_LO, P_HI = 1e-12, 1e12   # bracket for price searches; wide enough for any sane calibration


def solve_increasing(f, shape, lo: float = P_LO, hi: float = P_HI, iters: int = 80):
    """Root of an increasing function f(p) (elementwise), found by bisection in log p.

    Example:
        solve_increasing(lambda p: p**2 - 4.0, (3,))   # -> array([2., 2., 2.])
    """
    a, b = np.full(shape, np.log(lo)), np.full(shape, np.log(hi))
    with np.errstate(all="ignore"):
        # NaN (e.g. inf - inf from overflow at extreme beta) fails these tests too, by design
        if not (np.all(f(np.exp(a)) < 0) and np.all(f(np.exp(b)) > 0)):
            raise ValueError("no sign change in the price bracket: check calibration / overflow")
        for _ in range(iters):
            mid = 0.5 * (a + b)
            positive = f(np.exp(mid)) > 0
            b, a = np.where(positive, mid, b), np.where(positive, a, mid)
    return np.exp(0.5 * (a + b))


@dataclass(frozen=True)
class StoneGeary:
    """v(c, q) = (c - c0)^(1-alpha) (q - q0)^alpha ; c0 = q0 = 0 is Cobb-Douglas.

    alpha is the housing budget share of income above subsistence; q0 > 0 makes
    the income elasticity of housing demand below one (non-homothetic).
    Expenditure function: e(p, u) = c0 + p q0 + u p^alpha / kappa.
    """
    alpha: float
    c0: float = 0.0
    q0: float = 0.0

    @property
    def kappa(self) -> float:
        return self.alpha**self.alpha * (1 - self.alpha) ** (1 - self.alpha)

    @property
    def is_cobb_douglas(self) -> bool:
        return self.c0 == 0.0 and self.q0 == 0.0

    def expenditure(self, p, u):
        return self.c0 + p * self.q0 + u * p**self.alpha / self.kappa

    def hicksian_q(self, p, u):
        """Compensated demand for floor space, e_p (Shephard's lemma)."""
        return self.q0 + u * self.alpha * p ** (self.alpha - 1) / self.kappa

    def e_u(self, p, u):
        """Income needed per unit of extra utility (1 / marginal utility of income)."""
        return p**self.alpha / self.kappa

    def utility(self, m, p):
        """Utility reachable with net income m at floor-space price p."""
        return (m - self.c0 - p * self.q0) * self.kappa / p**self.alpha

    def bid_price(self, m, u):
        """Price p solving e(p, u) = m (eq. bidprice in the note)."""
        m = np.asarray(m, float)
        if self.is_cobb_douglas:
            return (self.kappa * m / u) ** (1 / self.alpha)
        return solve_increasing(lambda p: self.expenditure(p, u) - m, m.shape)


def CobbDouglas(alpha: float) -> StoneGeary:
    return StoneGeary(alpha)


@dataclass(frozen=True)
class CobbDouglasTech:
    """Floor space per acre h(S) = S^beta, capital price i, optional height cap S_cap.

    With a cap (zoning), builders use S = min(S*(p), S_cap); land rent is still the
    zero-profit residual R(p) = p h(S) - i S (Bertaud-Brueckner 2005).
    """
    beta: float
    i: float = 1.0
    S_cap: float = np.inf

    def S_of_p(self, p):
        return np.minimum((self.beta * p / self.i) ** (1 / (1 - self.beta)), self.S_cap)

    def h(self, S):
        return S**self.beta

    def R(self, p):
        S = self.S_of_p(p)
        return p * self.h(S) - self.i * S

    def p_bar(self, rA: float) -> float:
        """Boundary price: R(p_bar) = rA. Depends only on rA and technology."""
        return float(solve_increasing(lambda p: self.R(p) - rA, (1,))[0])
