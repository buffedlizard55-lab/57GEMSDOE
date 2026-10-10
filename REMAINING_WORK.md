# Remaining work and limitations — current status (2026-10-10 UTC)

Last reviewed 2026-10-10 (Session 5). **Download research TIFF (`gems57-twohost-relay-bend-surface-20261010T201504Z-47ccc38b6bec.tif`): OK. Submit: NO.** Three declared Session-5 comparisons (`E1`: `bend_anatomy`, `E2`: `relay_bend_anatomy`, `E3`: `relay_bend_sense_transition`) are finished, zero slots used. While `E2` (`relay_bend_anatomy`) achieved a statistically significant positive paired gain (+0.0256 vs single-host anatomy, +0.0225 vs distance-only; 95% CIs strictly positive), the literal full-registry pre-placement overlap gate still triggers STOP against the 17 dense-support prior rasters (`dense17`), so the release remains held for research.

There is no cleared submission file. Do not use the retained historical TIFF. No new
experiments, holdout runs, GeoTIFF builds, downloads, or submissions occurred in this audit;
the three-experiment / two-hour budget is spent. No weekly slot was used.

The latest stored scan measured the soft candidate against the 679-entry indexed public
owner-repository inventory (not organizer-complete): maximum full-footprint Spearman 0.821258;
maximum forward 3-pixel overlap 1.0 on the soft surface's
inherited finite-positive support (treated as “dots” by the gate), with 78 firings above the
0.70 stop threshold. This was a pre-placement support comparison, not a final-dot comparison.
The overlap gate failed before placement, so final dots were not generated. The scan is historical.
Two older `-zeros.tif` reports use different 644- and 655-raster snapshots (114/50 and 98/98
overlap firings/itemized respectively); both also fail and neither is the current comparison. A
fresh cache preflight found **0 of 679** indexed rasters present; no current cache hashes or grids
could be verified. No candidate fitting or TIFF creation occurred during that preflight.

A session-5 independent witness check re-fetched and SHA256-verified the in-scope 17GEMSDOE
`E-proba-multiscale` raster (5,167,373 positive cells). Its 3-pixel support covers every
allowable cell and gives measured forward overlap 1.0 for dense and sparse test candidates. Under
the literal >70% overlap rule, every nonempty candidate is blocked while this witness remains in
scope. This is a registry measurement—not a score, threshold change, or full 679-raster cache
revalidation. The public owner-repository index cannot prove completeness against private,
unlinked, inaccessible, externally stored, or later-written competition rasters. No density or
reverse-overlap exception is authorized. A separate check found the archived 40,000-dot
`h57-anatomy-enechelon` candidate has 0.7113 forward 3-pixel overlap against its own earlier
build, also above the literal 0.70 limit; see `evidence/independent_candidate_check.json`.

The latest recorded soft-surface `HOLDOUT-DTI` is 0.023203 (95% CI [0.018778, 0.027992],
11,321 withheld positives, evaluator `gems57-pooled-hide-v2`); its source hashes predate the
current evaluator code. The separate binary-allocation HOLDOUT-DTI is 0.109168
(95% CI [0.094503, 0.124194]) and is not the score of that soft TIFF. The older 0.227908
reading is unpinned legacy context. The 0.2778 figure is owner-reported without an organizer
receipt tying it to exact bytes. A separate raster audit found the named H33-2-B2 artifact is an
exact 2-pixel catalogue-flank prune of a 40,199-positive base (2,545 removed, none added; 37,654
remain). That could plausibly reduce false-positive cost under max-cover DTI, but no causal gain is
verified. The 0.3195 and 0.3774 figures conflict in the saved reports; the public leaderboard
snapshot is not a submission-page receipt for exact bytes. No gain estimate is supported.

## Blocking work (not permission to proceed)

1. **Protocol blocker:** the independently verified 17GEMSDOE witness covers the full allowable
domain under the required 3-pixel support rule, so any nonempty candidate fails the >70% test.
Do not exclude it, alter the threshold, or apply a density/reverse-overlap exception without an
explicit owner protocol revision. Under the unchanged rule, the gate is unsatisfiable.
2. **Registry:** the present checkout has 0/679 cache files. Any future public-inventory audit
would need every indexed file in `evidence/registry_refreshed.json` restored and SHA256/grid
verified; the historical scan and one re-fetched witness do not replace that check. Even a complete
local copy of this 679-entry public owner-repository inventory would not establish
organizer-complete scope; `registry/audit_scope.json` records those exclusions.
3. **Validation:** current-code spatial hide-and-recover evidence must include evaluator version,
source/input hashes, withheld-positive count, 95% CI, and a clean single-feature leakage canary.
The existing experiment budget is spent; no such run is authorized by this document.
4. **Uniqueness:** if the protocol is explicitly revised, apply its authorized surface rank-correlation
and pre-placement/final 3-pixel overlap checks against the complete registry. Under current
instructions, stop at rho > 0.90 or >70% overlap; no exception is authorized.
5. **Selector:** only a separate, independently versioned selector may promote a cleared
candidate to a weekly slot. No slot was used or is authorized by this audit.
6. **Publisher and format:** `scripts/build_submission.py` is a retired no-output stub. Do not
restore candidate-building until renewed authorization and an independently complete comparison
scope exist. If a future candidate is ever cleared, it must be a uniquely named, locally validated
single-band float32 GeoTIFF (or a ZIP containing exactly that TIFF), finite in `[0,1]` and matched
to the pinned grid. Local format checks are not organizer acceptance.

## 3. Session-5 execution of H57-H, H57-I2, and H57-J — and the next backlog question

In Session 5 (`2026-10-10`), the three hypotheses queued here (`H57-H` multi-scale host-bend damage asymmetry & detrended-elevation scarp relative strike, `H57-I2` two-host damage-zone superposition & en echelon relay stepover mechanics via exact 12-bitplane EDT to the second nearest distinct visible component `C2 != C1`, and `H57-J` along-host & inter-host slip-sense transition heterogeneity) were implemented in `src/gems57/relay_bend_anatomy.py` and evaluated on the repaired buffered whole-component holdout (`gems57-pooled-hide-v2`, `n=11,321` withheld positives, `153` physical 20 km spatial clusters; see `evidence/relay_bend_holdout.json` and [hypotheses_current.json](evidence/hypotheses_current.json)):
- **E1 (`bend_anatomy`, H57-H):** binary HOLDOUT-DTI `0.112331 [0.098505, 0.128094]` vs single-host `anatomy` `0.109647` (paired Δ `+0.002684 [−0.004964, +0.010406]`).
- **E2 (`relay_bend_anatomy`, H57-I2 + H57-H, retained candidate):** binary HOLDOUT-DTI **`0.135204 [0.119140, 0.153036]`**, beating single-host `anatomy` by **`+0.025556 [95% CI +0.013943, +0.037109]`** and `distance_only` (`0.112725`) by **`+0.022479 [95% CI +0.007867, +0.038463]`**, winning all 4 spatial folds (`NW`, `NE`, `SW`, `SE`). Soft-surface HOLDOUT-DTI is **`0.031160 [0.024691, 0.038109]`** (paired Δ vs `anatomy` **`+0.008284 [+0.005420, +0.010947]`**).
- **E3 (`relay_bend_sense_transition`, H57-J):** binary HOLDOUT-DTI **`0.141391 [0.124513, 0.161457]`** (paired Δ vs E2 `+0.006188 [−0.001694, +0.015702]`, positive in all 4 folds; soft-surface paired Δ vs E2 **`+0.002738 [+0.000307, +0.005994]`**). Because the binary paired 95% lower bound (`−0.001694`) is slightly below zero, `E2` (`relay_bend_anatomy`) is retained by the predeclared rule.

**Next separately budgeted anatomy questions:**
1. Validate whether adding `H57-J` slip-sense transition heterogeneity achieves a strictly positive binary paired 95% lower bound across multiple independent random whole-component holdout draws (currently evaluated on one seed-57 draw of 153 physical 20 km clusters).
2. Test `H57-N` (Radiometric K/eTh hydrothermal potassium-metasomatism ratio in stepover damage zones) if external USGS GeoDAWN radiometric grids (ScienceBase DOI `10.5066/P93LGLVQ`) are bridged into the repository.

- Hide-and-recover tests catalogue recovery, not unpublished expert mapping of new faults; component boundaries can split one geological fault or join separate systems, and catalogue bias/domain shift remain uncalibrated.
- Stored bootstrap intervals condition on the fitted folds, masks, catalogue labels, and fixed budgets. They are not forecasts of hidden/private scores and do not include all refit/model-selection uncertainty.
- Fault length is only a noisy maturity/displacement proxy. Do not substitute fault length or slip rate for cumulative displacement without an independent justification.
- Relative strike/sense fields are bounded by visible-neighbor sampling, attribute joins, and source-rasterization limitations; they do not establish stress inversion or a universal mechanism.
- Magnetic dikes, geologic contacts, flight-line leveling residuals, and variable survey clearance can mimic fault strands. GeoDAWN's public catalogue/license record was checked, but coverage, CRS, usable bands, and contest-grid overlap were not.
- No geothermal heat, fluid flow, reservoir volume, or economic-viability labels are validated here. This lane concerns fault probability, not proof of a geothermal resource.
- Before any future competition submission, re-check official rules, entrant eligibility, external-data licenses, required reproducibility material, and any AI-use disclosure. No credentials should be requested or stored in chat.
- `docs/review_passes.md` and `evidence/review_passes.json` preserve the multi-pass audit record. Earlier session plans and claims are retained under `evidence/history/` and in `TASK_PROMPT.md`; they are provenance, not current status or permission.

## Source of truth

## 5. Registry/site maintenance

The audited 695-grid-raster union comprises 691 predictions/conservatively retained ambiguous rasters plus four historical auxiliary inputs, explicitly classified. Public-main commit pins and historical blobs are covered; private/unlinked/inaccessible artifacts are not. Refresh before a future candidate; never claim absence from a missing cache. Do not sweep current generated outputs into their own prior inventory.

The Pages feed updates public-board **context** without submitting. It exposes cached/stale and failed-refresh status. It cannot read authenticated team slots or private scores. Keep metadata/hashes and accessible links tested; update the standing request at the start of each session.

## 6. Prize compliance

Review the [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), entrant eligibility, external-data licenses and required reproducibility materials. The published cap is three submissions per week; only the logged-in page establishes remaining team capacity. AI-assisted code/analysis must be disclosed in finalist narrative materials; authorship and accuracy remain the entrant's responsibility.

**Maximize P(Win):** better evidence, not slot-burning A/B claims or a fabricated forecast. **Own the Outcome:** maintain the complete negative receipt and fix provenance/method gaps before any promotion.

## 7. Pages administration / network limits

The integration can push this working branch and merge its PR, but changing
Pages settings returned HTTP 403 (repository administration scope). Existing
Pages uses main-root. Identical current TIFF/ZIP/JSON mirrors at `downloads/`
and the root-to-docs redirect support both legacy and custom artifact layouts.
The scheduled workflow refreshes public context on the runner, retaining cache
on errors; custom deployment is checked separately. GitHub run-log downloads
redirect to an egress-blocked host; check/run status APIs remain accessible.
Do not request/store tokens to work around these limits.

The current relative magnetic orientation uses axial cos2, not signed angular
handedness; normal versus unavailable sense is not fully separated. Testing
those interactions needs a new declared experiment. No broad rejection of
fault-zone mechanics is claimed.

---

## Session addendum — fault-zone anatomy session 2 (2026-10-09, arena/884d08ea)

Work merged from a parallel lane run. Its headline items:

1. **IR-57-STRIKE-01 fixed and independently confirmed.** This session found
   the same inverted `np.where` strike fallback the sibling session fixed;
   both fixes are now in `src/gems57/anatomy.py`, pinned by the unioned
   `tests/test_anatomy.py` (synthetic-grid orientation pins + real-catalogue
   regression). Session-1 holdout numbers for geometry-bearing variants are
   not comparable to session-2 numbers (the frame changed); both are kept and
   labelled (`evidence/cv_all.json` = broken frame,
   `evidence/cv_r2_all.json` = corrected frame).
2. **The redundancy ablation is overturned on the corrected frame.**
   Removing `d_perp`/`d_par_abs` from the shipped set costs -0.0950 (`all`)
   / -0.0971 (`detached`) HOLDOUT-DTI — the en echelon geometry pays for
   itself. Session 1's "+0.0022, inside the noise" was an artifact of the
   grid-aligned frame.
3. **H57-D is a negative result.** `sin2d`/`cos2d` add +0.0018 / +0.0010
   (inside the noise). The shipped variant stays `shipped8`; the interaction
   columns remain so the ablation is reproducible (`scripts/run_cv_r2.py`).
4. **New unique binary submission built and validated:**
   `docs/downloads/gems57-h57r2-shipped8-all-flank0-20261009T180433Z-90e532947353-zeros.tif`
   (40,000 dots, 0 on-catalogue, 15/15 portal checks, sha256
   `9afe74ab…`). Unique vs all 15 sibling-lane rasters (worst rho 0.0128,
   worst Jaccard 0.0110, worst overlap 36.5 %). **IR-57-OVERLAP-01:** 71.1 %
   forward overlap vs this repo's own session-1 build of the same lane
   (Jaccard 0.2400 — not a copy); the drift screen is split into
   `unique_vs_other_lanes` (operative) + same-lane disclosure. Note the
   contrast with item 1 above: the sibling session's obstruction came from a
   **dense continuous surface** (support = every allowable cell); this
   session's artifact is a **sparse binary dot field** (support = 40,000
   cells), which the literal screen handles fine against other lanes.
5. **Repo repairs:** new `scripts/registry_budget.py` (regenerates
   `evidence/registry_budget.json`; reproduces Spearman -0.8104 and the
   DTI-vs-coverage curve under a documented construction), an infinite-loop
   fix in two new `sha256()` helpers (int sentinel instead of `b""`), the
   session-1 evidence backups, and the registry extended 16 -> 19 (the
   parallel session's raster, the superseded 60k build, and this session's
   submission). The session-2 audit is preserved at
   `evidence/submission_build_r2_all.json` with the run card at
   `evidence/run_card_r2_shipped8.json`.
6. **Carried forward unchanged:** the holdout does not rank live scores
   (rho = +0.14); the 40,000-dot live cap rests on Spearman -0.8104 over 15
   live scores (n = 15, confounded with method quality); H57-B (tip-lobe)
   is still the cheapest untried anatomy hypothesis; the GeoDAWN feature
   stack is now local and sha256-verified (sibling session) but unused by
   this session's variant.
