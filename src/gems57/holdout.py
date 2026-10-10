"""Buffered, spatially blocked hide-and-recover holdout for fault anatomy.

Primary instrument
------------------
* Hold out **whole between-junction branches**, not artificial 12-pixel chunks.
* Use four footprint quadrants with a 12-pixel erosion so train and test cells
  are physically separated from their shared boundary.
* Hide the selected branch from every catalogue-derived feature.  A 3-pixel
  Euclidean collar around withheld branches is also removed from feature inputs
  and from training negatives; the test scoring domain itself is *not* dilated
  or eroded by this collar.
* Mask remaining visible-catalogue pixels pixel-exactly in scoring.  Non-fault
  pixels close to withheld truth remain scoreable, so nearby predictions are
  still penalized by the 300 m triangular DTI kernel.
* DTI uses alpha=0.2, beta=0.8 and the shared metric implementation.

The outer leave-one-quadrant-out evaluator additionally removes the test fold's
hidden branches (and their collar) from all training-cell feature sources.  This
prevents a test target from surviving as a visible feature in a different cell.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from .grid import Grid
from .metric import dti_binary
from .network import STRUCT3, component_detached, segments

FOLD_NAMES = ("NW", "NE", "SW", "SE")
DOMAIN_ERODE = 12     # 1.2 km boundary erosion
BUFFER_PX = 3         # 300 m Euclidean collar around withheld whole branches
DETACH_PX = 4         # conservative detached-component subset
HIDE_FRAC = 0.20


@dataclass
class Cell:
    """One fold cell; all stored masks are cropped to ``bbox``."""
    key: str
    fold: int
    seed: int
    mode: str
    bbox: tuple[slice, slice]
    region: np.ndarray              # scored footprint domain, before exact known-fault mask
    visible: np.ndarray             # exact visible catalogue mask within region/crop
    active: np.ndarray              # region minus exactly visible catalogue pixels
    train_active: np.ndarray        # active minus the 3 px negative-label collar
    truth_yx: tuple[np.ndarray, np.ndarray]  # withheld truth indices within bbox
    n_truth: int


@dataclass
class HoldoutContext:
    grid: Grid
    quad: np.ndarray
    cells: list[Cell]
    hidden_by_cell: dict[str, np.ndarray]             # key -> full-grid hidden branch mask
    feature_visible_by_cell: dict[str, np.ndarray]   # key -> full-grid, buffered visible mask

    def visible(self, key: str) -> np.ndarray:
        """Buffered feature-source mask, excluding the hidden branch's 3 px collar."""
        return self.feature_visible_by_cell[key]

    def visible_exact(self, key: str) -> np.ndarray:
        """Exact catalogue visibility before the feature collar is applied."""
        return self.grid.catalogue & ~self.hidden_by_cell[key]

    def cell(self, key: str) -> Cell:
        for c in self.cells:
            if c.key == key:
                return c
        raise KeyError(key)

    def cells_of(self, mode: str) -> list[Cell]:
        return [c for c in self.cells if c.mode == mode]


def quadrant_ids(footprint: np.ndarray) -> np.ndarray:
    fp = np.asarray(footprint, bool)
    yy, xx = np.nonzero(fp)
    if not yy.size:
        raise ValueError("footprint is empty")
    ym, xm = int(np.median(yy)), int(np.median(xx))
    gy, gx = np.ogrid[: fp.shape[0], : fp.shape[1]]
    q = np.full(fp.shape, -1, np.int8)
    q[(gy < ym) & (gx < xm) & fp] = 0
    q[(gy < ym) & (gx >= xm) & fp] = 1
    q[(gy >= ym) & (gx < xm) & fp] = 2
    q[(gy >= ym) & (gx >= xm) & fp] = 3
    return q


def _pick_segments(rng, sizes: np.ndarray, ids: np.ndarray, target_px: float) -> np.ndarray:
    """Random whole branches until their cumulative size reaches ``target_px``."""
    if ids.size == 0:
        return ids
    perm = rng.permutation(ids)
    cum = np.cumsum(sizes[perm])
    k = int(np.searchsorted(cum, target_px)) + 1
    return perm[: min(k, perm.size)]


def _crop_bbox(q: np.ndarray, shape: tuple[int, int], pad: int = 6):
    rows = np.flatnonzero(q.any(axis=1))
    cols = np.flatnonzero(q.any(axis=0))
    if not rows.size or not cols.size:
        return None
    return (slice(max(0, int(rows[0]) - pad), min(shape[0], int(rows[-1]) + pad + 1)),
            slice(max(0, int(cols[0]) - pad), min(shape[1], int(cols[-1]) + pad + 1)))


def build_holdout(grid: Grid, hide_frac: float = HIDE_FRAC,
                  seeds: tuple[int, ...] = (20, 21),
                  modes: tuple[str, ...] = ("all", "detached"),
                  detach_px: int = DETACH_PX) -> HoldoutContext:
    """Build reusable whole-branch fold cells.

    ``all`` withholds eligible branches from every connected component.
    ``detached`` restricts the selection to components at least ``detach_px``
    from every other mapped component; it is a conservative sensitivity mode,
    not the primary holdout.
    """
    if not 0.0 < hide_frac <= 1.0:
        raise ValueError("hide_frac must be in (0, 1]")
    if not modes or any(m not in ("all", "detached") for m in modes):
        raise ValueError("modes must contain 'all' and/or 'detached'")
    cat = np.asarray(grid.catalogue, bool)
    footprint = np.asarray(grid.footprint, bool)
    if cat.shape != footprint.shape or cat.shape != grid.shape:
        raise ValueError("Grid catalogue/footprint shapes do not match grid.shape")

    quad = quadrant_ids(footprint)
    # None disables artificial chunking: each segment is one complete branch
    # between junction pixels, as required by the holdout protocol.
    seg, n_seg, _branch = segments(cat, max_len_px=None)
    del _branch
    sizes = np.bincount(seg.ravel(), minlength=n_seg + 1)
    all_ids = np.arange(1, n_seg + 1)

    detached_ids = None
    if "detached" in modes:
        comp, is_det = component_detached(cat, detach_px)
        detached_ids = np.isin(all_ids, np.unique(seg[comp[is_det[comp]]]))
        del comp, is_det

    hidden_by_cell: dict[str, np.ndarray] = {}
    feature_visible_by_cell: dict[str, np.ndarray] = {}
    cells: list[Cell] = []

    for seed in seeds:
        for fold, qname in enumerate(FOLD_NAMES):
            q = quad == fold
            bbox = _crop_bbox(q, grid.shape)
            if bbox is None:
                continue
            # Erosion keeps the scored quadrant away from the fold boundary;
            # a 6 px crop pad is enough for the 3 px metric and feature collar.
            domain = ndi.binary_erosion(q, structure=STRUCT3,
                                        iterations=DOMAIN_ERODE) & footprint
            clipped = np.isin(all_ids, np.unique(seg[~domain & cat]))
            eligible_base = all_ids[~clipped]
            target = hide_frac * float((cat & q & domain).sum())

            for mode in modes:
                pool = eligible_base if mode == "all" else eligible_base[detached_ids[eligible_base]]
                rng = np.random.default_rng(10_000 * (seed + 1) + 7 * fold
                                            + (0 if mode == "all" else 1))
                hidden_ids = _pick_segments(rng, sizes, pool, target)
                hidden = np.isin(seg, hidden_ids) & footprint
                # The Euclidean collar is used for *inputs* and training negatives,
                # never as a substitute for the evaluator's exact known-pixel mask.
                d_hidden = ndi.distance_transform_edt(~hidden)
                near_hidden = d_hidden <= BUFFER_PX
                visible_exact = cat & ~hidden
                feature_visible = visible_exact & ~near_hidden
                halo_negative = near_hidden & ~hidden

                key = f"draw{seed}_fold{qname}_{mode}"
                hidden_by_cell[key] = hidden
                feature_visible_by_cell[key] = feature_visible

                region_full = domain
                active_full = region_full & ~visible_exact
                train_active_full = active_full & ~halo_negative
                truth_full = hidden & region_full & active_full

                sl = bbox
                region_crop = region_full[sl].copy()
                visible_crop = visible_exact[sl].copy()
                active_crop = active_full[sl].copy()
                train_active_crop = train_active_full[sl].copy()
                truth_crop = truth_full[sl]
                truth_yx = np.nonzero(truth_crop)
                cells.append(Cell(key=key, fold=fold, seed=seed, mode=mode, bbox=sl,
                                  region=region_crop, visible=visible_crop,
                                  active=active_crop, train_active=train_active_crop,
                                  truth_yx=truth_yx, n_truth=int(truth_yx[0].size)))
                del hidden, d_hidden, near_hidden, visible_exact, feature_visible
                del halo_negative, region_full, active_full, train_active_full, truth_full
                del region_crop, visible_crop, active_crop, train_active_crop, truth_crop

    return HoldoutContext(grid=grid, quad=quad, cells=cells,
                          hidden_by_cell=hidden_by_cell,
                          feature_visible_by_cell=feature_visible_by_cell)


def score_cell(cell: Cell, emitted: np.ndarray) -> dict:
    """Exact DTI for one cell through the shared metric implementation.

    ``emitted`` may be the full grid or a crop matching ``cell.active``. The
    scoring region is the unexpanded evaluation domain; visible mapped-fault
    pixels are masked pixel-exactly and the feature collar is not applied here.
    """
    values = np.asarray(emitted, bool)
    if values.shape == cell.active.shape:
        prediction = values
    elif values.ndim == 2 and values.shape[0] >= cell.bbox[0].stop and values.shape[1] >= cell.bbox[1].stop:
        prediction = values[cell.bbox]
    else:
        raise ValueError("emitted predictions must match the cell crop or full grid")
    truth = np.zeros(cell.active.shape, bool)
    truth[cell.truth_yx] = True
    return dti_binary(prediction, truth, valid=cell.region, known=cell.visible)


def evaluate(emitted: np.ndarray, ctx: HoldoutContext, cell_mode: str = "") -> dict:
    """Per-fold and pooled DTI for one binary full-grid emission mask."""
    emitted = np.asarray(emitted, bool) & ctx.grid.footprint
    per_fold = {}
    tp = fp = fn = n_truth = n_emit = 0.0
    for cell in ctx.cells:
        if cell_mode and cell.mode != cell_mode:
            continue
        r = score_cell(cell, emitted)
        per_fold[cell.key] = r
        tp += r["tp"]; fp += r["fp"]; fn += r["fn"]
        n_truth += r["n_truth"]; n_emit += r["n_emitted"]
    from .metric import dti_from_components
    pooled = dti_from_components(tp, fp, fn)
    by_draw: dict[str, list[float]] = {}
    by_quad: dict[str, list[float]] = {}
    for key, result in per_fold.items():
        draw, fold_name, _mode = key.split("_")
        by_draw.setdefault(draw, []).append(result["dti"])
        by_quad.setdefault(fold_name, []).append(result["dti"])
    fold_scores = [r["dti"] for r in per_fold.values()]
    return {
        "emitted_pixels": int(emitted.sum()),
        "on_visible_catalogue": int((emitted & ctx.grid.catalogue).sum()),
        "pooled_dti": pooled,
        "pooled_coverage": float(tp / n_truth) if n_truth else 0.0,
        "pooled_tp": tp, "pooled_fp": fp, "pooled_fn": fn,
        "pooled_n_truth": int(n_truth), "n_emitted": int(n_emit),
        "mean_fold_dti": float(np.mean(fold_scores)) if fold_scores else 0.0,
        "std_fold_dti": float(np.std(fold_scores)) if fold_scores else 0.0,
        "per_fold_dti": {k: r["dti"] for k, r in per_fold.items()},
        "per_draw_dti": {k: float(np.mean(v)) for k, v in sorted(by_draw.items())},
        "per_quadrant_dti": {k: float(np.mean(v)) for k, v in sorted(by_quad.items())},
        "folds": per_fold,
    }


def wilson_ci(k_success_mass: float, n_mass: float,
              z: float = 1.959963985) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (coverage only)."""
    if n_mass <= 0:
        return (0.0, 0.0)
    p = k_success_mass / n_mass
    denom = 1.0 + z * z / n_mass
    centre = (p + z * z / (2 * n_mass)) / denom
    half = z * np.sqrt(p * (1 - p) / n_mass + z * z / (4 * n_mass * n_mass)) / denom
    return (float(max(0.0, centre - half)), float(min(1.0, centre + half)))


def score(prediction, fold, valid, restrict_to_region=True, extra=False):
    """Compatibility adapter for the shared template's dictionary-fold callers.

    v2 fixes the missing adapter; official arithmetic remains in metric.py.
    """
    from .metric import dti_exact
    region = fold['region'] if restrict_to_region else np.ones_like(valid, bool)
    known = fold.get('masked_known', fold['visible'])
    r = dti_exact(prediction, fold['truth'], valid=np.asarray(valid, bool) & region, known=known)
    return {**r, 'tpw': r['tp'], 'fpw': r['fp'], 'fnw': r['fn']}


def buffered_component_draw(grid, seed=20, hide_frac=0.20, buffer_px=3,
                            boundary_px=DOMAIN_ERODE):
    """A repaired label-blind quadrant draw with REAL catalogue context buffering.

    Whole original 8-connected components are withheld (no <=12-pixel chunks).
    Only components wholly inside a label-blind eroded quadrant are eligible.
    The same globally hidden draw supplies every outer LOQO model, so a tested
    component cannot reappear in a training quadrant's catalogue features.
    Buffer-removal is for FEATURE context, not a truth-shaped evaluation halo.
    Other catalogue pixels in that context collar remain pixel-exactly masked
    from scoring; they are not invented negatives or silently clipped truth.
    """
    if not 0 < hide_frac < 1 or buffer_px < 0 or boundary_px < buffer_px:
        raise ValueError('invalid holdout fraction/buffer')
    cat = np.asarray(grid.catalogue, bool)
    quad = quadrant_ids(grid.footprint)
    comp, count = ndi.label(cat, STRUCT3)
    sizes = np.bincount(comp.ravel(), minlength=count+1)
    hidden = np.zeros(cat.shape, bool)
    regions, receipts = [], []
    for q, name in enumerate(FOLD_NAMES):
        region = ndi.binary_erosion(quad == q, iterations=boundary_px) if boundary_px else quad == q
        region &= grid.footprint
        candidate = np.unique(comp[cat & region])
        clipped = np.unique(comp[cat & ~region])
        eligible = np.setdiff1d(candidate[candidate > 0], clipped, assume_unique=True)
        rng = np.random.default_rng(seed * 10_000 + q)
        chosen = _pick_segments(rng, sizes, eligible, hide_frac * float((cat & region).sum()))
        withheld = np.isin(comp, chosen) & cat
        if (withheld & ~region).any():
            raise AssertionError('a withheld component was clipped')
        hidden |= withheld
        regions.append(region)
        receipts.append(dict(fold=name, seed=seed, held_components=int(len(chosen)),
            withheld_positive_pixels=int(withheld.sum()), eligible_components=int(len(eligible)),
            boundary_buffer_px=boundary_px, feature_buffer_px=buffer_px))
    if not hidden.any():
        raise ValueError('no eligible withheld components')
    collar = ndi.distance_transform_edt(~hidden) <= buffer_px
    visible = cat & ~collar
    masked_known = cat & ~hidden
    if not visible.any():
        raise ValueError('no visible catalogue context')
    if (visible & hidden).any() or np.any(visible & collar):
        raise AssertionError('withheld truth/context buffer reached a feature')
    minimum = float(ndi.distance_transform_edt(~visible)[hidden].min())
    if minimum <= buffer_px:
        raise AssertionError('context buffer was not honored')
    folds = [dict(fold=i, name=FOLD_NAMES[i], region=regions[i], truth=hidden & regions[i],
                  visible=visible, masked_known=masked_known, hidden_all=hidden,
                  receipt={**receipts[i], 'nearest_visible_to_truth_px': minimum,
                           'split_version': 'buffered-whole-components-loqo-v2',
                           'evaluation_region_label_blind': True}) for i in range(4)]
    return folds, quad
