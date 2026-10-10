"""The checked-in executive site must stay internally sound and HOLD-first."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_site import build_hypotheses  # noqa: E402
from scripts.check_site import inspect_site  # noqa: E402
from scripts.run_orientation_experiments import require_batch_budget  # noqa: E402


def test_published_site_is_fail_closed_and_has_no_broken_links():
    assert inspect_site(ROOT / "docs") == []


def test_orientation_pipeline_refuses_a_spent_three_experiment_batch():
    require_batch_budget(0)
    for used in (1, 3):
        try:
            require_batch_budget(used)
        except RuntimeError as exc:
            assert "experiment budget already spent" in str(exc)
        else:
            raise AssertionError(f"spent batch unexpectedly accepted at {used}/3")
    for invalid in (None, -1, True):
        try:
            require_batch_budget(invalid)
        except RuntimeError as exc:
            assert "missing or invalid" in str(exc)
        else:
            raise AssertionError(f"invalid experiment count unexpectedly accepted: {invalid!r}")


def test_hypothesis_renderer_includes_each_candidate_and_ungraded_upside():
    source = json.loads((ROOT / "evidence" / "hypotheses_current.json").read_text())
    page = build_hypotheses()
    assert "qualitative research prior only" in page
    assert "Relative DTI upside / cost (prior only)" in page
    for candidate in source["candidates"]:
        assert html.escape(candidate["hypothesis"]) in page
        assert html.escape(candidate["physical_signature"]) in page
        assert html.escape(candidate["named_non_fault_mimic"]) in page
        assert html.escape(candidate["relative_expected_dti_upside"]["tier"]) in page
        assert html.escape(candidate["implementation_cost"]) in page
