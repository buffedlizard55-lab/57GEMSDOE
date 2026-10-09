"""The shipped submission must pass the template's format gate.

Also pins the writer's fail-closed contract: it REJECTS out-of-range values,
NaN anywhere, positive mass outside the footprint, and over-long names/notes —
no silent repair (the earlier "Predicted values must be in range [0, 1]"
organizer rejection is why callers must normalize before packaging).
"""
import numpy as np
import pytest
import rasterio

from gems57 import gates
from gems57.submission_writer import write_submission

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "docs" / "downloads" / "gems57-h57-anatomy-enechelon-20261009T070415Z-e9d8d59a4357-zeros.tif"
RECEIPT = ROOT / "docs" / "downloads" / "checks-gems57-h57-anatomy-enechelon-20261009T070415Z-e9d8d59a4357-zeros.tif.json"
SAMPLE = ROOT / "data" / "official" / "sample_submission.tif"


def test_shipped_submission_passes_format_gate():
    assert SUB.exists(), f"missing submission artifact: {SUB}"
    with rasterio.open(SAMPLE) as ds:
        footprint = np.isfinite(ds.read(1))
    rep = gates.format_report(SUB, SAMPLE, footprint=footprint)
    assert rep["ok"], rep.get("problems")
    assert rep["bands"] == 1
    assert rep["dtype"] == "float32"
    assert rep["crs"] == "EPSG:32611"
    assert rep["n_nan"] == 0
    assert rep["min"] >= 0.0 and rep["max"] <= 1.0
    assert rep["mass_outside_footprint"] == 0
    assert rep["n_nonzero"] == 35341  # emitted positives in the shipped file (see evidence/submission_build_all.json)
    with rasterio.open(SUB) as ds:
        vals = np.unique(ds.read(1))
    assert set(vals) <= {0.0, 1.0}


def test_shipped_submission_has_no_dots_on_known_faults():
    with rasterio.open(SUB) as ds:
        p = ds.read(1)
    with rasterio.open(ROOT / "data" / "official" / "labels.tif") as ds:
        cat = ds.read(1)
    assert float(p[cat > 0].sum()) == 0.0


def test_shipped_submission_sha256_matches_receipt():
    import hashlib
    import json
    rec = json.loads(RECEIPT.read_text())
    got = hashlib.sha256(SUB.read_bytes()).hexdigest()
    assert got == rec["sha256"] == "8ba5a9822d87eb7b1e159ae2bfee8ced429ecb9752761041309fe5629df0e482"
    assert rec["all_checks_passed"] is True
    note = json.loads((ROOT / "evidence" / "submission_build_all.json").read_text())["submission_note"]
    assert len(note) <= 140


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
