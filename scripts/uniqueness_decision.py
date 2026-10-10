#!/usr/bin/env python3
"""Measure literal forward-overlap behavior on local registry raster bytes.

The comparison panel includes rasters that earlier notes associated with
owner-reported values. Owner-source review now marks H33-2-B2 UNSCORED, leaves
0.2778 unverified and unlinked to exact bytes, and contradicts the 0.2708 file
attribution. This script measures geometry only; it cannot establish that an
organizer-scored submission was rejected or justify changing the gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RADIUS_PX = 3.0
OVERLAP_LIMIT = 0.70
RHO_LIMIT = 0.90
JACCARD_LIMIT = 0.50
BLIND_HALO = 0.70          # halo coverage above which the forward test is blind


def main() -> None:
    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as s:
        fp = np.isfinite(s.read(1))
    reg = json.loads((ROOT / "registry" / "registry_index.json").read_text())
    panel = [
        ("H33-2-B2 raster bytes (owner README: UNSCORED; 0.2778 claim unlinked)",
         "out/live_cache/live_02778_b2prune.tif"),
        ("live_02600_d28.tif (owner-reported value; no exact-file receipt)",
         "out/live_cache/live_02600_d28.tif"),
        ("live_02710_h36rung30.tif (owner-reported value; no exact-file receipt)",
         "out/live_cache/live_02710_h36rung30.tif"),
        ("live_01922_h195.tif (owner-reported value; no exact-file receipt)",
         "out/live_cache/live_01922_h195.tif"),
        ("r13-lattice-s5 (owner-reported value; file-only comparison)",
         "out/live_cache/live_00904_r13lattice.tif"),
    ]
    extra = [{
        "repo": "13GEMSDOE", "submission": "r13-lattice-s5 (file-only comparison)",
        "owner_reported_claim": 0.0904, "score_provenance": "OWNER-REPORTED; no exact-file receipt reviewed",
        "mode": "nan-outside", "file": "out/live_cache/live_00904_r13lattice.tif",
    }]
    reg = extra + reg

    def read(p):
        with rasterio.open(p) as s:
            return np.where(np.isfinite(s.read(1)), s.read(1), 0.0)

    rows = []
    for rec in reg:
        p = ROOT / rec["file"]
        if not p.exists():
            rows.append({"submission": rec["submission"], "error": "missing"})
            continue
        theirs = read(p)
        t = theirs > 0
        d = distance_transform_edt(~t)
        halo = float((d[fp] <= RADIUS_PX).mean())
        fwd = {}
        for nm, xp in panel:
            xp = ROOT / xp
            if not xp.exists():
                continue
            mine = read(xp) > 0
            fwd[nm.split(" ")[0]] = float((d[mine] <= RADIUS_PX).mean())
        rows.append(dict(
            submission=rec["submission"], repo=rec.get("repo"),
            owner_reported_claim=rec.get("owner_reported_claim", rec.get("owner_reported_score")),
            score_provenance=rec.get("score_provenance", "OWNER-REPORTED; not organizer-confirmed"),
            their_dots=int(t.sum()), halo_coverage_of_footprint=halo,
            forward_overlap_of_comparison_rasters=fwd,
            blind_forward_test=bool(halo >= BLIND_HALO)))

    # the panel's own forward overlaps against each other
    cross = []
    for n1, p1 in panel:
        a = read(ROOT / p1) > 0
        for n2, p2 in panel:
            if p1 == p2:
                continue
            b = read(ROOT / p2) > 0
            d = distance_transform_edt(~b)
            cross.append(dict(mine=n1.split(" ")[0], theirs=n2.split(" ")[0],
                              forward_overlap=float((d[a] <= RADIUS_PX).mean()),
                              jaccard=float((a & b).sum() / max((a | b).sum(), 1))))

    out = dict(
        schema="gems57.uniqueness-decision.v1",
        radius_px=RADIUS_PX, overlap_limit=OVERLAP_LIMIT,
        blind_halo_threshold=BLIND_HALO,
        question=("what file geometries trigger the literal forward-overlap gate? "
                  "This panel does not establish that the comparison rasters were organizer-scored."),
        score_provenance_audit="evidence/owner_score_reconciliation_session4.json",
        registry=rows, cross_panel=cross,
    )
    (ROOT / "evidence" / "uniqueness_decision.json").write_text(json.dumps(out, indent=1))

    print(f"{'registry raster':52s} {'dots':>7s} {'halo':>7s} {'blind':>6s}  "
          f"forward overlap of comparison rasters (no score receipt)")
    for r in rows:
        if "error" in r:
            print(f"{r['submission'][:52]:52s} MISSING")
            continue
        f = r["forward_overlap_of_comparison_rasters"]
        s = " ".join(f"{k.split('_')[-1].replace('.tif','')}={v:.3f}" for k, v in f.items())
        print(f"{r['submission'][:52]:52s} {r['their_dots']:7d} "
              f"{r['halo_coverage_of_footprint']:7.4f} "
              f"{'YES' if r['blind_forward_test'] else 'no':>6s}  {s}")
    print()
    print("Forward overlap between local comparison rasters (not submission receipts):")
    for c in cross:
        print(f"  {c['mine']:26s} -> {c['theirs']:26s}  fwd={c['forward_overlap']:.4f}"
              f"  jaccard={c['jaccard']:.4f}")


if __name__ == "__main__":
    main()
