"""Tests for DR-93: Proposal Composer Evaluation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


def test_dr93_imports():
    from audit.measurement_integrity.dr93_proposal_evaluation import (
        check_structural_validity, check_scientific_validity,
        check_discovery_validity, score_proposal_quality,
    )
    assert check_structural_validity is not None


def test_structural_validity_checks_all_fields():
    """Structural validity checks all 12 required fields."""
    from audit.measurement_integrity.dr93_proposal_evaluation import check_structural_validity
    from audit.measurement_integrity.dr92_proposal_composer import BridgeProposal

    p = BridgeProposal(
        proposal_id="T1",
        source_cluster_a=["a"], source_cluster_b=["b"],
        shared_mechanism="The concept 'test' appears in both sources",
        necessary_assumptions=["test is real"],
        prediction="If 'test' is present, then connection exists",
        alternative_explanations=["coincidence"],
        counterexample="If 'test' is removed, connection disappears",
        falsification_experiment="Check if 'test' appears in non-cross-domain papers",
        confidence=0.5,
        provenance={"shared_entity": "test"},
    )
    result = check_structural_validity(p)
    assert result["total"] == 12
    assert result["valid"] is True


def test_scientific_validity_checks_5_dimensions():
    """Scientific validity checks coherent, testable, plausible, specific, non_trivial."""
    from audit.measurement_integrity.dr93_proposal_evaluation import check_scientific_validity
    from audit.measurement_integrity.dr92_proposal_composer import BridgeProposal

    p = BridgeProposal(
        proposal_id="T2",
        source_cluster_a=["a"], source_cluster_b=["b"],
        shared_mechanism="The 'thermal_conductivity' connects domain A to domain B",
        necessary_assumptions=["thermal_conductivity is real"],
        prediction="If 'thermal_conductivity' is present then cross-domain connection should exist",
        alternative_explanations=["coincidence"],
        counterexample="If 'thermal_conductivity' is removed then connection disappears",
        falsification_experiment="Check if 'thermal_conductivity' appears in non-cross-domain papers",
        confidence=0.5,
        provenance={"shared_entity": "thermal_conductivity"},
    )
    result = check_scientific_validity(p)
    assert result["total"] == 5
    assert result["scores"]["coherent"] is True
    assert result["scores"]["testable"] is True


def test_discovery_validity_classifies():
    """Discovery validity classifies as KNOWN, TRIVIAL, or POTENTIALLY_NOVEL."""
    from audit.measurement_integrity.dr93_proposal_evaluation import check_discovery_validity
    from audit.measurement_integrity.dr92_proposal_composer import BridgeProposal

    p = BridgeProposal(
        proposal_id="T3",
        source_cluster_a=["a"], source_cluster_b=["b"],
        shared_mechanism="test", necessary_assumptions=["a"],
        prediction="test", alternative_explanations=["a"],
        counterexample="test", falsification_experiment="test",
        confidence=0.5,
        provenance={"shared_entity": "biomineralization"},
    )
    result = check_discovery_validity(p, ["biomineralization"])
    assert result["classification"] == "KNOWN"

    p2 = BridgeProposal(
        proposal_id="T4", source_cluster_a=["a"], source_cluster_b=["b"],
        shared_mechanism="test", necessary_assumptions=["a"],
        prediction="test", alternative_explanations=["a"],
        counterexample="test", falsification_experiment="test",
        confidence=0.5, provenance={"shared_entity": "temperature"},
    )
    result2 = check_discovery_validity(p2, ["biomineralization"])
    assert result2["classification"] == "TRIVIAL"


def test_quality_score_1_to_5():
    """Quality scores are on 1-5 scale."""
    from audit.measurement_integrity.dr93_proposal_evaluation import score_proposal_quality
    from audit.measurement_integrity.dr92_proposal_composer import BridgeProposal

    p = BridgeProposal(
        proposal_id="T5", source_cluster_a=["a"], source_cluster_b=["b"],
        shared_mechanism="The 'thermal_conductivity' connects domain A to domain B via phonon scattering",
        necessary_assumptions=["thermal_conductivity is real", "phonons exist"],
        prediction="If 'thermal_conductivity' is present then cross-domain connection should exist",
        alternative_explanations=["coincidence", "shared vocabulary"],
        counterexample="If 'thermal_conductivity' is removed then connection disappears",
        falsification_experiment="Check if 'thermal_conductivity' appears in non-cross-domain papers",
        confidence=0.5, provenance={"shared_entity": "thermal_conductivity"},
    )
    q = score_proposal_quality(p)
    assert 1 <= q["clarity"] <= 5
    assert 1 <= q["specificity"] <= 5
    assert 1 <= q["falsifiability"] <= 5
    assert 1 <= q["completeness"] <= 5
    assert 1 <= q["overall"] <= 5


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
