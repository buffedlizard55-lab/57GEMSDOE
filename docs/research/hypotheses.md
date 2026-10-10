# Fault-zone anatomy: current hypotheses and pre-registration

**Scope.** This page covers only catalogue-derived fault-zone anatomy. The public
catalogue is `existing_faults.tif`; no geophysical predictor, geothermal-proxy
raster, or third-party target layer is used in the experiment below. A spatial
hide-and-recover result measures recovery of withheld mapped branches, not
unmapped faults and not leaderboard transfer.

## Hypotheses and current eligibility

The earlier `H57-A` en-echelon feature set is historical context, not an approved
download. Its earlier holdout readings used a different pipeline and are not
H57-B results. `H57-F` (recorded slip-sense) was inconclusive in its historical
measurement; that result remains in `evidence/exp_sense_loqo_all.json` and was
not rerun. The old raster in `docs/downloads/` remains **HOLD**.

H57-B below is the one completed current feature test; it is **HOLD**, with a
non-comparable preregistered contrast and a post-hoc matched-mass sensitivity.
H57-G/H/I are untested hypotheses only. The experiment budget for this work is
exhausted, so none is authorized for a new run here. “Expected gain” is the
pre-run direction/range for local holdout contrast, **not an observed score, a
leaderboard projection, or evidence of improvement**. Each hypothesis names a
non-fault mimic.

| Rank | Hypothesis | Layers and physical signature | Why it could recover a missing strand | Difference from this repository | Expected HOLDOUT-DTI contrast vs comparable baseline | Cost / main risk |
|---:|---|---|---|---|---|---|
| 1 | **H57-B — filtered branch-terminal proximity** | `existing_faults.tif`; distance to endpoints of visible between-junction branches. Endpoints within the withheld branch's 3-px collar are discarded so masking cannot manufacture a “tip”. | A trace termination can be a point where a mapped strand relays, splays, or continues beneath cover. | Adds one learned distance feature to the existing eight-feature `no_side` anatomy baseline; no fixed cone angle or hand-set lobe. Related sibling outputs used tip/Euler ideas, so this is a distinct test, **not a novelty claim**. | Predict small positive contrast, roughly **+0.005 to +0.020 DTI**; zero or a negative result remains plausible. This is only a preregistered hypothesis. | Low. Main risk: endpoint pixels encode digitization breaks rather than geology. |
| 2 | **H57-G — facing-tip relay-gap geometry** | `existing_faults.tif`; paired visible branch termini, fitted along-strike gap, cross-strike separation, and relative strike. | En-echelon relays can link adjacent strands across a finite gap that a nearest-trace distance feature cannot represent. | Explicit pair geometry rather than isotropic density or the one-anchor stepover features already in `H57-A`. | Predict weak-to-small positive contrast, roughly **0 to +0.010 DTI**, conditional on a clean canary. | Medium. Main risks: branch pairing ambiguity and synthetic gaps caused by mapping resolution. |
| 3 | **H57-H — bend-localized secondary-strand enrichment** | `existing_faults.tif`; local change in strike along visible branches, with a scale fitted only on training folds. | Bends can localize stress and promote secondary fractures or linked strands. | The current `sin2`/`cos2` features encode absolute strike, not along-branch curvature or strike change. | Predict near-zero to small positive contrast, roughly **0 to +0.010 DTI**. | Medium. Main risks: raster stair-step curvature and natural drainage/road bends. |
| 4 | **H57-I — slip-rate-conditioned damage-zone width** | `data/external/qfault_attributes.csv` (`SLIPRT2023`, `SLIPRTNUM`) joined to visible fault sections; fit width from slip-rate rather than component length. | A fast-slipping host may support a wider damaged zone than a slow host of similar mapped pixel length. | Replaces the current coarse `log_len` proxy with a database attribute; it does not add a non-fault predictor. | Predict a small, uncertain positive contrast, roughly **0 to +0.010 DTI**, only if section-name joins are auditable. | Medium. Main risk: name/section join error and slip-rate coverage/semantics. Data columns exist locally; a section-level join audit is still required before implementation. |

## Experiment 1 preregistration — H57-B (protocol record)

- **Control:** the existing `no_side` feature set; **secondary control:** `d_only`.
- **Candidate:** `no_side + tip_distance`, one additional feature. The feature is
  built from exact visible fault pixels; cut-induced termini within 3 px of any
  held branch are removed before the distance transform.
- **Holdout:** whole branches between junctions (no 12-px chunking), four
  footprint quadrants, two fixed draws, 12-px quadrant erosion, and a 3-px
  feature/training-negative buffer. The test collar stays in the scoring region;
  remaining visible fault pixels are masked exactly.
- **Scoring:** shared `gems57.evaluate_holdout` evaluator, pooled DTI,
  α = 0.2, β = 0.8, 300 m triangular kernel; 20 km paired spatial-block 95% CI.
  All single-feature discriminative AUCs are checked; any AUC > 0.90 blocks
  promotion until leakage is resolved.
- **Comparable budget:** same 10,000-dot cap per held quadrant cell and the same
  greedy DTI allocator for all arms. If realized dot counts differ, the
  contrast is marked non-comparable and cannot promote.
- **Preregistered promotion rule:** the candidate must have a positive paired
  95% CI lower bound versus `no_side`, matched realized dot counts, and a clean
  feature canary. Passing only makes it eligible for the separate registry and
  format gates; it does **not** select a weekly slot.
- **Mimic:** road and dry-wash termini, map-sheet breaks, and digitization
  endpoints. The catalogue-only test cannot distinguish these from geological
  fault tips.

## Sources opened for the mechanism (not evidence of score gain)

- Tchalenko (1970), “Similarities between shear zones of different magnitudes,”
  *GSA Bulletin* 81, 1625–1640. [DOI](https://doi.org/10.1130/0016-7606(1970)81%5B1625%3ASBSZOD%5D2.0.CO%3B2)
- Schreurs (2003), “Fault development and interaction in distributed strike-slip
  shear zones,” *Geological Society, London, Special Publications* 210, 35–52.
  [DOI](https://doi.org/10.1144/GSL.SP.2003.210.01.03)
- Faulds, Henry & Hinz (2005), “Kinematics of the northern Walker Lane,”
  *Geology* 33, 505–508. [DOI](https://doi.org/10.1130/G21274.1)
- Savage & Brodsky (2011), “Collateral damage: Evolution with displacement of
  fracture distribution and secondary fault strands in fault damage zones,”
  *JGR: Solid Earth* 116, B03405. [DOI](https://doi.org/10.1029/2010JB007665)
- DrivenData, [GEMS Prize problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
  for the scoring metric and prediction target.

## Outcome log — H57-B HOLD

All DTI values below are `HOLDOUT-DTI` from
`gems57-buffered-whole-branch-pooled-v2.0`, with 22,276 withheld positives and
paired 20 km spatial-block 95% CIs. They are local holdout readings, not live
scores.

- **Preregistered 10,000-per-cell run:** candidate 0.1882084 [0.1760057,
  0.2014529] with 71,191 dots; `no_side` 0.1303988 [0.1188650, 0.1419912]
  with 80,000 dots. Counts differed in four of eight cells, so the arm contrast
  is non-comparable and cannot promote.
- **Matched-mass replay:** candidate 0.1712803 [0.1585123, 0.1843726],
  `no_side` 0.1103187 [0.0994158, 0.1222397], paired difference +0.0609616
  [+0.0520292, +0.0703759]. This was a post-hoc sensitivity: the common cap
  was selected after the primary output was observed, and the CI is conditional
  on that cap. It is not confirmatory.
- **Canary:** maximum single-feature discriminative AUC 0.8392, below the 0.90
  screen. The non-fault mimics in the preregistration remain unresolved by this
  catalogue-only test.
- **Registry:** full-surface check passed all 667 indexed rasters; maximum
  Spearman 0.4229688817. The final in-memory map had 27,088 dots and first
  fired at 0.7270747194 forward overlap within 3 px of one registry raster,
  exceeding the literal 0.70 limit. That final-dot scan stopped at its first
  firing; it was not a complete list. There is no reverse-overlap exemption and
  Jaccard is not a gate.
- **Artifact:** no H57-B TIF was generated; no format validator was run; download
  is **NOT CLEARED**; no submission or slot selection occurred. See the single
  authoritative `evidence/run_card.json` and the two gate reports under
  `evidence/` for full provenance.

The experiment budget is exhausted. Do not retune H57-B, run H57-G/H/I, select
a weekly slot, or produce a raster under this HOLD. A future experiment needs a
separately authorized budget and a new preregistration; passing a holdout alone
would still not select a slot.
