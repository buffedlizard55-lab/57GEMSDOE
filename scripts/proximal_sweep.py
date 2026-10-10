#!/usr/bin/env python3
"""Archived H57-K proximal sweep — execution disabled.

The former sweep depended on an unverified owner-score-derived mass. Its rows
are historical MODEL-SURROGATE arithmetic only and cannot guide placement or
submission.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems57.emit import allocate_patient      # noqa: E402
from gems57.grid import load_grid             # noqa: E402

G = 14088.747191011289


def main() -> None:
    raise SystemExit(
        "STOP: archived proximal sweep disabled because its owner-score anchor was invalidated."
    )
    grid = load_grid()
    p = np.load(ROOT / "out/h57k_surface_f32.npy")
    p = np.where(np.isfinite(p), p, 0.0).astype(np.float32)
    dcat = distance_transform_edt(~grid.catalogue)
    base = grid.footprint & ~grid.catalogue
    rows = []
    for r in [2.0, 4.0, 6.0, 8.0, 12.0, 20.0]:
        allowed = base & (dcat > r)
        a = allocate_patient(p, allowed, k_truth=G, floor=0.0, max_dots=400_000,
                             candidate_cap=4_000_000, patience=100_000)
        d = dcat[a.emitted]
        rows.append(dict(proximal_exclude_px=r, allowed_cells=int(allowed.sum()),
                         n_dots=int(a.n_dots), surrogate_dti=float(a.surrogate_dti),
                         model_T=float(a.expected_covered_credit),
                         dcat_median=float(np.median(d)) if d.size else None,
                         dcat_p90=float(np.percentile(d, 90)) if d.size else None))
        print(f"exclude<={r:5.1f}px  dots={a.n_dots:7,d}  surrogate DTI={a.surrogate_dti:.4f}  "
              f"T={a.expected_covered_credit:8.1f}  dcat median="
              f"{np.median(d) if d.size else 0:5.1f} p90={np.percentile(d, 90) if d.size else 0:5.1f}",
              flush=True)
    (ROOT / "evidence" / "h57k_proximal_sweep.json").write_text(json.dumps(
        dict(schema="gems57.proximal-sweep.v1",
             note="MODEL-SURROGATE on the session-4 surface; not a score.",
             rows=rows), indent=1))


if __name__ == "__main__":
    main()
