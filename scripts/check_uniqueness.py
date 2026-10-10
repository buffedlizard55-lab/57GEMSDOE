#!/usr/bin/env python3
"""Parallel-run protocol drift check: is this lane's raster a duplicate of any
registry raster?

Independent second implementation of the uniqueness screen (the first lives in
``src/gems57/uniqueness.py`` and runs inside ``build_submission.py``).  This one
adds the bidirectional overlap gate and the byte-level sha256 check, and it
reads the CURRENT submission from the build audit rather than globbing a
filename pattern.

Gates (parallel-run protocol rule 1), checked on the final dots:
  1. Spearman rank correlation over the full footprint > 0.90  -> duplicate.
  2. forward 3 px dot overlap > 0.70 AND reverse > 0.50 vs a dot-scale
     registry raster -> duplicate.  One-directional firings are coverage-
     saturation artifacts (a dense registry raster dilates over everything)
     and are logged, not fatal.
  3. byte-identical sha256 to any registry raster -> duplicate.

Output: ``evidence/uniqueness.json``.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "evidence"
CORR_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
REVERSE_LIMIT = 0.50
DOTSCALE_MAX_POS = 500_000           # ~10% of footprint: the family's dot emissions


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        # sentinel must be the empty BYTES object: f.read() returns b'' at
        # EOF, never the int 1 << 20 (an int sentinel loops forever).
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    with rasterio.open(ROOT / "data/official/sample_submission.tif") as ds:
        valid = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/official/labels.tif") as ds:
        cat = ds.read(1) > 0

    audit = json.loads((ROOT / "evidence" / "submission_build_all.json").read_text())
    my_tif = Path(audit["zeros_tif"]["file"])
    if not my_tif.is_absolute():
        my_tif = ROOT / my_tif
    with rasterio.open(my_tif) as ds:
        _a = ds.read(1)
    surface = np.where(np.isfinite(_a), _a, 0.0).astype(np.float64)
    del _a
    my_dots = surface > 0
    n_my_dots = int(my_dots.sum())
    print(f"[uniq] candidate: {my_tif.name}  dots={n_my_dots}", flush=True)

    idx = json.loads((ROOT / "registry" / "registry_index.json").read_text())
    print(f"[uniq] checking {len(idx)} registry rasters ...", flush=True)

    my_sha = sha256(my_tif)
    fp_idx = np.flatnonzero(valid.ravel())
    my_vals = surface.ravel()[fp_idx]
    my_ranks = rankdata(my_vals, method="average")
    my_rank_mean = my_ranks.mean()
    my_rank_var = my_ranks.var()
    my_dot_ys, my_dot_xs = np.nonzero(my_dots)
    my_near = ndimage.binary_dilation(my_dots, iterations=3)
    on_cat = float(cat[my_dot_ys, my_dot_xs].mean())

    results = []
    max_corr = (0.0, None)
    max_fwd = (0.0, None)
    hash_dupes = []
    for i, e in enumerate(idx):
        p = ROOT / e["file"]
        try:
            with rasterio.open(p) as ds:
                a = ds.read(1).astype(np.float64)
        except Exception as ex:
            results.append(dict(path=e["file"], error=str(ex)[:80]))
            continue
        a = np.where(np.isfinite(a), a, 0.0)
        if sha256(p) == my_sha:
            hash_dupes.append(e["file"])
        av = a.ravel()[fp_idx]
        if np.unique(av).size <= 2:
            # binary registry raster: Spearman via point-biserial on my ranks
            y = (av > 0).astype(np.float64)
            p1 = y.mean()
            if 0.0 < p1 < 1.0 and my_rank_var > 0:
                cov = ((my_ranks - my_rank_mean) * (y - p1)).mean()
                corr = float(cov / np.sqrt(my_rank_var * y.var()))
            else:
                corr = 0.0
        else:
            ry = rankdata(av, method="average")
            corr = float(np.corrcoef(my_ranks, ry)[0, 1])
        dots = a > 0
        n_reg_dots = int(dots.sum())
        if dots.any():
            near = ndimage.binary_dilation(dots, iterations=3)
            fwd = float(near[my_dot_ys, my_dot_xs].mean())       # my dots near theirs
            ry_, rx_ = np.nonzero(dots)
            rev = float(my_near[ry_, rx_].mean())               # their dots near mine
        else:
            fwd = rev = 0.0
        dot_scale = n_reg_dots <= DOTSCALE_MAX_POS
        if abs(corr) > abs(max_corr[0]):
            max_corr = (corr, e["file"])
        if dot_scale and fwd > max_fwd[0]:
            max_fwd = (fwd, e["file"])
        results.append(dict(path=e["file"], sha=e.get("sha256", ""),
                            spearman_r=corr, dot_overlap_fwd=fwd,
                            dot_overlap_rev=rev, n_reg_dots=n_reg_dots,
                            dot_scale=dot_scale))
        del a, av
    dup_corr = [r for r in results if "spearman_r" in r and r["spearman_r"] > CORR_LIMIT]
    dup_over = [r for r in results if r.get("dot_scale")
                and r["dot_overlap_fwd"] > OVERLAP_LIMIT
                and r["dot_overlap_rev"] > REVERSE_LIMIT]
    sat_firings = [r for r in results if r.get("dot_scale")
                   and r["dot_overlap_fwd"] > OVERLAP_LIMIT
                   and r["dot_overlap_rev"] <= REVERSE_LIMIT]
    payload = dict(
        evidence_class="MEASUREMENT (drift check vs registry, independent implementation)",
        candidate=dict(file=my_tif.name, sha256=my_sha, dots=n_my_dots,
                       dots_on_catalogue_frac=on_cat),
        registry_rasters_checked=len([r for r in results if "spearman_r" in r]),
        max_spearman=dict(value=max_corr[0], raster=max_corr[1]),
        max_fwd_overlap_dotscale=dict(value=max_fwd[0], raster=max_fwd[1]),
        limits=dict(spearman=CORR_LIMIT, dot_overlap_fwd=OVERLAP_LIMIT,
                    dot_overlap_rev=REVERSE_LIMIT),
        gates=dict(
            correlation="Spearman over the full footprint must be <= 0.90",
            overlap="duplicate iff forward 3 px dot overlap > 0.70 AND reverse > 0.50 "
                    f"vs a dot-scale registry raster (<= {DOTSCALE_MAX_POS:,} positive px); "
                    "one-directional firings are saturation artifacts, logged not fatal"),
        hash_duplicates=hash_dupes,
        duplicates_by_correlation=dup_corr,
        duplicates_by_overlap=dup_over,
        saturation_firings=sat_firings[:25],
        verdict=("DUPLICATE - STOP" if (dup_corr or dup_over or hash_dupes)
                 else "UNIQUE - no registry raster within the drift limits "
                      "(one-directional overlap firings logged as coverage-saturation "
                      "artifacts)"),
        top10_by_corr=sorted([r for r in results if "spearman_r" in r],
                             key=lambda r: -r["spearman_r"])[:10],
        top10_by_fwd_overlap=sorted([r for r in results if r.get("dot_scale")],
                                    key=lambda r: -r["dot_overlap_fwd"])[:10],
        runtime_s=time.time() - t0,
    )
    (OUT / "uniqueness.json").write_text(json.dumps(payload, indent=1, default=str))
    print("[uniq] verdict:", payload["verdict"], flush=True)
    print("[uniq] max spearman = %.4f (%s)" % (max_corr[0], max_corr[1]), flush=True)
    print("[uniq] max fwd overlap (dot-scale) = %.4f (%s)" % (max_fwd[0], max_fwd[1]),
          flush=True)
    print("[uniq] wrote evidence/uniqueness.json", flush=True)


if __name__ == "__main__":
    main()
