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
    assert not (docs/'data/leaderboard_snapshot.json').exists(), 'external score snapshot is not project evidence'
    assert not (docs/'data/feed_refresh_status.json').exists(), 'numeric external-score feed must not be published'
    for public_root in (docs, root/'downloads'):
        public_artifacts=[p for p in public_root.rglob('*')
                          if p.is_file() and p.suffix.lower() in {'.tif','.tiff','.zip'}]
        assert not public_artifacts, f'held artifact remains publicly servable: {public_artifacts}'
    card=json.loads((root/'evidence/run_card_current.json').read_text())
    public=json.loads((docs/'data/run_card.json').read_text())
    assert card==public,'public card is stale'
    assert card['okay_to_download'] is False and card['okay_to_submit'] is False
    assert card['download_status']=='HOLD — NOT OK TO DOWNLOAD OR SUBMIT'
    assert card['download_authorization']['research_download'] is False
    assert card['download_authorization']['competition_submission'] is False
    assert card['verdict']=='negative' and card['submission_slots_used']==0
    assert card['final_dots']['status']=='not_generated' and not card['surface_before_placement']['protocol_pass']
    assert 0<len(card['submission_name'])<=140 and 0<len(card['submission_note'])<=140
    assert card['submission_note_chars']==len(card['submission_note'])
    raster=root/card['file'];archive=root/card['zip_file']
    digest=hashlib.sha256(raster.read_bytes()).hexdigest()
    public_raster=docs/'downloads'/raster.name
    public_archive=docs/'downloads'/archive.name
    root_mirror=root/'downloads'/raster.name
    assert not public_raster.exists() and not public_archive.exists(), 'held TIFF/ZIP must not be served from docs'
    assert not root_mirror.exists(), 'held TIFF must not be mirrored at repository root'
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
    assert audit['registry_rasters_expected']==audit['registry_rasters_checked']==total
    assert audit['complete_accessible_scan'] and not audit['source_errors']
    assert len(audit['rows'])==total and not audit['unique'] and audit['worst_dot_overlap']>0.70
    assert audit['jaccard_diagnostic_only'] is True
    assert card['correlation_overlap_vs_registry']['jaccard_diagnostic_only'] is True
    assert audit['byte_unique_among_checked'] and audit['pixel_unique_among_checked']
    snapshots={row['repo']:row['commit'] for row in index['snapshots']}
    assert len(snapshots)==57
    sites=json.loads((root/'evidence/site_inventory.json').read_text())
    assert {row['repo']:row['commit'] for row in sites['repos']}==snapshots
    classification=json.loads((root/'evidence/registry_classification.json').read_text())
    assert classification['grid_rasters_checked']==total
    assert classification['auxiliary_inputs']==4
    structure=json.loads((root/'evidence/orientation_structure.json').read_text())
    relative=structure['relative_strike']
    assert structure['evidence_class']=='HOLDOUT-STRUCTURE (descriptive, not a score)'
    assert sum(relative['n_withheld'])==relative['n_withheld_total']==10811
    assert sum(relative['n_visible_reference'])==relative['n_visible_total']==21321
    assert structure['withheld_positive_pixels']==11321
    assert structure['model_fit_performed'] is False
    assert structure['dti_evaluated'] is False and structure['production_dots_generated'] is False
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
    selected_arm=card['holdout_dti'].get('selected_arm', card['holdout_dot_dti'].get('selected_arm', 'orientation'))
    assert selected_arm in holdout['raw_surface_holdout']['scores'] and selected_arm in holdout['scores']
    assert card['holdout_dti']['dti']==holdout['raw_surface_holdout']['scores'][selected_arm]['dti']
    assert card['holdout_dot_dti']['dti']==holdout['scores'][selected_arm]['dti']
    pages,errors=check_links(docs)
    assert not errors,'\n'.join(errors)
    active_artifact_links=[]
    for page in pages:
        text=page.read_text();parser=Links();parser.feed(text)
        for url in parser.links:
            path=urlsplit(url).path.lower()
            if path.endswith(('.tif','.tiff','.zip')):
                active_artifact_links.append(f'{page}: {url}')
        assert not parser.downloads, f'{page}: HTML download attribute remains'
    assert not active_artifact_links, '\n'.join(active_artifact_links)
    for name in ('index.html','executive-summary.html'):
        text=(docs/name).read_text()
        assert 'HOLD — NOT OK TO DOWNLOAD OR SUBMIT.' in text
        assert 'Download: NOT OK' in text and 'Submit to competition: NO' in text
        assert 'NOT OK TO DOWNLOAD OR SUBMIT' in text
        assert text.index('download-panel')<text.index('footer')
    js=(docs/'assets/site.js').read_text()
    assert 'localhost' not in js and '127.0.0.1' not in js
    for name in ('research.html','sources.html','results.html','irregularities.html'):
        assert 'ORGANIZER-CONFIRMED numbers as pasted' not in (docs/name).read_text()
    result=dict(pages_checked=len(pages),tiff_sha256=digest,tiff_bytes=raster.stat().st_size,
                historical_zip_exactly_one_tiff=True,zip_exactly_one_tiff=True,
                local_format_pass=True,links_pass=True,active_tif_zip_links=0,
                current_card_consistent=True,
                download_authorized=False,submission_cleared=False)
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
