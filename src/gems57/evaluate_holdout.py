"""Shared pooled hide-and-recover evaluator for the GEMS DTI.

The metric arithmetic and per-cell credit maps delegate to ``metric.py``.
Scoring masks are assembled here from the fold's visible catalogue, truth, and
region masks; spatial-block terms are additive summaries of those same exact
per-pixel credits, not a second scoring implementation.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
from . import metric

VERSION = 'gems57-pooled-hide-v2'
_EVALUATOR_FILES = (
    'src/gems57/evaluate_holdout.py',
    'src/gems57/holdout.py',
    'src/gems57/metric.py',
    'src/gems57/spatial.py',
    'src/gems57/grid.py',
    'src/gems57/network.py',
)
_ROOT = Path(__file__).resolve().parents[2]


def implementation_hashes():
    """Content hashes for the evaluator and its fold/grid dependencies."""
    return {name: hashlib.sha256((_ROOT / name).read_bytes()).hexdigest()
            for name in _EVALUATOR_FILES}


def evaluate(prediction, fold, valid, block_side=200):
    """Score one fold and return exact additive terms per spatial block.

    Required fold masks are ``region``, ``visible`` and ``truth``.  Predictions
    are validated before masking so malformed values cannot be hidden outside
    the scored region; visible catalogue cells are then removed pixel-exactly.
    """
    if not isinstance(block_side, (int, np.integer)) or block_side <= 0:
        raise ValueError('block_side must be a positive integer')
    if not isinstance(fold, dict) or not {'region', 'visible', 'truth'} <= set(fold):
        raise ValueError('fold must provide region, visible, and truth masks')

    p_raw = np.asarray(prediction)
    if p_raw.ndim != 2:
        raise ValueError('prediction must be a 2-D array')
    numeric = np.issubdtype(p_raw.dtype, np.number) or np.issubdtype(p_raw.dtype, np.bool_)
    if not numeric or np.iscomplexobj(p_raw):
        raise ValueError('prediction must be a real numeric array')
    if not np.isfinite(p_raw).all() or (p_raw < 0).any() or (p_raw > 1).any():
        raise ValueError('predictions must be finite in [0,1] before masking')
    valid = np.asarray(valid, dtype=bool)
    region = np.asarray(fold['region'], dtype=bool)
    visible = np.asarray(fold['visible'], dtype=bool)
    hidden = np.asarray(fold['truth'], dtype=bool)
    if any(mask.shape != p_raw.shape for mask in (valid, region, visible, hidden)):
        raise ValueError('prediction, validity, and fold masks must have matching shapes')
    truth = valid & region & hidden
    if not truth.any():
        raise ValueError('a holdout fold must contain positives in the scored region')
    if np.any(truth & visible):
        raise ValueError('withheld truth overlaps the visible catalogue mask')

    score_region = valid & region
    p = np.where(score_region & ~visible, p_raw, 0.0)
    covers, q, _ = metric.max_cover(p, truth)
    tpw = float(covers[truth].sum())
    fnw = float(truth.sum()) - tpw
    positive = p > 0
    fpw = float((p[positive].astype(np.float64) * (1.0 - q[positive])).sum())
    emitted = int(positive.sum())
    result = dict(
        dti=metric.dti_from_components(tpw, fpw, fnw),
        tpw=tpw, fpw=fpw, fnw=fnw,
        n_truth=int(truth.sum()), emitted=emitted,
        evidence_class='HOLDOUT-DTI', evaluator_version=VERSION,
    )

    h, w = truth.shape
    ncols = (w + block_side - 1) // block_side
    nrows = (h + block_side - 1) // block_side
    terms = np.zeros((ncols * nrows, 4), np.float64)
    y, x = np.nonzero(truth)
    ids = (y // block_side) * ncols + (x // block_side)
    terms[:, 0] = np.bincount(ids, weights=covers[y, x], minlength=len(terms))
    terms[:, 2] = np.bincount(ids, weights=1.0 - covers[y, x], minlength=len(terms))
    terms[:, 3] = np.bincount(ids, weights=np.ones(y.size), minlength=len(terms))
    y, x = np.nonzero(positive)
    ids = (y // block_side) * ncols + (x // block_side)
    terms[:, 1] = np.bincount(
        ids, weights=p[y, x].astype(np.float64) * (1.0 - q[y, x]), minlength=len(terms))
    totals = terms.sum(axis=0)
    np.testing.assert_allclose(totals, [tpw, fpw, fnw, result['n_truth']],
                               rtol=1e-11, atol=1e-7)
    result['spatial_bootstrap_cluster_m'] = block_side * metric.PIXEL_M
    return result, terms


def from_terms(terms):
    a = np.asarray(terms, dtype=float)
    tp, fp, fn = a[..., 0], a[..., 1], a[..., 2]
    den = tp + metric.ALPHA * fp + metric.BETA * fn + metric.EPS
    return np.divide(tp, den, out=np.zeros_like(tp), where=den > 0)


def pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate='disagreement'):
    """Pool terms first; paired percentile CI resamples physical 20 km blocks.

    Each arm has identical block coordinates/order and evaluation masks. Contributions
    from the same physical block across folds are merged BEFORE resampling, so overlap
    in a component tail is not mistaken for an independent new spatial cluster.
    """
    names = list(terms_by_arm)
    if not names or candidate not in terms_by_arm:
        raise ValueError('candidate and at least one arm required')
    if draws < 20:
        raise ValueError('too few bootstrap draws')
    arrays = {n: np.asarray(v, float) for n, v in terms_by_arm.items()}
    shape = next(iter(arrays.values())).shape
    if len(shape) != 2 or shape[1] != 4 or any(a.shape != shape for a in arrays.values()):
        raise ValueError('aligned per-spatial-block arrays of four terms required')
    if any(not np.isfinite(a).all() or (a < -1e-8).any() for a in arrays.values()):
        raise ValueError('invalid metric terms')
    reference_truth = arrays[names[0]][:, 3]
    if (not np.equal(reference_truth, np.rint(reference_truth)).all()
            or any(not np.array_equal(a[:, 3], reference_truth) for a in arrays.values())):
        raise ValueError('all candidate/control arms must use the same integer truth count per spatial block')
    # Include negative-only clusters carrying FP weight for any comparator.
    active = np.any(np.stack([a.sum(axis=1) > 0 for a in arrays.values()]), axis=0)
    arrays = {n: a[active] for n, a in arrays.items()}
    nb = int(active.sum())
    if nb < 2:
        raise ValueError('need at least two nonempty spatial clusters')
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, nb, size=(draws, nb))
    boot = {n: from_terms(a[picks].sum(axis=1)) for n, a in arrays.items()}
    summaries = {}
    for n, a in arrays.items():
        t = a.sum(axis=0)
        summaries[n] = dict(evidence_class='HOLDOUT-DTI', evaluator_version=VERSION,
            dti=float(from_terms(t)), ci95=[float(x) for x in np.quantile(boot[n], [.025, .975])],
            withheld_positive_pixels=int(round(t[3])), tpw=float(t[0]), fpw=float(t[1]), fnw=float(t[2]))
    controls = [n for n in names if n != candidate]
    best = max(controls, key=lambda n: summaries[n]['dti']) if controls else None
    differences = {}
    for n in controls:
        delta = boot[candidate] - boot[n]
        differences[n] = dict(evidence_class='HOLDOUT-DTI', evaluator_version=VERSION,
            delta=summaries[candidate]['dti'] - summaries[n]['dti'],
            ci95=[float(x) for x in np.quantile(delta, [.025, .975])],
            withheld_positive_pixels=summaries[candidate]['withheld_positive_pixels'])
    return dict(evidence_class='HOLDOUT-DTI', evaluator_version=VERSION,
        alpha=metric.ALPHA, beta=metric.BETA, triangular_radius_m=metric.R_M,
        pooled=True, scores=summaries, best_comparable_control=best,
        paired_differences=differences, bootstrap=dict(method='paired physical spatial-cluster percentile',
            clusters=nb, draws=draws, seed=seed, confidence=.95,
            caveat='Conditional on fitted folds, catalogue labels and fixed budgets; not a leaderboard interval.'),
        implementation_sha256=implementation_hashes())
