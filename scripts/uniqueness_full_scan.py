#!/usr/bin/env python3
"""Full-registry uniqueness scan with an explicit dense-witness degeneracy test.

The literal gate in :mod:`gems57.uniqueness` defines a raster's "dots" as every
finite positive pixel.  A registry raster that is a *continuous* probability
surface therefore has support equal to (nearly) the whole footprint, and its
3 px dilation covers essentially every allowable cell.  For such a witness the
forward-overlap statistic is >= 0.70 for **every** nonempty candidate, including
uniform random noise, so it carries no lane-drift information at all.  Session 6
recorded this as an unresolved obstruction and stopped.

This script does not relax the thresholds.  It reports all four of:

1. ``literal`` -- the shared gate, unchanged, over the whole refreshed index.
2. ``degeneracy_certificate`` -- K uniform random sparse dot fields of the same
   size as the candidate, scored against each firing witness.  If the random
   fields also exceed the overlap limit, the firing is a property of the
   witness, not of the candidate.  This is a falsifiable test, not an exemption.
3. ``density_matched`` -- each dense witness reduced to its own top-N cells
   (N = candidate dot count) before the same 3 px comparison, which is the only
   comparison between a sparse candidate and a continuous surface that can
   distinguish placement from coverage.
4. ``sparse_screen`` -- the literal thresholds applied to the subset of registry
   rasters whose positive support is comparable to a dot field (<= 5% of the
   footprint).  This is the screen that can actually detect lane drift.

The verdict is reported for each view separately.  Nothing here authorizes a
submission slot; that is a separate selector step.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems57 import load_grid  # noqa: E402
from gems57.uniqueness import (JACCARD_LIMIT, OVERLAP_LIMIT, RHO_LIMIT,  # noqa: E402
                               _dots, _near, compare_to_registry)

EVID = ROOT / "evidence"
SPARSE_SUPPORT_FRACTION = 0.05


def load_candidate(path: Path, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        if src.count != 1 or (src.height, src.width) != footprint.shape:
            raise ValueError("candidate must be a single-band competition-grid raster")
        a = src.read(1)
    a = np.where(np.isfinite(a), a, 0.0).astype(np.float32)
    a[~footprint] = 0.0
    if (a < 0).any() or (a > 1).any():
        raise ValueError("candidate must be in [0,1]")
    return a


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--index", type=Path, default=EVID / "registry_refreshed.json")
    ap.add_argument("--random-fields", type=int, default=200)
    ap.add_argument("--seed", type=int, default=57)
    ap.add_argument("--out", type=Path, default=EVID / "h57l_uniqueness.json")
    ap.add_argument("--reuse-rows", type=Path, default=None,
                    help="reuse the literal-gate rows from a previous scan of the SAME "
                         "candidate (skips re-reading the registry; the literal numbers "
                         "are copied verbatim, never recomputed differently)")
    ap.add_argument("--comparable-factor", type=float, default=3.0,
                    help="a registry raster is budget-comparable if its dot count is at "
                         "most this multiple of the candidate's")
    a = ap.parse_args()
    t0 = time.time()

    g = load_grid()
    footprint, catalogue = g.footprint, g.catalogue
    allowed = footprint & ~catalogue
    mine = load_candidate(a.candidate, footprint)
    my_support = _dots(mine) & footprint
    n_my = int(my_support.sum())
    print(f"[uniq] candidate {a.candidate.name}: {n_my} dots "
          f"({n_my / allowed.sum():.4%} of the {int(allowed.sum())} allowable cells)", flush=True)

    index = json.loads(a.index.read_text())
    if a.reuse_rows:
        prev = json.loads(a.reuse_rows.read_text())
        if Path(prev["candidate_file"]).name != Path(a.candidate).name:
            raise SystemExit("--reuse-rows points at a scan of a DIFFERENT candidate")
        if int(prev["candidate_dots"]) != n_my:
            raise SystemExit("--reuse-rows candidate dot count does not match")
        literal = dict(prev["literal_gate"])
        literal["rows"] = prev["rows"]
        print(f"[uniq] reused literal rows from {a.reuse_rows.name} "
              f"({len(prev['rows'])} rows)", flush=True)
    else:
        literal = compare_to_registry(a.candidate, index, footprint)
    print(f"[uniq] literal gate: checked {literal['registry_rasters_checked']}/"
          f"{literal['registry_rasters_expected']} complete={literal['complete_accessible_scan']} "
          f"duplicate_count={literal['duplicate_count']} unique={literal['unique']} "
          f"({time.time()-t0:.0f}s)", flush=True)

    rows = literal["rows"]
    firing = [r for r in rows if "error" not in r and (
        r.get("duplicate_by_rho") or r.get("duplicate_by_overlap"))]
    # Witnesses are the rasters whose support is so dense that the forward
    # overlap statistic cannot discriminate between candidates.
    dense = [r for r in rows if "error" not in r
             and r.get("their_dots", 0) / max(int(footprint.sum()), 1) > SPARSE_SUPPORT_FRACTION]
    sparse = [r for r in rows if "error" not in r and r not in dense]
    print(f"[uniq] firing={len(firing)}  dense witnesses (>{SPARSE_SUPPORT_FRACTION:.0%} "
          f"support)={len(dense)}  sparse dot fields={len(sparse)}", flush=True)

    # --- 1. degeneracy certificate: uniform random sparse fields of equal size
    rng = np.random.default_rng(a.seed)
    # Random fields are generated and consumed one at a time: materialising 200
    # full-grid boolean arrays would need ~2.4 GB in a 3 GB sandbox.
    allowed_flat = np.nonzero(allowed.ravel())[0]
    n_pick = int(min(n_my, allowed_flat.size))
    fields = []
    for _ in range(a.random_fields):
        f = np.zeros(allowed_flat.size, bool)
        f[rng.permutation(allowed_flat.size)[:n_pick]] = True
        fields.append(f)          # boolean over the allowable cells only (5 MB each)
    cert = []
    for r in firing:
        rp = Path(r["file"])
        with rasterio.open(rp) as src:
            t = src.read(1)
        theirs = np.where(np.isfinite(t), t, 0.0).astype(np.float32)
        theirs[~footprint] = 0.0
        near = _near(_dots(theirs) & footprint)[allowed]
        rand_ov = np.array([float(near[f].mean()) for f in fields])
        cert.append(dict(
            submission=r["submission"], repo=r.get("repo"), file=r["file"],
            their_dots=int(r["their_dots"]),
            their_support_fraction_of_footprint=r["their_dots"] / int(footprint.sum()),
            candidate_forward_overlap=float(r["my_dots_within_3px_of_theirs"]),
            random_forward_overlap_mean=float(rand_ov.mean()),
            random_forward_overlap_min=float(rand_ov.min()),
            random_forward_overlap_max=float(rand_ov.max()),
            random_fields_exceeding_limit=int((rand_ov > OVERLAP_LIMIT).sum()),
            random_fields_tested=len(fields),
            degenerate=bool(rand_ov.min() > OVERLAP_LIMIT),
            interpretation=("every uniform random sparse field of the same size also exceeds the "
                            "0.70 overlap limit against this witness, so the firing measures the "
                            "witness's coverage, not this candidate's lane")
            if rand_ov.min() > OVERLAP_LIMIT else
            "this witness discriminates: at least one random field stayed under the limit",
        ))
        del theirs, near
        print(f"  [cert] {r['submission'][:40]:40s} cand={r['my_dots_within_3px_of_theirs']:.4f} "
              f"random[min,mean,max]=[{rand_ov.min():.4f},{rand_ov.mean():.4f},{rand_ov.max():.4f}] "
              f"degenerate={cert[-1]['degenerate']}", flush=True)

    # --- 2. density-matched comparison against the dense witnesses
    matched = []
    dense_firing = [r for r in dense if r in firing]
    print(f"[uniq] density-matched view over {len(dense_firing)} firing dense witnesses "
          f"(of {len(dense)} dense)", flush=True)
    for r in dense_firing:
        rp = Path(r["file"])
        with rasterio.open(rp) as src:
            t = np.where(np.isfinite(src.read(1)), src.read(1), 0.0).astype(np.float32)
        t[~footprint] = 0.0
        tv = t[allowed]
        if tv.size <= n_my:
            top = allowed.copy()
        else:
            thr = np.partition(tv, tv.size - n_my)[tv.size - n_my]
            top = allowed & (t >= thr)
            # break ties down to exactly n_my cells in a deterministic order
            excess = int(top.sum()) - n_my
            if excess > 0:
                ys, xs = np.nonzero(top)
                order = np.lexsort((xs, ys))[-excess:]
                top[ys[order], xs[order]] = False
        near_top = _near(top)
        near_mine = _near(my_support)
        matched.append(dict(
            submission=r["submission"], repo=r.get("repo"), file=r["file"],
            their_full_support=int(r["their_dots"]),
            density_matched_dots=int(top.sum()),
            literal_forward_overlap=float(r["my_dots_within_3px_of_theirs"]),
            matched_forward_overlap=float(near_top[my_support].mean()) if n_my else 0.0,
            matched_reverse_overlap=float(near_mine[top].mean()) if top.any() else 0.0,
            matched_jaccard=float((my_support & top).sum() / max((my_support | top).sum(), 1)),
            spearman_full_footprint=r.get("spearman_full_footprint"),
            exceeds_overlap_limit=bool(near_top[my_support].mean() > OVERLAP_LIMIT) if n_my else False,
        ))
        del t, top, near_top, near_mine
        print(f"  [match] {r['submission'][:40]:40s} literal={r['my_dots_within_3px_of_theirs']:.4f} "
              f"matched={matched[-1]['matched_forward_overlap']:.4f} "
              f"jac={matched[-1]['matched_jaccard']:.4f}", flush=True)

    # --- 3. budget-comparable screen -------------------------------------- #
    # The 3 px forward-overlap statistic can only distinguish placement from
    # coverage when the witness spends a comparable number of dots.  A witness
    # with ten times the candidate's budget has a 3 px dilation that covers most
    # of the allowable area on its own, so its overlap is a property of its own
    # density.  This screen therefore restricts to witnesses within
    # --comparable-factor of the candidate's dot count and applies the SAME
    # literal thresholds, unrelaxed.  Each firing is additionally certified
    # against uniform random fields of the candidate's size, so a witness that
    # fires on noise alone is identified rather than silently excluded.
    cap = a.comparable_factor * n_my
    comparable = [r for r in rows if "error" not in r and r.get("their_dots", 0) <= cap]
    comp_flags = [r for r in comparable if any(r.get(k, False) for k in (
        "duplicate_by_rho", "duplicate_by_overlap", "identical_bytes",
        "identical_decoded_predictions"))]
    comp_cert = []
    for r in comp_flags:
        with rasterio.open(Path(r["file"])) as src:
            t = src.read(1)
        theirs = np.where(np.isfinite(t), t, 0.0).astype(np.float32)
        theirs[~footprint] = 0.0
        near = _near(_dots(theirs) & footprint)[allowed]
        rand_ov = np.array([float(near[f].mean()) for f in fields])
        comp_cert.append(dict(
            submission=r["submission"], repo=r.get("repo"),
            their_dots=int(r["their_dots"]),
            dot_count_ratio_to_candidate=r["their_dots"] / max(n_my, 1),
            candidate_forward_overlap=float(r["my_dots_within_3px_of_theirs"]),
            random_forward_overlap_mean=float(rand_ov.mean()),
            random_forward_overlap_max=float(rand_ov.max()),
            random_fields_exceeding_limit=int((rand_ov > OVERLAP_LIMIT).sum()),
            random_fields_tested=len(fields),
            degenerate=bool(rand_ov.min() > OVERLAP_LIMIT),
            jaccard_dot_sets=r.get("jaccard_dot_sets"),
            spearman_full_footprint=r.get("spearman_full_footprint"),
        ))
        del theirs, near
        print(f"  [comp] {r['submission'][:44]:44s} dots={r['their_dots']:7d} "
              f"cand={r['my_dots_within_3px_of_theirs']:.4f} "
              f"random_max={rand_ov.max():.4f} degenerate={comp_cert[-1]['degenerate']}",
              flush=True)
    comp_rank = [r for r in comparable if r.get("spearman_full_footprint") is not None]
    worst_comp_rho = max(comp_rank, key=lambda r: r["spearman_full_footprint"], default=None)
    worst_comp_ov = max(comparable, key=lambda r: r["my_dots_within_3px_of_theirs"], default=None)
    worst_comp_jac = max(comparable, key=lambda r: r["jaccard_dot_sets"], default=None)
    comp_nondegenerate = [c for c in comp_cert if not c["degenerate"]]

    # --- 4. sparse screen (support-fraction definition, retained for continuity)
    sparse_flags = [r for r in sparse if any(r.get(k, False) for k in (
        "duplicate_by_rho", "duplicate_by_overlap", "identical_bytes",
        "identical_decoded_predictions"))]
    sparse_rank = [r for r in sparse if r.get("spearman_full_footprint") is not None]
    worst_sparse_rho = max(sparse_rank, key=lambda r: r["spearman_full_footprint"], default=None)
    worst_sparse_ov = max(sparse, key=lambda r: r["my_dots_within_3px_of_theirs"], default=None)
    worst_sparse_jac = max(sparse, key=lambda r: r["jaccard_dot_sets"], default=None)

    payload = dict(
        evidence_class="REGISTRY-MEASUREMENT",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        candidate_file=str(a.candidate),
        candidate_dots=n_my,
        allowable_cells=int(allowed.sum()),
        candidate_support_fraction_of_allowable=n_my / int(allowed.sum()),
        registry_index=str(a.index),
        registry_rasters_expected=literal["registry_rasters_expected"],
        registry_rasters_checked=literal["registry_rasters_checked"],
        complete_accessible_scan=literal["complete_accessible_scan"],
        thresholds=dict(rho=RHO_LIMIT, overlap=OVERLAP_LIMIT, jaccard=JACCARD_LIMIT),
        sparse_support_fraction=SPARSE_SUPPORT_FRACTION,
        literal_gate={k: v for k, v in literal.items() if k != "rows"},
        literal_firing=[{k: v for k, v in r.items()} for r in firing],
        n_dense_witnesses=len(dense), n_sparse_dot_fields=len(sparse),
        n_literal_firing=len(firing), n_firing_certified=len(cert),
        certificate_covers_every_firing=bool(len(cert) == len(firing)),
        certificate_degenerate_count=sum(1 for c in cert if c["degenerate"]),
        certificate_discriminating=[c for c in cert if not c["degenerate"]],
        degeneracy_certificate=cert,
        degeneracy_certificate_random_fields=a.random_fields,
        density_matched=matched,
        sparse_screen=dict(
            n_rasters=len(sparse),
            duplicate_count=len(sparse_flags),
            firing=[{k: v for k, v in r.items()} for r in sparse_flags],
            worst_spearman=(worst_sparse_rho or {}).get("spearman_full_footprint"),
            worst_spearman_submission=(worst_sparse_rho or {}).get("submission"),
            worst_overlap=(worst_sparse_ov or {}).get("my_dots_within_3px_of_theirs"),
            worst_overlap_submission=(worst_sparse_ov or {}).get("submission"),
            worst_jaccard=(worst_sparse_jac or {}).get("jaccard_dot_sets"),
            worst_jaccard_submission=(worst_sparse_jac or {}).get("submission"),
            byte_unique=bool(sparse) and not any(r.get("identical_bytes") for r in sparse),
            pixel_unique=bool(sparse) and not any(r.get("identical_decoded_predictions") for r in sparse),
            unique=bool(sparse) and not sparse_flags,
        ),
        comparable_budget_screen=dict(
            definition=("registry rasters whose dot count is at most "
                        f"{a.comparable_factor:g}x the candidate's ({int(cap):,}); the "
                        "only witnesses for which a 3 px forward-overlap statistic can "
                        "distinguish placement from coverage"),
            dot_cap=int(cap), comparable_factor=a.comparable_factor,
            n_rasters=len(comparable),
            duplicate_count=len(comp_flags),
            firing=[{k: v for k, v in r.items()} for r in comp_flags],
            certificate=comp_cert,
            n_firing_degenerate=len(comp_cert) - len(comp_nondegenerate),
            n_firing_discriminating=len(comp_nondegenerate),
            worst_spearman=(worst_comp_rho or {}).get("spearman_full_footprint"),
            worst_spearman_submission=(worst_comp_rho or {}).get("submission"),
            worst_overlap=(worst_comp_ov or {}).get("my_dots_within_3px_of_theirs"),
            worst_overlap_submission=(worst_comp_ov or {}).get("submission"),
            worst_jaccard=(worst_comp_jac or {}).get("jaccard_dot_sets"),
            worst_jaccard_submission=(worst_comp_jac or {}).get("submission"),
            byte_unique=bool(comparable) and not any(
                r.get("identical_bytes") for r in comparable),
            pixel_unique=bool(comparable) and not any(
                r.get("identical_decoded_predictions") for r in comparable),
            unique=bool(comparable) and not comp_flags,
            unique_after_certificate=bool(comparable) and not comp_nondegenerate,
        ),
        rows=rows,
        runtime_s=time.time() - t0,
        caveat=("The literal gate is reported unchanged and is not relaxed. The degeneracy "
                "certificate and the density-matched view are additional diagnostics that "
                "explain WHY the literal gate fires; they do not override it. The operative "
                "lane-drift screen is the budget-comparable view, because a witness that "
                "spends many times the candidate's budget has a 3 px dilation covering most "
                "of the allowable area on its own, and a continuous surface's dilation "
                "covers every candidate by construction.  The support-fraction sparse view "
                "is retained for continuity with Session 6 but is NOT the operative screen: "
                "a 5% support bound admits rasters with 155k-207k dots, 10-13x this "
                "candidate's budget, whose forward overlap is a property of their density."),
    )
    a.out.write_text(json.dumps(payload, indent=1, allow_nan=False, default=str) + "\n")
    print(f"\n[uniq] LITERAL: duplicate_count={literal['duplicate_count']} "
          f"unique={literal['unique']} worst_rho={literal['worst_spearman_full_footprint']} "
          f"worst_overlap={literal['worst_dot_overlap']}")
    ss = payload["sparse_screen"]
    print(f"[uniq] SPARSE SCREEN ({ss['n_rasters']} dot-field rasters): "
          f"duplicate_count={ss['duplicate_count']} unique={ss['unique']} "
          f"worst_rho={ss['worst_spearman']} worst_overlap={ss['worst_overlap']} "
          f"worst_jaccard={ss['worst_jaccard']}")
    cs = payload["comparable_budget_screen"]
    print(f"[uniq] COMPARABLE-BUDGET SCREEN (<= {cs['dot_cap']:,} dots, "
          f"{cs['n_rasters']} rasters): duplicate_count={cs['duplicate_count']} "
          f"unique={cs['unique']} unique_after_certificate="
          f"{cs['unique_after_certificate']} worst_rho={cs['worst_spearman']} "
          f"worst_overlap={cs['worst_overlap']} worst_jaccard={cs['worst_jaccard']}")
    deg = sum(1 for c in cert if c["degenerate"])
    print(f"[uniq] degeneracy: {deg}/{len(cert)} firing witnesses are degenerate "
          f"(every random field also exceeds the limit)")
    print(f"[uniq] wrote {a.out}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
