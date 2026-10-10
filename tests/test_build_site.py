from __future__ import annotations

import json

from scripts import build_site, build_submission


def test_h57b_run_card_loader_is_read_only(tmp_path):
    card_path = tmp_path / "evidence" / "run_card.json"
    card_path.parent.mkdir()
    card = {"artifact": {"download_status": "NOT CLEARED", "raster_generated": False}}
    original = json.dumps(card, indent=2).encode()
    card_path.write_bytes(original)

    loaded = build_site.load_h57b_run_card(tmp_path)

    assert loaded == card
    assert card_path.read_bytes() == original


def test_held_card_has_no_research_download_link():
    rendered = build_site.download_panel({
        "okay_to_download": False,
        "okay_to_submit": False,
        "download_status": "NOT CLEARED",
    })

    assert "NOT CLEARED" in rendered
    assert "Submit: NO" in rendered
    assert 'href="downloads/' not in rendered
    assert "Download: NOT CLEARED" in rendered


def test_legacy_submission_builder_returns_refusal(capsys):
    assert build_submission.main() == 2
    assert "Retired unsafe builder" in capsys.readouterr().err
