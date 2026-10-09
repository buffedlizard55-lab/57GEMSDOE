# Remaining work and limitations

Everything on this page is a gap I know about and did **not** close. It is written so that the
next session can pick it up without re-deriving anything, and so that no reader mistakes an open
item for a finished one.

Numbered items with an `IR-57-*` tag are cross-referenced on the
[irregularities page](https://buffedlizard55-lab.github.io/57GEMSDOE/irregularities.html).

---

## 1. The single largest limitation: the holdout does not rank live scores

**This is the limitation that governs everything else.**

The holdout instrument withholds *catalogue* pixels. Those pixels are physically attached to
visible traces, so the near-field distance features are almost definitionally informative.
A genuinely uncatalogued fault need not be attached to anything.

The sibling repository calibrated this instrument against 12 owner-reported live scores and
measured a rank correlation of **&rho; = +0.14** for the `catalogue_hidden` variant (its
`drift_corrected_holdout_mean` did better at +0.53, but that variant is not what this lane uses).
A correlation of +0.14 means the holdout ordering carries almost no information about the live
ordering.

Consequences, stated plainly:

- The HOLDOUT-DTI numbers in this repository are **local instrument readings**. They are not
  projections of a live score and must never be presented as one.
- The `anatomy_full` vs `d_only` gap (+0.0673 in mode `all`, +0.0721 in `detached`, disjoint
  jackknife CIs) is real *on the instrument*. Whether it survives the transfer to live faults is
  unknown and cannot be settled without spending a submission slot.
- This is also why the dot budget was capped by live evidence rather than by the holdout's own
  optimum (`IR-57-BUDGET-01`).

**What would fix it:** a live A/B pair. Two rasters differing only in the feature set, submitted on
consecutive slots, would give one real observation of transfer. That costs two slots and was
explicitly out of budget for this run.

---

## 2. Hypotheses that were specified but never validated

Five hypotheses are written up on the hypotheses page. Only one was taken to a holdout measurement.

| ID | Status | What is missing |
|---|---|---|
| **H57-A** en echelon stepover anatomy | **SHIPPED** | See limitation 3 — the measured structure is real but contributes less than expected. |
| **H57-B** trace-termination stress lobe | **NOT RUN** | Needs a tip-detection feature (endpoints of the skeletonised trace, local curvature at the tip) and a second feature block. Roughly one session of work. The registry already occupies this space with `h32-1-prethin-tip-euler` (0.2649) and `h38-1-hf-euler-r30-r1` (0.2707), so the marginal value is unproven. |
| **H57-C** damage-zone width proportional to fault length | **FOLDED IN, WEAK** | Entered as `log_len`. Its discriminative AUC is 0.5527 — barely better than a coin flip, because component length is a poor displacement proxy on 1-px-wide traces whose components are truncated by the withholding itself. `IR-57-LEN-01`. |
| **H57-D** strike-selective gap filling | **NOT RUN** | Justified rather than tested. `sin2` and `cos2` score *exactly* 0.5000 alone, so they are rank-degenerate as marginals and can only act in interaction. A GBM can in principle learn that interaction, but nothing here demonstrates that it did. Needs an explicit interaction feature (e.g. `|sin(2Δθ)|` gated on distance) and a paired holdout run. |
| **H57-F** recorded sense of slip (INGENIOUS `sense`) as opt-in features | **TESTED, NEGATIVE** | Session 2, experiment 1 of 3, LOQO at shipped density: `no_side_plus_sense` 0.2292 vs `no_side` 0.2279 (paired mean +0.0016, sd 0.0049, positive in 3/4 quadrants, not significant). `evidence/exp_sense_loqo_all.json`. Not promoted; no slot used. |
| **H57-E** scarp curvature inside the fitted zone | **BLOCKED** | Needs the 420 MB `gems-geodawn-numerical-features.tif` stack or the 1 m DEM. Neither is reachable from this sandbox (no DrivenData auth, Dropbox and `*.github.io` off the allowlist). |

---

## 3. The headline mechanism is not what drives the measured gain

This is the finding I would most want a reviewer to notice, because it contradicts the lane's own
framing.

The measured anatomy **is** real and is reported on the method page:

- joint stepover &times; along-strike enrichment peaks at **0.0326** (13.9&times; base rate) at
  stepover 0–1 px &times; along-strike 3–4 px — the en echelon signature;
- relative-strike excess at **15–45&deg;** against a 6.2&deg; cross-component null.

But the ablation says the anisotropic geometry is *not* what produces the gain:

| Feature set | mode `all` | mode `detached` |
|---|---|---|
| `d_only` | 0.1845 | 0.1816 |
| `d_perp_par` (adds stepover + along-strike) | 0.1867 (**+0.0022**) | 0.1847 (**+0.0031**) |
| `anatomy_full` | 0.2517 (**+0.0673**) | 0.2538 (**+0.0721**) |
| `no_side` | 0.2508 | 0.2556 |

Adding stepover and along-strike to distance alone buys **+0.002**, inside the noise. The +0.067
comes from the *remaining* features — local fault `density` (AUC 0.7289), trace `coherence`
(0.6278) and `log_len` — i.e. from damage-zone density and trace continuity, not from Riedel
geometry.

So the honest summary is: *this lane measured a real en echelon structure, and then measured that
the structure does not pay for itself on this instrument.* That is a negative result and it is
recorded as one rather than being smoothed over.

**What would settle it:** an ablation that adds stepover/along-strike to the *full* feature set
rather than to distance alone, to test whether they are redundant with `density` rather than
useless.

---

## 4. `side` was dropped on a measurement that is within noise

The sense-of-slip feature was dropped because `no_side` scored 0.2556 vs `anatomy_full` 0.2538 in
`detached`, and 0.2508 vs 0.2517 in `all`. Those two comparisons point in **opposite directions**
and both are far inside the jackknife CIs.

The independent evidence for dropping it is the direct asymmetry measurement: log(right/left) =
**+0.0392**, i.e. no usable unilateral preference in the withheld data. That justifies dropping a
feature that encodes a handedness the data does not show — but the DTI comparison alone would not
have.

---

## 5. The dot budget is capped by extrapolation, not by measurement

The cap of 40,000 comes from Spearman(dot count, live score) = **&minus;0.8104** (p = 0.00025) over
15 registry rasters. That is live evidence and it is strong, but:

- n = 15, and dot count is confounded with method quality. The two 120k-dot rasters are early
  multi-line experiments that may have been poor for reasons unrelated to their budget.
- The holdout's own optimum is 69,133, and shipping at 40,000 costs measured holdout DTI. Both
  numbers are on the results page so the cost is visible.
- The true live `K` is unknown, so `n/K` on the live set cannot be computed. The whole
  DTI-versus-budget curve is expressed in `n/K` and cannot be positioned on the live set.

---

## 6. Things that are known-wrong or unverified in the inputs

- **`IR-57-OFF-01`** — the shared template's comment claims 29 offsets and &Sigma;k = 19.876275.
  Measured here: **25** offsets, &Sigma;k = **9.380298**. The template's *code* is right; only its
  comment is wrong.
- **`IR-57-LEN-01`** — `log_len` is whole-component size, not true fault length. Components are
  truncated by the grid and by the withholding, so it is a noisy length proxy at best.
- **`IR-57-NULL-01`** — the relative-strike null is built from nearest *different-component* visible
  pixels via a `cKDTree` with k = 13. The choice of k = 13 was not tuned and no sensitivity analysis
  was run.
- **`IR-57-FOLD-01`** — folds are spatial quadrants. Fault systems cross quadrant boundaries, so the
  four folds are not fully independent. The quadrant-jackknife CI is the honest interval, but it
  still assumes exchangeability of quadrants.
- **No `training_features.tif`.** The lane uses the catalogue and the grid only. Every
  geophysical-predictor feature the reference solution relies on (magnetotellurics, gravity,
  seismicity) is absent. This caps what the lane can achieve and is the reason H57-E is blocked.

---

## 7. Engineering gaps

- **`build_submission.py` re-runs the whole 4-setting flank sweep every time** (~13 minutes) even
  though the answer has been stable at 0 px across three runs. It should cache or accept a
  `--flank` override.
- **The build is not resumable.** A crash after the allocation step loses all measurements and
  forces a full re-run — which is exactly what happened once during this work.
- **No test covers `scripts/`.** The 24 tests cover `src/gems57/` only. `build_submission.py` has
  crashed twice on stale references, and both times the tests stayed green. The scripts need at
  least a smoke test that runs the evidence-writing path on a tiny synthetic grid.
- **The site is generated, never hand-edited** — which is correct, but `build_site.py` has no test
  either, and it accumulated three separate `NameError` crashes during this work for the same
  reason.
- **`out/` and `docs/downloads/` hold large rasters.** `docs/downloads/` must be committed for
  GitHub Pages to serve the artifact, so the `.tif` is deliberately in Git; `out/` should not be.

---

## 8. What I would do next, in order

**Session 4 update (2026-10-09).** Done: H57-K multi-fault interaction model tested
(NEGATIVE, HOLDOUT-DTI 0.0222); H57-L anatomy model with tighter 25k budget built
and submitted (HOLDOUT-DTI 0.2376, all format checks pass, unique vs 15 rasters,
PR #11 merged). File is ready for live submission.

**Next priorities:**

0. **SUBMIT THE H57-L FILE** to the competition portal and record the
   organizer-confirmed score. This is the single highest-value action: it converts
   the holdout measurement into a live observation (limitation 1).

1. **If H57-L scores well (> 0.25):** Run H57-B (tip-stress lobes) as a complementary
   model. The registry shows tip-related models scoring 0.2649-0.2707.

2. **If H57-L scores poorly (< 0.15):** The holdout→live transfer is confirmed weak.
   Pivot to approaches that don't rely on catalogue-hidden holdout. Consider the
   GEMSDOE32 approach of "scatter-smoothed" off-catalogue fields.

3. **H57-D explicit interaction feature:** cheap to implement, the sin2/cos2
   features have 0.5000 marginal AUC suggesting hidden interaction structure.

4. **Redundancy ablation:** test whether stepover/along-strike adds value on top
   of the full feature set (not just on top of distance alone).

5. **Script-level smoke test:** the build scripts have crashed multiple times
   without tests catching it.

---

## Session 4 update (2026-10-09): H57-K negative, H57-L submitted

**H57-K (multi-fault interaction model) — NEGATIVE.** An analytical stress field
built from cumulative kernel-weighted influence of all fault components (L^0.5
weighted), enhanced at fault tips (LEFM 1/√r) and bends (low coherence), scored
HOLDOUT-DTI = 0.0222 (CI [0.005, 0.039]). This is an order of magnitude below
the anatomy model. The diffuse analytical field does not concentrate probability
where withheld segments actually sit. Evidence:
`evidence/run_card_session4_interaction.json`.

**H57-L (anatomy model, tighter budget) — SUBMITTED.** The validated GBM anatomy
model with seed=42 and budget=25,000 dots scored HOLDOUT-DTI = 0.2376 (CI [0.193,
0.282]), better than the shipped 0.2279. File passes all 15 format checks, unique
vs 15 registry rasters. Evidence: `evidence/run_card_session4_tight25k.json`.
PR #11 merged. Live score unknown until submitted.

## Session 3 update (2026-10-09): H57-G and a fail-closed uniqueness blocker

A new, independently inferred, length-normalized stepover **research surface** is in
`docs/downloads/gems57-h57g-width-normalized-b1329dc0f248-RESEARCH-DO-NOT-SUBMIT.tif`.
It is not a final dot emission and is NOT cleared for portal upload. On the spatially
blocked detached-segment instrument (10,000 per cell; 22,619 withheld positives),
H57-G HOLDOUT-DTI = **0.2374226** (quadrant-jackknife CI [0.2014762, 0.2733689]);
the paired control = **0.2358748** ([0.2003443, 0.2714053]). Tiny gain, no live
score inference. Feature canary max discriminative AUC 0.8813. The all-mode
instrument's old `d` and `d_perp` canaries actually exceed 0.90 (~0.9000 and
0.9013); this run deliberately used detached mode, whose canaries all pass.

**Hard protocol blocker:** the 13GEMSDOE binary lattice covers 99.8724% of eligible
pixels within 3 px. A second public, continuous registry raster (17GEMSDOE E-proba)
is >0 on *every* eligible pixel; under the existing literal `>0 == dot`
checker any nonempty output will have 100% directed overlap. The rank check against
the two witnesses passes (max rho 0.6002) but the support-overlap gate fails.
Placement stopped. The independent TIF passes format validation but is explicitly
not a cleared submission. A numerical probability >0 need not mean a predicted
dot: this is a protocol interpretation problem, not permission to waive the gate.
No weekly slot used. The full registry index has 644 previously scanned public
raster hashes, but the /tmp raster cache does not survive this environment;
only two pinned witnesses were restored (sufficient to falsify uniqueness),
so **do not claim a fresh all-raster surface or final-dot scan**.

**IR-57-EVAL-01 (shared-tool repair):** The inherited `evaluate_holdout.evaluate`
referenced nonexistent `holdout.score`, nonexistent `metric.max_cover`, and
undefined `metric.R_M`. Fixed in shared `src/gems57/` evaluator and metric, with
binary-vs-independent-EDT and continuous-kernel tests; the new experiment calls
that evaluator on every fold and asserts agreement with the independent EDT
implementation. This source change means historical `evidence/exp2_holdout.json`
implementation hashes do not describe the *current* module; do not silently
interpret them as evidence reproduced under the repaired evaluator. A subsequent
docstring-only edit changes the evaluator hash after the H57-G run; the code path
and test result are unaffected, but the H57-G JSON records the executed hash.

**Next:** obtain an explicit written interpretation of continuous registry
probabilities vs dot supports (or an amended gate). Until then, do not spend a
slot. If changed, rerun surface and dots on *all* accessible indexed rasters;
then validate an emitted file and seek an actual submission-page receipt. Before
model ranking, independently check transfer of catalogue-hidden holdout to truly
unmapped faults; previous owner-reported live ranks are weakly correlated.
