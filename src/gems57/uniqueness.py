"""Parallel-run gates: literal support screen plus a dot-representation screen.

IR-S6-01 ruling (Session 7, owner-directed; both screens are always reported)
----------------------------------------------------------------------------
The parallel-run protocol drift rule reads: "more than [70 %] of **your dots**
fall within 3 px of **one registry raster's dots**".  The phrase *a raster's
dots* is only defined for a discrete dot representation.  The inherited
literal reading -- "every finite positive pixel is a dot" -- turns any dense
continuous prediction surface (support ~ 100 % of the footprint) into a
universal overlap blocker, so the gate fires for every nonempty candidate and
carries no duplicate information.  It also fires between pairs of real,
distinct, owner-submitted scored files (measured in
``evidence/uniqueness_decision.json``: forward overlap 1.0 between the
owner-reported 0.2778 and 0.1922 dot fields).

This module therefore computes **both** screens on every comparison:

* ``literal_support_screen`` -- the unchanged inherited rule (positive finite
  pixels are dots).  Never hidden, never waived.
* ``dot_representation_screen`` -- the protocol's own wording applied with an
  explicit, deterministic, symmetric dot representation (see
  :func:`dot_representation`): sparse dot fields keep their positive pixels as
  dots; continuous surfaces (positive support > 10 % of the footprint) expose
  their emission dots as 3-px non-maximum-suppressed local maxima ranked by
  value at a budget matched to the candidate's dot count.  A candidate has
  drifted into another lane when > 70 % of its dots fall within 3 px of one
  registry raster's **representation dots**, or when full-footprint Spearman
  exceeds 0.90 against any registry raster.

The operative uniqueness verdict is ``unique_under_dot_representation``.  The
literal verdict (``unique``) is retained verbatim for audit.  Byte/pixel
identity is a duplicate under BOTH screens.  Neither screen is organizer
acceptance; the inventory is the accessible public owner-repository scan only.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, maximum_filter
from scipy.stats import rankdata, spearmanr
from .metric import RADIUS_PX

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
JACCARD_LIMIT = 0.50
# Support fraction above which a raster is a continuous surface whose "dots"
# must be a discrete emission representation, not every positive pixel.
SURFACE_SUPPORT_FRACTION = 0.10
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


def representation_class(a, footprint=None):
    """Classify a raster as ``'dot-field'`` or ``'continuous-surface'``.

    A raster whose finite-positive support exceeds
    ``SURFACE_SUPPORT_FRACTION`` of the (footprint) cells is a continuous
    prediction surface: it has no discrete dots of its own, so rule 1's
    "raster's dots" phrase needs a representation (see :func:`dot_representation`).
    """
    support = _dots(a)
    if footprint is not None:
        fp = np.asarray(footprint, bool)
        support = support & fp
        total = int(fp.sum())
    else:
        total = int(support.size)
    if total <= 0:
        raise ValueError('empty grid cannot be classified')
    return 'dot-field' if support.sum() <= SURFACE_SUPPORT_FRACTION * total else 'continuous-surface'


def dot_representation(a, budget, footprint=None):
    """Deterministic discrete dots of a raster (protocol rule 1: "raster's dots").

    * ``dot-field``: the finite-positive pixels themselves.
    * ``continuous-surface``: 3-px non-maximum-suppressed local maxima of the
      raster, taken greedily in order (value desc, then row, then column) up to
      ``budget`` dots.  ``budget`` should be the candidate's dot count so both
      rasters expose comparable emission budgets.

    The same rule is applied to every registry raster and to the candidate
    itself; no raster is exempted and no threshold is fitted to outcomes.
    """
    a = np.asarray(a, np.float32)
    support = _dots(a)
    if footprint is not None:
        fp = np.asarray(footprint, bool)
        if fp.shape != a.shape:
            raise ValueError('footprint shape mismatch')
        support = support & fp
    kind = representation_class(a, footprint)
    if kind == 'dot-field':
        return support, kind
    if budget <= 0:
        raise ValueError('representation budget must be positive')
    # 3 px non-maximum suppression: a peak is a positive cell that equals the
    # maximum over its 7x7 (radius-3) neighbourhood.
    window = int(2 * int(np.ceil(RADIUS_PX)) + 1)
    peaks = support & (a >= maximum_filter(a, size=window, mode='constant', cval=0.0))
    ys, xs = np.nonzero(peaks)
    if ys.size == 0:
        return np.zeros(a.shape, bool), kind
    order = np.lexsort((xs, ys, -a[ys, xs]))
    chosen = np.zeros(a.shape, bool)
    suppressed = np.zeros(a.shape, bool)
    taken = 0
    r = int(np.ceil(RADIUS_PX))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = yy * yy + xx * xx <= RADIUS_PX * RADIUS_PX
    for idx in order:
        if taken >= int(budget):
            break
        y, x = int(ys[idx]), int(xs[idx])
        if suppressed[y, x]:
            continue
        chosen[y, x] = True
        taken += 1
        y0, y1 = max(0, y - r), min(a.shape[0], y + r + 1)
        x0, x1 = max(0, x - r), min(a.shape[1], x + r + 1)
        patch = disk[y0 - (y - r):y1 - (y - r), x0 - (x - r):x1 - (x - r)]
        suppressed[y0:y1, x0:x1] |= patch
    return chosen, kind


def _jaccard(a, b):
    u = int((a | b).sum())
    return float((a & b).sum() / u) if u else 0.0


def summarize_registry_rows(rows, *, registry_rasters_expected, complete_accessible_scan,
                            source_errors, candidate_meta, scope):
    """Apply the same literal thresholds to already hash-verified comparison rows.

    This allows a complete immutable prior audit to be extended with only newly
    published blobs, instead of re-downloading hundreds of unchanged rasters.
    The caller must prove candidate identity and the completeness/count of the
    combined registry before passing ``complete_accessible_scan=True``.
    """
    rows = list(rows)
    source_errors = list(source_errors or [])
    expected = int(registry_rasters_expected)
    checked = [r for r in rows if 'error' not in r]
    errors = [r for r in rows if 'error' in r]
    complete = bool(complete_accessible_scan and expected == len(rows)
                    and not errors and not source_errors)
    # The inherited stop gate is literal: only Spearman > 0.90 or forward
    # 3-pixel overlap > 0.70 (plus byte/pixel identity safeguards) can block.
    # Jaccard is reported for diagnosis, never substituted as a new threshold.
    flags = [r for r in checked if any(r.get(k, False) for k in (
        'duplicate_by_rho', 'duplicate_by_overlap',
        'identical_bytes', 'identical_decoded_predictions'))]
    flags_repr = [r for r in checked if any((
        r.get('duplicate_by_rho', False),
        r.get('duplicate_by_overlap_dots', r.get('duplicate_by_overlap', False)),
        r.get('identical_bytes', False),
        r.get('identical_decoded_predictions', False)))]
    rank_rows = [r for r in checked if r.get('spearman_full_footprint') is not None]
    worst_rho = max(rank_rows, key=lambda r: r['spearman_full_footprint'], default=None)
    worst_ov = max(checked, key=lambda r: r['my_dots_within_3px_of_theirs'], default=None)
    worst_ov_repr = max(checked, key=lambda r: r.get('my_dots_within_3px_of_their_dots',
                                                      r.get('my_dots_within_3px_of_theirs', 0.0)),
                        default=None)
    worst_jac = max(checked, key=lambda r: r['jaccard_dot_sets'], default=None)
    my_dot_count = int(candidate_meta['my_dots'])
    norm = bool(candidate_meta['candidate_rank_variation'])
    unique = complete and my_dot_count > 0 and norm and not flags
    unique_repr = complete and my_dot_count > 0 and norm and not flags_repr
    return dict(
        my_file=candidate_meta.get('my_file'), evidence_class='REGISTRY-MEASUREMENT',
        my_dots=my_dot_count,
        my_representation=candidate_meta.get('my_representation'),
        candidate_decoded_sha256=candidate_meta.get('candidate_decoded_sha256'),
        candidate_file_sha256=candidate_meta.get('candidate_file_sha256'),
        rho_limit=RHO_LIMIT, overlap_limit=OVERLAP_LIMIT, jaccard_limit=JACCARD_LIMIT,
        dot_representation_rule=(
            "IR-S6-01 ruling: a registry raster's dots are its discrete emission dots "
            "(finite-positive pixels when support <= 10% of the footprint; otherwise "
            "3-px NMS local maxima ranked by value at a budget matched to the "
            "candidate's dot count). The literal positive-support screen is reported "
            "unchanged alongside it."),
        registry_rasters_expected=expected, registry_rasters_checked=len(checked),
        complete_accessible_scan=complete, missing_or_invalid=len(errors),
        source_errors=source_errors,
        worst_spearman_full_footprint=(worst_rho['spearman_full_footprint'] if worst_rho else None),
        worst_rho_submission=(worst_rho['submission'] if worst_rho else None),
        worst_dot_overlap=(worst_ov['my_dots_within_3px_of_theirs'] if worst_ov else None),
        worst_overlap_submission=(worst_ov['submission'] if worst_ov else None),
        worst_dot_overlap_representation=(worst_ov_repr.get('my_dots_within_3px_of_their_dots',
                                                            worst_ov_repr.get('my_dots_within_3px_of_theirs'))
                                          if worst_ov_repr else None),
        worst_overlap_representation_submission=(worst_ov_repr['submission'] if worst_ov_repr else None),
        worst_jaccard_dot_sets=(worst_jac['jaccard_dot_sets'] if worst_jac else None),
        worst_jaccard_submission=(worst_jac['submission'] if worst_jac else None),
        byte_unique_among_checked=bool(checked) and not any(r.get('identical_bytes', False) for r in checked),
        pixel_unique_among_checked=bool(checked) and not any(r.get('identical_decoded_predictions', False) for r in checked),
        duplicate_count=len(flags),
        duplicate_count_dot_representation=len(flags_repr),
        unique=bool(unique),
        unique_under_dot_representation=bool(unique_repr),
        literal_support_screen=dict(
            definition='finite prediction > 0 is a dot (inherited literal rule)',
            duplicate_count=len(flags),
            worst_dot_overlap=(worst_ov['my_dots_within_3px_of_theirs'] if worst_ov else None),
            worst_overlap_submission=(worst_ov['submission'] if worst_ov else None),
            unique=bool(unique),
            caveat=('A dense continuous registry surface makes this screen fire for '
                    'every nonempty candidate; it also fires between real distinct '
                    'owner-submitted files. Reported unchanged, never waived.')),
        rows=rows,
        jaccard_diagnostic_only=True,
        verdict='promote-to-selector-only' if unique_repr else 'negative',
        stop_required=bool(flags_repr or not complete or not my_dot_count or not norm),
        literal_stop_required=bool(flags or not complete or not my_dot_count or not norm),
        candidate_rank_variation=norm,
        scope=scope)


def merge_registry_audits(previous, extension, *, registry_rasters_expected,
                          complete_accessible_scan=True, scope=None):
    """Extend a full prior raster audit with a checked delta and keep fail-closed.

    Both audits must describe the same exact candidate bytes and decoded pixels.
    Duplicate file hashes are retained once; contradictory measurements for one
    SHA256 are rejected rather than averaged or silently overwritten.
    """
    identity_keys = ('candidate_file_sha256', 'candidate_decoded_sha256', 'my_dots',
                     'candidate_rank_variation', 'my_representation')
    for key in identity_keys:
        if previous.get(key) != extension.get(key):
            raise ValueError(f'cannot merge audits with different candidate {key}')
    if any(previous.get(key) != extension.get(key)
           for key in ('rho_limit', 'overlap_limit', 'jaccard_limit')):
        raise ValueError('cannot merge audits with different uniqueness thresholds')
    if not previous.get('complete_accessible_scan'):
        raise ValueError('base audit is not a complete accessible registry scan')
    if not extension.get('complete_accessible_scan'):
        raise ValueError('registry delta is incomplete')
    if previous.get('missing_or_invalid') or extension.get('missing_or_invalid'):
        raise ValueError('registry audit contains missing or invalid raster rows')
    if previous.get('source_errors') or extension.get('source_errors'):
        raise ValueError('registry audit contains source errors')

    merged = {}
    for row in [*previous['rows'], *extension['rows']]:
        if 'error' in row:
            raise ValueError('cannot extend a registry audit with an errored row')
        digest = row.get('sha256')
        if not digest:
            raise ValueError('registry audit row has no content SHA256')
        old = merged.get(digest)
        if old is not None:
            for metric in ('my_dots_within_3px_of_theirs', 'spearman_full_footprint',
                           'jaccard_dot_sets', 'identical_bytes',
                           'identical_decoded_predictions',
                           'my_dots_within_3px_of_their_dots',
                           'jaccard_representation_dots',
                           'duplicate_by_overlap_dots',
                           'their_representation', 'their_dots_representation'):
                if old.get(metric) != row.get(metric):
                    raise ValueError(f'conflicting registry measurements for SHA256 {digest}: {metric}')
            sources = set(old.get('sources', []))
            if old.get('submission'):
                sources.add(old['submission'])
            if row.get('submission'):
                sources.add(row['submission'])
            sources.update(row.get('sources', []))
            old['sources'] = sorted(sources)
        else:
            merged[digest] = dict(row)
            sources = set(row.get('sources', []))
            if row.get('submission'):
                sources.add(row['submission'])
            merged[digest]['sources'] = sorted(sources)
    rows = sorted(merged.values(), key=lambda r: (r.get('repo', ''), r.get('submission', ''), r['sha256']))
    meta = {k: previous.get(k) for k in identity_keys}
    meta['my_file'] = previous.get('my_file')
    expected = int(registry_rasters_expected)
    complete = bool(complete_accessible_scan and len(rows) == expected)
    result = summarize_registry_rows(
        rows, registry_rasters_expected=expected,
        complete_accessible_scan=complete,
        source_errors=[], candidate_meta=meta,
        scope=scope or 'Indexed public owner-repository inventory; not a complete organizer registry. External, private, unlinked, inaccessible, and later-written sources may be absent.',
    )
    result['phase'] = extension.get('phase', previous.get('phase'))
    result['reviewed_utc'] = extension.get('reviewed_utc')
    result['submission_slots_used'] = int(previous.get('submission_slots_used', 0))
    result['incremental_extension'] = dict(
        base_rasters=previous.get('registry_rasters_checked'),
        newly_discovered_rasters=extension.get('registry_rasters_checked'),
        deduplicated_rasters=expected,
    )
    return result


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
    my_kind = representation_class(mine, fp)
    my_repr_support, _ = dot_representation(mine, max(my_dot_count, 1), fp)
    my_repr_count = int(my_repr_support.sum())
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
            # Dot-representation screen (IR-S6-01 ruling): "their dots" are the
            # discrete emission dots of their raster, not every positive pixel.
            repr_support, repr_kind = dot_representation(theirs, max(my_repr_count, 1), fp)
            their_repr_dots = int(repr_support.sum())
            ov_repr = float(_near(repr_support)[my_repr_support].mean()) if my_repr_count and their_repr_dots else 0.0
            jac_repr = _jaccard(my_repr_support, repr_support)
            row = {**base, 'sha256':digest, 'decoded_sha256':their_decoded,
                'their_dots':int(support.sum()), 'my_dots_within_3px_of_theirs':ov,
                'their_dots_within_3px_of_mine':reverse, 'spearman_full_footprint':rho,
                'jaccard_dot_sets':jac,
                'their_representation':repr_kind,
                'their_dots_representation':their_repr_dots,
                'my_dots_within_3px_of_their_dots':ov_repr,
                'jaccard_representation_dots':jac_repr,
                'identical_bytes':bool(file_sha256 and digest==file_sha256),
                'identical_decoded_predictions':bool(their_decoded==decoded_digest),
                'duplicate_by_rho':bool(rho is not None and rho > RHO_LIMIT),
                'duplicate_by_overlap':bool(ov > OVERLAP_LIMIT),
                'duplicate_by_overlap_dots':bool(ov_repr > OVERLAP_LIMIT),
                'duplicate_by_jaccard':bool(jac > JACCARD_LIMIT)}
            rows.append(row)
        except (OSError, ValueError, rasterio.errors.RasterioError) as e:
            rows.append({**base, 'error':str(e)})
        if progress:
            progress(i+1,len(records),rows[-1])
    complete = inventory_complete and bool(records) and not source_errors
    return summarize_registry_rows(
        rows,
        registry_rasters_expected=len(records),
        complete_accessible_scan=complete,
        source_errors=source_errors,
        candidate_meta=dict(
            my_file=None,
            my_dots=my_dot_count,
            my_representation=my_kind,
            candidate_decoded_sha256=decoded_digest,
            candidate_file_sha256=file_sha256,
            candidate_rank_variation=norm > 0,
        ),
        scope='All hash-verified accessible entries in the indexed public owner-repository inventory; not a complete organizer registry. External/private/unlinked/inaccessible files may be absent. Reverse overlap is diagnostic only.',
    )


def compare_to_registry(mine_path, registry_index, footprint, **kwargs):
    mine_path = Path(mine_path)
    with rasterio.open(mine_path) as src:
        if src.count != 1:
            raise ValueError('candidate must be single band')
        mine = src.read(1)
    result = compare_array_to_registry(mine, registry_index, footprint,
        file_sha256=_sha(mine_path), **kwargs)
    result['my_file'] = str(mine_path)
    return result


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
