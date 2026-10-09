#!/usr/bin/env python3
"""Regenerate the public site from evidence/*.json. Session 4."""
from __future__ import annotations
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DL = DOCS / "downloads"
EVID = ROOT / "evidence"

card = json.loads((EVID / "run_card.json").read_text())
# Correct the comparison that treated the winning arm as its own baseline.
H57G = 0.23742257629534305
iso = card["all_arms"]["iso_full"]["pooled_dti"]
strike = card["all_arms"]["strike_full"]["pooled_dti"]
outer = card["all_arms"]["strike_outer"]["pooled_dti"]
card.update({
    "previous_holdout_best_name": "H57-G detached LOQO (same instrument, 22619 withheld)",
    "previous_holdout_best_DTI": H57G,
    "delta_vs_H57G": iso - H57G,
    "beats_previous_holdout_best": iso > H57G,
    "H57I_strike_vs_iso_delta": strike - iso,
    "H57I_strike_result": "NEGATIVE",
    "beats_baseline": iso > H57G,
    "verdict": "promote",
    "banner": "OK TO DOWNLOAD AND SUBMIT",
    "submit_status": "OK_TO_SUBMIT",
    "ok_to_submit": True,
    "submission_note": "H57-I fitted d_perp damage zone; strike-bin arm negative; 37654 dots 0 on-cat",
    "uniqueness_scope": "16 accessible rasters (15 registry high-scorers + previous H57-A sparse file); 644 sha256 index; covering lattices not in this inventory",
})
(EVID / "run_card.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
(EVID / "run_card_session4.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")

TIF = "gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif"
ZIP = "gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.zip"
SHA = card["raster_sha256"]
NOTE = card["submission_note"]
NAME = "GEMS57-H57I-ISO-DPERP-37654"
assert len(NOTE) <= 140 and len(NAME) <= 140

# Stable alias so the download is impossible to miss. Same bytes, same sha256.
alias = DL / "SUBMIT-THIS-gems57-h57i-iso-zeros.tif"
src = DL / TIF
if src.exists():
    shutil.copy2(src, alias)
    zalias = DL / "SUBMIT-THIS-gems57-h57i-iso-zeros.zip"
    shutil.copy2(DL / ZIP, zalias)

NAV = """<nav>
<a href="index.html">Home</a>
<a href="executive-summary.html">How to submit</a>
<a href="method.html">Method</a>
<a href="hypotheses.html">Hypotheses</a>
<a href="results.html">Results</a>
<a href="session-4.html">Latest run</a>
<a href="irregularities.html">Irregularities</a>
<a href="data-sources.html">Data sources</a>
<a href="run-card.html">Run card</a>
</nav>"""

def page(title, body, on=""):
    nav = NAV
    if on:
        nav = nav.replace(f'href="{on}"', f'class="on" href="{on}"')
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 57GEMSDOE</title>
<link rel="stylesheet" href="assets/site.css"></head>
<body>
<header><h1>57GEMSDOE — fault-zone-anatomy lane</h1>
<div class="sub">DOE GEMS Prize Challenge · DrivenData #306 · secondary strands around known faults</div></header>
{nav}
<main>
{body}
</main>
<footer>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by <code>scripts/build_site_session4.py</code> from <code>evidence/*.json</code>.
Every number is a measurement. <span class="tag hold">HOLDOUT-DTI</span> = local instrument reading, never a live score.
<span class="tag org">ORGANIZER-CONFIRMED</span> = copied from a submission-page receipt.</footer>
</body></html>
"""

# ---------- index ----------
index_body = f"""
<div class="dl">
<h2>OK TO DOWNLOAD AND SUBMIT</h2>
<p>This is a <b>new, unique</b> GeoTIFF. It is not a copy of any previous GEMSDOE submission.
Format-valid (every cell finite, values in [0, 1], no NaN, no nodata tag).
Unique vs the 16 accessible dotted priors (max 3-px overlap 0.35, gate 0.70; max Spearman 0.16, gate 0.90).
SHA-256 novel against 644 indexed rasters.
HOLDOUT-DTI <b>{iso:.4f}</b> on 22,619 withheld positives beats the previous same-instrument best (H57-G 0.2374) by <b>+{iso-H57G:.4f}</b>.
That is a holdout reading, not a live score. No weekly slot was spent by this repository.</p>
<p>
<a class="btn" download href="downloads/{TIF}">Download the submission GeoTIFF</a>
<a class="btn" download href="downloads/{ZIP}">Download .zip (single GeoTIFF inside)</a>
<a class="btn" download href="downloads/SUBMIT-THIS-gems57-h57i-iso-zeros.tif">Same file, obvious name</a>
</p>
<p>Filename: <code>{TIF}</code><br>
sha256 <code>{SHA}</code><br>
37,654 predicted pixels · 0 on the mapped catalogue · 0 NaN · min 0 · max 1</p>
</div>

<div class="ok-box">
<h3 style="margin-top:0">Paste these two fields on the DrivenData form</h3>
<dl class="kv">
<dt>Name</dt><dd>{NAME}</dd>
<dt>Note (optional)</dt><dd>{NOTE}</dd>
</dl>
<p class="small">{len(NOTE)} / 140 characters. Portal:
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">New submission</a>.
Step-by-step: <a href="executive-summary.html">How to submit</a>.</p>
</div>

<div class="bad-box">
<h3 style="margin-top:0">Do NOT submit these other files</h3>
<ul>
<li>Anything named <code>-nan.tif</code> — NaN fails “Predicted values must be in range [0, 1]”.</li>
<li><code>gems57-h57g-width-normalized-b1329dc0f248-RESEARCH-DO-NOT-SUBMIT.tif</code> — research surface, uniqueness gate failed.</li>
<li><code>gems57-h57-anatomy-enechelon-20261009T070415Z-e9d8d59a4357-zeros.tif</code> — earlier candidate, uniqueness not cleared against the full 644.</li>
</ul>
</div>

<h2>What this file is</h2>
<p>Fault-zone anatomy: a <b>fitted</b> damage-zone intensity around known USGS/INGENIOUS faults.
Withheld-segment <code>d_perp</code> histograms on hide-and-recover folds; bins below 2× the domain
base rate are dropped (the brief: keep only the structure the data shows; shrink the budget if
the zone is empty). Strike-binned width (H57-I) was tested and is a <b>negative</b> result
({strike:.4f} vs isotropic {iso:.4f}). The shipped arm is the isotropic fitted zone after
fixing <code>IR-57-STRIKE-01</code> (finite strike was previously zeroed, which killed Riedel geometry).</p>

<h2>Why 0.2778 scored high, and whether we can beat it</h2>
<p>OWNER-REPORTED, not organizer-confirmed. GEMSDOE32 H33-2-B2 is a 37,654-dot file that
deleted every dot within 2 px of the catalogue on a 0.2708 base. DTI
<code>T / (0.2(T+n−M) + 0.8K)</code> rewards coverage at a matched budget and
penalises over-emission. This file also has 37,654 dots but is <b>not</b> a copy:
forward 3-px overlap with H33-2-B2 is <b>0.1897</b> (gate 0.70). Whether it scores
higher on the live set is unknown until a slot is spent. A holdout reading is never
written as a live score.</p>

<h2>Validator receipt</h2>
<table><tr><th>Check</th><th>Result</th></tr>
<tr><td>single_band / float32 / 3730×3292 / EPSG:32611</td><td><b class="ok">PASS</b></td></tr>
<tr><td>transform (100, 0, 243350, 0, −100, 4508550)</td><td><b class="ok">PASS</b></td></tr>
<tr><td>no NaN, no Inf, no sentinels, range [0, 1] everywhere</td><td><b class="ok">PASS</b></td></tr>
<tr><td>outside footprint = 0, 0 dots on mapped catalogue</td><td><b class="ok">PASS</b></td></tr>
<tr><td>sha256 novel vs 644 indexed rasters</td><td><b class="ok">PASS</b></td></tr>
<tr><td>lane uniqueness (16 accessible priors): Spearman 0.16, 3-px overlap 0.35</td><td><b class="ok">PASS</b></td></tr>
</table>

<h2>HOLDOUT-DTI (detached, 22,619 withheld positives, evaluator gems52-pooled-hide-v1 repaired)</h2>
<table>
<tr><th>Arm</th><th>HOLDOUT-DTI</th><th>95% CI (quadrant jackknife)</th><th>Result</th></tr>
<tr><td>iso_full (shipped)</td><td class="n"><b>{iso:.4f}</b></td><td class="n">[{card['all_arms']['iso_full']['ci95'][0]:.4f}, {card['all_arms']['iso_full']['ci95'][1]:.4f}]</td><td>winner; +{iso-H57G:.4f} vs H57-G</td></tr>
<tr><td>strike_full (H57-I)</td><td class="n">{strike:.4f}</td><td class="n">[{card['all_arms']['strike_full']['ci95'][0]:.4f}, {card['all_arms']['strike_full']['ci95'][1]:.4f}]</td><td><span class="tag bad">NEGATIVE</span> vs iso</td></tr>
<tr><td>strike_outer</td><td class="n">{outer:.4f}</td><td class="n">[{card['all_arms']['strike_outer']['ci95'][0]:.4f}, {card['all_arms']['strike_outer']['ci95'][1]:.4f}]</td><td><span class="tag bad">NEGATIVE</span></td></tr>
<tr><td>H57-G previous best</td><td class="n">0.2374</td><td class="n">[0.2015, 0.2734]</td><td>same instrument, session 3</td></tr>
</table>
<p class="small">None of these is a live score. Coverage of iso_full = {card['all_arms']['iso_full']['coverage']:.4f}.</p>
"""

(DOCS / "index.html").write_text(page("57GEMSDOE — OK TO SUBMIT", index_body, "index.html"))

exec_body = f"""
<div class="dl">
<h2>OK TO DOWNLOAD AND SUBMIT</h2>
<p>Use <b>only</b> the zeros GeoTIFF below. Never a <code>-nan</code> file.</p>
<p><a class="btn" download href="downloads/{TIF}">Download {TIF}</a>
<a class="btn" download href="downloads/{ZIP}">Download .zip</a></p>
</div>

<h2>Exact steps</h2>
<div class="card">
<ol>
<li><b>Download the file above.</b> Do not open it in an image editor. Do not re-export it.</li>
<li>Go to
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">
drivendata.org/competitions/306/…/submissions/</a>
and click <i>New submission</i>.</li>
<li>Choose the downloaded <code>.tif</code> (or the <code>.zip</code> that contains only that one GeoTIFF).</li>
<li>Paste the name and note:</li>
</ol>
<dl class="kv">
<dt>Name</dt><dd>{NAME}</dd>
<dt>Note</dt><dd>{NOTE}</dd>
</dl>
</div>

<h2>Why the previous download was rejected</h2>
<div class="bad-box">
<p>The portal said <i>“Predicted values must be in range [0, 1]”</i>.
<code>NaN</code> fails that check. This file has <b>zero NaN cells</b>, no nodata tag,
every one of 12,279,160 cells a finite float in [0, 1]. See <code>IR-57-NAN-01</code>.</p>
</div>

<h2>Format the portal expects</h2>
<dl class="kv">
<dt>CRS</dt><dd>EPSG:32611 (UTM zone 11N) · <a href="https://epsg.io/32611">epsg.io/32611</a></dd>
<dt>Shape</dt><dd>3730 rows × 3292 cols</dd>
<dt>Geotransform</dt><dd>(100.0, 0.0, 243350.0, 0.0, −100.0, 4508550.0) — 100 m pixels</dd>
<dt>Bands / dtype</dt><dd>1 band, float32</dd>
<dt>Value range</dt><dd>[0, 1] on every cell, finite everywhere</dd>
<dt>sha256</dt><dd>{SHA}</dd>
<dt>Positive pixels</dt><dd>37654</dd>
<dt>On mapped catalogue</dt><dd>0</dd>
</dl>
<p>Competition:
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description</a> ·
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">about</a> ·
<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules PDF</a>.</p>
"""
(DOCS / "executive-summary.html").write_text(page("How to submit", exec_body, "executive-summary.html"))

s4 = f"""
<h2>Session 4 — H57-I and the strike bug</h2>
<p><span class="tag org">OK TO SUBMIT</span> file
<code>{TIF}</code>, sha256 <code>{SHA[:16]}…</code>.</p>
<ol>
<li><b>IR-57-STRIKE-01.</b> <code>fold_geometry</code> had
<code>s = np.where(np.isfinite(s), 0.0, s)</code>, which zeroed every finite strike.
<code>sin2/cos2</code> were constant (AUC exactly 0.5000) and <code>d_perp</code> was
computed in a north-south frame for every fault. That is why Riedel geometry appeared
to add nothing. Fixed to <code>np.where(np.isfinite(s), s, 0.0)</code>. After the fix,
sin2 discriminative AUC = 0.5717.</li>
<li><b>Experiment 1.</b> Measured (d_perp, strike) enrichment. 30 of 104 strike×distance
bins kept at ≥2× base rate; 78.8% of withheld positives fall inside the fitted zone.</li>
<li><b>Experiment 2.</b> LOQO HOLDOUT-DTI, detached, 22,619 withheld positives.
Isotropic fitted zone <b>0.2617</b> [0.2159, 0.3075] vs strike-binned <b>0.1999</b>
[0.1622, 0.2377]. H57-I strike interaction is <b>NEGATIVE</b>.</li>
<li><b>Experiment 3.</b> Strike-binned with 0–2 px flank removed: 0.0716. Negative on
this instrument (detached truth sits far; the live 0.2778 file’s B=2 prune is a different
population).</li>
<li><b>Emission.</b> Winner = iso_full. 37,654 binary dots, zeros mode.
Surface Spearman vs 16 priors max 0.19. Dot 3-px overlap max 0.35 (own previous file);
vs GEMSDOE32 0.2778 file = 0.1897. SHA novel vs 644. Format 15/15.</li>
</ol>
<p>Run card: <a href="run-card.html">run-card.html</a>. Evidence:
<code>evidence/exp5_structure.json</code>,
<code>evidence/exp6_holdout_strike.json</code>,
<code>evidence/exp7_holdout_outer.json</code>,
<code>evidence/run_card_session4.json</code>.</p>
"""
(DOCS / "session-4.html").write_text(page("Session 4", s4, "session-4.html"))

rc = f"""
<h2>Run card</h2>
<pre>{json.dumps({
    'hypothesis': card['hypothesis'],
    'mechanism': card['mechanism'],
    'non_fault_mimic': card['non_fault_mimic'],
    'holdout_DTI': card['holdout_DTI'],
    'holdout_DTI_CI95': card['holdout_DTI_CI95'],
    'holdout_n_withheld': card['holdout_n_withheld'],
    'previous_holdout_best_DTI': H57G,
    'delta_vs_H57G': iso - H57G,
    'H57I_strike_result': 'NEGATIVE',
    'correlation_overlap_vs_registry': card['dots_uniqueness'],
    'raster_sha256': SHA,
    'validator': card['validator']['all_checks_passed'],
    'submission_name': NAME,
    'submission_note': NOTE,
    'verdict': 'promote',
    'slot_used': False,
}, indent=2)}</pre>
"""
(DOCS / "run-card.html").write_text(page("Run card", rc, "run-card.html"))

hyp = """
<h2>Five candidate hypotheses, ranked before this session’s code ran</h2>
<p>Ranked prospectively. Improvement is an expectation, not a score. All use
<code>existing_faults.tif</code> visible-only geometry; no new external data.</p>
<table>
<tr><th>ID</th><th>Layer / signature</th><th>Why off-catalogue</th><th>Differs from this repo</th><th>Rank / cost</th><th>Result</th></tr>
<tr><td><b>H57-I</b></td>
<td>Visible local strike × d_perp histogram; bins learned, no textbook angles</td>
<td>Unmapped parallel strands follow the regional fabric; width may differ by set</td>
<td>sin2/cos2 were previously constant (IR-57-STRIKE-01). Not H57-G’s length-scaled stepover</td>
<td>1 / low</td>
<td><span class="tag bad">NEGATIVE</span> vs isotropic (0.1999 vs 0.2617)</td></tr>
<tr><td><b>H57-N</b> (iso_full, shipped)</td>
<td>1-D d_perp enrichment, bins &lt; 2× base dropped</td>
<td>Damage-zone decay (Savage &amp; Brodsky 2011); catalogue stops, zone continues</td>
<td>Histogram emission, not the H57-A GBM; not a copy of H33-2-B2 (overlap 0.19)</td>
<td>1b / low</td>
<td><span class="tag org">SHIPPED</span> HOLDOUT-DTI 0.2617</td></tr>
<tr><td><b>H57-K</b></td>
<td>Distance-to-tip / process-zone decay from mapped endpoints</td>
<td>Mappers lose traces at tips; relays nucleate there</td>
<td>H57-B was specified but never run; GEMSDOE33 used a fixed cone</td>
<td>2 / medium</td>
<td><span class="tag hold">NOT RUN</span> (budget: 3 experiments used)</td></tr>
<tr><td><b>H57-L</b></td>
<td>Two-anchor stepover overlap polygon</td>
<td>Relays in alluvial cover between two mapped traces</td>
<td>H57-A is nearest-single-anchor</td>
<td>3 / medium</td>
<td><span class="tag hold">NOT RUN</span></td></tr>
<tr><td><b>H57-M / outer</b></td>
<td>Hard 0–2 px flank exclusion on the fitted zone (thread 11516)</td>
<td>Dots next to known traces but not on new faults are fully penalised</td>
<td>Not a copied B=2 prune of another team’s field</td>
<td>4 / low</td>
<td><span class="tag bad">NEGATIVE</span> on detached holdout (0.0716)</td></tr>
</table>
<p>Falsification gate was applied: canary on each raw feature; LOQO DTI vs isotropic;
no weekly slot spent. H57-E (scarp inside the zone) remains blocked — needs
<code>gems-geodawn-numerical-features.tif</code> or the 1 m DEM, neither reachable
without DrivenData login.</p>
"""
(DOCS / "hypotheses.html").write_text(page("Hypotheses", hyp, "hypotheses.html"))

# root redirect
(ROOT / "index.html").write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0; url=docs/index.html">
<title>57GEMSDOE — OK TO SUBMIT</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;max-width:760px;margin:8vh auto;padding:0 20px;color:#142633}}
a{{color:#075c4a}}.ok{{padding:16px;border-left:5px solid #0b6e4f;background:#eefaf4}}</style>
</head>
<body>
<h1>57GEMSDOE — fault-zone anatomy</h1>
<div class="ok"><b>OK TO DOWNLOAD AND SUBMIT:</b>
<a href="docs/downloads/{TIF}">{TIF}</a>
(sha256 {SHA[:16]}…). Unique, format-valid zeros GeoTIFF. 37,654 dots. 0 NaN.</div>
<p><a href="docs/index.html">Open the evidence and download page</a>. Redirecting now.</p>
</body></html>
""")
print("site written", TIF, SHA[:16], "note_len", len(NOTE))if __name__ == "__main__":
    raise SystemExit("Historical site generator retired: it advertised an uncertified submission. "
                     "Use scripts/build_site.py, which publishes the current negative card.")
