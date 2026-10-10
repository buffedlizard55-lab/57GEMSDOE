# Remaining work — do not bypass the current HOLD

Last reviewed 2026-10-10 (Session 7). **Download research TIFF (`gems57-h57m-relay-band-20261010T215522Z-gems57-h57m.tif`, 43,950 dots, sha `bb1f328d…`): OK. Submit: NO.** Session 7 produced a new, validated dotted emission from the retained two-host relay-band posterior, spent **zero** competition slots, kept the fail-closed verdict, and replaced an earlier monotone-surrogate budget choice with the exact 4-fold curve (IR-S7-01). The blocking gate is now measured rather than asserted: 40 of the 43 firings come from registry rasters whose own 3 px dilation covers ≥ 70 % of the footprint, so **no** nonempty candidate can pass the inherited one-directional test, and the owner's best-known file fires against 116 of the same 213 rasters (IR-S7-02).

## 1. Literal uniqueness obstruction — now measured across candidate and control

The [saturation certificate](evidence/uniqueness_saturation_certificate.json) already proved that one prior covers all 5,106,385 allowable cells. Session 7 extended the measurement to 213 pinned rasters (35 hashed local copies + 178 fetched and SHA256-verified): 40 have a 3 px dilation covering ≥ 70 % of the footprint, many covering 100 % with a **zero-area** sliver, so the inherited forward-overlap test fires mechanically for any candidate that places its dots on the geologically plausible grid. The three remaining firings are broad coverage fields (344,041-dot ensemble archive, 624,025-dot coverage raster; dilation coverage 0.61–0.65, forward 0.84–0.90, reverse 0.13–0.17). No raster fires in both directions (worst reverse 0.698725), and the owner's best-known file (`GEMSDOE32 h33-2-b2`) fires against **116 of 213**. Evidence: [gate_universality.json](evidence/gate_universality.json) · [h57m_uniqueness_certificate.json](evidence/h57m_uniqueness_certificate.json).

Session 7 applied **no** threshold, density or reverse-overlap exemption: the candidate stays held. Two paths forward, both requiring the owner:
1. accept that no nonempty candidate can satisfy the literal one-directional gate (then no submission is possible under this protocol); or
2. authorise an explicit revision — the measured candidate is that a symmetric both-direction condition currently yields **zero** firings on all 213 measured rasters while the best-known file still fires against 116.

Either way the revision must be logged in the audit ledger before a separate selector is allowed to clear a file for a slot.

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
3. Within the retained H57-M lane: compare the uniform density-transfer allocation against a *localised* allocation that spends the same 43,950-dot budget where the fitted positive-distance distribution concentrates (the 90th percentile is 25.55 px), under the exact evaluator and a second independent holdout draw. Require a strictly positive paired CI before it can replace the shipped emission.
4. Re-measure the shipped 43,950-dot file at the *exact* budget on the 4-fold curve (the shipped point sits between the measured 40,000 and 60,000 budgets) if a new budgeted session is authorised.

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

The audited registry now pins **696** unique-grid rasters across the 57 public owner repositories (852,760,087 bytes); Session 7 byte-measured **213** of them for the current candidate and the rest remain a stated scope limitation. The earlier 695-grid-raster union comprises 691 predictions/conservatively retained ambiguous rasters plus four historical auxiliary inputs, explicitly classified. Public-main commit pins and historical blobs are covered; private/unlinked/inaccessible artifacts are not. Refresh before a future candidate; never claim absence from a missing cache. Do not sweep current generated outputs into their own prior inventory.

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
