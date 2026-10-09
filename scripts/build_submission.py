#!/usr/bin/env python3
"""Build, validate and uniqueness-check the lane's submission GeoTIFF.

Steps
-----
1. Train the fault-zone-anatomy intensity on all holdout cells of the chosen
   withholding mode.
2. Measure two emission variants on the holdout -- with and without a hard
   exclusion of the immediate catalogue flank -- and pick by measurement, not by
   hand.
3. Rebuild the surface from the *full* catalogue and allocate dots at the
   holdout-optimal budget.
4. Write the portal-legal GeoTIFF (zeros mode) plus a diagnostic NaN variant.
5. Validate against every portal check and against every registry raster.
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
from gems57.submission_writer import write_submission as package_submission  # noqa: E402
from gems57.uniqueness import compare_to_registry                    # noqa: E402
from gems57.validate import assert_submittable, validate             # noqa: E402
from gems57 import anatomy                                           # noqa: E402
from scipy import ndimage as ndi                                     # noqa: E402

try:
    from gems57.geo import GEO_FEATURES, load_planes                 # noqa: E402
except Exception:  # geo stack absent: pure-geometry build still works
    GEO_FEATURES, load_planes = (), None

EVID = ROOT / "evidence"
DL = ROOT / "docs" / "downloads"

# named feature presets, resolved against the combined feature order
PRESETS = {
    "anatomy_full": lambda: list(FEATURES),
    "no_side": lambda: [n for n in FEATURES if n != "side"],
    "geo_only": lambda: list(GEO_FEATURES),
    "no_side_plus_geo": lambda: [n for n in FEATURES if n != "side"] + list(GEO_FEATURES),
    "anatomy_plus_geo": lambda: list(FEATURES) + list(GEO_FEATURES),
}


def _truth_crop(cell) -> np.ndarray:
    t = np.zeros(cell.active.shape, bool)
    t[cell.truth_yx] = True
    return t


def score_variant(ctx, cells, clf, scale, exclude_flank_px: int, *,
                  max_dots: int, floor: float,
                  cols: list[int] | None = None,
                  geo: dict | None = None) -> tuple[dict, list[dict]]:
    """Holdout DTI for one flank-exclusion setting."""
    res = []
    for cell in cells:
        g = cell_geometry(ctx, cell, geo=geo)
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["all", "detached"])
    ap.add_argument("--max-dots", type=int, default=200_000)
    ap.add_argument("--floor", type=float, default=0.015)
    ap.add_argument("--tag", default="")
    ap.add_argument("--drop-side", action="store_true",
                    help="drop the sense-of-slip `side` feature (measured to earn nothing)")
    ap.add_argument("--features", default="",
                    help="preset (no_side, no_side_plus_geo, anatomy_full, geo_only, "
                         "anatomy_plus_geo) or comma-separated feature names")
    ap.add_argument("--budget-cap", type=int, default=0,
                    help="hard cap on live dots; 0 = use the holdout-optimal budget")
    ap.add_argument("--flank", type=int, default=-1,
                    help="skip the flank sweep and use this exclusion (px); -1 = sweep")
    a = ap.parse_args()

    t0 = time.time()
    g = load_grid()
    geo = None
    if load_planes is not None:
        geo = load_planes(g.footprint)
        print(f"[{time.time()-t0:5.1f}s] geo planes loaded: {list(geo)}")
    all_names = tuple(FEATURES) + (tuple(geo) if geo else ())
    name_idx = {n: i for i, n in enumerate(all_names)}

    if a.features:
        if a.features in PRESETS:
            want = PRESETS[a.features]()
        else:
            want = [w.strip() for w in a.features.split(",") if w.strip()]
        unknown = [w for w in want if w not in name_idx]
        if unknown:
            raise SystemExit(f"unknown features {unknown}; available: {list(all_names)}")
        cols = [name_idx[w] for w in want]
    elif a.drop_side:
        cols = [i for i, n in enumerate(FEATURES) if n != "side"]
        print(f"dropping `side`; using {len(cols)} of {len(FEATURES)} features")
    else:
        cols = None
    if cols is not None:
        print(f"feature set ({len(cols)} of {len(all_names)}): "
              f"{[all_names[i] for i in cols]}")

    ctx = build_holdout(g)
    cells = ctx.cells_of(a.mode)
    print(f"[{time.time()-t0:5.1f}s] holdout ready ({len(cells)} cells, mode={a.mode})")

    geoms = [cell_geometry(ctx, c, geo=geo) for c in cells]
    clf, scale, base = fit_model(geoms, seed=0, cols=cols)
    geoms.clear(); gc.collect()
    print(f"[{time.time()-t0:5.1f}s] trained on all cells; calibration scale={scale:.4f} "
          f"base_rate={base:.6f}")

    # ---- 2. flank-exclusion measured on the holdout ------------------------
    variants = {}
    flanks = (a.flank,) if a.flank >= 0 else (0, 1, 2, 3)
    for flank in flanks:
        pl, per = score_variant(ctx, cells, clf, scale, flank,
                                max_dots=a.max_dots, floor=a.floor, cols=cols,
                                geo=geo)
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
        per_cap = budget // 2                      # 8 cells = 2 draws
        pl, per = score_variant(ctx, cells, clf, scale, best_flank,
                                max_dots=per_cap, floor=a.floor, cols=cols,
                                geo=geo)
        capped_holdout = pl
        print(f"[{time.time()-t0:5.1f}s] at capped budget {budget}: HOLDOUT-DTI "
              f"pooled={pl['pooled_dti']:.4f} coverage={pl['coverage']:.4f} dots={pl['n_dots']}")

    # ---- 3. final surface from the full catalogue --------------------------
    from gems57.anatomy import fold_geometry
    dom = g.footprint & ~g.catalogue
    geom = fold_geometry(g, g.catalogue, np.zeros(g.shape, bool), dom,
                         "live_full_catalogue", geo=geo)
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
    feat_tag = a.features or ("no_side" if a.drop_side else "anatomy_full")
    tag = a.tag or f"h57-{feat_tag}-{a.mode}-flank{best_flank}"
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
    # the zeros variant is packaged by the shared fail-closed writer (tif + zip
    # + receipt json); the nan variant is diagnostics only and never packaged
    rec = package_submission(
        zpath, np.where(dom, values, 0.0).astype(np.float32),
        ROOT / "data" / "official" / "sample_submission.tif", g.footprint,
        note=note, name=name,
        metadata={"lane": "fault-zone anatomy", "mode": a.mode,
                  "flank_px": best_flank, "feature_set": feat_tag,
                  "features": [all_names[i] for i in cols] if cols is not None
                              else list(all_names)})
    write_submission(npath, np.where(dom, values, np.nan), mode="nan")
    print(f"[{time.time()-t0:5.1f}s] wrote {zpath.name} and {npath.name} "
          f"(receipt {zpath.with_suffix('.json').name})")

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
        "feature_set": feat_tag,
        "features": [all_names[i] for i in cols] if cols is not None else list(all_names),
        "features_dropped": [n for i, n in enumerate(all_names)
                             if cols is None or i not in cols],
        "budget_cap": a.budget_cap,
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
        "packaging_receipt": rec,
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
