# 57GEMSDOE — fault-zone-anatomy lane for the DOE GEMS Prize Challenge

**Competition:** [DOE GEMS Prize (DrivenData #306)](https://www.drivendata.org/competitions/306/competition-doe-gems/)
· **Problem description:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
· **About / resources:** [page 968](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
· **Rules (PDF):** [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
· **Reference solution:** [github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
· **Site:** <https://buffedlizard55-lab.github.io/57GEMSDOE/>

---

## ⬇ DOWNLOADABLE RESEARCH CANDIDATE — NOT CLEARED FOR SUBMISSION

[Download the current H57 GeoTIFF](docs/downloads/gems57-h57-anatomy-enechelon-20261009T070415Z-e9d8d59a4357-zeros.tif) (`35,341` binary dots; SHA256 `8ba5a9822d87eb7b1e159ae2bfee8ced429ecb9752761041309fe5629df0e482`).
It passes the **local format/geometry/range checks**: one `float32` band,
`EPSG:32611`, `3730 × 3292`, competition transform, finite values in `[0,1]`,
and no dots on the mapped catalogue.

**Status: research-only; do not submit yet.** The valid out-of-fold score is not
matched to the candidate's 40,000-dot budget, two single-feature leakage canaries
are above 0.90 pending explanation, recorded INGENIOUS slip-sense is not encoded,
and this artifact has no pre-placement surface-correlation audit. A final-dot
comparison passed against 18 available local rasters only; this is not a complete
competition-wide uniqueness claim. No upload or organizer receipt is evidenced.
See [`evidence/run_card.json`](evidence/run_card.json) for the exact blockers and
[`evidence/uniqueness_review.json`](evidence/uniqueness_review.json) for the
finite local audit scope.

The current zeros TIFF is a valid **file-format** choice. The NaN diagnostic
variants in the archive are not submission files. Local validation must not be
confused with portal acceptance.

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

Applied here: *Maximize P(Win)* means no slot is spent on this candidate while
its cap-matched OOF evidence, leakage flags, sense-conditioning requirement, and
pre-placement uniqueness check are unresolved. *Own the Outcome* means the
historical in-sample `0.279349` builder reading and its incorrect cap accounting
are explicitly revoked as promotion evidence rather than quietly retained as a
headline.

---

## Standing brief (re-read at the start of every session)

The full task prompt and its provenance notes are retained at the bottom of
this file and in [`BRIEF.md`](BRIEF.md). Its operative constraints for this lane:

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

## Current validation and what the reported high score means

The strongest honest internal comparator for the current **no-side H57 variant** is
from saved leave-one-quadrant-out evaluation in [`evidence/cv_all.json`](evidence/cv_all.json):

| Evidence | Value | Interpretation |
| --- | ---: | --- |
| `HOLDOUT-DTI` | **0.250800** | local hide-and-recover OOF measurement, not a live score |
| Withheld positives | 22,641 | whole-segment positives across draws 20/21 |
| 95% CI | [0.216433, 0.285166] | four-quadrant jackknife, not a pixel-binomial interval |
| Emissions in saved CV | 136,293 across two draws | about 68,147 dots per full-map equivalent; **not** matched to the 40,000-dot candidate |
| Candidate output | 35,341 dots | format-valid local artifact; no budget-matched OOF score |

The saved single-feature canary also flags `d` (maximum discriminative AUC
0.900018) and `d_perp` (0.901345). Under the brief these remain leakage flags
until explained. The historical `0.279349` value in the earlier builder evidence
is **revoked as holdout evidence**: that builder trained and scored the same
fold cells, and divided its nominal budget across two draws instead of four
quadrants. It is retained only as a historical diagnostic; see the exact audit
in [`evidence/submission_build_all.json`](evidence/submission_build_all.json).

### The cited high score and improvement plausibility

The prompt contains conflicting high-score references (`0.2778`, `0.3195`,
`0.3774`). The checked-in 15-row registry has owner-reported values but no
submission-page receipts, and no live leaderboard was checked in this review.
Therefore I cannot identify which raster earned a specific cited value, explain
its performance, or compare the local `HOLDOUT-DTI` directly with it. Do not
call any of those values `ORGANIZER-CONFIRMED` without a receipt.

Improvement is **plausible but unproven**: the DTI denominator penalizes false
positive mass at weight 0.2 and missed truth at weight 0.8, and H57's local
spatial holdout shows that catalogue geometry contains predictive signal. That
does not establish live generalization to genuinely unmapped faults. A valid
next comparison needs the same spatial folds, a 40,000-dot full-map budget,
leakage-canary resolution, slip-sense conditioning where visible vector support
exists, and a saved 95% CI. No projected live score is reported.

The three-to-five ranked geology hypotheses and their expected gain/cost
trade-offs are in [`docs/research/hypotheses_h57.md`](docs/research/hypotheses_h57.md).

---

## What this repo actually contains

| Path | What it is |
| --- | --- |
| [`BRIEF.md`](BRIEF.md) | standing task prompt with score-provenance notes |
| [`src/gems57/metric.py`](src/gems57/metric.py) | DTI, verified against a brute-force transcription |
| [`src/gems57/grid.py`](src/gems57/grid.py) | CRS / shape / transform / footprint, sha256-pinned |
| [`src/gems57/network.py`](src/gems57/network.py) | fault segments, local strike, offset frame, detachment |
| [`src/gems57/holdout.py`](src/gems57/holdout.py) | hide-and-recover folds, pooled DTI |
| [`src/gems57/anatomy.py`](src/gems57/anatomy.py) | the active **fitted** H57 fault-zone-anatomy feature stack |
| [`src/gems57/faultzone.py`](src/gems57/faultzone.py) | legacy H1/H52 geometry helpers; sense is retained at record level but not propagated into pixel features, and this is not the active H57 path |
| [`src/gems57/emit.py`](src/gems57/emit.py) | lazy-greedy max-coverage allocation at the DTI fixed point |
| [`src/gems57/fitting.py`](src/gems57/fitting.py) | single-feature leakage canary + leave-one-quadrant-out CV |
| [`src/gems57/evaluate_holdout.py`](src/gems57/evaluate_holdout.py) | repaired shared DTI evaluator and spatial block terms |
| [`src/gems57/submission_writer.py`](src/gems57/submission_writer.py) | fail-closed packaging, format gate, one-TIFF ZIP and local receipt |
| [`src/gems57/validate.py`](src/gems57/validate.py) | local portal-format checks (not organizer acceptance) |
| [`src/gems57/uniqueness.py`](src/gems57/uniqueness.py) | pre-placement surface rank check and final-dot overlap against supplied inventory |
| [`scripts/run_lane.py`](scripts/run_lane.py) | `verify` / `measure` stages |
| [`scripts/run_cv.py`](scripts/run_cv.py) | canary + CV + ablation |
| [`scripts/build_submission.py`](scripts/build_submission.py) | final surface, emission, validation, uniqueness |
| [`scripts/build_site.py`](scripts/build_site.py) | regenerates `docs/` from the evidence JSONs |
| [`evidence/`](evidence/) | measurements and the single machine-readable run card |
| [`registry/`](registry/) | 15 owner-repository rasters plus 3 archived local rasters in the 18-row audit index; finite scope only |
| [`docs/review_passes.md`](docs/review_passes.md) | the three review passes and current stop flags |
| [`data/bridge/`](data/bridge/) | the two competition files, sha256-verified |

## Reproduce

```bash
pip install -r requirements.txt
python scripts/run_lane.py verify            # re-verify the two data files by sha256
python scripts/run_lane.py measure           # withhold structure measurement
python scripts/run_cv.py  --mode all         # leakage canary + LOQO CV + ablation
python scripts/build_submission.py --mode all
python scripts/build_site.py
pytest -q
```

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

## Limitations and irregularities

* **No organizer upload or result receipt.** The repository has local format
  checks and owner-reported registry values, not organizer-confirmed acceptance.
* **The large training feature raster is absent from this checkout.**
  `data/official/training_features.tif` is gitignored and approximately 419 MB;
  the data-preparation test now reports this as an expected skip/absence rather
  than pretending all pins were verified. It is not used by the geometry-only
  H57 candidate, and no cached feature-stack claim is made.
* **The present TIFF predates the shared-helper repair.** The active CV path and
  future builder now use the repaired `evaluate_holdout.py` and fail-closed
  `submission_writer.py`, but the saved CV evidence was not recalculated through
  the adapter and the existing TIFF was not regenerated. Provenance is recorded
  in the run card.
* **Sense-of-slip availability is split by source.** The official binary fault
  raster has no slip-sense band, but the local INGENIOUS vector file includes
  `sense` and `qfault_attributes.csv` includes `SLIPSENSE`. The current H57
  model does **not** encode it; that is a promotion blocker, not evidence that
  the field is unavailable.
* **The off-catalogue SGMC proxy files are present** in `data/external/`, but
  are not official hidden truth and are not used to build the candidate.
* **The holdout truth is withheld mapped-catalogue pixels**, which by
  construction belong to mapped systems. Genuinely unmapped faults are a
  different population. `all` and `detached` modes are local instruments, not
  proof of live performance.
* **Uniqueness coverage is finite.** Final dots were compared with 18 local
  rasters (15 owner-repository main-tree files and 3 archived local files).
  The public owner-repository manifests themselves exclude some private,
  unlinked or externally stored material. Pre-placement surface correlation was
  not recorded for the present artifact.
* **Canary irregularity:** the OOF evidence flags `d` and `d_perp` above the
  0.90 discriminative-AUC limit. The reason has not been established; treat the
  result as non-promotable pending an explanation or redesigned instrument.

---

## Appendix — retained task prompt and provenance notes

Re-read this at the start of every session. It is the specification this
repository is built against; the README summarises it, this file retains it and
records the evidence limits on owner-reported score references.

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

→ active ranked plan: [`docs/research/hypotheses_h57.md`](docs/research/hypotheses_h57.md). The archived H1 hypotheses are marked historical in [`docs/research/hypotheses.md`](docs/research/hypotheses.md).

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

These are owner-provided values quoted in the retained task brief; this checkout
contains no submission-page receipts for them, so they are **not independently
verified or organizer-confirmed here**. The prompt has conflicting high-score
references (0.2778, 0.3195, 0.3774). The conflict is logged as `IR-57-BRIEF-01`;
none is used as a measured target or compared directly to local HOLDOUT-DTI.

