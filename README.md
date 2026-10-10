# 57GEMSDOE — fault-zone-anatomy lane

**Competition:** [DOE GEMS Prize (DrivenData #306)](https://www.drivendata.org/competitions/306/competition-doe-gems/)<br>
**Method lane:** secondary fault strands and damage-zone anatomy around mapped faults.<br>
**Audit date:** 2026-10-10 (UTC).

## Operating values and session-start checklist

- **Maximize P(Win):** choose work by evidence, risk, and expected value—not enthusiasm or leaderboard speculation.
- **Own the Outcome:** carry findings through implementation, validation, and honest reporting; preserve negative results and surface blockers rather than hiding them.
- At the start of every project session, read this status-first README, the preserved request/report ledger in [`TASK_PROMPT.md`](TASK_PROMPT.md), the lane/protocol in [`BRIEF.md`](BRIEF.md), [`REMAINING_WORK.md`](REMAINING_WORK.md), and [`evidence/run_card.json`](evidence/run_card.json). The ledger is not a certified word-for-word chat transcript; historical notes are provenance, not current authorization.
- The controlling lane is fault-zone anatomy. Do not drift into unrelated geothermal-resource prediction, exceed the experiment/time budget, weaken a uniqueness gate, or use a retained raster as a submission without a new, evidence-backed clearance decision.

## Submission status — **HOLD**

> **NOT OK TO DOWNLOAD OR SUBMIT. There is no cleared submission file.**
> Historical TIFF/ZIP bytes remain at `docs/downloads/` for audit and a direct URL may still resolve;
> that is not download authorization. Do not use any retained artifact.

The latest recorded pre-placement comparison measured the candidate against
the 679-entry indexed public owner-repository inventory (not an
organizer-complete registry). Maximum forward 3-pixel overlap of the soft
surface's inherited positive support (finite values greater than zero, treated
as “dots” by the literal gate) was 1.0, exceeding the 0.70 stop threshold in
78 comparisons. This is not a final-dot comparison. Maximum
full-footprint Spearman was 0.821258, below its 0.90 threshold. The overlap
rule fired, so the candidate was **not cleared** and no final dots were
generated. That scan is historical, not a current cache revalidation: the
current cache preflight found **0 of 679** indexed rasters present. A separate
2026-10-10 witness audit re-fetched and SHA-verified the in-scope
`17GEMSDOE_E-proba-multiscale` raster (SHA256
`ab0a0a62eecf066a82713b09dd49f0f638a91fa3dd81f54cc34ae89afa3872be`). Its
3-pixel positive support covers every allowable cell; measured forward overlap
was 1.0 for dense and sparse test candidates. Under the unchanged literal
>70% rule, any nonempty candidate is blocked while this witness remains in
scope. This is a registry measurement, not a score, and the specific witness
check does not verify the other 678 local cache files. The separately retained
40,000-dot `h57-anatomy-enechelon` artifact also measured 0.7113 forward overlap
against its own earlier build, above the same literal limit; this independent
candidate check is not clearance either. Do not download or use the retained
research-surface TIFF or any archived `-zeros.tif`. See
[`evidence/run_card.json`](evidence/run_card.json),
[`evidence/session5_witness_verification.json`](evidence/session5_witness_verification.json),
[`evidence/independent_candidate_check.json`](evidence/independent_candidate_check.json),
[`registry/audit_scope.json`](registry/audit_scope.json), and the generated
[status site](docs/index.html).

The three-experiment / two-hour budget is spent. This audit ran tests and
site checks only; it did not run new geological experiments, holdouts,
candidate GeoTIFF builds, data downloads, or submissions. The exact historical
`lean-offset` TIFF was re-read against its receipt and locally passes the
single-band float32, grid, finite `[0,1]`, and 40,000-dot checks, but it is not
uniqueness-cleared or authorized to download/submit. The current `scripts/build_submission.py` is a retired no-output stub. Any
future replacement would require a current, independently reviewed clearance
receipt and an independently complete, hash-verified, grid-aligned comparison
set before fitting or writing any file; none is available here.

### What the reported scores do—and do not—mean

- The latest stored **HOLDOUT-DTI** soft-surface result is `0.023203`, 95% CI
  `[0.018778, 0.027992]`, with 11,321 withheld positives and evaluator
  `gems57-pooled-hide-v2`. It describes the surface representation only; its
  stored source hashes predate the current evaluator code, so it is historical
  validation, not current-code clearance or a live-score projection.
- A separate test-fold binary-allocation result is `HOLDOUT-DTI 0.109168`,
  95% CI `[0.094503, 0.124194]`, on the same withheld-positive count and
  evaluator. It is not the score of the soft TIFF; no production final dots
  were generated after the surface stop.
- The earlier local `0.227908` value, 95% CI `[0.186735, 0.269081]`, and
  22,641 withheld positives remain unpinned legacy context in
  [`evidence/run_card_historical_unpinned.json`](evidence/run_card_historical_unpinned.json).
- `0.2778` is an **owner-reported historical live score**; no submission-page
  receipt in this repository ties it to exact file bytes. The repository's
  separate raster audit found the named H33-2-B2 construction is an exact
  2-pixel catalogue-flank prune of a 40,199-positive base: 2,545 pixels were
  removed, none added, leaving 37,654. Sparse thinning and removing dots with
  little unique new-truth coverage could plausibly reduce false-positive cost
  under max-cover DTI, but the hidden truth and a receipt tying the score to
  these bytes are unavailable. This is a plausible mechanism, not a causal
  explanation for 0.2778. See
  [`evidence/best_submission_audit.json`](evidence/best_submission_audit.json).
- The brief's 0.3195 and 0.3774 highs conflict with its earlier framing; a
  saved public leaderboard snapshot is contextual evidence, not a
  submission-page receipt for exact bytes. None of these figures is labeled
  `ORGANIZER-CONFIRMED` here.
- Improvement is possible in principle, but the repository cannot estimate or
  claim it: holdout performance does not establish live performance, the
  reported score is not tied to an organizer receipt here, the literal registry
  gate is currently blocked by a universal overlap witness, and the experiment
  budget is spent. No projected score is supplied.

### Next candidates (not run)

Four source-grounded, untried fault-zone-anatomy hypotheses and their named
non-fault mimics, tested-method distinctions, physical signatures, qualitative
relative HOLDOUT-DTI upside priors, and implementation costs are ranked in
[`docs/research/hypotheses.md`](docs/research/hypotheses.md). The upside labels
are not scores or quantitative projections, and confidence is low. This is a
research shortlist, not an authorization to run experiments. Any future
validation must follow the brief's hide-and-recover and canary rules.

## Executive submission guide

[`docs/executive-summary.html`](docs/executive-summary.html) is the user-facing
guide. It repeats the HOLD in the first viewport and documents the required
single-band float32 GeoTIFF format and the future upload steps. The previous
portal error (“Predicted values must be in range [0, 1]”) is documented without
claiming an unproven root cause: the safe writer requires every value to be
finite and in `[0,1]`, uses zero outside the valid footprint, and never silently
clips or fills model output. Grid: EPSG:32611, 3730 × 3292, 100 m, pinned
sample transform. Local validation is not organizer acceptance.

## Standing protocol (reread `BRIEF.md` before every session)

1. Stay strictly in the fault-zone-anatomy lane.
2. Use whole-segment hide-and-recover, visible-only catalogue features,
   pixel-exact masking, pooled DTI (`alpha=0.2`, `beta=0.8`, 300 m triangular
   kernel). Apply the specified spatial holdout; do not reuse a stale evaluator.
3. Run the single-feature leakage canary; `AUC > 0.90` is leakage until disproven.
4. Compare surface rank correlation and inherited finite-positive-support
   3-pixel overlap before placement; then compare the pre-placement dot proposal
   and final dots. Stop if `rho > 0.90` or more than 70% of candidate support/dots
   fall within 3 pixels of any registry raster.
5. Label metrics `HOLDOUT-DTI` with evaluator version, withheld-positive count,
   and 95% CI, or `ORGANIZER-CONFIRMED` only when copied from an actual
   submission-page receipt. Projections are never scores.
6. Stop after 3 experiments or 2 hours. Do not spend a weekly slot; promotion
   is a separate selector decision.
7. End with one JSON run card containing hypothesis, mechanism, named non-fault
   mimic, holdout result/CI, registry comparison, raster SHA256, validator result,
   submission name/note (≤140 characters), and promote/negative verdict.

The standing task prompt and protocol are reproduced in the appendix below
and [`BRIEF.md`](BRIEF.md). The longer historical request/report ledger is
preserved separately in [`TASK_PROMPT.md`](TASK_PROMPT.md), including quoted
owner-reported figures that are not treated as verified scores here. These are
repository records, not certified word-for-word transcripts of the original
chat; current audit status and evidence above supersede historical claims.

## Repository map

| Path | Purpose |
| --- | --- |
| `BRIEF.md` | Standing user prompt and parallel-run protocol |
| `src/gems57/metric.py` | Shared exact DTI arithmetic, kernel, and credit maps |
| `src/gems57/evaluate_holdout.py` | Pooled hide-and-recover scorer and spatial-block terms |
| `src/gems57/evaluator_provenance.py` | Evaluator versions plus source/input hashes |
| `src/gems57/spatial.py` | Label-blind whole-component spatial folds |
| `src/gems57/submission_writer.py` | Fail-closed GeoTIFF/ZIP writer; no silent repair |
| `src/gems57/validate.py` / `gates.py` | Local format/range and registry checks |
| `scripts/run_cv.py` | Spatial CV instrument (not run during this audit) |
| `scripts/build_submission.py` | Retired fail-closed stub; creates no candidate TIFF or ZIP while HOLD remains |
| `scripts/build_r2_submission.py` | Retired session-2 publisher; its write-before-check/same-lane exception source is archived under `evidence/history/` |
| `scripts/build_site.py` / `scripts/check_site.py` | Generate the HOLD-first executive site and check internal links/status gates |
| `docs/research/hypotheses.md` | Ranked, source-grounded untried hypotheses |
| `evidence/run_card.json` | Current audit run card; HOLD verdict |
| `REMAINING_WORK.md` | Current blocking gaps and limitations; old plan retained separately in `evidence/history/` |

## Data provenance and limits

The checked-in `data/bridge/` files are pinned in [`data/README.md`](data/README.md).
`training_features.tif` is not present in this checkout, so geophysical-band
validation is data-blocked. An official, publicly accessible USGS/DOE GeoDAWN
catalogue record is documented in the hypotheses page; no GeoDAWN data were
downloaded, clipped, registered to the contest grid, or used in this audit.
The INGENIOUS attribute/vector files under `data/external/` are locally pinned;
record coverage and attribute missingness still require care. For GeoDAWN, the
GDR submission page displays CC-BY 4.0 while its linked USGS/ScienceBase record
is separately recorded as CC0 1.0; these are source-specific catalogue
statements, not a proven conflict. The exact binary asset/license, AOI coverage,
usable bands, and grid alignment are unverified, so that candidate is data-blocked.

---

## Appendix — the saved standing task prompt

Re-read this and `BRIEF.md` at the start of every session. This is the
repository's preserved task specification, not a certified transcript of the
original chat. Current audit status and evidence at the beginning of this README
take precedence over stale historical statements below.

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

→ The portal error's cause remains unproven (`IR-57-NAN-02`); the writer uses
an all-finite `[0,1]` local policy without claiming this was the cause. See
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

