# Archived session-2 experiment log (2026-10-09)

**Archive note:** The measurements below belong only to this historical run and its legacy `gems52-pooled-hide-v1` evaluator. They are not current H57 main-line evidence and must not be combined with the current `gems57-pooled-hide-v2` run card. In particular, do not confuse this log with the older H1 `scripts/run_holdout.py` attempt or use its figures as the current H57 result.

Number discipline: every DTI below is **HOLDOUT-DTI**, evaluator
`gems52-pooled-hide-v1`, hide-and-recover (4 spatial quadrants x draws 20/21,
whole-segment withholding, 12 px domain erosion, visible-only features, pooled
DTI alpha=0.2 beta=0.8 R=3 px triangular), leave-one-quadrant-out, with the
quadrant-jackknife 95% CI. Nothing here is a live score or a projection.

Budget: 3 experiments (EXP-1 CV, EXP-2 CV, EXP-3 build), within the 2-hour cap.

---

## Pre-experiment smoke test (caught two bugs before any experiment)

1. **IR-57-STRIKE-01** — `fold_geometry`'s strike fill was inverted
   (`np.where(np.isfinite(s), 0.0, s)`), zeroing every finite strike. sin2/cos2
   were constants and the offset frame was a strike-0 frame. Fixed in the shared
   template; regression tests added (`tests/test_anatomy.py`).
2. Overflow sentinels in `det_elev`/`depth_to_base_surf` derivatives (float32
   laplacian/hypot) — scrubbed to the in-footprint median and differenced in
   float64 inside `gems57/geo.py`.

## EXP-1 — feature-set CV, mode `all` (5 variants, 22,641 withheld positives)

| variant | features | HOLDOUT-DTI | CI95 (jackknife) | coverage | dots (8 cells) |
| --- | --- | --- | --- | --- | --- |
| `d_only` | d | 0.1845 | [0.1630, 0.2059] | 0.5036 | 220,010 |
| `d_perp_par` | d, d_perp, d_par_abs | **0.3180** | [0.2803, 0.3557] | 0.5044 | 92,985 |
| `no_side` | anatomy minus `side` (8) | **0.3270** | [0.2923, 0.3617] | 0.5105 | 92,585 |
| `geo_only` | H57-G1/G2/G3/G5 block (9) | 0.0621 | [0.0478, 0.0764] | 0.1828 | 242,387 |
| `no_side_plus_geo` | no_side + geo block (17) | 0.3171 | [0.2711, 0.3631] | 0.4900 | 91,183 |

Findings, stated plainly:

* **The strike-frame fix vindicates the lane's core hypothesis.** Before the fix
  (session 1), `d_perp_par` bought +0.0022 over distance-only and the en echelon
  geometry was written off as noise (REMAINING_WORK item 3). After the fix it
  buys **+0.1335**, and the full anatomy block reaches 0.3270 — the highest
  HOLDOUT-DTI this lane has measured. The session-1 negative result is retracted
  as bug-artefacted; the corrected number is the one on this page.
* **H57-G1 (zone-gated geophysical corroboration) is a validated NEGATIVE on
  this instrument.** The union (0.3171) does not beat `no_side` (0.3270);
  geophysics alone is far weaker (0.0621) than catalogue geometry. Per the
  brief, an idea that has not beaten the holdout best does not reach a
  submission slot. Caveat recorded: the holdout withholds *catalogue* pixels and
  under-represents the blind faults geophysics is supposed to find
  (holdout-to-live rho ~ +0.14), so this is a negative on the instrument, not a
  proof of live uselessness. The CONSENSUS-PROXY (exploratory) tests transfer.
* `d_only` reproduces the session-1 number exactly (0.1845) — evidence that the
  run_cv refactor (geometry caching, per-fold memory lifecycle) changed no
  semantics for frame-independent features.
* Leakage canary: all 9 geophysical columns clean (max discriminative AUC
  0.6011). `d` (0.9000) and `d_perp` (0.9245) exceed the 0.90 bar and are
  proven non-leaking by construction (visible-only features); the
  mapping-continuity confound is named in the run card (IR-57-CANARY-01).

## EXP-2 — detached-mode robustness + the `side` question

Mode `detached`: only withheld strands >= 400 m from every other component — the
conservative reading of "genuinely new geometry". Variants: `d_perp_par`,
`no_side`, `anatomy_full`. **22,619 withheld positives.**

| variant | HOLDOUT-DTI | CI95 (jackknife) | coverage | dots (8 cells) |
| --- | --- | --- | --- | --- |
| `d_perp_par` | 0.3255 | [0.2968, 0.3542] | 0.5062 | 89,361 |
| `anatomy_full` | 0.3276 | [0.3051, 0.3501] | 0.5015 | 88,376 |
| `no_side` | 0.3262 | [0.3041, 0.3483] | 0.5001 | 88,518 |

Findings:

* The anatomy gain **holds on the conservative instrument**: ~0.326 at the top
  vs the distance-only detached reference (0.1816, session 1 — `d` is
  frame-independent and reproduces exactly across runs).
* **The `side` question is closed.** `anatomy_full` (0.3276) vs `no_side`
  (0.3262) is inside the jackknife noise and in the *opposite* ordering to mode
  `all` (0.3270 `no_side`). Combined with the direct asymmetry measurement
  (log(right/left) = +0.0392, session 1) there is no usable handedness in the
  withheld data; `side` stays dropped and the shipped model is `no_side`.
* The lean 3-feature model (`d_perp_par`) is statistically tied with the 8-
  feature `no_side` on both instruments — the en echelon offset frame carries
  almost all of the signal (consistent with EXP-1). The lean variant is noted on
  the run card as the lower-variance alternative for live transfer; the shipped
  raster uses `no_side` (best point estimate on the primary mode).

## EXP-3 — submission build

Winner: `no_side`, mode `all`. Build with `--budget-cap 40000` (live-evidence
cap, IR-57-BUDGET-01), flank sweep measured on the holdout, uniqueness screen
against all 16 registry rasters including this lane's own previous ship
(registered 2026-10-09). — filled after the build.
