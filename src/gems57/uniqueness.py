"""Uniqueness checks against every raster in the supplied local inventory.

Inventory scope must be disclosed; this cannot certify uniqueness against
private, unlinked, externally stored, or otherwise unavailable submissions.
Parallel-run protocol rule 1: stop if positive full-footprint rank correlation
with any supplied raster exceeds 0.90, or if more than 70% of candidate dots
fall within 3 px of one supplied raster's dots. Check the surface before
placement and the final dots after allocation.
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


def compare_surface_to_registry(candidate: np.ndarray, registry_index: Path,
                                 footprint: np.ndarray) -> dict:
    """Pre-placement rank check against every row in a pinned local registry.

    Any unreadable, missing, or misaligned prior makes the audit incomplete and
    therefore fails closed. This is intentionally separate from the final-dot
    proximity comparison below.
    """
    mine = np.asarray(candidate, dtype=np.float32)
    fp = np.asarray(footprint, dtype=bool)
    if (mine.ndim != 2 or mine.shape != fp.shape or not np.isfinite(mine).all()
            or (mine < 0).any() or (mine > 1).any() or not fp.any()):
        raise ValueError("candidate surface and footprint must be matching finite 2D [0,1] arrays")
    if np.ptp(mine[fp]) == 0:
        raise ValueError("constant candidate surface has no rank-uniqueness evidence")
    index_path = Path(registry_index).resolve()
    root = index_path.parent.parent if index_path.parent.name == "registry" else index_path.parent
    idx = json.loads(index_path.read_text())
    rows = []
    for rec in idx:
        path = Path(rec["file"])
        if not path.is_absolute():
            path = root / path
        try:
            with rasterio.open(path) as src:
                if src.count != 1 or src.shape != mine.shape:
                    raise ValueError(f"not aligned single-band raster ({src.count} bands, {src.shape})")
                theirs = src.read(1)
            theirs = np.where(np.isfinite(theirs), theirs, 0.0).astype(np.float32)
            rho = surface_rho(mine, theirs, fp)
            value = rho["spearman_full_footprint"]
            rows.append({"repo": rec.get("repo"), "submission": rec.get("submission"),
                         "path": str(path), **rho,
                         "duplicate_by_rho": bool(np.isfinite(value) and value > RHO_LIMIT),
                         "rho_defined": bool(np.isfinite(value))})
        except Exception as exc:
            rows.append({"repo": rec.get("repo"), "submission": rec.get("submission"),
                         "path": str(path), "error": f"{type(exc).__name__}: {str(exc)[:180]}"})
    complete = (bool(idx) and len(rows) == len(idx)
                and not any("error" in r or not r.get("rho_defined", False) for r in rows))
    duplicate = any(r.get("duplicate_by_rho", False) for r in rows)
    vals = [r["spearman_full_footprint"] for r in rows
            if np.isfinite(r.get("spearman_full_footprint", np.nan))]
    worst = max(vals) if vals else float("nan")
    worst_row = next((r for r in rows if r.get("spearman_full_footprint") == worst), {})
    return {"phase": "surface-before-placement", "registry_index": str(registry_index),
            "n_registry_rows": len(idx), "n_checked": sum("error" not in r for r in rows),
            "complete": complete, "rho_limit": RHO_LIMIT,
            "worst_spearman_full_footprint": float(worst),
            "worst_submission": worst_row.get("submission"),
            "duplicate": bool(duplicate), "unique_within_inventory": bool(complete and not duplicate),
            "scope": "only rows in the supplied local registry index; not a complete competition-wide inventory",
            "rows": rows}


def compare_to_registry(mine_path: Path | np.ndarray, registry_index: Path,
                        footprint: np.ndarray) -> dict:
    if isinstance(mine_path, (str, Path)):
        with rasterio.open(mine_path) as src:
            if src.count != 1:
                raise ValueError(f"candidate has {src.count} bands, expected one")
            mine = src.read(1)
        mine_label = str(mine_path)
    else:
        mine = np.asarray(mine_path, dtype=np.float32)
        mine_label = "in-memory candidate"
    fp = np.asarray(footprint, dtype=bool)
    if (mine.shape != fp.shape or not np.isfinite(mine).all()
            or (mine < 0).any() or (mine > 1).any() or not fp.any() or not (mine > 0).any()):
        raise ValueError("candidate must be nonempty finite [0,1] and match the footprint shape")
    index_path = Path(registry_index).resolve()
    root = index_path.parent.parent if index_path.parent.name == "registry" else index_path.parent
    idx = json.loads(index_path.read_text())
    rows = []
    worst_rho = -2.0
    worst_overlap = 0.0
    worst_jaccard = 0.0
    worst_rho_name = worst_overlap_name = worst_jaccard_name = ""
    for rec in idx:
        p = Path(rec["file"])
        if not p.is_absolute():
            p = root / p
        try:
            with rasterio.open(p) as src:
                if src.count != 1 or src.shape != mine.shape:
                    raise ValueError(f"not aligned single-band raster ({src.count} bands, {src.shape})")
                theirs = src.read(1)
        except Exception as exc:
            rows.append({**rec, "file": str(p),
                         "error": f"{type(exc).__name__}: {str(exc)[:180]}"})
            continue
        theirs = np.where(np.isfinite(theirs), theirs, 0.0)
        rho = surface_rho(mine, theirs, footprint)
        ov = dot_overlap(mine, theirs)
        ov_rev = dot_overlap(theirs, mine)
        rho_value = rho["spearman_full_footprint"]
        rows.append({
            "repo": rec["repo"], "submission": rec["submission"],
            "owner_reported_score": rec.get("owner_reported_score"),
            "their_dots": int((theirs > 0).sum()),
            "my_dots_within_3px_of_theirs": ov,
            "their_dots_within_3px_of_mine": ov_rev,
            **rho,
            "rho_defined": bool(np.isfinite(rho_value)),
            # the protocol's rank test: POSITIVE agreement over the footprint
            "duplicate_by_rho": bool(np.isfinite(rho_value) and rho_value > RHO_LIMIT),
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
    audit_complete = (bool(idx) and len(rows) == len(idx)
                      and not any("error" in r or not r.get("rho_defined", False)
                                  for r in rows))
    unique = audit_complete and not any(
        r.get("duplicate_by_rho") or r.get("duplicate_by_overlap")
        or r.get("duplicate_by_jaccard") for r in rows)
    return {
        "my_file": mine_label,
        "my_dots": int((mine > 0).sum()),
        "rho_limit": RHO_LIMIT, "overlap_limit": OVERLAP_LIMIT,
        "worst_spearman_full_footprint": worst_rho, "worst_rho_submission": worst_rho_name,
        "jaccard_limit": JACCARD_LIMIT,
        "worst_jaccard_dot_sets": worst_jaccard, "worst_jaccard_submission": worst_jaccard_name,
        "worst_dot_overlap": worst_overlap, "worst_overlap_submission": worst_overlap_name,
        "unique": bool(unique),
        "audit_complete": bool(audit_complete),
        "n_registry_rows": len(idx),
        "n_checked": sum("error" not in r for r in rows),
        "scope": "only rows in the supplied local registry index; not a complete competition-wide inventory",
        "rows": rows,
    }
