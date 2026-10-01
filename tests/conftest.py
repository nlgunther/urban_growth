import pytest

from muthmills import CobbDouglas, CobbDouglasTech, Spec, StoneGeary

BASE = dict(y=6e4, t=400.0, rA=1.28e5)


@pytest.fixture
def cd_spec():
    """Calibrated Cobb-Douglas city of the note (alpha=.25, beta=.8, L=1e6)."""
    return Spec(CobbDouglas(0.25), CobbDouglasTech(0.8), L=1e6, **BASE)


@pytest.fixture
def sg_spec():
    """Non-homothetic Stone-Geary city: minimum floor space q0 and subsistence c0."""
    return Spec(StoneGeary(0.25, c0=5000.0, q0=30.0), CobbDouglasTech(0.8), L=1e6, **BASE)
