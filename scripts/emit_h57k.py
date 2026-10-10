#!/usr/bin/env python3
"""Retired H57-K emitter; retained only to fail closed for legacy invocations.

The historical emitter used a live-anchored allocation, skipped the required
pre-placement surface check, and reported alternate Jaccard/blind-forward
screens that are not part of the literal protocol. Its artifacts and receipts
remain available for audit, but this entry point must not create another file.
The current fault-zone-anatomy review is HOLD; there is no cleared raster.
"""


def main() -> None:
    raise SystemExit(
        "H57-K emission is retired: no TIFF was generated or cleared. "
        "Use the archived evidence only; do not select or submit a slot."
    )


if __name__ == "__main__":
    main()
