#!/usr/bin/env python3
"""Audit the fixed H57-B candidate without writing a raster.

The workflow intentionally performs the two literal registry gates in memory:
continuous surface Spearman before allocation, then final-dot Spearman and
one-way <=3 px overlap. It fails closed on an incomplete/misaligned inventory.
The current H57-B evidence includes a post-hoc matched-mass sensitivity replay,
so this audit never publishes or writes a candidate GeoTIFF; it produces the
single run card and uniqueness receipts only.
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid                                   # noqa: E402
from gems57.anatomy import FEATURES, TIP_FEATURES, fold_geometry  # noqa: E402
from gems57.emit import greedy_allocate                         # noqa: E402
from gems57.fitting import fit_model_from_cells                 # noqa: E402
from gems57.holdout import build_holdout                         # noqa: E402
from gems57.uniqueness import (compare_dots_to_registry,
                               compare_surface_to_registry)       # noqa: E402

EVID = ROOT / "evidence"
INDEX = EVID / "registry_full_index.json"
PRIMARY = EVID / "exp_h57b_holdout.json"
SENSITIVITY = EVID / "exp_h57b_holdout_matched6772.json"
RUN_CARD = EVID / "run_card.json"
BUDGET_PER_CELL = 6_772  # fixed matched-mass sensitivity cap; do not tune
FLOOR = 0.015
CHUNK = 250_000


def _json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def _score_record(run: dict, arm: str) -> dict:
    score = run["pooled_summary"]["scores"][arm]
    return {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": score["evaluator_version"],
        "withheld_positive_count": score["withheld_positive_count"],
        "dti": score["dti"],
        "ci95": score["ci95"],
        "bootstrap": run["pooled_summary"]["bootstrap"],
    }


def _unique_name(decoded_sha: str) -> str:
    base = f"gems57-h57b-tip-distance-{BUDGET_PER_CELL}-{decoded_sha[:12]}"
    name = base
    version = 2
    while any((ROOT / "docs" / "downloads").glob(name + "*")):
        name = f"{base}-v{version}"
        version += 1
    return name


def _surface_summary(report: dict) -> dict:
    return {k: report.get(k) for k in (
        "phase", "verdict", "rho_limit", "n_registry_indexed",
        "n_registry_checked", "n_reprojected_priors", "registry_complete",
        "short_circuited_on_failure", "max_spearman_full_footprint",
        "candidate_surface_array_sha256", "n_rho_firings", "first_rho_firing",
        "errors", "coverage_errors")}


def _dot_summary(report: dict | None) -> dict:
    if report is None:
        return {"verdict": "NOT RUN — surface gate did not pass; allocation was skipped"}
    return {k: report.get(k) for k in (
        "phase", "verdict", "candidate_dots", "rho_limit", "overlap_limit",
        "overlap_radius_px", "n_registry_indexed", "n_registry_checked",
        "n_reprojected_priors", "registry_complete", "short_circuited_on_failure",
        "max_spearman_full_footprint", "max_dot_overlap_fwd_3px",
        "n_rho_firings", "n_overlap_firings", "first_firing",
        "candidate_decoded_array_sha256", "errors", "coverage_errors")}


def main() -> None:
    started = time.time()
    if not INDEX.is_file() or not PRIMARY.is_file() or not SENSITIVITY.is_file():
        raise SystemExit("missing registry index or H57-B holdout evidence; no candidate audit run")
    index = json.loads(INDEX.read_text())
    primary = json.loads(PRIMARY.read_text())
    sensitivity = json.loads(SENSITIVITY.read_text())
    if sensitivity.get("analysis_role") != "posthoc-matched-sensitivity":
        raise SystemExit("matched-mass output is not marked as post-hoc sensitivity; refusing to infer status")

    print("loading grid and fixed H57-B training cells", flush=True)
    grid = load_grid()
    ctx = build_holdout(grid, modes=("all",))
    cells = sorted(ctx.cells_of("all"), key=lambda c: (c.seed, c.fold))
    if len(cells) != 8:
        raise RuntimeError(f"expected 8 fixed whole-branch cells, found {len(cells)}")
    cols = [i for i, name in enumerate(FEATURES) if name != "side"] + [len(FEATURES)]
    clf, scale, base_rate = fit_model_from_cells(
        ctx, cells, seed=0, cols=cols, include_tip=True)
    print(f"final fixed-feature fit ready: {len(cols)} features, scale={scale:.6g}", flush=True)

    domain = grid.footprint & ~grid.catalogue
    full_features = fold_geometry(
        grid, grid.catalogue, np.zeros(grid.shape, bool), domain,
        "full-visible-catalogue", include_tip=True, tip_source=grid.catalogue)
    surface = np.zeros(grid.shape, np.float32)
    for start in range(0, full_features.X.shape[0], CHUNK):
        stop = min(start + CHUNK, full_features.X.shape[0])
        batch = full_features.X[start:stop, cols]
        values = clf.predict_proba(batch)[:, 1].astype(np.float32) * np.float32(scale)
        np.clip(values, 0.0, 1.0, out=values)
        surface[full_features.rows[start:stop], full_features.cols[start:stop]] = values
        del batch, values
    del full_features, clf
    gc.collect()
    surface_sha = hashlib.sha256(surface.astype("<f4", copy=False).tobytes()).hexdigest()
    print(f"full-catalogue surface built: {int(domain.sum()):,} active pixels; sha256(array)={surface_sha}", flush=True)

    print(f"running pre-placement Spearman gate against {index.get('n_unique_grid_rasters')} indexed rasters", flush=True)
    surface_gate = compare_surface_to_registry(surface, INDEX, grid.footprint, stop_on_first=True)
    surface_gate["evidence_class"] = "literal registry uniqueness diagnostic; not a score"
    surface_gate["candidate_surface_array_sha256"] = surface_sha
    (EVID / "uniqueness_h57b_surface.json").write_text(
        json.dumps(surface_gate, indent=2, allow_nan=False) + "\n")

    dot_gate = None
    allocation = None
    if surface_gate["verdict"] == "PASS":
        truth_budget = sum(c.n_truth for c in cells if c.seed == 20)
        allocation = greedy_allocate(
            surface, domain, k_truth=float(truth_budget), floor=FLOOR,
            max_dots=4 * BUDGET_PER_CELL)
        dot_array_sha = hashlib.sha256(
            allocation.emitted.astype("<f4").tobytes()).hexdigest()
        print(f"allocated {allocation.n_dots:,} diagnostic dots in memory (fixed cap {4*BUDGET_PER_CELL:,})", flush=True)
        print("running final-dot literal gate; no reverse-overlap exemption", flush=True)
        dot_gate = compare_dots_to_registry(
            surface, allocation.emitted, INDEX, grid.footprint, stop_on_first=True)
        dot_gate["evidence_class"] = "literal registry uniqueness diagnostic; not a score"
        dot_gate["candidate_decoded_array_sha256"] = dot_array_sha
        (EVID / "uniqueness_h57b_dots.json").write_text(
            json.dumps(dot_gate, indent=2, allow_nan=False) + "\n")
    else:
        dot_array_sha = None
        print(f"pre-placement verdict: {surface_gate['verdict']}; allocation correctly skipped", flush=True)

    name_basis_sha = dot_array_sha or surface_sha
    planned_name = _unique_name(name_basis_sha)
    note = ("Fault-zone anatomy H57-B tip-distance; matched-mass sensitivity only. "
            "HOLD: not cleared, no upload or slot selected.")
    if len(note) > 140:
        raise AssertionError(f"submission note exceeds 140 characters: {len(note)}")

    aucs = sensitivity["canary"]
    max_auc = max((v.get("discriminative_auc_max") or 0.0) for v in aucs.values())
    candidate_sensitivity = _score_record(sensitivity, "h57b_tip_distance")
    control_sensitivity = _score_record(sensitivity, "no_side")
    candidate_primary = _score_record(primary, "h57b_tip_distance")
    control_primary = _score_record(primary, "no_side")
    primary_contrast = primary["pooled_summary"]["paired_differences"]["no_side"]
    sensitivity_contrast = sensitivity["pooled_summary"]["paired_differences"]["no_side"]

    if surface_gate["verdict"] != "PASS":
        verdict = "HOLD — pre-placement registry gate failed or is incomplete; no allocation or raster"
    elif dot_gate is None or dot_gate["verdict"] != "PASS":
        verdict = "HOLD — final-dot literal registry gate failed or is incomplete; no raster"
    else:
        verdict = ("HOLD — uniqueness gates passed, but only the post-hoc matched-mass sensitivity is positive; "
                   "the original preregistered run was non-comparable, so no submission raster is cleared")

    registry_meta = {
        "scope": "public sibling-repository GitHub archive; not an authoritative list of all organizer submissions",
        "owner": index.get("owner"),
        "repos_scanned": len(index.get("repos_scanned", [])),
        "repos_unreachable_or_missing": index.get("repos_unreachable_or_missing", []),
        "n_unique_grid_rasters": index.get("n_unique_grid_rasters"),
        "skipped": index.get("skipped"),
        "index_path": str(INDEX.relative_to(ROOT)),
    }
    card = {
        "record_type": "single GEMS fault-zone-anatomy run card",
        "run_date_local": "2026-10-09",
        "lane": "fault-zone anatomy only",
        "hypothesis": "Withheld whole fault branches are enriched near visible branch termini after cut-induced endpoints within the 3 px collar are filtered.",
        "mechanism": "Append one learned distance-to-filtered-terminal feature to the no_side anatomy baseline; derive terminals and all other catalogue geometry only from visible faults; do not hand-set an angle or lobe width.",
        "named_non_fault_mimic": "Road and dry-wash terminations, map-sheet or digitization breaks, and other non-fault line endings; no independent geology/topography layer was used to disambiguate them.",
        "holdout": {
            "primary_preregistered_run": {
                "candidate": candidate_primary,
                "control_no_side": control_primary,
                "paired_candidate_minus_control": primary_contrast,
                "realized_dot_counts_matched_across_arms": primary.get("mass_matched_across_arms"),
                "verdict": primary.get("holdout_verdict"),
                "interpretation": "The original 10,000-dot cap was not saturated equally; the candidate emitted fewer dots in four of eight cells. The score is HOLDOUT-DTI, but the arm contrast is non-comparable and cannot promote."
            },
            "matched_mass_sensitivity_not_confirmatory": {
                "candidate": candidate_sensitivity,
                "control_no_side": control_sensitivity,
                "paired_candidate_minus_control": sensitivity_contrast,
                "dot_counts_per_cell": {k: sorted(set(v.values())) for k, v in
                                         sensitivity["paired_dot_count_comparison"].items()},
                "cap_per_cell": BUDGET_PER_CELL,
                "numeric_rule_passed": sensitivity.get("numeric_promotion_rule_passed"),
                "promotion_eligible": False,
                "analysis_role": sensitivity.get("analysis_role"),
                "interpretive_limit": sensitivity.get("interpretive_limit"),
                "interpretation": "Favorable sensitivity reading, not confirmatory: the common cap was derived from the first run's candidate counts after the original result was observed. The paired spatial-block CI is conditional on this selected cap."
            },
            "evaluator_version": candidate_sensitivity["evaluator_version"],
            "withheld_positive_count": candidate_sensitivity["withheld_positive_count"],
            "confidence_interval_method": sensitivity["pooled_summary"]["bootstrap"],
            "metric": {"alpha": 0.2, "beta": 0.8, "triangular_kernel_radius_m": 300},
            "feature_canary": {
                "threshold": 0.90,
                "maximum_discriminative_auc": max_auc,
                "per_feature": {name: {
                    "discriminative_auc_mean": item.get("discriminative_auc_mean"),
                    "discriminative_auc_max": item.get("discriminative_auc_max"),
                    "leakage_flag": item.get("leakage_flag")}
                    for name, item in aucs.items()},
                "clean": sensitivity.get("all_features_canary_clean"),
                "full_result_json": "evidence/exp_h57b_holdout_matched6772.json",
            },
        },
        "registry": {
            "inventory": registry_meta,
            "pre_placement_surface": _surface_summary(surface_gate),
            "pre_placement_full_report_json": "evidence/uniqueness_h57b_surface.json",
            "final_dots": _dot_summary(dot_gate),
            "final_dots_full_report_json": ("evidence/uniqueness_h57b_dots.json"
                                             if dot_gate is not None else None),
            "rho_threshold": 0.90,
            "candidate_dot_overlap_threshold": 0.70,
            "dot_overlap_distance_px": 3,
            "reverse_overlap_exemption": False,
            "jaccard_gate": False,
        },
        "artifact": {
            "raster_generated": False,
            "raster_sha256": None,
            "planned_decoded_array_sha256": dot_array_sha,
            "proposed_name_basis_sha256": name_basis_sha,
            "submission_name": planned_name,
            "submission_name_status": "proposed unique label only; no file or slot assigned",
            "submission_note": note,
            "submission_note_characters": len(note),
            "validator_output": "NOT RUN — no candidate GeoTIFF was generated because this evidence is not confirmatory under the original preregistration.",
            "download_status": "NOT CLEARED — no new TIF generated",
            "submission_status": "NOT SUBMITTED — no organizer receipt exists",
            "weekly_slot_selected": False,
        },
        "promote_verdict": verdict,
        "projection_or_leaderboard_claim": "None. HOLDOUT-DTI is a local hide-and-recover measurement, not a live score or leaderboard projection.",
        "sources_and_limitations": {
            "sources": [
                {"source": "DrivenData metric/problem description", "url": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/"},
                {"source": "Schreurs (2003), distributed strike-slip shear zones", "url": "https://doi.org/10.1144/GSL.SP.2003.210.01.03"},
                {"source": "Tchalenko (1970), shear-zone analogues", "url": "https://doi.org/10.1130/0016-7606(1970)81%5B1625%3ASBSZOD%5D2.0.CO%3B2"},
                {"source": "Savage & Brodsky (2011), fault damage zones", "url": "https://doi.org/10.1029/2010JB007665"},
            ],
            "limitations": [
                "Truth is withheld mapped catalogue geometry, not the organizer's unpublished targets; transfer to unmapped faults is unknown.",
                "The H57-B matched-mass sensitivity is post-hoc, despite using unchanged seeds, features, model parameters, and folds; no confirmatory retest was allowed by the experiment budget.",
                "The GitHub sibling-repository archive is not a guaranteed complete list of private or organizer submissions.",
                "No receipt or organizer confirmation exists; no submission slot was selected or used."
            ],
        },
        "runtime_seconds": time.time() - started,
    }
    RUN_CARD.write_text(json.dumps(card, indent=2, default=_json_default, allow_nan=False) + "\n")
    print(f"wrote {RUN_CARD.relative_to(ROOT)}", flush=True)
    print(f"verdict: {verdict}", flush=True)


if __name__ == "__main__":
    main()
