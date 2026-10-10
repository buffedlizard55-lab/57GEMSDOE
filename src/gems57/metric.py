"""Distance-Weighted Tversky Index (DTI) for the DOE GEMS Prize Challenge.

Metric definition transcribed from the official problem description
(DrivenData competition 306, page 967) and cross-checked against the shared
template implementation in ``GEMSDOE32/src/gems32/metric.py`` (cloned from
https://github.com/buffedlizard55-lab/GEMSDOE32, commit-verified locally).

Definitions
-----------
Triangular kernel, radius R = 300 m = 3 px at the 100 m grid::

    k(d) = max(1 - d / R, 0)

Components (G = truth pixels, P = predicted pixels, p(x) = predicted value)::

    TP_w = sum_{g in G} max_{x : d(x,g) <= R} p(x) * k(d(x,g))
    FP_w = sum_{x : p(x) > 0} p(x) * [1 - max_{g in G} k(d(x,g))]
    FN_w = |G| - TP_w
    DTI  = TP_w / (TP_w + alpha*FP_w + beta*FN_w)      alpha = 0.2, beta = 0.8

Binary-dot algebra (used for the emission decision)
---------------------------------------------------
For a binary dot field of n dots, write

* ``T = TP_w = sum_{g in G} max_{x in P} k(d(x,g))``  -- a sum over **truth** cells
* ``M = sum_{x in P} max_{g in G} k(d(x,g))``         -- a sum over **dots**

so that ``FP_w = n - M`` and the denominator is::

    D = alpha*(T + n - M) + beta*|G|

``T`` and ``M`` are **not** the same quantity: ``T`` saturates at 1 per truth
cell while ``M`` saturates at 1 per dot, so a cluster of dots around one truth
cell has ``M > T``.  Collapsing ``D`` to ``alpha*n + beta*|G|`` is only valid
when ``T == M`` (a near-bijection between dots and truth cells) -- an error
carried by the shared template's prose and corrected here; the template's own
:func:`dti_algebra` keeps ``T``, ``S`` and ``M`` separate and is right.

Adding one dot with self-credit ``k = max_g k(d(x,g))`` and marginal truth credit
``dT`` (``dT <= k``, with equality when the dot covers only truth cells no
earlier dot already covered) gives ``dD = alpha*(dT + 1 - k)`` and, writing
``DTI = T / D``,

    new DTI = (T + dT) / (D + alpha*(dT + 1 - k))
    dDTI > 0  <=>  (T + dT)*D > T*(D + alpha*(dT + 1 - k))
              <=>  dT > alpha * DTI * (dT + 1 - k)

For a non-redundant dot (``dT == k``) this reduces to the simple bar
``k > alpha * DTI``, which is the form quoted in the competition literature.

.. warning:: an earlier revision of this module tested ``dT * D > DTI * alpha *
   (dT + 1 - k)``, which is the same inequality multiplied through by ``D`` on
   the wrong side only.  Because ``D`` is of order ``beta*K`` (tens of
   thousands), that form makes the bar smaller by a factor of ``D`` and the
   greedy allocation never terminates -- it ran to its hard cap and emitted
   960,000 dots for a HOLDOUT-DTI of 0.0797.  Caught by the DTI-vs-brute-force
   test suite; see irregularity ``IR-57-BAR-01``.
:func:`gems57.emit.greedy_allocate` uses the **exact** two-sided test above,
tracking both ``T`` and ``M``.  All of it is verified against
:func:`dti_bruteforce` by ``tests/test_metric.py``.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA: float = 0.2
BETA: float = 0.8
RADIUS_PX: float = 3.0      # 300 m at the 100 m competition grid
PIXEL_M: float = 100.0
RADIUS_M: float = RADIUS_PX * PIXEL_M
EPS: float = 1e-12


def kernel(d, radius: float = RADIUS_PX) -> np.ndarray:
    """Triangular kernel ``max(1 - d/R, 0)``; ``d`` in pixels."""
    return np.maximum(1.0 - np.asarray(d, dtype=np.float64) / radius, 0.0)


def offsets(radius: float = RADIUS_PX) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """All lattice offsets with non-zero kernel weight, and their weights."""
    r = int(np.ceil(radius))
    dy, dx, kw = [], [], []
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            k = float(kernel(np.hypot(j, i), radius))
            if k > 0.0:
                dy.append(j)
                dx.append(i)
                kw.append(k)
    return (np.array(dy, np.int64), np.array(dx, np.int64), np.array(kw, np.float64))


OFF_DY, OFF_DX, OFF_K = offsets()


def marginal_inclusion_threshold(current_dti: float, alpha: float = ALPHA) -> float:
    """Minimum realised kernel credit ``k`` for one more **non-redundant** dot.

    ``dDTI > 0 <=> k > alpha * DTI`` when the dot's marginal truth credit equals
    its self-credit.  For a redundant dot use :func:`marginal_accept`, which
    applies the exact two-sided test.
    """
    return alpha * float(current_dti)


def marginal_accept(dT: float, k_self: float, T: float, M: float, n: int,
                    K: float, alpha: float = ALPHA, beta: float = BETA) -> bool:
    """Exact test: does adding one dot raise DTI?

    ``dT`` is the increase in ``TP_w``; ``k_self`` is the dot's own
    ``max_g k(d(x,g))``; ``T``/``M``/``n`` are the current totals; ``K = |G|``.

    Implemented by recomputing DTI before and after rather than by algebra, so
    the test cannot drift from the metric.
    """
    D0 = alpha * (T + n - M) + beta * K + EPS
    D1 = alpha * (T + dT + (n + 1) - (M + k_self)) + beta * K + EPS
    return (T + dT) / D1 > T / D0


def dti_from_components(tp: float, fp: float, fn: float,
                        alpha: float = ALPHA, beta: float = BETA):
    """DTI from additive components; accepts scalars or aligned NumPy arrays."""
    value = np.asarray(tp, dtype=np.float64) / (
        np.asarray(tp, dtype=np.float64)
        + alpha * np.asarray(fp, dtype=np.float64)
        + beta * np.asarray(fn, dtype=np.float64) + EPS)
    return float(value) if value.ndim == 0 else value


def dti_binary(pred_bool, truth, valid=None, known=None,
               alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Exact DTI for a binary prediction field via Euclidean distance transforms.

    ``valid`` restricts the scored domain (the study-area footprint); ``known``
    removes pixels that the organiser masks out of scoring (mapped catalogue
    faults -- see organiser thread 11516).
    """
    pred_bool = np.asarray(pred_bool, bool)
    truth = np.asarray(truth, bool)
    valid_ = np.ones(pred_bool.shape, bool) if valid is None else np.asarray(valid, bool)
    known_ = np.zeros(pred_bool.shape, bool) if known is None else np.asarray(known, bool)
    if pred_bool.shape != truth.shape or pred_bool.shape != valid_.shape:
        raise ValueError("grid shape mismatch")
    active = valid_ & ~known_
    p = pred_bool & active
    g = truth & active
    n = int(g.sum())
    n_emit = int(p.sum())
    if n == 0:
        return dict(tp=0.0, fp=float(n_emit), fn=0.0, n_truth=0, n_emitted=n_emit,
                    dti=0.0, coverage=0.0)
    if n_emit == 0:
        return dict(tp=0.0, fp=0.0, fn=float(n), n_truth=n, n_emitted=0,
                    dti=0.0, coverage=0.0)
    dp = distance_transform_edt(~p)
    tp = float(kernel(dp[g]).sum())
    fn = float(n) - tp
    dg = distance_transform_edt(~g)
    fp = float((1.0 - kernel(dg[p])).sum())
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n, n_emitted=n_emit,
                dti=dti_from_components(tp, fp, fn, alpha, beta), coverage=tp / n)


def max_cover(pred, truth):
    """Return official-kernel credit per truth pixel, per-pixel truth credit, and distance.

    The first result is row-major over truth pixels; the second and third match
    the prediction grid. Empty truth returns zero credit everywhere rather than
    treating the raster boundary as an implicit truth source.
    """
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, bool)
    if p.ndim != 2 or p.shape != g.shape:
        raise ValueError("grid shape mismatch")
    if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
        raise ValueError("predictions must be finite in [0,1]")
    yy, xx = np.nonzero(g)
    credit = np.zeros(len(yy), np.float64)
    h, w = p.shape
    for j, i, weight in zip(OFF_DY, OFF_DX, OFF_K):
        ny, nx = yy + j, xx + i
        valid = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        credit[valid] = np.maximum(
            credit[valid], p[ny[valid], nx[valid]] * weight)
    distance = (distance_transform_edt(~g) if len(yy)
                else np.full(p.shape, np.inf, dtype=np.float64))
    return credit, kernel(distance), distance


def _dti_vectors(pred, truth, active):
    """Shared exact-metric primitive: truth credits and emitted-pixel FP weights."""
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, bool) & np.asarray(active, bool)
    if p.ndim != 2 or g.shape != p.shape or np.asarray(active).shape != p.shape:
        raise ValueError("pred, truth and active must be aligned 2D arrays")
    vals = p[active]
    if not np.isfinite(vals).all() or (vals < 0).any() or (vals > 1).any():
        raise ValueError("predictions inside the scored domain must be finite and in [0, 1]")
    # Mask before credit convolution as well as before counting emitted pixels;
    # otherwise a prediction on a known/invalid fault pixel could credit a
    # neighboring withheld truth even though it should be excluded exactly.
    p = np.where(active, p, 0.0)
    yy, xx = np.nonzero(g)
    py, px = np.nonzero((p > 0) & active)
    n = int(yy.size)
    credit = np.zeros(n, np.float64)
    if n:
        H, W = p.shape
        for j, i, k in zip(OFF_DY, OFF_DX, OFF_K):
            ny, nx = yy + j, xx + i
            ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
            credit[ok] = np.maximum(credit[ok], p[ny[ok], nx[ok]] * k)
        dg = distance_transform_edt(~g)
        fp_values = (p[py, px].astype(np.float64)
                     * (1.0 - kernel(dg[py, px])))
    else:
        fp_values = p[py, px].astype(np.float64)
    return yy, xx, credit, py, px, fp_values


def dti_spatial_terms(pred, truth, valid=None, known=None, *, origin=(0, 0),
                      global_shape=None, block_side=200,
                      alpha: float = ALPHA, beta: float = BETA):
    """Exact DTI and additive terms grouped by fixed physical spatial blocks.

    Coordinates in ``origin`` place a cropped fold inside ``global_shape``;
    repeated folds/draws therefore land in the same clusters before bootstrap.
    Each returned row is ``(TP_w, FP_w, FN_w, withheld_positive_count)``.
    The arithmetic is shared with :func:`dti_exact`, not a second metric.
    """
    p = np.asarray(pred)
    g = np.asarray(truth, bool)
    if p.ndim != 2 or g.shape != p.shape:
        raise ValueError("pred and truth must be aligned 2D arrays")
    valid_ = np.ones(p.shape, bool) if valid is None else np.asarray(valid, bool)
    known_ = np.zeros(p.shape, bool) if known is None else np.asarray(known, bool)
    if valid_.shape != p.shape or known_.shape != p.shape:
        raise ValueError("grid shape mismatch")
    if int(block_side) <= 0:
        raise ValueError("block_side must be positive")
    oy, ox = map(int, origin)
    if min(oy, ox) < 0:
        raise ValueError("origin must be non-negative")
    if global_shape is None:
        global_shape = (oy + p.shape[0], ox + p.shape[1])
    gh, gw = map(int, global_shape)
    if gh <= 0 or gw <= 0 or oy + p.shape[0] > gh or ox + p.shape[1] > gw:
        raise ValueError("crop origin/shape is outside global_shape")
    active = valid_ & ~known_
    yy, xx, credit, py, px, fp_values = _dti_vectors(p, g, active)
    n_truth, n_emit = int(yy.size), int(py.size)
    tp, fp = float(credit.sum()), float(fp_values.sum())
    fn = float(n_truth) - tp
    result = dict(tp=tp, fp=fp, fn=fn, n_truth=n_truth, n_emitted=n_emit,
                  dti=dti_from_components(tp, fp, fn, alpha, beta),
                  coverage=float(tp / n_truth) if n_truth else 0.0)

    ncols = (gw + int(block_side) - 1) // int(block_side)
    nrows = (gh + int(block_side) - 1) // int(block_side)
    terms = np.zeros((nrows * ncols, 4), np.float64)
    if n_truth:
        gy, gx = yy + oy, xx + ox
        ids = (gy // block_side) * ncols + (gx // block_side)
        terms[:, 0] = np.bincount(ids, weights=credit, minlength=len(terms))
        terms[:, 2] = np.bincount(ids, weights=1.0 - credit, minlength=len(terms))
        terms[:, 3] = np.bincount(ids, minlength=len(terms))
    if n_emit:
        gy, gx = py + oy, px + ox
        ids = (gy // block_side) * ncols + (gx // block_side)
        terms[:, 1] = np.bincount(ids, weights=fp_values, minlength=len(terms))
    # Keep the total formula tied to the aggregate terms used by the bootstrap.
    totals = terms.sum(axis=0)
    expected = np.asarray([tp, fp, fn, n_truth], np.float64)
    np.testing.assert_allclose(totals, expected, rtol=1e-11, atol=1e-7)
    return result, terms


def dti_exact(pred, truth, valid=None, known=None,
              alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Exact DTI for arbitrary soft predictions in [0, 1] (max over the kernel)."""
    pred = np.asarray(pred)
    truth = np.asarray(truth, bool)
    valid_ = np.ones(pred.shape, bool) if valid is None else np.asarray(valid, bool)
    known_ = np.zeros(pred.shape, bool) if known is None else np.asarray(known, bool)
    if pred.shape != truth.shape or valid_.shape != pred.shape or known_.shape != pred.shape:
        raise ValueError("grid shape mismatch")
    active = valid_ & ~known_
    yy, xx, credit, py, px, fp_values = _dti_vectors(pred, truth, active)
    tp, fp = float(credit.sum()), float(fp_values.sum())
    n_truth = int(yy.size)
    fn = float(n_truth) - tp
    return dict(tp=tp, fp=fp, fn=fn, n_truth=n_truth, n_emitted=int(py.size),
                dti=dti_from_components(tp, fp, fn, alpha, beta),
                coverage=float(tp / n_truth) if n_truth else 0.0)


def dti_bruteforce(pred, truth, alpha: float = ALPHA, beta: float = BETA,
                   radius: float = RADIUS_PX) -> dict:
    """Literal O(|G|*|P|) transcription of the published equations (unit-test oracle)."""
    pred = np.asarray(pred, float)
    truth = np.asarray(truth, bool)
    gs = np.argwhere(truth)
    xs = np.argwhere(pred > 0)
    tp = fn = 0.0
    for g in gs:
        best = 0.0
        for x in xs:
            d = float(np.hypot(*(x - g)))
            if d <= radius:
                best = max(best, pred[tuple(x)] * max(1.0 - d / radius, 0.0))
        tp += best
        fn += 1.0 - best
    fp = 0.0
    for x in xs:
        kmax = 0.0
        for g in gs:
            kmax = max(kmax, max(1.0 - float(np.hypot(*(x - g))) / radius, 0.0))
        fp += pred[tuple(x)] * (1.0 - kmax)
    return dict(tp=tp, fp=fp, fn=fn,
                dti=dti_from_components(tp, fp, fn, alpha, beta))
