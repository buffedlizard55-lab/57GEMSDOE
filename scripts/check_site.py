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
    assert card==json.loads((docs/'data/run_card_current.json').read_text()),'public current-card copy is stale'
    assert card['okay_to_download'] is True and card['okay_to_submit'] is False
    assert card['verdict']=='negative' and card['submission_slots_used']==0
    # research download is explicitly scoped and is not a submission clearance (IR-S7A-03)
    scope=card['download_permission_status']
    assert scope['authorized'] is True and scope['scope']=='research download only'
    assert scope['submission_cleared'] is False and scope['file_availability_is_permission'] is False
    assert card['okay_to_submit'] is False
    # fail-closed consistency: a fired gate must be recorded, never cleared here
    registry=card['correlation_overlap_vs_registry']
    assert registry['duplicate_count']>0 and registry['complete_accessible_scan'] is False
    assert registry['worst_dot_overlap']>0.70
    assert 0<len(card['submission_name'])<=140 and 0<len(card['submission_note'])<=140
    assert card['submission_note_chars']==len(card['submission_note'])
    raster=root/card['file'];archive=root/card['zip_file']
    digest=hashlib.sha256(raster.read_bytes()).hexdigest()
    for source in (raster, archive, raster.with_suffix('.json')):
        assert (root/'downloads'/source.name).read_bytes()==source.read_bytes(), 'legacy/root mirror is stale'
    assert digest==card['raster_sha256'],'TIFF changed after its audit'
    receipt=json.loads(raster.with_suffix('.json').read_text())
    assert digest==receipt['sha256'] and receipt['approved_for_weekly_slot'] is False
    assert receipt['note']==card['submission_note'] and receipt['submission_name']==card['submission_name']
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
    assert int((values>0).sum())==card['validator_output']['emitted_positive_pixels']==card['final_dots']
    # the current-candidate registry measurement, pinned to the shipped bytes
    cert=json.loads((root/'evidence/h57m_uniqueness_certificate.json').read_text())
    assert cert['candidate_sha256']==digest,'certificate is for different bytes'
    assert cert['candidate_dots']==card['final_dots']
    assert cert['rasters_measured_this_run']<=cert['registry_rasters_pinned']
    assert cert['literal_reading']['duplicate'] is True and cert['like_for_like_reading']['duplicate'] is True
    assert card['correlation_overlap_vs_registry']['registry_rasters_checked']==cert['rasters_measured_this_run']
    univ=json.loads((root/'evidence/gate_universality.json').read_text())
    assert univ['candidate']==cert['candidate'] and univ['blanket_rasters']>0
    assert univ['forward_firings_blanket']+univ['forward_firings_localised']==univ['forward_firings_total']
    assert univ['rasters_firing_in_both_directions']==0
    assert univ['best_known_control']['forward_overlap_firings']>0
    # local format preflight receipt matches the card
    validation=json.loads((root/'evidence/h57m_validation.json').read_text())
    assert validation['sha256']==digest and validation['all_checks_passed'] is True
    assert card['validator_output']['all_checks_passed'] is True
    # the shipped budget's holdout reading is the nearest measured point, not an interpolation
    emission=json.loads((root/'evidence/h57m_emission.json').read_text())
    assert emission['file']==card['file'] and emission['sha256']==digest
    at={int(p['budget']):p for p in emission['holdout_curve']}
    near=min(at,key=lambda b:abs(b-card['holdout_dti']['budget']))
    assert near==card['holdout_dti']['nearest_measured_budget']
    assert math.isclose(at[near]['holdout_dti'],card['holdout_dti']['dti'],abs_tol=1e-12)
    for point in emission['holdout_curve']:
        assert point['withheld_positive_pixels']==11321
        lo,hi=point['holdout_ci95'];assert 0<=lo<=hi<=1
    assert card['holdout_dot_dti']['budget_curve']==[[int(p['budget']),p['holdout_dti']] for p in emission['holdout_curve']]
    holdout=json.loads((root/'evidence/h57m_holdout.json').read_text())
    for value in holdout['scores'].values():
        assert value['evidence_class']=='HOLDOUT-DTI'
        assert value['withheld_positive_pixels']==11321
    canary=json.loads((root/'evidence/h57m_canary.json').read_text())
    for feature in canary['features'].values():
        assert not feature['leakage_flag'] and feature['discriminative_auc_max']<=.90
    index=json.loads((root/'evidence/registry_refreshed.json').read_text())
    assert index['n_unique_grid_rasters']==695
    snapshots={row['repo']:row['commit'] for row in index['snapshots']}
    assert len(snapshots)==57
    sites=json.loads((root/'evidence/site_inventory.json').read_text())
    assert {row['repo']:row['commit'] for row in sites['repos']}==snapshots
    classification=json.loads((root/'evidence/registry_classification.json').read_text())
    assert classification['auxiliary_inputs']==4
    # the separate pre-placement lane: STOP evidence and its own fail-closed card
    preflight=json.loads((root/'evidence/preflight_anatomy.json').read_text())
    assert preflight==json.loads((docs/'data/preflight_anatomy.json').read_text()),'preflight site copy is stale'
    assert preflight['literal_preplacement_gate']=='STOP'
    assert preflight['certificate']['universal_overlap_blocker']
    assert preflight['certificate']['uncovered_allowed_pixels']==0
    latest=json.loads((root/'evidence/run_card_preflight.json').read_text())
    assert latest==json.loads((docs/'data/run_card_preflight.json').read_text()),'latest site card is stale'
    assert latest['raster_sha256'] is None and latest['okay_to_download'] is False
    assert latest['okay_to_submit'] is False and latest['submission_slots_used']==0
    gate696=json.loads((root/'evidence/uniqueness_session6_full_registry_696.json').read_text())
    assert gate696['registry_rasters_checked']==696 and gate696['duplicate_count']==80
    assert gate696['unique'] is False and gate696['stop_required'] is True
    irreg=json.loads((root/'evidence/irregularities_current.json').read_text())
    ids={i['id']:i for i in irreg['irregularities']}
    assert ids['IR-S6-10']['status'].startswith('RESOLVED OPERATIONALLY')
    assert 'pending explicit owner decision' in ids['IR-S6-10']['status'].lower()
    assert ids['IR-S6-01']['status'].startswith('OPEN')
    assert {'IR-S7A-01','IR-S7A-02','IR-S7A-03'}.issubset(ids)
    # descriptive structure + holdout receipts that the site still publishes
    structure=json.loads((root/'evidence/orientation_structure.json').read_text())
    assert structure['evidence_class']=='HOLDOUT-STRUCTURE (descriptive, not a score)'
    assert structure['model_fit_performed'] is False and structure['dti_evaluated'] is False
    for name in ('orientation_canary','relay_bend_canary'):
        rows=json.loads((root/'evidence'/f'{name}.json').read_text())['features']
        assert all((not v['leakage_flag']) and v['discriminative_auc_max']<=.90 for v in rows.values())
    for name in ('leaderboard_snapshot.json','feed_refresh_status.json','attribute_audit_20261010.json',
                 'holdout_scope_reconciliation_20261010.json','session6_hypotheses.json','preflight_anatomy.json',
                 'run_card_preflight.json','h6_1_proximity_pruning_holdout.json','run_card_session7_h6_1.json','review_passes_h57m.json',
                 'session7_proximal_holdout.json','session7_proximal_hypotheses.json','session7_registry_precheck.json','session7_review_passes.json'):
        source=root/'evidence'/name; public_copy=docs/'data'/name
        assert source.is_file() and public_copy.is_file(),f'missing public audit copy: {name}'
        assert source.read_bytes()==public_copy.read_bytes(),f'public audit copy is stale: {name}'
    feed=json.loads((root/'evidence/leaderboard_snapshot.json').read_text())
    feed_status=json.loads((root/'evidence/feed_refresh_status.json').read_text())
    assert 'ORGANIZER-PUBLISHED' in feed['evidence_class']
    assert feed['receipt_attribution_available'] is False and feed['organizer_confirmed_submission_score'] is None
    if feed_status.get('ok') is True:
        assert feed_status.get('rows')==len(feed['rows'])
    else:
        assert feed_status.get('retained_previous_snapshot') is True
    ranked=json.loads((root/'evidence/session6_hypotheses.json').read_text())['ranked']
    assert 3<=len(ranked)<=5 and [item['rank'] for item in ranked]==list(range(1,len(ranked)+1))
    lane=json.loads((root/'evidence/session7_hypotheses.json').read_text())['ranked']
    assert [item['rank'] for item in lane]==list(range(1,len(lane)+1))
    session7=json.loads((root/'evidence/session7_proximal_holdout.json').read_text())
    assert session7==json.loads((docs/'data/session7_proximal_holdout.json').read_text())
    assert session7['holdout_promotion_condition_met'] is False
    assert session7['candidate_geoTIFF_sha256'] is None
    assert session7['okay_to_download'] is False and session7['okay_to_submit'] is False
    assert session7['submission_slots_used']==0
    paired=session7['paired_differences']['matched_random_prune']
    assert paired['ci95'][0] <= 0 <= paired['ci95'][1]
    cross=session7['cross_branch_context']
    assert cross['prior_h6_1_promotion_rule_passed'] is False
    assert cross['current_comparable_best_after_main_fetch']['evaluator_hashes_match'] is True
    assert cross['current_comparable_best_after_main_fetch']['paired_cross_model_test_performed'] is False
    assert cross['current_comparable_best_after_main_fetch']['dti'] > cross['current_comparable_best_after_main_fetch']['s7_1_proximal_dti']
    proximal_slate=json.loads((root/'evidence/session7_proximal_hypotheses.json').read_text())
    assert proximal_slate['post_run_cross_branch_audit']['action'].startswith('Preserve the original')
    review=json.loads((root/'evidence/session7_review_passes.json').read_text())
    assert review['final_decision']['independent_replication'] is False
    pages,errors=check_links(docs)
    assert not errors,'\n'.join(errors)
    for name in ('index.html','executive-summary.html'):
        text=(docs/name).read_text();parser=Links();parser.feed(text)
        assert 'Download for research: OK' in text and 'Submit to competition: NO' in text
        assert parser.downloads[0]==f'downloads/{raster.name}'
        assert parser.downloads[1]==f'downloads/{archive.name}'
        assert 'Matched pruning did not improve over equal-count random' in text
        assert 'S7-1 download: NO' in text and 'not an independent replication' in text
        assert text.index('download-panel')<text.index('session7-proximal')<text.index('footer')
    latest=(docs/'session-7-verification.html').read_text()
    assert 'Research verdict: negative' in latest
    assert 'S7-1: NEGATIVE FOR PROMOTION' in latest
    assert 'NOT REPOSITORY-NOVEL' in latest
    assert 'session7_proximal_hypotheses.json' in latest
    assert 'session7_review_passes.json' in latest
    assert '0.135204' in latest and '0.101005' in latest
    js=(docs/'assets/site.js').read_text()
    assert 'localhost' not in js and '127.0.0.1' not in js
    for name in ('research.html','sources.html','results.html','irregularities.html'):
        assert 'ORGANIZER-CONFIRMED numbers as pasted' not in (docs/name).read_text()
    result=dict(pages_checked=len(pages),tiff_sha256=digest,tiff_bytes=raster.stat().st_size,
                zip_exactly_one_tiff=True,local_format_pass=True,links_pass=True,
                current_card_consistent=True,submission_cleared=False)
    print(json.dumps(result,indent=2))
    return result


def inspect_site(docs):
    """Check local HTML and the Session-7 research-review Markdown links."""
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
