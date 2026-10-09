# GEMSDOE57 — fault-zone anatomy lane

DrivenData **GEMS Prize** (competition 306): predict per-pixel fault probability for the
whole GeoDAWN study area (Nevada, UTM 11N / EPSG:32611, 100 m). The hidden labels are
**new expert-mapped faults not in USGS/INGENIOUS** — splays and parallel strands count.
Metric: distance-weighted Tversky, `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`, 300 m
credit radius; FP cheap, FN expensive. Leaderboard high 0.3774; the incumbent to beat is
0.2778 (and the user's stated target is 0.3195).

**→ [Download the submission GeoTIFF](https://buffedlizard55-lab.github.io/57GEMSDOE/)**
(the button is the first thing on the site) ·
[Executive summary — exactly how to submit](https://buffedlizard55-lab.github.io/57GEMSDOE/executive-summary.html)
· [Research & run card](https://buffedlizard55-lab.github.io/57GEMSDOE/research.html)
· [Sources](https://buffedlizard55-lab.github.io/57GEMSDOE/sources.html)

## What this session produced

| Deliverable | Where |
|---|---|
| Submission GeoTIFF (60,000 dots, 0 on known faults, validator PASS) | `docs/downloads/gems57-faultzone-anatomy-60000px-20261009T054251Z.tif` |
| sha256 of the submission | `a08650cadb9a1baf36f00a87bbbd80e789ba01f45c9d57936865a94174cc9cd8` |
| Methodology note (≤140 ch) | "fault-zone anatomy: fitted damage-zone halo around USGS+INGENIOUS faults; 60000 dots, 0 on known faults; HOLDOUT-DTI 0.0580 [0.0507,0.0663]" |
| HOLDOUT-DTI @ 60k (evaluator `gems52-pooled-hide-v1`, 38,339 withheld positives, 95% CI) | **0.0580 [0.0507, 0.0663]** — `evidence/exp2_holdout.json` |
| SGMC-truth proxy DTI @ 60k / 120k (79,025 real off-catalogue fault px) | 0.0457 / 0.0650 — `evidence/exp3_build.json` |
| Leakage canary (max single-feature AUC, threshold 0.90) | 0.6538 → no leakage |
| Registry drift check (663 rasters) | max |Spearman| 0.6271 < 0.90; 0 bidirectional duplicates; sha256 unique → **UNIQUE** — `evidence/uniqueness.json` |
| Run card (hypothesis, mechanism, mimic process, verdict) | `evidence/run_card.json` |
| Ranked hypotheses H1–H5 | `docs/research/hypotheses.md` |
| Reproducible experiments | `scripts/explore_zone2.py` (Exp 1b), `scripts/run_holdout.py` (Exp 2), `scripts/build_submission.py` (Exp 3) |

**Verdict: negative as a standalone score-beater.** The lane is validated (beats its own
controls on the brief's holdout: 0.0580 vs random 0.0492 and uniform-halo 0.0117 at 60k),
unique, and non-leaking — but on the SGMC-truth instrument it trails the incumbents 2–3×
(0.0457 vs 0.0931–0.1450), so it is not expected to beat the incumbent live score. **No
submission slot should be spent on this file**; promotion is a separate selector step.
The submission is generated, validated and downloadable, and the negative result is the
deliverable. Next work (ranked): H2 zone-gated geophysical corroboration, H3 tip-relay
targeting, a 120k-budget variant, H4 slip-rate-weighted width, H5 USGS vector sense join
(data-blocked).

## Repository layout

```
src/gems57/            vendored GEMSDOE52 template (metric/holdout/grid/gates/writer/
                       emit/evaluate_holdout/spatial — unmodified) + lane modules
                       faultzone.py (segment linking, halo features) and fit.py
                       (fitted intensity, SGMC near-band extension)
scripts/               prepare_data.py (sha256 pin verification), download_competition_data.sh,
                       explore_zone.py (Exp 1), explore_zone2.py (Exp 1b), run_holdout.py
                       (Exp 2), calibrate_registry.py, build_submission.py (Exp 3),
                       check_uniqueness.py, build_site.py (this site)
data/official/         labels.tif, existing_faults.tif, sample_submission.tif (committed,
                       sha256-pinned); training_features.tif (gitignored, 419 MB —
                       fetched+verified by scripts/prepare_data.py)
data/external/         SGMC rasters, INGENIOUS qfaults CSVs + receipts (committed, pinned)
evidence/              exp1/exp1b/exp2/exp3/calibration/uniqueness JSONs + run_card.json
                       (committed); .npz build products (gitignored)
docs/                  GitHub Pages site + downloads/ (the submission .tif/.zip/receipt)
tests/                 metric worked example, format gate, faultzone linking
```

## Reproduce

```bash
python scripts/prepare_data.py                 # verify every sha256 pin
python scripts/explore_zone2.py                # Exp 1b: measure the zone anatomy
python scripts/run_holdout.py                  # Exp 2: HOLDOUT-DTI arms × budgets
python scripts/calibrate_registry.py           # calibrate both instruments vs 11 rasters
python scripts/build_submission.py             # Exp 3: rebuild the submission (deterministic)
python scripts/check_uniqueness.py             # drift check vs 663 registry rasters
python scripts/build_site.py                   # rebuild docs/
python -m pytest tests/ -q                     # sanity tests
```

Environment: Python 3.11 with rasterio, numpy, scipy, scikit-learn, pandas
(`/home/user/venv/bin/python` in the research sandbox). The sandbox has 3 GB RAM —
the scripts are written for it (halo-restricted arrays, int32 segment labels,
`gc.collect()` between folds).

---

## Standing starting point — the original task prompt

The full prompt this repository was created from, kept verbatim as the standing
starting point for future sessions:

> # GEMSDOE57 — session brief
>
> ## 1. Highest urgency: MUST GENERATE A UNIQUE TIF SUBMISSION
>
> I need a new submission file for the DrivenData GEMS prize challenge generated and ready
> to upload — one that stands a real chance of scoring higher than my current best
> submission on the leaderboard. My best so far is **0.2778**, and the highest score on
> the leaderboard right now is **0.3195**, so the new file needs to beat that to be worth
> submitting. The submission must be **unique** — it must not be a copy of any previous
> submission I've made (copying is only okay for learning).
>
> The competition is DrivenData competition 306, "GEMS — Geothermal Energy Mondiale
> (something)" — the GeoDAWN fault-prediction challenge. The goal: predict where faults
> are across the study area in Nevada (UTM zone 11N, EPSG:32611, 100 m pixels) using the
> provided training data. You predict per-pixel fault probability; the hidden test set
> is new expert-mapped faults that are NOT in the USGS or INGENIOUS fault databases.
> Organizers confirmed: "a new fault is defined as any fault pixel that is not already
> captured by USGS/INGENIOUS. This includes newly mapped geometry of an existing fault
> system (e.g., splays and parallel strands count)."
>
> The metric is distance-weighted Tversky: `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`
> where weights decay linearly to zero at 300 m (3 pixels). FP is cheap (0.2), FN is
> expensive (0.8) — so missing a real fault hurts 4× more than a false alarm.
>
> **Submission format (must pass validation):** single-band 32-bit float GeoTIFF,
> EPSG:32611, 100 m resolution, same bounds/geotransform as the training data, values in
> [0,1], no NaN inside the footprint, null/NaN outside bounds. Unique filename + a short
> note (≤140 chars).
>
> ## 2. Deliverables
>
> 1. **A unique submission .tif**, easy to download from the GitHub Pages site.
> 2. It must pass validation (see above).
> 3. An **"Executive summary" subpage** on the site explaining exactly how to make a
>    submission into the contest.
> 4. The full prompt (this message) in the repo README as the standing starting point.
> 5. A clean GitHub Pages site (`docs/`) with official verified links as sources.
>
> ## 3. Working style
>
> - Work autonomously, but verify your work line by line. No hallucinations.
> - Flag any irregularities for review.
> - Use a 3-pass workflow: (1) implement + verify it works, (2) bug/edge-case review,
>   (3) re-check against the original request.
> - Create a PR and merge it to main when done. Suggest remaining work/limitations.
>
> ## 4. Parallel-run protocol (critical)
>
> Multiple sessions are running from this same prompt in parallel. Before implementing,
> check the registry of prediction rasters from other sessions (`/home/user/registry/`).
> If your raster's rank-correlation with any registry raster exceeds [0.90], or more than
> [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into
> another lane: log it as a duplicate and stop. Check this on the surface before placement
> AND on the final dots.
>
> ## 5. Lane assignment: fault-zone anatomy
>
> Your lane is **fault-zone anatomy** — study the shear-zone damage halo around the known
> USGS/INGENIOUS faults (Tchalenko 1970; Schreurs 2003; Savage & Brodsky 2011). The
> hypothesis: new expert-mapped faults cluster as secondary strands in the damage zones of
> known faults.
>
> Label every number you report as one of: **HOLDOUT-DTI** (state the evaluator version,
> the number of withheld positives, and a 95% CI) or **ORGANIZER-CONFIRMED**.
>
> Leakage canary: if a single feature alone achieves holdout AUC > 0.90, that feature is
> leaking the answer — do not use it.
>
> End the session with one JSON run card: hypothesis; mechanism; the named non-fault
> process that could mimic it; holdout DTI + CI; correlation/overlap vs registry;
> raster sha256; validator output; submission name + ≤140-char note; verdict
> promote/negative. Negative results are deliverables.
>
> ## 6. Budget
>
> Stop after 3 experiments or 2 hours, whichever comes first. Promotion to a real
> submission slot is a separate selector step — do not pick submissions for the real
> slots yourself.
>
> ## 7. Before implementing: candidate hypotheses
>
> Generate 3–5 candidate geological hypotheses we haven't tried yet (layers, physical
> signature, why it catches faults missing from USGS/INGENIOUS, how it differs), ranked
> by expected DTI improvement and implementation cost. Validate the top candidate on our
> spatially-blocked holdout set before touching a weekly submission slot — do not spend a
> submission slot on an idea that hasn't beaten the current holdout best.
>
> ## 8. Constraints
>
> - MUST generate a UNIQUE TIF submission; never copy a previous submission (copying only
>   OK for learning).
> - Submission values in [0,1]; the user got "Predicted values must be in range [0, 1]" —
>   fix the cause in the writer (clip, NaN only outside footprint, validate before
>   packaging).
> - No DrivenData auth → cannot download from the data page.
> - Only free, publicly available, official/verified external data sources; provide
>   links for manual review.
> - No hallucinations; verify line by line; flag irregularities.
> - Budget cap: 3 experiments or 2 hours per session; promotion to real slot is a
>   separate selector step.
