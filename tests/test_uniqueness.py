"""Regression tests for the protocol thresholds and diagnostic-only Jaccard."""
import hashlib

import numpy as np
import pytest
import rasterio
from affine import Affine

from gems57.uniqueness import (JACCARD_LIMIT, OVERLAP_LIMIT, RHO_LIMIT,
                               compare_array_to_registry, dot_overlap, surface_rho)

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


def test_a_90_percent_copy_exceeds_the_jaccard_diagnostic_threshold():
    a = _sparse(4, 4000).astype(np.float32)
    b = a.copy()
    ys, xs = np.nonzero(b)
    rng = np.random.default_rng(9)
    k = len(ys) // 10
    b[ys[:k], xs[:k]] = False
    b[rng.integers(0, SHAPE[0], k), rng.integers(0, SHAPE[1], k)] = True
    r = surface_rho(a, b, np.ones(SHAPE, bool))
    # measured: rho_full = 0.8985 (just under the bar), jaccard = 0.8198.
    # Jaccard highlights a near-copy diagnostically; the protocol's rho/forward-overlap
    # thresholds remain the only uniqueness stop rules.
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


def test_jaccard_above_diagnostic_threshold_does_not_add_a_stop_rule(tmp_path):
    candidate = np.zeros(SHAPE, dtype=np.float32)
    prior = np.zeros(SHAPE, dtype=np.float32)
    points = [(10 + 20 * x, 10 + 20 * y) for y in range(10) for x in range(10)]
    for y, x in points:
        candidate[y, x] = 1.0
    for y, x in points[:65]:
        prior[y, x] = 1.0
    for y, x in [(250 + 20 * (i // 5), 20 + 20 * (i % 5)) for i in range(25)]:
        prior[y, x] = 1.0

    path = tmp_path / "prior.tif"
    with rasterio.open(path, "w", driver="GTiff", height=SHAPE[0], width=SHAPE[1],
                       count=1, dtype="float32", crs="EPSG:32611",
                       transform=Affine(100, 0, 0, 0, -100, 40000)) as dst:
        dst.write(prior, 1)
    manifest = {
        "complete_accessible_scan": True,
        "errors": [],
        "rasters": [{"repo_first": "fixture", "sources": ["fixture:prior"],
                      "cache_file": str(path),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}],
    }
    report = compare_array_to_registry(candidate, manifest, np.ones(SHAPE, bool))
    row = report["rows"][0]
    assert row["spearman_full_footprint"] < RHO_LIMIT
    assert row["my_dots_within_3px_of_theirs"] == pytest.approx(0.65)
    assert row["jaccard_dot_sets"] > JACCARD_LIMIT
    assert row["duplicate_by_jaccard"] is True
    assert report["jaccard_diagnostic_only"] is True
    assert report["duplicate_count"] == 0 and report["unique"]


# --- IR-S6-01 dot-representation screen (Session 7 shared-tool fix) --- #

def test_dot_field_representation_is_its_positive_pixels():
    from gems57.uniqueness import dot_representation, representation_class
    a = _sparse(11, 2000).astype(np.float32)
    fp = np.ones(SHAPE, bool)
    assert representation_class(a, fp) == "dot-field"
    repr_dots, kind = dot_representation(a, int((a > 0).sum()), fp)
    assert kind == "dot-field"
    assert int(repr_dots.sum()) == int((a > 0).sum())
    assert np.array_equal(repr_dots, a > 0)


def test_dense_surface_representation_is_budgeted_nms_maxima():
    """A whole-footprint soft surface is a continuous surface: its dots are a
    budgeted non-maximum-suppressed local-maxima set, not every positive cell."""
    from gems57.uniqueness import dot_representation, representation_class
    rng = np.random.default_rng(12)
    a = rng.random(SHAPE).astype(np.float32)  # positive nearly everywhere
    fp = np.ones(SHAPE, bool)
    assert representation_class(a, fp) == "continuous-surface"
    budget = 500
    repr_dots, kind = dot_representation(a, budget, fp)
    assert kind == "continuous-surface"
    assert 1 <= int(repr_dots.sum()) <= budget
    # every representation dot is positive
    assert not (repr_dots & (a <= 0)).any()
    # deterministic
    again, _ = dot_representation(a, budget, fp)
    assert np.array_equal(repr_dots, again)
    # peaks are >= 3 px apart (suppression disk radius 3)
    ys, xs = np.nonzero(repr_dots)
    for i in range(len(ys)):
        for j in range(i + 1, len(ys)):
            assert (ys[i] - ys[j]) ** 2 + (xs[i] - xs[j]) ** 2 > 9 or (ys[i] == ys[j] and xs[i] == xs[j])


def test_dense_surface_representation_prefers_highest_values():
    from gems57.uniqueness import dot_representation
    a = np.zeros(SHAPE, np.float32)
    a[50, 50] = 0.99
    a[50, 250] = 0.98
    a[250, 250] = 0.97
    a += 0.5  # dense positive background
    fp = np.ones(SHAPE, bool)
    repr_dots, _ = dot_representation(a, 3, fp)
    ys, xs = np.nonzero(repr_dots)
    assert (50, 50) in set(zip(ys.tolist(), xs.tolist()))
    assert (50, 250) in set(zip(ys.tolist(), xs.tolist()))
    assert (250, 250) in set(zip(ys.tolist(), xs.tolist()))


def test_literal_screen_still_reports_dense_prior_block_but_repr_screen_does_not(tmp_path):
    """The dual screen: a dense prior fires the literal overlap gate but its
    representation dots give the protocol's own 'raster's dots' reading."""
    from gems57.uniqueness import dot_representation
    candidate = np.zeros(SHAPE, np.float32)
    for y, x in [(30, 30), (30, 300), (300, 30), (300, 300), (150, 150)]:
        candidate[y, x] = 1.0
    prior = np.full(SHAPE, 0.5, np.float32)  # dense continuous surface
    path = tmp_path / "dense.tif"
    with rasterio.open(path, "w", driver="GTiff", height=SHAPE[0], width=SHAPE[1],
                       count=1, dtype="float32", crs="EPSG:32611",
                       transform=Affine(100, 0, 0, 0, -100, 40000)) as dst:
        dst.write(prior, 1)
    manifest = {
        "complete_accessible_scan": True,
        "errors": [],
        "rasters": [{"repo_first": "fixture", "sources": ["fixture:dense"],
                      "cache_file": str(path),
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}],
    }
    report = compare_array_to_registry(candidate, manifest, np.ones(SHAPE, bool))
    row = report["rows"][0]
    # literal: every candidate dot is inside the dense positive support halo
    assert row["my_dots_within_3px_of_theirs"] == pytest.approx(1.0)
    assert row["duplicate_by_overlap"] is True
    assert report["unique"] is False
    assert report["literal_support_screen"]["unique"] is False
    # representation: the dense surface exposes budgeted NMS maxima only
    assert row["their_representation"] == "continuous-surface"
    assert row["their_dots_representation"] <= 5
    assert row["my_dots_within_3px_of_their_dots"] <= 0.70
    assert row["duplicate_by_overlap_dots"] is False
    assert report["unique_under_dot_representation"] is True
    assert report["verdict"] == "promote-to-selector-only"
