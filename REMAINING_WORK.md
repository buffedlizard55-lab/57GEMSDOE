# Remaining work and limitations — current status (2026-10-10 UTC)

## Submission status: **HOLD — NOT OK TO DOWNLOAD OR SUBMIT**

There is no cleared submission file. Do not use the retained historical TIFF. No new
experiments, holdout runs, GeoTIFF builds, downloads, or submissions occurred in this audit;
the three-experiment / two-hour budget is spent. No weekly slot was used.

The latest stored scan measured the soft candidate against the 679-entry indexed public
owner-repository inventory (not organizer-complete): maximum full-footprint Spearman 0.821258;
maximum forward 3-pixel overlap 1.0 on the soft surface's
inherited finite-positive support (treated as “dots” by the gate), with 78 firings above the
0.70 stop threshold. This was a pre-placement support comparison, not a final-dot comparison.
The overlap gate failed before placement, so final dots were not generated. The scan is historical.
Two older `-zeros.tif` reports use different 644- and 655-raster snapshots (114/50 and 98/98
overlap firings/itemized respectively); both also fail and neither is the current comparison. A
fresh cache preflight found **0 of 679** indexed rasters present; no current cache hashes or grids
could be verified. No candidate fitting or TIFF creation occurred during that preflight.

A session-5 independent witness check re-fetched and SHA256-verified the in-scope 17GEMSDOE
`E-proba-multiscale` raster (5,167,373 positive cells). Its 3-pixel support covers every
allowable cell and gives measured forward overlap 1.0 for dense and sparse test candidates. Under
the literal >70% overlap rule, every nonempty candidate is blocked while this witness remains in
scope. This is a registry measurement—not a score, threshold change, or full 679-raster cache
revalidation. The public owner-repository index cannot prove completeness against private,
unlinked, inaccessible, externally stored, or later-written competition rasters. No density or
reverse-overlap exception is authorized. A separate check found the archived 40,000-dot
`h57-anatomy-enechelon` candidate has 0.7113 forward 3-pixel overlap against its own earlier
build, also above the literal 0.70 limit; see `evidence/independent_candidate_check.json`.

The latest recorded soft-surface `HOLDOUT-DTI` is 0.023203 (95% CI [0.018778, 0.027992],
11,321 withheld positives, evaluator `gems57-pooled-hide-v2`); its source hashes predate the
current evaluator code. The separate binary-allocation HOLDOUT-DTI is 0.109168
(95% CI [0.094503, 0.124194]) and is not the score of that soft TIFF. The older 0.227908
reading is unpinned legacy context. The 0.2778 figure is owner-reported without an organizer
receipt tying it to exact bytes. A separate raster audit found the named H33-2-B2 artifact is an
exact 2-pixel catalogue-flank prune of a 40,199-positive base (2,545 removed, none added; 37,654
remain). That could plausibly reduce false-positive cost under max-cover DTI, but no causal gain is
verified. The saved public board now shows rank #1 at 0.3774, DARD at rank #8 / 0.3195, and
extradr19 at rank #22 / 0.2778 in the selected-row snapshot retrieved 2026-10-10 20:40:27 UTC.
Only rows 1–22 were captured; raw HTML was not retained. The numeric rank-22/H33 match does not
establish participant identity or exact-file attribution. See `evidence/leaderboard_snapshot.json`
and `evidence/feed_refresh_status.json`; the Pages workflow is configured for scheduled public
refresh, but this local manual capture was not produced by `scripts/refresh_feed.py`. No public
board number here is `ORGANIZER-CONFIRMED` exact-file evidence.

The historical H57-K `lane8_geophys` reading is **HOLDOUT-DTI (historical; evaluator version ID
not recorded)** 0.110327, 95% quadrant-jackknife CI [0.091677, 0.128977], 22,619 withheld
positives over 8 recorded cells. Its single-feature canary flags `d`, `d_perp`, and `vis_dtip`
above AUC 0.90; that run's own evidence does not pin evaluator/input hashes. The later pooled-hide-v2
records use 11,321 withheld positives and different outputs; their stored source hashes do not
match the current tree. These scores are not comparable. The later soft surface and binary
allocation are not the same representation. No candidate has beaten a valid, comparable,
current-code holdout benchmark. See `evidence/holdout_scope_reconciliation_20261010.json`.

The read-only local attribute audit (`evidence/attribute_audit_20261010.json`) found 84,331 trace
rows (1,126 records), with 1,394 sense values missing; QFault has 22,956 rows with numeric
`SLIPRTNUM` and `RECNUM`, but only 89 nonmissing `SECONDARY` values and 4,059 missing `MAPSCALE`
values. This is descriptive completeness only: no host-level join or spatial test was run. `RECNUM`
is the upper bound on the latest surface-deforming earthquake; slip rate/recency are not cumulative
displacement. The revised four-item shortlist ranks explicit visible branch-end/junction topology × recorded sense first, then slip-rate- and recency-conditioned anatomy, followed by a data-gated official USGS tendency modifier. The generic sense-by-angle/distance model was already tested; the current top item is a narrower topology-conditioned refinement. The slip-rate idea was proposed earlier in the archived H57 slate but remains unrun. None is implemented or validated.

## Blocking work (not permission to proceed)

1. **Protocol blocker:** the independently verified 17GEMSDOE witness covers the full allowable
domain under the required 3-pixel support rule, so any nonempty candidate fails the >70% test.
Do not exclude it, alter the threshold, or apply a density/reverse-overlap exception without an
explicit owner protocol revision. Under the unchanged rule, the gate is unsatisfiable.
2. **Registry:** the present checkout has 0/679 cache files. Any future public-inventory audit
would need every indexed file in `evidence/registry_refreshed.json` restored and SHA256/grid
verified; the historical scan and one re-fetched witness do not replace that check. Even a complete
local copy of this 679-entry public owner-repository inventory would not establish
organizer-complete scope; `registry/audit_scope.json` records those exclusions.
3. **Validation:** current-code spatial hide-and-recover evidence must include evaluator version,
source/input hashes, withheld-positive count, 95% CI, and a clean single-feature leakage canary.
The existing experiment budget is spent; no such run is authorized by this document.
4. **Uniqueness:** if the protocol is explicitly revised, apply its authorized surface rank-correlation
and pre-placement/final 3-pixel overlap checks against the complete registry. Under current
instructions, stop at rho > 0.90 or >70% overlap; no exception is authorized.
5. **Selector:** only a separate, independently versioned selector may promote a cleared
candidate to a weekly slot. No slot was used or is authorized by this audit.
6. **Publisher and format:** `scripts/build_submission.py` is a retired no-output stub. Do not
restore candidate-building until renewed authorization and an independently complete comparison
scope exist. If a future candidate is ever cleared, it must be a uniquely named, locally validated
single-band float32 GeoTIFF (or a ZIP containing exactly that TIFF), finite in `[0,1]` and matched
to the pinned grid. Local format checks are not organizer acceptance.

## Future research shortlist (unrun)

Four ranked fault-zone-anatomy hypotheses, named non-fault mimics, mechanism evidence, data needs,
and controls are documented in [`docs/research/hypotheses.md`](docs/research/hypotheses.md) and
[`evidence/hypotheses_current.json`](evidence/hypotheses_current.json). The ranking is a future
research priority, not a projected DTI gain. None is actionable under the current universal
uniqueness blocker; do not implement or evaluate them without explicit protocol resolution,
renewed authorization, and a new experiment budget.

## Additional scientific, data, and compliance limits

- Hide-and-recover tests catalogue recovery, not unpublished expert mapping of new faults; component boundaries can split one geological fault or join separate systems, and catalogue bias/domain shift remain uncalibrated.
- Stored bootstrap intervals condition on the fitted folds, masks, catalogue labels, and fixed budgets. They are not forecasts of hidden/private scores and do not include all refit/model-selection uncertainty.
- Fault length is only a noisy maturity/displacement proxy. Do not substitute fault length or slip rate for cumulative displacement without an independent justification.
- Relative strike/sense fields are bounded by visible-neighbor sampling, attribute joins, and source-rasterization limitations; they do not establish stress inversion or a universal mechanism.
- Magnetic dikes, geologic contacts, flight-line leveling residuals, and variable survey clearance can mimic fault strands. GeoDAWN's public catalogue/license record was checked, but coverage, CRS, usable bands, and contest-grid overlap were not.
- No geothermal heat, fluid flow, reservoir volume, or economic-viability labels are validated here. This lane concerns fault probability, not proof of a geothermal resource.
- Before any future competition submission, re-check official rules, entrant eligibility, external-data licenses, required reproducibility material, and any AI-use disclosure. No credentials should be requested or stored in chat.
- `docs/review_passes.md` and `evidence/review_passes.json` preserve the multi-pass audit record. Earlier session plans and claims are retained under `evidence/history/` and in `TASK_PROMPT.md`; they are provenance, not current status or permission.

## Source of truth

- [`README.md`](README.md): status-first brief and preserved task prompt.
- [`BRIEF.md`](BRIEF.md): standing protocol and current HOLD notice.
- [`evidence/run_card.json`](evidence/run_card.json): current machine-readable audit record.
- [`docs/executive-summary.html`](docs/executive-summary.html): user-facing conditional guide;
  it explicitly says no download or submission is approved.
- [`evidence/history/remaining_work_legacy_2026-10-09.md`](evidence/history/remaining_work_legacy_2026-10-09.md): prior planning notes retained for provenance only; not current instructions.
