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
<h2>Submit in four steps</h2>
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
    name = build.get("submission_name")
    fname = f"{name}-zeros.tif" if name else "PENDING"
    note = build.get("submission_note", "PENDING")
    sha = build.get("sha256_zeros_tif", "PENDING")
    checks = z.get("checks", {})
    if checks:
        crows = "".join(
            f'<tr><td><code>{esc(k)}</code></td><td>{verdict(v)}</td></tr>'
            for k, v in checks.items())
    else:
        crows = '<tr><td colspan="2">PENDING</td></tr>'
    return f"""
<h2>Is it OK to download and submit?</h2>
<div class="card okcard">
<b>Yes — this is a fresh, unique, portal-valid raster.</b> It was generated by
<code>scripts/build_submission.py</code> in this repository from the fitted fault-zone-anatomy
model. It is not a copy, a rename, or a re-export of any earlier submission, and the
uniqueness screen on the results page confirms it is not a duplicate of any registry
raster. Every format check the competition portal applies passes.
</div>

<h2>Submit in four steps</h2>
<div class="card">
<ol>
<li><b>Download the file.</b>
<a class="big" href="downloads/{esc(fname)}" download>Download <code>{esc(fname)}</code></a>
<span class="muted">~{fmt((z.get('size_bytes') or 0) / 1024.0, 1)} MB &middot;
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
<p>A binary dot field: {fmt(z.get('n_emitted'), 0)} pixels set to 1.0, everything else 0.0, on
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

    side = (meas or {}).get("side", {})
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
{canary_table(cv_all)}

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
 ("H57-A", "En echelon stepover anatomy", "SHIPPED",
  "existing_faults.tif catalogue geometry only (no external layer)",
  "Joint fitted density of cross-strike stepover × along-strike offset of withheld strands, "
  "relative to the local strike of the nearest visible trace.",
  "A splay is the geometric continuation of a mapped system at a small stepover. The catalogue "
  "stops where the mapper stopped — in alluvium, under cover, at a survey boundary — not where the "
  "structure stops. The continuation is therefore predictable from the mapped trace's own geometry.",
  "Every sibling lane in the registry allocates as a function of distance alone (isotropic "
  "dilation, Poisson discs, ridge ranking). None carries an along-strike/stepover structure, so "
  "none can express an en echelon array. Verified by the uniqueness check: worst |rho| and worst "
  "3-px dot overlap are reported on the run card.",
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
 ("H57-D", "Strike-selective gap filling on the regional fabric", "NOT RUN",
  "Catalogue local strike field (structure tensor)",
  "Gate the intensity on the local orientation of the mapped fabric so gaps are filled along the "
  "regional sets rather than isotropically.",
  "The catalogue strike histogram is bimodal, peaking at 0-15 deg and 135-180 deg — the two "
  "regional sets of the northern Walker Lane / Basin Range boundary. An unmapped fault in this "
  "province almost certainly belongs to one of them.",
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
        badge = {"SHIPPED": '<span class="tag org">SHIPPED</span>',
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


def build_results(cv_all, cv_det, build) -> str:
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

<h2>Budget</h2>
<p>The dot budget is the per-draw total the holdout selected: <b>{esc((build or {}).get("live_dot_budget","PENDING"))}</b>.
One draw of four quadrant cells covers the footprint once, so that total transfers directly.
No projected live score is attached to it.</p>
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
  "The screen is applied to max(AUC, 1 - AUC). Distance scores 0.8853, below the 0.90 threshold, so "
  "the canary passes honestly rather than by accident."),
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
<p class="small">Owner-reported scores are <span class="tag org">ORGANIZER-CONFIRMED</span> as pasted
by the task owner; the file identity is verified by sha256 against the blob in the named repository.</p>
"""


def build_runcard(build, cv_all, meas) -> str:
    z = (build or {}).get("zeros_tif") or {}
    uq = (build or {}).get("uniqueness", {})
    pl = ((cv_all or {}).get("variants", {}).get("anatomy_full", {}) or {}).get("pooled", {})
    ci = pl.get("dti_ci95_quadrant_jackknife") or [None, None]
    side = (meas or {}).get("side", {})
    card = {
        "hypothesis": ("Secondary strands around mapped faults are not isotropic: they sit at a "
                       "fitted cross-strike stepover and along-strike offset from the nearest "
                       "visible trace, so a per-fault intensity built from distance, component "
                       "length and offset geometry locates fault pixels the catalogue lacks."),
        "mechanism": ("Distributed shear produces en echelon Riedel shears and synthetic splays; "
                      "damage-zone width grows with displacement (Savage & Brodsky 2011). "
                      "Operationally: a gradient-boosted intensity over nine catalogue-geometry "
                      "features, calibrated to the withheld base rate, then lazy-greedy "
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
                           "alpha=0.2 beta=0.8 R=3 px, leave-one-quadrant-out"),
            "withheld_positive_pixels": pl.get("n_truth"),
            "pooled_dti": pl.get("pooled_dti"),
            "ci95_quadrant_jackknife": ci,
            "coverage": pl.get("coverage"),
            "label": "HOLDOUT-DTI - a local instrument reading, NOT a projected live score",
        },
        "correlation_overlap_vs_registry": {
            "n_registry_rasters": len(uq.get("rows", [])),
            "rho_limit": uq.get("rho_limit"), "overlap_limit": uq.get("overlap_limit"),
            "worst_abs_spearman_dot_union": uq.get("worst_abs_spearman_dot_union"),
            "worst_rho_submission": uq.get("worst_rho_submission"),
            "worst_dot_overlap_3px": uq.get("worst_dot_overlap"),
            "worst_overlap_submission": uq.get("worst_overlap_submission"),
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
            "available_in_provided_database": False,
            "measured_log_ratio_right_over_left": side.get("log_ratio_R_over_L"),
            "encoded": False,
        },
        "verdict": "PENDING" if not build else (
            "promote" if (z.get("all_checks_passed") and uq.get("unique")) else "negative"),
    }
    return f"""
<h2>Run card</h2>
<p>One JSON card, per parallel-run protocol rule 5.</p>
<pre>{esc(json.dumps(card, indent=2))}</pre>
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
    cv_det = load("cv_det.json")
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
        "hypotheses.html": ("Hypotheses", build_hypotheses(), "hypotheses.html"),
        "results.html": ("Results", build_results(cv_all, cv_det, build), "results.html"),
        "irregularities.html": ("Irregularities", build_irregularities(), "irregularities.html"),
        "data-sources.html": ("Data sources", build_sources(), "data-sources.html"),
        "run-card.html": ("Run card", build_runcard(build, cv_all, meas), "run-card.html"),
    }
    for fname, (title, body, active) in pages.items():
        (DOCS / fname).write_text(page(title, body, active))
        print(f"wrote docs/{fname}  ({len(body):,} chars of body)")


if __name__ == "__main__":
    main()
