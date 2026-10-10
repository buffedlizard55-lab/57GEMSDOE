# 57GEMSDOE — fault-zone-anatomy lane for the DOE GEMS Prize Challenge

**Competition:** [DOE GEMS Prize (DrivenData #306)](https://www.drivendata.org/competitions/306/competition-doe-gems/)
· **Problem description:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
· **About / resources:** [page 968](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
· **Rules (PDF):** [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
· **Reference solution:** [github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
· **Site:** <https://buffedlizard55-lab.github.io/57GEMSDOE/>

---

## Download / submission status — NOT CLEARED (2026-10-09)

> **Do not download or submit an H57-B candidate. No new GeoTIFF was generated.**
> The in-memory candidate fails the literal final-dot registry gate; the format validator
> was therefore not run. No weekly slot was selected, no upload was made, and no organizer
> receipt exists. The single authoritative run card is [`evidence/run_card.json`](evidence/run_card.json).

The tested lane remains fault-zone anatomy. On the **original preregistered** 10,000-dot-per-cell
run, the H57-B candidate emitted 71,191 dots versus 80,000 for `no_side` across eight holdout
cells, so the arm contrast is **non-comparable and cannot promote**. Its measured values are still
labelled `HOLDOUT-DTI` (evaluator `gems57-buffered-whole-branch-pooled-v2.0`, 22,276 withheld
positives, paired 20 km spatial-block 95% CI); they are not leaderboard scores.

A later **post-hoc matched-mass sensitivity** used exactly 6,772 dots per cell in all three arms.
It measured candidate `HOLDOUT-DTI` 0.17128 (95% CI [0.15851, 0.18437]) versus `no_side` 0.11032
([0.09942, 0.12224]), paired difference +0.06096 ([+0.05203, +0.07038]). The cap was derived
from the first run's candidate counts after seeing that run; its interval is conditional on that
selected cap. This result is favorable sensitivity evidence, **not confirmatory** and not promotion
eligibility. The pre-run expectation (+0.005 to +0.020) was exceeded; this is recorded, not treated
as evidence of leaderboard transfer.

The feature-only canary was clean (maximum discriminative AUC 0.8392; threshold 0.90). The
full-catalogue emission surface passed the pre-placement check (maximum full-footprint Spearman
0.42297 over all 667 indexed rasters). The 27,088-dot in-memory map then failed the literal final
dot gate: 72.71% of its dots were within 3 px of
`13GEMSDOE:docs/downloads/13gems_20261001_r11-greedy-mp_v2_nan-outside.tif` (limit 70%). The scan
stopped at its first firing. No reverse-overlap exemption or Jaccard gate was used. See
[`evidence/uniqueness_h57b_surface.json`](evidence/uniqueness_h57b_surface.json) and
[`evidence/uniqueness_h57b_dots.json`](evidence/uniqueness_h57b_dots.json).

The older file `gems57-h57-anatomy-enechelon-20261009T070415Z-e9d8d59a4357-zeros.tif` remains in
`docs/downloads/` for historical review only. Its old 644-raster audit is stale relative to the
refreshed 667-raster archive; the file remains **HOLD** and this README deliberately provides no
download link. Its former format receipt is not a validation receipt for H57-B.

**Proposed name (draft only):** `gems57-h57b-tip-distance-6772-323af960dbef`

**Draft note (116 characters; not assigned):** `Fault-zone anatomy H57-B tip-distance; matched-mass sensitivity only. HOLD: not cleared, no upload or slot selected.`

---

## Core values (kept central to every decision in this repository)

> **Maximize P(Win).** *"Maximize the Probability of Winning"* is our
> decision-making framework. In every decision we weigh tradeoffs, assess risk,
> and choose the path that maximizes the probability that we win this prize. We
> set aside our emotions and make tough decisions in order to maximize P(Win).
> It frees us from constraints and clarifies that we must put the outcome first.
>
> **Own the Outcome.** We own results end to end — not just our individual slice
> of the work. When problems arise and we have the means to act, we act without
> waiting for permission or assignment. We treat failure and success as signals
> and use them to improve. We stay accountable to the final outcome.

Applied here: *Maximize P(Win)* is why the lane's dot budget and its flank
exclusion are **chosen by holdout measurement** rather than by hand, and why no
submission slot is spent on an idea that has not beaten the holdout bar.
*Own the Outcome* is why three bugs found in this session's own code — including
one inherited from the shared template's prose — are recorded in
[`docs/irregularities.html`](docs/irregularities.html) instead of being quietly
patched.

---

## Standing brief (re-read at the start of every session)

The full task prompt is reproduced verbatim at the bottom of this file and in
[`BRIEF.md`](BRIEF.md). Its operative constraints for this lane:

1. **Lane.** Fault-zone anatomy — predict where secondary strands sit around
   known faults from shear-zone mechanics. Stay inside it. If the raster's
   rank-correlation with any registry raster exceeds **0.90**, or more than
   **70 %** of its dots fall within 3 px of one registry raster's dots, log it as
   a duplicate and stop.
2. **Reuse, don't rebuild.** Hide-and-recover holdout; withhold whole fault
   segments with a buffer; derive every catalogue feature only from the visible
   faults; mask visible faults pixel-exactly; score pooled DTI (α = 0.2,
   β = 0.8, 300 m triangular kernel).
3. **Label every number** `HOLDOUT-DTI` (evaluator version, number of withheld
   positives, 95 % CI) or `ORGANIZER-CONFIRMED` (copied from a submission-page
   receipt). **A projection is never written as a score.**
4. **Leakage canary.** Test each feature alone before trusting any result.
   AUC above **0.90** means leakage until proven otherwise.
5. **Run card.** End with one JSON card (see [`docs/run-card.html`](docs/run-card.html)).
6. **Budget.** Stop after **3** experiments or **2** hours. Negative results are
   deliverables.

---

## Prior H57-A / H57-F status (historical; H57-B is above)

* The older H57-A file remains in `docs/downloads/` for historical review; it is **not cleared**.
  Its old 15-check local format receipt applies only to that existing file, not to H57-B. The old
  644-raster uniqueness scan is superseded by a refreshed 667-raster index; do not use the old
  result as current clearance.
* The earlier shipped-density H57-A reading (per-cell cap 10,000; mode `all`; 22,641 withheld
  positives) was `HOLDOUT-DTI` 0.2279, 95% CI [0.1867, 0.2691], from
  [`evidence/exp_sense_loqo_all.json`](evidence/exp_sense_loqo_all.json). It is a local reading,
  not a leaderboard score and not the H57-B result.
* The earlier 0.2508 / 0.2517 H57-A figures were measured at about 2x shipped density (~136k dots)
  and are not the shipped configuration (`IR-57-SHIP-01`).
* Recorded sense of slip (H57-F) was historically inconclusive/negative: `no_side_plus_sense` 0.2292
  vs 0.2279; mean paired difference +0.0016, positive in 3/4 quadrants but not significant. It was
  not carried into the existing file.
* The initial legacy uniqueness result (114 forward-overlap firings among 644 rasters) is a
  historical hold. Reverse overlap is not an exemption. The new H57-B final-dot check independently
  fails the same literal one-way rule at 72.71% vs a 70% limit.
* No weekly slot has been selected, no submission made, and no organizer receipt exists.

**Official leaderboard snapshot fetched 2026-10-09:** #1 xiaofanhu 0.3774; #7 DARD 0.3195;
#16 extradr19 0.2778. The leaderboard does not identify which raster or method produced a
participant's score. These entries are not targets this repository claims it can beat.

## Historical H57-A metric analysis (not a current candidate)

Hide-and-recover holdout, leave-one-quadrant-out. **Every number below is a
`HOLDOUT-DTI` instrument reading. None of them is a projected live score. H57-B's current
status is summarized at the top of this README and in the run card.**

**Shipped density (per-cell cap 10,000, mode `all`, 22,641 withheld positives):**

| Feature set | HOLDOUT-DTI | 95% CI (quadrant jackknife) | coverage |
| --- | --- | --- | --- |
| `no_side` (shipped: 8 features) | **0.2279** | [0.1867, 0.2691] | 0.3288 |
| `no_side_plus_sense` (tested, negative) | 0.2292 | [0.1892, 0.2693] | 0.3308 |

Paired (sense − no sense) per quadrant: NW +0.0038, NE +0.0056, SW +0.0025,
SE −0.0056. Not significant. A distance-only baseline at shipped density has not
been measured yet, so the gain over distance-only below is **at 2x density only**.

**About 2x shipped density (earlier run, ~136k dots; not the shipped configuration):**

| Feature set | mode `all` | 95% CI (quadrant jackknife) | mode `detached` | 95% CI |
| --- | --- | --- | --- | --- |
| `d_only` (distance to nearest visible fault) | 0.1845 | [0.1630, 0.2059] | 0.1816 | [0.1683, 0.1950] |
| `d_perp_par` (+ stepover, along-strike) | 0.1867 | [0.1605, 0.2128] | 0.1847 | [0.1665, 0.2029] |
| `anatomy_full` (all 9 features) | **0.2517** | [0.2183, 0.2851] | 0.2538 | [0.2309, 0.2766] |
| `no_side` (8 features) | 0.2508 | [0.2164, 0.2852] | **0.2556** | [0.2329, 0.2784] |

At 2x density the full model beats distance-only by **+0.0673** (`all`) and
**+0.0721** (`detached`) with disjoint confidence intervals.

**But the gain is not from the Riedel geometry.** Adding stepover and
along-strike to distance alone buys only **+0.0022** — inside the noise. The
+0.067 comes from local fault `density` (AUC 0.7289), trace `coherence` (0.6278)
and `log_len`. The en echelon structure this lane set out to find **is** there in
the data (joint stepover x along-strike enrichment 0.0326, **13.9x** base rate),
and it **does not pay for itself on this instrument**. That is recorded as a
negative result in [`REMAINING_WORK.md`](REMAINING_WORK.md) rather than smoothed
over.

### Metric mechanics and the evidence gap around public scores

`DTI = T / (0.2(T + n - M) + 0.8K)`. Two arithmetic facts are verified against
the brute-force implementation:

1. **The ceiling is 1.0, not 0.5556.** A perfect prediction has `n = M = T = K`,
   so `D = 0.2K + 0.8K = K`. (0.05556 is a different number: the marginal
   acceptance bar `alpha * DTI` at DTI = 0.2778.)
2. **At a fixed truth field, dot budget affects DTI.** At the measured base rate
   0.00221, a random pixel lands within 3 px of a true one only 2.1% of the time.
   In the exact synthetic metric calculation, coverage 0.2778 is worth **0.3162**
   at `n/K = 0.5` and **0.1809** at `n/K = 6`. This is metric arithmetic, not
   a forecast of any team's score.

Separately, the `GEMSDOE32` README reports for H33-2-B2 (37,654 dots) a local
holdout gain of +0.004870 over a 0.2708 base and a projected live score of 0.2747;
the latter is that repository's projection, not a measurement. The official
leaderboard snapshot lists a 0.2778 entry at #16, but no receipt or artifact-level
record here links that entry to H33-2-B2. These distinct facts do not establish
why the public entry scored as it did, and they do not explain the current #1 at
0.3774. No DTI projection or leaderboard-beating claim is made here.

**Remaining work and every known limitation:** [`REMAINING_WORK.md`](REMAINING_WORK.md).

---

## What this repo actually contains

| Path | What it is |
| --- | --- |
| [`BRIEF.md`](BRIEF.md) | the standing task prompt, verbatim |
| [`src/gems57/metric.py`](src/gems57/metric.py) | DTI, verified against a brute-force transcription |
| [`src/gems57/grid.py`](src/gems57/grid.py) | CRS / shape / transform / footprint, sha256-pinned |
| [`src/gems57/network.py`](src/gems57/network.py) | fault segments, local strike, offset frame, detachment |
| [`src/gems57/holdout.py`](src/gems57/holdout.py) | hide-and-recover folds, pooled DTI |
| [`src/gems57/anatomy.py`](src/gems57/anatomy.py) | the **fitted** fault-zone-anatomy intensity |
| [`src/gems57/emit.py`](src/gems57/emit.py) | lazy-greedy max-coverage allocation at the DTI fixed point |
| [`src/gems57/fitting.py`](src/gems57/fitting.py) | leakage canary + leave-one-quadrant-out CV |
| [`src/gems57/validate.py`](src/gems57/validate.py) | every portal check |
| [`src/gems57/uniqueness.py`](src/gems57/uniqueness.py) | rank-correlation and 3 px dot overlap vs the registry |
| [`scripts/run_lane.py`](scripts/run_lane.py) | `verify` / `measure` stages |
| [`scripts/run_cv.py`](scripts/run_cv.py) | canary + CV + ablation |
| [`scripts/audit_h57b_candidate.py`](scripts/audit_h57b_candidate.py) | fixed H57-B surface/dot registry gates in memory; writes no TIF |
| [`scripts/check_uniqueness_full.py`](scripts/check_uniqueness_full.py) | literal full-archive surface or final-dot gate |
| [`scripts/scan_gemsdoe_registry.py`](scripts/scan_gemsdoe_registry.py) | refreshes the public sibling-repository raster index |
| [`scripts/build_submission.py`](scripts/build_submission.py) | legacy in-sample builder; disabled for promotion use |
| [`scripts/build_site.py`](scripts/build_site.py) | regenerates docs without rewriting the run card |
| [`evidence/`](evidence/) | every measurement, machine-readable |
| [`registry/`](registry/) | 15 earlier submission rasters, provenance-indexed |
| [`data/bridge/`](data/bridge/) | the two competition files, sha256-verified |

## Reproduce

```bash
pip install -r requirements.txt
python scripts/run_lane.py verify   # re-verify the two pinned data files by SHA-256
python scripts/build_site.py        # renders the committed card and evidence; does not rewrite the card
pytest -q
```

The H57-B holdout and registry audits are frozen evidence in `evidence/`; replaying them would
consume the exhausted experiment budget and is not needed to render or review the current verdict.
`build_submission.py` is a legacy in-sample selector and is **disabled**; do not run it to create a
candidate or download artifact. The current H57-B remains HOLD; see `evidence/run_card.json`.

## Verified data provenance

| File | sha256 | Source |
| --- | --- | --- |
| `existing_faults.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | [GEMSDOE2 `data/bridge/`](https://github.com/buffedlizard55-lab/GEMSDOE2/blob/main/data/bridge/existing_faults.tif) |
| `sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | [GEMSDOE2 `data/bridge/`](https://github.com/buffedlizard55-lab/GEMSDOE2/blob/main/data/bridge/example_submission.tif) |

`existing_faults.tif` is byte-identical to the `labels.tif` recorded in
[`GEMSDOE32/data/restore_receipt.json`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/data/restore_receipt.json)
(same sha256, same 425,830 bytes) — the public "labels" raster **is** the mapped
fault catalogue, and the scored truth is not published. That is what forces the
hide-and-recover design.

## Limitations

* **No DrivenData credentials in the sandbox.** The 420 MB
  `gems-geodawn-numerical-features.tif` feature stack is present in the bridge
  repos as five parts but is not pulled here; this lane is catalogue-geometry
  only and does not need it.
* **Sense of slip is available only in the INGENIOUS and Q-fault vectors, not in the
  competition raster.** `existing_faults.tif` has exactly three values, `{-1, 0, 1}`,
  and carries no sense. `data/external/trace_segments_utm11.csv` has a `sense`
  column (N 66,861 / RL 8,448 / LL 7,628 / blank 1,394 segments) and
  `qfault_attributes.csv` has `SLIPSENSE`. Tested as opt-in features: **negative**
  (`IR-57-SLIP-02`, H57-F). The shipped file does not use it.
* **No external SGMC-derived fault raster**, so the secondary off-catalogue
  instrument used by the shared template cannot be reproduced here.
* **The holdout truth is withheld *catalogue* pixels**, which by construction
  belong to mapped systems. Genuinely unmapped faults are a different
  population. The `detached` withholding mode is the conservative reading and is
  reported alongside the primary one.

---

## Appendix — the full task prompt, verbatim

Re-read this at the start of every session. It is the specification this
repository is built against; the README summarises it, this file *is* it.

---

## The lane

> Fault-zone anatomy lane: predict where secondary strands sit around known
> faults from shear-zone mechanics. The organizers define a new fault as any
> fault pixel not already captured by USGS/INGENIOUS, including newly mapped
> geometry of an existing system (thread 11536), so splays and parallel strands
> count. They also confirmed that a dot near a known trace but far from any
> new-fault pixel is fully penalized (thread 11516), so the allocation must be
> fitted, not assumed. Analogue experiments of distributed dextral shear
> (Schreurs, 2003) produce left-stepping en echelon Riedel shears linked by
> short synthetic shears subparallel to the bulk shear. The classical framework
> is Tchalenko (1970), and the pattern is consistent with the left-stepping
> dextral faults Faulds, Henry and Hinz document in the northern Walker Lane.
> Damage-zone work (Savage and Brodsky, JGR 2011) shows secondary-fracture and
> strand density decaying away from the primary fault, with zone width growing
> with displacement and then more slowly. Build a per-fault intensity from
> distance, fault length as a displacement proxy, and strand orientation
> relative to the primary strike, conditioned on recorded sense of slip where
> the database has it. Do not hard-code textbook angles. On the hide-and-recover
> holdout, measure the relative-strike and distance distributions of withheld
> segments against their nearest visible fault and keep only the structure the
> data shows. Shrink this lane's dot budget if few withheld positives fall
> inside the fitted zone. Output the standard validated GeoTIFF,
> uniqueness-checked against every earlier raster.

## Parallel-run protocol — read first

> 1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If
>    your raster's rank-correlation with any registry raster exceeds **[0.90]**,
>    or more than **[70%]** of your dots fall within 3 px of one registry
>    raster's dots, you have drifted into another lane: log it as a duplicate and
>    stop. Check this on the surface before placement AND on the final dots.
>
> 2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack,
>    `evaluate_holdout.py` and `submission_writer.py`. Holdout = hide-and-recover:
>    withhold whole fault segments with a buffer, derive every catalogue-based
>    feature only from the visible faults, mask visible faults pixel-exactly,
>    score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared
>    tool is wrong, fix it once in the template and report it; never keep a
>    private fork.
>
> 3. **LABEL EVERY NUMBER** as HOLDOUT-DTI (evaluator version, number of withheld
>    positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page
>    receipt). A projection is never written as a score.
>
> 4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting
>    any result. AUC above **[0.90]** means leakage until proven otherwise.
>
> 5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; the named
>    non-fault process that could mimic it; holdout DTI + CI; correlation/overlap
>    vs registry; raster sha256; validator output (no NaN inside the footprint,
>    values in [0,1], CRS/shape/transform match); submission name + note of at
>    most 140 characters; verdict promote / negative. Negative results are
>    deliverables.
>
> 6. **BUDGET.** Stop after **[3]** experiments or **[2]** hours. Do not pick
>    submissions: promotion to a real slot is a separate selector step, within
>    the weekly cap shown on the submission page.

## Candidate hypotheses — required before implementing

> Before implementing, generate 3–5 candidate geological hypotheses we haven't
> tried yet, each naming: the specific layer(s) involved, the physical signature
> being targeted (e.g., an edge-detection or curvature transform), why it should
> catch a fault missing from the USGS/INGENIOUS catalogue rather than one already
> in it, and how it differs from anything already implemented in this repo. Rank
> them by expected DTI improvement and implementation cost. Validate the top
> candidate on our spatially-blocked holdout set before touching a weekly
> submission slot — do not spend a submission slot on an idea that hasn't beaten
> the current holdout best. If a candidate can't be validated without new
> external data, name the specific free, official source needed and check it's
> obtainable before proposing the idea as viable.

→ delivered in [`docs/hypotheses.html`](docs/hypotheses.html).

## Submission mechanics

> We need to focus on being able to generate a submission into the competition.
> The site should be able to generate a TIF file that is required for submission.
> It should be as easy as download to click a File to submit into the
> competition. This needs to be in the executive summary or the very beginning of
> the site. It should be obvious when you visit the site.
>
> I tried to submit the document that i downloaded from the site but it returned
> this error on the submission form: **"Predicted values must be in range [0, 1]"**
>
> Also we need to give it a unique name and a short comment to help you or your
> team tell submissions apart later, e.g. clustering with k=25.
>
> Create a executive summary subpage that explains exactly how to make a
> submission into the contest.

> The submission form says: *You can submit a single-band GeoTIFF (.tif) file, or
> a .zip file containing a single GeoTIFF, with your predictions. It must match
> the submission format's CRS, shape, and geotransform.*

→ root cause and fix: `IR-57-NAN-01` in
[`docs/irregularities.html`](docs/irregularities.html).

## Quality bar

> Work line by line verifying from official verified trusted sources, provide
> links for manual review. There should be no manual input, work on your own to
> complete tasks. Flag any irregularities for review. No hallucinations.
>
> Run this task through multiple passes.
> Pass 1: Implement the task completely and verify the result.
> Pass 2: Review your work for bugs, missing requirements, incorrect assumptions,
> and edge cases. Fix everything you find.
> Pass 3: Re-check the entire implementation against the original request.
> Improve accuracy, reliability, completeness, and code quality. Fix any
> remaining issues.
> Do not stop after the first pass.

## Reference links from the brief

| Purpose | Link |
| --- | --- |
| Competition home | https://www.drivendata.org/competitions/306/competition-doe-gems/ |
| Problem description | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ |
| About / resources | https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/ |
| Data (login required) | https://www.drivendata.org/competitions/306/competition-doe-gems/data/ |
| Leaderboard | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ |
| Reference solution | https://github.com/drivendataorg/gems-prize-reference-solution |
| Rules PDF | https://docs.nlr.gov/docs/fy26osti/96647.pdf |
| GeodAWN survey (USGS) | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and |
| INGENIOUS (GBCGE) | https://gbcge.org/current-projects/ingenious/ |
| EPSG:32611 | https://epsg.io/32611 |
| Tversky index | https://en.wikipedia.org/wiki/Tversky_index |
| GDR submission 1391 | https://gdr.openei.org/submissions/1391 |

## Owner-reported scores quoted in the brief

These are **OWNER-REPORTED** numbers as pasted by the task owner. None is backed by a
submission-page receipt, so none is ORGANIZER-CONFIRMED in this repo's label scheme
(`IR-57-LABEL-01`). Two
different "highest score" values appear in the brief (0.3774 and 0.3195); the
conflict is registered as `IR-57-BRIEF-01` and neither is treated as a target
this repo claims to beat.

