# Data and cache provenance — read before interpreting scores

**Data placement is complete in this workspace.** `evidence/data_preparation.json`
records verification of all eight pins. The large feature raster and derived caches
are ignored by Git and must be restored after a fresh checkout.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
PYTHON=.venv/bin/python bash scripts/download_competition_data.sh --cache-bands
.venv/bin/python scripts/prepare_data.py
```

The downloader uses **api.github.com**, not a disallowed raw host. It downloads five
immutable, separately SHA256-checked parts, assembles the feature stack atomically,
checks the final hash, and caches its **19 actual bands**. No GPU is needed for this lane.

## What is and is not authenticated

These files match the [public bridge manifest at its pinned commit](https://github.com/buffedlizard55-lab/6GEMSDOE/blob/e2fe3f41c6f5dd2dcb2fc91958ee67698f114ada/data/bridge/manifest.json).
That proves **bridge-byte identity**, not independent official-origin authentication.
The directory name `official/` is retained for compatibility, not evidence of provenance.
The [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
was checked and redirected to login. No authenticated DrivenData session or organizer
data/submission receipt is available.

The organizer describes its sample as predicting total fault absence; the bridge's
`example_submission.tif` contains both 0 and 1. Do **not** claim that these are independently
verified identical official samples. We use its **header and finite footprint**, not its
prediction values. Grid agreement is verified against the bridged feature stack;
EPSG:32611 and 100 m resolution also match the public specification.

## Pinned bytes

| Local file | Bytes | SHA256 |
|---|---:|---|
| `official/labels.tif` | 425830 | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` |
| `official/existing_faults.tif` | 425830 | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` |
| `official/sample_submission.tif` | 1599597 | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` |
| `official/training_features.tif` | 418912844 | `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` |
| `external/sgmc_faults_100m.tif` | 213034 | `26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c` |
| `external/derived_sgmc_faults_100m.tif` | 198602 | `643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0` |
| `external/trace_segments_utm11.csv` | 5283577 | `c5edf9df3e0e1413c52784884fc38e5b9ca54627b27c6f8baf7713e908f48513` |
| `external/qfault_attributes.csv` | 5786456 | `3b8745f0086a57b8255f6679afa1bf1168c10b5573491666c75cf53217029507` |

`labels.tif` and `existing_faults.tif` are byte-identical **in the bridge**. The exact
known-pixel mask is taken from that raster; it is not dilated for evaluation. The official
staff response says the mask equals the supplied training labels, not a 300 m known-fault halo.

## Current model inputs and exclusions

- Cached band 14, short name `tmi`: Gaussian derivatives provide a catalogue-independent
  candidate edge tangent and coherence. No prediction raster is a feature.
- Visible catalogue geometry: distance, cross-/along-strike offsets, axial host strike,
  coherence, density and log connected-component pixel count (a noisy length proxy).
- Matched INGENIOUS sense: tested as an ablation, masked to visible context only.
- **SGMC rasters are not used** in the current model, fitting, dot budget or validation.
- Embedded feature descriptions are preserved as metadata, **not blindly trusted semantics**.
  In particular `tc` was described as tilt/curvature in the bridge, and conductive-base depth
  was called basement depth. Neither disputed band is used in this candidate.

## Free official sources and licenses

- [GeoDAWN USGS release, DOI 10.5066/P93LGLVQ](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and): metadata retrieved, marked CC0 1.0.
- [INGENIOUS GDR compilation, DOI 10.15121/1881483](https://gdr.openei.org/submissions/1391): metadata retrieved, publicly linked Quaternary Faults v2, CC BY 4.0 with attribution.
- [Official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf): verify entrant eligibility, third-party licensing, AI-use disclosure and reproducibility requirements before submission.

Binary downloads from these official hosts are outside the sandbox's egress allowlist.
The bridge is an obtainable transport, not a substitute for a provenance receipt. No private
labels, geothermal temperatures, flow rates or hidden-test data are available here.
