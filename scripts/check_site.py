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
import re
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
    public_current=json.loads((docs/'data/run_card_current.json').read_text())
    assert card==public_current,'public current-card copy is stale'
    assert card['okay_to_download'] is False and card['okay_to_submit'] is False
    assert card.get('download_permission_status',{}).get('resolution')=='HOLD pending explicit owner decision (IR-S6-10)'
    assert card['verdict']=='negative' and card['submission_slots_used']==0
    assert card['final_dots']['status']=='not_generated' and not card['surface_before_placement']['protocol_pass']
    assert 0<len(card['submission_name'])<=140 and 0<len(card['submission_note'])<=140
    assert card['submission_note_chars']==len(card['submission_note'])
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
    assert card['holdout_dti']['dti']==holdout['raw_surface_holdout']['scores']['orientation']['dti']
    assert card['holdout_dot_dti']['dti']==holdout['scores']['orientation']['dti']
    session7=json.loads((root/'evidence/session7_proximal_holdout.json').read_text())
    session7_public=json.loads((docs/'data/session7_proximal_holdout.json').read_text())
    assert session7==session7_public,'public Session-7 receipt is stale'
    assert session7['evidence_class']=='HOLDOUT-DTI'
    assert session7['evaluator_version']=='gems57-pooled-hide-v2'
    assert session7['scores']['proximal_prune']['withheld_positive_pixels']==11321
    assert session7['paired_differences']['matched_random_prune']['ci95'][0] <= 0 <= session7['paired_differences']['matched_random_prune']['ci95'][1]
    assert session7['holdout_promotion_condition_met'] is False
    assert session7['full_production_surface_built'] is False and session7['production_dots_generated'] is False
    assert session7['candidate_geoTIFF_sha256'] is None and session7['okay_to_download'] is False and session7['okay_to_submit'] is False
    assert session7['historical_holdout_reference']['comparable_for_promotion'] is False
    assert session7['registry_gate']['forward_dot_overlap_implied']==1.0
    assert session7['submission_slots_used']==0
    for name in ('leaderboard_snapshot.json','feed_refresh_status.json','attribute_audit_20261010.json',
                 'holdout_scope_reconciliation_20261010.json','session6_hypotheses.json',
                 'session7_hypotheses.json','session7_registry_precheck.json','session7_review_passes.json'):
        source=root/'evidence'/name
        public_copy=docs/'data'/name
        assert source.is_file() and public_copy.is_file(),f'missing public audit copy: {name}'
        assert source.read_bytes()==public_copy.read_bytes(),f'public audit copy is stale: {name}'
    feed_snapshot=json.loads((root/'evidence/leaderboard_snapshot.json').read_text())
    feed_status=json.loads((root/'evidence/feed_refresh_status.json').read_text())
    assert 'ORGANIZER-PUBLISHED' in feed_snapshot['evidence_class']
    assert feed_snapshot['receipt_attribution_available'] is False
    assert feed_snapshot['organizer_confirmed_submission_score'] is None
    if feed_status.get('ok') is True:
        assert feed_status.get('rows')==len(feed_snapshot['rows'])
    else:
        assert feed_status.get('retained_previous_snapshot') is True
    assert feed_snapshot['top_public_dti']==feed_snapshot['rows'][0]['public_dti']
    session6_hypotheses=json.loads((root/'evidence/session6_hypotheses.json').read_text())
    ranked=session6_hypotheses['ranked']
    assert 3<=len(ranked)<=5 and [item['rank'] for item in ranked]==list(range(1,len(ranked)+1))
    audit=json.loads((root/'evidence/attribute_audit_20261010.json').read_text())
    assert audit['evidence_class'].startswith('DATA-AUDIT') and 'limits' in audit
    reconciliation=json.loads((root/'evidence/holdout_scope_reconciliation_20261010.json').read_text())
    assert reconciliation['current_session5_evidence']['evaluator_version']=='gems57-pooled-hide-v2'
    assert reconciliation['current_session5_evidence']['withheld_positive_pixels']==11321
    irreg=json.loads((root/'evidence/irregularities_current.json').read_text())
    download_ir=[item for item in irreg['irregularities'] if item['id']=='IR-S6-10']
    assert len(download_ir)==1 and 'resolved operationally' in download_ir[0]['status'].lower()
    pages,errors=check_links(docs)
    assert not errors,'\n'.join(errors)
    tiff_or_zip_links=[]
    for page in pages:
        parser=Links();parser.feed(page.read_text())
        for value in parser.links:
            lowered=value.lower().split('#',1)[0].split('?',1)[0]
            if lowered.endswith(('.tif','.tiff','.zip')) or 'downloads/' in lowered:
                tiff_or_zip_links.append(f'{page.relative_to(docs)}: {value}')
        assert not parser.downloads,f'active download attribute on {page.relative_to(docs)}'
    assert not tiff_or_zip_links,'site must not publish raster/ZIP download links while authorization is unresolved: '+repr(tiff_or_zip_links)
    for name in ('index.html','executive-summary.html'):
        text=(docs/name).read_text();parser=Links();parser.feed(text)
        assert 'Download for research: NO' in text and 'Submit to competition: NO' in text
        assert 'NOT OK TO DOWNLOAD OR SUBMIT' in text and 'IR-S6-10' in text
        assert 'S7-1' in text and 'no production surface/dots' in text
        assert 'Paired proximal-minus-random difference' in text
        assert not parser.downloads
        assert text.index('latest-holdout')<text.index('download-panel')<text.index('footer')
    latest=(docs/'session-7-verification.html').read_text()
    assert 'Research verdict: negative' in latest
    assert 'NOT OK TO DOWNLOAD OR SUBMIT' in latest
    assert 'candidate-specific full-registry uniqueness/correlation scan' in latest
    assert 'session7_registry_precheck.json' in latest
    assert 'session7_review_passes.json' in latest
    js=(docs/'assets/site.js').read_text()
    assert 'localhost' not in js and '127.0.0.1' not in js
    for name in ('research.html','sources.html','results.html','irregularities.html'):
        assert 'ORGANIZER-CONFIRMED numbers as pasted' not in (docs/name).read_text()
    result=dict(pages_checked=len(pages),tiff_sha256=digest,tiff_bytes=raster.stat().st_size,
                zip_exactly_one_tiff=True,local_format_pass=True,links_pass=True,
                current_card_consistent=True,research_download_cleared=False,submission_cleared=False)
    print(json.dumps(result,indent=2))
    return result


def inspect_site(docs):
    """Check local HTML and current hypothesis-review Markdown links."""
    docs=Path(docs).resolve()
    pages,errors=check_links(docs)
    markdown_link=re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+)\)')
    for source in (docs/'research/hypotheses.md',docs/'research/hypotheses_h57.md',docs/'research/session7_hypotheses.md'):
        if not source.is_file():
            continue
        for href in markdown_link.findall(source.read_text(encoding='utf-8')):
            url=urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target=(source.parent/unquote(url.path)).resolve()
            if not target.is_relative_to(docs):
                errors.append(f'{source}: local Markdown link escapes site: {href}')
            elif not target.is_file():
                errors.append(f'{source}: broken local Markdown link: {href}')
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
