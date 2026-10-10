"""Pin the local all-finite policy; this is not a statement about portal acceptance."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems57 import grid as gridmod
from gems57.validate import validate


def test_zeros_mode_passes_and_nan_mode_fails(tmp_path):
    foot = np.zeros((gridmod.HEIGHT, gridmod.WIDTH), bool)
    foot[100:200, 100:200] = True
    cat = np.zeros_like(foot); cat[150, 150] = True
    vals = np.zeros((gridmod.HEIGHT, gridmod.WIDTH), np.float32)
    vals[110:120, 110:120] = 1.0

    z = tmp_path / "z.tif"
    gridmod.write_submission(z, np.where(foot, vals, 0.0), mode="zeros")
    rz = validate(z, foot, cat)
    assert rz["all_checks_passed"], [k for k, v in rz["checks"].items() if not v]
    assert rz["checks"]["zero_dots_on_mapped_catalogue"] is True
    assert rz["n_nan"] == 0

    n = tmp_path / "n.tif"
    gridmod.write_submission(n, np.where(foot, vals, np.nan), mode="nan")
    rn = validate(n, foot, cat)
    # This fails our conservative all-finite policy; portal rejection cause is unproven.
    assert rn["checks"]["no_nan_anywhere"] is False
    assert rn["all_checks_passed"] is False


def test_legacy_grid_writer_fails_closed_instead_of_clipping(tmp_path):
    import pytest

    valid = np.zeros((gridmod.HEIGHT, gridmod.WIDTH), np.float32)
    valid[100, 100] = 0.5
    for bad in (-0.01, 1.01, np.inf, -np.inf):
        candidate = valid.copy()
        candidate[110, 110] = bad
        with pytest.raises(ValueError):
            gridmod.write_submission(tmp_path / f"invalid-{bad}.tif", candidate, mode="zeros")

    candidate = valid.copy()
    candidate[110, 110] = np.nan
    with pytest.raises(ValueError, match="all values finite"):
        gridmod.write_submission(tmp_path / "nan-zeros.tif", candidate, mode="zeros")


def test_nan_mode_checks_finite_values_but_preserves_nan_for_diagnostics(tmp_path):
    import pytest

    values = np.zeros((gridmod.HEIGHT, gridmod.WIDTH), np.float32)
    values[0, 0] = np.nan
    values[1, 1] = 0.25
    path = tmp_path / "diagnostic.tif"
    gridmod.write_submission(path, values, mode="nan")
    import rasterio
    with rasterio.open(path) as src:
        written = src.read(1)
        assert np.isnan(written[0, 0])
        assert written[1, 1] == np.float32(0.25)
    values[1, 1] = 1.1
    with pytest.raises(ValueError, match="no silent clipping"):
        gridmod.write_submission(tmp_path / "out-of-range-nan.tif", values, mode="nan")


def test_shape_crs_transform_are_pinned():
    import rasterio
    p = gridmod.DATA_DIR / "sample_submission.tif"
    with rasterio.open(p) as ds:
        assert (ds.height, ds.width) == (gridmod.HEIGHT, gridmod.WIDTH)
        assert str(ds.crs) == f"EPSG:{gridmod.EPSG}"
        assert tuple(ds.transform)[:6] == tuple(gridmod.TRANSFORM)[:6]
