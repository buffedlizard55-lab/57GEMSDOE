# Fault-zone-anatomy hypotheses — ranked, untried

**Status: HOLD — no candidate is cleared to download or submit.** The three-experiment / two-hour budget is spent, the public-registry cache preflight is 0/679, and the independently verified universal-overlap witness makes the literal >70% 3-pixel gate unsatisfiable for every nonempty candidate while it remains in scope. This document is a research shortlist only; no candidate was implemented or evaluated in this audit.

The priorities below are qualitative. There is no evidence-based numerical expected DTI gain or gain probability. “Potential” means relative next-test priority, not a predicted score. The candidate list is based on the latest read-only attribute audit in [`attribute_audit_20261010.json`](../data/attribute_audit_20261010.json); that audit did not join attributes to visible hosts or run a model.

## Lane and validation status

Stay inside the secondary-strand anatomy lane: infer off-trace strand position from visible-host distance, host length, relative orientation, and recorded slip sense where the database supports a reliable visible-only join. Fit orientation and distance patterns from the holdout; do not hard-code Riedel angles or assume a universal step direction.

The stored holdouts are not a valid common benchmark. The historical H57-K geophysics arm is leakage-flagged on `d`, `d_perp`, and `vis_dtip` (each single-feature discriminatory AUC exceeds 0.90), and its result file does not pin evaluator/input hashes. A later `gems57-pooled-hide-v2` record uses a different split/count and its stored code hashes do not match the current tree. The soft-surface and binary-allocation results are different representations. See [`holdout_scope_reconciliation_20261010.json`](../data/holdout_scope_reconciliation_20261010.json). No candidate has beaten a valid, comparable, current-code holdout benchmark.

A deliberate novelty review checked `scripts/explore_zone.py`, `scripts/explore_zone2.py`, `scripts/run_sense_experiment.py`, `scripts/run_orientation_experiments.py`, `src/gems57/anatomy.py`, and the archived [`hypotheses_h57.md`](hypotheses_h57.md). The older exploration scripts measured distance, relative azimuth, normalized along-strike position, host length and marginal sense-conditioned distance; the newer model tested recorded-sense columns alongside broad geometry and relative magnetic strike. Therefore a generic sense-by-angle/distance model is **already tried**, not an untried idea. The old archived slate also proposed generic tip-relay, junction/stepover, and slip-rate hypotheses, but those proposals were marked unmeasured and no experiment receipt shows them run. This shortlist is scoped to unrun operationalizations in this repository, not global novelty; rank 1 is a narrower explicit visible-topology × sense fit, not a claim to invent relay geometry.

The recorded-sense comparison is **already tried**: `HOLDOUT-DTI`, evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives, paired difference +0.003580783591493636, 95% CI `[-0.005722027160876473, 0.014532120997528746]`; the interval includes zero and sense was not retained. This historical comparison is not current-code validation. See [`orientation_holdout.json`](../data/orientation_holdout.json) and [`run_card.json`](../data/run_card.json).

## Audited attribute availability (descriptive only)

- `data/external/trace_segments_utm11.csv`: 84,331 rows across 1,126 record IDs; sense counts `N=66,861`, `RL=8,448`, `LL=7,628`, missing `1,394`.
- `data/external/qfault_attributes.csv`: 22,956 rows. `SLIPRTNUM` and `RECNUM` are numeric on all rows; `FCODE2023` is populated on all rows; `SECONDARY` is populated on only 89 rows; `MAPSCALE` is missing on 4,059 rows.
- The field definitions describe `SLIPRTNUM` as assigned slip rate in mm/year and `RECNUM` as the upper-bounding time (years) of the most recent surface-deforming earthquake. Neither is cumulative displacement.
- These are CSV-level counts, **not** a spatial/host join, not proof of unambiguous correspondence to rasterized visible faults, and not predictive evidence. Preserve missing values; do not infer `SECONDARY`.
- Official data record for manual review: [INGENIOUS / GDR submission 1391](https://gdr.openei.org/submissions/1391), which lists Quaternary Faults v2 and its field-definition text. The record page states CC BY 4.0. Local input hashes and field counts are in the audit JSON.

## Ranked shortlist

### 1. Visible-topology × recorded-sense relay anatomy

**Hypothesis.** Explicitly extracted visible-host branch ends and junctions may condition where nearby secondary strands occur; any relationship to recorded slip sense must be estimated, not assumed. Fit the location and relative-strike distribution of withheld strands around visible tips/junctions, with sparse topology/sense classes shrunk toward a pooled fit.

**Layers/data.** Build endpoint/junction type and distance from the visible-only fault skeleton/branch graph in each fold, with local strike, cross- and along-strike offsets, and component length. Add INGENIOUS trace `sense` only after a predeclared, leakage-safe visible-host join is proven reliable. Do not use hidden-fault topology or hidden-fault sense as a predictor.

**Physical signature.** In fold-training faults, compare withheld strand locations relative to the nearest visible endpoint or junction: distance, signed normalized along-strike/cross-strike offset, and relative strike. Fit distributions only on training folds. No fixed Riedel angles, stepping direction, or universal tip effect.

**Why it may find missing faults.** Relay and splay structures can occupy off-trace zones near mapped branch terminations or junctions. A topology-conditioned halo could focus mass on those geometries rather than broad buffers around every host; recorded sense may separate supported kinematic classes, but only if the join and sample size permit.

**What is new here—and what is not.** `explore_zone.py` / `explore_zone2.py` measured `d`, relative azimuth, normalized along-strike position, length and marginal sense-conditioned distance; `run_sense_experiment.py` / `run_orientation_experiments.py` tested recorded-sense features with broad geometry/orientation. The active feature matrix has no explicit visible branch-end/junction topology by fold. An archived H57 slate already proposed generic tip-relay and junction/stepover hypotheses, but recorded them as unmeasured; this is a narrower topology-conditioned refinement, not a new generic relay or sense-by-angle idea and not a claim of global novelty. The prior sense comparison's paired `HOLDOUT-DTI` difference was +0.003580783591493636, evaluator `gems57-pooled-hide-v2`, 11,321 withheld positives, 95% CI `[-0.005722027160876473, 0.014532120997528746]`; sense was not retained.

**Named non-fault mimic.** Raster fragmentation, cartographic line breaks, lithologic/dike contacts, drainage lineaments, and vector-snapping errors can create false endpoints/junctions or apparent sense-specific relays.

**Priority and cost.** Rank 1; highest relative priority because it targets off-trace secondary-strand localization, but confidence is very low and no DTI gain is estimated. Medium-high cost: fold-specific endpoint/junction extraction, fragmentation/boundary tests, visible-host sense-join audit, sparse-class controls, and separate feature canaries.

**Sources reviewed.** [INGENIOUS GDR 1391](https://gdr.openei.org/submissions/1391); Wang et al. (2017), [stepover/bend stress and strain localization](https://doi.org/10.1016/j.tecto.2017.10.001). These provide fault-geometry context, not evidence that this feature improves contest DTI.

### 2. Slip-rate-conditioned damage-zone width/decay

**Hypothesis.** A recorded host slip rate may condition the fitted radial/cross-strike width and decay of nearby secondary strands beyond host length alone. Estimate a rate-by-distance/relative-orientation interaction. Treat slip rate as a measured rate—not cumulative displacement, maturity, or a displacement substitute.

**Layers/data.** Visible-only fault geometry and host length; QFault/INGENIOUS `SLIPRTNUM` or its documented category `SCODE2023`, only after a validated host-level join. The audit found `SLIPRTNUM` numeric on all 22,956 QFault rows (84 distinct values; 0.0001–4.5 mm/year); the join was not tested.

**Why it may find missing faults.** If present-day deformation rate is associated with the spatial distribution of secondary strands, a fitted, class-conditioned halo could prioritize off-trace locations near hosts with different observed rates. The holdout must establish whether any association exists.

**What is new here.** Current anatomy uses a connected-component length proxy; the inspected code does not use a validated QFault slip-rate interaction. The archived H57 hypothesis slate had already proposed slip-rate-scaled width as an unmeasured candidate, so this remains untried but is not a newly invented idea. It is distinct from changing the existing length exponent or repeating geometry-only tests.

**Named non-fault mimic.** Mapping effort, catalogue completeness, recency coding, and lithologic contrasts may covary with assigned rate and mimic a physical effect.

**Priority and cost.** Rank 2; low-to-medium relative potential, no supported gain estimate. Low-to-medium cost only if the join is clean; otherwise medium/high.

**Sources reviewed.** [INGENIOUS GDR 1391 / QFault v2](https://gdr.openei.org/submissions/1391); Savage & Brodsky (2011), [damage-zone fracture distribution versus displacement](https://doi.org/10.1029/2010JB007665). The latter motivates testing displacement effects but does not license substituting slip rate for cumulative displacement.

### 3. Recency-conditioned strand distribution

**Hypothesis.** The recorded upper-bound recency of a host’s most recent surface-deforming earthquake may change the relative distance/offset distribution of secondary strands. Test a predeclared recency-class interaction with fitted distance and relative-strike anatomy; estimate both near/far and along-strike responses without assuming the direction.

**Layers/data.** Visible-only host strike, distance, offset, and length plus QFault/INGENIOUS `RECNUM` or `RCODE2023`. The local audit found numeric `RECNUM` on all 22,956 QFault rows (67 values; 88–66,000,000 years); the field definition calls it an upper bound on the most recent surface-deforming event. Host joins are not verified.

**Why it may find missing faults.** Recent and long-inactive host systems could preserve different spatial patterns of secondary strands; a fitted interaction could place mass on off-trace geometry while avoiding an assumption that all activity is contemporaneous.

**What is new here.** Repository search of the reviewed scripts, active anatomy implementation, and archived H57 slate found no `RECNUM`/`RCODE2023` join or recency-conditioned model. This is untried within the checked-in work, not a claim of global novelty. It is not the global distance/length/orientation fit, the additive sense ablation, or the slip-rate interaction above.

**Named non-fault mimic.** Regional differences in dating, scarp preservation, erosion, and map compilation can make recency appear predictive without a causal strand-age relation.

**Priority and cost.** Rank 3; low relative potential and low confidence before validation. Medium cost because age categories, join quality, and regional confounding must be controlled.

**Sources reviewed.** [INGENIOUS GDR 1391 / QFault v2](https://gdr.openei.org/submissions/1391); [Savage & Brodsky (2011)](https://doi.org/10.1029/2010JB007665) for damage-zone context only.

### 4. USGS fault slip/dilation-tendency modifier

**Hypothesis.** An independently estimated tendency-to-slip or dilate for a visible host may modify the fitted orientation/distance distribution of secondary strands within a fixed host-derived halo.

**Layers/data.** The competition host geometry plus the USGS ScienceBase data release, [DOI 10.5066/P9YL58W6](https://doi.org/10.5066/P9YL58W6). Its catalog record describes slip/dilation tendency on Great Basin Quaternary fault segments and lists downloadable Great Basin and INGENIOUS shapefile/KMZ archives.

**Why it may find missing faults.** A host's stress/tendency context might be associated with nearby off-trace secondary structures. This is a test of structural fault anatomy, not proof of geothermal resource, permeability, heat, or a hidden-fault score.

**What is new here.** The inspected model has not joined or tested this separate fault-tendency dataset. It is not the already-tested 19-band feature stack or a scalar magnetic edge.

**Named non-fault mimic.** Stress-model assumptions, uncertain host geometry, common-source ancestry, and lithologic boundaries can create apparent tendency/strand associations without predicting new faults.

**Priority and cost.** Rank 4; low and highly uncertain relative potential until overlap is demonstrated; high data/registration cost. The catalog makes a source obtainable, but this candidate is **not yet a viable feature**: no archive was downloaded, and contest AOI overlap, schema/CRS, reuse terms, and grid registration remain unchecked.

**Sources reviewed.** [Official USGS ScienceBase item](https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d) / [DOI 10.5066/P9YL58W6](https://doi.org/10.5066/P9YL58W6); [INGENIOUS GDR 1391](https://gdr.openei.org/submissions/1391). The catalog describes the data purpose and file availability; it does not establish contest-grid coverage or predictive value.

## Cross-candidate controls and next steps

- `FCODE2023` (mapping certainty) and `MAPSCALE` are observation-process/confounding fields, not proof of a fault. `MAPSCALE` is missing on 4,059 rows; any future use requires a visible-host join audit. `SECONDARY` is nonmissing on only 89 rows and must not be imputed.
- No current shared feature cache or `training_features.tif` is present. Historical feature-cache receipts do not make the underlying current inputs available or independently authenticate their origin.
- Do not run, download, fit, or emit under the spent budget and unresolved uniqueness blocker. If the project is explicitly reauthorized, first resolve the literal universal-overlap stop and establish a new budget; then preregister the join and feature, reuse the shared cache/evaluator/writer, withhold whole buffered segments, derive catalog features only from visible faults, mask visible pixels exactly, use pooled DTI (`alpha=0.2`, `beta=0.8`, 300 m triangular kernel), test each feature alone for leakage (`AUC >0.90` means leakage until resolved), compare registry rank correlation and 3-pixel overlap before placement and on final dots, and finish each experiment with the required JSON run card.
- **No hypothesis here is implemented, validated, promoted, or approved for a competition slot.**
