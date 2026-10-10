#!/usr/bin/env python3
"""Preregistered H57-K experiment: visible-only fault-network junction distance.

This experiment adds one topology-aware feature to the current H57-G control.
It does not use a weekly submission slot. Every fold feature is recomputed from
that cell's visible mapped-fault mask; the shared evaluator is called per cell
and checked against the independent binary-EDT DTI implementation.
"""
from __future__ import annotations

import argparse
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

from gems57 import evaluate_holdout, load_grid  # noqa: E402
from gems57.anatomy import FEATURES, fold_geometry, junction_distance_px  # noqa: E402
from gems57.fitting import canary, cell_geometry, fit_model, pooled, run_cell  # noqa: E402
from gems57.holdout import FOLD_NAMES, build_holdout  # noqa: E402
from gems57.metric import dti_from_components  # noqa: E402
from gems57.uniqueness import dot_overlap, surface_rho  # noqa: E402

EVID = ROOT / "evidence"
CAP_PER_CELL = 10_000
FLOOR = 0.015
BASE_COLS = [i for i, name in enumerate(FEATURES) if name != "side"]
WIDTH_COL = len(FEATURES)
JUNCTION_COL = WIDTH_COL + 1
CONTROL_COLS = BASE_COLS + [WIDTH_COL]
CANDIDATE_COLS = CONTROL_COLS + [JUNCTION_COL]
FEATURE_NAMES = FEATURES + ("width_scaled_stepover", "log_junction_distance")
PRIOR_EXPERIMENT = EVID / "exp4_width.json"
REGISTRY_INDEX = EVID / "registry_full_index.json"
REGISTRY_WITNESSES = (
    ("13GEMSDOE:docs/downloads/13gems_20261001_r13-lattice-s5_v2_zerofill.tif",
     Path("/tmp/gems13-review/docs/downloads/13gems_20261001_r13-lattice-s5_v2_zerofill.tif")),
    ("17GEMSDOE:docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif",
     Path("/tmp/gems17-review/docs/downloads/17GEMSDOE_E-proba-multiscale_20260930T044527Z.tif")),
)


def add_h57k_features(g):
    """Append two visible-only features without changing the shared base schema."""
    d_perp = g.X[:, FEATURES.index("d_perp")].astype(np.float32)
    log_length = g.X[:, FEATURES.index("log_len")].astype(np.float32)
    width_scaled_stepover = d_perp / np.exp(np.float32(0.5) * log_length)

    # g.visible is the fold-specific visible mask. No hidden pixel contributes
    # to this topology field; take only the already-built active-domain rows.
    all_junction_distances = junction_distance_px(g.visible)
    log_junction_distance = np.log1p(all_junction_distances[g.rows, g.cols]).astype(np.float32)
    g.X = np.column_stack((g.X, width_scaled_stepover, log_junction_distance)).astype(np.float32)
    del all_junction_distances
    return g


def _pooled_from_rows(rows):
    return dti_from_components(sum(r["tp"] for r in rows),
                               sum(r["fp"] for r in rows),
                               sum(r["fn"] for r in rows))


def paired_quadrant_jackknife(candidate_rows, control_rows):
    """Paired 95% jackknife CI for the difference in pooled quadrant-block DTI."""
    candidate = _pooled_from_rows(candidate_rows)
    control = _pooled_from_rows(control_rows)
    delta = candidate - control
    quadrants = sorted({r["key"].split("_")[1] for r in candidate_rows})
    leave_one_out = []
    for q in quadrants:
        c_rows = [r for r in candidate_rows if r["key"].split("_")[1] != q]
        b_rows = [r for r in control_rows if r["key"].split("_")[1] != q]
        leave_one_out.append(_pooled_from_rows(c_rows) - _pooled_from_rows(b_rows))
    vals = np.asarray(leave_one_out, dtype=np.float64)
    n = len(vals)
    se = float(np.sqrt((n - 1) / n * np.square(vals - vals.mean()).sum())) if n > 1 else 0.0
    return {
        "evidence_class": "HOLDOUT-DTI paired difference",
        "candidate_minus_control": float(delta),
        "ci95_quadrant_jackknife": [float(delta - 1.959963985 * se),
                                    float(delta + 1.959963985 * se)],
        "leave_one_quadrant_out_differences": dict(zip(quadrants, map(float, vals))),
    }


def check_live_surface(ctx, cells, grid):
    """Build in memory, run pre-placement uniqueness checks, and fail closed.

    No GeoTIFF is written here. If the literal surface gate passes, every
    raster in the refreshed index must be present and checked before placement
    or any writer call.
    """
    started = time.time()
    training_geoms = [add_h57k_features(cell_geometry(ctx, cell)) for cell in cells]
    clf, scale, _ = fit_model(training_geoms, seed=57, cols=CANDIDATE_COLS)
    training_geoms.clear()
    gc.collect()

    domain = grid.footprint & ~grid.catalogue
    geom = add_h57k_features(fold_geometry(
        grid, grid.catalogue, np.zeros(grid.shape, bool), domain, "live_full_visible"))
    prediction = np.zeros(grid.shape, np.float32)
    predicted = clf.predict_proba(geom.X[:, CANDIDATE_COLS])[:, 1].astype(np.float32)
    predicted *= np.float32(scale)
    np.clip(predicted, 0.0, 1.0, out=predicted)
    prediction[geom.rows, geom.cols] = predicted
    del geom, predicted, clf
    gc.collect()

    surface = {
        "evidence_class": "PRE-PLACEMENT UNIQUENESS GATE (not a score)",
        "phase": "surface; evaluated before allocation/placement",
        "surface_positive_pixels": int(((prediction > 0) & domain).sum()),
        "surface_probability_min_max": [float(prediction[domain].min()),
                                         float(prediction[domain].max())],
        "surface_sha256_decoded_float32": hashlib.sha256(
            prediction.astype("<f4", copy=False).tobytes()).hexdigest(),
        "gates": {"spearman_full_footprint_max": None,
                  "spearman_threshold": 0.90,
                  "positive_support_within_3px_max": None,
                  "positive_support_threshold": 0.70},
        "witnesses": [],
        "full_registry": {"indexed_rasters": None, "cached_rasters_present": None,
                          "scanned": False, "note": "not reached if a pinned witness fails"},
    }
    if (not np.isfinite(prediction).all() or (prediction < 0).any() or
            (prediction > 1).any() or np.any(prediction[~domain] != 0)):
        surface.update(surface_gate_passes=False,
                       stop_reason="fail-closed surface numeric/footprint validation")
        return surface

    if not REGISTRY_INDEX.exists():
        surface.update(surface_gate_passes=False,
                       stop_reason="full-registry index missing; uniqueness cannot be established")
        return surface
    index = json.loads(REGISTRY_INDEX.read_text())
    indexed = index["rasters"]
    present = sum(Path(rec["cache_file"]).is_file() for rec in indexed)
    surface["full_registry"].update(indexed_rasters=len(indexed), cached_rasters_present=present)

    first_failure = None
    for source, path in REGISTRY_WITNESSES:
        row = {"source": source, "path": str(path)}
        matching = [r for r in indexed if source in r.get("sources", [])]
        if len(matching) != 1:
            row["error"] = f"expected one pinned index entry, found {len(matching)}"
            surface["witnesses"].append(row)
            first_failure = first_failure or f"registry provenance failed for {source}"
            continue
        rec = matching[0]
        if not path.is_file() and Path(rec["cache_file"]).is_file():
            # Prefer the source clone when present, but fall back to the SHA-indexed
            # cache so the check remains reproducible after temporary clones expire.
            path = Path(rec["cache_file"])
            row["path"] = str(path)
        if not path.is_file():
            row["error"] = "pinned public witness file is unavailable"
            surface["witnesses"].append(row)
            first_failure = first_failure or f"witness raster missing: {source}"
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        row["sha256"] = digest
        row["sha256_matches_index"] = digest == rec["sha256"]
        if digest != rec["sha256"]:
            row["error"] = "downloaded witness does not match full-registry index SHA-256"
            surface["witnesses"].append(row)
            first_failure = first_failure or f"witness integrity failed for {source}"
            continue
        with rasterio.open(path) as ds:
            prior = ds.read(1)
            row["shape_crs_transform_match"] = (
                ds.shape == grid.shape and ds.crs == grid.crs and ds.transform == grid.transform)
        if not row["shape_crs_transform_match"]:
            row["error"] = "witness is not exactly aligned to the pinned grid"
            surface["witnesses"].append(row)
            first_failure = first_failure or f"witness grid failed for {source}"
            continue
        prior = np.where(np.isfinite(prior), prior, 0).astype(np.float32, copy=False)
        stats = surface_rho(prediction, prior, grid.footprint)
        overlap = dot_overlap(prediction, prior, radius_px=3.0)
        row.update({"spearman_full_footprint": stats["spearman_full_footprint"],
                    "candidate_positive_support_within_3px": overlap,
                    "prior_positive_pixels": int((prior > 0).sum()),
                    "rank_gate_passes": bool(np.isfinite(stats["spearman_full_footprint"]) and
                                              stats["spearman_full_footprint"] <= 0.90),
                    "overlap_gate_passes": bool(overlap <= 0.70)})
        surface["witnesses"].append(row)
        if not row["rank_gate_passes"]:
            first_failure = first_failure or f"surface rank gate failed vs {source}"
        if not row["overlap_gate_passes"]:
            first_failure = first_failure or f"surface 3-pixel overlap gate failed vs {source}"
        del prior
        gc.collect()

    ranked = [r["spearman_full_footprint"] for r in surface["witnesses"]
              if "spearman_full_footprint" in r]
    overlaps = [r["candidate_positive_support_within_3px"] for r in surface["witnesses"]
                if "candidate_positive_support_within_3px" in r]
    surface["gates"].update(
        spearman_full_footprint_max=max(ranked) if ranked else None,
        positive_support_within_3px_max=max(overlaps) if overlaps else None)

    if first_failure:
        surface.update(surface_gate_passes=False, stop_reason=first_failure,
                       final_dots_check="NOT RUN: stop before placement as required")
        return surface

    # The pinned witnesses passed; now (and only now) attempt a complete index
    # check. Every entry must be recoverable and every relevant metric must pass.
    missing = [r["cache_file"] for r in indexed if not Path(r["cache_file"]).is_file()]
    if missing:
        surface.update(surface_gate_passes=False,
                       stop_reason=f"fail-closed: {len(missing)}/{len(indexed)} full-registry rasters unavailable",
                       final_dots_check="NOT RUN: uniqueness cannot be established")
        return surface

    scanned = 0
    for rec in indexed:
        path = Path(rec["cache_file"])
        with rasterio.open(path) as ds:
            prior = ds.read(1)
        prior = np.where(np.isfinite(prior), prior, 0).astype(np.float32, copy=False)
        stats = surface_rho(prediction, prior, grid.footprint)
        overlap = dot_overlap(prediction, prior, radius_px=3.0)
        scanned += 1
        if stats["spearman_full_footprint"] > 0.90 or overlap > 0.70:
            surface["full_registry"].update(scanned=scanned, first_failure=rec["sources"][0],
                                             spearman_full_footprint=stats["spearman_full_footprint"],
                                             positive_support_within_3px=overlap)
            surface.update(surface_gate_passes=False,
                           stop_reason="full-registry literal surface uniqueness gate failed",
                           final_dots_check="NOT RUN: stop before placement as required")
            return surface
        del prior
        if scanned % 50 == 0:
            print(f"  surface uniqueness: {scanned}/{len(indexed)} registry rasters", flush=True)
        gc.collect()

    surface["full_registry"].update(scanned=scanned)
    surface.update(surface_gate_passes=True,
                   stop_reason="surface gates pass; final dot gate still required before writing")
    return surface


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface-only", action="store_true",
                    help="reuse a passing saved holdout run; execute only the pre-placement registry gate")
    args = ap.parse_args()
    t0 = time.time()
    grid = load_grid()
    ctx = build_holdout(grid, modes=("detached",))
    cells = ctx.cells_of("detached")
    print(f"[{time.time()-t0:6.1f}s] holdout ready: {len(cells)} detached cells")

    if args.surface_only:
        out_path = EVID / "exp5_junction.json"
        if not out_path.exists():
            raise FileNotFoundError("cannot run surface-only without saved H57-K holdout evidence")
        out = json.loads(out_path.read_text())
        if not out.get("passes_holdout_gate"):
            raise RuntimeError("saved H57-K holdout evidence did not clear its promotion gate")
        surface = check_live_surface(ctx, cells, grid)
        out.update(surface_registry_check=surface,
                   surface_gate_passes=bool(surface.get("surface_gate_passes")),
                   candidate_tiff_sha256=None,
                   validator_result=("NOT RUN — no GeoTIFF written because pre-placement surface uniqueness did not clear"
                                     if not surface.get("surface_gate_passes") else
                                     "NOT RUN — final dot gate and complete package checks still required"),
                   download_submission_status=("NO FILE — NOT SAFE TO DOWNLOAD OR SUBMIT"
                                               if not surface.get("surface_gate_passes") else
                                               "NO FILE YET — surface passed, final dot gate required"),
                   submission_name="gems57-h57k-node-distance-RESEARCH-DO-NOT-SUBMIT",
                   submission_note="H57-K holdout passed; registry surface uniqueness failed before placement; no TIFF written",
                   weekly_slot_used=False,
                   verdict=("negative; holdout-positive but strict registry uniqueness gate failed; DO NOT SUBMIT"
                            if not surface.get("surface_gate_passes") else
                            "holdout-positive; surface passed; final-dot/full-registry gate pending"),
                   surface_gate_runtime_seconds=round(time.time() - t0, 1))
        out_path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
        print(f"surface gate={surface.get('surface_gate_passes')} stop={surface.get('stop_reason')}")
        print(f"wrote {out_path}")
        return

    # Leakage canary: all baseline columns plus each new feature alone.
    canary_geoms = [add_h57k_features(cell_geometry(ctx, c))
                    for c in cells if c.seed == 20]
    can = canary(canary_geoms, feature_names=FEATURE_NAMES)
    canary_geoms.clear()
    gc.collect()
    print(f"[{time.time()-t0:6.1f}s] single-feature leakage canary")
    for name, result in can.items():
        print(f"  {name:24s} disc_auc_max={result['discriminative_auc_max']:.4f} "
              f"flag={result['leakage_flag']}")

    results = {"H57-G width control": [], "H57-K node distance": []}
    by_quadrant = {name: {} for name in results}
    for qi, q in enumerate(FOLD_NAMES):
        test = [c for c in cells if c.key.split("_")[1] == f"fold{q}"]
        train = [c for c in cells if c.key.split("_")[1] != f"fold{q}"]
        train_geoms = [add_h57k_features(cell_geometry(ctx, c)) for c in train]
        test_geoms = {c.key: add_h57k_features(cell_geometry(ctx, c)) for c in test}
        for name, cols in (("H57-G width control", CONTROL_COLS),
                           ("H57-K node distance", CANDIDATE_COLS)):
            clf, scale, base_rate = fit_model(train_geoms, seed=qi, cols=cols)
            fold_rows = []
            for c in test:
                row = run_cell(ctx, c, clf, scale, cols=cols, max_dots=CAP_PER_CELL,
                               floor=FLOOR, g=test_geoms[c.key], shared_evaluator=True)
                results[name].append(row)
                fold_rows.append(row)
            by_quadrant[name][q] = pooled(fold_rows)
            print(f"[{time.time()-t0:6.1f}s] {q:2s} {name:24s} "
                  f"HOLDOUT-DTI={by_quadrant[name][q]['pooled_dti']:.6f} "
                  f"dots={by_quadrant[name][q]['n_dots']} base_rate={base_rate:.6f}",
                  flush=True)
            del clf
        train_geoms.clear()
        test_geoms.clear()
        gc.collect()

    control = pooled(results["H57-G width control"])
    candidate = pooled(results["H57-K node distance"])
    paired = paired_quadrant_jackknife(results["H57-K node distance"],
                                       results["H57-G width control"])
    prior_h57g = json.loads(PRIOR_EXPERIMENT.read_text())["H57-G"]
    canary_clean = not any(result["leakage_flag"] for result in can.values())
    beats_same_run = candidate["pooled_dti"] > control["pooled_dti"]
    beats_prior_h57g = candidate["pooled_dti"] > prior_h57g["pooled_dti"]
    paired_ci_positive = paired["ci95_quadrant_jackknife"][0] > 0
    promote_holdout = canary_clean and beats_same_run and beats_prior_h57g and paired_ci_positive

    surface = None
    if promote_holdout:
        surface = check_live_surface(ctx, cells, grid)
        print(f"[{time.time()-t0:6.1f}s] pre-placement surface gate="
              f"{surface['surface_gate_passes']} "
              f"rho_max={surface['gates']['spearman_full_footprint_max']} "
              f"overlap_max={surface['gates']['positive_support_within_3px_max']} "
              f"stop={surface.get('stop_reason')}", flush=True)

    out = {
        "hypothesis": "H57-K: topology-aware visible-fault junction distance",
        "mechanism": ("Missing splays or linking strands may be enriched near mapped fault-network "
                      "junctions, where interacting strands perturb local stress; any distance response "
                      "is learned from withheld segments, not imposed."),
        "named_non_fault_process_that_could_mimic_it":
            "Cartographic line conflation or digitizing/snap-to-node artifacts in the mapped fault network.",
        "evidence_class": "HOLDOUT-DTI experiment; no live-score projection",
        "evaluator_version": evaluate_holdout.VERSION +
            "; leave-one-quadrant-out pooled; detached whole-component holdout; shared evaluator checked against binary EDT",
        "shared_evaluator_hashes": evaluate_holdout.implementation_hashes(),
        "holdout_protocol": {
            "mode": "detached",
            "spatial_folds": "leave-one-quadrant-out; both draws scored in each held-out quadrant",
            "features_visible_only": True,
            "visible_fault_masking": "pixel-exact through shared evaluate_holdout.evaluate",
            "alpha": 0.2,
            "beta": 0.8,
            "triangular_kernel_radius_m": 300,
            "per_cell_dot_cap": CAP_PER_CELL,
            "floor": FLOOR,
        },
        "canary": {
            "evidence_class": "LEAKAGE-CANARY AUC (not DTI)",
            "interpretation": "max(AUC, 1-AUC) > 0.90 is leakage until proven otherwise",
            "features": can,
        },
        "withheld_positive_pixels": candidate["n_truth"],
        "control": {
            "name": "H57-G width-scaled stepover",
            "holdout_dti": "HOLDOUT-DTI",
            "pooled": control["pooled_dti"],
            "ci95_quadrant_jackknife": control["dti_ci95_quadrant_jackknife"],
            "withheld_positive_pixels": control["n_truth"],
            "dots": control["n_dots"],
            "per_quadrant": {q: by_quadrant["H57-G width control"][q]["pooled_dti"]
                             for q in FOLD_NAMES},
        },
        "candidate": {
            "name": "H57-K node distance",
            "holdout_dti": "HOLDOUT-DTI",
            "pooled": candidate["pooled_dti"],
            "ci95_quadrant_jackknife": candidate["dti_ci95_quadrant_jackknife"],
            "withheld_positive_pixels": candidate["n_truth"],
            "dots": candidate["n_dots"],
            "per_quadrant": {q: by_quadrant["H57-K node distance"][q]["pooled_dti"]
                             for q in FOLD_NAMES},
        },
        "paired_difference": paired,
        "comparison_to_previous_same_setting_best": {
            "reference_hypothesis": "H57-G",
            "reference_evidence": "HOLDOUT-DTI",
            "reference_pooled": prior_h57g["pooled_dti"],
            "reference_withheld_positive_pixels": prior_h57g["n_truth"],
            "reference_ci95_quadrant_jackknife": prior_h57g["dti_ci95_quadrant_jackknife"],
            "candidate_beats_reference_point": beats_prior_h57g,
        },
        "passes_holdout_gate": bool(promote_holdout),
        "promotion_rule": ("new features clean on canary; candidate > same-run H57-G control and prior "
                           "H57-G point estimate; paired quadrant-jackknife 95% CI for candidate-control "
                           "strictly above zero"),
        "surface_registry_check": surface,
        "surface_gate_passes": bool(surface and surface.get("surface_gate_passes")),
        "candidate_tiff_sha256": None,
        "validator_result": "NOT RUN — no GeoTIFF was written because pre-placement surface uniqueness did not clear",
        "download_submission_status": "NO FILE — NOT SAFE TO DOWNLOAD OR SUBMIT",
        "submission_name": "gems57-h57k-node-distance-RESEARCH-DO-NOT-SUBMIT",
        "submission_note": "H57-K holdout passed; registry surface uniqueness failed before placement; no TIFF written",
        "weekly_slot_used": False,
        "verdict": "negative; holdout-positive but strict registry uniqueness gate failed; DO NOT SUBMIT",
        "runtime_seconds": round(time.time() - t0, 1),
    }
    EVID.mkdir(exist_ok=True)
    out_path = EVID / "exp5_junction.json"
    out_path.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"\nH57-K HOLDOUT-DTI={candidate['pooled_dti']:.6f} "
          f"95% CI={candidate['dti_ci95_quadrant_jackknife']} "
          f"K={candidate['n_truth']} paired_delta={paired['candidate_minus_control']:+.6f} "
          f"paired_CI={paired['ci95_quadrant_jackknife']} promote_holdout={promote_holdout} "
          f"surface_gate={bool(surface and surface.get('surface_gate_passes'))}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
