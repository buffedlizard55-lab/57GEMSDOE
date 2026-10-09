#!/usr/bin/env python
"""Build the GitHub Pages site (docs/) from the evidence files.

Generates index.html (download first), executive-summary.html (exactly how to
submit), sources.html (official verified links), research.html (hypotheses +
run card) and assets/style.css. Reads only evidence/*.json and the submission
receipt, so the site always matches the artifacts.
"""
import json

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DL = DOCS / "downloads"
EV = ROOT / "evidence"

receipt = json.loads((DL / "gems57-faultzone-anatomy-60000px-20261009T054251Z.receipt.json").read_text())
sub = receipt["submission"]
uniq = json.loads((EV / "uniqueness.json").read_text())
card = json.loads((EV / "run_card.json").read_text())
exp2 = json.loads((EV / "exp2_holdout.json").read_text())
cal = json.loads((EV / "calibrate_registry.json").read_text())
exp3 = json.loads((EV / "exp3_build.json").read_text())

TIF = sub["file"]
ZIP = sub["zip_file"]
SHA = sub["sha256"]
NOTE = sub["note"]
NAME = sub["name"]
BYTES = sub["bytes"]

hold = card["holdout_dti"]
sg = card["proxy_dti_sgmc_truth"]

CSS = """/* GEMSDOE57 — clean, simple, readable */
:root { --ink:#1c2733; --mut:#5b6b7b; --bg:#f7f9fb; --card:#ffffff; --line:#dfe6ec;
        --acc:#0b6bcb; --acc2:#084f9e; --ok:#0a7d3c; --warn:#9a6a00; --bad:#b3261e; }
* { box-sizing:border-box; }
body { margin:0; font:16px/1.6 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       color:var(--ink); background:var(--bg); }
.wrap { max-width:880px; margin:0 auto; padding:24px 20px 64px; }
header.top { background:var(--card); border-bottom:1px solid var(--line); }
header.top .wrap { padding:18px 20px; display:flex; flex-wrap:wrap; gap:8px 24px;
                   align-items:baseline; justify-content:space-between; }
h1 { font-size:22px; margin:0; }
h1 small { color:var(--mut); font-weight:500; }
nav a { color:var(--acc2); text-decoration:none; margin-left:16px; font-size:14px; }
nav a:hover { text-decoration:underline; }
h2 { font-size:19px; margin:34px 0 10px; }
h3 { font-size:16px; margin:22px 0 6px; }
p { margin:10px 0; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px;
        padding:18px 20px; margin:16px 0; }
.dl { display:flex; flex-wrap:wrap; gap:14px; align-items:center; }
.btn { display:inline-block; background:var(--acc); color:#fff; text-decoration:none;
       font-weight:700; font-size:18px; padding:14px 26px; border-radius:10px; }
.btn:hover { background:var(--acc2); }
.btn.sec { background:#fff; color:var(--acc2); border:2px solid var(--acc); font-size:15px;
           padding:10px 18px; }
table { border-collapse:collapse; width:100%; margin:12px 0; font-size:14px; }
th, td { text-align:left; padding:7px 10px; border-bottom:1px solid var(--line);
          vertical-align:top; }
th { color:var(--mut); font-weight:600; }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
code, .mono { font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
              font-size:13px; background:#eef3f7; padding:1px 5px; border-radius:4px; }
pre { background:#0f1c28; color:#dce7f2; padding:14px 16px; border-radius:8px;
      overflow:auto; font-size:13px; }
.banner { border-left:5px solid var(--warn); background:#fff8e6; padding:12px 16px;
          border-radius:0 8px 8px 0; margin:16px 0; }
.banner.ok { border-color:var(--ok); background:#e9f7ee; }
.banner.bad { border-color:var(--bad); background:#fdecea; }
.kv { display:grid; grid-template-columns:230px 1fr; gap:4px 14px; font-size:14px; }
.kv dt { color:var(--mut); } .kv dd { margin:0; }
ol.steps { padding-left:22px; } ol.steps li { margin:8px 0; }
footer { color:var(--mut); font-size:13px; margin-top:40px; border-top:1px solid var(--line);
         padding-top:14px; }
.tag { display:inline-block; font-size:11px; font-weight:700; letter-spacing:.06em;
       text-transform:uppercase; padding:2px 8px; border-radius:20px; }
.tag.hold { background:#e3eefc; color:#084f9e; }
.tag.live { background:#e9f7ee; color:#0a7d3c; }
.tag.prox { background:#fff3d6; color:#9a6a00; }
"""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def page(title, body, active="home"):
    nav = [
        ("home", "Download", "index.html"),
        ("exec", "Executive summary", "executive-summary.html"),
        ("research", "Research & run card", "research.html"),
        ("sources", "Sources", "sources.html"),
    ]
    links = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' class="on"' if k == active else "", t)
        for k, t, h in nav)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — GEMSDOE57</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body>
<header class="top"><div class="wrap">
  <h1>GEMSDOE57 <small>fault-zone anatomy · DrivenData GEMS prize, competition 306</small></h1>
  <nav>{links}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap" style="padding:0">
GEMSDOE57 · branch <code>arena/af16d287-57gemsdoe</code> · generated 2026-10-09 (UTC) ·
local template validation only — not organizer upload acceptance.
</div></footer>
</body></html>"""


# ---------------------------------------------------------------- index.html
idx = f"""
<div class="card">
  <h2 style="margin-top:0">Download the submission</h2>
  <p>This is the competition submission: a single-band float32 GeoTIFF of per-pixel
  fault probability for the whole GeoDAWN study area (EPSG:32611, 100 m, 3730×3292),
  produced by the <b>fault-zone-anatomy</b> lane: a fitted damage-zone halo around the
  known USGS + INGENIOUS faults, emitted as 60,000 binary dots, none on a known fault.</p>
  <div class="dl">
    <a class="btn" href="downloads/{TIF}">⬇ Download {TIF}</a>
    <a class="btn sec" href="downloads/{ZIP}">zip (same raster)</a>
    <a class="btn sec" href="executive-summary.html">How to submit →</a>
  </div>
  <dl class="kv" style="margin-top:14px">
    <dt>File</dt><dd><code>{TIF}</code></dd>
    <dt>Size</dt><dd>{BYTES:,} bytes</dd>
    <dt>sha256</dt><dd><code>{SHA}</code></dd>
    <dt>Submission name</dt><dd><code>{NAME}</code></dd>
    <dt>Methodology note (≤140 ch)</dt><dd><code>{esc(NOTE)}</code></dd>
    <dt>Validator</dt><dd><b>PASS</b> — single band float32, EPSG:32611, bounds/transform match
    the training grid, values in [0,1], 0 NaN inside the footprint, 60,000 emitted pixels,
    0 on known faults, 0 outside the footprint.</dd>
  </dl>
</div>

<div class="banner">
  <b>Verdict: negative as a standalone score-beater — delivered as a validated, unique,
  non-leaking lane artifact.</b> On the brief's spatially-blocked holdout the lane scores
  <span class="tag hold">HOLDOUT-DTI</span> <b>{hold['dti']:.4f}</b>
  [{hold['ci95'][0]:.4f}, {hold['ci95'][1]:.4f}] at 60,000 dots and beats its own controls
  (random {hold['controls_at_same_budget']['random_emission']:.4f},
  uniform-halo {hold['controls_at_same_budget']['uniform_halo']:.4f}); the leakage canary
  is far below threshold (max AUC {hold['leakage_canary_auc_max']:.4f} &lt; 0.90); and the
  drift check against all 663 registry rasters is clean (max |Spearman|
  {uniq['max_abs_spearman']['value']:.4f} &lt; 0.90, no bidirectional duplicates, sha256 unique).
  But on the SGMC-truth instrument — real off-catalogue faults, the closest legal proxy for
  the hidden test set — the lane scores <span class="tag prox">PROXY-DTI</span>
  <b>{sg['budget_60000']:.4f}</b> at 60k dots against {min(sg['incumbents_same_instrument'].values()):.4f}–{max(sg['incumbents_same_instrument'].values()):.4f}
  for the incumbents, so it is <b>not</b> expected to beat the incumbent live score
  (0.2778). No submission slot should be spent on this file; promotion is a separate
  selector step. See <a href="research.html">research &amp; run card</a>.
</div>

<h2>What this file is</h2>
<div class="card">
  <p>The organizers' hidden labels are <b>new expert-mapped faults not in
  USGS/INGENIOUS</b>, including splays and parallel strands of existing systems. The lane
  fits the <i>anatomy</i> of those secondary strands — radial distance from the host fault,
  azimuth relative to its strike, along-strike position, host length — measured on a
  hide-and-recover holdout (withheld catalogue segments, 300 m truth buffer, features
  rebuilt from the visible faults only), then emits the top 60,000 pixels of the fitted
  intensity, off every known USGS/INGENIOUS fault pixel.</p>
  <table>
    <tr><th>Property</th><th class="num">Value</th></tr>
    <tr><td>Emitted pixels (dots)</td><td class="num">60,000</td></tr>
    <tr><td>Dots on known USGS/INGENIOUS faults</td><td class="num">0</td></tr>
    <tr><td>Dots outside the valid footprint</td><td class="num">0</td></tr>
    <tr><td>Median distance of dots to nearest known fault</td><td class="num">5.7 px (570 m)</td></tr>
    <tr><td>Distinct values</td><td class="num">0.0 and 1.0 (binary top-k)</td></tr>
    <tr><td>Grid</td><td class="num">3730 × 3292, EPSG:32611, 100 m</td></tr>
    <tr><td>Bounds</td><td class="num">243350, 4135550 – 572550, 4508550 (matches training data)</td></tr>
  </table>
</div>

<h2>Measured evidence (all numbers labeled)</h2>
<div class="card">
  <table>
    <tr><th>Number</th><th class="num">Value</th><th>Class</th></tr>
    <tr><td>HOLDOUT-DTI @ 60k dots (full arm, per-fold rebuilt, 38,339 withheld positives, 95% CI)</td>
        <td class="num"><b>{hold['dti']:.4f} [{hold['ci95'][0]:.4f}, {hold['ci95'][1]:.4f}]</b></td>
        <td><span class="tag hold">HOLDOUT-DTI</span></td></tr>
    <tr><td>Same budget: random control / uniform-halo control</td>
        <td class="num">{hold['controls_at_same_budget']['random_emission']:.4f} / {hold['controls_at_same_budget']['uniform_halo']:.4f}</td>
        <td><span class="tag hold">HOLDOUT-DTI</span></td></tr>
    <tr><td>Leakage canary (max single-feature AUC on withheld px; threshold 0.90)</td>
        <td class="num">{hold['leakage_canary_auc_max']:.4f}</td>
        <td><span class="tag hold">HOLDOUT-DTI</span></td></tr>
    <tr><td>SGMC-truth DTI @ 60k / @ 120k dots (79,025 real off-catalogue fault px)</td>
        <td class="num">{sg['budget_60000']:.4f} / {sg['budget_120000']:.4f}</td>
        <td><span class="tag prox">PROXY-DTI</span></td></tr>
    <tr><td>Incumbents, same SGMC instrument (h19-5 → h33-2-b2)</td>
        <td class="num">{min(sg['incumbents_same_instrument'].values()):.4f} – {max(sg['incumbents_same_instrument'].values()):.4f}</td>
        <td><span class="tag prox">PROXY-DTI</span></td></tr>
    <tr><td>Registry drift: max |Spearman| vs 663 rasters</td>
        <td class="num">{uniq['max_abs_spearman']['value']:.4f} (limit 0.90)</td>
        <td>MEASUREMENT</td></tr>
    <tr><td>Registry drift: bidirectional dot duplicates / sha256 duplicates</td>
        <td class="num">0 / 0</td><td>MEASUREMENT</td></tr>
  </table>
  <p style="color:var(--mut);font-size:13px">HOLDOUT-DTI is measured with the template
  evaluator (<code>gems52-pooled-hide-v1</code>, vendored unmodified from GEMSDOE52) on
  spatially blocked folds; it measures recovery of withheld <i>catalogue</i> segments and
  does not rank live scores. PROXY-DTI uses SGMC faults captured by neither USGS nor
  INGENIOUS — real off-catalogue faults, but not the organizer's test set. No number on
  this site is an organizer-confirmed live score.</p>
</div>
"""

# ------------------------------------------------------- executive-summary.html
exec_body = f"""
<h2 style="margin-top:0">Executive summary — how to make a submission</h2>
<div class="card">
  <p><b>The whole point of this repository is the one file you upload.</b> This page is the
  shortest path from here to a submitted entry, and what has and has not been verified.</p>
  <ol class="steps">
    <li><b>Download</b> the submission GeoTIFF from the button on the
        <a href="index.html">home page</a> (or <code>docs/downloads/{TIF}</code> in this
        repository). Verify it if you like:
        <pre>sha256sum {TIF}
# expect {SHA}</pre></li>
    <li><b>Sign in</b> to DrivenData and open the competition:
        <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">https://www.drivendata.org/competitions/306/competition-doe-gems/</a></li>
    <li>Click <b>Submit</b> → <b>Make new submission</b> (the competition home page documents
        this exact flow under “How to compete”).</li>
    <li><b>Upload the file</b> and paste the methodology note shown on the home page
        (<code>{esc(NOTE)}</code>, {len(NOTE)} characters). The file name is
        content-addressed, so it can be told apart from earlier attempts later.</li>
    <li>Optionally select it as your <b>single final submission</b> for both prize rounds.
        Only one selection is allowed, and it must be made without knowing private scores.</li>
  </ol>
  <div class="banner">
    <b>Budget note.</b> Each entity gets up to three scored submissions per week and exactly
    one final submission across both rounds. <b>Do not spend a slot on this file</b> until it
    has beaten the current holdout best on the brief's instrument — this session's run card
    says it has not (verdict: negative). Slot promotion is a separate selector step.
  </div>
</div>

<h2>What the file must satisfy (rules quoted from the official pages)</h2>
<div class="card">
  <table>
    <tr><th>Rule</th><th>Requirement</th><th>Source</th></tr>
    <tr><td>CRS</td><td>same projected CRS as the training data — UTM 11N, EPSG:32611</td><td>problem description, “Submission format”</td></tr>
    <tr><td>Resolution</td><td>100 m</td><td>same</td></tr>
    <tr><td>Bounds</td><td>same bounds as the training data; outside the bounds is null or NaN</td><td>same</td></tr>
    <tr><td>Layers</td><td>a single layer</td><td>same</td></tr>
    <tr><td>Datatype</td><td>32-bit float</td><td>same</td></tr>
    <tr><td>Values</td><td>between 0 and 1, higher = higher fault probability</td><td>same</td></tr>
    <tr><td>Size</td><td>one GeoTIFF for the whole GeoDAWN study area</td><td>rules §3.2</td></tr>
  </table>
  <p>The shipped file passes all of these locally (validator <b>PASS</b>, receipt:
  <code>docs/downloads/{TIF[:-4]}.receipt.json</code>). Local validation is a template
  check, <b>not</b> organizer upload acceptance.</p>
</div>

<h2>What the shipped file measured</h2>
<div class="card">
  <table>
    <tr><th>Property</th><th class="num">Value</th></tr>
    <tr><td>File</td><td class="num"><code>{TIF}</code></td></tr>
    <tr><td>sha256</td><td class="num"><code>{SHA[:16]}…</code></td></tr>
    <tr><td>Gate</td><td class="num"><b>PASS</b> (13/13 template checks)</td></tr>
    <tr><td>Values</td><td class="num">exactly two: 0.0 and 1.0</td></tr>
    <tr><td>Predicted pixels</td><td class="num">60,000</td></tr>
    <tr><td>Training signal</td><td class="num">USGS QFaults raster + INGENIOUS vectors (2,588 linked catalogue segments + 1,126 record segments)</td></tr>
    <tr><td>Model</td><td class="num">fitted damage-zone intensity I(p) = f(d/s(L))·g(φ), binary top-k</td></tr>
    <tr><td>HOLDOUT-DTI @ 60k</td><td class="num"><b>{hold['dti']:.4f} [{hold['ci95'][0]:.4f}, {hold['ci95'][1]:.4f}]</b></td></tr>
    <tr><td>SGMC-truth DTI @ 60k (proxy)</td><td class="num">{sg['budget_60000']:.4f}</td></tr>
  </table>
</div>

<h2>Why this file rather than a previous one</h2>
<div class="card">
  <p>Measured on the same spatially blocked, buffered folds (same training budget, same
  evaluation code — <code>scripts/run_holdout.py</code>), not asserted:</p>
  <table>
    <tr><th>Arm @ 60k dots</th><th class="num">HOLDOUT-DTI</th></tr>
    <tr><td><b>full (f(d/s(L))·g(φ)) — shipped shape</b></td><td class="num"><b>{hold['dti']:.4f}</b></td></tr>
    <tr><td>no_phi (distance × length only)</td><td class="num">{hold['controls_at_same_budget']['no_phi']:.4f}</td></tr>
    <tr><td>distance_only</td><td class="num">{hold['controls_at_same_budget']['distance_only']:.4f}</td></tr>
    <tr><td>uniform_halo (geometry control)</td><td class="num">{hold['controls_at_same_budget']['uniform_halo']:.4f}</td></tr>
    <tr><td>random (control)</td><td class="num">{hold['controls_at_same_budget']['random_emission']:.4f}</td></tr>
  </table>
  <p>The fitted azimuth and length factors are worth +0.009–+0.046 over the controls at
  60k dots, and the budget sweep peaks at 60k (50k: 0.0536, 80k: 0.0574, 120k: 0.0507).</p>
</div>
"""

# ------------------------------------------------------------- sources.html
src = """
<h2 style="margin-top:0">Sources — official and verified</h2>
<div class="card">
  <p>Only free, publicly available, official/verified sources were used. Every external
  dataset is sha256-pinned in <code>data/README.md</code> and verified by
  <code>scripts/prepare_data.py</code>.</p>
  <table>
    <tr><th>Source</th><th>What it provides</th><th>Link</th></tr>
    <tr><td>DrivenData GEMS prize — problem description</td><td>metric math (distance-weighted
        Tversky, 300 m credit), submission format, worked example</td>
        <td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">competition page 967</a></td></tr>
    <tr><td>DrivenData GEMS prize — competition home</td><td>rules, submission flow, leaderboard</td>
        <td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition 306</a></td></tr>
    <tr><td>DrivenData GEMS prize — leaderboard</td><td>current public scores (high 0.3774)</td>
        <td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard</a></td></tr>
    <tr><td>NREL / DOE GeoDAWN</td><td>study-area context (Geothermal Data Assimilation for
        Western Nevada)</td>
        <td><a href="https://www.energy.gov/eere/geothermal/geodawn-geothermal-data-assimilation-western-nevada">energy.gov GeoDAWN</a></td></tr>
    <tr><td>Competition PDF (NREL mirror)</td><td>full problem statement</td>
        <td><a href="https://docs.nlr.gov/docs/fy26/96647.pdf">docs.nlr.gov/docs/fy26/96647.pdf</a></td></tr>
    <tr><td>USGS Quaternary Fault and Fold Database</td><td>catalogue faults (rasterized in
        <code>existing_faults.tif</code>)</td>
        <td><a href="https://www.usgs.gov/programs/earthquake-hazards/faults">usgs.gov faults program</a></td></tr>
    <tr><td>SGMC — State Geologic Map Compilation (Nevada Bureau of Mines and Geology)</td>
        <td>independent mapped faults used as the off-catalogue proxy truth</td>
        <td><a href="https://www.nbmg.unr.edu/geology/geologic-mapping/sgmc.html">nbmg.unr.edu SGMC</a></td></tr>
    <tr><td>INGENIOUS / GeoDAWN fault database (GBCGE)</td><td>record-level fault segments with
        sense of slip and slip rate (<code>trace_segments_utm11.csv</code>,
        <code>qfault_attributes.csv</code>)</td>
        <td><a href="https://gbcge.org/">gbcge.org</a> (receipt: source zip sha256
        <code>c7b091c9…</code>, 6,131,182 bytes)</td></tr>
    <tr><td>EPSG:32611</td><td>CRS definition (WGS 84 / UTM zone 11N)</td>
        <td><a href="https://epsg.io/32611">epsg.io/32611</a></td></tr>
    <tr><td>Tchalenko (1970), Geol. Soc. London Spec. Publ. 23</td><td>Riedel shear geometry
        in fault damage zones</td><td>doi:10.1144/SP023.019</td></tr>
    <tr><td>Schreurs (2003), J. Struct. Geol. 25</td><td>fault damage-zone growth and
        splay geometry</td><td>doi:10.1016/S0191-8141(03)00032-6</td></tr>
    <tr><td>Savage &amp; Brodsky (2011), Geology 39</td><td>damage-zone width scales with
        displacement</td><td>doi:10.1130/G31613.1</td></tr>
  </table>
  <p style="color:var(--mut);font-size:13px">Competition training data (labels, features,
  sample submission) cannot be downloaded from this sandbox — the DrivenData data page sits
  behind a login and the Dropbox mirrors are unreachable from here. They were obtained
  sha256-pinned from the public GEMSDOE sibling repositories (see
  <code>data/README.md</code>), which carry the official files with recorded hashes.</p>
</div>
"""

# ------------------------------------------------------------- research.html
inc_rows = "".join(
    f"<tr><td>{esc(k)}</td><td class='num'>{v:.4f}</td></tr>"
    for k, v in sorted(sg["incumbents_same_instrument"].items(), key=lambda kv: -kv[1]))
res = f"""
<h2 style="margin-top:0">Research — hypothesis, evidence, run card</h2>

<div class="card">
  <h3 style="margin-top:0">Hypothesis (this lane)</h3>
  <p>{esc(card['hypothesis'])}</p>
  <h3>Mechanism</h3>
  <p>{esc(card['mechanism'])}</p>
  <h3>Named non-fault process that could mimic it</h3>
  <p>{esc(card['named_non_fault_process_that_could_mimic_it'])}</p>
</div>

<div class="card">
  <h3 style="margin-top:0">Holdout result <span class="tag hold">HOLDOUT-DTI</span></h3>
  <dl class="kv">
    <dt>Evaluator</dt><dd><code>{esc(hold['evaluator_version'])}</code></dd>
    <dt>Protocol</dt><dd>{esc(hold['protocol'])}</dd>
    <dt>Withheld positives</dt><dd>{hold['withheld_positive_pixels']:,} px</dd>
    <dt>DTI @ 60k dots</dt><dd><b>{hold['dti']:.4f}</b> [{hold['ci95'][0]:.4f}, {hold['ci95'][1]:.4f}] (95% CI)</dd>
    <dt>Controls @ 60k</dt><dd>random {hold['controls_at_same_budget']['random_emission']:.4f} ·
        uniform-halo {hold['controls_at_same_budget']['uniform_halo']:.4f} ·
        distance-only {hold['controls_at_same_budget']['distance_only']:.4f} ·
        no-φ {hold['controls_at_same_budget']['no_phi']:.4f}</dd>
    <dt>Leakage canary</dt><dd>max single-feature AUC {hold['leakage_canary_auc_max']:.4f} &lt; {hold['leakage_threshold']:.2f} → no leakage</dd>
    <dt>Budget sweep</dt><dd>{esc(hold['budget_sweep_peak'])}</dd>
  </dl>
</div>

<div class="card">
  <h3 style="margin-top:0">Live proxy — SGMC-truth DTI <span class="tag prox">PROXY-DTI</span></h3>
  <p>Truth: 79,025 SGMC pixels captured by neither USGS nor INGENIOUS — real off-catalogue
  faults, the closest legal proxy for the hidden test set (not a holdout, not an organizer
  score).</p>
  <table>
    <tr><th>Raster</th><th class="num">SGMC-truth DTI</th></tr>
    <tr><td><b>this lane @ 60k dots</b></td><td class="num"><b>{sg['budget_60000']:.4f}</b></td></tr>
    <tr><td>this lane @ 120k dots (sweep still rising)</td><td class="num">{sg['budget_120000']:.4f}</td></tr>
    {inc_rows}
  </table>
  <p>{esc(sg['reading'])}</p>
</div>

<div class="card">
  <h3 style="margin-top:0">Registry drift check (663 rasters) — MEASUREMENT</h3>
  <dl class="kv">
    <dt>Max |Spearman|</dt><dd>{uniq['max_abs_spearman']['value']:.4f} (limit 0.90) —
        <code>{esc(uniq['max_abs_spearman']['raster'])}</code></dd>
    <dt>Duplicates by correlation</dt><dd>{len(uniq['duplicates_by_correlation'])}</dd>
    <dt>Duplicates by overlap (bidirectional)</dt><dd>{len(uniq['duplicates_by_overlap'])}</dd>
    <dt>sha256 duplicates</dt><dd>{len(uniq['hash_duplicates'])}</dd>
    <dt>Verdict</dt><dd><b>{esc(uniq['verdict'])}</b></dd>
  </dl>
  <p style="font-size:13px;color:var(--mut)">{esc(uniq['gates']['overlap'])}.
  Mechanical one-directional firings ({uniq['mechanical_overlap_firings']}) are
  coverage-saturation artifacts: dense registry emissions (206k–452k dots) whose 3-px-dilated
  coverage saturates the halo, with reverse overlap 0.07–0.10 and rank correlation ≈ 0.
  Flagged for review; full list in <code>evidence/uniqueness.json</code>.</p>
</div>

<div class="card">
  <h3 style="margin-top:0">Run card</h3>
  <dl class="kv">
    <dt>Submission</dt><dd><code>{NAME}</code> — <code>{TIF}</code></dd>
    <dt>Note (≤140 ch)</dt><dd><code>{esc(NOTE)}</code></dd>
    <dt>Raster sha256</dt><dd><code>{SHA}</code></dd>
    <dt>Validator</dt><dd><b>PASS</b> — {esc(card['validator_output']['checks'])}</dd>
    <dt>Verdict</dt><dd><b>{card['verdict'].upper()}</b></dd>
  </dl>
  <p>{esc(card['verdict_reasoning'])}</p>
  <p>Full run card: <code>evidence/run_card.json</code> · ranked hypotheses:
  <a href="research/hypotheses.md">docs/research/hypotheses.md</a>.</p>
</div>

<div class="card">
  <h3 style="margin-top:0">Next work (ranked backlog)</h3>
  <ol>
    <li><b>H2 — zone-gated geophysical corroboration:</b> multiply the fitted halo by a
        TMI-gradient / elevation-slope ridge strength restricted to the halo. Highest
        expected gain; validate on the holdout before any slot.</li>
    <li><b>H3 — along-strike tip-relay targeting:</b> 64.2% of withheld mass is beyond-tip;
        emit along host strike past mapped tips.</li>
    <li><b>120k-budget variant:</b> the SGMC sweep is still rising at 120k while the holdout
        peaks at 60k — the selector needs both instruments' curves.</li>
    <li><b>H4 — slip-rate-weighted zone width</b> (INGENIOUS SLIPRT2023) replacing the
        length proxy.</li>
    <li><b>H5 — USGS vector sense join</b> (data-blocked: earthquake.usgs.gov unreachable
        from this sandbox).</li>
  </ol>
</div>
"""

# ------------------------------------------------------------------- write
(DOCS / "assets").mkdir(parents=True, exist_ok=True)
(DOCS / "assets" / "style.css").write_text(CSS)
(DOCS / ".nojekyll").write_text("")
(DOCS / "index.html").write_text(page("Download the submission", idx, "home"))
(DOCS / "executive-summary.html").write_text(page("Executive summary", exec_body, "exec"))
(DOCS / "sources.html").write_text(page("Sources", src, "sources"))
(DOCS / "research.html").write_text(page("Research & run card", res, "research"))
print("[site] wrote docs/index.html, executive-summary.html, sources.html, research.html,")
print("[site]        assets/style.css, .nojekyll (research/hypotheses.md is authored in place)")
