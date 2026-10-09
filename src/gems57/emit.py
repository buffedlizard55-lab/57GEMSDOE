"""Dot allocation: greedy max-coverage at the exact DTI marginal bar.

Why this allocation rule
------------------------
For a binary dot field (see :mod:`gems57.metric` for the derivation, including
why the denominator does **not** collapse to ``alpha*n + beta*|G|``)::

    D   = alpha*(T + n - M) + beta*|G|
    DTI = T / D

where ``T`` is the covered truth credit and ``M`` the total self-credit of the
emitted dots.  A dot at ``x`` has a **fixed** self-credit
``k(x) = E[k](x) = sum_g p(g) k(d(x,g))`` -- the convolution of the per-cell
truth probability with the kernel -- which does not depend on the other dots,
while its marginal truth credit ``dT(x)`` falls as neighbouring truth cells get
covered.  The exact acceptance test ``dT > alpha*DTI*(dT + 1 - k)`` therefore
rearranges to a per-candidate bar::

    dT > c * (1 - k(x)),     c = alpha*DTI / (1 - alpha*DTI)

which is what the loop below applies.  Candidates are processed in rounds in
decreasing ``E[k]`` order with the bar frozen inside a round; a candidate is only
re-evaluated when a nearby acceptance could have changed its ``dT``.  ``dT`` is
non-increasing and the bar rises while DTI rises, so the loop terminates when a
round accepts nothing.

Nothing about the *shape* of the emission is assumed here -- the spatial
structure comes entirely from ``p``, which :mod:`gems57.anatomy` fits to the
hide-and-recover holdout.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage as ndi

from .metric import ALPHA, BETA, EPS, OFF_DX, OFF_DY, OFF_K


def expected_credit(p: np.ndarray) -> np.ndarray:
    """``E[k](x) = sum_g p(g) k(d(x,g))`` -- convolution of ``p`` with the kernel.

    For a candidate dot at ``x`` this is simultaneously the expected marginal
    truth credit (when nothing nearby is covered yet) and the dot's self-credit
    ``k(x)``.
    """
    p = np.asarray(p, np.float32)
    out = np.zeros(p.shape, np.float32)
    H, W = p.shape
    for j, i, k in zip(OFF_DY, OFF_DX, OFF_K):
        ys0, ys1 = max(0, j), min(H, H + j)
        xs0, xs1 = max(0, i), min(W, W + i)
        out[ys0:ys1, xs0:xs1] += p[max(0, -j):min(H, H - j),
                                   max(0, -i):min(W, W - i)] * np.float32(k)
    return out


@dataclass
class Allocation:
    emitted: np.ndarray
    n_dots: int
    expected_covered_credit: float = 0.0   # running T under the surrogate p
    expected_self_credit: float = 0.0      # running M under the surrogate p
    rounds: int = 0
    surrogate_dti: float = 0.0
    trace: list = field(default_factory=list)


def greedy_allocate(p: np.ndarray, allowed: np.ndarray, k_truth: float, *,
                    floor: float = 0.02, max_dots: int = 200_000,
                    candidate_cap: int = 400_000, per_round: int = 20_000,
                    max_rounds: int = 400, trace_every: int = 0) -> Allocation:
    """Select dots while each one provably raises the surrogate DTI.

    Parameters
    ----------
    p
        Per-cell probability of being a hidden truth cell, in [0, 1].
    allowed
        Boolean mask of cells that may carry a dot (footprint, catalogue removed).
    k_truth
        ``|G|``, the number of hidden truth cells, which sets the bar.
    floor
        Cells with ``E[k] < floor`` are never considered.  Pure speed-up: with
        ``alpha = 0.2`` the bar is ``c*(1-k) >= 0`` and any candidate accepted at
        a realistic score has ``E[k]`` well above this.
    """
    p = np.asarray(p, np.float32)
    H, W = p.shape
    ek = expected_credit(p)
    cand = allowed & (ek >= floor)
    ys, xs = np.nonzero(cand)
    if ys.size == 0:
        return Allocation(np.zeros(p.shape, bool), 0)
    order = np.argsort(-ek[ys, xs], kind="stable")
    if order.size > candidate_cap:
        order = order[:candidate_cap]
    ys, xs = ys[order], xs[order]
    ekc = ek[ys, xs].astype(np.float64)
    # ``E[k]`` is a *sum* of p*k over the neighbourhood and can exceed 1, but the
    # metric's per-dot self-credit is ``max_g k(d(x,g))``, which cannot.  Using
    # the unclipped sum makes ``1 - k`` negative, which flips the bar negative and
    # lets zero-credit dots through -- that bug produced 7,987 duplicate
    # acceptances on a synthetic field (``IR-57-KCLIP-01``).
    kself = np.minimum(ekc, 1.0)
    ncand = ys.size

    cover = np.zeros(p.shape, np.float32)
    emitted = np.zeros(p.shape, bool)
    upper = ekc.copy()            # non-increasing upper bound on each candidate's dT
    dirty = np.ones(ncand, bool)  # needs (re-)evaluation
    T = M = 0.0
    n_dots = 0
    rounds = 0
    trace: list[dict] = []

    while n_dots < max_dots and rounds < max_rounds:
        rounds += 1
        def _c() -> float | None:
            D_ = ALPHA * (T + n_dots - M) + BETA * k_truth + EPS
            a_ = ALPHA * (T / D_)
            return None if a_ >= 1.0 else a_ / (1.0 - a_)

        c = _c()
        if c is None:
            break
        # the bar is recomputed after every acceptance: DTI moves inside a round,
        # and freezing it lets marginal acceptances slip through that would
        # actually lower DTI (the surrogate DTI was non-monotone before this fix)
        eligible = dirty & (upper > c * (1.0 - kself))
        if not eligible.any():
            break
        idxs = np.flatnonzero(eligible)
        if idxs.size > per_round:
            idxs = idxs[:per_round]
        accepted = 0
        for i in idxs:
            if n_dots >= max_dots:
                break
            if c is None:
                break
            y, x = int(ys[i]), int(xs[i])
            if emitted[y, x]:
                dirty[i] = False
                continue
            ny = y + OFF_DY
            nx = x + OFF_DX
            ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
            nyv, nxv, kw = ny[ok], nx[ok], OFF_K[ok]
            pv = p[nyv, nxv].astype(np.float64)
            cv = cover[nyv, nxv].astype(np.float64)
            dT = float((pv * np.maximum(kw - cv, 0.0)).sum())
            upper[i] = dT
            dirty[i] = False
            if dT <= c * (1.0 - kself[i]):
                continue
            emitted[y, x] = True
            n_dots += 1
            T += dT
            M += float(kself[i])
            np.maximum.at(cover, (nyv, nxv), kw.astype(np.float32))
            accepted += 1
            c = _c()
            # candidates within 6 px can have a changed dT (3 px kernel, twice)
            m = (ys >= y - 6) & (ys <= y + 6) & (xs >= x - 6) & (xs <= x + 6)
            dirty[m] = True
            dirty[i] = False
            if trace_every and n_dots % trace_every == 0:
                D2 = ALPHA * (T + n_dots - M) + BETA * k_truth + EPS
                trace.append({"n_dots": n_dots, "T": T, "M": M,
                              "dti_est": T / D2, "last_dT": dT})
        if accepted == 0:
            break

    D = ALPHA * (T + n_dots - M) + BETA * k_truth + EPS
    return Allocation(emitted=emitted, n_dots=n_dots,
                      expected_covered_credit=T, expected_self_credit=M,
                      rounds=rounds, surrogate_dti=float(T / D), trace=trace)


def dilate_zone(mask: np.ndarray, px: int) -> np.ndarray:
    """Dilate a mask by ``px`` pixels (square structuring element)."""
    return ndi.binary_dilation(np.asarray(mask, bool), iterations=int(px))
