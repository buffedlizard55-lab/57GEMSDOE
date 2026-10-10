# Session 4 — three-pass review log

Review date: 2026-10-10. Scope is the fault-zone-anatomy lane only. This review refers to the **visible-network junction-distance** H57-K run; it is distinct from the mainline H57-K strand-expression artifact. The junction run produced no TIFF; the separate archived mainline TIFF is also not cleared for download or submission.

## Pass 1 — geology, protocol, and score provenance

- Rechecked the prospective hypotheses and H57-K mechanism against the implementation: junction distance is computed from each fold's visible-only fault mask; whole-segment detached holdout, visible-only features, exact visible-fault masking, shared evaluator, α=0.2, β=0.8, and 300 m triangular kernel are recorded.
- Reconciled the score claims against the inspected owner evidence: H33-2-B2 is marked UNSCORED; 0.2747 is a projection; 0.2778 is an unverified owner-reported claim, not a confirmed score-to-file mapping; the 0.2708 attribution is contradicted. Those disputed assignments were excluded from the 13-entry descriptive owner-value relation (Spearman −0.7686, p=0.00214).
- Confirmed the local metrics are labeled HOLDOUT-DTI / PROXY-DTI and are not described as organizer scores or projections.

## Pass 2 — registry gate and artifact safety

- Re-read `evidence/exp5_junction.json` and the dedicated `evidence/run_card_session4_junction.json`. H57-K HOLDOUT-DTI is 0.242353 (95% quadrant-jackknife CI 0.205591–0.279115), versus H57-G 0.237423; paired gain +0.004930 (95% CI 0.001497–0.008364). These are local holdout measurements.
- Verified both SHA-pinned witnesses match the refreshed index. Maximum surface Spearman is 0.558503 (<0.90), but candidate-positive support within 3 px is 0.998724 and 1.000000 (>0.70). Placement stopped before dots; no H57-K TIFF, final-dot check, file hash, validator result, safe download, or submission exists.
- Separately completed the full scan of the archived 35,341-dot H57-G raster: 667 grid rasters, 56 repositories, all reachable/cached; 114 directed-overlap firings, verdict not cleared. This does not constitute a scan or clearance for H57-K.

## Pass 3 — code, generated pages, and test suite

- `python -m py_compile scripts/build_site.py scripts/experiment_junction.py scripts/calibrate_registry.py src/gems57/anatomy.py` passed; `git diff --check` passed.
- Rebuilt the ten generated site pages successfully. Checked the front page, Session 4 page, run card, results, data-source table, and irregularity ledger for the no-safe-download status and score/projection labels.
- Full test suite: **43 passed, 1 skipped**. Final targeted rerun of Session 3 gate tests, H57-K feature tests, and shared-evaluator tests: **7 passed**.

## Review verdict

The holdout improvement is a research result, not a competition score. The required literal overlap gate fails. No candidate was promoted, no slot was used, and no TIFF is cleared for download or submission.
