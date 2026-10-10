# Archived session-2 candidate geological hypotheses — 5 candidates, ranked

**ARCHIVED (2026-10-10):** This is a historical session record, not the current H57 slate or release evidence. Its statements about data availability, baselines, and prior-session status describe that earlier execution only. This checkout currently lacks the gitignored `data/official/training_features.tif`; see the current README, data-pin tests, and `evidence/run_card_current.json` before relying on availability or score claims.

Date: 2026-10-09. Scope: candidates **not tried in any previous session** of this
repository (H57-A shipped; H57-B..E specified but unvalidated). Each candidate names
the layer(s), the physical signature, why it should catch a fault missing from
USGS/INGENIOUS rather than one already catalogued, and how it differs from anything
implemented here or in the 15 registered sibling rasters.

**New capability this session:** the pinned 419 MB feature stack
`data/official/training_features.tif` (sha256 `4371c82e…`, 19 bands, EPSG:32611,
same grid) was assembled from the sha256-verified 6GEMSDOE bridge parts and passed
`scripts/prepare_data.py` — *all 8 pins verified*. Every geophysical candidate below
is therefore **obtainable today, free, from the official competition data** (the
stack is the competition's own training-features file; no third-party download
needed). That removes the block recorded as `H57-E`/`REMAINING_WORK` item 2.

Instrument discipline (unchanged): candidates are ranked for expected **HOLDOUT-DTI**
improvement over the current holdout best (`no_side` 0.2556 detached / `anatomy_full`
0.2517 all), with the known caveat that holdout-to-live transfer is weak
(ρ ≈ +0.14, `REMAINING_WORK` item 1). A second, explicitly-labelled
**CONSENSUS-PROXY** instrument (agreement with six registry rasters bearing
owner-reported value labels) is used only as an exploratory file-agreement feature;
those labels are not exact-file organizer receipts. In particular, the 0.2778
claim is unverified and H33-2-B2 is owner-marked UNSCORED. This proxy is not a
live-truth calibration and is never written as a score.

---

## Ranking summary

| Rank | ID | Candidate | Layers (pinned stack band) | Expected HOLDOUT-DTI gain | Cost | Status |
|---|---|---|---|---|---|---|
| 1 | **H57-G1** | Zone-gated multi-method edge corroboration | `tmi_hg` 3, `tc` 6, `det_elev_slope` 19, `iso_grav_anom_hg` 18 | high (adds the incumbents' proven off-catalogue signal inside our fitted zone) | medium | **validated this session (EXP-1)** |
| 2 | **H57-G2** | Conductive clay-cap / alteration targeting | `cond_surf` 17, `iso_grav_anom_vg` 11, `depth_to_base_surf` 15 | medium-high (geothermal-specific; no registry lane uses conductivity) | low once G1 exists | folded into EXP-1 feature block |
| 3 | **H57-G3** | Blind-fault cover-contrast edge | `depth_to_base_surf` 15 gradient, `iso_grav_anom_slope` 5, `geod_2ndinv` 4 | medium (catches buried faults with zero surface expression) | medium | backlog |
| 4 | **H57-G4** | Tip-lobe splay nucleation | catalogue only (trace endpoints, tip curvature) | low-medium (registry tip rasters have owner-reported labels 0.2632–0.2710; exact-file receipts not verified here) | low | backlog (drift risk vs registry tip rasters) |
| 5 | **H57-G5** | Geodetic strain-corridor intersection | `geod_shearrate` 7, `geod_dilaterate` 8, `deq_n100a15` 10, `ieq_n100a15` 16 | low (signal diffuse at 100 m) | low | backlog |

---

## H57-G1 — Zone-gated multi-method edge corroboration (TOP CANDIDATE)

**Hypothesis.** The fitted fault-zone-anatomy intensity is a *prior* for where
secondary strands sit; independent geophysical edge evidence is the *likelihood*.
Emitting at their product concentrates the dot budget where a strand is both
mechanically expected and physically detected, which is the intersection neither
this lane's pure-geometry model nor the incumbents' ungated geophysics can reach.

**Layers.** `training_features.tif` bands `tmi_hg` (TMI horizontal-gradient
magnitude), `tc` (tilt derivative — edge detector), `det_elev_slope`
(detrended-elevation slope — scarp detector), `iso_grav_anom_hg` (isostatic-gravity
horizontal gradient), each robust-z scored inside the footprint; plus their max
("multi-method edge consensus"). Gated by the fitted anatomy zone of H57-A.

**Physical signature.** Ridge/edge transforms. A fault strand offsets magnetic
blocks (TMI horizontal-gradient ridges, tilt-derivative edges), density contrasts
(gravity horizontal gradient) and topography (scarps on detrended elevation). Four
independent sensors; a lithologic contact produces at most one or two of them
aligned, a through-going strand produces all four along one lineament.

**Why it catches faults missing from USGS/INGENIOUS.** A newly mapped strand of an
existing system (organizer thread 11536) is, by definition, not in the catalogue —
but it still offsets magnetic blocks and bedrock topography. The incumbents prove
the geophysical signal may help locate off-catalogue structures; earlier raster
files with owner-reported values were described as geophysics-ranked, but those
values are not uniform exact-file receipts and 0.2778 is unverified. SGMC
off-catalogue pixels sit overwhelmingly within 1–2 km of known faults (41.0 %
within 1 km, measured in EXP-1b). The intersection of geophysical detection and
mechanical placement near a known fault is a hypothesis about the hidden truth,
not an established sampling rule.

**How it differs from everything in the repo/registry.** (i) H57-A is pure catalogue
geometry — no band of the stack entered it. (ii) The six top registry rasters rank
geophysics over the *whole footprint* and then prune dots near the catalogue
(incumbents keep 0 dots within 200 m of it) — they cannot place a dot in the damage
zone at all, by construction. (iii) GEMSDOE45 `h51-km-faultzone` used
a *fixed* kernel (its repository-reported value is not an organizer receipt
verified here); 7GEMSDOE `halo15-gbt` used a 15-px halo GBT (max |Spearman| vs
this lane 0.6271 — historical drift measurement only). This candidate uses the fitted, length-scaled,
azimuth-weighted zone as the gate and sparse binary emission at the DTI fixed point.

**Validation plan (executed).** EXP-1: leave-one-quadrant-out CV on the
hide-and-recover holdout, variants `d_only`, `no_side` (controls), `geo_only`
(G1 block alone), `no_side_plus_geo` (union), leakage canary on all 17 features.
Promote to the build only if the union beats `no_side` on pooled HOLDOUT-DTI with
its jackknife CI, canary clean.

---

## H57-G2 — Conductive clay-cap / alteration targeting (geothermal-specific)

**Hypothesis.** Blind geothermal systems express themselves as conductive clay caps
and hydrothermal alteration, not as mapped surface faults. Off-catalogue fault
pixels associated with geothermal circulation should coincide with conductivity
highs (`cond_surf`, the magnetotelluric surface-conductivity band) and the gravity
signature of altered, low-density rock (`iso_grav_anom_vg`), over basement
structural highs (`depth_to_base_surf`).

**Layers.** `cond_surf` (17), `iso_grav_anom_vg` (11), `depth_to_base_surf` (15).

**Physical signature.** Electrical-conductivity highs (smectite/argillic alteration
above a convective cell), negative gravity vertical-gradient over altered rock,
basement relief. This is the standard geothermal exploration triad (e.g. USGS
geothermal play-fairway methodology); it is the *vent-discovery* science the brief
asks us to research deeply.

**Why it catches catalogue-missing faults.** Geothermal systems are precisely where
new faults get mapped during field validation (veins, fumaroles, sinter — the prize
is about geothermal vents). Their controlling structures are commonly blind. No
catalogue-geometry feature can see them.

**How it differs.** No registered sibling raster uses `cond_surf` at all (registry
lanes use TMI/elevation/curvature). Folded into the EXP-1 feature block so its
marginal contribution is measured by the canary and the ablation; if EXP-1 shows
the union helps while the edge block alone does not, G2 is the surviving mechanism.

---

## H57-G3 — Blind-fault cover-contrast edge

**Hypothesis.** Faults buried under basin fill offset the basement surface without
any surface scarp. The horizontal gradient of `depth_to_base_surf` maps those
offsets; `iso_grav_anom_slope` and `geod_2ndinv` corroborate where the structure is
active or density-contrasted.

**Layers.** `depth_to_base_surf` (15) horizontal gradient, `iso_grav_anom_slope`
(5), `geod_2ndinv` (4).

**Physical signature.** Steps/edges in an otherwise smooth depth-to-basement field,
plus strain-rate localization.

**Why it catches catalogue-missing faults.** Surface-mapping catalogues (USGS
QFaults) systematically under-represent blind strands; the organizers' "new faults"
include them. SGMC contains named strands absent from QFaults for exactly this
reason.

**How it differs.** No repo lane uses the basement surface. Distinct from G1 in that
it does not need a surface expression at all. **Cost medium:** needs a derivative
transform of band 15 plus a holdout run. Backlog after G1/G2.

---

## H57-G4 — Tip-lobe splay nucleation

**Hypothesis.** Splays nucleate from the stress concentration at fault tips
(beyond-tip extension, wing cracks). Distance-to-visible-tip, tip-local curvature
and along-strike position beyond a tip should predict withheld strand pixels beyond
what distance-to-trace predicts.

**Layers.** Catalogue only: skeleton endpoints of visible components, local
curvature at the endpoint, along-strike offset beyond the tip.

**Physical signature.** Tip stress lobes (e.g. wing-crack geometry), relay ramps
between overlapping tips.

**Why it catches catalogue-missing faults.** The organizers confirmed newly mapped
*geometry of an existing system* counts (thread 11536); beyond-tip extensions and
relay splays are the canonical case.

**How it differs.** H57-B (specified last session, never run) is this candidate;
what is new here is only the execution. Registry tip-centric lanes
(`h32-1-prethin-tip-euler` 0.2649, `h38-1-hf-euler-r30-r1` 0.2707,
`h33d-analog-tip-stepover` 0.2632) occupy this space, so the uniqueness gates
(rho ≤ 0.90, 3-px dot overlap ≤ 70 %) must be watched on the final dots. **Cost
low.** Backlog.

---

## H57-G5 — Geodetic strain-corridor intersection

**Hypothesis.** Where geodetic shear-rate corridors (`geod_shearrate`,
`geod_2ndinv`) cross the fitted zone and seismicity density (`ieq_n100a15`,
`deq_n100a15`) is elevated, brittle strand density is elevated — active shear
localization outruns geological mapping.

**Layers.** `geod_shearrate` (7), `geod_dilaterate` (8), `deq_n100a15` (10),
`ieq_n100a15` (16).

**Physical signature.** Strain-rate tensor magnitude and shear-rate corridors,
dilatational jogs, earthquake-density halos.

**Why it catches catalogue-missing faults.** Active structures are still
accumulating displacement and may never have been mapped; the geodetic field sees
the total zone, not the mapped trace.

**How it differs.** No repo lane uses geodesy. **Expected gain low** — at 100 m
pixels the geodetic fields are smooth and far-field; ranked last. **Cost low.**
Backlog.

---

## Cross-cutting instrument note (all candidates)

The hide-and-recover holdout withholds *catalogue* pixels and is a local instrument
(transfer to live is weak). The **CONSENSUS-PROXY** added this session measures how
much of a candidate's emitted dots fall within 3 px of ≥ 2 of the six independent
registry rasters carrying owner-reported value labels; the values are not
uniformly tied to exact bytes by submission receipts, and the H33-2-B2 / 0.2778
mapping is specifically withdrawn. Agreement among these files is an exploratory
proxy only, not a live-calibrated or hidden-truth-bearing measurement. It is never
reported as a score and cannot rescue a candidate that fails the holdout.
