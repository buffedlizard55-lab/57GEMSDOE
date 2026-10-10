# Archived artifacts — **DO NOT DOWNLOAD OR SUBMIT**

Every GeoTIFF in this directory is retained only for provenance. The newer
historical `-zeros.tif` file one directory up is also **not cleared** and must
not be downloaded or submitted.

No file in `docs/downloads/` is an approved submission. The retained candidate
failed the literal full-registry overlap gate; see `evidence/run_card.json` and
`evidence/uniqueness_full_shipped-h57-zeros.json`. A local format pass is not
uniqueness clearance, organizer acceptance, or a weekly-slot decision.

Earlier documentation speculated that `NaN` caused a portal range error. The
actual cause remains unproven (`IR-57-NAN-02`). The current writer is
fail-closed: it requires already finite `[0,1]` values, rejects mass outside the
footprint, never clips/fills predictions, and validates the on-disk GeoTIFF and
single-TIFF ZIP before committing outputs.

No item in this archive was submitted in this session. No weekly submission
slot was spent.
