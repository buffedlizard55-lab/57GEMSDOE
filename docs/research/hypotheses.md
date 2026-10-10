# Candidate geological hypotheses — ranked by expected DTI improvement and cost

> **Archived backlog snapshot.** Its H1 metrics and 663-raster count refer to the earlier
> experiment, not the current Session 4 run. Current H57-K measured detached-mode
> **HOLDOUT-DTI 0.242353** (95% quadrant-jackknife CI 0.205591–0.279115), but failed the
> strict pre-placement 3-px registry-overlap gate. No H57-K TIFF exists and no artifact is
> cleared for download/submission. See [`session4-hypotheses.md`](session4-hypotheses.md),
> the [`README`](../../README.md), and [`IR-57-SCORE-02`](../irregularities.html).

Scope: the hidden truth is **new expert-mapped faults NOT in USGS/INGENIOUS** — including
splays and parallel strands of existing systems (organizer thread 11536) — and pixels of
known USGS/INGENIOUS faults are masked out of the evaluation (thread 11516). The metric is
distance-weighted Tversky: `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`, credit radius
300 m (3 px), FP cheap, FN expensive. Every candidate below is scored on the same two
instruments before any slot is touched:

- **HOLDOUT-DTI** (brief's instrument): `gems52-pooled-hide-v1`, 4 random whole-segment
  folds, 300 m truth buffer, features from visible faults only, 38,339 withheld
  positives, paired spatial-block bootstrap 95% CI. Measures catalogue-segment recovery.
- **PROXY-DTI (SGMC-truth)**: the 79,025 SGMC pixels captured by neither USGS nor
  INGENIOUS — a local off-catalogue proxy, not an organizer score. The H33-2-B2 raster's
  local proxy DTI is 0.0931; that measurement does not validate a live score or attribute
  0.2778 to the raster. The inspected GEMSDOE32 owner repository marks H33-2-B2 UNSCORED;
  0.2747 is a projection. See [`IR-57-SCORE-02`](../irregularities.html).

Lane protocol: 3 experiments, 2 hours. **All 3 are used** (Exp 1b measurement, Exp 2
holdout arms × budget, Exp 3 submission build). H1 below is the lane that was run;
H2–H5 are the ranked backlog for the next session.

---

## H1 — Fault-zone anatomy (RUN — this lane)

**Hypothesis.** New expert-mapped faults concentrate as secondary strands in the damage
zones of known faults: subparallel splays and parallel strands whose distance from the
primary trace, azimuth relative to its strike, and along-strike position (beyond-tip
extensions) follow shear-zone mechanics, with zone width growing with fault length.

**Layers.** `existing_faults.tif` (USGS QFaults raster) + INGENIOUS record vectors
(`data/external/trace_segments_utm11.csv`, `qfault_attributes.csv`), linked into 2,588
catalogue segments; 1,126 INGENIOUS record segments as vector ground truth.

**Physical signature.** Geometric halo: Euclidean distance to the nearest known-fault
pixel, offset azimuth relative to the host fault's strike, along-strike position
(beyond-tip), host-fault length (displacement proxy), recorded sense of slip.

**Why it catches faults missing from USGS/INGENIOUS.** The organizers said a new fault
includes "newly mapped geometry of an existing system," and splays/parallel strands count
(thread 11536). SGMC (real off-catalogue faults) confirms the anatomy: 41.0% of SGMC
off-catalogue pixels lie within 1 km of a known fault; the radial density peaks at
1–2 px from known traces and the offset-azimuth mass concentrates across-strike
(φ median 72°, 43.4% beyond 75°).

**How it differs from what the family already does.** Every top registry lane ranks
pixels by *geophysical evidence* (TMI gradients, RTP, elevation slope, density — h16–h63,
d28, anderson) and then prunes dots off the catalogue (the incumbents keep 0 dots within
200 m of it). The previous fault-zone attempt (GEMSDOE45 `h51-km-faultzone`, owner-reported
0.0106) placed a *fixed* kernel around the catalogue. H1 instead **fits** the radial, azimuth and
length distributions on the holdout and emits a sparse binary top-k inside the fitted
halo at 400–1000 m from known faults — the region the incumbents deliberately avoid.

**Measured (HOLDOUT-DTI 0.0580 [0.0507, 0.0663] @ 60k; SGMC-truth 0.0457 @ 60k,
0.0650 @ 120k).** Beats its own controls (random 0.0492, uniform-halo 0.0117 at 60k),
leakage canary max AUC 0.6538 < 0.90, unique vs all 663 registry rasters
(max |Spearman| 0.6271). Trails the incumbents 2–3× on the SGMC instrument.

**Cost.** Low (done, ~40 min compute). **Rank: baseline — validated, delivered, negative
as a standalone score-beater.**

---

## H2 — Zone-gated geophysical corroboration (TOP RANKED for the next session)

**Hypothesis.** The fitted damage zone says *where* new faults can be (the halo, 4.35M px);
geophysical lineament strength says *which* halo pixels actually host strands. Multiplying
the fitted intensity by a geophysical ridge/edge strength **restricted to the fitted halo**
should beat both the pure-geometry halo (H1) and the ungated geophysics (the incumbents'
approach, which spreads its budget over the whole footprint and is then pruned).

**Layers.** `training_features.tif` bands — `tmi_hg` (TMI horizontal-gradient magnitude,
a ridge detector), `det_elev_slope` (slope of detrended elevation, scarp detector),
`rtp` — masked to the fitted halo; catalogue + INGENIOUS as in H1.

**Physical signature.** Edge/ridge transforms of gravity and topography: fault strands
produce linear magnetic-gradient ridges and elevation scarps subparallel to the host.

**Why it catches faults missing from USGS/INGENIOUS.** The incumbents prove the
geophysical signal finds off-catalogue faults (SGMC-truth 0.093–0.145); the halo proves
where new faults sit (SGMC: 41% within 1 km of known). Their intersection is the highest-
precision region in the study area; gating concentrates the emission budget where the
metric's FN pressure is highest.

**How it differs.** H1 is pure catalogue geometry; the incumbents are ungated
geophysics-ML; H2 is the *product* — geophysics ranks pixels, the fitted zone bounds
them. Also differs from GEMSDOE45's fixed-kernel zone by using the fitted, length-scaled,
azimuth-weighted zone and from 7GEMSDOE's `halo15-gbt` (a GBT trained on a 15-px halo,
1.83M positive px, max |Spearman| 0.6271 vs this lane) by emitting a sparse binary top-k
inside a *fitted* 60-px halo.

**Expected DTI improvement.** Highest of the backlog: the incumbents' off-catalogue
signal (SGMC 0.093–0.145) concentrated inside the fitted halo instead of spread over the
footprint. **Cost.** Medium (~1–2 h: ridge extraction, halo masking, Exp-2-style holdout
rerun). **Validation before any slot:** HOLDOUT-DTI must beat the current holdout best
(d15 scores 0.0844 as-is on these folds; H1 scores 0.0580 rebuilt) on the same
instrument, plus the SGMC-truth sweep.

---

## H3 — Along-strike tip-relay targeting (vector-native)

**Hypothesis.** Beyond-tip extensions are the single most reliable new geometry: the
holdout measured **64.2% of withheld mass beyond segment tips**, and SGMC off-catalogue
faults show 45.3% beyond-tip with Δstrike median 19.5° (63.0% within 30° of the host
strike). Emitting along the host fault's strike azimuth, just past mapped tips, targets
the highest-precision subset of the H1 zone.

**Layers.** `trace_segments_utm11.csv` + `existing_faults.tif` (vector segments give
tips and strikes directly; the raster alone cannot).

**Physical signature.** Along-strike continuation (φ ≈ 0 relative to host strike) at
`u < 0` or `u > 1` (beyond-tip), with tip-to-tip distance following the fitted
length scaling.

**Why it catches faults missing from USGS/INGENIOUS.** "Newly mapped geometry of an
existing system" (thread 11536) is most often a mapped tip extension or a strand the
mapper added along strike; the holdout's beyond-tip majority says the same for the
withheld population.

**How it differs.** H1 fits the *full* azimuth distribution (including the across-strike
splay mode); H3 emits only the beyond-tip along-strike class. It is a subset of H1's
zone with a sharper azimuth prior.

**Expected DTI improvement.** Moderate — a smaller, higher-precision emission (fewer FP
per TP inside the 3-px credit radius). **Cost.** Low–medium. **Validation:** holdout
with the tip-relay arm isolated (the template's tip instrument already measures
tip-adjacent recovery); must beat H1's 0.0580 on HOLDOUT-DTI and improve the
SGMC-truth sweep at equal budget.

---

## H4 — Slip-rate-weighted zone width (physical refinement of H1)

**Hypothesis.** H1 uses segment *length* as a displacement proxy; the INGENIOUS database
records slip rate directly (`SLIPRT2023`, mm/yr in `qfault_attributes.csv`). Savage &
Brodsky (2011) and the Tchalenko/Schreurs damage-zone literature scale zone width with
displacement; fitting the width against the recorded rate should sharpen the radial
density where the proxy is crude (long but slow vs short but fast faults).

**Layers.** `qfault_attributes.csv` (slip rate) + `trace_segments_utm11.csv` +
`existing_faults.tif`.

**Physical signature.** Wider damage halos around higher-slip-rate faults; the radial
density's scale parameter becomes a fitted function of slip rate instead of length.

**Why it catches faults missing from USGS/INGENIOUS.** New strands are likelier where
the host accommodates more displacement; the length proxy mis-ranks hosts whose raster
segments are fragmented or merged.

**How it differs.** A refinement *inside* H1's mechanism (replaces `s(L)` with
`s(slip)`), not a new lane.

**Expected DTI improvement.** Small–moderate. **Cost.** Low. **Validation:** ablation
inside Exp 2's protocol — the `full` arm with `s(slip)` vs `s(L)` on HOLDOUT-DTI; ship
only if it beats 0.0580 within the CI.

---

## H5 — USGS QFaults vector sense join (DATA-BLOCKED in this sandbox)

**Hypothesis.** The catalogue raster carries no sense of slip; dextral, sinistral and
normal hosts produce *mirrored* splay geometries (Riedel R vs R′ shear orientations, and
normal-fault antithetic splays). Conditioning the azimuth factor `ĝ(φ)` on the host's
recorded sense should sharpen the across-strike mode. The holdout cannot resolve sense
(nearest-visible sense: unk 38,063 / N 214 / RL 53 / LL 9) — the INGENIOUS database has
it for only 1,126 of 3,714 segments — so the USGS Quaternary Fault and Fold Database
vectors would extend sense coverage to the whole known set.

**Layers.** USGS QFaults vector database (Quaternary Fault and Fold Database of the
United States — `earthquake.usgs.gov` / ScienceBase; official, free, public domain) joined
to `existing_faults.tif` by fault name/section.

**Physical signature.** Sense-conditioned offset-azimuth density: Riedel R shears at
~15° and R′ at ~75° to the host for strike-slip (Tchalenko 1970), antithetic vs
synthetic splays for normal faults (Schreurs 2003).

**Why it catches faults missing from USGS/INGENIOUS.** New strands inherit their host's
sense; a dextral host's new splays appear on the Riedel-R side, which the marginal
azimuth fit currently smears over both sides.

**How it differs.** Extends H1's `ĝ(φ)` from a marginal to a resolved conditioning.

**Expected DTI improvement.** Moderate. **Cost.** Low once data is in hand — **but the
source is unreachable from this sandbox** (`earthquake.usgs.gov` returns HTTP 000;
verified repeatedly). Needs a fetcher from a network that can reach it, or a manual
download. **Validation:** sense-conditioned ablation in Exp 2's protocol; the canary
(single-feature AUC) must stay < 0.90.

---

## Ranking summary

| # | Hypothesis | Expected DTI gain | Cost | Status |
|---|---|---|---|---|
| H2 | Zone-gated geophysical corroboration | **highest** | medium | backlog — validate next |
| H1 | Fault-zone anatomy (fitted halo) | baseline (measured) | low | **RUN — delivered, negative standalone** |
| H3 | Along-strike tip-relay targeting | moderate | low–med | backlog |
| H5 | USGS vector sense join | moderate | low | **data-blocked** (earthquake.usgs.gov unreachable) |
| H4 | Slip-rate-weighted zone width | small–moderate | low | backlog |

Slot rule honored: H1 was validated on the spatially-blocked holdout **before** any
submission was written, and the verdict is **negative** for slot promotion — on the
brief's holdout instrument H1 (0.0580 rebuilt) does not beat the current holdout best
(d15, 0.0844 as-is on the same folds), and on the SGMC-truth live proxy it trails the
incumbents 2–3×. The generated TIF is a validated unique artifact, not a slot candidate.
