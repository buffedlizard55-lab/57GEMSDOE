"""Regression tests for the shared spatial holdout evaluator."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems57 import evaluate_holdout, metric


def test_max_cover_and_shared_evaluator_match_canonical_dti():
    rng = np.random.default_rng(57)
    pred = rng.uniform(0.0, 0.9, size=(19, 23)).astype(np.float32)
    truth = np.zeros(pred.shape, dtype=bool)
    truth[[3, 8, 12, 16], [4, 17, 9, 20]] = True

    credit, q, distance_to_truth = metric.max_cover(pred, truth)
    canonical = metric.dti_exact(pred, truth)
    assert credit.size == int(truth.sum())
    assert q.shape == pred.shape
    assert distance_to_truth.shape == pred.shape
    np.testing.assert_allclose(credit.sum(), canonical["tp"], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(
        (pred * (1.0 - q)).sum(), canonical["fp"], rtol=1e-6, atol=1e-6)

    valid = np.ones(pred.shape, dtype=bool)
    valid[:2, :] = False
    region = np.zeros(pred.shape, dtype=bool)
    region[2:18, 1:22] = True
    visible = np.zeros(pred.shape, dtype=bool)
    visible[6:8, 7:12] = True
    fold_truth = truth.copy()
    fold_truth[6, 8] = True  # visible truth is masked from the score
    fold = {"truth": fold_truth, "visible": visible, "region": region}

    result, terms = evaluate_holdout.evaluate(pred, fold, valid, block_side=5)
    active = valid & region & ~visible
    expected = metric.dti_exact(pred, fold_truth, valid=active)
    np.testing.assert_allclose(result["dti"], expected["dti"], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(result["tpw"], expected["tp"], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(result["fpw"], expected["fp"], rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(result["fnw"], expected["fn"], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(terms.sum(axis=0),
                               [result["tpw"], result["fpw"], result["fnw"],
                                result["n_truth"]], rtol=1e-12, atol=1e-6)
    assert result["evidence_class"] == "HOLDOUT-DTI"
    assert result["evaluator_version"] == evaluate_holdout.VERSION


def test_cropped_fold_block_terms_align_to_global_grid():
    shape = (20, 20)
    pred = np.zeros(shape, dtype=np.float32)
    truth = np.zeros(shape, dtype=bool)
    pred[2, 3] = 1.0
    pred[16, 17] = 1.0
    truth[2, 2] = True
    truth[17, 17] = True
    valid = np.ones(shape, dtype=bool)

    def fold_for(t):
        return {"truth": t, "visible": np.zeros_like(t),
                "region": np.ones_like(t)}

    full, full_terms = evaluate_holdout.evaluate(
        pred, fold_for(truth), valid, block_side=5)
    pieces = np.zeros_like(full_terms)
    for y0, x0, y1, x1 in ((0, 0, 10, 10), (10, 10, 20, 20)):
        crop = (slice(y0, y1), slice(x0, x1))
        _, terms = evaluate_holdout.evaluate(
            pred[crop], fold_for(truth[crop]), valid[crop], block_side=5,
            origin=(y0, x0), global_shape=shape)
        pieces += terms
    np.testing.assert_allclose(pieces, full_terms, rtol=1e-12, atol=1e-7)


def test_shared_evaluator_rejects_invalid_prediction_before_masking():
    pred = np.zeros((4, 5), dtype=np.float32)
    pred[0, 0] = np.nan
    truth = np.zeros_like(pred, dtype=bool)
    truth[2, 2] = True
    fold = {"truth": truth, "visible": np.zeros_like(truth),
            "region": np.ones_like(truth)}
    try:
        evaluate_holdout.evaluate(pred, fold, np.ones_like(truth), block_side=2)
    except ValueError as exc:
        assert "finite" in str(exc)
    else:
        raise AssertionError("non-finite predictions must be rejected before masking")
