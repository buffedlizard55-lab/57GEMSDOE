#!/usr/bin/env python3
"""Which offline instrument actually ranks owner-reported live scores?

Motivation
----------
``evidence/calibrate_registry.json`` recorded two offline instruments for 10
registry rasters and both appeared to ANTI-correlate with the owner-reported
live score (Spearman -0.951 hide-and-recover, -0.963 SGMC-truth).  This session
re-derived why, from the DTI algebra in ``src/gems57/metric.py``::

    DTI = T / (0.2*T + 0.2*(n - M) + 0.8*(G - T))

where ``T = sum_truth max_dot k``, ``M = sum_dot max_truth k``, ``n`` = emitted
dots and ``G`` = |truth|.  Both ``T`` and ``M`` scale with ``n``, and the
``0.8*G`` term is a constant that depends only on the *instrument's* truth
size.  An instrument whose ``G`` is much larger than the organizer's therefore
ranks rasters mostly by recall, i.e. mostly by ``n`` -- which is exactly the
confound seen above.

The quantity that is free of both confounds is

    credit_per_dot = M / n = mean_{dot} max_{truth} k(d)

It does not contain ``G``, and it is scale-free in ``n``.  At fixed ``n`` it
monotonically determines DTI.  This script measures ``credit_per_dot`` for every
owner-labelled registry raster against three candidate truth sets and reports
which one ranks the owner-reported live scores.

Truth sets
----------
``sgmc_off_known``  Nevada State Geologic Map Compilation faults rasterised at
    100 m, minus the INGENIOUS vector traces and minus the competition catalogue.
    This is an *independent expert compilation* of fault pixels that USGS /
    INGENIOUS does not contain -- the closest legal analogue to the organiser's
    definition ("any fault pixel not already captured by USGS/INGENIOUS").
``catalogue``       the competition's own mapped faults.  Used as a negative
    control: a good submission must NOT be near it.
``withheld``        pooled hide-and-recover truth (buffered whole-component LOQO).

Evidence class: REGISTRY-MEASUREMENT joined to OWNER-REPORTED scores.  Nothing
here is ORGANIZER-CONFIRMED and nothing is a HOLDOUT-DTI reading unless labelled.
"""
from __future__ import annotations

import gc
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import faultzone as fz  # noqa: E402
from gems57 import load_grid  # noqa: E402
from gems57 import metric as M  # noqa: E402
from gems57.holdout import buffered_component_draw  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "evidence" / "instrument_calibration.json"
STUDY = ROOT / "evidence" / "live_geometry_study.json"


def read_raster(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float64)
    return np.where(np.isfinite(a), a, 0.0)


def credit(pred: np.ndarray, truth: np.ndarray, valid: np.ndarray,
           known: np.ndarray) -> dict:
    """T, M, n and the budget-free credit-per-dot for one truth set."""
    p = np.where(valid & ~known, pred, 0.0)
    p = np.clip(p, 0.0, 1.0)
    g = valid & ~known & truth
    n = int((p > 0).sum())
    if n == 0 or not g.any():
        return dict(n=n, T=0.0, M=0.0, credit_per_dot=0.0, coverage=0.0,
                    n_truth=int(g.sum()), dti=0.0)
    credit_truth, q, _ = M.max_cover(p, g)
    T = float(credit_truth.sum())
    Mtot = float((p * q).sum())
    fp = float((p * (1.0 - q)).sum())
    fn = float(g.sum()) - T
    return dict(n=n, T=T, M=Mtot, credit_per_dot=Mtot / n, coverage=T / float(g.sum()),
                n_truth=int(g.sum()),
                dti=M.dti_from_components(T, fp, fn, M.ALPHA, M.BETA))


def main() -> int:
    t0 = time.time()
    g = load_grid()
    footprint, catalogue = g.footprint, g.catalogue
    shape = g.shape

    # --- truth set 1: SGMC off known, reproducing scripts/calibrate_registry.py
    with rasterio.open(DATA / "external/derived_sgmc_faults_100m.tif") as ds:
        sgmc = ds.read(1) > 0
        if (ds.height, ds.width) != shape:
            raise ValueError("SGMC grid mismatch")
    ing_stats, ing_pix, tmap, _ = fz.ingenious_record_segments(
        DATA / "external/trace_segments_utm11.csv", shape, g.transform)
    ingen_mask = tmap > 0
    known = (catalogue | ingen_mask) & footprint
    sgmc_truth = sgmc & ~known & footprint
    print(f"[truth] catalogue={int(catalogue.sum())} ingen_vector={int(ingen_mask.sum())} "
          f"known={int(known.sum())} sgmc={int(sgmc.sum())} sgmc_off_known={int(sgmc_truth.sum())}",
          flush=True)

    # --- truth set 3: pooled hide-and-recover (the repo's current instrument)
    folds, _quad = buffered_component_draw(g, seed=20)
    withheld = np.zeros(shape, bool)
    for f in folds:
        withheld |= f["truth"]
    n_withheld = int(withheld.sum())
    print(f"[truth] withheld_hide_and_recover={n_withheld} folds={len(folds)}", flush=True)

    study = json.loads(STUDY.read_text())
    index = json.loads((ROOT / "evidence" / "registry_refreshed.json").read_text())
    by_sha = {r["sha256"]: r for r in index["rasters"]}

    truth_sets = {
        "sgmc_off_known": (sgmc_truth, footprint, known),
        "catalogue_negative_control": (catalogue, footprint, np.zeros(shape, bool)),
        "withheld_hide_and_recover": (withheld, footprint, known),
    }

    # One profile per distinct raster, shared by every label that joined to it.
    cache: dict[str, dict] = {}
    rows = []
    for r in study["rows"]:
        sha = r["sha256"]
        if sha not in cache:
            p = ROOT / by_sha[sha]["cache_file"]
            pred = read_raster(p)
            pred[~footprint] = 0.0
            entry = {"n_dots": int(((pred > 0) & footprint).sum())}
            for name, (truth, valid, kn) in truth_sets.items():
                entry[name] = credit(pred, truth, valid, kn)
            cache[sha] = entry
            del pred
            gc.collect()
        rows.append(dict(repo=r["repo"], submission=r["submission"], sha256=sha,
                         live_owner_reported=r["live_owner_reported"],
                         **{k: v for k, v in cache[sha].items()}))
        print(f"  [{len(rows):3d}] {r['submission'][:38]:38s} live={r['live_owner_reported']:.4f} "
              f"n={cache[sha]['n_dots']:7d} "
              f"cpd_sgmc={cache[sha]['sgmc_off_known']['credit_per_dot']:.4f} "
              f"cpd_cat={cache[sha]['catalogue_negative_control']['credit_per_dot']:.4f}",
              flush=True)

    distinct = list(cache.values())
    live_of = {}
    for r in rows:
        live_of.setdefault(r["sha256"], r["live_owner_reported"])
    live = np.array([live_of[s] for s in cache], float)
    ns = np.array([v["n_dots"] for v in distinct], float)

    def sp(a, b=None):
        """Spearman vs live as [rho, p]; NaN/inf -> None so JSON stays valid.

        A constant statistic has no defined rank correlation; recording ``null``
        is honest, recording ``nan`` breaks ``allow_nan=False`` serialization.
        """
        x = np.asarray(a, float)
        y = live if b is None else np.asarray(b, float)
        if np.ptp(x) == 0 or np.ptp(y) == 0:
            return [None, None]
        r = spearmanr(y, x)
        out = [float(r.statistic), float(r.pvalue)]
        return [None if not np.isfinite(v) else v for v in out]

    correlations = {"n_distinct_rasters": int(len(distinct))}
    for name in truth_sets:
        cpd = np.array([v[name]["credit_per_dot"] for v in distinct])
        cov = np.array([v[name]["coverage"] for v in distinct])
        dti = np.array([v[name]["dti"] for v in distinct])
        cnt = np.array([v[name]["n"] for v in distinct], float)
        correlations[name] = dict(
            n_truth=int(distinct[0][name]["n_truth"]),
            spearman_live_vs_dti=sp(dti),
            spearman_live_vs_coverage=sp(cov),
            spearman_live_vs_credit_per_dot=sp(cpd),
            spearman_live_vs_n_dots=sp(cnt),
            spearman_credit_per_dot_vs_n_dots=sp(cpd, cnt),
            spearman_dti_vs_n_dots=sp(dti, cnt),
            cpd_min=float(cpd.min()), cpd_max=float(cpd.max()),
        )

    payload = dict(
        evidence_class="REGISTRY-MEASUREMENT + OWNER-REPORTED live scores (not ORGANIZER-CONFIRMED)",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        metric_constants=dict(alpha=M.ALPHA, beta=M.BETA, radius_px=M.RADIUS_PX),
        truth_sets={k: int((v[0] & v[1] & ~v[2]).sum()) for k, v in truth_sets.items()},
        withheld_positive_pixels=n_withheld,
        correlations=correlations,
        rows=sorted(rows, key=lambda r: -r["live_owner_reported"]),
        runtime_s=time.time() - t0,
        caveat=("Live scores are OWNER-REPORTED public-page values, not submission-page receipts. "
                "credit_per_dot = M/n is free of the instrument's truth size G and scale-free in n, "
                "so it is the only one of these statistics that can rank two placements at matched "
                "budget. A clean rank correlation over a self-selected raster family is calibration "
                "evidence for this registry, not proof about the organizer's private truth."),
    )
    OUT.write_text(json.dumps(payload, indent=1, allow_nan=False) + "\n")

    print(f"\n=== Spearman vs OWNER-REPORTED live (n={len(distinct)} distinct rasters) ===")
    print(f"{'truth set':32s} {'|G|':>8s} {'DTI':>8s} {'coverage':>9s} {'CREDIT/DOT':>11s} {'n_dots':>8s}")
    for name in truth_sets:
        c = correlations[name]
        f = lambda v: float('nan') if v is None else v
        print(f"{name:32s} {c['n_truth']:8d} {f(c['spearman_live_vs_dti'][0]):+8.4f} "
              f"{f(c['spearman_live_vs_coverage'][0]):+9.4f} "
              f"{f(c['spearman_live_vs_credit_per_dot'][0]):+11.4f} "
              f"{f(c['spearman_live_vs_n_dots'][0]):+8.4f}")
    print(f"\ncredit_per_dot vs n_dots (is the statistic budget-free?):")
    for name in truth_sets:
        v = correlations[name]['spearman_credit_per_dot_vs_n_dots'][0]
        print(f"  {name:32s} rho={'n/a' if v is None else f'{v:+.4f}'}")
    print(f"\nwrote {OUT.relative_to(ROOT)}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
