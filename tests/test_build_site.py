from __future__ import annotations

import json

import pytest

from scripts import build_site, build_submission


def test_run_card_renderer_is_read_only(tmp_path, monkeypatch):
    card_path = tmp_path / "run_card.json"
    card = {
        "artifact": {
            "submission_status": "NOT SUBMITTED",
            "download_status": "NOT CLEARED — no new TIF generated",
            "raster_generated": False,
        },
        "holdout": {},
    }
    original = json.dumps(card, indent=2).encode()
    card_path.write_bytes(original)
    monkeypatch.setattr(build_site, "EVID", tmp_path)

    rendered = build_site.build_runcard()

    assert "NOT SUBMITTED" in rendered
    assert "does not regenerate or modify it" in rendered
    assert card_path.read_bytes() == original


def test_cleared_card_without_download_path_fails_closed(tmp_path, monkeypatch):
    (tmp_path / "run_card.json").write_text(json.dumps({
        "artifact": {"download_status": "CLEARED TO DOWNLOAD"},
    }))
    monkeypatch.setattr(build_site, "EVID", tmp_path)

    rendered = build_site.submission_status_html()

    assert "NOT CLEARED" in rendered
    assert "no validated download path is recorded" in rendered
    assert 'href="' not in rendered
    assert "do not submit" in rendered.lower()


def test_legacy_submission_builder_is_disabled():
    with pytest.raises(SystemExit, match="Disabled"):
        build_submission.main()
