# Active H57 fault-zone-anatomy hypothesis slate

**Status:** research backlog only. Nothing below has a new H57 HOLDOUT-DTI result. Do not promote the current artifact: its saved OOF result is not budget-matched, two single-feature leakage canaries are unresolved, and recorded slip-sense is not yet encoded. See [`evidence/run_card.json`](../../evidence/run_card.json).

## Baseline and hard gates

The current H57 candidate is a geometry-only, 40,000-dot-budget raster with 35,341 emitted dots. Its historical builder value `0.279349` is in-sample and has incorrect per-fold cap accounting; it is not a valid holdout score. The saved leave-one-quadrant-out `no_side` comparator is **HOLDOUT-DTI 0.250800**, evaluator record `H57 OOF canonical DTI + quadrant jackknife`, **22,641 withheld positives**, 95% quadrant-jackknife CI **[0.216433, 0.285166]**. That run emits about 68,147 dots per full-map equivalent, so it is not budget-matched to the candidate. Single-feature canaries flag `d` (0.900018) and `d_perp` (0.901345) under the protocol's discriminative-AUC >0.90 rule. Treat the baseline as non-promotable until these flags are explained or the instrument is redesigned.

All proposed variants must stay in the fault-zone-anatomy lane and use the shared hide-and-recover protocol: whole-segment withholding, 12 px domain erosion, feature construction from visible faults only, exact visible-pixel masking, pooled DTI with α=0.2, β=0.8 and a 300 m triangular kernel, individual feature canaries, cap-matched OOF evaluation, and a 95% CI. Use no more than three experiments or two hours total. Do not spend a competition slot.

## Ranked hypotheses

| Rank | Hypothesis | Expected DTI gain | Implementation / validation cost | Data status |
| --- | --- | --- | --- | --- |
| 1 | Sense-conditioned Riedel side and azimuth | Moderate, unmeasured | Medium | Existing local INGENIOUS vector fields include `sense`; official fault raster itself does not. |
| 2 | Slip-rate-scaled damage-zone width | Small–moderate, unmeasured | Low–medium | Existing local vector CSVs include `slip_mm_yr` / `SLIPRT2023`. |
| 3 | Along-strike tip-relay targeting | Moderate, unmeasured | Medium | Existing local vector endpoints and official fault raster. |
| 4 | Junction/stepover-context refinement | Small–moderate, unmeasured | Low | Existing official binary raster and local vectors. |
| 5 | Within-zone geophysical corroboration | Potentially high, unmeasured | High; currently blocked | Official competition training-feature raster is pinned in docs but absent from this checkout; do not call it viable until obtained and hash-verified. |

These are ranked by expected value subject to lane fit, data readiness, cost, and the requirement to resolve the baseline integrity gates. “Expected gain” is qualitative, not a score projection.

### H57-1 — Sense-conditioned Riedel side and relative azimuth (highest priority)

- **Layers.** `data/official/existing_faults.tif`; `data/external/trace_segments_utm11.csv` (`sense`); `data/external/qfault_attributes.csv` (`SLIPSENSE`). The two vector files are locally present and SHA256-pinned in [`data/README.md`](../../data/README.md). The current official fault raster is binary and has no sense field.
- **Physical target.** Mirrored secondary-strand orientation and side relative to the visible host fault, conditional on recorded RL, LL, or N sense. Do not hard-code a textbook angle; estimate the conditional distribution from withheld segments.
- **Rationale.** A marginal side/azimuth feature can average away a slip-direction-specific pattern. A sense-conditioned feature could separate synthetic and antithetic splays while staying within the existing fault-zone mechanism.
- **Difference from current H57.** Current `side` is a geometric left/right offset under an arbitrary strike convention; it is **not** a slip-sense feature. Current H57 does not use the available vector attribute. This candidate must attach sense only to vector trace pixels overlapping the fold's visible catalogue, so a withheld trace cannot leak its label through the full vector record. Unknown/missing sense must remain an explicit unknown, not be imputed from a textbook rule.
- **Expected gain / cost.** Moderate potential; medium cost for building a visible-only sense map, checking spatial overlap/coverage, adding categorical interactions, canarying each new feature separately, and running cap-matched OOF CV.
- **Availability check.** The local CSVs and fields are present and pinned. The fraction of visible official faults with a valid overlapping sense record has **not** been measured. Do not claim full coverage or use the feature until that alignment is audited.

### H57-2 — Slip-rate-scaled zone width

- **Layers.** `trace_segments_utm11.csv` (`slip_mm_yr`) and `qfault_attributes.csv` (`SLIPRT2023`), joined to visible rasterized segments.
- **Physical target.** Let the radial damage-zone scale depend on recorded slip rate rather than using connected-component length alone as the displacement proxy.
- **Rationale.** Equal-length fault traces can accommodate different slip rates. If damage-zone width follows displacement or accumulated slip more closely than raster component size, rate may improve the placement of secondary strands.
- **Difference from current H57.** The current `log_len` feature uses visible connected-component size; rate is absent. Fit a continuous, regularized interaction rather than imposing a threshold or a monotone law without evidence.
- **Expected gain / cost.** Small–moderate potential; low–medium cost because the attribute table is already local, but record-to-raster joins and missing-rate handling need a leak-safe audit.
- **Availability check.** The field exists locally. Coverage, units consistency, and alignment to visible official fault components still need to be measured before modeling.

### H57-3 — Along-strike tip relay

- **Layers.** `trace_segments_utm11.csv` endpoints and strike; `existing_faults.tif` for the scored catalogue geometry.
- **Physical target.** New strands near mapped fault tips or relay zones, with orientation and gap distance estimated from the held-out segments.
- **Rationale.** A strand that continues or relays a host structure can be more localized than a broad isotropic damage halo.
- **Difference from current H57.** The present model uses absolute along-strike offset to the nearest visible pixel and component length; it does not explicitly represent segment endpoints, normalized tip position, or relay geometry.
- **Expected gain / cost.** Moderate potential; medium cost to construct endpoints from visible pieces without using the withheld segment's geometry, then run the same OOF/cap/CI protocol.
- **Availability check.** Vector endpoints are present locally. Their alignment and coverage against the official raster must be checked first.

### H57-4 — Junction and stepover context

- **Layers.** `existing_faults.tif`, local fault vectors, and topology derived from visible connected segments only.
- **Physical target.** Secondary strands near fault intersections, bends, stepovers, or terminations rather than anywhere within a fixed-distance band.
- **Rationale.** These local geometric contexts can focus a fault-zone model on structurally plausible sites and distinguish a broad parallel halo from relay architecture.
- **Difference from current H57.** Current local density and strike-offset features do not explicitly encode branch order, junction angle, or whether a visible fault feature is a tip or a crossing.
- **Expected gain / cost.** Small–moderate potential; low cost for a topology-only variant, but endpoint/junction extraction needs tests for raster fragmentation and boundary artefacts.
- **Availability check.** Required raster and vector sources are already local; no new external data is needed.

### H57-5 — Within-zone geophysical corroboration (blocked)

- **Layers.** The competition's official `training_features.tif` bands (for example, magnetic-gradient and detrended-elevation derivatives), restricted strictly to a previously fitted fault-zone support, plus the mapped-fault geometry.
- **Physical target.** Rank pixels inside the fault-zone anatomy by independent magnetic lineaments or scarps that may coincide with secondary strands.
- **Rationale.** Geometry can constrain *where* to look while geophysics can discriminate candidate strands from an empty halo. This must not become an unconstrained whole-footprint geophysical lane.
- **Difference from current H57.** The active H57 candidate uses catalogue geometry only; this is a within-zone corroborator, not a replacement for the fault-zone prior.
- **Expected gain / cost.** Potentially high but unmeasured; high cost for data retrieval, normalization, leakage checks, and a fresh spatial OOF run.
- **Official source and availability.** The official DrivenData data endpoint is [competition #306 data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/). The 418,912,844-byte raster has a hash pin in [`data/README.md`](../../data/README.md), but `data/official/training_features.tif` is absent and the local pin check reports it missing. Therefore this hypothesis is **blocked, not viable yet**. Do not fetch an unverified substitute or claim availability until the official bytes are obtained and the pin matches.

## Trusted source links and provenance

- [DOE GEMS / DrivenData competition](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Competition problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data page (login may be required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [USGS GeoDAWN survey metadata](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [INGENIOUS project overview](https://gbcge.org/current-projects/ingenious/)
- [Local source hashes and field inventory](../../data/README.md)
- [Current validation and negative verdict](../../evidence/run_card.json)

## Irregularities / stop flags

1. H57's `d` and `d_perp` single-feature canaries exceed 0.90 in `mode=all`; their cause is unresolved.
2. The historical `0.279349` builder value is invalid as holdout evidence (same-fold fitting/scoring and incorrect budget accounting).
3. The valid saved OOF comparator is not matched to the 40,000-dot candidate budget.
4. H57 has not encoded the available local slip-sense field.
5. The current artifact has no preserved pre-placement surface for the required surface-correlation audit. The builder has been repaired to check surfaces before allocation on future builds.
6. The 18-raster final-dot comparison is a finite local inventory, not a complete competition registry.
7. No score in this document is a leaderboard projection. No organizer receipt is present.
