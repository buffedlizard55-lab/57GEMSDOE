"""Session 4 candidate is unique, format-valid, and advertised as submittable."""
from pathlib import Path
import hashlib
import json
import zipfile

import numpy as np
import rasterio

from gems57 import load_grid
from gems57.validate import validate
from gems57.uniqueness import compare_to_registry

ROOT = Path(__file__).resolve().parents[1]
TIF = ROOT / "docs" / "downloads" / "gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif"
ALIAS = ROOT / "docs" / "downloads" / "SUBMIT-THIS-gems57-h57i-iso-zeros.tif"
SHA = "0025ec29647e3778043b81f5bf998e0e652ea25a8ead03339f40e9939de78b22"
INDEX = ROOT / "evidence" / "registry_full_index.json"


def test_submission_tif_format_and_sha():
    assert TIF.is_file()
    g = load_grid()
    v = validate(TIF, g.footprint, g.catalogue)
    assert v["all_checks_passed"]
    assert v["n_nan"] == 0
    assert v["min"] == 0.0 and v["max"] == 1.0
    assert v["emitted_positive_pixels"] == 37654
    assert v["on_catalogue_positive_pixels"] == 0
    assert v["sha256"] == SHA
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == SHA
    with rasterio.open(TIF) as ds:
        a = ds.read(1)
        assert ds.nodata is None
        assert set(np.unique(a)) <= {0.0, 1.0}


def test_alias_is_byte_identical():
    assert ALIAS.is_file()
    assert ALIAS.read_bytes() == TIF.read_bytes()


def test_zip_contains_only_the_tif():
    zp = TIF.with_suffix(".zip")
    with zipfile.ZipFile(zp) as z:
        assert z.namelist() == [TIF.name]
        assert z.read(TIF.name) == TIF.read_bytes()


def test_sha_novel_vs_644_and_unique_vs_local_registry():
    idx = {r["sha256"] for r in json.loads(INDEX.read_text())["rasters"]}
    assert SHA not in idx
    g = load_grid()
    uniq = compare_to_registry(TIF, ROOT / "registry" / "registry_index.json", g.footprint)
    assert uniq["unique"] is True
    assert uniq["worst_spearman_full_footprint"] < 0.90
    assert uniq["worst_dot_overlap"] < 0.70
    assert uniq["worst_jaccard_dot_sets"] < 0.50


def test_site_says_ok_to_submit_and_names_the_file():
    idx = (ROOT / "docs" / "index.html").read_text()
    root = (ROOT / "index.html").read_text()
    assert "OK TO DOWNLOAD AND SUBMIT" in idx
    assert "OK TO DOWNLOAD AND SUBMIT" in root
    assert TIF.name in idx
    assert SHA in idx
    note = json.loads((ROOT / "evidence" / "run_card.json").read_text())["submission_note"]
    assert 1 <= len(note) <= 140
    assert note in idx
    card = json.loads((ROOT / "evidence" / "run_card.json").read_text())
    assert card["ok_to_submit"] is True
    assert card["verdict"] == "promote"
    assert card["slot_used"] is False
    assert card["raster_sha256"] == SHA
