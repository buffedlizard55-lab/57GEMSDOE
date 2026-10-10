# Fault-zone-anatomy hypotheses — ranked, not run

**Status: HOLD.** The candidate is not cleared to download or submit. The
three-experiment / two-hour budget is spent; this audit ran tests and code review
only. None of the hypotheses below was implemented or evaluated in this session.
The ranking is a **priority order for a future authorized validation**, based on
mechanistic relevance, data readiness, and cost. It is not a numerical DTI-gain
estimate or a claim that any candidate will improve a score.

## Scope and current baseline

Stay inside the fault-zone-anatomy lane: infer where secondary strands may occur
around the mapped USGS/INGENIOUS fault network. The tested baseline uses nearest-fault distance, local orientation/offset, and
a host-size proxy. The three completed comparisons also tested a candidate
magnetic-edge relative-strike feature and a recorded-sense ablation; a prior
dot-budget sweep was run. Do not relabel those exact implementations as
untried. The latest stored soft-surface `HOLDOUT-DTI` is 0.023203 (95% CI
[0.018778, 0.027992], 11,321 withheld positives; evaluator
`gems57-pooled-hide-v2`). A separate binary-allocation test-fold result is
0.109168 (95% CI [0.094503, 0.124194]); it is not the score of the soft TIFF.
The stored evaluator hashes predate the current code, and the historical 679-raster
pre-placement scan fires the literal 3-pixel overlap stop on soft-surface
finite-positive support (not final dots). Neither value is a live-score projection
or current clearance. The older 0.227908 result (95% CI [0.186735, 0.269081],
22,641 positives) is unpinned legacy context.

A session-5 independent uniqueness audit also verified a 17GEMSDOE raster in the
recorded inventory whose 3-pixel positive support covers every allowable cell.
Measured forward overlap is 1.0 for dense and sparse test candidates; under the
unchanged literal >70% rule, any nonempty candidate is blocked while it remains
in scope. This is not a score, and not authorization to alter the threshold. Session 6 re-verified all
696/696 indexed cache files on its then-current snapshot (679/679 on the earlier snapshot), superseding the earlier 0/679 note; the later PR #20 audit is a separate 698-entry snapshot for the H57-I surface.
The shortlist is scientific future-work context only until an explicit protocol
decision and renewed experiment budget exist.

## Ranked shortlist: relative DTI potential and implementation cost

The requested ranking is necessarily qualitative: the hidden competition truth is unavailable, the latest stored holdout is not reproducible under the current `evaluate_holdout.py` hash, and the literal registry-overlap gate blocks any nonempty candidate. These labels are **research priors, not HOLDOUT-DTI results, score projections, or promotion recommendations**. “Expected upside” means only relative plausibility of an incremental holdout benefit if the mechanism transfers; confidence is low throughout. No numerical gain is estimable from this evidence.

| Rank | Hypothesis | Relative expected DTI upside (qualitative prior only) | Implementation cost / data readiness |
|---:|---|---|---|
| 1 | Segment-pair stepover/bend geometry | **Moderate; highest relative prior, very low confidence.** Directly targets connectors and tip/subparallel strands that a radial halo can miss. | **Medium.** Existing raster/vector geometry is present; freeze visible-only pair rules and audit sense joins. |
| 2 | Fault-tip relay/termination anatomy | **Low to moderate; very low confidence.** A spatially focused tip signal could help, but may cover few withheld pixels and endpoints are mapping-sensitive. | **Low to medium.** Existing trace endpoints; matched controls and leakage-safe endpoint handling required. |
| 3 | Host maturity/scale covariate | **Low / uncertain.** A genuinely independent maturity measure might refine decay beyond length; present-day slip rate or mapping completeness may add little or bias it. | **Low to medium if the attribute join is reliable; otherwise data-blocked.** Audit coverage and missingness before any fit. |
| 4 | Fixed-halo geophysical corroboration | **Indeterminate, potentially useful but not presently viable.** A merged-main receipt records a prior bridge transfer, but the exact training-feature raster is absent from this checkout; external coverage/alignment are also unverified, so no gain claim is justified. | **High.** Official GeoDAWN metadata/license were checked, but the actual raster file, AOI coverage, band definitions, and grid registration were not verified. Do not treat this as an obtainable usable feature yet. |

The ordering is a risk-adjusted research priority, not a measured ranking of DTI scores. It balances mechanistic specificity against cost and data readiness; a future authorized holdout, not this table, must determine whether any candidate helps.

### 1. Segment-pair stepover/bend geometry → connector and subparallel-strand zones

**Hypothesis.** Secondary fault pixels are enriched in geometrically defined
stepovers and bends, with the pattern depending on gap width, overlap, and—only
where reliable host sense exists—whether the bend is releasing or restraining.
Narrow gaps predict connector structures; wider stepovers may concentrate
strands at segment tips or as subparallel faults. This tests pairwise host
geometry, not another radial halo or the previously tested sense-only feature.

**Lane data.** `data/bridge/existing_faults.tif` and the locally pinned
`data/external/trace_segments_utm11.csv`; `qfault_attributes.csv` contains
recorded attributes but its coverage/missingness must be audited before using
sense to assign a bend class.

**Mechanism/source.** Wang et al. (2017) numerically model elevated stress and
localized strain around strike-slip bends and stepovers; their abstract reports
narrow-step connector localization and tip/subparallel localization for wider
steps. Zhu et al. (2024) review bend structures and explicitly note that bend
angle, displacement, stress regime, and model setup affect the structures.
These support testing the geometry, not a prediction gain.

**Named non-fault mimic.** Alluvial-fan risers and drainage lineaments can form
linear topographic patterns near basin faults; magnetic/lithologic contacts may
also align with structural trends. A geometry-only association could therefore
recover landscape continuity rather than a new fault.

**Future test.** Predefine the pair/stepover rules using visible catalogue traces
only; hide whole components; measure connector-, tip-, and subparallel-zone
recovery separately under the spatial holdout and the single-feature canary.
Keep bend class unknown where sense is missing. Do not pick a class boundary by
scoring the same holdout.

**Priority/cost:** highest priority; medium implementation cost. DTI effect is
unknown.

### 2. Fault-tip relay/termination anatomy → asymmetric tip neighborhoods

**Hypothesis.** The spatial distribution of withheld secondary strands differs
between along-strike tip neighborhoods and the mid-fault wall zone. Test signed
along-strike position and neighboring-segment linkage rather than a generic
unsigned distance-to-fault feature. Treat relay/linkage and termination as
competing mechanisms; a tip cluster can also shield or arrest growth.

**Lane data.** The existing fault raster and vector trace endpoints in
`data/external/trace_segments_utm11.csv`; no new raster is required to define
candidate tip geometry.

**Mechanism/source.** d'Alessio & Martel (2004) document clustered parallel
faults near a strike-slip fault-system end and analyze how those faults can
redistribute tip stress and inhibit growth. Wang et al. (2017) report that wider
stepovers localize strain near segment tips. These findings motivate a
bidirectional test, not an assumption that every tip is a growth site.

**Named non-fault mimic.** Alluvial-fan margins, dry washes, and road corridors
can produce lineaments near mapped fault ends and can be mistaken for relay
strands.

**Future test.** Calculate signed tip distance from visible vectors only, compare
held-out pixels at tips with matched mid-wall controls, and report both sides of
the fault. Reject a tip rule if the leakage canary fires or if results depend on
truth-informed endpoint geometry.

**Priority/cost:** second; low-to-medium cost. DTI effect is unknown.

### 3. Host maturity/scale → secondary-strand density and decay

**Hypothesis.** Damage-zone radial decay and secondary-strand density may vary
with host fault maturity/scale. Test whether independently recorded host
attributes add information beyond the already-used length proxy; do not
reinterpret fault length or slip rate as cumulative displacement without
validation.

**Lane data.** Locally pinned `data/external/qfault_attributes.csv` includes
`SLIPRT2023`, `REC2023`, and mapping fields; `trace_segments_utm11.csv` provides
trace geometry. The actual availability and independence of these attributes
at the host-segment level must be established before use.

**Mechanism/source.** Savage & Brodsky (2011) describe a displacement-dependent
change in apparent damage-zone thickness/decay and interpret mature zones as
superposed damage from secondary strands. Their evidence concerns displacement
and fracture distributions; it does **not** establish that present-day slip rate
is a substitute for cumulative displacement or a direct DTI predictor.

**Named non-fault mimic.** Inherited joints and lithologic contacts can raise
fracture/lineament density without representing secondary faults generated by
the mapped host.

**Future test.** First audit the attribute join and missingness without looking
at holdout outcomes. Use only a well-supported, predeclared host covariate; keep
length-only as a control and test a single additional factor on spatially
withheld components. If cumulative displacement cannot be sourced reliably,
retain this as exploratory and do not describe slip rate as displacement.

**Priority/cost:** third; low-to-medium cost if metadata joins cleanly, otherwise
data-blocked. DTI effect is unknown.

### 4. Independent geophysical confirmation, restricted to a fixed fault-zone halo

**Hypothesis.** Within a damage-zone region fixed from visible catalogue geometry,
local magnetic-gradient magnitude/coherence may help distinguish secondary
fault traces from the broader geometric halo. This tests fixed-halo local
geophysical support—not the already-tested candidate magnetic-edge tangent's
relative-strike feature. It is a within-lane corroborator, not an unconstrained
geophysical classifier over the whole survey; incremental value is unknown.

**Lane data.** `training_features.tif` is declared in `data/README.md`. Merged main records a prior eight-pin bridge transport check, but the file is absent from this checkout and was not re-fetched or used in this audit. Public catalogue metadata for the USGS/DOE GeoDAWN
northwestern Great Basin Nevada/California survey is available through the
Geothermal Data Repository and links to USGS ScienceBase. GDR submission 1591
displays public access and CC-BY 4.0; the linked USGS/ScienceBase record is
separately recorded as CC0 1.0 in the source audit. Those are source-specific
statements, not a proven conflict. No exact binary asset/license receipt was
retrieved; the data file, coverage, usable bands, CRS, and contest-grid
alignment have **not** been verified. Therefore this candidate is data-blocked
and is not currently viable. No GeoDAWN data were downloaded or used.

**Mechanism/source.** USGS Open-File Report 2002-384 documents a
high-resolution aeromagnetic survey used to image shallow faults in Dixie
Valley, Nevada. It is a regional interpretive analogue—not validation of this
feature, the competition-grid coverage, or contest-grid alignment.

**Named non-fault mimic.** Magnetic contrasts at lithologic contacts, surficial
drainages, and anthropogenic metallic features can produce lineaments or
anomaly edges without a fault strand.

**Future test.** Only proceed after an official free data file is obtained with
receipt, checked for coverage/grid/CRS, and restricted to a preregistered halo.
Hide complete segments; recompute geophysical transforms without withheld-label
access; apply the same leakage canary and compare HOLDOUT-DTI against the
geometry-only control. If the exact official features remain unavailable, do
not substitute an unverified source.

**Priority/cost:** fourth; high data/registration cost. DTI effect is unknown.

## Validation gate (not a slot decision)

Any future authorized run must use the whole-segment spatial hide-and-recover
protocol, visible-only catalogue features, pixel-exact masking, pooled DTI
(alpha 0.2, beta 0.8, 300 m triangular kernel), the single-feature leakage
canary, and a version/input-hash-pinned evaluator with withheld-positive count
and 95% CI. Before placement and on final dots, apply the registry checks; stop
at `rho > 0.90` or more than 70% of candidate dots within 3 px of any registry
raster. A separate selector decides whether to promote a candidate to a weekly
slot. No hypothesis here is cleared, submitted, or claimed to improve a score.

## Sources reviewed

1. Wang, H., Liu, M., Ye, J., Cao, J. & Jing, Y. (2017). “Strain partitioning
   and stress perturbation around stepovers and bends of strike-slip faults:
   Numerical results.” *Tectonophysics* 721, 211–226.
   [DOI: 10.1016/j.tecto.2017.10.001](https://doi.org/10.1016/j.tecto.2017.10.001).
   Abstract and article preview reviewed.
2. Zhu, M. et al. (2024). “An overview of structures associated with bends of
   strike-slip faults: Focus on analogue and numerical models.” *Marine and
   Petroleum Geology* 167, 106983.
   [DOI: 10.1016/j.marpetgeo.2024.106983](https://doi.org/10.1016/j.marpetgeo.2024.106983).
   Abstract and review highlights reviewed; authors caution that model setup
   and heterogeneous settings matter.
3. d'Alessio, M. A. & Martel, S. J. (2004). “Fault terminations and barriers to
   fault growth.” *Journal of Structural Geology* 26(10), 1885–1896.
   [DOI: 10.1016/j.jsg.2004.01.010](https://doi.org/10.1016/j.jsg.2004.01.010).
   Abstract and article preview reviewed.
4. Savage, H. M. & Brodsky, E. E. (2011). “Collateral damage: Evolution with
   displacement of fracture distribution and secondary fault strands in fault
   damage zones.” *Journal of Geophysical Research: Solid Earth* 116(B3).
   [DOI: 10.1029/2010JB007665](https://doi.org/10.1029/2010JB007665).
   Open-access abstract reviewed.
5. Grauch, V. J. S. (2002). “High-resolution aeromagnetic survey to image
   shallow faults, Dixie Valley geothermal field, Nevada.” USGS Open-File
   Report 2002-384. [DOI: 10.3133/ofr02384](https://doi.org/10.3133/ofr02384).
   Official USGS report record reviewed; no data download performed.
6. Glen, J. & Earney, T. (2024). “GeoDAWN: Airborne magnetic and radiometric
   surveys of the northwestern Great Basin, Nevada and California.” Geothermal
   Data Repository, USGS. The [GDR record 1591](https://gdr.openei.org/submissions/1591)
   displays public access and CC-BY 4.0; the linked [USGS ScienceBase record](https://doi.org/10.5066/P93LGLVQ)
   is separately recorded as CC0 1.0 in the official source audit. The exact
   binary asset/license was not retrieved, so these source-specific statements
   do not establish the applicable terms for a future file. Coverage, bands,
   CRS, and grid alignment remain unverified.
