# Current audit status — 2026-10-10 UTC

**HOLD — not cleared to download or submit.** The latest recorded pre-placement
scan covered 679 rasters and fired the literal forward-overlap stop in 78
comparisons (maximum 3-pixel overlap 1.0 on soft-surface finite-positive
support, not final dots); it is historical, not a current cache revalidation.
The current cache preflight found 0/679 indexed rasters present. A session-5
witness audit independently verified one in-scope 17GEMSDOE raster whose
3-pixel support covers every allowable candidate cell; under the literal
>70% rule, any nonempty candidate is blocked while it remains in scope. That
single-witness check does not revalidate all 679 local cache files. No new
experiments, holdout runs, GeoTIFF builds, data downloads, or submissions were
performed in this audit; the three-experiment / two-hour budget is spent. See
`evidence/run_card.json` and `evidence/irregularities_current.json`.

## Current outcome, 2026-10-10 (Session 5)

**New TIFF generated (`gems57-twohost-relay-bend-surface-20261010T201504Z-47ccc38b6bec.tif`). Download for research: OK. Submit: NO.**

The current [run card](evidence/run_card_current.json) is negative for competition submission. All **695** accessible pinned grid rasters across all 57 sibling repositories were checked (`evidence/relay_bend_surface_uniqueness.json`). Against all **665 rasters from the other 56 repositories**, worst full-footprint Spearman rank correlation is **0.658029 ≤ 0.90** (and against the **15 discriminating sibling-lane rasters**, worst Spearman is **0.028783 ≤ 0.90** and worst 3-px dot overlap is **0.237470 ≤ 0.70**). However, literal forward overlap against the 17 dense-support prior rasters is **1.0** (above 0.70), and full-footprint Spearman against this repository's own earlier Session-3 soft surface (sharing the exact 2,452,550 zeroed pixels outside the fitted `d1 ≤ 25.55 px` damage zone) is **0.975291**. A dense-prior saturation certificate proves every nonempty allowed support is blocked under the inherited `finite > 0` definition. No density or reverse-overlap exemption, no production final dots, no weekly slot.

On the repaired buffered whole-component holdout (`gems57-pooled-hide-v2`, `n=11,321` withheld positive pixels, `153` physical 20 km spatial clusters), Session 5 executed the three predeclared hypotheses from `REMAINING_WORK.md` §3 (`H57-H` multi-scale host-bend damage asymmetry & detrended-elevation scarp strike, `H57-I2` two-host damage-zone superposition & en echelon relay stepover mechanics via exact 12-bitplane EDT to the second nearest distinct visible component `C2 != C1`, and `H57-J` slip-sense transition heterogeneity):
- **E2 (`relay_bend_anatomy`, H57-I2 + H57-H)** achieves binary **HOLDOUT-DTI = 0.135204 [0.119140, 0.153036]**, beating single-host `anatomy` (**0.109647**) by **+0.025556 [95% CI +0.013943, +0.037109]** and `distance_only` (**0.112725**) by **+0.022479 [95% CI +0.007867, +0.038463]**, winning all 4 spatial folds (`NW`, `NE`, `SW`, `SE`). Its soft-surface HOLDOUT-DTI is **0.031160 [0.024691, 0.038109]**, beating single-host `anatomy` by **+0.008284 [95% CI +0.005420, +0.010947]**.
- **E3 (`relay_bend_sense_transition`, H57-J)** achieves binary **HOLDOUT-DTI = 0.141391 [0.124513, 0.161457]** (**+0.006188 [−0.001694, +0.015702]** over E2) and soft-surface HOLDOUT-DTI **0.033898 [0.026890, 0.041928]** (**+0.002738 [+0.000307, +0.005994]** over E2); because the binary paired 95% lower bound (`−0.001694`) slightly straddles zero, **E2 (`relay_bend_anatomy`) is retained** by the predeclared rule.

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

These are **OWNER-REPORTED** numbers as pasted by the task owner; no submission-page
receipt is present in this repository, so none is `ORGANIZER-CONFIRMED`. The
reported 0.2778 and conflicting "highest score" values 0.3774 and 0.3195 remain
unverified and are not presented as verified targets this repo can beat.
