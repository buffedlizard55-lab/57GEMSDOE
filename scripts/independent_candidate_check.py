#!/usr/bin/env python3
"""Session-5 independent re-check of candidate GeoTIFFs (no new placement).

Re-derives the literal gates from src/gems57/uniqueness.py against the LOCAL
registry rasters only (registry/rasters; the full 679-raster inventory is not
present in this checkout). Self-matches (identical sha256) are excluded and
reported separately. Jaccard is diagnostic only; it is not a gate. This local
scan cannot clear an artifact. Writes evidence/independent_candidate_check.json.
"""
import glob, hashlib, json, sys
from pathlib import Path
import numpy as np, rasterio
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems57.uniqueness import dot_overlap, surface_rho, _dots  # shared functions, not a fork
from gems57.metric import RADIUS_PX

CANDIDATES = [
    "docs/downloads/archive/gems57-h57r2-shipped8-all-flank0-20261009T180433Z-90e532947353-zeros.tif",
    "downloads/archive/gems57-relative-strand-surface-20261009T195324Z-88e3bcb35a95.tif",
]
REF = ROOT / "data/official/sample_submission.tif"
OVERLAP_LIMIT, RHO_LIMIT = 0.70, 0.90
WITNESS_SHA256 = "ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be"

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    witness_record = json.loads((ROOT / "evidence/session5_witness_verification.json").read_text())
    witness = witness_record["witness"]
    certificate = json.loads((ROOT / "evidence/uniqueness_saturation_certificate.json").read_text())
    if (witness.get("sha256") != WITNESS_SHA256 or not witness.get("matches_certificate_sha256")
            or certificate.get("witness_sha256") != WITNESS_SHA256
            or not certificate.get("universal_overlap_blocker")):
        raise RuntimeError("Session-5 dense-witness receipts do not match the pinned SHA-256/blocker")
    out = {"evidence_class": "RASTER-MEASUREMENT (not a score)", "radius_px": RADIUS_PX,
           "limits": dict(forward_overlap=OVERLAP_LIMIT, rho_full_footprint=RHO_LIMIT),
           "diagnostics_only": {"jaccard": "reported, not a gate"},
           "registry_scope": "19 local files in registry/rasters; full 679 inventory NOT available here",
           "release_disposition": "NOT CLEARED — local scan is incomplete and the cited dense witness blocks every nonempty candidate under the literal forward-overlap gate",
           "known_dense_witness": {"sha256": WITNESS_SHA256,
                                   "positive_pixels": witness["positive_pixels"],
                                   "allowed_pixels": certificate["allowed_pixels"],
                                   "forward_overlap_any_nonempty_candidate": 1.0,
                                   "derivation": certificate["implication"],
                                   "source_url": witness_record["source_urls"][0]},
           "candidates": []}
    with rasterio.open(REF) as r:
        ref_shape, ref_tr, ref_crs = r.shape, tuple(r.transform)[:6], r.crs.to_string()
    registry = sorted(glob.glob(str(ROOT / "registry/rasters/*.tif")))
    for cp in CANDIDATES:
        cpath = ROOT / cp
        with rasterio.open(cpath) as d:
            m = d.read(1)
            fmt = dict(crs=d.crs.to_string(), shape=list(d.shape), dtype=d.dtypes[0], count=d.count,
                       transform_ok=tuple(d.transform)[:6] == ref_tr,
                       crs_ok=d.crs.to_string() == ref_crs, shape_ok=d.shape == ref_shape,
                       nan_count=int((~np.isfinite(m)).sum()),
                       min=float(np.nanmin(m)), max=float(np.nanmax(m)))
        valid = np.isfinite(m)
        c = dict(file=cp, sha256=sha(cpath), format=fmt, dots=int(_dots(m).sum()), comparisons=[])
        for rp in registry:
            t_sha = sha(rp)
            if t_sha == c["sha256"]:
                c["comparisons"].append(dict(registry=Path(rp).name, self_match=True))
                continue
            with rasterio.open(rp) as r:
                t = r.read(1)
            if t.shape != m.shape:
                c["comparisons"].append(dict(registry=Path(rp).name, error="shape mismatch")); continue
            s = surface_rho(m, t, valid)
            c["comparisons"].append(dict(registry=Path(rp).name, self_match=False,
                                         forward_overlap=dot_overlap(m, t), reverse_overlap=dot_overlap(t, m),
                                         rho_full_footprint=s["spearman_full_footprint"],
                                         jaccard=s["jaccard_dot_sets"]))
        non_self = [x for x in c["comparisons"] if not x.get("self_match") and "error" not in x]
        c["worst_forward_overlap_non_self"] = max(x["forward_overlap"] for x in non_self)
        c["worst_rho_non_self"] = max(x["rho_full_footprint"] for x in non_self)
        c["worst_jaccard_non_self"] = max(x["jaccard"] for x in non_self)
        c["triggered_non_self"] = [x["registry"] for x in non_self
                                   if x["forward_overlap"] > OVERLAP_LIMIT
                                   or x["rho_full_footprint"] > RHO_LIMIT]
        c["literal_gate_pass_local_registry"] = len(c["triggered_non_self"]) == 0
        c["literal_gate_pass_with_known_dense_witness"] = False
        c["forward_overlap_to_known_dense_witness"] = 1.0
        c["witness_overlap_value_source"] = "universal-support certificate; derived, not individually recomputed in this script"
        c["download_status"] = "NOT CLEARED — archive provenance only"
        c["submission_status"] = "NOT SUBMITTED — no organizer receipt exists"
        out["candidates"].append(c)
    p = ROOT / "evidence/independent_candidate_check.json"
    p.write_text(json.dumps(out, indent=2) + "\n")
    for c in out["candidates"]:
        print(c["file"].split("/")[-1][:60], "fwd_worst", round(c["worst_forward_overlap_non_self"], 4),
              "rho_worst", round(c["worst_rho_non_self"], 4), "pass", c["literal_gate_pass_local_registry"],
              "triggered", c["triggered_non_self"])
    print("wrote", p)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
