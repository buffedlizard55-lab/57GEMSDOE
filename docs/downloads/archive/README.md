# Archived artifacts — DO NOT SUBMIT

Every file in this directory is an older/superseded research artifact kept for provenance and
included in the finite local uniqueness audit. None is currently cleared for competition
submission.

The current downloadable H57 research artifact is one directory up:

`docs/downloads/gems57-h57-anatomy-enechelon-20261009T070415Z-e9d8d59a4357-zeros.tif`

It passes local GeoTIFF format checks but is **not cleared for upload**. See
[`evidence/run_card.json`](../../../evidence/run_card.json) for the negative verdict and blockers.

## Why these were retired

| File | Reason it is not submittable |
| --- | --- |
| `57GEMSDOE-faultzone-anatomy-12000dots-nan.tif` | Carries `NaN` outside the footprint. The portal rejects it with *"Predicted values must be in range [0, 1]"* because `NaN` satisfies neither `v >= 0` nor `v <= 1`. `IR-57-NAN-01`. |
| `57GEMSDOE-faultzone-anatomy-12000dots-zeros.tif` | Superseded by a later build. 12,000 dots is well below the budget the registry's live evidence supports. |
| `gems57-faultzone-anatomy-60000px-*.tif` | Superseded by the 35,341-dot candidate. Earlier live-score/budget analysis is owner-reported and lacks submission receipts here; do not treat it as organizer-confirmed. `IR-57-BUDGET-01`. |
| `*-nan.zip`, `*.zip` | Zipped variants of the above. |
| `run_card.json` | An earlier lane's run card. The current one is [`evidence/run_card.json`](../../../evidence/run_card.json). |
| `*-audit.json`, `*.receipt.json` | Receipts for the builds above. |

No submission-page receipt for any archived artifact is present in this checkout. Do not infer
competition upload history from these local files.
