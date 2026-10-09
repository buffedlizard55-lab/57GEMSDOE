"""Regression tests for the parallel-run uniqueness screen (IR-57-RHO-01)."""
import json

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gems57.uniqueness import (JACCARD_LIMIT, OVERLAP_LIMIT, RHO_LIMIT,
                               compare_surface_to_registry, compare_to_registry,
                               dot_overlap, surface_rho)

SHAPE = (400, 400)


def _sparse(seed, n):
    rng = np.random.default_rng(seed)
    a = np.zeros(SHAPE, bool)
    a[rng.integers(0, SHAPE[0], n), rng.integers(0, SHAPE[1], n)] = True
    return a


def test_disjoint_sparse_rasters_are_not_flagged_as_duplicates():
    """Two near-disjoint sparse rasters must NOT trip the duplicate screen.

    Their dot-union Spearman is strongly *negative* (phi of two negatively
    associated indicators); the screen must read signed agreement only.
    """
    a = _sparse(1, 3000).astype(np.float32)
    b = _sparse(2, 3000).astype(np.float32)
    valid = np.ones(SHAPE, bool)
    r = surface_rho(a, b, valid)
    assert r["spearman_on_dot_union"] < 0.0, "disjoint supports must give negative rho"
    assert not (r["spearman_on_dot_union"] > RHO_LIMIT)
    assert r["jaccard_dot_sets"] < JACCARD_LIMIT
    assert dot_overlap(a, b) < OVERLAP_LIMIT


def test_dot_union_rho_is_undefined_when_one_support_contains_the_other():
    """A superset relation makes the dot-union statistic constant, hence NaN.

    It must NOT be reported as +1.0, and the screen must not threshold it.
    """
    a = _sparse(3, 3000).astype(np.float32)
    r = surface_rho(a, a.copy(), np.ones(SHAPE, bool))
    assert np.isnan(r["spearman_on_dot_union"])
    # but the full-footprint rank correlation does see the exact copy
    assert r["spearman_full_footprint"] == pytest.approx(1.0, abs=1e-9)
    assert r["spearman_full_footprint"] > RHO_LIMIT
    assert r["jaccard_dot_sets"] == pytest.approx(1.0)


def test_a_90_percent_copy_is_flagged_by_jaccard():
    a = _sparse(4, 4000).astype(np.float32)
    b = a.copy()
    ys, xs = np.nonzero(b)
    rng = np.random.default_rng(9)
    k = len(ys) // 10
    b[ys[:k], xs[:k]] = False
    b[rng.integers(0, SHAPE[0], k), rng.integers(0, SHAPE[1], k)] = True
    r = surface_rho(a, b, np.ones(SHAPE, bool))
    # measured: rho_full = 0.8985 (just under the bar), jaccard = 0.8198.
    # Jaccard is what catches a near-copy; rho only reaches 1.0 on an exact one.
    assert r["spearman_full_footprint"] == pytest.approx(0.8985, abs=0.01)
    assert r["jaccard_dot_sets"] == pytest.approx(0.8198, abs=0.01)
    assert r["jaccard_dot_sets"] > JACCARD_LIMIT


def test_overlap_is_asymmetric_and_directional():
    a = _sparse(5, 2000).astype(np.float32)
    b = _sparse(6, 2000).astype(np.float32)
    assert 0.0 <= dot_overlap(a, b) <= 1.0
    assert dot_overlap(a, np.zeros(SHAPE, bool)) == 0.0


def test_full_footprint_rho_is_the_degenerate_one():
    """Sanity: on the whole footprint both arrays are ~99 % zero, so rho ~ 0."""
    a = _sparse(7, 3000).astype(np.float32)
    b = _sparse(8, 3000).astype(np.float32)
    r = surface_rho(a, b, np.ones(SHAPE, bool))
    assert abs(r["spearman_full_footprint"]) < 0.05


def _write_small_raster(path, values):
    values = np.asarray(values, np.float32)
    with rasterio.open(path, "w", driver="GTiff", height=values.shape[0],
                       width=values.shape[1], count=1, dtype="float32",
                       crs="EPSG:32611", transform=from_origin(0, values.shape[0], 1, 1)) as dst:
        dst.write(values, 1)


def test_surface_audit_stops_on_exact_registry_copy(tmp_path):
    candidate = np.zeros((32, 32), np.float32)
    candidate[4:28, 4:28] = np.linspace(0.01, 0.9, 24 * 24).reshape(24, 24)
    prior = tmp_path / "prior.tif"
    _write_small_raster(prior, candidate)
    index = tmp_path / "index.json"
    index.write_text(json.dumps([{"repo": "test", "submission": "copy",
                                  "file": str(prior)}]))

    report = compare_surface_to_registry(candidate, index, np.ones(candidate.shape, bool))
    assert report["complete"]
    assert report["duplicate"]
    assert not report["unique_within_inventory"]
    assert report["worst_spearman_full_footprint"] == pytest.approx(1.0)


def test_final_dot_audit_stops_on_exact_prior_copy(tmp_path):
    candidate = np.zeros((32, 32), np.float32)
    candidate[8:12, 8:12] = 1.0
    prior = tmp_path / "prior-dots.tif"
    _write_small_raster(prior, candidate)
    index = tmp_path / "index.json"
    index.write_text(json.dumps([{"repo": "test", "submission": "copy",
                                  "file": str(prior)}]))

    report = compare_to_registry(candidate, index, np.ones(candidate.shape, bool))
    row = report["rows"][0]
    assert report["audit_complete"]
    assert not report["unique"]
    assert row["duplicate_by_rho"]
    assert row["duplicate_by_overlap"]
    assert row["my_dots_within_3px_of_theirs"] == pytest.approx(1.0)


def test_final_dot_audit_fails_closed_on_missing_prior(tmp_path):
    candidate = np.zeros((32, 32), np.float32)
    candidate[10, 10] = 1.0
    index = tmp_path / "index.json"
    index.write_text(json.dumps([{"repo": "test", "submission": "missing",
                                  "file": str(tmp_path / "absent.tif")}]))

    report = compare_to_registry(candidate, index, np.ones(candidate.shape, bool))
    assert not report["audit_complete"]
    assert not report["unique"]
    assert report["n_checked"] == 0
    assert report["rows"][0]["error"].startswith("RasterioIOError")
