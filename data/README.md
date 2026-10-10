# Data manifest — pinned bridge files and external sources

Present files and provenance receipts are SHA256-pinned. The competition feature
raster is not present in this checkout. `scripts/prepare_data.py` verifies
available pins when invoked; this audit did not download or prepare data.

## Competition-grid bridge files (`data/official/` and `data/bridge/`)

| File | Bytes | sha256 | Source |
|---|---|---|---|
| `labels.tif` | 425,830 | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | DrivenData competition 306 training labels (GeoDAWN region) |
| `existing_faults.tif` | 425,830 | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | same raster as labels (USGS QFaults catalogue, rasterized) |
| `sample_submission.tif` | 1,599,597 | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | DrivenData sample submission (defines grid, CRS, bounds) |
| `training_features.tif` | 418,912,844 | `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` | Expected training-feature raster from the pinned bridge — **not committed** (gitignored); see below |

Provenance limits and notes:

- The checked-in copies `data/official/labels.tif` and `data/official/existing_faults.tif`
  are byte-identical to one another and to the pinned bridge raster. This establishes
  byte identity within the bridge, **not independent authentication that the bridge is
  identical to a fresh official DrivenData download**.
- The DrivenData data tab was observed behind login; no authenticated download or organizer
  data receipt was available for this audit. The external Dropbox route was not used. The
  public sibling-repository manifest supplies transport hashes, not an organizer attestation.
- `training_features.tif` is gitignored (about 419 MB) and is absent from this checkout.
  The listed size/hash describe the expected bridge file only. The older
  `evidence/data_preparation.json` and `evidence/feature_cache.json` receipts record a prior
  verified 19-band bridge file, but are not dated and do not establish current availability.
  `scripts/prepare_data.py` can verify it if it is placed locally; this audit did not fetch it.
- The GeoDAWN USGS/DOE catalogue record and its public license were checked for future
  geophysical validation; exact coverage, CRS/grid overlap, and usable file contents were
  **not** verified. No GeoDAWN raster was downloaded or used. See
  [`docs/research/hypotheses.md`](../docs/research/hypotheses.md).

## External sources (`data/external/`)

| File | Bytes | sha256 | Source |
|---|---|---|---|
| `sgmc_faults_100m.tif` | 213,034 | `26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c` | SGMC — State Geologic Map Compilation, Nevada Bureau of Mines and Geology (nbmg.unr.edu), 100 m rasterization |
| `derived_sgmc_faults_100m.tif` | 198,602 | `643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0` | derived: SGMC minus USGS∪INGENIOUS footprint (the off-catalogue proxy truth, 79,025 px) |
| `trace_segments_utm11.csv` | 5,283,577 | `c5edf9df3e0e1413c52784884fc38e5b9ca54627b27c6f8baf7713e908f48513` | INGENIOUS qfaults shapefile exported to CSV, UTM 11N (NAD83 CONUS Albers source, reprojected) |
| `qfault_attributes.csv` | 5,786,456 | `3b8745f0086a57b8255f6679afa1bf1168c10b5573491666c75cf53217029507` | INGENIOUS qfaults attribute table (sense of slip, slip rate) |
| `qfaults_8_README_fielddefinitions_...txt` | 3,864 | — | INGENIOUS field definitions (shipped with the source) |
| `qfaults_receipt.json` | 3,422 | — | source receipts: qfaults zip sha256 `c7b091c9ac8bca140ad89ee6bb2bd63dd3ac12e3013acbfd8373d11c9faee59d` (6,131,182 B, 22,956 records); geodetics zip sha256 `0dd65ccc…` (54,515,392 B) |

SGMC rasters are retained as an off-catalogue proxy layer from earlier work. Their prior
use in calibration is historical and is not current-code validation, an organizer score, or
clearance to build/submit a candidate. No new SGMC analysis was run in this audit.
