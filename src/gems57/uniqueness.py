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
JACCARD_LIMIT = 0.50


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


def _jaccard(a: np.ndarray, b: np.ndarray) -> float:
    u = int((a | b).sum())
    return float((a & b).sum() / u) if u else 0.0


def surface_rho(mine: np.ndarray, theirs: np.ndarray, valid: np.ndarray) -> dict:
    """Rank correlation of two emission surfaces, plus set-agreement statistics.

    ``IR-57-RHO-01`` -- the dot-union Spearman is *not* a usable duplicate test on
    sparse binary rasters, and this function no longer treats it as one.

    On the union of two dot supports both arrays are 0/1 indicators of near-
    disjoint sets, so their rank correlation is the phi coefficient of two
    negatively associated indicators: a pixel that is *my* dot is unlikely to be
    *theirs*, which drives rho toward -1.  Measured over the registry itself,
    ``gate_ortho_w0.25-40k`` and ``h19-4-multiline-corroborated`` -- different
    lanes, live scores 0.2376 and 0.1894, Jaccard 0.022 -- give rho = -0.9408.
    Taking ``abs()`` of that flags every sparse raster in the registry as a
    duplicate of every other one.

    Duplication therefore has to be read off *positive* agreement and off set
    overlap.  Reported here:

    * ``spearman_full_footprint`` -- the operative rank statistic.  Measured over
      the registry it is **+1.0 for an exact copy** and 0.0003-0.0109 for all 15
      distinct rasters, so the protocol's 0.90 threshold separates cleanly.
    * ``jaccard_dot_sets`` -- |A n B| / |A u B|.  Near 1 for a re-export.
    * ``spearman_on_dot_union`` -- signed, and **never thresholded**.  Reported so
      the degeneracy is visible: it sits near -1 for every pair of distinct sparse
      rasters and is NaN whenever one support contains the other.
    """
    m = np.asarray(mine, np.float32)[valid]
    t = np.asarray(theirs, np.float32)[valid]
    mb, tb = m > 0, t > 0
    union = mb | tb
    out = {}
    if union.sum() > 10 and mb[union].any() and tb[union].any() \
            and not (mb[union].all() or tb[union].all()):
        with np.errstate(invalid="ignore"):
            out["spearman_on_dot_union"] = float(spearmanr(m[union], t[union]).statistic)
    else:
        # one support contains the other: the statistic is undefined, not 1.0
        out["spearman_on_dot_union"] = float("nan")
    out["n_dot_union"] = int(union.sum())
    out["jaccard_dot_sets"] = _jaccard(mb, tb)
    out["spearman_full_footprint"] = float(spearmanr(m, t).statistic)
    return out


def compare_to_registry(mine_path: Path, registry_index: Path,
                        footprint: np.ndarray) -> dict:
    mine = rasterio.open(mine_path).read(1)
    idx = json.loads(Path(registry_index).read_text())
    rows = []
    worst_rho = -2.0
    worst_overlap = 0.0
    worst_jaccard = 0.0
    worst_rho_name = worst_overlap_name = worst_jaccard_name = ""
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
            # the protocol's rank test: POSITIVE agreement over the footprint
            "duplicate_by_rho": bool(rho["spearman_full_footprint"] > RHO_LIMIT),
            "duplicate_by_jaccard": bool(rho["jaccard_dot_sets"] > JACCARD_LIMIT),
            "duplicate_by_overlap": bool(ov > OVERLAP_LIMIT),
        })
        r_u = rho["spearman_full_footprint"]
        if r_u > worst_rho:
            worst_rho = r_u; worst_rho_name = rec["submission"]
        if rho["jaccard_dot_sets"] > worst_jaccard:
            worst_jaccard = rho["jaccard_dot_sets"]; worst_jaccard_name = rec["submission"]
        if ov > worst_overlap:
            worst_overlap = ov; worst_overlap_name = rec["submission"]
    unique = not any(r.get("duplicate_by_rho") or r.get("duplicate_by_overlap")
                     or r.get("duplicate_by_jaccard")
                     for r in rows if "error" not in r)
    return {
        "my_file": str(mine_path),
        "my_dots": int((mine > 0).sum()),
        "rho_limit": RHO_LIMIT, "overlap_limit": OVERLAP_LIMIT,
        "worst_spearman_full_footprint": worst_rho, "worst_rho_submission": worst_rho_name,
        "jaccard_limit": JACCARD_LIMIT,
        "worst_jaccard_dot_sets": worst_jaccard, "worst_jaccard_submission": worst_jaccard_name,
        "worst_dot_overlap": worst_overlap, "worst_overlap_submission": worst_overlap_name,
        "unique": bool(unique),
        "rows": rows,
    }
