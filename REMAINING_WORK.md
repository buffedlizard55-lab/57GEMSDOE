# Current status and remaining work — 2026-10-10

## Decision first

**H57-B remains HOLD.** It is a fault-zone-anatomy hypothesis tested on the repository's buffered whole-branch hide-and-recover instrument. The original preregistered contrast is non-comparable because candidate and control emitted different dot counts. A later matched-mass replay is a post-hoc sensitivity, not confirmation. The in-memory final-dot map failed the literal registry-overlap rule. **No H57-B TIF was generated, format-validated, cleared, downloaded, or submitted. No weekly slot was selected.**

The remaining experiment budget is exhausted. Do not run another model/feature/hyperparameter experiment, select a weekly slot, or generate a TIF under the current HOLD. This file records status and limitations; it is not authorization to continue experiments.

## H57-B evidence

All score-like values below are **HOLDOUT-DTI** from evaluator `gems57-buffered-whole-branch-pooled-v2.0`, with 22,276 withheld positives and paired 20 km spatial-block 95% confidence intervals. These are local measurements on withheld mapped branches, **not live scores or leaderboard projections**.

### Preregistered 10,000-per-cell run — non-comparable

| Arm | HOLDOUT-DTI | 95% CI | Emitted dots |
|---|---:|---:|---:|
| H57-B tip-distance feature | 0.1882084 | [0.1760057, 0.2014529] | 71,191 |
| `no_side` control | 0.1303988 | [0.1188650, 0.1419912] | 80,000 |

Counts differed in four of eight cells. The preregistered arm comparison therefore cannot identify a causal feature gain and cannot promote. Do not interpret the nominal difference as confirmatory.

### Matched-mass replay — post-hoc sensitivity only

The later replay used a common 6,772-per-cell cap selected after the initial run was observed. Candidate HOLDOUT-DTI was **0.1712803** [0.1585123, 0.1843726], versus `no_side` **0.1103187** [0.0994158, 0.1222397]. The paired difference was **+0.0609616** [ +0.0520292, +0.0703759 ]. This favorable sensitivity is conditional on a post-hoc cap; the interval does not represent cap-selection uncertainty. It is not a confirmatory result and does not repair the preregistered comparison.

The maximum single-feature discriminative AUC was 0.8392, below the 0.90 leakage screen. This is the canary result for the tested visible-catalogue features, not proof that catalogue hide-and-recover transfers to genuinely uncatalogued faults. The named non-fault mimics are road/dry-wash endings, map-sheet breaks, and digitization endpoints.

### Literal registry gates

- **Before placement:** all 667 indexed single-band, grid-shaped rasters were checked. The surface gate passed; maximum full-footprint Spearman was 0.4229688817.
- **After placement:** the 27,088-dot in-memory map first fired at 0.7270747194 of candidate dots within 3 px of `13GEMSDOE:docs/downloads/13gems_20261001_r11-greedy-mp_v2_nan-outside.tif`, exceeding the literal 0.70 limit. The final-dot scan stopped at its first firing; it was not a complete list of final-dot comparisons.
- No reverse-overlap exemption or Jaccard gate was used. The SHA-256 `323af960dbef0bc85a42001d0da19b73da8b1a509a6f21966e257ddb38d0be67` is for the in-memory decoded array, **not** for a raster file.

The machine-readable gate reports are [`evidence/uniqueness_h57b_surface.json`](evidence/uniqueness_h57b_surface.json) and [`evidence/uniqueness_h57b_dots.json`](evidence/uniqueness_h57b_dots.json). The single authoritative decision card is [`evidence/run_card.json`](evidence/run_card.json); it records a null raster-file SHA, validator not run, download **NOT CLEARED**, submission **NOT SUBMITTED**, and no slot selected. Draft-only name: `gems57-h57b-tip-distance-6772-323af960dbef`. Draft-only note (116 characters): “Fault-zone anatomy H57-B tip-distance; matched-mass sensitivity only. HOLD: not cleared, no upload or slot selected.”

## Historical context — not current H57-B results

- H57-A measured local hide-and-recover DTI for withheld catalogue pixels. At its shipped-density setting, the old `no_side` reading was 0.2279 [0.1867, 0.2691], with 22,641 withheld positives. Higher-density readings (0.2508/0.2517) were at about twice the old file's density. None is a live score or H57-B result.
- H57-F's recorded-sense feature was inconclusive/negative: historical `no_side_plus_sense` 0.2292 versus 0.2279; mean paired difference +0.0016, positive in three of four quadrants but not significant.
- The older raster in `docs/downloads/` is historical and remains HOLD. Its prior 644-raster scan is superseded by the refreshed 667-raster registry and is not current clearance.
- The official DrivenData leaderboard snapshot fetched 2026-10-09 listed #1 at 0.3774, #7 at 0.3195, and #16 at 0.2778. It does not attribute entries to a raster or method. Repository holdout values and sibling-repository projections do not explain or predict those leaderboard entries; no claim is made that new work will beat them.

## Transfer limitation

The hide-and-recover instrument withholds whole mapped branches. Those hidden catalogue pixels can remain physically connected to visible faults; genuinely uncatalogued faults need not be. The matched-mass H57-B result therefore cannot establish transfer to the hidden competition truth. The sibling-repository calibration of this instrument against owner-reported scores had only +0.14 rank correlation for the corresponding `catalogue_hidden` variant (12 scores); this is weak, confounded calibration evidence, not a correction factor or score projection.

## Engineering and documentation status

- `scripts/build_submission.py` is an unsafe legacy in-sample builder. Its CLI now exits before doing work and writes no raster. It is not a promotion path.
- `scripts/build_site.py` renders `evidence/run_card.json` read-only; it does not reconstruct or overwrite that card. The generated pages state the HOLD, with no current download link.
- The README reproduce section is limited to data-pin verification, site generation, and tests; it does not replay the exhausted experiments or invoke the legacy builder.
- The full test suite passed in this branch (one test skipped because optional training data was absent). The site generator ran successfully, `git diff --check` passed, and the run-card SHA-256 was unchanged by site generation.

## Future work — blocked, not authorized here

Any future candidate idea must remain in the fault-zone-anatomy lane, be preregistered under a newly authorized experiment budget, test each feature alone for leakage, use the valid buffered whole-segment holdout, and pass both literal registry gates before a format validator or writer is considered. A candidate must have a genuinely new raster, a file SHA-256, successful format validation, a unique name and a note of at most 140 characters before any download is offered. The weekly-slot selector remains separate. These are gates for a future separately authorized run, not a plan to spend a slot now.

## Source trail

- Official [DrivenData competition description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
- Official [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) snapshot dated 2026-10-09.
- Mechanistic background: Schreurs (2003), https://doi.org/10.1144/GSL.SP.2003.210.01.03; Tchalenko (1970), https://doi.org/10.1130/0016-7606(1970)81%5B1625%3ASBSZOD%5D2.0.CO%3B2; Faulds, Henry & Hinz (2005), https://doi.org/10.1130/G21274.1; Savage & Brodsky (2011), https://doi.org/10.1029/2010JB007665. These sources motivate hypotheses; they do not establish competition-performance gains.
