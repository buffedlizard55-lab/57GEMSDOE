#!/usr/bin/env python3
"""Calibration: score the registry's top rasters (and controls) on THIS lane's
holdout instrument, so the lane's HOLDOUT-DTI is comparable to the live scores
those rasters carry.  Also score every raster on the SGMC-truth instrument
(real off-catalogue faults = the closest legal proxy for the hidden truth).

Both instruments use the template metric (alpha 0.2, beta 0.8, 300 m).  All
numbers are HOLDOUT-DTI / PROXY-DTI, never organizer scores.
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
from gems57 import evaluate_holdout as EH  # noqa: E402
from gems57 import holdout as HO  # noqa: E402
from gems57 import metric as M  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "evidence"
REG = Path("/home/user/registry")
BASE = 100000
BUFFER_PX = 3
N_FOLDS = 4
PREVALENCE = 0.002
SEED = 20261009

# registry rasters that carry owner-reported live scores (top of the family)
REGISTRY = [
    ("h33-2-b2 LIVE 0.2778", "GEMSDOE48-main/data/raw/dotted_h33_2_b2_zeros.tif"),
    ("h27-4-solo LIVE 0.2708", "GEMSDOE48-main/data/raw/ref_h27_4_solo.tif"),
    ("h36-1-rung30 LIVE 0.2710", "GEMSDOE48-main/data/raw/ref_h36_1_rung30.tif"),
    ("tip-h33d LIVE 0.2632", "GEMSDOE48-main/data/raw/tip_h33d_stepover.tif"),
    ("tip-h32-1 LIVE 0.2649", "GEMSDOE48-main/data/raw/tip_h32_1_prethin_tip_euler.tif"),
    ("h19-5 LIVE 0.1922", "GEMSDOE48-main/data/raw/scored/h19_5_01922.tif"),
    ("d15 LIVE 0.2477", "GEMSDOE48-main/data/raw/scored/d15_02477.tif"),
    ("h32 LIVE 0.2649", "GEMSDOE48-main/data/raw/scored/h32_prethin_tip_02649.tif"),
    ("h36 LIVE 0.2710", "GEMSDOE48-main/data/raw/scored/h36_rung30_02710.tif"),
    ("anderson LIVE 0.2750", "GEMSDOE36-main/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif"),
    ("catalogue (sample_submission)", "official/sample_submission.tif"),
]


def read_raster(path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float64)
    return np.where(np.isfinite(a), a, 0.0)


def main():
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    with rasterio.open(DATA / "official/labels.tif") as ds:
        cat = ds.read(1) > 0
        transform = ds.transform
    with rasterio.open(DATA / "official/sample_submission.tif") as ds:
        valid = np.isfinite(ds.read(1))
    with rasterio.open(DATA / "external/derived_sgmc_faults_100m.tif") as ds:
        sgmc = ds.read(1) > 0

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

    rng = np.random.default_rng(SEED)
    cat_ids = np.arange(1, n_cat + 1)
    assign = rng.integers(0, N_FOLDS, size=cat_ids.size)
    target = PREVALENCE * float(valid.sum())
    folds = []
    for f in range(N_FOLDS):
        ids = cat_ids[assign == f]
        order = rng.permutation(ids)
        keep = []
        tot = 0.0
        for sid in order:
            if tot >= target:
                break
            keep.append(int(sid))
            tot += float(seg_stats[sid]["size"])
        held = np.isin(seg_lab, keep)
        folds.append(dict(fold=f, held=held, kept=keep))

    fold_dicts = []
    for f in folds:
        visible = known & ~f["held"]
        near_visible = ndimage.binary_dilation(visible, iterations=BUFFER_PX)
        truth = f["held"] & valid & ~near_visible
        fold_dicts.append(dict(fold=f["fold"], mode="hide", truth=truth,
                               visible=visible, region=valid, fit=valid,
                               boundary=near_visible, n_truth=int(truth.sum()),
                               n_held=int(f["held"].sum())))
        del visible, near_visible, truth
        gc.collect()

    results = {}
    for name, rel in REGISTRY:
        path = REG / rel
        if not path.exists():
            path = DATA / rel
        if not path.exists():
            print(f"  MISSING {rel}", flush=True)
            continue
        p = read_raster(path)
        terms = []
        per_fold = []
        for fd in fold_dicts:
            result, t = EH.evaluate(p, fd, valid, block_side=200)
            terms.append(t)
            per_fold.append(dict(fold=fd["fold"], dti=result["dti"],
                                 tpw=result["tpw"], fpw=result["fpw"],
                                 fnw=result["fnw"], emitted=result["emitted"]))
        merged = np.stack(terms).sum(axis=0)
        s = EH.pooled_summary({"candidate": merged}, draws=1000, seed=SEED + 7,
                              candidate="candidate")
        # SGMC-truth instrument: mask known pixel-exactly, score vs SGMC off-known
        pm = np.where(known, 0.0, p)
        r = M.dti(pm.astype(np.float32), sgmc_truth)
        results[name] = dict(
            file=rel,
            holdout_dti=s["scores"]["candidate"]["dti"],
            holdout_ci95=s["scores"]["candidate"]["ci95"],
            holdout_withheld_positives=s["scores"]["candidate"]["withheld_positive_pixels"],
            holdout_tpw=s["scores"]["candidate"]["tpw"],
            holdout_fpw=s["scores"]["candidate"]["fpw"],
            holdout_fnw=s["scores"]["candidate"]["fnw"],
            per_fold=per_fold,
            sgmc_truth_dti=r["dti"], sgmc_tpw=r["tpw"], sgmc_fpw=r["fpw"],
            sgmc_fnw=r["fnw"], sgmc_n_truth=r["n_truth"],
            emitted_px=int((p > 0).sum()))
        print(f"  {name:34s} holdout DTI {results[name]['holdout_dti']:.4f} "
              f"[{results[name]['holdout_ci95'][0]:.4f},{results[name]['holdout_ci95'][1]:.4f}]  "
              f"SGMC-truth DTI {r['dti']:.4f}  emitted {int((p > 0).sum())}", flush=True)
        del p, pm
        gc.collect()

    payload = dict(
        evidence_class="HOLDOUT-DTI + PROXY-DTI (SGMC-truth)",
        evaluator_version=EH.VERSION,
        protocol="same folds as exp2; registry rasters scored as-is (masked pixel-exactly "
                 "on visible known faults per fold)",
        withheld_positive_pixels=sum(fd["n_truth"] for fd in fold_dicts),
        sgmc_truth_pixels=int(sgmc_truth.sum()),
        results=results,
        runtime_s=time.time() - t0,
    )
    (OUT / "calibrate_registry.json").write_text(json.dumps(payload, indent=1, default=str))
    print("[calib] wrote evidence/calibrate_registry.json", flush=True)


if __name__ == "__main__":
    main()
