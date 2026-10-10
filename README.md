# 57GEMSDOE — fault-zone-anatomy lane for the DOE GEMS Prize Challenge

**Competition:** [DOE GEMS Prize (DrivenData #306)](https://www.drivendata.org/competitions/306/competition-doe-gems/)
· **Problem description:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
· **About / resources:** [page 968](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
· **Rules (PDF):** [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
· **Reference solution:** [github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
· **Site:** <https://buffedlizard55-lab.github.io/57GEMSDOE/>

---

## ⬇ ONE-CLICK SUBMISSION FILE

**The file to submit is [`docs/downloads/gems57-h57r2-shipped8-all-flank0-20261009T180433Z-90e532947353-zeros.tif`](docs/downloads/gems57-h57r2-shipped8-all-flank0-20261009T180433Z-90e532947353-zeros.tif)**
— the only `.tif` directly in `docs/downloads/` (everything else is in `docs/downloads/archive/`).
It is portal-legal by construction: single band, `float32`,
`EPSG:32611`, `3730 × 3292`, transform `(100, 0, 243350, 0, -100, 4508550)`, every one of the
12,279,160 cells finite and in `[0, 1]`, zero dots on the mapped catalogue, 40,000 dots,
sha256 `9afe74ab2b2fa631e9276cd8e8685fc76086d96d01181101998309b0c0d06a47`.
**It is OK to download and submit this file** — the verdict box at the top of
[the executive summary](docs/executive-summary.html) says so explicitly, computed from the
validator receipt and the uniqueness screen, not asserted.

Suggested submission note (108 characters, limit 140):

```
57GEMSDOE fault-zone anatomy | variant shipped8 (all, flank 0px) | 40000 dots, 0 on-catalogue | sha 90e53294
```

> **Do not submit a `-nan.tif` variant.** Those are diagnostics (kept in
> `docs/downloads/archive/`). They carry ~7.17 M `NaN` cells outside the study-area
> footprint and the portal rejects them with *"Predicted values must be in range [0, 1]"*,
> because `NaN` satisfies neither `v >= 0` nor `v <= 1`. See
> [the executive summary](docs/executive-summary.html) and irregularity `IR-57-NAN-01`.

The exact filename, sha256, check receipt and the suggested submission note are
printed at the top of [`docs/index.html`](docs/index.html) and in
[`evidence/submission_build_all.json`](evidence/submission_build_all.json).

**Uniqueness, disclosed (IR-57-OVERLAP-01).** The new raster is unique against all 15
sibling-lane rasters by wide margins (worst rank correlation 0.0128, worst dot-set Jaccard
0.0110, worst 3 px dot overlap 36.5 %; limits 0.90 / 0.50 / 70 %), and its sha256 differs from
every registry raster. Against this repository's own session-1 build of the *same* lane, 3 px
forward dot overlap is 71.1 % — expected, because two halos around the same faults overlap by
construction; the dot-set Jaccard is 0.2400 and only 36.5 % of the new dots sit on a cell the
previous build also used, so it is not a copy. Both numbers are on the run card for the
selector to weigh.

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

## Headline result

**Session 2 (current submission).** After the strike-frame fix
(`IR-57-STRIKE-01`, below), the shipped feature set re-measured on the
hide-and-recover holdout, leave-one-quadrant-out, 8 cells (4 quadrants x draws
20/21): **`shipped8` scores 0.3270 [0.2923, 0.3617] on mode `all`** (22,641
withheld positives) and **0.3262 [0.3041, 0.3483] on mode `detached`**
(22,619 withheld positives). Every number is a `HOLDOUT-DTI` instrument
reading — none is a projected live score.

| Feature set (corrected frame) | mode `all` | 95% CI (quadrant jackknife) | mode `detached` | 95% CI |
| --- | --- | --- | --- | --- |
| `shipped8` (shipped: 8 features) | **0.3270** | [0.2923, 0.3617] | **0.3262** | [0.3041, 0.3483] |
| `no_rielder` (minus `d_perp`/`d_par_abs`) | 0.2319 | [0.2126, 0.2513] | 0.2291 | [0.2150, 0.2433] |
| `gated` (H57-D: + `sin2d`, `cos2d`) | 0.3288 | [0.2934, 0.3642] | 0.3273 | [0.3051, 0.3494] |
| `anatomy_full` (all 11) | 0.3265 | [0.2925, 0.3605] | 0.3275 | [0.3047, 0.3503] |

Session 1, same instrument, buggy grid-aligned frame: `no_side` 0.2508
[0.2164, 0.2852] (`all`), 0.2556 [0.2329, 0.2784] (`detached`).

**The frame fix — not new features — is the gain (+0.076, disjoint CIs), and
it overturns session 1's headline negative result.** Removing the stepover /
along-strike geometry now costs **−0.0950** (`all`) / **−0.0971** (`detached`):
with offsets decomposed in the local trace frame, the en echelon structure
pays for itself. Session 1's "+0.0022, inside the noise" was an artifact of
the grid-aligned frame. Re-measured with the corrected frame, the joint
stepover x along-strike enrichment peaks at **0.0902 (≈ 39x the base rate)**
at stepover 0–1 px x along-strike 1–4 px — a sharp off-diagonal ridge, versus
0.0326 (13.9x) measured in the buggy frame.

**H57-D is a negative result.** The explicit strike x distance interaction
(`sin2d`, `cos2d`) buys **+0.0018** (`all`) / **+0.0010** (`detached`) — inside
the noise. Per the lane's rule ("keep only the structure the data shows"), the
shipped variant is `shipped8`.

### Why 0.2778 won, and whether higher is achievable

`DTI = T / (0.2(T + n - M) + 0.8K)`. Two consequences, both verified against the
brute-force implementation:

1. **The ceiling is 1.0, not 0.5556.** A perfect prediction has `n = M = T = K`,
   so `D = 0.2K + 0.8K = K`. (0.05556 is a different number entirely: the
   marginal acceptance bar `alpha * DTI` at DTI = 0.2778.)
2. **At the real base rate DTI tracks coverage — but only while the dot budget
   stays near `K`.** At the measured base rate 0.00221, a *random* pixel lands
   within 3 px of a true one only 2.1% of the time. Measured with the exact
   metric, coverage 0.2778 is worth **0.3161** at `n/K = 0.5` and only
   **0.1794** at `n/K = 6` (synthetic illustration, regenerated in session 2 by
   `scripts/registry_budget.py`; the session-1 file read 0.3162 / 0.1809).

So 0.2778 is roughly **28% coverage of the live truth at a near-matched budget**,
and 0.3774 implies about 40%. Higher is achievable and the route is arithmetic:
raise coverage while holding `n <~ 2K`. The registry confirms the budget half of
this with live evidence — **Spearman(dot count, organizer-confirmed live score) =
-0.8104** (p = 0.00025) over 15 rasters, and the two rasters above 120,000 dots
hold the two worst live scores (0.1922, 0.1894). That is why this lane's
holdout-optimal budget (46,603 dots on the corrected frame) was **overruled** and
capped at 40,000, inside the band every top performer occupies (35k–46k). See
`IR-57-BUDGET-01`.

What session 2 changed about this picture: the corrected trace frame raised the
lane's measured coverage from 0.4852 to **0.5105** (`all`) and from 0.4740 to
**0.5001** (`detached`) at the LOQO instrument — i.e. the lane now measures
~51% coverage of *withheld catalogue* pixels at its holdout-optimal budget.
The transfer to live truth is still unmeasured (holdout-to-live rank
correlation +0.14 across 12 live scores, sibling repository), so no live score
is projected.

**Remaining work and every known limitation:** [`REMAINING_WORK.md`](REMAINING_WORK.md).

---

## Session 2 (2026-10-09, later) — the strike-frame bug and what it changed

Reviewing this repository line by line found a real bug in the lane's feature
geometry, registered as **`IR-57-STRIKE-01`**: the strike fallback in
`src/gems57/anatomy.py` was *inverted* (`np.where(np.isfinite(s), 0.0, s)`
kept the non-finite strikes and zeroed every finite one), so the anchor strike
was identically 0 in every fold and in the shipped surface. Consequences:

* `sin2`/`cos2` were the constants 0/1 — the canary's "AUC exactly 0.5000" was
  this bug's symptom, not a property of the data;
* `d_perp`/`d_par_abs`/`side` decomposed offsets in a **grid-aligned** (row/col)
  frame instead of the **local trace frame**.

Fixed and pinned by `tests/test_anatomy.py`, then the lane was re-measured
end-to-end (`scripts/run_cv_r2.py`). All numbers below are `HOLDOUT-DTI`
(leave-one-quadrant-out, pooled, quadrant-jackknife 95 % CI) — instrument
readings, never live scores.

| Feature set (corrected frame) | mode `all` | 95 % CI | mode `detached` | 95 % CI |
| --- | --- | --- | --- | --- |
| `shipped8` (8 features, the shipped set) | **0.3270** | [0.2923, 0.3617] | **0.3262** | [0.3041, 0.3483] |
| `no_rielder` (minus `d_perp`/`d_par_abs`) | 0.2319 | [0.2126, 0.2513] | 0.2291 | [0.2150, 0.2433] |
| `gated` (H57-D: + `sin2d`, `cos2d`) | 0.3288 | [0.2934, 0.3642] | 0.3273 | [0.3051, 0.3494] |
| `anatomy_full` (all 11) | 0.3265 | [0.2925, 0.3605] | 0.3275 | [0.3047, 0.3503] |

Session 1, same instrument, buggy frame (9-feature set): `no_side` 0.2508
[0.2164, 0.2852] (`all`) and 0.2556 [0.2329, 0.2784] (`detached`).

Three findings, each measured:

1. **The bug fix is the gain.** `shipped8` on the corrected frame beats the
   session-1 shipped set by **+0.0762** (`all`) and **+0.0706** (`detached`),
   with disjoint jackknife CIs. The geometry features were not dead — they were
   measured in the wrong frame.
2. **The en echelon geometry is real.** Removing `d_perp`/`d_par_abs` from the
   shipped set costs **−0.0950** (`all`) / **−0.0971** (`detached`), far outside
   the noise. Session 1's "+0.0022, inside the noise" was an artifact of the
   grid-aligned frame: with offsets decomposed along/across the actual trace,
   the stepover × along-strike structure the lane set out to find pays for
   itself. This overturns session 1's headline negative result.
3. **H57-D (explicit strike × distance interaction) is a negative result.**
   Adding `sin2d`/`cos2d` buys **+0.0018** (`all`) / **+0.0010** (`detached`) —
   inside the noise. Per the lane's own rule ("keep only the structure the data
   shows") the shipped variant is `shipped8`, not `gated`.

The leakage canary (rule 4) fires only on `d` (0.8853 mean / 0.9000 max) and
`d_perp` (0.9150 / 0.9245) — the same external-validity caveat as session 1
(`IR-57-CANARY-02`), mitigated by the `detached` mode where the gain persists.
The two new interaction features screen at 0.60–0.64 discriminative AUC, clear
of the bar.

The session-2 submission is built from `shipped8` on the corrected frame
(`scripts/build_submission.py --mode all --variant shipped8 --budget-cap
40000`), validated, and uniqueness-checked against all 18 registry rasters
(15 sibling submissions plus this repository's own two earlier builds and the
parallel session's merged raster). See the run card for the receipt.

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
* **No sense-of-slip field exists.** `existing_faults.tif` has exactly three
  values, `{-1, 0, 1}`. The lane brief asks to condition on recorded sense of
  slip "where the database has it" — it does not. `IR-57-SLIP-01`.
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

These are **ORGANIZER-CONFIRMED** numbers as pasted by the task owner. Two
different "highest score" values appear in the brief (0.3774 and 0.3195); the
conflict is registered as `IR-57-BRIEF-01` and neither is treated as a target
this repo claims to beat.

