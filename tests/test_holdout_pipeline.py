import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems57.evaluate_holdout import evaluate, pooled_summary, VERSION
from gems57.grid import Grid
from gems57.holdout import BUFFER_PX, build_holdout
from gems57.metric import dti_exact, dti_spatial_terms
from gems57.network import segments


def _small_grid():
    shape = (80, 80)
    footprint = np.ones(shape, bool)
    catalogue = np.zeros(shape, bool)
    # One isolated, unchunked branch safely inside each eroded quadrant.
    catalogue[15:25, 20] = True
    catalogue[15:25, 60] = True
    catalogue[55:65, 20] = True
    catalogue[55:65, 60] = True
    return Grid(footprint=footprint, catalogue=catalogue, crs="EPSG:32611",
                transform=None, height=shape[0], width=shape[1])


def test_none_keeps_a_whole_branch_while_integer_limit_chunks_it():
    trace = np.zeros((100, 100), bool)
    trace[10:90, 20] = True
    whole, n_whole, _ = segments(trace, max_len_px=None)
    chunks, n_chunks, _ = segments(trace, max_len_px=12)
    assert n_whole == 1
    assert np.unique(whole[trace]).tolist() == [1]
    assert n_chunks > 1
    assert len(np.unique(chunks[trace])) == n_chunks
    assert int((whole > 0).sum()) == int(trace.sum())


def test_holdout_hides_whole_branch_and_keeps_buffer_scoring_domain():
    grid = _small_grid()
    ctx = build_holdout(grid, seeds=(20,), modes=("all",), hide_frac=0.15)
    cell = ctx.cell("draw20_foldNW_all")
    hidden = ctx.hidden_by_cell[cell.key]
    assert cell.n_truth == int(hidden[cell.bbox].sum())
    # Each chosen segment is an intact between-junction branch (not a 12 px chunk).
    seg, _, _ = segments(grid.catalogue, max_len_px=None)
    ids = np.unique(seg[hidden])
    assert len(ids) == 1 and ids[0] > 0
    assert int(hidden.sum()) == 10

    dist_to_hidden = distance_transform_edt(~hidden)
    feature_visible = ctx.visible(cell.key)
    exact_visible = ctx.visible_exact(cell.key)
    assert np.array_equal(exact_visible, grid.catalogue & ~hidden)
    assert not np.any(feature_visible & (dist_to_hidden <= BUFFER_PX))

    # The collar is excluded from training negatives but remains in the test
    # scoring region; visible fault pixels themselves are still masked exactly.
    halo_negative = (dist_to_hidden > 0) & (dist_to_hidden <= BUFFER_PX) & ~hidden
    cropped_halo = halo_negative[cell.bbox]
    assert np.any(cell.region & cropped_halo)
    assert np.any(cell.active & cropped_halo)
    assert not np.any(cell.train_active & cropped_halo)
    assert np.array_equal(cell.active, cell.region & ~cell.visible)


def test_shared_evaluator_masks_visible_faults_pixel_exactly_and_matches_metric():
    prediction = np.zeros((40, 40), np.float32)
    truth = np.zeros((40, 40), bool)
    visible = np.zeros((40, 40), bool)
    region = np.ones((40, 40), bool)
    prediction[18, 19] = 1.0
    visible[18, 18] = True
    truth[18, 20] = True
    result, terms = evaluate(prediction, {"region": region, "visible": visible,
                                          "truth": truth}, region,
                             block_side=10, origin=(190, 190),
                             global_shape=(400, 400))
    reference = dti_exact(prediction, truth, valid=region, known=visible)
    assert result["evidence_class"] == "HOLDOUT-DTI"
    assert result["evaluator_version"] == VERSION
    assert result["withheld_positive_count"] == 1
    assert result["tp"] == reference["tp"]
    assert result["fp"] == reference["fp"]
    assert result["fn"] == reference["fn"]
    assert np.allclose(terms.sum(axis=0),
                       [reference["tp"], reference["fp"], reference["fn"], 1.0])
    assert terms.shape == (40 * 40, 4)


def test_spatial_terms_are_global_origin_aligned_and_pooled_bootstrap_is_paired():
    prediction = np.zeros((30, 30), bool)
    truth = np.zeros((30, 30), bool)
    valid = np.ones((30, 30), bool)
    prediction[4, 4] = True
    truth[4, 5] = True
    known = np.zeros((30, 30), bool)
    result, terms = dti_spatial_terms(
        prediction, truth, valid=valid, known=known, origin=(98, 98),
        global_shape=(300, 300), block_side=100)
    assert result["n_truth"] == 1
    # Global coordinate (102,103) belongs to row block 1, column block 1 (id 4);
    # local-index-based binning would incorrectly place the contribution in block 0.
    assert terms[4, 3] == 1
    better = terms.copy()
    better[8, 1] = 0.1  # a second physical cluster, without adding withheld truth
    worse = better.copy()
    worse[4, 1] += 1.0
    summary = pooled_summary({"h57b_tip_distance": better, "no_side": worse},
                             draws=200, seed=7, candidate="h57b_tip_distance")
    assert summary["scores"]["h57b_tip_distance"]["evidence_class"] == "HOLDOUT-DTI"
    assert summary["scores"]["h57b_tip_distance"]["withheld_positive_count"] == 1
    assert summary["paired_differences"]["no_side"]["delta"] > 0
    assert summary["bootstrap"]["confidence"] == 0.95
