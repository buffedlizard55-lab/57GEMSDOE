import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def test_disputed_owner_values_are_not_exact_file_scores():
    audit = load("evidence/owner_score_reconciliation_session4.json")
    assert audit["findings"]["H33-2-B2"]["owner_status"] == "UNSCORED"
    assert audit["findings"]["H33-2-B2"]["projected_live_value"] == 0.2747
    assert audit["findings"]["H33-2-B2"]["projected_live_value_class"] == "PROJECTION; NOT A SCORE"
    assert audit["findings"]["0.2778"]["classification"] == "OWNER-REPORTED / UNVERIFIED"
    assert audit["findings"]["0.2778"]["exact_file_attribution"] is None
    assert audit["findings"]["0.2708"]["attribution_to_H27_4_r1_solo_d2_8"] is False
    assert audit["descriptive_owner_value_analysis"]["included_records"] == 13


def test_registry_budget_generator_rows_only_matches_corrected_receipt():
    proc = subprocess.run(
        [sys.executable, "scripts/registry_budget.py", "--rows-only"], cwd=ROOT,
        text=True, capture_output=True, check=False, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert "-0.7686" in proc.stdout
    assert "over 13 eligible rasters; excluded 2" in proc.stdout
    assert "no evidence written" in proc.stdout


def test_registry_budget_excludes_both_disputed_mappings():
    budget = load("evidence/registry_budget.json")
    assert budget["n_rasters"] == 13
    assert budget["spearman_dots_vs_owner_reported_value"] == -0.7686
    assert len(budget["excluded_score_file_mappings"]) == 2
    assert "not organizer-confirmed" in budget["evidence_class"].lower()
    assert all("owner_reported_value" in row for row in budget["rows"])
    assert all("live_score" not in row for row in budget["rows"])


def test_site_owner_report_parser_keeps_disputed_claims_unattached_to_bytes():
    sys.path.insert(0, str(ROOT))
    from scripts.build_site import owner_reports

    reports = owner_reports(
        "https://buffedlizard55-lab.github.io/GEMSDOE32/\n"
        "h33-h33-2-b2-zeros.tif: 0.2778\n"
        "https://buffedlizard55-lab.github.io/GEMSDOE28/\n"
        "h27-4-r1-solo-d2-8.tif: 0.2708\n"
    )
    h33 = next(r for r in reports if "h33-h33-2-b2" in r["reported_filename"])
    h27 = next(r for r in reports if "h27-4-r1-solo-d2-8" in r["reported_filename"])
    assert "owner_reported_dti" not in h33 and h33["owner_reported_claim"] == 0.2778
    assert "UNSCORED" in h33["attribution_status"]
    assert "owner_reported_dti" not in h27 and h27["owner_reported_claim"] == 0.2708
    assert "CONTRADICTED" in h27["attribution_status"]


def test_registry_index_marks_disputed_claims_as_ineligible():
    rows = load("registry/registry_index.json")
    h33 = next(r for r in rows if r["repo"] == "GEMSDOE32" and "h33-h33-2-b2" in r["submission"])
    h27 = next(r for r in rows if r["repo"] == "GEMSDOE28" and "h27-4-r1-solo-d2-8" in r["submission"])
    assert "owner_reported_score" not in h33 and h33["owner_reported_claim"] == 0.2778
    assert "UNSCORED" in h33["score_provenance"]
    assert h33["eligible_for_descriptive_owner_value_analysis"] is False
    assert "owner_reported_score" not in h27 and h27["owner_reported_claim"] == 0.2708
    assert "contradicted" in h27["score_provenance"].lower()
    assert h27["eligible_for_descriptive_owner_value_analysis"] is False


def test_archived_h57k_emitter_and_model_comparison_fail_closed():
    before = set((ROOT / "docs" / "downloads").glob("gems57-h57k-damagezone-strandexpr-*-zeros.tif"))
    for script, guard in (
        ("scripts/emit_h57k.py", "STOP: archived H57-K emitter disabled"),
        ("scripts/model_compare.py", "STOP: archived H57-K model comparison disabled"),
    ):
        proc = subprocess.run(
            [sys.executable, script], cwd=ROOT,
            text=True, capture_output=True, check=False, timeout=30,
        )
        assert proc.returncode != 0
        assert guard in proc.stderr + proc.stdout
    after = set((ROOT / "docs" / "downloads").glob("gems57-h57k-damagezone-strandexpr-*-zeros.tif"))
    assert after == before
