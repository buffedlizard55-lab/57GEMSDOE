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


## Session 6 (2026-10-10) — three passes

Full record: `evidence/review_passes.json` (entries `session-6-1` to `session-6-3`).

- **Pass 1 (implement and verify):** re-fetched all 679 indexed rasters with blob, SHA256 and grid checks (0 errors); reran the literal gate on that complete cache (78 firings, reproducing the historical scan); measured a 37,654-pixel raster as a subset of a 40,199-pixel base with 2,545 near-catalogue pixels removed (all 1.41–2.00 px from the catalogue). **Later owner-source review supersedes the old score labels:** H33-2-B2 is marked UNSCORED, 0.2778 is unverified, and the 0.2708 file attribution is contradicted. The subset is a file-geometric result only, not a score-to-file relation; see `evidence/owner_score_reconciliation_session4.json`.
- **Pass 2 (review):** fixed a stale checker guard that would have failed the verified state, a boundary error in one of my own tests, loose partition and overlap wording in the ledger, and stale cache statements in four documents. Full list in the JSON record.
- **Pass 3 (re-check against the request):** Session 6 itself created no new candidate or holdout result and used no slot. At that point, main still linked the Session-5 TIFF as a research download despite the literal STOP; Session 6 recorded the unresolved conflict as IR-S6-10. The follow-up below resolves the operational status conservatively without changing the uniqueness rule.

## Merge reconciliation and permission review — 2026-10-10

- Merged the latest `origin/main` Session-6 evidence (`fab2657`) into this branch without replacing its 696-raster audit, mechanism analysis, or pre-registered hypotheses. Updated the PR work to the latest state; no experiment, holdout, candidate build, external data download, or submission-slot use occurred.
- Resolved IR-S6-10 **operationally and fail-closed**: no explicit owner authorization to download the Session-5 research TIFF was recorded, so both `okay_to_download` and `okay_to_submit` are false. Removed TIFF/ZIP links from generated pages; retained bytes remain for provenance/validation and may still resolve via direct static URL, which is not permission. The uniqueness threshold and surface-vs-dot definition were not changed; IR-S6-01 remains open.
- Updated the overview/executive/site archive, README, BRIEF, run cards and audit ledger to show the current permission explicitly. The public feed now displays selected rows, exact retrieval time/method, stale/failure status, and repeated non-receipt/no-attribution caveats. The later 20:40 UTC snapshot records DARD at rank 8 (an earlier snapshot recorded rank 7); the shift is preserved, not treated as an exact-file receipt.
- Corrected the historical holdout reconciliation: H57-K remains leakage/provenance-invalid for cross-session ranking; Session-5 E2's paired `HOLDOUT-DTI` gains are reported only within its recorded split/evaluator, not as a new run or competition score. Four fault-anatomy hypotheses and the Session-6 protocol shortlist remain unrun; no numerical gain forecast is made.
- Validation: `pytest` **133 passed, 2 skipped / 135 collected**; skips require the absent 419 MB `training_features.tif`. `scripts/check_site.py` passed **30 HTML pages**, run-card/byte/ZIP checks and link checks, with zero TIFF/ZIP page links, download clearance false, and submission clearance false. Python compile check passed. No live competition page, private score or organizer file receipt was accessed.

---

## Follow-up — PR #29 provenance reconciliation (2026-10-10)

This review is distinct from the archived 2026-10-09 review above. Scope: preserve the newer mainline and the separate Session-4 H57-K junction-distance experiment while correcting score-to-file provenance and preparing PR #29 for merge. No modeling experiment, holdout rerun, TIFF build, download authorization, or competition submission occurred.

### Pass 1 — integration and fail-closed code review

- Confirmed the target branch is `arena/779294eb-57gemsdoe`, PR #29 targets `main`, the local merge has no unresolved Git conflicts, and the Session-4 junction experiment remains in its dedicated evidence/page rather than being conflated with mainline strand-expression H57-K.
- Reviewed the legacy score-anchored H57-K build, emitter, calibration, credit-shell, proximal-sweep, and model-comparison entry points. They stop before candidate work; the archived model comparison was also disabled. No TIFF-generation path was executed.
- Ran `scripts/registry_budget.py --rows-only`; it recomputed 13 eligible owner-reported rows from raster bytes, Spearman `-0.7686` (`p=0.00214159`), excluded the two disputed mappings, and did not write evidence.

### Pass 2 — score provenance, evidence, and permission review

- Reconciled against the inspected GEMSDOE32 owner README and the machine-readable audit: H33-2-B2 is **UNSCORED**; `0.2747` is a projection; `0.2778` is an unverified owner claim without an exact-file submission receipt; the H27-4 / `0.2708` attribution is contradicted. None is labeled ORGANIZER-CONFIRMED.
- Kept owner claims, local HOLDOUT-DTI, projections, and organizer receipts distinct in registry data, copied evidence, legacy audit artifacts, and the generated report table. Historical model arithmetic and raster geometry remain explicitly non-score evidence.
- Confirmed the Session-4 junction-distance run's local HOLDOUT-DTI and CI are separate from current mainline. Its pre-placement rank gate passed the two checked witnesses, but directed 3-px overlap was `0.998724` and `1.000000` (limit `0.70`); no final dots, TIFF SHA, or validator result exists for that run.
- Rebuilt the static site. No TIFF was generated or cleared; current download and submission permissions remain false.

### Pass 3 — independent tests and delivery check

- `.venv/bin/python -m pytest -q --junitxml=evidence/tests-pr29.xml`: **152 collected, 150 passed, 0 failed, 2 skipped**. Both skips require the ignored 419 MB feature TIFF or `.cache` band file absent from this checkout snapshot; prior hash receipts remain historical and no refetch was performed.
- `compileall`, JSON parsing (197 files), and `git diff --check`: pass.
- `scripts/check_site.py`: **31 pages**, links and local format/ZIP identity pass; `research_download_cleared=false`, `submission_cleared=false`. The retained audit TIFF SHA256 remains `cf7b903dd9e669fb6ef71241e6e5e3e840acd2f39df7d599f8472b2d9a489648`.
- At this review point PR #29 is open against `main` and the validated merge commit is pushed to the intended branch. GitHub reported no status checks or workflow runs and still returned `mergeable=UNKNOWN`; the explicit merge action remains pending.

Machine-readable record: `evidence/review_passes.json` → `pr29_provenance_cleanup_20261010`. Final merge outcome will be added there after GitHub reports it.
