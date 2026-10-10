#!/usr/bin/env python3
"""Generate the HOLD-first executive site from the current audit run card.

This generator intentionally does not expose an active download link or emit
historical, unversioned CV/live-score comparisons as verified results.
"""
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVIDENCE = ROOT / "evidence"
HOLD_TEXT = "HOLD — NOT OK TO DOWNLOAD OR SUBMIT"

NAV = [
    ("index.html", "Status"),
    ("executive-summary.html", "Submission guide"),
    ("method.html", "Method"),
    ("hypotheses.html", "Hypotheses"),
    ("results.html", "Results"),
    ("data-sources.html", "Sources"),
    ("run-card.html", "Run card"),
    ("irregularities.html", "Audit notes"),
]

CSS = """
:root{--ink:#13232d;--mut:#586c78;--line:#d9e2e7;--bg:#f4f7f8;--card:#fff;
--green:#0c7051;--red:#9f2f21;--amber:#815700;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:#075f48}header{background:#13232d;color:white;padding:17px max(22px,calc((100% - 1060px)/2))}
header h1{font-size:20px;margin:0}header .sub{color:#c5d2d8;font-size:13px}
nav{display:flex;flex-wrap:wrap;gap:2px;background:#203742;padding:0 max(16px,calc((100% - 1080px)/2))}
nav a{color:#e1e9ed;text-decoration:none;padding:10px 12px;font-size:13px;border-bottom:3px solid transparent}
nav a.on,nav a:hover{color:#fff;border-bottom-color:#ffce66}main{max-width:1080px;margin:auto;padding:24px 22px 60px}
h2{font-size:21px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}h3{font-size:17px;margin:18px 0 6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:17px 19px;margin:13px 0}
.alert{background:#fff0ed;border:2px solid #b74735;border-left-width:8px;padding:16px 18px;border-radius:8px;margin:16px 0}
.alert strong{font-size:20px}.note{background:#fff8e8;border-left:5px solid #d09b18;padding:12px 15px;margin:14px 0}
.ok{background:#e8f7ee;border-left:5px solid var(--green);padding:12px 15px;margin:14px 0}
.tag{display:inline-block;border-radius:4px;padding:2px 7px;font-size:11px;font-weight:750;letter-spacing:.3px;text-transform:uppercase;background:#fff0d0;color:var(--amber)}
.tag.red{background:#fbe0db;color:var(--red)}.tag.green{background:#e0f4e7;color:var(--green)}
code,pre{font-family:var(--mono)}code{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#172932;color:#e5edf1;padding:15px;border-radius:8px;font-size:12px}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px;background:white}th,td{border:1px solid var(--line);padding:8px;vertical-align:top;text-align:left}th{background:#eaf0f3}
.kv{display:grid;grid-template-columns:245px 1fr;gap:5px 12px}.kv dt{color:var(--mut)}.kv dd{margin:0;overflow-wrap:anywhere;font-family:var(--mono);font-size:13px}
footer{max-width:1080px;margin:auto;border-top:1px solid var(--line);padding:16px 22px 34px;color:var(--mut);font-size:12px}
.small{font-size:13px;color:var(--mut)}
"""


def load_card() -> dict:
    path = EVIDENCE / "run_card.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_public_feed() -> tuple[dict, dict]:
    """Load the last successful public board snapshot and latest refresh attempt."""
    snapshot_path = EVIDENCE / "leaderboard_snapshot.json"
    status_path = EVIDENCE / "feed_refresh_status.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8")) if snapshot_path.is_file() else {}
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {}
    return snapshot, status


def load_hypotheses() -> dict:
    path = EVIDENCE / "hypotheses_current.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value) -> str:
    return html.escape(str(value))


def number(value, places=6) -> str:
    if value is None:
        return "NOT AVAILABLE"
    try:
        return f"{float(value):.{places}f}"
    except (TypeError, ValueError):
        return esc(value)


def page(title: str, body: str, active: str) -> str:
    nav = "".join(
        f'<a class="{"on" if href == active else ""}" href="{href}">{esc(label)}</a>'
        for href, label in NAV
    )
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · 57GEMSDOE</title><link rel="stylesheet" href="assets/site.css"></head>
<body><header><h1>57GEMSDOE — fault-zone-anatomy lane</h1>
<div class="sub">DOE GEMS Prize · secondary strands around mapped faults</div></header>
<nav>{nav}</nav><main>{body}</main>
<footer>Generated {generated}. Local checks and historical HOLDOUT-DTI readings are not organizer acceptance.
No active download or submission is approved.</footer></body></html>"""


def hold_banner() -> str:
    return """<div class="alert" role="alert">
<strong>HOLD — NOT OK TO DOWNLOAD OR SUBMIT</strong>
<p><b>Submit to competition: NO. Download: NOT OK.</b> There is no cleared submission file.
Historical TIFF/ZIP files remain in the repository for provenance; a direct static URL may still
resolve. That is not download authorization. No weekly slot was used. The current decision is
<b>negative / not promoted</b>.</p>
</div>"""


def build_status(card: dict) -> str:
    hold = card.get("holdout_result", {})
    registry = card.get("registry_comparison", {})
    cache = registry.get("current_cache_preflight", {})
    validator = card.get("validator_result", {})
    dti = number(hold.get("pooled_dti"))
    indexed = registry.get("indexed_matching_grid_rasters", "NOT AVAILABLE")
    scope = card.get("registry_scope", "Public owner-repository inventory; not organizer-complete.")
    firing_count = registry.get("forward_overlap_firings", "NOT AVAILABLE")
    itemized = registry.get("firings_itemized_in_stored_report", "NOT AVAILABLE")
    verified = cache.get("verified_rasters", "NOT VERIFIED")
    missing = cache.get("missing_cache_files", "NOT VERIFIED")
    cache_status = cache.get("status", "NOT VERIFIED")
    return f"""
{hold_banner()}
<h2>Executive status</h2>
<div class="card"><dl class="kv">
<dt>Download / submission</dt><dd><b>NOT CLEARED</b></dd>
<dt>Weekly slot</dt><dd>Not promoted; selector decision is separate</dd>
<dt>Experiments this audit</dt><dd>{esc(card.get('audit_actions', {}).get('new_experiments_run', 0))} — no holdout run or score-producing experiment</dd>
<dt>Previous candidate SHA256</dt><dd>{esc(card.get('raster_sha256', 'NOT AVAILABLE'))}</dd>
<dt>Historical artifact name</dt><dd>{esc(card.get('submission_name', 'NOT AVAILABLE'))}</dd>
<dt>Historical note (not approved)</dt><dd>{esc(card.get('submission_note', 'NOT AVAILABLE'))}</dd>
<dt>Historical local format receipt</dt><dd>{esc(validator.get('evidence_status', 'NOT AVAILABLE'))}</dd>
<dt>Historic HOLDOUT-DTI</dt><dd>{number(hold.get('pooled_dti'))} · 95% CI {esc(hold.get('ci95_spatial_block_bootstrap', hold.get('ci95', [])))}</dd>
<dt>Withheld positives</dt><dd>{esc(hold.get('withheld_positive_pixels', 'NOT AVAILABLE'))}</dd>
<dt>Evaluator</dt><dd>{esc(hold.get('evaluator_version', 'NOT AVAILABLE'))}</dd>
<dt>Registry index size</dt><dd>{esc(indexed)}</dd>
<dt>Registry scope</dt><dd>{esc(scope)}</dd>
<dt>Registry cache preflight</dt><dd>{esc(cache_status)} — {esc(verified)}/{esc(indexed)} verified; {esc(missing)} missing</dd>
<dt>Literal overlap gate</dt><dd>{esc(registry.get('literal_gate_verdict', 'NOT AVAILABLE'))}; max pre-placement positive-support overlap within 3 px {number(registry.get('max_forward_dot_overlap_within_3px'))}; {esc(firing_count)} firings</dd>
<dt>Independent universal-overlap witness</dt><dd>17GEMSDOE raster SHA256 {esc(registry.get('independent_witness_blocker', {}).get('sha256', 'NOT AVAILABLE'))}; covers every allowable cell. Any nonempty candidate has measured 3-px forward overlap 1.0 while this witness remains in scope. This is not a score or full-cache revalidation.</dd>
</dl></div>
<div class="note"><b>Interpretation:</b> the stored {dti} value is a historical
HOLDOUT-DTI reading whose source hashes do not match the current tree; it is not current-code clearance or a live-score projection. The indexed public-inventory
report records {esc(firing_count)} forward-overlap firings ({esc(itemized)} itemized) on the
soft surface's finite-positive support, not final dots; it therefore does not clear the literal
stop rule. Current cache verification is {esc(cache_status)}. The publisher is retired; any future replacement must verify every indexed raster and disclose that this inventory is not organizer-complete.
See <a href="run-card.html">the run card</a>.</div>
<h2>What must happen before a future build</h2>
<ol>
<li>Generate a current-code, source/input-hash-pinned spatial holdout result and an independent
selector receipt. The recorded three-experiment budget is exhausted; this is not authorization to
run one now.</li>
<li>Restore and SHA256-verify every raster in the indexed registry. Missing cache entries mean the
uniqueness gate cannot run.</li>
<li>Run the continuous-surface comparison, pre-placement dot comparison, and final-dot comparison.
Stop at the protocol thresholds; do not retune after a firing.</li>
<li>Only then may the fail-closed writer package one validated GeoTIFF and a one-TIFF ZIP. A weekly
slot still requires a separate selector decision.</li>
</ol>
<p>See the <a href="executive-summary.html">executive submission guide</a> and the
<a href="hypotheses.html">ranked untried hypotheses</a>.</p>
"""


def build_executive(card: dict) -> str:
    registry = card.get("registry_comparison", {})
    cache = registry.get("current_cache_preflight", {})
    indexed = registry.get("indexed_matching_grid_rasters", "NOT AVAILABLE")
    scope = card.get("registry_scope", "Indexed public owner-repository inventory; not organizer-complete.")
    verified = cache.get("verified_rasters", "NOT VERIFIED")
    missing = cache.get("missing_cache_files", "NOT VERIFIED")
    cache_status = cache.get("status", "NOT VERIFIED")
    return f"""
{hold_banner()}
<h2>Executive submission guide</h2>
<p><b>This is a conditional guide, not permission to submit.</b> No current file is cleared. The
historical soft research-surface GeoTIFF has a local format receipt but fails the literal registry
stop rule and must not be used.</p>
<div class="note"><b>Inventory scope:</b> {esc(scope)} This finite public index is not an
organizer-complete registry and cannot certify uniqueness against inaccessible submissions.</div>
<h3>Before any upload is possible</h3>
<ol>
<li>Obtain renewed authorization and an independently reviewed, version-pinned holdout and
selector decision. Current evidence is not version-attested; the three-experiment budget is spent.</li>
<li>Restore and verify all {esc(indexed)} rasters in the pinned public index by recorded SHA256. The
current cache preflight is {esc(cache_status)} ({esc(verified)}/{esc(indexed)} verified;
{esc(missing)} missing). This check would still not establish organizer-wide completeness.</li>
<li>The current submission publisher is retired and creates no candidate TIFF or ZIP. Do not run
fitting or build commands under this HOLD. Any future replacement requires a separately reviewed,
organizer-complete comparison scope, current holdout clearance, and literal surface/pre-placement/
final-dot gates; any stop means no output.</li>
<li>If a future candidate is actually cleared, review its exact GeoTIFF and local format receipt.
The writer does not clip or fill predictions; local validity is not organizer acceptance.</li>
<li>Only after a separate selector says to use a weekly slot, upload the exact validated single-band
GeoTIFF (or a ZIP with exactly one GeoTIFF) on the competition submission page; record the actual
organizer receipt before labeling a score `ORGANIZER-CONFIRMED`.</li>
</ol>
<div class="note"><b>Additional blocking uniqueness result:</b> a session-5 independent witness check verified that the 17GEMSDOE positive-support raster covers every allowable candidate cell within 3 px. Under the unchanged literal &gt;70% rule, every nonempty candidate is blocked while this raster remains in scope. Do not exclude it or alter the threshold without explicit owner authorization. The checked witness does not revalidate the other 678 cache files.</div>
<h3>Format requirements</h3>
<ul>
<li>One band, float32; EPSG:32611; 3730 × 3292; 100 m pixels; exact pinned sample transform.</li>
<li>Every serialized value finite and in [0,1]. The conservative writer emits zero outside the
valid footprint and uses no nodata tag; it rejects invalid values rather than silently repairing
model output.</li>
<li>No positive mass outside the footprint or on mapped catalogue cells; unique submission name
and note each no longer than 140 characters.</li>
</ul>
<div class="note"><b>Portal error:</b> “Predicted values must be in range [0, 1]”. Its specific root cause
is not established. The writer therefore applies a conservative local policy: every serialized
value is finite and in [0,1], including outside the valid footprint. This avoids relying on
unspecified nodata handling; it does not claim to identify the earlier rejection cause.</div>
<p><b>Current answer to “can I download and submit?”: No.</b> No file link is provided here.</p>
"""


def build_method(card: dict) -> str:
    hold = card.get("holdout_result", {})
    registry = card.get("registry_comparison", {})
    firing_count = registry.get("forward_overlap_firings", "NOT AVAILABLE")
    return f"""
{hold_banner()}
<h2>Method and validation contract</h2>
<p>The only permitted lane is fault-zone anatomy: describe likely secondary strands relative to
visible mapped faults. Do not move to an unconstrained alternate prediction lane.</p>
<h3>Hide-and-recover</h3>
<ul>
<li>Withhold whole fault segments/components; compute every catalogue-derived feature from the
visible-only catalogue.</li>
<li>Mask visible catalogue pixels pixel-exactly from scoring.</li>
<li>Score pooled distance-weighted Tversky (DTI), alpha 0.2, beta 0.8, triangular 300 m kernel.</li>
<li>Record evaluator version, implementation/input hashes, withheld-positive count, and a 95% CI.
The stored historic result has no source-hash match: {esc(hold.get('evaluator_version', 'not available'))}.</li>
<li>Apply a single-feature canary; AUC &gt; 0.90 means leakage until disproven.</li>
</ul>
<h3>Uniqueness stop rule</h3>
<p>Before placement, compare the continuous surface by rank correlation and its inherited positive
support (finite values &gt; 0) by 3-pixel overlap; separately compare the deterministic pre-placement
dot proposal. Compare final dots only after those gates pass. Stop if rho &gt; 0.90 or if more than
70% of candidate support/dots are within 3 px of any registry raster. The historical soft-surface
report fires {esc(firing_count)} times and is not cleared; it is not a final-dot comparison. Jaccard,
reverse overlap, and exact pixel/byte identity are diagnostics, not extra stop thresholds. Do not
treat a one-direction overlap exception as a pass.</p>
<h3>Current code controls</h3>
<p><code>src/gems57/evaluate_holdout.py</code> shares its per-pixel credit primitive with
<code>src/gems57/metric.py</code>. <code>src/gems57/evaluator_provenance.py</code> pins code and data
inputs for future spatial CV. <code>src/gems57/submission_writer.py</code> writes to temporary paths,
validates the bytes, refuses overwrites, and never clips/fills predictions. These controls do not
make an old score or candidate retroactively valid.</p>
"""


def build_hypotheses(hypotheses: dict) -> str:
    candidates = hypotheses.get("candidates", [])
    cards = []
    for candidate in candidates:
        source_links = "".join(
            f'<li><a href="{esc(source.get("url", ""))}">'
            f'{esc(source.get("citation", "Source record"))}</a>: '
            f'{esc(source.get("checked_takeaway", ""))}</li>'
            for source in candidate.get("sources", [])
        )
        prior_work = candidate.get("prior_work_note")
        prior_html = (
            f'<p><b>Prior work / distinction:</b> {esc(prior_work)}</p>'
            if prior_work else ""
        )
        cards.append(f"""
<div class="card">
<h3>Rank {esc(candidate.get('rank'))}: {esc(candidate.get('hypothesis', ''))}
<span class="tag">UNTRIED</span></h3>
<p><b>Layers/data:</b> {esc('; '.join(candidate.get('layers', [])))}</p>
<p><b>Physical signature:</b> {esc(candidate.get('physical_signature', ''))}</p>
<p><b>Why it may find missing faults:</b> {esc(candidate.get('why_it_may_find_missing_faults', ''))}</p>
<p><b>What differs from inspected work:</b> {esc(candidate.get('difference_from_inspected_work', ''))}</p>
{prior_html}
<p><b>Named non-fault mimic:</b> {esc(candidate.get('named_non_fault_mimic', ''))}</p>
<p><b>Relative expected DTI potential:</b> {esc(candidate.get('relative_expected_dti_potential', 'Not estimated'))}</p>
<p><b>Implementation cost:</b> {esc(candidate.get('implementation_cost', 'Not estimated'))}</p>
<p><b>Data readiness:</b> {esc(candidate.get('data_readiness', 'Not audited'))}</p>
<p><b>Sources reviewed:</b></p><ul>{source_links}</ul>
<p><b>Future test gate:</b> {esc(candidate.get('future_test_gate', 'Not specified'))}</p>
</div>""")
    rows = "".join(cards)
    status = hypotheses.get("status", "RESEARCH SHORTLIST ONLY; NOT RUN")
    ranking = hypotheses.get("ranking_basis", "No numerical DTI gain is estimated.")
    blocker = hypotheses.get("current_blocker", "Current protocol status not recorded.")
    return f"""
{hold_banner()}
<h2>{len(candidates)} ranked, untried fault-zone-anatomy hypotheses</h2>
<p><b>{esc(status)}</b></p>
<p>{esc(ranking)}</p>
<p>Attribute counts are descriptive only. No visible-host spatial join, model test, holdout score,
or candidate implementation was performed. The shortlist is not approval to download data, run
experiments, build a TIFF, or use a competition slot. The full structured evidence and protocol
controls are in <a href="research/hypotheses.md">docs/research/hypotheses.md</a> and
<a href="data/hypotheses_current.json">the JSON shortlist</a>.</p>
<div class="note"><b>Current blocker:</b> {esc(blocker)}</div>
{rows}
"""


def build_public_board(snapshot: dict, status: dict) -> str:
    """Render organizer-published public values without implying file attribution."""
    url = snapshot.get(
        "source_url",
        "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
    )
    retrieved = snapshot.get("retrieved_utc") or snapshot.get("retrieved_date_utc", "NOT RECORDED")
    attempted = status.get("attempted_utc", "NOT RECORDED")
    method = str(status.get("method", snapshot.get("retrieval_method", "not recorded")))
    rows = snapshot.get("rows", [])
    freshness_warning = ""
    try:
        checked = dt.datetime.fromisoformat(str(retrieved).replace("Z", "+00:00"))
        if checked.tzinfo is None:
            checked = checked.replace(tzinfo=dt.timezone.utc)
        age = dt.datetime.now(dt.timezone.utc) - checked.astimezone(dt.timezone.utc)
        if age > dt.timedelta(hours=26) or age < -dt.timedelta(minutes=5):
            freshness_warning = (
                '<p class="note"><b>STALE / CLOCK-SKEWED SNAPSHOT.</b> '
                "Use the linked official leaderboard for current context.</p>"
            )
    except (TypeError, ValueError, OverflowError):
        freshness_warning = (
            '<p class="note"><b>Snapshot timestamp could not be verified.</b> '
            "Use the linked official leaderboard for current context.</p>"
        )
    highlighted = []
    if isinstance(rows, list):
        highlighted = [
            row for row in rows
            if isinstance(row, dict) and row.get("rank") in {1, 2, 3, 8, 22}
        ]
    table_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            esc(row.get("rank", "")),
            esc(row.get("participant_display", "")),
            number(row.get("public_dti"), 4),
        )
        for row in highlighted
    )
    if table_rows:
        table = (
            "<table><tr><th>Rank</th><th>Participant display</th>"
            "<th>Public-board DTI</th></tr>" + table_rows + "</table>"
        )
    else:
        table = "<p>No valid selected rows are available in the retained snapshot.</p>"

    status_warning = ""
    if status.get("ok") is False:
        status_warning = (
            "<p class=\"note\"><b>Latest refresh failed.</b> The displayed values are the last "
            "successful cached public snapshot, not a fresh result of this failed attempt. "
            + esc(status.get("error", "No error detail was retained."))
            + "</p>"
        )
    elif status.get("ok") is None:
        status_warning = (
            "<p class=\"note\"><b>Refresh state unknown.</b> Do not treat the retained snapshot "
            "as current; use the linked official board for current context.</p>"
        )
    elif "not scripts/refresh_feed.py" in method.lower():
        status_warning = (
            "<p class=\"note\">This capture used the page-retrieval tool, not the repository's "
            "scheduled raw-HTML refresh script. Only the selected rows shown in the saved snapshot "
            "were retained; raw HTML was not saved.</p>"
        )
    status_warning += freshness_warning

    full_scope = snapshot.get("scope", "Scope not recorded; exact-file attribution is unavailable.")
    return f"""
<div class="card"><h3>Public leaderboard snapshot — context only, not a submission receipt</h3>
<p><b>Evidence class: organizer-published public-board values, not ORGANIZER-CONFIRMED exact-file
scores.</b> Retrieved {esc(retrieved)}; latest recorded attempt {esc(attempted)}. Method: {esc(method)}.
See the <a href="{esc(url)}">official DrivenData leaderboard</a>.</p>
<p>{esc(full_scope)}</p>
{table}
<p>No submission-page receipt or raster hash ties these participant rows to H33-2-B2 or to any
artifact in this repository. The public rank-22 value of 0.2778 numerically matches an
owner-reported H33 figure, but that is not evidence that the participant, score, or file is the
same. Do not infer attribution or causality.</p>
{status_warning}
</div>
"""


def build_results(card: dict, feed_snapshot: dict, feed_status: dict) -> str:
    hold = card.get("holdout_result", {})
    report = card.get("registry_comparison", {})
    reported = card.get("reported_live_score", {})
    return f"""
{hold_banner()}
<h2>Results: historical evidence, not current clearance</h2>
<div class="card"><h3>Local holdout reading</h3>
<p><span class="tag">HOLDOUT-DTI</span> <b>{number(hold.get('pooled_dti'))}</b>, 95% CI
{esc(hold.get('ci95_spatial_block_bootstrap', hold.get('ci95', [])))}, {esc(hold.get('withheld_positive_pixels', 'not available'))}
withheld positives. Evaluator record: <code>{esc(hold.get('evaluator_version', 'not available'))}</code>.</p>
<p>This is a historical instrument reading whose stored evaluator source hashes do not match the
current tree. It is not current-code validation, not a live-score projection, and does not clear
the candidate.</p></div>
<div class="card"><h3>Separate binary-allocation HOLDOUT-DTI</h3>
<p><span class="tag">HOLDOUT-DTI</span> {number(card.get('binary_dot_holdout_result', {}).get('pooled_dti'))},
95% CI {esc(card.get('binary_dot_holdout_result', {}).get('ci95_spatial_block_bootstrap', []))},
{esc(card.get('binary_dot_holdout_result', {}).get('withheld_positive_pixels', 'not available'))}
withheld positives; evaluator <code>{esc(card.get('binary_dot_holdout_result', {}).get('evaluator_version', 'not available'))}</code>.
This is a test-fold allocator comparison only, not the soft TIFF's value; no production final dots were generated.</p></div>
<div class="note"><b>Holdout reconciliation:</b> the historical H57-K `lane8_geophys` result uses 22,619 withheld positives across 8 recorded cells; its evaluator version/input hashes are not pinned in that arm record, and its single-feature canary flags `d`, `d_perp`, and `vis_dtip` above the 0.90 leakage threshold. The later pooled-hide-v2 records use 11,321 withheld positives and stored code hashes that do not match this tree. The soft surface and binary allocation are also different representations. These values are <b>not comparable</b>; no candidate has beaten a valid comparable benchmark. See <a href="data/holdout_scope_reconciliation_20261010.json">the machine-readable reconciliation</a>.</div>
<div class="card"><h3>Indexed public-inventory comparison</h3>
<p>Recorded public owner-repository inventory: {esc(report.get('indexed_matching_grid_rasters', 'not available'))} indexed rasters;
not organizer-complete. Max Spearman {number(report.get('max_spearman_full_footprint'))}; max Jaccard diagnostic
{number(report.get('max_jaccard'))} (not a stop threshold); maximum pre-placement positive-support overlap within 3 px
{number(report.get('max_forward_dot_overlap_within_3px'))} (finite surface values &gt; 0, not final dots);
{esc(report.get('forward_overlap_firings', 'not available'))} firings above
{number(report.get('stop_threshold_forward_overlap'))}. Only
{esc(report.get('firings_itemized_in_stored_report', 'not available'))} firings are itemized.
Literal verdict: <b>{esc(report.get('literal_gate_verdict', 'not available'))}</b>.</p>
<p>The protocol says log and stop. Reverse-overlap or saturation exceptions are not silently applied.</p></div>
{build_public_board(feed_snapshot, feed_status)}
<h2>Owner-reported H33 value and artifact audit</h2>
<p>The historical H33 <b>{number(reported.get('value'), 4)}</b> value remains labeled
<b>{esc(reported.get('classification', 'OWNER-REPORTED; no organizer receipt'))}</b>. It is neither a
HOLDOUT-DTI result nor an ORGANIZER-CONFIRMED exact-file result. The public
board values shown above are organizer-published, but no submission-page receipt or raster hash
in this checkout ties them to H33-2-B2 or any exact repository bytes. No
`ORGANIZER-CONFIRMED` exact-file score is available here.</p>
<div class="card"><h3>What the available 0.2778 artifact audit suggests</h3>
<p>The separate raster audit found the named H33-2-B2 artifact is an exact 2-pixel catalogue-flank
prune of a 40,199-positive base: 2,545 cells were removed, none added, leaving 37,654. Sparse
thinning and pruning dots with little unique new-truth coverage could plausibly lower false-positive
cost under max-cover DTI. Hidden truth and an organizer receipt tying the score to exact bytes are
unavailable, so this is a plausible mechanism—not a causal explanation for 0.2778. See
<a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/best_submission_audit.json">the raster audit</a>.</p></div>
<div class="note"><b>Improvement:</b> possible in principle, but no expected gain or probability can be estimated from the evidence here. The universal overlap witness currently blocks every nonempty candidate under the unchanged literal rule, and the experiment budget is spent.</div>
<h2>Could a future candidate improve?</h2>
<p>Possibly, but the available evidence cannot establish a probability or expected gain. The local
holdout reading and owner-reported value are different evidence classes; the old candidate also fails the
uniqueness gate. The experiment budget is spent, so this audit makes no gain claim and runs no new
experiment. The next step is an independently authorized, version-pinned validation—not a score
projection.</p>
"""


def build_sources() -> str:
    audit_path = "data/attribute_audit_20261010.json"
    reconciliation_path = "data/holdout_scope_reconciliation_20261010.json"
    return f"""
{hold_banner()}
<h2>Competition and local data</h2>
<ul>
<li>Official competition home and task statement: <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData #306</a> and its
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description</a>.
Competition-grid features are not present in this checkout. The historical `training_features.tif`
receipt records a 19-band third-party bridge, but does not authenticate official origin or present-file
availability; no feature raster was downloaded or prepared in this audit.</li>
<li>Local INGENIOUS/QFault extracts are pinned in
<a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/data/README.md">data/README.md</a>.
The read-only field/count audit is <a href="{audit_path}">available as JSON</a>; it is a completeness
inventory only, not a spatial join, feature, experiment, or holdout result.</li>
</ul>
<h2>Official fault and regional-data records reviewed</h2>
<ul>
<li><b>INGENIOUS / QFault:</b> <a href="https://gdr.openei.org/submissions/1391">Geothermal Data Repository submission 1391</a>
(DOI <a href="https://doi.org/10.15121/1881483">10.15121/1881483</a>). The record lists Quaternary
Faults v2 with field definitions and states public access / CC BY 4.0. Local definitions describe
slip rate and most-recent-event recency; those fields are not cumulative displacement. Local row
counts do not prove a correct join to rasterized hosts.</li>
<li><b>USGS fault slip/dilation tendency:</b> official
<a href="https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d">ScienceBase item</a>,
DOI <a href="https://doi.org/10.5066/P9YL58W6">10.5066/P9YL58W6</a>. The record describes tendency
estimates for Great Basin Quaternary-fault segments and lists downloadable archives. No archive was
downloaded; contest-area overlap, detailed schema/CRS, reuse terms, and grid registration are
unverified. It is a data-gated proposal, not a viable feature yet.</li>
<li><b>GeoDAWN:</b> official USGS page for the
<a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">airborne magnetic/radiometric data release</a>
(DOI <a href="https://doi.org/10.5066/P93LGLVQ">10.5066/P93LGLVQ</a>) and
<a href="https://gdr.openei.org/submissions/1591">GDR submission 1591</a>. Public catalog/license
metadata was reviewed. The USGS page describes two overlapping survey areas and warns that actual
flight heights vary with terrain; contest-grid overlap and alignment remain unverified.</li>
<li><b>USGS magnetic-fault analogue:</b> Grauch (2002), Open-File Report 2002-384,
<a href="https://doi.org/10.3133/ofr02384">official record</a>. Reviewed as regional background only;
no data were downloaded.</li>
</ul>
<h2>Mechanistic literature reviewed</h2>
<ul>
<li>Wang et al. (2017), stress/strain localization around strike-slip stepovers and bends,
<a href="https://doi.org/10.1016/j.tecto.2017.10.001">DOI</a>.</li>
<li>Zhu et al. (2024), review of bend-associated structures and modeling limitations,
<a href="https://doi.org/10.1016/j.marpetgeo.2024.106983">DOI</a>.</li>
<li>d'Alessio &amp; Martel (2004), fault terminations and barriers to fault growth,
<a href="https://doi.org/10.1016/j.jsg.2004.01.010">DOI</a>.</li>
<li>Savage &amp; Brodsky (2011), displacement and secondary strands in damage zones,
<a href="https://doi.org/10.1029/2010JB007665">open-access DOI</a>.</li>
</ul>
<p>These sources support mechanisms and data review; they do not establish DTI improvement or
validate a raster. Holdout scope and version limitations are documented in
<a href="{reconciliation_path}">the reconciliation JSON</a>. See
<a href="research/hypotheses.md">the ranked shortlist</a> for candidate-specific sources and controls.</p>
"""


def build_irregularities(card: dict) -> str:
    registry = card.get("registry_comparison", {})
    cache = registry.get("current_cache_preflight", {})
    firing_count = registry.get("forward_overlap_firings", "NOT AVAILABLE")
    itemized = registry.get("firings_itemized_in_stored_report", "NOT AVAILABLE")
    indexed = registry.get("indexed_matching_grid_rasters", "NOT AVAILABLE")
    verified = cache.get("verified_rasters", "NOT VERIFIED")
    missing = cache.get("missing_cache_files", "NOT VERIFIED")
    cache_status = cache.get("status", "NOT VERIFIED")
    return f"""
{hold_banner()}
<h2>Audit findings and fail-closed controls</h2>
<table><tr><th>Finding</th><th>Consequence / control</th></tr>
<tr><td>Historical holdout artifact lacks current evaluator/input source hashes.</td><td>Keep as historical HOLDOUT-DTI only; do not use it as current clearance.</td></tr>
<tr><td>Historical soft-surface positive-support comparison has {esc(firing_count)} forward-overlap firings above the literal 0.70 threshold; only {esc(itemized)} are itemized. This is not a final-dot comparison.</td><td>HOLD / STOP. No reverse-overlap exception is applied.</td></tr>
<tr><td>A session-5 verified 17GEMSDOE witness has positive support covering every allowable cell within 3 px; any nonempty candidate therefore has forward overlap 1.0.</td><td>Current literal &gt;70% rule is unsatisfiable while this raster remains in scope. Keep HOLD; do not change policy without explicit owner authorization. This single witness is not full-cache revalidation.</td></tr>
<tr><td>The public owner-repository inventory lists {esc(indexed)} rasters; it is not organizer-complete. Current cache preflight is {esc(cache_status)} ({esc(verified)} verified, {esc(missing)} missing).</td><td>The submission publisher is retired and writes no candidate. Any future replacement must verify every indexed file and disclose this scope limit; the current cache cannot clear anything.</td></tr>
<tr><td>Old score comparisons and standalone research/source pages contained unsupported or unversioned claims.</td><td>Replaced with HOLD-first pages; only version-pinned current evidence can be used for future clearance.</td></tr>
<tr><td>Earlier notes mislabeled the absent feature stack as 105-band/unobtainable; a historic bridge receipt reports 19 bands, but the file is absent now.</td><td>Corrected the count and retained-file status; no current data download/preparation was performed, and the bridge does not independently authenticate official origin.</td></tr>
<tr><td>Prior “NaN caused the range error” explanation was stronger than the evidence.</td><td>Cause remains unknown (`IR-57-NAN-02`). Writer uses all-finite [0,1] policy without claiming that NaN caused rejection.</td></tr>
<tr><td>The legacy session-4 publisher could overwrite the run card with a positive banner and active download links from a partial registry.</td><td>Its entry point is retired; exact source is preserved in <code>evidence/history/</code>. Only the current HOLD-first site generator may publish pages.</td></tr>
<tr><td>The session-2 publisher wrote candidate TIFFs before its uniqueness check and excluded same-lane prior rasters from its drift verdict.</td><td>That publisher is now a no-output stub; its exact source is archived for provenance. The literal all-indexed-raster rule has no same-lane exception.</td></tr>
<tr><td>Old submission writer silently clipped/fill-repaired model output and did not gate registry before packaging.</td><td>Writer rejects invalid values, stages outputs, validates on-disk TIFF/ZIP, refuses overwrite; build requires independent holdout clearance, complete registry, and three strict uniqueness checks.</td></tr>
<tr><td>Evaluator API/caller drift included a nonexistent metric call and stale confidence interval/code labels.</td><td>Shared `max_cover` and DTI primitives, source hashes, caller corrections, and unit regression tests added.</td></tr>
</table>
<p>The historical raster's local validator receipt is not a current authorization. The run card records
its SHA and HOLD verdict without presenting it as downloadable.</p>
"""


def build_run_card(card: dict) -> str:
    return f"""
{hold_banner()}
<h2>Current JSON run card</h2>
<p>Machine-readable record: <a href="https://github.com/buffedlizard55-lab/57GEMSDOE/blob/main/evidence/run_card.json"><code>evidence/run_card.json</code></a>.
A historical prior version is retained separately as <code>evidence/run_card_historical_unpinned.json</code>.</p>
<pre>{esc(json.dumps(card, indent=2, allow_nan=False))}</pre>
"""


def build_legacy_research(card: dict) -> str:
    return f"""
{hold_banner()}
<h2>Research page updated</h2>
<p>This URL previously served a legacy page with unversioned score comparisons and an unsupported
“validated/unique/downloadable” claim. Those claims are retired. See the
<a href="hypotheses.html">current ranked hypotheses</a>,
<a href="results.html">current evidence status</a>, and
<a href="run-card.html">current run card</a>.</p>
"""


def build_archive_page(title: str, details: str) -> str:
    return f"""
{hold_banner()}
<h2>{esc(title)}</h2>
<p><b>DO NOT SUBMIT any archived output.</b> Historical audit material is retained for provenance
only. It is not an approved download, submission, or selector decision. The current run card is the
source of truth.</p>
{details}
<p><b>Current status:</b> HOLD — not OK to download or submit. The latest measured surface failed
the literal forward-overlap gate; the current 679-raster cache preflight is incomplete.</p>
"""


def preserve_legacy_pages() -> None:
    archive = EVIDENCE / "history"
    archive.mkdir(parents=True, exist_ok=True)
    for name in ("archive.html", "h57k.html", "session-3.html", "session-4.html"):
        source = DOCS / name
        target = archive / f"site_{name.removesuffix('.html')}_legacy_2026-10-09.html"
        if source.is_file() and not target.exists():
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    card = load_card()
    feed_snapshot, feed_status = load_public_feed()
    hypotheses = load_hypotheses()
    preserve_legacy_pages()
    DOCS.mkdir(exist_ok=True)
    (DOCS / "assets").mkdir(exist_ok=True)
    (DOCS / "assets" / "site.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    pages = {
        "index.html": ("Submission status", build_status(card), "index.html"),
        "executive-summary.html": ("Executive submission guide", build_executive(card), "executive-summary.html"),
        "method.html": ("Method and validation", build_method(card), "method.html"),
        "hypotheses.html": ("Ranked hypotheses", build_hypotheses(hypotheses), "hypotheses.html"),
        "results.html": ("Results and score interpretation", build_results(card, feed_snapshot, feed_status), "results.html"),
        "data-sources.html": ("Data and source record", build_sources(), "data-sources.html"),
        "irregularities.html": ("Audit findings", build_irregularities(card), "irregularities.html"),
        "run-card.html": ("Run card", build_run_card(card), "run-card.html"),
        # Standalone legacy URLs remain directly accessible, so they also carry the HOLD.
        "research.html": ("Research status", build_legacy_research(card), "hypotheses.html"),
        "sources.html": ("Source record", build_sources(), "data-sources.html"),
        "archive.html": ("Historical artifacts", build_archive_page(
            "Historical artifacts — not approved for download",
            "<p>Legacy file retained by the repository: <code>gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif</code>. "
            "The research-only raster <code>gems57-h57g-width-normalized-b1329dc0f248-RESEARCH-DO-NOT-SUBMIT.tif</code> is also retained. "
            "Historical bytes and receipts are not current clearance.</p>"), "index.html"),
        "h57k.html": ("Archived research", build_archive_page(
            "Archived research candidate", "<p>The prior candidate page is retired. No file link or download permission is provided.</p>"), "index.html"),
        "session-3.html": ("Archived session", build_archive_page(
            "Archived session notes", "<p>Historical notes are retained in the repository for provenance; they do not authorize experiments or a slot.</p>"), "index.html"),
        "session-4.html": ("Archived session", build_archive_page(
            "Archived H57-I notes — DO NOT SUBMIT", "<p>Historical artifact name: <code>gems57-h57i-iso_full-20261009T202310Z-5e393d50e59a-zeros.tif</code>. This is not a current approved output.</p>"), "index.html"),
    }
    for filename, (title, body, active) in pages.items():
        (DOCS / filename).write_text(page(title, body, active), encoding="utf-8")
        print(f"wrote docs/{filename} ({len(body):,} chars)")

    public_data = DOCS / "data"
    public_data.mkdir(exist_ok=True)
    # Publish the exact successful public snapshot, its latest refresh state, and
    # the source/scope audits used by the visible research pages.
    for filename in (
        "leaderboard_snapshot.json",
        "feed_refresh_status.json",
        "attribute_audit_20261010.json",
        "holdout_scope_reconciliation_20261010.json",
        "orientation_holdout.json",
        "review_passes.json",
    ):
        source_path = EVIDENCE / filename
        if source_path.is_file():
            (public_data / filename).write_bytes(source_path.read_bytes())
    card_json = json.dumps(card, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    # Keep the canonical evidence alias and both public card URLs synchronized;
    # an old *_current.json path must not expose stale approval.
    (EVIDENCE / "run_card_current.json").write_text(card_json, encoding="utf-8")
    for filename in ("run_card.json", "run_card_current.json"):
        (public_data / filename).write_text(card_json, encoding="utf-8")
    hypotheses_path = EVIDENCE / "hypotheses_current.json"
    if hypotheses_path.is_file():
        hypotheses_json = json.dumps(
            json.loads(hypotheses_path.read_text(encoding="utf-8")),
            indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        (public_data / "hypotheses_current.json").write_text(hypotheses_json, encoding="utf-8")
    irregularities_path = EVIDENCE / "irregularities_current.json"
    irregularities = json.loads(irregularities_path.read_text(encoding="utf-8"))
    (public_data / "irregularities_current.json").write_text(
        json.dumps(irregularities, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8")

    # Preserve legacy /docs/*.html URLs as safe redirects to the HOLD-first pages.
    aliases = DOCS / "docs"
    aliases.mkdir(exist_ok=True)
    for filename in pages:
        redirect = f"../{filename}"
        (aliases / filename).write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0;url={redirect}">'
            f'<title>57GEMSDOE — HOLD</title></head><body>'
            f'<strong>{HOLD_TEXT}</strong><p><a href="{redirect}">Open the current page</a>.</p>'
            '</body></html>', encoding="utf-8")


if __name__ == "__main__":
    main()
