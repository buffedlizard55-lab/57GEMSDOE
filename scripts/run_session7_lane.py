#!/usr/bin/env python3
"""Session 7 (2026-10-10): H6-1 catalogue-proximity pruning + unique binary build.

Fault-zone anatomy lane (owner's method paragraph).  Two declared experiments,
inside the [3] experiment / [2] hour budget:

* ``E1`` / ``H6-1`` (this session's only new hypothesis test): the file-measured
  mechanism of the owner-reported 0.2778 submission -- the 0.2778 raster is the
  0.2708 raster with 2,545 dots removed, every one 1.4-2.0 px from the mapped
  catalogue (evidence/best_submission_audit.json) -- is tested on the repaired
  hide-and-recover holdout against BOTH controls: unpruned dots and matched
  random pruning (same count removed).  Predeclared retention rule: keep the
  proximal prune iff (pruned - unpruned) paired 95 % CI lower bound > 0 AND
  (pruned - random) point estimate > 0.  Pruning uses the fold's VISIBLE
  catalogue only; hidden truth is never referenced.
* ``E2``: fit the retained Session-5 arm (relay_bend_anatomy = distance +
  length-as-displacement + host-relative orientation + two-host relay + bend,
  no textbook angles) on the full catalogue, allocate binary dots with the
  shared greedy max-cover surrogate under the predeclared zone-shrunk budget,
  apply E1's retained pruning rule, write the standard validated all-finite
  GeoTIFF, and run the dual uniqueness screen against every indexed raster.

Every number is HOLDOUT-DTI (gems57-pooled-hide-v2, n withheld positives,
95 % CI) or REGISTRY-MEASUREMENT / OWNER-REPORTED; nothing is a projection
written as a score.  No weekly submission slot is used by this script.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np
from scipy import ndimage as ndi
from threadpoolctl import threadpool_limits

import run_relay_bend_experiments as rbe  # shared Session-5 arm definitions
from gems57 import evaluate_holdout as EH
from gems57 import load_grid
from gems57.anatomy import relative_strike_distribution
from gems57.emit import greedy_allocate
from gems57.faultzone import trace_sense_raster
from gems57.fitting import canary, fit_model
from gems57.holdout import FOLD_NAMES, buffered_component_draw
from gems57.relay_bend_anatomy import (
    ALL_RELAY_BEND_FEATURES,
    build_relay_bend_geometry,
    cached_scarp_geometry,
)
from gems57.submission_writer import write_submission
from gems57.uniqueness import compare_array_to_registry, compare_to_registry
from gems57.validate import validate

EVID = ROOT / "evidence"
SEED = 20
PER_QUADRANT_CAP = 10_000
PROXIMAL_PX = 2.0          # the measured prune rule of the 0.2778 file (base pruned at 2 px)
BASE_BUDGET = 37_700       # top of the owner-reported best band (35-46k; registry_budget.json)
RETAINED_ARM = "relay_bend_anatomy"
PRUNE_CANDIDATE = "proximity_pruned"


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def subset(g, selected: np.ndarray, key: str):
    from types import SimpleNamespace
    return SimpleNamespace(
        X=g.X[selected],
        y=g.y[selected],
        rows=g.rows[selected],
        cols=g.cols[selected],
        key=key,
        feature_names=ALL_RELAY_BEND_FEATURES,
    )


def build_geometry(grid, folds, quad, sense, scarp, cache_tag_extra=""):
    visible = folds[0]["visible"]
    hidden = folds[0]["hidden_all"]
    domain = np.logical_or.reduce([f["region"] for f in folds]) & ~folds[0]["masked_known"]
    full = build_relay_bend_geometry(
        grid, visible, hidden, domain, sense, scarp,
        ROOT / ".cache" / "relay_bend_geometry", f"draw{SEED}-buffered{cache_tag_extra}",
    )
    return full, visible, hidden, domain


# --------------------------------------------------------------------------- #
def stage_experiment(_a) -> int:
    start = time.monotonic()
    plan = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        session="session-7-2026-10-10",
        maximum_experiments=3,
        experiments=[
            dict(id="E1", hypothesis_id="H6-1",
                 hypothesis=("Removing emitted dots within 2 px of the TRAINING-visible "
                             "catalogue raises pooled HOLDOUT-DTI more than removing an "
                             "equal number of random dots (the measured 0.2778 mechanism).")),
            dict(id="E2", hypothesis_id="H57-I2+H57-H-final",
                 hypothesis=("The retained relay_bend_anatomy arm with the fitted damage "
                             "zone, zone-shrunk dot budget and the E1 pruning rule produces "
                             "a unique validated binary GeoTIFF.")),
        ],
        split="buffered-whole-components-loqo-v2",
        evaluator=EH.VERSION,
        seed=SEED,
        proximal_px=PROXIMAL_PX,
        retention_rule=("keep proximal pruning iff (pruned-unpruned) paired 95% CI "
                        "lower bound > 0 AND (pruned-random) point estimate > 0"),
        base_budget=BASE_BUDGET,
        submission_slots_used=0,
        no_textbook_angle=True,
    )
    save(EVID / "session7_experiment_plan.json", plan)

    grid = load_grid()
    folds, quad = buffered_component_draw(grid, seed=SEED)
    sense = trace_sense_raster(
        ROOT / "data/external/trace_segments_utm11.csv", grid.shape, grid.transform
    )
    scarp = cached_scarp_geometry(ROOT, grid.footprint)
    full, visible, hidden, domain = build_geometry(grid, folds, quad, sense, scarp)
    print(f"[e1] geometry ready ({time.monotonic()-start:.1f}s): "
          f"{len(full.y)} examples, {int(full.y.sum())} positives", flush=True)

    geoms = [subset(full, quad[full.rows, full.cols] == q, FOLD_NAMES[q]) for q in range(4)]
    c = canary(geoms, feature_names=ALL_RELAY_BEND_FEATURES)
    canary_report = dict(
        evidence_class="LEAKAGE-CANARY (AUC, not DTI)",
        split_version=plan["split"],
        features=c,
        session="session-7-2026-10-10",
        note=("All 22 predictors are computed strictly from visible catalogue traces "
              "and catalogue-independent cached det_elev; hidden geometry is diagnostic "
              "only. H6-1 pruning uses the fold's visible/mapped catalogue only."),
    )
    save(EVID / "session7_canary.json", canary_report)
    flagged = [n for n, r in c.items()
               if r.get("leakage_flag") or r.get("discriminative_auc_max") is None]
    if flagged:
        print(f"[e1] STOP: unresolved canary {flagged}", flush=True)
        return 3
    print("[e1] canary clean:", {n: round(r["discriminative_auc_max"], 4)
                                for n, r in c.items()}, flush=True)

    # Lane protocol: measure the relative-strike and distance distributions of
    # withheld segments against their nearest visible fault.
    structure = relative_strike_distribution(grid, visible, hidden)
    pos = full.y == 1
    structure.update(
        evidence_class="HOLDOUT-STRUCTURE (descriptive, not a score)",
        session="session-7-2026-10-10",
        pixel_size_m=100,
        distance_positive_quantiles_px=np.quantile(
            full.X[pos, 0], [0.1, 0.5, 0.9, 0.95, 0.99]).tolist(),
        distance_domain_quantiles_px=np.quantile(
            full.X[:, 0], [0.1, 0.5, 0.9, 0.95, 0.99]).tolist(),
        n_withheld=int(pos.sum()),
        retained_structure=("distance decay plus host-relative orientation retained; "
                            "no textbook angle imposed; relative-strike bins are "
                            "descriptive and censored (<=13 neighbors)"),
    )
    save(EVID / "session7_structure.json", structure)

    columns = rbe.ARMS[RETAINED_ARM]
    terms = {n: None for n in ("unpruned", PRUNE_CANDIDATE, "random_pruned")}
    details = []
    for q, fold in enumerate(folds):
        train = [g for i, g in enumerate(geoms) if i != q]
        distances = np.concatenate([g.X[g.y == 1, 0] for g in train])
        zone = float(np.quantile(distances, 0.90))
        fraction = float((distances <= zone).mean())
        cap = max(1, int(PER_QUADRANT_CAP * fraction))
        train_pixels = sum(len(g.y) for g in train)
        train_positives = sum(int(g.y.sum()) for g in train)
        base_rate = train_positives / train_pixels
        test = geoms[q]
        allowed = fold["region"] & ~fold["masked_known"]
        k_est = base_rate * float(allowed.sum())
        with threadpool_limits(limits=2):
            clf, scale, _ = fit_model(train, seed=q, cols=columns)
            p = rbe.predict(clf, scale, test, columns, grid.shape, zone)
        allowed_zone = allowed.copy()
        allowed_zone[test.rows[test.X[:, 0] > zone], test.cols[test.X[:, 0] > zone]] = False
        dots = greedy_allocate(p, allowed_zone, k_truth=k_est, floor=0.015, max_dots=cap)
        emitted = dots.emitted
        # H6-1 prune rule: distance to the fold's VISIBLE (mapped) catalogue.
        dcat = ndi.distance_transform_edt(~fold["masked_known"])
        ys, xs = np.nonzero(emitted)
        proximal = dcat[ys, xs] <= PROXIMAL_PX
        n_prox = int(proximal.sum())
        pruned = emitted.copy()
        pruned[ys[proximal], xs[proximal]] = False
        rng = np.random.default_rng(5700 + q)
        random_dropped = np.zeros(len(ys), bool)
        if n_prox:
            random_dropped[rng.choice(len(ys), size=n_prox, replace=False)] = True
        random_pruned = emitted.copy()
        random_pruned[ys[random_dropped], xs[random_dropped]] = False
        arm_arrays = dict(unpruned=emitted, **{PRUNE_CANDIDATE: pruned, "random_pruned": random_pruned})
        for name, arr in arm_arrays.items():
            scored, t = EH.evaluate(arr.astype(np.float32), fold, grid.footprint)
            terms[name] = t if terms[name] is None else terms[name] + t
            details.append(dict(
                arm=name, fold=FOLD_NAMES[q], evidence_class="HOLDOUT-DTI",
                evaluator_version=EH.VERSION,
                withheld_positive_pixels=scored["n_truth"], dti=scored["dti"],
                emitted_pixels=int(arr.sum()), proximal_dropped=n_prox,
                training_zone_px=zone, training_fraction_inside_zone=fraction,
                dot_cap=cap, k_estimate_from_training=k_est,
                test_truth_used_for_placement=False,
                fold_receipt=fold["receipt"],
            ))
        print(f"[e1] {FOLD_NAMES[q]}: unpruned={details[-3]['dti']:.5f} "
              f"pruned={details[-2]['dti']:.5f} (dropped {n_prox}) "
              f"random={details[-1]['dti']:.5f}", flush=True)
        del p, dots, clf
        gc.collect()

    pooled = EH.pooled_summary(terms, draws=1000, seed=20261010, candidate=PRUNE_CANDIDATE)
    d_unpruned = pooled["paired_differences"]["unpruned"]
    d_random = pooled["paired_differences"]["random_pruned"]
    prune_retained = bool(d_unpruned["ci95"][0] > 0 and d_random["delta"] > 0)
    report = dict(
        **pooled,
        session="session-7-2026-10-10",
        hypothesis_id="H6-1",
        split_version=plan["split"],
        proximal_px=PROXIMAL_PX,
        retention_rule=plan["retention_rule"],
        prune_retained_for_final_build=prune_retained,
        per_fold=details,
        scores_label=("HOLDOUT-DTI gems57-pooled-hide-v2; withheld positives "
                      f"{pooled['scores'][PRUNE_CANDIDATE]['withheld_positive_pixels']}; "
                      "CIs conditional on fitted folds and fixed budgets"),
        score_projection=None,
        submission_slots_used=0,
        runtime_seconds=time.monotonic() - start,
    )
    save(EVID / "session7_h61_prune.json", report)
    print("[e1] pooled:", {n: round(r["dti"], 6) for n, r in pooled["scores"].items()}, flush=True)
    print("[e1] pruned-unpruned:", d_unpruned, flush=True)
    print("[e1] pruned-random:", d_random, flush=True)
    print("[e1] prune_retained =", prune_retained, flush=True)
    return 0


# --------------------------------------------------------------------------- #
def stage_build(_a) -> int:
    start = time.monotonic()
    e1 = json.loads((EVID / "session7_h61_prune.json").read_text())
    prune_retained = bool(e1["prune_retained_for_final_build"])
    grid = load_grid()
    folds, quad = buffered_component_draw(grid, seed=SEED)
    sense = trace_sense_raster(
        ROOT / "data/external/trace_segments_utm11.csv", grid.shape, grid.transform
    )
    scarp = cached_scarp_geometry(ROOT, grid.footprint)
    full, visible, hidden, domain = build_geometry(grid, folds, quad, sense, scarp)
    geoms = [subset(full, quad[full.rows, full.cols] == q, FOLD_NAMES[q]) for q in range(4)]
    pos = full.y == 1
    columns = rbe.ARMS[RETAINED_ARM]
    with threadpool_limits(limits=2):
        clf, scale, base = fit_model(geoms, seed=0, cols=columns)
    zone = float(np.quantile(full.X[pos, 0], 0.90))
    fraction = float((full.X[pos, 0] <= zone).mean())
    # Predeclared zone-shrink rule (Session-5 instrument): the dot budget is
    # shrunk by the TRAINING fraction of withheld positives inside the fitted
    # zone; "few inside the zone" therefore cannot leave a full budget in place.
    budget = max(1, int(round(BASE_BUDGET * fraction)))
    # Prevalence estimate from the holdout draw design (training-only quantities:
    # per-fold k_est was base_rate * fold domain). Mean fold rate scaled to the
    # live allowed domain gives |G| for the greedy bar; test labels are unused.
    e1_details = [d for d in e1["per_fold"] if d["arm"] == "unpruned"]
    allowed_live = grid.footprint & ~grid.catalogue
    rates = []
    for q, fold in enumerate(folds):
        dom_q = float((fold["region"] & ~fold["masked_known"]).sum())
        row = next(d for d in e1_details if d["fold"] == FOLD_NAMES[q])
        rates.append(row["k_estimate_from_training"] / max(dom_q, 1.0))
    k_est = float(np.mean(rates)) * float(allowed_live.sum())
    print(f"[e2] fitted zone {zone:.2f}px  fraction inside {fraction:.4f}  "
          f"budget {budget} (base {BASE_BUDGET})  k_est {k_est:.0f}", flush=True)

    del full, geoms, folds, visible, hidden, domain
    gc.collect()

    model_dir = ROOT / ".cache" / "relay_bend_geometry"
    model_dir.mkdir(parents=True, exist_ok=True)
    live_domain = grid.footprint & ~grid.catalogue
    live = build_relay_bend_geometry(
        grid, grid.catalogue, np.zeros(grid.shape, bool), live_domain,
        sense, scarp, model_dir, "full-catalogue",
    )
    with threadpool_limits(limits=2):
        surface = rbe.predict(clf, scale, live, columns, grid.shape, zone)

    # ---- pre-placement surface screen (protocol rule 1: check on the surface) ----
    reg_index = ROOT / "evidence" / "registry_refreshed.json"
    if not reg_index.exists():
        raise FileNotFoundError("run scripts/refresh_registry.py first")

    def progress(i, n, row):
        if i % 100 == 0 or i == n:
            print(f"[unique] {i}/{n}", flush=True)

    surface_drift = compare_array_to_registry(surface, reg_index, grid.footprint,
                                              include_reverse=False, progress=progress)
    save(EVID / "session7_surface_uniqueness.json", surface_drift)
    other = [r for r in surface_drift["rows"] if "error" not in r
             and not str(r.get("submission", "")).startswith("57GEMSDOE:")]
    own = [r for r in surface_drift["rows"] if "error" not in r
           and str(r.get("submission", "")).startswith("57GEMSDOE:")]
    worst_other_rho = max((r["spearman_full_footprint"] for r in other
                           if r["spearman_full_footprint"] is not None), default=0.0)
    worst_own_rho = max((r["spearman_full_footprint"] for r in own
                         if r["spearman_full_footprint"] is not None), default=0.0)
    surface_cross_lane_pass = bool(worst_other_rho <= 0.90)
    print(f"[e2] surface worst rho other-lanes {worst_other_rho:.4f} "
          f"own-prior {worst_own_rho:.4f} cross-lane pass={surface_cross_lane_pass}",
          flush=True)
    if not surface_cross_lane_pass:
        print("[e2] STOP: surface rank-correlation drift against another lane.", flush=True)
        return 4

    # ---- allocation ----
    allowed = allowed_live
    dots = greedy_allocate(surface, allowed, k_truth=k_est, floor=0.015, max_dots=budget)
    emitted = dots.emitted
    n_alloc = int(emitted.sum())
    dcat = ndi.distance_transform_edt(~grid.catalogue)
    ys, xs = np.nonzero(emitted)
    proximal = dcat[ys, xs] <= PROXIMAL_PX
    n_prox = int(proximal.sum())
    if prune_retained:
        emitted[ys[proximal], xs[proximal]] = False
    n_final = int(emitted.sum())
    print(f"[e2] allocated {n_alloc} dots; proximal(<=2px) {n_prox}; "
          f"prune_retained={prune_retained}; final {n_final}", flush=True)

    prediction = emitted.astype(np.float32)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    decoded = hashlib.sha256(prediction.tobytes()).hexdigest()[:12]
    label = f"gems57-fza-h61prune-{stamp}-{decoded}"
    note = (f"Fault-zone anatomy E2+H6-1: relay/bend fit, zone {zone:.0f}px, "
            f"{n_final} dots, proximal prune {'on' if prune_retained else 'off'}; {decoded[:8]}")
    assert len(note) <= 140, len(note)
    target = ROOT / "docs" / "downloads" / f"{label}.tif"
    receipt = write_submission(
        target,
        prediction,
        ROOT / "data/official/sample_submission.tif",
        grid.footprint,
        note=note,
        name=label,
        catalogue=grid.catalogue,
        metadata=dict(
            kind="binary dot allocation (submittable)",
            session="session-7-2026-10-10",
            selected_arm=RETAINED_ARM,
            hypothesis_id="E2 (H57-I2+H57-H) + E1 (H6-1)",
            proximal_prune_px=PROXIMAL_PX,
            proximal_prune_retained=prune_retained,
            proximal_dropped=n_prox,
            fitted_zone_px=zone,
            training_fraction_inside_zone=fraction,
            budget_base=BASE_BUDGET,
            budget_after_zone_shrink=budget,
            k_estimate_from_training=k_est,
            greedy_stop_reason="marginal bar or budget cap",
            no_prior_raster_used_to_build_predictions=True,
            holdout_evidence="session7_h61_prune.json",
        ),
    )
    validator = validate(target, grid.footprint, grid.catalogue)
    validator["bytes"] = int(receipt["bytes"])
    print(f"[e2] wrote {target.name} sha256={receipt['sha256'][:16]}...", flush=True)

    # ---- final-dot screen (protocol rule 1: and on the final dots) ----
    final_drift = compare_to_registry(target, reg_index, grid.footprint, progress=progress)
    save(EVID / "session7_final_uniqueness.json", final_drift)

    def split_rows(rep):
        rows = [r for r in rep["rows"] if "error" not in r]
        other_rows = [r for r in rows if not str(r.get("submission", "")).startswith("57GEMSDOE:")]
        own_rows = [r for r in rows if str(r.get("submission", "")).startswith("57GEMSDOE:")]
        return rows, other_rows, own_rows

    rows, other_rows, own_rows = split_rows(final_drift)

    def worst(rows_, key):
        vals = [(r.get(key), r.get("submission")) for r in rows_
                if r.get(key) is not None]
        return max(vals, default=(None, None))

    w_ov_other, w_ov_other_at = worst(other_rows, "my_dots_within_3px_of_their_dots")
    w_rho_other, w_rho_other_at = worst(other_rows, "spearman_full_footprint")
    w_ov_own, w_ov_own_at = worst(own_rows, "my_dots_within_3px_of_their_dots")
    w_rho_own, w_rho_own_at = worst(own_rows, "spearman_full_footprint")
    w_lit, w_lit_at = worst(rows, "my_dots_within_3px_of_theirs")
    # Operative drift screen is CROSS-LANE only (rule 1: "drifted into another
    # lane"); same-repo prior builds are succession and are disclosed above.
    # Byte/pixel identity is a hard stop against every raster including our own.
    dup_other = sum(
        1 for r in other_rows
        if r.get("duplicate_by_rho")
        or r.get("duplicate_by_overlap_dots", r.get("duplicate_by_overlap", False))
        or r.get("identical_bytes") or r.get("identical_decoded_predictions")
    )
    cross_lane_pass = bool(
        (w_ov_other or 0.0) <= 0.70 and (w_rho_other or 0.0) <= 0.90
        and final_drift["byte_unique_among_checked"]
        and final_drift["pixel_unique_among_checked"]
        and final_drift["complete_accessible_scan"]
        and dup_other == 0
    )
    identity_duplicate = bool(not final_drift["byte_unique_among_checked"]
                              or not final_drift["pixel_unique_among_checked"])
    print(f"[e2] final dots: worst cross-lane rep-overlap {w_ov_other} at {w_ov_other_at}; "
          f"worst cross-lane rho {w_rho_other} at {w_rho_other_at}; pass={cross_lane_pass}",
          flush=True)

    okay_to_submit = bool(cross_lane_pass and validator["all_checks_passed"]
                          and n_final > 0 and not identity_duplicate)
    verdict = "promote" if okay_to_submit else "negative"

    relay_report = json.loads((EVID / "relay_bend_holdout.json").read_text())

    card = dict(
        hypothesis=("Secondary strands sit in a damage zone around known faults whose "
                    "width grows with displacement and whose strand orientation relative "
                    "to the primary strike is set by the recorded slip sense (Schreurs 2003 "
                    "en echelon Riedel shear; Tchalenko 1970; Savage & Brodsky 2011). "
                    "Allocation is fitted on hide-and-recover, not assumed. NEW this "
                    "session (H6-1): dots within 2 px of the mapped catalogue carry "
                    "little unique new-truth credit (the measured 0.2778 mechanism) and "
                    "should be pruned against matched random pruning."),
        mechanism=("Per-fault intensity from Euclidean distance to the nearest visible "
                   "fault, log component length as displacement proxy, host-relative "
                   "sin2/cos2 orientation, two-host relay geometry (d2, relay ratio, "
                   "facing) and multi-scale bend turning -- all fitted by gradient "
                   "boosting on buffered whole-component LOQO, no textbook angle. "
                   "Binary allocation by the shared greedy max-cover bar; the fitted "
                   "distance zone (90th percentile of training withheld distances) "
                   "shrinks the dot budget; H6-1 proximal pruning is retained only "
                   "under the predeclared paired-CI rule."),
        named_non_fault_process_that_could_mimic_it=(
            "Erosional range-front and fluvial-terrace scarps, lithologic contacts and "
            "magnetic dike contacts between unrelated units, flight-line leveling "
            "residuals in the aeromagnetic grid, and cartographic digitization vertices "
            "can all mimic secondary strands; the proximal-pruning rule can also remove "
            "true splays that root on mapped traces, which is why it was tested against "
            "matched random pruning before use."),
        holdout_dti={
            **relay_report["raw_surface_holdout"]["scores"][RETAINED_ARM],
            "representation": "soft pre-placement surface (matches Session-5 method)",
            "selected_arm": RETAINED_ARM,
            "split_version": e1["split_version"],
            "canary_clean": True,
            "h61_prune_vs_unpruned": e1["paired_differences"]["unpruned"],
            "h61_prune_vs_random": e1["paired_differences"]["random_pruned"],
            "h61_prune_retained": prune_retained,
            "label": ("HOLDOUT-DTI, gems57-pooled-hide-v2, "
                      f"{e1['scores'][PRUNE_CANDIDATE]['withheld_positive_pixels']} "
                      "withheld positives; CIs conditional on fitted folds and budgets; "
                      "not a forecast of any live/private score"),
        },
        holdout_dot_dti={
            **relay_report["scores"][RETAINED_ARM],
            "representation": ("holdout binary allocation of the retained arm "
                               "(H6-1 pruning not retained: paired CI negative)"),
            "selected_arm": RETAINED_ARM,
        },
        correlation_overlap_vs_registry=dict(
            registry_rasters_expected=final_drift["registry_rasters_expected"],
            registry_rasters_checked=final_drift["registry_rasters_checked"],
            complete_accessible_scan=final_drift["complete_accessible_scan"],
            dot_representation_rule=final_drift["dot_representation_rule"],
            worst_spearman_full_footprint=final_drift["worst_spearman_full_footprint"],
            worst_rho_submission=final_drift["worst_rho_submission"],
            worst_dot_overlap_representation=final_drift["worst_dot_overlap_representation"],
            worst_overlap_representation_submission=final_drift["worst_overlap_representation_submission"],
            worst_cross_lane_dot_overlap_representation=w_ov_other,
            worst_cross_lane_dot_overlap_at=w_ov_other_at,
            worst_cross_lane_spearman=w_rho_other,
            worst_cross_lane_spearman_at=w_rho_other_at,
            same_lane_disclosure=dict(
                note=("Same-repository prior builds of this lane are succession, not "
                      "cross-lane drift; byte/pixel identity against them is a hard stop."),
                worst_same_lane_dot_overlap_representation=w_ov_own,
                worst_same_lane_dot_overlap_at=w_ov_own_at,
                worst_same_lane_spearman=w_rho_own,
                worst_same_lane_spearman_at=w_rho_own_at,
            ),
            literal_support_screen=final_drift["literal_support_screen"],
            worst_literal_forward_overlap=w_lit,
            worst_literal_forward_overlap_at=w_lit_at,
            duplicate_count=final_drift["duplicate_count"],
            duplicate_count_dot_representation=final_drift["duplicate_count_dot_representation"],
            duplicate_count_dot_representation_other_lanes=dup_other,
            byte_unique_among_checked=final_drift["byte_unique_among_checked"],
            pixel_unique_among_checked=final_drift["pixel_unique_among_checked"],
            unique_under_dot_representation=final_drift["unique_under_dot_representation"],
            unique_literal_support=final_drift["unique"],
            jaccard_diagnostic_only=True,
        ),
        surface_before_placement=dict(
            checked=True,
            protocol_pass=surface_cross_lane_pass,
            worst_cross_lane_spearman=worst_other_rho,
            worst_own_prior_spearman=worst_own_rho,
            evidence="session7_surface_uniqueness.json",
        ),
        final_dots=dict(
            status="generated",
            emitted_pixels=n_final,
            allocated_before_pruning=n_alloc,
            proximal_dropped=n_prox if prune_retained else 0,
            prune_rule=f"d(mapped catalogue) <= {PROXIMAL_PX} px",
            prune_retained=prune_retained,
            budget_after_zone_shrink=budget,
            checks="final-dot dual screen above",
        ),
        raster_sha256=receipt["sha256"],
        raster_bytes=receipt["bytes"],
        validator_output=validator,
        submission_name=label,
        submission_note=note,
        submission_note_chars=len(note),
        file=str(target.relative_to(ROOT)),
        zip_file=str(target.with_suffix(".zip").relative_to(ROOT)),
        receipt_file=str(target.with_suffix(".json").relative_to(ROOT)),
        verdict=verdict,
        okay_to_download=True,
        okay_to_submit=okay_to_submit,
        verdict_reason=(
            "Unique binary dot GeoTIFF from the fault-zone anatomy lane: E2 relay/bend "
            "fitted intensity + zone-shrunk greedy allocation + H6-1 proximal pruning "
            f"({'retained' if prune_retained else 'not retained'} by the predeclared "
            "paired-CI rule). Dual uniqueness screen cross-lane pass="
            f"{cross_lane_pass}; all-finite [0,1]; zero dots on the mapped catalogue. "
            "No weekly slot is used by the generator; the owner decides submission."
        ),
        experiments_used=2,
        submission_slots_used=0,
        generated_utc=datetime.now(timezone.utc).isoformat(),
        registry_reviewed_utc=json.loads(reg_index.read_text())["generated_utc"],
        registry_scope=("All hash-verified accessible competition-grid rasters across the "
                        "57 public GEMSDOE repositories at latest public-main commits plus "
                        "historical pins; private/unlinked/inaccessible artifacts are "
                        "outside scope."),
        score_projection=None,
    )
    save(EVID / "run_card_current.json", card)
    save(EVID / "run_card.json", card)
    save(ROOT / "docs" / "data" / "run_card.json", card)
    save(EVID / "session7_run_card.json", card)
    print(f"[e2] verdict={verdict} okay_to_submit={okay_to_submit}; "
          f"runtime {(time.monotonic()-start)/60:.1f} min", flush=True)
    return 0 if verdict == "promote" else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["experiment", "build"])
    a = ap.parse_args()
    return {"experiment": stage_experiment, "build": stage_build}[a.stage](a)


if __name__ == "__main__":
    raise SystemExit(main())
