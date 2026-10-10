"""Regression tests for the shared pooled hide-and-recover evaluator."""
import numpy as np
import pytest

from gems57 import evaluate_holdout as evaluator
from gems57 import metric


def _example():
    valid = np.ones((9, 11), dtype=bool)
    region = valid.copy()
    visible = np.zeros_like(valid)
    visible[2, 2] = True
    truth = np.zeros_like(valid)
    truth[3, 3] = True
    truth[5, 7] = True
    prediction = np.zeros(valid.shape, dtype=np.float32)
    prediction[3, 3] = 0.8
    prediction[4, 3] = 0.6
    prediction[5, 6] = 0.4
    prediction[2, 2] = 1.0  # must be removed pixel-exactly as visible catalogue mass
    prediction[8, 10] = 0.2
    fold = {"region": region, "visible": visible, "truth": truth}
    return prediction, fold, valid


def test_evaluate_matches_shared_exact_metric_and_block_totals():
    prediction, fold, valid = _example()
    prediction = prediction.astype(np.float64)
    prediction[3, 3] = np.nextafter(0.8, 1.0)
    result, terms = evaluator.evaluate(prediction, fold, valid, block_side=4)

    expected = metric.dti_exact(prediction, fold["truth"], valid=valid, known=fold["visible"])
    assert result["dti"] == pytest.approx(expected["dti"])
    assert result["tpw"] == pytest.approx(expected["tp"])
    assert result["fpw"] == pytest.approx(expected["fp"])
    assert result["fnw"] == pytest.approx(expected["fn"])
    assert result["n_truth"] == 2
    assert result["emitted"] == 4  # the visible-catalogue pixel is excluded
    assert result["evidence_class"] == "HOLDOUT-DTI"
    assert result["evaluator_version"] == evaluator.VERSION
    assert terms.shape == (3 * 3, 4)
    np.testing.assert_allclose(terms.sum(axis=0),
                               [result["tpw"], result["fpw"], result["fnw"], 2.0],
                               atol=1e-7, rtol=1e-11)


def test_evaluate_rejects_invalid_prediction_even_outside_score_region():
    prediction, fold, valid = _example()
    fold["region"][:] = False
    prediction[0, 0] = np.nan
    with pytest.raises(ValueError, match=r"finite in \[0,1\]"):
        evaluator.evaluate(prediction, fold, valid)


def test_evaluate_rejects_truth_visible_overlap():
    prediction, fold, valid = _example()
    fold["truth"][2, 2] = True
    with pytest.raises(ValueError, match="overlaps the visible catalogue"):
        evaluator.evaluate(prediction, fold, valid)


def test_evaluate_rejects_mask_shape_mismatch():
    prediction, fold, valid = _example()
    fold["region"] = np.ones((2, 2), dtype=bool)
    with pytest.raises(ValueError, match="matching shapes"):
        evaluator.evaluate(prediction, fold, valid)


def test_evaluate_rejects_holdout_without_scored_positives():
    prediction, fold, valid = _example()
    fold["truth"][:] = False
    with pytest.raises(ValueError, match="must contain positives"):
        evaluator.evaluate(prediction, fold, valid)


def test_metric_radius_is_300_metres_at_the_pinned_grid():
    assert metric.R_M == 300.0

def test_pooled_summary_requires_identical_per_block_truth_counts():
    candidate = np.zeros((3, 4), dtype=np.float64)
    control = np.zeros_like(candidate)
    candidate[0, 3] = 2
    control[0, 3] = 1
    with pytest.raises(ValueError, match="same integer truth count per spatial block"):
        evaluator.pooled_summary({"candidate": candidate, "control": control}, draws=20,
                                 candidate="candidate")
