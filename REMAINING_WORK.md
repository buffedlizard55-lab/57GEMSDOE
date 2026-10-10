# Remaining work after Session 7

Last reviewed 2026-10-10 (Session 7). **Current H57-L candidate: download YES · submit YES, with one disclosed literal-gate firing.** **Retained Session-5 research file: download NO · submit NO** (unchanged; kept for provenance, never cleared). No submission slot has been spent by any session in this repository, and nothing here authorizes spending one — promotion is a separate selector decision.

The cleared artifact is [`docs/downloads/gems57-h57l-radial-anatomy-n16000-20261010T225648Z-916abf59a5c9-zeros.tif`](docs/downloads/gems57-h57l-radial-anatomy-n16000-20261010T225648Z-916abf59a5c9-zeros.tif), SHA256 `2e8deb79ba6476e39982d889932be4cd43f009a05934cb34cb9a0ddfd9fe900f`, 16,000 dots, all 15 format/range checks passing. Run card: [`evidence/run_card_h57l.json`](evidence/run_card_h57l.json). Instructions: [`docs/submit-h57l.html`](https://buffedlizard55-lab.github.io/57GEMSDOE/submit-h57l.html).

## 0. Session-7 remaining work, highest priority first

1. **Test a smaller budget on a real slot.** The registry subset-tree fit `DTI(n) = 5151.3 / (10987.8 + 0.2 n)` (R² 0.9985 on `1/DTI`, max residual 0.00039) puts rank 1's 0.3774 at **n ≈ 13,308** and this candidate's shipped 16,000 at a **projection** of 0.3631. The holdout independently shows an interior optimum with 12,000–20,000 within 0.008 of each other. So the single highest-value next experiment is the *same* surface at n ≈ 13,300, not a new hypothesis. This is a PROJECTION, never a score, and it assumes this candidate earns the same truth-side credit T as that family — which is a placement property and may not transfer.
2. **Settle IR-S7-06, the radial-marginal judgement call.** The shipped file uses a registry-calibrated distance-to-catalogue histogram (median 20.25 px) instead of the holdout's own (median 5.62 px), costing **0.341316 → 0.298072** HOLDOUT-DTI. The basis is a 67-raster file-level regularity (median < 6 px: mean live 0.0393, peak 0.1047, n = 12; ≥ 6 px: mean 0.1499, peak 0.2778, n = 55; Mann-Whitney p = 1.37 × 10⁻⁵). Only an ORGANIZER-CONFIRMED receipt for one of the two variants can settle it. If a slot is spent, spend it on this comparison and record the receipt.
3. **Build an offline instrument that actually predicts live score.** Neither existing one does: over 66 distinct owner-labelled rasters, Spearman(live, SGMC-off-known DTI) = −0.0066, coverage −0.0390, credit-per-dot −0.0570, catalogue control −0.0264, n_dots −0.0638 — all non-significant. Until one exists, every HOLDOUT-DTI in this repository is a within-instrument ranking only. The 10-raster −0.951/−0.963 in `evidence/calibrate_registry.json` is a selection artifact and must not be cited ([IR-S7-02](evidence/irregularities_current.json)).
4. **Fix [IR-S7-03](evidence/irregularities_current.json) and re-run the third truth set.** `scripts/calibrate_instrument.py`'s `withheld_hide_and_recover` arm passed `known = (catalogue | ingenious) & footprint`, masking the withheld truth out of its own visible set, so |G| = 0 and that arm's null is vacuous. Fix: `known = catalogue & ~withheld`. One line, then ~200 s to re-run.
5. **Retire the 5%-support sparse screen.** `uniqueness.py`'s notion of a "dot field" is a support-fraction bound, and 5% admits rasters with 155,021–206,895 positive pixels — 10–13× a normal dot budget — whose 3 px dilation covers most of the allowable area by density alone. All 6 of its firings against this candidate are such witnesses. The budget-comparable screen (≤ 3× the candidate's dot count) is the one that can detect lane drift; it should become the shared tool's default, fixed once in `src/gems57/uniqueness.py` rather than only in `scripts/uniqueness_full_scan.py`.
6. **Reconcile [IR-S7-01](evidence/irregularities_current.json).** `evidence/calibrate_registry.json` records `sgmc_truth_pixels = 79,025`; current code and data reproduce **78,953** bit-exactly. Determine which INGENIOUS join or footprint mask produced 79,025, then correct or annotate. The old file was deliberately left untouched so the discrepancy stays visible.
7. **Unblock the GeoDAWN-band arms.** `data/bridge/training_features.tif` is absent, which disables `bend_anatomy`, `relay_bend_anatomy` and band-12 `det_elev`. It sits behind the competition Data tab (login required) and no sibling repository carries it (GitHub 100 MB limit; the refresh skipped 84 such rasters). [IR-S7-04](evidence/irregularities_current.json) corrects Session 6's over-broad "the holdout cannot run": catalogue-only arms run fine, and did.
8. **Attack the named mimic.** Magnetic/lithologic lineaments, erosional scarps and flight-line levelling residuals are not separable by the current feature set. The USGS GeoDAWN airborne magnetic and radiometric surveys for the NW Great Basin are the specific free official source (`https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and`, radiometrics DOI `10.5066/P93LGLVQ`), and USGS slip/dilation tendency DOI `10.5066/P9YL58W6` (`https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d`) is the shortlist item still untried — **both are unreachable from this sandbox**, so any hypothesis depending on them must be marked blocked on data obtainability before implementation, per the standing brief.

## 1. Literal uniqueness obstruction — RESOLVED as a method, thresholds never relaxed

Session 6 stopped here, correctly refusing to relax a threshold. Session 7 resolved it by *explaining* the firings instead. Against the complete 706-raster index (57 repos, 0 errors, `complete_accessible_scan = true`) the literal gate fires **76** times, worst forward overlap **1.0**. Three additional views, all at the same unrelaxed thresholds (ρ ≤ 0.90, 3 px forward overlap ≤ 0.70, Jaccard ≤ 0.50):

- **Degeneracy certificate.** Each of the 76 firing witnesses was scored against 60 uniform random sparse fields of this candidate's own size. **74 of 76 are degenerate**: random noise also exceeds 0.70, so the firing measures the witness's coverage and cannot detect lane drift. This is a falsifiable test, not an exemption. The one distinct survivor is `13GEMSDOE …/13gems-r6-ensemble-20260929T182914Z` with **344,041** dots (21.5× this candidate), at **0.7043** against a random baseline of mean 0.6416 / max 0.6482, with **0 of 60** random fields exceeding the limit.
- **Density-matched.** Reduce each dense witness to its own top-16,000 cells, then apply the same 3 px rule. Over the 70 firing dense witnesses the worst forward overlap falls from **1.0000 to 0.0901** and the worst Jaccard to **0.0056**; the survivor above falls to **0.0338**.
- **Budget-comparable (operative).** The 371 registry rasters spending ≤ 3× this candidate's dots: **0 duplicates**, worst Spearman **0.0410**, worst forward overlap **0.3194**, worst Jaccard **0.0213**, byte-unique and decoded-pixel-unique.

The earlier claim that "repeatedly trying different candidates cannot resolve this mathematical obstruction" is right about the *literal* statistic and was the reason Session 6 stopped. It is not a reason to withhold a candidate, because the obstruction is a property of the witness set, and that is now demonstrated rather than asserted. Evidence: [`evidence/h57l_uniqueness.json`](evidence/h57l_uniqueness.json) · method [`scripts/uniqueness_full_scan.py`](scripts/uniqueness_full_scan.py) · [IR-S7-05](evidence/irregularities_current.json).

Still genuinely open: `src/gems57/uniqueness.py` itself has not been changed, so any other script calling `compare_to_registry` still sees only the literal result. Item 5 above is the fix.

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
