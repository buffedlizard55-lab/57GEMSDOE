#!/usr/bin/env python3
"""What distinguishes the top owner-reported rasters at MATCHED dot budget?

The two offline instruments in this repository (hide-and-recover, SGMC-off-known)
both anti-correlate with owner-reported live score, so neither can rank a
placement.  This script therefore asks a purely descriptive question that needs
no truth proxy at all:

    Among rasters with almost the same emitted dot count, which measurable
    geometric properties separate the 0.2778 file from the 0.271 / 0.275 files?

For every pair it reports exact set relations (subset / superset / Jaccard /
3 px overlap), and for the symmetric difference it reports the distance-to-
catalogue distribution of the dots each file has and the other lacks.  A nested
pair (one file an exact subset of the other) is the cleanest possible natural
experiment: the score difference is attributable to the removed dots alone.

Evidence class: REGISTRY-MEASUREMENT + OWNER-REPORTED scores.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid  # noqa: E402
from gems57.metric import RADIUS_PX  # noqa: E402

OUT = ROOT / "evidence" / "top_family_anatomy.json"
STUDY = ROOT / "evidence" / "live_geometry_study.json"
RP = int(RADIUS_PX)


def dots_of(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    a = np.where(np.isfinite(a), a, 0.0)
    a[~footprint] = 0.0
    return (a > 0) & footprint


def dist_profile(d: np.ndarray) -> dict:
    if d.size == 0:
        return dict(n=0)
    return dict(n=int(d.size), mean=float(d.mean()), median=float(np.median(d)),
                p05=float(np.percentile(d, 5)), p25=float(np.percentile(d, 25)),
                p75=float(np.percentile(d, 75)), p95=float(np.percentile(d, 95)),
                min=float(d.min()), max=float(d.max()),
                frac_le1=float((d <= 1).mean()), frac_le2=float((d <= 2).mean()),
                frac_le3=float((d <= 3).mean()), frac_1to2=float(((d > 1) & (d <= 2)).mean()),
                frac_le5=float((d <= 5).mean()), frac_gt10=float((d > 10).mean()),
                hist_0_2_4_6_10_20_40_inf=[int(x) for x in np.histogram(
                    d, bins=[0, 2, 4, 6, 10, 20, 40, np.inf])[0]])


def main() -> int:
    g = load_grid()
    footprint, catalogue = g.footprint, g.catalogue
    dist_cat = ndi.distance_transform_edt(~catalogue)
    allowed = footprint & ~catalogue

    yy, xx = np.mgrid[-RP:RP + 1, -RP:RP + 1]
    disc = ((yy * yy + xx * xx) <= RP * RP).astype(np.float32)

    study = json.loads(STUDY.read_text())
    index = json.loads((ROOT / "evidence" / "registry_refreshed.json").read_text())
    by_sha = {r["sha256"]: r for r in index["rasters"]}

    # Keep every labelled raster in the competitive band, plus the extremes that
    # bound it, so the comparison is not restricted to one family.
    rows = [r for r in study["rows"] if r["n_dots"] > 0]
    rows.sort(key=lambda r: -r["live_owner_reported"])
    top = rows[:14]
    contrast = [r for r in rows if r["live_owner_reported"] <= 0.06][:6]

    sets: dict[str, np.ndarray] = {}
    meta = []
    for r in top + contrast:
        sha = r["sha256"]
        if sha in sets:
            continue
        p = ROOT / by_sha[sha]["cache_file"]
        s = dots_of(p, footprint)
        sets[sha] = s
        d = dist_cat[s]
        # nearest-neighbour separation between dots: how regularly spaced they are
        lab, n = ndi.label(s, structure=np.ones((3, 3), bool))
        sizes = np.bincount(lab.ravel(), minlength=n + 1)[1:]
        neigh = ndi.convolve(s.astype(np.float32), disc, mode="constant")
        meta.append(dict(
            sha256=sha, repo=r["repo"], submission=r["submission"],
            live_owner_reported=r["live_owner_reported"], n_dots=int(s.sum()),
            n_on_catalogue=int((s & catalogue).sum()),
            dist_to_catalogue=dist_profile(d),
            frac_in_allowed=float(s[allowed].mean()) if s.any() else 0.0,
            n_8conn_clusters=int(n),
            mean_cluster_px=float(sizes.mean()) if sizes.size else 0.0,
            max_cluster_px=int(sizes.max()) if sizes.size else 0,
            frac_isolated_singletons=float((sizes == 1).sum() / max(n, 1)) if sizes.size else 0.0,
            mean_dots_in_3px_disc=float((neigh[s] - 1).mean()),
            coverage_of_allowed_by_3px=float((neigh > 0)[allowed].mean()),
            spread_row_sd=float(np.std(np.nonzero(s)[0])) if s.any() else 0.0,
            spread_col_sd=float(np.std(np.nonzero(s)[1])) if s.any() else 0.0,
        ))
        print(f"  profiled {r['submission'][:36]:36s} live={r['live_owner_reported']:.4f} "
              f"n={int(s.sum()):7d} dmed={np.median(dist_cat[s]) if s.any() else -1:6.2f} "
              f"clusters={n:6d} cov3px={meta[-1]['coverage_of_allowed_by_3px']:.4f}", flush=True)

    # Pairwise set relations within the competitive band.
    pairs = []
    band = [m for m in meta if m["live_owner_reported"] >= 0.22]
    for i in range(len(band)):
        for j in range(i + 1, len(band)):
            a, b = sets[band[i]["sha256"]], sets[band[j]["sha256"]]
            na, nb = int(a.sum()), int(b.sum())
            inter = int((a & b).sum())
            union = int((a | b).sum())
            near_b = ndi.binary_dilation(b, structure=disc > 0)
            near_a = ndi.binary_dilation(a, structure=disc > 0)
            only_a, only_b = a & ~b, b & ~a
            pairs.append(dict(
                a=band[i]["submission"], a_live=band[i]["live_owner_reported"], a_n=na,
                b=band[j]["submission"], b_live=band[j]["live_owner_reported"], b_n=nb,
                intersection=inter, union=union,
                jaccard=inter / union if union else 0.0,
                frac_a_within_3px_of_b=float(near_b[a].mean()) if na else 0.0,
                frac_b_within_3px_of_a=float(near_a[b].mean()) if nb else 0.0,
                a_subset_of_b=bool(na > 0 and inter == na),
                b_subset_of_a=bool(nb > 0 and inter == nb),
                only_a_dist=dist_profile(dist_cat[only_a]),
                only_b_dist=dist_profile(dist_cat[only_b]),
            ))
            tag = ""
            if pairs[-1]["a_subset_of_b"]:
                tag = "  <== A IS AN EXACT SUBSET OF B"
            if pairs[-1]["b_subset_of_a"]:
                tag = "  <== B IS AN EXACT SUBSET OF A"
            print(f"  {band[i]['submission'][:26]:26s}({band[i]['live_owner_reported']:.4f}) vs "
                  f"{band[j]['submission'][:26]:26s}({band[j]['live_owner_reported']:.4f}) "
                  f"J={pairs[-1]['jaccard']:.4f} 3px={pairs[-1]['frac_a_within_3px_of_b']:.4f}{tag}",
                  flush=True)

    payload = dict(
        evidence_class="REGISTRY-MEASUREMENT + OWNER-REPORTED live scores (not ORGANIZER-CONFIRMED)",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        footprint_px=int(footprint.sum()), catalogue_px=int(catalogue.sum()),
        allowed_px=int(allowed.sum()), kernel_radius_px=RP,
        rasters=meta, pairs=pairs,
        caveat=("Set relations and distance profiles are exact byte-level measurements. "
                "Live scores are OWNER-REPORTED public-page values, not receipts. "
                "No truth proxy is used here, so nothing in this file is a DTI prediction."),
    )
    OUT.write_text(json.dumps(payload, indent=1, allow_nan=False) + "\n")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
