#!/usr/bin/env python3
"""Uniqueness of one candidate raster against the FULL GEMSDOE registry.

Input : evidence/registry_full_index.json  (built by scripts/scan_gemsdoe_registry.py index)
Gates : the parallel-run protocol, computed by gems57.uniqueness.compare_to_registry:
          * rank:    full-footprint Spearman > 0.90            -> duplicate
          * overlap: > 70 % of my dots within 3 px of one registry raster's dots -> duplicate
          * jaccard: > 0.50 (exact-copy / re-export detector)  -> duplicate
        The overlap gate is one-directional as written in the protocol. For dense
        registry rasters (300k+ dots) a forward overlap > 0.70 is mechanical (their
        dots cover the candidate), so every such firing is ALSO reported with the
        reverse overlap, as the earlier evidence did (IR-57-OVL-01).

Usage : python scripts/check_uniqueness_full.py <candidate.tif> <label> [--out evidence/...json]
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

from gems57 import load_grid                          # noqa: E402
from gems57.uniqueness import compare_to_registry, dot_overlap  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path)
    ap.add_argument("label")
    ap.add_argument("--index", type=Path, default=ROOT / "evidence" / "registry_full_index.json")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    idx = json.loads(a.index.read_text())
    recs = []
    for r in idx["rasters"]:
        recs.append({"repo": r["repo_first"], "submission": r["sources"][0],
                     "owner_reported_score": None, "file": r["cache_file"],
                     "sha256": r["sha256"]})
    tmp = ROOT / "evidence" / f".registry_tmp_{a.label}.json"
    tmp.write_text(json.dumps(recs))
    g = load_grid()
    res = compare_to_registry(a.candidate, tmp, g.footprint)
    tmp.unlink()

    mine = rasterio.open(a.candidate).read(1)
    mine = np.where(np.isfinite(mine), mine, 0.0)
    # two-sided view for every firing of the one-directional overlap gate
    firings = []
    for row in res["rows"]:
        if "error" in row or not row.get("duplicate_by_overlap"):
            continue
        t = rasterio.open(next(r["file"] for r in recs if r["submission"] == row["submission"]
                               and r["repo"] == row["repo"])).read(1)
        t = np.where(np.isfinite(t), t, 0.0)
        rev = dot_overlap(t, mine)
        firings.append({"submission": row["submission"], "repo": row["repo"],
                        "their_dots": row["their_dots"],
                        "fwd_overlap": row["my_dots_within_3px_of_theirs"],
                        "rev_overlap": rev,
                        "spearman": row["spearman_full_footprint"],
                        "mechanical_saturation": bool(rev < 0.5)})
    n_true_dup = sum(1 for f in firings if not f["mechanical_saturation"])
    n_rho = sum(1 for r in res["rows"] if r.get("duplicate_by_rho"))
    n_jac = sum(1 for r in res["rows"] if r.get("duplicate_by_jaccard"))
    top = sorted((r for r in res["rows"] if "error" not in r),
                 key=lambda r: -r["spearman_full_footprint"])[:5]
    out = {
        "evidence_class": "MEASUREMENT (full GEMSDOE registry uniqueness scan)",
        "label": a.label,
        "candidate": {"file": a.candidate.name, "sha256": _sha(a.candidate),
                      "dots": int((mine > 0).sum())},
        "registry": {"n_unique_grid_rasters": idx["n_unique_grid_rasters"],
                     "repos_scanned": len(idx["repos_scanned"]),
                     "repos_unreachable_or_missing": idx["repos_unreachable_or_missing"],
                     "skipped": idx["skipped"]},
        "limits": {"spearman": res["rho_limit"], "dot_overlap_3px": res["overlap_limit"],
                   "jaccard": res["jaccard_limit"]},
        "max_spearman_full_footprint": {"value": res["worst_spearman_full_footprint"],
                                        "raster": res["worst_rho_submission"]},
        "max_dot_overlap_fwd_3px": {"value": res["worst_dot_overlap"],
                                    "raster": res["worst_overlap_submission"]},
        "max_jaccard": {"value": res["worst_jaccard_dot_sets"],
                        "raster": res["worst_jaccard_submission"]},
        "n_duplicate_by_rho": n_rho,
        "n_duplicate_by_jaccard": n_jac,
        "n_overlap_firings_one_directional": len(firings),
        "n_overlap_firings_two_sided_true_duplicates": n_true_dup,
        "overlap_firings": firings,   # complete list (an earlier version truncated to 50; IR-57-UNIQ-02)
        "top5_by_spearman": [{"submission": r["submission"], "repo": r["repo"],
                              "spearman": r["spearman_full_footprint"],
                              "fwd_overlap": r["my_dots_within_3px_of_theirs"]} for r in top],
        # LITERAL protocol: any forward overlap > 0.70 (one registry raster) is drift -> log and stop.
        "unique_by_protocol": bool(n_rho == 0 and n_jac == 0 and len(firings) == 0),
        # informational only: the two-sided reading (reverse overlap < 0.5 called "mechanical").
        # It is NOT a clearance rule in the protocol and must not be used as one without a user decision.
        "informational_two_sided_true_duplicates": n_true_dup,
        "verdict": ("UNIQUE vs every accessible GEMSDOE raster (literal gates)" if (n_rho == 0 and n_jac == 0 and len(firings) == 0)
                    else f"DRIFT-FLAGGED by the literal forward-overlap gate ({len(firings)} registry rasters > 0.70): log and stop; NOT cleared for submission"),
    }
    out_path = a.out or (ROOT / "evidence" / f"uniqueness_full_{a.label}.json")
    out_path.write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(json.dumps({k: out[k] for k in ["candidate", "max_spearman_full_footprint",
                                          "max_dot_overlap_fwd_3px", "max_jaccard",
                                          "n_duplicate_by_rho", "n_overlap_firings_one_directional",
                                          "n_overlap_firings_two_sided_true_duplicates", "verdict"]},
                     indent=2, default=float))
    print(f"wrote {out_path}")
    return 0


def _sha(p: Path) -> str:
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


if __name__ == "__main__":
    sys.exit(main())
