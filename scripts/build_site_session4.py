#!/usr/bin/env python3
"""Retired historical site builder.

This generator advertised an uncertified historical raster as "OK TO DOWNLOAD
AND SUBMIT". It has no supported execution path; the current evidence-led site
is built only by ``scripts/build_site.py`` from ``run_card_current.json``.
"""

if __name__ == "__main__":
    raise SystemExit(
        "Historical site generator retired: it advertised an uncertified submission. "
        "Use scripts/build_site.py, which publishes the current negative card."
    )
