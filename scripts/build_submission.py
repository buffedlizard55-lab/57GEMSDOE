#!/usr/bin/env python3
"""Build a research-only lane GeoTIFF with explicit, fail-closed audit gates.

The saved leave-one-quadrant-out evidence is loaded as a comparator, never
replaced by in-sample scoring of the same folds used to train the final model.
Surface correlation runs before dot allocation; final-dot overlap runs after
allocation and before packaging. A missing/incomplete local registry or a
threshold breach stops the build. Neither local validation nor this script is
an organizer receipt or a promotion decision.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import grid as gridmod                                   # noqa: E402
from gems57 import load_grid                                          # noqa: E402
from gems57.submission_writer import write_submission as write_portal_submission  # noqa: E402
from gems57.anatomy import FEATURES                                  # noqa: E402
from gems57.emit import greedy_allocate                             # noqa: E402
from gems57.fitting import cell_geometry, fit_model                 # noqa: E402
from gems57.holdout import build_holdout                             # noqa: E402
from gems57.uniqueness import (compare_surface_to_registry,          # noqa: E402
                               compare_to_registry)
from gems57.validate import assert_submittable, validate             # noqa: E402
from scipy import ndimage as ndi                                     # noqa: E402

EVID = ROOT / "evidence"
DL = ROOT / "docs" / "downloads"


def load_oof_baseline(mode: str, variant: str) -> dict:
    """Load the saved leave-one-quadrant-out result; never score training folds in-sample."""
    path = EVID / f"cv_{mode}.json"
    if not path.exists():
        return {"available": False, "path": str(path),
                "promotion_eligible": False,
                "reason": "no saved out-of-fold CV evidence; builder will not substitute an in-sample score"}
    data = json.loads(path.read_text())
    item = data.get("variants", {}).get(variant)
    if item is None:
        return {"available": False, "path": str(path), "variant": variant,
                "promotion_eligible": False,
                "reason": "requested model variant is absent from saved CV evidence"}
    pooled = item.get("pooled", {})
    canary = data.get("canary", {})
    flags = [name for name, result in canary.items() if result.get("leakage_flag")]
    dots = int(pooled.get("n_dots", 0))
    seeds = max(int(data.get("n_cells", 0)) // 4, 1)
    per_map_dots = dots / seeds
    return {
        "available": True,
        "evidence_class": "HOLDOUT-DTI",
        "path": str(path),
        "withholding_mode": mode,
        "variant": variant,
        "pooled_dti": pooled.get("pooled_dti"),
        "ci95_quadrant_jackknife": pooled.get("dti_ci95_quadrant_jackknife"),
        "withheld_positive_pixels": pooled.get("n_truth"),
        "n_dots_across_all_draws": dots,
        "n_spatial_draws": seeds,
        "dots_per_full_map_approx": per_map_dots,
        "budget_matched": False,
        "evaluator_version": data.get(
            "evaluator_version",
            "legacy H57 metric.dti_binary + fitting.pooled; saved OOF CV before adapter v2"),
        "evaluator_implementation_hashes": data.get("evaluator_implementation_hashes"),
        "leakage_canary_flags": flags,
        "canary": canary,
        "promotion_eligible": bool(not flags),
        "reason": ("single-feature leakage canary exceeds 0.90; explain/retest before promotion"
                   if flags else
                   "saved OOF result is not budget-matched to this build; require a cap-matched OOF run"),
        "scope_note": "local hide-and-recover validation only; not a live/organizer score",
    }


def runtime_registry_index(exclude: Path | None = None) -> Path:
    """Merge the pinned audit set with additional local download rasters.

    Existing submission TIFFs become priors on the next build, so relying only
    on a static index could silently permit a repeat. ``exclude`` is used when
    auditing an already-built candidate, to avoid comparing that file with
    itself. NaN-filled diagnostic variants are excluded because they are not
    submission candidates. Paths are absolute because the temporary index lives
    outside ROOT.
    """
    base = ROOT / "registry" / "audit_index.json"
    rows = json.loads(base.read_text())
    root = base.parent.parent
    excluded = exclude.resolve() if exclude is not None else None
    known = set()
    filtered_rows = []
    for row in rows:
        p = Path(row["file"])
        if not p.is_absolute():
            p = root / p
        p = p.resolve()
        if p == excluded:
            continue
        row["file"] = str(p)
        filtered_rows.append(row)
        known.add(p)
    rows = filtered_rows
    for p in sorted(DL.glob("*.tif")):
        # The builder writes a NaN-filled diagnostic beside the finite portal
        # candidate. It is not a submission prior and must not poison future
        # uniqueness checks after non-finite values are normalized to zero.
        if p.stem.endswith("-nan"):
            continue
        resolved = p.resolve()
        if resolved == excluded or resolved in known:
            continue
        rows.append({"repo": "57GEMSDOE-local-downloads",
                     "submission": p.name, "file": str(resolved),
                     "owner_reported_score": None, "mode": "local-prior"})
        known.add(resolved)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     prefix="gems57-registry-audit-",
                                     encoding="utf-8", delete=False) as tmp:
        json.dump(rows, tmp, indent=2)
        return Path(tmp.name)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["all", "detached"])
    ap.add_argument("--max-dots", type=int, default=40_000,
                    help="final-map dot budget (default 40,000); not a holdout score")
    ap.add_argument("--floor", type=float, default=0.015)
    ap.add_argument("--tag", default="")
    ap.add_argument("--include-geometric-side", action="store_true",
                    help="include the geometric left/right feature; it is not slip-sense data")
    ap.add_argument("--flank-px", type=int, choices=range(0, 4), default=0,
                    help="pre-registered catalogue exclusion; not selected from in-sample scores")
    a = ap.parse_args()

    cols = [i for i, n in enumerate(FEATURES)
            if a.include_geometric_side or n != "side"]
    feature_variant = "anatomy_full" if a.include_geometric_side else "no_side"
    print(f"using {len(cols)} H57 geometry features ({feature_variant}); "
          "recorded slip-sense is not encoded in this model")
    t0 = time.time()

    g = load_grid()
    ctx = build_holdout(g)
    cells = ctx.cells_of(a.mode)
    print(f"[{time.time()-t0:5.1f}s] holdout ready ({len(cells)} cells, mode={a.mode})")

    # The prior builder trained and scored these same folds in-sample and split
    # a 40k map budget across only two draws, not four quadrants. Do not repeat
    # that invalid evaluation. Load only saved leave-one-quadrant-out evidence;
    # a missing or mismatched OOF run is a hard promotion stop.
    holdout_evidence = load_oof_baseline(a.mode, feature_variant)
    holdout_evidence["budget_matched"] = bool(
        holdout_evidence.get("available") and
        holdout_evidence.get("dots_per_full_map_approx", float("inf")) <= a.max_dots)
    holdout_evidence["promotion_eligible"] = bool(
        holdout_evidence.get("promotion_eligible") and holdout_evidence["budget_matched"])
    holdout_reasons = []
    if holdout_evidence.get("leakage_canary_flags"):
        holdout_reasons.append("single-feature leakage canary exceeds 0.90")
    if not holdout_evidence["budget_matched"]:
        holdout_reasons.append("saved OOF CV is not budget-matched; no cap-matched spatial score")
    if not holdout_evidence.get("available"):
        holdout_reasons.append(holdout_evidence.get("reason", "no OOF evidence"))
    holdout_evidence["reason"] = "; ".join(holdout_reasons) or "saved OOF baseline loaded"
    print(f"saved OOF evidence: {holdout_evidence.get('pooled_dti')} "
          f"({holdout_evidence.get('evaluator_version')}); promotion_eligible="
          f"{holdout_evidence['promotion_eligible']}; {holdout_evidence.get('reason')}")

    geoms = [cell_geometry(ctx, c) for c in cells]
    clf, scale, base = fit_model(geoms, seed=0, cols=cols)
    geoms.clear(); gc.collect()
    print(f"[{time.time()-t0:5.1f}s] trained final model; calibration scale={scale:.4f} "
          f"base_rate={base:.6f}")
    best_flank = int(a.flank_px)
    budget = int(a.max_dots)

    # ---- 2. final surface from the full catalogue --------------------------
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

    registry_index = runtime_registry_index()
    surface_audit = compare_surface_to_registry(p, registry_index, g.footprint)
    surface_audit["registry_index"] = (
        "runtime merge of registry/audit_index.json and pre-existing docs/downloads/*.tif")
    print(f"[{time.time()-t0:5.1f}s] pre-placement surface audit: "
          f"complete={surface_audit['complete']} worst rho="
          f"{surface_audit['worst_spearman_full_footprint']:.4f} vs "
          f"{surface_audit['worst_submission']}")
    if not surface_audit["unique_within_inventory"]:
        registry_index.unlink(missing_ok=True)
        raise SystemExit("STOP: pre-placement surface audit is duplicate or incomplete")

    truth_seed = min(c.seed for c in cells)
    k_truth = float(sum(c.n_truth for c in cells if c.seed == truth_seed))
    alloc = greedy_allocate(p, allowed, k_truth=k_truth,
                            floor=a.floor, max_dots=budget)
    print(f"[{time.time()-t0:5.1f}s] allocated {alloc.n_dots} dots; "
          f"expected covered credit={alloc.expected_covered_credit:.1f}")

    # Final-dot proximity is a second, separate gate. It runs before packaging,
    # so a duplicate is stopped locally and never looks like a submission.
    uniq = compare_to_registry(alloc.emitted.astype(np.float32),
                               registry_index, g.footprint)
    print(f"[{time.time()-t0:5.1f}s] final-dot audit: complete={uniq['audit_complete']} "
          f"worst rho={uniq['worst_spearman_full_footprint']:.4f} "
          f"({uniq['worst_rho_submission']}); worst <=3px overlap="
          f"{uniq['worst_dot_overlap']*100:.1f}% ({uniq['worst_overlap_submission']})")
    registry_index.unlink(missing_ok=True)
    if not uniq["unique"]:
        raise SystemExit("STOP: final-dot audit is duplicate or incomplete")

    # ---- 4. write ----------------------------------------------------------
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(alloc.emitted.tobytes()).hexdigest()[:12]
    tag = a.tag or f"h57-anatomy-enechelon-{a.mode}-flank{best_flank}"
    name = f"gems57-{tag}-{stamp}-{digest}"
    # The portal shown in the task has one optional note field, not a separate
    # submission-name field. Put the unique run ID in that note so it survives
    # after upload, while keeping the note within the 140-character cap.
    note = f"{name} | fitted fault-zone anatomy; {alloc.n_dots} dots; 0 on catalogue"
    assert len(note) <= 140, f"submission note is {len(note)} chars, limit 140"
    DL.mkdir(parents=True, exist_ok=True)
    values = alloc.emitted.astype(np.float32)
    zpath = DL / f"{name}-zeros.tif"
    npath = DL / f"{name}-nan.tif"
    portal_values = np.where(g.footprint, values, 0.0).astype(np.float32)
    submission_receipt = write_portal_submission(
        zpath, portal_values, gridmod.DATA_DIR / "sample_submission.tif",
        g.footprint, note=note, name=name,
        metadata={"lane": "fault-zone anatomy", "mode": a.mode,
                  "selected_flank_px": best_flank, "budget_cap": budget,
                  "emitted_pixels": int(alloc.n_dots)})
    gridmod.write_submission(npath, np.where(dom, values, np.nan), mode="nan")
    print(f"[{time.time()-t0:5.1f}s] wrote {zpath.name} and {npath.name}")

    # ---- 5. validate + provenance -----------------------------------------
    vz = validate(zpath, g.footprint, g.catalogue)
    vn = validate(npath, g.footprint, g.catalogue)
    assert_submittable(vz)
    print(f"[{time.time()-t0:5.1f}s] ZEROS variant: {len(vz['checks'])} checks, "
          f"all_passed={vz['all_checks_passed']}, sha256={vz['sha256'][:16]}")
    print(f"  NaN variant all_passed={vn['all_checks_passed']} "
          f"(NOT submittable: n_nan={vn['n_nan']}) -- diagnostics only")

    sense_encoded = False
    promotion_eligible = bool(
        holdout_evidence.get("promotion_eligible")
        and surface_audit.get("unique_within_inventory")
        and uniq.get("unique")
        and vz["all_checks_passed"]
        and sense_encoded)
    audit = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "lane": "fault-zone anatomy / secondary strands around known faults",
        "withholding_mode": a.mode,
        "features": [FEATURES[i] for i in cols],
        "features_dropped": [n for n in FEATURES if FEATURES.index(n) not in cols],
        "recorded_sense_of_slip_encoded": sense_encoded,
        "budget_cap": budget,
        "holdout_evidence": holdout_evidence,
        "holdout_at_capped_budget": None,
        "holdout_score_status": "no budget-matched OOF score; never substitute self-fit scoring",
        "calibration": {"scale": scale, "base_rate": base},
        "flank_selection": "pre-registered CLI value; not selected from in-sample scores",
        "selected_flank_px": best_flank,
        "holdout_dot_budget": holdout_evidence.get("dots_per_full_map_approx"),
        "live_dot_budget": budget,
        "emitted_pixels": int(alloc.n_dots),
        "submission_name": name,
        "submission_note": note,
        "submission_note_len": len(note),
        "zeros_tif": vz,
        "nan_tif": vn,
        "submission_receipt": submission_receipt,
        "surface_uniqueness": surface_audit,
        "uniqueness": uniq,
        "promote": promotion_eligible,
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
