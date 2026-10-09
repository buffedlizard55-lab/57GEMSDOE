#!/usr/bin/env python3
"""Regenerate ``docs/`` from evidence JSONs and pinned protocol metadata.

Run-specific measurements are read from ``evidence/*.json`` and
``registry/registry_index.json`` at build time. Fixed protocol constants and
sample-grid metadata are sourced from checked-in code/data pins. Missing
measurement evidence is rendered as ``PENDING`` rather than guessed.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DOCS = ROOT / "docs"
EVID = ROOT / "evidence"

NAV = [("index.html", "Home"), ("executive-summary.html", "Download status"),
       ("method.html", "Method"), ("hypotheses.html", "Hypotheses"),
       ("results.html", "Results"), ("irregularities.html", "Irregularities"),
       ("data-sources.html", "Data sources"), ("run-card.html", "Run card")]

CSS = """
:root{--ink:#12212b;--mut:#5b6b76;--line:#dfe6ea;--bg:#f6f8f9;--card:#fff;
--acc:#0b6e4f;--warn:#a3341f;--ok:#0b6e4f;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
a{color:var(--acc)}
header{background:#12212b;color:#fff;padding:18px 28px}
header h1{margin:0;font-size:20px;font-weight:650}
header .sub{color:#a9bcc7;font-size:13px;margin-top:3px}
nav{background:#1c323f;padding:0 28px;display:flex;flex-wrap:wrap;gap:2px}
nav a{color:#cfdbe2;text-decoration:none;padding:10px 13px;font-size:13.5px;border-bottom:3px solid transparent}
nav a:hover{color:#fff}nav a.on{color:#fff;border-bottom-color:#3ecf9a}
main{max-width:1080px;margin:0 auto;padding:26px 22px 70px}
h2{font-size:21px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:16.5px;margin:22px 0 7px}
p{margin:9px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0}
.dl{background:#0b6e4f;color:#fff;border-radius:12px;padding:22px 24px;margin:0 0 18px}
.dl h2{border:0;color:#fff;margin:0 0 6px;font-size:22px}
.dl p{color:#d9f0e7;margin:6px 0}
.dl a.btn{display:inline-block;background:#fff;color:#0b6e4f;font-weight:700;text-decoration:none;
padding:13px 22px;border-radius:8px;margin:10px 8px 4px 0;font-size:16px}
.dl code{background:rgba(255,255,255,.16);color:#fff;padding:2px 6px;border-radius:4px}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px;background:#fff}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#eef3f5;font-weight:650}
td.n,th.n{text-align:right;font-family:var(--mono)}
code,pre{font-family:var(--mono)}
pre{background:#12212b;color:#e6eef3;padding:14px 16px;border-radius:8px;overflow-x:auto;font-size:12.5px;line-height:1.5}
.tag{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.4px;padding:2px 7px;border-radius:4px;
background:#e3edff;color:#1c4b91;text-transform:uppercase}
.tag.hold{background:#fff3d6;color:#7a5300}
.tag.org{background:#dff3e6;color:#0b6e4f}
.tag.bad{background:#fbe3de;color:#a3341f}
.note{border-left:4px solid #d8a017;background:#fffaee;padding:11px 15px;border-radius:0 7px 7px 0;margin:13px 0}
.bad-box{border-left:4px solid var(--warn);background:#fdf1ee;padding:11px 15px;border-radius:0 7px 7px 0;margin:13px 0}
.ok-box{border-left:4px solid var(--ok);background:#eefaf4;padding:11px 15px;border-radius:0 7px 7px 0;margin:13px 0}
.kv{display:grid;grid-template-columns:230px 1fr;gap:5px 14px;font-size:14px}
.kv dt{color:var(--mut)}.kv dd{margin:0;font-family:var(--mono);font-size:13px;word-break:break-all}
footer{border-top:1px solid var(--line);color:var(--mut);font-size:12.5px;padding:18px 22px 40px;max-width:1080px;margin:0 auto}
.small{font-size:12.5px;color:var(--mut)}
"""


def load(name: str):
    p = EVID / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def esc(x) -> str:
    return html.escape(str(x))


def fmt(x, nd=4):
    if x is None:
        return "PENDING"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return esc(x)


def verdict(v) -> str:
    return '<b class="ok">PASS</b>' if v else '<b class="bad">FAIL</b>'


def kv(pairs) -> str:
    return "".join(f"<tr><th>{esc(k)}</th><td>{v}</td></tr>" for k, v in pairs)


def kv_rows(d, empty: str = "PENDING") -> str:
    if not d:
        return f'<tr><td colspan="2">{esc(empty)}</td></tr>'
    return "".join(f'<tr><th>{esc(str(k))}</th>'
                   f'<td><code class="ok">{esc(str(v))}</code></td></tr>'
                   for k, v in d.items())


def page(title: str, body: str, active: str) -> str:
    nav = "".join(
        f'<a class="{"on" if f == active else ""}" href="{f}">{esc(n)}</a>' for f, n in NAV)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · 57GEMSDOE</title>
<link rel="stylesheet" href="assets/site.css"></head>
<body>
<header><h1>57GEMSDOE — fault-zone-anatomy lane</h1>
<div class="sub">DOE GEMS Prize Challenge · DrivenData #306 · secondary strands around known faults</div></header>
<nav>{nav}</nav>
<main>{body}</main>
<footer>Generated {stamp} by <code>scripts/build_site.py</code> from <code>evidence/*.json</code>.
Run-specific measurements come from checked-in evidence; fixed protocol constants and grid metadata come from source code and pinned data.
<span class="tag hold">HOLDOUT-DTI</span> = local instrument reading, never a live score.
<span class="tag org">ORGANIZER-CONFIRMED</span> = copied from a submission-page receipt.</footer>
</body></html>
"""


# --------------------------------------------------------------------------- #
def build_index(build, cv_all, uniq_src) -> str:
    build = build or {}
    card = load("run_card.json") or {}
    z = build.get("zeros_tif") or {}
    name = build.get("submission_name") or card.get("submission_name")
    fname = f"{name}-zeros.tif" if name else "PENDING"
    note = card.get("submission_note") or build.get("submission_note", "PENDING")
    checks = z.get("checks", {})
    crows = "".join(
        f'<tr><td><code>{esc(k)}</code></td><td>{verdict(v)}</td></tr>'
        for k, v in checks.items()) or '<tr><td colspan="2">PENDING</td></tr>'
    sha = card.get("raster_sha256") or z.get("sha256", "PENDING")
    emitted = card.get("raster_validation", {}).get("emitted_pixels", z.get("emitted_positive_pixels", "PENDING"))
    return f"""
<div class="dl">
<h2>H57 fault-zone anatomy — research artifact</h2>
<p><b>Download:</b> a locally format-validated GeoTIFF. It is <b>not cleared for competition submission</b>.
Do not upload it while the holdout, leakage, slip-sense, and surface-audit blockers below remain.</p>
<a class="btn" href="downloads/{esc(fname)}" download>Download research GeoTIFF</a>
<p>File: <code>{esc(fname)}</code> · {esc(emitted)} emitted dots · SHA256 <code>{esc(sha)}</code></p>
</div>
<div class="bad-box"><b>Promotion verdict: NEGATIVE / DO NOT SUBMIT.</b>
The saved OOF comparator is not budget-matched to this 40,000-dot map; `d` and `d_perp`
canaries exceed 0.90 pending explanation; local INGENIOUS slip-sense is not encoded; and the
required pre-placement surface-correlation audit was not preserved for this artifact. The final-dot
audit covers 18 local rasters only, not the complete competition registry. No upload receipt exists.</div>
<h2>What did pass locally</h2>
<table><tr><th>Format check</th><th>Result</th></tr>{crows}</table>
<dl class="kv">
<dt>CRS / shape / transform</dt><dd>EPSG:32611 · 3730 × 3292 · matches sample_submission.tif</dd>
<dt>Value range</dt><dd>finite float32 values in [0, 1]</dd>
<dt>Catalogue overlap</dt><dd>0 positive pixels on the mapped catalogue</dd>
<dt>Artifact SHA256</dt><dd>{esc(sha)}</dd>
<dt>Candidate note ({len(note)}/140 chars; do not use until cleared)</dt><dd><code>{esc(note)}</code></dd>
</dl>
<p>Local format validation proves only that the raster matches the checked-in grid and range gates.
It does not prove portal acceptance, uniqueness against unavailable submissions, live performance, or
organizer approval. See the <a href="run-card.html">run card</a>, <a href="results.html">results</a>,
and <a href="irregularities.html">irregularities</a>.</p>
"""


def build_exec(build) -> str:
    build = build or {}
    card = load("run_card.json") or {}
    z = build.get("zeros_tif") or {}
    name = build.get("submission_name") or card.get("submission_name")
    fname = f"{name}-zeros.tif" if name else "PENDING"
    note = card.get("submission_note") or build.get("submission_note", "PENDING")
    sha = card.get("raster_sha256") or z.get("sha256", "PENDING")
    status = card.get("submission_status", "research-only")
    checks = z.get("checks", {})
    crows = "".join(
        f'<tr><td><code>{esc(k)}</code></td><td>{verdict(v)}</td></tr>'
        for k, v in checks.items()) or '<tr><td colspan="2">PENDING</td></tr>'
    return f"""
<h2>Download and validation status</h2>
<div class="bad-box"><b>{esc(status)}.</b> The file is easy to download and its local GeoTIFF format
checks pass, but the current evidence does not clear it for submission. Do not upload it as a
competition entry until the run card blockers are resolved and reviewed.</div>
<div class="card"><p><a class="dl-link" href="downloads/{esc(fname)}" download>Download the H57 research TIFF</a></p>
<dl class="kv"><dt>Filename</dt><dd>{esc(fname)}</dd>
<dt>SHA256</dt><dd>{esc(sha)}</dd>
<dt>Emitted dots</dt><dd>{esc(card.get('raster_validation', {}).get('emitted_pixels', 'PENDING'))}</dd>
<dt>Submission note candidate</dt><dd><code>{esc(note)}</code> ({len(note)} characters, portal limit 140)</dd>
<dt>Organizer receipt</dt><dd>None recorded — no upload is evidenced</dd></dl></div>
<h2>Local format checks</h2>
<p>The file has one float32 band, the competition sample grid (EPSG:32611, 3730×3292 and matching
transform), finite values in [0,1], no positive mass outside the footprint, and zero dots on the
mapped catalogue. These checks are not an organizer acceptance receipt.</p>
<table><tr><th>Validator check</th><th>Result</th></tr>{crows}</table>
<h2>Why it is not submission-ready</h2>
<ul><li>No cap-matched leave-one-quadrant-out DTI/CI is available for the 40,000-dot map.</li>
<li>The `d` and `d_perp` single-feature leakage canaries exceed 0.90 and are unexplained.</li>
<li>Recorded INGENIOUS slip-sense is available locally but is not used by this candidate.</li>
<li>The current artifact has no pre-placement surface-to-registry correlation audit.</li>
<li>Final-dot uniqueness was checked against 18 local rasters only; the full competition registry is unavailable.</li>
</ul>
<h2>Submission procedure — only after the run card is cleared</h2>
<ol><li>Wait until the run card explicitly says the candidate is eligible; it currently says <b>negative</b>.</li>
<li>Download the exact `-zeros.tif` file linked on the home page. Do not open/save it in GIS software, because that can change the grid metadata.</li>
<li>Open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData submissions page</a>, choose <i>New submission</i>, and upload the TIFF or a ZIP containing that one TIFF.</li>
<li>Enter the exact submission name and note shown in the JSON run card (the note must be at most 140 characters), then submit.</li>
<li>Save the submission-page receipt. Only that receipt can support an `ORGANIZER-CONFIRMED` score label.</li></ol>
<p>Until the blockers above are resolved, treat this GeoTIFF as a research artifact and do not upload it.</p>
"""


def build_method(meas, cv_all, cv_det) -> str:
    card = load("run_card.json") or {}
    holdout = card.get("holdout_dti", {})
    canary = holdout.get("single_feature_leakage_canary", {})
    flags = canary.get("flags", [])
    flag_rows = "".join(
        f'<tr><td><code>{esc(x.get("feature"))}</code></td>'
        f'<td class="n">{fmt(x.get("discriminative_auc_max"), 6)}</td>'
        f'<td>{esc(x.get("status"))}</td></tr>' for x in flags)
    if not flag_rows:
        flag_rows = '<tr><td colspan="3">No flags recorded</td></tr>'
    return f"""
<h2>Active lane and data scope</h2>
<p>H57 models secondary-strand intensity from fault-catalogue geometry. The holdout withholds
whole fault segments by spatial quadrant; catalogue features are recomputed from visible faults
only, and visible fault pixels are masked exactly during scoring. The current candidate uses the
`no_side` variant: distance, cross-strike offset, absolute along-strike offset, visible-component
length proxy, doubled-angle strike encoding, coherence, and local density.</p>
<p>The local external INGENIOUS vector data includes recorded slip sense (`sense` and `SLIPSENSE`),
but the candidate does not use it. The official binary fault raster does not carry that field.
Geometric `side` is not a substitute for recorded slip-sense.</p>

<h2>Metric</h2>
<p>The project implements pooled distance-weighted Tversky index
<code>DTI = TPw / (TPw + 0.2·FPw + 0.8·FNw)</code>, with a 300 m triangular kernel (3 pixels at
100 m). Every visible-catalogue pixel is removed from the scored domain. See
<a href="../src/gems57/metric.py"><code>src/gems57/metric.py</code></a> and its brute-force tests.</p>

<h2>Valid saved spatial OOF baseline</h2>
<dl class="kv">
<dt>Evidence label</dt><dd>HOLDOUT-DTI — saved leave-one-quadrant-out `no_side` result</dd>
<dt>Evaluator record</dt><dd>{esc(holdout.get('evaluator_version', 'PENDING'))}</dd>
<dt>Withheld positives</dt><dd>{esc(holdout.get('withheld_positive_pixels', 'PENDING'))}</dd>
<dt>Pooled DTI</dt><dd>{fmt(holdout.get('pooled_dti'), 6)}</dd>
<dt>95% CI</dt><dd>{esc(holdout.get('ci95', 'PENDING'))} (four-quadrant jackknife)</dd>
<dt>Emissions</dt><dd>{esc(holdout.get('dots_across_two_spatial_draws', 'PENDING'))} across two draws; about {fmt(holdout.get('approx_dots_per_full_map'), 1)} per full-map equivalent</dd>
<dt>Budget match</dt><dd>{esc(holdout.get('budget_matched_to_candidate', False))} — candidate budget is 40,000, so no cap-matched DTI is available</dd>
</dl>
<div class="bad-box"><b>Not promotable.</b> The canary rule is discriminative AUC &gt; 0.90 until explained.
The saved `mode=all` result flags the following features:</div>
<table><tr><th>Feature</th><th class="n">Max discriminative AUC</th><th>Status</th></tr>{flag_rows}</table>

<h2>Historical builder number (revoked)</h2>
<p>The earlier `0.279349` reading used the same cells for fitting and scoring and misapplied the
40,000-dot budget across two draws rather than four quadrants per draw. It is retained in the
historical JSON but is explicitly invalid as candidate HOLDOUT-DTI.</p>

<h2>Interpretation limit</h2>
<p>The withheld truth is mapped catalogue geometry, not a random sample of genuinely unmapped
faults. The detached mode is a useful stress test but does not remove all distribution shift.
No local holdout value is compared directly with the owner-reported or conflicting leaderboard
numbers. No live score is projected.</p>
<p>For the active geological backlog, see <a href="hypotheses.html">Hypotheses</a> or
<a href="research/hypotheses_h57.md">the active H57 hypothesis slate</a>.</p>
"""


def build_hypotheses() -> str:
    hypotheses = [
        ("1", "Sense-conditioned Riedel side and relative azimuth", "Moderate", "Medium", "local INGENIOUS sense fields; coverage overlap not measured"),
        ("2", "Slip-rate-scaled damage-zone width", "Small–moderate", "Low–medium", "local slip-rate fields; join coverage not measured"),
        ("3", "Along-strike tip relay", "Moderate", "Medium", "local vector endpoints; visible-only extraction required"),
        ("4", "Junction and stepover context", "Small–moderate", "Low", "local official raster and vectors"),
        ("5", "Within-zone geophysical corroboration", "Potentially high", "High / blocked", "official training raster is pinned but absent from this checkout"),
    ]
    rows = "".join(
        f'<tr><td>{esc(rank)}</td><td><b>{esc(name)}</b></td><td>{esc(gain)}</td>'
        f'<td>{esc(cost)}</td><td>{esc(status)}</td></tr>'
        for rank, name, gain, cost, status in hypotheses)
    return f"""
<h2>Active H57 hypotheses — ranked backlog</h2>
<div class="bad-box"><b>No new hypothesis has been validated in this turn.</b> The current H57
candidate remains research-only because its cap-matched OOF score, leakage flags, and slip-sense
conditioning are unresolved. Expected gains below are qualitative hypotheses, not scores.</div>
<table><tr><th>Rank</th><th>Hypothesis</th><th>Expected DTI gain</th><th>Cost</th><th>Verified data status</th></tr>{rows}</table>
<p>Each item is within the fault-zone-anatomy lane and the active document names the layers,
physical target, differentiation from H57, source links, and validation cost:</p>
<p><a href="research/hypotheses_h57.md"><b>Read the active H57 hypotheses and source/availability checks.</b></a></p>
<p>The historical H1/H52-era slate is archived separately at
<a href="research/hypotheses.md">docs/research/hypotheses.md</a>; its measurements are not the
current H57 result.</p>
"""


def build_results(cv_all, cv_det, build, rb=None) -> str:
    card = load("run_card.json") or {}
    h = card.get("holdout_dti", {})
    def cv_table(cv, label):
        if not cv:
            return f'<h3>Mode {esc(label)}</h3><p>PENDING</p>'
        rows = ""
        for name, result in cv.get("variants", {}).items():
            pl = result.get("pooled", {})
            ci = pl.get("dti_ci95_quadrant_jackknife", [None, None])
            rows += (f'<tr><td><code>{esc(name)}</code></td>'
                     f'<td class="n">{fmt(pl.get("pooled_dti"), 6)}</td>'
                     f'<td class="n">[{fmt(ci[0], 6)}, {fmt(ci[1], 6)}]</td>'
                     f'<td class="n">{esc(pl.get("n_truth", "PENDING"))}</td>'
                     f'<td class="n">{esc(pl.get("n_dots", "PENDING"))}</td></tr>')
        return (f'<h3>Spatial OOF mode <code>{esc(label)}</code> <span class="tag hold">HOLDOUT-DTI</span></h3>'
                f'<table><tr><th>Variant</th><th class="n">Pooled DTI</th>'
                f'<th class="n">95% CI (quadrant jackknife)</th><th class="n">Withheld positives</th>'
                f'<th class="n">Dots across draws</th></tr>{rows}</table>')
    uq = card.get("registry_correlation_overlap", {})
    return f"""
<h2>Local spatial holdout results — no live-score comparison</h2>
<div class="note">All values in the tables below are internal <b>HOLDOUT-DTI</b> measurements from
saved leave-one-quadrant-out CV. Each spatial test quadrant is excluded from fitting. CIs are
four-quadrant jackknife intervals. These values are not projections and are not directly comparable
to owner-reported or organizer leaderboard values.</div>
{cv_table(cv_all, "all")}
{cv_table(cv_det, "detached")}
<p>The current candidate uses `no_side`, mode `all`: HOLDOUT-DTI
<b>{fmt(h.get("pooled_dti"), 6)}</b>, 22,641 withheld positives,
95% quadrant-jackknife CI <code>{esc(h.get("ci95", "PENDING"))}</code>. It used about
{fmt(h.get("approx_dots_per_full_map"), 1)} dots per full-map equivalent, so it is <b>not matched</b>
to the 40,000-dot candidate.</p>
<div class="bad-box"><b>Do not cite the older 0.279349 builder result.</b> It trained and evaluated on the
same cells and used an incorrect per-quadrant cap. The only valid saved comparator in the run card
is 0.250800, still non-promotable because the budget does not match and `d` / `d_perp` canaries
exceed 0.90.</div>

<h2>Final-dot uniqueness — finite local scope</h2>
<dl class="kv">
<dt>Inventory checked</dt><dd>{esc(uq.get("n_rasters_checked", "PENDING"))} local rasters (15 owner-repository + 3 archived)</dd>
<dt>Worst full-footprint Spearman</dt><dd>{fmt(uq.get("worst_spearman_full_footprint"), 6)} vs {esc(uq.get("worst_rho_submission", "PENDING"))}</dd>
<dt>Worst candidate-dot fraction within 3 px</dt><dd>{fmt(uq.get("worst_candidate_dot_fraction_within_3px"), 6)} vs {esc(uq.get("worst_overlap_submission", "PENDING"))}</dd>
<dt>Local result</dt><dd>{"PASS within checked inventory" if uq.get("unique_within_checked_18_raster_inventory") else "PENDING / FAIL"}</dd>
<dt>Surface check</dt><dd>{esc(uq.get("preplacement_surface_correlation", "NOT RUN"))}</dd>
<dt>Competition-wide uniqueness</dt><dd>NOT CLAIMED — private, unlinked and external rasters are outside this inventory</dd>
</dl>

<h2>Why the cited high score cannot be explained here</h2>
<p>The task prompt contains conflicting highs (0.2778, 0.3195, 0.3774). This repository has no
submission-page receipts or live leaderboard snapshot. Registry numbers are owner-reported and
must not be called organizer-confirmed. We can explain the DTI formula and show that higher
coverage at a sensible dot budget is mathematically plausible, but no live improvement is claimed
or projected.</p>
<p>See the <a href="run-card.html">JSON run card</a> for evaluator version, withheld-positive count,
CI, raster hash, validator summary, note, and the negative verdict.</p>
"""


IRREG = [
 ("IR-57-NAN-01", "NaN export is not submission-safe", "LOCAL FORMAT FIX VERIFIED",
  "The sample submission carries NaN outside the footprint, but NaN is not within the portal's stated [0,1] range. The diagnostic NaN raster is not a submission artifact.",
  "The current zeros TIFF is finite float32 in [0,1] everywhere, matches the sample grid, and passes the repository's local validator. This is not proof of portal acceptance."),
 ("IR-57-EVAL-01", "Shared evaluator called removed functions", "FIXED IN SHARED HELPER; UNIT TESTED",
  "evaluate_holdout.py called holdout.score and metric.max_cover, neither of which existed in the checked-out modules.",
  "The helper now delegates exact DTI arithmetic to metric.dti_exact and exposes metric.max_cover; per-block terms are checked against pooled totals. The active CV and build paths use the shared helper."),
 ("IR-57-BUILD-01", "Historical 0.279349 builder score was not a holdout score", "REVOKED AS PROMOTION EVIDENCE",
  "The final model was fit using all cells subsequently scored. The 40,000-dot cap was divided by two draws rather than four quadrants per draw, so it was not cap-matched either.",
  "The historical JSON is preserved but marked invalid. The current run card uses the saved leave-one-quadrant-out no_side result 0.250800 with 22,641 positives and a 95% quadrant-jackknife CI; that result is not cap-matched and is not promotable."),
 ("IR-57-CANARY-02", "Distance canaries exceed the leakage threshold", "OPEN — NON-PROMOTABLE",
  "The saved mode=all canary reports discriminative AUC 0.900018 for d and 0.901345 for d_perp. The protocol treats AUC above 0.90 as leakage until explained.",
  "No explanation has been independently established. Detached-mode results do not erase the mode=all flag; the baseline remains non-promotable pending explanation or a redesigned instrument."),
 ("IR-57-SLIP-01", "Sense-of-slip availability was misreported", "CORRECTED; MODEL STILL NONCOMPLIANT",
  "The official binary fault raster has no sense field, but local INGENIOUS trace vectors include sense and qfault_attributes.csv includes SLIPSENSE. Earlier docs incorrectly generalized raster limitations to the full local database.",
  "The current candidate does not encode these available attributes. A visible-only vector/raster overlap audit and sense-conditioned OOF experiment are still required."),
 ("IR-57-UNI-01", "Pre-placement correlation and registry scope were incomplete", "FINAL-DOT CHECK RE-RUN; SURFACE CHECK OPEN",
  "The current artifact has no preserved pre-placement surface. Earlier uniqueness evidence covered only 15 local owner-repository rasters and did not include archived artifacts.",
  "Final dots were rechecked against 18 local rasters with no threshold breach. The builder now runs the surface check before allocation and final-dot overlap before packaging. Neither local check proves complete competition-wide uniqueness."),
 ("IR-57-DATA-01", "Pinned training feature raster is absent in this checkout", "FLAGGED / BLOCKED",
  "data/official/training_features.tif is a gitignored 418,912,844-byte file and is not present. The local pin-check reports it missing; source pages may require login.",
  "Tests now explicitly skip the all-pins test when this file is absent and verify that the missing-file condition is reported. No substitute raster is treated as verified."),
 ("IR-57-BRIEF-01", "Conflicting leaderboard highs and no receipts", "UNRESOLVED; NO SCORE CLAIM",
  "The retained task prompt cites 0.2778, 0.3195 and 0.3774. This checkout has no submission-page receipt or live leaderboard snapshot.",
  "Treat the values as owner-provided only; do not compare them directly with HOLDOUT-DTI or call them ORGANIZER-CONFIRMED."),
]


def build_irregularities() -> str:
    rows = ""
    for iid, title, status, desc, res in IRREG:
        if "OPEN" in status or "BLOCKED" in status or "UNRESOLVED" in status:
            badge = '<span class="tag bad">OPEN / STOP</span>'
        elif "FIX" in status or "CORRECTED" in status or "RE-RUN" in status:
            badge = '<span class="tag hold">REVIEWED</span>'
        else:
            badge = '<span class="tag">FLAGGED</span>'
        rows += (f'<tr><td><code>{esc(iid)}</code><br>{badge}</td><td><b>{esc(title)}</b></td>'
                 f'<td>{esc(desc)}</td><td>{esc(res)}</td></tr>')
    return f"""
<h2>Current irregularity ledger</h2>
<p>Open evidence gaps are shown as stop flags, not quietly converted into a positive promotion
claim. Historical measurements remain machine-readable but are labeled according to their actual
validation design.</p>
<table><tr><th>ID</th><th>Title</th><th>What was wrong</th><th>Resolution / remaining work</th></tr>{rows}</table>
<div class="note"><b>Integrity rule:</b> local format validation, owner-reported registry scores, and
internal HOLDOUT-DTI measurements are different evidence classes. None substitutes for a
submission-page receipt or complete registry coverage.</div>
"""


def build_sources() -> str:
    reg = json.loads((ROOT / "registry" / "registry_index.json").read_text()) \
        if (ROOT / "registry" / "registry_index.json").exists() else []
    rrows = "".join(
        f'<tr><td>{esc(r["repo"])}</td><td>{esc(r["submission"])}</td>'
        f'<td class="n">{fmt(r.get("owner_reported_score"))}</td>'
        f'<td><code>{esc(r["sha256"][:16])}…</code></td><td class="n">{r["bytes"]:,}</td>'
        f'<td><a href="https://github.com/buffedlizard55-lab/{esc(r["repo"])}">repo</a></td></tr>'
        for r in reg)
    return f"""
<h2>Competition data and trusted references</h2>
<table><tr><th>Source</th><th>Available local evidence</th><th>Official link</th></tr>
<tr><td>Competition #306 data</td><td>labels, existing_faults, sample_submission pinned; 418,912,844-byte training_features raster absent</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">DrivenData data page</a></td></tr>
<tr><td>Metric and task</td><td>Local implementation and tests; no leaderboard receipt</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Problem description</a></td></tr>
<tr><td>Reference solution</td><td>Repository clone and checked-in local notes</td><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">GitHub</a></td></tr>
<tr><td>GeodAWN survey</td><td>External USGS site was not independently checked from this sandbox</td><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS metadata</a></td></tr>
<tr><td>INGENIOUS vectors</td><td>Local trace_segments_utm11.csv includes sense; qfault_attributes.csv includes SLIPSENSE; SHA256 pins in data/README.md</td><td><a href="https://gbcge.org/current-projects/ingenious/">GBCGE INGENIOUS</a></td></tr>
</table>
<p>Local source hashes and availability notes are in <a href="../data/README.md"><code>data/README.md</code></a>.
The official binary fault raster does not have a sense band, but the local external INGENIOUS vectors
do have sense attributes. The current candidate has not yet used them.</p>
<p class="small">Outbound network access in this workspace is restricted to GitHub and package hosts.
Links to DrivenData, USGS and GBCGE are provided as source links, not as claims of live verification.
The official training raster is hash-pinned but missing locally, so hypotheses requiring it remain
blocked.</p>

<h2>Owner-repository raster inventory</h2>
<table><tr><th>Repo</th><th>Submission</th><th class="n">Owner-reported score</th>
<th>sha256</th><th class="n">Bytes</th><th>Link</th></tr>{rrows}</table>
<p class="small">The displayed scores are owner-reported only; this checkout has no corresponding
submission-page receipts. The separate 18-raster audit adds three local archived rasters, but does
not cover private, unlinked, external, or inaccessible competition artifacts. It is not a complete
registry-wide uniqueness certification.</p>
"""


def build_runcard(build, cv_all, meas) -> str:
    # evidence/run_card.json is the source of truth. Never regenerate it from
    # older builder fields: doing so previously overwrote the negative verdict.
    card = load("run_card.json") or {}
    card_txt = json.dumps(card, indent=2)
    return f"""
<h2>Current H57 run card</h2>
<p>Authoritative machine-readable copy: <a href="../evidence/run_card.json"><code>evidence/run_card.json</code></a>.
The site renders that file and does not rewrite it.</p>
<div class="bad-box"><b>Verdict: NEGATIVE / DO NOT SUBMIT.</b> Local format validation passed, but the
cap-matched OOF, leakage, recorded slip-sense, pre-placement surface-correlation, and complete
registry-scope requirements remain unresolved.</div>
<pre>{esc(card_txt)}</pre>
<h2>Evidence labels</h2>
<ul>
<li><b>HOLDOUT-DTI</b> is a local hide-and-recover result with its evaluator record, withheld-positive
count, and 95% CI. It is not a live score.</li>
<li><b>ORGANIZER-CONFIRMED</b> requires a submission-page receipt. None is present in this checkout.</li>
<li>Final-dot uniqueness passes only within the checked 18-raster local inventory; the required
pre-placement surface check is missing for the current artifact.</li>
</ul>
"""


def main() -> None:
    build = load("submission_build_all.json")
    cv_all = load("cv_all.json")
    rb = load("registry_budget.json")
    cv_det = load("cv_detached.json") or load("cv_det.json")
    meas = load("withheld_structure.json")
    reg = (ROOT / "registry" / "registry_index.json")
    uniq_src = json.loads(reg.read_text()) if reg.exists() else []

    DOCS.mkdir(exist_ok=True)
    (DOCS / "assets").mkdir(exist_ok=True)
    (DOCS / "assets" / "site.css").write_text(CSS)
    (DOCS / ".nojekyll").write_text("")

    pages = {
        "index.html": ("57GEMSDOE — fault-zone anatomy", build_index(build, cv_all, uniq_src), "index.html"),
        "executive-summary.html": ("Download and validation status", build_exec(build), "executive-summary.html"),
        "method.html": ("Method", build_method(meas, cv_all, cv_det), "method.html"),
        "hypotheses.html": ("Hypotheses", build_hypotheses(), "hypotheses.html"),
        "results.html": ("Results", build_results(cv_all, cv_det, build, rb), "results.html"),
        "irregularities.html": ("Irregularities", build_irregularities(), "irregularities.html"),
        "data-sources.html": ("Data sources", build_sources(), "data-sources.html"),
        "run-card.html": ("Run card", build_runcard(build, cv_all, meas), "run-card.html"),
    }
    for fname, (title, body, active) in pages.items():
        (DOCS / fname).write_text(page(title, body, active))
        print(f"wrote docs/{fname}  ({len(body):,} chars of body)")


if __name__ == "__main__":
    main()
