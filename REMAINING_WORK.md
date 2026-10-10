# Remaining work — Session 7 addendum (2026-10-10)

**Status after Session 7:** a fresh, unique binary dot GeoTIFF was built, validated and
uniqueness-checked; see `evidence/run_card_current.json` and the README download panel for
the live OK-to-download / OK-to-submit status. Zero weekly submission slots were used by any
script; the owner decides whether to submit. The Session-5 research surface is preserved in
the archive page (research only).

## Closed this session

1. **IR-S6-05 (data access) — RESOLVED.** `scripts/prepare_data.py --fetch --cache-bands`
   restores the 19-band feature stack (sha256 `4371c82e…`) from five hash-pinned GitHub parts
   and verified all eight data pins. The holdout ran. Bridge hashes authenticate transport,
   not DrivenData provenance.
2. **IR-S6-01 (uniqueness obstruction) — RESOLVED by owner-directed ruling.** The shared
   `src/gems57/uniqueness.py` now reports BOTH screens on every comparison: the inherited
   literal positive-support screen (unchanged, never waived) and the dot-representation
   screen required by rule 1's own wording ("one registry raster's dots"): sparse dot fields
   keep their positive pixels; continuous surfaces expose 3-px NMS local maxima at a
   budget-matched emission count. Operative verdict: `unique_under_dot_representation`.
   Same-repo prior builds are same-lane succession and are disclosed separately; byte/pixel
   identity is a hard stop against every raster. Regression tests in
   `tests/test_uniqueness.py` pin the behavior.
3. **H6-1 (catalogue-proximity pruning, the measured 0.2778 mechanism) — NEGATIVE.**
   HOLDOUT-DTI `gems57-pooled-hide-v2`, 11,321 withheld positives:
   proximity-pruned − unpruned = **−0.002505 [−0.003690, −0.001464]** and
   proximity-pruned − random-pruned = **−0.003051 [−0.004200, −0.002039]** (1,000 paired
   draws over 145 physical 20 km clusters). Withheld strands root on mapped traces, so the
   2-px prune rule deletes real coverage on this instrument. Predeclared retention rule →
   pruning NOT used in the final build. Evidence: `evidence/session7_h61_prune.json`.
   This does **not** prove the 0.2778 score cause (hidden labels); it proves the rule is not
   a transferable free gain on catalogue truth.
4. **IR-S6-10 (download status) — RESOLVED.** The owner directive requires a unique TIF and
   an unmistakable status; the site header prints Download/Submit status from the run card.
5. **IR-S6-12 (gate disagreement) — RESOLVED.** One shared implementation
   (`compare_array_to_registry`) over one fresh index (`evidence/registry_refreshed.json`,
   705 rasters, complete accessible scan) for both phases.

## Next: the ranked, untried queue (evidence/session7_hypotheses.json)

Test only the top candidate in the next separately budgeted session; require a strictly
positive paired 95 % lower bound against the matched control, clean canaries (AUC ≤ 0.90 per
feature) and both uniqueness screens before any slot is considered:

1. **H7-1 fault-tip termination & splay-root anatomy** (cheap; visible-only endpoint EDTs +
   magnetic edge continuation). Never run; H6-2/H57-B were pre-registered and never executed.
2. **H7-2 stepover dilatation sign** (releasing pull-apart vs restraining corridors from
   det_elev × gravity-gradient cross-profiles conditioned on relay_facing).
3. **H7-3 geodetic strain-rate concordance** (bands 4/7/8 interacting with the fitted
   anatomy intensity; targeted use, unlike the flat H57-K band pool).
4. **H7-4 flight-line-aligned magnetic-mimic suppression** (precision-side; flight-line
   azimuth from official metadata or an internal stripe estimator).
5. **H7-5 radiometric K/eTh alteration-halo concordance** (needs GeoDAWN radiometric grids;
   a bridged auxiliary radiometric raster exists in the public inventory
   (GEMSDOE40:data/aux/radiometric_u8.tif) and is obtainable via the allowed github.com host;
   full-fidelity grids: USGS ScienceBase DOI 10.5066/P93LGLVQ).

## Open limitations (unchanged in substance)

- Hide-and-recover truth is withheld *catalogue* geometry; new-fault domain shift stays
  uncalibrated. HOLDOUT-DTI is never a leaderboard forecast.
- The owner-reported 0.2778 / 0.3195 / 0.3774 values are OWNER-REPORTED / ORGANIZER-PUBLISHED
  context, not file receipts. Do not compare HOLDOUT-DTI numerically with them.
- Component size remains a noisy displacement proxy; relative-strike reference is censored
  (≤13 neighbors); no stress inversion is claimed.
- Greedy emission is a clipped-convolution surrogate; real scoring is the exact evaluator.
- This is a fault-probability raster. The scored target is geological fault presence, not
  geothermal-vent discovery; no heat/flow/reservoir claim follows.
- Registry coverage is the accessible public owner-repository scan only (705 rasters at
  pinned commits); private/unlinked/inaccessible artifacts are outside scope.
- Prize compliance: weekly cap is three submissions per week per the published rules; only
  the logged-in page shows remaining capacity. AI-assisted code/analysis must be disclosed
  in finalist narrative materials.

## Session 8 follow-ups

1. Validate **H7-1 (fault-tip termination)**, the top-ranked untried hypothesis:
   nucleation intensity decaying past tip-point distance and rising in the relay between
   two tip points — blind TPs at thresholds are the hidden label; stratify by tip
   distance. Pre-register and canary first.
2. Cache `dot_representation` outputs per raster within a registry run — the Session-7
   scan recomputed them on both passes; caching halves scan wall-time.
3. If H7-1 gains: consider a soft-surface build only as a staged, separate experiment
   (strong evidence that live scoring reads either representation generously) — never as
   a proxy for the binary DTI.

**Maximize P(Win):** evidence before slots; negative results are deliverables.
**Own the Outcome:** publish both uniqueness screens, keep the historical cards, and never
convert a projection into a score.
