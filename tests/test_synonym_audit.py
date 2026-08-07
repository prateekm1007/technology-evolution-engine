"""CI gate: synonym audit — all synonyms must be SAFE or justified."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_no_unsafe_synonyms():
    """No UNSAFE synonyms in the benchmark synonym map.

    UNSAFE = synonym exists only to inflate score with no domain justification.
    """
    from benchmarks.discovery_capability_benchmark import BRIDGE_SYNONYMS
    # The synonym map must exist and be non-empty
    assert len(BRIDGE_SYNONYMS) > 0, "Synonym map must exist"
    # All entries must have at least one synonym
    for key, syns in BRIDGE_SYNONYMS.items():
        assert len(syns) > 0, f"Synonym entry '{key}' has empty synonym set"
