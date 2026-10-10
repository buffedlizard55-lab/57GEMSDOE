import numpy as np

from gems57.anatomy import junction_distance_px


def test_junction_distance_uses_the_supplied_visible_mask():
    visible = np.zeros((15, 15), bool)
    visible[7, 3:12] = True
    visible[3:12, 7] = True
    dist = junction_distance_px(visible)
    assert dist.shape == visible.shape
    assert dist[7, 7] == 0.0
    # The shared junction definition marks a small cluster around the cross;
    # the horizontal end is three pixels from that cluster.
    assert dist[7, 3] == 3.0
    assert np.isfinite(dist).all()


def test_no_visible_junction_returns_finite_far_field():
    visible = np.zeros((5, 9), bool)
    visible[2, 1:8] = True
    dist = junction_distance_px(visible)
    assert np.isfinite(dist).all()
    assert np.allclose(dist, np.hypot(*visible.shape))
