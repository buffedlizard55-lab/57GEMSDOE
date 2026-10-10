#!/usr/bin/env python3
"""Literal fault-zone-lane registry gate for an emission surface or final dots.

This checker applies the standing protocol to every unique, aligned raster in
``evidence/registry_full_index.json``. The surface phase uses full-footprint
Spearman before allocation. The dots phase uses full-footprint Spearman plus the
one-way fraction of candidate dots within 3 px of each prior raster's positive
pixels. There is no Jaccard threshold, no reverse-overlap exemption, and no
silent clearance when inventory files are missing.

For the candidate builder, call the same functions in memory before writing a
GeoTIFF. This script is the reproducible on-disk entry point for later audits.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np                                    # noqa: E402
import rasterio                                       # noqa: E402

from gems57 import load_grid                         # noqa: E402
from gems57.uniqueness import (compare_dots_to_registry,
                               compare_surface_to_registry)  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path,
                    help="single-band aligned surface or binary final-dot raster")
    ap.add_argument("label", help="short run label for the output filename")
    ap.add_argument("--phase", choices=("surface", "dots"), required=True)
    ap.add_argument("--index", type=Path, default=ROOT / "evidence" / "registry_full_index.json")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--scan-all", action="store_true",
                    help="do not short-circuit after the first literal duplicate firing")
    a = ap.parse_args()

    grid = load_grid()
    with rasterio.open(a.candidate) as ds:
        if ds.count != 1 or ds.shape != grid.shape or str(ds.crs) != str(grid.crs):
            raise SystemExit("candidate must be a single-band raster aligned to the competition grid")
        values = ds.read(1)
        if tuple(ds.transform)[:6] != tuple(grid.transform)[:6]:
            raise SystemExit("candidate transform does not match the competition grid")
    values = np.where(np.isfinite(values), values, 0.0).astype(np.float32)
    if (values < 0).any() or (values > 1).any():
        raise SystemExit("candidate values must be finite in [0,1]")

    stop_on_first = not a.scan_all
    if a.phase == "surface":
        result = compare_surface_to_registry(values, a.index, grid.footprint,
                                             stop_on_first=stop_on_first)
    else:
        dots = (values > 0.0) & grid.footprint
        if not dots.any() or not np.isin(values[grid.footprint], [0.0, 1.0]).all():
            raise SystemExit("dots phase requires a non-empty binary 0/1 raster")
        result = compare_dots_to_registry(values, dots, a.index, grid.footprint,
                                          stop_on_first=stop_on_first)
    result["evidence_class"] = "literal registry uniqueness diagnostic; not a score or organizer confirmation"
    result["candidate_file"] = str(a.candidate)
    result["candidate_sha256"] = __import__("hashlib").sha256(a.candidate.read_bytes()).hexdigest()
    result["label"] = a.label
    result["phase"] = a.phase
    out_path = a.out or (ROOT / "evidence" / f"uniqueness_full_{a.phase}_{a.label}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in (
        "phase", "candidate_sha256", "n_registry_indexed", "n_registry_checked",
        "registry_complete", "max_spearman_full_footprint",
        "max_dot_overlap_fwd_3px", "n_rho_firings", "n_overlap_firings",
        "first_firing", "verdict") if k in result}, indent=2, allow_nan=False))
    print(f"wrote {out_path}")
    return 0 if result["unique_by_protocol"] else 2


if __name__ == "__main__":
    sys.exit(main())
