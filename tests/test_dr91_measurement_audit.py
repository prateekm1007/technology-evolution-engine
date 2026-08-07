"""Tests for DR-91 forensic measurement audit.

Enforces:
- Independent matchers (no production imports)
- 5 matching modes produce separate scores
- Discovery F1 ≠ Recognition F1 (never combined)
- FP floor measurement
- Verdict is one of TRUSTWORTHY / PARTIALLY TRUSTWORTHY / NOT TRUSTWORTHY
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


def test_dr91_imports():
    from audit.measurement_integrity.dr91_measurement_audit import (
        canon, m_exact, m_token, m_fuzzy, m_synonym, m_reference,
        score, explain_every_point, audit_synonyms, audit_gold_leakage,
        proposal_locus_audit, false_positive_audit,
    )
    assert m_exact is not None


def test_no_production_matching_imports():
    """DR-91: zero production matching logic imported."""
    import audit.measurement_integrity.dr91_measurement_audit as am
    source = open(am.__file__).read()
    assert "from benchmarks.discovery_capability_benchmark import _bridge_matches" not in source
    assert "from benchmarks.discovery_capability_benchmark import canonicalize" not in source


def test_five_matchers_exist():
    """Five independent matching modes exist."""
    from audit.measurement_integrity.dr91_measurement_audit import (
        m_exact, m_token, m_fuzzy, m_synonym, m_reference,
    )
    assert m_exact("thermal_emission", "thermal emission")
    assert m_token("thermal_emission", "thermal emissions")
    assert m_fuzzy("thermal_emission", "thermal_emissions")
    assert not m_reference("thermal_emission", "radiative_heat")


def test_score_produces_trace():
    """Score function produces per-hit traces."""
    from audit.measurement_integrity.dr91_measurement_audit import score, m_exact
    gold = [{"bridge": "alpha", "id": "1"}, {"bridge": "beta", "id": "2"}]
    cands = ["alpha", "gamma"]
    r = score(gold, cands, m_exact, "test")
    assert r.tp == 1
    assert r.fn == 1
    assert len(r.matches) == 2
    assert r.matches[0]["matched_by"] == "exact"
    assert r.matches[1]["matched_by"] == "missed"


def test_discovery_vs_recognition_separated():
    """Discovery F1 and Recognition F1 are NEVER combined."""
    from audit.measurement_integrity.dr91_measurement_audit import (
        proposal_locus_audit, m_synonym,
    )
    gold = [{"bridge": "alpha", "id": "1"}]
    all_ents = ["alpha", "beta"]
    shared_ents = ["beta"]  # alpha is NOT shared
    synmap = {}
    result = proposal_locus_audit(gold, all_ents, shared_ents, synmap)
    assert "recognition_f1" in result
    assert "discovery_f1" in result
    assert result["recognition_f1"] != result["discovery_f1"]  # must differ


def test_fp_audit_verdict():
    """FP audit produces PASS or FAIL verdict."""
    from audit.measurement_integrity.dr91_measurement_audit import (
        false_positive_audit, m_exact,
    )
    gold = [{"bridge": "alpha"}]
    cands = ["alpha", "beta", "gamma"]
    result = false_positive_audit(gold, cands, m_exact, n_shuffles=100)
    assert result["verdict"] in ["PASS", "FAIL"]


def test_verdict_is_valid():
    """FINAL_MEASUREMENT_VERDICT.md contains a valid verdict."""
    repo = Path(__file__).resolve().parents[2]
    verdict_file = repo / "FINAL_MEASUREMENT_VERDICT.md"
    if verdict_file.exists():
        content = verdict_file.read_text()
        valid = ["TRUSTWORTHY", "PARTIALLY TRUSTWORTHY", "NOT TRUSTWORTHY"]
        assert any(v in content for v in valid), \
            f"Verdict must be one of {valid}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
