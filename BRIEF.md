# Standing brief — start here, then read the complete README request

Read [README.md](README.md) and [TASK_PROMPT.md](TASK_PROMPT.md) at the start of **every** session. The historical request is preserved for requirements and context, not word-for-word certified chat fidelity or score verification.

## Current outcome, 2026-10-10 (Session 7 — read first)

Status unchanged: **Download for research: OK. Submit: NO.** Session 7 restored and hash-verified the feature stack, reproduced the Session-5 holdout (0 numeric differences), and found that the holdout collar makes near-trace dots unobservable (IR-S7-04). The uniqueness gate is still blocked by a dense prior (IR-S7-01), which needs an owner ruling. See [README Session 7](README.md) and [REMAINING_WORK.md](REMAINING_WORK.md).

## Previous outcome, 2026-10-10 (Session 5)

**New TIFF generated (`gems57-twohost-relay-bend-surface-20261010T201504Z-47ccc38b6bec.tif`). Download for research: OK. Submit: NO.**

The current [run card](evidence/run_card_current.json) is negative for competition submission. Session 6 (2026-10-10) re-verified the current 696-raster index (696/696, 0 errors) and reran the literal gate on the offered TIF: 80 duplicate firings, unique=false. No slot was used and no candidate was built (see README, Session 6). All **695** accessible pinned grid rasters across all 57 sibling repositories were checked (`evidence/relay_bend_surface_uniqueness.json`). Against all **665 rasters from the other 56 repositories**, worst full-footprint Spearman rank correlation is **0.658029 ≤ 0.90** (and against the **15 discriminating sibling-lane rasters**, worst Spearman is **0.028783 ≤ 0.90** and worst 3-px dot overlap is **0.237470 ≤ 0.70**). However, literal forward overlap against the 17 dense-support prior rasters is **1.0** (above 0.70), and full-footprint Spearman against this repository's own earlier Session-3 soft surface (sharing the exact 2,452,550 zeroed pixels outside the fitted `d1 ≤ 25.55 px` damage zone) is **0.975291**. A dense-prior saturation certificate proves every nonempty allowed support is blocked under the inherited `finite > 0` definition. No density or reverse-overlap exemption, no production final dots, no weekly slot.

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
9. Prominent real TIFF/ZIP download and explicit download/submission permission on the overview and executive summary. Never upload a webpage or JSON receipt.
10. Three implementation/review passes, auditable source/irregularity tables, clean Pages site, PR then merge, and next-session limitations. Work autonomously; never ask for passwords/tokens.

**Maximize P(Win):** demand paired evidence and preserve scarce slots. **Own the Outcome:** fix tools, restore data, publish failures and keep status truthful.

## Closed previous blockers

- Five feature parts restored, eight hashes verified, actual 19-band cache ready. CPU lane; no GPU requirement.
- Shared evaluator API, missing `fn`, host-strike fallback, empty-visible behavior and trace/sense indexing corrected.
- Missing `/tmp` registry caches replaced with ignored immutable workspace caches; missing/incomplete manifests fail closed.
- Unsafe in-sample/oracle-budget builder and unauthorized `>=0.5` / universal-probe uniqueness helpers retired.
- Portal NaN explanation downgraded to an unproven hypothesis; conservative finite export remains.

See [REMAINING_WORK.md](REMAINING_WORK.md), not old “SHIPPED/UNIQUE” archived claims, for the next budgeted session.
