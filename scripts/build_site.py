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
# Every page section reads one of these receipts. A missing file fails the
# build; nothing falls back to another session's numbers.
PUBLIC = ['run_card_current', 'h58_holdout', 'h58_canary', 'h58_structure',
          'h58_build', 'h58_experiment_plan', 'h58_uniqueness_final_dots',
          'h58_uniqueness_surface_before_placement', 'h58_registry_profile',
          'live_submission_patterns',
          'relay_bend_holdout', 'relay_bend_canary', 'relay_bend_structure', 'relay_bend_surface_uniqueness',
          'hypotheses_current', 'irregularities_current', 'source_checks', 'registry_classification', 'uniqueness_session6_full_registry_696', 'session6_mechanism_and_witness',
          'registry_refreshed', 'site_inventory', 'best_submission_audit',
          'uniqueness_saturation_certificate', 'leaderboard_snapshot', 'environment',
          'feature_cache', 'data_preparation', 'experiment_plan', 'orientation_surface_uniqueness']


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
            item = dict(repo=repo, reported_filename=name,
                        owner_reported_dti=float(value) if value else None,
                        evidence_class='OWNER-REPORTED; NOT ORGANIZER-CONFIRMED',
                        submission_receipt=None)
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
<title>{esc(title)} · 57GEMSDOE</title><meta name="description" content="Fault-zone anatomy research. A new, format-valid GeoTIFF is downloadable; its submission is blocked by the literal uniqueness gate.">
<link rel="stylesheet" href="assets/site.css"><script src="assets/site.js" defer></script></head>
<body><a class="skip-link" href="#main">Skip to content</a>
<header><div class="header-inner"><a class="brand" href="index.html"><span class="brand-number">57</span><span>GEMS<span class="brand-sub">FAULT-ZONE ANATOMY</span></span></a>
<span class="status-pill">RESEARCH · HOLD</span></div><nav aria-label="Primary">{nav}</nav></header>
<main id="main">{body}</main>
<footer><div><strong>Maximize P(Win). Own the Outcome.</strong> Publish negative evidence; don't spend a slot to hide uncertainty.</div>
<p>Site built {esc(stamp)}. Results are local <strong>HOLDOUT-DTI</strong>, not leaderboard scores. No submission-page receipt is available.
{link('data/run_card.json', 'JSON run card')} · {link('run-card.html', 'Readable card')} · {link('https://github.com/buffedlizard55-lab/57GEMSDOE', 'Repository')}</p></footer></body></html>'''


def download_panel(card):
    """The download block, generated only from the current run card and its bytes."""
    filename = Path(card['file']).name
    zipname = Path(card['zip_file']).name
    v = card['validator_output']
    dots = card['final_dots']
    gate = card['correlation_overlap_vs_registry']['final_dots']
    ok_dl = bool(card['okay_to_download'])
    ok_sub = bool(card['okay_to_submit'])
    perm = (f'<span class="permission {"yes" if ok_dl else "no"}">Download for research: '
            f'{"OK" if ok_dl else "NO"}</span>'
            f'<span class="permission {"yes" if ok_sub else "no"}">Submit to competition: '
            f'{"OK" if ok_sub else "NO"}</span>')
    banner = ('<div class="warning"><strong>Download only.</strong> The file is a format-valid, '
              'content-distinct research raster; the repository\'s own literal drift gate is not '
              'cleared, so this session does not release a slot. Read the exact reason below.</div>'
              if not ok_sub else
              '<div class="warning"><strong>Gate cleared.</strong> Still a separate selector step, '
              'not an automatic upload: check the logged-in weekly counter before submitting.</div>')
    return f'''<section class="download-panel" aria-labelledby="download-title">
<div class="eyebrow">NEW GEOTIFF · GENERATED {esc(card['generated_utc'][:10])} · H58 FAULT-ZONE ANATOMY</div>
<h1 id="download-title">Fitted damage-zone envelope around mapped faults.</h1>
<p class="hero-sub">Per-fault intensity from distance, mapped-length (displacement proxy) and host-strike
structure, with sense-conditioned obliquity tested and rejected by the data. {dots['dots']:,} dots, none on
the mapped catalogue. Built from scratch this session &mdash; not a copy of any earlier raster.</p>
<div class="permissions">{perm}</div>
{banner}
<p class="hold-reason"><strong>{'SUBMITTABLE' if ok_sub else 'HOLD · DO NOT SUBMIT'}:</strong>
{esc(card['verdict_reason'])}</p>
<div class="actions"><a class="button primary" href="downloads/{esc(filename)}" download>&darr; Download GeoTIFF <span>{('%d KB' % round(v['bytes'] / 1024)) if v['bytes'] < 1_000_000 else ('%.2f MB' % (v['bytes'] / 1_000_000))}</span></a>
<a class="button secondary" href="downloads/{esc(zipname)}" download>Single-TIFF ZIP</a>
<a class="text-link" href="executive-summary.html">Exact submission steps &rarr;</a></div>
<details class="file-details"><summary>Exact filename, SHA256, note and portal checks</summary>
<p class="mono">{esc(filename)}</p><p class="mono">SHA256 {esc(card['raster_sha256'])}</p>
<p>Suggested note ({card['submission_note_chars']} / 140 characters):</p>
<p class="mono" id="submission-note">{esc(card['submission_note'])}</p>
<button class="copy-button" type="button" data-copy="submission-note">Copy note</button>
<ul><li>Submission name to paste: <code>{esc(card['submission_name'])}</code> (140-char limit, {len(card['submission_name'])} used)</li>
<li>Validator: {sum(1 for k, x in v['checks'].items() if x)}/{len(v['checks'])} checks PASS · values in [0,1] · no NaN inside the footprint · CRS/shape/geotransform match the bridge sample</li>
<li>Registry audit: {gate['registry_rasters_checked']} hash-pinned rasters · worst Spearman {number(gate['worst_spearman_full_footprint'])} (limit 0.90) · worst 3-px forward overlap {number(gate['worst_dot_overlap'])} (limit 0.70) · byte-unique {gate['byte_unique_among_checked']} · pixel-unique {gate['pixel_unique_among_checked']}</li></ul>
<p class="small">The ID inside the filename hashes the decoded pixel array; the SHA256 above hashes the actual bytes you download. {link('data/run_card.json', 'Download the complete run card')} · {link('data/h58_build.json', 'Writer receipt')}.</p>
</details></section>'''


def evidence_notice(card):
    score = card['holdout_dot_dti']
    ev, n, seed = score["evaluator_version"], score["withheld_positive_pixels"], score["draw_seed"]
    return (f'<p class="evidence-note"><strong>Local evidence only.</strong> Evaluator '
            f'<code>{esc(ev)}</code> \u00b7 {n:,} withheld positive pixels \u00b7 pooled terms \u00b7 '
            f'95% spatial-block bootstrap CI \u00b7 draw seed {seed}. No live submission score or '
            f'private-label claim.</p>')


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
<h2>4 · What the 0.2778 raster is (and is not)</h2>
<p>The owner-reported 0.2708 file (GEMSDOE28) and the 0.2778 file (GEMSDOE32) are <b>file-measured</b> as nested: the 0.2778 raster adds nothing and removes {esc(pc.get('removed_vs_base', na))} of the {esc(pc.get('base_positive', na))} base dots. Every removed dot lies within {number(pc.get('removed_distance_px_min', na), 2)}–{number(pc.get('removed_distance_px_max', na), 2)} px of the mapped catalogue, none on it. The nearest kept dot is {number(pc.get('target_distance_px_min', na), 2)} px away.</p>
<p>That is a plausible mechanism for a precision gain under the DTI cost. It is <b>not</b> a demonstrated causal score gain: the scores are owner-reported, and the organizer board is not a file receipt. Source: <code>evidence/session6_mechanism_and_witness.json</code>.</p>
<h2>5 · Holdout and leaderboard</h2>
<ul>
<li>No holdout was run this session. <code>training_features.tif</code> is absent, and its link was unreachable from the audit environment (IR-S6-05).</li>
<li>The leaderboard snapshot shows 0.3774 at rank 1 and 0.3195 at rank 7. The brief's “highest” claim conflicts with that snapshot (IR-S6-06). Snapshot: <code>data/leaderboard_snapshot.json</code>.</li>
</ul>
<p>{link('irregularities.html', 'Audit ledger, including IR-S6-01 to IR-S6-12 →')} · {link('executive-summary.html', 'Download and submission guide →')}</p>
"""


def build(root=ROOT, make_preview=True):
    docs = root / 'docs'
    data = docs / 'data'
    data.mkdir(parents=True, exist_ok=True)
    evidence = {name: json.loads((root / 'evidence' / f'{name}.json').read_text()) for name in PUBLIC}
    card = evidence['run_card_current']
    h57k = None
    h57k_files = ['h57k_run_card', 'h57k_submission', 'h57k_model_compare',
                  'h57k_proximal_sweep', 'h57k_exact_duplicate_check']
    h57k_paths = {n: root / 'evidence' / f'{n}.json' for n in h57k_files}
    if all(path.is_file() for path in h57k_paths.values()):
        h57k = {n: json.loads(path.read_text()) for n, path in h57k_paths.items()}
        for name, path in h57k_paths.items():
            shutil.copyfile(path, data / f'{name}.json')
    # The page never contradicts the card, and the card never contradicts itself.
    if bool(card['okay_to_submit']) != (card['verdict'] == 'promote-candidate'):
        raise ValueError('run-card verdict and submission permission disagree; refusing to publish')
    if not card['validator_output'].get('all_checks_passed'):
        raise ValueError('delivered raster fails the local format/range preflight')
    if int(card['final_dots']['dots']) <= 0:
        raise ValueError('no final dots in the current release; nothing to advertise')
    if not (root / card['file']).is_file() or not (root / card['zip_file']).is_file():
        raise FileNotFoundError('current downloadable raster/ZIP missing; no historical fallback')
    for name in PUBLIC:
        shutil.copyfile(root / 'evidence' / f'{name}.json', data / f'{name}.json')
    shutil.copyfile(root / 'evidence/run_card_current.json', data / 'run_card.json')
    for name in ['feed_refresh_status', 'review_passes', 'sibling_page_reviews', 'browser_qa', 'registry_concurrent_extension', 'registry_open_pr_extension', 'uniqueness_current_review', 'uniqueness_concurrent_extension', 'uniqueness_open_pr_extension', 'registry_h57i_extension', 'uniqueness_h57i_extension']:
        source = root / 'evidence' / f'{name}.json'
        if source.exists():
            shutil.copyfile(source, data / source.name)
    reports = owner_reports((root / 'TASK_PROMPT.md').read_text())
    (data / 'owner_reports.json').write_text(json.dumps(reports, indent=2, allow_nan=False) + '\n')
    if make_preview:
        preview(root, card)
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    holdout = evidence['h58_holdout']
    registry = card['correlation_overlap_vs_registry']['final_dots']
    surface_gate = card['correlation_overlap_vs_registry']['surface_before_placement']
    profile = card['correlation_overlap_vs_registry']['registry_profile']
    raw = card['holdout_surface_dti']
    dots = card['holdout_dot_dti']
    panel = download_panel(card)
    disclaimer = evidence_notice(card)
    names = {'distance_only': 'Distance only (control)',
             'anatomy10': 'Reference: repaired visible-fault anatomy (no side term)',
             'anatomy10_sense': '+ recorded slip sense from INGENIOUS',
             'anatomy10_sense_obliq': 'Candidate: + signed radial obliquity and the W(L) distance ratio'}
    score_rows = []
    for key in sorted(holdout['scores']):
        arm, _, flank = key.partition('__')
        sc = holdout['scores'][key]
        sv = holdout['soft_surface_holdout']['scores'][key]
        label = f"{esc(names.get(arm, arm))} <span class='small'>&middot; {esc(flank)}</span>"
        score_rows.append([label, f"{number(sv['dti'])} {interval(sv['ci95'])}",
                           f"{number(sc['dti'])} {interval(sc['ci95'])}",
                           f"{sc['withheld_positive_pixels']:,}"])
    score_table = table(['Arm and flank policy', 'Soft-surface HOLDOUT-DTI [95% CI]',
                         'Binary-allocation HOLDOUT-DTI [95% CI]', 'Withheld positives'], score_rows)
    canary = evidence['h58_canary']
    canary_rows = [[f'<code>{esc(k)}</code>', number(v['discriminative_auc_max']), 'PASS (< 0.90)' if not v['leakage_flag'] else '<strong>LEAKAGE FLAG</strong>'] for k, v in canary['features'].items()]
    max_auc = max(v['discriminative_auc_max'] for v in canary['features'].values())

    law = card['width_law']
    struct = card['structure_measurements']
    gain = card['paired_gain_candidate_minus_reference']
    live = card['live_submission_evidence']
    index = panel + f'''<section class="stat-grid" aria-label="Current research diagnostics">
<div class="stat"><span>Local format</span><strong>PASS</strong><small>Float32 &middot; one band &middot; values in [0,1] &middot; {card['final_dots']['dots']:,} dots</small></div>
<div class="stat"><span>Registry audit</span><strong>{registry['registry_rasters_checked']} / {registry['registry_rasters_expected']}</strong><small>Every hash-pinned raster present in this checkout</small></div>
<div class="stat"><span>Worst 3-px overlap</span><strong>{registry['worst_dot_overlap']:.0%}</strong><small>Limit 70% &middot; {profile['universal_overlap_blockers']} dense priors make this unsatisfiable</small></div>
<div class="stat"><span>Weekly slots spent</span><strong>0</strong><small>Three predeclared experiments, zero submissions</small></div></section>

<section class="two-column"><div><div class="eyebrow">THE SCIENTIFIC RESULT &middot; H58 &middot; 2026-10-10</div>
<h2>Damage-zone width grows with mapped length, but very sub-linearly &mdash; and the handed Riedel term is not supported.</h2>
<p><strong>Fitted width law.</strong> On a fresh buffered whole-component draw (seed {holdout['draw_seed']}, {struct['withheld_positive_pixels']:,} withheld positives), the 90th-percentile distance of withheld strands to their nearest visible trace was regressed against mapped-component length across {law['n_bins']} bins: <code>gamma = {number(law['gamma'], 3)}</code>, 95% CI {interval(law['gamma_ci95'])}. The interval excludes 1, so widening is strongly sub-linear in this proxy &mdash; consistent with damage-zone growth that decelerates with displacement (Savage &amp; Brodsky 2011) and <em>not</em> with a constant-ratio halo. Absolute half-widths are {number(law['w0_px'], 1)} px at L0 = {number(law['l0_px'], 0)} px, i.e. kilometres, not tens of metres.</p>
<p><strong>Structure the data does <em>not</em> show.</strong> Signed radial obliquity of withheld pixels around their host, and its interaction with the recorded slip sense, produced no enriched bin (all enrichment &le; {max(struct['obliquity_enrichment']):.3f} against a base rate of {struct['base_rate']:.4f}), and the left/right ratio by host sense is {struct['side_asymmetry_by_sense_record']['recorded_strike_slip_host']['log_ratio_R_over_L']:+.3f} / {struct['side_asymmetry_by_sense_record']['no_recorded_sense']['log_ratio_R_over_L']:+.3f} nats &mdash; noise. The candidate arm that adds those columns therefore beats the reference by {number(gain.get('delta'))} with 95% CI {interval(gain.get('ci95'))}; the arm ships only if that interval clears zero (retained: <strong>{card['paired_gain_candidate_minus_reference']['retained']}</strong>). Axial relative strike, by contrast, <em>is</em> real: withheld medians {number(struct['relative_strike_median_withheld_deg'],1)}&deg; versus a {number(struct['relative_strike_median_visible_null_deg'],1)}&deg; visible-null.</p>
<p><strong>Allocation.</strong> The dot budget is the lane rule, not a tuned number: {int(card['final_dots']['cap']):,} ceiling = 4 &times; 10,000 &times; the fitted fraction of withheld positives inside the kept (distance &times; strike) zone, {number(struct['fraction_pos_in_kept_zone'])}. Dots are kept &gt; 2 px off the mapped catalogue because organiser thread 11516 fully penalises that flank; on this instrument that policy is untestable (the 3 px context collar already emptied it, so the flank effect measures {number(min(abs(v['delta']) for v in holdout['flank_policy_effect'].values()), 4)}). The budget shape is inherited from a re-measured registry fact, not taste: across {live['scored_rasters']} owner-scored rasters in this repository, dot count correlates with the reported score at Spearman {number(live['rank_correlations']['dots'], 3)} (p = {number(live['rank_correlation_p']['dots'], 5)}) and median distance-to-catalogue at {number(live['rank_correlations']['median_distance_to_catalogue_px'], 3)} &mdash; confounded by construction, since method and budget change together, so it sets a prior about density, not a target.</p>
<p><strong>Holdout score.</strong> Production arm binary-allocation HOLDOUT-DTI {number(dots['dti'])} {interval(dots['ci95'])}; soft surface {number(raw['dti'])} {interval(raw['ci95'])}. These are instrument readings, not leaderboard projections &mdash; the repository already records that this holdout does not rank live scores.</p>
{disclaimer}<p>{link('results.html', 'Every arm, fold and gate number &rarr;')}</p></div>
<figure class="map-preview"><img src="assets/preview.png" alt="North-up display of the H58 emitted dot field on the bridged competition grid" width="600" height="680"><figcaption>Actual H58 emission &middot; north &uarr; &middot; EPSG:32611 &middot; downsampled maximum; display colours are not probabilities and are not ground truth.</figcaption></figure></section>

<section class="card"><h2>Why the literal drift gate cannot be cleared by anyone right now</h2>
<p>Support is defined literally as <code>finite prediction &gt; 0</code>. {profile['universal_overlap_blockers']} of the {profile['read']} audited priors are positive on <em>every</em> one of the {profile['allowed_pixels']:,} allowed cells, so their 3 px dilation covers the whole usable domain and <em>any</em> non-empty candidate scores forward overlap 1.0 against them. Our candidate is byte-unique and pixel-unique against all {registry['registry_rasters_checked']} priors, its worst Spearman is {number(registry['worst_spearman_full_footprint'])} and its worst Jaccard is {number(registry['worst_jaccard_dot_sets'])}; {registry['duplicate_count']} comparisons trip the overlap clause and all of them are dense-surface priors. We report the trip instead of inventing an exemption, and we do not call the file cleared.</p>
<p>{link('data/h58_registry_profile.json', 'Registry support profile')} &middot; {link('data/h58_uniqueness_final_dots.json', 'Per-prior gate rows for the final dots')} &middot; {link('data/h58_uniqueness_surface_before_placement.json', 'Same audit on the pre-placement surface')}</p></section>

<section class="card"><div class="eyebrow">REVIEW FINDING CARRIED FORWARD</div><h2>Host-strike fallback bug (IR-57-STRIKE-01) stays fixed and pinned.</h2><p>An inverted finite-value fallback once reset every valid host strike to zero, which made every earlier orientation claim meaningless. It remains fixed with regressions; the H58 obliquity test above is the first test of <em>signed</em> handedness on the corrected frame, and it is reported as a negative.</p><p>{link('irregularities.html', 'Audit ledger &rarr;')}</p></section>
<section class="card feed-card"><div class="eyebrow">PUBLIC ORGANIZER FEED · NOT A FILE RECEIPT</div><h2>Leaderboard context</h2><p><strong id="leaderboard-top">{number(evidence['leaderboard_snapshot']['top_public_dti'])}</strong> <span id="leaderboard-context">top public DTI in the last successful organizer snapshot</span></p><p id="feed-status" aria-live="polite">Checked on 2026-10-09. Date-precision snapshot; open the official board for current context.</p><p>{link('https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/', 'Official leaderboard')} · {link('data/leaderboard_snapshot.json', 'Timestamped snapshot')}</p><p class="small">Scheduled Pages builds refresh this public feed. Failures retain the prior snapshot with a visible freshness warning. Neither the team's remaining slots nor its private score is known.</p></section>
'''

    v = card['validator_output']
    patterns = evidence['live_submission_patterns']
    best = patterns['best_vs_base']
    pattern_n_exec = len([r for r in patterns['rows'] if r.get('owner_reported_score') and r.get('dots')])
    executive = panel + f'''<section><h2>Read this before opening &ldquo;New submission&rdquo;</h2>
<div class="warning"><strong>{'This file is gate-cleared; a separate selector still has to approve the slot.' if card['okay_to_submit'] else 'Do not submit this release.'}</strong>
Downloading the TIFF or ZIP is {'approved' if card['okay_to_download'] else 'not approved'}. A local format PASS is never organiser acceptance, and this repository does not spend weekly slots from a build.</div>
<p>{registry['duplicate_count']} of {registry['registry_rasters_checked']} registry comparisons trip the literal 3-px overlap clause; {profile['universal_overlap_blockers']} of them are dense soft-surface priors whose support already covers every allowed cell, which makes the clause unsatisfiable for <em>any</em> non-empty candidate, including this repository's own earlier releases. Byte and decoded-pixel identity pass against all {registry['registry_rasters_checked']} priors (worst Spearman {number(registry['worst_spearman_full_footprint'])}, worst Jaccard {number(registry['worst_jaccard_dot_sets'])}), so the file is not a copy; the trip is a representation-class collision in the inherited rule, recorded here rather than redefined away.</p></section>

<section><h2>Exact submission steps</h2><ol class="steps">
<li><strong>Read the release card.</strong> Require format PASS, both drift-gate phases reported, a clean leakage canary, and a paired holdout result you accept. Promotion to a real slot is a separate selector step: <code>evidence/run_card_current.json</code>.</li>
<li><strong>Download the <code>.tif</code>, or the single-TIFF <code>.zip</code>.</strong> Never upload the web page, a JSON receipt, a PDF or a repository archive. The shared writer round-trip checked that this ZIP contains exactly one GeoTIFF, byte-identical to the download.</li>
<li><strong>Open the submission page and check your remaining capacity.</strong> {link('https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/', 'DrivenData: GEMS submissions')}. Log in, accept the official rules, and read the weekly counter on the page; the published rules allow three submissions per week and only the logged-in page knows what is left.</li>
<li><strong>Attach the file under &ldquo;File to submit&rdquo;, paste the unique name and the note, then submit</strong> &mdash; only if the selector cleared it. Name (paste exactly): <code>{esc(card['submission_name'])}</code>. Note ({card['submission_note_chars']}/140 chars): <code>{esc(card['submission_note'])}</code>. Nothing in this project clicks Submit for you.</li>
<li><strong>Save the organiser receipt.</strong> Copy the score the page returns, with the timestamp and the exact filename, into <code>evidence/</code>. A public-leaderboard value cannot be attributed to a file hash, which is why every number on this site is labelled HOLDOUT-DTI or OWNER-REPORTED.</li></ol>
<p class="small">The form also rejects rasters whose CRS, shape or geotransform differ from the template. Ours is written from the same bridge grid it validates against: 1 band, float32, EPSG:32611, 3730 &times; 3292, transform <code>(100, 0, 243350, 0, -100, 4508550)</code>.</p></section>

<section><h2>Why the reported &ldquo;values must be in range [0, 1]&rdquo; error cannot occur with this file</h2>
<p>The bytes of the file that produced that error are not in this workspace, so its cause is <strong>not established</strong>. The public problem page does permit null/NaN outside the bounds, so the safest reading is a NaN or out-of-range value <em>inside</em> the submitted array: the validator compares values against [0, 1], and any NaN makes that comparison fail. Our writer therefore refuses non-finite or out-of-range input, writes finite zeros outside the footprint, re-reads the file it wrote and validates that, and refuses to overwrite an existing release. {sum(1 for x in v['checks'].values() if x)}/{len(v['checks'])} local checks pass on the delivered bytes.</p>
{table(['Local check on the delivered TIFF', 'Result'], [[f'<code>{esc(k)}</code>', 'PASS' if x else '<strong>FAIL</strong>'] for k, x in v['checks'].items()])}
<p class="small">Min {v['min']:.1f}, max {v['max']:.8f}, {v['emitted_positive_pixels']:,} positive pixels, {v['n_nan']} NaN, {v['n_infinite']} infinite. Positive mass on the mapped catalogue: {v.get('on_catalogue_positive_pixels', 'n/a')}.</p></section>

<section><h2>What the published scores actually tell us about this metric</h2>
<p>We measured the registry rasters instead of trusting prose. The owner-reported best file in this family ({best.get('best_dots', 0):,} dots) is a strict subset of its {best.get('base_dots', 0):,}-dot base ({best.get('best_is_subset_of_base')}): it adds nothing and deletes {best.get('removed_dots', 0):,} dots, all of them within {best.get('removed_max_distance_to_catalogue_px', float('nan')):.2f} px of the mapped catalogue, while every kept dot sits at least {best.get('kept_min_distance_to_catalogue_px', float('nan')):.2f} px away &mdash; and the deletion is reproduced exactly by a 2 px rule ({best.get('equals_base_pruned_at_2px')}). Under the official metric a catalogue-adjacent dot with no new-fault pixel within 3 px buys zero coverage and pays 0.2&thinsp;&times;&thinsp;p in false-positive cost, so that prune is arithmetic, not luck.</p>
<p>Across the scored registry the same direction repeats (rank-correlation table on the research page), but method and dot budget change together there, so it is description with n = {pattern_n_exec} and no causal control. It is why this release keeps dots off the catalogue flank and caps its budget. It is <strong>not</strong> a claim about our file's future score.</p>
<p>{link('data/live_submission_patterns.json', 'Full registry support measurements')} &middot; {link('research.html', 'The 0.2778 analysis')}</p></section>'''

    paired = holdout['paired_differences']
    comp_rows = [[f"<code>{esc(k)}</code>", number(v['delta']), interval(v['ci95']),
                  'positive (CI excludes 0)' if v['ci95'][0] > 0 else
                  ('negative (CI excludes 0)' if v['ci95'][1] < 0 else 'indistinguishable from 0')]
                 for k, v in sorted(paired.items(), key=lambda kv: -kv[1]['delta'])]
    flank_rows = [[esc(names.get(k, k)), number(v['dti_flank0']), number(v['dti_flank2']), number(v['delta'])]
                  for k, v in holdout['flank_policy_effect'].items()]
    fold_rows = [[esc(d['fold']), esc(d['arm']), esc(d['flank']), number(d['dti']), number(d['soft_surface_dti']),
                  f"{d['dots']:,}", number(d['training_gamma'], 3), number(d['training_fraction_inside_zone'])]
                 for d in holdout['per_fold']]
    results = f'''<div class="eyebrow">THREE PREDECLARED EXPERIMENTS &middot; ZERO SUBMISSIONS</div>
<h1>Sub-linear damage-zone widening is supported; handed Riedel obliquity is not.</h1>{disclaimer}
<h2>Every arm, same folds, same evaluator</h2>{score_table}
<p class="small">Pooled over the four label-blind quadrants of one buffered whole-component draw (seed {holdout['draw_seed']}); evaluator <code>{esc(holdout['evaluator_version'])}</code>; 1,000 paired bootstrap draws over physical 20 km clusters ({len(holdout['scores'])} arms &times; 2 flank policies). CIs condition on the fitted folds, masks and budgets: they exclude model-selection and private-label uncertainty. <code>flank0</code>/<code>flank2</code> = keep all off-trace pixels / also drop pixels within 2 px of a visible trace.</p>
<h2>Paired differences against the candidate arm</h2>{table(['Compared arm', 'Paired HOLDOUT-DTI difference', '95% CI', 'Reading'], comp_rows)}
<p>Candidate: <code>{esc(holdout['candidate'])}</code> vs reference <code>{esc(holdout['reference'])}</code>. Retained by the predeclared rule: <strong>{holdout['candidate_retained']}</strong>. Production arm used for the delivered TIFF: <code>{esc(holdout['production_arm'])}</code>.</p>
<h2>Catalogue-flank suppression, measured on this instrument</h2>{table(['Arm', 'HOLDOUT-DTI flank0', 'HOLDOUT-DTI flank2', 'Delta'], flank_rows)}
<p>Zero everywhere. That is not evidence that the flank is harmless on the live truth: the holdout's own 3 px context collar makes withheld positives structurally impossible inside 2 px of a visible trace, so the instrument cannot price the rule. The live reason to keep the flank empty is organiser thread 11516, plus the registry measurement on the research page. Recorded as a limitation, not as a win.</p>
<h2>Per fold</h2>{table(['Quadrant', 'Arm', 'Flank', 'Binary HOLDOUT-DTI', 'Soft-surface HOLDOUT-DTI', 'Dots', 'fitted gamma', 'fraction inside zone'], fold_rows)}
<h2>Leakage canaries</h2>
<p>Every column was tested alone before the fit was trusted, as <code>max(AUC, 1&minus;AUC)</code> in every fold, so an inversely-ranked feature cannot hide behind a low raw AUC. Maximum discriminative AUC: {number(max_auc)}; flags: {canary['flagged'] or 'none'}. Passing this screen does not prove the absence of every leakage channel &mdash; it rules out the one the protocol names.</p>{table(['Feature', 'Max discriminative fold AUC', 'Canary'], canary_rows)}
<h2>Full-registry drift gate</h2>{table(['Measurement (not a score)', 'Result'], [
 ['Hash-pinned grid rasters audited', f"{registry['registry_rasters_checked']} / {registry['registry_rasters_expected']}"],
 ['Missing or hash-mismatched priors', f"{profile['missing']} / {profile['sha_mismatch']}"],
 ['Candidate positive pixels', f"{card['final_dots']['dots']:,}"],
 ['Worst full-footprint Spearman (limit 0.90)', number(registry['worst_spearman_full_footprint']) + f" &middot; {esc(str(registry['worst_rho_submission']))}"],
 ['Worst 3-px forward overlap (limit 0.70)', number(registry['worst_dot_overlap']) + f" &middot; {esc(str(registry['worst_overlap_submission']))}"],
 ['Worst Jaccard of dot sets (diagnostic only)', number(registry['worst_jaccard_dot_sets'])],
 ['Byte / decoded-pixel identity', 'distinct from every prior checked'],
 ['Triggered comparisons', str(registry['duplicate_count'])],
 ['Dense priors covering every allowed cell', str(profile['universal_overlap_blockers'])],
 ['Literal protocol verdict', '<strong>FAIL &rarr; logged, no exemption invented</strong>' if not registry['unique'] else 'PASS'],
 ['Same audit on the pre-placement soft surface', f"unique={surface_gate['unique']}, worst Spearman {number(surface_gate['worst_spearman_full_footprint'])}, worst overlap {number(surface_gate['worst_dot_overlap'])}"]])}
<p>{link('data/h58_holdout.json', 'Complete HOLDOUT-DTI receipt')} &middot; {link('data/h58_uniqueness_final_dots.json', 'Per-prior gate rows')} &middot; {link('data/h58_structure.json', 'Structure measurements')} &middot; {link('data/h58_experiment_plan.json', 'Predeclared plan')}</p>'''

    structure = evidence['h58_structure']['structure']
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
<section><h2>Catalogue-blind candidate evidence, visible-only hosts</h2><p>H58 deliberately used <strong>only</strong> the cached visible-fault geometry and the recorded slip-sense table: the 19-band geophysical feature cache is gitignored and was not restored this session, so no scarp or magnetic term entered the fit and none is claimed. The shared builder still supports it (<code>geo=</code> / <code>cached_scarp_geometry</code>), which is why this is a scope limit and not a missing file. Band 14 (<code>tmi</code>) is a scalar magnetic field. Gaussian derivatives provide an axial edge tangent, log-gradient magnitude and structure coherence. The angle feature is <code>cos(2 × (candidate strike − primary strike))</code>. It is not the angle of a pixel’s offset from the host.</p><p>The visible catalogue supplies nearest-host distance, cross-/along-strike offsets, axial strike, coherence, density and log component pixel count. Component count is a <strong>noisy mapped-length proxy</strong>, not measured displacement. A histogram-gradient-boosted intensity learns interactions; no textbook Riedel angle, damage-width exponent or assumed dextral sense is inserted.</p><p>Recorded slip sense is used only where a record matches visible context, and its incremental value is explicitly ablated. The final research surface omits it because the paired lower confidence bound is not positive.</p></section>
<section><h2>Whole-component, buffered hide-and-recover</h2><ol><li>Withhold whole original 8-connected raster fault components, rather than ≤12-pixel chunks. Components may still be fragments of geological systems.</li><li>Remove a 3-pixel (300 m) visible-catalogue context collar around held traces. Apply a 12-pixel quadrant-boundary erosion. Derive all catalogue features only from the globally visible context.</li><li>Leave one quadrant out when fitting each model. Evaluation domains are label-blind. Mask the exact unhidden known catalogue, not its 300 m dilation; the buffer is feature-context removal, not a new scoring mask.</li><li>Fit zone radius from the training withheld-distance 90th percentile and shrink the nominal dot cap by training-positive occupancy in that zone. Estimate positive count from training prevalence only—never oracle test-positive count.</li><li>Pool TPw/FPw/FNw before computing DTI. Resample paired, aligned physical 20 km block terms. Never average quadrant DTI as if it were pooled DTI.</li></ol>{disclaimer}</section>
<section><h2>Descriptive geometry is not a universal shear angle</h2><p>On this fixed buffered holdout, the 10th / 50th / 90th percentiles of withheld-positive nearest-visible-host distance are {number(structure['distance_positive_quantiles_px'][0], 1)}, {number(structure['distance_positive_quantiles_px'][1], 2)}, and {number(structure['distance_positive_quantiles_px'][2], 2)} pixels (100 m per pixel). The saved distance quantiles use probabilities [0.10, 0.50, 0.90, 0.95, 0.99], not quartiles.</p><p>The distribution below is <strong>HOLDOUT-STRUCTURE (descriptive, not a score)</strong>: unsigned axial difference between local raster strikes, folded to 0–90°. It is pixel-weighted, not segment-weighted. Of {structure['withheld_positive_pixels']:,} withheld-positive pixels, {relative['n_withheld_total']:,} have finite local strike with coherence &gt; {relative['minimum_local_coherence']:.1f}; the remaining {structure['withheld_positive_pixels'] - relative['n_withheld_total']:,} do not enter the angle histogram. The visible-reference column contains {relative['n_visible_total']:,} valid pixel-pair samples; each pair uses the nearest different-component visible trace among the 13 nearest queried visible pixels (including the query pixel). Unavailable and low-coherence comparisons are omitted. Percentages in both columns are conditional on each column’s valid angle samples. This censored convenience null is not significance testing, a validated stress inversion, or evidence of a DTI gain.</p>{angle_table}<p>HOLDOUT-STRUCTURE medians are {relative['median_withheld']:.2f}° (withheld) and {relative['median_visible']:.2f}° (visible reference). No inferential test was run. These summaries do not change any fitted model, HOLDOUT-DTI result, production-dot placement or promotion decision.</p><p>{link('data/h58_structure.json', 'Descriptive distributions and null caveat')} &middot; {link('data/h58_experiment_plan.json', 'Predeclared comparisons')}</p></section>
<section><h2>Why sparse placement and precision matter</h2><p>For binary predictions, let <em>T</em> be maximum triangular-kernel coverage of truth pixels, <em>M</em> prediction self-credit, <em>N</em> prediction count, and <em>K</em> truth count. The official-formula arithmetic becomes:</p><pre>DTI = T / (0.2 T + 0.2 N − 0.2 M + 0.8 K)</pre><p>Max-cover means overlapping dots cannot repeatedly buy the same coverage. A dot far from every new-fault pixel adds false-positive cost without coverage. A dot near a known trace gets no credit merely for that proximity. This is why geometry, calibration and the emitted dot budget must all be tested—large probabilities and an impressive-looking lineament image are not scores.</p></section>
<section><h2>Reproduce locally</h2><pre>python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/python scripts/prepare_data.py --fetch --cache-bands
.venv/bin/python scripts/refresh_registry.py --workers 8
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_relay_bend_experiments.py --build-research-surface --minutes 65
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_site.py</pre><p>CPU only. These commands reproduce the same declared experiments, not permission to add trials or spend slots. Restore the ignored feature stack and registry cache after a new checkout. Historical in-sample/oracle-budget builders are disabled.</p></section>'''

    hypothesis_rows = []
    for h in evidence['hypotheses_current']['candidates']:
        hypothesis_rows.append([str(h['rank']), f"<strong>{esc(h['id'])}: {esc(h['hypothesis'])}</strong><p>{esc(h['signature'])}</p>", '<br>'.join(esc(x) for x in h['layers']), esc(h['why_missing_faults']), esc(h['difference_from_repo']), f"{esc(h['expected_improvement'])}<br>{esc(h['implementation_cost'])}", f"{esc(h['non_fault_mimic'])}<p>{esc(h['status'])}</p>"])
    tested7 = evidence['hypotheses_current'].get('tested_session7_h58', {})
    tested_rows = [[f"<code>{esc(t['id'])}</code>", esc(t['claim']),
                    f"<strong>{esc(t['result'])}</strong>", esc(t['value'])]
                   for t in tested7.get('tested', [])]
    hypotheses = f'''<div class="eyebrow">BEFORE CODE · QUALITATIVE EXPECTATIONS, NOT SCORES</div><h1>{len(evidence['hypotheses_current']['candidates'])} ranked questions; five closed by H58 on 2026-10-10.</h1><p>The ranking was declared before implementation. Novelty means different from the inspected repository implementations; it is not proof that no sibling or researcher has ever tried it. No numeric leaderboard forecasts are assigned.</p>
{table(['Rank', 'Hypothesis & physical signature', 'Layers', 'Why a missing strand?', 'Difference from existing work', 'Expected improvement / cost', 'Non-fault mimic / status'], hypothesis_rows)}
<h2>What H58 actually returned</h2>{table(['Ref', 'Claim tested', 'Outcome', 'Measured value'], tested_rows)}
<p class="small">{esc(tested7.get('note', ''))}</p>
<p>In Session 5 (2026-10-10), E1 tested multi-scale host-bend damage asymmetry &amp; detrended-elevation scarp strike (H57-H), E2 added two-host damage-zone superposition &amp; en echelon relay stepover mechanics (H57-I2) via exact 12-bitplane Euclidean distance transforms to the second nearest distinct visible component (<code>C2 != C1</code>), and E3 tested slip-sense transition heterogeneity (H57-J). E2 achieved a statistically significant positive paired gain (+0.0256 vs single-host anatomy, +0.0225 vs distance-only).</p><p>Required band/geometry data were obtained and hash verified; source-origin and attribute-matching caveats remain.</p>'''

    prow = [r for r in evidence['live_submission_patterns']['rows'] if r.get('owner_reported_score')]
    prow.sort(key=lambda r: -r['owner_reported_score'])
    corr = evidence['live_submission_patterns']['rank_correlations']
    pattern_table = table(['Owner-reported DTI (not confirmed)', 'File', 'Dots',
                           'Median px to catalogue', 'p10 px', 'Min px', 'frac &le; 3 px',
                           'Median neighbour spacing px'],
                          [[number(r['owner_reported_score'], 4), f"<code>{esc(Path(r['file']).name)[:54]}</code>",
                            f"{r['dots']:,}", number(r['median_distance_to_catalogue_px'], 1),
                            number(r['p10_distance_to_catalogue_px'], 1), number(r['min_distance_to_catalogue_px'], 2),
                            number(r['fraction_within_3px_of_catalogue'], 3),
                            number(r['median_neighbour_spacing_px'], 2)] for r in prow])
    pattern_corr = table(['Dot-field statistic', "Spearman &rho; vs owner-reported score", 'p', 'n',
                          'Observed range'],
                         [[f"<code>{esc(k)}</code>", number(v['spearman_vs_owner_reported_score'], 3),
                           f"{v['p_value']:.3g}", v['n'],
                           f"{v['range'][0]:.3g} &ndash; {v['range'][1]:.3g}"]
                          for k, v in corr.items()])
    pattern_n = len(prow)

    research = f'''<div class="eyebrow">CAUSAL CLAIMS REQUIRE MORE THAN A LEADERBOARD</div><h1>What can explain the reported 0.2778?</h1><div class="warning">0.2778 is <strong>OWNER-REPORTED</strong> for the named GEMSDOE32 file. No organizer submission-page receipt attributes that score to its exact bytes. The public board’s matching participant value does not close that gap.</div>
<section><h2>What we independently established</h2><p>H33-2-B2 is exactly its 40,199-dot GEMSDOE28 base minus 2,545 dots at catalogue distance ≤2 pixels, leaving 37,654. No dots were added or relocated. The canonical TIFF SHA256 is <code>c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9</code>. This is a construction measurement, not a scoring receipt.</p><p>{link('data/best_submission_audit.json', 'Independent construction audit')} · {link('https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/registry/submission_build.json', 'Original construction source')}</p></section>
<section><h2>A plausible metric mechanism—not a proven geological cause</h2><p>Its inherited sparse dots can cover distinct truth pixels more efficiently than a broad low-confidence field, while pruning can reduce false-positive cost if the removed dots contribute little unique coverage. That is mathematically plausible under the max-cover metric. It does not establish that the file discovered specific secondary strands or that the 2-pixel exclusion caused a hidden-label gain.</p><p>New geometry can lie next to known geometry. Therefore a blind catalogue halo exclusion can remove true new-fault pixels as well as redundant false positives. A single reported best result, uncontrolled pipeline differences and repeated reuse across sites cannot isolate causality. We use the construction only for learning—not as a base, a feature or a copied output.</p></section>
<section><h2>Can this lane exceed 0.2778?</h2><p>There is no metric ceiling at that value, but <strong>this experiment does not demonstrate a higher submission</strong>. Its held-out binary relative-orientation candidate does not beat the recomputed distance-only control. The soft candidate’s added value over anatomy is also uncertain. A local catalogue-hide CI is not a forecast of newly mapped expert labels or private-round performance.</p><p>The earlier claim that host orientation adds no value was additionally undermined by the finite-strike bug: constant sin2/cos2 cannot express a host-direction interaction. The corrected test now yields a defensible negative for this particular feature/scale/model, not proof that damage-zone mechanics is useless.</p></section>
<section><h2>Why the geological mechanism remains difficult</h2><ul><li><strong>Mechanics ≠ universal geometry.</strong> Schreurs’ analogue arrays and the classical Tchalenko framework justify testing secondary-strand anatomy, not enforcing one angle across mixed normal/dextral systems.</li><li><strong>Length ≠ displacement.</strong> Savage–Brodsky support distance decay and changing zone-width relationships; raster connectivity is an uncertain local displacement proxy, affected by trace fragmentation and mapping completeness.</li><li><strong>Magnetic edge ≠ fault.</strong> Dikes, contacts, topography-dependent clearance and east–west leveling stripes can mimic a strand. Area 2’s 400 m flight-line spacing is coarse relative to a 300 m scoring kernel; 100 m output pixels do not create independent 100 m survey resolution.</li><li><strong>Catalogue hiding ≠ discovery truth.</strong> Existing faults and new expert annotations differ in mapping bias, scale and location. Clean canaries and spatial separation reduce specific leakage risks, not all domain shift.</li><li><strong>Fault map ≠ geothermal-vent map.</strong> Faults can support permeability, but this target has no heat, fluid-flow or reservoir-economic labels. No geothermal-vent or resource-discovery claim follows from this TIFF alone.</li></ul></section>
<section><h2>Measured geometry of the scored submissions (this session)</h2>
<p>Rather than repeat prose, we read every owner-scored raster in the registry and measured its dot field: count, distance to the mapped catalogue, and nearest-neighbour spacing. Values below are raster measurements; the score column is OWNER-REPORTED and attached by filename only.</p>
{pattern_table}
{pattern_corr}
<p>Reading: these are rank correlations over {pattern_n} owner-reported entries whose method <em>and</em> budget change together, so they are confounded by construction and are reported as description only. What is safe to say is narrow: within this family the better-reported entries are broad, delete near-catalogue dots and space dots near 3 px, while the worst-reported entries are dense 1&ndash;2 px fields with tens of thousands more dots. That motivated the <em>shape</em> of our support &mdash; capped, spaced, flank-suppressed, sub-linear width &mdash; and it is not a forecast for our file.</p>
</section>
<section><h2>Historical reports for learning only</h2><p>All filename/value pairs below come from the preserved owner prompt. A blank remains unknown; duplicate pasted pairs are deduplicated. None has been upgraded to ORGANIZER-CONFIRMED, and none is used as a model feature or a promotion forecast.</p>
{table(['Repository', 'Reported file', 'OWNER-REPORTED DTI—not confirmed'], [[link(f'https://buffedlizard55-lab.github.io/{r["repo"]}/', r['repo']), f'<code>{esc(r["reported_filename"])}</code>', number(r['owner_reported_dti'])] for r in reports])}
<p>{link('data/owner_reports.json', 'Machine-readable historical reports')} · {link('hypotheses.html', 'Pre-implementation hypothesis ranking')} · {link('sources.html', 'Primary-source claim ledger')}</p></section>'''

    source_rows = [[f"<strong>{esc(s['id'])}</strong><p>{esc(s['authority'])}</p>", '<ul>' + ''.join(f'<li>{esc(c)}</li>' for c in s['claims_verified']) + '</ul>', esc(s['status']), link(s['url'], 'Review source ↗')] for s in evidence['source_checks']['sources']]
    site_rows = [[link(s['website'], s['repo']), f'<code>{esc(s["commit"][:12])}</code>', esc(', '.join(s['index_files']) or 'No index in pinned tree'), link(f'https://github.com/buffedlizard55-lab/{s["repo"]}/tree/{s["commit"]}', 'Pinned tree')] for s in evidence['site_inventory']['repos']]
    sources = f'''<div class="eyebrow">AUDITABLE · BOUNDED VERIFICATION</div><h1>Claims, bytes and primary sources.</h1><p>Checked 2026-10-09. This is a source ledger, not a guarantee of zero error or a claim that every full paper was read. Verification scope is stated per row.</p>{table(['Authority', 'Supported claims', 'Review scope', 'Link'], source_rows)}
<h2>Data provenance and availability</h2><p>All eight input pins passed; the restored feature stack has 19 bands. GitHub bridge hashes authenticate transport identity, <strong>not independently authenticated official origin</strong>. The DrivenData data page redirected to login. Header/footprint validation therefore remains bridge-relative. Questionable embedded <code>tc</code> and conductive-base descriptions are not used as geological facts or current model inputs.</p><p>Official USGS GeoDAWN metadata is CC0; the GDR Quaternary Faults v2 metadata is CC BY 4.0. Direct source binary hosts are outside sandbox egress. No paid/private input was introduced; no GPU is required. No data-placement blocker remains for the current CPU model.</p><p>{link('data/data_preparation.json', 'Eight-pin transport report')} · {link('data/feature_cache.json', '19-band cache metadata')} · {link('data/environment.json', 'Reproduction environment')}</p>
<h2>Every listed sibling repository</h2><p>All 57 public-main trees were pinned and inventoried, including this repo’s old archives. Trees and file hashes establish availability and construction scope, not scientific validity or organizer scores. The complete raw audit retained dense soft predictions and ambiguous grid rasters, not just 15 curated priors.</p>{table(['Site', 'Pinned commit', 'Homepage files found', 'Manual review'], site_rows)}
<p>{link('data/site_inventory.json', 'Complete site inventory')} · {link('data/registry_refreshed.json', 'Complete immutable raster inventory')}</p>'''

    irregularity_rows = [[f'<strong>{esc(i["id"])}</strong><p>{esc(i["severity"])}</p>', esc(i['finding']), f"<strong>{esc(i['status'])}</strong><p>{esc(i['resolution'])}</p>", esc(i.get('remaining', ''))] for i in evidence['irregularities_current']['irregularities']]
    irregularities = f'''<div class="eyebrow">OWN THE OUTCOME</div><h1>Fixes without rewriting history.</h1><p>The interrupted first attempt is explicitly invalid. Current results use the corrected strike field and shared buffered evaluator. Old in-sample, unbuffered, oracle-budget and relaxed-gate reports remain historical evidence, not recommendations.</p>{table(['ID / severity', 'Finding', 'Resolution', 'Still limited'], irregularity_rows)}
<h2>Remaining work—before any promotion</h2><ol><li>Resolve the universal literal overlap obstruction only through an explicit protocol revision. Do not quietly redefine soft support, exempt dense maps, add a reverse-overlap condition or choose another raster after STOP.</li><li>Obtain organizer receipts to authenticate exact file-to-score attribution and the official data/template provenance chain. Do not ask for or store credentials in chat.</li><li>In a new budgeted session, test at most the next predeclared anatomy hypothesis against corrected spatial controls. Require positive paired evidence and both uniqueness phases before a separate selector considers a slot.</li><li>Strengthen geological-system holdouts, record matching and domain-shift diagnostics. Verify actual fault displacement indicators; investigate magnetic contacts/flight-line mimics.</li><li>Keep source/feed timestamps visible. AI-assisted code and analysis must be disclosed according to the official rules if entering finalist materials.</li></ol><p>{link('data/irregularities_current.json', 'Audit JSON')} · {link('data/review_passes.json', 'Three-pass verification record')} · {link('archive.html', 'Archived outputs—invalid/held, never submit')} · {link('session-6-verification.html', 'Session 6 verification')}</p>'''

    runcard = '<div class="eyebrow">THE COMPLETE RECEIPT</div><h1>Run card · negative</h1><p>Download OK; submit NO. Format validity and pixel identity are not uniqueness clearance.</p><p>' + link('data/run_card.json', 'Download JSON') + '</p><pre>' + esc(json.dumps(card, indent=2, allow_nan=False)) + '</pre>'
    archive = '''<div class="eyebrow">HISTORICAL EVIDENCE ONLY</div><h1>Archived files are not cleared submissions.</h1><p>Earlier outputs in downloads or archives are preserved for learning and audit. They have invalidated geometry, suspect leakage, in-sample scoring, partial registries or failed uniqueness gates. None is recommended for submission. Current evidence is the held release linked on the overview; do not select an old file to bypass STOP.</p><p><a href="index.html">Return to the current release →</a></p>'''
    archived = sorted(path for path in (root / 'docs/downloads').glob('*.tif') if path.name != Path(card['file']).name)
    archive += '<h2>DO NOT SUBMIT any archived output</h2><ul>' + ''.join('<li>' + link('downloads/' + path.name, path.name) + ' — learning/audit only, not cleared</li>' for path in archived) + '</ul>'
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
        cmp_rows = [[esc(r['label']), f"{r['n_dots']:,}", number(r['model_T'], 1),
                     number(r['model_surrogate_dti']),
                     (f"<strong>{number(r['owner_reported_score'])}</strong>"
                      if r.get('owner_reported_score') else '&mdash;')]
                    for r in rc['contradicting_instruments']['model_compare']]
        h57k_page = f'''<div class="eyebrow">H57-K CANDIDATE · BUILT, VALID, NOT CLEARED</div><h1>A second opinion on the overlap rule.</h1>
<div class="warning"><strong>Download for review; do not submit.</strong> This file is portal-valid and unique by every statistic that can discriminate, but it fails protocol rule 1 exactly as written. This page does not claim an exemption.</div>
<section class="stat-grid"><div class="stat"><span>Local format</span><strong>{sum(1 for v in rc['validator_output']['checks'].values() if v)}/{len(rc['validator_output']['checks'])}</strong><small>Every portal check passes</small></div>
<div class="stat"><span>Dots</span><strong>{sb['dots']['n_dots']:,}</strong><small>None on the mapped catalogue</small></div>
<div class="stat"><span>Worst Spearman</span><strong>{number(uq['worst_spearman_full_footprint'])}</strong><small>Required &le;0.90 · PASS</small></div>
<div class="stat"><span>Worst forward overlap</span><strong>{uq['worst_forward_overlap_discriminating_only']:.0%}</strong><small>Discriminating rasters only · literal FAIL</small></div></section>
<section><h2>Download (review only)</h2><p><a class="button" href="downloads/{esc(Path(sb['file']).name)}">Download {esc(Path(sb['file']).name)}</a> &middot; <a href="downloads/{esc(Path(sb['file']).with_suffix('.zip').name)}">single-TIFF .zip</a></p>
<p class="small">SHA256 <code>{esc(sb['sha256'])}</code> · {sb['bytes']:,} bytes. Note ({sb['note_chars']}/140 chars): <code>{esc(sb['note'])}</code></p></section>
<section><h2>The science worked; the gate did not.</h2>
<p>Strand expression &mdash; whether a pixel inside a damage zone actually carries the geophysical signature of a fault &mdash; was added to the lane geometry the prompt asks for, using the official 19-band GeoDAWN stack that no earlier session of this repository had. No angle is hard-coded; every weight is fitted on the holdout.</p>
{table(['Arm', 'Features', 'HOLDOUT-DTI', '95% CI'], arm_rows)}
<p class="small">{esc(rc['holdout']['evaluator'])}. {rc['holdout']['n_cells']} cells, {rc['holdout']['n_withheld_positives']:,} withheld positives. The geophysical term's +0.008 over lane geometry sits inside the intervals, so it is reported as measured, not as a win.</p></section>
<section><h2>Why it is not cleared</h2>
<p>{number(uq['worst_forward_overlap_all'] * 100, 1)}% of its dots fall within 3&nbsp;px of <code>r13-lattice-s5</code>, whose 3&nbsp;px halo covers 0.9987 of the footprint. Rule 1's prescribed action is to log a duplicate and stop. This session measured that clause before relying on it and found it cannot be passed by <em>any</em> nonempty dot set: the same clause also fires for this family's own OWNER-REPORTED 0.2778 submission, at 0.999 against that same lattice.</p>
<p>That conclusion is not unique to this run. An independent session of this repository already certified the same obstruction from a different witness &mdash; <code>{esc(sat.get('source', ''))}</code>, positive over the entire allowed domain, giving every candidate forward overlap {number(sat.get('covered_allowed_fraction'), 2)}. Two sessions, two witnesses, one finding.</p>
<p>An earlier session recorded the remedy explicitly: <strong>resolve the obstruction through an owner protocol revision</strong>, not by redefining support, exempting dense maps, adding a reverse-overlap condition, or choosing another raster after STOP. This run honours that. Verdict <strong>{esc(rc['verdict'])}</strong>; promotion ready <strong>no</strong>.</p>
<p>{link('data/h57k_run_card.json', 'Run card JSON')} &middot; {link('data/h57k_submission.json', 'Uniqueness and validator receipt')} &middot; {link('data/h57k_exact_duplicate_check.json', 'Byte-identity check vs 655 registry rasters')}</p></section>
<section><h2>The contradiction I could not resolve</h2>
<p>{esc(rc['contradicting_instruments']['live_anchored'])}. Against that, {esc(rc['contradicting_instruments']['holdout_model'])}.</p>
{table(['Excluded band', 'Dots', 'Modelled T', 'Surrogate DTI', 'Median distance'], sweep_rows)}
<p>Only the &le;&nbsp;2&nbsp;px exclusion is a measurement, so only that was imposed. The emission sits at median <strong>{number(rc['contradicting_instruments']['emission_median_distance_to_catalogue_px'], 1)}&nbsp;px</strong> from the mapped catalogue, where every raster in this family that has ever been scored sits at ~19.6&nbsp;px. That is the largest reason it could underperform, independent of the gate.</p>
<h3>The same surface scored on rasters that were really submitted</h3>
{table(['Dot field', 'Dots', 'Modelled T', 'Surrogate DTI', 'Owner-reported'], cmp_rows)}
<p>The model credits this session's field with roughly five times the modelled credit of the 0.2778 raster, yet under-credits that raster fourfold against its actual owner-reported score. Its own number is therefore not a score, and is not presented as one.</p></section>
<section><h2>A template bug found and fixed here</h2>
<p><code>gems57.emit.allocate_by_marginal_bar</code> breaks at the first candidate failing the DTI test, but marginal credit depends on local kernel saturation, not rank, so on this surface's flat plateaus it stopped at 3,405 dots. <code>allocate_patient</code> keeps the identical test and stops only after <code>patience</code> consecutive rejections: 62,872 dots, surrogate DTI 0.0832 &rarr; 0.2927. Fixed once, in the shared template, with regression tests; the original function is retained for callers and comparison.</p></section>'''
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
    print(f"Built {len(pages)} evidence-led pages. Download "
          f"{'OK' if card['okay_to_download'] else 'NOT OK'}; submission "
          f"{'CLEARED (selector still decides)' if card['okay_to_submit'] else 'HELD'}. "
          f"No model run or slot used by this build.")
    return card


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--no-preview', action='store_true', help='reuse the existing numeric preview during feed-only builds')
    a = p.parse_args()
    build(make_preview=not a.no_preview)


if __name__ == '__main__':
    main()
