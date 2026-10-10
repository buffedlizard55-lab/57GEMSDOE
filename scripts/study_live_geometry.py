#!/usr/bin/env python3
"""File-level geometry study of owner-reported live scores across the full registry.

Question (owner request): *why* did the 0.2778 raster score highest, and can a
raster be designed to beat it?

Everything here is measured from TIFF bytes that are hash-pinned in the
refreshed public registry index (``evidence/registry_refreshed.json``, fetched by
``scripts/refresh_registry.py`` through the GitHub blob API and verified against
their immutable Git blob SHA-1).  Scores joined to those bytes are
**OWNER-REPORTED** values pasted by the owner from public repository pages.
They are *not* ORGANIZER-CONFIRMED receipts and *not* HOLDOUT-DTI readings.

The study deliberately does NOT fit a model to the holdout.  It answers a
different, purely descriptive question: which measurable properties of a
submission raster covary with the owner-reported live score?  The DTI algebra in
``src/gems57/metric.py`` then says whether that covariance has a mechanism.

Usage::

    .venv/bin/python scripts/study_live_geometry.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid  # noqa: E402
from gems57.metric import ALPHA, BETA, RADIUS_PX  # noqa: E402

OUT = ROOT / "evidence" / "live_geometry_study.json"

# ---------------------------------------------------------------------------
# Owner-reported live scores, transcribed from the owner's prompt.  Each entry
# is (repository, distinctive basename substring, reported score).  A raster is
# joined only when BOTH the repository and the substring match a registry source
# path, so a score can never be attached to the wrong bytes.
# ---------------------------------------------------------------------------
OWNER_REPORTED: list[tuple[str, str, float]] = [
    ("GEMSDOE", "gems-submission-20260925T001403Z-7f00890a", 0.1563),
    ("6GEMSDOE", "gems6_hgb88-topk03", 0.0286),
    ("GEMSDOE3", "pindrop-v4-nodes", 0.1193),
    ("GEMSDOE3", "pindrop-v4-discovery", 0.0830),
    ("GEMSDOE3", "pindrop-v4-ridge", 0.1152),
    ("GEMSDOE2", "gemsdoe2-dual-family-union", 0.1560),
    ("GEMSDOE4", "gems-submission-20260926T163915Z-237f0063", 0.0343),
    ("5GEMSDOE", "gems-submission-20260926T175114Z-7f00890a", 0.1563),
    ("7GEMSDOE", "lidarscarp-ridge-top2pct", 0.1461),
    ("8GEMSDOE", "Hedge-v2", 0.1563),
    ("GEMSDOE9", "2314b599", 0.0107),
    ("11GEMSDOE", "gems-structural-area06-v1", 0.0202),
    ("12GEMSDOE", "r7-nms3-dem10-scarp", 0.1294),
    ("15GEMSDOE", "gems-tso1-20260929T005627Z-conj_alteration_mag", 0.0782),
    ("14GEMSDOE", "GEMS_r5-geom-horse-ensemble", 0.0020),
    ("17GEMSDOE", "17GEMSDOE_F-ensemble-2pct", 0.0187),
    ("18GEMSDOE", "H19-C_20260930T212401Z", 0.0297),
    ("19GEMSDOE", "h19-4-multiline-corroborated-openness-thermal-pop", 0.1894),
    ("19GEMSDOE", "h19-5-powerlaw-budget-multiline-corroborated", 0.1922),
    ("GEMSDOE10", "h16-continuation", 0.0461),
    ("GEMSDOE10", "h20-dem10-scarp-thin", 0.0921),
    ("GEMSDOE10", "H25-ctx-ridge", 0.1280),
    ("GEMSDOE10", "h28-dotted-ridge", 0.1839),
    ("13GEMSDOE", "20261001_r13-lattice-s5_v2", 0.0904),
    ("16GEMSDOE", "h16-1-topo-geophys-baseline-ridges", 0.1855),
    ("16GEMSDOE", "h18-3a-topo-geophys-x-complexity-prior", 0.0976),
    ("16GEMSDOE", "h18-4-usgs-geologic-map-faults-gap", 0.0360),
    ("GEMSDOE21", "h19-4-reference", 0.1894),
    ("20GEMSDOE", "h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack", 0.1890),
    ("20GEMSDOE", "h20-5-continuous-pu-proxy", 0.1859),
    ("GEMSDOE22", "h23-a-dti-optimal-emission-6pct", 0.1002),
    ("GEMSDOE22", "h23-b-dti-optimal-emission-10pct", 0.0748),
    ("GEMSDOE23", "h30-arrangement-matched-habitat", 0.1352),
    ("GEMSDOE24", "h25-1-dotted-h19-5-d1-5", 0.2477),
    ("GEMSDOE25", "dotted-h19-5-d2-8", 0.2600),
    ("GEMSDOE26", "dilcond-oof-v1", 0.1223),
    ("GEMSDOE27", "topo-gap-closure-t-v2-on-d1-5", 0.2449),
    ("GEMSDOE30", "d28-poisson300m-offcat-44090", 0.2600),
    ("GEMSDOE31", "h27-4-solo-d28", 0.2708),
    ("GEMSDOE33", "h33d-analog-tip-stepover-r30", 0.2632),
    ("GEMSDOE34", "h34-scatter-q50-arr-matched", 0.0778),
    ("GEMSDOE35", "h35-06-aaa86efb25", 0.0418),
    ("GEMSDOE36", "anderson-geothermal-pinn-38854", 0.2750),
    ("GEMSDOE37", "h6-physics-dotted-80k", 0.1193),
    ("GEMSDOE38", "D-step-3p0-07pct-tipProt", 0.0763),
    ("GEMSDOE42", "xscale-worm-persistence", 0.0581),
    ("GEMSDOE43", "sup01-hgb21-sep40-n40000", 0.0424),
    ("GEMSDOE45", "h51-km-faultzone", 0.0106),
    ("GEMSDOE49", "gate_ortho_w0.25-40k", 0.2376),
    ("GEMSDOE32", "h33-h33-2-b2", 0.2778),
    ("GEMSDOE28", "h27-4-r1-solo-d2-8", 0.2708),
    ("GEMSDOE28", "h32-1-prethin-tip-euler-d2-8", 0.2649),
    ("GEMSDOE28", "h36-1-rung30-blind-r1", 0.2710),
    ("GEMSDOE28", "h38-1-hf-euler-r30-r1", 0.2707),
    ("GEMSDOE29", "efd28-repro", 0.2600),
    ("GEMSDOE29", "repo-c0-habitat-emission", 0.0041),
    ("GEMSDOE29", "sgmc-off-catalogue-44k", 0.0512),
    ("GEMSDOE29", "wormrank-d28", 0.2560),
    ("GEMSDOE29", "wormsurv-filter", 0.0532),
    ("GEMSDOE29", "xfit-c0-habitat", 0.0439),
    ("GEMSDOE46", "r11f-scarp-radiometric-fusion", 0.1589),
    ("GEMSDOE46", "r12-scarp-rad-concordance", 0.0843),
    ("GEMSDOE39", "h40-e-disc-h40e-30k", 0.0339),
    ("GEMSDOE40", "h8-euler-lineament-depthcluster", 0.0355),
    ("GEMSDOE41", "h42-submission-primary", 0.0245),
    ("GEMSDOE44", "h46-twostageAB", 0.0715),
    ("GEMSDOE47", "h60-lidarscarp-s2p0", 0.0430),
    ("GEMSDOE48", "h59-cover-ds-belief-b2xh33d", 0.2296),
    ("GEMSDOE50", "h59-sharpened-scarp-scatter-90k", 0.0764),
    ("GEMSDOE51", "h53-twostage", 0.1047),
    ("GEMSDOE53", "h8-tiprelay-ridgeconcord-pr2-n80000", 0.0159),
]

DIST_EDGES = np.array([0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 20.0, 40.0, np.inf])


def profile(path: Path, footprint: np.ndarray, catalogue: np.ndarray,
            dist_cat: np.ndarray) -> dict | None:
    with rasterio.open(path) as src:
        if src.count != 1 or (src.height, src.width) != footprint.shape:
            return None
        a = src.read(1)
    a = np.where(np.isfinite(a), a, 0.0).astype(np.float64)
    a[~footprint] = 0.0
    dots = (a > 0) & footprint
    n = int(dots.sum())
    if n == 0:
        return dict(n_dots=0)
    d = dist_cat[dots]
    v = a[dots]
    # Local dot density: how many other dots sit within the scoring kernel radius.
    yy, xx = np.mgrid[-RADIUS_PX:RADIUS_PX + 1, -RADIUS_PX:RADIUS_PX + 1]
    kernel = ((yy * yy + xx * xx) <= RADIUS_PX * RADIUS_PX).astype(np.float32)
    neigh = ndi.convolve(dots.astype(np.float32), kernel.astype(np.float32), mode="constant")
    nb = neigh[dots] - 1.0  # exclude self
    hist, _ = np.histogram(d, bins=DIST_EDGES)
    return dict(
        n_dots=n,
        n_on_catalogue=int((dots & catalogue).sum()),
        frac_on_catalogue=float((dots & catalogue).mean()),
        d_min=float(d.min()), d_p05=float(np.percentile(d, 5)),
        d_p25=float(np.percentile(d, 25)), d_median=float(np.median(d)),
        d_p75=float(np.percentile(d, 75)), d_p95=float(np.percentile(d, 95)),
        d_mean=float(d.mean()),
        frac_d_le1=float((d <= 1).mean()), frac_d_le2=float((d <= 2).mean()),
        frac_d_le3=float((d <= 3).mean()), frac_d_le5=float((d <= 5).mean()),
        frac_d_le8=float((d <= 8).mean()), frac_d_gt20=float((d > 20).mean()),
        dist_hist=[int(x) for x in hist],
        value_min=float(v.min()), value_max=float(v.max()),
        value_mean=float(v.mean()), n_distinct_values=int(len(np.unique(v))),
        is_binary=bool(len(np.unique(v)) <= 2),
        mean_neighbours_in_kernel=float(nb.mean()),
        frac_isolated=float((nb == 0).mean()),
        coverage_3px=float((neigh > 0)[footprint & ~catalogue].mean()),
    )


def main() -> int:
    g = load_grid()
    footprint, catalogue = g.footprint, g.catalogue
    # Distance from every cell to the nearest mapped catalogue pixel.
    dist_cat = ndi.distance_transform_edt(~catalogue)

    index = json.loads((ROOT / "evidence" / "registry_refreshed.json").read_text())
    by_sha = {r["sha256"]: r for r in index["rasters"]}

    rows, unmatched, joined_sha = [], [], {}
    for repo, substr, live in OWNER_REPORTED:
        hits = []
        for sha, rec in by_sha.items():
            for src in rec["sources"]:
                r, _, p = src.partition(":")
                if r == repo and substr.lower() in Path(p).name.lower():
                    hits.append((sha, src))
        if not hits:
            unmatched.append(dict(repo=repo, substring=substr, live=live,
                                  reason="no registry source path matched"))
            continue
        sha, src = sorted(hits)[0]
        if sha in joined_sha:  # identical bytes already profiled under another label
            prof = joined_sha[sha]
        else:
            p = ROOT / by_sha[sha]["cache_file"]
            prof = profile(p, footprint, catalogue, dist_cat)
            joined_sha[sha] = prof
        if prof is None:
            unmatched.append(dict(repo=repo, substring=substr, live=live,
                                  reason="not a single-band competition-grid raster"))
            continue
        rows.append(dict(repo=repo, submission=substr, source=src, sha256=sha,
                         live_owner_reported=live, **prof))

    labelled = [r for r in rows if r["n_dots"] > 0]
    stats = {}
    if len(labelled) >= 8:
        live = np.array([r["live_owner_reported"] for r in labelled], float)
        for key in ("n_dots", "frac_on_catalogue", "d_median", "d_mean", "d_p25",
                    "frac_d_le1", "frac_d_le2", "frac_d_le3", "frac_d_le5",
                    "frac_d_gt20", "mean_neighbours_in_kernel", "frac_isolated",
                    "coverage_3px", "value_mean"):
            x = np.array([float(r[key]) for r in labelled])
            if np.ptp(x) == 0:
                continue
            res = spearmanr(live, x)
            stats[key] = dict(spearman=float(res.statistic), p_value=float(res.pvalue),
                              n=int(len(x)))
        # The DTI algebra gives one physically motivated composite: mean credit
        # per dot under the 300 m triangular kernel, using the *catalogue* as a
        # stand-in for truth.  This is a diagnostic, not a score.
        rho = float(spearmanr(live, [1.0 / r["n_dots"] for r in labelled]).statistic)
        stats["inverse_n_dots"] = dict(spearman=rho, n=len(labelled))

    payload = dict(
        evidence_class="REGISTRY-MEASUREMENT + OWNER-REPORTED live scores (not ORGANIZER-CONFIRMED)",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        registry_index="evidence/registry_refreshed.json",
        registry_rasters_indexed=int(index["n_unique_grid_rasters"]),
        registry_complete_accessible_scan=bool(index["complete_accessible_scan"]),
        registry_errors=int(len(index["errors"])),
        metric_constants=dict(alpha=ALPHA, beta=BETA, radius_px=RADIUS_PX),
        distance_edges_m=[float(e * 100.0) for e in DIST_EDGES[:-1]] + ["inf"],
        n_owner_reported_labels=len(OWNER_REPORTED),
        n_joined=len(rows), n_labelled_nonempty=len(labelled),
        n_unmatched=len(unmatched), unmatched=unmatched,
        distinct_raster_bytes_profiled=len(joined_sha),
        spearman_vs_live=stats,
        rows=sorted(rows, key=lambda r: -r["live_owner_reported"]),
        caveat=("Owner-reported live scores are pasted public repository values, not submission-page "
                "receipts. Byte-level joins are exact (repository + basename substring + registry SHA256). "
                "Rank correlations across a self-selected family of submissions are confounded with "
                "method quality; they describe this registry, not the organizer's scoring function."),
    )
    OUT.write_text(json.dumps(payload, indent=1, allow_nan=False) + "\n")

    print(f"joined {len(rows)}/{len(OWNER_REPORTED)} owner-reported labels to registry bytes "
          f"({len(joined_sha)} distinct rasters); unmatched {len(unmatched)}")
    print(f"\nSpearman(owner-reported live, geometry), n={len(labelled)}:")
    for k, v in sorted(stats.items(), key=lambda kv: -abs(kv[1]["spearman"])):
        print(f"  {k:28s} rho={v['spearman']:+.4f}  p={v.get('p_value', float('nan')):.2g}")
    print(f"\nTop / bottom by owner-reported live score:")
    for r in sorted(labelled, key=lambda r: -r["live_owner_reported"])[:8]:
        print(f"  {r['live_owner_reported']:.4f}  n={r['n_dots']:7d}  d_med={r['d_median']:5.2f}  "
              f"frac<=2px={r['frac_d_le2']:.3f}  on_cat={r['frac_on_catalogue']:.4f}  "
              f"iso={r['frac_isolated']:.3f}  {r['submission'][:40]}")
    for r in sorted(labelled, key=lambda r: r["live_owner_reported"])[:5]:
        print(f"  {r['live_owner_reported']:.4f}  n={r['n_dots']:7d}  d_med={r['d_median']:5.2f}  "
              f"frac<=2px={r['frac_d_le2']:.3f}  on_cat={r['frac_on_catalogue']:.4f}  "
              f"iso={r['frac_isolated']:.3f}  {r['submission'][:40]}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
