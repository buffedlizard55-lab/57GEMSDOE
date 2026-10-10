# Remaining work and limitations — current status (2026-10-10 UTC)

## Submission status: **HOLD — NOT OK TO DOWNLOAD OR SUBMIT**

There is no cleared submission file. Do not use the retained historical TIFF. No new
experiments, holdout runs, GeoTIFF builds, downloads, or submissions occurred in this audit;
the three-experiment / two-hour budget is spent. No weekly slot was used.

The literal full-registry report records a maximum forward 3-pixel dot overlap of 1.0 and 114
firings above the 0.70 stop threshold (only 50 itemized), so its verdict remains **HOLD / STOP**.
A separate current-cache preflight found **0 of 644** indexed rasters present; all cache paths
were missing. No candidate fitting or TIFF creation occurred during that preflight.

The historical local `HOLDOUT-DTI` value 0.227908 (95% CI [0.186735, 0.269081], 22,641
withheld positives) is unpinned legacy context, not current-code validation or a live-score
projection. The 0.2778 figure is owner-reported without an organizer receipt in this repository;
0.3195 and 0.3774 remain conflicting, unverified reports. No gain estimate is supported.

## Blocking work (not permission to proceed)

1. **Registry:** restore the 644 cache files for the exact SHA256-pinned full inventory and verify
every file and grid before any future candidate fitting. A missing or changed entry keeps the
uniqueness decision blocked.
2. **Validation:** current-code spatial hide-and-recover evidence must include evaluator version,
source/input hashes, withheld-positive count, 95% CI, and a clean single-feature leakage canary.
The existing experiment budget is spent; no such run is authorized by this document.
3. **Uniqueness:** apply the literal surface rank-correlation and pre-placement/final 3-pixel dot
overlap checks against the complete registry. Stop at rho > 0.90 or >70% overlap; no reverse-
overlap or saturation exception is authorized.
4. **Selector:** require an independent versioned local-build selector receipt only after the
validation and registry gates clear. Weekly-slot promotion is a separate decision. No slot may be
used by the build script.
5. **Format:** only after all gates clear may the fail-closed writer create a uniquely named,
validated single-band float32 GeoTIFF and a ZIP containing exactly that TIFF. Local format checks
are not organizer acceptance.

## Future research shortlist (unrun)

Four ranked fault-zone-anatomy hypotheses, named non-fault mimics, mechanism evidence, data needs,
and controls are documented in [`docs/research/hypotheses.md`](docs/research/hypotheses.md). The
ranking is a future test priority, not a projected DTI gain. Do not implement or evaluate them
without renewed authorization and budget.

## Source of truth

- [`README.md`](README.md): status-first brief and preserved task prompt.
- [`BRIEF.md`](BRIEF.md): standing protocol and current HOLD notice.
- [`evidence/run_card.json`](evidence/run_card.json): current machine-readable audit record.
- [`docs/executive-summary.html`](docs/executive-summary.html): user-facing conditional guide;
  it explicitly says no download or submission is approved.
- [`evidence/history/remaining_work_legacy_2026-10-09.md`](evidence/history/remaining_work_legacy_2026-10-09.md): prior planning notes retained for provenance only; not current instructions.
