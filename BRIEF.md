# Standing brief — start here, then read the complete README request

Read [README.md](README.md) and [TASK_PROMPT.md](TASK_PROMPT.md) at the start of **every** session. The historical request is preserved for requirements and context, not word-for-word certified chat fidelity or score verification.

## Current outcome, 2026-10-10 (Session 7 / H58 fault-zone anatomy)

**New TIFF generated from scratch (`docs/downloads/gems57-h58-damagezone-envelope-21748dots-20261010T221137Z-673354bceb7d-zeros.tif`, 87,169 bytes, 21,748 binary dots). Download for research: OK. Submit to competition: NO. Zero weekly slots used.**

The [run card](evidence/run_card_current.json) is **negative**: the inherited literal drift gate trips on the 3-px overlap clause (worst overlap 1.0 against **45** priors whose support already covers all 5,106,385 allowed cells; 95 triggered comparisons of 695), even though the release is byte- and pixel-distinct from every audited raster and its worst full-footprint Spearman is **0.2172**. Both required phases were audited — the fitted surface *before* placement and the final dots — and STOP was honoured. Owner ruling on how soft rasters define a "dot" is still open (IR-S6-01).

Three predeclared experiments, all completed:
- **E1 structure:** fitted damage-zone law `W(L) = w0·(L/40 px)^γ` gives **γ = 0.1544 [0.0732, 0.2882]** over 6 length bins and 11,360 withheld positives — strongly sub-linear, and the interval also excludes √L. Withheld positives sit at median **13.64°** oblique to their nearest visible host against a **6.39°** visible-reference null. **Signed (handed) radial obliquity and its sense interaction produced no enriched bin (max 0.0065 vs base 0.00235; L/R log-ratio +0.096 / −0.153) — recorded as a negative result, so no Riedel handedness is claimed.**
- **E2 holdout (four buffered whole-component quadrants, evaluator `gems57-pooled-hide-v2`):** candidate `anatomy10_sense_obliq` beats reference `anatomy10` by only **+0.00171 [−0.00367, +0.00780]** → dropped by the predeclared rule; shipped arm `anatomy10__flank2` binary **HOLDOUT-DTI 0.09456 [0.07990, 0.11072]**, soft **0.01675 [0.01423, 0.01942]**. The `distance_only` control scored **0.11004 [0.09600, 0.12287]** binary, i.e. better than every anatomy arm on this draw while being far worse on the soft surface. Canary clean: 14 features, max discriminative AUC 0.7614, no flags. `flank0` and `flank2` are identical for all arms (Δ = 0) because the collar already emptied the near-flank bins — the flank policy is therefore justified by thread 11516 and by the registry measurement, never by this CI.
- **E3 build:** budget = `4 × 10,000 × 0.5437` (fitted fraction of withheld positives inside the kept distance × strike zone) = **21,748 dots**, support = footprint ∧ ¬catalogue ∧ d > 2 px ∧ d ≤ W(L); 15/15 local format checks, no NaN anywhere, values {0,1}, zero positive mass on the catalogue. The mismatch between the holdout arm budget (29,889 pooled) and the shipped cap is disclosed in the card and in the README, not smoothed over.

Also measured from bytes this session ([evidence/live_submission_patterns.json](evidence/live_submission_patterns.json)): across 15 owner-reported registry entries, ρ(dots, reported score) = **−0.8104** (p = 0.00025) and ρ(median dot-to-catalogue distance, score) = **+0.7663**; the 0.2778 file is the 0.2708 file minus exactly 2,545 dots all ≤ 2.00 px from the catalogue, with every kept dot ≥ 2.236 px away (`equals_base_pruned_at_2px: true`). Confounded by construction, so it informs the support shape and is not a causal estimate.

**Merge state:** PR #36 (this branch) is open and CONFLICTING against a concurrently merged Session-7 H57-M release; both cards are negative and neither spent a slot. Resolution procedure: IR-58-07. Do not force-merge either card.

## Prior outcome, 2026-10-10 (Session 5, superseded as the current release)

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
