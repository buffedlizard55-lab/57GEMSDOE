"""Shared pooled hide-and-recover evaluator.

All local scores in this module are labelled HOLDOUT-DTI.  The metric arithmetic
is delegated to ``gems57.metric``; spatial blocks only provide paired uncertainty
estimates conditional on the catalogue and fitted fold predictions.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from . import metric

VERSION = "gems57-buffered-whole-branch-pooled-v2.0"


def implementation_hashes() -> dict[str, str]:
    """File hashes needed to identify the exact local evaluator implementation."""
    names = ("evaluate_holdout.py", "holdout.py", "metric.py", "spatial.py", "network.py")
    base = Path(__file__).parent
    return {name: hashlib.sha256((base / name).read_bytes()).hexdigest()
            for name in names}


def evaluate(prediction, fold, valid, block_side=200, *, origin=(0, 0),
             global_shape=None):
    """Exact fold DTI plus additive (TPw, FPw, FNw, withheld count) per spatial block.

    ``fold`` must provide pixel-exact ``visible`` and ``truth`` masks, plus the
    scored ``region``. Visible pixels are masked from scoring even if the truth
    input includes them. ``valid`` may further restrict that region. ``origin``
    maps a cropped fold to global grid coordinates; this makes equal 20 km cells
    from different folds/draws merge before bootstrap resampling.
    """
    p = np.asarray(prediction)
    if p.ndim != 2:
        raise ValueError("prediction must be a 2D array")
    required = ("region", "visible", "truth")
    if any(name not in fold for name in required):
        raise ValueError("fold must include region, visible and truth masks")
    region = np.asarray(fold["region"], bool)
    visible = np.asarray(fold["visible"], bool)
    truth = np.asarray(fold["truth"], bool)
    valid_ = np.asarray(valid, bool)
    if any(a.shape != p.shape for a in (region, visible, truth, valid_)):
        raise ValueError("prediction, fold masks and valid grid shape mismatch")
    scored_region = region & valid_
    result, terms = metric.dti_spatial_terms(
        p, truth, valid=scored_region, known=visible, origin=origin,
        global_shape=global_shape, block_side=block_side)
    if result["n_truth"] <= 0:
        raise ValueError("a holdout fold must contain positives among its withheld positive pixels")
    result.update(
        tpw=result["tp"], fpw=result["fp"], fnw=result["fn"],
        emitted=result["n_emitted"],
        evidence_class="HOLDOUT-DTI",
        evaluator_version=VERSION,
        withheld_positive_count=int(result["n_truth"]),
        pooled=False,
        alpha=metric.ALPHA,
        beta=metric.BETA,
        triangular_radius_m=metric.RADIUS_M,
        spatial_block_side_px=int(block_side),
        spatial_block_size_m=int(block_side) * metric.PIXEL_M,
    )
    return result, terms


def from_terms(terms):
    """Vectorized DTI of one or more rows of additive metric terms."""
    a = np.asarray(terms, dtype=np.float64)
    if a.shape[-1] != 4:
        raise ValueError("metric terms must end with TPw, FPw, FNw, withheld count")
    return metric.dti_from_components(a[..., 0], a[..., 1], a[..., 2])


def pooled_summary(terms_by_arm, draws=2000, seed=520810,
                   candidate="h57b_tip_distance"):
    """Pool terms first, then paired-bootstrap physical spatial clusters.

    Input arrays share the fixed global block order returned by ``evaluate``.
    Contributions from the same physical block across folds/draws are already
    merged by summing rows before this function is called.  Intervals are
    conditional on fitted folds, fixed emission budgets and catalogue labels;
    they are not leaderboard intervals.
    """
    names = list(terms_by_arm)
    if not names or candidate not in terms_by_arm:
        raise ValueError("candidate arm and at least one comparator are required")
    if int(draws) < 100:
        raise ValueError("at least 100 spatial bootstrap draws are required")
    arrays = {name: np.asarray(value, dtype=np.float64)
              for name, value in terms_by_arm.items()}
    shape = next(iter(arrays.values())).shape
    if len(shape) != 2 or shape[1] != 4 or any(a.shape != shape for a in arrays.values()):
        raise ValueError("all arms need aligned per-spatial-block arrays of four terms")
    if any(not np.isfinite(a).all() or (a < -1e-8).any() for a in arrays.values()):
        raise ValueError("metric terms must be finite and non-negative")
    truth_counts = [a[:, 3] for a in arrays.values()]
    reference_counts = truth_counts[0]
    if not np.allclose(reference_counts, np.rint(reference_counts), rtol=0.0, atol=1e-8):
        raise ValueError("spatial-block truth counts must be integers")
    if any(not np.array_equal(counts, reference_counts) for counts in truth_counts[1:]):
        raise ValueError("all candidate/control arms must use the same integer truth count per spatial block")
    active = np.any(np.stack([a.sum(axis=1) > 0 for a in arrays.values()]), axis=0)
    arrays = {name: a[active] for name, a in arrays.items()}
    n_clusters = int(active.sum())
    if n_clusters < 2:
        raise ValueError("need at least two non-empty spatial blocks")

    totals = {name: a.sum(axis=0) for name, a in arrays.items()}
    rng = np.random.default_rng(seed)
    picks = rng.integers(0, n_clusters, size=(int(draws), n_clusters))
    boot = {name: from_terms(a[picks].sum(axis=1))
            for name, a in arrays.items()}

    scores = {}
    for name, total in totals.items():
        scores[name] = dict(
            evidence_class="HOLDOUT-DTI",
            evaluator_version=VERSION,
            pooled=True,
            dti=float(from_terms(total)),
            ci95=[float(x) for x in np.quantile(boot[name], [0.025, 0.975])],
            withheld_positive_count=int(round(total[3])),
            withheld_positive_pixels=int(round(total[3])),
            tpw=float(total[0]), fpw=float(total[1]), fnw=float(total[2]),
        )

    controls = [name for name in names if name != candidate]
    best_control = max(controls, key=lambda n: scores[n]["dti"]) if controls else None
    paired = {}
    for name in controls:
        delta = boot[candidate] - boot[name]
        paired[name] = dict(
            evidence_class="HOLDOUT-DTI",
            evaluator_version=VERSION,
            delta=float(scores[candidate]["dti"] - scores[name]["dti"]),
            ci95=[float(x) for x in np.quantile(delta, [0.025, 0.975])],
            withheld_positive_count=scores[candidate]["withheld_positive_count"],
        )
    return dict(
        evidence_class="HOLDOUT-DTI",
        evaluator_version=VERSION,
        alpha=metric.ALPHA,
        beta=metric.BETA,
        triangular_radius_m=metric.RADIUS_M,
        scores=scores,
        best_comparable_control=best_control,
        paired_differences=paired,
        bootstrap=dict(method="paired physical spatial-block percentile",
                       block_side_px=200, block_size_m=20_000,
                       clusters=n_clusters, draws=int(draws), seed=int(seed),
                       confidence=0.95,
                       caveat="Conditional on fitted folds, fixed dot caps and visible catalogue labels; not a leaderboard interval."),
        implementation_sha256=implementation_hashes(),
    )
