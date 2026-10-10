# Three-pass review record — H57 submission-integrity repair

Date: 2026-10-09 (UTC)

**Scope note:** This three-pass review covers the PR #8 candidate and its pre-merge code snapshot only. It is an archived integrity record, not the current main-line H57 release assessment; use the current README and `evidence/run_card_current.json` for that. The public owner-repository inventory discussed here is not a complete organizer registry; private, unlinked, external, and otherwise inaccessible rasters may be absent.

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
- The pre-merge `no_side` summary could not be matched to a raw result receipt in the integrated evidence tree, so it is not carried forward as a verified score. The newer main-line run card is authoritative.
- The pre-merge candidate's `d`/`d_perp` canary flags, missing sense conditioning, and absent pre-placement surface remain documented as historical blockers for that artifact; they are not substituted for the newer main-line diagnostics.
- Final verdict: **negative / do not submit**. The GeoTIFF is downloadable and locally format-validated, but it is not cleared as a competition submission. No organizer receipt or live score is claimed.

## Test result

`89 passed, 2 skipped` (`.venv/bin/python -m pytest -ra`; 91 tests collected). Both skips require the 418,912,844-byte gitignored `training_features.tif`, which is absent in this checkout; a separate test verifies the missing-file condition. `scripts/check_site.py` passed (28 pages, local format and links pass, current card consistent, submission not cleared). `.venv/bin/python -m compileall -q src scripts tests` and `git diff --check` passed.

## Main-line integration validation — 2026-10-10

- Integrated PR #8 head `58840b86` with current `origin/main` `5309c85a` (including Session 5 / PR #18), preserving the newer main-line H57 run card, candidate, and witness-verification evidence. The older PR #8 artifact and its research slate are labeled historical; no candidate was rebuilt.
- Kept main's newer `metric.max_cover` return contract (distance grid) and routed active `fitting.run_cell` scoring through the shared evaluator. Targeted evaluator/pipeline tests: **16 passed**; after the final Session 5 merge, the full suite again passed: **89 passed, 2 skipped**.
- Repaired the inventory wording across README, site, run cards, and gate tooling. The evidence is an indexed public owner-repository inventory, not a complete organizer registry; private, unlinked, external, and otherwise inaccessible rasters may be absent. Session 5's 19 local raster re-check is an even narrower cache slice, not a replacement for that index.
- The Session 5 witness is a raster measurement, not a score; it corroborates the existing STOP and is not a new registry scan performed during this integration. No new experiment or organizer submission was run.


## Current prompt execution audit — 2026-10-10 UTC

**Scope:** Review of the current fault-zone-anatomy request and repository state. The recorded three-experiment / two-hour budget is spent. This audit performed documentation, code-provenance, test, and static-site checks only; it did not perform a geological experiment, holdout run, data download, candidate TIFF build, or competition submission.

### Pass 1 — requirements and evidence

- Re-read the status-first README, preserved request ledger, `BRIEF.md`, `REMAINING_WORK.md`, current JSON card, holdout/witness records, H33-2-B2 raster audit, hypothesis evidence, source checks, and publisher/site code.
- Confirmed that the current governing request is the single fault-zone-anatomy lane and the literal pre-placement/final-dot uniqueness rule; no broad geothermal-resource or vent-prediction method was added.
- Retained four untried hypotheses and made their relative DTI upside explicitly qualitative, low-confidence research priors, with implementation cost and data readiness. No numerical DTI gain was inferred.
- The independent 17GEMSDOE witness covers every allowable cell. Under the unchanged >70% 3-pixel forward-overlap rule, any nonempty candidate is blocked. Consequently no new TIFF was made; this is required by the protocol STOP, despite the standing desire for a downloadable submission.

### Pass 2 — code, data, and tests

- Verified current code hashes against the stored holdout receipt: `evaluate_holdout.py` differs; `holdout.py`, `metric.py`, and `spatial.py` match. Thus the stored `HOLDOUT-DTI` results remain historical and no current-code holdout claim is made.
- Confirmed `data/official/training_features.tif` is absent and the full local registry cache remains 0/679. `scripts/build_submission.py` is a retired no-output stub. No data downloads or raster generation were attempted.
- Added regression coverage that the hypothesis page renders every evidence-backed candidate, physical signature, mimic, qualitative upside, and implementation cost.
- **LOCAL-QA (not a model score):** `.venv/bin/pytest -q -ra --junitxml=evidence/tests-session6-review.xml` — 108 collected; 106 passed; 2 skipped; 0 failures; 10 warnings. Both skips require the absent, gitignored feature raster. JUnit evidence is saved in `evidence/tests-session6-review.xml`.

### Pass 3 — source, site, and status

- Rebuilt the GitHub Pages content from the current run card and checked all 28 HTML pages. Internal links resolve; no active TIFF/ZIP download links remain; HOLD is prominent; run-card/hypothesis/irregularity JSON copies agree.
- Flagged the GeoDAWN metadata nuance: GDR submission 1591 displays CC-BY 4.0, while the linked USGS/ScienceBase record is separately recorded as CC0 1.0. This is not established as a legal conflict; the exact binary asset/license, coverage, bands, CRS, and alignment remain unverified. Candidate FZA-U4 is therefore not currently viable.
- The H33-2-B2 figure `0.2778` remains owner-reported/public-board context without a submission-page receipt tying the exact bytes to it. Raster measurements show a two-pixel prune of its base, but do not prove why the reported score occurred. No higher score is claimed or projected.
- **Final status: HOLD — NOT OK TO DOWNLOAD OR SUBMIT.** No new TIFF, holdout result, external data, or submission was produced.

The machine-readable results are in `evidence/run_card.json` and `evidence/review_passes.json`.
