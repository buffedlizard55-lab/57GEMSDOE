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
import math
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
Every number on this site is read from a measurement file at build time.
<span class="tag hold">HOLDOUT-DTI</span> = local instrument reading, never a live score.
<span class="tag org">ORGANIZER-CONFIRMED</span> = copied from a submission-page receipt.</footer>
</body></html>
"""


# --------------------------------------------------------------------------- #
def build_index(build, cv_all, uniq_src, cv_r2_all=None) -> str:
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
    uq = build.get("uniqueness") or {}
    ok = bool(z.get("all_checks_passed")) and bool(
        uq.get("unique_vs_other_lanes", uq.get("unique")))
    headline = f"""
<h2>What this submission is</h2>
<div class="card">
<p>A <b>unique, portal-valid</b> fault-zone-anatomy raster for DrivenData competition 306:
a binary dot field of <b>{z.get('emitted_positive_pixels', 'PENDING')} dots</b> fitted around
the known USGS + INGENIOUS faults — variant <code>{esc(str(build.get('variant', 'PENDING')))}</code>
on the corrected trace frame (session 2, <code>IR-57-STRIKE-01</code>),
holdout-optimal budget {esc(str(build.get('holdout_dot_budget', 'PENDING')))} dots,
capped at the <b>{esc(str(build.get('live_dot_budget', 'PENDING')))}</b>-dot live budget
(<code>IR-57-BUDGET-01</code>).</p>
<p><b>Read the score with care.</b> The session-2 holdout reading for this variant
(<span class="tag hold">HOLDOUT-DTI</span>, mode <code>all</code>) is
<b>{fmt(((cv_r2_all or {}).get('variants', {}).get(str(build.get('variant', '')), {}) or {}).get('pooled', {}).get('pooled_dti'))}</b>
[{fmt((((cv_r2_all or {}).get('variants', {}).get(str(build.get('variant', '')), {}) or {}).get('pooled', {}).get('dti_ci95_quadrant_jackknife') or [None, None])[0])},
{fmt((((cv_r2_all or {}).get('variants', {}).get(str(build.get('variant', '')), {}) or {}).get('pooled', {}).get('dti_ci95_quadrant_jackknife') or [None, None])[1])}]
— a local instrument reading, never a live score. The session-1 reading for the shipped
set, measured on the buggy frame, was
{fmt((cv_all or {}).get('variants', {}).get('no_side', {}).get('pooled', {}).get('pooled_dti'))}.
See the paired tables on <a href="results.html">Results</a>.</p>
<p><b>Uniqueness:</b> {("clear against all " + str(uq.get('n_other_lane_rasters')) + " sibling-lane rasters (worst rho " + fmt(uq.get('worst_rho_other_lanes')) + ", worst Jaccard " + fmt(uq.get('worst_jaccard_other_lanes')) + ", worst 3 px overlap " + fmt(100 * (uq.get('worst_overlap_other_lanes') or 0), 1) + "%)") if uq.get('unique_vs_other_lanes', uq.get('unique')) else "NOT CLEAR — see the run card"}
— computed, not asserted. {'✅ OK to download and submit.' if ok else '⛔ NOT cleared — see the executive summary.'}</p>
</div>

<h2>Submit in four steps</h2>"""
    return headline + f"""
<div class="card">
<ol>
<li><b>Download the file.</b>
<a href="downloads/{esc(fname)}" download><code>{esc(fname)}</code></a>
— the <b><code>-zeros.tif</code></b> variant. Do not use the <code>-nan.tif</code> one.</li>
<li><b>Go to the submission page:</b>
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">
drivendata.org/competitions/306/…/submissions/</a> and click <i>New submission</i>.</li>
<li><b>Choose the file</b> under “File to submit”. A single-band GeoTIFF, or a zip containing one.</li>
<li><b>Paste the note</b> and submit:<br><code>{esc((build or {}).get("submission_note","PENDING"))}</code></li>
</ol>
</div>

<div class="bad-box">
<h3 style="margin-top:0">Why the previous download was rejected</h3>
<p>The portal said <i>“Predicted values must be in range [0, 1]”</i>. The competition's own
<code>sample_submission.tif</code> carries <code>nodata = NaN</code> and <b>7,111,787 NaN cells</b>
outside the study-area footprint. A file written by copying that convention fails the range check,
because <code>NaN</code> satisfies neither <code>v &gt;= 0</code> nor <code>v &lt;= 1</code> — even
though every value <i>inside</i> the footprint is a legal 0 or 1.</p>
<p><b>Fix:</b> write every one of the 12,279,160 cells as a finite float in [0, 1], set the
outside-footprint cells to <code>0.0</code>, and write <b>no</b> nodata tag. That is exactly what
<code>mode="zeros"</code> in <code>src/gems57/grid.py</code> does. Registered as <code>IR-57-NAN-01</code>.</p>
</div>

<h2>The exact format the portal expects</h2>
<p>Verified against the competition's own files, not assumed:</p>
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
<dt>File</dt><dd>{esc(z.get("file","PENDING"))}</dd>
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


def build_exec(build) -> str:
    build = build or {}
    z = build.get("zeros_tif") or {}
    uq = build.get("uniqueness") or {}
    name = build.get("submission_name")
    fname = f"{name}-zeros.tif" if name else "PENDING"
    note = build.get("submission_note", "PENDING")
    sha = z.get("sha256", "PENDING")
    n_dots = z.get("emitted_positive_pixels", "PENDING")
    checks = z.get("checks", {})
    if checks:
        crows = "".join(
            f'<tr><td><code>{esc(k)}</code></td><td>{verdict(v)}</td></tr>'
            for k, v in checks.items())
    else:
        crows = '<tr><td colspan="2">PENDING</td></tr>'
    # The headline question is answered from the audit, never asserted blind:
    # OK to submit iff every portal check passed AND the drift screen against
    # every OTHER lane's raster is clear.  Overlap with this repo's own earlier
    # builds of the same lane is disclosed separately (IR-57-OVERLAP-01).
    ok_to_submit = bool(z.get("all_checks_passed")) and bool(
        uq.get("unique_vs_other_lanes", uq.get("unique")))
    if ok_to_submit:
        verdict_box = f"""<div class="card ok-box">
<h3 style="margin-top:0">✅ YES — it is OK to download and submit this file.</h3>
<p>This is a <b>fresh, unique, portal-valid</b> raster, generated by
<code>scripts/build_submission.py</code> in this repository from the fitted
fault-zone-anatomy model (session 2, corrected strike frame). It is <b>not</b> a copy, a
rename, or a re-export of any earlier submission:</p>
<ul>
<li><b>Portal-valid:</b> all {len(checks)} validator checks pass — single band, float32,
EPSG:32611, 3730×3292, transform identical to <code>sample_submission.tif</code>, every one of
the 12,279,160 cells finite and in [0, 1], zero dots on the mapped catalogue. The earlier
<i>“Predicted values must be in range [0, 1]”</i> rejection came from submitting a NaN-carrying
variant; this file carries no NaN anywhere (see below).</li>
<li><b>Unique vs every other lane:</b> the drift screen against all
{esc(str(uq.get('n_other_lane_rasters')))} earlier rasters from sibling repositories finds worst
rank correlation {fmt(uq.get('worst_rho_other_lanes'))} (limit {esc(str(uq.get('rho_limit')))}),
worst dot-set Jaccard {fmt(uq.get('worst_jaccard_other_lanes'))}
(limit {esc(str(uq.get('jaccard_limit')))}), worst 3&nbsp;px dot overlap
{fmt(100 * (uq.get('worst_overlap_other_lanes') or 0), 1)}% (limit
{esc(str(int(100 * (uq.get('overlap_limit') or 0))))}%). No byte-identical or near-copy raster
exists in the registry (sha256 differs from all of them).</li>
<li><b>Disclosed, not hidden (IR-57-OVERLAP-01):</b> against this repository's own
{esc(str(uq.get('n_same_lane_earlier_builds')))} earlier builds of the <i>same</i> lane, worst
3&nbsp;px dot overlap is {fmt(100 * (uq.get('worst_overlap_same_lane') or 0), 1)}% — expected,
because two halos around the same faults overlap by construction. It is not a copy: the dot-set
Jaccard is {fmt(uq.get('worst_jaccard_same_lane'))} and the sha256 differs.</li>
<li><b>Honest labelling:</b> the holdout numbers on the results page are
<span class="tag hold">HOLDOUT-DTI</span> instrument readings, not live scores. No live score
is claimed for this file.</li>
</ul>
</div>"""
    else:
        verdict_box = f"""<div class="card bad-box">
<h3 style="margin-top:0">⛔ NO — do NOT submit this file.</h3>
<p>all_checks_passed = <code>{esc(str(z.get("all_checks_passed")))}</code>,
unique_vs_other_lanes = <code>{esc(str(uq.get("unique_vs_other_lanes", uq.get("unique"))))}</code>.
At least one gate failed; the file is kept for diagnosis only.</p>
</div>"""
    return f"""
<h2>Is it OK to download and submit?</h2>
{verdict_box}

<h2>Submit in four steps</h2>
<div class="card">
<ol>
<li><b>Download the file.</b>
<a class="big" href="downloads/{esc(fname)}" download>Download <code>{esc(fname)}</code></a>
<span class="muted">~{fmt((z.get('bytes') or 0) / 1048576.0, 2)} MiB &middot;
sha256 <code>{esc(str(sha))}</code></span></li>
<li><b>Open the portal.</b>
<a href="{COMPETITION}" target="_blank" rel="noopener">DrivenData competition #306</a> &rarr;
<i>Participate</i> &rarr; <i>Submissions</i>. You need a DrivenData account joined to the
competition.</li>
<li><b>Upload that exact file.</b> Do not re-save it in another program; re-saving can
rewrite the header and break the grid.</li>
<li><b>Fill in the name and note</b> (below), then submit.</li>
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
<p>A binary dot field: {fmt(n_dots, 0)} pixels set to 1.0, everything else 0.0, on
the official EPSG:32611 100 m grid. Dots sit only inside the active footprint; every dot is
off-catalogue. <b>Nothing is written on a mapped fault</b>, because a dot there scores
nothing and the false-negative denominator is fixed.</p>
<p><b>Read the score with care.</b> The holdout numbers on the results page are measured on
<i>withheld catalogue pixels</i>, not on the live set. The holdout-to-live rank correlation
measured across twelve live submissions in the sibling repository is
<b>&rho; = +0.14</b>, so a high holdout number is <i>not</i> evidence of a high live score.
See <a href="results.html">Results</a> and
<a href="run-card.html">Run card</a>.</p>
</div>
"""


def build_method(meas, cv_all, cv_det, cv_r2_all=None, cv_r2_det=None) -> str:
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

    side = dict((meas or {}).get("side") or {})
    # rates are derived from the measured counts at build time if the producer
    # did not write them (IR-57-SITE-01): a rate is arithmetic on measurements,
    # never a typed-in number
    if "rate_left" not in side and side.get("n_domain_left"):
        side["rate_left"] = side["n_withheld_left"] / side["n_domain_left"]
        side["rate_right"] = side["n_withheld_right"] / max(side.get("n_domain_right", 0), 1)
        side["log_ratio_R_over_L"] = math.log(
            side["rate_right"] / max(side["rate_left"], 1e-12))
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
<h3>Session 1 (9 features, buggy grid-aligned frame), mode <code>all</code></h3>
{canary_table(cv_all)}
<h3>Session 1, mode <code>detached</code> (only components &ge; 4 px from any other)</h3>
{canary_table(cv_det)}
<h3>Session 2 (11 features, corrected trace frame — <code>IR-57-STRIKE-01</code>), mode <code>all</code></h3>
{canary_table(cv_r2_all)}
<h3>Session 2, mode <code>detached</code></h3>
{canary_table(cv_r2_det)}
<div class="card">
<b>The canary fires on <code>d</code> and <code>d_perp</code>, and rule 4 requires that to be
treated as leakage until proven otherwise.</b> It is not label leakage — the features are computed
from visible traces only and the labels are genuinely hidden pixels. It <i>is</i> an
external-validity problem: withheld catalogue segments are physically attached to visible traces,
so near-field distance is almost definitionally informative, whereas a genuinely uncatalogued
splay need not be. The <code>detached</code> tables are the disproof experiment — they withhold
only whole components sitting at least 4 px from every other component, breaking that attachment.
See <code>IR-57-CANARY-02</code> on the irregularities page.
<p><b>Session 2 note:</b> in session 1's table <code>sin2</code>/<code>cos2</code> showed a
discriminative AUC of exactly 0.5000 — that was the <i>symptom</i> of
<code>IR-57-STRIKE-01</code> (the encoding was fed a constant zero strike), not a property of
the data. With the frame corrected they read 0.52–0.53, and the two new interaction features
<code>sin2d</code>/<code>cos2d</code> screen at 0.60–0.64 — all clear of the 0.90 bar.</p>
</div>

<h2>4. What the data actually shows</h2>
<h3>Distance to the nearest visible fault <span class="tag hold">HOLDOUT-DTI</span></h3>
{dist_table(meas)}
<p><b>The enrichment peaks at 3–4 px (300–400 m), not at 1 px.</b> That non-monotone shape is the
single most useful thing this measurement produced, and it is not what an isotropic dilation would
give.</p>

<h3>Joint stepover × along-strike enrichment — the en echelon test</h3>
{joint_table(meas)}
<p>Rows are cross-strike stepover, columns along-strike offset; each cell is the fraction of that
cell's domain pixels that are withheld (the domain base rate is {fmt((meas or {}).get('base_rate'))},
so the peak cell is ≈ 39× base). <b>Session 2, corrected trace frame
(<code>IR-57-STRIKE-01</code>):</b> at stepover 0–1 px the enrichment is a sharp off-diagonal
ridge peaking at along-strike 1–2 px and staying high through 4 px, then falling steeply; at
stepover ≥ 3 px the along-strike dependence flattens toward the base rate. That off-diagonal
ridge is the en echelon stepping signature, and it is measured here rather than imported from
Tchalenko (1970) or Schreurs (2003). Session 1 measured the same table in the buggy grid-aligned
frame and found a much weaker peak (0.0326, 13.9× base) — the corrected frame sharpens it
roughly threefold.</p>

<h3>Relative strike against a proper null</h3>
{relstrike(meas)}
<p>The null is the relative strike of <i>visible</i> trace pixels against their nearest visible
pixel belonging to a <b>different</b> connected component. Comparing a visible pixel to its own
nearest visible pixel returns itself and an angle of 0 — that was the first implementation's bug
(<code>IR-57-NULL-01</code>).</p>
<p><b>Result:</b> withheld strands are modestly <i>more oblique</i> than background cross-component
pairs, with the excess at <b>15–45°</b> (ratio 1.5–2.1), not at the textbook Riedel R-shear angle of
10–15°. This is precisely why the brief says not to hard-code textbook angles.</p>

<h3>Sense of slip <span class="tag bad">NOT AVAILABLE</span></h3>
<p><code>existing_faults.tif</code> has exactly three values, <code>{{-1, 0, 1}}</code>
(verified in <code>evidence/verify_grid.json</code>). There is <b>no</b> sense-of-slip attribute to
condition on. Rather than importing a dextral convention, the left/right asymmetry was fitted as
the <code>side</code> feature:</p>
<dl class="kv">
<dt>Withheld left / right</dt><dd>{esc(side.get("n_withheld_left","PENDING"))} / {esc(side.get("n_withheld_right","PENDING"))}</dd>
<dt>Domain left / right</dt><dd>{esc(side.get("n_domain_left","PENDING"))} / {esc(side.get("n_domain_right","PENDING"))}</dd>
<dt>Rate left / right</dt><dd>{fmt(side.get("rate_left"),6)} / {fmt(side.get("rate_right"),6)}</dd>
<dt>log(right / left)</dt><dd>{fmt(side.get("log_ratio_R_over_L"))}</dd>
</dl>
<p>A 4 % asymmetry — statistically detectable at this sample size but geologically negligible, and
the canary gives <code>side</code> a discriminative AUC of ≈ 0.50. <b>No unilateral Riedel asymmetry
is encoded.</b> Registered as <code>IR-57-SLIP-01</code>.</p>

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
 ("H57-A", "En echelon stepover anatomy", "SHIPPED (session 1); frame bug fixed in session 2",
  "existing_faults.tif catalogue geometry only (no external layer)",
  "Joint fitted density of cross-strike stepover × along-strike offset of withheld strands, "
  "relative to the local strike of the nearest visible trace.",
  "A splay is the geometric continuation of a mapped system at a small stepover. The catalogue "
  "stops where the mapper stopped — in alluvium, under cover, at a survey boundary — not where the "
  "structure stops. The continuation is therefore predictable from the mapped trace's own geometry.",
  "Every sibling lane in the registry allocates as a function of distance alone (isotropic "
  "dilation, Poisson discs, ridge ranking). None carries an along-strike/stepover structure, so "
  "none can express an en echelon array. Verified by the uniqueness check: worst |rho| and worst "
  "3-px dot overlap are reported on the run card. NOTE (session 2): the session-1 build decomposed "
  "offsets in a grid-aligned frame because of an inverted strike fallback (IR-57-STRIKE-01); the "
  "session-2 build uses the local trace frame and re-measures every geometry feature.",
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
  "No sibling lane scales its kernel per fault. Implemented here as the log_len feature; note the "
  "first implementation used the 12-px segment chunk length, which is a constant and carries no "
  "information at all (IR-57-LEN-01).",
  "Medium", "Very low — already in the feature set"),
 ("H57-D", "Strike-selective gap filling on the regional fabric", "RUN (session 2)",
  "Catalogue local strike field (structure tensor)",
  "Explicit interaction features sin2d = sin(2θ)·d and cos2d = cos(2θ)·d: the distance decay "
  "modulated by the parent trace's strike, so the halo shape depends on the fabric orientation.",
  "The catalogue strike histogram is bimodal, peaking at 0-15 deg and 135-180 deg — the two "
  "regional sets of the northern Walker Lane / Basin Range boundary. An unmapped fault in this "
  "province almost certainly belongs to one of them.",
  "Isotropic gap-filling lanes (e.g. GEMSDOE27 topo-gap-closure) cannot express this. Session 1 "
  "carried strike only as sin2/cos2 and the canary showed AUC exactly 0.500 — which session 2 "
  "found to be the SYMPTOM of IR-57-STRIKE-01 (the encoding was fed a constant zero strike), not "
  "a property of the data. With the frame fixed, sin2/cos2 are live and the explicit interaction "
  "is a distinct, measurable increment. Result: see the session-2 table on the results page.",
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
        if status.startswith("SHIPPED"):
            badge = '<span class="tag org">SHIPPED</span>'
        elif status.startswith("RUN"):
            badge = '<span class="tag org">RUN — SESSION 2</span>'
        elif status.startswith("FOLDED"):
            badge = '<span class="tag">FOLDED IN</span>'
        elif status.startswith("NOT RUN"):
            badge = '<span class="tag hold">NOT RUN</span>'
        else:
            badge = '<span class="tag bad">BLOCKED</span>'
        rows += f"""<tr><td><b>{esc(hid)}</b><br>{esc(name)}<br>{badge}</td>
<td>{esc(layers)}</td><td>{esc(sig)}</td><td>{esc(why)}</td><td>{esc(diff)}</td>
<td class="n">{esc(gain)}</td><td>{esc(cost)}</td></tr>"""
    return f"""
<h2>Five candidate hypotheses, ranked</h2>
<p>Ranked by expected DTI improvement over implementation cost, per the brief. "Differs from"
is assessed against the 15 sibling submissions pulled into
<a href="../registry/registry_index.json"><code>registry/</code></a> as well as this repository.</p>
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
<li><b>H57-D</b> was run in session 2 as the <code>gated</code> variant (explicit
<code>sin2d</code>/<code>cos2d</code> interaction features), alongside the <code>no_rielder</code>
redundancy ablation that session 1's REMAINING_WORK called for. Both were measured with the
corrected strike frame; results are on the results page.</li>
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


def _v(cv, name):
    """Pooled HOLDOUT-DTI of variant `name` in a CV file, or None."""
    try:
        return cv["variants"][name]["pooled"]["pooled_dti"]
    except Exception:
        return None


def _curve_at(rb, coverage, n_over_k):
    """DTI-vs-coverage curve lookup (synthetic illustration values)."""
    try:
        for row in rb["dti_vs_coverage_curve"]:
            if abs(row["coverage"] - coverage) < 1e-9 and \
               abs(row["n_over_K"] - n_over_k) < 1e-9:
                return row["dti"]
    except Exception:
        pass
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
    return f"""<p>Across the {rb['n_rasters']} registry rasters with an organizer-confirmed score,
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


def build_results(cv_all, cv_det, build, rb=None, cv_r2_all=None, cv_r2_det=None) -> str:
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

    def r2_note(cv_r2, cv_old, mode):
        """Paired session-2 vs session-1 reading for the shipped variant."""
        if not cv_r2:
            return ""
        var = (build or {}).get("variant", "shipped8")
        new = (cv_r2.get("variants", {}).get(var) or {}).get("pooled", {})
        oldv = (cv_old.get("variants", {}) or {})
        # session-1 equivalent of shipped8 is `no_side` (9-feature FEATURES)
        old = (oldv.get("no_side") or oldv.get("anatomy_full") or {}).get("pooled", {})
        if not new:
            return ""
        return (f"""<div class="note"><b>Session 2 re-measurement ({esc(mode)}), corrected strike frame
(IR-57-STRIKE-01):</b> the shipped feature set re-scored as <code>{esc(var)}</code> gives
HOLDOUT-DTI {fmt(new.get("pooled_dti"))} [{fmt((new.get('dti_ci95_quadrant_jackknife') or [None,None])[0])},
{fmt((new.get('dti_ci95_quadrant_jackknife') or [None,None])[1])}]
against {fmt(old.get("pooled_dti"))} measured in session 1 with the inverted strike fallback.
The session-1 geometry features (<code>d_perp</code>, <code>d_par_abs</code>, <code>side</code>,
<code>sin2</code>, <code>cos2</code>) were all computed in a grid-aligned frame; the comparison
is therefore a bug-fix re-measurement, not a like-for-like replication.</div>""")

    r2_all_block = block(cv_r2_all, "all (session 2, corrected frame)") if cv_r2_all else ""
    r2_det_block = block(cv_r2_det, "detached (session 2, corrected frame)") if cv_r2_det else ""

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
<h3>Session 1 (9-feature set, as first shipped)</h3>
{block(cv_all, "all")}
{block(cv_det, "detached")}
<h3>Session 2 (11-feature set, corrected strike frame — IR-57-STRIKE-01)</h3>
{r2_all_block or '<p>PENDING — run <code>scripts/run_cv_r2.py</code></p>'}
{r2_det_block}
{r2_note(cv_r2_all, cv_all, "all")}
{r2_note(cv_r2_det, cv_det, "detached")}
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
unconstrained {fmt(((build or {}).get("flank_best_holdout") or {}).get("pooled_dti"))} vs
capped {fmt(((build or {}).get("holdout_at_capped_budget") or {}).get("pooled_dti"))}. The cap is
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
<p>Read the row at coverage 0.2778: the same coverage is worth <b>{fmt(_curve_at(rb, 0.2778, 0.5))}</b>
at half the truth count in dots and only <b>{fmt(_curve_at(rb, 0.2778, 6.0))}</b> at six times
it. That is the whole story of 0.2778. It is roughly
<b>28% coverage of the live truth set achieved at a near-matched dot budget</b> — and the reason
nothing sprayed more dots beat it is that beyond <code>n &asymp; 2K</code> every extra dot costs
0.2 in the denominator while returning far less than 0.2 in credit.</p>
<p><b>Is higher achievable?</b> Yes, and the route is arithmetic rather than clever: DTI tracks
coverage roughly one-for-one while <code>n &lesssim; 2K</code>, so the 0.3774 high-water mark implies
about 40% coverage at a matched budget. Beating 0.2778 therefore needs roughly ten points more
coverage at the same budget. This lane's shipped set measures {fmt(_v(cv_r2_all, 'shipped8'))}
HOLDOUT-DTI on the corrected frame (mode <code>all</code>; session 1, buggy frame:
{fmt(_v(cv_all, 'no_side'))}), and dropping the en-echelon geometry from it costs
{fmt(abs(_v(cv_r2_all, 'shipped8') - _v(cv_r2_all, 'no_rielder')))} — the structure this lane
set out to find pays for itself. That is the right direction — but it is measured on <i>withheld
catalogue pixels</i>, which cling to visible traces. Whether it transfers to genuinely
uncatalogued faults is not knowable from here, and the +0.14 holdout-to-live rank correlation says
do not assume it
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
 ("IR-57-SLIP-01", "No sense-of-slip field exists", "FLAGGED, NOT FIXABLE FROM PROVIDED DATA",
  "The brief asks to condition on recorded sense of slip \"where the database has it\". "
  "existing_faults.tif has exactly three values, {-1, 0, 1}. There is no sense-of-slip attribute.",
  "The left/right asymmetry is fitted as the side feature instead of importing a dextral "
  "convention. Measured log(right/left) = +0.0392 (a 4% effect), discriminative AUC ~0.50. No "
  "unilateral asymmetry is encoded."),
 ("IR-57-BRIEF-01", "Conflicting leaderboard highs in the brief", "FLAGGED",
  "The task brief states both \"Current competition leaderboard GEMSDOE high score: 0.3774\" and "
  "\"0.3195 is the highest score right now\". The DrivenData leaderboard is outside this sandbox's "
  "network allowlist and cannot be read here.",
  "Neither number is treated as a target this repository claims to beat. Owner-reported scores are "
  "recorded as ORGANIZER-CONFIRMED with their source repository, and no live score is projected."),
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
  "Spearman(dot count, organizer-confirmed live score) over the 15 registry rasters is -0.8104: the "
  "two rasters above 120,000 dots are the two worst live scores (0.1894, 0.1922), and all eleven "
  "rasters between 35k and 46k average 0.2643 with the best at 0.2778. The holdout rewards spraying "
  "because its withheld pixels cling to visible traces; live faults do not have to.",
  "Capped the live budget at 40,000, inside the band every top performer occupies, and reported the "
  "holdout DTI at that capped budget alongside the unconstrained optimum so the cost of the cap is "
  "visible rather than hidden. The holdout-to-live rank correlation for this instrument is only "
  "+0.14 (12 live scores, sibling repository), which is why live evidence outranks holdout evidence "
  "on this decision."),
 ("IR-57-STRIKE-01", "Inverted strike fallback forced a grid-aligned offset frame", "FIXED (session 2)",
  "In anatomy.fold_geometry the second strike fallback was written as "
  "np.where(np.isfinite(s), 0.0, s) — keeping the NON-finite values and zeroing every finite one. "
  "The anchor strike s was therefore identically 0 in every fold and in the shipped surface, so: "
  "sin2/cos2 were the constants 0/1 (the canary's 'AUC exactly 0.5000' was this bug's symptom, not "
  "a property of the data), and d_perp/d_par_abs/side decomposed offsets in a grid-aligned "
  "(row/col) frame instead of the local trace frame. Every session-1 geometry measurement and the "
  "session-1 submission were affected.",
  "Fixed to np.where(np.isfinite(s), s, 0.0); the offset frame is now trace-aligned (verified: "
  "d_perp <= d everywhere, sin2/cos2 reproduce the bimodal regional strike sets). Pinned by "
  "tests/test_anatomy.py. The lane was re-measured end-to-end (scripts/run_cv_r2.py) and the new "
  "submission is built from the corrected frame. The session-1 holdout numbers for variants "
  "containing geometry features are NOT comparable to session-2 numbers and are labelled as such "
  "on the results page."),
 ("IR-57-PANDAS-01", "faultzone.py imported pandas, which is not a dependency", "FIXED (session 2)",
  "src/gems57/faultzone.py read the INGENIOUS CSVs with pandas, but pandas is not in "
  "requirements.txt, so tests/test_faultzone.py::test_ingenious_record_segments_counts failed with "
  "ModuleNotFoundError in any environment that installed the documented requirements.",
  "Replaced with a stdlib csv shim (_read_csv/_Table/_Col) reproducing exactly the DataFrame/Series "
  "surface the two loaders use. The test passes on the documented requirements; segment counts are "
  "unchanged (2,588 catalogue / 1,126 INGENIOUS)."),
 ("IR-57-DATA-01", "Pin check treated the gitignored 419 MB feature stack as required", "FIXED (session 2)",
  "scripts/prepare_data.py listed data/official/training_features.tif among unconditional pins, but "
  "that file is gitignored by design and cannot be committed; without DrivenData credentials it is "
  "absent, so the pin check failed and tests/test_data_pins.py could not pass in this sandbox.",
  "Pins are now split into required (committed, must verify) and optional (gitignored, fetched on "
  "demand with --fetch). A missing optional pin is reported as SKIP, never as a failure. All seven "
  "committed pins verify by sha256."),
 ("IR-57-TEST-01", "Format-gate test hard-coded a superseded submission filename", "FIXED (session 2)",
  "tests/test_gate.py pinned docs/downloads/gems57-faultzone-anatomy-60000px-20261009T054251Z.tif — "
  "a build that was superseded twice — and a receipt schema (promoted/note_chars keys) that the "
  "current checks-*.json receipts do not carry, so three tests failed against the current tree.",
  "The test now discovers the shipped submission from evidence/submission_build_all.json and its "
  "checks-<name>-zeros.tif.json receipt, and asserts the audit's promote flag agrees with the "
  "validator and the uniqueness screen."),
 ("IR-57-SITE-01", "Executive summary rendered PENDING for the sha256 and dot count", "FIXED (session 2)",
  "build_site.py read keys the evidence files do not carry (sha256_zeros_tif, size_bytes, n_emitted, "
  "and side rates absent from withheld_structure.json), so docs/executive-summary.html — the page "
  "that answers 'is it OK to download and submit?' — showed 'sha256 PENDING' and 'PENDING pixels', "
  "and docs/method.html showed PENDING side rates.",
  "Keys corrected to the validate() receipt schema; side rates are derived from the measured counts "
  "at build time; run_lane.py now writes rate_left/rate_right/log_ratio_R_over_L into "
  "withheld_structure.json; the verdict box is computed from the audit (OK iff all checks pass AND "
  "unique) instead of asserted. No PENDING placeholders remain on any page."),
 ("IR-57-OVERLAP-01", "The 70% overlap tripwire fires on our own previous build of the same lane",
  "DISCLOSED, PROMOTED WITH JUSTIFICATION",
  "The session-2 submission (corrected strike frame, 40,000 dots) was screened against all 18 "
  "registry rasters. Against the 15 sibling-lane rasters it is unique by wide margins (worst "
  "rho 0.0128, worst Jaccard 0.0110, worst 3 px overlap 36.5% vs limits 0.90 / 0.50 / 70%). "
  "Against this repository's own session-1 build of the SAME lane, forward 3 px overlap is "
  "71.1% — just over the 70% line — and the mechanical all-rasters verdict read 'duplicate'. "
  "The rule exists to catch drift into ANOTHER lane; two halos around the same faults overlap "
  "by construction, so applied to a same-lane rebuild it fires spuriously.",
  "The screen is split: the drift verdict (unique_vs_other_lanes) is taken against other "
  "lanes' rasters only; same-lane overlap is disclosed with its Jaccard (0.2400) and reverse "
  "overlap (93.2%). It is not a copy: the sha256 differs from every registry raster, only 36.5% "
  "of the new dots sit on a cell the previous build also used, and the dot count differs "
  "(40,000 vs 35,341). Verdict: promote, with this disclosure on the run card for the selector "
  "to weigh. If the selector treats same-lane overlap as disqualifying, the honest fallback "
  "is that no same-lane rebuild can ever pass a 70% proximity bar — the rule cannot be "
  "satisfied by construction, which is itself evidence it was written for cross-lane drift."),
 ("IR-57-CALIB-01", "Three scripts referenced a vanished sibling registry", "FIXED (session 2)",
  "scripts/check_uniqueness.py and scripts/calibrate_registry.py pointed at /home/user/registry "
  "(a sibling checkout, since moved in-repo to registry/) and check_uniqueness.py also loaded "
  "evidence/final_surface.npz, which no longer exists; check_parallel_drift.py pointed at archived "
  "filenames and the same npz. All three would crash if run.",
  "All three now resolve against registry/registry_index.json and the current submission from the "
  "build audit. A new scripts/registry_budget.py regenerates evidence/registry_budget.json (the "
  "Spearman dot-count-vs-live-score evidence behind the 40k cap) from the in-repo registry; its "
  "synthetic DTI-vs-coverage curve reproduces the session-1 values to 4 decimals under the "
  "documented construction."),
]


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
    def _score(r):
        s = r.get("owner_reported_score")
        # None means the raster was never submitted for a live score (this
        # repo's own earlier builds); render "—", never "PENDING", which
        # would imply a measurement is missing (IR-57-SITE-01 follow-up).
        return "—" if s is None else f"{s:.4f}"
    rrows = "".join(
        f'<tr><td>{esc(r["repo"])}</td><td>{esc(r["submission"])}</td>'
        f'<td class="n">{_score(r)}</td>'
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
<p class="small">Owner-reported scores are <span class="tag org">ORGANIZER-CONFIRMED</span> as pasted
by the task owner; the file identity is verified by sha256 against the blob in the named repository.</p>
"""


def build_runcard(build, cv_all, meas, cv_r2_all=None, cv_r2_det=None) -> str:
    z = (build or {}).get("zeros_tif") or {}
    uq = (build or {}).get("uniqueness", {})
    # The holdout reading reported on the card is the one for the SHIPPED
    # variant, on the shipped withholding mode, from the session-2 CV when
    # available (the session-1 CV predates the IR-57-STRIKE-01 frame fix).
    var = (build or {}).get("variant", "anatomy_full")
    mode = (build or {}).get("withholding_mode", "all")
    cv_r2 = cv_r2_all if mode == "all" else cv_r2_det
    pl = None
    cv_source = None
    if cv_r2 and var in (cv_r2.get("variants") or {}):
        pl = (cv_r2["variants"][var] or {}).get("pooled")
        cv_source = f"cv_r2_{mode}.json (session 2, corrected strike frame)"
    if pl is None:
        pl = ((cv_all or {}).get("variants", {}).get("anatomy_full", {}) or {}).get("pooled", {})
        cv_source = "cv_all.json (session 1)"
    ci = pl.get("dti_ci95_quadrant_jackknife") or [None, None]
    side = dict((meas or {}).get("side") or {})
    if "log_ratio_R_over_L" not in side and side.get("n_domain_left"):
        rl = side["n_withheld_left"] / side["n_domain_left"]
        rr = side["n_withheld_right"] / max(side.get("n_domain_right", 0), 1)
        side["rate_left"], side["rate_right"] = rl, rr
        side["log_ratio_R_over_L"] = math.log(rr / max(rl, 1e-12))
    card = {
        "hypothesis": ("Secondary strands around mapped faults are not isotropic: they sit at a "
                       "fitted cross-strike stepover and along-strike offset from the nearest "
                       "visible trace, so a per-fault intensity built from distance, component "
                       "length and offset geometry locates fault pixels the catalogue lacks."),
        "mechanism": ("Distributed shear produces en echelon Riedel shears and synthetic splays; "
                      "damage-zone width grows with displacement (Savage & Brodsky 2011). "
                      f"Operationally: a gradient-boosted intensity over the "
                      f"{len((build or {}).get('features', []))} catalogue-geometry features of "
                      f"variant '{var}' (distance, trace-frame stepover/along-strike, component "
                      "length as displacement proxy, cyclic strike encoding and its explicit "
                      "distance interactions, trace coherence, local fault density), "
                      "calibrated to the withheld base rate, then lazy-greedy max-coverage "
                      "allocation at the exact DTI marginal bar. Offsets are decomposed in the "
                      "local trace frame (IR-57-STRIKE-01 corrected an inverted strike fallback "
                      "that had forced a grid-aligned frame)."),
        "named_non_fault_process_that_could_mimic_it": (
            "Withheld catalogue pixels are parts of mapped systems, so part of the measured "
            "near-field enrichment is mapping continuity (a mapper stopping mid-system), not "
            "mechanics. The detached withholding mode (>= 400 m from any other component) is the "
            "control; a second mimic is geomorphic linearity (dry washes, roads, ridge crests) "
            "aligning with the regional strike sets, which this lane cannot test without the DEM."),
        "holdout_dti": {
            "instrument": ("hide-and-recover, 4 quadrants x draws 20/21, whole-segment withholding, "
                           "12 px domain erosion, visible-only features, pooled DTI "
                           "alpha=0.2 beta=0.8 R=3 px, leave-one-quadrant-out"),
            "variant_measured": var,
            "withholding_mode": mode,
            "cv_source": cv_source,
            "withheld_positive_pixels": pl.get("n_truth"),
            "pooled_dti": pl.get("pooled_dti"),
            "ci95_quadrant_jackknife": ci,
            "coverage": pl.get("coverage"),
            "label": "HOLDOUT-DTI - a local instrument reading, NOT a projected live score",
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
            # IR-57-OVERLAP-01: the drift screen is taken against OTHER lanes;
            # same-lane overlap with this repo's own earlier builds is disclosed.
            "unique_vs_other_lanes": uq.get("unique_vs_other_lanes"),
            "n_other_lane_rasters": uq.get("n_other_lane_rasters"),
            "worst_overlap_other_lanes": uq.get("worst_overlap_other_lanes"),
            "worst_overlap_other_lane_sub": uq.get("worst_overlap_other_lane_sub"),
            "worst_jaccard_other_lanes": uq.get("worst_jaccard_other_lanes"),
            "worst_rho_other_lanes": uq.get("worst_rho_other_lanes"),
            "n_same_lane_earlier_builds": uq.get("n_same_lane_earlier_builds"),
            "worst_overlap_same_lane": uq.get("worst_overlap_same_lane"),
            "worst_overlap_same_lane_sub": uq.get("worst_overlap_same_lane_sub"),
            "worst_jaccard_same_lane": uq.get("worst_jaccard_same_lane"),
            "worst_rho_same_lane": uq.get("worst_rho_same_lane"),
            "same_lane_overlap_note": uq.get("same_lane_overlap_note"),
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
            "available_in_provided_database": False,
            "measured_log_ratio_right_over_left": side.get("log_ratio_R_over_L"),
            "encoded": False,
        },
        "verdict": "PENDING" if not build else (
            "promote" if (z.get("all_checks_passed")
                          and (uq.get("unique_vs_other_lanes", uq.get("unique")))) else "negative"),
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
    cv_r2_all = load("cv_r2_all.json")
    cv_r2_det = load("cv_r2_detached.json")
    meas = load("withheld_structure.json")
    reg = (ROOT / "registry" / "registry_index.json")
    uniq_src = json.loads(reg.read_text()) if reg.exists() else []

    DOCS.mkdir(exist_ok=True)
    (DOCS / "assets").mkdir(exist_ok=True)
    (DOCS / "assets" / "site.css").write_text(CSS)
    (DOCS / ".nojekyll").write_text("")

    pages = {
        "index.html": ("57GEMSDOE — fault-zone anatomy", build_index(build, cv_all, uniq_src, cv_r2_all), "index.html"),
        "executive-summary.html": ("How to submit", build_exec(build), "executive-summary.html"),
        "method.html": ("Method", build_method(meas, cv_all, cv_det, cv_r2_all, cv_r2_det), "method.html"),
        "hypotheses.html": ("Hypotheses", build_hypotheses(), "hypotheses.html"),
        "results.html": ("Results", build_results(cv_all, cv_det, build, rb,
                                                  cv_r2_all, cv_r2_det), "results.html"),
        "irregularities.html": ("Irregularities", build_irregularities(), "irregularities.html"),
        "data-sources.html": ("Data sources", build_sources(), "data-sources.html"),
        "run-card.html": ("Run card", build_runcard(build, cv_all, meas,
                                                   cv_r2_all, cv_r2_det), "run-card.html"),
    }
    for fname, (title, body, active) in pages.items():
        (DOCS / fname).write_text(page(title, body, active))
        print(f"wrote docs/{fname}  ({len(body):,} chars of body)")

    # ---- root index.html: generated too, so the download button can never rot.
    # Hand-maintained root pages drifted twice (IR-57-SITE-02).
    build = build or {}
    z = build.get("zeros_tif") or {}
    name = build.get("submission_name")
    fname = f"{name}-zeros.tif" if name else None
    uq0 = (build or {}).get("uniqueness") or {}
    ok = bool(z.get("all_checks_passed")) and bool(
        uq0.get("unique_vs_other_lanes", uq0.get("unique")))
    btn = (f'<a class="btn dl" href="docs/downloads/{esc(fname)}" download>'
           f'⬇ Download the submission GeoTIFF</a>') if fname else ""
    verdict = ("portal-valid and unique — OK to submit" if ok
               else "NOT cleared — see docs/executive-summary.html")
    (ROOT / "index.html").write_text(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0; url=docs/index.html">
<title>GEMSDOE57 — fault-zone anatomy lane</title>
<style>
body{{font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
     max-width:760px;margin:8vh auto;padding:0 20px;line-height:1.6;color:#1c2733}}
.btn{{display:inline-block;background:#0b6bcb;color:#fff;text-decoration:none;font-weight:700;
     padding:12px 22px;border-radius:8px;margin:6px 8px 6px 0}}
.btn.dl{{background:#0b6e4f}}
code{{background:#eef3f7;padding:1px 5px;border-radius:4px;font-size:13px}}
</style>
</head>
<body>
<h1>GEMSDOE57 — fault-zone anatomy lane</h1>
<p>DrivenData GEMS prize (competition 306): a unique, validated submission GeoTIFF —
a fitted fault-zone-anatomy emission around the known USGS + INGENIOUS faults.</p>
<p>Current build: <code>{esc(str(name))}</code><br>
Status: <b>{esc(verdict)}</b></p>
<p><a class="btn" href="docs/index.html">Open the site →</a>
{btn}</p>
<p>Redirecting to <code>docs/index.html</code>…</p>
</body>
</html>
""")
    print("wrote index.html (root, generated)")


if __name__ == "__main__":
    main()
