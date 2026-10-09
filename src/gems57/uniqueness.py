"""Uniqueness check against every earlier raster in the registry.

Parallel-run protocol rule 1: a submission has drifted into another lane if its
rank-correlation with any registry raster exceeds 0.90, or if more than 70 % of
its dots fall within 3 px of one registry raster's dots.  Both statistics are
computed here, on the emission surface *before* placement and on the final dots.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata, spearmanr

from .metric import RADIUS_PX

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70


def _dots(a: np.ndarray) -> np.ndarray:
    return np.asarray(a) > 0


def dot_overlap(mine: np.ndarray, theirs: np.ndarray, radius_px: float = RADIUS_PX) -> float:
    """Fraction of my dots lying within ``radius_px`` of one of their dots."""
    m, t = _dots(mine), _dots(theirs)
    if not m.any():
        return 0.0
    if not t.any():
        return 0.0
    d = distance_transform_edt(~t)
    return float((d[m] <= radius_px).mean())


def surface_rho(mine: np.ndarray, theirs: np.ndarray, valid: np.ndarray) -> dict:
    """Spearman rank correlation of two emission surfaces.

    Computed twice: over the whole footprint (dominated by the shared zero mass,
    so it is a weak statistic) and over the union of the two dot supports (the
    statistic that actually tells you whether the two surfaces put their mass in
    the same places).
    """
    m = np.asarray(mine, np.float32)[valid]
    t = np.asarray(theirs, np.float32)[valid]
    union = (m > 0) | (t > 0)
    out = {}
    if union.sum() > 10:
        out["spearman_on_dot_union"] = float(spearmanr(m[union], t[union]).statistic)
        out["n_dot_union"] = int(union.sum())
    else:
        out["spearman_on_dot_union"] = None
        out["n_dot_union"] = int(union.sum())
    # full-footprint Spearman with ties handled by average ranks
    out["spearman_full_footprint"] = float(spearmanr(m, t).statistic)
    return out


def compare_to_registry(mine_path: Path, registry_index: Path,
                        footprint: np.ndarray) -> dict:
    mine = rasterio.open(mine_path).read(1)
    idx = json.loads(Path(registry_index).read_text())
    rows = []
    worst_rho = -1.0
    worst_overlap = 0.0
    worst_rho_name = worst_overlap_name = ""
    for rec in idx:
        p = Path(rec["file"])
        if not p.exists():
            rows.append({**rec, "error": "missing file"})
            continue
        theirs = rasterio.open(p).read(1)
        theirs = np.where(np.isfinite(theirs), theirs, 0.0)
        rho = surface_rho(mine, theirs, footprint)
        ov = dot_overlap(mine, theirs)
        ov_rev = dot_overlap(theirs, mine)
        rows.append({
            "repo": rec["repo"], "submission": rec["submission"],
            "owner_reported_score": rec["owner_reported_score"],
            "their_dots": int((theirs > 0).sum()),
            "my_dots_within_3px_of_theirs": ov,
            "their_dots_within_3px_of_mine": ov_rev,
            **rho,
            "duplicate_by_rho": bool(rho["spearman_on_dot_union"] is not None
                                     and abs(rho["spearman_on_dot_union"]) > RHO_LIMIT),
            "duplicate_by_overlap": bool(ov > OVERLAP_LIMIT),
        })
        if rho["spearman_on_dot_union"] is not None and abs(rho["spearman_on_dot_union"]) > worst_rho:
            worst_rho = abs(rho["spearman_on_dot_union"]); worst_rho_name = rec["submission"]
        if ov > worst_overlap:
            worst_overlap = ov; worst_overlap_name = rec["submission"]
    unique = not any(r.get("duplicate_by_rho") or r.get("duplicate_by_overlap")
                     for r in rows if "error" not in r)
    return {
        "my_file": str(mine_path),
        "my_dots": int((mine > 0).sum()),
        "rho_limit": RHO_LIMIT, "overlap_limit": OVERLAP_LIMIT,
        "worst_abs_spearman_dot_union": worst_rho, "worst_rho_submission": worst_rho_name,
        "worst_dot_overlap": worst_overlap, "worst_overlap_submission": worst_overlap_name,
        "unique": bool(unique),
        "rows": rows,
    }
