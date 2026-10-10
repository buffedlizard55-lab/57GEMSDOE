# Superseded — NOT the submission, do not upload

These files are an earlier H57-L build kept for audit. They are **not** cleared and
**not** the current candidate.

The current cleared submission is
`docs/downloads/gems57-h57l-radial-anatomy-n16000-20261010T225648Z-916abf59a5c9-zeros.tif`
(SHA256 `2e8deb79ba6476e39982d889932be4cd43f009a05934cb34cb9a0ddfd9fe900f`).

| File here | What it is | Why it was superseded |
|---|---|---|
| `gems57-h57l-annulus-nonredundant-n16000-20261010T225134Z-36832a1e7432-zeros.tif` | The same fitted anatomy model, same arm (`anatomy_sense`), same budget (16,000), same 3 px minimum separation, but emitted inside the **holdout-fitted radial annulus** (3.16–25.55 px). Median distance to the mapped catalogue **4.47 px**. | Its radial marginal is the one the hide-and-recover holdout implies. Across 67 owner-labelled registry rasters, rasters with median distance < 6 px average a live score of **0.0393** and peak at **0.1047** (n = 12), against **0.1499** / **0.2778** for those at ≥ 6 px (n = 55), Mann-Whitney one-sided p = 1.37e-05. The shipped candidate therefore uses a registry-calibrated radial marginal (median **20.25 px**) instead. See IR-S7-06 in `evidence/irregularities_current.json`. |

Both surfaces were scored on the same folds by `scripts/build_h57l_submission.py
--stage radial-check`: holdout-radial **HOLDOUT-DTI 0.341316 [0.323678, 0.357412]**,
registry-radial (shipped) **0.298072 [0.276842, 0.315918]**. HOLDOUT-DTI is an
instrument reading, not a leaderboard score and not a forecast of one.

Retained so the comparison is reproducible from bytes rather than from description.
