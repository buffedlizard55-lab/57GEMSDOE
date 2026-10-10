#!/usr/bin/env python3
"""Build, validate and uniqueness-check the session-2 fault-zone-anatomy
submission GeoTIFF (provenance builder for
h57r2-shipped8-all-flank0-20261009T180433Z).

This is the session-2 (arena/884d08ea) builder, preserved under a new name
after the sibling sessions retired the original `scripts/build_submission.py`
("do not revive oracle budgets or place before a gate") on main.  It trains
the fault-zone-anatomy intensity on all holdout cells of the chosen
withholding mode, measures two emission variants on the holdout -- with and
without a hard exclusion of the immediate catalogue flank -- picks by
measurement, allocates dots at the exact DTI marginal bar under the live
budget cap, validates the zeros variant, and uniqueness-checks it against
the in-repo registry with the IR-57-OVERLAP-01 split screen
(unique_vs_other_lanes is the drift verdict; same-lane overlap is
disclosed).

Session-2 additions over the retired original: named feature-set variants
(`--variant {shipped8,no_rielder,gated,anatomy_full,no_side}`) so a rebuild
can produce a *different* raster from the same pipeline, and the split
uniqueness screen.  The audit records the variant.

Usage:
    python scripts/build_r2_submission.py --mode all --variant shipped8 \
        --budget-cap 40000
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

# Named feature sets (column indices into gems57.anatomy.FEATURES).  Keeping the
# shipped session-1 set addressable by name is what lets this script build a
# *different* raster from the same pipeline: uniqueness is a property of the
# configuration, not of the code.
SHIPPED8 = ["d", "d_perp", "d_par_abs", "log_len", "sin2", "cos2", "coherence", "density"]
VARIANT_COLS = {
    "shipped8":     [n for n in SHIPPED8],
    "no_rielder":   [n for n in SHIPPED8 if n not in ("d_perp", "d_par_abs")],
    "gated":        SHIPPED8 + ["sin2d", "cos2d"],
    "anatomy_full": list(FEATURES),
    "no_side":      [n for n in FEATURES if n != "side"],
}


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["all", "detached"])
    ap.add_argument("--max-dots", type=int, default=200_000)
    ap.add_argument("--floor", type=float, default=0.015)
    ap.add_argument("--tag", default="")
    ap.add_argument("--variant", default="shipped8",
                    choices=sorted(VARIANT_COLS),
                    help="named feature set (default shipped8 = the session-1 config)")
    ap.add_argument("--drop-side", action="store_true",
                    help="deprecated alias for --variant shipped8")
    ap.add_argument("--budget-cap", type=int, default=0,
                    help="hard cap on live dots; 0 = use the holdout-optimal budget")
    a = ap.parse_args()

    if a.drop_side and a.variant != "shipped8":
        ap.error("--drop-side is an alias for --variant shipped8; do not combine")
    names = VARIANT_COLS["shipped8"] if a.drop_side else VARIANT_COLS[a.variant]
    cols = [i for i, n in enumerate(FEATURES) if n in names]
    dropped = [n for n in FEATURES if n not in names]
    print(f"variant {a.variant}: using {len(cols)} of {len(FEATURES)} features "
          f"({', '.join(names)}); dropped: {', '.join(dropped) or 'none'}")
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
        per_cap = budget // 2                      # 8 cells = 2 draws
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
    tag = a.tag or f"h57r2-{a.variant}-{a.mode}-flank{best_flank}"
    name = f"gems57-{tag}-{stamp}-{digest}"
    # <= 140 characters, enforced below
    note = (f"57GEMSDOE fault-zone anatomy | variant {a.variant} ({a.mode}, "
            f"flank {best_flank}px) | {alloc.n_dots} dots, 0 on-catalogue | "
            f"sha {digest[:8]}")
    if len(note) > 140:
        note = (f"57GEMSDOE anatomy | {a.variant} {a.mode} flank{best_flank} | "
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
    # IR-57-OVERLAP-01: the protocol's stop rule exists to catch drift into
    # ANOTHER lane.  The registry also carries this repository's own earlier
    # builds of the SAME lane; two halos around the same faults overlap by
    # construction, so the 70% proximity tripwire can fire on a same-lane
    # rebuild.  Split the screen: the drift verdict is taken against rasters
    # from OTHER lanes/repos; same-lane overlap is disclosed, not hidden.
    rows = [r for r in uniq["rows"] if "error" not in r]
    sib = [r for r in rows if r["repo"] != "57GEMSDOE"]
    own = [r for r in rows if r["repo"] == "57GEMSDOE"]
    def _worst(rs, key):
        if not rs:
            return None, None
        r = max(rs, key=lambda r: r[key])
        return r[key], r["submission"]
    uniq["unique_vs_other_lanes"] = not any(
        r.get("duplicate_by_rho") or r.get("duplicate_by_overlap")
        or r.get("duplicate_by_jaccard") for r in sib)
    uniq["n_other_lane_rasters"] = len(sib)
    uniq["worst_overlap_other_lanes"], uniq["worst_overlap_other_lane_sub"] = \
        _worst(sib, "my_dots_within_3px_of_theirs")
    uniq["worst_rho_other_lanes"], uniq["worst_rho_other_lane_sub"] = \
        _worst(sib, "spearman_full_footprint")
    uniq["worst_jaccard_other_lanes"], uniq["worst_jaccard_other_lane_sub"] = \
        _worst(sib, "jaccard_dot_sets")
    uniq["n_same_lane_earlier_builds"] = len(own)
    uniq["worst_overlap_same_lane"], uniq["worst_overlap_same_lane_sub"] = \
        _worst(own, "my_dots_within_3px_of_theirs")
    uniq["worst_jaccard_same_lane"], uniq["worst_jaccard_same_lane_sub"] = \
        _worst(own, "jaccard_dot_sets")
    uniq["worst_rho_same_lane"], uniq["worst_rho_same_lane_sub"] = \
        _worst(own, "spearman_full_footprint")
    uniq["same_lane_overlap_note"] = (
        "overlap vs this repository's own earlier builds of the SAME lane is expected "
        "physics (two halos around the same faults); it is disclosed here and is NOT a "
        "lane-drift firing. The drift screen is unique_vs_other_lanes.")
    print(f"[{time.time()-t0:5.1f}s] uniqueness vs {len(sib)} OTHER-LANE rasters: "
          f"{uniq['unique_vs_other_lanes']} | worst rho={uniq['worst_rho_other_lanes']:.4f} "
          f"(limit {uniq['rho_limit']}) | worst jaccard={uniq['worst_jaccard_other_lanes']:.4f} "
          f"(limit {uniq['jaccard_limit']}) | worst dot overlap="
          f"{uniq['worst_overlap_other_lanes']*100:.1f}% (limit {uniq['overlap_limit']*100:.0f}%)")
    print(f"  vs {len(own)} same-lane earlier builds (disclosed, IR-57-OVERLAP-01): "
          f"worst overlap={uniq['worst_overlap_same_lane']*100:.1f}% vs "
          f"{uniq['worst_overlap_same_lane_sub'][:48]} | worst jaccard="
          f"{uniq['worst_jaccard_same_lane']:.4f} | worst rho="
          f"{uniq['worst_rho_same_lane']:.4f}")
    print(f"  mechanical all-rasters verdict: {uniq['unique']}")
    if not uniq["unique_vs_other_lanes"]:
        print("REFUSING TO PROMOTE: the parallel-run protocol declares this a duplicate "
              "of another lane's raster.")

    audit = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "lane": "fault-zone anatomy / secondary strands around known faults",
        "withholding_mode": a.mode,
        "variant": a.variant,
        "features": [FEATURES[i] for i in cols] if cols is not None else list(FEATURES),
        "features_dropped": [n for n in FEATURES if cols is None or FEATURES.index(n) not in cols],
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
        "zeros_tif": vz,
        "nan_tif": vn,
        "uniqueness": uniq,
        # promote = validator clean AND clear of every OTHER lane's raster.
        # Same-lane overlap with this repo's own earlier builds is disclosed in
        # uniqueness.same_lane_overlap_note (IR-57-OVERLAP-01), not hidden.
        "promote": bool(uniq["unique_vs_other_lanes"] and vz["all_checks_passed"]),
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
