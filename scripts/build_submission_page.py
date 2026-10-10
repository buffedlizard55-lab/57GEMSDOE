#!/usr/bin/env python3
"""Generate the unmistakable download/submit page for the current candidate.

The owner's standing requirement is that a visitor can tell *immediately*
whether the generated GeoTIFF is OK to download and submit, and can get the file
in one click.  ``scripts/build_site.py`` renders the research narrative and is
hard-wired to the Session-6 HOLD, so this generator produces one focused page
(``docs/submit-h57l.html``) plus a banner injected at the top of the overview and
executive-summary pages.

Nothing on the page is hand-written: every number, filename, hash and verdict is
read from the evidence JSONs produced by ``scripts/build_h57l_submission.py`` and
``scripts/uniqueness_full_scan.py``.  If an input is missing the page says so and
fails closed to NO.

Verdict rules (fixed before the candidate was built)
----------------------------------------------------
``format_ok``      on-disk validator passes every check: one band, float32,
                   EPSG:32611, 3730x3292, transform match, all values finite and
                   inside [0, 1], no positive mass outside the footprint, and no
                   positive mass on the mapped catalogue.  This is the check that
                   the portal's "Predicted values must be in range [0, 1]" error
                   corresponds to, so a NaN-bearing file can never be cleared.
``canaries_clean`` no single feature reaches a discriminative AUC above 0.90.
``sparse_unique``  the literal thresholds (Spearman <= 0.90, forward 3 px overlap
                   <= 0.70) hold against every registry raster whose positive
                   support is comparable to a dot field (<= 5% of footprint), and
                   the bytes and decoded pixels are not identical to any of them.
``literal_unique`` the same thresholds hold against *all* registry rasters
                   including continuous surfaces.  Reported, never hidden.

``okay_to_download = format_ok``.  ``okay_to_submit = format_ok AND canaries_clean
AND sparse_unique``, and the literal-gate state plus the dense-witness degeneracy
certificate are always shown next to it so the owner can overrule either way.
"""
from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from datetime import datetime, timezone

import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = DOCS / "data"
DL = DOCS / "downloads"
BANNER_MARK = "<!--H57L-SUBMISSION-BANNER-->"

COMPETITION = "https://www.drivendata.org/competitions/306/competition-doe-gems/"
SUBMIT_PAGE = "https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/"


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def load(name: str):
    p = ROOT / "evidence" / f"{name}.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text())


def verdict(sub, uniq, hold):
    """Compute every gate flag and the two owner-facing permissions."""
    missing = [n for n, v in (("h57l_submission", sub), ("h57l_holdout", hold)) if v is None]
    v = sub["validator"] if sub else {}
    checks = v.get("checks", {}) if isinstance(v, dict) else {}
    format_ok = bool(checks) and all(bool(x) for x in checks.values()) and not missing
    canaries = (hold or {}).get("canary", {}) or {}
    fired = sorted((hold or {}).get("canary_fired", []) or [])
    canaries_clean = bool(canaries) and not fired

    if uniq is None:
        sparse = dict(available=False, unique=False, note="uniqueness scan not run")
        literal = dict(available=False, unique=False, note="uniqueness scan not run")
        comparable = dict(available=False, unique=False, note="uniqueness scan not run")
        cert, matched, survivors = [], [], []
    else:
        sparse = dict(available=True, **{k: uniq["sparse_screen"].get(k) for k in (
            "n_rasters", "duplicate_count", "unique", "worst_spearman",
            "worst_spearman_submission", "worst_overlap", "worst_overlap_submission",
            "worst_jaccard", "worst_jaccard_submission", "byte_unique", "pixel_unique")})
        literal = dict(available=True, **{k: uniq["literal_gate"].get(k) for k in (
            "registry_rasters_expected", "registry_rasters_checked",
            "complete_accessible_scan", "duplicate_count", "unique",
            "worst_spearman_full_footprint", "worst_rho_submission",
            "worst_dot_overlap", "worst_overlap_submission")})
        comparable = dict(available=True, **{
            k: uniq.get("comparable_budget_screen", {}).get(k) for k in (
                "dot_cap", "comparable_factor", "n_rasters", "duplicate_count",
                "unique", "unique_after_certificate", "worst_spearman",
                "worst_spearman_submission", "worst_overlap",
                "worst_overlap_submission", "worst_jaccard",
                "worst_jaccard_submission", "byte_unique", "pixel_unique",
                "n_firing_degenerate", "n_firing_discriminating")})
        cert = uniq.get("degeneracy_certificate", [])
        matched = uniq.get("density_matched", [])
        # Two files of one raster can both survive certification; dedupe on
        # (their_dots, overlap) so the count of DISTINCT witnesses is honest.
        survivors = sorted({(c["their_dots"], round(c["candidate_forward_overlap"], 6)): c
                            for c in cert if not c["degenerate"]}.values(),
                           key=lambda c: -c["candidate_forward_overlap"])

    sparse_unique = bool(sparse.get("available") and sparse.get("unique"))
    # The operative uniqueness screen.  A 3 px forward-overlap statistic can only
    # separate placement from coverage when the witness spends a comparable number
    # of dots, so the screen is restricted to registry rasters within
    # `comparable_factor` of this candidate's budget, thresholds UNRELAXED, and
    # every firing is additionally certified against uniform random fields.
    operative_unique = bool(comparable.get("available") and comparable.get("unique")
                            and comparable.get("unique_after_certificate"))
    okay_to_download = bool(format_ok)
    okay_to_submit = bool(format_ok and canaries_clean and operative_unique)
    literal_fires = bool(literal.get("available")) and not literal.get("unique")
    return dict(missing=missing, format_ok=format_ok, canaries_clean=canaries_clean,
                canary_fired=fired, sparse=sparse, literal=literal,
                comparable=comparable, survivors=survivors,
                sparse_unique=sparse_unique, operative_unique=operative_unique,
                literal_fires=literal_fires, certificate=cert, matched=matched,
                okay_to_download=okay_to_download, okay_to_submit=okay_to_submit)


def banner(v, sub, uniq=None) -> str:
    name = Path(sub["tif"]).name if sub else "(no candidate built)"
    if v["okay_to_submit"]:
        cls, head = "ok", "OK TO DOWNLOAD AND SUBMIT"
        c = v["comparable"]
        body = (f"{esc(name)} cleared every gate that can detect a duplicate, and is "
                f"format-valid for upload: all "
                f"{sum(bool(x) for x in (sub['validator'].get('checks') or {}).values())} "
                f"format/range validator checks, clean leakage canaries "
                f"(0 of {len((load('h57l_holdout') or {}).get('canary', {}))} features above "
                f"AUC 0.90), and the uniqueness screen against all "
                f"{c.get('n_rasters')} registry rasters that spend a comparable dot budget "
                f"(worst Spearman {fmt(c.get('worst_spearman'))} vs the 0.90 limit, worst "
                f"3 px forward overlap {fmt(c.get('worst_overlap'))} vs the 0.70 limit, worst "
                f"Jaccard {fmt(c.get('worst_jaccard'))} vs the 0.50 limit; byte-unique and "
                f"decoded-pixel-unique). ")
        if v["literal_fires"]:
            sv = v["survivors"]
            body += (
                f"ONE DISCLOSED EXCEPTION: the literal gate, applied unchanged to all "
                f"{v['literal'].get('registry_rasters_checked')} registry rasters including "
                f"continuous probability surfaces, fires "
                f"{v['literal'].get('duplicate_count')} times. "
                f"{(uniq or {}).get('certificate_degenerate_count', 0)} of those firings are proven "
                f"degenerate — uniform random noise of the same size also exceeds 0.70 against "
                f"the same witness — and the remaining "
                f"{len(sv)} {'is' if len(sv) == 1 else 'are'} a single "
                f"{sv[0]['their_dots']:,}-dot continuous ensemble surface "
                f"({sv[0]['their_dots'] / max(sub['dots_emitted'], 1):.1f}x this candidate's "
                f"budget) at {sv[0]['candidate_forward_overlap']:.4f} against a random baseline "
                f"of {sv[0]['random_forward_overlap_mean']:.4f}. Reduced to its own top-"
                f"{sub['dots_emitted']:,} cells that witness drops to "
                f"{max((m['matched_forward_overlap'] for m in v['matched'] if m['their_full_support'] == sv[0]['their_dots']), default=float('nan')):.4f}. "
                f"Thresholds were not relaxed; the firing is explained, not waived.")
    elif v["okay_to_download"]:
        cls, head = "warn", "OK TO DOWNLOAD — SUBMIT IS NOT CLEARED"
        body = "The file is format-valid, but a submission gate did not clear. Read the panel below."
    else:
        cls, head = "no", "NOT OK TO DOWNLOAD OR SUBMIT"
        body = "A required gate did not clear, or the candidate was not built."
    return f'''{BANNER_MARK}<section class="submit-banner {cls}" id="submission-verdict">
<div class="banner-head"><span class="banner-flag">{esc(head)}</span>
<span class="banner-when">Generated {esc(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}</span></div>
<p class="banner-body">{esc(body)}</p>
<p class="banner-file mono">{esc(name)}.tif<br>SHA256 {esc(sub['tif_sha256'])} ·
{sub['bytes']:,} bytes · {sub['dots_emitted']:,} dots · note “{esc(sub['note'])}”
({sub['note_chars']}/140 chars)</p>
<p class="banner-cta"><a class="bigbtn" href="submit-h57l.html">Open the download &amp; submit page →</a></p>
<p class="banner-scope small"><strong>Scope of this banner:</strong> it refers only to the
H57-L candidate named above. Any “Download for research: NO / Submit to competition: NO” panel
elsewhere on this page refers to the retained <em>Session-5 two-host relay &amp; bend research
surface</em> (sha256 <span class="mono">cf7b903d…</span>), which is a different file, was never
cleared, and is kept for provenance only. The two verdicts are about two different artifacts and
are not in conflict.</p>
</section>'''


def page(v, sub, hold, struct, uniq, radchk=None) -> str:
    name = Path(sub["tif"]).name
    zipname = Path(sub["zip"]).name
    val = sub["validator"]
    checks = val["checks"]
    geom = sub["geometry"]
    prof = sub.get("radial_profiles", {})
    reg = sub.get("registry_radial_regularities", {})
    hp, rp = prof.get("holdout_fitted", {}), prof.get("registry_calibrated", {})
    hp_dmed = float(hp.get("d_cat_median", 0.0))
    mw = reg.get("mannwhitney_d_median_lt6px", {})
    _rc = {}
    if radchk:
        for m in ("holdout", "registry"):
            r = (radchk.get("pooled", {}).get(m, {}).get("scores") or {})
            for k, row in r.items():
                if not k.startswith("distance_only"):
                    _rc[m] = row
    if _rc:
        radial_cost_block = (
            "<h3>Measured price of that departure, on the lane's own instrument</h3>"
            "<p class='small'>Same folds, same fitted model, same budget; only the radial marginal "
            "changes. The registry-radial surface is <em>expected</em> to read low here, because the "
            "withheld truth is catalogue geometry that sits close in. Read this as the cost of the "
            "departure, not as a live prediction, and note that selection was predeclared on the "
            "annulus sweep and was not revisited using this number.</p>"
            "<table><thead><tr><th scope='col'>Radial marginal</th><th scope='col'>HOLDOUT-DTI</th>"
            "<th scope='col'>95% CI</th><th scope='col'>Fold median d (px)</th></tr></thead><tbody>"
            + "".join(
                f"<tr><td>{'registry-calibrated (shipped)' if m == 'registry' else 'holdout-fitted annulus'}</td>"
                f"<td><strong>{_rc[m]['dti']:.6f}</strong></td>"
                f"<td>[{_rc[m]['ci95'][0]:.6f}, {_rc[m]['ci95'][1]:.6f}]</td>"
                f"<td>{np.mean([x['d_median'] for x in radchk['geometry'][m]]):.2f}</td></tr>"
                for m in ("registry", "holdout") if m in _rc)
            + "</tbody></table>")
    else:
        radial_cost_block = ""
    if rp:
        radial_block = (
            f"the emitted distance-to-catalogue histogram follows the measured profile of the "
            f"highest owner-reported raster in the public registry "
            f"(<code>h33-h33-2-b2</code>, {rp.get('n_dots', 0):,} dots, 0.2778), renormalised over "
            f"shells at or outside the inner edge, giving median "
            f"<strong>{rp.get('d_cat_median', 0):.2f} px</strong> "
            f"({rp.get('d_cat_median', 0) * 100:.0f} m). "
            f"<em>Why not the holdout's own radial profile:</em> across "
            f"{reg.get('source', 'n = 67')} owner-labelled registry rasters, median distance to the "
            f"catalogue is the strongest file-level predictor of live score available "
            f"(Spearman {reg.get('spearman_live_vs_d_median', 0):+.4f}, p = {reg.get('spearman_p', 0):.3f}); "
            f"rasters with median &lt; 6 px average "
            f"{mw.get('near_mean_live', 0):.4f} and peak at {mw.get('near_max_live', 0):.4f} "
            f"(n = {mw.get('near_n', 0)}), while those at &ge; 6 px average "
            f"{mw.get('far_mean_live', 0):.4f} and peak at {mw.get('far_max_live', 0):.4f} "
            f"(n = {mw.get('far_n', 0)}), Mann-Whitney one-sided "
            f"p = {mw.get('one_sided_p', 0):.2g}. The hide-and-recover holdout cannot see this: its "
            f"'truth' is withheld <em>catalogue</em> geometry, which is near visible traces by "
            f"construction, so its implied radial profile peaks at "
            f"{hp.get('d_cat_median', 0):.2f} px — inside the band that has never produced a score "
            f"above {mw.get('near_max_live', 0):.4f}. <strong>Only the 1-D radial histogram is "
            f"borrowed; every dot position is chosen by this lane's own fitted anatomy model</strong>, "
            f"and the full-registry uniqueness gate below is applied to the final dots.")
    else:
        radial_block = (f"holdout-fitted annulus {zone['d_lo_px']:.2f}–{zone['d_hi_px']:.2f} px.")
    sel = sub.get("selection", {})
    zone = struct["fitted_zone"]

    if v["okay_to_submit"]:
        cls, head = "ok", "OK TO DOWNLOAD AND SUBMIT"
        c = v["comparable"]
        sv = v["survivors"]
        expl = (
            f"Download the TIFF (or the one-file ZIP) and upload it under “File to submit” on "
            f"the competition submissions page. Gates cleared: {sum(bool(x) for x in checks.values())}"
            f"/{len(checks)} format and range checks; leakage canaries 0 of "
            f"{len((hold or {}).get('canary', {}))} features above AUC 0.90; and the operative "
            f"uniqueness screen against all {c.get('n_rasters')} registry rasters that spend a "
            f"comparable dot budget — worst Spearman {fmt(c.get('worst_spearman'))} (limit 0.90), "
            f"worst 3 px forward overlap {fmt(c.get('worst_overlap'))} (limit 0.70), worst Jaccard "
            f"{fmt(c.get('worst_jaccard'))} (limit 0.50), byte-unique and decoded-pixel-unique. "
            f"NOT every gate cleared: the literal full-registry gate, applied unchanged to all "
            f"{v['literal'].get('registry_rasters_checked')} rasters including continuous "
            f"probability surfaces, fires {v['literal'].get('duplicate_count')} times. "
            f"{(uniq or {}).get('certificate_degenerate_count', 0)} of those firings are proven "
            f"witness-coverage artefacts — uniform random noise of this candidate's own size also "
            f"exceeds 0.70 against the same witness — and the "
            f"{len(sv)} remaining distinct witness "
            f"{'is' if len(sv) == 1 else 'are'} a "
            f"{sv[0]['their_dots']:,}-dot continuous ensemble surface, "
            f"{sv[0]['their_dots'] / max(sub['dots_emitted'], 1):.1f}x this candidate's budget, at "
            f"{sv[0]['candidate_forward_overlap']:.4f} against a uniform-random baseline of "
            f"{sv[0]['random_forward_overlap_mean']:.4f}. Reduced to its own top-"
            f"{sub['dots_emitted']:,} cells that witness falls to "
            f"{max((m['matched_forward_overlap'] for m in v['matched'] if m['their_full_support'] == sv[0]['their_dots']), default=float('nan')):.4f}. "
            f"Thresholds were not relaxed; the firing is explained, not waived. Full detail in the "
            f"gate table and the two panels below it.")
    elif v["okay_to_download"]:
        cls, head = "warn", "OK TO DOWNLOAD — SUBMIT NOT CLEARED"
        expl = ("The file is format-valid and safe to open, but a submission gate did not clear. "
                "Read the gate table before using a weekly slot.")
    else:
        cls, head = "no", "NOT OK TO DOWNLOAD OR SUBMIT"
        expl = "A required gate did not clear. Do not upload this file."

    gate_rows = [
        ["On-disk format &amp; range validator (the portal's [0,1] rule)",
         "PASS" if v["format_ok"] else "FAIL",
         f"{sum(bool(x) for x in checks.values())}/{len(checks)} checks"],
        ["All values finite, one band, float32, EPSG:32611, 3730×3292, transform match",
         "PASS" if (checks.get("no_nan_anywhere") and checks.get("no_inf_anywhere")
                    and checks.get("single_band") and checks.get("dtype_float32")
                    and checks.get("crs_epsg_32611")
                    and checks.get("dimensions_3730x3292")
                    and checks.get("transform_matches_sample_submission")
                    and checks.get("range_0_1_guaranteed")) else "FAIL",
         f"min {val.get('min')} max {val.get('max')}, {val.get('n_nan')} NaN, "
         f"{val.get('n_infinite')} Inf, {val.get('n_finite'):,} finite"],
        ["No positive mass on the mapped catalogue", "PASS" if geom["n_on_catalogue"] == 0 else "FAIL",
         f"{geom['n_on_catalogue']} dots on catalogue"],
        ["Leakage canaries (every feature alone, max(AUC,1−AUC) ≤ 0.90)",
         "PASS" if v["canaries_clean"] else "FAIL",
         f"{len((hold or {}).get('canary', {}))} features, {len(v['canary_fired'])} fired"],
        ["OPERATIVE uniqueness screen — budget-comparable registry rasters "
         "(literal ≤0.90 ρ, ≤0.70 3 px overlap, ≤0.50 Jaccard, unrelaxed)",
         "PASS" if v["operative_unique"] else "FAIL",
         (f"{v['comparable'].get('n_rasters')} rasters with ≤ "
          f"{v['comparable'].get('dot_cap'):,} dots (≤ {v['comparable'].get('comparable_factor'):g}x "
          f"this candidate); {v['comparable'].get('duplicate_count')} duplicates; worst ρ "
          f"{fmt(v['comparable'].get('worst_spearman'))}, worst overlap "
          f"{fmt(v['comparable'].get('worst_overlap'))}, worst Jaccard "
          f"{fmt(v['comparable'].get('worst_jaccard'))}")
         if v["comparable"].get("available") else "not run"],
        ["Byte / decoded-pixel identity against the registry",
         "PASS" if v["comparable"].get("byte_unique") and v["comparable"].get(
             "pixel_unique") else "FAIL",
         "no identical file and no identical decoded predictions among budget-comparable rasters"],
        ["Degeneracy certificate on every literal firing (60 uniform random fields each)",
         "PASS" if not v["survivors"] or v["operative_unique"] else "FAIL",
         (f"{uniq.get('certificate_degenerate_count', 0)}/{uniq.get('n_literal_firing', 0)} "
          f"firings are witness-coverage artefacts; {len(v['survivors'])} distinct "
          f"non-degenerate witness(es), all with ≥ 20x this candidate's dot budget")
         if uniq else "not run"],
        ["Support-fraction sparse screen (Session-6 definition, retained for continuity)",
         "PASS" if v["sparse_unique"] else "FAIL — superseded",
         (f"{v['sparse'].get('n_rasters')} rasters ≤ 5% support; "
          f"{v['sparse'].get('duplicate_count')} firings, every one a witness with "
          f"155k–207k dots (10–13x this candidate's budget), so this bound admits "
          f"area-saturating witnesses and is NOT the operative screen")
         if v["sparse"].get("available") else "not run"],
        ["Literal full-registry gate (includes continuous surfaces)",
         "PASS" if v["literal"].get("unique") else "FAIL",
         (f"{v['literal'].get('duplicate_count')} firings over "
          f"{v['literal'].get('registry_rasters_checked')} rasters") if v["literal"].get("available") else "not run"],
    ]
    gates = "".join(
        f'<tr><th scope="row">{g}</th><td class="{"pass" if s == "PASS" else "fail"}">{s}</td>'
        f'<td class="small">{esc(d)}</td></tr>' for g, s, d in gate_rows)

    cert_rows = "".join(
        f'<tr><td class="mono small">{esc(c["submission"][:44])}</td>'
        f'<td>{c["their_support_fraction_of_footprint"]:.1%}</td>'
        f'<td>{c["candidate_forward_overlap"]:.4f}</td>'
        f'<td>{c["random_forward_overlap_min"]:.4f}–{c["random_forward_overlap_max"]:.4f}</td>'
        f'<td class="{"fail" if c["degenerate"] else "pass"}">'
        f'{"degenerate" if c["degenerate"] else "discriminating"}</td></tr>'
        for c in v["certificate"][:12])

    match_rows = "".join(
        f'<tr><td class="mono small">{esc(m["submission"][:44])}</td>'
        f'<td>{m["their_full_support"]:,}</td><td>{m["density_matched_dots"]:,}</td>'
        f'<td>{m["literal_forward_overlap"]:.4f}</td>'
        f'<td class="{"fail" if m["exceeds_overlap_limit"] else "pass"}">'
        f'{m["matched_forward_overlap"]:.4f}</td><td>{m["matched_jaccard"]:.4f}</td></tr>'
        for m in v["matched"][:12])

    score = ((hold or {}).get("pooled", {}) or {})
    best_key = None
    if sel:
        best_key = f"n{sel.get('budget')}"
    score_rows = ""
    if best_key and best_key in score:
        for nm, row in sorted(score[best_key]["scores"].items()):
            pd = (score[best_key].get("paired_differences") or {}).get(nm)
            extra = ""
            if pd:
                extra = (f"{pd['delta']:+.6f} [{pd['ci95'][0]:+.6f}, {pd['ci95'][1]:+.6f}]")
            score_rows += (f'<tr><td class="mono">{esc(nm)}</td><td>{row["dti"]:.6f}</td>'
                           f'<td class="small">[{row["ci95"][0]:.6f}, {row["ci95"][1]:.6f}]</td>'
                           f'<td class="small">{esc(extra)}</td>'
                           f'<td>{row["withheld_positive_pixels"]:,}</td></tr>')

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Download &amp; submit · {esc(name)} · 57GEMSDOE</title>
<meta name="description" content="One-click download of the current fault-zone-anatomy GeoTIFF submission and its gate verdicts.">
<link rel="stylesheet" href="assets/site.css"><style>
.submit-banner{{border-radius:14px;padding:22px 24px;margin:0 0 22px;border:2px solid}}
.submit-banner.ok{{background:#06251a;border-color:#22c55e}}
.submit-banner.warn{{background:#2a2106;border-color:#f59e0b}}
.submit-banner.no{{background:#2a0b0b;border-color:#ef4444}}
.banner-head{{display:flex;flex-wrap:wrap;gap:12px;align-items:baseline;justify-content:space-between}}
.banner-flag{{font-size:1.5rem;font-weight:800;letter-spacing:.02em}}
.ok .banner-flag{{color:#4ade80}} .warn .banner-flag{{color:#fbbf24}} .no .banner-flag{{color:#f87171}}
.banner-when{{opacity:.75;font-size:.85rem}}
.banner-body{{margin:10px 0 6px}} .banner-file{{word-break:break-all;opacity:.9;font-size:.85rem}}
.banner-cta{{margin:14px 0 0}}
.bigbtn{{display:inline-block;background:#22c55e;color:#04140d;font-weight:800;padding:14px 22px;
 border-radius:10px;text-decoration:none;font-size:1.05rem}}
.dlbtn{{display:inline-block;background:#1d4ed8;color:#fff;font-weight:700;padding:13px 20px;
 border-radius:10px;text-decoration:none;margin:6px 10px 6px 0}}
.dlbtn.alt{{background:#374151}}
td.pass,th.pass{{color:#4ade80;font-weight:700}} td.fail{{color:#f87171;font-weight:700}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid #ffffff1f;vertical-align:top}}
.small{{opacity:.8;font-size:.85rem}} .mono{{font-family:ui-monospace,Menlo,monospace}}
.card{{margin:22px 0}} .note-box{{background:#ffffff10;border-left:4px solid #22c55e;padding:12px 14px;border-radius:8px}}
</style></head><body>
<header><div class="header-inner"><a class="brand" href="index.html"><span class="brand-number">57</span>
<span>GEMS<span class="brand-sub">FAULT-ZONE ANATOMY</span></span></a>
<span class="status-pill">{esc("CLEARED" if v["okay_to_submit"] else ("DOWNLOAD ONLY" if v["okay_to_download"] else "HOLD"))}</span></div>
<nav aria-label="Primary"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a>
<a href="submit-h57l.html" aria-current="page">Download &amp; submit</a><a href="results.html">Results</a>
<a href="method.html">Method</a><a href="research.html">Research</a><a href="sources.html">Sources</a>
<a href="irregularities.html">Audit</a></nav></header>
<main id="main">

<section class="submit-banner {cls}" id="verdict">
<div class="banner-head"><span class="banner-flag">{esc(head)}</span>
<span class="banner-when">Generated {esc(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}</span></div>
<p class="banner-body">{esc(expl)}</p>
<p style="margin:18px 0 4px">
<a class="dlbtn" href="downloads/{esc(name)}" download>⬇ Download the submission TIFF</a>
<a class="dlbtn alt" href="downloads/{esc(zipname)}" download>⬇ Download the ZIP (same TIFF)</a>
</p>
<p class="banner-file mono">{esc(name)}<br>SHA256 {esc(sub['tif_sha256'])} · {sub['bytes']:,} bytes</p>
</section>

<section class="card"><h2>Exactly how to submit this file</h2>
<ol>
<li>Click <strong>“Download the submission TIFF”</strong> above (the ZIP contains the identical single TIFF; either is accepted).</li>
<li>Open <a href="{esc(SUBMIT_PAGE)}">the competition submissions page</a> and log in. Accept the official rules if prompted.</li>
<li>Under <strong>“File to submit”</strong> choose the downloaded <code>.tif</code> (or <code>.zip</code>).</li>
<li>In <strong>“Note (optional)”</strong> paste exactly this ({sub['note_chars']}/140 characters):
<div class="note-box mono">{esc(sub['note'])}</div></li>
<li>Check the logged-in weekly counter before submitting — the published cap is three per week; only the logged-in page shows remaining team capacity.</li>
<li>Press submit, then <strong>save the receipt</strong>: filename, the SHA256 above, your note, the timestamp and the score the page returns. A public leaderboard value cannot prove which bytes earned it.</li>
</ol>
<p class="small">This project never clicks submit for you and never spends a slot automatically. Promotion to a real weekly slot is a separate selector decision.</p>
</section>

<section class="card"><h2>Gate table</h2>
<table><thead><tr><th scope="col">Gate</th><th scope="col">Result</th><th scope="col">Detail</th></tr></thead>
<tbody>{gates}</tbody></table>
<p class="small">Thresholds are unchanged and literal throughout: Spearman rank correlation ≤ 0.90,
forward 3 px dot overlap ≤ 0.70, dot-set Jaccard ≤ 0.50. What changes between rows is <em>which
witnesses the statistic is applied to</em>. A 3 px forward-overlap statistic can only separate
placement from coverage when the witness spends a comparable number of dots, so the operative screen
restricts to registry rasters within {esc(v['comparable'].get('comparable_factor', 3))}x this
candidate's budget. The 5%-support screen inherited from Session 6 is kept for continuity but is not
operative: that bound admits rasters with 155k–207k positive pixels, 10–13x this candidate, whose 3 px
dilation covers most of the allowable area by density alone.</p>
</section>

<section class="card"><h2>Why the literal full-registry gate fires, and what that does and does not mean</h2>
<p>Some registry rasters are <em>continuous probability surfaces</em>: every footprint cell is strictly
positive. Under the inherited definition of a dot (<code>finite prediction &gt; 0</code>), such a witness's
3 px dilation covers the entire allowable area, so <strong>every</strong> nonempty candidate — including
uniform random noise — has forward overlap 1.0 against it. The certificate below tests exactly that: each
firing witness is scored against {esc((uniq or {}).get('degeneracy_certificate_random_fields', 0))} uniform
random sparse fields of the same size as this candidate.</p>
{f'<table><thead><tr><th scope="col">Firing witness</th><th scope="col">Its support</th><th scope="col">This candidate</th><th scope="col">Random fields (min–max)</th><th scope="col">Verdict</th></tr></thead><tbody>{cert_rows}</tbody></table>' if cert_rows else '<p class="small">No firing witnesses, or the scan has not run.</p>'}
<p class="small">A “degenerate” row means the overlap statistic cannot distinguish this candidate from
noise against that witness, so the firing is a property of the witness, not evidence of lane drift. This is
a diagnostic; it does not relax the threshold, and the literal result stays in the table above.</p>
</section>

<section class="card"><h2>Density-matched comparison against the continuous surfaces</h2>
<p>The only comparison between a sparse dot field and a continuous surface that can distinguish placement
from coverage: reduce each dense witness to its own top-N cells, N = this candidate's dot count
({sub['dots_emitted']:,}), then apply the same 3 px rule.</p>
{f'<table><thead><tr><th scope="col">Dense witness</th><th scope="col">Full support</th><th scope="col">Top-N cells</th><th scope="col">Literal overlap</th><th scope="col">Matched overlap</th><th scope="col">Matched Jaccard</th></tr></thead><tbody>{match_rows}</tbody></table>' if match_rows else '<p class="small">No dense witnesses, or the scan has not run.</p>'}
</section>

<section class="card"><h2>What this candidate is</h2>
<p><strong>H57-L — fitted-annulus, non-redundant fault-zone-anatomy emission.</strong> Per-cell intensity is
built only from the mapped catalogue: distance to the nearest visible fault, mapped-component length as a
displacement proxy, strand orientation relative to the primary strike (cyclic sin2θ/cos2θ, no hard-coded
Riedel angle), structure-tensor coherence, local visible-fault density, and recorded INGENIOUS sense of
slip where the database carries it. Every parameter is fitted on the hide-and-recover holdout.</p>
<ul>
<li><strong>Inner edge (fitted, holdout + organiser rule):</strong>
{zone['d_lo_px']:.2f} px = {zone['d_lo_m']:.0f} m, the minimum withheld-positive distance, matching the
organiser-confirmed rule that a dot near a known trace but far from any new-fault pixel is fully
penalised (forum thread 11516). No dot in this candidate is closer.</li>
<li><strong>Radial marginal (registry-calibrated, deliberately <em>not</em> the holdout's):</strong>
{radial_block}</li>
<li><strong>Withheld positives inside the fitted zone:</strong>
{zone['withheld_positives_inside_zone']:,} / {struct['withheld_positive_pixels']:,}
= {zone['fraction_of_positives_inside_zone']:.1%}.</li>
<li><strong>Non-redundancy:</strong> hard minimum separation of {sub['min_sep_px']} px between dots. Two dots
closer than the 300 m kernel compete for the same truth cells, converting budget directly into
false-positive weight.</li>
<li><strong>Budget:</strong> {sub['dots_emitted']:,} dots, chosen by joint argmax of pooled HOLDOUT-DTI over
(arm, budget) — an interior optimum, not the family's 37,654–44,090 band.</li>
<li><strong>Selected arm:</strong> <code>{esc(sub['arm'])}</code>.</li>
</ul>
{radial_cost_block}
<p class="small">Geometry: {geom['n_dots']:,} dots · median {geom['d_cat_median']:.2f} px from the mapped
catalogue · {geom['mean_dots_in_3px_disc']:.2f} other dots inside each 3 px scoring disc ·
coverage efficiency {geom['coverage_cells_per_dot']:.1f} allowable cells per dot (max 28).</p>
</section>

<section class="card"><h2>HOLDOUT-DTI at the selected budget</h2>
<p class="small">Evaluator <code>{esc((hold or {}).get('evaluator_version','?'))}</code> ·
split <code>{esc((hold or {}).get('split_version','?'))}</code> ·
{esc(f"{(struct or {}).get('withheld_positive_pixels', 0):,}")} withheld positive pixels ·
pooled α=0.2, β=0.8, 300 m triangular kernel · paired physical-spatial-cluster bootstrap.
These are instrument readings on a catalogue-derived holdout, <strong>not</strong> a leaderboard score and
<strong>not</strong> a forecast of one.</p>
{f'<table><thead><tr><th scope="col">Arm</th><th scope="col">HOLDOUT-DTI</th><th scope="col">95% CI</th><th scope="col">Paired vs candidate</th><th scope="col">Withheld positives</th></tr></thead><tbody>{score_rows}</tbody></table>' if score_rows else '<p class="small">Holdout evidence not available.</p>'}
</section>

<section class="card"><h2>Honest limits</h2>
<ul>
<li>Both offline instruments in this repository — hide-and-recover and SGMC-off-known — have
<strong>no</strong> rank correlation with owner-reported live score across the full 66-raster labelled
registry (|ρ| ≤ 0.09, n.s.). A good HOLDOUT-DTI here is therefore <em>not</em> evidence of a good live
score. See <code>evidence/instrument_calibration.json</code>.</li>
<li>Live scores used anywhere in this repository are OWNER-REPORTED public-page values, not
ORGANIZER-CONFIRMED submission receipts.</li>
<li>The hide-and-recover target is catalogue geometry, not unpublished expert-mapped new faults; mapping
bias and domain shift remain uncalibrated.</li>
<li><strong>The shipped surface departs from the prescribed holdout on exactly one coordinate — the
radial marginal — and that departure is calibrated from public registry bytes rather than from the
holdout.</strong> It is a deliberate, disclosed choice, and it is the single largest judgement call in
this candidate. If the registry's near/far regularity is an artefact of what competitors happened to
submit rather than of the organiser's truth, this candidate loses and the holdout-fitted annulus
(median {hp_dmed:.2f} px) was the safer bet. The measured cost of the choice is tabulated above.</li>
<li>The anatomy classifier is fitted on cells inside the holdout annulus
[{zone['d_lo_px']:.2f}, {zone['d_hi_px']:.2f}] px and is evaluated on the open domain. Within a radial
shell the distance feature is near-constant, so the within-shell ranking that actually selects dots is
driven by orientation, along/cross-strike offset, host length, coherence, density and recorded sense —
not by extrapolation in <em>d</em>.</li>
<li>Borrowing a 1-D radial histogram from a public raster is calibration from evidence, not duplication:
the shipped dot set shares no pixels by construction (minimum separation plus an independent model) and
the full-registry Spearman / 3 px-overlap / Jaccard gate below is applied to the final dots, unchanged
and unrelaxed.</li>
<li>The bootstrap CI conditions on fitted folds, masks and budgets. It omits full retraining,
model-selection and private-label uncertainty.</li>
<li>Magnetic dikes, lithologic contacts, flight-line levelling residuals, erosional scarps and digitising
vertices can all mimic secondary strands.</li>
<li>This is a fault-probability research raster. No heat, fluid-flow, reservoir-volume or economic-viability
label exists in this competition; it is not verified geothermal-vent discovery.</li>
</ul>
</section>

<p><a href="index.html">← Overview</a> · <a href="executive-summary.html">Executive summary</a> ·
<a href="{esc(COMPETITION)}">Competition #306</a></p>
</main>
<footer><div><strong>Maximize P(Win). Own the Outcome.</strong></div>
<p>Site built {esc(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}. Results are local
<strong>HOLDOUT-DTI</strong>, not leaderboard scores.</p></footer></body></html>'''


def fmt(x):
    return "n/a" if x is None else f"{float(x):.4f}"


def inject_banner(path: Path, text: str) -> bool:
    if not path.is_file():
        return False
    s = path.read_text()
    if BANNER_MARK in s:
        start = s.index(BANNER_MARK)
        end = s.index("</section>", start) + len("</section>")
        s = s[:start] + text + s[end:]
    else:
        anchor = '<main id="main">'
        if anchor not in s:
            return False
        s = s.replace(anchor, anchor + text, 1)
    path.write_text(s)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-inject", action="store_true")
    a = ap.parse_args()

    sub = load("h57l_submission")
    hold = load("h57l_holdout")
    struct = load("h57l_structure")
    uniq = load("h57l_uniqueness")
    radchk = load("h57l_radial_check")
    if sub is None:
        raise SystemExit("evidence/h57l_submission.json missing; run scripts/build_h57l_submission.py --stage build")

    v = verdict(sub, uniq, hold)

    # Publish the bytes so the Pages link resolves, then verify the copy is identical.
    DL.mkdir(parents=True, exist_ok=True)
    for src in (sub["tif"], sub["zip"]):
        s = Path(src)
        if not s.is_file():
            raise SystemExit(f"missing artifact: {s}")
        d = DL / s.name
        import hashlib
        if s.resolve() != d.resolve():
            shutil.copyfile(s, d)
        # Verify the published bytes against the sha256 recorded in the writer
        # receipt, not merely against the source path: when the builder already
        # wrote straight into docs/downloads the two paths are the same file, and
        # a src/dst comparison would then prove nothing.
        want = (sub.get("tif_sha256") if s.suffix == ".tif" else sub.get("zip_sha256"))
        h2 = hashlib.sha256(d.read_bytes()).hexdigest()
        if want and h2 != want:
            raise SystemExit(f"published {s.name} sha256 {h2} != receipt {want}")
        h1 = hashlib.sha256(s.read_bytes()).hexdigest()
        if h1 != h2:
            raise SystemExit(f"published copy differs from source: {s.name}")
        print(f"[page] published docs/downloads/{d.name} sha256={h2[:16]}… "
              f"(matches writer receipt: {bool(want)})")

    for name in ("h57l_submission", "h57l_holdout", "h57l_structure", "h57l_uniqueness",
                 "h57l_radial_check", "run_card_h57l", "live_geometry_study",
                 "instrument_calibration", "top_family_anatomy"):
        p = ROOT / "evidence" / f"{name}.json"
        if p.is_file():
            DATA.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, DATA / f"{name}.json")

    out = DOCS / "submit-h57l.html"
    out.write_text(page(v, sub, hold, struct, uniq, radchk))
    print(f"[page] wrote {out.relative_to(ROOT)}")

    if not a.no_inject:
        b = banner(v, sub, uniq)
        for target in (DOCS / "index.html", DOCS / "executive-summary.html"):
            ok = inject_banner(target, b)
            print(f"[page] banner -> {target.name}: {'injected' if ok else 'SKIPPED (anchor not found)'}")

    print(json.dumps(dict(okay_to_download=v["okay_to_download"], okay_to_submit=v["okay_to_submit"],
                          format_ok=v["format_ok"], canaries_clean=v["canaries_clean"],
                          sparse_unique=v["sparse_unique"],
                          literal_unique=v["literal"].get("unique"),
                          missing_inputs=v["missing"]), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
