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

from itertools import chain

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from .anatomy import FEATURES, fold_geometry
from .emit import greedy_allocate
from .holdout import BUFFER_PX, Cell, HoldoutContext
from . import evaluate_holdout

NEG_PER_CELL = 60_000
GBM_KW = dict(max_depth=6, max_iter=220, learning_rate=0.08,
              min_samples_leaf=60, l2_regularization=1.0,
              early_stopping=False, random_state=0)


def _full(ctx: HoldoutContext, cell: Cell, *, training: bool = False) -> np.ndarray:
    mask = cell.train_active if training else cell.active
    full = np.zeros(ctx.grid.shape, bool)
    full[cell.bbox] = mask
    return full


def cell_geometry(ctx: HoldoutContext, cell: Cell, sense_src=None, *,
                  training: bool = False, include_tip: bool = False,
                  feature_exclude: tuple[str, ...] = ()):
    """Build one fold's visible-only features.

    ``training`` applies the 3 px negative-label collar.  ``feature_exclude``
    names the outer test-fold cells whose hidden branches must also be removed
    from this training cell's feature source (and from the tip buffer).
    """
    domain = _full(ctx, cell, training=training)
    feature_visible = ctx.visible(cell.key)
    tip_source = ctx.visible_exact(cell.key)
    tip_exclusion = ctx.hidden_by_cell[cell.key].copy()
    for key in feature_exclude:
        excluded = ctx.hidden_by_cell[key]
        feature_visible = feature_visible & ~excluded & (ndi.distance_transform_edt(~excluded) > BUFFER_PX)
        tip_source = tip_source & ~excluded
        tip_exclusion |= excluded
    return fold_geometry(ctx.grid, feature_visible, ctx.hidden_by_cell[cell.key],
                         domain, cell.key, sense_src=sense_src,
                         include_tip=include_tip, tip_source=tip_source,
                         tip_exclusion=tip_exclusion, tip_buffer_px=BUFFER_PX)


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


def fit_model_from_cells(ctx: HoldoutContext, cells: list[Cell], seed: int = 0,
                         cols: list[int] | None = None, *,
                         include_tip: bool = False,
                         feature_excludes: dict[str, tuple[str, ...]] | None = None,
                         sense_src=None, neg_per_cell: int = NEG_PER_CELL):
    """Fit from context cells while releasing each full feature matrix immediately."""
    rng = np.random.default_rng(seed)
    Xs, ys, ws = [], [], []
    exclusions = feature_excludes or {}
    for cell in cells:
        g = cell_geometry(ctx, cell, sense_src=sense_src, training=True,
                          include_tip=include_tip,
                          feature_exclude=exclusions.get(cell.key, ()))
        pos = g.y == 1
        if not pos.any():
            raise ValueError(f"training cell {cell.key} has no withheld positive pixels")
        Xs.append(g.X[pos]); ys.append(np.ones(int(pos.sum()), np.int8))
        ws.append(np.ones(int(pos.sum()), np.float64))
        neg = np.flatnonzero(~pos)
        if neg.size > neg_per_cell:
            neg = rng.choice(neg, size=neg_per_cell, replace=False)
        Xs.append(g.X[neg]); ys.append(np.zeros(neg.size, np.int8))
        weight = float((~pos).sum()) / max(neg.size, 1)
        ws.append(np.full(neg.size, weight, np.float64))
        del g
    X, y, w = np.vstack(Xs), np.concatenate(ys), np.concatenate(ws)
    if cols is not None:
        X = X[:, cols]
    clf = HistGradientBoostingClassifier(**GBM_KW)
    clf.fit(X, y, sample_weight=w)
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


def canary(geoms) -> dict:
    """Stream single-feature AUCs; discriminative AUC >0.90 is a leakage flag."""
    iterator = iter(geoms)
    first = next(iterator, None)
    if first is None:
        return {}
    names = tuple(first.feature_names or FEATURES)
    aucs = {name: [] for name in names}
    for g in chain((first,), iterator):
        if g.X.shape[1] != len(names) or tuple(g.feature_names or FEATURES) != names:
            raise ValueError("feature matrix widths/names do not match across folds")
        for j, name in enumerate(names):
            if (g.y == 1).sum() < 10 or (g.y == 0).sum() < 10:
                continue
            pos = np.flatnonzero(g.y == 1)
            neg = np.flatnonzero(g.y == 0)
            if neg.size > 200_000:
                neg = np.random.default_rng(1).choice(neg, 200_000, replace=False)
            idx = np.concatenate([pos, neg])
            aucs[name].append(float(roc_auc_score(g.y[idx], g.X[idx, j])))
    out = {}
    for name, values in aucs.items():
        disc = [max(a, 1.0 - a) for a in values]
        out[name] = {"auc_per_fold": values,
                     "auc_mean": float(np.mean(values)) if values else None,
                     "auc_min": float(np.min(values)) if values else None,
                     "auc_max": float(np.max(values)) if values else None,
                     "discriminative_auc_mean": float(np.mean(disc)) if disc else None,
                     "discriminative_auc_max": float(max(disc)) if disc else None,
                     "leakage_threshold": 0.90,
                     "leakage_flag": bool(max(disc) > 0.90) if disc else False}
    return out


def predict_surface_crop(clf, scale: float, g, cell: Cell,
                         cols: list[int] | None = None) -> np.ndarray:
    """Predict only the padded fold crop, avoiding a full-grid surface allocation."""
    p = np.zeros(cell.active.shape, np.float32)
    if g.X.shape[0]:
        Xin = g.X[:, cols] if cols is not None else g.X
        values = clf.predict_proba(Xin)[:, 1].astype(np.float32) * np.float32(scale)
        np.clip(values, 0.0, 1.0, out=values)
        y = g.rows - int(cell.bbox[0].start)
        x = g.cols - int(cell.bbox[1].start)
        p[y, x] = values
    return p


def run_cell(ctx: HoldoutContext, cell: Cell, clf, scale: float,
             *, max_dots: int = 120_000, floor: float = 0.015,
             cols: list[int] | None = None, g=None,
             include_tip: bool = False) -> dict:
    """Predict, allocate and score one fold cell with the shared evaluator."""
    own_g = g is None
    if own_g:
        g = cell_geometry(ctx, cell, include_tip=include_tip)
    p = predict_surface_crop(clf, scale, g, cell, cols)
    alloc = greedy_allocate(p, cell.active, k_truth=float(cell.n_truth),
                            floor=floor, max_dots=max_dots)
    fold = {"region": cell.region, "visible": cell.visible,
            "truth": _truth_crop(ctx, cell)}
    result, terms = evaluate_holdout.evaluate(
        alloc.emitted, fold, cell.region,
        origin=(int(cell.bbox[0].start), int(cell.bbox[1].start)),
        global_shape=ctx.grid.shape, block_side=200)
    out = {
        "key": cell.key, "mode": cell.mode, "n_truth": cell.n_truth,
        "evidence_class": result["evidence_class"],
        "evaluator_version": result["evaluator_version"],
        "withheld_positive_count": result["withheld_positive_count"],
        "n_dots": alloc.n_dots, "dti": result["dti"],
        "coverage": result["coverage"], "tp": result["tp"],
        "fp": result["fp"], "fn": result["fn"],
        "expected_covered_credit": alloc.expected_covered_credit,
        "p_mean": float(p[cell.active].mean()) if cell.active.any() else 0.0,
        "p_max": float(p.max()),
        "spatial_terms": terms,
    }
    del p, alloc, fold, result, terms
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
