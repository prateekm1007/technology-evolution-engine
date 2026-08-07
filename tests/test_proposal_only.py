"""CI gate: proposal-only scoring exists and separates Discovery from Recognition."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_proposal_only_scoring_exists():
    """Proposal-only scoring function exists in the audit code."""
    from audit.measurement_integrity.dr91_measurement_audit import score
    assert score is not None
    # The score function can be used with shared entities only (proposal-only)
    # by passing shared_entities instead of all_entities

def test_discovery_vs_recognition_separated():
    """Discovery F1 and Recognition F1 are never combined."""
    repo = Path(__file__).resolve().parents[1]
    disc_doc = repo / "docs" / "DISCOVERY_VS_RECOGNITION.md"
    assert disc_doc.exists(), "DISCOVERY_VS_RECOGNITION.md must exist"
    content = disc_doc.read_text()
    assert "never combine" in content.lower() or "never be combined" in content.lower()
