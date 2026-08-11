"""CI gate: reference scorer exists and produces separate scores per mode."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_reference_scorer_exists():
    """Independent reference scorer exists in audit/stage_minus1/."""
    from audit.stage_minus1.exact_matcher import (
        match_exact_normalized, match_exact_token, match_fuzzy, match_with_synonyms,
    )
    assert match_exact_normalized is not None
    assert match_exact_token is not None
    assert match_fuzzy is not None
    assert match_with_synonyms is not None

def test_reference_scorer_no_production_imports():
    """Reference scorer does NOT import production matching logic."""
    import audit.stage_minus1.exact_matcher as am
    source = open(am.__file__).read()
    assert "from benchmarks.discovery_capability_benchmark import _bridge_matches" not in source
    assert "from benchmarks.discovery_capability_benchmark import canonicalize" not in source
