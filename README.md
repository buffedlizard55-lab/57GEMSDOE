# 57GEMSDOE — fault-zone-anatomy lane for the DOE GEMS Prize Challenge

**Competition:** [DOE GEMS Prize (DrivenData #306)](https://www.drivendata.org/competitions/306/competition-doe-gems/)
· **Problem description:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
· **About / resources:** [page 968](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
· **Rules (PDF):** [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
· **Reference solution:** [github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
· **Site:** <https://buffedlizard55-lab.github.io/57GEMSDOE/>

---

## ⬇ ONE-CLICK SUBMISSION FILE

**The file to submit is the `-zeros.tif` variant in [`docs/downloads/`](docs/downloads/).**
It is portal-legal by construction: single band, `float32`, `EPSG:32611`,
`3730 × 3292`, transform `(100, 0, 243350, 0, -100, 4508550)`, every one of the
12,279,160 cells finite and in `[0, 1]`, zero dots on the mapped catalogue.

> **Do not submit the `-nan.tif` variant.** It is a diagnostic. It carries
> 7,111,787 `NaN` cells outside the study-area footprint and the portal rejects
> it with *"Predicted values must be in range [0, 1]"*, because `NaN` satisfies
> neither `v >= 0` nor `v <= 1`. See [the executive summary](docs/executive-summary.html)
> and irregularity `IR-57-NAN-01`.

The exact filename, sha256, check receipt and the suggested submission note are
printed at the top of [`docs/index.html`](docs/index.html) and in
[`evidence/submission_build_all.json`](evidence/submission_build_all.json).

---

## Core values (kept central to every decision in this repository)

> **Maximize P(Win).** *"Maximize the Probability of Winning"* is our
> decision-making framework. In every decision we weigh tradeoffs, assess risk,
> and choose the path that maximizes the probability that we win this prize. We
> set aside our emotions and make tough decisions in order to maximize P(Win).
> It frees us from constraints and clarifies that we must put the outcome first.
>
> **Own the Outcome.** We own results end to end — not just our individual slice
> of the work. When problems arise and we have the means to act, we act without
> waiting for permission or assignment. We treat failure and success as signals
> and use them to improve. We stay accountable to the final outcome.

Applied here: *Maximize P(Win)* is why the lane's dot budget and its flank
exclusion are **chosen by holdout measurement** rather than by hand, and why no
submission slot is spent on an idea that has not beaten the holdout bar.
*Own the Outcome* is why three bugs found in this session's own code — including
one inherited from the shared template's prose — are recorded in
[`docs/irregularities.html`](docs/irregularities.html) instead of being quietly
patched.

---

## Standing brief (re-read at the start of every session)

The full task prompt is preserved verbatim in [`BRIEF.md`](BRIEF.md). Its
operative constraints for this lane:

1. **Lane.** Fault-zone anatomy — predict where secondary strands sit around
   known faults from shear-zone mechanics. Stay inside it. If the raster's
   rank-correlation with any registry raster exceeds **0.90**, or more than
   **70 %** of its dots fall within 3 px of one registry raster's dots, log it as
   a duplicate and stop.
2. **Reuse, don't rebuild.** Hide-and-recover holdout; withhold whole fault
   segments with a buffer; derive every catalogue feature only from the visible
   faults; mask visible faults pixel-exactly; score pooled DTI (α = 0.2,
   β = 0.8, 300 m triangular kernel).
3. **Label every number** `HOLDOUT-DTI` (evaluator version, number of withheld
   positives, 95 % CI) or `ORGANIZER-CONFIRMED` (copied from a submission-page
   receipt). **A projection is never written as a score.**
4. **Leakage canary.** Test each feature alone before trusting any result.
   AUC above **0.90** means leakage until proven otherwise.
5. **Run card.** End with one JSON card (see [`docs/run-card.html`](docs/run-card.html)).
6. **Budget.** Stop after **3** experiments or **2** hours. Negative results are
   deliverables.

---

## What this repo actually contains

| Path | What it is |
| --- | --- |
| [`BRIEF.md`](BRIEF.md) | the standing task prompt, verbatim |
| [`src/gems57/metric.py`](src/gems57/metric.py) | DTI, verified against a brute-force transcription |
| [`src/gems57/grid.py`](src/gems57/grid.py) | CRS / shape / transform / footprint, sha256-pinned |
| [`src/gems57/network.py`](src/gems57/network.py) | fault segments, local strike, offset frame, detachment |
| [`src/gems57/holdout.py`](src/gems57/holdout.py) | hide-and-recover folds, pooled DTI |
| [`src/gems57/anatomy.py`](src/gems57/anatomy.py) | the **fitted** fault-zone-anatomy intensity |
| [`src/gems57/emit.py`](src/gems57/emit.py) | lazy-greedy max-coverage allocation at the DTI fixed point |
| [`src/gems57/fitting.py`](src/gems57/fitting.py) | leakage canary + leave-one-quadrant-out CV |
| [`src/gems57/validate.py`](src/gems57/validate.py) | every portal check |
| [`src/gems57/uniqueness.py`](src/gems57/uniqueness.py) | rank-correlation and 3 px dot overlap vs the registry |
| [`scripts/run_lane.py`](scripts/run_lane.py) | `verify` / `measure` stages |
| [`scripts/run_cv.py`](scripts/run_cv.py) | canary + CV + ablation |
| [`scripts/build_submission.py`](scripts/build_submission.py) | final surface, emission, validation, uniqueness |
| [`scripts/build_site.py`](scripts/build_site.py) | regenerates `docs/` from the evidence JSONs |
| [`evidence/`](evidence/) | every measurement, machine-readable |
| [`registry/`](registry/) | 15 earlier submission rasters, provenance-indexed |
| [`data/bridge/`](data/bridge/) | the two competition files, sha256-verified |

## Reproduce

```bash
pip install -r requirements.txt
python scripts/run_lane.py verify            # re-verify the two data files by sha256
python scripts/run_lane.py measure           # withhold structure measurement
python scripts/run_cv.py  --mode all         # leakage canary + LOQO CV + ablation
python scripts/build_submission.py --mode all
python scripts/build_site.py
pytest -q
```

## Verified data provenance

| File | sha256 | Source |
| --- | --- | --- |
| `existing_faults.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | [GEMSDOE2 `data/bridge/`](https://github.com/buffedlizard55-lab/GEMSDOE2/blob/main/data/bridge/existing_faults.tif) |
| `sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | [GEMSDOE2 `data/bridge/`](https://github.com/buffedlizard55-lab/GEMSDOE2/blob/main/data/bridge/example_submission.tif) |

`existing_faults.tif` is byte-identical to the `labels.tif` recorded in
[`GEMSDOE32/data/restore_receipt.json`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/data/restore_receipt.json)
(same sha256, same 425,830 bytes) — the public "labels" raster **is** the mapped
fault catalogue, and the scored truth is not published. That is what forces the
hide-and-recover design.

## Limitations

* **No DrivenData credentials in the sandbox.** The 420 MB
  `gems-geodawn-numerical-features.tif` feature stack is present in the bridge
  repos as five parts but is not pulled here; this lane is catalogue-geometry
  only and does not need it.
* **No sense-of-slip field exists.** `existing_faults.tif` has exactly three
  values, `{-1, 0, 1}`. The lane brief asks to condition on recorded sense of
  slip "where the database has it" — it does not. `IR-57-SLIP-01`.
* **No external SGMC-derived fault raster**, so the secondary off-catalogue
  instrument used by the shared template cannot be reproduced here.
* **The holdout truth is withheld *catalogue* pixels**, which by construction
  belong to mapped systems. Genuinely unmapped faults are a different
  population. The `detached` withholding mode is the conservative reading and is
  reported alongside the primary one.
