# Three-pass review record — H57 submission-integrity repair

Date: 2026-10-09 (UTC)

**Scope note:** This three-pass review covers the PR #8 candidate and its pre-merge code snapshot only. It is an archived integrity record, not the current H57-B assessment; use the current README and `evidence/run_card.json` for this review. `evidence/run_card_current.json` documents a separate older H57-K artifact. The public owner-repository inventory discussed here is not a complete organizer registry; private, unlinked, external, and otherwise inaccessible rasters may be absent.

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
- The pre-merge `no_side` summary could not be matched to a raw result receipt in the integrated evidence tree, so it is not carried forward as a verified score. The H57-B source-of-truth card at `evidence/run_card.json` governs the current review.
- The pre-merge candidate's `d`/`d_perp` canary flags, missing sense conditioning, and absent pre-placement surface remain documented as historical blockers for that artifact; they are not substituted for the newer main-line diagnostics.
- Final verdict: **negative / do not submit**. The pre-merge PR #8 TIFF had a local format-validation receipt but is archived in the current branch and is not cleared to download or submit. No organizer receipt or live score is claimed.

## Test result

`89 passed, 2 skipped` (`.venv/bin/python -m pytest -ra`; 91 tests collected). Both skips require the 418,912,844-byte gitignored `training_features.tif`, which is absent in this checkout; a separate test verifies the missing-file condition. `scripts/check_site.py` passed (28 pages, local format and links pass, current card consistent, submission not cleared). `.venv/bin/python -m compileall -q src scripts tests` and `git diff --check` passed.

## PR #16 latest-main integration validation — 2026-10-10

- Integrated the already-resolved PR #18/main snapshot `5309c85a` and then latest `origin/main` `bf6d9260` (PR #8 merge). Preserved the H57-B run card byte-for-byte and retained the no-raster/no-submission HOLD. PR #8 artifacts and its research slate remain explicitly historical.
- Kept H57-B's globally aligned `metric.dti_spatial_terms` evaluator and added the compatible `metric.max_cover` primitive expected by main's evaluator regression tests. Visible catalogue pixels are masked from scoring. The full suite passed: **100 passed, 2 skipped** (102 collected). Two data-dependent skips are expected because the 418,912,844-byte gitignored training-feature raster is absent.
- Retired `scripts/emit_h57k.py` as a fail-closed entry point after finding its obsolete Jaccard and blind-forward alternative gates and direct TIFF-emission path. Legacy Jaccard row fields were audited: reported `duplicate_count` values match only rank/forward-overlap triggers; the JSON receipts now label those legacy fields as diagnostics.
- Rebuilt and checked the site: 30 pages, local format and links passed, current card consistent, `submission_cleared: false`. The overview has no active artifact links; `docs/downloads/` and `downloads/` have no direct files. No H57-B TIFF was generated.
- The source card hash remained `27bacbec2620a4a2bb41ca14d68505dc646a9b6a9da8da2b4471bc41358a2923`. The training-feature pin is unverified and the file is absent in this checkout; no data was fetched and no experiment, submission, or slot selection occurred. The 679-raster set is an indexed public owner-repository inventory, not a complete organizer registry; the Session-5 19-file scan is narrower still.
