#!/usr/bin/env python
"""Verify (and, where reachable, fetch) every pinned data file.

Usage:
    python scripts/prepare_data.py            # verify only (default)
    python scripts/prepare_data.py --fetch    # also download missing files

Pins live in data/README.md (and are duplicated in PIN below). The DrivenData
data page requires a login and the Dropbox mirrors are unreachable from this
sandbox, so --fetch pulls the official files from the sha256-pinned public
GEMSDOE sibling repositories (the provenance bridge documented in
data/README.md). training_features.tif (419 MB) is fetched from the same
bridge; it is gitignored and never committed.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Required pins: committed to git, must verify in every environment.
PIN = {
    "data/official/labels.tif":
        "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "data/official/existing_faults.tif":
        "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "data/official/sample_submission.tif":
        "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    "data/external/sgmc_faults_100m.tif":
        "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
    "data/external/derived_sgmc_faults_100m.tif":
        "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
    "data/external/trace_segments_utm11.csv":
        "c5edf9df3e0e1413c52784884fc38e5b9ca54627b27c6f8baf7713e908f48513",
    "data/external/qfault_attributes.csv":
        "3b8745f0086a57b8255f6679afa1bf1168c10b5573491666c75cf53217029507",
}

# Optional pins: gitignored, fetched on demand with --fetch (IR-57-DATA-01).
# A missing optional pin is reported as SKIP, never as a failure: the 419 MB
# feature stack cannot be committed and the sandbox has no DrivenData auth.
OPTIONAL_PIN = {
    "data/official/training_features.tif":
        "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
}

# Provenance bridge: public sibling repositories that carry the official files
# with recorded hashes (see data/README.md). Tried in order.
BRIDGE_RAW = [
    "https://raw.githubusercontent.com/buffedlizard55-lab/6GEMSDOE/main/{path}",
    "https://raw.githubusercontent.com/buffedlizard55-lab/GEMSDOE52/main/{path}",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _check(rel: str, want: str, fetch: bool, required: bool) -> bool:
    p = ROOT / rel
    if not p.exists():
        if fetch:
            p.parent.mkdir(parents=True, exist_ok=True)
            got = False
            for tpl in BRIDGE_RAW:
                url = tpl.format(path=rel)
                r = subprocess.run(["curl", "-fsSL", "-o", str(p), url],
                                   capture_output=True, text=True)
                if r.returncode == 0 and p.exists() and sha256(p) == want:
                    print(f"[data] fetched  {rel}  (sha256 OK)")
                    got = True
                    break
                p.unlink(missing_ok=True)
            if not got:
                print(f"[data] MISSING  {rel}  (fetch failed — see data/README.md)")
                return False
            return True
        if required:
            print(f"[data] MISSING  {rel}  (run with --fetch; see data/README.md)")
            return False
        print(f"[data] SKIP   {rel}  (optional, gitignored; fetch with --fetch)")
        return True
    got = sha256(p)
    status = "OK " if got == want else "BAD"
    if got != want:
        return False
    print(f"[data] {status}  {rel}  {got[:16]}…")
    return True


def main() -> int:
    fetch = "--fetch" in sys.argv
    ok = True
    n_skip = 0
    for rel, want in PIN.items():
        ok &= _check(rel, want, fetch, required=True)
    for rel, want in OPTIONAL_PIN.items():
        ok &= _check(rel, want, fetch, required=False)
        # a SKIP is not a failure; count it for the summary line
        if not (ROOT / rel).exists() and not fetch:
            n_skip += 1
    if ok:
        extra = f"  ({n_skip} optional pin skipped)" if n_skip else ""
        print(f"[data] ALL PINS VERIFIED{extra}")
    else:
        print("[data] PIN CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
