#!/usr/bin/env bash
# Download and verify the official DrivenData GEMS competition 306 data.
#
# Two routes, in order of preference:
#   1. The official competition data page (requires a DrivenData login):
#        https://www.drivendata.org/competitions/306/competition-doe-gems/data/
#      Download labels.tif, existing_faults.tif, sample_submission.tif and
#      training_features.tif into data/official/ by hand, then run
#        python scripts/prepare_data.py
#      to verify every sha256 pin.
#   2. The provenance bridge (no login): the public GEMSDOE sibling repositories
#      carry the official files with recorded hashes. From a network that can
#      reach raw.githubusercontent.com:
#        python scripts/prepare_data.py --fetch
#
# The Dropbox mirrors linked from the data page are NOT used (unreachable from
# the research sandbox; see data/README.md).
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/prepare_data.py "$@"
