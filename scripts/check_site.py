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
    public=json.loads((docs/'data/run_card.json').read_text())
    assert card==public,'public card is stale'
    assert card['okay_to_download'] is True
    assert card['verdict'] in ('promote','negative')
    assert card['okay_to_submit'] is (card['verdict']=='promote')
    assert card['submission_slots_used']==0
    assert card['experiments_used']<=3
    assert 0<len(card['submission_name'])<=140 and 0<len(card['submission_note'])<=140
    assert card['submission_note_chars']==len(card['submission_note'])
    dots=card['final_dots']
    assert dots['status']=='generated' and dots['emitted_pixels']>0
    assert card['surface_before_placement']['checked'] is True
    raster=root/card['file'];archive=root/card['zip_file']
    digest=hashlib.sha256(raster.read_bytes()).hexdigest()
    for source in (raster, archive, raster.with_suffix('.json')):
        assert (root/'downloads'/source.name).read_bytes()==source.read_bytes(), 'legacy/root mirror is stale'
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
    assert np.isfinite(values).all(),'submission must be all-finite (portal range error precaution)'
    assert values.min()>=0.0 and values.max()<=1.0,'values must lie in [0,1]'
    with rasterio.open(root/'data/official/labels.tif') as ds:
        known=ds.read(1)>0
    assert not (values[known]>0).any(),'positive predictions on known mask'
    assert int((values>0).sum())==card['validator_output']['emitted_positive_pixels']==dots['emitted_pixels']
    # dual uniqueness screen: operative dot-representation + literal support, both stored
    audit=json.loads((root/'evidence/session7_final_uniqueness.json').read_text())
    assert audit['candidate_file_sha256']==digest
    index=json.loads((root/'evidence/registry_refreshed.json').read_text())
    total=index['n_unique_grid_rasters']
    assert audit['registry_rasters_expected']==audit['registry_rasters_checked']==total
    assert audit['complete_accessible_scan'] and not audit['source_errors']
    assert len(audit['rows'])==total
    assert audit['byte_unique_among_checked'] and audit['pixel_unique_among_checked']
    assert audit['jaccard_diagnostic_only'] is True
    assert card['correlation_overlap_vs_registry']['jaccard_diagnostic_only'] is True
    assert 'literal_support_screen' in audit and 'literal_support_screen' in card['correlation_overlap_vs_registry']
    if card['okay_to_submit']:
        # operative clearance is cross-lane (same-lane succession may fire the
        # representation screen; only byte/pixel identity is a same-lane stop)
        assert card['correlation_overlap_vs_registry']['duplicate_count_dot_representation_other_lanes'] == 0
        assert card['correlation_overlap_vs_registry']['byte_unique_among_checked'] is True
        assert card['correlation_overlap_vs_registry']['pixel_unique_among_checked'] is True
    rows=[r for r in audit['rows'] if 'error' not in r]
    other=[r for r in rows if not str(r.get('submission','')).startswith('57GEMSDOE:')]

    def rep_stop(r):
        return bool(r.get('duplicate_by_rho')
                    or r.get('duplicate_by_overlap_dots', r.get('duplicate_by_overlap', False))
                    or r.get('identical_bytes') or r.get('identical_decoded_predictions'))
    worst_ov=max((r['my_dots_within_3px_of_their_dots'] for r in other),default=0.0)
    worst_rho=max((r['spearman_full_footprint'] for r in other if r['spearman_full_footprint'] is not None),default=0.0)
    assert abs(worst_ov-card['correlation_overlap_vs_registry']['worst_cross_lane_dot_overlap_representation'])<1e-12
    assert abs(worst_rho-card['correlation_overlap_vs_registry']['worst_cross_lane_spearman'])<1e-12
    assert card['correlation_overlap_vs_registry']['duplicate_count_dot_representation_other_lanes']==sum(rep_stop(r) for r in other)
    if card['okay_to_submit']:
        assert worst_ov<=0.70 and worst_rho<=0.90, 'cross-lane drift screen failed'
        assert sum(rep_stop(r) for r in other)==0, 'cross-lane representation screen fired'
        # same-lane succession may fire the representation screen; only identity is a stop
        assert all(not r.get('identical_bytes') and not r.get('identical_decoded_predictions') for r in rows)
    snapshots={row['repo']:row['commit'] for row in index['snapshots']}
    assert len(snapshots)==57
    sites=json.loads((root/'evidence/site_inventory.json').read_text())
    assert {row['repo']:row['commit'] for row in sites['repos']}==snapshots
    # Session-7 experiment receipt: labels, CIs and the predeclared retention rule
    s7=json.loads((root/'evidence/session7_h61_prune.json').read_text())
    assert s7['evidence_class'].startswith('HOLDOUT-DTI')
    for name,value in s7['scores'].items():
        assert value['evidence_class']=='HOLDOUT-DTI'
        assert value['evaluator_version']=='gems57-pooled-hide-v2'
        assert value['withheld_positive_pixels']==11321
        lo,hi=value['ci95'];assert 0<=lo<=hi<=1
        assert math.isclose(value['tpw']+value['fnw'],11321,abs_tol=1e-6)
        calculated=value['tpw']/(value['tpw']+.2*value['fpw']+.8*value['fnw'])
        assert math.isclose(calculated,value['dti'],abs_tol=1e-9)
    du=s7['paired_differences']['unpruned']
    assert du['ci95'][1]<0, 'H6-1 was a strictly negative paired result'
    assert s7['prune_retained_for_final_build'] is False
    assert dots['prune_retained'] is False
    assert card['holdout_dti']['h61_prune_retained'] is False
    # structure + canary on the same draw
    structure=json.loads((root/'evidence/session7_structure.json').read_text())
    assert structure['evidence_class']=='HOLDOUT-STRUCTURE (descriptive, not a score)'
    assert structure['n_withheld']==11321
    canary=json.loads((root/'evidence/session7_canary.json').read_text())
    assert len(canary['features'])==22
    for feature in canary['features'].values():
        assert not feature['leakage_flag'] and feature['discriminative_auc_max']<=.90
    holdout=json.loads((root/'evidence/relay_bend_holdout.json').read_text())
    for scores in (holdout['scores'],holdout['raw_surface_holdout']['scores']):
        for value in scores.values():
            assert value['evidence_class']=='HOLDOUT-DTI'
            assert value['evaluator_version']=='gems57-pooled-hide-v2'
            assert value['withheld_positive_pixels']==11321
            lo,hi=value['ci95'];assert 0<=lo<=hi<=1
            assert math.isclose(value['tpw']+value['fnw'],11321,abs_tol=1e-7)
            calculated=value['tpw']/(value['tpw']+.2*value['fpw']+.8*value['fnw'])
            assert math.isclose(calculated,value['dti'],abs_tol=1e-12)
    assert card['holdout_dti']['dti']==holdout['raw_surface_holdout']['scores']['relay_bend_anatomy']['dti']
    assert card['holdout_dot_dti']['dti']==holdout['scores']['relay_bend_anatomy']['dti']
    pages,errors=check_links(docs)
    assert not errors,'\n'.join(errors)
    for name in ('index.html','executive-summary.html'):
        text=(docs/name).read_text();parser=Links();parser.feed(text)
        assert 'Download GeoTIFF: OK' in text
        if card['okay_to_submit']:
            assert 'Submit to competition: OK' in text
        else:
            assert 'Submit to competition: NO' in text
        assert parser.downloads[0]==f'downloads/{raster.name}'
        assert parser.downloads[1]==f'downloads/{archive.name}'
        assert text.index('download-panel')<text.index('footer')
    js=(docs/'assets/site.js').read_text()
    assert 'localhost' not in js and '127.0.0.1' not in js
    for name in ('research.html','sources.html','results.html','irregularities.html'):
        assert 'ORGANIZER-CONFIRMED numbers as pasted' not in (docs/name).read_text()
    result=dict(pages_checked=len(pages),tiff_sha256=digest,tiff_bytes=raster.stat().st_size,
                zip_exactly_one_tiff=True,local_format_pass=True,links_pass=True,
                current_card_consistent=True,submission_cleared=bool(card['okay_to_submit']))
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
