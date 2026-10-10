"""Literal parallel-run gates, fail closed on incomplete registries.

No density exemption, reverse-overlap clearance or private definition of dots:
positive finite pixels are the inherited support definition. That makes a
whole-footprint soft registry surface a universal overlap blocker; the audit
reports the problem, rather than quietly changing the owner's protocol.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.stats import rankdata, spearmanr
from .metric import RADIUS_PX

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
# Retained solely as a descriptive benchmark for old evidence; Jaccard is not
# part of the user's literal duplicate/drift gate.
JACCARD_LIMIT = 0.50
ROOT = Path(__file__).resolve().parents[2]


def _dots(a):
    a = np.asarray(a)
    return np.isfinite(a) & (a > 0)


def _near(support, radius_px=RADIUS_PX):
    r = int(np.ceil(radius_px))
    yy, xx = np.mgrid[-r:r+1, -r:r+1]
    return binary_dilation(support, structure=yy*yy+xx*xx <= radius_px*radius_px)


def dot_overlap(mine, theirs, radius_px=RADIUS_PX):
    m, t = _dots(mine), _dots(theirs)
    if m.shape != t.shape:
        raise ValueError('overlap grid shape mismatch')
    if not m.any() or not t.any():
        return 0.0
    return float(_near(t, radius_px)[m].mean())


def _jaccard(a, b):
    u = int((a | b).sum())
    return float((a & b).sum() / u) if u else 0.0


def surface_rho(mine, theirs, valid):
    m = np.asarray(mine, np.float32)[valid]
    t = np.asarray(theirs, np.float32)[valid]
    mb, tb = _dots(m), _dots(t)
    union = mb | tb
    rho_union = float('nan')
    if union.sum() > 10 and mb[union].any() and tb[union].any() and not (mb[union].all() or tb[union].all()):
        rho_union = float(spearmanr(m[union], t[union]).statistic)
    rho = float(spearmanr(m, t).statistic) if np.ptp(m) and np.ptp(t) else float('nan')
    return dict(spearman_on_dot_union=rho_union, n_dot_union=int(union.sum()),
                jaccard_dot_sets=_jaccard(mb,tb), spearman_full_footprint=rho)


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for c in iter(lambda: stream.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def _registry_rows(index_path, shape):
    """Load inventory rows, verify pinned bytes and note transform alignment."""
    if isinstance(index_path, (dict, list)):
        index = index_path
    else:
        index = json.loads(Path(index_path).read_text())
    records = index.get("rasters", []) if isinstance(index, dict) else index
    if not isinstance(records, list):
        raise ValueError("registry index must contain a raster list")
    from .grid import CRS_EPSG, TRANSFORM
    expected_transform = tuple(float(x) for x in tuple(TRANSFORM)[:6])
    rows = []
    for record in records:
        path = Path(record.get("cache_file") or record.get("file") or "")
        if not path.is_absolute():
            path = ROOT / path
        sources = record.get("sources") or [record.get("submission", str(path))]
        base = {"submission": sources[0], "sources": sources,
                "repo": record.get("repo_first") or record.get("repo"),
                "sha256": record.get("sha256"), "file": str(path)}
        if not path.is_file():
            rows.append({**base, "error": "missing registry raster"})
            continue
        try:
            actual_sha = _sha(path)
            if base["sha256"] and actual_sha != base["sha256"]:
                raise ValueError("registry SHA256 pin mismatch")
            with rasterio.open(path) as ds:
                if ds.count != 1 or ds.shape != shape:
                    raise ValueError(f"unaligned shape/bands: {ds.shape} / {ds.count}")
                if ds.crs is None or ds.crs.to_epsg() != 32611:
                    raise ValueError(f"unaligned CRS: {ds.crs}")
                got_transform = tuple(float(x) for x in tuple(ds.transform)[:6])
            rows.append({**base, "path": path, "sha256": actual_sha,
                         "source_transform": list(got_transform),
                         "needs_reproject": got_transform != expected_transform})
        except Exception as exc:
            rows.append({**base, "error": f"{type(exc).__name__}: {str(exc)[:160]}"})
    return index, rows


def _read_registry_on_candidate_grid(path, shape):
    """Nearest-neighbour align a prior whose affine transform is offset."""
    from rasterio.warp import Resampling, reproject
    from .grid import CRS_EPSG, TRANSFORM
    with rasterio.open(path) as ds:
        source = ds.read(1)
        aligned = (ds.shape == shape and ds.crs is not None
                   and ds.crs.to_epsg() == 32611
                   and tuple(float(x) for x in tuple(ds.transform)[:6])
                   == tuple(float(x) for x in tuple(TRANSFORM)[:6]))
        if aligned:
            return source
        dest = np.zeros(shape, dtype=source.dtype)
        reproject(source=source, destination=dest,
                  src_transform=ds.transform, src_crs=ds.crs,
                  dst_transform=TRANSFORM, dst_crs=CRS_EPSG,
                  src_nodata=ds.nodata, dst_nodata=0,
                  resampling=Resampling.nearest)
        return dest


def _registry_coverage_errors(index, rows):
    """A clearance needs an explicit complete, reachable, count-matched index."""
    errors = []
    if not isinstance(index, dict):
        return ["registry index lacks a full-inventory completeness certificate"]
    if index.get("complete_accessible_scan") is not True:
        errors.append("registry index lacks a true complete_accessible_scan attestation")
    expected = index.get("n_unique_grid_rasters")
    if expected is None:
        errors.append("registry index lacks n_unique_grid_rasters")
    elif int(expected) != len(rows):
        errors.append(f"index count mismatch: metadata={expected}, records={len(rows)}")
    if not rows:
        errors.append("registry index contains no raster records")
    unreachable = index.get("repos_unreachable_or_missing") or []
    if unreachable:
        errors.append(f"unreachable/missing repositories: {len(unreachable)}")
    if index.get("errors"):
        errors.append(f"registry index reports errors: {len(index['errors'])}")
    skipped = index.get("skipped") or {}
    if isinstance(skipped, dict):
        omitted = int(skipped.get("too_large_or_missing", 0)) + int(skipped.get("over_lazy_ceiling", 0))
        if omitted:
            errors.append(f"large/missing/over-ceiling raster skips: {omitted}")
    return errors


def _spearman_ranked(candidate_rank_centered, candidate_ss, values):
    """Tie-aware Spearman correlation using a precomputed candidate rank."""
    v = np.asarray(values, np.float64)
    if v.size == 0 or float(v.min()) == float(v.max()) or candidate_ss <= 0:
        return None
    if np.logical_or(v == v.min(), v == v.max()).all():
        y = (v == v.max()).astype(np.float64)
        p = float(y.mean())
        if p <= 0.0 or p >= 1.0:
            return None
        cov = float(np.mean(candidate_rank_centered * (y - p)))
        return float(cov / np.sqrt((candidate_ss / v.size) * p * (1.0 - p)))
    r = rankdata(v, method="average").astype(np.float64)
    r -= r.mean()
    ss = float(np.dot(r, r))
    return float(np.dot(candidate_rank_centered, r) / np.sqrt(candidate_ss * ss)) if ss > 0 else None


def compare_surface_to_registry(surface, registry_index, footprint, *, stop_on_first=True):
    """Pre-placement surface rho gate; no dot-support or reverse-overlap proxy."""
    c = np.asarray(surface, np.float32)
    fp = np.asarray(footprint, bool)
    if c.ndim != 2 or c.shape != fp.shape or not fp.any():
        raise ValueError("surface and non-empty footprint must be aligned 2D arrays")
    vals = c[fp].astype(np.float64)
    if not np.isfinite(vals).all() or (vals < 0).any() or (vals > 1).any():
        raise ValueError("surface must be finite and in [0,1] across the footprint")
    ranks = rankdata(vals, method="average").astype(np.float64)
    ranks -= ranks.mean()
    rank_ss = float(np.dot(ranks, ranks))
    if rank_ss <= 0:
        raise ValueError("constant surface has no rank-uniqueness evidence")
    index, rows = _registry_rows(registry_index, c.shape)
    audited = []
    worst = -2.0
    worst_row = None
    firing = None
    for row in rows:
        if "error" in row:
            audited.append({k: v for k, v in row.items() if k != "path"})
            continue
        entry = {k: v for k, v in row.items() if k != "path"}
        try:
            prior = _read_registry_on_candidate_grid(row["path"], c.shape)
            prior_vals = np.where(np.isfinite(prior[fp]), prior[fp], 0.0).astype(np.float64)
            rho = _spearman_ranked(ranks, rank_ss, prior_vals)
            flagged = rho is not None and rho > RHO_LIMIT
            entry.update(spearman_full_footprint=rho, duplicate_by_rho=bool(flagged))
            audited.append(entry)
            if rho is not None and rho > worst:
                worst, worst_row = rho, entry
            if flagged:
                firing = entry
                if stop_on_first:
                    break
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
            audited.append(entry)
    errors = [r for r in audited if "error" in r]
    coverage_errors = _registry_coverage_errors(index, rows)
    complete = len(audited) == len(rows) and not errors and not coverage_errors
    flagged = [r for r in audited if r.get("duplicate_by_rho")]
    return {
        "phase": "pre-placement surface",
        "rho_limit": RHO_LIMIT,
        "n_registry_indexed": len(rows),
        "n_registry_checked": sum("error" not in r for r in audited),
        "n_reprojected_priors": sum(bool(r.get("needs_reproject")) for r in audited),
        "registry_complete": complete,
        "short_circuited_on_failure": bool(firing and stop_on_first),
        "max_spearman_full_footprint": None if worst_row is None else {
            "value": float(worst), "raster": worst_row.get("submission"),
            "repo": worst_row.get("repo")},
        "n_rho_firings": len(flagged),
        "first_rho_firing": firing,
        "errors": errors,
        "coverage_errors": coverage_errors,
        "rows": audited,
        "unique_by_protocol": bool(complete and not firing),
        "verdict": ("PASS" if complete and not firing else
                    "FAIL — surface rho > 0.90" if firing else
                    "HOLD — registry scan incomplete"),
    }


def compare_dots_to_registry(surface, dots, registry_index, footprint, *, stop_on_first=True):
    """Final-dot gate: surface rank correlation OR forward-only 3 px overlap."""
    c = np.asarray(surface, np.float32)
    d = np.asarray(dots, bool)
    fp = np.asarray(footprint, bool)
    if c.ndim != 2 or c.shape != fp.shape or d.shape != fp.shape:
        raise ValueError("surface, dots and footprint must be aligned 2D arrays")
    if not np.isfinite(c[fp]).all() or (c[fp] < 0).any() or (c[fp] > 1).any():
        raise ValueError("surface must be finite and in [0,1] across the footprint")
    if d[~fp].any():
        raise ValueError("candidate dots must be zero outside the footprint")
    mine = d & fp
    n_dots = int(mine.sum())
    if not n_dots:
        raise ValueError("final dot map is empty")
    dot_rank = rankdata(mine[fp].astype(np.float64), method="average")
    dot_rank -= dot_rank.mean()
    dot_ss = float(np.dot(dot_rank, dot_rank))
    index, rows = _registry_rows(registry_index, c.shape)
    audited = []
    worst_rho = -2.0
    worst_rho_row = None
    worst_overlap = -1.0
    worst_overlap_row = None
    firing = None
    for row in rows:
        if "error" in row:
            audited.append({k: v for k, v in row.items() if k != "path"})
            continue
        entry = {k: v for k, v in row.items() if k != "path"}
        try:
            prior = _read_registry_on_candidate_grid(row["path"], c.shape)
            prior_fp = np.where(np.isfinite(prior[fp]), prior[fp], 0.0).astype(np.float64)
            rho = _spearman_ranked(dot_rank, dot_ss, prior_fp)
            support = np.isfinite(prior) & (prior > 0.0) & fp
            overlap = float((distance_transform_edt(~support)[mine] <= RADIUS_PX).mean()) if support.any() else 0.0
            rho_flag = rho is not None and rho > RHO_LIMIT
            overlap_flag = overlap > OVERLAP_LIMIT
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
            entry["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
            audited.append(entry)
    errors = [r for r in audited if "error" in r]
    coverage_errors = _registry_coverage_errors(index, rows)
    complete = len(audited) == len(rows) and not errors and not coverage_errors
    flagged = [r for r in audited if r.get("duplicate_by_rho") or r.get("duplicate_by_overlap")]
    return {
        "phase": "final dots",
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
        "n_rho_firings": sum(bool(r.get("duplicate_by_rho")) for r in flagged),
        "n_overlap_firings": sum(bool(r.get("duplicate_by_overlap")) for r in flagged),
        "first_firing": firing,
        "errors": errors,
        "coverage_errors": coverage_errors,
        "rows": audited,
        "unique_by_protocol": bool(complete and not firing),
        "verdict": ("PASS" if complete and not firing else
                    "FAIL — literal rank/forward-overlap gate" if firing else
                    "HOLD — registry scan incomplete"),
    }


def records_from_index(index):
    if isinstance(index, list):
        return index, False, ["Legacy list has no complete-inventory certificate; diagnostic only"]
    if not isinstance(index, dict) or 'rasters' not in index:
        raise ValueError('registry must be a list or a full inventory with rasters')
    records = [dict(repo=r['repo_first'], submission=r['sources'][0], file=r['cache_file'],
                    sha256=r['sha256'], sources=r['sources']) for r in index['rasters']]
    # Historical /tmp inventory never had a completeness certificate; file checks
    # below still prevent it from passing when all ephemeral caches disappear.
    complete = index.get('complete_accessible_scan', False)
    return records, bool(complete), index.get('errors', [])


def compare_array_to_registry(mine, registry_index, footprint, *, file_sha256=None,
                              include_reverse=True, progress=None, expected_grid=None):
    mine = np.asarray(mine, np.float32)
    fp = np.asarray(footprint, bool)
    if mine.ndim != 2 or mine.shape != fp.shape or not fp.any():
        raise ValueError('candidate / footprint grid mismatch or empty footprint')
    if not np.isfinite(mine).all() or (mine < 0).any() or (mine > 1).any():
        raise ValueError('candidate must already be finite in [0,1]')
    if (mine[~fp] > 0).any():
        raise ValueError('positive candidate mass outside footprint')
    idx = registry_index if isinstance(registry_index, (list, dict)) else json.loads(Path(registry_index).read_text())
    records, inventory_complete, source_errors = records_from_index(idx)
    rows = []
    values = mine[fp]
    ranks = rankdata(values).astype(np.float64)
    ranks -= ranks.mean()
    norm = float(np.linalg.norm(ranks))
    my_support = _dots(mine) & fp
    my_dot_count = int(my_support.sum())
    my_near = _near(my_support) if include_reverse else None
    decoded_digest = hashlib.sha256(np.ascontiguousarray(mine).tobytes()).hexdigest()
    for i, rec in enumerate(records):
        p = Path(rec['file'])
        if not p.is_absolute():
            p = ROOT / p
        base = dict(repo=rec.get('repo'), submission=rec.get('submission',p.name), file=str(p))
        try:
            if not p.exists():
                raise FileNotFoundError('missing registry file; cannot certify uniqueness')
            digest = _sha(p)
            if rec.get('sha256') and digest != rec['sha256']:
                raise ValueError('registry SHA256 pin mismatch')
            with rasterio.open(p) as src:
                if src.count != 1 or src.shape != mine.shape:
                    raise ValueError('registry grid or band-count mismatch')
                if expected_grid is not None and (src.shape, src.crs, src.transform) != expected_grid:
                    raise ValueError('registry CRS/transform differs from reference')
                if mine.shape == (3730,3292):
                    from .grid import TRANSFORM
                    if src.crs is None or src.crs.to_epsg()!=32611 or src.transform != TRANSFORM:
                        raise ValueError('registry CRS/transform mismatch')
                theirs = src.read(1).astype(np.float32)
            theirs = np.where(np.isfinite(theirs), theirs, 0.0)
            # Outside-footprint values are ignored for support and pixel identity.
            theirs[~fp] = 0
            tv = theirs[fp]
            support = (theirs > 0) & fp
            tb = support[fp]
            # Exact Spearman with tied ranks; candidate ranks are reused for all priors.
            if norm == 0 or np.ptp(tv) == 0:
                rho = None
            elif np.all((tv == 0) | (tv == 1)):
                nt = int(tb.sum()); n = len(tv)
                rho = float(ranks[tb].sum() / (norm * np.sqrt(nt*(n-nt)/n)))
            else:
                tr = rankdata(tv).astype(np.float64)
                tr -= tr.mean()
                rho = float(np.dot(ranks,tr)/(norm*np.linalg.norm(tr)))
            ov = float(_near(support)[my_support].mean()) if my_dot_count else 0.0
            reverse = float(my_near[support].mean()) if include_reverse and support.any() else 0.0
            jac = _jaccard(my_support, support)
            their_decoded = hashlib.sha256(np.ascontiguousarray(theirs).tobytes()).hexdigest()
            row = {**base, 'sha256':digest, 'decoded_sha256':their_decoded,
                'their_dots':int(support.sum()), 'my_dots_within_3px_of_theirs':ov,
                'their_dots_within_3px_of_mine':reverse, 'spearman_full_footprint':rho,
                'jaccard_dot_sets':jac,
                'identical_bytes':bool(file_sha256 and digest==file_sha256),
                'identical_decoded_predictions':bool(their_decoded==decoded_digest),
                'duplicate_by_rho':bool(rho is not None and rho > RHO_LIMIT),
                'duplicate_by_overlap':bool(ov > OVERLAP_LIMIT),
                'jaccard_over_diagnostic_reference':bool(jac > JACCARD_LIMIT)}
            rows.append(row)
        except (OSError, ValueError, rasterio.errors.RasterioError) as e:
            rows.append({**base, 'error':str(e)})
        if progress:
            progress(i+1,len(records),rows[-1])
    checked = [r for r in rows if 'error' not in r]
    errors = [r for r in rows if 'error' in r]
    # The protocol gate is exactly Spearman > 0.90 OR candidate-forward 3 px
    # overlap > 0.70. Jaccard and byte/pixel identity remain diagnostics only.
    flags = [r for r in checked if r['duplicate_by_rho'] or r['duplicate_by_overlap']]
    complete = inventory_complete and bool(records) and not errors and not source_errors
    rank_rows = [r for r in checked if r['spearman_full_footprint'] is not None]
    worst_rho = max(rank_rows, key=lambda r:r['spearman_full_footprint'], default=None)
    worst_ov = max(checked,key=lambda r:r['my_dots_within_3px_of_theirs'],default=None)
    worst_jac = max(checked,key=lambda r:r['jaccard_dot_sets'],default=None)
    unique = complete and my_dot_count > 0 and norm > 0 and not flags
    return dict(evidence_class='REGISTRY-MEASUREMENT', my_dots=my_dot_count,
        candidate_decoded_sha256=decoded_digest, candidate_file_sha256=file_sha256,
        rho_limit=RHO_LIMIT, overlap_limit=OVERLAP_LIMIT,
        jaccard_diagnostic_reference=JACCARD_LIMIT,
        protocol='duplicate iff Spearman > 0.90 OR candidate-forward 3 px overlap > 0.70; no reverse-overlap exemption',
        registry_rasters_expected=len(records), registry_rasters_checked=len(checked),
        complete_accessible_scan=complete, missing_or_invalid=len(errors), source_errors=source_errors,
        worst_spearman_full_footprint=worst_rho['spearman_full_footprint'] if worst_rho else None,
        worst_rho_submission=worst_rho['submission'] if worst_rho else None,
        worst_dot_overlap=worst_ov['my_dots_within_3px_of_theirs'] if worst_ov else None,
        worst_overlap_submission=worst_ov['submission'] if worst_ov else None,
        worst_jaccard_dot_sets=worst_jac['jaccard_dot_sets'] if worst_jac else None,
        worst_jaccard_submission=worst_jac['submission'] if worst_jac else None,
        byte_unique_among_checked=bool(checked) and not any(r['identical_bytes'] for r in checked),
        pixel_unique_among_checked=bool(checked) and not any(r['identical_decoded_predictions'] for r in checked),
        duplicate_count=len(flags), unique=bool(unique), rows=rows,
        verdict='promote-to-selector-only' if unique else 'negative',
        stop_required=bool(flags or not complete or not my_dot_count or norm == 0),
        candidate_rank_variation=norm > 0,
        scope='All hash-verified accessible inventory entries; not inaccessible/private/unlinked files. Reverse overlap is diagnostic only.')


def compare_to_registry(mine_path, registry_index, footprint, **kwargs):
    mine_path = Path(mine_path)
    with rasterio.open(mine_path) as src:
        if src.count != 1:
            raise ValueError('candidate must be single band')
        mine = src.read(1)
    return dict(my_file=str(mine_path), **compare_array_to_registry(mine, registry_index, footprint,
                file_sha256=_sha(mine_path), **kwargs))


def saturation_certificate(registry_path, footprint, catalogue=None):
    """A witness that proves every nonempty allowed dot set fails the overlap gate."""
    fp = np.asarray(footprint,bool)
    allowed = fp if catalogue is None else fp & ~np.asarray(catalogue,bool)
    if not allowed.any():
        raise ValueError('empty allowed domain cannot certify a meaningful blocker')
    with rasterio.open(registry_path) as src:
        a = src.read(1)
        if a.shape != fp.shape or src.count != 1:
            raise ValueError('witness grid mismatch')
    positive = _dots(a) & fp
    covered = _near(positive)
    uncovered = int((allowed & ~covered).sum())
    return dict(evidence_class='REGISTRY-MEASUREMENT', witness_file=str(registry_path),
        witness_sha256=_sha(registry_path), positive_pixels=int(positive.sum()),
        allowed_pixels=int(allowed.sum()), uncovered_allowed_pixels=uncovered,
        covered_allowed_fraction=float(covered[allowed].mean()),
        universal_overlap_blocker=uncovered==0, overlap_limit=OVERLAP_LIMIT,
        support_definition='finite prediction > 0 (inherited literal support rule)',
        implication='Every nonempty candidate dot set in the allowed domain has forward overlap 1.0 with this prior; therefore it cannot pass the 0.70 gate.' if uncovered==0 else 'No universal blockage established.')
