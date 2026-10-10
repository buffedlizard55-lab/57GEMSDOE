"""Fault-zone anatomy lane: secondary-strand intensity around known faults.

Mechanics (no hard-coded textbook angles anywhere in this module):

* The public catalogue raster is a set of short dashed fragments, not whole
  traces, so fragments are first linked into fault *segments* (traces) by
  endpoint proximity + strike compatibility (union-find).  Segment length is
  the displacement proxy of Savage & Brodsky (JGR 2011): damage-zone width
  grows with displacement, which grows with fault length.
* For every pixel we compute, from the VISIBLE faults only:
    d(p)   Euclidean distance to the nearest visible fault pixel (EDT),
    phi(p) azimuth of the offset from the nearest visible pixel to p
           (0 deg = along strike, 90 deg = perpendicular offset),
    u(p)   along-strike position of p relative to the nearest visible
           segment, normalised by that segment's length (<0 or >1 = beyond
           a tip, i.e. along-strike extension rather than parallel strand),
    L*(p)  length of the nearest visible segment (displacement proxy),
    sense  recorded sense of slip of the nearest visible segment where the
           INGENIOUS database has it (RL / LL / N), else "unk".
* The intensity  I(p) = w(L*) * f(d) * g(phi) * h(u)  is FITTED on the
  hide-and-recover holdout: f, g, h, w are empirical distributions of the
  withheld segments measured against their nearest VISIBLE fault.  Nothing
  is set to a Riedel/Tchalenko angle by hand; whatever the withheld data
  shows is what is kept (ablation-tested factor by factor).

All functions take an explicit ``visible`` mask so the holdout can recompute
every feature from visible faults only.
"""
from __future__ import annotations

from collections import Counter

import numpy as np
from scipy import ndimage

# ---------------------------------------------------------------- linking ---

def _principal_axis(dy: np.ndarray, dx: np.ndarray):
    """Unit principal axis of centred (dy, dx) point sets (2x2 covariance)."""
    if dy.size < 2:
        return None
    c = np.array([[np.dot(dy, dy), np.dot(dy, dx)],
                  [np.dot(dy, dx), np.dot(dx, dx)]], dtype=np.float64)
    w, vec = np.linalg.eigh(c)
    v = vec[:, int(np.argmax(w))]
    n = np.linalg.norm(v)
    return v / n if n > 0 else None


def _fragment_stats(mask: np.ndarray):
    """8-connected fragments of ``mask`` with principal-axis geometry."""
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), dtype=bool))
    if n == 0:
        return lab, n, {}
    ys, xs = np.nonzero(lab)
    ids = lab[ys, xs]
    order = np.argsort(ids, kind="stable")
    ys, xs, ids = ys[order], xs[order], ids[order]
    starts = np.searchsorted(ids, np.arange(1, n + 1))
    ends = np.append(starts[1:], ids.size)
    stats = {}
    for k in range(n):
        yy = ys[starts[k]:ends[k]].astype(np.float64)
        xx = xs[starts[k]:ends[k]].astype(np.float64)
        cy, cx = yy.mean(), xx.mean()
        v = _principal_axis(yy - cy, xx - cx)
        if v is None:
            v = np.array([1.0, 0.0])
        proj = v[0] * (yy - cy) + v[1] * (xx - cx)
        # orient so the axis points "north-east-ish" (deterministic sign)
        if v[0] < 0 or (v[0] == 0 and v[1] < 0):
            v = -v
            proj = -proj
        strike = float(np.degrees(np.arctan2(v[1], v[0]))) % 180.0
        p0 = np.array([cy + v[0] * proj.min(), cx + v[1] * proj.min()])
        p1 = np.array([cy + v[0] * proj.max(), cx + v[1] * proj.max()])
        stats[k + 1] = dict(
            size=int(yy.size), length_px=float(proj.max() - proj.min()),
            strike=strike, axis=v, centroid=np.array([cy, cx]),
            p0=p0, p1=p1,
        )
    return lab, n, stats


def _strike_diff(a: float, b: float) -> float:
    """Absolute strike difference on the 180-degree circle."""
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def link_segments(mask: np.ndarray, max_gap_px: float = 4.0,
                  max_dstrike_deg: float = 30.0,
                  max_link_angle_deg: float = 45.0) -> tuple[np.ndarray, dict]:
    """Link catalogue fragments into fault segments (traces).

    Two fragments link when an endpoint pair is within ``max_gap_px``, their
    strikes agree within ``max_dstrike_deg``, and the link direction is
    within ``max_link_angle_deg`` of the strike (end-to-end, not side-by-side).
    Returns a per-pixel segment label map (0 = no fault) and per-segment stats.
    """
    lab, n, st = _fragment_stats(mask)
    if n == 0:
        return lab, {}
    parent = np.arange(n + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    ends = {k: (st[k]["p0"], st[k]["p1"]) for k in range(1, n + 1)}
    # bucket endpoints on a coarse grid for a cheap neighbour search
    cell = max(max_gap_px * 2.0, 8.0)
    buckets: dict[tuple[int, int], list[int]] = {}
    for k in range(1, n + 1):
        for p in ends[k]:
            buckets.setdefault((int(p[0] // cell), int(p[1] // cell)), []).append(k)
    for k in range(1, n + 1):
        p0, p1 = ends[k]
        for p in (p0, p1):
            bi, bj = int(p[0] // cell), int(p[1] // cell)
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    for m in buckets.get((bi + di, bj + dj), ()):
                        if m <= k:
                            continue
                        q0, q1 = ends[m]
                        gap = min(np.linalg.norm(p - q0), np.linalg.norm(p - q1))
                        if gap > max_gap_px:
                            continue
                        if _strike_diff(st[k]["strike"], st[m]["strike"]) > max_dstrike_deg:
                            continue
                        # link direction must be along-strike-ish
                        other = q0 if np.linalg.norm(p - q0) <= np.linalg.norm(p - q1) else q1
                        link = other - p
                        ln = np.linalg.norm(link)
                        if ln < 1e-9:
                            union(k, m)
                            continue
                        ang = np.degrees(np.arccos(np.clip(
                            abs(float(link @ st[k]["axis"])) / ln, -1.0, 1.0)))
                        if ang <= max_link_angle_deg:
                            union(k, m)

    roots = np.array([find(k) for k in range(n + 1)])
    uniq = np.unique(roots[1:])
    remap = np.zeros(n + 1, dtype=np.int32)
    remap[uniq] = np.arange(1, uniq.size + 1)
    seg_lab = remap[roots[lab]].astype(np.int32, copy=False)

    seg_stats = {}
    pix_lists = segment_pixel_lists(seg_lab, uniq.size)
    for sid in range(1, uniq.size + 1):
        members = uniq[sid - 1]
        frag_ids = np.flatnonzero(roots[1:] == members) + 1
        ys, xs = pix_lists[sid - 1]
        yy = ys.astype(np.float64); xx = xs.astype(np.float64)
        cy, cx = yy.mean(), xx.mean()
        v = _principal_axis(yy - cy, xx - cx)
        if v is None:
            v = np.array([1.0, 0.0])
        if v[0] < 0 or (v[0] == 0 and v[1] < 0):
            v = -v
        proj = v[0] * (yy - cy) + v[1] * (xx - cx)
        # total length: sum of fragment spans (fragments are dashed pieces of one trace)
        total_len = float(sum(st[f]["length_px"] for f in frag_ids))
        seg_stats[sid] = dict(
            size=int(yy.size),
            length_px=total_len,
            span_px=float(proj.max() - proj.min()),
            strike=float(np.degrees(np.arctan2(v[1], v[0]))) % 180.0,
            axis=v,
            centroid=np.array([cy, cx]),
            p0=np.array([cy + v[0] * proj.min(), cx + v[1] * proj.min()]),
            p1=np.array([cy + v[0] * proj.max(), cx + v[1] * proj.max()]),
            n_fragments=int(frag_ids.size),
        )
    return seg_lab, seg_stats


# ------------------------------------------------------- per-pixel features ---

def pixel_features(visible: np.ndarray, seg_lab: np.ndarray,
                   seg_stats: dict) -> dict[str, np.ndarray]:
    """Per-pixel geometry from the visible fault mask and its segments.

    Returns d (px to nearest visible pixel), seg_id of nearest visible
    segment (0 = none), phi (deg, azimuth of the offset from the nearest
    visible pixel, 0 = along +strike reference of that segment's axis),
    u (along-strike position normalised by segment length; <0/>1 = beyond a
    tip), L (nearest segment length in px).
    """
    d, (iy, ix) = ndimage.distance_transform_edt(~visible, return_indices=True)
    seg_at_nearest = seg_lab[iy, ix]
    seg_at_nearest[~visible[iy, ix]] = 0
    # azimuth of offset from nearest visible pixel to p
    dy = np.arange(visible.shape[0])[:, None] - iy
    dx = np.arange(visible.shape[1])[None, :] - ix
    has = visible.any()
    out = dict(d=d, seg_id=seg_at_nearest)
    if not has or not seg_stats:
        out.update(phi=np.zeros_like(d), u=np.full_like(d, np.nan),
                   L=np.zeros_like(d))
        return out
    phi = np.full(d.shape, np.nan)
    u = np.full(d.shape, np.nan)
    L = np.zeros(d.shape)
    on = visible
    for sid, s in seg_stats.items():
        sel = seg_at_nearest == sid
        if not sel.any():
            continue
        v = s["axis"]
        # phi: angle of (p - nearest) relative to the segment strike axis
        az = np.degrees(np.arctan2(dx[sel], dy[sel])) % 180.0
        st = s["strike"]
        rel = (az - st) % 180.0
        rel = np.minimum(rel, 180.0 - rel)      # 0 = along strike, 90 = across
        phi[sel] = rel
        # u: projection of (p - centroid) on the axis, normalised by span
        span = max(s["span_px"], 1e-9)
        proj = v[0] * (np.nonzero(sel)[0] - s["centroid"][0]) + \
               v[1] * (np.nonzero(sel)[1] - s["centroid"][1])
        mid = 0.0  # centroid is the origin of proj
        u[sel] = (proj - mid) / span + 0.5     # 0..1 inside the segment
        L[sel] = s["length_px"]
    out.update(phi=phi, u=u, L=L)
    out["_on_fault"] = on
    return out


# ------------------------------------------------------------- sense of slip ---

def rasterize_traces(csv_path, shape, transform) -> tuple[np.ndarray, "object"]:
    """Rasterize INGENIOUS UTM-11 trace segments; return mask + dataframe."""
    import pandas as pd
    tr = pd.read_csv(csv_path)
    inv = ~transform
    H, W = shape
    mask = np.zeros((H, W), bool)
    # ``Affine * (x, y)`` returns (col, row), NOT (row, col).  Named accordingly.
    # (IR-57-TRANS-01: the earlier version swapped the two and rasterised traces
    # transposed -- 1.8 % of catalogue cells near its traces instead of 100 %.)
    c0, r0 = (inv * (tr.x0.values, tr.y0.values))
    c1, r1 = (inv * (tr.x1.values, tr.y1.values))
    r0 = np.asarray(r0).astype(int); c0 = np.asarray(c0).astype(int)
    r1 = np.asarray(r1).astype(int); c1 = np.asarray(c1).astype(int)
    for a, b, cc, d in zip(c0, r0, c1, r1):
        npts = max(abs(b - a), abs(d - cc)) + 1
        rr = np.linspace(b, d, npts).astype(int)     # rows
        ccc = np.linspace(a, cc, npts).astype(int)   # cols
        ok = (rr >= 0) & (rr < H) & (ccc >= 0) & (ccc < W)
        mask[rr[ok], ccc[ok]] = True
    return mask, tr


SENSE_CODE = {"N": 1, "RL": 2, "LL": 3}   # 0 = no recorded sense (or no trace)


def trace_sense_raster(csv_path, shape, transform) -> np.ndarray:
    """int8 raster of recorded sense of slip on the INGENIOUS trace grid.

    0 = no trace / no recorded sense, 1 = N (normal), 2 = RL, 3 = LL.  Built from
    the ``sense`` column of ``data/external/trace_segments_utm11.csv`` (1,126
    records; RL 87, LL 76, N 868, blank 95 -- the strike-slip records are the
    ones the sense-of-slip feature needs).  Same convention as
    ``rasterize_traces`` (``Affine * (x, y)`` -> (col, row)).
    """
    import pandas as pd
    tr = pd.read_csv(csv_path)
    inv = ~transform
    H, W = shape
    out = np.zeros((H, W), np.int8)
    c0, r0 = (inv * (tr.x0.values, tr.y0.values))
    c1, r1 = (inv * (tr.x1.values, tr.y1.values))
    codes = tr["sense"].map(SENSE_CODE).fillna(0).astype(np.int8).values
    for a, b, cc, d, code in zip(np.asarray(c0).astype(np.int64), np.asarray(r0).astype(np.int64),
                                 np.asarray(c1).astype(np.int64), np.asarray(r1).astype(np.int64),
                                 codes):
        if code == 0:
            continue
        npts = max(abs(b - d), abs(a - cc)) + 1
        rr = np.linspace(b, d, npts).astype(np.int64)
        ccc = np.linspace(a, cc, npts).astype(np.int64)
        ok = (rr >= 0) & (rr < H) & (ccc >= 0) & (ccc < W)
        out[rr[ok], ccc[ok]] = code
    return out


SENSE_CLASSES = ("RL", "LL", "N", "unk")


def ingenious_record_segments(csv_path, shape, transform):
    """INGENIOUS vector traces grouped by record into fault segments.

    Each record is one named fault (zone): real vector geometry, so length,
    strike and recorded sense of slip (RL/LL/N) come straight from the
    database -- no raster fragmentation, no join needed.  Returns
    (seg_lab, seg_stats, trace_id_map, trace_sense) where seg_lab holds
    record-segment ids offset by ``base_id``.
    """
    import pandas as pd
    tr = pd.read_csv(csv_path)
    inv = ~transform
    H, W = shape
    tmap = np.zeros((H, W), dtype=np.int32)
    c0, r0 = (inv @ (tr.x0.values, tr.y0.values))   # (col, row), see rasterize_traces
    c1, r1 = (inv @ (tr.x1.values, tr.y1.values))
    pix_rows = []
    for i, (a, b, cc, d) in enumerate(zip(np.asarray(c0).astype(np.int64), np.asarray(r0).astype(np.int64),
                                         np.asarray(c1).astype(np.int64), np.asarray(r1).astype(np.int64)),
                                       start=1):
        npts = max(abs(b - a), abs(d - cc)) + 1
        rr = np.linspace(b, d, npts).astype(np.int64)    # rows
        ccc = np.linspace(a, cc, npts).astype(np.int64)  # cols
        ok = (rr >= 0) & (rr < H) & (ccc >= 0) & (ccc < W)
        rr = rr[ok]; ccc = ccc[ok]
        tmap[rr, ccc] = i
        pix_rows.append((rr.astype(np.int32), ccc.astype(np.int32)))
    trace_sense = np.array(["unk"] + [str(s) for s in tr.sense], dtype=object)
    rec_ids = tr.record_id.values
    uniq = pd.unique(rec_ids)
    seg_stats = {}
    seg_pix = {}
    for new_id, rec in enumerate(uniq, start=1):
        rows = np.flatnonzero(rec_ids == rec)
        ys = np.concatenate([pix_rows[r - 1][0] for r in rows])
        xs = np.concatenate([pix_rows[r - 1][1] for r in rows])
        yy = ys.astype(np.float64); xx = xs.astype(np.float64)
        cy, cx = yy.mean(), xx.mean()
        v = _principal_axis(yy - cy, xx - cx)
        if v is None:
            v = np.array([1.0, 0.0])
        if v[0] < 0 or (v[0] == 0 and v[1] < 0):
            v = -v
        proj = v[0] * (yy - cy) + v[1] * (xx - cx)
        # vector length: sum of polyline segment lengths (metres/100 = px)
        x0 = tr.x0.values[rows]; y0 = tr.y0.values[rows]
        x1 = tr.x1.values[rows]; y1 = tr.y1.values[rows]
        vec_len_px = float(np.sum(np.hypot(x1 - x0, y1 - y0)) / 100.0)
        senses = [str(trace_sense[r]) for r in rows]
        sense = Counter(senses).most_common(1)[0][0]
        seg_stats[new_id] = dict(
            size=int(yy.size), length_px=vec_len_px,
            span_px=float(proj.max() - proj.min()),
            strike=float(np.degrees(np.arctan2(v[1], v[0]))) % 180.0,
            axis=v, centroid=np.array([cy, cx]),
            p0=np.array([cy + v[0] * proj.min(), cx + v[1] * proj.min()]),
            p1=np.array([cy + v[0] * proj.max(), cx + v[1] * proj.max()]),
            n_fragments=int(rows.size), sense=sense if sense in SENSE_CLASSES else "unk",
            name=str(tr.NAME.iloc[rows[0]]) if "NAME" in tr.columns else "",
        )
        seg_pix[new_id] = (ys, xs)
    return seg_stats, seg_pix, tmap, trace_sense


def segment_pixel_lists(seg_lab: np.ndarray, n_seg: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Per-segment (ys, xs) index arrays, computed once (O(pixels log pixels))."""
    ys, xs = np.nonzero(seg_lab)
    ids = seg_lab[ys, xs]
    order = np.argsort(ids, kind="stable")
    ys, xs, ids = ys[order], xs[order], ids[order]
    starts = np.searchsorted(ids, np.arange(1, n_seg + 1))
    ends = np.append(starts[1:], ids.size)
    return [(ys[starts[k]:ends[k]], xs[starts[k]:ends[k]]) for k in range(n_seg)]


def nearest_segment_features(visible: np.ndarray, seg_lab: np.ndarray,
                             seg_stats: dict) -> dict[str, np.ndarray]:
    """Per-pixel geometry vs the nearest visible fault pixel/segment.

    d      distance (px) to nearest visible fault pixel
    seg_id id of the nearest visible segment (0 = none)
    phi    azimuth of the offset relative to that segment's strike
           (0 = along strike, 90 = across strike), NaN where no segment
    u      along-strike position vs that segment (0..1 inside, <0/>1 beyond tip)
    L      length (px) of that segment (displacement proxy)
    """
    d, (iy, ix) = ndimage.distance_transform_edt(~visible, return_indices=True)
    seg_near = seg_lab[iy, ix].astype(np.int64)
    seg_near[~visible[iy, ix]] = 0
    H, W = visible.shape
    yy = np.arange(H)[:, None]
    xx = np.arange(W)[None, :]
    dy = yy - iy
    dx = xx - ix
    az = np.degrees(np.arctan2(dx, dy)) % 180.0
    # lookup tables indexed by segment id (vectorised gather, no per-segment loop)
    max_id = max(seg_stats) if seg_stats else 0
    strike_of = np.zeros(max_id + 1)
    vy_of = np.zeros(max_id + 1); vx_of = np.zeros(max_id + 1)
    cy_of = np.zeros(max_id + 1); cx_of = np.zeros(max_id + 1)
    span_of = np.ones(max_id + 1)
    len_of = np.zeros(max_id + 1)
    for sid, s in seg_stats.items():
        strike_of[sid] = s["strike"]
        vy_of[sid], vx_of[sid] = float(s["axis"][0]), float(s["axis"][1])
        cy_of[sid], cx_of[sid] = float(s["centroid"][0]), float(s["centroid"][1])
        span_of[sid] = max(s["span_px"], 1e-9)
        len_of[sid] = s["length_px"]
    has = seg_near > 0
    phi = np.full(d.shape, np.nan)
    u = np.full(d.shape, np.nan)
    L = np.zeros(d.shape)
    if has.any():
        sy, sx = np.nonzero(has)
        sn = seg_near[sy, sx]
        rel = (az[sy, sx] - strike_of[sn]) % 180.0
        phi[sy, sx] = np.minimum(rel, 180.0 - rel)
        proj = vy_of[sn] * (sy - cy_of[sn]) + vx_of[sn] * (sx - cx_of[sn])
        u[sy, sx] = proj / span_of[sn] + 0.5
        L[sy, sx] = len_of[sn]
    return dict(d=d, seg_id=seg_near, phi=phi, u=u, L=L, on=visible.copy())
