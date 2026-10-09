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
       ('results.html', 'Results'), ('method.html', 'Method'), ('research.html', 'Research'),
       ('sources.html', 'Sources'), ('irregularities.html', 'Audit')]
PUBLIC = ['run_card_current', 'orientation_holdout', 'orientation_canary', 'orientation_structure',
          'hypotheses_current', 'irregularities_current', 'source_checks', 'registry_classification',
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
    filename = Path(card['file']).name
    zipname = Path(card['zip_file']).name
    validator = card['validator_output']
    return f'''<section class="download-panel" aria-labelledby="download-title">
<div class="eyebrow">NEW GEOTIFF · GENERATED OCT 9, 2026</div><h1 id="download-title">A new file. An honest verdict.</h1>
<p class="hero-sub">Learned magnetic-edge orientation around visible faults.<br>Fresh predictions—not a copy of an earlier submission.</p>
<div class="permissions"><span class="permission yes">Download for research: OK</span><span class="permission no">Submit to competition: NO</span></div>
<p class="hold-reason"><strong>HOLD · DO NOT SUBMIT:</strong> the mandatory forward-overlap gate failed. No demonstrated binary holdout gain. No production dots placed; no weekly slot used.</p>
<div class="actions"><a class="button primary" href="downloads/{esc(filename)}" download>↓ Download GeoTIFF <span>{validator['bytes']/1_000_000:.2f} MB</span></a>
<a class="button secondary" href="downloads/{esc(zipname)}" download>Single-TIFF ZIP</a><a class="text-link" href="executive-summary.html">Submission guide →</a></div>
<details class="file-details"><summary>Exact filename, SHA256 and note</summary><p class="mono">{esc(filename)}</p><p class="mono">SHA256 {esc(card['raster_sha256'])}</p>
<p>Suggested note ({card['submission_note_chars']} / 140 characters):</p><p class="mono" id="submission-note">{esc(card['submission_note'])}</p><button class="copy-button" type="button" data-copy="submission-note">Copy note</button>
<p class="small">The filename's ID hashes decoded pixels. The SHA256 above hashes the actual downloaded TIFF. {link('data/run_card.json', 'Download complete run card')}.</p></details></section>'''


def evidence_notice(card):
    score = card['holdout_dti']
    return f'''<p class="evidence-note"><strong>Local evidence only.</strong> Evaluator <code>{esc(score['evaluator_version'])}</code> · {score['withheld_positive_pixels']:,} withheld positive pixels · pooled terms · 95% spatial-block bootstrap CI. No live submission score or private-label claim.</p>'''


def build(root=ROOT, make_preview=True):
    docs = root / 'docs'
    data = docs / 'data'
    data.mkdir(parents=True, exist_ok=True)
    evidence = {name: json.loads((root / 'evidence' / f'{name}.json').read_text()) for name in PUBLIC}
    card = evidence['run_card_current']
    if card['okay_to_submit'] or card['verdict'] != 'negative':
        raise ValueError('This site release is a held negative experiment, not an authorized selector.')
    if not (root / card['file']).is_file() or not (root / card['zip_file']).is_file():
        raise FileNotFoundError('current downloadable raster/ZIP missing; no historical fallback')
    for name in PUBLIC:
        shutil.copyfile(root / 'evidence' / f'{name}.json', data / f'{name}.json')
    shutil.copyfile(root / 'evidence/run_card_current.json', data / 'run_card.json')
    for name in ['feed_refresh_status', 'review_passes', 'sibling_page_reviews', 'browser_qa', 'registry_concurrent_extension', 'registry_open_pr_extension', 'uniqueness_current_review', 'uniqueness_concurrent_extension', 'uniqueness_open_pr_extension']:
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
    raw = card['holdout_dti']
    dots = card['holdout_dot_dti']
    panel = download_panel(card)
    disclaimer = evidence_notice(card)
    names = {'distance_only': 'Distance only', 'anatomy': 'Visible-host anatomy',
             'orientation': 'Anatomy + relative magnetic tangent', 'orientation_sense': 'Candidate + recorded sense (ablation)'}
    score_rows = []
    for name in names:
        s, d = holdout['raw_surface_holdout']['scores'][name], holdout['scores'][name]
        score_rows.append([esc(names[name]), f"{number(s['dti'])} {interval(s['ci95'])}", f"{number(d['dti'])} {interval(d['ci95'])}", f"{d['withheld_positive_pixels']:,}"])
    score_table = table(['Method', 'Soft-surface HOLDOUT-DTI [95% CI]', 'Binary-allocation HOLDOUT-DTI [95% CI]', 'Withheld positives'], score_rows)
    canary = evidence['orientation_canary']
    canary_rows = [[f'<code>{esc(k)}</code>', number(v['discriminative_auc_max']), 'PASS (< 0.90)' if not v['leakage_flag'] else '<strong>LEAKAGE FLAG</strong>'] for k, v in canary['features'].items()]
    max_auc = max(v['discriminative_auc_max'] for v in canary['features'].values())

    index = panel + f'''<section class="stat-grid" aria-label="Current research diagnostics">
<div class="stat"><span>Local format</span><strong>PASS</strong><small>Finite Float32 · one band · [0, 1]</small></div>
<div class="stat"><span>Registry audit</span><strong>{registry['registry_rasters_checked']} / {registry['registry_rasters_expected']}</strong><small>All accessible pinned grid rasters</small></div>
<div class="stat"><span>Worst forward overlap</span><strong>{registry['worst_dot_overlap']:.0%}</strong><small>Required ≤70% · FAIL</small></div>
<div class="stat"><span>Weekly slots spent</span><strong>0</strong><small>Three predeclared comparisons completed</small></div></section>
<section class="two-column"><div><div class="eyebrow">THE SCIENTIFIC RESULT</div><h2>Orientation did not earn a slot.</h2>
<p>The candidate's binary-allocation <strong>HOLDOUT-DTI is {number(dots['dti'])}</strong>, 95% CI {interval(dots['ci95'])}. Distance-only is {number(holdout['scores']['distance_only']['dti'])}, with its own CI in the results table. Their paired interval includes zero. Recorded sense also has no demonstrated gain and is not retained.</p>
<p>The downloadable file is a <strong>soft research surface</strong>, not those test-fold dots. Its method's HOLDOUT-DTI is <strong>{number(raw['dti'])}</strong>, 95% CI {interval(raw['ci95'])}. Do not attach the binary score to this TIFF.</p>{disclaimer}
<p>{link('results.html', 'Inspect all comparisons →')}</p></div><figure class="map-preview"><img src="assets/preview.png" alt="North-up display of the new relative-strand research surface on the bridged competition grid" width="600" height="680"><figcaption>Actual research surface · north ↑ · EPSG:32611. Downsampled maximum with nonlinear display colors; not ground truth, a vent map or the submitted pixel values.</figcaption></figure></section>
<section class="card"><div class="eyebrow">REVIEW FOUND A REAL BUG</div><h2>Every valid host strike had been reset to zero.</h2><p>A reversed finite-value fallback corrupted the earlier host-relative geometry. It is fixed, with regressions for east–west offsets and hidden-value invariance. Earlier orientation interpretations and the interrupted run are invalidated, not recycled as evidence.</p><p>{link('irregularities.html', 'IR-57-STRIKE-01 and other audit findings →')}</p></section>
<section><h2>Why the overlap rule cannot clear any nonempty candidate</h2><p>One earlier dense soft raster is positive over the entire footprint. Under the inherited literal definition of a dot—<code>finite prediction &gt; 0</code>—every allowable nonempty candidate has forward overlap 1.0 with it. This is a measured obstruction, not permission to invent a density or reverse-overlap exemption.</p><p>{link('data/uniqueness_saturation_certificate.json', 'Hash-verified saturation certificate')} · {link('data/orientation_surface_uniqueness.json', 'All per-raster checks')}</p></section>
<section class="card feed-card"><div class="eyebrow">PUBLIC ORGANIZER FEED · NOT A FILE RECEIPT</div><h2>Leaderboard context</h2><p><strong id="leaderboard-top">{number(evidence['leaderboard_snapshot']['top_public_dti'])}</strong> <span id="leaderboard-context">top public DTI in the last successful organizer snapshot</span></p><p id="feed-status" aria-live="polite">Checked on 2026-10-09. Date-precision snapshot; open the official board for current context.</p><p>{link('https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/', 'Official leaderboard')} · {link('data/leaderboard_snapshot.json', 'Timestamped snapshot')}</p><p class="small">Scheduled Pages builds refresh this public feed. Failures retain the prior snapshot with a visible freshness warning. Neither the team's remaining slots nor its private score is known.</p></section>'''

    executive = panel + f'''<section><h2>Read this before opening “New submission”</h2><div class="warning"><strong>Do not submit this release.</strong> Downloading the actual TIFF or ZIP is safe for review. Local format PASS is not organizer acceptance, uniqueness clearance or permission to use a weekly slot.</div>
<p>{registry['duplicate_count']} registry comparisons triggered a literal duplicate condition. Worst rank correlation is {number(registry['worst_spearman_full_footprint'])} (below 0.90); worst forward overlap is {registry['worst_dot_overlap']:.2f} (above 0.70). Pixel and byte identity checks pass, but that alone is not the protocol.</p></section>
<section><h2>Exact submission steps—for a future selector-cleared file</h2><ol class="steps"><li><strong>Check the release card.</strong> Require format PASS, full-registry surface PASS before placement, final-dot PASS, clean canaries and a positive paired holdout gain. A separate selector must clear the real slot.</li>
<li><strong>Download the .tif, or the single-TIFF .zip.</strong> Do not upload this HTML page, a JSON receipt, a PDF or a ZIP of the repository. Our ZIP is round-trip checked to contain exactly one GeoTIFF.</li>
<li><strong>Open the competition submission page.</strong> {link('https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/', 'DrivenData: submissions')}. Log in, accept the official rules and check the logged-in weekly counter. The published rules say three submissions per week; remaining team capacity is unknown here.</li>
<li><strong>Choose the cleared file under “File to submit.”</strong> Keep its unique filename; paste its ≤140-character note. Only then submit, if the separate selector has approved it. This project never clicks Submit for you.</li>
<li><strong>Preserve the organizer receipt.</strong> Record exact filename, TIFF SHA256, note, timestamp, evaluation version and submission-page score. A public board value cannot prove which bytes earned it.</li></ol></section>
<section><h2>What fixes the reported range-error risk?</h2><p>The rejected file bytes are unavailable, so its cause is <strong>not established</strong>. The public description permits null/NaN outside the bounds. As a conservative precaution our shared writer refuses nonfinite or out-of-range predictions, writes finite zeros outside the footprint, and validates the TIFF after reading it back. It never silently clips bad caller values.</p>
{table(['Local check', 'This TIFF'], [[esc(k), 'PASS' if v else 'FAIL'] for k, v in card['validator_output']['checks'].items()])}
<p>Metadata: 1 band · Float32 · EPSG:32611 · 3730 × 3292 · transform <code>(100, 0, 243350, 0, -100, 4508550)</code>. Min {card['validator_output']['min']:.1f}, max {card['validator_output']['max']:.8f}, no NaN/Inf, zero positive mass on the known catalogue or outside the footprint. Header/footprint are verified against the bridge, not an authenticated official template.</p></section>'''

    delta = holdout['paired_differences']['distance_only']
    anatomy_delta = holdout['paired_differences']['anatomy']
    sense = holdout['sense_comparison']
    results = f'''<div class="eyebrow">THREE PREDECLARED EXPERIMENTS · ZERO SUBMISSIONS</div><h1>Negative is a deliverable.</h1>{disclaimer}
{score_table}<p class="small">Each arm uses the same fold masks and nominal 10,000-dot per-quadrant cap, shrunk by its training-only fitted-zone fraction. These are different representations, not interchangeable scores. Conditional CI: 1,000 paired draws from 153 physical 20 km clusters; catalogue labels and fitted models are held fixed.</p>
<h2>The comparisons that matter</h2>{table(['Comparison', 'Paired HOLDOUT-DTI difference', '95% CI', 'Verdict'], [["Candidate minus distance-only (binary)", number(delta['delta']), interval(delta['ci95']), 'No demonstrated improvement'], ["Candidate minus anatomy (binary)", number(anatomy_delta['delta']), interval(anatomy_delta['ci95']), 'No demonstrated added orientation value'], ["Recorded-sense addition (binary)", number(sense['delta']), interval(sense['ci95']), 'Not significant; sense not retained']])}
<p>These comparisons use 11,321 withheld positives and <code>gems57-pooled-hide-v2</code>. The historical 0.2279 reading is not a comparable best: it used the corrupted strike field and a different short-chunk, unbuffered instrument. A static prior generated from the unhidden catalogue is also not a valid hide-and-recover comparator.</p>
<h2>Soft surfaces do not rescue a negative dot result</h2><p>Relative orientation improves the soft-surface point estimate against distance-only, but its added soft value over anatomy is {number(holdout['raw_surface_holdout']['paired_differences']['anatomy']['delta'])}, 95% CI {interval(holdout['raw_surface_holdout']['paired_differences']['anatomy']['ci95'])}. That includes zero. No unpredeclared representation switch is used to claim promotion.</p>
<h2>Leakage canaries</h2><p>Every feature alone was tested before trusting the fit. We use <code>max(AUC, 1−AUC)</code> in every fold, so an inverse distance feature cannot hide leakage. Maximum discriminative AUC: {number(max_auc)}; all 14 are below 0.90. Passing this check does not prove all possible leakage absent.</p>{table(['Feature', 'Max discriminative fold AUC (diagnostic)', 'Canary'], canary_rows)}
<h2>Full-registry gate</h2>{table(['Measurement (not DTI)', 'Result'], [['Accessible grid rasters checked', str(registry['registry_rasters_checked'])], ['Worst full-footprint tied-rank Spearman', number(registry['worst_spearman_full_footprint'])], ['Worst candidate-to-prior ≤3 px forward overlap', number(registry['worst_dot_overlap'])], ['Triggered comparisons', str(registry['duplicate_count'])], ['Byte / decoded-pixel identity', 'Distinct from all checked entries'], ['Literal protocol', '<strong>FAIL → STOP</strong>'], ['Production final dots', 'Not generated: pre-placement gate failed']])}
<p>The {registry['registry_rasters_checked']}-raster audit conservatively includes four historical auxiliary input rasters; {registry['registry_rasters_checked'] - 4} are predictions or retained ambiguous grid rasters. Classification is disclosed, not used to clear the gate. All 57 listed repositories were scanned at pinned public-main commits, unioned with historical pins. Private, unlinked or inaccessible artifacts remain outside scope.</p><p>{link('data/orientation_holdout.json', 'Full HOLDOUT-DTI receipt')} · {link('data/orientation_surface_uniqueness.json', 'Complete registry measurements')} · {link('data/registry_classification.json', 'Input/prediction classification')}</p>'''

    structure = evidence['orientation_structure']
    method = f'''<div class="eyebrow">SHARED INSTRUMENT · NO PRIVATE FORKS</div><h1>Measure the anatomy. Don’t assume it.</h1>
<section><h2>Catalogue-blind candidate evidence, visible-only hosts</h2><p>Band 14 (<code>tmi</code>) is a scalar magnetic field. Gaussian derivatives provide an axial edge tangent, log-gradient magnitude and structure coherence. The angle feature is <code>cos(2 × (candidate strike − primary strike))</code>. It is not the angle of a pixel’s offset from the host.</p><p>The visible catalogue supplies nearest-host distance, cross-/along-strike offsets, axial strike, coherence, density and log component pixel count. Component count is a <strong>noisy mapped-length proxy</strong>, not measured displacement. A histogram-gradient-boosted intensity learns interactions; no textbook Riedel angle, damage-width exponent or assumed dextral sense is inserted.</p><p>Recorded slip sense is used only where a record matches visible context, and its incremental value is explicitly ablated. The final research surface omits it because the paired lower confidence bound is not positive.</p></section>
<section><h2>Whole-component, buffered hide-and-recover</h2><ol><li>Withhold whole original 8-connected raster fault components, rather than ≤12-pixel chunks. Components may still be fragments of geological systems.</li><li>Remove a 3-pixel (300 m) visible-catalogue context collar around held traces. Apply a 12-pixel quadrant-boundary erosion. Derive all catalogue features only from the globally visible context.</li><li>Leave one quadrant out when fitting each model. Evaluation domains are label-blind. Mask the exact unhidden known catalogue, not its 300 m dilation; the buffer is feature-context removal, not a new scoring mask.</li><li>Fit zone radius from the training withheld-distance 90th percentile and shrink the nominal dot cap by training-positive occupancy in that zone. Estimate positive count from training prevalence only—never oracle test-positive count.</li><li>Pool TPw/FPw/FNw before computing DTI. Resample paired, aligned physical 20 km block terms. Never average quadrant DTI as if it were pooled DTI.</li></ol>{disclaimer}</section>
<section><h2>Descriptive geometry is not a universal shear angle</h2><p>On this draw the 10th / 50th / 90th percentiles of withheld-positive nearest-visible-host distance are {number(structure['distance_positive_quantiles_px'][0], 1)}, {number(structure['distance_positive_quantiles_px'][1], 2)}, and {number(structure['distance_positive_quantiles_px'][2], 2)} pixels (100 m per pixel). The saved array uses probabilities [0.10, 0.50, 0.90, 0.95, 0.99], not quartiles. Relative-strike summaries are censored nearest-component diagnostics, not a significance test and not a validated stress inversion.</p><p>{link('data/orientation_structure.json', 'Descriptive distributions and null caveat')} · {link('data/experiment_plan.json', 'Predeclared comparisons')}</p></section>
<section><h2>Why sparse placement and precision matter</h2><p>For binary predictions, let <em>T</em> be maximum triangular-kernel coverage of truth pixels, <em>M</em> prediction self-credit, <em>N</em> prediction count, and <em>K</em> truth count. The official-formula arithmetic becomes:</p><pre>DTI = T / (0.2 T + 0.2 N − 0.2 M + 0.8 K)</pre><p>Max-cover means overlapping dots cannot repeatedly buy the same coverage. A dot far from every new-fault pixel adds false-positive cost without coverage. A dot near a known trace gets no credit merely for that proximity. This is why geometry, calibration and the emitted dot budget must all be tested—large probabilities and an impressive-looking lineament image are not scores.</p></section>
<section><h2>Reproduce locally</h2><pre>python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
PYTHON=.venv/bin/python bash scripts/download_competition_data.sh --cache-bands
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/refresh_registry.py
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_orientation_experiments.py --build-research-surface --minutes 65
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_site.py</pre><p>CPU only. These commands reproduce the same declared experiments, not permission to add trials or spend slots. Restore the ignored feature stack and registry cache after a new checkout. Historical in-sample/oracle-budget builders are disabled.</p></section>'''

    hypothesis_rows = []
    for h in evidence['hypotheses_current']['candidates']:
        hypothesis_rows.append([str(h['rank']), f"<strong>{esc(h['id'])}: {esc(h['hypothesis'])}</strong><p>{esc(h['signature'])}</p>", '<br>'.join(esc(x) for x in h['layers']), esc(h['why_missing_faults']), esc(h['difference_from_repo']), f"{esc(h['expected_improvement'])}<br>{esc(h['implementation_cost'])}", f"{esc(h['non_fault_mimic'])}<p>{esc(h['status'])}</p>"])
    hypotheses = f'''<div class="eyebrow">BEFORE CODE · QUALITATIVE EXPECTATIONS, NOT SCORES</div><h1>Four new questions. One tested lead.</h1><p>The ranking was declared before implementation. Novelty means different from the inspected repository implementations; it is not proof that no sibling or researcher has ever tried it. No numeric leaderboard forecasts are assigned.</p>
{table(['Rank', 'Hypothesis & physical signature', 'Layers', 'Why a missing strand?', 'Difference from existing work', 'Expected improvement / cost', 'Non-fault mimic / status'], hypothesis_rows)}
<p>H57-G was the top candidate. E1 rebuilt controls, E2 tested candidate-to-host relative magnetic strike, and E3 ablated recorded sense. Three comparisons are complete. Multi-scale bends, two-host superposition and sense transitions were not run; a single-sense ablation is not a sense-transition test.</p><p>Required band/geometry data were obtained and hash verified; source-origin and attribute-matching caveats remain. No extra experiment is launched to rescue the negative result.</p>'''

    research = f'''<div class="eyebrow">CAUSAL CLAIMS REQUIRE MORE THAN A LEADERBOARD</div><h1>What can explain the reported 0.2778?</h1><div class="warning">0.2778 is <strong>OWNER-REPORTED</strong> for the named GEMSDOE32 file. No organizer submission-page receipt attributes that score to its exact bytes. The public board’s matching participant value does not close that gap.</div>
<section><h2>What we independently established</h2><p>H33-2-B2 is exactly its 40,199-dot GEMSDOE28 base minus 2,545 dots at catalogue distance ≤2 pixels, leaving 37,654. No dots were added or relocated. The canonical TIFF SHA256 is <code>c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9</code>. This is a construction measurement, not a scoring receipt.</p><p>{link('data/best_submission_audit.json', 'Independent construction audit')} · {link('https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/registry/submission_build.json', 'Original construction source')}</p></section>
<section><h2>A plausible metric mechanism—not a proven geological cause</h2><p>Its inherited sparse dots can cover distinct truth pixels more efficiently than a broad low-confidence field, while pruning can reduce false-positive cost if the removed dots contribute little unique coverage. That is mathematically plausible under the max-cover metric. It does not establish that the file discovered specific secondary strands or that the 2-pixel exclusion caused a hidden-label gain.</p><p>New geometry can lie next to known geometry. Therefore a blind catalogue halo exclusion can remove true new-fault pixels as well as redundant false positives. A single reported best result, uncontrolled pipeline differences and repeated reuse across sites cannot isolate causality. We use the construction only for learning—not as a base, a feature or a copied output.</p></section>
<section><h2>Can this lane exceed 0.2778?</h2><p>There is no metric ceiling at that value, but <strong>this experiment does not demonstrate a higher submission</strong>. Its held-out binary relative-orientation candidate does not beat the recomputed distance-only control. The soft candidate’s added value over anatomy is also uncertain. A local catalogue-hide CI is not a forecast of newly mapped expert labels or private-round performance.</p><p>The earlier claim that host orientation adds no value was additionally undermined by the finite-strike bug: constant sin2/cos2 cannot express a host-direction interaction. The corrected test now yields a defensible negative for this particular feature/scale/model, not proof that damage-zone mechanics is useless.</p></section>
<section><h2>Why the geological mechanism remains difficult</h2><ul><li><strong>Mechanics ≠ universal geometry.</strong> Schreurs’ analogue arrays and the classical Tchalenko framework justify testing secondary-strand anatomy, not enforcing one angle across mixed normal/dextral systems.</li><li><strong>Length ≠ displacement.</strong> Savage–Brodsky support distance decay and changing zone-width relationships; raster connectivity is an uncertain local displacement proxy, affected by trace fragmentation and mapping completeness.</li><li><strong>Magnetic edge ≠ fault.</strong> Dikes, contacts, topography-dependent clearance and east–west leveling stripes can mimic a strand. Area 2’s 400 m flight-line spacing is coarse relative to a 300 m scoring kernel; 100 m output pixels do not create independent 100 m survey resolution.</li><li><strong>Catalogue hiding ≠ discovery truth.</strong> Existing faults and new expert annotations differ in mapping bias, scale and location. Clean canaries and spatial separation reduce specific leakage risks, not all domain shift.</li><li><strong>Fault map ≠ geothermal-vent map.</strong> Faults can support permeability, but this target has no heat, fluid-flow or reservoir-economic labels. No geothermal-vent or resource-discovery claim follows from this TIFF alone.</li></ul></section>
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
<h2>Remaining work—before any promotion</h2><ol><li>Resolve the universal literal overlap obstruction only through an explicit protocol revision. Do not quietly redefine soft support, exempt dense maps, add a reverse-overlap condition or choose another raster after STOP.</li><li>Obtain organizer receipts to authenticate exact file-to-score attribution and the official data/template provenance chain. Do not ask for or store credentials in chat.</li><li>In a new budgeted session, test at most the next predeclared anatomy hypothesis against corrected spatial controls. Require positive paired evidence and both uniqueness phases before a separate selector considers a slot.</li><li>Strengthen geological-system holdouts, record matching and domain-shift diagnostics. Verify actual fault displacement indicators; investigate magnetic contacts/flight-line mimics.</li><li>Keep source/feed timestamps visible. AI-assisted code and analysis must be disclosed according to the official rules if entering finalist materials.</li></ol><p>{link('data/irregularities_current.json', 'Audit JSON')} · {link('data/review_passes.json', 'Three-pass verification record')} · {link('archive.html', 'Archived outputs—invalid/held, never submit')}</p>'''

    runcard = '<div class="eyebrow">THE COMPLETE RECEIPT</div><h1>Run card · negative</h1><p>Download OK; submit NO. Format validity and pixel identity are not uniqueness clearance.</p><p>' + link('data/run_card.json', 'Download JSON') + '</p><pre>' + esc(json.dumps(card, indent=2, allow_nan=False)) + '</pre>'
    archive = '''<div class="eyebrow">HISTORICAL EVIDENCE ONLY</div><h1>Archived files are not cleared submissions.</h1><p>Earlier outputs in downloads or archives are preserved for learning and audit. They have invalidated geometry, suspect leakage, in-sample scoring, partial registries or failed uniqueness gates. None is recommended for submission. Current evidence is the held release linked on the overview; do not select an old file to bypass STOP.</p><p><a href="index.html">Return to the current release →</a></p>'''
    archived = sorted(path for path in (root / 'docs/downloads').glob('*.tif') if path.name != Path(card['file']).name)
    archive += '<h2>DO NOT SUBMIT any archived output</h2><ul>' + ''.join('<li>' + link('downloads/' + path.name, path.name) + ' — learning/audit only, not cleared</li>' for path in archived) + '</ul>'
    pages = {'index.html': ('Overview', index), 'executive-summary.html': ('Download & submit', executive),
             'results.html': ('Results', results), 'method.html': ('Method', method),
             'hypotheses.html': ('Hypotheses', hypotheses), 'research.html': ('Research', research),
             'sources.html': ('Sources', sources), 'data-sources.html': ('Data & sources', sources),
             'irregularities.html': ('Audit', irregularities), 'run-card.html': ('Run card', runcard),
             'archive.html': ('Archive warning', archive), 'session-3.html': ('Archived session', archive)}
    for filename, (title, body) in pages.items():
        (docs / filename).write_text(page(title, body, filename, stamp))
    # Preserve the old /docs/index.html URL after switching to artifact-based Pages.
    aliases = docs / 'docs'
    aliases.mkdir(exist_ok=True)
    for filename in pages:
        (aliases / filename).write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../{filename}"><title>57GEMSDOE · moved</title></head><body><p>Research release HOLD; not cleared for submission. <a href="../{filename}">Open current page</a>.</p></body></html>')
    (docs / '.nojekyll').touch()
    print(f'Built {len(pages)} evidence-led pages. Download OK; submission HOLD. No model run or slot used.')
    return card


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--no-preview', action='store_true', help='reuse the existing numeric preview during feed-only builds')
    a = p.parse_args()
    build(make_preview=not a.no_preview)


if __name__ == '__main__':
    main()
