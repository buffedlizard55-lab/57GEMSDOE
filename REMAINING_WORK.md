# Remaining work — do not bypass the current HOLD

**2026-10-10 pre-placement addendum (supersedes historical Session-6 missing-data status below):** The permitted GitHub API restored `data/official/training_features.tif`; all eight bridge pins verified ([receipt](evidence/data_preparation.json)). The stack remains a third-party bridge, not a verified official DrivenData receipt. The literal uniqueness obstruction is independently rechecked on the pinned public-main 17GEMSDOE witness ([preflight](evidence/preflight_anatomy.json)); every allowed pixel is covered, so every nonempty candidate fails. Do not train/place a new submission until the protocol is explicitly revised, even though the missing-feature blocker is locally resolved. [Negative preflight card](evidence/run_card_preflight.json); zero new experiments and zero slots this addendum.

## Session 7 addendum (2026-10-10) — next actions in priority order

Evidence: [evidence/run_card_session7.json](evidence/run_card_session7.json), [evidence/session7_irregularities.json](evidence/session7_irregularities.json). Status unchanged from main (PR #23): research download NO pending explicit owner authorization; submission NO; 0 slots used.

1. **Owner ruling on the dense-prior gate (IR-S7-01).** Decide how a soft raster that is positive on the whole footprint defines its "dots" for the 70 % 3-px overlap test. Until then, no candidate can pass the literal gate, whatever its content.
2. **Holdout redesign for near-trace truth (IR-S7-04).** The 3-px collar leaves withheld truth at least √10 px from any visible fault. A new validation needs (a) a collar of 0–1 px, or a design that keeps truth adjacent to visible traces, and (b) a leakage canary on the new split. Only then can dots within a few pixels of a known trace be evaluated locally. A near-trace exclusion can be tested as a file/holdout mechanism, but must not be presented as an explanation of 0.2778: that remains an unverified owner claim with no exact-file receipt for H33-2-B2.
3. **Conditional export validation (IR-S7-03).** Do not emit or clear a TIFF under the current failed uniqueness rule. Only after an explicit owner ruling changes the applicable protocol may an export be built; then verify NaN-outside behavior, format, and registry uniqueness on the resulting bytes before considering any download or upload.
4. **Regenerate the Session-5 holdout receipt (IR-S7-06).** The stored evaluator hash does not match HEAD, though the numbers reproduce exactly. Rerun the holdout in a scratch copy and write the receipt with its current hashes.
5. **Official-origin checks (IR-S7-02, IR-S7-05).** Obtain a DrivenData download receipt for `labels.tif`, `existing_faults.tif` and `sample_submission.tif` if the account allows. Until then the bridged bytes stay bridge-only.

Budget: Session 7 used 2 of 3 experiments (reproduction; collar audit).

---

 **Historical text, superseded by the HOLD at the top: research download NO; submit NO.** Three declared Session-5 comparisons (`E1`: `bend_anatomy`, `E2`: `relay_bend_anatomy`, `E3`: `relay_bend_sense_transition`) are finished, zero slots used. While `E2` (`relay_bend_anatomy`) achieved a statistically significant positive paired gain (+0.0256 vs single-host anatomy, +0.0225 vs distance-only; 95% CIs strictly positive), the literal full-registry pre-placement overlap gate still triggers STOP against the 17 dense-support prior rasters (`dense17`), so the release remains held for research.
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
4. **Historical binary artifact; not cleared for download or submission:**
   `docs/downloads/gems57-h57r2-shipped8-all-flank0-20261009T180433Z-90e532947353-zeros.tif`
   (40,000 dots; recorded sha256 `9afe74ab…`). The cited comparison covered
   only 15 sibling-lane rasters and the same-lane overlap was disclosed; it was
   not a registry-wide authorization. The old 15/15 validator note and local
   file-geometry readings are historical only. Current README/preflight status
   controls: no retained TIFF is cleared. The apparent sparse-vs-dense contrast
   cannot waive the literal gate or the later whole-footprint witness.
5. **Repo repairs and provenance correction:** the legacy 15-row budget
   artifact and `submission_build_r2_all.json` are retained for audit, not as
   score evidence. Their earlier score-to-file labels included H33-2-B2 / 0.2778
   (owner source marks the file UNSCORED; no exact-file receipt) and H27-4 /
   0.2708 (attribution contradicted). The legacy Spearman -0.8104 is therefore
   not a verified live-score relationship. The corrected 13-entry descriptive
   owner-reported-value analysis is `evidence/registry_budget.json` (Spearman
   -0.7686, p=0.0021415873); it remains observational, unverified, and not
   organizer-confirmed. The original session-2 audit and run card remain at
   `evidence/submission_build_r2_all.json` and
   `evidence/run_card_r2_shipped8.json` as historical records.
6. **Other carried-forward context (not score evidence):** holdout-to-owner-label
   transfer was previously estimated at rho = +0.14, but the label provenance
   requires separate scrutiny; H57-B (tip-lobe) was listed as an untried
   hypothesis at that time; the GeoDAWN feature stack's local hash pin does not
   authenticate its origin as an official competition download.


---

## Session 7 addendum — 2026-10-10 (verification only; HOLD unchanged)

Evidence: [evidence/literal_gate_witness_verification_20261010.json](evidence/literal_gate_witness_verification_20261010.json), reproduced by `scripts/verify_literal_gate_witness.py` and pinned by `tests/test_literal_gate_witness.py`.

- **IR-S7-01 (correction to Session 6).** `training_features.tif` is **listed** on the GitHub bridge `buffedlizard55-lab/GEMSDOE` (`data/bridge/gems-geodawn-numerical-features.tif.part-000…004` + `manifest.json`, ref `c0c06ac82178f26b94fce3397036ef8f12a2f3a0`) via the authenticated GitHub API; part-000 is 94,371,840 bytes. It was not downloaded. Session 6's "unreachable" note is stale for the GitHub bridge; DrivenData (login) and Dropbox are still unreachable from this sandbox. The bridge gives transport identity only, not official-origin authentication. The gate verdict does not depend on features.
- **IR-S7-02 (leaderboard prompt conflict).** The prompt's "0.3195 is highest" is contradicted by the repo's organizer-published snapshot (`docs/data/leaderboard_snapshot.json`, 2026-10-10 20:40 UTC, selected rows): 0.3774 rank 1, 0.3195 rank 8. The prompt also lists 0.3774 under the GEMSDOE site as a participant value. Neither is a file receipt. DrivenData cannot be re-fetched from this sandbox.
- **IR-S7-03 (the one decision that unblocks everything).** The literal support rule (every positive finite pixel is a dot) makes any soft or whole-footprint registry raster a universal blocker. Independently reproduced: 17GEMSDOE E-proba-multiscale covers 5,167,373 / 5,167,373 allowed cells, so every footprint-confined candidate has overlap 1.0. The owner must choose: keep the rule (no candidate can pass), revise the support definition for all candidates and all registry rasters, or exclude the witness with a stated reason. No choice was made here.
- **GEMSDOE32 mechanism, file level.** Exact subset of the 40,199-dot base; 2,545 removed, all at 1.41–2.00 px from the catalogue; kept dots ≥ 2.236 px. At owner-reported DTI 0.2778 the metric bar is `k > 0.0556`, i.e. within 2.83 px of new truth. Plausible, not verified: holdout test still needed, and this requires IR-S6-05 resolved first.
- **Experiments run:** 0 of 3. **Hours:** under one. **Candidates generated:** 0. **Slots used:** 0. **Download / submit:** NO.

Next steps, in order (none authorized by this addendum):
1. Owner ruling on IR-S7-03 (support definition). Until then, no candidate can be promoted.
2. If the ruling allows: restore the 19-band stack from the bridge with the existing `scripts/download_features.sh` (hash-verified), then run the hypothesis H6-1 (training-catalogue proximity pruning vs matched random pruning) on the spatially blocked holdout, with a leakage canary per feature.
3. Re-fetch the DrivenData leaderboard from an allowed route, or have the owner paste the current board, to resolve IR-S7-02.
