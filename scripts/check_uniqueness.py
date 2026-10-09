#!/usr/bin/env python3
"""Fail-closed uniqueness audit for the current local candidate.

This replaces an obsolete script that depended on /home/user/registry and a
missing final_surface.npz. By default it audits final dots against the pinned
local inventory plus other top-level downloads. Pass --surface with a saved
2-D .npz (key ``surface``) or single-band GeoTIFF to add the required
pre-placement Spearman check. Without that input, the surface phase is reported
NOT RUN, exits nonzero, and never returns a promotion-eligible verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems57 import load_grid  # noqa: E402
from gems57.uniqueness import compare_surface_to_registry, compare_to_registry  # noqa: E402
from build_submission import runtime_registry_index  # noqa: E402


def _surface(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".npz":
        with np.load(path, allow_pickle=False) as data:
            if "surface" not in data:
                raise ValueError("surface NPZ must contain a 'surface' array")
            return np.asarray(data["surface"], dtype=np.float32)
    with rasterio.open(path) as src:
        if src.count != 1:
            raise ValueError("surface TIFF must be single-band")
        return src.read(1).astype(np.float32)


def _json_safe(value):
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", type=Path,
                    help="candidate TIFF (default: evidence/run_card.json raster_path)")
    ap.add_argument("--surface", type=Path,
                    help="optional saved surface NPZ ('surface' key) or single-band TIFF")
    ap.add_argument("--output", type=Path,
                    default=ROOT / "evidence" / "uniqueness_cli.json")
    args = ap.parse_args()

    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    candidate = args.candidate or (ROOT / card["raster_path"])
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    grid = load_grid()
    index = runtime_registry_index(exclude=candidate)
    try:
        final = compare_to_registry(candidate, index, grid.footprint)
        if args.surface:
            surface_path = args.surface if args.surface.is_absolute() else ROOT / args.surface
            s = _surface(surface_path)
            surface = compare_surface_to_registry(s, index, grid.footprint)
            surface["surface_path"] = str(surface_path.resolve())
            surface["registry_index"] = "temporary merged local inventory"
        else:
            surface = {"phase": "surface-before-placement", "status": "NOT RUN",
                       "reason": "no saved pre-placement surface supplied",
                       "unique_within_inventory": False}
        eligible = bool(surface.get("unique_within_inventory") and final.get("unique")
                        and card.get("promote"))
        payload = {
            "evidence_class": "LOCAL UNIQUENESS AUDIT",
            "candidate": str(candidate),
            "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
            "inventory_raster_count": final.get("n_registry_rows"),
            "surface_audit": surface,
            "final_dot_audit": final,
            "promotion_eligible": eligible,
            "scope": "pinned registry/audit_index.json plus other existing docs/downloads/*.tif (candidate excluded); finite local inventory, not a complete competition-wide registry",
            "organizer_receipt_present": False,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(_json_safe(payload), indent=2, allow_nan=False) + "\n")
        print("surface phase:", surface.get("status", surface.get("unique_within_inventory")))
        print("final-dot inventory complete:", final.get("audit_complete"))
        print("final-dot unique within inventory:", final.get("unique"))
        audit_passed = bool(surface.get("unique_within_inventory")
                            and final.get("audit_complete") and final.get("unique"))
        print("promotion eligible:", eligible)
        print("complete two-phase audit passed:", audit_passed)
        print("wrote", output)
        return 0 if audit_passed else 1
    finally:
        index.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
