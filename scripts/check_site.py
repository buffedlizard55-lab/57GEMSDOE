#!/usr/bin/env python3
"""Fail-closed local delivery QA: links, actual bytes, range, ZIP and run-card.

No model fitting, registry download, live submission or slot selection here.
The stored complete audit is checked against its immutable candidate hash.
"""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
from urllib.parse import unquote, urlsplit
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set();self.downloads=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.add(attrs['id'])
        for key in ('href','src'):
            if attrs.get(key):self.links.append(attrs[key])
        if tag=='a' and 'download' in attrs:self.downloads.append(attrs.get('href',''))


def check_links(docs):
    errors=[];pages=list(docs.rglob('*.html'))
    for page in pages:
        parser=Links();parser.feed(page.read_text())
        for value in parser.links:
            url=urlsplit(value)
            if url.scheme or url.netloc or value.startswith(('mailto:','data:')):continue
            target=(page.parent/unquote(url.path)).resolve() if url.path else page
            if not target.is_relative_to(docs.resolve()):
                errors.append(f'{page}: local link escapes site: {value}');continue
            if target.is_dir():target=target/'index.html'
            if not target.is_file():errors.append(f'{page}: broken local link {value}');continue
            if url.fragment and target.suffix=='.html':
                other=Links();other.feed(target.read_text())
                if unquote(url.fragment) not in other.ids:errors.append(f'{page}: missing anchor {value}')
    return pages,errors


def check(root=ROOT):
    import sys
    sys.path.insert(0,str(root/'src'))
    import numpy as np
    import rasterio
    from gems57.gates import format_report
    docs=root/'docs'
    card=json.loads((root/'evidence/run_card_current.json').read_text())
    public=json.loads((docs/'data/run_card_h57k.json').read_text())
    h57b=json.loads((root/'evidence/run_card.json').read_text())
    public_h57b=json.loads((docs/'data/run_card.json').read_text())
    assert card==public,'historical H57-K card is stale'
    assert h57b==public_h57b,'H57-B run card is stale'
    assert (docs/'data/run_card.json').read_bytes()==(root/'evidence/run_card.json').read_bytes()
    assert h57b['artifact']['raster_generated'] is False
    assert h57b['artifact']['raster_sha256'] is None
    assert h57b['artifact']['download_status'].startswith('NOT CLEARED')
    assert h57b['artifact']['submission_status'].startswith('NOT SUBMITTED')
    assert h57b['artifact']['weekly_slot_selected'] is False
    assert 'NOT RUN' in h57b['artifact']['validator_output']
    assert card['okay_to_download'] is False and card['okay_to_submit'] is False
    assert card['download_status'].startswith('NOT CLEARED')
    assert card['submission_status'].startswith('NOT SUBMITTED') and card['weekly_slot_selected'] is False
    assert not Path(card['validator_output']['file']).is_absolute()
    assert card['validator_output']['file']==card['file']
    assert card['verdict']=='negative' and card['submission_slots_used']==0
    assert card['final_dots']['status']=='not_generated' and not card['surface_before_placement']['protocol_pass']
    assert 0<len(card['submission_name'])<=140 and 0<len(card['submission_note'])<=140
    assert card['submission_note_chars']==len(card['submission_note'])
    raster=root/card['file'];archive=root/card['zip_file']
    digest=hashlib.sha256(raster.read_bytes()).hexdigest()
    for source in (raster, archive, raster.with_suffix('.json')):
        assert (root/'downloads'/'archive'/source.name).read_bytes()==source.read_bytes(), 'archive provenance mirror is stale'
    assert digest==card['raster_sha256'],'TIFF changed after its audit'
    receipt=json.loads(raster.with_suffix('.json').read_text())
    assert digest==receipt['sha256'] and receipt['approved_for_weekly_slot'] is False
    assert receipt['note']==card['submission_note']
    assert receipt['bytes']==raster.stat().st_size==card['validator_output']['bytes']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['zip_sha256']
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.namelist()==[raster.name],'ZIP must contain ONLY one TIFF'
        assert zipped.read(raster.name)==raster.read_bytes(),'ZIP contents differ'
    with rasterio.open(root/'data/official/sample_submission.tif') as ds:
        footprint=np.isfinite(ds.read(1))
    report=format_report(raster,root/'data/official/sample_submission.tif',footprint=footprint)
    assert report['ok'],report['problems']
    with rasterio.open(raster) as ds:
        assert ds.nodata is None
        values=ds.read(1)
    with rasterio.open(root/'data/official/labels.tif') as ds:
        known=ds.read(1)>0
    assert not (values[known]>0).any(),'positive predictions on known mask'
    assert int((values>0).sum())==card['validator_output']['emitted_positive_pixels']
    audit=json.loads((root/'evidence/orientation_surface_uniqueness.json').read_text())
    assert audit['candidate_file_sha256']==digest
    index=json.loads((root/'evidence/registry_refreshed.json').read_text())
    total=index['n_unique_grid_rasters']
    # Preserve the separate latest-main 698-row H57-K report as provenance, but
    # prove that it is not the 695-row public-main index and cannot clear H57-K.
    mainline_review=json.loads((root/'evidence/uniqueness_current_review.json').read_text())
    index_hashes={row['sha256'] for row in index['rasters']}
    review_hashes={row['sha256'] for row in mainline_review['rows']}
    assert mainline_review['registry_rasters_expected']==mainline_review['registry_rasters_checked']==698
    assert len(review_hashes)==698 and len(review_hashes-index_hashes)==4
    assert audit['candidate_file_sha256'] in index_hashes
    assert audit['candidate_file_sha256'] not in review_hashes
    assert not mainline_review['unique']
    card_audit=card['correlation_overlap_vs_registry']
    audit_count=audit['registry_rasters_expected']
    assert audit_count==audit['registry_rasters_checked']==len(audit['rows'])
    assert card_audit['registry_rasters_expected']==card_audit['registry_rasters_checked']==audit_count
    assert audit['complete_accessible_scan'] and not audit['source_errors']
    assert not audit['unique'] and audit['worst_dot_overlap']>0.70
    audit_literal_flags=sum(bool(row.get('duplicate_by_rho')) or bool(row.get('duplicate_by_overlap')) for row in audit['rows'] if 'error' not in row)
    assert audit_literal_flags==audit['duplicate_count']
    assert audit['byte_unique_among_checked'] and audit['pixel_unique_among_checked']
    # H57-K's candidate-specific receipt is an older 679-raster audit; the latest
    # public-main index is 695. Preserve the mismatch as an explicit historical
    # scope boundary, never coerce the old receipt into current clearance.
    h57k_audit_matches_latest_index=(audit_count==total)
    if not h57k_audit_matches_latest_index:
        assert audit_count < total
        assert card['okay_to_download'] is False and card['okay_to_submit'] is False
        assert card['verdict']=='negative'
    relay_audit=json.loads((root/'evidence/relay_bend_surface_uniqueness.json').read_text())
    held_h57j=json.loads((root/'evidence/history/run_card_session5_relay_bend_held.json').read_text())
    assert relay_audit['registry_rasters_expected']==relay_audit['registry_rasters_checked']==total
    assert relay_audit['complete_accessible_scan'] and not relay_audit['unique']
    relay_literal_flags=sum(bool(row.get('duplicate_by_rho')) or bool(row.get('duplicate_by_overlap')) for row in relay_audit['rows'] if 'error' not in row)
    assert relay_literal_flags==relay_audit['duplicate_count']
    assert relay_audit['jaccard_diagnostic_only'] is True
    assert relay_audit['candidate_file_sha256']==held_h57j['raster_sha256']
    assert held_h57j['okay_to_download'] is False and held_h57j['okay_to_submit'] is False
    assert held_h57j['surface_before_placement']['protocol_pass'] is False
    assert held_h57j['final_dots']['status']=='not_generated'
    assert held_h57j['permission_withdrawal']['source_card_claimed_okay_to_download'] is True
    assert held_h57j['permission_withdrawal']['withdrawn'] is True
    snapshots={row['repo']:row['commit'] for row in index['snapshots']}
    assert len(snapshots)==57
    sites=json.loads((root/'evidence/site_inventory.json').read_text())
    assert {row['repo']:row['commit'] for row in sites['repos']}==snapshots
    classification=json.loads((root/'evidence/registry_classification.json').read_text())
    assert classification['grid_rasters_checked']==total
    assert classification['auxiliary_inputs']==4
    structure=json.loads((root/'evidence/orientation_structure.json').read_text())
    assert structure['evidence_class']=='HOLDOUT-STRUCTURE (descriptive, not a score)'
    assert structure['n_withheld']==11321
    assert sum(structure['n_visible_reference'])==structure['n_visible_total']==21321
    assert structure['distance_quantile_probabilities']==[.1,.5,.9,.95,.99]
    relay_structure=json.loads((root/'evidence/relay_bend_structure.json').read_text())
    relay_relative=relay_structure['relative_strike']
    assert relay_structure['evidence_class']=='HOLDOUT-STRUCTURE (descriptive, not a score)'
    assert sum(relay_relative['n_withheld'])==relay_relative['n_withheld_total']==10811
    assert sum(relay_relative['n_visible_reference'])==relay_relative['n_visible_total']==21321
    assert relay_relative['sample_unit']=='fault raster pixel; not segment-weighted'
    assert relay_relative['minimum_local_coherence']==.2
    assert relay_relative['angle_convention']=='unsigned axial difference in degrees, folded to [0,90]'
    assert relay_structure['model_fit_performed'] is False
    assert relay_structure['dti_evaluated'] is False and relay_structure['production_dots_generated'] is False
    canary=json.loads((root/'evidence/orientation_canary.json').read_text())
    assert len(canary['features']) in (14, 22)
    for feature in canary['features'].values():
        assert not feature['leakage_flag'] and feature['discriminative_auc_max']<=.90
    holdout=json.loads((root/'evidence/orientation_holdout.json').read_text())
    for scores in (holdout['scores'],holdout['raw_surface_holdout']['scores']):
        for value in scores.values():
            assert value['evidence_class']=='HOLDOUT-DTI'
            assert value['evaluator_version']=='gems57-pooled-hide-v2'
            assert value['withheld_positive_pixels']==11321
            lo,hi=value['ci95'];assert 0<=lo<=hi<=1
            assert math.isclose(value['tpw']+value['fnw'],11321,abs_tol=1e-7)
            calculated=value['tpw']/(value['tpw']+.2*value['fpw']+.8*value['fnw'])
            assert math.isclose(calculated,value['dti'],abs_tol=1e-12)
    assert card['holdout_dti']['dti']==holdout['raw_surface_holdout']['scores']['orientation']['dti']
    assert card['holdout_dot_dti']['dti']==holdout['scores']['orientation']['dti']
    pages,errors=check_links(docs)
    assert not errors,'\n'.join(errors)
    for page in pages:
        parser=Links();parser.feed(page.read_text())
        assert not any(urlsplit(link).path.lower().endswith(('.tif','.tiff','.zip')) for link in parser.links), f'{page} exposes a held raster/ZIP link'
    for name in ('index.html','executive-summary.html'):
        text=(docs/name).read_text();parser=Links();parser.feed(text)
        assert 'Download: NOT CLEARED' in text and 'Submit: NO' in text
        assert 'Download for research: OK' not in text
        assert not parser.downloads, f'{name} exposes a download link while the release is held'
        assert text.index('download-panel')<text.index('footer')
    h57b_text=(docs/'h57b.html').read_text();h57b_links=Links();h57b_links.feed(h57b_text)
    assert 'H57-B is on HOLD' in h57b_text and 'NOT CLEARED' in h57b_text
    assert not h57b_links.downloads and f'downloads/{raster.name}' not in h57b_text
    h57k_text=(docs/'h57k.html').read_text();h57k_links=Links();h57k_links.feed(h57k_text)
    assert 'do not download or submit' in h57k_text.lower() and not h57k_links.downloads
    js=(docs/'assets/site.js').read_text()
    assert 'localhost' not in js and '127.0.0.1' not in js
    for name in ('research.html','sources.html','results.html','irregularities.html'):
        assert 'ORGANIZER-CONFIRMED numbers as pasted' not in (docs/name).read_text()
    result=dict(pages_checked=len(pages),tiff_sha256=digest,tiff_bytes=raster.stat().st_size,
                zip_exactly_one_tiff=True,local_format_pass=True,links_pass=True,
                latest_public_main_registry_rasters=total,
                h57k_historical_audit_rasters=audit_count,
                h57k_audit_matches_latest_index=h57k_audit_matches_latest_index,
                h57j_audit_matches_latest_index=True,
                current_card_consistent=True,submission_cleared=False)
    print(json.dumps(result,indent=2))
    return result


def inspect_site(docs):
    """Compatibility helper for the repository's separate site-link smoke test."""
    pages, errors = check_links(Path(docs))
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',action='store_true')
    args=parser.parse_args()
    if args.build:
        from build_site import build
        build()
    check()


if __name__=='__main__':main()
