# Three-pass review record — H57 submission-integrity repair

Date: 2026-10-09 (UTC)

## Pass 1 — requirement and method audit

- Kept scope in fault-zone anatomy and retained the full task prompt in `README.md` / `BRIEF.md`.
- Distinguished archived H1/H52 hypotheses from the active H57 slate.
- Re-read the current OOF results, builder evidence, run card, candidate TIFF, local registry index, and data-field definitions.
- Found that `evaluate_holdout.py` called missing `holdout.score` and `metric.max_cover` functions; implemented the shared metric adapter and exact cover helper, and routed active CV scoring through it.
- Found that the old `0.279349` builder value was in-sample and its 40,000-dot cap was misallocated across folds. Kept the historical value but revoked it as holdout/promotion evidence.
- No new modeling experiment or competition upload was run. Existing spatial CV was reused because the protocol caps experiments/time.

## Pass 2 — data, artifact, and test audit

- Rechecked the candidate TIF SHA256, 35,341 emitted pixels, grid geometry, finite `[0,1]` range, and zero catalogue overlap using the existing validation record and tests.
- Recompared final dots with 18 accessible local rasters: 15 owner-repository inventory rows plus 3 archived local rasters. Worst full-footprint Spearman was 0.010702; worst candidate-dot fraction within 3 px was 0.357206. No configured duplicate threshold was crossed in that finite scope.
- Confirmed that the current artifact has no preserved pre-placement surface; the surface check is therefore explicitly `NOT RUN` for this artifact. The builder now fails closed on its surface check before placement for future builds.
- Confirmed that local INGENIOUS vectors contain `sense` and `qfault_attributes.csv` contains `SLIPSENSE`; H57 does not encode them. The official binary raster itself has no sense field. Inspection beyond line 360 in `faultzone.py` found that `ingenious_record_segments` aggregates record sense, while `nearest_segment_features` returns only geometry (`d`, `seg_id`, `phi`, `u`, `L`, `on`) and drops the sense field. Corrected the stale module/return-value documentation to make that scope explicit. The active H57 path is `anatomy.fold_geometry`, not this legacy module. Archived `scripts/explore_zone.py` calls undefined `faultzone.assign_sense_from_tracemap`; it and `explore_zone2.py` are explicitly marked historical, not active.
- Confirmed that `training_features.tif` is absent. Tests now distinguish the missing, gitignored large raster from a successful all-pins verification; the untracked-data test is skipped with an explicit reason.
- Added regression tests for the shared evaluator, globally aligned crop blocks, fail-closed writer packaging, both pre-placement and final-dot uniqueness gates, runtime inventory paths, exclusion of the audited candidate and NaN diagnostics, and saved-OOF promotion stops. Replaced the obsolete uniqueness CLI's hard-coded `/home/user/registry` dependency with the pinned/runtime local inventory; it exits nonzero unless both the surface and final-dot phases pass, and reports the missing surface as `NOT RUN` unless supplied.

## Pass 3 — claims, site, and promotion recheck

- Updated README, generated site pages, research hypotheses, registry provenance notes, and the single JSON run card so owner-reported leaderboard values are not labeled organizer-confirmed.
- Rechecked that the valid saved `no_side` OOF comparator is labeled `HOLDOUT-DTI`, has 22,641 withheld positives and a four-quadrant jackknife 95% CI `[0.216433, 0.285166]`, and is explicitly not cap-matched.
- Rechecked that `d` and `d_perp` canary flags remain visible and unresolved, and that missing slip-sense conditioning and pre-placement uniqueness prevent promotion.
- Final verdict: **negative / do not submit**. The GeoTIFF is downloadable and locally format-validated, but it is not cleared as a competition submission. No organizer receipt or live score is claimed.

## Test result

`49 passed, 1 skipped` (`.venv/bin/pytest -q`; 50 tests collected). The one expected skip is the all-data-pin test because the 418,912,844-byte gitignored `training_features.tif` is absent; a separate test verifies that the missing-file condition is reported. `.venv/bin/python -m compileall -q src scripts tests` and `git diff --check` passed after the latest uniqueness helper and regression-test changes.
