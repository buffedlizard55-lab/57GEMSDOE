#!/usr/bin/env python3
"""Retired unsafe session-4 publisher.

The original source is preserved at
``evidence/history/build_site_session4_legacy_2026-10-09.py`` for provenance.
It previously rewrote the current run card, restored a positive submission banner,
and emitted active download links from a partial registry. Use only
``scripts/build_site.py`` and ``scripts/check_site.py`` for the current HOLD-first
site.
"""
from __future__ import annotations


def main() -> int:
    raise SystemExit(
        "Retired: session-4 publisher could restore withdrawn OK-to-submit claims. "
        "Use scripts/build_site.py; no download or submission is cleared."
    )


if __name__ == "__main__":
    main()
