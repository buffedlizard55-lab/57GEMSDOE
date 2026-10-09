"""Pin the organizer's published worked example and the metric's algebra.

The problem page (competition 306, page 967) gives a worked example with
TPw 3.00, FPw 1.89, FNw 2.00 evaluating to 0.60 (0.6026516673... unrounded).
"""
import numpy as np

from gems57.metric import dti, dti_bruteforce, kernel


def test_worked_example_from_problem_page():
    # The page's arithmetic, pinned:
    tpw, fpw, fnw = 3.00, 1.89, 2.00
    expect = tpw / (tpw + 0.2 * fpw + 0.8 * fnw)
    assert abs(expect - 0.6026516673) < 1e-8

    # The same numbers through the module: 3 covered truth px (isolated, so no
    # partial credit leaks between them), 2 uncovered truth px, 1.89 FP mass
    # placed >3 px from every truth pixel (no credit).
    g = np.zeros((9, 13))
    g[0, 0] = g[0, 6] = g[0, 12] = 1.0     # covered truth
    g[5, 0] = g[5, 6] = 1.0               # uncovered truth
    p = np.zeros((9, 13))
    p[0, 0] = p[0, 6] = p[0, 12] = 1.0    # TPw = 3.00
    p[8, 3] = 1.0                          # FP mass 1.00 (>3 px from all truth)
    p[8, 4] = 0.89                         # FP mass 0.89
    r = dti(p, g)
    assert abs(r["tpw"] - 3.0) < 1e-9
    assert abs(r["fpw"] - 1.89) < 1e-9
    assert abs(r["fnw"] - 2.0) < 1e-9
    assert abs(r["dti"] - 0.6026516673) < 1e-8


def test_dti_matches_bruteforce():
    rng = np.random.default_rng(7)
    g = (rng.random((23, 19)) < 0.08).astype(float)
    p = (rng.random((23, 19)) < 0.15).astype(float)
    a = dti(p, g)["dti"]
    b = dti_bruteforce(p, g)          # reference implementation returns a float
    assert abs(a - b) < 1e-9


def test_kernel_decays_to_zero_at_300m():
    k = kernel(np.array([0.0, 150.0, 299.0, 300.0, 450.0]))
    assert abs(k[0] - 1.0) < 1e-12
    assert abs(k[1] - 0.5) < 1e-12
    assert abs(k[2] - (1.0 - 299.0 / 300.0)) < 1e-12
    assert k[3] == 0.0
    assert k[4] == 0.0


def test_dti_rejects_out_of_range_predictions():
    g = np.ones((3, 3))
    try:
        dti(np.full((3, 3), 1.5), g)
    except ValueError:
        pass
    else:
        raise AssertionError("predictions > 1 must be rejected")
