# 57GEMSDOE — fault-zone anatomy, evidence before slots

**[Open the site](https://buffedlizard55-lab.github.io/57GEMSDOE/)** · [Executive summary / submission guide](https://buffedlizard55-lab.github.io/57GEMSDOE/executive-summary.html) · [Competition #306](https://www.drivendata.org/competitions/306/competition-doe-gems/)

## Download at the beginning — and an unmistakable status

### **Download for research: OK. Submit to competition: NO.**

**[↓ Download the new GeoTIFF](https://buffedlizard55-lab.github.io/57GEMSDOE/downloads/gems57-relative-strand-surface-20261009T195324Z-88e3bcb35a95.tif)** · **[Single-TIFF ZIP](https://buffedlizard55-lab.github.io/57GEMSDOE/downloads/gems57-relative-strand-surface-20261009T195324Z-88e3bcb35a95.zip)** · [Complete JSON run card](evidence/run_card_current.json)

This is a newly fitted **soft research surface**, not a copy or modification of a prior submission. Byte/pixel identity is distinct against all 679 audited grid rasters, but **the literal uniqueness protocol FAILED**: worst forward overlap is 1.0 (limit 0.70), with 78 triggered comparisons. Worst full-footprint Spearman is 0.821258 (limit 0.90). A dense previous surface is a universal overlap blocker under `finite value > 0` support. See the [measured certificate](evidence/uniqueness_saturation_certificate.json). No density/reverse-overlap exception was applied. **STOP was honored: no production final dots and zero real submission slots used.**

Local on-disk format checks PASS: one Float32 band, EPSG:32611, 3730 × 3292, transform `(100, 0, 243350, 0, -100, 4508550)`, every cell finite, range `[0, 0.7537760735]`, zero positive mass on the known catalogue or outside the footprint. This is bridge-template compatibility, **not authenticated official-template identity or organizer acceptance**. The cause of the owner's reported range error is unproven; all-finite zero-fill is a precaution, not a claim that the portal rejects outside-footprint NaN.

- File: `gems57-relative-strand-surface-20261009T195324Z-88e3bcb35a95.tif` (10,010,096 bytes).
- TIFF SHA256: `f273e778341ff726edc5d36bda61c45f53cb0c8f3361f1c55817bc87ddb1012a`.
- Suggested note, **131 / 140 characters**:
  > Fault-zone anatomy: learned magnetic-edge relative strike and host length; buffered LOQO. Research surface; HOLD, not slot-cleared.
- Do **not** upload HTML, a JSON receipt, a PDF or a repository ZIP. Our ZIP contains exactly one TIFF and is round-trip verified.

## What the corrected holdout actually says

**HOLDOUT-DTI only** — evaluator `gems57-pooled-hide-v2`, buffered whole-component LOQO, **11,321 withheld positive pixels**, pooled α=0.2 / β=0.8 / 300 m triangular kernel; 1,000 paired draws over 153 physical 20 km clusters. CIs are conditional on catalogue labels, fixed fitted folds and budgets, not forecasts of live/private scores.

| Arm | Soft-surface HOLDOUT-DTI [95% CI] | Binary-allocation HOLDOUT-DTI [95% CI] |
|---|---|---|
| Distance only | 0.006178 [0.005766, 0.006589] | **0.112725 [0.100561, 0.123569]** |
| Visible-host anatomy | 0.022753 [0.018475, 0.027264] | 0.109753 [0.094653, 0.124432] |
| Anatomy + candidate magnetic relative strike | **0.023203 [0.018778, 0.027992]** | 0.109168 [0.094503, 0.124194] |
| Candidate + recorded sense (ablation) | 0.024209 [0.019704, 0.029288] | 0.112749 [0.098049, 0.128302] |

The downloadable TIFF matches the **soft-surface method**, not the binary test-fold dots. Do not attach 0.109168 to its soft representation. Its relative-orientation binary difference versus distance-only is −0.003557, paired 95% CI [−0.017766, 0.010967]. Added orientation over anatomy is −0.000585 [−0.006179, 0.004966]; added sense is +0.003581 [−0.005722, 0.014532]. All use the evaluator/positive count above. **No demonstrated binary improvement; sense was not retained.** Three predeclared comparisons are complete. No extra tuning run was used to rescue the result.

All **14 feature-alone leakage canaries** were tested using `max(AUC, 1−AUC)` per fold. Maximum discriminative AUC is **0.825867** (diagnostic, not DTI), below 0.90. A clean canary reduces specific risks; it does not certify the absence of all leakage or new-fault domain shift.

Receipts: [holdout](evidence/orientation_holdout.json), [canaries](evidence/orientation_canary.json), [structure](evidence/orientation_structure.json), [all per-raster checks](evidence/orientation_surface_uniqueness.json), [registry classification](evidence/registry_classification.json), [environment](evidence/environment.json).

## The important review finding

**IR-57-STRIKE-01:** a reversed `np.where` fallback reset **every finite primary strike to zero**. Host-relative offsets were global-frame offsets; sin2/cos2 were constant. It is fixed in the shared `anatomy.py`, with east–west-offset and hidden-value-invariance regressions. Empty visible catalogues now fail rather than invent an array-boundary fault.

The first new attempt was stopped; its [aborted receipt/log](evidence/orientation_attempt1-aborted.json) is explicitly untrusted. The same three predeclared hypotheses were repeated only after the tooling repair. Earlier 0.2279/0.2517 readings and claims that constant orientation features might help in interaction are **not valid current mechanism evidence**. Historical artifacts remain for learning, not recommendations. Unsafe in-sample/oracle-budget builders and relaxed uniqueness helpers are retired.

Other shared repairs: metric/evaluator API mismatch, missing `fn`, vector endpoint sampling, zero-based sense-record indexing, exact finite-support/Euclidean-radius uniqueness, and missing-registry fail-closed behavior. [Audit ledger](evidence/irregularities_current.json).

## Why the reported GEMSDOE32 0.2778 is not a scientific explanation

The named result is **OWNER-REPORTED**, not `ORGANIZER-CONFIRMED`: no submission-page receipt attributes it to exact file bytes. The public board lists the participant value but is not a file receipt. We independently established that canonical H33-2-B2 is **40,199 base dots minus 2,545 catalogue-near dots (≤2 px), leaving 37,654; nothing added or relocated**. [Construction proof](evidence/best_submission_audit.json).

Sparse coverage and removing dots with little unique new-truth coverage can reduce false-positive cost under max-cover DTI. That is a plausible mechanism, **not a demonstrated causal gain or proof of secondary-strand discovery**. Nearby newly mapped geometry can also be true. We studied the base only for learning; it is not a feature or base raster for the new model. This experiment does not show that we can exceed 0.2778. The organizer's public board currently provides context, not a forecast or private-score guarantee.

The target is **geological fault presence**, not geothermal-vent, temperature, flow or economic-reservoir labels. Fault mapping supports exploration; it alone does not establish a geothermal resource.

## Core values in practice

- **Maximize P(Win):** reject unsupported improvements, fit zones and budgets from training evidence, distinguish representations and preserve real weekly slots.
- **Own the Outcome:** autonomously restore data, repair shared tools, invalidate corrupted results, publish complete negative evidence and keep download/submission status prominent. No silent protocol relaxation.

## Reproduce, without manual data placement or a GPU

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
PYTHON=.venv/bin/python bash scripts/download_competition_data.sh --cache-bands
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/refresh_registry.py
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_orientation_experiments.py --build-research-surface --minutes 65
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_site.py
.venv/bin/python -m pytest
```

These are reproduction instructions for the **same declared research experiment**, not permission to add experiments or spend slots. Large data/caches are Git-ignored. All eight pins were verified, including the assembled **19-band** 418,912,844-byte feature stack restored from five immutable public GitHub parts. Hashes prove bridge-byte transport identity, **not independently authenticated official origin**. Data placement is no longer the blocker. CPU execution is sufficient for this lane.

The shared instrument is `evaluate_holdout.py`; packaging uses `submission_writer.py`. Catalogue features are visible-only; exact unhidden known pixels are masked for scoring. Whole raster components are withheld with a 3-pixel context collar and quadrant-boundary erosion. Training-only fitted distance zones and prevalence set allocation limits; test-positive counts never choose placement.

## Sources, feed and future work

- [Primary-source claim ledger](evidence/source_checks.json): organizer specifications/staff answers, official rules, USGS GeoDAWN, GDR INGENIOUS and publisher/institutional records; full-paper review is **not** claimed where only an abstract/bibliography was retrieved.
- [Four pre-implementation hypotheses](evidence/hypotheses_current.json), ranked qualitatively by expected value and CPU cost. Relative magnetic strike tested; multi-scale bends, two-host superposition and sense transitions not run.
- [57 pinned sibling sites](evidence/site_inventory.json); [679 conservative grid-raster inventory](evidence/registry_refreshed.json). Four grandfathered auxiliary inputs are separately classified; no dense prediction is exempted. Private/unlinked/inaccessible artifacts remain outside scope.
- Static Pages deployment with tests, read-only public-feed refresh and visible stale/failure status. Public board values remain **ORGANIZER-PUBLISHED**, not submission receipts.
- [Remaining work](REMAINING_WORK.md): explicit uniqueness-protocol decision, authenticated provenance/receipts, geological-system holdouts and the next separately budgeted hypothesis. **Do not submit this release.**

AI assistance was used for code and analysis. The official rules require generative-AI disclosure in finalist narrative materials; entrants remain responsible for authorship, accuracy and licenses.

## Standing request — re-read at every session

The complete preserved standing request follows below and is also in [TASK_PROMPT.md](TASK_PROMPT.md). It records the requested work and historical reports, **not verified scores or current operating status**. The condensed session/prior brief does not establish word-for-word fidelity to the original chat, so it is not labeled “verbatim.” The dated status and evidence above supersede stale factual claims in the historical request (GPU need, unreachable stack, 0.3195 highest, and portal-error causation).

<!-- BEGIN PRESERVED STANDING REQUEST -->

# Preserved standing request and historical report ledger

This preserves the standing request available from session context and the prior repository brief. It is not a word-for-word certified transcript of the original chat, nor evidence that any quoted score or historical limitation is verified. Current status/evidence at the beginning of README.md take precedence over stale factual claims below. Re-read both before future work.

---

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.

Fault-zone anatomy lane: predict where secondary strands sit around known faults from shear-zone mechanics. The organizers define a new fault as any fault pixel not already captured by USGS/INGENIOUS, including newly mapped geometry of an existing system (thread 11536), so splays and parallel strands count. They also confirmed that a dot near a known trace but far from any new-fault pixel is fully penalized (thread 11516), so the allocation must be fitted, not assumed. Analogue experiments of distributed dextral shear (Schreurs, 2003) produce left-stepping en echelon Riedel shears linked by short synthetic shears subparallel to the bulk shear. The classical framework is Tchalenko (1970), and the pattern is consistent with the left-stepping dextral faults Faulds, Henry and Hinz document in the northern Walker Lane. Damage-zone work (Savage and Brodsky, JGR 2011) shows secondary-fracture and strand density decaying away from the primary fault, with zone width growing with displacement and then more slowly. Build a per-fault intensity from distance, fault length as a displacement proxy, and strand orientation relative to the primary strike, conditioned on recorded sense of slip where the database has it. Do not hard-code textbook angles. On the hide-and-recover holdout, measure the relative-strike and distance distributions of withheld segments against their nearest visible fault and keep only the structure the data shows. Shrink this lane’s dot budget if few withheld positives fall inside the fitted zone. Output the standard validated GeoTIFF, uniqueness-checked against every earlier raster.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py) and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.3774

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)

gems-submission-20260926T163915Z-237f0063: 0.0343

....

[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)

Hedge-v2_submission: 0.1563

....

[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)

2314b599: 0.0107

....

[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)

gems-structural-area06-v1: 0.0202

....

[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)

H19-C_20260930T212401Z_c11e495e: 0.0297

....

[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)

h19-4-reference-20260930-691e4dfa: 0.1894

....

[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859

....

[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748

....

[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)

h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE26/](https://buffedlizard55-lab.github.io/GEMSDOE26/)

dilcond-oof-v1-20261003-47629f496133-nan: 0.1223

....

[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

....

[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

....

[https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html)

h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778

....

[https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html)

h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418

....

[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

....

[https://buffedlizard55-lab.github.io/GEMSDOE37/](https://buffedlizard55-lab.github.io/GEMSDOE37/)

h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193

....

[https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html)

D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763

....

[https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html)

xscale-worm-persistence-20261006T000541Z-nan: 0.0581

....

[https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html)

sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: 0.0424

....

[https://buffedlizard55-lab.github.io/GEMSDOE45/](https://buffedlizard55-lab.github.io/GEMSDOE45/)

h51-km-faultzone-20261006-zeros: 0.0106

....

[https://buffedlizard55-lab.github.io/GEMSDOE49/](https://buffedlizard55-lab.github.io/GEMSDOE49/)

gate_ortho_w0.25-40k-20261006T213721Z-nan: 0.2376

....

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

....

[https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html)

efd28-repro-20261003-1cc7dc534d51-nan: 0.2600

repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041

sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512

wormrank-d28-20261003-59dcaf6dd11d-zeros:0.2560

wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532

xfit-c0-habitat-20261003-ca879db0089a-zeros:

xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros:

....

[https://buffedlizard55-lab.github.io/GEMSDOE46/](https://buffedlizard55-lab.github.io/GEMSDOE46/)

r11f-scarp-radiometric-fusion-00e049b51218-zeros:0.1589

r12-scarp-rad-concordance-23e807e2de9f-zeros: 0.0843

....

[https://buffedlizard55-lab.github.io/GEMSDOE39/](https://buffedlizard55-lab.github.io/GEMSDOE39/)

h40-e-disc-h40e-30k-zeros: 0.0339

....

[https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html)

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: 0.0355

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard:

h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros:

....

[https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html)

h42-submission-primary: 0.0245

....

[https://buffedlizard55-lab.github.io/GEMSDOE44/docs/](https://buffedlizard55-lab.github.io/GEMSDOE44/docs/)

h46-twostageAB_20261006T160000Z_b0cfe956-zeros: 0.0715

....

[https://buffedlizard55-lab.github.io/GEMSDOE47/](https://buffedlizard55-lab.github.io/GEMSDOE47/)

h60-lidarscarp-s2p0-20261007-nanoutside: 0.0430

....

[https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html)

h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8: 0.2296

....

[https://buffedlizard55-lab.github.io/GEMSDOE50/](https://buffedlizard55-lab.github.io/GEMSDOE50/)

h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite:

....

[https://buffedlizard55-lab.github.io/GEMSDOE51/](https://buffedlizard55-lab.github.io/GEMSDOE51/)

h53-twostage-20261008T040951Z-9a0b32c871:

....

[https://buffedlizard55-lab.github.io/GEMSDOE52/](https://buffedlizard55-lab.github.io/GEMSDOE52/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html)

h8-tiprelay-ridgeconcord-pr2-n80000-20261009-49bec522-zeros:

....

[https://buffedlizard55-lab.github.io/GEMSDOE54/docs/](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/)

h54c-manifest-edge-20261009T025732Z-73454bc5:

....

55GEMSDOE

:

....

56GEMSDOE

:

....

57GEMSDOE

:

....

The following is the leaderboard for the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See below for more links and information related to the competition:

[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)

[https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

[https://gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/)

[https://epsg.io/32611](https://epsg.io/32611)

[https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195	is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)

“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). We must put Arena first.

Own the Outcome

We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.



Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission

File to submitNo file chosen

You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.

Note (optional)

A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow.[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)

Get familiar with the problem through the overview and problem description,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want to reference additional resources available on the about page,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).

Download the data from the data,[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), tab.

Create and train your own model. This reference solution,[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.

[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (verified redirect to login)

See below for links from the above site.  See attached files for links from the above site.

[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (requires login) to data/

See links below for competition data:

[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0)

[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0)

[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0)

[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0)

[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0)

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.

Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.

Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.


## Session addendum — H57-K candidate (2026-10-09, this session)

A separate lane run, merged on top of the release above. It produced a second
file, and reached the **same blocker by an independent route**.

### What was built

- **The official 19-band GeoDAWN feature stack is now local and sha256-verified**
  (`scripts/download_features.sh`, fails closed unless the bytes and hash match
  the pin). This closes the gap recorded in `REMAINING_WORK.md` §6: no earlier
  session of this repository had it.
- **A live-anchored credit instrument** (`scripts/live_credit_shells.py`)
  converts nine OWNER-REPORTED scores into pooled credit using the
  GEMSDOE48-corrected identity `DTI = T / (0.2T + 0.2n − 0.2Q + 0.8G)`, fixing
  the hidden-truth mass **G = 14,089** from one nested owner-reported pair. It
  measures the ≤ 2 px proximal band at **0.0024** credit per dot against
  **0.1387** for the dots the 0.2778 submission kept, and falsifies
  distance-to-catalogue alone: two dot fields with nearly identical distance
  distributions differ **6×** in measured credit.
- **H57-K** adds *strand expression* — whether a pixel inside a damage zone
  actually carries the geophysical signature of a fault — to the lane geometry
  the prompt asks for. No angle is hard-coded; every weight is fitted on the
  hide-and-recover holdout. HOLDOUT-DTI, 8 detached cells, **22,619** withheld
  positives, α = 0.2 β = 0.8, 300 m kernel:

  | Arm | Features | HOLDOUT-DTI | 95 % CI (quadrant jackknife) |
  |---|---|---|---|
  | `d_only` | 1 | 0.0507 | [0.0358, 0.0655] |
  | `lane8` | 8 | 0.1024 | [0.0840, 0.1209] |
  | `lane8_geophys` | 48 | **0.1103** | [0.0917, 0.1290] |

  The geophysical term's +0.008 sits inside the intervals, so it is reported as
  measured, **not** as a win.

### A defect found and fixed in the shared template

`gems57.emit.allocate_by_marginal_bar` visits candidates once in descending
`E[k]` order and **breaks** at the first candidate failing the two-sided DTI
test. Marginal credit `dT` depends on *local kernel saturation*, not on rank, so
on a surface with flat plateaus of near-equal `E[k]` the next candidate in
row-major order can sit on a dot already placed, return `dT = 0`, and end the
pass early: measured here, **3,405** dots instead of **62,872**, surrogate DTI
0.0832 instead of 0.2927. Fixed once, in the template, as
`gems57.emit.allocate_patient` — identical accept/reject test, but it stops only
after `patience` consecutive rejections. Six regression tests in
`tests/test_allocator_nonredundant.py`; the original function is retained for
callers and comparison. No private fork.

### The file, and why it is still not cleared

`docs/downloads/gems57-h57k-damagezone-strandexpr-62872dots-20261009T220159Z-f38e36d82033-zeros.tif`
(854,692 B, sha256 `749fdffc…d30f9d6`), plus a single-TIFF `.zip`.
**15/15 local format checks pass.** 62,872 dots, none on the mapped catalogue.
Byte identity checked against the **full 655-raster registry index**: **0**
exact matches, so it is provably not a copy of any earlier raster. Worst
Spearman over the full footprint **0.0246** (limit 0.90); worst dot-set Jaccard
**0.0198** (limit 0.50).

**It still fails protocol rule 1 exactly as written, and this run does not claim
an exemption.** 99.8 % of its dots fall within 3 px of `r13-lattice-s5`, whose
3 px halo covers 0.9987 of the footprint. That clause was measured before being
relied on: it also fires for the family's own OWNER-REPORTED 0.2778 submission
at 0.999 against the same lattice, so it cannot be passed by *any* nonempty dot
set. This is the **same obstruction the release above certifies**, found
independently from a different witness raster. The remedy recorded by the
earlier session stands: an **owner protocol revision**, not a redefinition of
support, not an exemption for dense maps, not a reverse-overlap condition, and
not choosing another raster after STOP.

Run card `evidence/h57k_run_card.json`: **verdict `negative`**,
`okay_to_submit: false`, `promotion_ready: false`. The scientific result is
positive; the submission candidate is blocked. Page: `docs/h57k.html`.

### The dominant open risk

The two calibrated instruments disagree about *where* dots belong. The
live-anchored instrument says the ≤ 2 px band is dead and every raster in this
family that has ever scored sits at median **19.6 px** from the catalogue. The
holdout model — trained on withheld *catalogue* pixels — puts essentially all
its mass within a few pixels of it: sweeping the proximal exclusion from 2 px to
20 px collapses modelled credit from 6,057 to 179. Only the ≤ 2 px exclusion is
a measurement, so only that was imposed, and the emission sits at median
**3.6 px**. Unresolved; `IR-57-PROX-01`.

### Scope limit of the uniqueness screen

The correlation/overlap screen ran against the **16** registry rasters present
in this sandbox. The full index has **655**; the other 639 live in sibling
repositories and were not re-downloaded. Byte identity *was* checked against all
655. That asymmetry is disclosed rather than papered over.

---

<!-- END PRESERVED STANDING REQUEST -->
