import numpy as np
import pytest

from muthmills import solve
from muthmills.valuation import land_value, path_specs

XS = [5.0, 20.0, 32.0]


def test_flat_path_has_no_growth_premium(cd_spec):
    v = land_value(cd_spec, {"L": np.full(6, 1e6)}, XS, rho=0.06)
    assert np.allclose(v["growth_premium"], 0, atol=1e-12)
    assert np.allclose(v["static_value"], solve(cd_spec).land_rent(XS) * 1.06 / 0.06)


def test_growth_premium_uniform_inside_for_pure_population_growth(cd_spec):
    # Cobb-Douglas artifact: L shifts ln p uniformly, so every built-up parcel has the same premium.
    v = land_value(cd_spec, {"L": 1e6 * 1.02 ** np.arange(31)}, XS, rho=0.06)
    assert np.all(v["growth_premium"] > 0)
    assert np.allclose(v["growth_premium"], v["growth_premium"][0])


def test_land_beyond_boundary_is_worth_more_than_farmland_once_reached(cd_spec):
    v = land_value(cd_spec, {"L": 1e6 * 1.02 ** np.arange(31)}, [36.0], rho=0.06)
    assert v["value"][0] > v["static_value"][0] == pytest.approx(cd_spec.rA * 1.06 / 0.06)


def test_path_specs_reject_ragged_paths(cd_spec):
    with pytest.raises(ValueError):
        path_specs(cd_spec, {"L": [1e6, 1.1e6], "y": [6e4]})
