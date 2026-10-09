"""Every committed data file must match its sha256 pin in data/README.md."""
import hashlib
import subprocess
import sys

from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    not (ROOT / "data" / "official" / "training_features.tif").exists(),
    reason="the 419 MB training_features.tif is gitignored and not present in this checkout",
)
def test_prepare_data_verifies_all_pins():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prepare_data.py")],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ALL PINS VERIFIED" in r.stdout


def test_prepare_data_explicitly_reports_missing_gitignored_training_features():
    training = ROOT / "data" / "official" / "training_features.tif"
    if training.exists():
        pytest.skip("training features are present; the full-pin test covers this case")
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prepare_data.py")],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 1
    assert "MISSING  data/official/training_features.tif" in r.stdout
    assert "PIN CHECK FAILED" in r.stdout
    assert "BAD" not in r.stdout


def test_labels_and_existing_faults_are_byte_identical():
    def sha(p):
        h = hashlib.sha256()
        h.update(Path(p).read_bytes())
        return h.hexdigest()
    a = ROOT / "data" / "official" / "labels.tif"
    b = ROOT / "data" / "official" / "existing_faults.tif"
    assert sha(a) == sha(b) == \
        "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
