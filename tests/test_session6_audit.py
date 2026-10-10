"""Session-6 registry audit: synthetic unit tests plus pins on committed evidence.

CI has no .cache/registry (818 MB, gitignored), so the evidence pins read only
committed JSON. The synthetic tests exercise the helper functions directly.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_audit():
    spec = importlib.util.spec_from_file_location("session6_registry_audit", ROOT / "scripts" / "session6_registry_audit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


audit = _load_audit()


def test_profile_counts_finite_positive_cells_inside_footprint_only():
    fp = np.zeros((4, 4), bool)
    fp[:2, :] = True                       # 8 footprint cells
    a = np.zeros((4, 4), np.float32)
    a[0, 1:] = 0.5                         # 3 positive in footprint
    a[3, 0] = 0.9                          # 1 positive OUTSIDE footprint
    a[1, 1] = np.nan                       # non-finite is never a dot
    p = audit.profile_array(a, fp)
    assert p["positive_in_footprint"] == 3
    assert p["positive_outside_footprint"] == 1
    assert p["footprint_fraction_positive"] == pytest.approx(3 / 8)
    assert p["dense"] is False
    assert p["all_finite_values_in_0_1"] is True


def test_dense_flag_triggers_at_half_footprint():
    fp = np.ones((2, 5), bool)             # 10 footprint cells
    a = np.zeros((2, 5), np.float32)
    a[:, :] = 0.3                          # 10 positive
    a[0, 0] = 0.0                          # 9 positive -> 0.9, dense
    assert audit.profile_array(a, fp)["dense"] is True
    a[0, 1] = 0.0                          # 8 positive -> 0.8
    a[0, 2] = 0.0                          # 7 positive
    a[0, 3] = 0.0                          # 6 positive
    a[0, 4] = 0.0                          # 5 positive -> exactly 0.5, dense (>= 0.5)
    assert audit.profile_array(a, fp)["footprint_fraction_positive"] == pytest.approx(0.5)
    assert audit.profile_array(a, fp)["dense"] is True
    a[1, 0] = 0.0                          # 4 positive -> 0.4, not dense
    assert audit.profile_array(a, fp)["dense"] is False


def test_containment_reports_removed_cells_and_catalogue_distance():
    cat = np.zeros((9, 9), bool)
    cat[4, :] = True                       # a mapped trace along row 4
    base = np.zeros((9, 9), bool)
    base[2, 4] = True                      # distance 2 px to the trace
    base[4, 0] = True                      # on the trace (distance 0)
    base[7, 7] = True                      # far from the trace (distance 3)
    target = base.copy()
    target[4, 0] = False                   # removed on the trace
    target[2, 4] = False                   # removed at 2 px
    out = audit.containment(base, target, cat)
    assert out["target_subset_of_base"] is True
    assert out["added_vs_base"] == 0
    assert out["removed_vs_base"] == 2
    assert out["removed_on_catalogue"] == 1
    assert out["removed_distance_px_min"] == pytest.approx(0.0)
    assert out["removed_distance_px_max"] == pytest.approx(2.0)


def test_containment_detects_added_cells():
    cat = np.zeros((3, 3), bool)
    base = np.zeros((3, 3), bool)
    target = np.zeros((3, 3), bool)
    target[1, 1] = True
    assert audit.containment(base, target, cat)["target_subset_of_base"] is False


def test_git_blob_sha1_matches_git_object_format(tmp_path):
    import subprocess
    f = tmp_path / "x.bin"
    f.write_bytes(b"gems57\n")
    expected = subprocess.run(["git", "hash-object", str(f)], capture_output=True, text=True, check=True).stdout.strip()
    assert audit.git_blob_sha1(f) == expected


def test_committed_profile_summary_is_pinned():
    p = json.loads((ROOT / "evidence" / "registry_profile_session6.json").read_text())
    assert p["registry_index"] == "evidence/registry_refreshed_20261010T2001.json"
    s = p["summary"]
    assert s["indexed"] == 696
    assert s["fetched_and_verified"] == 696
    assert s["errors"] == 0
    assert s["sha256_pin_mismatches"] == 0
    assert s["git_blob_sha1_mismatches"] == 0
    assert s["footprint_cells"] == 5167373
    assert s["dense_rasters_ge_50pct_footprint"] == 53


def test_committed_witness_is_universal_blocker_and_mechanism_is_subset():
    m = json.loads((ROOT / "evidence" / "session6_mechanism_and_witness.json").read_text())
    w = m["witness_saturation"]
    assert w["uncovered_allowed_pixels"] == 0
    assert w["universal_overlap_blocker"] is True
    assert w["witness_sha256"] == "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be"
    c = m["owner_reported_pair_containment"]
    assert c["base_positive"] == 40199 and c["target_positive"] == 37654
    assert c["target_subset_of_base"] is True
    assert c["added_vs_base"] == 0 and c["removed_vs_base"] == 2545
    assert c["removed_on_catalogue"] == 0
    assert c["removed_distance_px_min"] >= 1.0 and c["removed_distance_px_max"] <= 2.0 + 1e-9


def test_committed_gate_on_696_index_fails_and_card_stays_unsubmittable():
    g = json.loads((ROOT / "evidence" / "uniqueness_session6_full_registry_696.json").read_text())
    assert g["registry_rasters_checked"] == 696
    assert g["complete_accessible_scan"] is True
    assert g["duplicate_count"] == 80
    assert g["unique"] is False
    assert g["stop_required"] is True
    card = json.loads((ROOT / "evidence" / "run_card_current.json").read_text())
    # The current card describes the Session-7 artifact. Research download is explicitly scoped to research
    # only (IR-S7A-03) and is not a permission to enter the competition; submission stays fail-closed under
    # the fired literal gate, and IR-S6-10 still governs the retained Session-5 file.
    assert card["okay_to_download"] is True
    scope = card["download_permission_status"]
    assert scope["authorized"] is True and scope["scope"] == "research download only"
    assert scope["submission_cleared"] is False and scope["file_availability_is_permission"] is False
    assert card["okay_to_submit"] is False
    assert card["verdict"] == "negative"
    s6 = card["session6_verification"]
    assert s6["literal_gate_on_offered_tif"]["duplicate_count"] == 80
    assert s6["experiments_run"] == 0 and s6["submission_slots_used"] == 0
    ids = {i["id"]: i for i in json.loads((ROOT / "evidence" / "irregularities_current.json").read_text())["irregularities"]}
    assert ids["IR-S6-10"]["status"].startswith("RESOLVED OPERATIONALLY")
    assert "pending explicit owner decision" in ids["IR-S6-10"]["status"].lower()
    assert ids["IR-S6-01"]["status"].startswith("OPEN")
