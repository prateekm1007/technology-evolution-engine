"""CI gate: historical recalibration documentation exists."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_measurement_history_exists():
    """MEASUREMENT_HISTORY.md exists documenting all historical scores."""
    repo = Path(__file__).resolve().parents[1]
    hist_path = repo / "docs" / "MEASUREMENT_HISTORY.md"
    assert hist_path.exists(), "MEASUREMENT_HISTORY.md must exist"
    content = hist_path.read_text()
    # Must mention key cycles
    assert "196" in content or "197" in content  # original benchmark
    assert "242" in content or "DR-91" in content  # audit
    assert "INVALID" in content or "invalid" in content  # scores marked invalid

def test_recalibration_status_documented():
    """MEASUREMENT_REASSESSMENT.md exists documenting recalibration status."""
    repo = Path(__file__).resolve().parents[1]
    reassess_path = repo / "docs" / "MEASUREMENT_REASSESSMENT.md"
    assert reassess_path.exists(), "MEASUREMENT_REASSESSMENT.md must exist"
    content = reassess_path.read_text()
    assert "NOT YET PERFORMED" in content or "INCOMPLETE" in content
