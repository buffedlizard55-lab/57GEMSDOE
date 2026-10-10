# Archived artifacts — historical only, DO NOT SUBMIT

**There is no currently cleared submission artifact in this repository.** H57-B is on HOLD; no
new H57-B raster was generated, no current file-format validation was run, and nothing is cleared
to download or submit. No weekly slot was selected.

The older H57-A file,
`docs/downloads/archive/gems57-h57-anatomy-enechelon-20261009T070415Z-e9d8d59a4357-zeros.tif`, is also
**HOLD and not cleared**. Its old format receipt applies only to that historical file; its prior
644-raster uniqueness scan is stale against the refreshed registry. The 40,000-dot H57-R2 file
`gems57-h57r2-shipped8-all-flank0-20261009T180433Z-90e532947353-zeros.tif` is likewise archive-only:
its measured same-lane forward overlap of 0.711325 exceeds the literal 0.70 limit. No same-lane or
reverse-overlap exemption applies. The current project status and single H57-B run card are at
[`docs/index.html`](../../index.html) and [`evidence/run_card.json`](../../../evidence/run_card.json).

## Session-5 H57-J relay-bend surface — NOT CLEARED

`gems57-twohost-relay-bend-surface-20261010T201504Z-47ccc38b6bec.tif` and its single-TIFF ZIP are archived for audit only. The TIFF is a new pre-placement research surface (not copied from a prior submission) and its historical local format checks passed; that is not permission to download or submit. The source-main uniqueness receipt checked 695 indexed rasters and reported `unique: false`, 81 threshold-triggered comparisons, worst full-footprint Spearman **0.975315** (>0.90), and worst candidate-forward 3 px overlap **1.0** (>0.70). No reverse-overlap or Jaccard exemption applies. No final dots, submission, or weekly-slot selection were made.

The upstream mainline H57-J card had `okay_to_download: true` despite the failed uniqueness receipt. That inconsistent clearance claim is withdrawn in `evidence/history/run_card_session5_relay_bend_held.json` and the archived sidecar receipt; both now explicitly say **NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT**. H57-B's protected `evidence/run_card.json` remains unchanged. The original source commit remains in Git history as provenance; the current site does not link to the TIFF or ZIP.

Files in this archive are retained for provenance only. Their old validation receipts do not
clear any other artifact. The previous explanation that NaN alone caused a portal rejection was
not established; see `IR-57-NAN-02` on the current irregularities page.
