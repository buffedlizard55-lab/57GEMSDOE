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
    # A historical uniqueness audit is internally consistent with the index IT was
    # run against, which it records itself.  It must not be required to equal the
    # CURRENT index: refreshing the registry (695 -> 706 rasters) would otherwise
    # invalidate every earlier artifact even though nothing about them changed.
    # The audit's own coverage is asserted exactly; drift versus the live index is
    # asserted to be growth only, and reported.
    hist_total=audit['registry_rasters_expected']
    assert hist_total==audit['registry_rasters_checked']==len(audit['rows']),(
        'historical audit is not internally consistent: expected=%s checked=%s rows=%d'%(
            hist_total,audit['registry_rasters_checked'],len(audit['rows'])))
    assert total>=hist_total,'registry index shrank (%d < %d): refresh lost rasters'%(
        total,hist_total)
    registry_drift=total-hist_total
    assert audit['complete_accessible_scan'] and not audit['source_errors']
    assert not audit['unique'] and audit['worst_dot_overlap']>0.70
    assert audit['jaccard_diagnostic_only'] is True
    assert card['correlation_overlap_vs_registry']['jaccard_diagnostic_only'] is True
    assert audit['byte_unique_among_checked'] and audit['pixel_unique_among_checked']
    cur=json.loads((root/'evidence/h57l_uniqueness.json').read_text())
    assert cur['registry_rasters_checked']==cur['registry_rasters_expected']==total,(
        'current candidate scan covered %s/%s of a %d-raster index'%(
            cur['registry_rasters_checked'],cur['registry_rasters_expected'],total))
    assert cur['complete_accessible_scan'],'current scan is not a complete accessible scan'
    cs=cur['comparable_budget_screen']
    assert cs['unique'] and cs['unique_after_certificate'],'operative screen did not clear'
    assert cs['worst_spearman']<=0.90 and cs['worst_overlap']<=0.70 and cs['worst_jaccard']<=0.50
    print('  registry drift: historical audits used %d rasters, live index has %d (+%d); '
          'current candidate scan covers %d/%d'%(hist_total,total,registry_drift,
          cur['registry_rasters_checked'],total))
    snapshots={row['repo']:row['commit'] for row in index['snapshots']}
    assert len(snapshots)==57
    sites=json.loads((root/'evidence/site_inventory.json').read_text())
    assert {row['repo']:row['commit'] for row in sites['repos']}==snapshots
    classification=json.loads((root/'evidence/registry_classification.json').read_text())
    # Same rule: the classification was computed on the historical index.
    assert classification['grid_rasters_checked']==hist_total,(
        'classification checked %s rasters, historical audit used %s'%(
            classification['grid_rasters_checked'],hist_total))
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
    for name in ('leaderboard_snapshot.json','feed_refresh_status.json','attribute_audit_20261010.json',
                 'holdout_scope_reconciliation_20261010.json','session6_hypotheses.json'):
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
    # Download policy is CARD-CONDITIONAL, not absolute.  Session 6 failed closed
    # because nothing was cleared; that blanket ban must not survive a cleared
    # candidate, or the site could never offer the one-click download the brief
    # requires.  The rule now is: a page may carry an active `download` attribute
    # and a raster/ZIP link ONLY if (a) the current run card says download is OK,
    # (b) the page is the submission page, and (c) the link target is the cleared
    # artifact.  Everything else still fails closed, including every link to the
    # retained Session-5 research file.
    card=json.loads((root/'evidence/run_card_h57l.json').read_text())
    cleared_name=Path(card['raster']['submission_name']).name
    download_ok=bool(card['gate_verdicts']['okay_to_download'])
    submit_ok=bool(card['gate_verdicts']['okay_to_submit'])
    allowed_targets={f'downloads/{cleared_name}.tif',f'downloads/{cleared_name}.zip'}
    pages,errors=check_links(docs)
    assert not errors,'\n'.join(errors)
    tiff_or_zip_links=[]
    for page in pages:
        rel=str(page.relative_to(docs))
        parser=Links();parser.feed(page.read_text())
        for value in parser.links:
            lowered=value.lower().split('#',1)[0].split('?',1)[0]
            if lowered.endswith(('.tif','.tiff','.zip')) or 'downloads/' in lowered:
                if download_ok and rel=='submit-h57l.html' and value in allowed_targets:
                    continue
                tiff_or_zip_links.append(f'{rel}: {value}')
        if parser.downloads:
            assert download_ok and rel=='submit-h57l.html',(
                f'active download attribute on {rel} while okay_to_download={download_ok}; '
                f'only the cleared submission page may carry one')
    assert not tiff_or_zip_links,('site must not publish raster/ZIP download links outside the '
        f'cleared submission page ({sorted(allowed_targets)}): '+repr(tiff_or_zip_links))
    assert submit_ok,'run card does not clear submission; the banner must not say otherwise'
    banner_page=(docs/'submit-h57l.html').read_text()
    assert cleared_name in banner_page and card['raster']['tif_sha256'] in banner_page,(
        'submission page does not name the cleared artifact and its sha256')
    for nm in ('index.html','executive-summary.html'):
        txt=(docs/nm).read_text()
        assert 'OK TO DOWNLOAD AND SUBMIT' in txt,f'{nm} is missing the cleared banner'
        assert 'Scope of this banner' in txt,(
            f'{nm} carries both a cleared and an uncleared verdict without scoping them')
    for name in ('index.html','executive-summary.html'):
        text=(docs/name).read_text();parser=Links();parser.feed(text)
        assert 'Download for research: NO' in text and 'Submit to competition: NO' in text
        assert 'NOT OK TO DOWNLOAD OR SUBMIT' in text and 'IR-S6-10' in text
        assert not parser.downloads
        assert text.index('download-panel')<text.index('footer')
    js=(docs/'assets/site.js').read_text()
    assert 'localhost' not in js and '127.0.0.1' not in js
    for name in ('research.html','sources.html','results.html','irregularities.html'):
        assert 'ORGANIZER-CONFIRMED numbers as pasted' not in (docs/name).read_text()
    # Two cards are live and they are about two different artifacts.  Reporting a
    # single hard-coded cleared/uncleared pair (as Session 6 did) made the site
    # summary contradict the page it was checking, so each card is reported under
    # its own name with the artifact it governs.
    result=dict(pages_checked=len(pages),tiff_sha256=digest,tiff_bytes=raster.stat().st_size,
                zip_exactly_one_tiff=True,local_format_pass=True,links_pass=True,
                current_card_consistent=True,
                cards={
                    'session5_relay_bend_research_surface': dict(
                        artifact_sha256=digest,
                        research_download_cleared=False,submission_cleared=False,
                        status='retained for provenance; never cleared'),
                    'h57l_anatomy_candidate': dict(
                        artifact=card['raster']['submission_name'],
                        artifact_sha256=card['raster']['tif_sha256'],
                        research_download_cleared=download_ok,
                        submission_cleared=submit_ok,
                        status=card['verdict']),
                })
    print(json.dumps(result,indent=2))
    return result


def inspect_site(docs):
    """Check local HTML and current hypothesis-review Markdown links."""
    docs=Path(docs).resolve()
    pages,errors=check_links(docs)
    markdown_link=re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+)\)')
    for source in (docs/'research/hypotheses.md',docs/'research/hypotheses_h57.md'):
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
