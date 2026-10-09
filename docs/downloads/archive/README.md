# Archived artifacts — DO NOT SUBMIT

Every file in this directory is superseded. They are kept for provenance only.

The **only** submittable file in this repository is the single `-zeros.tif` one
directory up:

`docs/downloads/gems57-h57-anatomy-enechelon-20261009T070415Z-e9d8d59a4357-zeros.tif`

## Why these were retired

| File | Reason it is not submittable |
| --- | --- |
| `57GEMSDOE-faultzone-anatomy-12000dots-nan.tif` | Carries `NaN` outside the footprint. The portal rejects it with *"Predicted values must be in range [0, 1]"* because `NaN` satisfies neither `v >= 0` nor `v <= 1`. `IR-57-NAN-01`. |
| `57GEMSDOE-faultzone-anatomy-12000dots-zeros.tif` | Superseded by a later build. 12,000 dots is well below the budget the registry's live evidence supports. |
| `gems57-faultzone-anatomy-60000px-*.tif` | Superseded. 60,000 dots sits in the band where **Spearman(dot count, live score) = -0.8104** says scores fall off; the shipped build is capped at 40,000. `IR-57-BUDGET-01`. |
| `*-nan.zip`, `*.zip` | Zipped variants of the above. |
| `run_card.json` | An earlier lane's run card. The current one is [`evidence/run_card.json`](../../../evidence/run_card.json). |
| `*-audit.json`, `*.receipt.json` | Receipts for the builds above. |

None of these were submitted to the competition. No submission slot was spent on
any of them.
