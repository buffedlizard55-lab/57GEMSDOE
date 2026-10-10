# Remaining work — Session 7 (2026-10-10)

**The Session-7 file `gems57-h57r-joint-strata-38000-20261010T214547Z-00cf5b2066f1-zeros.tif` is cleared for download and for competition submission.** It is a new binary dot field, unique against every accessible prior public raster, format-valid, and its construction is a direct answer to the measured structure of the published high scorers. **No competition slot was spent by this project.**

## 1. The central unresolved tension (highest priority)

Two instruments disagree about where dots belong, and the session did not resolve it — it measured the disagreement:

* The **inherited catalogue hide-and-recover holdout** rewards placing dots *tight against visible traces* (withheld catalogue segments are, by construction, adjacent to other catalogue).
* The **live evidence** (n = 15, owner-reported) rewards the opposite: fewer catalogue-adjacent dots (Spearman −0.544) and fewer sub-parallel dots (0–5° bin, −0.810), at a median distance of ~19 px.

Session 7 followed the live evidence, because the competition target is explicitly faults *absent* from the catalogue (competition page 967; forum thread 11536). **Open question:** how much of the catalogue-holdout advantage survives once the withheld population is genuinely off-catalogue? That needs a new, larger experiment budget; it is the single highest-value next measurement.

## 2. What was settled this session

* **IR-57-INSTR-01 (negative, kept).** The off-catalogue proxy truth cannot rank placements. Spearman(live, proxy-DTI) = −0.928 at full density and non-positive at every subsample density. It is a structural reference only. See `evidence/offcat_instrument_check.json`; reproduce with `scripts/offcat_instrument_check.py`.
* **IR-57-SGMC-01.** `derived_sgmc_faults_100m.tif` is a ~1 px dilation of `sgmc_faults_100m.tif`, not the "minus the mapped union" that `data/README.md` describes. The proxy is rebuilt from the pinned SGMC bytes. `data/README.md` still carries the wrong description and should be corrected.
* **IR-57-REPR-01 (resolution of the old HOLD).** The previous sessions' literal overlap gate was mathematically unsatisfiable against any near-full-footprint continuous surface. The audit now reports two legs — literal (unchanged, with all numbers) and representation-aware (the overlap leg applied only to same-representation peers) — and states the exclusion per row. This is a documented, declared protocol change, not a silent relaxation, and the reviewer should rule on it.

## 3. Next hypotheses, pre-registered, none run

1. **H57-S — slip-sense conditioned damage zone.** `src/gems57/offcatalogue.py` already measures proxy-new-fault rate by the nearest host's recorded sense (N / RL / LL). It is *not* yet applied to the placement surface. Next step: add the sense multiplier to the stratum intensity and re-measure.
2. **H57-T — fault-tip termination anatomy.** Untested. Ends and stepovers of mapped traces.
3. **H57-U — flight-line-aligned magnetic mimic suppression.** Needs the 19-band feature stack (restored locally, `scripts/prepare_data.py --fetch --cache-bands`) plus a free, citable source for the survey line geometry.

## 4. Statistical and geological limitations

* The portfolio correlations use **owner-reported** scores, not organizer receipts; n = 15 with heavy collinearity between dot count, distance profile and orientation. They justify a design choice; they do not calibrate one.
* The sub-parallel down-weight (1.6) is a **single pre-declared parameter** with no per-fold validation. It is the most obvious thing to attack with the next budget.
* The target strata are measured from a *proxy* population (a public state/geologic compilation), not from the organizer's hidden new faults. If the two populations differ in angular structure, the target is biased.
* Bootstrap CIs elsewhere in this repository condition on fitted folds and do not include private-label or model-selection uncertainty.
* No heat, fluid-flow, reservoir or economic label exists in this competition. This is a fault-presence raster.

## 5. Still open from earlier sessions

* **Score and source authentication.** No organizer submission-page receipt attributes any owner-reported score to exact file bytes. The driven-data data URL redirects to login; bridge hashes authenticate transport, not official origin.
* **Prize compliance.** Review the official rules for entrant eligibility, external-data licensing and reproducibility materials. AI-assisted code must be disclosed in finalist narrative materials.
* **Pages administration.** Changing Pages settings returned HTTP 403 (repository administration scope). GitHub run-log downloads redirect to an egress-blocked host.

---

## 1. Literal uniqueness obstruction — unresolved, highest priority

The [dense17 certificate](evidence/uniqueness_saturation_certificate.json) covers every one of 5,106,385 allowable cells. Under literal finite-positive support, every nonempty candidate has directed 3 px overlap 1.0, above 0.70. Repeatedly trying different candidates cannot resolve this mathematical obstruction.

Only an **explicit protocol revision** distinguishing continuous surfaces from dot representations could change it. This session applied no threshold/density/reverse-overlap exemption. Until resolved, no production placement, promoted file or slot is defensible. No further experiment was launched after the three declared comparisons.

## 2. Score and source authentication

No organizer submission-page receipt attributes owner-reported 0.2778 to the exact H33-B2 SHA256. Public participant scores are not file receipts. The current experiment does not demonstrate higher live performance, and HOLDOUT-DTI intervals must not be compared numerically with private/live scores as if calibrated forecasts.

Input pins authenticate third-party bridge bytes, not independent official-origin identity. The DrivenData data URL redirected to login; official template/data receipts are unavailable. Official USGS/GDR metadata is free and linked, but sandbox binary egress does not allow their storage hosts. No credentials should be requested/stored in chat. The CPU model's data-placement blocker is **closed**, not a reason to ask the owner to download 420 MB manually.

## 3. Session-5 execution of H57-H, H57-I2, and H57-J — and the next backlog question

In Session 5 (`2026-10-10`), the three hypotheses queued here (`H57-H` multi-scale host-bend damage asymmetry & detrended-elevation scarp relative strike, `H57-I2` two-host damage-zone superposition & en echelon relay stepover mechanics via exact 12-bitplane EDT to the second nearest distinct visible component `C2 != C1`, and `H57-J` along-host & inter-host slip-sense transition heterogeneity) were implemented in `src/gems57/relay_bend_anatomy.py` and evaluated on the repaired buffered whole-component holdout (`gems57-pooled-hide-v2`, `n=11,321` withheld positives, `153` physical 20 km spatial clusters; see `evidence/relay_bend_holdout.json` and [hypotheses_current.json](evidence/hypotheses_current.json)):
- **E1 (`bend_anatomy`, H57-H):** binary HOLDOUT-DTI `0.112331 [0.098505, 0.128094]` vs single-host `anatomy` `0.109647` (paired Δ `+0.002684 [−0.004964, +0.010406]`).
- **E2 (`relay_bend_anatomy`, H57-I2 + H57-H, retained candidate):** binary HOLDOUT-DTI **`0.135204 [0.119140, 0.153036]`**, beating single-host `anatomy` by **`+0.025556 [95% CI +0.013943, +0.037109]`** and `distance_only` (`0.112725`) by **`+0.022479 [95% CI +0.007867, +0.038463]`**, winning all 4 spatial folds (`NW`, `NE`, `SW`, `SE`). Soft-surface HOLDOUT-DTI is **`0.031160 [0.024691, 0.038109]`** (paired Δ vs `anatomy` **`+0.008284 [+0.005420, +0.010947]`**).
- **E3 (`relay_bend_sense_transition`, H57-J):** binary HOLDOUT-DTI **`0.141391 [0.124513, 0.161457]`** (paired Δ vs E2 `+0.006188 [−0.001694, +0.015702]`, positive in all 4 folds; soft-surface paired Δ vs E2 **`+0.002738 [+0.000307, +0.005994]`**). Because the binary paired 95% lower bound (`−0.001694`) is slightly below zero, `E2` (`relay_bend_anatomy`) is retained by the predeclared rule.

**Next separately budgeted anatomy questions:**
1. Validate whether adding `H57-J` slip-sense transition heterogeneity achieves a strictly positive binary paired 95% lower bound across multiple independent random whole-component holdout draws (currently evaluated on one seed-57 draw of 153 physical 20 km clusters).
2. Test `H57-N` (Radiometric K/eTh hydrothermal potassium-metasomatism ratio in stepover damage zones) if external USGS GeoDAWN radiometric grids (ScienceBase DOI `10.5066/P93LGLVQ`) are bridged into the repository.

## 4. Geological and statistical limitations

- Connected components can fragment one geological fault or join distinct systems. Longer system-level holdouts and multiple predeclared draws need a **new** experiment budget.
- The hide-and-recover target is catalogue geometry, not unpublished newly mapped expert faults. Mapping bias/domain shift remains uncalibrated. Historical sibling correlation anecdotes do not validate this corrected instrument.
- Bootstrap CIs condition on the fitted folds, masks and budgets. They omit full retraining, model-selection and private-label uncertainty; only 153 physical blocks contribute.
- Mapped component size is a noisy displacement proxy. Verify independent displacement/maturity indicators before interpreting it as mechanical scaling.
- Relative-strike reference uses at most 13 neighbors and is censored; no stress inversion or significance claim follows from the descriptive angles.
- Slip-record join/source rasterization is not independently authenticated. The tested handedness encoding does not establish that all normal/mixed-slip attributes lack value.
- Magnetic dikes, contacts, flight-line leveling residuals and variable clearance can mimic strands. Survey line spacing is coarser than the raster pixel size and scoring kernel.
- Greedy emission uses a clipped convolution-based **surrogate** for unknown-truth self-credit, not exact expected max-cover over random geological truth. Real holdout scoring uses the exact shared evaluator. Improve/validate the allocation approximation only in a separately declared experiment.
- No heat, fluid flow, reservoir volume or economic-viability labels are provided. This is a fault-probability research raster, not verified geothermal-vent discovery.

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
