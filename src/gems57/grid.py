"""Study-area grid: CRS, shape, geotransform and the scored footprint.

Every constant here is read from the two competition files committed in
``data/bridge/`` and re-verified by ``scripts/run_lane.py verify`` (writes ``evidence/verify_grid.json``):

* ``existing_faults.tif``  sha256 ``7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093``
  (byte-identical to the ``labels.tif`` recorded in
  ``GEMSDOE32/data/restore_receipt.json``, sha256 ``7ba308cc...`` -- i.e. the
  public "labels" raster *is* the mapped-fault catalogue; the scored truth is
  not published.)
* ``sample_submission.tif`` sha256 ``2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc``

Verified properties
-------------------
CRS ``EPSG:32611`` (UTM zone 11N), shape ``3730 x 3292``, transform
``(100, 0, 243350, 0, -100, 4508550)``, 100 m pixels, bounds
``(243350, 4135550) - (572550, 4508550)``.  The sample submission carries
``nodata = NaN`` with 7,111,787 NaN cells and 5,167,373 finite cells; the finite
cells define the scored footprint.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

EPSG = 32611
HEIGHT = 3730
WIDTH = 3292
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
PIXEL_M = 100.0

# --- names the earlier lanes' modules (gates.py, submission_writer.py) import ---
# Added at merge time so those modules keep working unchanged rather than being
# forked. Same six pinned numbers, same measured shape; no second source of truth.
SHAPE = (HEIGHT, WIDTH)
CELL_M = PIXEL_M
CRS_EPSG = f"EPSG:{EPSG}"

SHA256_EXISTING_FAULTS = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
SHA256_SAMPLE_SUBMISSION = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "bridge"


@dataclass(frozen=True)
class Grid:
    footprint: np.ndarray      # bool, scored study-area cells (sample_submission finite)
    catalogue: np.ndarray      # bool, mapped USGS/INGENIOUS fault cells inside the footprint
    crs: object
    transform: object
    height: int
    width: int

    @property
    def shape(self) -> tuple[int, int]:
        return (self.height, self.width)


def _check(src, what: str) -> None:
    if str(src.crs) != f"EPSG:{EPSG}":
        raise ValueError(f"{what}: CRS is {src.crs}, expected EPSG:{EPSG}")
    if (src.height, src.width) != (HEIGHT, WIDTH):
        raise ValueError(f"{what}: shape {src.height}x{src.width}, expected {HEIGHT}x{WIDTH}")
    if tuple(src.transform)[:6] != tuple(TRANSFORM)[:6]:
        raise ValueError(f"{what}: transform {tuple(src.transform)}, expected {tuple(TRANSFORM)}")


def load_grid(data_dir: Path | None = None) -> Grid:
    d = Path(data_dir) if data_dir else DATA_DIR
    with rasterio.open(d / "existing_faults.tif") as src:
        _check(src, "existing_faults.tif")
        cat = src.read(1)
    with rasterio.open(d / "sample_submission.tif") as src:
        _check(src, "sample_submission.tif")
        sub = src.read(1)
    footprint = np.isfinite(sub)
    catalogue = (cat > 0) & footprint
    return Grid(footprint=footprint, catalogue=catalogue, crs=src.crs,
                transform=TRANSFORM, height=HEIGHT, width=WIDTH)


def write_submission(path: Path, values: np.ndarray, *, mode: str = "zeros") -> dict:
    """Write a portal-legal single-band GeoTIFF.

    ``mode="zeros"`` -- every cell finite, outside-footprint cells set to 0.0 and
    no nodata tag.  This is the only mode that survives the portal check
    *"Predicted values must be in range [0, 1]"*, because ``NaN`` is neither
    ``>= 0`` nor ``<= 1``.  The competition's own ``sample_submission.tif``
    carries 7,111,787 NaN cells, so a submission written by copying its nodata
    convention fails that check; see ``docs/executive-summary`` and irregularity
    ``IR-57-NAN-01``.

    ``mode="nan"`` is produced for comparison/diagnostics only and must NOT be
    submitted.
    """
    values = np.asarray(values, np.float32)
    if values.shape != (HEIGHT, WIDTH):
        raise ValueError(f"values shape {values.shape} != {(HEIGHT, WIDTH)}")
    if mode == "zeros":
        out = np.where(np.isfinite(values), values, 0.0).astype(np.float32)
        np.clip(out, 0.0, 1.0, out=out)
        nodata = None
    elif mode == "nan":
        out = values.astype(np.float32)
        nodata = float("nan")
    else:
        raise ValueError("mode must be 'zeros' or 'nan'")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff", height=HEIGHT, width=WIDTH, count=1,
        dtype="float32", crs=f"EPSG:{EPSG}", transform=TRANSFORM,
        nodata=nodata, compress="lzw", tiled=False,
    ) as dst:
        dst.write(out, 1)
        dst.set_band_description(1, "predicted_new_fault_probability")
    return {"path": str(path), "mode": mode, "nodata": nodata}


def read_geotiff(path: str | Path) -> dict:
    """Everything a validator can complain about, re-derived from the bytes on disk.

    Kept byte-compatible with the earlier lanes' receipt format so their gates
    still read what they expect.
    """
    import hashlib

    p = Path(path)
    with rasterio.open(p) as src:
        a = src.read(1)
        info = dict(
            path=str(p), bytes=p.stat().st_size,
            sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            bands=src.count, dtype=src.dtypes[0], height=src.height, width=src.width,
            crs=str(src.crs) if src.crs is not None else None,
            transform=[float(v) for v in tuple(src.transform)[:6]],
            res=[float(v) for v in src.res],
            nodata=src.nodata, nodata_repr=repr(src.nodata),
        )
    finite = np.isfinite(a)
    info.update(
        finite_pixels=int(finite.sum()),
        min=float(np.nanmin(a)) if finite.any() else None,
        max=float(np.nanmax(a)) if finite.any() else None,
        positive_pixels=int((a > 0).sum()),
        nonzero_in_footprint=int(((a > 0) & finite).sum()),
        unique_values=int(len(np.unique(a[finite]))) if finite.any() else 0,
    )
    return info


def write_geotiff(path: str | Path, arr: np.ndarray, *, nodata: float | None = None) -> dict:
    """Write a single-band float32 GeoTIFF on the pinned grid and re-read it.

    The re-read is the contract: this returns what the *file* says. Tiled 256 px
    with deflate + horizontal predictor, matching what this family has shipped.
    """
    from rasterio.transform import from_origin

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if arr.dtype != np.float32:
        raise TypeError(f"submission must be float32, got {arr.dtype}")
    if arr.shape != SHAPE:
        raise ValueError(f"submission must be {SHAPE}, got {arr.shape}")
    if not np.isfinite(arr).all():
        raise ValueError("submission contains NaN/inf; the portal requires finite values")
    if arr.min() < 0.0 or arr.max() > 1.0:
        raise ValueError(f"submission out of range: min={arr.min()} max={arr.max()}")
    tr = Affine(*[float(v) for v in tuple(TRANSFORM)[:6]])
    west, north, xs, ys = tr.c, tr.f, tr.a, -tr.e
    check = from_origin(west, north, xs, ys)
    if tuple(float(v) for v in check)[:6] != tuple(tr)[:6]:
        raise AssertionError(f"transform drifted: {tuple(check)[:6]} != {tuple(tr)[:6]}")
    if abs(xs) != CELL_M or abs(ys) != CELL_M:
        raise AssertionError(f"cell size {xs} x {ys} != {CELL_M} m")
    profile = dict(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                   dtype="float32", crs=CRS_EPSG, transform=tr,
                   tiled=True, blockxsize=256, blockysize=256,
                   compress="deflate", predictor=2)
    if nodata is not None:
        profile["nodata"] = float(nodata)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)
    return read_geotiff(path)
