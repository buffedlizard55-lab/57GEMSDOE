#!/usr/bin/env python3
"""Fail-closed local delivery QA: links, actual bytes, range, ZIP, run-card and gate receipts.

Nothing here fits a model, downloads the registry or spends a slot. Every number
is re-derived from the files on disk: if a raster, a receipt or a page drifts out
of agreement with the others, this script fails instead of trusting prose.
Assertions are deliberately *generic* (they follow the current card) rather than
pinned to one session's strings, so a future release cannot satisfy them by
editing text.
"""
from __future__ import annotations
import argparse
import hashlib
from html import escape as htmlescape
from html.parser import HTMLParser
import json
import math
from pathlib import Path
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.ids = set(); self.downloads = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if attrs.get(key): self.links.append(attrs[key])
        if tag == 'a' and 'download' in attrs: self.downloads.append(attrs.get('href', ''))


def check_links(docs):
    errors = []; pages = list(docs.rglob('*.html'))
    for page in pages:
        parser = Links(); parser.feed(page.read_text())
        for value in parser.links:
            url = urlsplit(value)
            if url.scheme or url.netloc or value.startswith(('mailto:', 'data:')): continue
            target = (page.parent / unquote(url.path)).resolve() if url.path else page
            if not target.is_relative_to(docs.resolve()):
                errors.append(f'{page}: local link escapes site: {value}'); continue
            if target.is_dir(): target = target / 'index.html'
            if not target.is_file(): errors.append(f'{page}: broken local link {value}'); continue
            if url.fragment and target.suffix == '.html':
                other = Links(); other.feed(target.read_text())
                if unquote(url.fragment) not in other.ids: errors.append(f'{page}: missing anchor {value}')
    return pages, errors


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(root=ROOT):
    import sys
    sys.path.insert(0, str(root / 'src'))
    import numpy as np
    import rasterio
    from gems57.gates import format_report
    docs = root / 'docs'
    ev = lambda name: json.loads((root / 'evidence' / f'{name}.json').read_text())
    card = ev('run_card_current')
    problems = []

    def need(condition, message):
        if not condition:
            problems.append(message)

    # ---- card internal consistency, then card vs public copy ------------------
    need(card['verdict'] in ('negative', 'promote-candidate'), f"unknown verdict {card['verdict']!r}")
    need(bool(card['okay_to_submit']) == (card['verdict'] == 'promote-candidate'),
         'run-card permission and verdict disagree')
    need(card['okay_to_download'] is True, 'the delivered release must be downloadable')
    need(card['submission_slots_used'] == 0 and card['experiments_used'] == 3,
         'a build never spends a slot, and the protocol caps this task at three experiments')
    need(0 < len(card['submission_name']) <= 140 and 0 < len(card['submission_note']) <= 140,
         'submission name/note must fit the 140-character portal field')
    need(card['submission_note_chars'] == len(card['submission_note']), 'note length mismatch')
    need(json.loads((docs / 'data/run_card.json').read_text()) == card, 'public card is stale')

    # ---- the bytes advertised are the bytes audited ---------------------------
    raster = root / card['file']; archive = root / card['zip_file']
    digest = sha(raster)
    need(digest == card['raster_sha256'], 'TIFF changed after its audit')
    for source in (raster, archive, raster.with_suffix('.json')):
        need((root / 'downloads' / source.name).read_bytes() == source.read_bytes(),
             f'legacy/root mirror is stale: {source.name}')
        need((docs / 'downloads' / source.name).read_bytes() == source.read_bytes(),
             f'site copy is stale: {source.name}')
    receipt = json.loads(raster.with_suffix('.json').read_text())
    need(digest == receipt['sha256'] and receipt['approved_for_weekly_slot'] is False,
         'writer receipt does not match the bytes or authorises a slot')
    need(receipt['note'] == card['submission_note'], 'receipt note differs from the card')
    need(receipt['bytes'] == raster.stat().st_size == card['validator_output']['bytes'],
         'byte count disagreement between receipt, disk and card')
    need(sha(archive) == receipt['zip_sha256'], 'ZIP hash does not match the receipt')
    with zipfile.ZipFile(archive) as zipped:
        need(zipped.namelist() == [raster.name], 'ZIP must contain ONLY one TIFF')
        need(zipped.read(raster.name) == raster.read_bytes(), 'ZIP contents differ from the TIFF')

    # ---- independent format/range re-measurement -------------------------------
    with rasterio.open(root / 'data/official/sample_submission.tif') as ds:
        footprint = np.isfinite(ds.read(1))
    report = format_report(raster, root / 'data/official/sample_submission.tif', footprint=footprint)
    need(report['ok'], f"portal-format report: {report['problems']}")
    with rasterio.open(raster) as ds:
        nodata = ds.nodata
        values = ds.read(1)
    with rasterio.open(root / 'data/official/labels.tif') as ds:
        known = ds.read(1) > 0
    need(nodata is None, 'a nodata tag is not allowed in a [0,1] float32 export')
    need(np.isfinite(values).all(), 'non-finite value inside the raster: the portal range check rejects NaN')
    need(values.min() >= 0.0 and values.max() <= 1.0, 'value outside [0, 1]')
    need(not (values[known] > 0).any(), 'positive predictions on the mapped catalogue')
    dots = int((values > 0).sum())
    need(dots == card['final_dots']['dots'] == card['validator_output']['emitted_positive_pixels'],
         f'dot count disagreement: raster {dots} vs card {card["final_dots"]["dots"]}')
    need(bool(card['validator_output']['all_checks_passed']), 'card validator did not pass')
    need(digest == card['validator_output']['sha256'], 'validator receipt hash drift')

    # ---- both drift-gate phases, re-read from their receipts -------------------
    index = ev('registry_refreshed')
    total = index['n_unique_grid_rasters']
    gate = card['correlation_overlap_vs_registry']['final_dots']
    surface_gate = card['correlation_overlap_vs_registry']['surface_before_placement']
    profile = card['correlation_overlap_vs_registry']['registry_profile']
    for label, audit, expect_hash in (
            ('final dots', ev('h58_uniqueness_final_dots'), digest),
            ('pre-placement surface', ev('h58_uniqueness_surface_before_placement'), digest)):
        need(audit['candidate_file_sha256'] == expect_hash, f'{label}: audit describes different bytes')
        need(audit['registry_rasters_expected'] == audit['registry_rasters_checked'] == total,
             f'{label}: registry scope is not the full manifest ({audit["registry_rasters_checked"]}/{total})')
        need(audit['complete_accessible_scan'] and not audit['source_errors'], f'{label}: incomplete scan')
        need(len(audit['rows']) == total, f'{label}: per-raster rows missing')
        need(audit['jaccard_diagnostic_only'] is True, f'{label}: Jaccard must stay diagnostic')
        need(audit['byte_unique_among_checked'] and audit['pixel_unique_among_checked'],
             f'{label}: candidate is not distinct from every prior')
        need(bool(audit['unique']) == bool(audit['stop_required'] is False), f'{label}: gate flag inconsistency')
        ref = gate if label == 'final dots' else surface_gate
        for key in ('worst_spearman_full_footprint', 'worst_dot_overlap', 'worst_jaccard_dot_sets',
                    'duplicate_count'):
            need(abs(float(audit[key]) - float(ref[key])) < 1e-12,
                 f'{label}: card {key} disagrees with the receipt')
    need(profile['rasters_indexed'] == total and profile['read'] == total,
         'registry support profile does not cover the whole manifest')
    need(profile['missing'] == 0 and profile['sha_mismatch'] == 0, 'registry cache is not fully restored')
    need(bool(card['surface_before_placement']['checked']),
         'the protocol requires the drift gate on the surface BEFORE placement')
    need(card['final_dots']['status'] == 'generated' and dots > 0, 'no final dots were emitted')
    need(bool(card['final_dots']['protocol_pass']) == bool(gate['unique']),
         'final-dot permission does not follow the gate receipt')
    if not gate['unique']:
        need(card['okay_to_submit'] is False, 'a tripped drift gate must forbid submission')
    need(gate['registry_rasters_checked'] == total, 'card registry scope narrowed itself')

    # ---- holdout receipt: recompute the metric from its own terms --------------
    holdout = ev('h58_holdout')
    structure = ev('h58_structure')
    canary = ev('h58_canary')
    n_pos = structure['withheld_positive_pixels']
    need(n_pos == card['structure_measurements']['withheld_positive_pixels'],
         'card withheld-positive count drifted from the structure receipt')
    for scores in (holdout['scores'], holdout['soft_surface_holdout']['scores']):
        for value in scores.values():
            need(value['evidence_class'] == 'HOLDOUT-DTI', 'mislabelled holdout evidence class')
            need(value.get('evaluator_version', holdout['evaluator_version']) == holdout['evaluator_version'],
                 'evaluator drift inside one receipt')
            need(value['withheld_positive_pixels'] == n_pos, 'withheld positive count disagreement')
            lo, hi = value['ci95']; need(0 <= lo <= hi <= 1, 'CI not ordered or out of range')
            need(math.isclose(value['tpw'] + value['fnw'], n_pos, abs_tol=1e-6),
                 'TPw + FNw must equal the withheld positive count')
            calculated = value['tpw'] / (value['tpw'] + .2 * value['fpw'] + .8 * value['fnw'])
            need(math.isclose(calculated, value['dti'], abs_tol=1e-9), 'DTI does not recompute from its terms')
    arm = card['holdout_dot_dti']['arm']
    need(arm == holdout['production_arm'], 'card ships a different arm than the declared production arm')
    need(math.isclose(card['holdout_dot_dti']['dti'], holdout['scores'][arm]['dti'], abs_tol=1e-12),
         'card dot DTI drifted from the receipt')
    need(math.isclose(card['holdout_surface_dti']['dti'],
                      holdout['soft_surface_holdout']['scores'][arm]['dti'], abs_tol=1e-12),
         'card surface DTI drifted from the receipt')
    need(holdout['split_version'] == card['holdout_dot_dti']['split_version'], 'split version drift')
    for feature in canary['features'].values():
        need(not feature['leakage_flag'] and feature['discriminative_auc_max'] <= .90,
             'a feature exceeded the leakage-canary threshold')
    need(canary['flagged'] == [] and card['leakage_canary']['flags'] == [],
         'a canary flag exists but the card claims a clean screen')
    need(card['leakage_canary']['features'] == len(canary['features']),
         'card canary feature count drifted from the receipt')
    rel = structure['structure']['relative_strike']
    need(sum(rel['n_withheld']) == rel['n_withheld_total'] <= n_pos, 'strike histogram does not sum to its total')
    need(structure['evidence_class'].startswith('HOLDOUT-STRUCTURE'),
         'structure receipt must be labelled descriptive, never a score')
    need(structure['withheld_positive_pixels'] == n_pos, 'nested structure count disagrees')
    for key in ('dti', 'holdout_dti', 'promote'):
        need(key not in structure, f'structure receipt claims a score field {key!r}')
    law = card['width_law']
    need(law['n_bins'] >= 4 and law['gamma_ci95'][0] < law['gamma_ci95'][1], 'width-law receipt malformed')
    need(math.isclose(card['structure_measurements']['fraction_pos_in_kept_zone'],
                      structure['fraction_pos_in_kept_zone'], abs_tol=1e-12),
         'budget shrink factor drifted between card and receipt')
    need(0 < card['final_dots']['cap'] <= 4 * 10_000 * 1.0, 'dot cap is not the declared lane formula')
    need(dots <= card['final_dots']['cap'], 'emitted dots exceed the declared cap')

    # ---- pages: labels, links, ordering, and no orphan numbers ----------------
    pages, errors = check_links(docs)
    need(not errors, 'broken links: ' + '\n'.join(errors))
    for name in ('index.html', 'executive-summary.html'):
        text = (docs / name).read_text(); parser = Links(); parser.feed(text)
        need(('Download for research: OK' in text) == bool(card['okay_to_download']),
             f'{name}: download permission label does not follow the card')
        need(('Submit to competition: OK' in text) == bool(card['okay_to_submit']),
             f'{name}: submission permission label does not follow the card')
        need(parser.downloads[:2] == [f'downloads/{raster.name}', f'downloads/{archive.name}'],
             f'{name}: the TIFF must be the first download link, then the ZIP')
        need(text.index('download-panel') < text.index('footer'), f'{name}: download panel is not above the fold')
        # the page escapes HTML, so compare against the escaped form of the same string
        need(htmlescape(card['submission_name']) in text and htmlescape(card['submission_note']) in text,
             f'{name}: the exact paste-ready name and note are missing')
        need(f"{dots:,}" in text, f'{name}: advertised dot count is not the measured dot count')
        need(card['raster_sha256'] in text, f'{name}: SHA256 of the delivered bytes is missing')
    js = (docs / 'assets/site.js').read_text()
    need('localhost' not in js and '127.0.0.1' not in js, 'browser code must not call the sandbox host')
    for name in ('research.html', 'sources.html', 'results.html', 'irregularities.html'):
        need('ORGANIZER-CONFIRMED numbers as pasted' not in (docs / name).read_text(),
             f'{name}: reuses the forbidden score label')

    result = dict(pages_checked=len(pages), tiff_sha256=digest, tiff_bytes=raster.stat().st_size,
                  dots=dots, zip_exactly_one_tiff=True, local_format_pass=True,
                  links_pass=not errors, current_card_consistent=True,
                  registry_rasters_checked=gate['registry_rasters_checked'],
                  final_dots_gate_unique=bool(gate['unique']),
                  surface_gate_checked=True, submission_cleared=bool(card['okay_to_submit']))
    if problems:
        raise SystemExit('site QA FAILED:\n- ' + '\n- '.join(problems))
    print(json.dumps(result, indent=2))
    return result


def inspect_site(docs):
    """Compatibility helper for the repository's separate site-link smoke test."""
    pages, errors = check_links(Path(docs))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    if args.build:
        from build_site import build
        build()
    check()


if __name__ == '__main__':
    main()
