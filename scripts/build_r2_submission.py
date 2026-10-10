#!/usr/bin/env python3
"""Historical session-2 fault-zone-anatomy research builder.

This is retained for provenance/reproduction only. It is NOT a cleared release
or slot selector. Any output is written to `docs/downloads/archive/`, and the
shared literal registry gate applies to every raster, including same-lane
rasters: Spearman > 0.90 OR candidate-forward 3 px overlap > 0.70 is a failure.
No reverse-overlap, Jaccard, or same-lane exemption is permitted. The current
Session-5 dense-witness certificate proves that every nonempty allowable
candidate fails the forward-overlap gate, so this builder must not be used to
promote a file under the current registry/protocol.

The old feature variants are documented only to identify the historical
configuration. Running this builder would be a new experiment and is outside
the current exhausted experiment budget.

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
DL = ROOT / "docs" / "downloads" / "archive"

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
    blocker_path = EVID / "uniqueness_saturation_certificate.json"
    if not blocker_path.is_file():
        raise SystemExit("FAIL-CLOSED: dense-witness certificate missing; no TIFF will be generated.")
    blocker = json.loads(blocker_path.read_text())
    if blocker.get("universal_overlap_blocker") is True:
        raise SystemExit(
            "FAIL-CLOSED: the pinned dense witness covers every allowable cell; "
            "the literal overlap gate cannot pass. No TIFF was generated."
        )

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
    # Every registry raster is subject to the same literal rule. Same-lane
    # overlap is not exempt; Jaccard and reverse overlap are diagnostics only.
    rows = [r for r in uniq["rows"] if "error" not in r]
    own = [r for r in rows if r.get("repo") == "57GEMSDOE"]
    uniq["same_lane_rasters_checked"] = len(own)
    uniq["same_lane_exemption"] = False
    uniq["same_lane_overlap_note"] = (
        "Same-lane rasters are included in the literal registry gate with no exemption. "
        "Jaccard and reverse overlap are diagnostic only.")
    uniq["jaccard_role"] = "diagnostic only; not a promotion or duplicate gate"
    print(f"[{time.time()-t0:5.1f}s] literal registry gate across {len(rows)} checked rasters: "
          f"pass={uniq['unique']} (rho limit {uniq['rho_limit']}; "
          f"forward overlap limit {uniq['overlap_limit']})")
    print(f"  same-lane rasters checked under the same gate: {len(own)}; "
          f"worst forward overlap={uniq.get('worst_dot_overlap')}; "
          f"worst Spearman={uniq.get('worst_spearman_full_footprint')}; "
          f"Jaccard is diagnostic only")
    if not uniq["unique"]:
        print("REFUSING TO PROMOTE: literal gate failed or registry completeness is unverified.")

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
        # Selector eligibility requires validator PASS and the literal full-registry
        # gate. This builder never selects a slot or clears a download.
        "promote": bool(uniq["unique"] and vz["all_checks_passed"]),
        "okay_to_download": False,
        "download_status": "NOT CLEARED — historical builder output is archive-only",
        "okay_to_submit": False,
        "submission_status": "NOT SUBMITTED — no organizer receipt exists",
        "submission_slots_used": 0,
        "weekly_slot_selected": False,
        "release_role": "historical/research builder; archive provenance only",
        "runtime_s": time.time() - t0,
    }
    EVID.mkdir(exist_ok=True)
    (EVID / f"submission_build_{a.mode}.json").write_text(json.dumps(audit, indent=2))
    (DL / f"checks-{name}-zeros.tif.json").write_text(json.dumps(vz, indent=2))
    print(f"  submission note ({len(note)} chars): {note}")
    print(f"\nwrote evidence/submission_build_{a.mode}.json")
    print(f"ARCHIVED RESEARCH ARTIFACT (NOT CLEARED): docs/downloads/archive/{name}-zeros.tif")


if __name__ == "__main__":
    main()
