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

## Follow-up audit — 2026-10-10 (current scope; no modeling run)

This follow-up supplements, and does not rewrite, the dated historical review above. Current status and evidence are governed by `README.md`, `BRIEF.md`, `evidence/run_card.json`, and the 2026-10-10 reconciliation records.

### Pass 1 — scope, sources, and benchmark reconciliation

- Re-read the standing protocol, README, current run card, H57-K arms/run card, later orientation results, data manifest, and current public-registry blocker.
- Directly inspected `scripts/explore_zone.py`, `scripts/explore_zone2.py`, `scripts/run_sense_experiment.py`, `scripts/run_orientation_experiments.py`, `src/gems57/anatomy.py`, and the archived `docs/research/hypotheses_h57.md`. The older explorations measured distance/relative azimuth/along-strike position/length and marginal sense-conditioned distances; current historical experiments tested sense with broad geometry/orientation. The generic sense-by-angle/distance idea is therefore already tried. The older H57 slate had also proposed generic tip-relay, junction/stepover, and slip-rate ideas, but marked them unmeasured. The shortlist was corrected: rank 1 is now the narrower, still-unrun visible branch-topology × sense fit; recency-conditioned geometry is new to the inspected slate; the slip-rate item is explicitly marked as previously proposed but unrun. No global novelty claim is made.
- Reviewed the official DrivenData problem description and public leaderboard, GDR submission 1391 / QFault v2, GDR submission 1591 / GeoDAWN, the USGS GeoDAWN record, and USGS ScienceBase DOI `10.5066/P9YL58W6`. The public board is preserved as selected rows 1–22 only; it is not a submission-page receipt or exact-file attribution.
- Reconciled historical holdouts: H57-K's `d`, `d_perp`, and `vis_dtip` single-feature canaries cross the 0.90 leakage threshold, and the H57-K arm artifacts lack their own evaluator/input hashes. Later pooled-hide-v2 records use another split/count, have stored source hashes that do not match the current tree, and distinguish soft-surface from binary-allocation representations. No comparable current-code result was identified.
- No external data archive was downloaded, no host-level CSV join was tested, and no experiment or holdout was authorized or run.

### Pass 2 — evidence, shortlist, and feed/site implementation

- Added a SHA256-pinned, read-only CSV attribute inventory; it records completeness and frequency only, not spatial overlap, host correspondence, a feature, or a model result.
- Re-ranked four unrun within-lane hypotheses after novelty review: visible branch-end/junction topology × recorded-sense anatomy; slip-rate-conditioned anatomy (previously proposed, still unrun); recency-conditioned anatomy; and a data-gated USGS slip/dilation-tendency modifier. Each names layers, physical signature, why it could locate off-trace strands, repository-scoped novelty/prior work, a non-fault mimic, qualitative priority/cost, sources, and a future test gate. No numerical DTI gain is claimed.
- Fixed a public-feed integration gap: the refresh workflow previously wrote evidence without syncing the selected snapshot into `docs/data` or rendering provenance on the site. The builder now copies canonical feed/audit JSON and displays selected public-board values with retrieval scope, stale/failure context, and an explicit no-receipt/no-file-attribution warning. The scheduled refresh script remains public-board-only, hashes returned HTML without retaining it, and preserves a successful prior snapshot on failure.
- A full-suite review caught a regression-test contract requiring the blocker to say the literal gate is “unsatisfiable”; the shortlist now states this directly, with no threshold or uniqueness-policy change. A later feed-renderer test initially asserted “not a submission-page receipt” while the page correctly says “not a submission receipt”; the test expectation was fixed. Redirect allowlist, failure retention, and stale-snapshot warnings are covered without live network calls.

### Pass 3 — independent requirements, edge cases, and final checks

- Rechecked README's standing prompt/protocol, the prominent download/submission HOLD, no-active-download link rule, one-TIFF/grid/`[0,1]` guide, and all generated site pages. The public leaderboard rows remain classified as organizer-published context, never `ORGANIZER-CONFIRMED` exact-file scores.
- `.venv/bin/pytest -q -rs`: **115 collected, 113 passed, 2 skipped**. `tests/test_anatomy.py` skips because `training_features.tif` is not assembled; `tests/test_data_pins.py` skips because the 419 MB gitignored raster is absent. Existing raster-affine pending-deprecation warnings remain; no test failures.
- `scripts/check_site.py --build`: **PASS**, 28 HTML pages; HTML and reviewed Markdown local links resolve; HOLD is prominent; zero active TIFF/ZIP downloads; evidence/public JSON copies match; 0/679 registry cache and universal-overlap blocker remain explicit.
- `python -m compileall -q src scripts tests` and `git diff --check`: PASS.
- No geological experiments, holdout runs, feature joins, external-data archive downloads, TIFF/ZIP builds, submission-slot use, or organizer submissions occurred. The 3-experiment / 2-hour budget remains spent.

**Current verdict:** negative / not promoted / not cleared to download or submit. The checklist and hypothesis slate do not override the universal-overlap stop or authorize future model work. Current blockers and limitations remain in `REMAINING_WORK.md`.
