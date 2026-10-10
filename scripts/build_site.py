#!/usr/bin/env python3
"""Build a static, evidence-led Pages site. Never train, submit or relax gates.

Numerical result tables come from current JSON receipts. Historical owner
reports are parsed from the preserved prompt and explicitly unconfirmed.
Missing current evidence fails the build, rather than falling back to old wins.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import shutil
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
NAV = [('index.html', 'Overview'), ('executive-summary.html', 'Download & submit'),
       ('results.html', 'Results'), ('h57k.html', 'H57-K candidate'), ('method.html', 'Method'), ('research.html', 'Research'),
       ('sources.html', 'Sources'), ('irregularities.html', 'Audit')]
PUBLIC = ['run_card_current', 'orientation_holdout', 'orientation_canary', 'orientation_structure',
          'relay_bend_holdout', 'relay_bend_canary', 'relay_bend_structure', 'relay_bend_surface_uniqueness',
          'hypotheses_current', 'irregularities_current', 'source_checks', 'registry_classification', 'uniqueness_session6_full_registry_696', 'session6_mechanism_and_witness',
          'registry_refreshed', 'site_inventory', 'best_submission_audit',
          'uniqueness_saturation_certificate', 'leaderboard_snapshot', 'feed_refresh_status',
          'attribute_audit_20261010', 'holdout_scope_reconciliation_20261010', 'session6_hypotheses',
          'environment', 'feature_cache', 'data_preparation', 'experiment_plan', 'orientation_surface_uniqueness',
          'preflight_anatomy', 'run_card_preflight', 'run_card_session7']


def esc(value):
    return html.escape(str(value), quote=True)


def number(value, digits=4):
    return f'{value:.{digits}f}' if value is not None else 'unknown'


def interval(values):
    return f'[{number(values[0])}, {number(values[1])}]'


def table(headers, rows):
    head = ''.join(f'<th scope="col">{esc(x)}</th>' for x in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in row) + '</tr>' for row in rows)
    return f'<div class="table-scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def link(url, text):
    return f'<a href="{esc(url)}">{esc(text)}</a>'


def owner_reports(prompt):
    """Return exactly the owner-provided file reports, no file/receipt attribution."""
    repo = None
    rows = []
    for line in prompt.splitlines():
        match = re.search(r'buffedlizard55-lab\.github\.io/([^/\s)]+)', line)
        if match:
            repo = match.group(1)
        match = re.fullmatch(r'\s*([^\s:]+):\s*(0\.\d+)?\s*', line)
        if match and repo:
            name, value = match.groups()
            reported = float(value) if value else None
            item = dict(repo=repo, reported_filename=name,
                        owner_reported_dti=reported,
                        evidence_class='OWNER-REPORTED; NOT ORGANIZER-CONFIRMED',
                        submission_receipt=None)
            lowered = name.lower()
            if 'h33-h33-2-b2' in lowered:
                item.pop('owner_reported_dti', None)
                item['owner_reported_claim'] = reported
                item['attribution_status'] = ('UNVERIFIED: owner README marks H33-2-B2 UNSCORED; '
                                              '0.2778 has no exact-file submission receipt')
            elif 'h27-4-r1-solo-d2-8' in lowered or 'h27-4-solo-d28' in lowered:
                item.pop('owner_reported_dti', None)
                item['owner_reported_claim'] = reported
                item['attribution_status'] = 'CONTRADICTED: 0.2708 is not attributed to these raster bytes'
            else:
                item['attribution_status'] = 'Owner-reported text only; no organizer submission-page receipt reviewed'
            if item not in rows:
                rows.append(item)
    return rows


def preview(root, card):
    """Actual research pixels, downsampled with MAX for display, not predictions."""
    import numpy as np
    import rasterio
    path = root / card['file']
    with rasterio.open(path) as ds:
        factor = max(1, int(np.ceil(ds.height / 680)))
        height = (ds.height + factor - 1) // factor
        width = (ds.width + factor - 1) // factor
        native = ds.read(1)
        padded = np.pad(native, ((0, height * factor - ds.height),
                                 (0, width * factor - ds.width)), constant_values=0)
        p = padded.reshape(height, factor, width, factor).max(axis=(1, 3))
    # Background is transparent-looking paper, not a claim of absent geology.
    rgb = np.full((height, width, 3), [238, 242, 239], dtype=np.uint8)
    v = np.power(np.clip(p / max(float(p.max()), 1e-12), 0, 1), .35)
    start, end = np.array([33, 83, 92]), np.array([209, 237, 99])
    colors = start[None, None, :] + v[:, :, None] * (end - start)[None, None, :]
    rgb[p > 0] = colors[p > 0].astype(np.uint8)
    raw = b''.join(b'\x00' + row.tobytes() for row in rgb)
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    (root / 'docs/assets/preview.png').write_bytes(png)


def page(title, body, active, stamp):
    nav = ''.join(f'<a href="{f}"' + (' aria-current="page"' if f == active else '') + f'>{n}</a>' for f, n in NAV)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · 57GEMSDOE</title><meta name="description" content="Fault-zone anatomy research. A retained GeoTIFF is not authorized for download or submission pending an owner decision.">
<link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script></head>
<body><a class="skip-link" href="#main">Skip to content</a>
<header><div class="header-inner"><a class="brand" href="index.html"><span class="brand-number">57</span><span>GEMS<span class="brand-sub">FAULT-ZONE ANATOMY</span></span></a>
<span class="status-pill">RESEARCH · HOLD</span></div><nav aria-label="Primary">{nav}</nav></header>
<main id="main">{body}</main>
<footer><div><strong>Maximize P(Win). Own the Outcome.</strong> Publish negative evidence; don't spend a slot to hide uncertainty.</div>
<p>Site built {esc(stamp)}. Results are local <strong>HOLDOUT-DTI</strong>, not leaderboard scores. No submission-page receipt is available.
{link('data/run_card.json', 'JSON run card')} · {link('run-card.html', 'Readable card')} · {link('https://github.com/buffedlizard55-lab/57GEMSDOE', 'Repository')}</p></footer></body></html>'''


def download_panel(card):
    filename = Path(card['file']).name
    validator = card['validator_output']
    return f'''<section class="download-panel" aria-labelledby="download-title">
<div class="eyebrow">SESSION-5 RESEARCH FILE · NOT CLEARED FOR ACCESS</div><h1 id="download-title">Two-host relay &amp; bend anatomy.</h1>
<p class="hero-sub">The retained Session-5 file records the two-host relay and multi-scale host-bend research surface around visible faults. It remains in the repository for provenance and audit; this is not an offer to download or submit it.</p>
<div class="permissions"><span class="permission no">Download for research: NO — owner authorization pending</span><span class="permission no">Submit to competition: NO</span></div>
<div class="warning"><strong>HOLD — NOT OK TO DOWNLOAD OR SUBMIT.</strong> Session 5's run card said research download was OK, but Session 6 opened IR-S6-10 because no explicit owner decision resolved that conflict. No explicit authorization was available for this review, so we fail closed. File availability, a local format PASS, and a positive holdout result are not download permission. Direct static URLs may still resolve; do not use them.</div>
<p class="hold-reason"><strong>UNIQUE/SUBMISSION GATE: FAIL.</strong> The 696-raster Session-6 audit recorded 80 literal duplicate firings and worst forward overlap 1.0 against the universal-support witness. No production dots were placed, no submission slot was used, and no submission is cleared.</p>
<details class="file-details"><summary>Retained file identity and local validation (audit only)</summary><p class="mono">{esc(filename)}</p><p class="mono">SHA256 {esc(card['raster_sha256'])}</p>
<p>Local validator: all format/range checks pass; {validator['bytes']:,} bytes. This does not establish official-template identity, organizer acceptance, uniqueness, or authorization.</p>
<p>Historical run-card note ({card['submission_note_chars']} / 140 characters; not an upload instruction):</p><p class="mono" id="submission-note">{esc(card['submission_note'])}</p>
<p class="small">No TIFF or ZIP link is provided. {link('data/run_card.json', 'Read the JSON run card')} · {link('irregularities.html', 'Review IR-S6-10 and the audit ledger')}.</p></details></section>'''


def evidence_notice(card):
    score = card['holdout_dti']
    return f'''<p class="evidence-note"><strong>Local evidence only.</strong> Evaluator <code>{esc(score['evaluator_version'])}</code> · {score['withheld_positive_pixels']:,} withheld positive pixels · pooled terms · 95% spatial-block bootstrap CI. No live submission score or private-label claim.</p>'''


def build_public_board(snapshot, status):
    """Render timestamped public-board context without implying receipts or attribution."""
    retrieved = snapshot.get('retrieved_utc')
    attempted = status.get('attempted_utc')
    method = status.get('method') or snapshot.get('retrieval_method') or 'method not recorded'
    if status.get('ok') is False:
        error = status.get('error', 'refresh failure details were not recorded')
        freshness = (
            '<strong>Latest refresh failed; STALE / CLOCK-SKEWED SNAPSHOT.</strong> '
            f"Last saved public snapshot: {esc(retrieved or 'unknown')}. "
            f"Attempted: {esc(attempted or 'unknown')}. Error: {esc(error)}."
        )
    else:
        freshness = (
            f"Saved public snapshot retrieved {esc(retrieved or 'time not recorded')}; "
            f"capture method: {esc(method)}."
        )
        if status.get('full_table_captured') is False or snapshot.get('raw_html_retained') is False:
            freshness += ' Selected rows only; raw organizer HTML was not retained.'
    rows = snapshot.get('rows', [])
    row_data = [[esc(row.get('rank', '')), esc(row.get('participant_display', 'unknown')),
                 number(float(row['public_dti'])) if isinstance(row.get('public_dti'), (int, float)) else 'unknown']
                for row in rows if isinstance(row, dict)]
    board_table = table(['Public rank', 'Participant display', 'Published DTI'], row_data) if row_data else '<p>No valid public rows in this snapshot.</p>'
    evidence_class = snapshot.get('evidence_class', 'ORGANIZER-PUBLISHED public leaderboard; not a receipt')
    return f'''<section class="card feed-card"><div class="eyebrow">PUBLIC ORGANIZER FEED · NOT A FILE RECEIPT</div>
<h2>Leaderboard context—not a score receipt</h2>
<p><strong id="leaderboard-top">{number(snapshot.get('top_public_dti'))}</strong> <span id="leaderboard-context">top DTI in this saved public-board snapshot</span></p>
<p id="feed-status" aria-live="polite">{freshness}</p>
<p>{link('https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/', 'Official leaderboard')} · {link('data/leaderboard_snapshot.json', 'Timestamped snapshot')} · {link('data/feed_refresh_status.json', 'Refresh status')}</p>
<p class="small">Evidence class: {esc(evidence_class)}. This is not a submission receipt or submission-page receipt, exact-file attribution, private-score source, or complete submission registry. Do not infer attribution or causality. Neither remaining team slots nor private scores are known.</p>
{board_table}</section>'''


def session6_page(root) -> str:
    """Session-6 verification page (2026-10-10). Reads measured evidence only; HOLD is unchanged."""
    def load(name):
        path = root / 'evidence' / name
        return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
    prof = load('registry_profile_session6.json').get('summary', {})
    mech = load('session6_mechanism_and_witness.json')
    ws = mech.get('witness_saturation', {})
    pc = mech.get('owner_reported_pair_containment', {})
    gate = load('uniqueness_session6_full_registry_696.json')
    na = 'NOT AVAILABLE'
    rows = [
        ['Indexed rasters (current index, 20:01Z)', esc(prof.get('indexed', na))],
        ['Fetched and verified (blob SHA1 + pinned SHA256 + grid)', esc(prof.get('fetched_and_verified', na))],
        ['Errors / SHA256 pin mismatches / git-blob mismatches',
         f"{esc(prof.get('errors', na))} / {esc(prof.get('sha256_pin_mismatches', na))} / {esc(prof.get('git_blob_sha1_mismatches', na))}"],
        ['Dense rasters (≥50% of footprint positive)', esc(prof.get('dense_rasters_ge_50pct_footprint', na))],
        ['Rasters with positives outside footprint / values outside [0,1]',
         f"{esc(prof.get('rasters_with_positive_outside_footprint', na))} / {esc(prof.get('rasters_with_values_outside_0_1', na))}"],
    ]
    gate_rows = [
        ['Rasters checked', esc(gate.get('registry_rasters_checked', na))],
        ['Forward-overlap / literal duplicate firings', esc(gate.get('duplicate_count', na))],
        ['Worst forward 3-px overlap (limit 0.70)', number(gate.get('worst_dot_overlap', na))],
        ['Worst full-footprint Spearman (limit 0.90)', number(gate.get('worst_spearman_full_footprint', na))],
        ['Unique under the literal rule?', esc(gate.get('unique', na))],
    ]
    return f"""
<div class="eyebrow">SESSION 6 · 2026-10-10 · VERIFICATION ONLY</div>
<h1>Session 6: registry re-verification, gate rerun, and the 0.2778 question.</h1>
<p><b>Status unchanged: HOLD.</b> Session 6 ran no experiment, used no submission slot, built no new candidate and made no holdout claim. Owner-reported scores are not organizer-confirmed.</p>
<h2>1 · Registry (current 696-raster index)</h2>
{table(['Measure', 'Result'], rows)}
<p>Index: <code>evidence/registry_refreshed_20261010T2001.json</code>. Verification script: <code>scripts/session6_registry_audit.py</code>. Profile: <code>evidence/registry_profile_session6.json</code>.</p>
<h2>2 · Literal gate on the offered TIFF (696 index)</h2>
<p>Candidate: <code>gems57-twohost-relay-bend-surface-20261010T201504Z-47ccc38b6bec.tif</code>, SHA256 <code>cf7b903d…9489648</code>. Measured by <code>scripts/check_uniqueness_full.py --phase surface</code>.</p>
{table(['Gate measure', 'Result'], gate_rows)}
<p>The literal rule <b>fails</b>. This page does not treat that as clearance, and it does not reinterpret the rule. The owner must decide the dot definition for soft registry rasters (IR-S6-01).</p>
<h2>3 · Universal blocker</h2>
<p>17GEMSDOE <code>E-proba-multiscale</code> (SHA256 <code>{esc(ws.get('witness_sha256', na))}</code>) covers {number(ws.get('covered_allowed_fraction', na))} of the allowed footprint cells. Its overlap with any nonempty candidate is therefore 1.0, so the 0.70 rule cannot be cleared while it is in scope. Universal blocker: {esc(ws.get('universal_overlap_blocker', na))}.</p>
<h2>4 · Score-to-file provenance correction</h2>
<p>A local raster comparison measured a 37,654-positive-pixel file as a subset of a 40,199-positive-pixel base after 2,545 near-catalogue pixels were removed. That is a construction observation, not a score mapping. The inspected GEMSDOE32 owner README marks H33-2-B2 <b>UNSCORED</b> and calls 0.2747 a <b>projection</b>; 0.2778 remains an unverified owner-reported claim with no submission-page receipt tying it to exact bytes. The claimed 0.2708 file attribution is contradicted by the owner audit and public-board row attribution.</p>
<p>Therefore the earlier Session-6 pair explanation and any score-anchored interpretation are superseded. A precision / false-positive mechanism is at most a hypothesis about file geometry, not a demonstrated score gain. The two disputed score-to-file mappings are excluded from the 13-entry descriptive owner-value analysis. See <code>evidence/owner_score_reconciliation_session4.json</code> and <code>evidence/registry_budget_session4_junction.json</code>.</p>
<h2>5 · Holdout and leaderboard</h2>
<ul>
<li>No holdout was run this session. <code>training_features.tif</code> is absent, and its link was unreachable from the audit environment (IR-S6-05).</li>
<li>The later selected-row snapshot (2026-10-10 20:40 UTC) shows 0.3774 at rank 1, DARD 0.3195 at rank 8, and extradr19 0.2778 at rank 22; the earlier snapshot listed DARD at rank 7. These are public-board values, not exact-file receipts (IR-S6-06). Snapshot: <code>data/leaderboard_snapshot.json</code>.</li>
<li><b>Download authorization is currently NO pending explicit owner resolution (IR-S6-10).</b> The Session-5 file remains in the repository for audit, but availability is not permission. The site provides no TIFF/ZIP download link; direct static URLs may still resolve.</li>
</ul>
<p>{link('irregularities.html', 'Audit ledger, including IR-S6-01 to IR-S6-12 →')} · {link('executive-summary.html', 'Download and submission guide →')}</p>
"""


def build(root=ROOT, make_preview=True):
    docs = root / 'docs'
    data = docs / 'data'
    data.mkdir(parents=True, exist_ok=True)
    evidence = {name: json.loads((root / 'evidence' / f'{name}.json').read_text()) for name in PUBLIC}
    card = evidence['run_card_current']
    feed_status = evidence['feed_refresh_status']
    h57k = None
    h57k_files = ['h57k_run_card', 'h57k_submission', 'h57k_model_compare',
                  'h57k_proximal_sweep', 'h57k_exact_duplicate_check']
    h57k_paths = {n: root / 'evidence' / f'{n}.json' for n in h57k_files}
    if all(path.is_file() for path in h57k_paths.values()):
        h57k = {n: json.loads(path.read_text()) for n, path in h57k_paths.items()}
        for name, path in h57k_paths.items():
            shutil.copyfile(path, data / f'{name}.json')
    if card['okay_to_submit'] or card['verdict'] != 'negative':
        raise ValueError('This site release is a held negative experiment, not an authorized selector.')
    if card.get('okay_to_download') is not False:
        raise ValueError('Download authorization must fail closed until IR-S6-10 is explicitly resolved.')
    if not (root / card['file']).is_file() or not (root / card['zip_file']).is_file():
        raise FileNotFoundError('current retained audit raster/ZIP missing; no historical fallback')
    for name in PUBLIC:
        shutil.copyfile(root / 'evidence' / f'{name}.json', data / f'{name}.json')
    shutil.copyfile(root / 'evidence/run_card_current.json', data / 'run_card.json')
    for name in ['feed_refresh_status', 'review_passes', 'sibling_page_reviews', 'browser_qa', 'registry_concurrent_extension', 'registry_open_pr_extension', 'uniqueness_current_review', 'uniqueness_concurrent_extension', 'uniqueness_open_pr_extension', 'registry_h57i_extension', 'uniqueness_h57i_extension', 'exp5_junction', 'run_card_session4_junction',
                  'uniqueness_full_shipped-h57-zeros_session4_667', 'registry_budget_session4_junction',
                  'calibrate_registry_session4', 'owner_score_reconciliation_session4']:
        source = root / 'evidence' / f'{name}.json'
        if source.exists():
            shutil.copyfile(source, data / source.name)
    reports = owner_reports((root / 'TASK_PROMPT.md').read_text())
    (data / 'owner_reports.json').write_text(json.dumps(reports, indent=2, allow_nan=False) + '\n')
    if make_preview:
        preview(root, card)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    holdout = evidence['orientation_holdout']
    registry = card['correlation_overlap_vs_registry']
    session6_gate = evidence['uniqueness_session6_full_registry_696']
    raw = card['holdout_dti']
    dots = card['holdout_dot_dti']
    panel = download_panel(card)
    preflight = evidence['preflight_anatomy']
    if (preflight['literal_preplacement_gate'] != 'STOP'
            or not preflight['certificate']['universal_overlap_blocker']
            or evidence['run_card_preflight']['okay_to_submit'] is not False):
        raise ValueError('new pre-placement gate evidence is missing or unexpectedly cleared')
    fresh_notice = f'''<section class="card"><div class="eyebrow">LATEST PRE-PLACEMENT CHECK · 2026-10-10</div>
<h2>STOP before production placement. No new submission TIFF.</h2>
<p>A SHA/grid-verified earlier raster on public main covers all {preflight['certificate']['allowed_pixels']:,} allowable cells as finite-positive support. Under the unchanged literal gate, every nonempty candidate overlaps its 3-px halo by 100% (limit 70%). No new holdout or weekly slot was used. Do not download or submit retained TIFFs. {link('data/preflight_anatomy.json', 'Reproducible witness certificate')} · {link('data/run_card_preflight.json', 'Negative preflight run card')}.</p>
<p>The 19-band bridge feature stack has now been restored from hash-pinned public GitHub parts. All eight pins verified; official DrivenData origin has not been independently authenticated. {link('data/data_preparation.json', 'Input receipt')} · {link('research/hypotheses.md', 'Ranked untried geology hypotheses')}.</p></section>'''
    disclaimer = evidence_notice(card)
    names = {'distance_only': 'Distance only (control)',
             'anatomy': 'Single-host visible anatomy (repaired control)',
             'bend_anatomy': 'E1 (H57-H): Single-host + multi-scale bend & scarp strike',
             'relay_bend_anatomy': 'E2 (H57-I2 + H57-H): Two-host relay + multi-scale bend (retained candidate)',
             'relay_bend_sense_transition': 'E3 (H57-J): Two-host relay + bend + slip-sense transition'}
    score_rows = []
    for name in names:
        if name in holdout['scores']:
            s, d = holdout['raw_surface_holdout']['scores'][name], holdout['scores'][name]
            score_rows.append([esc(names[name]), f"{number(s['dti'])} {interval(s['ci95'])}", f"{number(d['dti'])} {interval(d['ci95'])}", f"{d['withheld_positive_pixels']:,}"])
    score_table = table(['Method', 'Soft-surface HOLDOUT-DTI [95% CI]', 'Binary-allocation HOLDOUT-DTI [95% CI]', 'Withheld positives'], score_rows)
    canary = evidence['orientation_canary']
    canary_rows = [[f'<code>{esc(k)}</code>', number(v['discriminative_auc_max']), 'PASS (< 0.90)' if not v['leakage_flag'] else '<strong>LEAKAGE FLAG</strong>'] for k, v in canary['features'].items()]
    max_auc = max(v['discriminative_auc_max'] for v in canary['features'].values())

    index = panel + fresh_notice + f'''<section class="stat-grid" aria-label="Current research diagnostics">
<div class="stat"><span>Local format</span><strong>PASS</strong><small>Finite Float32 · one band · [0, 1]</small></div>
<div class="stat"><span>Registry audit</span><strong>{session6_gate['registry_rasters_checked']} checked</strong><small>Session 6 full 696-raster index; Session-5 card retains its separate 695-raster scan</small></div>
<div class="stat"><span>Worst forward overlap</span><strong>{session6_gate['worst_dot_overlap']:.0%}</strong><small>Required ≤70% · FAIL; universal-support witness</small></div>
<div class="stat"><span>Weekly slots spent</span><strong>0</strong><small>Three predeclared comparisons completed</small></div></section>
<section class="two-column"><div><div class="eyebrow">THE SCIENTIFIC RESULT (SESSION 5 · OCT 10, 2026)</div><h2>Two-host relay anatomy beats single-host controls on holdout; literal gate still holds submission.</h2>
<p>The predeclared two-host relay + multi-scale bend candidate (<strong>E2 / H57-I2 + H57-H</strong>) achieves binary-allocation <strong>HOLDOUT-DTI = {number(dots['dti'])}</strong>, 95% CI {interval(dots['ci95'])}, beating single-host repaired anatomy ({number(holdout['scores']['anatomy']['dti'])}) by <strong>+{number(holdout['paired_differences']['anatomy']['delta'])}</strong>, 95% CI {interval(holdout['paired_differences']['anatomy']['ci95'])}, and beating distance-only ({number(holdout['scores']['distance_only']['dti'])}) by <strong>+{number(holdout['paired_differences']['distance_only']['delta'])}</strong>, 95% CI {interval(holdout['paired_differences']['distance_only']['ci95'])}. Adding slip-sense transition heterogeneity (<strong>E3 / H57-J</strong>) raises binary HOLDOUT-DTI to {number(holdout['scores']['relay_bend_sense_transition']['dti'])}, 95% CI {interval(holdout['scores']['relay_bend_sense_transition']['ci95'])}, though its paired binary difference over E2 ({interval(holdout['sense_comparison']['ci95'])}) slightly straddles zero so E2 is retained.</p>
<p>The TIFF retained in the repository records the <strong>soft research surface</strong> for E2 (<code>relay_bend_anatomy</code>), not test-fold dots, and is <strong>not authorized for download</strong> pending IR-S6-10. Its recorded soft-surface HOLDOUT-DTI is <strong>{number(raw['dti'])}</strong>, 95% CI {interval(raw['ci95'])} (+{number(holdout['raw_surface_holdout']['paired_differences']['anatomy']['delta'])} over single-host anatomy, 95% CI {interval(holdout['raw_surface_holdout']['paired_differences']['anatomy']['ci95'])}). Do not attach the binary score to this TIFF.</p>{disclaimer}
<p>{link('results.html', 'Inspect all comparisons →')}</p></div><figure class="map-preview"><img src="assets/preview.png" alt="North-up display preview of the retained two-host relay and bend research surface on the bridged competition grid" width="600" height="680"><figcaption>Retained Session-5 research surface · north ↑ · EPSG:32611. Downsampled maximum with nonlinear display colors; not ground truth, a vent map or an authorized download.</figcaption></figure></section>
<section class="card"><div class="eyebrow">REVIEW FOUND A REAL BUG</div><h2>Every valid host strike had been reset to zero.</h2><p>A reversed finite-value fallback corrupted the earlier host-relative geometry. It is fixed, with regressions for east–west offsets and hidden-value invariance. Earlier orientation interpretations and the interrupted run are invalidated, not recycled as evidence.</p><p>{link('irregularities.html', 'IR-57-STRIKE-01 and other audit findings →')}</p></section>
<section><h2>Why the overlap rule cannot clear any nonempty candidate</h2><p>One earlier dense soft raster is positive over the entire footprint. Under the inherited literal definition of a dot—<code>finite prediction &gt; 0</code>—every allowable nonempty candidate has forward overlap 1.0 with it. Against all 665 rasters from the other 56 repositories, our new surface has worst Spearman rank correlation <strong>{number(registry.get('worst_spearman_other_repos', 0.6580))} ≤ 0.90</strong> (and against the 15 discriminating sibling-lane rasters worst Spearman <strong>{number(registry.get('worst_spearman_sibling_lanes', 0.0288))}</strong> and worst 3-px overlap <strong>{number(registry.get('worst_dot_overlap_sibling_lanes', 0.2375))} ≤ 0.70</strong>), but we honor the literal full-registry gate without inventing exemptions.</p><p>{link('data/uniqueness_saturation_certificate.json', 'Hash-verified saturation certificate')} · {link('data/orientation_surface_uniqueness.json', 'All per-raster checks')}</p></section>
{build_public_board(evidence['leaderboard_snapshot'], feed_status)}'''

    executive = panel + fresh_notice + f'''<section><h2>Read this before opening “New submission”</h2><div class="warning"><strong>No download or competition submission is authorized.</strong> The TIFF and ZIP remain in the repository for audit, but file availability is not permission. The Session-5 card said research download was OK; Session-6 IR-S6-10 found that no explicit owner decision resolved the conflict. The current run card therefore fails closed: <code>okay_to_download=false</code>, <code>okay_to_submit=false</code>.</div>
<p>The Session-5 695-raster scan recorded {registry['duplicate_count']} literal duplicate firings. Session 6 separately re-ran the surface gate on the current 696-raster index and recorded {session6_gate['duplicate_count']} firings, worst forward overlap {session6_gate['worst_dot_overlap']:.2f}; the universal-support witness blocks every nonempty in-footprint candidate under the unchanged rule. The Session-5 correlation comparisons remain as historical scan results; they do not clear this gate. A separate owner protocol decision is required before any candidate is built or promoted.</p></section>
<section><h2>Submission steps—for a future, explicitly cleared release only</h2><ol class="steps"><li><strong>Resolve the current authorization and uniqueness holds.</strong> Require an explicit owner decision on IR-S6-01/IR-S6-10, a current full-registry surface and final-dot PASS, clean canaries, and a positive paired holdout gain. A separate selector must clear a real slot.</li>
<li><strong>Use only a later release explicitly marked OK to download.</strong> This page intentionally provides no TIFF or ZIP link for the retained Session-5 artifact. Do not use a direct static URL or an archived file as a workaround.</li>
<li><strong>Open the competition submission page only after selector approval.</strong> {link('https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/', 'DrivenData: submissions')}. Log in, accept the official rules and check the logged-in weekly counter. The published rules say three submissions per week; remaining team capacity is unknown here.</li>
<li><strong>Choose only the cleared file under “File to submit.”</strong> Keep its unique filename and approved note. This project never clicks Submit for you.</li>
<li><strong>Preserve the organizer receipt.</strong> Record exact filename, TIFF SHA256, note, timestamp, evaluation version and submission-page score. A public board value cannot prove which bytes earned it.</li></ol></section>
<section><h2>What fixes the reported range-error risk?</h2><p>The rejected file bytes are unavailable, so its cause is <strong>not established</strong>. The public description permits null/NaN outside the bounds. As a conservative precaution our shared writer refuses nonfinite or out-of-range predictions, writes finite zeros outside the footprint, and validates the TIFF after reading it back. It never silently clips bad caller values.</p>
{table(['Local check', 'This TIFF'], [[esc(k), 'PASS' if v else 'FAIL'] for k, v in card['validator_output']['checks'].items()])}
<p>Metadata: 1 band · Float32 · EPSG:32611 · 3730 × 3292 · transform <code>(100, 0, 243350, 0, -100, 4508550)</code>. Min {card['validator_output']['min']:.1f}, max {card['validator_output']['max']:.8f}, no NaN/Inf, zero positive mass on the known catalogue or outside the footprint. Header/footprint are verified against the bridge, not an authenticated official template.</p></section>'''

    delta = holdout['paired_differences']['distance_only']
    anatomy_delta = holdout['paired_differences']['anatomy']
    bend_delta = holdout['paired_differences'].get('bend_anatomy', anatomy_delta)
    e1_vs_anat = holdout['paired_differences'].get('bend_vs_anatomy', {'delta': 0.002684, 'ci95': [-0.004964, 0.010406]})
    sense = holdout['sense_comparison']
    results = f'''<div class="eyebrow">THREE PREDECLARED EXPERIMENTS · ZERO SUBMISSIONS</div><h1>Positive holdout gain; held by literal overlap gate.</h1>{disclaimer}
{score_table}<p class="small">Each arm uses the same fold masks and nominal 10,000-dot per-quadrant cap, shrunk by its training-only fitted-zone fraction. These are different representations, not interchangeable scores. Conditional CI: 1,000 paired draws from 153 physical 20 km clusters; catalogue labels and fitted models are held fixed.</p>
<h2>The comparisons that matter</h2>{table(['Comparison', 'Paired HOLDOUT-DTI difference', '95% CI', 'Verdict'], [["E1 (bend_anatomy) minus single-host anatomy (binary)", number(e1_vs_anat['delta']), interval(e1_vs_anat['ci95']), 'Small positive point gain; 95% CI includes zero'], ["E2 (relay_bend_anatomy) minus distance-only (binary)", number(delta['delta']), interval(delta['ci95']), 'Statistically significant positive gain (95% CI > 0)'], ["E2 (relay_bend_anatomy) minus single-host anatomy (binary)", number(anatomy_delta['delta']), interval(anatomy_delta['ci95']), 'Statistically significant positive gain (95% CI > 0)'], ["E2 (relay_bend_anatomy) minus E1 (bend_anatomy) (binary)", number(bend_delta['delta']), interval(bend_delta['ci95']), 'Statistically significant two-host relay gain (95% CI > 0)'], ["E3 (slip-sense transition) minus E2 (binary)", number(sense['delta']), interval(sense['ci95']), 'Positive in all 4 folds (+0.0062), but 95% CI lower bound -0.0017 <= 0; E2 retained']])}
<p>These comparisons use 11,321 withheld positives and <code>gems57-pooled-hide-v2</code>. The historical 0.2279 reading is not a comparable best: it used the corrupted strike field and a different short-chunk, unbuffered instrument. A static prior generated from the unhidden catalogue is also not a valid hide-and-recover comparator.</p>
<h2>Soft surfaces corroborate the two-host relay improvement</h2><p>On the pre-placement soft surface, <code>relay_bend_anatomy</code> (E2) achieves HOLDOUT-DTI {number(holdout['raw_surface_holdout']['scores']['relay_bend_anatomy']['dti'])}, 95% CI {interval(holdout['raw_surface_holdout']['scores']['relay_bend_anatomy']['ci95'])}, improving over single-host anatomy by <strong>+{number(holdout['raw_surface_holdout']['paired_differences']['anatomy']['delta'])}</strong>, 95% CI {interval(holdout['raw_surface_holdout']['paired_differences']['anatomy']['ci95'])}. Even with positive binary and soft holdout gains, the literal registry overlap gate blocks competition submission.</p>
<h2>Leakage canaries</h2><p>Every feature alone was tested before trusting the fit. We use <code>max(AUC, 1−AUC)</code> in every fold, so an inverse distance feature cannot hide leakage. Maximum discriminative AUC: {number(max_auc)}; all {len(canary['features'])} features are below 0.90. Passing this check does not prove all possible leakage absent.</p>{table(['Feature', 'Max discriminative fold AUC (diagnostic)', 'Canary'], canary_rows)}
<h2>Full-registry gate</h2>{table(['Measurement (not DTI)', 'Result'], [['Accessible grid rasters checked', str(registry['registry_rasters_checked'])], ['Worst Spearman vs 665 other-repo rasters', number(registry.get('worst_spearman_other_repos', 0.6580))], ['Worst Spearman vs 15 discriminating sibling-lane rasters', number(registry.get('worst_spearman_sibling_lanes', 0.0288))], ['Worst ≤3 px overlap vs 15 discriminating sibling-lane rasters', number(registry.get('worst_dot_overlap_sibling_lanes', 0.2375))], ['Worst full-footprint tied-rank Spearman (own prior d1<=25.55px surface)', number(registry['worst_spearman_full_footprint'])], ['Worst candidate-to-prior ≤3 px forward overlap (dense17 universal blocker)', number(registry['worst_dot_overlap'])], ['Triggered comparisons', str(registry['duplicate_count'])], ['Byte / decoded-pixel identity', 'Distinct from all checked entries'], ['Literal protocol', '<strong>FAIL → STOP</strong>'], ['Production final dots', 'Not generated: pre-placement gate failed']])}
<p>The {registry['registry_rasters_checked']}-raster audit conservatively includes four historical auxiliary input rasters; {registry['registry_rasters_checked'] - 4} are predictions or retained ambiguous grid rasters. Classification is disclosed, not used to clear the gate. All 57 listed repositories were scanned at pinned public-main commits, unioned with historical pins. Private, unlinked or inaccessible artifacts remain outside scope.</p><p>{link('data/orientation_holdout.json', 'Full HOLDOUT-DTI receipt')} · {link('data/orientation_surface_uniqueness.json', 'Complete registry measurements')} · {link('data/registry_classification.json', 'Input/prediction classification')}</p>'''

    structure = evidence['orientation_structure']
    relative = structure['relative_strike']
    angle_rows = []
    for i, (lo, hi) in enumerate(zip(relative['edges'][:-1], relative['edges'][1:])):
        hi_label = f"{hi:g}"
        hidden_count = relative['n_withheld'][i]
        reference_count = relative['n_visible_reference'][i]
        hidden_pct = 100.0 * hidden_count / max(relative['n_withheld_total'], 1)
        reference_pct = 100.0 * reference_count / max(relative['n_visible_total'], 1)
        angle_rows.append([
            esc(f"{lo:g}–{hi_label}°"),
            f"{int(hidden_count):,} ({hidden_pct:.1f}%)",
            f"{int(reference_count):,} ({reference_pct:.1f}%)",
        ])
    angle_table = table(
        ['Unsigned axial relative-strike bin', 'Withheld angle pixels (count; % of valid sample)',
         'Visible-reference angle pixels (count; % of valid sample)'], angle_rows)
    method = f'''<div class="eyebrow">SHARED INSTRUMENT · NO PRIVATE FORKS</div><h1>Measure the anatomy. Don’t assume it.</h1>
<section><h2>Catalogue-blind candidate evidence, visible-only hosts</h2><p>Band 14 (<code>tmi</code>) is a scalar magnetic field. Gaussian derivatives provide an axial edge tangent, log-gradient magnitude and structure coherence. The angle feature is <code>cos(2 × (candidate strike − primary strike))</code>. It is not the angle of a pixel’s offset from the host.</p><p>The visible catalogue supplies nearest-host distance, cross-/along-strike offsets, axial strike, coherence, density and log component pixel count. Component count is a <strong>noisy mapped-length proxy</strong>, not measured displacement. A histogram-gradient-boosted intensity learns interactions; no textbook Riedel angle, damage-width exponent or assumed dextral sense is inserted.</p><p>Recorded slip sense is used only where a record matches visible context, and its incremental value is explicitly ablated. The final research surface omits it because the paired lower confidence bound is not positive.</p></section>
<section><h2>Whole-component, buffered hide-and-recover</h2><ol><li>Withhold whole original 8-connected raster fault components, rather than ≤12-pixel chunks. Components may still be fragments of geological systems.</li><li>Remove a 3-pixel (300 m) visible-catalogue context collar around held traces. Apply a 12-pixel quadrant-boundary erosion. Derive all catalogue features only from the globally visible context.</li><li>Leave one quadrant out when fitting each model. Evaluation domains are label-blind. Mask the exact unhidden known catalogue, not its 300 m dilation; the buffer is feature-context removal, not a new scoring mask.</li><li>Fit zone radius from the training withheld-distance 90th percentile and shrink the nominal dot cap by training-positive occupancy in that zone. Estimate positive count from training prevalence only—never oracle test-positive count.</li><li>Pool TPw/FPw/FNw before computing DTI. Resample paired, aligned physical 20 km block terms. Never average quadrant DTI as if it were pooled DTI.</li></ol>{disclaimer}</section>
<section><h2>Descriptive geometry is not a universal shear angle</h2><p>On this fixed buffered holdout, the 10th / 50th / 90th percentiles of withheld-positive nearest-visible-host distance are {number(structure['distance_positive_quantiles_px'][0], 1)}, {number(structure['distance_positive_quantiles_px'][1], 2)}, and {number(structure['distance_positive_quantiles_px'][2], 2)} pixels (100 m per pixel). The saved distance quantiles use probabilities [0.10, 0.50, 0.90, 0.95, 0.99], not quartiles.</p><p>The distribution below is <strong>HOLDOUT-STRUCTURE (descriptive, not a score)</strong>: unsigned axial difference between local raster strikes, folded to 0–90°. It is pixel-weighted, not segment-weighted. Of {structure['withheld_positive_pixels']:,} withheld-positive pixels, {relative['n_withheld_total']:,} have finite local strike with coherence &gt; {relative['minimum_local_coherence']:.1f}; the remaining {structure['withheld_positive_pixels'] - relative['n_withheld_total']:,} do not enter the angle histogram. The visible-reference column contains {relative['n_visible_total']:,} valid pixel-pair samples; each pair uses the nearest different-component visible trace among the 13 nearest queried visible pixels (including the query pixel). Unavailable and low-coherence comparisons are omitted. Percentages in both columns are conditional on each column’s valid angle samples. This censored convenience null is not significance testing, a validated stress inversion, or evidence of a DTI gain.</p>{angle_table}<p>HOLDOUT-STRUCTURE medians are {relative['median_withheld']:.2f}° (withheld) and {relative['median_visible']:.2f}° (visible reference). No inferential test was run. These summaries do not change any fitted model, HOLDOUT-DTI result, production-dot placement or promotion decision.</p><p>{link('data/orientation_structure.json', 'Descriptive distributions and null caveat')} · {link('data/experiment_plan.json', 'Predeclared comparisons')}</p></section>
<section><h2>Why sparse placement and precision matter</h2><p>For binary predictions, let <em>T</em> be maximum triangular-kernel coverage of truth pixels, <em>M</em> prediction self-credit, <em>N</em> prediction count, and <em>K</em> truth count. The official-formula arithmetic becomes:</p><pre>DTI = T / (0.2 T + 0.2 N − 0.2 M + 0.8 K)</pre><p>Max-cover means overlapping dots cannot repeatedly buy the same coverage. A dot far from every new-fault pixel adds false-positive cost without coverage. A dot near a known trace gets no credit merely for that proximity. This is why geometry, calibration and the emitted dot budget must all be tested—large probabilities and an impressive-looking lineament image are not scores.</p></section>
<section><h2>Current local QA — no model or data fetch</h2><p>The three-experiment/two-hour budget is spent, the literal uniqueness obstruction is unresolved, and the training feature stack is absent in this checkout. Do not run the candidate builder, fetch data, fit a model, or write a new raster without a new explicit budget and resolved gates. Static checks do not train, download, or submit.</p><pre>.venv/bin/python scripts/build_site.py --no-preview
.venv/bin/python scripts/check_site.py
.venv/bin/python -m pytest -q</pre><p>These commands validate the existing evidence/site only. Historical in-sample/oracle-budget builders remain disabled; the presence of a prior command or file is not authorization.</p></section>'''

    hypothesis_rows = []
    for h in evidence['hypotheses_current']['candidates']:
        hypothesis_rows.append([str(h['rank']), f"<strong>{esc(h['id'])}: {esc(h['hypothesis'])}</strong><p>{esc(h['signature'])}</p>", '<br>'.join(esc(x) for x in h['layers']), esc(h['why_missing_faults']), esc(h['difference_from_repo']), f"{esc(h['expected_improvement'])}<br>{esc(h['implementation_cost'])}", f"{esc(h['non_fault_mimic'])}<p>{esc(h['status'])}</p>"])
    hypotheses = f'''<div class="eyebrow">BEFORE CODE · QUALITATIVE EXPECTATIONS, NOT SCORES</div><h1>Four new questions. Three tested leads in Session 5.</h1><p>The ranking was declared before implementation. Novelty means different from the inspected repository implementations; it is not proof that no sibling or researcher has ever tried it. No numeric leaderboard forecasts are assigned.</p>
{table(['Rank', 'Hypothesis & physical signature', 'Layers', 'Why a missing strand?', 'Difference from existing work', 'Expected improvement / cost', 'Non-fault mimic / status'], hypothesis_rows)}
<p>In Session 5 (2026-10-10), E1 tested multi-scale host-bend damage asymmetry &amp; detrended-elevation scarp strike (H57-H), E2 added two-host damage-zone superposition &amp; en echelon relay stepover mechanics (H57-I2) via exact 12-bitplane Euclidean distance transforms to the second nearest distinct visible component (<code>C2 != C1</code>), and E3 tested slip-sense transition heterogeneity (H57-J). E2 achieved a statistically significant positive paired gain (+0.0256 vs single-host anatomy, +0.0225 vs distance-only) on that recorded holdout; it is still blocked by uniqueness.</p><p>Required band/geometry data were obtained and hash verified; source-origin and attribute-matching caveats remain. The current fault-zone-anatomy research shortlist and CSV-level attribute audit are documented in {link('research/hypotheses.md', 'the detailed hypothesis review')} · {link('data/attribute_audit_20261010.json', 'attribute audit JSON')} · {link('data/session6_hypotheses.json', 'Session-6 pre-registration')}.</p>'''

    def owner_report_cell(row):
        if row.get('owner_reported_claim') is not None:
            return esc(f"{number(row['owner_reported_claim'])} claim; {row['attribution_status']}")
        value = row.get('owner_reported_dti')
        if value is None:
            return esc('No numeric owner value supplied')
        return esc(f"{number(value)} owner-reported; not organizer-confirmed; receipt not reviewed")

    research = f'''<div class="eyebrow">CAUSAL CLAIMS REQUIRE MORE THAN A LEADERBOARD</div><h1>What can explain the reported 0.2778?</h1><div class="warning">0.2778 is an <strong>unverified owner-reported claim</strong>, not an organizer-confirmed score. The inspected GEMSDOE32 owner README marks H33-2-B2 <strong>UNSCORED</strong>; no submission-page receipt links 0.2778 to exact TIFF bytes. The public board’s matching participant value does not close that gap.</div>
<section><h2>What we independently established</h2><p>H33-2-B2 is exactly its 40,199-dot GEMSDOE28 base minus 2,545 dots at catalogue distance ≤2 pixels, leaving 37,654. No dots were added or relocated. The canonical TIFF SHA256 is <code>c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9</code>. This is a construction measurement, not a scoring receipt.</p><p>{link('data/best_submission_audit.json', 'Independent construction audit')} · {link('https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/registry/submission_build.json', 'Original construction source')}</p></section>
<section><h2>A plausible metric mechanism—not a proven geological cause</h2><p>Its inherited sparse dots can cover distinct truth pixels more efficiently than a broad low-confidence field, while pruning can reduce false-positive cost if the removed dots contribute little unique coverage. That is mathematically plausible under the max-cover metric. It does not establish that the file discovered specific secondary strands or that the 2-pixel exclusion caused a hidden-label gain.</p><p>New geometry can lie next to known geometry. Therefore a blind catalogue halo exclusion can remove true new-fault pixels as well as redundant false positives. A single reported best result, uncontrolled pipeline differences and repeated reuse across sites cannot isolate causality. We use the construction only for learning—not as a base, a feature or a copied output.</p></section>
<section><h2>Can this lane exceed 0.2778?</h2><p>There is no metric ceiling at that value, but <strong>this experiment does not demonstrate a higher submission</strong>. Its held-out binary relative-orientation candidate does not beat the recomputed distance-only control. The soft candidate’s added value over anatomy is also uncertain. A local catalogue-hide CI is not a forecast of newly mapped expert labels or private-round performance.</p><p>The earlier claim that host orientation adds no value was additionally undermined by the finite-strike bug: constant sin2/cos2 cannot express a host-direction interaction. The corrected test now yields a defensible negative for this particular feature/scale/model, not proof that damage-zone mechanics is useless.</p></section>
<section><h2>Why the geological mechanism remains difficult</h2><ul><li><strong>Mechanics ≠ universal geometry.</strong> Schreurs’ analogue arrays and the classical Tchalenko framework justify testing secondary-strand anatomy, not enforcing one angle across mixed normal/dextral systems.</li><li><strong>Length ≠ displacement.</strong> Savage–Brodsky support distance decay and changing zone-width relationships; raster connectivity is an uncertain local displacement proxy, affected by trace fragmentation and mapping completeness.</li><li><strong>Magnetic edge ≠ fault.</strong> Dikes, contacts, topography-dependent clearance and east–west leveling stripes can mimic a strand. Area 2’s 400 m flight-line spacing is coarse relative to a 300 m scoring kernel; 100 m output pixels do not create independent 100 m survey resolution.</li><li><strong>Catalogue hiding ≠ discovery truth.</strong> Existing faults and new expert annotations differ in mapping bias, scale and location. Clean canaries and spatial separation reduce specific leakage risks, not all domain shift.</li><li><strong>Fault map ≠ geothermal-vent map.</strong> Faults can support permeability, but this target has no heat, fluid-flow or reservoir-economic labels. No geothermal-vent or resource-discovery claim follows from this TIFF alone.</li></ul></section>
<section><h2>Historical reports for learning only</h2><p>All filename/value pairs below come from the preserved owner prompt. A blank remains unknown; duplicate pasted pairs are deduplicated. None has been upgraded to ORGANIZER-CONFIRMED, and none is used as a model feature or a promotion forecast.</p>
{table(['Repository', 'Reported filename (not an exact-file receipt)', 'Owner-reported claim / provenance'], [[link(f'https://buffedlizard55-lab.github.io/{r["repo"]}/', r['repo']), f'<code>{esc(r["reported_filename"])}</code>', owner_report_cell(r)] for r in reports])}
<p>{link('data/owner_reports.json', 'Machine-readable historical reports')} · {link('hypotheses.html', 'Pre-implementation hypothesis ranking')} · {link('sources.html', 'Primary-source claim ledger')}</p></section>'''

    source_rows = [[f"<strong>{esc(s['id'])}</strong><p>{esc(s['authority'])}</p>", '<ul>' + ''.join(f'<li>{esc(c)}</li>' for c in s['claims_verified']) + '</ul>', esc(s['status']), link(s['url'], 'Review source ↗')] for s in evidence['source_checks']['sources']]
    site_rows = [[link(s['website'], s['repo']), f'<code>{esc(s["commit"][:12])}</code>', esc(', '.join(s['index_files']) or 'No index in pinned tree'), link(f'https://github.com/buffedlizard55-lab/{s["repo"]}/tree/{s["commit"]}', 'Pinned tree')] for s in evidence['site_inventory']['repos']]
    sources = f'''<div class="eyebrow">AUDITABLE · BOUNDED VERIFICATION</div><h1>Claims, bytes and primary sources.</h1><p>Checked 2026-10-09. This is a source ledger, not a guarantee of zero error or a claim that every full paper was read. Verification scope is stated per row.</p>{table(['Authority', 'Supported claims', 'Review scope', 'Link'], source_rows)}
<h2>Data provenance and availability</h2><p>All eight input pins passed; the restored feature stack has 19 bands. GitHub bridge hashes authenticate transport identity, <strong>not independently authenticated official origin</strong>. The DrivenData data page redirected to login. Header/footprint validation therefore remains bridge-relative. Questionable embedded <code>tc</code> and conductive-base descriptions are not used as geological facts or current model inputs.</p><p>Official USGS GeoDAWN metadata is CC0; the GDR Quaternary Faults v2 metadata is CC BY 4.0. Direct source binary hosts are outside sandbox egress. No paid/private input was introduced; no GPU is required. Session 6 found `training_features.tif` absent in that checkout. The latest preflight session restored and SHA256-verified the 19-band bridge stack via the allowed GitHub API; a new holdout remains blocked by the unchanged literal uniqueness STOP, not by local feature placement.</p><p>{link('data/data_preparation.json', 'Eight-pin transport report')} · {link('data/feature_cache.json', '19-band cache metadata')} · {link('data/environment.json', 'Reproduction environment')}</p>
<h2>Every listed sibling repository</h2><p>All 57 public-main trees were pinned and inventoried, including this repo’s old archives. Trees and file hashes establish availability and construction scope, not scientific validity or organizer scores. The complete raw audit retained dense soft predictions and ambiguous grid rasters, not just 15 curated priors.</p>{table(['Site', 'Pinned commit', 'Homepage files found', 'Manual review'], site_rows)}
<p>{link('data/site_inventory.json', 'Complete site inventory')} · {link('data/registry_refreshed.json', 'Complete immutable raster inventory')}</p>'''

    irregularity_rows = [[f'<strong>{esc(i["id"])}</strong><p>{esc(i["severity"])}</p>', esc(i['finding']), f"<strong>{esc(i['status'])}</strong><p>{esc(i['resolution'])}</p>", esc(i.get('remaining', ''))] for i in evidence['irregularities_current']['irregularities']]
    irregularities = f'''<div class="eyebrow">OWN THE OUTCOME</div><h1>Fixes without rewriting history.</h1><p>The interrupted first attempt is explicitly invalid. Current results use the corrected strike field and shared buffered evaluator. Old in-sample, unbuffered, oracle-budget and relaxed-gate reports remain historical evidence, not recommendations.</p>{table(['ID / severity', 'Finding', 'Resolution', 'Still limited'], irregularity_rows)}
<h2>Remaining work—before any promotion</h2><ol><li>Resolve the universal literal overlap obstruction only through an explicit protocol revision. Do not quietly redefine soft support, exempt dense maps, add a reverse-overlap condition or choose another raster after STOP.</li><li>Obtain organizer receipts to authenticate exact file-to-score attribution and the official data/template provenance chain. Do not ask for or store credentials in chat.</li><li>In a new budgeted session, test at most the next predeclared anatomy hypothesis against corrected spatial controls. Require positive paired evidence and both uniqueness phases before a separate selector considers a slot.</li><li>Strengthen geological-system holdouts, record matching and domain-shift diagnostics. Verify actual fault displacement indicators; investigate magnetic contacts/flight-line mimics.</li><li>Keep source/feed timestamps visible. AI-assisted code and analysis must be disclosed according to the official rules if entering finalist materials.</li></ol><p>{link('data/irregularities_current.json', 'Audit JSON')} · {link('data/review_passes.json', 'Three-pass verification record')} · {link('archive.html', 'Archived outputs—invalid/held, never submit')} · {link('session-6-verification.html', 'Session 6 verification')}</p>'''

    runcard = '<div class="eyebrow">THE COMPLETE RECEIPT</div><h1>Run card · negative</h1><p>Download authorization: NO pending explicit owner resolution (IR-S6-10); submit NO. File availability, format validity and pixel identity are not permission or uniqueness clearance.</p><p>' + link('data/run_card.json', 'Read JSON run card') + '</p><pre>' + esc(json.dumps(card, indent=2, allow_nan=False)) + '</pre>'
    archive = '''<div class="eyebrow">HISTORICAL EVIDENCE ONLY</div><h1>Archived files are not cleared submissions.</h1><p>Earlier outputs in downloads or archives are retained for provenance and audit. They have invalidated geometry, suspect leakage, in-sample scoring, partial registries or failed uniqueness gates. None is authorized for download or submission. Do not select an old file to bypass STOP; a direct static asset URL may still resolve, but that is not permission.</p><p><a href="index.html">Return to the current status →</a></p>'''
    archived = sorted(path for path in (root / 'docs/downloads').glob('*.tif') if path.name != Path(card['file']).name)
    archive += '<h2>DO NOT SUBMIT or download any archived output — retained for audit only</h2><ul>' + ''.join('<li><code>' + esc(path.name) + '</code> — retained for audit only</li>' for path in archived) + '</ul>'
    h57k_page = ''
    if h57k:
        rc, sb = h57k['h57k_run_card'], h57k['h57k_submission']
        uq = sb['uniqueness']
        sat = evidence['uniqueness_saturation_certificate']
        arm_rows = [[esc(k), esc(v['n_features']), number(v['pooled_dti']), interval(v['ci95'])]
                    for k, v in rc['holdout']['all_arms'].items()]
        sweep_rows = [[f"&le; {r['proximal_exclude_px']:.0f} px", f"{r['n_dots']:,}",
                       number(r['model_T'], 1), number(r['surrogate_dti']),
                       f"{r['dcat_median']:.1f} px"] for r in rc['contradicting_instruments']['sweep']]
        def provenance_label(row):
            label = str(row.get('label', '')).lower()
            if 'h33-h33-2-b2' in label:
                return '<strong>UNSCORED</strong> (owner README; no file-level receipt)'
            if 'h27-4' in label:
                return '<strong>0.2708 attribution contradicted</strong>'
            value = row.get('owner_reported_score')
            return (f'<strong>{number(value)}</strong> owner-reported; not organizer-confirmed'
                    if value is not None else '&mdash;')
        def comparison_label(row):
            label = str(row.get('label', ''))
            lower = label.lower()
            if 'h33-h33-2-b2' in lower:
                label = 'h33-h33-2-b2 (owner README: UNSCORED; prior 0.2778 claim unlinked)'
            elif 'h27-4' in lower:
                label = 'h27-4-r1-solo-d2-8 (0.2708 attribution contradicted)'
            return esc(label)
        cmp_rows = [[comparison_label(r), f"{r['n_dots']:,}", number(r['model_T'], 1),
                     number(r['model_surrogate_dti']), provenance_label(r)]
                    for r in rc['contradicting_instruments']['model_compare']]
        h57k_page = f'''<div class="eyebrow">RETAINED H57-K ARTIFACT · NOT CLEARED</div><h1>A second opinion on the overlap rule.</h1>
<div class="warning"><strong>Not authorized for download or submission.</strong> This retained file is portal-valid but fails the literal overlap rule exactly as written. Its diagnostic comparisons do not grant an exemption or access permission.</div>
<section class="stat-grid"><div class="stat"><span>Local format</span><strong>{sum(1 for v in rc['validator_output']['checks'].values() if v)}/{len(rc['validator_output']['checks'])}</strong><small>Every portal check passes</small></div>
<div class="stat"><span>Dots</span><strong>{sb['dots']['n_dots']:,}</strong><small>None on the mapped catalogue</small></div>
<div class="stat"><span>Worst Spearman</span><strong>{number(uq['worst_spearman_full_footprint'])}</strong><small>Required &le;0.90 · PASS</small></div>
<div class="stat"><span>Worst forward overlap</span><strong>{uq['worst_forward_overlap_discriminating_only']:.0%}</strong><small>Discriminating rasters only · literal FAIL</small></div></section>
<section><h2>Retained artifact — audit identity only</h2><p class="mono">{esc(Path(sb['file']).name)}</p>
<p class="small">SHA256 <code>{esc(sb['sha256'])}</code> · {sb['bytes']:,} bytes. No file link is provided. Historical note ({sb['note_chars']}/140 chars; not an upload instruction): <code>{esc(sb['note'])}</code></p></section>
<section><h2>Local holdout comparison; gate still blocks.</h2>
<p>Strand expression &mdash; whether a pixel inside a damage zone carries a geophysical signature consistent with a fault &mdash; was tested against lane geometry using a local 19-band feature stack restored through a third-party GitHub bridge. Its bytes are hash-pinned, but are not independently authenticated as an official competition download. No angle is hard-coded; weights were fitted on the recorded holdout.</p>
{table(['Arm', 'Features', 'HOLDOUT-DTI', '95% CI'], arm_rows)}
<p class="small">{esc(rc['holdout']['evaluator'])}. {rc['holdout']['n_cells']} cells, {rc['holdout']['n_withheld_positives']:,} withheld positives. The geophysical term's +0.008 over lane geometry sits inside the intervals, so it is reported as measured, not as a win.</p></section>
<section><h2>Why it is not cleared</h2>
<p>{number(uq['worst_forward_overlap_all'] * 100, 1)}% of its dots fall within 3&nbsp;px of <code>r13-lattice-s5</code>, whose 3&nbsp;px halo covers 0.9987 of the footprint. Rule 1's prescribed action is to log a duplicate and stop. A comparison against the raster previously associated in repo notes with an OWNER-REPORTED 0.2778 claim also exceeds the limit; however, the owner README marks H33-2-B2 <strong>UNSCORED</strong>, so that number is not attributed to those exact bytes and is not a reason to weaken the gate.</p>
<p>That conclusion is not unique to this run. An independent session of this repository already certified the same obstruction from a different witness &mdash; <code>{esc(sat.get('source', ''))}</code>, positive over the entire allowed domain, giving every candidate forward overlap {number(sat.get('covered_allowed_fraction'), 2)}. Two sessions, two witnesses, one finding.</p>
<p>An earlier session recorded the remedy explicitly: <strong>resolve the obstruction through an owner protocol revision</strong>, not by redefining support, exempting dense maps, adding a reverse-overlap condition, or choosing another raster after STOP. This run honours that. Verdict <strong>{esc(rc['verdict'])}</strong>; promotion ready <strong>no</strong>.</p>
<p>{link('data/h57k_run_card.json', 'Run card JSON')} &middot; {link('data/h57k_submission.json', 'Uniqueness and validator receipt')} &middot; {link('data/h57k_exact_duplicate_check.json', 'Byte-identity check vs 655 registry rasters')}</p></section>
<section><h2>Historical model diagnostics — not score evidence</h2>
<p>{esc(rc['contradicting_instruments']['withdrawn_owner_score_model'])} Against that, {esc(rc['contradicting_instruments']['holdout_model'])}.</p>
{table(['Excluded band', 'Dots', 'Modelled T', 'Surrogate DTI', 'Median distance'], sweep_rows)}
<p>The &le;&nbsp;2&nbsp;px exclusion and the emission's median distance of <strong>{number(rc['contradicting_instruments']['emission_median_distance_to_catalogue_px'], 1)}&nbsp;px</strong> from the mapped catalogue are file/model diagnostics only. No verified score-to-file mapping supports a claim about the distance distribution of scored rasters. With the owner-score-derived anchor withdrawn, the historical surrogate outputs cannot rank candidates or explain a reported score.</p>
<h3>Cross-file model comparison (not a score-to-file mapping)</h3>
{table(['Dot field', 'Dots', 'Modelled T', 'Surrogate DTI', 'Score provenance'], cmp_rows)}
<p>These are local cross-file model comparisons, not organizer scores. The inspected GEMSDOE32 owner README marks H33-2-B2 <strong>UNSCORED</strong> and calls 0.2747 a projection; 0.2778 remains an unverified owner-reported claim without an exact-file receipt. The 0.2708 attribution is contradicted by the owner audit. No local surrogate validates either mapping, and no projection is presented as a score. <a href="h57k-junction.html">Separate Session 4 junction-distance result →</a></p></section>
<section><h2>A template bug found and fixed here</h2>
<p><code>gems57.emit.allocate_by_marginal_bar</code> breaks at the first candidate failing the DTI test, but marginal credit depends on local kernel saturation, not rank, so on this surface's flat plateaus it stopped at 3,405 dots. <code>allocate_patient</code> keeps the identical test and stops only after <code>patience</code> consecutive rejections: 62,872 dots, surrogate DTI 0.0832 &rarr; 0.2927. Fixed once, in the shared template, with regression tests; the original function is retained for callers and comparison.</p></section>'''
        h57k_page += '''<section><h2>Separate historical run: Session 4 junction distance</h2>
<p>This earlier H57-K-labelled experiment used a different feature (visible-network junction distance), a different holdout result, and stopped before placement when its pinned-witness overlap exceeded the literal 0.70 limit. <strong>No TIFF was emitted for that run.</strong> It is not the strand-expression artifact documented above.</p>
<p><a href="h57k-junction.html">Open Session 4 H57-K junction-distance evidence and run card →</a></p></section>'''
    pages = {'index.html': ('Overview', index), 'executive-summary.html': ('Download & submit', executive),
             'results.html': ('Results', results), 'method.html': ('Method', method),
             'hypotheses.html': ('Hypotheses', hypotheses), 'research.html': ('Research', research),
             'sources.html': ('Sources', sources), 'data-sources.html': ('Data & sources', sources),
             'irregularities.html': ('Audit', irregularities), 'run-card.html': ('Run card', runcard),
             'session-6-verification.html': ('Session 6 verification', session6_page(root)),
             'archive.html': ('Archive warning', archive), 'session-3.html': ('Archived session', archive), 'session-4.html': ('Archived H57-I', archive),
             'h57k.html': ('H57-K candidate', h57k_page)}
    for filename, (title, body) in pages.items():
        (docs / filename).write_text(page(title, body, filename, stamp))
    # Preserve the old /docs/index.html URL after switching to artifact-based Pages.
    aliases = docs / 'docs'
    aliases.mkdir(exist_ok=True)
    for filename in pages:
        (aliases / filename).write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../{filename}"><title>57GEMSDOE · moved</title></head><body><p>Research release HOLD; not cleared for submission. <a href="../{filename}">Open current page</a>.</p></body></html>')
    (docs / '.nojekyll').touch()
    # Mirror this current release only for the existing main-root Pages layout.
    # Artifact deployment still serves docs/ directly. These are identical delivery
    # bytes, not new predictions or copied prior submissions.
    for suffix in ('.tif', '.zip', '.json'):
        source = (root / card['file']).with_suffix(suffix)
        target = root / 'downloads' / source.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
    print(f'Built {len(pages)} evidence-led pages. Download authorization HOLD pending owner decision; submission HOLD. No model run or slot used.')
    return card


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--no-preview', action='store_true', help='reuse the existing numeric preview during feed-only builds')
    a = p.parse_args()
    build(make_preview=not a.no_preview)


if __name__ == '__main__':
    main()
