"""Exercise the project's strict finite/[0,1] GeoTIFF preflight policy."""
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
    # Local all-finite policy rejects the NaN diagnostic; it does not establish the portal's cause.
    assert rn["checks"]["no_nan_anywhere"] is False
    assert rn["all_checks_passed"] is False


def test_shape_crs_transform_are_pinned():
    import rasterio
    p = gridmod.DATA_DIR / "sample_submission.tif"
    with rasterio.open(p) as ds:
        assert (ds.height, ds.width) == (gridmod.HEIGHT, gridmod.WIDTH)
        assert str(ds.crs) == f"EPSG:{gridmod.EPSG}"
        assert tuple(ds.transform)[:6] == tuple(gridmod.TRANSFORM)[:6]
