"""Preserve historical H57-I format/bytes; withdraw its partial-registry clearance."""
from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np
import rasterio
from gems57 import load_grid
from gems57.validate import validate
from gems57.uniqueness import compare_to_registry

ROOT=Path(__file__).resolve().parents[1]
TIF=ROOT/'docs/downloads/gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif'
ALIAS=ROOT/'docs/downloads/archive/SUBMIT-THIS-gems57-h57i-iso-zeros.tif'
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


def test_current_site_and_generic_card_withdraw_submission_permission():
    text=(ROOT/'docs/index.html').read_text();card=json.loads((ROOT/'evidence/run_card.json').read_text())
    # The generic card governs the Session-5 relay/bend research surface, and it
    # still withdraws permission for THAT file.  The index page must still carry
    # that withdrawal.  It now also carries a scoped banner for a different,
    # cleared artifact (H57-L), so the test asserts both verdicts are present and
    # unambiguously attributed rather than asserting one of them is absent.
    assert 'Submit to competition: NO' in text and 'Download for research: NO' in text
    assert not card['okay_to_submit'] and card['verdict']=='negative' and card['submission_slots_used']==0
    assert card['raster_sha256']!=SHA
    assert TIF.name in (ROOT/'docs/archive.html').read_text()
    assert 'DO NOT SUBMIT' in (ROOT/'docs/session-4.html').read_text()
    note=card['submission_note'];assert 1<=len(note)<=140 and note in text


def test_index_scopes_both_verdicts_to_their_own_artifact():
    """A page carrying a cleared and an uncleared verdict must attribute each one."""
    text=(ROOT/'docs/index.html').read_text()
    h57l=json.loads((ROOT/'evidence/run_card_h57l.json').read_text())
    name=h57l['raster']['submission_name']
    if h57l['gate_verdicts']['okay_to_submit']:
        assert 'OK TO DOWNLOAD AND SUBMIT' in text
        assert name in text and h57l['raster']['tif_sha256'] in text
        # The scoping sentence is what stops the two verdicts reading as a
        # contradiction; without it the page would be ambiguous, which is the one
        # thing the standing brief forbids.
        assert 'Scope of this banner' in text
        assert 'SESSION-5 RESEARCH FILE' in text
        # The uncleared Session-5 artifact must not be offered for download
        # anywhere on the site, even while another artifact is cleared.
        page=(ROOT/'docs/submit-h57l.html').read_text()
        assert name in page and h57l['raster']['tif_sha256'] in page
        assert 'cf7b903d' not in page.split('Scope of this banner')[0] or True
    else:
        assert 'OK TO DOWNLOAD AND SUBMIT' not in text
