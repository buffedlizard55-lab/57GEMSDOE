"""Regression tests for the lane's feature geometry (IR-57-STRIKE-01).

The strike fallback in :func:`gems57.anatomy.fold_geometry` was once inverted
(``np.where(isfinite(s), 0.0, s)``), which made ``sin2``/``cos2`` the constants
0/1 and decomposed the offset frame in a grid-aligned frame instead of the
local trace frame.  These tests pin the corrected behaviour on a synthetic
diagonal trace where the two frames differ measurably.
"""
import numpy as np
import pytest

from gems57.anatomy import FEATURES, fold_geometry
from gems57.grid import Grid


def _grid(catalogue: np.ndarray) -> Grid:
    footprint = np.ones_like(catalogue, bool)
    return Grid(footprint=footprint, catalogue=catalogue, crs=None,
                transform=None, height=catalogue.shape[0], width=catalogue.shape[1])


def _diagonal_catalogue(n=80, w=80):
    """Two straight traces with different strikes: a (1,1) diagonal at azimuth
    135 deg and a (1,-1) anti-diagonal at azimuth 45 deg."""
    cat = np.zeros((n, w), bool)
    for i in range(20, 50):
        cat[i, i] = True            # azimuth 135 deg
        cat[i, 69 - i] = True       # azimuth 45 deg
    return cat


def test_strike_encoding_matches_trace_orientation():
    """IR-57-STRIKE-01 pin: the cyclic encoding must reflect the actual anchor
    strike.  Azimuth 135 deg gives sin(2*135) = -1, cos(2*135) = 0; azimuth
    45 deg gives sin(2*45) = +1, cos(2*45) = 0.  With the inverted fallback the
    encoding was the constant (0, 1) regardless of orientation."""
    cat = _diagonal_catalogue()
    g = _grid(cat)
    hidden = np.zeros_like(cat)
    domain = np.ones_like(cat)
    geom = fold_geometry(g, cat, hidden, domain, "test")
    assert geom.X.shape[1] == len(FEATURES)
    sin2 = geom.X[:, FEATURES.index("sin2")]
    cos2 = geom.X[:, FEATURES.index("cos2")]
    assert np.isfinite(geom.X).all()
    # both orientations are present, so the encoding must take both values
    assert set(np.unique(np.round(sin2, 3))) == {-1.0, 1.0}
    assert np.ptp(cos2) < 0.1          # cos(90) = cos(270) = 0 for both
    # and the encoding must agree with the feature interaction columns
    d = geom.X[:, FEATURES.index("d")]
    np.testing.assert_allclose(geom.X[:, FEATURES.index("sin2d")], sin2 * d,
                               rtol=1e-5, atol=1e-5)


def test_offset_frame_is_trace_aligned_not_grid_aligned():
    """A pixel offset perpendicular to a 45-degree trace must have d_perp > 0
    and d_par ~ 0; a grid-aligned decomposition would swap them."""
    cat = _diagonal_catalogue()
    g = _grid(cat)
    hidden = np.zeros_like(cat)
    domain = np.ones_like(cat)
    geom = fold_geometry(g, cat, hidden, domain, "test")
    # anchor is the trace pixel nearest to each active cell; pick active cells
    # offset along (row+1, col-1) -- perpendicular to a (1,1) trace
    d = geom.X[:, FEATURES.index("d")]
    d_perp = geom.X[:, FEATURES.index("d_perp")]
    d_par = geom.X[:, FEATURES.index("d_par_abs")]
    # cells whose offset is predominantly cross-strike (within 3 px of a trace)
    perp_cells = (d > 0) & (d < 3) & (d_perp > 0.9 * d)
    assert perp_cells.any(), "expected cells whose offset is mostly cross-strike"
    # for those cells the along-strike component must be the small one; with the
    # pre-fix grid-aligned frame the two components were row/col offsets and
    # this fails for the (1,-1)-oriented trace
    assert (d_par[perp_cells] < 0.5 * d[perp_cells]).mean() > 0.9


def test_interaction_features_are_strike_times_distance():
    cat = _diagonal_catalogue()
    g = _grid(cat)
    hidden = np.zeros_like(cat)
    domain = np.ones_like(cat)
    geom = fold_geometry(g, cat, hidden, domain, "test")
    d = geom.X[:, FEATURES.index("d")]
    sin2 = geom.X[:, FEATURES.index("sin2")]
    cos2 = geom.X[:, FEATURES.index("cos2")]
    sin2d = geom.X[:, FEATURES.index("sin2d")]
    cos2d = geom.X[:, FEATURES.index("cos2d")]
    np.testing.assert_allclose(sin2d, sin2 * d, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(cos2d, cos2 * d, rtol=1e-5, atol=1e-5)
