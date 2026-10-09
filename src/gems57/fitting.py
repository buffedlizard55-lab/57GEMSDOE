"""Fitting, leakage canary and leave-one-quadrant-out evaluation.

The intensity model is a gradient-boosted classifier over the nine
fault-zone-anatomy features in :data:`gems57.anatomy.FEATURES`.  Nothing about
the shape of the response is assumed: the distance decay, the stepover/along-
strike coupling, the length scaling and the orientation selectivity are all
learned.  The model is calibrated to the observed withheld-pixel base rate by a
single moment-matching scale factor, because the emission bar
(``alpha * DTI``) is an *absolute* threshold on expected kernel credit.

Evaluation is leave-one-quadrant-out: the model for quadrant *q* is trained on
the six cells of the other three quadrants (both draws) and applied to the two
cells of *q*.  Quadrants are spatially disjoint, so this is a spatially blocked
estimate, not a random split.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from .anatomy import FEATURES, fold_geometry
from .emit import expected_credit, greedy_allocate
from .holdout import Cell, HoldoutContext
from .metric import dti_binary

NEG_PER_CELL = 60_000
GBM_KW = dict(max_depth=6, max_iter=220, learning_rate=0.08,
              min_samples_leaf=60, l2_regularization=1.0,
              early_stopping=False, random_state=0)


def _full(ctx: HoldoutContext, cell: Cell) -> np.ndarray:
    m = np.zeros(ctx.grid.shape, bool)
    m[cell.bbox] = cell.active
    return m


def cell_geometry(ctx: HoldoutContext, cell: Cell, geo: dict | None = None):
    dom = _full(ctx, cell)
    g = fold_geometry(ctx.grid, ctx.visible(cell.key),
                      ctx.hidden_by_cell[cell.key], dom, cell.key, geo=geo)
    return g


def sample_train(rng, geoms: list, neg_per_cell: int = NEG_PER_CELL):
    """Stack feature matrices with negative subsampling and compensating weights."""
    Xs, ys, ws = [], [], []
    for g in geoms:
        pos = g.y == 1
        Xs.append(g.X[pos]); ys.append(np.ones(int(pos.sum()), np.int8))
        ws.append(np.ones(int(pos.sum()), np.float64))
        neg = np.flatnonzero(~pos)
        if neg.size > neg_per_cell:
            neg = rng.choice(neg, size=neg_per_cell, replace=False)
        Xs.append(g.X[neg]); ys.append(np.zeros(neg.size, np.int8))
        w = float((~pos).sum()) / max(neg.size, 1)
        ws.append(np.full(neg.size, w, np.float64))
    return np.vstack(Xs), np.concatenate(ys), np.concatenate(ws)


def fit_model(geoms: list, seed: int = 0, cols: list[int] | None = None):
    """Fit the GBM and return it with the moment-matching calibration scale.

    ``cols`` restricts the feature set (used for the ablation that measures how
    much the anisotropic anatomy adds over distance alone).
    """
    rng = np.random.default_rng(seed)
    X, y, w = sample_train(rng, geoms)
    if cols is not None:
        X = X[:, cols]
    clf = HistGradientBoostingClassifier(**GBM_KW)
    clf.fit(X, y, sample_weight=w)
    # moment calibration on the (weighted) training sample: make the mean
    # predicted probability equal the observed base rate
    p_all = clf.predict_proba(X)[:, 1]
    base = float((y * w).sum() / w.sum())
    mean_p = float((p_all * w).sum() / w.sum())
    scale = base / max(mean_p, 1e-12)
    return clf, scale, base


def predict_surface(clf, scale: float, g, shape: tuple[int, int],
                    cols: list[int] | None = None) -> np.ndarray:
    """Per-cell probability of being a withheld/new fault pixel, on the full grid."""
    full = np.zeros(shape, np.float32)
    if g.X.shape[0]:
        Xin = g.X[:, cols] if cols is not None else g.X
        surf = clf.predict_proba(Xin)[:, 1].astype(np.float32) * np.float32(scale)
        np.clip(surf, 0.0, 1.0, out=surf)
        full[g.rows, g.cols] = surf
    return full


def canary(geoms: list) -> dict:
    """Single-feature AUC per fold (no fitting, so no fitting-induced leakage).

    A feature whose AUC exceeds 0.90 is treated as leakage until proven
    otherwise (parallel-run protocol rule 4).  The test is applied to the
    **discriminative** AUC ``max(auc, 1 - auc)``, because an AUC of 0.11 is just
    as informative as 0.89 -- it only means the feature is inversely ranked.
    Reporting the raw value alone would let a strongly predictive inverse
    feature pass a naive "> 0.90" screen.

    ``d`` is expected to be highly discriminative -- it is the physical signal
    the lane is built on -- but it must not be near-perfect, which would mean the
    withheld mask itself is recoverable from a feature.
    """
    out = {}
    names = tuple(getattr(geoms[0], "feature_names", FEATURES)) if geoms else FEATURES
    for j, name in enumerate(names):
        aucs = []
        for g in geoms:
            if (g.y == 1).sum() < 10 or (g.y == 0).sum() < 10:
                continue
            v = g.X[:, j]
            # subsample negatives so the AUC is computable quickly
            rng = np.random.default_rng(1)
            pos = np.flatnonzero(g.y == 1)
            neg = np.flatnonzero(g.y == 0)
            if neg.size > 200_000:
                neg = rng.choice(neg, 200_000, replace=False)
            idx = np.concatenate([pos, neg])
            aucs.append(roc_auc_score(g.y[idx], v[idx]))
        disc = [max(a, 1.0 - a) for a in aucs]
        out[name] = {"auc_per_fold": [float(a) for a in aucs],
                     "auc_mean": float(np.mean(aucs)) if aucs else None,
                     "auc_min": float(np.min(aucs)) if aucs else None,
                     "auc_max": float(np.max(aucs)) if aucs else None,
                     "discriminative_auc_mean": float(np.mean(disc)) if disc else None,
                     "discriminative_auc_max": float(np.max(disc)) if disc else None,
                     "leakage_threshold": 0.90,
                     "leakage_flag": bool(np.max(disc) > 0.90) if disc else False}
    return out


def run_cell(ctx: HoldoutContext, cell: Cell, clf, scale: float,
             *, max_dots: int = 120_000, floor: float = 0.015,
             cols: list[int] | None = None, g=None) -> dict:
    """Predict, allocate and score one fold cell."""
    own_g = g is None
    if own_g:
        g = cell_geometry(ctx, cell)
    p = predict_surface(clf, scale, g, ctx.grid.shape, cols)
    allowed = np.zeros(ctx.grid.shape, bool)
    allowed[cell.bbox] = cell.active
    alloc = greedy_allocate(p, allowed, k_truth=float(cell.n_truth),
                            floor=floor, max_dots=max_dots)
    emitted_full = alloc.emitted
    # score on the crop
    res = dti_binary(emitted_full[cell.bbox], _truth_crop(ctx, cell),
                     valid=cell.active)
    out = {
        "key": cell.key, "mode": cell.mode, "n_truth": cell.n_truth,
        "n_dots": alloc.n_dots, "dti": res["dti"], "coverage": res["coverage"],
        "tp": res["tp"], "fp": res["fp"], "fn": res["fn"],
        "expected_covered_credit": alloc.expected_covered_credit,
        "p_mean": float(p[allowed].mean()), "p_max": float(p.max()),
    }
    del p, allowed, alloc, emitted_full
    if own_g:
        del g
    return out


def _truth_crop(ctx: HoldoutContext, cell: Cell) -> np.ndarray:
    t = np.zeros(cell.active.shape, bool)
    t[cell.truth_yx] = True
    return t


def pooled(results: list[dict]) -> dict:
    tp = sum(r["tp"] for r in results)
    fp = sum(r["fp"] for r in results)
    fn = sum(r["fn"] for r in results)
    n = sum(r["n_truth"] for r in results)
    from .metric import dti_from_components
    dti = dti_from_components(tp, fp, fn)
    if n == 0:
        return {"pooled_dti": dti, "coverage": 0.0, "coverage_ci95": [0.0, 0.0],
                "dti_ci95_coverage_only": [0.0, 0.0],
                "dti_ci95_quadrant_jackknife": [0.0, 0.0],
                "jackknife_drop_quadrant": {}, "tp": tp, "fp": fp, "fn": fn,
                "n_truth": 0, "n_dots": sum(r["n_dots"] for r in results)}
    # Wilson interval on the pooled coverage, then propagated through the DTI
    cov = tp / max(n, 1)
    z = 1.959963985
    denom = 1 + z * z / n
    centre = (cov + z * z / (2 * n)) / denom
    half = z * np.sqrt(cov * (1 - cov) / n + z * z / (4 * n * n)) / denom
    lo, hi = max(0.0, centre - half), min(1.0, centre + half)
    # hold fp and n fixed and propagate the coverage interval into DTI
    d_lo = dti_from_components(lo * n, fp, n - lo * n)
    d_hi = dti_from_components(hi * n, fp, n - hi * n)

    # quadrant jackknife: drop each spatial quadrant in turn.  This is the CI that
    # respects the spatial blocking; the Wilson interval above only propagates
    # binomial noise on the coverage and ignores spatial heterogeneity.
    quads = sorted({r["key"].split("_")[1] for r in results})
    jk = []
    for q in quads:
        rs = [r for r in results if r["key"].split("_")[1] != q]
        jk.append(dti_from_components(sum(r["tp"] for r in rs), sum(r["fp"] for r in rs),
                                      sum(r["fn"] for r in rs)))
    jk = np.array(jk)
    m = len(quads)
    jk_se = float(np.sqrt((m - 1) / m * ((jk - jk.mean()) ** 2).sum())) if m > 1 else 0.0
    return {"pooled_dti": dti, "coverage": cov, "coverage_ci95": [lo, hi],
            "dti_ci95_coverage_only": [d_lo, d_hi],
            "dti_ci95_quadrant_jackknife": [float(dti - 1.959963985 * jk_se),
                                            float(dti + 1.959963985 * jk_se)],
            "jackknife_drop_quadrant": {q: float(v) for q, v in zip(quads, jk)},
            "tp": tp, "fp": fp, "fn": fn, "n_truth": n,
            "n_dots": sum(r["n_dots"] for r in results)}
