#!/usr/bin/env python3
"""Regenerate ``docs/`` from committed evidence, with fail-closed run-card status.

Measured values are loaded from ``evidence/*.json`` and
``registry/registry_index.json`` at build time. Explanatory text also includes
protocol thresholds, historical context, and cited public-source snapshots.
Missing measurements are rendered as ``PENDING`` rather than guessed.
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
<footer>Generated {stamp} by <code>scripts/build_site.py</code> from committed evidence.
Measured values come from evidence files; protocol thresholds, historical context, and date-bounded public-source snapshots are stated inline.
<span class="tag hold">HOLDOUT-DTI</span> = local instrument reading, never a live score.
<span class="tag org">ORGANIZER-CONFIRMED</span> = copied from a submission-page receipt.</footer>
</body></html>
"""


# --------------------------------------------------------------------------- #
def submission_status_html() -> str:
    """Render the current run card as a fail-closed download/submission decision."""
    card = load("run_card.json") or {}
    artifact = card.get("artifact", {})
    holdout = card.get("holdout", {})
    primary = holdout.get("primary_preregistered_run", {})
    sensitivity = holdout.get("matched_mass_sensitivity_not_confirmatory", {})
    registry = card.get("registry", {})
    surface = registry.get("pre_placement_surface", {})
    dots = registry.get("final_dots", {})
    firing = dots.get("first_firing") or {}
    cleared = artifact.get("download_status") == "CLEARED TO DOWNLOAD"
    if not card:
        return ('<div class="bad-box"><b>NOT CLEARED:</b> no current run card is available. '
                'Do not download or submit any candidate.</div>')
    if cleared:
        path = artifact.get("download_path")
        if path:
            return (f'<div class="ok-box"><b>Cleared to download only:</b> '
                    f'<a href="{esc(path)}" download>{esc(Path(path).name)}</a>. '
                    'This is not organizer acceptance or a weekly-slot selection.</div>')
        return ('<div class="bad-box"><b>NOT CLEARED:</b> run card says cleared but no validated '
                'download path is recorded. Fail closed; do not submit.</div>')

    maxrho = surface.get("max_spearman_full_footprint") or {}
    overlap = firing.get("my_dots_within_3px_of_theirs")
    overlap_text = (f"{100*overlap:.2f}%" if isinstance(overlap, (int, float)) else "not measured")
    prior = firing.get("submission", "not measured")
    c = sensitivity.get("candidate", {})
    ctrl = sensitivity.get("control_no_side", {})
    delta = sensitivity.get("paired_candidate_minus_control", {})
    delta_ci = delta.get("ci95") or [None, None]
    c_ci = c.get("ci95") or [None, None]
    return f"""
<h2>Download / submission status</h2>
<div class="bad-box" style="border-width:3px">
<h3 style="margin-top:0">NOT CLEARED — do not download or submit</h3>
<p>No new candidate GeoTIFF was generated. The in-memory H57-B final-dot map has a literal
3-px forward-overlap of <b>{esc(overlap_text)}</b> with <code>{esc(prior)}</code>, above the
<b>70%</b> stop threshold. The surface gate passed (full-footprint max Spearman
<b>{fmt(maxrho.get("value"), 3)}</b>; {esc(surface.get("n_registry_checked", "?"))} of
{esc(surface.get("n_registry_indexed", "?"))} indexed rasters checked), but the final-dot gate
failed and stopped at its first firing. No reverse-overlap exemption or Jaccard gate was applied.</p>
<p>The original 10,000-dot-cap preregistered result is not comparable: realized counts differed in
four of eight cells. A later equal-mass reading is only a post-hoc sensitivity (candidate
HOLDOUT-DTI <b>{fmt(c.get("dti"), 5)}</b>, 95% CI [{fmt(c_ci[0], 5)}, {fmt(c_ci[1], 5)}],
with {esc(c.get("withheld_positive_count", "?"))} withheld positives; paired difference
<b>{fmt(delta.get("delta"), 5)}</b>, 95% CI [{fmt(delta_ci[0], 5)}, {fmt(delta_ci[1], 5)}]).
It is not confirmatory and cannot clear the original preregistration.</p>
<p><b>Validator:</b> not run; no TIF exists. <b>Download:</b> not cleared.
<b>Submission:</b> not submitted; no receipt. <b>Weekly slot:</b> not selected.</p>
</div>
<p>Proposed name (draft only): <code>{esc(artifact.get("submission_name", "PENDING"))}</code><br>
Proposed note ({esc(artifact.get("submission_note_characters", "?"))} characters; not assigned):
<code>{esc(artifact.get("submission_note", "PENDING"))}</code></p>
<p>The earlier <code>gems57-h57-anatomy-…-zeros.tif</code> remains a historic HOLD artifact in
<code>docs/downloads/</code>; its old 644-raster scan is not a current clearance. This page
intentionally provides no download link. See the <a href="run-card.html">current run card</a>.</p>
"""


def build_index(build, cv_all, uniq_src) -> str:
    return submission_status_html() + """
<h2>What the experiment measured</h2>
<p>H57-B tests a single visible-branch-terminal distance feature in the fault-zone-anatomy lane.
The hide-and-recover targets are whole mapped fault branches, not independent unmapped faults.
All numerical results are labelled <span class="tag hold">HOLDOUT-DTI</span>, not leaderboard
scores. Full protocol, bootstrap intervals, canary AUCs and limitations are in
<code>evidence/exp_h57b_holdout.json</code> and
<code>evidence/exp_h57b_holdout_matched6772.json</code>.</p>
<h2>Format notes for any future eligible raster</h2>
<p>The local writer/validator requires a single-band float32 GeoTIFF on the pinned EPSG:32611,
3730 × 3292 grid, values in [0,1], finite everywhere, with zero mass outside the footprint.
Passing those local checks is not organizer acceptance. No current H57-B file reached the writer.
</p>
"""


def exec_ok_card() -> str:
    return submission_status_html()


def build_exec(build) -> str:
    return submission_status_html() + """
<h2>What the status means</h2>
<ul>
<li><b>HOLDOUT-DTI</b> is a local hide-and-recover instrument reading, not a live score or
leaderboard projection.</li>
<li><b>Registry uniqueness</b> is evaluated before allocation on the surface and after allocation
on final dots. The literal forward-overlap rule is applied as written; no reverse exemption.</li>
<li><b>ORGANIZER-CONFIRMED</b> is reserved for a submission-page receipt. No receipt exists.</li>
</ul>
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
<p class="note"><b>Historical H57-A method measurements.</b> These hide-and-recover summaries are not the H57-B result and do not estimate a live leaderboard score. H57-B's separate HOLDOUT-DTI evidence and HOLD decision are on the Results and Run card pages.</p>
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
 ("H57-B", "Filtered branch-terminal proximity", "TESTED: HOLD",
  "Catalogue geometry only; distance to termini of visible between-junction branches",
  "One learned distance-to-filtered-terminal feature appended to the no_side anatomy baseline; "
  "termini near withheld branches are removed with the 3-px collar.",
  "Visible branch termini may mark relays, splays or covered continuations; the experiment tests "
  "that enrichment on whole-branch hide-and-recover folds.",
  "No fixed cone angle or hand-set lobe. Adds one feature to the no_side baseline; this is a tested "
  "mechanism hypothesis, not a novelty claim.",
  "Pre-run expected +0.005 to +0.020 DTI; primary run was non-comparable, matched-cap sensitivity "
  "+0.06096 HOLDOUT-DTI (post-hoc; not confirmatory). Literal final-dot overlap 0.7271 > 0.70; HOLD.",
  "Low. Mimics include road/dry-wash termini, map-sheet breaks and digitization endpoints."),
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
                 "TESTED: HOLD": '<span class="tag bad">TESTED — HOLD</span>',
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
<th>Pre-run expectation / measured status</th><th>Cost / limitation</th></tr>
{rows}
</table>
<h2>Order of work</h2>
<ol>
<li><b>H57-A</b> was built and validated first, because it needs no external data and its central
claim — that secondary strands sit at a measurable stepover and along-strike offset — is testable
on the hide-and-recover holdout alone.</li>
<li><b>H57-C</b> came free as a feature, after the length-proxy bug was fixed.</li>
<li><b>H57-D</b> is the cheapest remaining increment and needs no new data.</li>
<li><b>H57-B</b> was tested with a filtered branch-terminal distance feature; the primary run was non-comparable and the post-hoc matched-mass sensitivity is not confirmatory. It remains HOLD after a literal overlap firing.</li>
<li><b>H57-E</b> is blocked. The specific free official source needed is the GeodAWN airborne
magnetic and radiometric survey / 1 m DEM set linked from
<a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">usgs.gov</a>
and the competition's own <code>gems-geodawn-numerical-features.tif</code>. Both were checked: the
USGS page is outside this sandbox's network allowlist, and the feature stack is present in the
bridge repositories as five ~90 MB parts that this session does not pull.</li>
</ol>
<div class="note"><b>No weekly slot has been selected and no submission has been made.</b>
H57-B remains HOLD: its original preregistered contrast was non-comparable, its matched-mass
sensitivity was post-hoc, and its final-dot overlap exceeded the literal 0.70 gate.</div>
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
<h2>Historical holdout results — H57-A</h2>
<p class="small">These earlier measurements are not the H57-B result and not a current candidate or live-score projection. H57-B is reported in its own section below.</p>
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

<h2>Metric mechanics; no leaderboard prediction</h2>
<p>The exact metric is <code>DTI = T / (0.2(T + n - M) + 0.8K)</code>, where
<code>T</code> is covered truth credit, <code>n</code> the dot count, <code>M</code> the dots' total
self-credit and <code>K</code> the number of true new-fault pixels. A perfect prediction has
<code>n = M = T = K</code>, so the metric ceiling is 1.0. The table above is a synthetic arithmetic
sensitivity to coverage and dot budget; it is not an empirical forecast.</p>
<p>The public <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">leaderboard snapshot</a>
fetched 2026-10-09 lists #1 at 0.3774 and #7 at 0.3195. It does not identify the artifact or method
behind those entries. This repository cannot infer how much coverage they achieved or claim that
this lane can beat them. Historical H57-A holdout readings concern withheld catalogue pixels only;
current H57-B status is reported below as a separate HOLDOUT-DTI sensitivity and registry audit.</p>

"""


IRREG = [
 ("IR-57-NAN-01", "Range-validation rejection; causal diagnosis unverified", "SAFE WORKAROUND; NOT CLEARED",
  "An earlier portal attempt returned “Predicted values must be in range [0, 1]”. The provided "
  "sample raster contains NaN outside the footprint, while the competition specification describes "
  "out-of-bounds cells as null or NaN. The exact cause of that rejection was not established (see "
  "IR-57-NAN-02); it must not be attributed to NaN as a verified cause.",
  "The local zeros writer can produce finite values in [0, 1] with zero outside the footprint, a "
  "conservative format workaround for any future eligible candidate. No current H57-B file exists, "
  "has been validated, or is cleared for download/submission."),
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
 ("IR-57-UNIQ-02", "Full-registry scan dropped the firing list and reported a verdict from an exemption", "HISTORICAL REPORT CORRECTED; 64 FIRINGS REMAIN UNITEMIZED",
  "The first run of check_uniqueness_full.py saved only the first 50 forward-overlap firings, while its summary counted 114. Its verdict "
  "called the shipped file UNIQUE by a reverse-overlap exemption (rev < 0.5 = 'mechanical saturation') that is not in the protocol.",
  "The historical verdict is false under the literal rule (unique_by_protocol=false); the old report still lacks 64 firing details. No reverse-overlap exemption applies. The current H57-B audit separately checks the 667-raster surface and stops on its first final-dot firing."),
 ("IR-57-UNIQ-03", "Shipped file is DRIFT-FLAGGED by the literal uniqueness gate", "HOLD; HISTORICAL FILE",
  "Spearman max 0.180 (below the 0.90 threshold); Jaccard max 0.083 is diagnostic only, not a gate. The forward-overlap gate (> 0.70 of candidate dots within 3 px of one registry raster) fired for 114 of 644 registry rasters, max 1.00. Among the 50 itemized, reverse overlap is 0.03-0.21; reverse overlap does not exempt the candidate.",
  "Not cleared and not a current candidate. The literal protocol is applied without exemptions: log and stop on a firing. Any future replacement must pass its holdout and both registry gates; no protocol change or reverse-overlap clearance is made here."),

 ("IR-57-LABEL-01", "Owner-reported scores were labelled ORGANIZER-CONFIRMED", "FIXED (relabelled OWNER-REPORTED)",
  "The budget correlation (Spearman -0.8104, n = 15) and the brief's 0.3774 / 0.3195 quotes come from owner-pasted "
  "scores with no submission-page receipt. The label ORGANIZER-CONFIRMED is reserved for receipts.",
  "Re-derived this session from registry/registry_index.json (owner_reported_score). README and this page relabelled."),
 ("IR-57-INSAMPLE-01", "Legacy builder's holdout numbers are in-sample", "FLAGGED; BUILDER DISABLED",
  "The legacy scripts/build_submission.py fit the intensity on all 8 holdout cells and then scored the same "
  "8 cells (flank sweep and capped holdout). Those results are optimistic and are not valid confirmatory "
  "HOLDOUT-DTI readings.",
  "The CLI now exits before doing work, so it cannot write a candidate TIF. The README reproduce path uses "
  "the in-memory H57-B audit, which writes no raster. Legacy evidence remains historical; no LOQO "
  "replacement builder was implemented."),
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
 ("IR-57-UNIQ-01", "Uniqueness evidence cited files not in the repository", "FIXED; SCOPE DISCLOSED",
  "The earlier full index reported 644 rasters. A refreshed scan of all 56 public sibling-repository HEADs, "
  "with single-band validation and explicit non-submission filtering, now indexes 667 unique same-shape/CRS rasters. "
  "Fifteen off-grid rasters and 44 known external/non-submission files are recorded as skipped; one same-CRS "
  "transform-offset raster is reprojected to the pinned grid for comparison.",
  "The current H57-B surface gate checked all 667; final dots stopped at the first literal overlap failure, "
  "as required. The archive is public/accessibly cloned but is not a complete list of private or organizer submissions."),
 ("IR-57-TEST-01", "Test suite failed on main", "FIXED",
  "Five tests failed: pandas was imported but absent from requirements.txt; the gate tests pointed at a "
  "file moved to docs/downloads/archive/ and asserted an out-of-date emitted count; the data-pin test "
  "requires training_features.tif, which the sandbox cannot reach.",
  "pandas added to requirements.txt; gate tests point at the shipped file and its checks receipt; the "
  "data-pin test skips with its reason when the 419 MB file is absent."),
 ("IR-57-LEAD-01", "Official leaderboard snapshot", "VERIFIED SNAPSHOT; METHOD UNATTRIBUTED",
  "The official DrivenData leaderboard was fetched on 2026-10-09: #1 xiaofanhu 0.3774, #7 DARD 0.3195, "
  "#16 extradr19 0.2778. The page does not identify the raster or method behind a participant's score.",
  "Snapshot is date-bounded and is not an organizer receipt for any local artifact. No live score or ranking is projected for this lane."),
 ("IR-57-BRIEF-01", "Conflicting leaderboard highs in the brief", "RESOLVED AS-OF 2026-10-09",
  "The brief gives both 0.3774 and 0.3195 as the highest score. The official page resolves their ranks "
  "for the 2026-10-09 snapshot: 0.3774 is #1; 0.3195 is #7.",
  "Neither leaderboard entry establishes the underlying method or file. The project makes no claim that its holdout result will beat either entry."),
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
  "The operative rank statistic is tie-aware Spearman over the full footprint, signed: +1 for an exact "
  "copy, with the literal threshold rho > 0.90. The second literal gate is one-way candidate-dot proximity: "
  "more than 70% of candidate dots within 3 px of one prior raster is a failure. Jaccard is diagnostic only, "
  "not a gate; there is no reverse-overlap exemption unless the owner changes the protocol. The old shipped "
  "raster remains HOLD under its historical archive scan."),
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
 ("IR-57-H57B-01", "H57-B primary cap is non-comparable; matched sensitivity is post-hoc", "HOLD; NO PROMOTION",
  "At the preregistered 10,000 per-cell cap, H57-B emitted 71,191 dots versus 80,000 for no_side; "
  "the arms differed in four of eight cells. The initial contrast is non-comparable. A later 6,772 "
  "per-cell replay matched counts and produced a +0.06096 paired HOLDOUT-DTI difference, but the cap "
  "was derived after the first output was observed. The pre-run expectation was +0.005 to +0.020.",
  "The replay is disclosed as favorable post-hoc sensitivity only; its CI is conditional on that cap. "
  "No further experiment was run, and H57-B is not confirmatory or promotion-eligible."),
 ("IR-57-REG-02", "Archive index included non-submission and transform-misaligned rasters", "FIXED; SCOPE DISCLOSED",
  "The first refreshed scan exposed a 3-band Q-fault external asset and a same-CRS raster with a shifted "
  "transform. The former is not a valid single-band submission; the latter covers a different extent.",
  "The scanner now excludes the external asset, indexes 667 unique single-band same-shape/CRS rasters, "
  "records 56/56 public sibling repositories, and nearest-neighbour reprojects the one transform-offset "
  "raster onto the pinned competition grid. Off-grid/non-submission exclusions are recorded in the index."),
 ("IR-57-UNIQ-04", "H57-B final-dot overlap exceeds the literal lane limit", "HOLD; STOPPED",
  "The pre-placement surface passed across all 667 indexed rasters (max Spearman 0.42297). The in-memory "
  "27,088-dot map had 72.707% of its dots within 3 px of one prior raster, above the 70% limit.",
  "Stopped at the first literal firing; no reverse-overlap exemption and no Jaccard gate were used. "
  "No candidate TIF was generated, no validator receipt exists, and download/submission are not cleared."),
]


def build_session2() -> str:
    """Current H57-B evidence and literal registry disposition from the run card."""
    primary = load("exp_h57b_holdout.json") or {}
    matched = load("exp_h57b_holdout_matched6772.json") or {}
    surface = load("uniqueness_h57b_surface.json") or {}
    dots = load("uniqueness_h57b_dots.json") or {}
    run_card = load("run_card.json") or {}
    def score(run, arm):
        return run.get("pooled_summary", {}).get("scores", {}).get(arm, {})
    def ci_text(rec):
        ci = rec.get("ci95") or [None, None]
        return f"[{fmt(ci[0], 5)}, {fmt(ci[1], 5)}]"
    p_c, p_b = score(primary, "h57b_tip_distance"), score(primary, "no_side")
    m_c, m_b = score(matched, "h57b_tip_distance"), score(matched, "no_side")
    pair = matched.get("pooled_summary", {}).get("paired_differences", {}).get("no_side", {})
    pair_ci = pair.get("ci95") or [None, None]
    firing = dots.get("first_firing") or {}
    card_art = run_card.get("artifact", {})
    overlap = firing.get("my_dots_within_3px_of_theirs")
    return f"""
<h2>H57-B — filtered branch-terminal proximity</h2>
<p>One added feature measures distance to visible branch termini after removing cut-induced
endpoints inside the 3-px holdout collar. The named mimics are road/dry-wash endings, map-sheet
breaks and digitization endpoints. All scores below are <span class="tag hold">HOLDOUT-DTI</span>
from evaluator <code>{esc(m_c.get('evaluator_version', 'PENDING'))}</code>, with
<b>{esc(m_c.get('withheld_positive_count', 'PENDING'))}</b> withheld positives and paired
20-km spatial-block 95% intervals. None is a live score.</p>

<h3>Original preregistered run — 10,000 cap per cell</h3>
<table><tr><th>Arm</th><th class="n">HOLDOUT-DTI</th><th class="n">95% CI</th><th class="n">Dots (8 cells)</th></tr>
<tr><td>H57-B + tip distance</td><td class="n">{fmt(p_c.get('dti'),5)}</td><td class="n">{ci_text(p_c)}</td><td class="n">{sum(primary.get('variants',{}).get('h57b_tip_distance',{}).get('dot_counts_by_cell',{}).values())}</td></tr>
<tr><td>no_side control</td><td class="n">{fmt(p_b.get('dti'),5)}</td><td class="n">{ci_text(p_b)}</td><td class="n">{sum(primary.get('variants',{}).get('no_side',{}).get('dot_counts_by_cell',{}).values())}</td></tr></table>
<div class="note"><b>Non-comparable; cannot promote.</b> The candidate did not match realized dots
in four of eight cells (71,191 candidate vs 80,000 control dots), violating the preregistered
comparison rule. Do not interpret the nominal difference as a causal feature gain.</div>

<h3>Equal-mass sensitivity — cap 6,772 per cell</h3>
<table><tr><th>Arm</th><th class="n">HOLDOUT-DTI</th><th class="n">95% CI</th></tr>
<tr><td>H57-B + tip distance</td><td class="n">{fmt(m_c.get('dti'),5)}</td><td class="n">{ci_text(m_c)}</td></tr>
<tr><td>no_side control</td><td class="n">{fmt(m_b.get('dti'),5)}</td><td class="n">{ci_text(m_b)}</td></tr>
<tr><td>Paired candidate − control</td><td class="n">{fmt(pair.get('delta'),5)}</td><td class="n">[{fmt(pair_ci[0],5)}, {fmt(pair_ci[1],5)}]</td></tr></table>
<p><b>Post-hoc sensitivity only, not confirmatory.</b> The equal-mass cap was derived from the
first run's candidate counts after that run had been observed. It did not use the DTI scores, and
the features, seeds, model settings and folds did not change, but cap-selection uncertainty is not
represented by the bootstrap CI. The preregistered primary result remains HOLD. The preregistered
pre-run range was +0.005 to +0.020; the sensitivity difference (+0.06096) is outside that range
and is reported as an irregularity, not rationalized as a live-score gain.</p>

<h3>Leakage canary and registry gates</h3>
<p>All single-feature discriminative AUCs were below 0.90; maximum
<b>{fmt(run_card.get('holdout',{}).get('feature_canary',{}).get('maximum_discriminative_auc'),4)}</b>.
The pre-placement surface passed: max Spearman {fmt((surface.get('max_spearman_full_footprint') or {}).get('value'),4)}
across {esc(surface.get('n_registry_checked','?'))}/{esc(surface.get('n_registry_indexed','?'))}
indexed rasters. The final in-memory map emitted {esc(dots.get('candidate_dots','?'))} dots and
failed the literal one-way overlap gate: <b>{fmt(overlap,4)}</b> within 3 px of
<code>{esc(firing.get('submission','PENDING'))}</code> (limit 0.70). The scan stopped after the first
firing as required; no reverse-overlap exemption and no Jaccard gate were used.</p>
<p>Registry scope: {esc((run_card.get('registry',{}).get('inventory') or {}).get('n_unique_grid_rasters','?'))}
unique single-band, grid-shaped rasters across 56 public sibling repositories; this is an accessible
GitHub archive, not a guaranteed complete list of private/organizer submissions. One transform-offset
raster was reprojected to the pinned grid; multiband and known external/non-submission assets were not
included.</p>

<div class="bad-box"><b>FINAL VERDICT: HOLD.</b> No candidate TIF was generated; local format validation was
not run; no download is cleared; no submission was made and no weekly slot was selected. Draft name
<code>{esc(card_art.get('submission_name','PENDING'))}</code> and the {esc(card_art.get('submission_note_characters','?'))}-character note
are not assigned. See <a href="run-card.html">the single run card</a>.</div>
"""


def build_session2_hyp() -> str:
    card = load("run_card.json") or {}
    h = card.get("holdout", {}).get("matched_mass_sensitivity_not_confirmatory", {})
    d = h.get("paired_candidate_minus_control", {})
    ci = d.get("ci95") or [None, None]
    return f"""
<h2>Session 2 candidates tested</h2>
<table>
<tr><th>Hypothesis</th><th>Layer(s)</th><th>Physical signature</th><th>Result</th></tr>
<tr><td><b>H57-B</b> filtered branch-terminal proximity</td>
<td>Visible catalogue geometry only; endpoint distance after a 3-px cut-artifact filter</td>
<td>Withheld whole branches may cluster near true relays or splays at visible termini.</td>
<td><span class="tag bad">HOLD</span> Original cap run was non-comparable. Post-hoc matched-mass
sensitivity: paired HOLDOUT-DTI difference {fmt(d.get('delta'),5)}, 95% CI
[{fmt(ci[0],5)}, {fmt(ci[1],5)}], not confirmatory. Final-dot overlap failed the literal registry gate.</td></tr>
<tr><td><b>H57-F</b> recorded sense of slip conditions strand side</td>
<td>INGENIOUS trace <code>sense</code> column (RL / LL / N), rasterised to visible pixels only</td>
<td>Handedness-relative side of the strand, sense_sgn times side (fitted, not assumed)</td>
<td><span class="tag bad">NEGATIVE</span> historical paired gain +0.0016 over four quadrants, signs disagree.
Not promoted; no submission slot was used.</td></tr>
</table>
"""


def build_irregularities() -> str:
    rows = ""
    for iid, title, status, desc, res in IRREG:
        css_class = ("bad" if any(flag in status for flag in
                                   ("FLAGGED", "HOLD", "DISABLED", "OPEN", "NOT CLEARED"))
                     else "org" if "FIXED" in status else "")
        badge = f'<span class="tag {css_class}">{esc(status)}</span>'
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


def build_runcard(build=None, cv_all=None, meas=None) -> str:
    """Render the committed single run card; never reconstruct or overwrite it."""
    card = load("run_card.json") or {}
    if not card:
        return '<h2>Run card</h2><p class="bad-box">PENDING — evidence/run_card.json is missing.</p>'
    card_txt = json.dumps(card, indent=2, allow_nan=False)
    artifact = card.get("artifact", {})
    return f"""
<h2>Current run card</h2>
<p>The authoritative machine-readable decision is
<a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/run_card.json"><code>evidence/run_card.json</code></a>.
This page renders that file and does not regenerate or modify it.</p>
<pre>{esc(card_txt)}</pre>
<h2>How to read it</h2>
<ul>
<li><b>HOLDOUT-DTI</b> is a local hide-and-recover measurement, not a live score or leaderboard projection.</li>
<li>The H57-B primary cap run was non-comparable; the later matched-mass reading is explicitly
post-hoc sensitivity and is not confirmatory.</li>
<li>The current final-dot map fails the literal forward 3-px overlap gate. No GeoTIFF was generated,
no file is cleared to download, and no submission slot was selected.</li>
<li>The proposed name and note are drafts only. <b>{esc(artifact.get("submission_status", "PENDING"))}</b>.</li>
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
        "irregularities.html": ("Irregularities", build_irregularities(), "irregularities.html"),
        "data-sources.html": ("Data sources", build_sources(), "data-sources.html"),
        "run-card.html": ("Run card", build_runcard(build, cv_all, meas), "run-card.html"),
    }
    for fname, (title, body, active) in pages.items():
        (DOCS / fname).write_text(page(title, body, active))
        print(f"wrote docs/{fname}  ({len(body):,} chars of body)")


if __name__ == "__main__":
    main()
