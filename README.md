# 57GEMSDOE — fault-zone anatomy lane, evidence before slots

**[Open the site](https://buffedlizard55-lab.github.io/57GEMSDOE/)** ·
**[Executive summary / how to submit](https://buffedlizard55-lab.github.io/57GEMSDOE/executive-summary.html)** ·
[Competition #306](https://www.drivendata.org/competitions/306/competition-doe-gems/) ·
[Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

## Download at the beginning — and an unmistakable status

### Download GeoTIFF: OK · Submit to competition: **NO — do not submit** (see the run card)

**[↓ Download the submission GeoTIFF](https://buffedlizard55-lab.github.io/57GEMSDOE/downloads/gems57-fza-h61prune-20261010T222725Z-3791510cd5d8.tif)** ·
**[Single-TIFF ZIP](https://buffedlizard55-lab.github.io/57GEMSDOE/downloads/gems57-fza-h61prune-20261010T222725Z-3791510cd5d8.zip)** ·
[Complete JSON run card](evidence/run_card_current.json)

This is a **Session-7 (2026-10-10) binary dot submission** from the fault-zone anatomy lane
(`33,930` dots, zone-shrunk greedy max-cover allocation of the retained
two-host relay + bend intensity). It is **byte- and pixel-identical to nothing** among
**705** indexed grid rasters across all **57** public GEMSDOE
repositories, and worst cross-lane full-footprint Spearman is only
**0.1287** — but the operative drift screen (rule 1, dot
representation) **STOPPED** it: 29 of 679 cross-lane rows fire the 3-px dot-overlap
threshold. A saturation certificate
([evidence/uniqueness_scaffold_saturation.json](evidence/uniqueness_scaffold_saturation.json))
shows **21 of those rows cannot discriminate** (scaffold/union emissions whose 3-px
neighborhoods cover 0.745–0.9996 of the allowed domain — any nonempty placement fires
them). The other **8 rows (8 files, 5 sibling projects) are genuine agreement**: independent
secondary-strand models (tip-relay 0.919 at 23.7% domain coverage, relay 0.716 at 16.0%,
physics-dotted 0.702, ridge-concordant 0.717/0.740, 8GEMSDOE 0.725) place their dots where
this lane's dots land at **2.2–4.5× chance enrichment**. Under the portfolio's anti-drift
rule — thresholds unchanged, no exemptions — that is a stop: **verdict NEGATIVE**, zero
weekly slots, and any threshold revision is the owner's explicit, dated protocol decision
(IR-S7-01), never a silent re-screen. The inherited literal positive-support screen is also
published unchanged in the run card and per-raster rows
(it cannot discriminate — see [evidence/uniqueness_decision.json](evidence/uniqueness_decision.json)).

Local format checks PASS: one Float32 band, EPSG:32611, 3730 × 3292, transform
`(100, 0, 243350, 0, -100, 4508550)`, **every cell finite**, range
`[0.0, 1.00000000]`, zero positive
mass on the USGS/INGENIOUS catalogue or outside the footprint. This is bridge-template
compatibility, **not** authenticated official-template identity or organizer acceptance.

- File: `gems57-fza-h61prune-20261010T222725Z-3791510cd5d8.tif` (92,615 bytes).
- TIFF SHA256: `b6201a4aa3e63dbc74e32d0393728d0a29d3a2c592c049223ca7c4b55514b6da`.
- Suggested note, **95 / 140 characters**:
  > Fault-zone anatomy E2+H6-1: relay/bend fit, zone 26px, 33930 dots, proximal prune off; 3791510c
- Do **not** upload HTML, a JSON receipt, a PDF or a repository ZIP. Our ZIP contains exactly
  one TIFF and is round-trip verified. All-finite `[0,1]` values prevent the portal error
  "Predicted values must be in range [0, 1]".
- **Weekly slots spent by this project: 0.** Promotion to a real
  slot is the owner's selection decision within the published cap (three per week).

## Why did h33-h33-2-b2 score 0.2778 — and can we beat it?

**Why (file-level, measured; the score itself is OWNER-REPORTED).** The 0.2778 raster is an
exact subset of the owner-reported 0.2708 raster: it removes 2,545 dots, every one 1.4–2.0 px
from the mapped catalogue, and adds nothing
([evidence/best_submission_audit.json](evidence/best_submission_audit.json)). Under the
max-cover DTI (α = 0.2, β = 0.8, 300 m triangular kernel) a dot that adds no marginal truth
credit only adds false-positive cost, so a precision-side prune can raise DTI — a plausible
mechanism, **not** a demonstrated causal gain (no organizer file receipt links those bytes to
that score).

**What that mechanism is worth on real evidence (HOLDOUT-DTI, this session).** We tested the
prune rule on the repaired hide-and-recover holdout against *both* controls at matched dot
counts (11,321 withheld positives, gems57-pooled-hide-v2, 1,000 paired draws over 145 physical
20 km clusters):

| Arm (binary allocation) | HOLDOUT-DTI [95% CI] |
|---|---|
| unpruned | 0.135204 [0.118458, 0.153061] |
| proximity-pruned (≤ 2 px of mapped catalogue) | 0.132699 [0.116090, 0.150936] |
| random-pruned (same count) | 0.135750 [0.119065, 0.153695] |

Paired differences: pruned − unpruned = **-0.002505**
[-0.003690, -0.001464];
pruned − random = **-0.003051**
[-0.004200, -0.002039].
**Both strictly negative.** On withheld catalogue truth, strands root on mapped traces (new
geometry of an existing system counts as new fault — organizer thread 11536), so the blanket
2-px prune deletes real coverage. Per the predeclared rule the final build does **not** prune.
The 0.2778 file's labels are hidden, so we cannot prove what its prune bought there; we can
say the rule is not a transferable free gain, and the transferable lessons are **sparse
allocation** (37–40k dots; dot-count vs live score Spearman −0.8104 over 15 owner-reported
files) and **precision-side budget discipline**.

**Can we score higher than 0.2778?** There is no metric ceiling at that value, and this release
is a genuinely new construction — a holdout-fitted two-host relay/bend intensity (binary
HOLDOUT-DTI 0.135204 [0.119140, 0.153036]; +0.0256
over single-host anatomy, 95% CI [+0.0139, +0.0371]) with 33,930 greedy
dots — but the portfolio's own anti-drift rule stopped it before any slot could be
considered (IR-S7-01, above), so **it is not submittable under the current protocol** and no
organizer-confirmed score above 0.2778 has been demonstrated. A hide-and-recover CI is not a
live-score forecast. The owner-reported 0.2778 / 0.3195 / 0.3774 values are context, not
forecasts or receipts. The discriminating cross-lane agreements (tip-relay/relay/physics
models landing within 3 px of this lane's dots at 2–4× chance) are convergent evidence that
the anatomy lane finds real structure — which is precisely why rule 1 reads them as
"another lane's result" and stops.

## Session-7 run summary (HOLDOUT-DTI or REGISTRY-MEASUREMENT labels)

- **E1 / H6-1 (negative, delivered):** catalogue-proximity pruning tested against unpruned and
  matched-random controls — table above; canary clean (max feature AUC 0.825867, all < 0.90);
  retained = false. Receipt: [evidence/session7_h61_prune.json](evidence/session7_h61_prune.json).
- **E2 (built):** retained arm `relay_bend_anatomy` (distance, log-length displacement proxy,
  host-relative sin2/cos2, two-host relay d2/ratio/facing, multi-scale bend, scarp strike; no
  textbook angles), fitted zone 25.55 px (90th percentile of training withheld
  distances) with a zone-shrunk budget of 33,930 dots,
  greedy allocation, all-finite export. Structure measured as the lane requires
  ([evidence/session7_structure.json](evidence/session7_structure.json)): withheld positives
  sit at median 9.06 px from their nearest visible fault vs 25.50 px for domain pixels; the
  retained features keep only that measured decay + orientation structure.
- **Uniqueness:** surface screen before placement and final-dot screen after
  ([evidence/session7_surface_uniqueness.json](evidence/session7_surface_uniqueness.json),
  [evidence/session7_final_uniqueness.json](evidence/session7_final_uniqueness.json)) — both
  screens (dot-representation + literal) on every one of the 705 rows.
  Result: **STOP** (IR-S7-01) — 29 fired rows, 21 non-discriminating scaffolds, 8 genuine
  cross-lane agreements; verdict **NEGATIVE**.
- **Budget respected:** 2 experiments, 0 submission slots.
- **IR ledger:** IR-S6-01 / 05 / 10 / 12 resolved; IR-S7-01 open (stop honored)
  ([evidence/irregularities_current.json](evidence/irregularities_current.json)).

## Ranked untried hypotheses for the next budgeted session

Full pre-registration with layers, signatures, falsifiers and data sources:
[evidence/session7_hypotheses.json](evidence/session7_hypotheses.json). Test only rank 1 next.

| Rank | ID | Hypothesis | Layers | Cost | Falsifier |
|---|---|---|---|---|---|
| 1 | **H7-1** | Fault-tip termination and splay-root anatomy: the signed along-strike distance to visible component tips, and the fan of damage around them, adds held-out skill beyond distance-to-fault and two-host relay geometry. | data/official/existing_faults.tif (visible-only component endpoints), data/external/trace_segments_utm11.csv (INGENIOUS segment terminations)… | low (visible-only EDTs and endpoint extraction; 2-4 new columns) | Paired 95% lower bound vs relay_bend_anatomy is at or below zero; or skill concentrates on one side of the fau… |
| 2 | **H7-2** | Stepover dilatation sign: releasing (transtensional pull-apart) relay corridors between left-stepping dextral hosts carry higher secondary-strand intensity than restraining ones, measurable from detrended topography and isostatic-gravity gradients without any textbook angle. | band 12 det_elev and band 19 det_elev_slope (corridor subsidence and flank scarps), band 13 iso_grav_anom and band 5 iso_grav_anom_slope (low-density basin fill)… | medium (cross-corridor profile sampling in the two-host frame; 3-5 columns) | No paired gain over relay_bend_anatomy; or the effect flips under a matched restraining-bend control; canary A… |
| 3 | **H7-3** | Geodetic strain-rate concordance: secondary-strand probability rises where the damage-zone intensity coincides with an anomaly in geodetic shear-rate / second invariant, because the catalogue misses young active strands and geodesy is catalogue-independent. | band 7 geod_shearrate, band 4 geod_2ndinv, band 8 geod_dilaterate, band 10 deq_n100a15 and band 16 ieq_n100a15 (seismicity context)… | low-medium (band caches already local; interaction columns only) | Interaction column alone fires the canary (seismicity/distance confound); or paired gain is at or below zero; … |
| 4 | **H7-4** | Flight-line-aligned magnetic-mimic suppression: magnetic-gradient lineaments parallel to survey flight-line direction and unmatched by a gravity or scarp edge are leveling artifacts, and down-weighting them improves held-out precision over the unsuppressed magnetic-edge feature. | band 1 mag_anom, band 2 rtp, band 14 tmi, band 9 tmi_vg (magnetic family), band 13 iso_grav_anom, band 12 det_elev (independent edge corroboration)… | medium (flight-line azimuth from official metadata text pages or an internal FFT/structure-tensor stripe estimator; no new raster required) | Suppression removes true-fault signal (withheld recall drops more than precision gains); or the paired lower b… |
| 5 | **H7-5** | Radiometric K/eTh alteration-halo concordance: potassic-alteration ratios adjacent to stepover damage zones corroborate permeable Quaternary strand habitat and improve precision over the anatomy intensity alone. | GeoDAWN radiometric grids (K, eTh, eU) from ScienceBase DOI 10.5066/P93LGLVQ, bridged auxiliary raster GEMSDOE40:data/aux/radiometric_u8.tif in the public owner inventory (obtainable through the allowed github.com host; provenance UNVERIFIED until pinned and profiled)… | higher (data acquisition, provenance authentication, ratio construction, NODATA screening) | No paired gain once K/Th is added to the anatomy arm; or the ratio tracks lithologic units (diorite vs basalt)… |

## How to submit (full guide: [executive-summary](https://buffedlizard55-lab.github.io/57GEMSDOE/executive-summary.html))

1. Download the `.tif` (or single-TIFF `.zip`) from the link at the top of this page.
2. Open [DrivenData: New submission](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/), log in, check your weekly counter (published cap: 3/week).
3. Choose the file under "File to submit"; it matches the submission format's CRS/shape/geotransform.
4. Paste the ≤140-character note above into the optional Note field.
5. Save the organizer receipt (filename, SHA256, note, timestamp, score). A public board value is not a file receipt.

## Method and instrument (no private forks)

Hide-and-recover: whole fault components withheld with a 3-px feature collar and 12-px quadrant
erosion; every catalogue feature derived from visible faults only; visible faults masked
pixel-exactly from scoring (a dot near a known trace with no new-fault pixel earns nothing —
organizer thread 11516); pooled DTI α = 0.2 / β = 0.8 / 300 m triangular kernel
(`gems57-pooled-hide-v2`). Shared tools: `src/gems57/evaluate_holdout.py`,
`src/gems57/submission_writer.py`, `src/gems57/uniqueness.py` (both uniqueness screens live
here, fixed once). Every number above is HOLDOUT-DTI or REGISTRY-MEASUREMENT; no projection is
written as a score. The target is **geological fault presence**, not geothermal-vent labels;
fault mapping supports exploration but does not establish a resource.

## Sources for manual review

- Organizer problem/mask definitions: [DrivenData competition page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- Official data/metadata: [USGS GeoDAWN (DOI 10.5066/P93LGLVQ)](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [GDR/INGENIOUS](https://gbcge.org/current-projects/ingenious/) · [GDR submission 1391](https://gdr.openei.org/submissions/1391) · [EPSG:32611](https://epsg.io/32611)
- Mechanics literature named in the lane: Schreurs (2003) en echelon Riedel shears; Tchalenko (1970) shear-zone framework; Savage & Brodsky (JGR 2011) damage-zone scaling; Faulds, Henry & Hinz (northern Walker Lane) left-stepping dextral faults. Full claim ledger: [evidence/source_checks.json](evidence/source_checks.json).
- Metric: [Tversky index](https://en.wikipedia.org/wiki/Tversky_index) (distance-weighted for DTI).

## Core values in practice

- **Maximize P(Win):** evidence before slots; predeclared experiments with paired CIs; negative
  results published, not hidden; no slot spent on an unvalidated idea.
- **Own the Outcome:** data restored and hash-verified autonomously; shared tools repaired once
  and pinned by tests; both uniqueness screens published; the download/submit status is
  unmistakable and driven by the run card.

## Reproduce (CPU, no manual data placement)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
.venv/bin/python scripts/prepare_data.py --fetch --cache-bands
.venv/bin/python scripts/refresh_registry.py --workers 8
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_session7_lane.py experiment
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python scripts/run_session7_lane.py build
.venv/bin/python scripts/build_site.py
.venv/bin/python scripts/check_site.py
.venv/bin/python -m pytest
```

Large data/caches are Git-ignored and restored by hash. AI assistance was used for code and
analysis; the official rules require generative-AI disclosure in finalist narrative materials,
and authorship/accuracy remain the entrant's responsibility.

## Standing owner prompt (re-read at the start of every session)

<details>
<summary>The complete standing request, preserved verbatim (also at <a href="TASK_PROMPT.md">TASK_PROMPT.md</a>)</summary>

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

</details>
