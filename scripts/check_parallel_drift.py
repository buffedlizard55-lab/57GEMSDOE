#!/usr/bin/env python3
"""Drift check of the CURRENT submission against the PARALLEL session's
rasters (same lane, fault-zone anatomy).

History: PR #1 (arena/a5412310) merged the same lane (12k dots, synthetic
P/Riedel strands within 15 px of known faults) while an earlier session of
this repo built a fitted-density 60k-dot halo.  Those rasters are kept in
``docs/downloads/archive/`` and indexed in ``registry/registry_index.json``;
this script re-checks the current submission against them specifically, with
the bidirectional overlap rule (forward > 0.70 AND reverse > 0.50 = duplicate)
and the signed full-footprint Spearman (IR-57-RHO-01: the dot-union statistic
is degenerate and is reported but never thresholded).

Writes ``evidence/uniqueness_parallel.json``.
"""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage, stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence"

# parallel-session rasters: repo "57GEMSDOE", submission tag "parallel"
PARALLEL_TAG = "parallel"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        # sentinel must be the empty BYTES object: f.read() returns b'' at
        # EOF, never the int 1 << 20 (an int sentinel loops forever).
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    t0 = time.time()
    with rasterio.open(ROOT / "data/official/sample_submission.tif") as ds:
        valid = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/official/labels.tif") as ds:
        cat = ds.read(1) > 0

    audit = json.loads((ROOT / "evidence" / "submission_build_all.json").read_text())
    mine_path = Path(audit["zeros_tif"]["file"])
    if not mine_path.is_absolute():
        mine_path = ROOT / mine_path
    with rasterio.open(mine_path) as ds:
        _a = ds.read(1)
    my_surf = np.where(np.isfinite(_a), _a, 0.0).astype(np.float64)
    del _a
    my_dots = my_surf > 0
    ys, xs = np.nonzero(my_dots)
    my_near = ndimage.binary_dilation(my_dots, iterations=3)
    dcat = ndimage.distance_transform_edt(~cat)
    fp = valid.ravel()
    x = my_surf.ravel()[fp]

    idx = json.loads((ROOT / "registry" / "registry_index.json").read_text())
    parallel = [e for e in idx if PARALLEL_TAG in e["submission"].lower()
                or "12000dots" in e["submission"]]
    print(f"[par] {len(parallel)} parallel-session rasters to check", flush=True)

    results = []
    for e in parallel:
        p = ROOT / e["file"]
        with rasterio.open(p) as ds:
            _b = ds.read(1)
        a = np.where(np.isfinite(_b), _b, 0.0)
        del _b
        dots = a > 0
        n = int(dots.sum())
        on_cat = int(dots[cat].sum())
        near = ndimage.binary_dilation(dots, iterations=3)
        fwd = float(near[ys, xs].mean())
        ry, rx = np.nonzero(dots)
        rev = float(my_near[ry, rx].mean())
        rho, _ = stats.spearmanr(x, a.ravel()[fp])
        dd = dcat[ry, rx]
        results.append(dict(
            raster=p.name, sha256=sha256(p), dots=n, dots_on_catalogue=on_cat,
            their_dots_d_to_catalogue_px=dict(median=float(np.median(dd)),
                                              frac_le_3px=float((dd <= 3).mean()),
                                              frac_le_15px=float((dd <= 15).mean())),
            spearman_my_surface_vs_their_raster=float(rho),
            forward_overlap_my_dots_within_3px_of_theirs=fwd,
            reverse_overlap_their_dots_within_3px_of_mine=rev,
            duplicate_by_correlation=bool(rho > 0.90),
            duplicate_by_overlap=bool(fwd > 0.70 and rev > 0.50),
        ))
        print(f"[par] {p.name}: dots {n} on-cat {on_cat} | rho {rho:+.4f} "
              f"fwd {fwd:.4f} rev {rev:.4f}", flush=True)

    payload = dict(
        evidence_class="MEASUREMENT (drift check vs the parallel session's rasters)",
        context="The parallel session ran the same lane (fault-zone anatomy) from the "
                "same prompt. Its rasters are kept in docs/downloads/archive/ and in "
                "the registry; this script checks the CURRENT submission against them.",
        candidate=dict(file=mine_path.name, sha256=sha256(mine_path),
                       dots=int(my_dots.sum()),
                       dots_on_catalogue=int(my_dots[cat].sum()),
                       my_dots_d_to_catalogue_px=dict(median=float(np.median(dcat[ys, xs])))),
        limits=dict(spearman=0.90, dot_overlap_fwd=0.70, dot_overlap_rev=0.50),
        parallel_rasters=results,
        verdict=("DUPLICATE - STOP" if any(r["duplicate_by_correlation"]
                                           or r["duplicate_by_overlap"]
                                           for r in results)
                 else "UNIQUE - distinct from the parallel session's rasters "
                      "(rank correlation and bidirectional overlap within limits)"),
        runtime_s=time.time() - t0,
    )
    (OUT / "uniqueness_parallel.json").write_text(json.dumps(payload, indent=1))
    print("[par] verdict:", payload["verdict"], flush=True)
    print("[par] wrote evidence/uniqueness_parallel.json", flush=True)


if __name__ == "__main__":
    main()
