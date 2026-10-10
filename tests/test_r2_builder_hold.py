"""The historical R2 builder must honor the current universal HOLD."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_historical_r2_builder_fails_closed_before_generating_tiff(capsys):
    certificate = json.loads(
        (ROOT / "evidence/uniqueness_saturation_certificate.json").read_text()
    )
    assert certificate["universal_overlap_blocker"] is True

    spec = importlib.util.spec_from_file_location(
        "build_r2_submission", ROOT / "scripts/build_r2_submission.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    before = set((ROOT / "docs/downloads/archive").glob("gems57-h57r2-*.tif"))
    assert module.main() == 2
    stderr = capsys.readouterr().err
    assert "no-output stub" in stderr
    assert "HOLD — NOT OK TO DOWNLOAD OR SUBMIT" in stderr
    assert "no fit, download, placement, or file write" in stderr
    after = set((ROOT / "docs/downloads/archive").glob("gems57-h57r2-*.tif"))
    assert after == before
