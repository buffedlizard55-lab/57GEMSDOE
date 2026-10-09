"""Conservative local GeoTIFF validator, not organizer upload acceptance.

Validates raw values, the pinned bridged grid and the supplied footprint.
The organizer permits outside-bounds null/NaN; all-finite zero-fill is our
precaution. The cause of the owner's rejected file is not established.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import rasterio

from .grid import EPSG, HEIGHT, WIDTH, TRANSFORM

SENTINELS = (-9999.0, -999.0, 9999.0, -3.4e38, 1e30)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(path: Path, footprint: np.ndarray | None = None,
             catalogue: np.ndarray | None = None) -> dict:
    """Run local template/range checks. Returns a local receipt, not portal acceptance."""
    path = Path(path)
    with rasterio.open(path) as ds:
        a = ds.read(1)
        meta = dict(crs=str(ds.crs), shape=[ds.height, ds.width], dtype=ds.dtypes[0],
                    count=ds.count, nodata=None if ds.nodata is None else float(ds.nodata),
                    transform=list(tuple(ds.transform)[:6]),
                    profile_compress=ds.profile.get("compress"))
        desc = ds.descriptions
        h, w = ds.height, ds.width

    finite = np.isfinite(a)
    checks = {
        "single_band": meta["count"] == 1,
        "dtype_float32": meta["dtype"] == "float32",
        f"dimensions_{HEIGHT}x{WIDTH}": (h, w) == (HEIGHT, WIDTH),
        f"crs_epsg_{EPSG}": meta["crs"] == f"EPSG:{EPSG}",
        "transform_matches_sample_submission": meta["transform"] == list(tuple(TRANSFORM)[:6]),
        "no_nan_anywhere": bool(finite.all()),
        "no_inf_anywhere": bool(np.isfinite(a).all()),
        "no_sentinel_values": bool(not np.isin(a[np.isfinite(a)], SENTINELS).any()),
        "range_0_1_guaranteed": bool(np.nanmin(a) >= 0.0 and np.nanmax(a) <= 1.0),
        "min_ge_0": bool(np.nanmin(a) >= 0.0),
        "max_le_1": bool(np.nanmax(a) <= 1.0),
    }
    if footprint is not None:
        checks["in_footprint_all_finite"] = bool(finite[footprint].all())
        checks["in_footprint_range_0_1"] = bool(a[footprint].min() >= 0.0
                                                and a[footprint].max() <= 1.0)
        checks["outside_footprint_zero"] = bool(np.all(a[~footprint] == 0.0))
    if catalogue is not None:
        checks["zero_dots_on_mapped_catalogue"] = int((a[catalogue] > 0).sum()) == 0

    receipt = {
        "file": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "meta": meta,
        "band_description": list(desc),
        "n_finite": int(finite.sum()),
        "n_nan": int((~finite).sum()),
        "min": float(np.nanmin(a)), "max": float(np.nanmax(a)),
        "mean": float(np.nanmean(a)),
        "emitted_positive_pixels": int((a > 0).sum()),
        "checks": checks,
        "all_checks_passed": bool(all(checks.values())),
    }
    if catalogue is not None:
        receipt["on_catalogue_positive_pixels"] = int((a[catalogue] > 0).sum())
    if footprint is not None:
        receipt["in_footprint_positive_pixels"] = int((a[footprint] > 0).sum())
        receipt["footprint_fraction"] = float((a[footprint] > 0).sum() / footprint.sum())
    return receipt


def assert_submittable(receipt: dict) -> None:
    """Raise unless every check passed.  Used as the gate before publishing."""
    bad = [k for k, v in receipt["checks"].items() if not v]
    if bad:
        raise AssertionError(f"submission would be rejected by the portal: {bad}")
