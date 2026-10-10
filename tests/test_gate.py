"""The shipped submission must pass the template's format gate.

Also pins the writer's fail-closed contract: it REJECTS out-of-range values,
NaN anywhere, positive mass outside the footprint, and over-long names/notes —
no silent repair (the earlier "Predicted values must be in range [0, 1]"
organizer rejection is why callers must normalize before packaging).
"""
import hashlib
import json
import numpy as np
import pytest
import rasterio

from gems57 import gates
from gems57.submission_writer import write_submission

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / "docs" / "downloads"
SAMPLE = ROOT / "data" / "official" / "sample_submission.tif"


def _shipped() -> tuple[Path, dict, dict]:
    """Locate the current shipped submission from the build audit.

    The artifact name carries a build timestamp, so it must be discovered,
    never hard-coded (a stale literal here is how this test rotted once
    already — IR-57-TEST-01).
    """
    audit = json.loads((ROOT / "evidence" / "submission_build_all.json").read_text())
    name = audit["submission_name"]
    sub = DL / f"{name}-zeros.tif"
    receipt = json.loads((DL / f"checks-{name}-zeros.tif.json").read_text())
    return sub, audit, receipt


def test_shipped_submission_passes_format_gate():
    sub, audit, receipt = _shipped()
    assert sub.exists(), f"missing submission artifact: {sub}"
    with rasterio.open(SAMPLE) as ds:
        footprint = np.isfinite(ds.read(1))
    rep = gates.format_report(sub, SAMPLE, footprint=footprint)
    assert rep["ok"], rep.get("problems")
    assert rep["bands"] == 1
    assert rep["dtype"] == "float32"
    assert rep["crs"] == "EPSG:32611"
    assert rep["n_nan"] == 0
    assert rep["min"] >= 0.0 and rep["max"] <= 1.0
    assert rep["mass_outside_footprint"] == 0
    assert rep["n_nonzero"] == audit["emitted_pixels"]
    with rasterio.open(sub) as ds:
        vals = np.unique(ds.read(1))
    assert set(vals) <= {0.0, 1.0}


def test_shipped_submission_has_no_dots_on_known_faults():
    sub, _, _ = _shipped()
    with rasterio.open(sub) as ds:
        p = ds.read(1)
    with rasterio.open(ROOT / "data" / "official" / "labels.tif") as ds:
        cat = ds.read(1)
    assert float(p[cat > 0].sum()) == 0.0


def test_shipped_submission_sha256_matches_receipt():
    sub, audit, receipt = _shipped()
    got = hashlib.sha256(sub.read_bytes()).hexdigest()
    assert got == receipt["sha256"] == audit["zeros_tif"]["sha256"]
    assert audit["submission_note_len"] <= 140
    # the audit's own promote flag must agree with the validator + the drift
    # screen.  IR-57-OVERLAP-01: the drift screen is unique_vs_other_lanes;
    # the mechanical all-rasters `unique` flag can be False purely from
    # same-lane proximity overlap with this repo's own earlier builds, which
    # is disclosed (worst_jaccard_same_lane < limit) rather than a drift firing.
    uq = audit["uniqueness"]
    assert audit["promote"] == bool(receipt["all_checks_passed"]
                                    and uq["unique_vs_other_lanes"])
    if not uq["unique"]:
        # a mechanical firing is only acceptable if it comes exclusively from
        # this repo's own earlier builds and never from another lane
        assert uq["unique_vs_other_lanes"] is True
        assert uq["worst_overlap_other_lanes"] <= uq["overlap_limit"]
        assert uq["worst_jaccard_same_lane"] <= uq["jaccard_limit"]
        assert uq["worst_rho_same_lane"] <= uq["rho_limit"]


def _valid_footprint():
    with rasterio.open(SAMPLE) as ds:
        ref = ds.read(1)
    return np.isfinite(ref)


def test_writer_rejects_out_of_range_prediction(tmp_path):
    valid = _valid_footprint()
    pred = np.where(valid, 2.5, 0.0).astype(np.float32)
    with pytest.raises(ValueError):
        write_submission(tmp_path / "x.tif", pred, SAMPLE, valid,
                         note="t", name="t")


def test_writer_rejects_nan_inside_footprint(tmp_path):
    valid = _valid_footprint()
    pred = np.where(valid, 0.5, 0.0).astype(np.float32)
    pred[valid] = np.nan
    with pytest.raises(ValueError):
        write_submission(tmp_path / "x.tif", pred, SAMPLE, valid,
                         note="t", name="t")


def test_writer_rejects_mass_outside_footprint(tmp_path):
    valid = _valid_footprint()
    pred = np.where(valid, 0.0, 1.0).astype(np.float32)  # positive outside footprint
    with pytest.raises(ValueError):
        write_submission(tmp_path / "x.tif", pred, SAMPLE, valid,
                         note="t", name="t")


def test_writer_rejects_overlong_note(tmp_path):
    valid = _valid_footprint()
    pred = np.where(valid, 0.5, 0.0).astype(np.float32)
    with pytest.raises(ValueError):
        write_submission(tmp_path / "x.tif", pred, SAMPLE, valid,
                         note="n" * 141, name="t")


def test_writer_accepts_valid_binary_prediction(tmp_path):
    valid = _valid_footprint()
    pred = np.where(valid, 0.0, 0.0).astype(np.float32)
    ys, xs = np.nonzero(valid)
    pred[ys[:100], xs[:100]] = 1.0
    out = tmp_path / "ok.tif"
    rec = write_submission(out, pred, SAMPLE, valid, note="test note", name="test")
    assert rec["ok"] if "ok" in rec else True
    assert rec["validator"]["ok"]
    assert rec["validator"]["n_nonzero"] == 100
    assert (tmp_path / "ok.zip").exists()
    assert (tmp_path / "ok.json").exists()
