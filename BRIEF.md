# Standing brief — start here, then read the complete README request

Read [README.md](README.md) and [TASK_PROMPT.md](TASK_PROMPT.md) at the start of **every** session. The historical request is preserved for requirements and context, not word-for-word certified chat fidelity or score verification.

## Latest preflight (2026-10-10; supersedes the data-access paragraph below)

STOP before production placement: `scripts/preflight_anatomy.py` checked the pinned 17GEMSDOE witness against public main, validated SHA/grid, and proved all 5,106,385 allowed cells covered under the unchanged finite-positive-dot rule. See `evidence/preflight_anatomy.json` and `evidence/run_card_preflight.json`. No new TIFF, holdout or slot in that lane; the retained Session-5 file keeps research download NO and submit NO. `scripts/prepare_data.py --fetch` also restored the 19-band bridge stack via the permitted GitHub API (eight pins verified; third-party bridge, not independently authenticated official-origin data). Older Session-6 references to an unavailable feature TIFF describe that session only.
## Current outcome, 2026-10-10 (Session 7 — read first)

The Session-5 artifact's status is unchanged from main (PR #23): **research download NO, submit NO**. The Session-7 dotted emission has its own explicit status on the README top card: **research download OK (scoped, IR-S7A-03), competition submission NO**. Session 7 restored and hash-verified the feature stack, reproduced the Session-5 holdout (0 numeric differences), and found that the holdout collar makes near-trace dots unobservable (IR-S7-04). The uniqueness gate is still blocked by a dense prior (IR-S7-01), which needs an owner ruling. See [README Session 7](README.md) and [REMAINING_WORK.md](REMAINING_WORK.md).

## Current outcome, 2026-10-10 (Session-6 follow-up)

**Session-5 artifact: research download NO pending explicit owner authorization (IR-S6-10); competition submission NO.** It remains in the repository for audit only; the README and site provide no link for it. The current [run card](evidence/run_card_current.json) describes the Session-7 artifact and is negative: it records `okay_to_submit=false` with `okay_to_download=true` scoped to research download only (`download_permission_status.scope = "research download only"`).

Session 6 (2026-10-10) re-verified the current 696-raster index (696/696, 0 errors) and reran the literal gate on the retained Session-5 TIFF: 80 duplicate firings, unique=false. The universal-support witness blocks every nonempty candidate under the unchanged rule. No slot was used; this follow-up ran no model/holdout, built no new candidate, and did not reauthorize access (see README, Session 6). All **695** accessible pinned grid rasters across all 57 sibling repositories were checked (`evidence/relay_bend_surface_uniqueness.json`). Against all **665 rasters from the other 56 repositories**, worst full-footprint Spearman rank correlation is **0.658029 ≤ 0.90** (and against the **15 discriminating sibling-lane rasters**, worst Spearman is **0.028783 ≤ 0.90** and worst 3-px dot overlap is **0.237470 ≤ 0.70**). However, literal forward overlap against the 17 dense-support prior rasters is **1.0** (above 0.70), and full-footprint Spearman against this repository's own earlier Session-3 soft surface (sharing the exact 2,452,550 zeroed pixels outside the fitted `d1 ≤ 25.55 px` damage zone) is **0.975291**. A dense-prior saturation certificate proves every nonempty allowed support is blocked under the inherited `finite > 0` definition. No density or reverse-overlap exemption, no production final dots, no weekly slot.

On the repaired buffered whole-component holdout (`gems57-pooled-hide-v2`, `n=11,321` withheld positive pixels, `153` physical 20 km spatial clusters), Session 5 executed the three predeclared hypotheses from `REMAINING_WORK.md` §3 (`H57-H` multi-scale host-bend damage asymmetry & detrended-elevation scarp strike, `H57-I2` two-host damage-zone superposition & en echelon relay stepover mechanics via exact 12-bitplane EDT to the second nearest distinct visible component `C2 != C1`, and `H57-J` slip-sense transition heterogeneity):
- **E2 (`relay_bend_anatomy`, H57-I2 + H57-H)** achieves binary **HOLDOUT-DTI = 0.135204 [0.119140, 0.153036]**, beating single-host `anatomy` (**0.109647**) by **+0.025556 [95% CI +0.013943, +0.037109]** and `distance_only` (**0.112725**) by **+0.022479 [95% CI +0.007867, +0.038463]**, winning all 4 spatial folds (`NW`, `NE`, `SW`, `SE`). Its soft-surface HOLDOUT-DTI is **0.031160 [0.024691, 0.038109]**, beating single-host `anatomy` by **+0.008284 [95% CI +0.005420, +0.010947]**.
- **E3 (`relay_bend_sense_transition`, H57-J)** achieves binary **HOLDOUT-DTI = 0.141391 [0.124513, 0.161457]** (**+0.006188 [−0.001694, +0.015702]** over E2) and soft-surface HOLDOUT-DTI **0.033898 [0.026890, 0.041928]** (**+0.002738 [+0.000307, +0.005994]** over E2); because the binary paired 95% lower bound (`−0.001694`) slightly straddles zero, **E2 (`relay_bend_anatomy`) is retained** by the predeclared rule.

## Non-negotiable protocol

1. Stay in **fault-zone anatomy**: secondary strands, visible-host distance/length/orientation and recorded sense where justified. No copied prior prediction as a feature, base or output.
2. Surface gate **before production placement**, then final-dot gate: signed full-footprint rank correlation >0.90 **or** >70% candidate support within Euclidean 3 px of any earlier raster → duplicate, log and STOP. Literal positive finite support; no alternate policy.
3. Reuse shared cached features, `evaluate_holdout.py` and `submission_writer.py`. Repair shared tools once; no private scoring forks.
4. Hide whole fault components with a context buffer. All catalogue features visible-only; pixel-exact unhidden known-fault score mask. Pooled α=0.2, β=0.8, 300 m triangular kernel. Fit budgets/zone only on training folds; never oracle test-positive count.
5. Every score must be **HOLDOUT-DTI** with evaluator, positive count and CI, or **ORGANIZER-CONFIRMED** from a submission-page receipt. Historical quoted values stay **OWNER-REPORTED**; public board context is not a file receipt. A projection is not a score.
6. Every feature alone: `max(AUC,1−AUC)>0.90` is leakage until resolved. Passing canaries is not proof of zero leakage.
7. Three experiments or two hours per session. Negative results count. Real slots are a **separate selector step**, never chosen/spent here.
8. End with one JSON run card: hypothesis, mechanism, named mimic, holdout/CI, registry checks, TIFF SHA256, validator, unique filename/note ≤140 characters and promote/negative verdict.
9. Prominent, unmistakable download/submission permission on the overview and executive summary. Publish a real TIFF/ZIP link only when download authorization and all applicable gates are explicitly clear; otherwise state NO/HOLD, keep the file link-free, and distinguish repository availability from permission. Never upload a webpage or JSON receipt.
10. Three implementation/review passes, auditable source/irregularity tables, clean Pages site, PR then merge, and next-session limitations. Work autonomously; never ask for passwords/tokens.

**Maximize P(Win):** demand paired evidence and preserve scarce slots. **Own the Outcome:** fix tools, restore data, publish failures and keep status truthful.

## Closed previous blockers

- Session 5 restored five feature parts and verified eight hashes for the 19-band stack; Session 6 reports `training_features.tif` absent in the current checkout and the linked copy unreachable. Do not treat the historical assembly receipt as current input availability. CPU lane; no GPU requirement.
- Shared evaluator API, missing `fn`, host-strike fallback, empty-visible behavior and trace/sense indexing corrected.
- Missing `/tmp` registry caches replaced with ignored immutable workspace caches; missing/incomplete manifests fail closed.
- Unsafe in-sample/oracle-budget builder and unauthorized `>=0.5` / universal-probe uniqueness helpers retired.
- Portal NaN explanation downgraded to an unproven hypothesis; conservative finite export remains.

See [REMAINING_WORK.md](REMAINING_WORK.md), not old “SHIPPED/UNIQUE” archived claims, for the next budgeted session.
