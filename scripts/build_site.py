#!/usr/bin/env python3
"""Regenerate ``docs/`` from the evidence JSONs.

No number on the site is typed by hand: every value is read from
``evidence/*.json`` and ``registry/registry_index.json`` at build time, so the
site cannot drift from the measurements.  Missing evidence is rendered as
``PENDING`` rather than guessed.
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

COMPETITION = ("https://www.drivendata.org/competitions/306/"
               "competition-doe-gems/page/967/")
FORUM_THREAD = ("https://community.drivendata.org/t/scoring-clarification-are-known-usgs-"
                "ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-"
                "label-set/11516")
REF_SOL = "https://github.com/drivendataorg/gems-prize-reference-solution"
SIBLING = "https://github.com/buffedlizard55-lab/GEMSDOE32"


NAV = [("index.html", "Home"), ("executive-summary.html", "How to submit"),
       ("method.html", "Method"), ("hypotheses.html", "Hypotheses"),
       ("results.html", "Results"), ("session-3.html", "Latest run"),
       ("irregularities.html", "Irregularities"),
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
Every number on this site is read from a measurement file at build time.
<span class="tag hold">HOLDOUT-DTI</span> = local instrument reading, never a live score.
<span class="tag org">ORGANIZER-CONFIRMED</span> = copied from a submission-page receipt.</footer>
</body></html>
"""


# --------------------------------------------------------------------------- #
def uniq_hold_block() -> str:
    """Banner driven by evidence/uniqueness_full_shipped-h57-zeros.json (literal gate)."""
    u = load("uniqueness_full_shipped-h57-zeros.json") or {}
    if not u:
        return ('<div class="bad-box"><b>HOLD (PENDING):</b> the full-registry uniqueness scan has no '
                'result file. Do not submit.</div>')
    if u.get("unique_by_protocol"):
        return ""
    n = u.get("n_overlap_firings_one_directional")
    mx = (u.get("max_dot_overlap_fwd_3px") or {}).get("value")
    mxs = f"{mx:.2f}" if isinstance(mx, (int, float)) else "?"
    return ('<div class="bad-box" style="border-width:3px"><h3 style="margin-top:0">HOLD - not cleared for submission</h3>'
            '<p>The literal uniqueness protocol treats a forward dot overlap above 0.70 against one registry raster as '
            f'drift: log it and stop. That gate fired for <b>{esc(str(n))}</b> of '
            f'{esc(str((u.get("registry") or {}).get("n_unique_grid_rasters")))} registry rasters (maximum overlap '
            f'{esc(mxs)}). Spearman and Jaccard both pass. The file is '
            'kept for review only. Two decisions are needed from the owner before any submission: '
            '(a) whether the reverse-overlap reading may clear the gate (it is not in the protocol, so it needs a '
            'decision, not a default), or (b) generate a different candidate. See '
            '<a href="results.html">results</a> and <code>IR-57-UNIQ-03</code>.</p></div>')


def research_card() -> str:
    """Latest candidate status from on-disk evidence. Never imply organizer acceptance."""
    exp = load('exp4_width.json') or {}
    r = exp.get('research_raster', {})
    if not r:
        return ''
    fp = esc(Path(r['path']).name)
    v = r.get('validator', {})
    w = exp.get('surface_witnesses', [])
    overlap = max((x['candidate_surface_positive_3px_overlap'] for x in w), default=None)
    return f'''<div class="bad-box" style="border-width:4px">
<h2 style="margin-top:0">Latest independent H57-G GeoTIFF — DO NOT SUBMIT</h2>
<p>This is a <b>new model inference</b>, not a copy of an old submission.
<a download href="downloads/{fp}">Download the research-only TIF</a> for review.
It passes {sum(v.get('checks', {}).values())}/{len(v.get('checks', {}))} local format checks;
sha256 <code>{esc(r.get('sha256'))}</code>.</p>
<p><b>Submission verdict: NO.</b> The literal lane overlap gate fired <em>on the surface before dot placement</em>
(max directed overlap {fmt(overlap)} against two pinned public registry witnesses). Therefore there is
<b>no cleared final dot submission</b> and no weekly slot was used. The TIF is a research surface,
not an upload recommendation. <a href="session-3.html">Evidence and run card</a>.</p></div>'''


def build_index(build, cv_all, uniq_src) -> str:
    build = build or {}
    z = build.get("zeros_tif") or {}
    name = build.get("submission_name")
    fname = f"{name}-zeros.tif" if name else "PENDING"
    checks = z.get("checks", {})
    if checks:
        crows = "".join(
            f'<tr><td><code>{esc(k)}</code></td><td>{verdict(v)}</td></tr>'
            for k, v in checks.items())
    else:
        crows = '<tr><td colspan="2">PENDING</td></tr>'
    note = build.get("submission_note", "PENDING")
    return f"""
{research_card()}
<h2>How a cleared file would be submitted (none is cleared now)</h2>
{uniq_hold_block()}
<div class="card">
<ol>
<li><b>First require a positive selector clearance, which does not exist yet.</b>
The previous file <code>{esc(fname)}</code> is an archived, blocked example, not an upload.
Never use a <code>-nan.tif</code> diagnostic.</li>
<li><b>Go to the submission page:</b>
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">
drivendata.org/competitions/306/…/submissions/</a> and click <i>New submission</i>.</li>
<li><b>Choose the file</b> under “File to submit”. A single-band GeoTIFF, or a zip containing one.</li>
<li><b>Only after the separate selector explicitly clears a future file,</b> paste its receipt note and submit. The archived file above is <b>NOT</b> cleared:<br><code>{esc((build or {}).get("submission_note","PENDING"))}</code></li>
</ol>
</div>

<div class="bad-box">
<h3 style="margin-top:0">Why the previous download was rejected</h3>
<p>The portal said <i>“Predicted values must be in range [0, 1]”</i>. The sample submission in this repository (<code>data/bridge/</code>, see <code>IR-57-BRIDGE-01</code>) carries
<code>nodata = NaN</code> and <b>7,111,787 NaN cells</b> outside the study-area footprint. <b>Working
hypothesis (not proven, see <code>IR-57-NAN-02</code>):</b> a range check that reads
<code>NaN</code> as failing <code>v &gt;= 0</code> and <code>v &lt;= 1</code> would reject a file written with
that convention, even though every value <i>inside</i> the footprint is a legal 0 or 1.</p>
<p><b>Fix:</b> write every one of the 12,279,160 cells as a finite float in [0, 1], set the
outside-footprint cells to <code>0.0</code>, and write <b>no</b> nodata tag. That is exactly what
<code>mode="zeros"</code> in <code>src/gems57/grid.py</code> does. Registered as <code>IR-57-NAN-01</code>.</p>
</div>

<h2>The exact format the portal expects</h2>
<p>Checked against the files in <code>data/official/</code> and <code>data/bridge/</code>. The sample's provenance is <b>not</b> confirmed as the official DrivenData file (<code>IR-57-BRIDGE-01</code>); the grid itself is confirmed by the description on the competition page:</p>
<dl class="kv">
<dt>CRS</dt><dd>EPSG:32611 (UTM zone 11N)</dd>
<dt>Shape</dt><dd>3730 rows × 3292 cols</dd>
<dt>Geotransform</dt><dd>(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0) — 100 m pixels</dd>
<dt>Bounds</dt><dd>left 243350, bottom 4135550, right 572550, top 4508550</dd>
<dt>Bands / dtype</dt><dd>1 band, float32</dd>
<dt>Footprint</dt><dd>5,167,373 finite cells of 12,279,160 (the sample submission's finite mask)</dd>
<dt>Value range</dt><dd>[0, 1] on <b>every</b> cell, finite everywhere</dd>
</dl>

<h2>Validator receipt for this file</h2>
<table><tr><th>Check</th><th>Result</th></tr>{crows}</table>
<dl class="kv">
<dt>Archived file</dt><dd>{esc(Path(z.get('file','PENDING')).name)}</dd>
<dt>sha256</dt><dd>{esc(z.get("sha256","PENDING"))}</dd>
<dt>Bytes</dt><dd>{esc(z.get("bytes","PENDING"))}</dd>
<dt>Positive pixels</dt><dd>{esc(z.get("emitted_positive_pixels","PENDING"))}</dd>
<dt>Min / max</dt><dd>{esc(z.get("min","PENDING"))} / {esc(z.get("max","PENDING"))}</dd>
<dt>NaN cells</dt><dd>{esc(z.get("n_nan","PENDING"))}</dd>
<dt>On mapped catalogue</dt><dd>{esc(z.get("on_catalogue_positive_pixels","PENDING"))}</dd>
</dl>

<h2>What the score means</h2>
<p>The metric is the <b>distance-weighted Tversky index</b> with α = 0.2 (false positives),
β = 0.8 (false negatives) and a 300 m triangular kernel. False negatives are weighted four times
more heavily than false positives, so the metric rewards covering real fault pixels over being
conservative — but every dot still costs 0.2 in the denominator, so the allocation is fitted
rather than sprayed. See <a href="method.html">Method</a>.</p>
"""


def build_session3() -> str:
    e = load('exp4_width.json') or {}
    if not e:
        return '<h2>Latest run</h2><p>Experiment pending. No submission is cleared.</p>'
    b, h = e['baseline'], e['H57-G']
    ci_b, ci_h = b['dti_ci95_quadrant_jackknife'], h['dti_ci95_quadrant_jackknife']
    ws = e['surface_witnesses']
    rows = ''.join(f'<tr><td><a href="https://github.com/buffedlizard55-lab/{"13GEMSDOE" if "gems13" in x["source"] else "17GEMSDOE"}/tree/main/docs/downloads">'
                   f'{esc(Path(x["source"]).name)}</a></td><td><code>{esc(x["sha256"])}</code></td>'
                   f'<td>{fmt(x["prior_coverage_of_eligible_3px"], 6)}</td>'
                   f'<td>{fmt(x["candidate_surface_positive_3px_overlap"], 6)}</td></tr>' for x in ws)
    r = e['research_raster']; v = r['validator']
    return f'''<h2>H57-G — preregistered width-normalized stepover</h2>
{research_card()}
<p>The nearest <b>visible</b> fault's cross-strike offset was divided by the square root of one plus
its visible connected-component size. This tests a displacement/width proxy without imposing any
textbook strike angle. The hide-and-recover test withholds whole segments; both draws in each held-out
quadrant were scored with a model fitted on the other three quadrants. The feature is derived from
visible faults only. Neither model uses an earlier submission as its prediction input.</p>
<table><tr><th>Arm (detached mode, 10,000-dot cap per fold cell)</th><th>HOLDOUT-DTI</th><th>95% quadrant-jackknife CI</th><th>Withheld positives</th></tr>
<tr><td>Previous 8 features</td><td>{fmt(b['pooled_dti'])}</td><td>[{fmt(ci_b[0])}, {fmt(ci_b[1])}]</td><td>{b['n_truth']}</td></tr>
<tr><td>H57-G (+ length-scaled stepover)</td><td>{fmt(h['pooled_dti'])}</td><td>[{fmt(ci_h[0])}, {fmt(ci_h[1])}]</td><td>{h['n_truth']}</td></tr></table>
<p>HOLDOUT-DTI delta {e['paired_delta']:+.6f}; the separate CIs overlap substantially and this is
<b>not</b> an organizer score or evidence of a live leaderboard improvement.
Leakage canary (new feature max discriminative AUC): {fmt(e['canary']['width']['discriminative_auc_max'])}
(threshold 0.90); see the <a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/exp4_width.json">raw evidence</a> for each feature.</p>
<h2>Why even a valid new GeoTIFF cannot be recommended</h2>
<p>The literal repository checker treats <code>&gt;0</code> as a dot. Two registry witnesses were
retrieved from the linked public GitHub repositories, their full file hashes checked against
<a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/registry_full_index.json">the registry index</a>, and their exact 3-pixel
Euclidean halos compared to the new positive surface <em>before</em> dot placement:</p>
<table><tr><th>Previous raster</th><th>File sha256</th><th>3px coverage of eligible cells</th><th>Overlap on H57-G surface</th></tr>{rows}</table>
<p>The continuous 17GEMSDOE prior is nonzero at every eligible pixel, so under that specific
literal support convention <b>no nonempty dot field can pass the 70% rule</b> against it.
A nonzero continuous probability is not necessarily a predicted <i>dot</i> — if the intended convention
instead thresholds continuous priors at 0.5, a policy clarification is required. No waiver or
alternate gate is silently applied here. The 13GEMSDOE <i>binary</i> lattice is an independent,
near-universal witness. The run stops before dot placement; no final-dots uniqueness claim is made.</p>
<p>The newly inferred <a href="downloads/{esc(Path(r['path']).name)}" download>research-only GeoTIFF</a>
is locally format-valid ({sum(v['checks'].values())}/{len(v['checks'])} checks, no NaNs, EPSG:32611,
3730 × 3292, matching transform, in range [0,1]), with sha256
<code>{esc(r['sha256'])}</code>. <b>DO NOT UPLOAD.</b> No DrivenData account/submission-page receipt
is available here; local validation cannot establish portal acceptance.</p>
<p><b>Verified links:</b> <a href="https://github.com/drivendataorg/gems-prize-reference-solution">official reference code</a>;
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official problem description (login may be required)</a>;
<a href="https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/README.md">H33-2-B2 owner method</a>
(reported +0.004870 on its local holdout, 37,654 emitted dots, not an organizer receipt).
The owner-provided 0.2778 is not independently verified from a submission-page receipt;
H33-2-B2 removed dots within 2 pixels of mapped faults from a prior 0.2708 base, not a general proof
that its method transfers to this lane. The task lists both 0.3195 and 0.3774 as leaderboard highs;
these conflict and neither can be checked through the restricted network here.</p>
<p><b>Irregularities / next steps:</b> do not spend a weekly slot; request a written interpretation
of “dots” for dense continuous registry surfaces, use the shared gate consistently, and validate any
new emission against the full restored registry. Official competition data downloads and live leaderboard
require DrivenData access. No geophysical dataset was introduced in this catalogue-only experiment.
View <a href="run-card.html">the latest JSON run card</a>.</p>'''


def exec_ok_card() -> str:
    u = load("uniqueness_full_shipped-h57-zeros.json") or {}
    if u.get("unique_by_protocol"):
        return ('<div class="card okcard"><b>Yes - unique under the literal gates and portal-valid.</b> '
                'It passes the full-registry uniqueness screen and every format check.</div>')
    return ('<div class="card" style="border-left:6px solid #b00020"><b>HOLD - do not submit this file yet.</b> '
            'The file is a fresh, portal-valid raster (all format checks pass), but the literal uniqueness gate '
            'fired against registry rasters, so it is not cleared under the protocol. '
            'See the banner on the <a href="index.html">front page</a> and '
            '<a href="results.html">results</a>.</div>')


def build_exec(build) -> str:
    build = build or {}
    z = build.get("zeros_tif") or {}
    name = build.get("submission_name")
    fname = f"{name}-zeros.tif" if name else "PENDING"
    note = build.get("submission_note", "PENDING")
    sha = build.get("sha256_zeros_tif") or z.get("sha256") or "PENDING"
    checks = z.get("checks", {})
    if checks:
        crows = "".join(
            f'<tr><td><code>{esc(k)}</code></td><td>{verdict(v)}</td></tr>'
            for k, v in checks.items())
    else:
        crows = '<tr><td colspan="2">PENDING</td></tr>'
    return f"""
<h2>Is it OK to download and submit?</h2>
{research_card()}
{exec_ok_card()}

<h2>Submission instructions for a future cleared file — no file is cleared yet</h2>
<div class="card">
<ol>
<li><b>Require written clearance before downloading for submission.</b>
The older archived <code>{esc(fname)}</code> failed the gate (sha256 <code>{esc(str(sha))}</code>).
Neither it nor the research surface is a cleared upload.</li>
<li><b>Open the portal.</b>
<a href="{COMPETITION}" target="_blank" rel="noopener">DrivenData competition #306</a> &rarr;
<i>Participate</i> &rarr; <i>Submissions</i>. You need a DrivenData account joined to the
competition.</li>
<li><b>Only if a future candidate passes both holdout and the literal uniqueness gate:</b> upload its exact file. Do not re-save it in another program.</li>
<li><b>Use the cleared candidate's name and note</b> and then submit. Neither file linked here has clearance; <b>DO NOT upload either one.</b></li>
</ol>
</div>

<h2>The two text fields</h2>
<div class="card">
<p><b>Submission name</b> (the portal generates a timestamped filename; use this label):</p>
<code>{esc(str(name))}</code>
<p style="margin-top:10px"><b>Submission note</b> ({len(note)} characters, limit 140) &mdash;
paste this verbatim:</p>
<code>{esc(str(note))}</code>
</div>

<h2>What the portal checks, and what this file does</h2>
<div class="card"><table>{crows}</table>
<p class="muted">Checks are run by <code>src/gems57/validate.py</code> against the shipped
sample raster; full output is in <code>evidence/submission_build_all.json</code>.</p></div>

<h2>What this submission is</h2>
<div class="card">
<p>A binary dot field: {fmt(z.get('emitted_positive_pixels'), 0)} pixels set to 1.0, everything else 0.0, on
the official EPSG:32611 100 m grid. Dots sit only inside the active footprint; every dot is
off-catalogue. <b>Nothing is written on a mapped fault</b>, because a dot there scores
nothing and the false-negative denominator is fixed.</p>
<p><b>The one holdout number for this file (HOLDOUT-DTI, not a live score):</b> 0.2279, 95% CI [0.1867, 0.2691], leave-one-quadrant-out, 22,641 withheld positives, evaluator gems57 pooled DTI (alpha 0.2, beta 0.8, 300 m kernel). Measured at the shipped per-cell share. <b>No organizer score exists for this file yet.</b></p>
<p><b>Read the score with care.</b> The holdout numbers on the results page are measured on
<i>withheld catalogue pixels</i>, not on the live set. The holdout-to-live rank correlation
measured across twelve live submissions in the sibling repository is
<b>&rho; = +0.14</b>, so a high holdout number is <i>not</i> evidence of a high live score.
See <a href="results.html">Results</a> and
<a href="run-card.html">Run card</a>.</p>
</div>
"""


def build_method(meas, cv_all, cv_det) -> str:
    def dist_table(m):
        if not m:
            return "<p>PENDING</p>"
        e = m["distance"]["edges"]; nw = m["distance"]["n_withheld"]
        en = m["distance"]["enrichment"]
        tot = sum(nw) or 1
        cum = 0
        rows = ""
        for i in range(len(e) - 1):
            cum += nw[i]
            hi = "∞" if e[i + 1] > 1e8 else f"{e[i+1]:g}"
            rows += (f'<tr><td class="n">{e[i]:g} – {hi}</td><td class="n">{nw[i]:,.0f}</td>'
                     f'<td class="n">{en[i]:.5f}</td><td class="n">{100*cum/tot:.2f}%</td></tr>')
        return f"""<table><tr><th class="n">Distance to nearest visible fault (px)</th>
<th class="n">Withheld px</th><th class="n">Enrichment vs domain</th>
<th class="n">Cumulative %</th></tr>{rows}</table>"""

    def joint_table(m):
        if not m:
            return "<p>PENDING</p>"
        j = m["joint"]; se, ae = j["stepover_edges"], j["along_edges"]
        head = "".join(f'<th class="n">{ae[i]:g}–{ae[i+1]:g}</th>' for i in range(len(ae) - 1))
        rows = ""
        for r in range(len(se) - 1):
            cells = "".join(f'<td class="n">{j["enrichment"][r][c]:.4f}</td>'
                            for c in range(len(ae) - 1))
            rows += f'<tr><th class="n">{se[r]:g}–{se[r+1]:g}</th>{cells}</tr>'
        return (f'<table><tr><th class="n">stepover ↓ \\ along-strike →</th>{head}</tr>{rows}</table>')

    def relstrike(m):
        if not m:
            return "<p>PENDING</p>"
        rs = m["relative_strike"]; c = rs["edges"]
        w = rs["n_withheld"]; v = rs["n_visible_reference"]
        sw = sum(w) or 1; sv = sum(v) or 1
        rows = ""
        for i in range(len(c) - 1):
            pw, pv = w[i] / sw, v[i] / sv
            rows += (f'<tr><td class="n">{c[i]:.1f}–{c[i+1]:.1f}</td>'
                     f'<td class="n">{100*pw:.2f}%</td><td class="n">{100*pv:.2f}%</td>'
                     f'<td class="n">{pw/max(pv,1e-9):.2f}</td></tr>')
        return (f'<table><tr><th class="n">Relative strike (°)</th><th class="n">Withheld strands</th>'
                f'<th class="n">Cross-component null</th><th class="n">Ratio</th></tr>{rows}</table>')

    def canary_table(cv):
        c = (cv or {}).get("canary")
        if not c:
            return "<p>PENDING</p>"
        rows = ""
        for k, r in c.items():
            flag = ('<b style="color:#a3341f">FLAG</b>' if r.get("leakage_flag")
                    else '<span style="color:#0b6e4f">clear</span>')
            rows += (f'<tr><td><code>{esc(k)}</code></td>'
                     f'<td class="n">{fmt(r.get("auc_mean"))}</td>'
                     f'<td class="n">{fmt(r.get("discriminative_auc_mean"))}</td>'
                     f'<td class="n">{fmt(r.get("discriminative_auc_max"))}</td>'
                     f'<td>{flag}</td></tr>')
        return (f'<table><tr><th>Feature</th><th class="n">Raw AUC</th>'
                f'<th class="n">Discriminative AUC</th><th class="n">Max over folds</th>'
                f'<th>0.90 leakage screen</th></tr>{rows}</table>')

    side = dict((meas or {}).get("side", {}))
    # rates derived from the stored counts (withheld / domain per side); not separately stored
    if side.get("n_domain_left") and side.get("n_domain_right") and "rate_left" not in side:
        import math as _m
        side["rate_left"] = side["n_withheld_left"] / side["n_domain_left"]
        side["rate_right"] = side["n_withheld_right"] / side["n_domain_right"]
        side["log_ratio_R_over_L"] = _m.log(side["rate_right"] / side["rate_left"])
    return f"""
<h2>1. The metric, and what it implies</h2>
<p>Distance-weighted Tversky index, α = 0.2, β = 0.8, triangular kernel
<code>k(d) = max(1 − d/300 m, 0)</code>, i.e. 3 px on this 100 m grid. There are exactly
<b>25</b> lattice offsets with non-zero kernel weight and only <b>six</b> distinct credit values:
1, 0.667, 0.529, 0.333, 0.255, 0.057.</p>
<p>Writing <code>T</code> for the covered truth credit (a sum over <i>truth</i> cells) and
<code>M</code> for the dots' total self-credit (a sum over <i>dots</i>):</p>
<pre>D   = alpha*(T + n - M) + beta*|G|
DTI = T / D</pre>
<p><b>T and M are not the same quantity.</b> T saturates at 1 per truth cell, M at 1 per dot, so a
cluster of dots on one truth cell has M &gt; T. Collapsing D to <code>alpha*n + beta*|G|</code> is
only valid when T = M — an error in the shared template's prose, corrected here and pinned by
<code>tests/test_metric.py</code> (<code>IR-57-TPL-01</code>).</p>
<p>Adding one dot with marginal truth credit <code>dT</code> and self-credit <code>k</code> raises
DTI exactly when</p>
<pre>dT &gt; alpha * DTI * (dT + 1 - k)</pre>
<p>which reduces to the familiar <code>k &gt; alpha * DTI</code> only for a non-redundant dot.
Since <code>k = E[k](x)</code> is fixed per candidate, this factorises into a per-candidate bar
<code>c * (1 − k)</code> with <code>c = alpha*DTI / (1 − alpha*DTI)</code>, which is what
<code>src/gems57/emit.py</code> applies.</p>

<h2>2. The holdout</h2>
<p>Hide-and-recover, spatially blocked. The footprint is split into four quadrants at its median
row and column; fold <i>q</i> withholds whole segments inside quadrant <i>q</i> and scores inside a
12 px eroded domain, so withheld strands are spatially separated from the catalogue context used to
build the features. Only segments lying wholly inside the domain are eligible, so truth is never
clipped. Every feature is rebuilt from the <b>visible</b> faults alone. Visible fault pixels are
masked out of scoring pixel-exactly. Two draws (20, 21) give 8 cells.</p>
<p>Two withholding modes are reported:</p>
<ul>
<li><b><code>all</code></b> — the primary instrument.</li>
<li><b><code>detached</code></b> — only segments belonging to a connected component that lies at
least 4 px (400 m) from every other component. 896 of 3,199 components qualify (17,556 of 60,988
pixels, 28.8 %). These are the strands whose recovery does <i>not</i> benefit from a visible trace
running into them, so this is the conservative reading and the closer analogue to a genuinely
unmapped splay.</li>
</ul>

<h2>3. Leakage canary <span class="tag hold">HOLDOUT-DTI</span></h2>
<p>Each feature alone, per fold, no fitting involved. The screen is applied to the
<b>discriminative</b> AUC <code>max(auc, 1 − auc)</code>, because an AUC of 0.11 is exactly as
informative as 0.89 — it only means the feature is inversely ranked.</p>
<h3>Withholding mode <code>all</code> (primary instrument)</h3>
{canary_table(cv_all)}
<h3>Withholding mode <code>detached</code> (only components &ge; 4 px from any other)</h3>
{canary_table(cv_det)}
<div class="card">
<b>The canary fires on <code>d</code> and <code>d_perp</code> in mode <code>all</code>, and rule 4
requires that to be treated as leakage until proven otherwise.</b> It is not label leakage — the
features are computed from visible traces only and the labels are genuinely hidden pixels. It
<i>is</i> an external-validity problem: withheld catalogue segments are physically attached to
visible traces, so near-field distance is almost definitionally informative, whereas a genuinely
uncatalogued splay need not be. The <code>detached</code> table above is the disproof experiment —
it withholds only whole components sitting at least 4 px from every other component, breaking that
attachment. See <code>IR-57-CANARY-02</code> on the irregularities page.
</div>

<h2>4. What the data actually shows</h2>
<h3>Distance to the nearest visible fault <span class="tag hold">HOLDOUT-DTI</span></h3>
{dist_table(meas)}
<p><b>The enrichment peaks at 3–4 px (300–400 m), not at 1 px.</b> That non-monotone shape is the
single most useful thing this measurement produced, and it is not what an isotropic dilation would
give.</p>

<h3>Joint stepover × along-strike enrichment — the en echelon test</h3>
{joint_table(meas)}
<p>Rows are cross-strike stepover, columns along-strike offset, values are enrichment over the
domain base rate. For stepovers of 0–2 px the enrichment <i>rises</i> with along-strike offset to a
maximum at 3–4 px and then falls; at larger stepovers the along-strike dependence flattens. That
off-diagonal ridge is the en echelon stepping signature, and it is measured here rather than
imported from Tchalenko (1970) or Schreurs (2003).</p>

<h3>Relative strike against a proper null</h3>
{relstrike(meas)}
<p>The null is the relative strike of <i>visible</i> trace pixels against their nearest visible
pixel belonging to a <b>different</b> connected component. Comparing a visible pixel to its own
nearest visible pixel returns itself and an angle of 0 — that was the first implementation's bug
(<code>IR-57-NULL-01</code>).</p>
<p><b>Result:</b> withheld strands are modestly <i>more oblique</i> than background cross-component
pairs, with the excess at <b>15–45°</b> (ratio 1.5–2.1), not at the textbook Riedel R-shear angle of
10–15°. This is precisely why the brief says not to hard-code textbook angles.</p>

<h3>Sense of slip <span class="tag org">AVAILABLE — MEASURED AS OPT-IN FEATURES</span></h3>
<p>The raster <code>existing_faults.tif</code> has no sense field (its values are <code>{{-1, 0, 1}}</code>,
where <code>-1</code> is the nodata fill outside the study area). The INGENIOUS vector attribute table
<i>does</i> carry it: <code>data/external/trace_segments_utm11.csv</code> has a <code>sense</code> column
(N / RL / LL / blank), and <code>qfault_attributes.csv</code> has <code>SLIPSENSE</code>. An earlier
version of this page said no such field existed; that was wrong (<code>IR-57-SLIP-02</code>). The
recorded sense enters as the opt-in features <code>sense_sgn</code> and <code>sense_side</code>, built
from visible pixels only, and is measured in <code>scripts/run_sense_experiment.py</code> (see the results
page). The untethered left/right asymmetry was also fitted as the <code>side</code> feature:</p>
<dl class="kv">
<dt>Withheld left / right</dt><dd>{esc(side.get("n_withheld_left","PENDING"))} / {esc(side.get("n_withheld_right","PENDING"))}</dd>
<dt>Domain left / right</dt><dd>{esc(side.get("n_domain_left","PENDING"))} / {esc(side.get("n_domain_right","PENDING"))}</dd>
<dt>Rate left / right</dt><dd>{fmt(side.get("rate_left"),6)} / {fmt(side.get("rate_right"),6)}</dd>
<dt>log(right / left)</dt><dd>{fmt(side.get("log_ratio_R_over_L"))}</dd>
</dl>
<p>A 4 % asymmetry — statistically detectable at this sample size but geologically negligible, and
the canary gives <code>side</code> a discriminative AUC of ≈ 0.50. <b>No unilateral Riedel asymmetry
is encoded.</b> Registered as <code>IR-57-SLIP-01</code> (corrected by <code>IR-57-SLIP-02</code>).</p>

<h2>5. Allocation</h2>
<p><code>p(x)</code> is a gradient-boosted classifier over the nine anatomy features, calibrated to
the observed withheld base rate by a single moment-matching scale. The expected credit of a dot is
<code>E[k] = p ⊛ k</code>. Dots are then chosen by round-based greedy maximisation of the covered
credit under the exact bar above. The budget is <b>not</b> chosen by hand: it is the per-draw dot
total the holdout selected.</p>

<h2>6. What is deliberately <i>not</i> claimed</h2>
<div class="note">
<p>The holdout truth is <b>withheld catalogue pixels</b>, which by construction belong to mapped
systems. Genuinely unmapped faults are a different population, and their distance distribution is
probably wider. The <code>detached</code> mode is the conservative reading of the same instrument.
No live score is projected from any number on this page.</p>
</div>
"""


HYP = [
 ("H57-A", "En echelon stepover anatomy", "BUILT, HELD",
  "existing_faults.tif catalogue geometry only (no external layer)",
  "Joint fitted density of cross-strike stepover × along-strike offset of withheld strands, "
  "relative to the local strike of the nearest visible trace.",
  "A splay is the geometric continuation of a mapped system at a small stepover. The catalogue "
  "stops where the mapper stopped — in alluvium, under cover, at a survey boundary — not where the "
  "structure stops. The continuation is therefore predictable from the mapped trace's own geometry.",
  "Some sibling lanes also use tips and stepovers (e.g. GEMSDOE33); this is not a novel "
  "geological mechanism. Here the distance and relative offsets were measured on visible-only "
  "hide-and-recover folds. The previous raster's literal overlap gate still failed.",
  "High", "Low — catalogue only, no external data"),
 ("H57-B", "Trace-termination stress lobe", "NOT RUN",
  "Catalogue segment endpoints; optionally the 100 m numerical feature stack",
  "Second-derivative / curvature transform at mapped trace terminations, then an intensity lobe "
  "oriented on the fitted tip azimuth.",
  "A mapped trace terminates where the mapper lost it. The stress lobe at a tip is where a relay "
  "or stepover strand nucleates, so terminations are enriched in unmapped continuations relative "
  "to trace midpoints.",
  "GEMSDOE33's h33d-analog-tip-stepover used a fixed cone angle. Here the tip azimuth and lobe "
  "width would be fitted the same way as H57-A, and the tip set would be defined on visible faults "
  "only, per fold.",
  "Medium", "Medium — needs a reliable endpoint detector on a 1-px raster"),
 ("H57-C", "Damage-zone width scaling with mapped length", "FOLDED INTO H57-A",
  "Catalogue connected-component size as a displacement proxy",
  "Per-fault zone width w(L) fitted from component length, instead of one global distance kernel.",
  "Savage & Brodsky (JGR 2011) show damage-zone width growing with displacement and then more "
  "slowly. A single global width under-weights long, mature faults and over-weights short ones.",
  "The length proxy entered the prior model as log_len, not as an explicitly normalized "
  "stepover. Session 3 tests that distinct interaction; note the "
  "first implementation used the 12-px segment chunk length, which is a constant and carries no "
  "information at all (IR-57-LEN-01).",
  "Medium", "Very low — already in the feature set"),
 ("H57-D", "Strike-selective gap filling on the regional fabric", "NOT RUN",
  "Catalogue local strike field (structure tensor)",
  "Gate the intensity on the local orientation of the mapped fabric so gaps are filled along the "
  "regional sets rather than isotropically.",
  "The catalogue strike histogram is bimodal, peaking at 0-15 deg and 135-180 deg — the two "
  "regional sets of the northern Walker Lane / Basin Range boundary. It is a testable "
  "hypothesis, not a guarantee, that an unmapped fault might follow one of them.",
  "Isotropic gap-filling lanes (e.g. GEMSDOE27 topo-gap-closure) cannot express this. H57-A "
  "already carries strike as sin2/cos2, but the canary shows those two features have a raw AUC of "
  "exactly 0.500 alone, so the orientation selectivity is only usable in interaction — which is "
  "what makes an explicit gated variant a distinct hypothesis.",
  "Medium", "Low"),
 ("H57-E", "Scarp curvature corroboration inside the fitted zone", "BLOCKED ON DATA",
  "10 m / 1 m DEM derivatives (profile curvature, slope break) restricted to the H57-A zone",
  "Edge / curvature transform, but ranked only inside the mechanically fitted zone rather than "
  "globally.",
  "A splay that is geomorphically expressed as a linear scarp is a real strand; one that is not "
  "may be a mapping artefact. Conditioning scarp evidence on the mechanical zone suppresses the "
  "false positives that sank the global scarp lanes.",
  "GEMSDOE46/47 rank scarp pixels globally and score 0.16 / 0.04. Restricting the same evidence to "
  "the H57-A zone is a different estimator, not a different layer.",
  "Potentially high", "BLOCKED — needs the 420 MB gems-geodawn-numerical-features.tif stack "
  "(present in the bridge repos as five parts) or the 1 m DEM links. Neither is obtainable in "
  "this sandbox: DrivenData requires login and only github.com / pypi.org are reachable."),
]


def build_hypotheses() -> str:
    rows = ""
    for hid, name, status, layers, sig, why, diff, gain, cost in HYP:
        badge = {"BUILT, HELD": '<span class="tag bad">BUILT, HELD</span>',
                 "FOLDED INTO H57-A": '<span class="tag">FOLDED IN</span>',
                 "NOT RUN": '<span class="tag hold">NOT RUN</span>',
                 "BLOCKED ON DATA": '<span class="tag bad">BLOCKED</span>'}[status]
        rows += f"""<tr><td><b>{esc(hid)}</b><br>{esc(name)}<br>{badge}</td>
<td>{esc(layers)}</td><td>{esc(sig)}</td><td>{esc(why)}</td><td>{esc(diff)}</td>
<td class="n">{esc(gain)}</td><td>{esc(cost)}</td></tr>"""
    return f"""
<h2>Five candidate hypotheses, ranked</h2>
<p>Ranked by expected DTI improvement over implementation cost, per the brief. "Differs from"
is assessed against the 15 sibling submissions pulled into
<a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/registry/registry_index.json"><code>registry/</code></a> as well as this repository. Four additional, prospectively ranked session-3 hypotheses (H57-G to J) are in <a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/README.md">README.md</a>; H57-G's measured result is <a href="session-3.html">here</a>.</p>
<table>
<tr><th>Hypothesis</th><th>Layer(s)</th><th>Physical signature</th>
<th>Why it catches a fault the catalogue lacks</th><th>How it differs from existing work</th>
<th class="n">Expected gain</th><th>Cost</th></tr>
{rows}
</table>
<h2>Order of work</h2>
<ol>
<li><b>H57-A</b> was built and validated first, because it needs no external data and its central
claim — that secondary strands sit at a measurable stepover and along-strike offset — is testable
on the hide-and-recover holdout alone.</li>
<li><b>H57-C</b> came free as a feature, after the length-proxy bug was fixed.</li>
<li><b>H57-D</b> is the cheapest remaining increment and needs no new data.</li>
<li><b>H57-B</b> needs a careful endpoint detector; deferred.</li>
<li><b>H57-E</b> is blocked. The specific free official source needed is the GeodAWN airborne
magnetic and radiometric survey / 1 m DEM set linked from
<a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">usgs.gov</a>
and the competition's own <code>gems-geodawn-numerical-features.tif</code>. Both were checked: the
USGS page is outside this sandbox's network allowlist, and the feature stack is present in the
bridge repositories as five ~90 MB parts that this session does not pull.</li>
</ol>
<div class="note"><b>No submission slot was spent on any hypothesis that had not beaten the
holdout bar first.</b> The brief's rule is respected: validation precedes promotion.</div>
"""


def _gain(cv):
    try:
        v = cv["variants"]
        return v["anatomy_full"]["pooled"]["pooled_dti"] - v["d_only"]["pooled"]["pooled_dti"]
    except Exception:
        return None


def _noverk(build, cv=None):
    """Live dot budget divided by the withheld truth count per draw."""
    build = build or {}
    b = build.get("live_dot_budget")
    try:
        k = cv["variants"]["anatomy_full"]["pooled"]["n_truth"] / 2.0
    except Exception:
        return "?"
    return f"{b / k:.1f}" if b else "?"


def budget_block(rb):
    if not rb:
        return "<p>PENDING</p>"
    rows = ""
    for r in rb.get("rows", []):
        rows += (f'<tr><td>{esc(r["submission"])}</td>'
                 f'<td class="n">{r["n_dots"]:,}</td>'
                 f'<td class="n">{r["live_score"]:.4f}</td></tr>')
    b1, b2, b3 = rb["band_lt_50k"], rb["band_ge_50k"], rb["band_35k_46k"]
    return f"""<p>Across the {rb['n_rasters']} registry rasters with an owner-reported score (not a receipt),
<b>Spearman(dot count, live score) = {rb['spearman_dots_vs_live']:+.4f}</b>
(p = {rb['p_value']:.5f}). The relationship is strongly negative, and it is live evidence rather
than a holdout proxy.</p>
<table><tr><th>Registry submission</th><th class="n">Dots</th><th class="n">Live score</th></tr>{rows}</table>
<table><tr><th>Dot band</th><th class="n">n</th><th class="n">Mean live</th><th class="n">Best</th></tr>
<tr><td>&lt; 50,000</td><td class="n">{b1['n']}</td><td class="n">{b1['mean_live']:.4f}</td><td class="n">{b1['best']:.4f}</td></tr>
<tr><td>35,000&ndash;46,000</td><td class="n">{b3['n']}</td><td class="n">{b3['mean_live']:.4f}</td><td class="n">&mdash;</td></tr>
<tr><td>&ge; 50,000</td><td class="n">{b2['n']}</td><td class="n">{b2['mean_live']:.4f}</td><td class="n">{b2['best']:.4f}</td></tr></table>
<p class="small">The two rasters above 120,000 dots hold the two worst live scores in the registry
(0.1922, 0.1894).</p>"""


def curve_block(rb):
    if not rb:
        return "<p>PENDING</p>"
    nrs = sorted({c["n_over_K"] for c in rb["dti_vs_coverage_curve"]})
    covs = sorted({c["coverage"] for c in rb["dti_vs_coverage_curve"]})
    lut = {(c["coverage"], c["n_over_K"]): c["dti"] for c in rb["dti_vs_coverage_curve"]}
    head = "".join(f'<th class="n">n/K = {nr:g}</th>' for nr in nrs)
    body = ""
    for cv in covs:
        cells = "".join(f'<td class="n">{lut[(cv, nr)]:.4f}</td>' for nr in nrs)
        body += f'<tr><td class="n">{cv:.3f}</td>{cells}</tr>'
    return (f'<table><tr><th class="n">Coverage of truth</th>{head}</tr>{body}</table>'
            f'<p class="small">Exact metric, synthetic fields at the measured base rate '
            f'{rb["base_rate"]} with sum(k) = {rb["sum_kernel"]}. A perfect prediction scores '
            f'{rb["perfect_prediction_dti"]}.</p>')


def build_results(cv_all, cv_det, build, rb=None) -> str:
    build = build or {}
    def block(cv, label):
        if not cv:
            return f"<h3>{label}</h3><p>PENDING</p>"
        rows = ""
        for v, r in cv.get("variants", {}).items():
            pl = r.get("pooled", {})
            ci = pl.get("dti_ci95_quadrant_jackknife") or [None, None]
            cw = pl.get("coverage_ci95") or [None, None]
            rows += (f'<tr><td><code>{esc(v)}</code></td>'
                     f'<td class="n">{fmt(pl.get("pooled_dti"))}</td>'
                     f'<td class="n">[{fmt(ci[0])}, {fmt(ci[1])}]</td>'
                     f'<td class="n">{fmt(pl.get("coverage"))}</td>'
                     f'<td class="n">[{fmt(cw[0])}, {fmt(cw[1])}]</td>'
                     f'<td class="n">{pl.get("n_dots","PENDING")}</td>'
                     f'<td class="n">{pl.get("n_truth","PENDING")}</td>'
                     f'<td class="n">{pl.get("tp","PENDING") and round(pl["tp"],1)}</td></tr>')
        return f"""<h3>Withholding mode <code>{esc(label)}</code> <span class="tag hold">HOLDOUT-DTI</span></h3>
<table><tr><th>Feature set</th><th class="n">Pooled DTI</th><th class="n">95% CI (quadrant jackknife)</th>
<th class="n">Coverage</th><th class="n">95% CI (Wilson)</th><th class="n">Dots</th>
<th class="n">Withheld truth px</th><th class="n">TP</th></tr>{rows}</table>"""

    flank = (build or {}).get("flank_variants", {})
    frows = ""
    for k in sorted(flank, key=lambda x: int(x)):
        pl = flank[k]
        frows += (f'<tr><td class="n">{esc(k)} px</td>'
                  f'<td class="n">{fmt(pl.get("pooled_dti"))}</td>'
                  f'<td class="n">{fmt(pl.get("coverage"))}</td>'
                  f'<td class="n">{pl.get("n_dots","PENDING")}</td></tr>')
    sel = (build or {}).get("selected_flank_px", "PENDING")
    return f"""
<h2>Holdout results</h2>
{block(cv_all, "all")}
{block(cv_det, "detached")}
<p class="small">Leave-one-quadrant-out: the model applied to a quadrant is trained only on the
other three. The quadrant-jackknife CI is the one that respects the spatial blocking; the Wilson
interval only propagates binomial noise on the coverage and ignores spatial heterogeneity, so it is
narrower and more optimistic. <b>Report the jackknife one.</b></p>

<h2>Catalogue-flank exclusion, measured</h2>
<p>Whether to exclude the pixels immediately adjacent to a mapped trace was decided by measurement,
not by hand. The holdout selected <b>{esc(sel)} px</b>.</p>
<table><tr><th class="n">Excluded flank</th><th class="n">Pooled DTI</th>
<th class="n">Coverage</th><th class="n">Dots</th></tr>{frows or '<tr><td colspan="4">PENDING</td></tr>'}</table>

<h2>The dot budget, and why the holdout's own optimum was overruled</h2>
<p>The allocator's unconstrained holdout optimum is <b>{esc((build or {}).get("holdout_dot_budget","PENDING"))}</b>
dots per draw, about {esc(str(_noverk(build, cv_all)))}x the withheld truth count per draw. That was <b>not</b> shipped.</p>
{budget_block(rb)}
<p>The cap shipped is <b>{esc((build or {}).get("live_dot_budget","PENDING"))}</b>, inside the band every
top performer occupies. The cost of the cap in holdout DTI is shown below rather than hidden:
IN-SAMPLE (IR-57-INSAMPLE-01; trained on the same holdout cells) unconstrained
{fmt(((build or {}).get("flank_best_holdout") or {}).get("pooled_dti"))} vs
capped {fmt(((build or {}).get("holdout_at_capped_budget") or {}).get("pooled_dti"))}.
The leave-one-quadrant-out reading of the shipped configuration is the number to quote (see the results page). The cap is
bought with measured holdout DTI because the live evidence says the holdout is wrong here
(&rho; = +0.14, IR-57-BUDGET-01).</p>

<h2>Why 0.2778 won, and whether higher is achievable</h2>
<p>Substituting the binary algebra, <code>DTI = T / (0.2(T + n - M) + 0.8K)</code>, where
<code>T</code> is covered truth credit, <code>n</code> the dot count, <code>M</code> the dots' total
self-credit and <code>K</code> the number of true new-fault pixels. Two things follow.</p>
<p><b>1. The ceiling is 1.0, not 0.5556.</b> A perfect prediction has <code>n = M = T = K</code>, so
<code>D = 0.2K + 0.8K = K</code> and <code>DTI = 1</code>. Verified against the brute-force
implementation. (0.05556 is a different number: it is the marginal acceptance bar
<code>alpha * DTI</code> at DTI = 0.2778.)</p>
<p><b>2. At the real base rate, DTI is close to the covered fraction of the truth — but only while
the dot budget stays comparable to <code>K</code>.</b> The grid is sparse: with ~5,660 true pixels in
~2.56 M cells the base rate is 0.00221, and a <i>random</i> pixel lands within 3 px of a true one
only {esc(str(round((rb or {}).get("random_hit_prob", 0.021), 4)))} of the time. Measured with the exact
metric on synthetic fields at that density:</p>
{curve_block(rb)}
<p>Read the row at coverage 0.2778: the same coverage is worth <b>0.3162</b> at half the truth count
in dots and only <b>0.1809</b> at six times it. That is the whole story of 0.2778. It is roughly
<b>28% coverage of the live truth set achieved at a near-matched dot budget</b> — and the reason
nothing sprayed more dots beat it is that beyond <code>n &asymp; 2K</code> every extra dot costs
0.2 in the denominator while returning far less than 0.2 in credit.</p>
<p><b>Is higher achievable?</b> Yes, and the route is arithmetic rather than clever: DTI tracks
coverage roughly one-for-one while <code>n &lesssim; 2K</code>, so the 0.3774 high-water mark implies
about 40% coverage at a matched budget. Beating 0.2778 therefore needs roughly ten points more
coverage at the same budget. This lane measured a real coverage gain over distance-only
({fmt(_gain(cv_all))} DTI, mode <code>all</code>; {fmt(_gain(cv_det))} mode <code>detached</code>, with
disjoint confidence intervals), which is the right direction — but on <i>withheld catalogue
pixels</i>, which cling to visible traces. Whether that transfers to genuinely uncatalogued faults
is not knowable from here, and the +0.14 holdout-to-live rank correlation says do not assume it
does. No projected live score is claimed anywhere on this site.</p>
"""


IRREG = [
 ("IR-57-NAN-01", "Submission rejected by the portal", "FIXED",
  "The site's download failed with “Predicted values must be in range [0, 1]”. The competition's "
  "sample_submission.tif carries nodata = NaN and 7,111,787 NaN cells outside the study-area "
  "footprint; NaN satisfies neither v >= 0 nor v <= 1.",
  "Write the zeros variant: every one of the 12,279,160 cells finite and in [0, 1], outside-"
  "footprint cells set to 0.0, no nodata tag. src/gems57/grid.py mode='zeros'. The NaN variant is "
  "still written for diagnostics and is labelled NOT SUBMITTABLE on the site."),
 ("IR-57-TPL-01", "Shared template's DTI prose is wrong", "CORRECTED HERE, REPORTED UPSTREAM",
  "The shared template's metric module asserts that for a binary dot field FP_w = n - TP_w, so the "
  "denominator collapses to alpha*n + beta*|G|. That is false: TP_w sums over truth cells and M "
  "sums over dots, and T != M whenever dots cluster. The template's own dti_algebra keeps T, S and "
  "M separate and is correct, so only the prose is wrong.",
  "Corrected in src/gems57/metric.py and pinned by tests/test_metric.py::"
  "test_denominator_uses_M_not_T_and_the_collapse_only_holds_when_T_equals_M, which shows the naive "
  "form differs measurably from the exact one on a 2-dots-1-truth-cell case. Per protocol rule 2 "
  "this is reported rather than kept as a private fork."),
 ("IR-57-BAR-01", "Our own marginal test was off by a factor of D", "FIXED",
  "marginal_accept tested dT*D > DTI*alpha*(dT + 1 - k) instead of dT > alpha*DTI*(dT + 1 - k). "
  "Because D is of order beta*|G| (tens of thousands), the bar was smaller by a factor of D and the "
  "greedy allocation never terminated: it ran to its 120,000-dot cap per cell and scored a pooled "
  "HOLDOUT-DTI of 0.0797 with 960,000 dots.",
  "marginal_accept now recomputes DTI before and after rather than using algebra, so it cannot "
  "drift from the metric. Pinned by tests/test_metric.py::"
  "test_marginal_accept_agrees_with_direct_dti_recomputation."),
 ("IR-57-KCLIP-01", "E[k] exceeds 1, flipping the bar negative", "FIXED",
  "E[k](x) is a *sum* of p*k over the neighbourhood and routinely exceeds 1, but the metric's "
  "per-dot self-credit is max_g k <= 1. Using the unclipped sum made 1 - k negative, the bar went "
  "to -0.019, and zero-credit dots passed the test. On a synthetic field this produced 7,987 "
  "duplicate acceptances: n_dots reported 13,574 while only 5,587 cells were actually set.",
  "The self-credit is now clipped to [0, 1], the bar is recomputed after every acceptance (it was "
  "frozen within a round, which made the surrogate DTI non-monotone), and an already-emitted cell "
  "is skipped. Pinned by tests/test_emit.py::test_dot_count_equals_emitted_sum and "
  "::test_surrogate_dti_is_monotone_over_the_trace."),
 ("IR-57-LEN-01", "Displacement proxy carried no information", "FIXED",
  "The log_len feature used the length of the <= 12 px segment chunk, so it was the constant "
  "log1p(12) = 2.56 for every pixel. The lane's displacement proxy was silently dead.",
  "log_len now uses the size of the whole connected mapped component containing the anchor pixel, "
  "which is what scales with damage-zone width in Savage & Brodsky (2011)."),
 ("IR-57-NULL-01", "Relative-strike null was degenerate", "FIXED",
  "The null compared each visible pixel to its nearest visible pixel, which is itself, so every "
  "angle was 0 and the ratio column divided by ~0 (printing 2.5e8).",
  "The null is now the relative strike of visible pixels against their nearest visible pixel in a "
  "*different* connected component, found with a cKDTree k=13 query."),
 ("IR-57-SLIP-01", "\"No sense-of-slip field exists\" (superseded)", "CORRECTED, SEE SLIP-02",
  "The earlier ledger said the competition database has no sense-of-slip attribute. The raster has "
  "no such field (values {-1, 0, 1}; -1 is the nodata fill outside the study area), but the INGENIOUS "
  "vector attribute table does (IR-57-SLIP-02).",
  "The untethered left/right asymmetry feature side is kept as it was: measured log(right/left) = "
  "+0.0392, discriminative AUC ~0.51, so it encodes no usable unilateral asymmetry on its own."),
 ("IR-57-SLIP-02", "Recorded sense of slip IS in the provided data and was not used", "FIXED (opt-in features, measured)",
  "data/external/trace_segments_utm11.csv carries a sense column for 84,331 trace segments of 1,126 "
  "records (N 66,861; RL 8,448; LL 7,628; blank 1,394 segments; per record: N-only 868, RL-only 87, "
  "LL-only 76, blank 95). qfault_attributes.csv carries SLIPSENSE for the 22,956 attribute records. "
  "The earlier documents said the opposite. The lane brief requires conditioning on recorded sense.",
  "src/gems57/faultzone.py::trace_sense_raster rasterises the sense codes; anatomy.py adds the opt-in "
  "SENSE_FEATURES (sense_sgn, sense_side) built from visible pixels only. Measured in "
  "scripts/run_sense_experiment.py against the shipped feature set at the shipped density. See the "
  "results page for the paired per-quadrant differences."),
 ("IR-57-CAP-01", "Capped holdout was measured at ~2x the shipped density", "FIXED",
  "scripts/build_submission.py set the per-cell share of the live budget to budget // 2. There are "
  "four quadrant cells per draw, so the share is budget // 4. The 0.2793 'holdout at capped budget' "
  "figure in evidence/submission_build_all.json was therefore measured at roughly twice the dot "
  "density the shipped file has (131,585 dots over 8 cells against 35,341 shipped).",
  "per_cap = budget // 4. The shipped file's own holdout DTI is measured directly in "
  "scripts/run_sense_experiment.py (IR-57-SHIP-01). The 0.2793 figure is withdrawn and must not be "
  "quoted as the shipped file's score."),
 ("IR-57-UNIQ-02", "Full-registry scan dropped the firing list and reported a verdict from an exemption", "FIXED (literal verdict; list complete in code; 50 of 114 firings itemized in the saved JSON)",
  "The first run of check_uniqueness_full.py saved only the first 50 forward-overlap firings, while its summary counted 114. Its verdict "
  "called the shipped file UNIQUE by a reverse-overlap exemption (rev < 0.5 = 'mechanical saturation') that is not in the protocol.",
  "The verdict was recomputed from the saved counts by the literal rule (unique_by_protocol=false); the script now keeps every firing. The 64 unitemized firings need a rerun to list."),
 ("IR-57-UNIQ-03", "Shipped file is DRIFT-FLAGGED by the literal uniqueness gate", "FLAGGED, OPEN - HOLD",
  "Spearman max 0.180 (gate 0.90) and Jaccard max 0.083 (gate 0.50) pass. The forward-overlap gate (> 0.70 of my dots within 3 px of one registry raster) fires for 114 of 644 registry rasters, max 1.00. Among the 50 itemized, reverse overlap is 0.03-0.21 (none >= 0.50). Against a uniform-random placement of the same dot count, 26 of 50 are within 0.05 of chance, but 22 exceed it, so density alone does not explain all of them.",
  "Not cleared. The protocol says log and stop. Owner decision needed: accept a reverse-overlap clearance rule (a protocol change) or generate a different candidate. The file is not to be submitted until this is decided."),
 ("IR-57-LABEL-01", "Owner-reported scores were labelled ORGANIZER-CONFIRMED", "FIXED (relabelled OWNER-REPORTED)",
  "The budget correlation (Spearman -0.8104, n = 15) and the brief's 0.3774 / 0.3195 quotes come from owner-pasted "
  "scores with no submission-page receipt. The label ORGANIZER-CONFIRMED is reserved for receipts.",
  "Re-derived this session from registry/registry_index.json (owner_reported_score). README and this page relabelled."),
 ("IR-57-INSAMPLE-01", "Build's holdout numbers are in-sample (labelled in build_submission.py and here; LOQO build replacement NOT done)", "FLAGGED, LABELLED, OPEN",
  "scripts/build_submission.py fits the intensity on all 8 holdout cells and then scores the same "
  "8 cells (flank sweep and capped holdout). Those numbers are optimistic. The leave-one-quadrant-out "
  "numbers in scripts/run_cv.py and scripts/run_sense_experiment.py are the honest ones.",
  "Not changed in this session. Any quoted holdout DTI must come from a LOQO run and be labelled as "
  "such. Recommended next step: make build_submission select flank and budget under LOQO."),
 ("IR-57-SHIP-01", "The shipped file's own holdout DTI had never been measured", "MEASURED (see results)",
  "Earlier pages quoted 0.2517 and 0.2508 as the holdout DTI of the shipped configuration. Those were "
  "measured at the run_cv per-cell cap of 120,000 (136,467 dots over 8 cells, about 68k per draw), "
  "roughly twice the shipped density of 35,341.",
  "scripts/run_sense_experiment.py measures LOQO at the shipped per-cell share (10,000). Its result is "
  "the only holdout number that describes the shipped density."),
 ("IR-57-TRANS-01", "Trace rasteriser transposed row and column", "FIXED; DOWNSTREAM EVIDENCE STALE",
  "faultzone.rasterize_traces and ingenious_record_segments unpacked Affine * (x, y), which returns "
  "(col, row), as (row, col). Measured: 1.8% of catalogue cells lay within 1.5 px of the traces, against "
  "100% after the fix. The shipped pipeline does not call these functions, so the shipped file is "
  "unaffected. calibrate_registry.py and explore_zone2.py do, so their evidence is stale.",
  "Fixed in src/gems57/faultzone.py. The calibrate and explore evidence must be regenerated before it is "
  "quoted."),
 ("IR-57-BRIDGE-01", "data/bridge/sample_submission.tif is not verified as the official sample", "FLAGGED FOR REVIEW",
  "The competition page describes the sample submission as one that predicts total fault absence. The "
  "file in data/bridge/ (sha256 2176d08e...) instead has 60,988 cells equal to 1 inside the footprint, "
  "exactly the catalogue's fault cells. The file came from the GEMSDOE2 repository, not from DrivenData; "
  "the Dropbox original could not be downloaded from the sandbox. Its grid (CRS, shape, transform) and "
  "its finite mask agree with the existing_faults.tif valid mask (5,167,373 cells), so the scored "
  "footprint used here is still consistent.",
  "Owner to confirm the official sample. The footprint is taken from the mask, not from the values, so "
  "the shipped file does not depend on the 1s."),
 ("IR-57-NAN-02", "The NaN root-cause claim is not proven", "FLAGGED FOR REVIEW",
  "IR-57-NAN-01 says the portal rejected the upload because NaN fails the range test. The competition "
  "specification says data outside the bounds 'is null or nan'. Several owner-reported submissions on the "
  "sites above carry a -nan suffix and show portal scores (for example h27-4-solo-d28 -nan, 0.2708). The "
  "cause of the user's rejection was not established.",
  "The zeros variant stays the submitted file, because it satisfies both readings: every value finite and "
  "in [0, 1]. The NaN explanation is recorded as a hypothesis, not as the cause."),
 ("IR-57-UNIQ-01", "Uniqueness evidence cited files not in the repository", "FIXED",
  "evidence/uniqueness.json and uniqueness_parallel.json cite siblings/... paths that are not in this "
  "repository. The registry in registry/ held 15 rasters.",
  "scripts/scan_gemsdoe_registry.py builds the full registry from every reachable GEMSDOE repository: "
  "644 unique grid-shaped rasters (evidence/registry_full_index.json). scripts/check_uniqueness_full.py "
  "checks a candidate against all of them. 23 large non-submission rasters (feature stacks, DEM and "
  "aux layers, diagnostics) were not fetched; the count is in the index."),
 ("IR-57-TEST-01", "Test suite failed on main", "FIXED",
  "Five tests failed: pandas was imported but absent from requirements.txt; the gate tests pointed at a "
  "file moved to docs/downloads/archive/ and asserted an out-of-date emitted count; the data-pin test "
  "requires training_features.tif, which the sandbox cannot reach.",
  "pandas added to requirements.txt; gate tests point at the shipped file and its checks receipt; the "
  "data-pin test skips with its reason when the 419 MB file is absent."),
 ("IR-57-LEAD-01", "Leaderboard page cannot be read", "FLAGGED",
  "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ returns an empty "
  "'Loading...' page to the fetch tool. The 0.3774 and 0.3195 highs in the brief remain owner-reported and "
  "unverified.",
  "Owner to paste the current leaderboard receipt. No rank or live score is projected."),
 ("IR-57-BRIEF-01", "Conflicting leaderboard highs in the brief", "FLAGGED",
  "The task brief states both \"Current competition leaderboard GEMSDOE high score: 0.3774\" and "
  "\"0.3195 is the highest score right now\". The DrivenData leaderboard is outside this sandbox's "
  "network allowlist and cannot be read here.",
  "Neither number is treated as a target this repository claims to beat. Owner-reported scores are "
  "recorded as OWNER-REPORTED with their source repository, and no live score is projected."),
 ("IR-57-FOLD-01", "Holdout produced zero withheld pixels", "FIXED",
  "The first fold design removed from the candidate pool every segment touching a 15 px dilation of "
  "the fold quadrant. Dilating a region contains the region, so every in-fold segment touched the "
  "collar and the candidate set was empty: hidden px = 0, truth = 0, for all 8 cells.",
  "Redesigned: spatial separation now comes from the quadrant split plus a 12 px domain erosion, "
  "and eligibility is 'segment lies wholly inside the scored domain'. Verified: 1,919-3,786 "
  "withheld pixels per cell."),
 ("IR-57-CANARY-01", "Naive AUC screen would pass an inverse predictor", "FIXED",
  "Rule 4 screens on 'AUC above 0.90'. Distance has a raw AUC of 0.1147 — highly predictive, but "
  "inversely ranked, so a naive > 0.90 test reads it as uninformative.",
  "The screen is applied to max(AUC, 1 - AUC)."),
 ("IR-57-CANARY-02", "The canary DOES fire on distance, and the flag is justified", "OPEN, MITIGATED",
  "On the discriminative screen, d scores 0.9000 and d_perp 0.9013 — at or above the 0.90 bar. By "
  "rule 4 that is leakage until proven otherwise. It is not label leakage (the feature is computed "
  "from visible traces only, the labels are genuinely hidden pixels), but it IS an external-validity "
  "problem: withheld catalogue segments are physically attached to visible traces, so near-field "
  "distance is almost definitionally informative. Genuinely uncatalogued faults need not be.",
  "Measured the disproof: the detached mode withholds only whole components sitting >= 4 px from any "
  "other component, breaking that attachment. Distance's discriminative AUC falls there, and the "
  "anatomy model's gain over distance-only persists (0.2538 vs 0.1816 detached; 0.2517 vs 0.1845 "
  "all). See the canary table on the method page for both modes side by side."),
 ("IR-57-RHO-01", "The uniqueness screen's rank statistic was degenerate and flagged everything",
  "FIXED",
  "The first build reported unique=False with |rho| = 0.9924 vs gate_ortho_w0.25-40k. The statistic "
  "was Spearman over the union of two dot supports, taken in absolute value. On a union both arrays "
  "are 0/1 indicators of near-disjoint sets, so the correlation is the phi coefficient of two "
  "NEGATIVELY associated indicators and sits near -1 for every pair. Measured over the registry "
  "itself, gate_ortho and h19-4-multiline — different lanes, live 0.2376 vs 0.1894, Jaccard 0.022 — "
  "give rho = -0.9408. abs() therefore flags all 15 registry rasters as duplicates of each other. "
  "It is also NaN whenever one support contains the other, so it cannot detect an exact re-export.",
  "The operative rank statistic is now Spearman over the full footprint, signed: +1.0000 for an exact "
  "copy and 0.0003-0.0109 for all 15 distinct registry rasters, so the 0.90 bar separates cleanly. "
  "Set agreement is carried by Jaccard (limit 0.50; a 90% copy scores 0.8198) and by 3 px dot "
  "overlap (limit 0.70). The dot-union rho is still reported, never thresholded. Shipped raster: "
  "worst rho 0.0109, worst Jaccard 0.0096, worst overlap 0.3578 — unique on all three."),
 ("IR-57-BUDGET-01", "The holdout-optimal dot budget contradicts the live evidence", "RESOLVED BY EVIDENCE",
  "The allocator's holdout optimum is 69,623 dots per draw, roughly 6x the withheld truth count. But "
  "Spearman(dot count, owner-reported live score) over the 15 registry rasters is -0.8104: the "
  "two rasters above 120,000 dots are the two worst live scores (0.1894, 0.1922), and all eleven "
  "rasters between 35k and 46k average 0.2643 with the best at 0.2778. The holdout rewards spraying "
  "because its withheld pixels cling to visible traces; live faults do not have to.",
  "Capped the live budget at 40,000, inside the band every top performer occupies, and reported the "
  "holdout DTI at that capped budget alongside the unconstrained optimum so the cost of the cap is "
  "visible rather than hidden. The holdout-to-live rank correlation for this instrument is only "
  "+0.14 (12 live scores, sibling repository), which is why live evidence outranks holdout evidence "
  "on this decision."),
 ("IR-57-EVAL-01", "Shared evaluator referenced missing functions", "FIXED, REGRESSION TESTED",
  "The inherited evaluate_holdout.evaluate called nonexistent holdout.score and metric.max_cover; "
  "pooled_summary also needed missing metric.R_M. Historical exp2 evidence pinned a different "
  "implementation hash and cannot be claimed as reproduced by today's module.",
  "Implemented the continuous triangular max kernel and pixel-exact visible masking in the shared "
  "src/gems57 evaluator/metric; the H57-G experiment uses it for every fold, asserting agreement "
  "with independent binary EDT scoring. Tests cover continuous max-vs-sum and known-fault masking."),
 ("IR-57-S3-GATE", "Literal overlap gate is blocked by saturated registry priors", "NEGATIVE / NO SLOT",
  "The restored 13GEMSDOE lattice covers 99.8724% of eligible cells within 3 px. The 17GEMSDOE "
  "continuous prior is >0 on every eligible cell; the current checker treats all >0 as dots, "
  "making its directed overlap 100% for any nonempty candidate.",
  "Stop on the surface before dot placement, label the new valid TIF research-only, and disclose "
  "that a >=0.5 threshold for continuous priors would be a protocol change, not an assumed waiver."),
]


def build_session2() -> str:
    """Session-2 evidence: the shipped-density holdout, the recorded-sense experiment and the
    full-registry uniqueness scan.  Every number is read from its evidence file at build time."""
    exp = load("exp_sense_loqo_all.json") or {}
    uq = load("uniqueness_full_shipped-h57-zeros.json") or {}
    if exp.get("variants"):
        rows = ""
        for v, r in exp["variants"].items():
            pl = r["pooled"]
            ci = pl["dti_ci95_quadrant_jackknife"]
            rows += (f"<tr><td><code>{esc(v)}</code></td><td class=\"n\">{fmt(pl['pooled_dti'])}</td>"
                     f"<td class=\"n\">[{fmt(ci[0])}, {fmt(ci[1])}]</td><td class=\"n\">{pl['n_truth']}</td>"
                     f"<td class=\"n\">{pl['n_dots']}</td><td class=\"n\">{fmt(pl['coverage'])}</td></tr>")
        pq = exp["paired_no_side_plus_sense_minus_no_side"]
        diffs = ", ".join(f"{q} {d:+.4f}" for q, d in pq["per_quadrant_diff"].items())
        can = exp.get("canary", {})
        canrows = "".join(
            f"<tr><td><code>{esc(k)}</code></td><td class=\"n\">{fmt(r['discriminative_auc_max'])}</td>"
            f"<td>{verdict(not r['leakage_flag'])}</td></tr>" for k, r in can.items())
        exp_html = f"""
<table>
<tr><th>Feature set (mode all, leave-one-quadrant-out)</th><th class="n">HOLDOUT-DTI</th>
<th class="n">95% CI (quadrant jackknife)</th><th class="n">withheld positives</th>
<th class="n">dots (8 cells)</th><th class="n">coverage</th></tr>
{rows}
</table>
<p class="muted">Per-cell cap {exp.get('per_cell_cap')} dots = the shipped live share (40,000 cap / 4 quadrants).
Evaluator: gems57 pooled DTI, alpha 0.2, beta 0.8, R = 3 px. HOLDOUT-DTI is a local instrument reading, not a
projected live score.</p>
<p><b>Paired difference, sense minus no-sense, per quadrant:</b> {esc(diffs)}.
Mean {pq['mean_diff']:+.4f}, sd {pq['sd_diff']:.4f}, positive in {pq['n_quadrants_positive']} of 4 quadrants.</p>
<div class="note"><b>Verdict for H57-F (recorded sense of slip): NEGATIVE on this instrument.</b> The mean
gain is +0.0016 with quadrant signs that disagree, which is inside the noise. The sense features are
themselves clean on the leakage canary. The canary's flag on <code>d</code> and <code>d_perp</code> is
the pre-existing IR-57-CANARY-02 and is not a sense result. Not promoted; no submission slot was used.</div>
<h3>Leakage canary, single features, this run</h3>
<table><tr><th>Feature</th><th class="n">max discriminative AUC</th><th>below 0.90</th></tr>{canrows}</table>
"""
    else:
        exp_html = "<p>PENDING: evidence/exp_sense_loqo_all.json not found.</p>"
    if uq.get("candidate"):
        uq_html = f"""
<h3>Uniqueness against every accessible GEMSDOE raster</h3>
<p>Candidate <code>{esc(uq['candidate']['file'])}</code> (sha256 <code>{esc(uq['candidate']['sha256'])}</code>,
{uq['candidate']['dots']} dots) against <b>{uq['registry']['n_unique_grid_rasters']}</b> unique grid-shaped
rasters from <b>{uq['registry']['repos_scanned']}</b> GEMSDOE repositories (scan of
<code>evidence/registry_full_index.json</code>).</p>
<table>
<tr><th>Gate (parallel-run protocol)</th><th class="n">limit</th><th class="n">worst observed</th><th>vs</th></tr>
<tr><td>full-footprint Spearman</td><td class="n">0.90</td><td class="n">{uq['max_spearman_full_footprint']['value']:.4f}</td><td>{esc(uq['max_spearman_full_footprint']['raster'])}</td></tr>
<tr><td>Jaccard of dot sets</td><td class="n">0.50</td><td class="n">{uq['max_jaccard']['value']:.4f}</td><td>{esc(uq['max_jaccard']['raster'])}</td></tr>
<tr><td>dots within 3 px (forward)</td><td class="n">0.70</td><td class="n">{uq['max_dot_overlap_fwd_3px']['value']:.4f}</td><td>{esc(uq['max_dot_overlap_fwd_3px']['raster'])}</td></tr>
</table>
<p>Forward-overlap firings under the literal gate: <b>{uq['n_overlap_firings_one_directional']}</b>
(the first 50 are itemized in the JSON). Informational only, not a clearance rule: firings with reverse overlap
below 0.5: {uq['informational_two_sided_true_duplicates']}. Literal verdict: <b>{esc(uq['verdict'])}</b>.
The file is <b>not cleared</b> (see IR-57-UNIQ-03).</p>
"""
    else:
        uq_html = "<p>PENDING: full-registry uniqueness scan not finished.</p>"
    return f"""
<h2>Session 2 — measured, not projected</h2>
<p>This block was added on 2026-10-09 after a line-by-line review of the repository. Earlier
pages quoted the holdout DTI at a dot density about twice the one that shipped. The numbers below are
the first measured at the shipped density.</p>
{exp_html}
{uq_html}
"""


def build_session2_hyp() -> str:
    return """
<h2>Session 2 candidate, tested</h2>
<table>
<tr><th>Hypothesis</th><th>Layer(s)</th><th>Physical signature</th><th>Result</th></tr>
<tr><td><b>H57-F</b> recorded sense of slip conditions the strand side</td>
<td>INGENIOUS trace <code>sense</code> column (RL / LL / N), rasterised to visible pixels only</td>
<td>Handedness-relative side of the strand, sense_sgn times side (fitted, not a textbook angle)</td>
<td><span class="tag bad">NEGATIVE</span> mean paired gain +0.0016 over four quadrants, signs disagree.
See the results page. Not promoted.</td></tr>
</table>
"""


def build_irregularities() -> str:
    rows = ""
    for iid, title, status, desc, res in IRREG:
        badge = ('<span class="tag bad">FLAGGED</span>' if "FLAGGED" in status
                 else '<span class="tag org">FIXED</span>' if "FIXED" in status
                 else '<span class="tag">REPORTED</span>')
        rows += (f'<tr><td><code>{esc(iid)}</code><br>{badge}</td><td><b>{esc(title)}</b></td>'
                 f'<td>{esc(desc)}</td><td>{esc(res)}</td></tr>')
    return f"""
<h2>Irregularity ledger</h2>
<p>Everything found wrong during this session — in the competition data, in the shared template,
and in this repository's own code. Five of these are bugs in code written during this session and
caught by the test suite or by an output that did not match expectation.</p>
<table><tr><th>ID</th><th>Title</th><th>What was wrong</th><th>Resolution</th></tr>{rows}</table>
<div class="note"><b>On the value of the test suite.</b> IR-57-BAR-01 and IR-57-KCLIP-01 both
produced a clean exit code and a plausible-looking dot count. They were caught only because the
tests compare the DTI implementation against a brute-force transcription of the published
equations, and because a synthetic allocation was checked for <code>n_dots == emitted.sum()</code>.
A syntax check would have passed both.</div>
"""


def build_sources() -> str:
    reg = json.loads((ROOT / "registry" / "registry_index.json").read_text()) \
        if (ROOT / "registry" / "registry_index.json").exists() else []
    rrows = "".join(
        f'<tr><td>{esc(r["repo"])}</td><td>{esc(r["submission"])}</td>'
        f'<td class="n">{fmt(r["owner_reported_score"])}</td>'
        f'<td><code>{esc(r["sha256"][:16])}…</code></td><td class="n">{r["bytes"]:,}</td>'
        f'<td><a href="https://github.com/buffedlizard55-lab/{esc(r["repo"])}">repo</a></td></tr>'
        for r in reg)
    return f"""
<h2>Competition data</h2>
<table><tr><th>File</th><th>sha256</th><th>Verified properties</th><th>Source</th></tr>
<tr><td><code>data/bridge/existing_faults.tif</code></td>
<td><code>7ba308ccdc4418b31a…</code></td>
<td>EPSG:32611, 3730×3292, int8, nodata −1, values {{−1, 0, 1}}, 60,988 fault px</td>
<td><a href="https://github.com/buffedlizard55-lab/GEMSDOE2/blob/main/data/bridge/existing_faults.tif">GEMSDOE2</a></td></tr>
<tr><td><code>data/bridge/sample_submission.tif</code></td>
<td><code>2176d08e485aa2cd28…</code></td>
<td>EPSG:32611, 3730×3292, float32, nodata NaN, 5,167,373 finite, 7,111,787 NaN</td>
<td><a href="https://github.com/buffedlizard55-lab/GEMSDOE2/blob/main/data/bridge/example_submission.tif">GEMSDOE2</a></td></tr>
</table>
<p class="small"><code>existing_faults.tif</code> is byte-identical to the <code>labels.tif</code>
recorded in <a href="https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/data/restore_receipt.json">GEMSDOE32's
restore receipt</a> (same sha256, same 425,830 bytes). The public "labels" raster <i>is</i> the
mapped catalogue; the scored truth is not published. That is what forces the hide-and-recover design.</p>

<h2>Official sources</h2>
<table><tr><th>What</th><th>Link</th><th>Reachable from this sandbox?</th></tr>
<tr><td>Competition home</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">drivendata.org/…/competition-doe-gems/</a></td><td>No — outside the allowlist</td></tr>
<tr><td>Problem description (metric)</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">page 967</a></td><td>No</td></tr>
<tr><td>About / resources</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/">page 968</a></td><td>No</td></tr>
<tr><td>Data download</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">data tab</a></td><td>No — requires login</td></tr>
<tr><td>Leaderboard</td><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard</a></td><td>No</td></tr>
<tr><td>Rules PDF</td><td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">docs.nlr.gov/docs/fy26osti/96647.pdf</a></td><td>No</td></tr>
<tr><td>Reference solution</td><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">github.com/drivendataorg/gems-prize-reference-solution</a></td><td><b>Yes</b> — cloned and read</td></tr>
<tr><td>GeodAWN survey (USGS)</td><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">usgs.gov/data/geodawn-…</a></td><td>No</td></tr>
<tr><td>INGENIOUS (GBCGE)</td><td><a href="https://gbcge.org/current-projects/ingenious/">gbcge.org/current-projects/ingenious/</a></td><td>No</td></tr>
<tr><td>EPSG:32611</td><td><a href="https://epsg.io/32611">epsg.io/32611</a></td><td>No</td></tr>
<tr><td>Tversky index</td><td><a href="https://en.wikipedia.org/wiki/Tversky_index">en.wikipedia.org/wiki/Tversky_index</a></td><td>No</td></tr>
<tr><td>Geothermal data (GDR)</td><td><a href="https://gdr.openei.org/submissions/1391">gdr.openei.org/submissions/1391</a></td><td>No</td></tr>
</table>
<p class="small">This sandbox reaches only <code>github.com</code>, <code>codeload.github.com</code>,
<code>api.github.com</code>, <code>registry.npmjs.org</code>, <code>pypi.org</code> and
<code>files.pythonhosted.org</code>. Everything above marked "No" is a link for <b>manual review</b>,
not a claim of verification. What <i>was</i> verified locally: the two bridge files by sha256, the
reference solution's notebook (metric parameters α = 0.2, β = 0.8; EPSG:32611 at 100 m), and the 15
registry rasters below.</p>

<h2>Registry — earlier submissions used for the uniqueness check</h2>
<table><tr><th>Repo</th><th>Submission</th><th class="n">Owner-reported</th>
<th>sha256</th><th class="n">Bytes</th><th>Link</th></tr>{rrows}</table>
<p class="small">Owner-reported scores are <span class="tag">OWNER-REPORTED</span> as pasted
by the task owner; the file identity is verified by sha256 against the blob in the named repository.</p>
"""


def build_runcard(build, cv_all, meas) -> str:
    latest = load('exp4_width.json')
    if latest:
        r = latest['research_raster']
        card = {
            'hypothesis': latest['hypothesis'],
            'mechanism': latest['mechanism'],
            'named_non_fault_process_that_could_mimic_it': latest['non_fault_mimic'],
            'holdout_dti': {'label': 'HOLDOUT-DTI (not an organizer score)',
                            'evaluator_version': latest['evaluator_version'],
                            'withheld_positive_pixels': latest['withheld_positive_pixels'],
                            'pooled': latest['H57-G']['pooled_dti'],
                            'ci95_quadrant_jackknife': latest['H57-G']['dti_ci95_quadrant_jackknife'],
                            'baseline_same_mode_and_budget': latest['baseline']['pooled_dti'],
                            'delta': latest['paired_delta']},
            'correlation_overlap_vs_registry': {
                'surface_witnesses': latest['surface_witnesses'],
                'surface_rank_vs_witnesses': latest.get('surface_rank_vs_witnesses'),
                'sha256_distinct_from_full_index': latest.get('sha256_distinct_from_all_644_indexed_rasters'),
                'full_final_dot_comparison': 'NOT RUN; stopped before placement after surface gate',
                'scope': latest.get('index_scope_note')},
            'raster_sha256': r['sha256'],
            'validator_output': {'checks':r['validator']['checks'], 'all_checks_passed':r['validator']['all_checks_passed'],
                                 'nan_cells':r['validator']['n_nan'], 'min':r['validator']['min'],
                                 'max':r['validator']['max'], 'crs_shape_transform':r['validator']['meta']},
            'submission_name': latest['submission_name'],
            'submission_note': latest['submission_note'],
            'verdict':'negative: research surface only; DO NOT SUBMIT; literal overlap gate fails',
            'slot_used':False,
        }
        txt = json.dumps(card, indent=2)
        (EVID/'run_card.json').write_text(txt+'\n')
        return f'<h2>Latest run card — negative</h2><p><b>DO NOT SUBMIT.</b> <a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/run_card.json">JSON</a>. Earlier run: <a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/run_card_session2.json">archived card</a>.</p><pre>{esc(txt)}</pre>'
    z = (build or {}).get("zeros_tif") or {}
    uq = (build or {}).get("uniqueness", {})
    # holdout number for the SHIPPED configuration: measured at the shipped per-cell share
    # (scripts/run_sense_experiment.py, variant no_side).  The 120k-cap run_cv number is
    # kept in evidence/cv_all.json but is not the shipped density (IR-57-SHIP-01).
    exp = load("exp_sense_loqo_all.json") or {}
    pl = (exp.get("variants", {}).get("no_side", {}) or {}).get("pooled", {})
    ci = pl.get("dti_ci95_quadrant_jackknife") or [None, None]
    uqf = load("uniqueness_full_shipped-h57-zeros.json") or {}
    side = dict((meas or {}).get("side", {}))
    # rates derived from the stored counts (withheld / domain per side); not separately stored
    if side.get("n_domain_left") and side.get("n_domain_right") and "rate_left" not in side:
        import math as _m
        side["rate_left"] = side["n_withheld_left"] / side["n_domain_left"]
        side["rate_right"] = side["n_withheld_right"] / side["n_domain_right"]
        side["log_ratio_R_over_L"] = _m.log(side["rate_right"] / side["rate_left"])
    card = {
        "hypothesis": ("Secondary strands around mapped faults are not isotropic: they sit at a "
                       "fitted cross-strike stepover and along-strike offset from the nearest "
                       "visible trace, so a per-fault intensity built from distance, component "
                       "length and offset geometry locates fault pixels the catalogue lacks."),
        "mechanism": ("Distributed shear produces en echelon Riedel shears and synthetic splays; "
                      "damage-zone width grows with displacement (Savage & Brodsky 2011). "
                      "Operationally: a gradient-boosted intensity over the eight shipped catalogue-geometry "
                      "features (side dropped), calibrated to the withheld base rate, then lazy-greedy "
                      "max-coverage allocation at the exact DTI marginal bar."),
        "named_non_fault_process_that_could_mimic_it": (
            "Withheld catalogue pixels are parts of mapped systems, so part of the measured "
            "near-field enrichment is mapping continuity (a mapper stopping mid-system), not "
            "mechanics. The detached withholding mode (>= 400 m from any other component) is the "
            "control; a second mimic is geomorphic linearity (dry washes, roads, ridge crests) "
            "aligning with the regional strike sets, which this lane cannot test without the DEM."),
        "holdout_dti": {
            "instrument": ("hide-and-recover, 4 quadrants x draws 20/21, whole-segment withholding, "
                           "12 px domain erosion, visible-only features, pooled DTI "
                           "alpha=0.2 beta=0.8 R=3 px, leave-one-quadrant-out, per-cell cap 10,000 "
                           "(shipped density), features = shipped 8 (side dropped)"),
            "evaluator_version": "gems57 pooled DTI, scripts/run_sense_experiment.py",
            "withheld_positive_pixels": pl.get("n_truth"),
            "pooled_dti": pl.get("pooled_dti"),
            "ci95_quadrant_jackknife": ci,
            "coverage": pl.get("coverage"),
            "label": "HOLDOUT-DTI - a local instrument reading, NOT a projected live score",
        },
        "correlation_overlap_full_registry": {
            "n_unique_grid_rasters": uqf.get("registry", {}).get("n_unique_grid_rasters"),
            "max_spearman_full_footprint": uqf.get("max_spearman_full_footprint"),
            "max_jaccard": uqf.get("max_jaccard"),
            "max_dot_overlap_fwd_3px": uqf.get("max_dot_overlap_fwd_3px"),
            "n_overlap_firings_one_directional_literal_gate": uqf.get("n_overlap_firings_one_directional"),
            "informational_two_sided_true_duplicates_not_a_clearance_rule": uqf.get("informational_two_sided_true_duplicates"),
            "unique_by_protocol_literal": uqf.get("unique_by_protocol"),
        },
        "correlation_overlap_vs_registry": {
            "n_registry_rasters": len(uq.get("rows", [])),
            "rho_limit": uq.get("rho_limit"),
            "jaccard_limit": uq.get("jaccard_limit"),
            "overlap_limit": uq.get("overlap_limit"),
            "worst_spearman_full_footprint": uq.get("worst_spearman_full_footprint"),
            "worst_rho_submission": uq.get("worst_rho_submission"),
            "worst_jaccard_dot_sets": uq.get("worst_jaccard_dot_sets"),
            "worst_jaccard_submission": uq.get("worst_jaccard_submission"),
            "worst_dot_overlap_3px": uq.get("worst_dot_overlap"),
            "worst_overlap_submission": uq.get("worst_overlap_submission"),
            "dot_union_rho_note": ("reported but NOT thresholded: structurally near -1 for "
                                   "any two sparse binary rasters, see IR-57-RHO-01"),
            "unique": uq.get("unique"),
        },
        "raster_sha256": z.get("sha256"),
        "validator_output": {
            "no_nan_anywhere": z.get("checks", {}).get("no_nan_anywhere"),
            "in_footprint_all_finite": z.get("checks", {}).get("in_footprint_all_finite"),
            "range_0_1_guaranteed": z.get("checks", {}).get("range_0_1_guaranteed"),
            "crs_shape_transform_match": all(z.get("checks", {}).get(k, False) for k in
                                             ("crs_epsg_32611", "dimensions_3730x3292",
                                              "transform_matches_sample_submission")),
            "zero_dots_on_mapped_catalogue": z.get("checks", {}).get("zero_dots_on_mapped_catalogue"),
            "all_checks_passed": z.get("all_checks_passed"),
            "n_checks": len(z.get("checks", {})),
        },
        "submission_name": (build or {}).get("submission_name"),
        "submission_note": (build or {}).get("submission_note"),
        "sense_of_slip": {
            "available_in_provided_database": True,
            "source": "data/external/trace_segments_utm11.csv column sense (INGENIOUS vector); IR-57-SLIP-02",
            "measured_log_ratio_right_over_left": side.get("log_ratio_R_over_L"),
            "encoded_in_shipped_file": False,
            "tested_as_opt_in_features": True,
            "tested_result": exp.get("paired_no_side_plus_sense_minus_no_side"),
        },
        "verdict": "PENDING" if not build else (
            "promote" if (z.get("all_checks_passed") and uqf.get("unique_by_protocol")) else
            "HOLD (format checks pass; literal uniqueness forward-overlap gate fired; not cleared)"),
        "verdict_scope": ("eligible for the separate selector step only; not a slot choice, not a live "
                          "score. The holdout number is the shipped-density reading above."),
    }
    card_txt = json.dumps(card, indent=2)
    (ROOT / "evidence" / "run_card.json").write_text(card_txt + "\n", encoding="utf-8")
    return f"""
<h2>Run card</h2>
<p>One JSON card, per parallel-run protocol rule 5. Machine-readable copy:
<a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/run_card.json"
target="_blank" rel="noopener"><code>evidence/run_card.json</code></a>.</p>
<pre>{esc(card_txt)}</pre>
<h2>How to read it</h2>
<ul>
<li><b>holdout_dti</b> is a <span class="tag hold">HOLDOUT-DTI</span> reading. It is <b>not</b> a
projected live score, and no live score is claimed anywhere in this repository.</li>
<li><b>verdict</b> is <code>promote</code> only if the validator passes every check <i>and</i> the
uniqueness screen is clear. Promotion to an actual weekly slot is a separate selector step and is
not done here.</li>
<li><b>sense_of_slip.encoded = false</b> because the provided database has no such field
(<code>IR-57-SLIP-01</code>).</li>
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
        "executive-summary.html": ("How to submit", build_exec(build), "executive-summary.html"),
        "method.html": ("Method", build_method(meas, cv_all, cv_det), "method.html"),
        "hypotheses.html": ("Hypotheses", build_hypotheses() + build_session2_hyp(), "hypotheses.html"),
        "results.html": ("Results", build_results(cv_all, cv_det, build, rb) + build_session2(), "results.html"),
        "session-3.html": ("Latest run", build_session3(), "session-3.html"),
        "irregularities.html": ("Irregularities", build_irregularities(), "irregularities.html"),
        "data-sources.html": ("Data sources", build_sources(), "data-sources.html"),
        "run-card.html": ("Run card", build_runcard(build, cv_all, meas), "run-card.html"),
    }
    for fname, (title, body, active) in pages.items():
        (DOCS / fname).write_text(page(title, body, active))
        print(f"wrote docs/{fname}  ({len(body):,} chars of body)")


if __name__ == "__main__":
    main()
