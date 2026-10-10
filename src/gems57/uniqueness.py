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


def _registry_rows(index_path: Path, shape: tuple[int, int]):
    """Load index metadata and return verified, aligned raster handles as paths.

    Missing or unaligned inventory entries remain errors and make any clearance
    fail closed; they are never silently dropped from the denominator.
    """
    index = json.loads(Path(index_path).read_text())
    records = index.get("rasters", []) if isinstance(index, dict) else index
    rows = []
    from .grid import CRS_EPSG, TRANSFORM
    expected_transform = tuple(float(x) for x in tuple(TRANSFORM)[:6])
    for record in records:
        path = Path(record.get("cache_file") or record.get("file") or "")
        sources = record.get("sources") or [record.get("submission", str(path))]
        base = {"submission": sources[0], "sources": sources,
                "repo": record.get("repo_first") or record.get("repo"),
                "sha256": record.get("sha256"), "file": str(path)}
        if not path.is_file():
            rows.append({**base, "error": "missing registry raster"})
            continue
        try:
            with rasterio.open(path) as ds:
                if ds.count != 1 or ds.shape != shape:
                    raise ValueError(f"unaligned shape/bands: {ds.shape} / {ds.count}")
                if str(ds.crs) != CRS_EPSG:
                    raise ValueError(f"unaligned CRS: {ds.crs}")
                got_transform = tuple(float(x) for x in tuple(ds.transform)[:6])
        except Exception as exc:
            rows.append({**base, "error": f"{type(exc).__name__}: {str(exc)[:160]}"})
            continue
        rows.append({**base, "path": path, "source_transform": list(got_transform),
                     "needs_reproject": got_transform != expected_transform})
    return index, rows


def _read_registry_on_candidate_grid(path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Read one prior and nearest-neighbour reproject transform offsets onto the pinned grid."""
    from rasterio.warp import Resampling, reproject
    from .grid import CRS_EPSG, TRANSFORM
    with rasterio.open(path) as ds:
        source = ds.read(1)
        same_grid = (ds.shape == shape and str(ds.crs) == CRS_EPSG
                     and tuple(float(x) for x in tuple(ds.transform)[:6])
                     == tuple(float(x) for x in tuple(TRANSFORM)[:6]))
        if same_grid:
            return source
        dest = np.zeros(shape, dtype=source.dtype)
        reproject(source=source, destination=dest,
                  src_transform=ds.transform, src_crs=ds.crs,
                  dst_transform=TRANSFORM, dst_crs=CRS_EPSG,
                  src_nodata=ds.nodata, dst_nodata=0,
                  resampling=Resampling.nearest)
        return dest


def _registry_coverage_errors(index: dict, rows: list[dict]) -> list[str]:
    errors = []
    if not isinstance(index, dict):
        return ["registry index is not an object with coverage metadata"]
    expected = index.get("n_unique_grid_rasters")
    if expected is not None and int(expected) != len(rows):
        errors.append(f"index count mismatch: metadata={expected}, records={len(rows)}")
    unreachable = index.get("repos_unreachable_or_missing") or []
    if unreachable:
        errors.append(f"unreachable/missing repositories: {len(unreachable)}")
    skipped = index.get("skipped") or {}
    omitted = int(skipped.get("too_large_or_missing", 0)) + int(skipped.get("over_lazy_ceiling", 0))
    if omitted > 0:
        errors.append(f"large/missing/over-ceiling raster skips: {omitted}")
    return errors


def _spearman_ranked(candidate_rank_centered: np.ndarray, candidate_ss: float,
                     values: np.ndarray) -> float | None:
    """Tie-aware Spearman correlation using a precomputed candidate rank."""
    v = np.asarray(values, np.float64)
    lo, hi = float(v.min()), float(v.max())
    if lo == hi or candidate_ss <= 0:
        return None
    # Most registry emissions are binary. Point-biserial correlation on the
    # candidate ranks is exactly Spearman when the other side has two values.
    two_values = bool(np.logical_or(v == lo, v == hi).all())
    if two_values:
        y = (v == hi).astype(np.float64)
        p = float(y.mean())
        if p <= 0.0 or p >= 1.0:
            return None
        cov = float(np.mean(candidate_rank_centered * (y - p)))
        return float(cov / np.sqrt((candidate_ss / v.size) * p * (1.0 - p)))
    from scipy.stats import rankdata
    r = rankdata(v, method="average")
    r -= r.mean()
    ss = float(np.dot(r, r))
    if ss <= 0.0:
        return None
    return float(np.dot(candidate_rank_centered, r) / np.sqrt(candidate_ss * ss))


def compare_surface_to_registry(surface: np.ndarray, registry_index: Path,
                                footprint: np.ndarray, *,
                                stop_on_first: bool = True) -> dict:
    """Pre-allocation surface Spearman check against every indexed raster.

    A missing/unreadable/unaligned registry file prevents clearance. The scan
    short-circuits only after a literal rho > 0.90 failure when requested.
    """
    from scipy.stats import rankdata
    c = np.asarray(surface, np.float32)
    fp = np.asarray(footprint, bool)
    if c.ndim != 2 or c.shape != fp.shape or not fp.any():
        raise ValueError("surface and non-empty footprint must be aligned 2D arrays")
    vals = c[fp].astype(np.float64)
    if not np.isfinite(vals).all() or (vals < 0).any() or (vals > 1).any():
        raise ValueError("surface must be finite and in [0,1] across the footprint")
    rank = rankdata(vals, method="average")
    rank -= rank.mean()
    ss = float(np.dot(rank, rank))
    if ss <= 0:
        raise ValueError("constant surface has no rank-uniqueness evidence")
    index, rows = _registry_rows(Path(registry_index), c.shape)
    audited = []
    worst_rho, worst_row = -2.0, None
    firing = None
    for row in rows:
        if "error" in row:
            audited.append({k: v for k, v in row.items() if k != "path"})
            continue
        try:
            prior = _read_registry_on_candidate_grid(row["path"], c.shape)
            prior_vals = np.where(np.isfinite(prior[fp]), prior[fp], 0.0).astype(np.float64)
            rho = _spearman_ranked(rank, ss, prior_vals)
            flagged = rho is not None and rho > RHO_LIMIT
            entry = {k: v for k, v in row.items() if k != "path"}
            entry.update(spearman_full_footprint=rho,
                         duplicate_by_rho=bool(flagged))
            audited.append(entry)
            if rho is not None and rho > worst_rho:
                worst_rho, worst_row = rho, entry
            if flagged:
                firing = entry
                if stop_on_first:
                    break
        except Exception as exc:
            entry = {k: v for k, v in row.items() if k != "path"}
            entry["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
            audited.append(entry)
    errors = [r for r in audited if "error" in r]
    coverage_errors = _registry_coverage_errors(index, rows)
    complete = len(audited) == len(rows) and not errors and not coverage_errors
    flagged_rows = [r for r in audited if r.get("duplicate_by_rho")]
    return {
        "phase": "pre-placement surface",
        "registry_scope": "all unique single-band rasters in the supplied full archive index; transform offsets are nearest-neighbour reprojected to the pinned grid; not proof that every file is an organizer submission",
        "rho_limit": RHO_LIMIT,
        "n_registry_indexed": len(rows),
        "n_registry_checked": sum("error" not in r for r in audited),
        "n_reprojected_priors": sum(bool(r.get("needs_reproject")) for r in audited),
        "registry_complete": complete,
        "short_circuited_on_failure": bool(firing and stop_on_first),
        "max_spearman_full_footprint": None if worst_row is None else {
            "value": float(worst_rho), "raster": worst_row.get("submission"),
            "repo": worst_row.get("repo")},
        "n_rho_firings": len(flagged_rows),
        "first_rho_firing": firing,
        "errors": errors,
        "coverage_errors": coverage_errors,
        "rows": audited,
        "unique_by_protocol": bool(complete and not firing),
        "verdict": ("PASS" if complete and not firing else
                    "FAIL — surface rho > 0.90" if firing else
                    "HOLD — registry scan incomplete"),
        "registry_index_metadata": ({k: index.get(k) for k in
                                     ("owner", "n_unique_grid_rasters", "repos_scanned",
                                      "repos_unreachable_or_missing", "skipped")}
                                     if isinstance(index, dict) else {}),
    }


def compare_dots_to_registry(surface: np.ndarray, dots: np.ndarray,
                             registry_index: Path, footprint: np.ndarray, *,
                             stop_on_first: bool = True) -> dict:
    """Post-allocation Spearman and literal one-way 3-px dot-overlap gates."""
    from scipy.stats import rankdata
    c = np.asarray(surface, np.float32)
    d = np.asarray(dots, bool)
    fp = np.asarray(footprint, bool)
    if c.ndim != 2 or c.shape != fp.shape or d.shape != fp.shape:
        raise ValueError("surface, dots and footprint must be aligned 2D arrays")
    if not np.isfinite(c[fp]).all() or (c[fp] < 0).any() or (c[fp] > 1).any():
        raise ValueError("surface must be finite and in [0,1] across the footprint")
    mine = d & fp
    n_dots = int(mine.sum())
    if not n_dots:
        raise ValueError("final dot map is empty")
    dot_vals = mine[fp].astype(np.float64)
    dot_rank = rankdata(dot_vals, method="average")
    dot_rank -= dot_rank.mean()
    dot_ss = float(np.dot(dot_rank, dot_rank))
    index, rows = _registry_rows(Path(registry_index), c.shape)
    audited = []
    worst_rho, worst_rho_row = -2.0, None
    worst_overlap, worst_overlap_row = -1.0, None
    firing = None
    for row in rows:
        if "error" in row:
            audited.append({k: v for k, v in row.items() if k != "path"})
            continue
        try:
            prior = _read_registry_on_candidate_grid(row["path"], c.shape)
            prior_fp = np.where(np.isfinite(prior[fp]), prior[fp], 0.0).astype(np.float64)
            rho = _spearman_ranked(dot_rank, dot_ss, prior_fp)
            support = np.isfinite(prior) & (prior > 0.0) & fp
            if support.any():
                dist = distance_transform_edt(~support)
                overlap = float((dist[mine] <= RADIUS_PX).mean())
            else:
                overlap = 0.0
            rho_flag = rho is not None and rho > RHO_LIMIT
            overlap_flag = overlap > OVERLAP_LIMIT
            entry = {k: v for k, v in row.items() if k != "path"}
            entry.update(spearman_full_footprint=rho,
                         my_dots_within_3px_of_theirs=overlap,
                         their_positive_pixels=int(support.sum()),
                         duplicate_by_rho=bool(rho_flag),
                         duplicate_by_overlap=bool(overlap_flag))
            audited.append(entry)
            if rho is not None and rho > worst_rho:
                worst_rho, worst_rho_row = rho, entry
            if overlap > worst_overlap:
                worst_overlap, worst_overlap_row = overlap, entry
            if rho_flag or overlap_flag:
                firing = entry
                if stop_on_first:
                    break
        except Exception as exc:
            entry = {k: v for k, v in row.items() if k != "path"}
            entry["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
            audited.append(entry)
    errors = [r for r in audited if "error" in r]
    coverage_errors = _registry_coverage_errors(index, rows)
    complete = len(audited) == len(rows) and not errors and not coverage_errors
    flagged_rows = [r for r in audited if r.get("duplicate_by_rho") or r.get("duplicate_by_overlap")]
    return {
        "phase": "final dots",
        "registry_scope": "all unique grid-aligned rasters in the supplied full archive index; prior dots are literal positive pixels (>0), no reverse-overlap exemption",
        "rho_limit": RHO_LIMIT,
        "overlap_limit": OVERLAP_LIMIT,
        "overlap_radius_px": RADIUS_PX,
        "candidate_dots": n_dots,
        "n_registry_indexed": len(rows),
        "n_registry_checked": sum("error" not in r for r in audited),
        "n_reprojected_priors": sum(bool(r.get("needs_reproject")) for r in audited),
        "registry_complete": complete,
        "short_circuited_on_failure": bool(firing and stop_on_first),
        "max_spearman_full_footprint": None if worst_rho_row is None else {
            "value": float(worst_rho), "raster": worst_rho_row.get("submission"),
            "repo": worst_rho_row.get("repo")},
        "max_dot_overlap_fwd_3px": None if worst_overlap_row is None else {
            "value": float(worst_overlap), "raster": worst_overlap_row.get("submission"),
            "repo": worst_overlap_row.get("repo")},
        "n_rho_firings": sum(bool(r.get("duplicate_by_rho")) for r in flagged_rows),
        "n_overlap_firings": sum(bool(r.get("duplicate_by_overlap")) for r in flagged_rows),
        "first_firing": firing,
        "errors": errors,
        "coverage_errors": coverage_errors,
        "rows": audited,
        "unique_by_protocol": bool(complete and not firing),
        "verdict": ("PASS" if complete and not firing else
                    "FAIL — literal rank/forward-overlap gate" if firing else
                    "HOLD — registry scan incomplete"),
        "registry_index_metadata": ({k: index.get(k) for k in
                                     ("owner", "n_unique_grid_rasters", "repos_scanned",
                                      "repos_unreachable_or_missing", "skipped")}
                                     if isinstance(index, dict) else {}),
    }


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
        ov = dot_overlap(_dots(mine) & footprint, _dots(theirs) & footprint)
        rows.append({
            "repo": rec["repo"], "submission": rec["submission"],
            "owner_reported_score": rec.get("owner_reported_score"),
            "their_dots": int((theirs > 0).sum()),
            "my_dots_within_3px_of_theirs": ov,
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
    registry_complete = bool(rows) and not any("error" in r for r in rows)
    unique = bool(registry_complete and not any(
        r.get("duplicate_by_rho") or r.get("duplicate_by_overlap") for r in rows))
    return {
        "my_file": str(mine_path),
        "my_dots": int((mine > 0).sum()),
        "rho_limit": RHO_LIMIT, "overlap_limit": OVERLAP_LIMIT,
        "worst_spearman_full_footprint": worst_rho, "worst_rho_submission": worst_rho_name,
        "jaccard_limit": JACCARD_LIMIT,
        "worst_jaccard_dot_sets": worst_jaccard, "worst_jaccard_submission": worst_jaccard_name,
        "worst_dot_overlap": worst_overlap, "worst_overlap_submission": worst_overlap_name,
        "registry_complete": bool(registry_complete),
        "unique_by_protocol": bool(unique),
        "unique": bool(unique),
        "jaccard_is_informational_not_a_protocol_gate": True,
        "rows": rows,
    }
