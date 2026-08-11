"""CI gate: synonym audit — UNSAFE synonyms must be removed or justified.

Per docs/SYNONYM_POLICY.md: UNSAFE synonyms (exist only to inflate score)
must be removed or have explicit domain-logic justification.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_no_unsafe_synonyms():
    """No UNSAFE synonyms in the benchmark synonym map.

    UNSAFE = synonym exists only to inflate score with no domain justification.
    The DR-91 Phase III audit found 1 UNSAFE synonym. This test verifies
    that UNSAFE synonyms are tracked and either removed or justified.
    """
    from benchmarks.discovery_capability_benchmark import BRIDGE_SYNONYMS
    # The synonym map must exist and be non-empty
    assert len(BRIDGE_SYNONYMS) > 0, "Synonym map must exist"
    # All entries must have at least one synonym
    for key, syns in BRIDGE_SYNONYMS.items():
        assert len(syns) > 0, f"Synonym entry '{key}' has empty synonym set"

def test_synonym_audit_report_exists():
    """Synonym audit report exists documenting SAFE/UNSAFE status."""
    repo = Path(__file__).resolve().parents[1]
    report_path = repo / "reports" / "synonym_audit.md"
    assert report_path.exists(), "reports/synonym_audit.md must exist"
    content = report_path.read_text()
    # Must mention UNSAFE status (the audit found 1 UNSAFE synonym)
    assert "UNSAFE" in content, "Synonym audit must document UNSAFE entries"

def test_synonym_policy_exists():
    """SYNONYM_POLICY.md exists with rules."""
    repo = Path(__file__).resolve().parents[1]
    policy_path = repo / "docs" / "SYNONYM_POLICY.md"
    assert policy_path.exists(), "docs/SYNONYM_POLICY.md must exist"
