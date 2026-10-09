# 57GEMSDOE — fault-zone-anatomy lane for the DOE GEMS Prize Challenge

**Competition:** [DOE GEMS Prize (DrivenData #306)](https://www.drivendata.org/competitions/306/competition-doe-gems/)
· **Problem description:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
· **About / resources:** [page 968](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
· **Rules (PDF):** [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
· **Reference solution:** [github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
· **Site:** <https://buffedlizard55-lab.github.io/57GEMSDOE/>

---

## 2026-10-09 latest run — independent H57-G raster, NOT SUBMITTABLE

**DO NOT UPLOAD ANY FILE FROM THIS REPOSITORY YET.** A freshly fitted length-normalized
cross-strike model produced a distinct [research GeoTIFF](docs/downloads/gems57-h57g-width-normalized-b1329dc0f248-RESEARCH-DO-NOT-SUBMIT.tif),
not copied from a previous submission. Its file SHA-256 differs from all 644
indexed raster file hashes; only two prior surfaces were rank-tested before the
literal gate stopped the run. The local GeoTIFF format validator passes all checks. **But the
literal directed-overlap rule fails against public registry witnesses on the
surface before dot placement, so no final-dot submission was generated.**
The earlier candidate below also failed that rule. The new model's spatial-blocked,
detached-segment HOLDOUT-DTI is 0.2374 [0.2015, 0.2734] on 22,619 withheld positives
vs its same-density baseline 0.2359 [0.2003, 0.2714]; the very small gain does not
establish a live benefit. Evidence: [`evidence/exp4_width.json`](evidence/exp4_width.json),
[`docs/session-3.html`](docs/session-3.html). No weekly slot was used.

**Measured blocker:** the binary 13GEMSDOE lattice's 3-px halo covers 99.8724% of
eligible cells. The continuous 17GEMSDOE E-proba raster is positive on 100% of
eligible cells, so *if* `>0` is interpreted literally as a dot in a continuous
prior (the existing checker does), no nonempty candidate can pass. That interpretation
is not equivalent to thresholding a probability surface at 0.5. Do not quietly
change the gate; seek a protocol interpretation before future promotion. Registry
scope is public accessible files, not private entries.

---

## ⬇ ONE-CLICK SUBMISSION FILE

> **STATUS: HOLD — do not submit yet.** The file is format-valid, but the literal
> uniqueness gate fired (forward dot overlap > 0.70 against one registry raster) for
> **114 of 644** registry rasters, so the protocol says log and stop. It is not cleared.
> Two owner decisions are needed (see `IR-57-UNIQ-03` and the banner on
> [`docs/index.html`](docs/index.html)). Nothing has been submitted.

**The candidate file (held) is the `-zeros.tif` variant in [`docs/downloads/`](docs/downloads/).**
It is portal-legal by construction: single band, `float32`, `EPSG:32611`,
`3730 × 3292`, transform `(100, 0, 243350, 0, -100, 4508550)`, every one of the
12,279,160 cells finite and in `[0, 1]`, zero dots on the mapped catalogue.

> **Do not submit the `-nan.tif` variant.** It is a diagnostic. It carries
> 7,111,787 `NaN` cells outside the study-area footprint and the portal rejects
> it with *"Predicted values must be in range [0, 1]"*, because `NaN` satisfies
> neither `v >= 0` nor `v <= 1`. See [the executive summary](docs/executive-summary.html)
> and irregularity `IR-57-NAN-01`.

The exact filename, sha256, check receipt and the suggested submission note are
printed at the top of [`docs/index.html`](docs/index.html) and in
[`evidence/submission_build_all.json`](evidence/submission_build_all.json).

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

The *operative excerpts* of the task prompt are reproduced in this file and in
[`BRIEF.md`](BRIEF.md); the long owner-supplied site-score list is summarized, not
reproduced verbatim. Re-read the standing brief and this README at every session.
Its operative constraints for this lane:

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

## Session 2 status (2026-10-09) — what is measured now

* **Shipped configuration, measured at its own density** (per-cell cap 10,000;
  LOQO, mode `all`; 22,641 withheld positives): `no_side` HOLDOUT-DTI **0.2279**,
  95% CI [0.1867, 0.2691]. This is the number to quote for the shipped file.
  Source: [`evidence/exp_sense_loqo_all.json`](evidence/exp_sense_loqo_all.json).
* **The 0.2508 / 0.2517 figures earlier in this README were measured at about 2x
  shipped density (~136k dots).** They are kept below, labelled as such. They are
  not the shipped configuration (`IR-57-SHIP-01`).
* **Recorded sense of slip was tested and is NEGATIVE** (experiment 1 of 3, H57-F):
  `no_side_plus_sense` 0.2292 vs 0.2279; paired difference +0.0016 mean, positive in
  3 of 4 quadrants, not significant. Sense is not in the shipped file.
* **Shipped file re-validated against its receipt**: sha256 `8ba5a9822d87eb7b1e159ae2bfee8ced429ecb9752761041309fe5629df0e482`,
  808,408 B, 15/15 checks, 0 on-catalogue dots, 35,341 dots. Identical to
  `docs/downloads/checks-…-zeros.tif.json`.
* **Full-registry uniqueness gate — NOT CLEARED (HOLD).** 644 rasters, both directions
  ([`evidence/uniqueness_full_shipped-h57-zeros.json`](evidence/uniqueness_full_shipped-h57-zeros.json)):
  * Spearman max **0.180** (gate 0.90): pass. Jaccard max **0.083** (gate 0.50): pass.
  * Forward dot overlap (gate 0.70): **fires for 114 rasters**, max **1.00**. The
    literal rule treats this as drift. The file lists only 50 of the 114 firings.
  * The reverse-overlap reading (below 0.5 for every itemized firing) would clear it,
    but that exemption is **not in the protocol**. It needs an owner decision.
  * An earlier version of the script called the file UNIQUE using that exemption.
    The verdict has been corrected (`IR-57-UNIQ-02`).
* **No submission slot was spent.** Nothing has been submitted or promoted to a slot.
* **Labels corrected:** the 15-raster budget correlation uses *owner-reported*
  scores, not organizer receipts (`IR-57-LABEL-01`). The build's holdout numbers are
  *in-sample* (`IR-57-INSAMPLE-01`).

## Headline result

Hide-and-recover holdout, leave-one-quadrant-out. **Every number below is a
`HOLDOUT-DTI` instrument reading. None of them is a projected live score.**

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

### Why 0.2778 scored highest, and whether higher is achievable

`DTI = T / (0.2(T + n - M) + 0.8K)`. Two consequences, both verified against the
brute-force implementation:

1. **The ceiling is 1.0, not 0.5556.** A perfect prediction has `n = M = T = K`,
   so `D = 0.2K + 0.8K = K`. (0.05556 is a different number entirely: the
   marginal acceptance bar `alpha * DTI` at DTI = 0.2778.)
2. **At the real base rate DTI tracks coverage — but only while the dot budget
   stays near `K`.** At the measured base rate 0.00221, a *random* pixel lands
   within 3 px of a true one only 2.1% of the time. Measured with the exact
   metric, coverage 0.2778 is worth **0.3162** at `n/K = 0.5` and only
   **0.1809** at `n/K = 6`.

What the repos document for the 0.2778 file (`GEMSDOE32`, H33-2-B2, 37,654 dots,
verified in its `README.md`): a **local** holdout gain of **+0.004870** over a 0.2708
base (4/4 quadrants), and a **projected** live score of 0.2747 (the repo's own
projection, not a measurement). The live 0.2778 was owner-reported after that.
So the 0.2778 score comes from a small holdout-validated tweak on a base near
0.27, with a dot count in the 37–42k band.

*Inference, not a measurement:* the 0.3774 high would need roughly 40% coverage
at a matched budget by the same arithmetic. That is a projection, not a score.
The repo does not demonstrate a higher score. The budget half of the argument is
supported by **owner-reported** scores (`IR-57-LABEL-01`): Spearman(dot count,
owner-reported live score) = **−0.8104** (p = 0.00025, n = 15, re-derived in this
session from `registry/registry_index.json`), and the two rasters above 120,000 dots
hold the two worst scores (0.1922, 0.1894). The correlation is confounded with
other differences between submissions, so it is evidence, not proof. That is why this lane's
holdout-optimal budget of 69,133 dots was **overruled** and capped at 40,000,
costing only 0.0015 holdout DTI. See `IR-57-BUDGET-01`.

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
| [`scripts/build_submission.py`](scripts/build_submission.py) | final surface, emission, validation, uniqueness |
| [`scripts/build_site.py`](scripts/build_site.py) | regenerates `docs/` from the evidence JSONs |
| [`evidence/`](evidence/) | every measurement, machine-readable |
| [`registry/`](registry/) | 15 earlier submission rasters, provenance-indexed |
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


## Session 3 pre-experiment hypotheses (2026-10-09; re-read the standing brief above)

Ranked *prospectively*, before code or validation; improvement is an expectation, not a score. All use the pinned mapped-fault raster and require no new external data. The physics is an analogy, **not** proof that withheld catalogue traces represent unknown faults. These are different from the existing raw `d`, `d_perp`, `d_par_abs`, `log_len`, density/coherence features; no new textbook angles are specified.

| Rank / cost | New hypothesis / layer | Fitted physical signature | Why off-catalogue pixels might respond / novelty relative to this repo |
|---|---|---|---|
| 1 / low | H57-G length-normalized transverse displacement; `existing_faults.tif` visible-only component length and nearest-trace frame | `d_perp / sqrt(1 + L)` conditioned on proximity; estimate response in leave-one-quadrant-out folds | A longer mapped fault is a *proxy* for displacement and a wider secondary-strand zone; scale invariance may retrieve an unmapped parallel trace. Previous model gave `d_perp` and `log_len` separately, not this explicit interaction. |
| 2 / medium | H57-H relay asymmetry at isolated tip pairs; visible fault segment endpoints and orientation | angle and separation of two *visible* facing trace tips, fitted jointly with side | A blind relay inside a mapped gap could be missed where catalogue ends; unlike the existing nearest-single-anchor along-strike offset, this requires two independent anchors. Related tip lanes in sibling repos mean uniqueness is uncertain. |
| 3 / low | H57-I orientation-dependent width; local strike/coherence + mapped-fault distance | fit distance decay separately by visible local strike bin; bins learned, not geologic angles imposed | Fault-strand density may vary with regional stress fabric; extends the global-distance field with a conditional interaction rather than the existing marginal `sin2/cos2`. |
| 4 / medium | H57-J bend-dependent strand width; local mapped-trace direction and finite-difference along-trace curvature | fitted widening of damage zone at mapped fault bends, controlling for segment length | Under-mapped splays can branch at bends; unlike the current linearity/coherence feature this uses signed change *along a trace* (without DEM). Road and wash bends are geological false-positive mimics. |

**Falsification gate:** test each new feature alone for leakage AUC; compare the top arm against the existing eight-feature arm with visible-only, whole-segment, buffered spatial-block holdout and pooled DTI. Do not spend a weekly slot. Independently, the strict directed-overlap gate may be **mathematically unsatisfiable** for a near-universal 5-pixel lattice already in the registry; report that as a blocker, not as a waiver.
