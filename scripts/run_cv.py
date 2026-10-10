#!/usr/bin/env python3
"""Leakage canary + leave-one-quadrant-out CV for the fault-zone-anatomy lane.

Runs, for one withholding mode:

1. the leakage canary -- single-feature AUC on every fold (no fitting involved,
   so nothing can leak through the fit);
2. leave-one-quadrant-out CV of four nested feature sets, so the value of the
   anisotropic anatomy is measured against a distance-only control;
3. pooled DTI with two CIs (coverage-Wilson and quadrant-jackknife).

All numbers printed are HOLDOUT-DTI instrument readings.  No live score is
projected anywhere in this file.
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

from gems57 import load_grid                                    # noqa: E402
from gems57.anatomy import FEATURES                              # noqa: E402
from gems57.fitting import (canary, cell_geometry, fit_model,    # noqa: E402
                            pooled, run_cell, sample_train)
from gems57.holdout import FOLD_NAMES, build_holdout             # noqa: E402
from gems57.evaluator_provenance import (CV_VERSION, cv_implementation_hashes,
                                         cv_input_hashes)         # noqa: E402

EVID = ROOT / "evidence"
IDX = {n: i for i, n in enumerate(FEATURES)}

VARIANTS = {
    "d_only":        [IDX["d"]],
    "d_perp_par":    [IDX["d"], IDX["d_perp"], IDX["d_par_abs"]],
    "anatomy_full":  list(range(len(FEATURES))),
    "no_side":       [i for i, n in enumerate(FEATURES) if n != "side"],
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["all", "detached"])
    ap.add_argument("--max-dots", type=int, default=120_000)
    ap.add_argument("--floor", type=float, default=0.015)
    ap.add_argument("--canary-only", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    ctx = build_holdout(load_grid())
    cells = ctx.cells_of(a.mode)
    print(f"[{time.time()-t0:5.1f}s] holdout ready: {len(cells)} cells, mode={a.mode}")

    # ---- 1. leakage canary -------------------------------------------------
    geoms_canary = []
    for c in cells[:4]:                      # 4 folds x 1 draw is enough for AUC
        geoms_canary.append(cell_geometry(ctx, c))
    can = canary(geoms_canary)
    print(f"\n[{time.time()-t0:5.1f}s] LEAKAGE CANARY (single-feature AUC, "
          f"{len(geoms_canary)} folds)")
    for name, r in can.items():
        flag = "  <== LEAKAGE FLAG" if r["leakage_flag"] else ""
        print(f"  {name:10s} raw_mean={r['auc_mean']:.4f} "
              f"discriminative_mean={r['discriminative_auc_mean']:.4f} "
              f"discriminative_max={r['discriminative_auc_max']:.4f}{flag}")
    geoms_canary.clear()
    gc.collect()
    provenance = {
        "evaluator_version": CV_VERSION,
        "evaluator_implementation_sha256": cv_implementation_hashes(),
        "evaluator_input_sha256": cv_input_hashes(),
    }
    if a.canary_only:
        EVID.mkdir(exist_ok=True)
        canary_payload = dict(evidence_class="MEASUREMENT", **provenance,
                              mode=a.mode, canary=can)
        (EVID / f"canary_{a.mode}.json").write_text(json.dumps(canary_payload, indent=2))
        print(f"wrote evidence/canary_{a.mode}.json")
        return

    # ---- 2. leave-one-quadrant-out CV --------------------------------------
    out = dict(evidence_class="HOLDOUT-DTI", **provenance, mode=a.mode,
               n_cells=len(cells), max_dots=a.max_dots, floor=a.floor,
               split_protocol="fixed label-blind quadrants; whole intersecting components hidden; "
                              "80 px train/evaluation buffer; visible-only features",
               metric_protocol="pooled DTI alpha=0.2 beta=0.8, 300 m triangular kernel",
               canary=can, variants={})
    for vname, cols in VARIANTS.items():
        t1 = time.time()
        results = []
        for qi, q in enumerate(FOLD_NAMES):
            test = [c for c in cells if c.key.split("_")[1] == f"fold{q}"]
            train = [c for c in cells if c.key.split("_")[1] != f"fold{q}"]
            geoms = []
            for c in train:
                geoms.append(cell_geometry(ctx, c))
            clf, scale, base = fit_model(geoms, seed=qi, cols=cols)
            geoms.clear()
            gc.collect()
            for c in test:
                results.append(run_cell(ctx, c, clf, scale, cols=cols,
                                        max_dots=a.max_dots, floor=a.floor))
            del clf
            gc.collect()
        pl = pooled(results)
        out["variants"][vname] = {"cols": [FEATURES[i] for i in cols],
                                  "pooled": pl, "per_cell": results}
        ci = pl["dti_ci95_quadrant_jackknife"]
        print(f"[{time.time()-t1:5.1f}s] {vname:14s} HOLDOUT-DTI pooled={pl['pooled_dti']:.4f} "
              f"CI95(jackknife)=[{ci[0]:.4f},{ci[1]:.4f}] coverage={pl['coverage']:.4f} "
              f"dots={pl['n_dots']} tp={pl['tp']:.0f} fp={pl['fp']:.0f} K={pl['n_truth']}")

    out["withheld_positive_pixels"] = int(
        out["variants"]["d_only"]["pooled"]["n_truth"])
    EVID.mkdir(exist_ok=True)
    (EVID / f"cv_{a.mode}.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote evidence/cv_{a.mode}.json   total {time.time()-t0:.1f}s")

    base = out["variants"]["d_only"]["pooled"]["pooled_dti"]
    full = out["variants"]["anatomy_full"]["pooled"]["pooled_dti"]
    print(f"\nanatomy gain over distance-only: {full-base:+.4f} DTI "
          f"({100*(full-base)/max(base,1e-9):+.1f}% relative)")


if __name__ == "__main__":
    main()
