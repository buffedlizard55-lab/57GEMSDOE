"""Preserve historical H57-I format/bytes; withdraw its partial-registry clearance."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zipfile
import numpy as np
import pytest
import rasterio
from gems57 import load_grid
from gems57.validate import validate
from gems57.uniqueness import compare_to_registry

ROOT=Path(__file__).resolve().parents[1]
TIF=ROOT/'evidence/history/public-downloads/gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif'
ALIAS=ROOT/'evidence/history/public-downloads/archive/SUBMIT-THIS-gems57-h57i-iso-zeros.tif'
SHA='0025ec29647e3778043b81f5bf998e0e652ea25a8ead03339f40e9939de78b22'


def test_historical_tif_format_and_sha_preserved():
    grid=load_grid();v=validate(TIF,grid.footprint,grid.catalogue)
    assert v['all_checks_passed'] and v['n_nan']==0
    assert v['min']==0 and v['max']==1
    assert v['emitted_positive_pixels']==37654 and v['on_catalogue_positive_pixels']==0
    assert v['sha256']==SHA==hashlib.sha256(TIF.read_bytes()).hexdigest()
    with rasterio.open(TIF) as ds:
        assert ds.nodata is None and set(np.unique(ds.read(1)))<={0.,1.}


def test_misleading_alias_is_archived_not_advertised():
    assert ALIAS.is_file() and ALIAS.read_bytes()==TIF.read_bytes()
    assert not (ROOT/'docs/downloads'/ALIAS.name).exists()
    assert 'SUBMIT-THIS' not in (ROOT/'docs/index.html').read_text()


def test_historical_zip_contains_only_its_tif():
    with zipfile.ZipFile(TIF.with_suffix('.zip')) as archive:
        assert archive.namelist()==[TIF.name]
        assert archive.read(TIF.name)==TIF.read_bytes()


def test_partial_16_prior_check_never_clears_and_dense_witness_fails():
    grid=load_grid()
    partial=compare_to_registry(TIF,ROOT/'registry/registry_index.json',grid.footprint)
    assert not partial['unique'] and not partial['complete_accessible_scan']
    withdrawal=json.loads((ROOT/'evidence/h57i_clearance_withdrawal.json').read_text())
    assert withdrawal['candidate_file_sha256']==SHA
    assert withdrawal['worst_dot_overlap']==1 and not withdrawal['unique']


def test_retired_h57i_entrypoint_cannot_run_or_clear_a_candidate():
    sys.path.insert(0, str(ROOT / 'src'))
    path = ROOT / 'scripts' / 'experiment_h57i.py'
    spec = importlib.util.spec_from_file_location('retired_h57i', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(SystemExit, match='partial-registry/saturation-policy clearance is prohibited'):
        module.main()


def test_h57k_emitter_and_model_runner_fail_closed_under_spent_budget():
    sys.path.insert(0, str(ROOT / 'src'))
    for script_name, match in (
        ('emit_h57k', 'partial-registry/Jaccard/saturation clearance is prohibited'),
        ('build_h57k', 'Experiment budget spent or unverified'),
    ):
        path = ROOT / 'scripts' / f'{script_name}.py'
        spec = importlib.util.spec_from_file_location(f'retired_{script_name}', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with pytest.raises(SystemExit, match=match):
            module.main()


def test_current_site_and_generic_card_withdraw_submission_permission():
    text=(ROOT/'docs/index.html').read_text();card=json.loads((ROOT/'evidence/run_card.json').read_text())
    assert 'Submit to competition: NO' in text and 'OK TO DOWNLOAD AND SUBMIT' not in text
    assert not card['okay_to_submit'] and card['verdict']=='negative' and card['submission_slots_used']==0
    assert card['raster_sha256']!=SHA
    assert TIF.name in (ROOT/'docs/archive.html').read_text()
    assert 'DO NOT SUBMIT' in (ROOT/'docs/session-4.html').read_text()
    note=card['submission_note'];assert 1<=len(note)<=140 and note in text
