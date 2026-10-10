#!/usr/bin/env python3
"""Buffered whole-branch LOQO test of the H57-B terminal-proximity hypothesis.

This is one preregistered experiment with three matched arms: distance-only,
the lane's current no-side anatomy baseline, and that same baseline plus one
new terminal-distance feature.  Every cell is scored by the shared evaluator.
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid                                             # noqa: E402
from gems57.anatomy import FEATURES, TIP_FEATURES                         # noqa: E402
from gems57.evaluate_holdout import pooled_summary, VERSION               # noqa: E402
from gems57.fitting import (canary, cell_geometry, fit_model_from_cells,
                            run_cell)                                      # noqa: E402
from gems57.holdout import FOLD_NAMES, build_holdout                      # noqa: E402

EVID = ROOT / "evidence"
BASE_NO_SIDE = [i for i, name in enumerate(FEATURES) if name != "side"]
TIP_INDEX = len(FEATURES)
VARIANTS = {
    "d_only": [FEATURES.index("d")],
    "no_side": BASE_NO_SIDE,
    "h57b_tip_distance": BASE_NO_SIDE + [TIP_INDEX],
}


def _json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["all", "detached"])
    ap.add_argument("--max-dots", type=int, default=10_000,
                    help="per test cell cap; one holdout realization is capped at 4x this value")
    ap.add_argument("--floor", type=float, default=0.015)
    ap.add_argument("--canary-only", action="store_true")
    ap.add_argument("--bootstrap-draws", type=int, default=2_000)
    ap.add_argument("--out", type=Path, default=EVID / "exp_h57b_holdout.json")
    ap.add_argument("--analysis-role", choices=("preregistered-primary", "posthoc-matched-sensitivity"),
                    default="preregistered-primary")
    a = ap.parse_args()
    if a.max_dots <= 0:
        raise SystemExit("--max-dots must be positive")
    expected_cap = 10_000 if a.analysis_role == "preregistered-primary" else 6_772
    if a.max_dots != expected_cap:
        raise SystemExit(f"{a.analysis_role} requires the fixed --max-dots {expected_cap}; no cap sweep is allowed")

    started = time.time()
    ctx = build_holdout(load_grid(), modes=(a.mode,))
    cells = sorted(ctx.cells_of(a.mode), key=lambda c: (c.seed, c.fold))
    if len(cells) != 8:
        raise RuntimeError(f"expected four quadrants x two draws, got {len(cells)} cells")
    by_key = {c.key: c for c in cells}
    print(f"[{time.time()-started:6.1f}s] buffered whole-branch holdout ready: "
          f"{len(cells)} cells, mode={a.mode}, evaluator={VERSION}", flush=True)

    # Streaming canary: no full-grid feature matrices are retained across folds.
    def canary_geometries():
        for cell in cells:
            yield cell_geometry(ctx, cell, include_tip=True, training=False)

    can = canary(canary_geometries())
    print(f"[{time.time()-started:6.1f}s] single-feature leakage canary", flush=True)
    for name, result in can.items():
        flag = " LEAKAGE FLAG" if result["leakage_flag"] else ""
        print(f"  {name:14s} disc-AUC mean={result['discriminative_auc_mean']:.4f} "
              f"max={result['discriminative_auc_max']:.4f}{flag}", flush=True)
    if a.canary_only:
        EVID.mkdir(exist_ok=True)
        (EVID / f"canary_{a.mode}_buffered.json").write_text(
            json.dumps({"evidence_class": "HOLDOUT-DTI", "evaluator_version": VERSION,
                        "canary": can}, indent=2) + "\n")
        return

    out = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": VERSION,
        "experiment_id": "H57-B-terminal-distance",
        "analysis_role": a.analysis_role,
        "plan_status": ("pre-registered before any H57-B outcome" if a.analysis_role == "preregistered-primary"
                        else "post-hoc matched-mass sensitivity plan written before this replay; not confirmatory"),
        "hypothesis": "Withheld fault branches are enriched near the termini of visible fault branches, after a 3 px holdout collar removes cut-induced endpoints.",
        "mechanism": "A single distance-to-visible-branch-terminal feature, appended to the existing no-side anatomy features; no angle or lobe width is hand-set.",
        "named_non_fault_mimic": "Road and dry-wash terminations, plus map-sheet or digitization breaks, can imitate mapped-fault endpoints; this catalogue-only experiment cannot distinguish those mimics without independent geology or topography.",
        "withholding": {"mode": a.mode, "whole_between_junction_branches": True,
                        "artificial_chunking": False, "draw_seeds": sorted({c.seed for c in cells}),
                        "quadrants": list(FOLD_NAMES), "domain_erosion_px": 12,
                        "feature_and_training_negative_buffer_px": 3,
                        "visible_fault_score_mask": "pixel-exact",
                        "test_region_near_truth": "retained and scored; not removed by the feature collar"},
        "allocation": {"method": "shared greedy DTI max-coverage", "per_cell_cap": a.max_dots,
                       "floor": a.floor, "alpha": 0.2, "beta": 0.8,
                       "triangular_radius_m": 300},
        "canary": can,
        "variants": {},
        "runtime_started_epoch_s": started,
    }

    n_blocks = ((ctx.grid.height + 199) // 200) * ((ctx.grid.width + 199) // 200)
    terms_by_arm = {}
    all_counts = {name: {} for name in VARIANTS}

    # A separate model per draw/fold prevents one randomized holdout replicate
    # from leaking into another replicate's training labels/features.
    for arm, cols in VARIANTS.items():
        t_arm = time.time()
        arm_rows = []
        arm_terms = np.zeros((n_blocks, 4), np.float64)
        for seed in sorted({c.seed for c in cells}):
            for fold, qname in enumerate(FOLD_NAMES):
                test = by_key[f"draw{seed}_fold{qname}_{a.mode}"]
                train = [c for c in cells if c.seed == seed and c.fold != fold]
                exclusions = {c.key: (test.key,) for c in train}
                clf, scale, base_rate = fit_model_from_cells(
                    ctx, train, seed=(5_200 + 100 * seed + fold), cols=cols,
                    include_tip=True, feature_excludes=exclusions)
                gc.collect()

                test_geom = cell_geometry(ctx, test, training=False, include_tip=True)
                row = run_cell(ctx, test, clf, scale, max_dots=a.max_dots,
                               floor=a.floor, cols=cols, g=test_geom)
                row["base_rate"] = float(base_rate)
                arm_terms += row.pop("spatial_terms")
                all_counts[arm][test.key] = int(row["n_dots"])
                arm_rows.append(row)
                del test_geom, clf, row
                gc.collect()
        terms_by_arm[arm] = arm_terms
        out["variants"][arm] = {"features": [FEATURES[i] for i in cols if i < len(FEATURES)]
                                       + ([TIP_FEATURES[0]] if TIP_INDEX in cols else []),
                                 "per_cell": arm_rows,
                                 "dot_counts_by_cell": all_counts[arm]}
        print(f"[{time.time()-t_arm:6.1f}s] completed {arm}: "
              f"dots={sum(all_counts[arm].values())}", flush=True)

    summary = pooled_summary(terms_by_arm, draws=a.bootstrap_draws,
                             candidate="h57b_tip_distance")
    out["pooled_summary"] = summary
    out["mass_matched_across_arms"] = all(
        len({all_counts[arm][key] for arm in VARIANTS}) == 1
        for key in all_counts["no_side"])
    out["all_features_canary_clean"] = not any(r["leakage_flag"] for r in can.values())
    contrast = summary["paired_differences"].get("no_side", {})
    ci = contrast.get("ci95", [None, None])
    numeric_gate = bool(
        out["mass_matched_across_arms"] and out["all_features_canary_clean"]
        and ci[0] is not None and ci[0] > 0.0)
    out["numeric_promotion_rule_passed"] = numeric_gate
    out["promotion_eligible_by_holdout_only"] = bool(
        numeric_gate and a.analysis_role == "preregistered-primary")
    if a.analysis_role == "posthoc-matched-sensitivity":
        out["holdout_verdict"] = ("POST-HOC SENSITIVITY ONLY — numeric rule passes; not confirmatory and not promotion-eligible"
                                  if numeric_gate else
                                  "POST-HOC SENSITIVITY NEGATIVE / HOLD")
    else:
        out["holdout_verdict"] = ("PROMOTE-ELIGIBLE FOR SEPARATE GATES ONLY"
                                  if numeric_gate else
                                  "NEGATIVE / HOLD — does not pass preregistered canary, matched-mass and paired-CI rule")
    out["paired_dot_count_comparison"] = all_counts
    out["runtime_s"] = time.time() - started

    EVID.mkdir(exist_ok=True)
    path = a.out if a.out.is_absolute() else ROOT / a.out
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, default=_json_default) + "\n")
    for arm, result in summary["scores"].items():
        ci = result["ci95"]
        print(f"{arm:20s} HOLDOUT-DTI={result['dti']:.5f} "
              f"95% CI=[{ci[0]:.5f},{ci[1]:.5f}] "
              f"withheld={result['withheld_positive_count']:,}", flush=True)
    print(f"paired tip - no_side: {contrast.get('delta')} "
          f"95% CI={contrast.get('ci95')} | matched mass={out['mass_matched_across_arms']} "
          f"canary clean={out['all_features_canary_clean']}", flush=True)
    print(f"verdict: {out['holdout_verdict']} | wrote {path.relative_to(ROOT)} "
          f"| runtime={out['runtime_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
