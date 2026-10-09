#!/usr/bin/env python3
"""Retired unsafe builder: do not revive oracle budgets or place before a gate.

The former implementation trained/scored in-sample, used test truth count for
allocation and consulted only 15 priors after placing/writing production dots.
It cannot produce a cleared submission under the current standing protocol.
The replacement reuses shared evaluate_holdout/submission_writer:

  python scripts/run_orientation_experiments.py --build-research-surface --minutes 65

That command repeats the declared research experiments; it never selects or
spends a real slot. Current release: download OK, submission HOLD.
"""
import sys


def main():
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
