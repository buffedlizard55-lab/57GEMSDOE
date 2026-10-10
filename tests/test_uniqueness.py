"""Regression tests for the parallel-run uniqueness screen (IR-57-RHO-01)."""
import hashlib
import json

import numpy as np
import pytest
import rasterio
from affine import Affine

from gems57.grid import CRS_EPSG, TRANSFORM
from gems57.uniqueness import (JACCARD_LIMIT, OVERLAP_LIMIT, RHO_LIMIT,
                               compare_array_to_registry,
                               compare_dots_to_registry,
                               compare_surface_to_registry,
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


def test_jaccard_similarity_is_a_diagnostic_not_a_gate():
    a = _sparse(4, 4000).astype(np.float32)
    b = a.copy()
    ys, xs = np.nonzero(b)
    rng = np.random.default_rng(9)
    k = len(ys) // 10
    b[ys[:k], xs[:k]] = False
    b[rng.integers(0, SHAPE[0], k), rng.integers(0, SHAPE[1], k)] = True
    r = surface_rho(a, b, np.ones(SHAPE, bool))
    # This is only a descriptive set-similarity measurement; the protocol
    # thresholds full-footprint rho and candidate-forward 3 px overlap.
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


def _write_registry(path, raster, submission="prior", transform=TRANSFORM):
    profile = {
        "driver": "GTiff", "height": raster.shape[0], "width": raster.shape[1],
        "count": 1, "dtype": raster.dtype, "crs": CRS_EPSG,
        "transform": transform,
    }
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(raster, 1)
    index_path = path.with_suffix(".json")
    index_path.write_text(json.dumps({"complete_accessible_scan": True,
        "n_unique_grid_rasters": 1, "rasters": [{
            "cache_file": str(path), "repo_first": "owner/repo",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "sources": [f"owner/repo:{submission}"],
        }]}))
    return index_path


def test_jaccard_above_diagnostic_reference_alone_does_not_fail_literal_gate(tmp_path):
    mine = np.zeros(SHAPE, np.float32)
    prior = np.zeros(SHAPE, np.float32)
    # 134 shared dots out of 200 in each map yield Jaccard > 0.50, while
    # exactly 67% of candidate dots overlap within 3 px. Spacing by 10 px
    # prevents unintended neighbours; full-footprint rho remains below 0.90.
    points = [(20 + (i // 30) * 10, 20 + (i % 30) * 10) for i in range(266)]
    for y, x in points[:200]:
        mine[y, x] = 1.0
    for y, x in points[:134] + points[200:266]:
        prior[y, x] = 1.0
    index = _write_registry(tmp_path / "prior.tif", prior)
    result = compare_array_to_registry(mine, index, np.ones(SHAPE, bool))
    row = result["rows"][0]
    assert row["jaccard_dot_sets"] > JACCARD_LIMIT
    assert row["jaccard_over_diagnostic_reference"]
    assert row["my_dots_within_3px_of_theirs"] == pytest.approx(0.67)
    assert abs(row["spearman_full_footprint"]) < RHO_LIMIT
    assert not row["duplicate_by_rho"] and not row["duplicate_by_overlap"]
    assert result["unique"] and result["duplicate_count"] == 0
    assert "jaccard_diagnostic_reference" in result
    assert "jaccard_limit" not in result


def test_literal_preplacement_rho_gate_detects_an_exact_surface_copy(tmp_path):
    surface = np.linspace(0, 1, 400 * 400, dtype=np.float32).reshape(SHAPE)
    footprint = np.ones(SHAPE, bool)
    index = _write_registry(tmp_path / "prior.tif", surface.copy())
    result = compare_surface_to_registry(surface, index, footprint)
    assert result["verdict"].startswith("FAIL")
    assert result["first_rho_firing"]["spearman_full_footprint"] == pytest.approx(1.0)
    assert result["n_registry_checked"] == 1
    assert result["short_circuited_on_failure"]


def test_literal_final_dot_gate_has_no_reverse_overlap_exemption(tmp_path):
    prior = np.zeros(SHAPE, np.uint8)
    mine = np.zeros(SHAPE, bool)
    # Every candidate dot is within 3 px of a prior dot. The prior has extra
    # dots too, but the protocol is the candidate-to-prior direction only.
    coords = [(100 + i * 8, 100) for i in range(8)]
    for y, x in coords:
        mine[y, x] = True
        prior[y, x] = 1
    prior[150, 150] = 1
    surface = np.zeros(SHAPE, np.float32)
    surface[90:170, 90:170] = np.linspace(0.1, 1.0, 80 * 80, dtype=np.float32).reshape(80, 80)
    index = _write_registry(tmp_path / "prior.tif", prior)
    result = compare_dots_to_registry(surface, mine, index, np.ones(SHAPE, bool))
    assert result["verdict"].startswith("FAIL")
    assert result["first_firing"]["duplicate_by_overlap"]
    assert result["first_firing"]["my_dots_within_3px_of_theirs"] == pytest.approx(1.0)
    assert result["first_firing"].get("their_dots_within_3px_of_mine") is None


def test_registry_clearance_fails_closed_on_missing_indexed_raster(tmp_path):
    surface = np.linspace(0, 1, 400 * 400, dtype=np.float32).reshape(SHAPE)
    missing_index = tmp_path / "missing.json"
    missing_index.write_text(json.dumps({"n_unique_grid_rasters": 1, "rasters": [{
        "cache_file": str(tmp_path / "absent.tif"), "sources": ["owner/repo:raster"],
    }]}))
    result = compare_surface_to_registry(surface, missing_index, np.ones(SHAPE, bool))
    assert result["verdict"] == "HOLD — registry scan incomplete"
    assert not result["registry_complete"]
    assert not result["unique_by_protocol"]


def test_transform_offset_is_reprojected_not_silently_dropped(tmp_path):
    rng = np.random.default_rng(20)
    surface = rng.random(SHAPE, dtype=np.float32)
    prior = (rng.random(SHAPE) < 0.08).astype(np.uint8)
    shifted = TRANSFORM @ Affine.translation(1, -1)
    index = _write_registry(tmp_path / "shifted.tif", prior,
                            submission="shifted", transform=shifted)
    result = compare_surface_to_registry(surface, index, np.ones(SHAPE, bool))
    assert result["registry_complete"]
    assert result["n_reprojected_priors"] == 1
    assert result["rows"][0]["needs_reproject"]
    assert result["verdict"] == "PASS"
