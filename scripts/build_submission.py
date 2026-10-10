#!/usr/bin/env python3
"""LEGACY in-sample builder; disabled as a promotion path.

The previous implementation is retained below for audit history only. Do not
use it to write a candidate: it selects configuration on the same holdout cells
it scores and writes the TIFF before the final literal registry gate. Its original
workflow trained on all holdout cells, selected a flank using those same cells,
then wrote and validated a GeoTIFF before uniqueness was known.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import grid as gridmod                                   # noqa: E402
from gems57 import load_grid, write_submission                       # noqa: E402
from gems57.anatomy import FEATURES                                  # noqa: E402
from gems57.emit import expected_credit, greedy_allocate             # noqa: E402
from gems57.fitting import (cell_geometry, fit_model, pooled,  # noqa: E402
                            predict_surface, run_cell)
from gems57.holdout import build_holdout                             # noqa: E402
from gems57.metric import dti_binary                                 # noqa: E402
from gems57.uniqueness import compare_to_registry                    # noqa: E402
from gems57.validate import assert_submittable, validate             # noqa: E402
from gems57 import anatomy                                           # noqa: E402
from scipy import ndimage as ndi                                     # noqa: E402

EVID = ROOT / "evidence"
DL = ROOT / "docs" / "downloads"


def _truth_crop(cell) -> np.ndarray:
    t = np.zeros(cell.active.shape, bool)
    t[cell.truth_yx] = True
    return t


def score_variant(ctx, cells, clf, scale, exclude_flank_px: int, *,
                  max_dots: int, floor: float,
                  cols: list[int] | None = None) -> tuple[dict, list[dict]]:
    """Holdout DTI for one flank-exclusion setting."""
    res = []
    for cell in cells:
        g = cell_geometry(ctx, cell)
        p = predict_surface(clf, scale, g, ctx.grid.shape, cols)
        allowed = np.zeros(ctx.grid.shape, bool)
        allowed[cell.bbox] = cell.active
        if exclude_flank_px > 0:
            d = ndi.distance_transform_edt(~ctx.visible(cell.key))
            allowed &= d > exclude_flank_px
        alloc = greedy_allocate(p, allowed, k_truth=float(cell.n_truth),
                                floor=floor, max_dots=max_dots)
        r = dti_binary(alloc.emitted[cell.bbox], _truth_crop(cell), valid=cell.active)
        res.append({"key": cell.key, "mode": cell.mode, "n_truth": cell.n_truth,
                    "n_dots": alloc.n_dots, **r})
        del p, allowed, alloc, g
        gc.collect()
    return pooled(res), res


def main() -> None:
    raise SystemExit(
        "Disabled: this legacy builder selects and scores in-sample and writes before the literal "
        "registry gate. No raster was generated. Use scripts/audit_h57b_candidate.py for the "
        "current in-memory audit; its HOLD verdict does not clear a download or submission."
    )
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["all", "detached"])
    ap.add_argument("--max-dots", type=int, default=200_000)
    ap.add_argument("--floor", type=float, default=0.015)
    ap.add_argument("--tag", default="")
    ap.add_argument("--drop-side", action="store_true",
                    help="drop the sense-of-slip `side` feature (measured to earn nothing)")
    ap.add_argument("--budget-cap", type=int, default=0,
                    help="hard cap on live dots; 0 = use the holdout-optimal budget")
    a = ap.parse_args()

    cols = None
    if a.drop_side:
        cols = [i for i, n in enumerate(FEATURES) if n != "side"]
        print(f"dropping `side`; using {len(cols)} of {len(FEATURES)} features")
    t0 = time.time()

    g = load_grid()
    ctx = build_holdout(g)
    cells = ctx.cells_of(a.mode)
    print(f"[{time.time()-t0:5.1f}s] holdout ready ({len(cells)} cells, mode={a.mode})")

    geoms = [cell_geometry(ctx, c) for c in cells]
    clf, scale, base = fit_model(geoms, seed=0, cols=cols)
    geoms.clear(); gc.collect()
    print(f"[{time.time()-t0:5.1f}s] trained on all cells; calibration scale={scale:.4f} "
          f"base_rate={base:.6f}")

    # ---- 2. flank-exclusion measured on the holdout ------------------------
    variants = {}
    for flank in (0, 1, 2, 3):
        pl, per = score_variant(ctx, cells, clf, scale, flank,
                                max_dots=a.max_dots, floor=a.floor, cols=cols)
        variants[flank] = {"pooled": pl, "per_cell": per}
        print(f"[{time.time()-t0:5.1f}s] flank<={flank}px excluded: HOLDOUT-DTI "
              f"pooled={pl['pooled_dti']:.4f} coverage={pl['coverage']:.4f} "
              f"dots={pl['n_dots']} (per draw ~{pl['n_dots']//2})")
    best_flank = max(variants, key=lambda k: variants[k]["pooled"]["pooled_dti"])
    print(f"  -> holdout selects flank exclusion = {best_flank} px")

    # budget: one draw covers the whole footprint once, so the live budget is the
    # per-draw dot total of the winning variant
    draw0 = [r for r in variants[best_flank]["per_cell"] if r["key"].startswith("draw20")]
    budget = int(sum(r["n_dots"] for r in draw0))
    print(f"  -> live dot budget from holdout = {budget}")
    if a.budget_cap > 0:
        print(f"  -> capped to --budget-cap = {a.budget_cap}")
        budget = min(budget, a.budget_cap)

    # ---- 2b. holdout DTI *at the capped budget*, so the shipped configuration
    #          has its own measured number rather than the unconstrained optimum
    capped_holdout = None
    if a.budget_cap > 0:
        # the live budget is the per-DRAW total over the 4 quadrant cells, so each cell
        # gets one quarter.  (IR-57-CAP-01: this was budget // 2, which measured the
        # capped holdout at ~2x the shipped density.)
        per_cap = budget // 4
        pl, per = score_variant(ctx, cells, clf, scale, best_flank,
                                max_dots=per_cap, floor=a.floor, cols=cols)
        capped_holdout = pl
        print(f"[{time.time()-t0:5.1f}s] at capped budget {budget}: HOLDOUT-DTI "
              f"pooled={pl['pooled_dti']:.4f} coverage={pl['coverage']:.4f} dots={pl['n_dots']}")

    # ---- 3. final surface from the full catalogue --------------------------
    from gems57.anatomy import fold_geometry
    dom = g.footprint & ~g.catalogue
    geom = fold_geometry(g, g.catalogue, np.zeros(g.shape, bool), dom, "live_full_catalogue")
    surf = clf.predict_proba(geom.X[:, cols] if cols is not None else geom.X
                             )[:, 1].astype(np.float32) * np.float32(scale)
    np.clip(surf, 0.0, 1.0, out=surf)
    p = np.zeros(g.shape, np.float32)
    p[geom.rows, geom.cols] = surf
    allowed = dom.copy()
    if best_flank > 0:
        d = ndi.distance_transform_edt(~g.catalogue)
        allowed &= d > best_flank
    print(f"[{time.time()-t0:5.1f}s] live surface: candidate cells={int(allowed.sum())} "
          f"p_max={float(p.max()):.4f}")

    alloc = greedy_allocate(p, allowed, k_truth=float(sum(r["n_truth"] for r in draw0)),
                            floor=a.floor, max_dots=budget)
    print(f"[{time.time()-t0:5.1f}s] allocated {alloc.n_dots} dots; "
          f"expected covered credit={alloc.expected_covered_credit:.1f}")

    # ---- 4. write ----------------------------------------------------------
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(alloc.emitted.tobytes()).hexdigest()[:12]
    tag = a.tag or f"h57-faultzone-anatomy-{a.mode}-flank{best_flank}"
    name = f"gems57-{tag}-{stamp}-{digest}"
    # <= 140 characters, enforced below
    note = (f"57GEMSDOE fault-zone anatomy | fitted en echelon stepover zone ({a.mode}, "
            f"flank {best_flank}px) | {alloc.n_dots} dots, 0 on-catalogue | "
            f"sha {digest[:8]}")
    if len(note) > 140:
        note = (f"57GEMSDOE fault-zone anatomy | {a.mode} flank{best_flank} | "
                f"{alloc.n_dots} dots 0 on-cat | {digest[:8]}")
    assert len(note) <= 140, f"submission note is {len(note)} chars, limit 140"
    DL.mkdir(parents=True, exist_ok=True)
    values = alloc.emitted.astype(np.float32)
    zpath = DL / f"{name}-zeros.tif"
    npath = DL / f"{name}-nan.tif"
    write_submission(zpath, np.where(dom, values, 0.0), mode="zeros")
    write_submission(npath, np.where(dom, values, np.nan), mode="nan")
    print(f"[{time.time()-t0:5.1f}s] wrote {zpath.name} and {npath.name}")

    # ---- 5. validate + uniqueness ------------------------------------------
    vz = validate(zpath, g.footprint, g.catalogue)
    vn = validate(npath, g.footprint, g.catalogue)
    assert_submittable(vz)
    print(f"[{time.time()-t0:5.1f}s] ZEROS variant: {len(vz['checks'])} checks, "
          f"all_passed={vz['all_checks_passed']}, sha256={vz['sha256'][:16]}")
    print(f"  NaN variant all_passed={vn['all_checks_passed']} "
          f"(NOT submittable: n_nan={vn['n_nan']}) -- diagnostics only")

    uniq = compare_to_registry(zpath, ROOT / "registry" / "registry_index.json", g.footprint)
    print(f"[{time.time()-t0:5.1f}s] uniqueness: {uniq['unique']} | worst rho_full="
          f"{uniq['worst_spearman_full_footprint']:.4f} (limit {uniq['rho_limit']}) | "
          f"worst jaccard={uniq['worst_jaccard_dot_sets']:.4f} "
          f"(limit {uniq['jaccard_limit']}) vs {uniq['worst_jaccard_submission']} | "
          f"worst dot overlap={uniq['worst_dot_overlap']*100:.1f}% "
          f"(limit {uniq['overlap_limit']*100:.0f}%) vs {uniq['worst_overlap_submission']}")
    if not uniq["unique"]:
        print("REFUSING TO PROMOTE: the parallel-run protocol declares this a duplicate.")

    audit = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "lane": "fault-zone anatomy / secondary strands around known faults",
        "withholding_mode": a.mode,
        "features": [FEATURES[i] for i in cols] if cols is not None else list(FEATURES),
        "features_dropped": [n for n in FEATURES if cols is None or FEATURES.index(n) not in cols],
        "budget_cap": a.budget_cap,
        # IR-57-INSAMPLE-01: the classifier is trained on the same holdout cells it is scored
        # on, so every holdout number in this file is IN-SAMPLE. Do not quote it as HOLDOUT-DTI.
        # The leave-one-quadrant-out reading is evidence/exp_sense_loqo_all.json (variant no_side).
        "holdout_is_in_sample": True,
        "holdout_at_capped_budget": capped_holdout,
        "calibration": {"scale": scale, "base_rate": base},
        "flank_variants": {str(k): v["pooled"] for k, v in variants.items()},
        "selected_flank_px": best_flank,
        "flank_best_holdout": variants[best_flank]["pooled"],
        "holdout_dot_budget": int(sum(r["n_dots"] for r in draw0)),
        "live_dot_budget": budget,
        "emitted_pixels": int(alloc.n_dots),
        "submission_name": name,
        "submission_note": note,
        "submission_note_len": len(note),
        "zeros_tif": vz,
        "nan_tif": vn,
        "uniqueness": uniq,
        "promote": bool(uniq["unique"] and vz["all_checks_passed"]),
        "runtime_s": time.time() - t0,
    }
    EVID.mkdir(exist_ok=True)
    (EVID / f"submission_build_{a.mode}.json").write_text(json.dumps(audit, indent=2))
    (DL / f"checks-{name}-zeros.tif.json").write_text(json.dumps(vz, indent=2))
    print(f"  submission note ({len(note)} chars): {note}")
    print(f"\nwrote evidence/submission_build_{a.mode}.json")
    print(f"SUBMISSION FILE: docs/downloads/{name}-zeros.tif")


if __name__ == "__main__":
    main()
