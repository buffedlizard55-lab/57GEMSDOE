"""Regression coverage for literal uniqueness gates and the HOLD-first site."""
from pathlib import Path
import hashlib
import importlib.util
import json

import numpy as np
import pytest
import rasterio
from affine import Affine

from gems57 import gates
from gems57.uniqueness import compare_array_to_registry

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(tmp_path, value=0.001):
    path = tmp_path / "dense.tif"
    transform = Affine(100, 0, 0, 0, -100, 2000)
    with rasterio.open(path, "w", driver="GTiff", height=20, width=20, count=1,
                       dtype="float32", crs="EPSG:32611", transform=transform) as dst:
        dst.write(np.full((20, 20), value, np.float32), 1)
    manifest = dict(
        rasters=[dict(repo_first="fixture", sources=["fixture:dense"],
                      cache_file=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())],
        complete_accessible_scan=True, errors=[], n_unique_grid_rasters=1,
    )
    candidate = np.zeros((20, 20), np.float32)
    candidate[10, 10] = 1
    return path, manifest, candidate, np.ones((20, 20), bool)


@pytest.mark.parametrize("phase", ["surface", "dots"])
def test_literal_forward_overlap_is_checked_at_both_phases(tmp_path, phase):
    prior, manifest, candidate, footprint = fixture(tmp_path)
    report = gates.lane_report(candidate, footprint, sample=prior,
                               registry_index=manifest, phase=phase)
    assert report["worst_dot_overlap"] == 1
    assert not report["ok"] and report["duplicate"]
    assert report["policy_exemptions"] == []


def test_saturation_exception_and_partial_old_gate_cannot_clear(tmp_path):
    prior, manifest, candidate, footprint = fixture(tmp_path)
    with pytest.raises(ValueError, match="not authorized"):
        gates.lane_report(candidate, footprint, sample=prior,
                          registry_index=manifest, probe_coverage=0.95)
    with pytest.raises(RuntimeError, match="inventory manifest"):
        gates.lane_report(candidate, footprint, [prior], sample=prior)
    with pytest.raises(RuntimeError, match="retired"):
        gates.uniqueness_report(candidate, [prior], top=1)


def test_bare_registry_list_is_unattested_even_when_files_exist(tmp_path):
    prior, _manifest, candidate, footprint = fixture(tmp_path)
    report = compare_array_to_registry(
        candidate, [dict(file=str(prior), submission="fixture")], footprint)
    assert not report["complete_accessible_scan"] and not report["unique"]
    assert report["source_errors"]


def test_constant_candidate_has_no_rank_evidence(tmp_path):
    prior, manifest, candidate, footprint = fixture(tmp_path)
    report = compare_array_to_registry(np.full_like(candidate, 0.001), manifest, footprint)
    assert not report["candidate_rank_variation"] and not report["unique"]
    assert report["stop_required"]


def test_registry_gate_rejects_fixture_transform_mismatch(tmp_path):
    prior, manifest, candidate, footprint = fixture(tmp_path)
    wrong = tmp_path / "wrong.tif"
    with rasterio.open(wrong, "w", driver="GTiff", height=20, width=20, count=1,
                       dtype="float32", crs="EPSG:32611",
                       transform=Affine(100, 0, 100, 0, -100, 2000)) as dst:
        dst.write(np.full_like(candidate, 0.001), 1)
    manifest["rasters"][0].update(
        cache_file=str(wrong), sha256=hashlib.sha256(wrong.read_bytes()).hexdigest())
    report = gates.lane_report(candidate, footprint, sample=prior,
                               registry_index=manifest, phase="surface")
    assert report["missing_or_invalid"] == 1 and not report["ok"]


def test_site_cards_and_pages_are_fail_closed():
    result = script("check_site").check()
    assert result["links_pass"] and result["active_download_links"] == 0
    assert result["current_card_consistent"] and result["current_irregularities_consistent"]
    assert result["public_receipts_withdrawn"] and result["session4_withdrawn"]
    assert not result["submission_cleared"]
    assert result["current_status"] == "HOLD — NOT OK TO DOWNLOAD OR SUBMIT"


def test_feed_parser_accepts_only_a_real_sorted_table():
    parse = script("refresh_feed").parse_leaderboard
    html = ('<table><tr><th>Rank</th><th>Team</th><th>Participant</th><th>Score</th></tr>'
            '<tr><td>#1</td><td></td><td>first</td><td>0.3774</td></tr>'
            '<tr><td>#2</td><td></td><td>second</td><td>0.3361</td></tr></table>')
    rows = parse(html)
    assert rows[0] == dict(rank=1, participant_display="first", public_dti=0.3774)
    with pytest.raises(ValueError):
        parse("<html>Login required</html>")
    with pytest.raises(ValueError):
        parse(html.replace("0.3361", "0.4774"))
    with pytest.raises(ValueError):
        parse(html.replace("0.3774", "2.0000"))


def test_reported_live_score_remains_unconfirmed():
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    report = card["reported_live_score"]
    assert report["value"] == 0.2778
    assert report["classification"].startswith("OWNER-REPORTED")
    assert report["conflicting_reported_highs"] == [0.3195, 0.3774]
    assert report["conflicts_verified"] is False
    assert card["okay_to_download"] is False and card["okay_to_submit"] is False


def test_historical_lean_offset_matches_receipt_but_remains_blocked():
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    audit = card["historical_artifact_review"]
    receipt = json.loads((ROOT / "evidence" / "submission_build_all.json").read_text())["packaging_receipt"]
    tif = ROOT / audit["file"]
    archive = ROOT / audit["zip_file"]
    assert receipt["sha256"] == audit["sha256"]
    assert receipt["bytes"] == audit["bytes"]
    assert receipt["zip_sha256"] == audit["zip_sha256"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == audit["sha256"]
    assert tif.stat().st_size == audit["bytes"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == audit["zip_sha256"]
    import zipfile
    with zipfile.ZipFile(archive) as zf:
        assert zf.namelist() == [tif.name]
        assert zf.read(tif.name) == tif.read_bytes()
    with rasterio.open(tif) as ds:
        assert ds.count == 1 and ds.dtypes == ("float32",)
        assert ds.crs.to_epsg() == 32611 and ds.shape == (3730, 3292)
        values = ds.read(1)
        assert np.isfinite(values).all() and values.min() >= 0 and values.max() <= 1
        assert int((values > 0).sum()) == 40000
    assert audit["okay_to_download"] is False and audit["okay_to_submit"] is False
    assert card["okay_to_download"] is False and card["okay_to_submit"] is False
    assert "not organizer-complete" in card["registry_scope"].lower()
    witness = card["registry_comparison"]["independent_witness_blocker"]
    assert witness["universal_overlap_blocker"] is True
    assert witness["uncovered_allowable_cells"] == 0


def test_hypothesis_shortlist_is_untried_and_evidence_linked():
    hypotheses = json.loads((ROOT / "evidence" / "hypotheses_current.json").read_text())
    rows = hypotheses["candidates"]
    assert 3 <= len(rows) <= 5
    assert [row["rank"] for row in rows] == list(range(1, len(rows) + 1))
    for row in rows:
        assert row["named_non_fault_mimic"]
        assert row["sources"]
        assert row["future_test_gate"]
    assert "budget spent" in hypotheses["status"].lower()
    assert "unsatisfiable" in hypotheses["current_blocker"].lower()


def test_all_published_legacy_pages_are_hold_first():
    for name in ("archive.html", "h57k.html", "session-3.html", "session-4.html"):
        text = (ROOT / "docs" / name).read_text()
        assert "HOLD — NOT OK TO DOWNLOAD OR SUBMIT" in text
        assert 'href="downloads/' not in text and "download=" not in text
    archive = (ROOT / "docs" / "archive.html").read_text()
    assert "gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif" in archive
    session4 = (ROOT / "docs" / "session-4.html").read_text()
    assert "DO NOT SUBMIT" in session4


def test_public_historical_receipts_are_withdrawn_and_originals_preserved():
    receipts = (
        ROOT / "docs/downloads/gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.json",
        ROOT / "docs/downloads/checks-gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif.json",
        ROOT / "docs/downloads/archive/run_card.json",
    )
    for path in receipts:
        record = json.loads(path.read_text())
        assert record["current_audit_status"] == "HOLD — NOT OK TO DOWNLOAD OR SUBMIT"
        assert record["current_submission_status"].startswith("NOT OK")
        assert record["current_download_status"].startswith("NOT OK")
        assert not record.get("status", "").startswith("OK TO DOWNLOAD")
        assert record.get("verdict") != "promote"
        archived = ROOT / record.get("archived_original_receipt", record.get("archived_original_card"))
        assert archived.is_file()


def test_owner_report_table_never_promotes_reported_scores_to_confirmed():
    rows = json.loads((ROOT / "docs/data/owner_reports.json").read_text())
    score = next(row for row in rows if row.get("owner_reported_dti") == 0.2778)
    assert score["evidence_class"].startswith("OWNER-REPORTED")
    assert score["submission_receipt"] is None
    assert all(row.get("submission_receipt") is None for row in rows)


def test_preview_asset_has_a_real_png_signature():
    preview = (ROOT / "docs/assets/preview.png").read_bytes()
    assert preview.startswith(b"\x89PNG\r\n\x1a\n")
