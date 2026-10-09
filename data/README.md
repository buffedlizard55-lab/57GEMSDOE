# Data manifest — official competition data and external sources

Everything here is free, publicly available, and sha256-pinned. `scripts/prepare_data.py`
verifies every pin before any script runs. The one file that cannot be fetched from this
sandbox is listed with its verified pin and its bridge source.

## Official competition data (`data/official/`)

| File | Bytes | sha256 | Source |
|---|---|---|---|
| `labels.tif` | 425,830 | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | DrivenData competition 306 training labels (GeoDAWN region) |
| `existing_faults.tif` | 425,830 | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | same raster as labels (USGS QFaults catalogue, rasterized) |
| `sample_submission.tif` | 1,599,597 | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | DrivenData sample submission (defines grid, CRS, bounds) |
| `training_features.tif` | 418,912,844 | `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` | DrivenData training features — **19 bands** (verified with rasterio on the pinned bytes; earlier prose here claimed 105, corrected 2026-10-09). **not committed** (gitignored); see below |

Notes:

- `labels.tif` and `existing_faults.tif` are byte-identical (same sha256): the catalogue
  raster and the label raster are the same file in the official package.
- The DrivenData data page sits behind a login and the Dropbox mirrors are unreachable
  from this sandbox, so the official files were obtained **sha256-pinned from the public
  GEMSDOE sibling repositories** (`buffedlizard55-lab/GEMSDOE*`), which carry the official
  files with recorded hashes (6GEMSDOE bridge manifest). This is a provenance bridge, not
  a modification: every byte is verified against the pin above.
- `training_features.tif` is gitignored (419 MB). To place it, run
  `scripts/prepare_data.py` on a machine that can reach the bridge (GitHub) or the
  competition data page; it re-verifies the sha256 after download.

## External sources (`data/external/`)

| File | Bytes | sha256 | Source |
|---|---|---|---|
| `sgmc_faults_100m.tif` | 213,034 | `26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c` | SGMC — State Geologic Map Compilation, Nevada Bureau of Mines and Geology (nbmg.unr.edu), 100 m rasterization |
| `derived_sgmc_faults_100m.tif` | 198,602 | `643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0` | derived: SGMC minus USGS∪INGENIOUS footprint (the off-catalogue proxy truth, 79,025 px) |
| `trace_segments_utm11.csv` | 5,283,577 | `c5edf9df3e0e1413c52784884fc38e5b9ca54627b27c6f8baf7713e908f48513` | INGENIOUS qfaults shapefile exported to CSV, UTM 11N (NAD83 CONUS Albers source, reprojected) |
| `qfault_attributes.csv` | 5,786,456 | `3b8745f0086a57b8255f6679afa1bf1168c10b5573491666c75cf53217029507` | INGENIOUS qfaults attribute table (sense of slip, slip rate) |
| `qfaults_8_README_fielddefinitions_...txt` | 3,864 | — | INGENIOUS field definitions (shipped with the source) |
| `qfaults_receipt.json` | 3,422 | — | source receipts: qfaults zip sha256 `c7b091c9ac8bca140ad89ee6bb2bd63dd3ac12e3013acbfd8373d11c9faee59d` (6,131,182 B, 22,956 records); geodetics zip sha256 `0dd65ccc…` (54,515,392 B) |

SGMC is used **only** as the off-catalogue proxy truth for calibration (PROXY-DTI). It is
never used to build the submission intensity: the lane's intensity is fitted on the
hide-and-recover holdout of the catalogue itself, and the d&lt;3 px near-band extension is
flagged as SGMC-informed in the run card.
