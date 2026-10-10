"""Fail-closed preflight tests; these never fit a model or build a GeoTIFF."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from scripts import build_submission as build
from gems57.anatomy import FEATURES
from gems57.evaluator_provenance import CV_VERSION


def test_missing_clearance_stops_before_any_output(tmp_path):
    with pytest.raises(RuntimeError, match="HOLD: no submission-clearance receipt"):
        build.load_clearance(build.EVID / "__absent_test_clearance__.json")
    assert list(tmp_path.iterdir()) == []


def _registry_manifest(entries):
    return {
        "grid": {"shape": [3730, 3292], "crs": "EPSG:32611"},
        "repos_unreachable_or_missing": [],
        "complete_accessible_scan": True,
        "errors": [],
        "n_unique_grid_rasters": len(entries),
        "rasters": entries,
    }


def test_full_registry_missing_cache_fails_closed(tmp_path, monkeypatch):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    monkeypatch.setattr(build, "EVID", evidence_dir)
    index = evidence_dir / "registry_refreshed.json"
    index.write_text(json.dumps(_registry_manifest([
        {"cache_file": str(tmp_path / "missing.tif"), "sha256": "0" * 64},
    ])))
    with pytest.raises(RuntimeError, match="0/1 files verified"):
        build.load_complete_registry()


def test_full_registry_hash_mismatch_fails_closed(tmp_path, monkeypatch):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    monkeypatch.setattr(build, "EVID", evidence_dir)
    raster = tmp_path / "prior.tif"
    raster.write_bytes(b"not a raster; index identity check must fail first")
    index = evidence_dir / "registry_refreshed.json"
    index.write_text(json.dumps(_registry_manifest([
        {"cache_file": str(raster), "sha256": "0" * 64},
    ])))
    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        build.load_complete_registry()


def test_full_registry_rejects_unaligned_grid_before_fitting(tmp_path, monkeypatch):
    import rasterio
    from rasterio.transform import from_origin

    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    monkeypatch.setattr(build, "EVID", evidence_dir)
    raster = tmp_path / "wrong_grid.tif"
    with rasterio.open(
        raster, "w", driver="GTiff", height=1, width=1, count=1, dtype="float32",
        crs="EPSG:32611", transform=from_origin(0, 100, 100, 100),
    ) as dst:
        dst.write(np.zeros((1, 1), dtype=np.float32), 1)
    sha = hashlib.sha256(raster.read_bytes()).hexdigest()
    index = evidence_dir / "registry_refreshed.json"
    index.write_text(json.dumps(_registry_manifest([
        {"cache_file": str(raster), "sha256": sha},
    ])))
    with pytest.raises(RuntimeError, match="grid mismatch"):
        build.load_complete_registry()


def test_full_registry_rejects_custom_subset_path(tmp_path, monkeypatch):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    monkeypatch.setattr(build, "EVID", evidence_dir)
    with pytest.raises(ValueError, match="custom subsets are forbidden"):
        build.load_complete_registry(tmp_path / "subset.json")


def test_preplacement_preview_is_deterministic_and_budgeted():
    surface = np.arange(30, dtype=np.float32).reshape(5, 6) / 30
    allowed = np.ones(surface.shape, dtype=bool)
    allowed[4, :] = False
    preview = build._topk_preview(surface, allowed, 4)
    assert int(preview.sum()) == 4
    expected = np.argpartition(surface[allowed], -4)[-4:]
    assert set(np.flatnonzero(preview)) == set(np.flatnonzero(allowed)[expected])
    tied = np.ones((5, 6), dtype=np.float32)
    tied_preview = build._topk_preview(tied, allowed, 3)
    assert set(np.flatnonzero(tied_preview)) == {0, 1, 2}
    with pytest.raises(ValueError, match="no allowed pixels"):
        build._topk_preview(surface, np.zeros_like(allowed), 1)
    with pytest.raises(ValueError, match="positive integer"):
        build._topk_preview(surface, allowed, True)


def test_versioned_clearance_requires_matching_evaluator_and_builder_hashes(tmp_path, monkeypatch):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    evidence_path = evidence_dir / "cv_all.json"
    clean_canary = {
        feature: {
            "auc_per_fold": [0.7, 0.7, 0.7, 0.7],
            "discriminative_auc_max": 0.7,
            "leakage_flag": False,
        }
        for feature in FEATURES
    }
    evidence = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": CV_VERSION,
        "evaluator_implementation_sha256": {"cv.py": "cv-hash"},
        "evaluator_input_sha256": {"grid.tif": "grid-hash"},
        "mode": "all",
        "max_dots": 120000,
        "floor": 0.015,
        "withheld_positive_pixels": 12,
        "canary": clean_canary.copy(),
        "variants": {"no_side": {"pooled": {
            "pooled_dti": 0.2,
            "dti_ci95_quadrant_jackknife": [0.1, 0.3],
            "n_truth": 12,
        }}},
    }
    evidence_path.write_text(json.dumps(evidence))
    evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    registry_index = evidence_dir / "registry_refreshed.json"
    registry_index.write_text(json.dumps(_registry_manifest([])))
    registry_sha = hashlib.sha256(registry_index.read_bytes()).hexdigest()
    monkeypatch.setattr(build, "cv_implementation_hashes", lambda: {"cv.py": "cv-hash"})
    monkeypatch.setattr(build, "cv_input_hashes", lambda: {"grid.tif": "grid-hash"})
    monkeypatch.setattr(build, "build_implementation_hashes", lambda: {"build.py": "build-hash"})

    clearance = {
        "schema": build.CLEARANCE_SCHEMA,
        "decision": "CLEAR_FOR_LOCAL_CANDIDATE_BUILD",
        "candidate_id": build.CANDIDATE_ID,
        "evidence_path": "evidence/cv_all.json",
        "evidence_sha256": evidence_sha,
        "evaluator_version": CV_VERSION,
        "evaluator_implementation_sha256": {"cv.py": "cv-hash"},
        "evaluator_input_sha256": {"grid.tif": "grid-hash"},
        "build_implementation_sha256": {"build.py": "build-hash"},
        "registry_index_sha256": registry_sha,
        "mode": "all",
        "variant": "no_side",
        "live_dot_budget": 40,
        "k_truth": 12,
        "floor": 0.015,
        "flank_px": 0,
        "selector_note": "Independent selector rationale for test only.",
        "slot_promotion": False,
    }
    receipt_path = evidence_dir / "submission_clearance.json"
    receipt_path.write_text(json.dumps(clearance))
    monkeypatch.setattr(build, "ROOT", tmp_path)
    monkeypatch.setattr(build, "EVID", evidence_dir)

    parsed, cv, pooled = build.load_clearance(receipt_path)
    assert parsed["holdout_summary"]["evidence_class"] == "HOLDOUT-DTI"
    assert parsed["holdout_summary"]["withheld_positive_pixels"] == 12
    assert pooled["pooled_dti"] == 0.2
    assert cv["evaluator_version"] == CV_VERSION

    evidence["canary"].pop(FEATURES[-1])
    evidence_path.write_text(json.dumps(evidence))
    clearance["evidence_sha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(clearance))
    with pytest.raises(ValueError, match="canary is incomplete"):
        build.load_clearance(receipt_path)

    evidence["canary"] = clean_canary.copy()
    evidence_path.write_text(json.dumps(evidence))
    clearance["evidence_sha256"] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    clearance["live_dot_budget"] = 4 * evidence["max_dots"] + 1
    receipt_path.write_text(json.dumps(clearance))
    with pytest.raises(ValueError, match="four times spatial CV's per-cell"):
        build.load_clearance(receipt_path)

    clearance["live_dot_budget"] = 40
    receipt_path.write_text(json.dumps(clearance))
    registry_index.write_text(json.dumps(_registry_manifest([
        {"cache_file": "missing.tif", "sha256": "0" * 64},
    ])))
    with pytest.raises(ValueError, match="registry-index SHA256"):
        build.load_clearance(receipt_path)


def test_clearance_rejects_slot_promotion(tmp_path, monkeypatch):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    monkeypatch.setattr(build, "EVID", evidence_dir)
    path = evidence_dir / "clearance.json"
    path.write_text(json.dumps({"slot_promotion": True}))
    with pytest.raises(ValueError, match="missing required fields"):
        build.load_clearance(path)
