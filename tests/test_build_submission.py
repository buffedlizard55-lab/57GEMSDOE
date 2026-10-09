"""Small integrity tests for the fail-closed submission build helpers."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import build_submission


def test_runtime_registry_index_includes_existing_candidate_downloads():
    index = build_submission.runtime_registry_index()
    try:
        rows = json.loads(index.read_text())
        assert len(rows) >= 19  # 18 pinned/archive priors + current top-level TIFF
        assert all(Path(row["file"]).is_absolute() for row in rows)
        assert all(Path(row["file"]).exists() for row in rows)
        assert any(row["repo"] == "57GEMSDOE-local-downloads" for row in rows)
    finally:
        index.unlink(missing_ok=True)


def test_runtime_registry_index_can_exclude_audited_candidate():
    candidates = sorted((ROOT / "docs" / "downloads").glob("*.tif"))
    assert candidates
    candidate = candidates[-1].resolve()
    index = build_submission.runtime_registry_index(exclude=candidate)
    try:
        rows = json.loads(index.read_text())
        paths = {Path(row["file"]).resolve() for row in rows}
        assert candidate not in paths
        assert all(path.exists() for path in paths)
    finally:
        index.unlink(missing_ok=True)


def test_runtime_registry_index_skips_nan_diagnostic_variants(tmp_path, monkeypatch):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    candidate = downloads / "candidate-zeros.tif"
    diagnostic = downloads / "candidate-nan.tif"
    candidate.write_bytes(b"candidate placeholder")
    diagnostic.write_bytes(b"diagnostic placeholder")
    monkeypatch.setattr(build_submission, "DL", downloads)

    index = build_submission.runtime_registry_index()
    try:
        rows = json.loads(index.read_text())
        paths = {Path(row["file"]).resolve() for row in rows}
        assert candidate.resolve() in paths
        assert diagnostic.resolve() not in paths
    finally:
        index.unlink(missing_ok=True)


def test_saved_oof_baseline_reports_canary_and_budget_stops():
    result = build_submission.load_oof_baseline("all", "no_side")
    assert result["available"]
    assert result["evidence_class"] == "HOLDOUT-DTI"
    assert result["withheld_positive_pixels"] == 22641
    assert set(result["leakage_canary_flags"]) == {"d", "d_perp"}
    assert result["dots_per_full_map_approx"] > 40000
    assert result["promotion_eligible"] is False
