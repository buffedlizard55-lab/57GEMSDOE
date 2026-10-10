# Remaining work — preserve the literal HOLD

Last reviewed 2026-10-10 during PR #16 integration. **No artifact is cleared to download or submit.** H57-B remains HOLD: no H57-B TIFF was generated or validated, no upload occurred, and no weekly slot was selected. Its protected source card is `evidence/run_card.json`; its SHA-256 remains `27bacbec2620a4a2bb41ca14d68505dc646a9b6a9da8da2b4471bc41358a2923`.

Session 5 used all three declared comparisons (E1/E2/E3). The new H57-J relay/bend research TIFF and ZIP are archived only. The 695-raster literal uniqueness receipt failed, so download permission is explicitly withdrawn and no final dots were generated. Do not restore the upstream `okay_to_download: true` claim. No model experiment, H57-B generation, data fetch, submission, or slot selection was performed during this integration review.

## 1. H57-J Session-5 results — research evidence, not release clearance

- **E1 / H57-H `bend_anatomy`:** binary HOLDOUT-DTI `0.112331 [0.098505, 0.128094]`; paired Δ vs single-host `anatomy` `+0.002684 [−0.004964, +0.010406]`. No demonstrated binary improvement.
- **E2 / H57-I2 + H57-H `relay_bend_anatomy` (retained arm):** binary HOLDOUT-DTI `0.135204 [0.119140, 0.153036]`; paired Δ vs `anatomy` `+0.025556 [+0.013943, +0.037109]`, and vs `distance_only` `+0.022479 [+0.007867, +0.038463]`; it won all four spatial folds. Soft-surface HOLDOUT-DTI `0.031160 [0.024691, 0.038109]`, paired Δ vs `anatomy` `+0.008284 [+0.005420, +0.010947]`.
- **E3 / H57-J `relay_bend_sense_transition`:** binary HOLDOUT-DTI `0.141391 [0.124513, 0.161457]`; paired Δ vs E2 `+0.006188 [−0.001694, +0.015702]`. Since the binary paired 95% CI crosses zero, E2 remains the predeclared selected arm. Soft-surface paired Δ vs E2 is `+0.002738 [+0.000307, +0.005994]`; that does not override the binary selection rule.
- These are **HOLDOUT-DTI** measurements from evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives and the recorded paired intervals—not organizer scores or projections. The 22 feature-alone canaries have maximum discriminative AUC `0.8259` (below the 0.90 leakage trigger); a clean canary is not proof of no leakage.
- The H57-J surface audit checked 695 indexed rasters and reports `unique: false`, 81 threshold-triggering comparisons, worst full-footprint Spearman `0.9753151923476495` (>0.90) and worst candidate-forward 3 px overlap `1.0` (>0.70). Both literal gates remain operative. There is no reverse-overlap or Jaccard exemption. The archived H57-J TIFF SHA-256 is `cf7b903dd9e669fb6ef71241e6e5e3e840acd2f39df7d599f8472b2d9a489648`; local format validation does not clear it.
- The source-main H57-J card claimed `okay_to_download: true` despite that failed audit. Its sanitized historical card is `evidence/history/run_card_session5_relay_bend_held.json`, explicitly false for download and submission. The TIFF/ZIP are under `docs/downloads/archive/`; there is no active site download link.

## 2. Literal uniqueness obstruction — do not change the protocol

The SHA-pinned dense17 certificate `evidence/uniqueness_saturation_certificate.json` covers all 5,106,385 allowable cells. Under the inherited finite-positive support definition, every nonempty candidate has directed 3 px overlap `1.0`, above the 0.70 limit. This obstruction is not permission to change thresholds, support, directionality, density, or the surface/final-dot gate. Only an explicit protocol revision could change that rule; none is authorized here. No production placement or slot choice is defensible while the gate fails.

## 3. H57-K audit scope remains unresolved

- H57-K candidate SHA-256: `f273e778341ff726edc5d36bda61c45f53cb0c8f3361f1c55817bc87ddb1012a`. Its candidate-specific 679-row audit is `evidence/orientation_surface_uniqueness.json` and remains historical; it is not current clearance.
- The refreshed public-main inventory has 695 rasters. A separate mainline review reports 698 rows, including four row hashes absent from that 695-row index and omitting the H57-K candidate hash that is present in the index. H57-J's 695-row audit is for a different candidate and cannot replace the H57-K audit.
- `IR-57-AUDIT-SCOPE-01` in `evidence/irregularities_current.json` records the mismatch and fail-closed resolution. Before any future H57-K status decision, reconcile the exact hash-pinned inventory and produce a candidate-specific audit. Keep H57-K NOT CLEARED until then.

## 4. Data and reproducibility limits

The current checkout lacks `data/official/training_features.tif`; `evidence/data_preparation.json` correctly marks its expected SHA-256 unverified. Historical bridge hashes establish transport-byte identity, not independently authenticated official origin. The data page redirected to login and direct binary hosts are outside sandbox egress. No data was fetched during this integration. Do not infer present cache availability from historical receipts, and do not ask for credentials.

Shared tools remain the single scoring/packaging implementations: `src/gems57/evaluate_holdout.py` and `src/gems57/submission_writer.py`. Preserve visible-only catalogue features, whole-component buffered holdouts, pixel-exact known-fault masking, pooled α=0.2 / β=0.8 DTI and the 300 m triangular kernel. Keep evaluator version, positive count and CI attached to every HOLDOUT-DTI label. Preserve the protected H57-B card byte-for-byte.

## 5. Next separately budgeted work — not part of this merge

The three Session-5 experiments are complete and no fourth experiment is authorized in this review. Any future experiment requires a fresh explicit budget and predeclaration. Potentially valuable questions include repeated independent component-holdout draws for H57-J and obtaining authenticated, locally hash-pinned external radiometric layers before H57-N; neither is authorized or run here. Do not select a weekly slot or submit as part of research/integration work.

## 6. Scientific/statistical limitations

- The holdout target is mapped catalogue geometry, not unpublished expert faults; geological-system holdouts, mapping bias and transfer to new faults remain uncalibrated.
- Connected components may split one geological fault or join distinct systems. Bootstrap intervals condition on fitted folds, masks and budgets; they omit full retraining/model-selection uncertainty and private-label uncertainty.
- Component size is a noisy displacement proxy. Relative-strike summaries are nearest-component, censored, pixel-weighted diagnostics; they are not segment-weighted significance tests or stress inversions.
- Slip-source joins/rasterization are not independently authenticated. Magnetic dikes, contacts, erosion, digitization vertices, flight-line residuals and survey clearance can mimic fault strands.
- Greedy emission uses a clipped convolution-based surrogate for unknown-truth self-credit; the shared holdout evaluator scores with the exact metric. No heat, fluid-flow, reservoir-volume or economic-viability labels are present.
- The public owner-repository raster inventory is not a complete organizer registry: private, unlinked, external and inaccessible files may be absent.

## 7. Pages, PR and prize compliance

The site build is render-only and must leave `evidence/run_card.json` unchanged. After any site rebuild, verify its SHA-256, inspect status/download language and run `scripts/check_site.py`; held TIFF/ZIP files must not acquire active links. The workflow publishes `docs/`; changing Pages settings previously returned HTTP 403. GitHub run-log downloads may redirect to an egress-blocked host; status APIs remain available.

The published cap is three submissions per week, but only the logged-in competition page can establish remaining team capacity. Selection is a separate step. Review official rules, external-data licenses and finalist reproducibility/disclosure requirements before any future promotion. **Maximize P(Win):** preserve scarce slots and demand evidence. **Own the Outcome:** publish negative results and keep all release language truthful.
