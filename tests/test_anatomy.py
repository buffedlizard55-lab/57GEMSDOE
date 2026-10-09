"""Regression tests for the fitted anatomy feature frame.

IR-57-STRIKE-01: ``fold_geometry`` once carried
``np.where(np.isfinite(s), 0.0, s)`` — an inverted NaN-fill that zeroed every
finite strike, collapsed sin2/cos2 to constants and forced the offset frame to
strike 0.  The tests here pin the corrected behaviour on the real catalogue.
"""
import numpy as np
import pytest
import rasterio

from pathlib import Path

from gems57 import load_grid
from gems57.anatomy import FEATURES, fold_geometry

ROOT = Path(__file__).resolve().parents[1]


def _visible_hidden_domain(grid):
    visible = grid.catalogue.copy()
    # withhold nothing; domain = whole footprint minus catalogue
    hidden = np.zeros(grid.shape, bool)
    domain = grid.footprint & ~visible
    return visible, hidden, domain


def test_fold_geometry_strike_frame_is_not_degenerate():
    grid = load_grid()
    visible, hidden, domain = _visible_hidden_domain(grid)
    # a small domain keeps the test fast: crop to a 400x400 px window on faults
    ys, xs = np.nonzero(visible)
    y0, x0 = ys[len(ys) // 2], xs[len(xs) // 2]
    sl = (slice(max(0, y0 - 200), y0 + 200), slice(max(0, x0 - 200), x0 + 200))
    dom = np.zeros(grid.shape, bool)
    dom[sl] = domain[sl]
    g = fold_geometry(grid, visible, hidden, dom, "regression_strike")
    assert g.X.shape[1] == len(FEATURES) == len(g.feature_names)
    i_sin = g.feature_names.index("sin2")
    i_cos = g.feature_names.index("cos2")
    i_perp = g.feature_names.index("d_perp")
    assert g.X.shape[0] > 1000, "window too small to be meaningful"
    # the bug signature: sin2 constant 0 and cos2 constant 1 (strike == 0)
    assert float(g.X[:, i_sin].std()) > 0.05, "sin2 is degenerate — strike frame broken"
    assert float(g.X[:, i_cos].std()) > 0.05, "cos2 is degenerate — strike frame broken"
    assert float(g.X[:, i_perp].std()) > 0.5, "d_perp has no spread — offset frame broken"


def test_geo_planes_load_and_match_grid():
    from gems57.geo import GEO_FEATURES, load_planes
    try:
        from gems57.geo import FEATURES_PATH
        if not FEATURES_PATH.exists():
            pytest.skip("training_features.tif not assembled (run prepare_data.py --fetch)")
    except Exception:
        pytest.skip("geo module unavailable")
    grid = load_grid()
    planes = load_planes(grid.footprint)
    assert set(planes) == set(GEO_FEATURES)
    for name, plane in planes.items():
        assert plane.shape == grid.shape and plane.dtype == np.float32
        v = plane[grid.footprint]
        assert np.isfinite(v).all(), f"{name} has non-finite values inside the footprint"
        assert float(np.abs(v).max()) <= 10.0 + 1e-6, f"{name} exceeds the robust clip"
    # geo-augmented fold_geometry appends the block in GEO_FEATURES order
    visible, hidden, domain = _visible_hidden_domain(grid)
    ys, xs = np.nonzero(visible)
    y0, x0 = ys[len(ys) // 2], xs[len(xs) // 2]
    dom = np.zeros(grid.shape, bool)
    dom[max(0, y0 - 100):y0 + 100, max(0, x0 - 100):x0 + 100] = True
    g = fold_geometry(grid, visible, hidden, dom, "regression_geo", geo=planes)
    assert g.feature_names == FEATURES + GEO_FEATURES
    assert g.X.shape[1] == len(FEATURES) + len(GEO_FEATURES)
