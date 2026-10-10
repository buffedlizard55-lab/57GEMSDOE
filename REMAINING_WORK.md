# Remaining work — do not bypass the current HOLD

## Session 7 addendum (2026-10-10) — next actions in priority order

Evidence: [evidence/run_card_session7.json](evidence/run_card_session7.json), [evidence/session7_irregularities.json](evidence/session7_irregularities.json). Status unchanged from main (PR #23): research download NO pending explicit owner authorization; submission NO; 0 slots used.

1. **Owner ruling on the dense-prior gate (IR-S7-01).** Decide how a soft raster that is positive on the whole footprint defines its "dots" for the 70 % 3-px overlap test. Until then, no candidate can pass the literal gate, whatever its content.
2. **Holdout redesign for near-trace truth (IR-S7-04).** The 3-px collar leaves withheld truth at least √10 px from any visible fault. A new validation needs (a) a collar of 0–1 px, or a design that keeps truth adjacent to visible traces, and (b) a leakage canary on the new split. Only then can dots within a few pixels of a known trace be scored. Test the 0.2778 mechanism (removing near-trace dots) only in that split.
3. **NaN-outside export (IR-S7-03).** Re-export the same soft surface with NaN outside the study footprint, as in the bridged template, and run the validator and the registry audit on the new bytes before any upload.
4. **Regenerate the Session-5 holdout receipt (IR-S7-06).** The stored evaluator hash does not match HEAD, though the numbers reproduce exactly. Rerun the holdout in a scratch copy and write the receipt with its current hashes.
5. **Official-origin checks (IR-S7-02, IR-S7-05).** Obtain a DrivenData download receipt for `labels.tif`, `existing_faults.tif` and `sample_submission.tif` if the account allows. Until then the bridged bytes stay bridge-only.

Budget: Session 7 used 2 of 3 experiments (reproduction; collar audit).

---

 **Download research TIFF (`gems57-twohost-relay-bend-surface-20261010T201504Z-47ccc38b6bec.tif`): OK. Submit: NO.** Three declared Session-5 comparisons (`E1`: `bend_anatomy`, `E2`: `relay_bend_anatomy`, `E3`: `relay_bend_sense_transition`) are finished, zero slots used. While `E2` (`relay_bend_anatomy`) achieved a statistically significant positive paired gain (+0.0256 vs single-host anatomy, +0.0225 vs distance-only; 95% CIs strictly positive), the literal full-registry pre-placement overlap gate still triggers STOP against the 17 dense-support prior rasters (`dense17`), so the release remains held for research.
Last reviewed 2026-10-10 (Session-6 follow-up). **Research download: NO pending explicit owner authorization (IR-S6-10). Submit: NO.** The Session-5 GeoTIFF/ZIP remain in the repository for provenance and audit, but the site has no TIFF/ZIP links; a direct static URL may still resolve and is not permission. The Session-5 card's research-download OK state was not explicitly resolved by an owner, so this follow-up fails closed. Three declared Session-5 comparisons (`E1`: `bend_anatomy`, `E2`: `relay_bend_anatomy`, `E3`: `relay_bend_sense_transition`) are finished, zero slots used. E2 achieved positive paired `HOLDOUT-DTI` differences (+0.025556 vs single-host anatomy, +0.022479 vs distance-only; 95% CIs strictly positive) on its recorded holdout, but the literal full-registry gate still triggers STOP against the universal-support witness. Session 6 verified 696 rasters and re-ran the gate: 80 duplicate firings, worst forward overlap 1.0.

## 1. Literal uniqueness obstruction — unresolved, highest priority

The [dense17 certificate](evidence/uniqueness_saturation_certificate.json) covers every one of 5,106,385 allowable cells. Under literal finite-positive support, every nonempty candidate has directed 3 px overlap 1.0, above 0.70. Repeatedly trying different candidates cannot resolve this mathematical obstruction.

Only an **explicit protocol revision** distinguishing continuous surfaces from dot representations could change it. This session applied no threshold/density/reverse-overlap exemption. Until resolved, no production placement, promoted file or slot is defensible. No further experiment was launched after the three declared comparisons.

## 2. Score and source authentication

No organizer submission-page receipt attributes owner-reported 0.2778 to the exact H33-B2 SHA256. Public participant scores are not file receipts. The current experiment does not demonstrate higher live performance, and HOLDOUT-DTI intervals must not be compared numerically with private/live scores as if calibrated forecasts.

Input pins authenticate third-party bridge bytes, not independent official-origin identity. The DrivenData data URL redirected to login; official template/data receipts are unavailable. Although Session 5 recorded a bridge-assembled 19-band stack, Session 6 reports `training_features.tif` absent in the current checkout and the feature link unreachable; a new holdout cannot run without an authorized, hash-pinned copy through an allowed route. Official USGS/GDR metadata is linked, but binary source coverage/alignment remain unverified. Do not request or store credentials in chat or treat old cache receipts as current access.

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

The Session-5 695-grid-raster union comprises 691 predictions/conservatively retained ambiguous rasters plus four historical auxiliary inputs, explicitly classified. Session 6 separately verified all 696 rasters in the updated index and re-ran the literal gate. Public-main commit pins and historical blobs are covered; private/unlinked/inaccessible artifacts are not. Refresh the index before any future authorized candidate; never claim absence from a missing cache. Do not sweep generated outputs into their own prior inventory.

The Pages feed updates ORGANIZER-PUBLISHED public-board **context**, not receipts, without submitting. It exposes the timestamp, selected-row scope, cached/stale state and failed-refresh status. It cannot read authenticated team slots or private scores. The current site removes TIFF/ZIP links because research download is not authorized pending IR-S6-10; retained bytes may still resolve by direct static URL, which is not permission. Keep the provenance/status copies and link checks synchronized; update the standing request at the start of each session.

## 6. Prize compliance

Review the [official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), entrant eligibility, external-data licenses and required reproducibility materials. The published cap is three submissions per week; only the logged-in page establishes remaining team capacity. AI-assisted code/analysis must be disclosed in finalist narrative materials; authorship and accuracy remain the entrant's responsibility.

**Maximize P(Win):** better evidence, not slot-burning A/B claims or a fabricated forecast. **Own the Outcome:** maintain the complete negative receipt and fix provenance/method gaps before any promotion.

## 7. Pages administration / network limits

The integration can push this working branch and merge its PR, but changing
Pages settings returned HTTP 403 (repository administration scope). Existing
Pages uses main-root. TIFF/ZIP/JSON mirrors remain in `downloads/` and
`docs/downloads/` for provenance and byte-integrity tests; generated pages do
not link them while IR-S6-10 download authorization is pending. A direct static
URL may still resolve; that is not access authorization. The scheduled workflow
refreshes public context on the runner and retains the last snapshot on errors;
the site publishes freshness/failure status. GitHub run-log downloads redirect
to an egress-blocked host; check/run status APIs remain accessible. Do not
request/store tokens to work around these limits.

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
