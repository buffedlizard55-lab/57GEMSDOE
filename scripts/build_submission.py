#!/usr/bin/env python3
"""Build a fault-zone-anatomy GeoTIFF only after independent, versioned clearance.

This command does not run a parameter sweep or select a weekly slot. It requires
an explicit selector receipt tied to a current spatial-CV evidence file and the
exact builder/writer source hashes. It also refuses to fit or write anything
until all 644 indexed matching-grid rasters are present and hash-verified.

The current repository has no valid clearance receipt and the full registry
cache is incomplete. Expected behavior today is a fail-closed HOLD before model
fitting, GeoTIFF creation, or ZIP packaging.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gc
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import gates, grid as gridmod                         # noqa: E402
from gems57.anatomy import FEATURES                               # noqa: E402
from gems57.emit import greedy_allocate                            # noqa: E402
from gems57.evaluator_provenance import (CV_VERSION, cv_implementation_hashes,
                                         cv_input_hashes, sha256_file)  # noqa: E402
from gems57.fitting import cell_geometry, fit_model                # noqa: E402
from gems57.holdout import build_holdout                           # noqa: E402
from gems57.submission_writer import write_submission              # noqa: E402
from gems57.validate import assert_submittable, validate           # noqa: E402

EVID = ROOT / "evidence"
DL = ROOT / "docs" / "downloads"
CLEARANCE_SCHEMA = "gems57-submission-clearance-v2"
CANDIDATE_ID = "fault-zone-anatomy"
BUILD_IMPLEMENTATION_FILES = (
    "scripts/build_submission.py",
    "src/gems57/evaluator_provenance.py",
    "src/gems57/fitting.py",
    "src/gems57/anatomy.py",
    "src/gems57/holdout.py",
    "src/gems57/metric.py",
    "src/gems57/emit.py",
    "src/gems57/grid.py",
    "src/gems57/spatial.py",
    "src/gems57/network.py",
    "src/gems57/gates.py",
    "src/gems57/validate.py",
    "src/gems57/submission_writer.py",
)

IDX = {name: i for i, name in enumerate(FEATURES)}
FEATURE_VARIANTS = {
    "d_only": [IDX["d"]],
    "d_perp_par": [IDX["d"], IDX["d_perp"], IDX["d_par_abs"]],
    "anatomy_full": list(range(len(FEATURES))),
    "no_side": [i for i, name in enumerate(FEATURES) if name != "side"],
}


def build_implementation_hashes() -> dict[str, str]:
    return {name: sha256_file(ROOT / name) for name in BUILD_IMPLEMENTATION_FILES}


def load_complete_registry(index_path: Path | None = None) -> tuple[list[Path], dict]:
    """Load and verify every indexed matching-grid raster or fail closed.

    The saved inventory is not submission-only; every accessible raster stays
    in scope. Missing, changed, or unindexed cache files make a uniqueness
    decision impossible and stop the build before fitting or writing anything.
    """
    pinned_index = (EVID / "registry_full_index.json").resolve()
    index_path = Path(index_path or pinned_index).resolve()
    if index_path != pinned_index:
        raise ValueError("registry index must be evidence/registry_full_index.json; custom subsets are forbidden")
    if not index_path.is_file():
        raise RuntimeError(f"full-registry index is missing: {index_path}")
    manifest = json.loads(index_path.read_text(encoding="utf-8"))
    entries = manifest.get("rasters")
    expected = manifest.get("n_unique_grid_rasters")
    if (not isinstance(entries, list) or not isinstance(expected, int)
            or isinstance(expected, bool) or expected <= 0 or len(entries) != expected):
        listed = len(entries) if isinstance(entries, list) else "invalid"
        raise RuntimeError(f"registry manifest is incomplete: expected {expected}, listed {listed}")
    if manifest.get("grid") != {"shape": [gridmod.HEIGHT, gridmod.WIDTH], "crs": gridmod.CRS_EPSG}:
        raise RuntimeError("registry manifest grid metadata does not match the pinned contest grid")
    unreachable = manifest.get("repos_unreachable_or_missing")
    if not isinstance(unreachable, list) or unreachable:
        raise RuntimeError("registry scan is incomplete: one or more source repositories were unavailable")
    indexed_shas = [entry.get("sha256") if isinstance(entry, dict) else None for entry in entries]
    if (any(not isinstance(value, str) or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value) for value in indexed_shas)
            or len(set(indexed_shas)) != expected):
        raise RuntimeError(f"registry manifest does not contain {expected} distinct valid SHA256 entries")
    paths: list[Path] = []
    problems: list[str] = []
    for entry in entries:
        raw = entry.get("cache_file")
        expected_sha = entry.get("sha256")
        path = Path(raw) if raw else Path()
        if raw and not path.is_absolute():
            path = ROOT / path
        if not raw or not expected_sha or not path.is_file():
            problems.append(f"missing cache: {raw or '<no path>'}")
            continue
        got = sha256_file(path)
        if got != expected_sha:
            problems.append(f"sha256 mismatch: {path}")
            continue
        try:
            with rasterio.open(path) as source:
                aligned = (
                    source.count == 1
                    and (source.height, source.width) == gridmod.SHAPE
                    and source.crs is not None
                    and source.crs.to_epsg() == gridmod.EPSG
                    and tuple(source.transform)[:6] == tuple(gridmod.TRANSFORM)[:6]
                )
            if not aligned:
                problems.append(f"grid mismatch: {path}")
                continue
        except Exception as exc:
            problems.append(f"unreadable raster: {path} ({type(exc).__name__}: {str(exc)[:100]})")
            continue
        paths.append(path)
    if problems or len(paths) != expected:
        preview = "; ".join(problems[:8])
        more = "" if len(problems) <= 8 else f"; and {len(problems) - 8} more"
        raise RuntimeError(
            f"full-registry uniqueness cannot be verified ({len(paths)}/{expected} files verified): "
            f"{preview}{more}. No fit or GeoTIFF was produced."
        )
    return paths, manifest


def _safe_evidence_path(raw: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValueError("clearance must name a versioned CV evidence file")
    path = (ROOT / raw).resolve()
    try:
        path.relative_to((ROOT / "evidence").resolve())
    except ValueError as exc:
        raise ValueError("CV evidence path must remain inside this repository's evidence directory") from exc
    if not path.is_file():
        raise FileNotFoundError(f"CV evidence is missing: {raw}")
    return path


def load_clearance(path: Path | None = None) -> tuple[dict, dict, dict]:
    """Validate the independent selector receipt, current CV evidence and hashes.

    `slot_promotion` must remain false here: this command only stages a locally
    validated artifact. Weekly-slot selection/organizer submission is separate.
    """
    path = Path(path or (EVID / "submission_clearance.json")).resolve()
    try:
        path.relative_to(EVID.resolve())
    except ValueError as exc:
        raise ValueError("clearance receipt must be stored inside evidence/") from exc
    if not path.is_file():
        raise RuntimeError(
            f"HOLD: no submission-clearance receipt at {path}; no model fit, download artifact, or submission"
        )
    clearance = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "schema", "decision", "candidate_id", "evidence_path", "evidence_sha256",
        "evaluator_version", "evaluator_implementation_sha256", "evaluator_input_sha256",
        "build_implementation_sha256", "registry_index_sha256", "mode", "variant",
        "live_dot_budget", "k_truth",
        "floor", "flank_px", "selector_note", "slot_promotion",
    }
    missing = sorted(required - set(clearance))
    if missing:
        raise ValueError(f"clearance receipt is missing required fields: {missing}")
    if clearance["schema"] != CLEARANCE_SCHEMA:
        raise ValueError("unknown clearance schema; refusing to build")
    if clearance["decision"] != "CLEAR_FOR_LOCAL_CANDIDATE_BUILD":
        raise ValueError("selector did not clear the candidate for local build")
    if clearance["candidate_id"] != CANDIDATE_ID:
        raise ValueError("clearance applies to a different candidate")
    if clearance["slot_promotion"] is not False:
        raise ValueError("slot promotion must be a separate decision; this builder cannot promote")
    if clearance["evaluator_version"] != CV_VERSION:
        raise ValueError("clearance does not use the current spatial-CV evaluator version")
    expected_cv_hashes = cv_implementation_hashes()
    if clearance["evaluator_implementation_sha256"] != expected_cv_hashes:
        raise ValueError("clearance spatial-CV source hashes do not match current code")
    expected_input_hashes = cv_input_hashes()
    if clearance["evaluator_input_sha256"] != expected_input_hashes:
        raise ValueError("clearance spatial-CV input hashes do not match current grid data")
    if clearance["build_implementation_sha256"] != build_implementation_hashes():
        raise ValueError("clearance builder/writer source hashes do not match current code")
    registry_index = (EVID / "registry_full_index.json").resolve()
    if not registry_index.is_file():
        raise FileNotFoundError(f"full-registry index is missing: {registry_index}")
    if clearance["registry_index_sha256"] != sha256_file(registry_index):
        raise ValueError("clearance registry-index SHA256 does not match the pinned full inventory")

    cv_path = _safe_evidence_path(clearance["evidence_path"])
    if sha256_file(cv_path) != clearance["evidence_sha256"]:
        raise ValueError("CV evidence SHA256 does not match the selector receipt")
    evidence = json.loads(cv_path.read_text(encoding="utf-8"))
    if evidence.get("evidence_class") != "HOLDOUT-DTI":
        raise ValueError("referenced evidence is not classified HOLDOUT-DTI")
    if evidence.get("evaluator_version") != CV_VERSION:
        raise ValueError("referenced CV evidence has a stale or missing evaluator version")
    if evidence.get("evaluator_implementation_sha256") != expected_cv_hashes:
        raise ValueError("referenced CV evidence has mismatched evaluator source hashes")
    if evidence.get("evaluator_input_sha256") != expected_input_hashes:
        raise ValueError("referenced CV evidence has mismatched evaluator input hashes")
    if clearance["mode"] not in ("all", "detached") or clearance["mode"] != evidence.get("mode"):
        raise ValueError("clearance mode does not match a supported referenced CV run")
    evidence_floor = evidence.get("floor")
    receipt_floor = clearance.get("floor")
    if (isinstance(evidence_floor, bool) or not isinstance(evidence_floor, (int, float))
            or not np.isfinite(evidence_floor)
            or isinstance(receipt_floor, bool) or not isinstance(receipt_floor, (int, float))
            or not np.isfinite(receipt_floor)
            or not np.isclose(float(receipt_floor), float(evidence_floor), rtol=0.0, atol=0.0)):
        raise ValueError("emission floor differs from the referenced spatial-CV run")
    if (not isinstance(evidence.get("max_dots"), int)
            or isinstance(evidence["max_dots"], bool) or evidence["max_dots"] <= 0):
        raise ValueError("referenced spatial-CV run lacks a valid dot budget")
    variant = clearance["variant"]
    if (not isinstance(variant, str) or variant not in FEATURE_VARIANTS
            or variant not in evidence.get("variants", {})):
        raise ValueError(f"unsupported/unmeasured feature variant: {variant}")
    if not isinstance(clearance["selector_note"], str) or not clearance["selector_note"].strip():
        raise ValueError("selector_note must document the independent promotion rationale")

    # Any single-feature canary >0.90 is leakage until disproven. Require all
    # declared anatomy features to have four finite fold measurements; a missing,
    # malformed, or internally inconsistent canary is a HOLD, not a pass.
    canary = evidence.get("canary")
    if not isinstance(canary, dict) or not canary:
        raise ValueError("versioned leakage canary is missing")
    missing_canary = sorted(set(FEATURES) - set(canary))
    if missing_canary:
        raise ValueError(f"single-feature leakage canary is incomplete: {missing_canary}")
    flagged = []
    for feature in FEATURES:
        result = canary[feature]
        if not isinstance(result, dict):
            raise ValueError(f"leakage canary for {feature} is malformed")
        fold_auc = result.get("auc_per_fold")
        if (not isinstance(fold_auc, list) or len(fold_auc) != 4
                or any(isinstance(value, bool) or not isinstance(value, (int, float))
                       or not np.isfinite(value) or not 0.0 <= value <= 1.0
                       for value in fold_auc)):
            raise ValueError(f"leakage canary for {feature} lacks four finite fold AUCs")
        discriminative = [max(float(value), 1.0 - float(value)) for value in fold_auc]
        measured_max = max(discriminative)
        recorded_max = result.get("discriminative_auc_max")
        if (isinstance(recorded_max, bool) or not isinstance(recorded_max, (int, float))
                or not np.isfinite(recorded_max)
                or not np.isclose(float(recorded_max), measured_max, rtol=0.0, atol=1e-12)):
            raise ValueError(f"leakage canary for {feature} has an inconsistent AUC summary")
        expected_flag = measured_max > 0.90
        if not isinstance(result.get("leakage_flag"), bool) or result["leakage_flag"] != expected_flag:
            raise ValueError(f"leakage canary for {feature} has an inconsistent leakage flag")
        if expected_flag:
            flagged.append(feature)
    if flagged:
        raise ValueError(f"single-feature leakage canary did not clear: {flagged}")

    variant_result = evidence["variants"][variant]
    if not isinstance(variant_result, dict) or not isinstance(variant_result.get("pooled"), dict):
        raise ValueError("referenced feature variant lacks a pooled holdout result")
    pooled = variant_result["pooled"]
    raw_dti = pooled.get("pooled_dti")
    if (isinstance(raw_dti, bool) or not isinstance(raw_dti, (int, float))
            or not np.isfinite(raw_dti) or not 0.0 <= raw_dti <= 1.0):
        raise ValueError("holdout DTI must be finite and in [0,1]")
    dti = float(raw_dti)
    ci = pooled.get("dti_ci95_quadrant_jackknife")
    raw_n_truth = pooled.get("n_truth")
    if (not isinstance(raw_n_truth, int) or isinstance(raw_n_truth, bool)
            or raw_n_truth <= 0):
        raise ValueError("withheld-positive count must be a positive integer")
    n_truth = raw_n_truth
    if (not isinstance(ci, list) or len(ci) != 2
            or any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not np.isfinite(value) for value in ci)
            or ci[0] > ci[1] or ci[0] < 0.0 or ci[1] > 1.0):
        raise ValueError("holdout CI or withheld-positive count is invalid")
    recorded_truth = evidence.get("withheld_positive_pixels")
    if (not isinstance(recorded_truth, int) or isinstance(recorded_truth, bool)
            or recorded_truth != n_truth):
        raise ValueError("withheld-positive count is inconsistent with pooled CV evidence")

    budget = clearance["live_dot_budget"]
    k_truth = clearance["k_truth"]
    floor = clearance["floor"]
    flank = clearance["flank_px"]
    if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
        raise ValueError("live_dot_budget must be a positive integer")
    cv_max_dots = evidence.get("max_dots")
    if not isinstance(cv_max_dots, int) or isinstance(cv_max_dots, bool) or cv_max_dots <= 0:
        raise ValueError("referenced spatial-CV evidence lacks a valid max_dots cap")
    if budget > 4 * cv_max_dots:
        raise ValueError("live dot budget exceeds four times spatial CV's per-cell max_dots cap")
    if (isinstance(k_truth, bool) or not isinstance(k_truth, (int, float))
            or not np.isfinite(k_truth) or k_truth <= 0):
        raise ValueError("k_truth must be finite and positive")
    if (isinstance(floor, bool) or not isinstance(floor, (int, float))
            or not np.isfinite(floor) or floor < 0):
        raise ValueError("floor must be finite and nonnegative")
    # run_cv validates no flank exclusion; do not promote an untested nonzero flank.
    if not isinstance(flank, int) or isinstance(flank, bool) or flank != 0:
        raise ValueError("this evaluator did not validate a nonzero flank exclusion")
    clearance["holdout_summary"] = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": CV_VERSION,
        "variant": variant,
        "pooled_dti": dti,
        "ci95_quadrant_jackknife": ci,
        "withheld_positive_pixels": n_truth,
    }
    return clearance, evidence, pooled


def _require_clear_gate(report: dict, label: str) -> None:
    if not report.get("ok") or report.get("error_count", 0):
        raise RuntimeError(
            f"{label} uniqueness gate did not clear: duplicate={report.get('duplicate')}, "
            f"offenders={report.get('offender_count')}, errors={report.get('error_count')}"
        )


def _topk_preview(surface: np.ndarray, allowed: np.ndarray, budget: int) -> np.ndarray:
    """Deterministic dot proposal for the required before-placement comparison."""
    raw = np.asarray(surface)
    mask = np.asarray(allowed, dtype=bool)
    if raw.shape != mask.shape or raw.ndim != 2:
        raise ValueError("surface and allowed mask must share a 2-D grid")
    numeric = np.issubdtype(raw.dtype, np.number) or np.issubdtype(raw.dtype, np.bool_)
    if not numeric or np.iscomplexobj(raw):
        raise ValueError("pre-placement surface must be a real numeric array")
    if not np.isfinite(raw).all() or (raw < 0).any() or (raw > 1).any():
        raise ValueError("pre-placement surface must be finite and in [0,1]")
    candidate = raw.astype(np.float32, copy=False)
    if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
        raise ValueError("pre-placement budget must be a positive integer")
    idx = np.flatnonzero(mask.ravel())
    count = min(budget, idx.size)
    if count == 0:
        raise ValueError("pre-placement mask has no allowed pixels")
    scores = candidate.ravel()[idx]
    cutoff = np.partition(scores, scores.size - count)[scores.size - count]
    above = idx[scores > cutoff]
    tied = idx[scores == cutoff]  # idx is row-major, so ties have a stable pixel order
    chosen = np.concatenate((above, tied[:count - above.size]))
    preview = np.zeros(candidate.shape, dtype=np.float32)
    preview.ravel()[chosen] = 1.0
    return preview


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clearance", type=Path, default=EVID / "submission_clearance.json",
                        help="independent selector receipt; missing/stale receipt fails closed")
    parser.add_argument("--tag", default="fault-zone-anatomy")
    args = parser.parse_args()

    # Both authorization and inventory checks happen before any model fit.
    clearance, cv_evidence, pooled = load_clearance(args.clearance)
    registry_index = EVID / "registry_full_index.json"
    registry_paths, _registry_manifest = load_complete_registry(registry_index)
    print(f"clearance verified: {clearance['candidate_id']} / {clearance['variant']}; "
          f"full registry verified: {len(registry_paths)} rasters")

    t0 = time.time()
    grid = gridmod.load_grid()
    ctx = build_holdout(grid)
    cells = ctx.cells_of(clearance["mode"])
    if not cells:
        raise RuntimeError("clearance mode has no training cells")
    cols = FEATURE_VARIANTS[clearance["variant"]]

    geoms = [cell_geometry(ctx, cell) for cell in cells]
    model, scale, base_rate = fit_model(geoms, seed=0, cols=cols)
    geoms.clear()
    gc.collect()

    # Build the single selected candidate; no parameter sweep or score optimization.
    from gems57.anatomy import fold_geometry
    domain = grid.footprint & ~grid.catalogue
    geometry = fold_geometry(grid, grid.catalogue, np.zeros(grid.shape, bool),
                             domain, "live_full_catalogue")
    x = geometry.X[:, cols] if cols is not None else geometry.X
    surface_values = model.predict_proba(x)[:, 1].astype(np.float32) * np.float32(scale)
    if (not np.isfinite(surface_values).all() or (surface_values < 0.0).any()
            or (surface_values > 1.0).any()):
        raise ValueError("calibrated surface is non-finite or outside [0,1]; refusing silent clipping")
    surface = np.zeros(grid.shape, dtype=np.float32)
    surface[geometry.rows, geometry.cols] = surface_values
    allowed = domain.copy()
    if clearance["flank_px"] > 0:
        distance = ndi.distance_transform_edt(~grid.catalogue)
        allowed &= distance > clearance["flank_px"]
    if not allowed.any():
        raise RuntimeError("selected placement mask is empty")

    sample = gridmod.DATA_DIR / "sample_submission.tif"
    surface_gate = gates.lane_uniqueness_report(
        surface, grid.footprint, registry_paths, sample=sample, phase="surface")
    _require_clear_gate(surface_gate, "continuous surface")

    preview = _topk_preview(surface, allowed, clearance["live_dot_budget"])
    preplacement_gate = gates.lane_uniqueness_report(
        preview, grid.footprint, registry_paths, sample=sample, phase="dots")
    _require_clear_gate(preplacement_gate, "pre-placement dots")

    allocation = greedy_allocate(
        surface, allowed, k_truth=float(clearance["k_truth"]),
        floor=float(clearance["floor"]), max_dots=int(clearance["live_dot_budget"]))
    if allocation.n_dots <= 0:
        raise RuntimeError("selected configuration emitted no dots")
    values = allocation.emitted.astype(np.float32)
    final_gate = gates.lane_uniqueness_report(
        values, grid.footprint, registry_paths, sample=sample, phase="dots")
    _require_clear_gate(final_gate, "final dots")

    # Nothing is created in docs/downloads until independent holdout clearance,
    # complete registry inventory, and all three before/final uniqueness gates pass.
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raster_sha = hashlib.sha256(values.tobytes()).hexdigest()
    short = raster_sha[:12]
    safe_tag = re.sub(r"[^A-Za-z0-9._-]+", "-", args.tag).strip("._-")[:48]
    if not safe_tag:
        raise ValueError("tag must contain at least one filename-safe character")
    name = f"gems57-{safe_tag}-{clearance['mode']}-{stamp}-{short}"
    note = (f"57GEMSDOE fault-zone anatomy | {clearance['variant']} spatial holdout | "
            f"{allocation.n_dots} dots | {short}")
    if len(name) > 140 or len(note) > 140:
        raise ValueError("submission name or note exceeds the 140-character limit")

    metadata = {
        "candidate_id": CANDIDATE_ID,
        "clearance_schema": CLEARANCE_SCHEMA,
        "clearance_receipt_sha256": sha256_file(args.clearance),
        "holdout": clearance["holdout_summary"],
        "registry_index_sha256": sha256_file(registry_index),
        "registry_rasters_verified": len(registry_paths),
        "uniqueness_scope": "all supplied indexed matching-grid rasters only; not private/unlinked submissions",
        "slot_promotion": False,
    }
    target = DL / f"{name}.tif"
    writer_receipt = write_submission(
        target, values, sample, grid.footprint, note=note, name=name,
        catalogue=grid.catalogue, metadata=metadata)
    try:
        on_disk = validate(target, grid.footprint, grid.catalogue)
        assert_submittable(on_disk)
        with rasterio.open(target) as source:
            disk_values = source.read(1)
        if not np.array_equal(disk_values, values):
            raise IOError("written GeoTIFF values differ from the uniqueness-checked final dots")
    except Exception:
        for candidate in (target, target.with_suffix(".zip"), target.with_suffix(".json")):
            candidate.unlink(missing_ok=True)
        raise

    audit = {
        "evidence_class": "HOLDOUT-DTI",
        "candidate_id": CANDIDATE_ID,
        "evaluator_version": CV_VERSION,
        "evaluator_implementation_sha256": cv_evidence["evaluator_implementation_sha256"],
        "evaluator_input_sha256": cv_evidence["evaluator_input_sha256"],
        "holdout": clearance["holdout_summary"],
        "selector_note": clearance["selector_note"],
        "features": [FEATURES[i] for i in cols],
        "mode": clearance["mode"],
        "live_dot_budget": clearance["live_dot_budget"],
        "emitted_pixels": int(allocation.n_dots),
        "model_calibration": {"scale": float(scale), "base_rate": float(base_rate)},
        "registry_index_sha256": sha256_file(registry_index),
        "registry_rasters_verified": len(registry_paths),
        "uniqueness": {
            "surface": surface_gate,
            "preplacement_dots": preplacement_gate,
            "final_dots": final_gate,
        },
        "validator": on_disk,
        "writer_receipt": writer_receipt,
        "raster_sha256": on_disk["sha256"],
        "submission_name": name,
        "submission_note": note,
        "download_status": "LOCALLY CLEARED WITHIN THE RECORDED INVENTORY; organizer acceptance is not established",
        "weekly_slot_status": "NOT PROMOTED; separate selector decision required",
        "promote": False,
        "runtime_s": time.time() - t0,
    }
    EVID.mkdir(exist_ok=True)
    audit_path = EVID / f"submission_build_{name}.json"
    try:
        audit_path.write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except Exception:
        for candidate in (target, target.with_suffix(".zip"), target.with_suffix(".json")):
            candidate.unlink(missing_ok=True)
        raise
    print(f"LOCAL DOWNLOAD CLEARANCE: {target}")
    print(f"WEEKLY SLOT: NOT PROMOTED (separate decision required)")
    print(f"SHA256: {on_disk['sha256']}")
    print(f"HOLDOUT-DTI {pooled['pooled_dti']:.6f} "
          f"95% CI {clearance['holdout_summary']['ci95_quadrant_jackknife']} "
          f"({clearance['holdout_summary']['withheld_positive_pixels']} positives)")
    print(f"wrote {audit_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
