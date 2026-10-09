#!/usr/bin/env python3
"""EXPERIMENT 3 (fault-zone anatomy lane): build the final surface from the FULL
known-fault set, sweep the dot budget on the SGMC-truth instrument (clean: SGMC
faults are never used to build the intensity), cross-check on the holdout
instrument (as-is scoring -- flagged optimistic, see exp2 for the honest
per-fold-rebuilt numbers), then write the validated submission GeoTIFF.

The primary budget decision stays with the brief's instrument: exp2's
per-fold-rebuilt holdout sweep (full arm peaked at 60k dots,
HOLDOUT-DTI 0.0580 [0.0507, 0.0663]).  The SGMC sweep is reported as the
off-catalogue cross-check.
"""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import faultzone as fz  # noqa: E402
from gems57 import fit as F  # noqa: E402
from gems57 import holdout as HO  # noqa: E402
from gems57 import metric as M  # noqa: E402
from gems57 import grid as G  # noqa: E402
from gems57 import gates  # noqa: E402
from gems57 import submission_writer as SW  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "evidence"
DOCS = ROOT / "docs" / "downloads"
BASE = 100000
BUFFER_PX = 3
N_FOLDS = 4
PREVALENCE = 0.002
SEED = 20261009
BUDGETS = [20000, 40000, 60000, 80000, 120000]
SUBMISSION_STEM = "gems57-faultzone-anatomy"


def main():
    OUT.mkdir(exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with rasterio.open(DATA / "official/labels.tif") as ds:
        cat = ds.read(1) > 0
        transform = ds.transform
    with rasterio.open(DATA / "official/sample_submission.tif") as ds:
        valid = np.isfinite(ds.read(1))
        sample_path = DATA / "official/sample_submission.tif"
    with rasterio.open(DATA / "external/derived_sgmc_faults_100m.tif") as ds:
        sgmc = ds.read(1) > 0

    print("[exp3] full known-fault store ...", flush=True)
    ing_stats, ing_pix, tmap, _ = fz.ingenious_record_segments(
        DATA / "external/trace_segments_utm11.csv", cat.shape, transform)
    ingen_mask = tmap > 0
    seg_lab_cat, seg_stats_cat = fz.link_segments(cat & valid)
    n_cat = len(seg_stats_cat)
    seg_lab = np.zeros(cat.shape, dtype=np.int32)
    pl = fz.segment_pixel_lists(seg_lab_cat, n_cat)
    for sid in range(1, n_cat + 1):
        ys, xs = pl[sid - 1]
        seg_lab[ys, xs] = sid
    del seg_lab_cat, pl
    gc.collect()
    for sid, (ys, xs) in ing_pix.items():
        seg_lab[ys, xs] = BASE + sid
    seg_stats = dict(seg_stats_cat)
    for sid, s in ing_stats.items():
        seg_stats[BASE + sid] = s
    known = (cat | ingen_mask) & valid
    sgmc_truth = sgmc & ~known & valid
    del tmap, ingen_mask, sgmc
    gc.collect()

    # fitted factors (from exp1b holdout measurements)
    pooled = np.load(OUT / "exp1b_pooled.npz")
    sgmc_p = np.load(OUT / "exp1b_sgmc.npz")
    f_dist = F.fit_distance_density(pooled["d"])
    near_density = F.extend_near_band_sgmc(pooled["d"], sgmc_p["d"])
    g_az = F.fit_azimuth_density(pooled["phi"])
    scaling = F.fit_length_scaling(pooled["d"], pooled["L"])

    print("[exp3] halo features from the full known set ...", flush=True)
    d, (iy, ix) = ndimage.distance_transform_edt(~known, return_indices=True)
    halo = (d <= F.D_MAX_PX) & valid & ~known
    ys, xs = np.nonzero(halo)
    dv = d[ys, xs]
    ny, nx = iy[ys, xs], ix[ys, xs]
    sn = seg_lab[ny, nx].astype(np.int64)
    sn[~known[ny, nx]] = 0
    dy = (ys - ny).astype(np.float64)
    dx = (xs - nx).astype(np.float64)
    az = np.degrees(np.arctan2(dx, dy)) % 180.0
    del d, iy, ix, dy, dx, ny, nx
    gc.collect()
    max_id = max(seg_stats)
    strike_of = np.zeros(max_id + 1)
    vy_of = np.zeros(max_id + 1); vx_of = np.zeros(max_id + 1)
    cy_of = np.zeros(max_id + 1); cx_of = np.zeros(max_id + 1)
    span_of = np.ones(max_id + 1)
    len_of = np.zeros(max_id + 1)
    for sid, s in seg_stats.items():
        strike_of[sid] = s["strike"]
        vy_of[sid], vx_of[sid] = float(s["axis"][0]), float(s["axis"][1])
        cy_of[sid], cx_of[sid] = float(s["centroid"][0]), float(s["centroid"][1])
        span_of[sid] = max(s["span_px"], 1e-9)
        len_of[sid] = s["length_px"]
    phi = np.full(ys.size, np.nan)
    L = np.zeros(ys.size)
    has = sn > 0
    snh = sn[has]
    rel = (az[has] - strike_of[snh]) % 180.0
    phi[has] = np.minimum(rel, 180.0 - rel)
    L[has] = len_of[snh]
    del az, strike_of, vy_of, vx_of, cy_of, cx_of, span_of, len_of, sn, has, snh
    gc.collect()
    sL = F.length_scale_lookup(L, scaling)
    d_eff = dv / sL
    f_d = F.density_at(d_eff, f_dist, near_density)
    f_d_nonnear = F.density_at(d_eff, f_dist, None)
    g_p = F.azimuth_at(phi, g_az)
    intensity = np.where(np.isfinite(f_d * g_p) & (f_d * g_p > 0), f_d * g_p, 0.0)
    intensity_nonnear = np.where(np.isfinite(f_d_nonnear * g_p) & (f_d_nonnear * g_p > 0),
                                 f_d_nonnear * g_p, 0.0)
    print(f"[exp3] halo {ys.size} px, intensity>0 on {(intensity > 0).sum()}", flush=True)

    # surface (continuous) on the full grid, float32
    surface = np.zeros(valid.shape, dtype=np.float32)
    surface[ys, xs] = intensity.astype(np.float32)
    surface_nn = np.zeros(valid.shape, dtype=np.float32)
    surface_nn[ys, xs] = intensity_nonnear.astype(np.float32)

    allowed = valid & ~known
    print(f"[exp3] allowed (off known faults, in footprint): {int(allowed.sum())}", flush=True)

    # ---- budget sweep on the SGMC-truth instrument (clean) ----
    sweep = {}
    for tag, surf in (("with_near_band", surface), ("no_near_band", surface_nn)):
        for b in BUDGETS:
            em = HO.emit_topk(surf, allowed, b)
            pm = np.where(known, 0.0, em.astype(np.float64))
            r = M.dti(pm.astype(np.float32), sgmc_truth)
            sweep[f"{tag}|{b}"] = dict(
                sgmc_truth_dti=r["dti"], tpw=r["tpw"], fpw=r["fpw"], fnw=r["fnw"],
                n_truth=r["n_truth"], emitted=int((em > 0).sum()),
                mass=float(em.sum()))
            print(f"  {tag:15s} budget {b:6d}: SGMC-truth DTI {r['dti']:.4f} "
                  f"(TPw {r['tpw']:.0f} FPw {r['fpw']:.0f} FNw {r['fnw']:.0f})", flush=True)
            del em, pm
            gc.collect()

    # ---- holdout cross-check ----
    # The honest holdout number is exp2's per-fold-REBUILT evaluation (features
    # from visible faults only): full arm peaks at 60k dots, DTI 0.0580
    # [0.0507, 0.0663], 38,339 withheld positives.  Scoring the full-data
    # emission as-is on the folds is degenerate for this lane and is NOT
    # reported as a number: the fitted zone peaks 5-6 px from its anchor
    # fault, outside the 3 px metric-credit radius of the anchor's own
    # pixels, and the global top-k cut dilutes the hidden folds' share of
    # dots (measured 0.0000 -- an artifact, not a result).
    holdout_asis = dict(
        note="as-is full-data scoring on the folds is degenerate for this lane "
             "(zone peak 5-6 px from anchors, outside the 3 px credit radius of "
             "the anchor's own pixels; global top-k dilutes hidden folds); the "
             "honest per-fold-rebuilt holdout is exp2_holdout.json",
        exp2_headline=dict(arm="full", budget=60000, dti=0.0580,
                           ci95=[0.0507, 0.0663],
                           evaluator="gems52-pooled-hide-v1",
                           withheld_positives=38339))

    # ---- final choice: holdout-primary (exp2: full arm peaks at 60k) ----
    FINAL_BUDGET = 60000
    near_tag = "with_near_band"   # SGMC: 23.8% of real off-catalogue faults sit within 3px
    final_em = HO.emit_topk(surface if near_tag == "with_near_band" else surface_nn,
                            allowed, FINAL_BUDGET)
    final = np.where(known, 0.0, final_em.astype(np.float32))
    assert np.isfinite(final).all() and final.min() >= 0 and final.max() <= 1
    assert not (final > 0)[known].any(), "emission on known faults"
    assert not (final > 0)[~valid].any(), "emission outside footprint"

    # ---- write the submission via the fail-closed template writer ----
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{SUBMISSION_STEM}-{FINAL_BUDGET}px-{ts}"
    tif_path = DOCS / f"{stem}.tif"
    note = (f"fault-zone anatomy: fitted damage-zone halo around USGS+INGENIOUS faults; "
            f"{FINAL_BUDGET} dots, 0 on known faults; HOLDOUT-DTI 0.0580 [0.0507,0.0663]")
    name = f"GEMSDOE57-FZA-{FINAL_BUDGET}px"
    assert len(note) <= 140 and len(name) <= 140, (len(note), len(name))
    surface_path = OUT / "final_surface.npz"
    np.savez_compressed(surface_path, surface=surface, final=final,
                        ys=ys, xs=xs, dv=dv, phi=phi, L=L)
    receipt = SW.write_submission(
        tif_path, final, sample_path, valid,
        note=note, name=name,
        metadata=dict(lane="fault-zone-anatomy", budget=FINAL_BUDGET,
                      near_band=near_tag, surface_sha=None))
    payload = dict(
        evidence_class="HOLDOUT-DTI (exp2, per-fold rebuilt) + PROXY-DTI (SGMC-truth)",
        submission=dict(file=tif_path.name, sha256=receipt["sha256"],
                        bytes=receipt["bytes"], name=name, note=note,
                        zip_file=receipt["zip_file"], zip_sha256=receipt["zip_sha256"],
                        emitted_px=int((final > 0).sum())),
        final_choice=dict(budget=FINAL_BUDGET, near_band=near_tag,
                          rule="holdout-primary: exp2 full arm peaks at 60k dots; "
                               "SGMC sweep reported as off-catalogue cross-check"),
        sweep=sweep,
        holdout_crosscheck=holdout_asis,
        exp2_headline=dict(arm="full", budget=60000, dti=0.0580, ci95=[0.0507, 0.0663],
                           evaluator="gems52-pooled-hide-v1", withheld_positives=38339),
        validator=receipt["validator"],
        runtime_s=time.time() - t0,
    )
    (OUT / "exp3_build.json").write_text(json.dumps(payload, indent=1, default=str))
    (DOCS / f"{stem}.receipt.json").write_text(json.dumps(payload, indent=1, default=str))
    print("[exp3] wrote", tif_path, receipt["sha256"], flush=True)
    print("[exp3] validator ok:", receipt["validator"]["ok"], flush=True)
    print("[exp3] wrote evidence/exp3_build.json", flush=True)


if __name__ == "__main__":
    main()
