"""The docs renderer must consume, not overwrite, the authoritative run card."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# The script is not a package module; add its directory to the import path.
sys.path.insert(0, str(ROOT / "scripts"))
import build_site


def test_runcard_renderer_does_not_overwrite_negative_source_of_truth():
    path = ROOT / "evidence" / "run_card.json"
    before = path.read_text()
    card = json.loads(before)
    body = build_site.build_runcard({}, {}, {})
    after = path.read_text()

    assert after == before
    assert card["verdict"] == "negative"
    assert card["promote"] is False
    assert "NEGATIVE / DO NOT SUBMIT" in body
    assert "ORGANIZER-CONFIRMED" in body
