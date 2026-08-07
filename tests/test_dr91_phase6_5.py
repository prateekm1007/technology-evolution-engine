"""Tests for DR-91 Phase VI.5: Discovery Object Audit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


def test_phase65_imports():
    from audit.measurement_integrity.dr91_phase6_5 import (
        BridgeProposal, score_proposal, adversarial_proposal_test,
    )
    assert BridgeProposal is not None


def test_bridge_proposal_has_5_components():
    """BridgeProposal has mechanism, shared_variables, prediction,
    falsification, evidence_sources."""
    from audit.measurement_integrity.dr91_phase6_5 import BridgeProposal
    bp = BridgeProposal(
        proposal_id="TEST-001",
        domain_a="A", domain_b="B",
        mechanism="X causes Y via Z",
        shared_variables=["x", "y"],
        prediction="if Z then W",
        falsification="if not-Z then not-W",
        evidence_sources=["s1", "s2"],
    )
    assert bp.mechanism
    assert len(bp.shared_variables) >= 1
    assert bp.prediction
    assert bp.falsification
    assert len(bp.evidence_sources) >= 2


def test_score_proposal_checks_all_5():
    """Score checks mechanism, variables, prediction, falsification, evidence."""
    from audit.measurement_integrity.dr91_phase6_5 import BridgeProposal, score_proposal
    gold = BridgeProposal(
        proposal_id="GOLD-001",
        domain_a="thermoelectric", domain_b="battery",
        mechanism="grain size reduction increases ZT via phonon scattering",
        shared_variables=["grain_size", "thermal_conductivity"],
        prediction="if grain_size < 50nm then ZT increases",
        falsification="if grain_size < 50nm and ZT does not increase",
        evidence_sources=["s1", "s2"],
    )
    # Good candidate
    good = BridgeProposal(
        proposal_id="CAND-001",
        domain_a="thermoelectric", domain_b="battery",
        mechanism="grain size reduction increases ZT via phonon scattering",
        shared_variables=["grain_size"],
        prediction="if grain_size < 50nm then ZT increases",
        falsification="if grain_size < 50nm and ZT does not increase",
        evidence_sources=["s1", "s2"],
    )
    result = score_proposal(gold, good)
    assert result["all_match"] is True

    # Bad candidate (wrong mechanism)
    bad = BridgeProposal(
        proposal_id="CAND-002",
        domain_a="A", domain_b="B",
        mechanism="completely different mechanism about batteries",
        shared_variables=["grain_size"],
        prediction="if grain_size < 50nm then ZT increases",
        falsification="if grain_size < 50nm and ZT does not increase",
        evidence_sources=["s1", "s2"],
    )
    result_bad = score_proposal(gold, bad)
    assert result_bad["all_match"] is False
    assert result_bad["mechanism_match"] is False


def test_adversarial_proposal_fp_lower_than_entity():
    """HONEST TEST: Proposal-level FP is lower than entity-level FP (1.0).

    The CTO's H4: the discovery object is wrong. Entity FP = 1.0.
    Proposal FP should be < 1.0 (even if not < 5% yet).
    """
    from audit.measurement_integrity.dr91_phase6_5 import (
        BridgeProposal, adversarial_proposal_test,
    )
    gold = [
        BridgeProposal(
            proposal_id="G1",
            domain_a="A", domain_b="B",
            mechanism="thermal conductivity affects charge transfer",
            shared_variables=["thermal_conductivity"],
            prediction="if thermal_conductivity decreases then efficiency increases",
            falsification="if thermal_conductivity decreases and efficiency does not increase",
            evidence_sources=["s1", "s2"],
        )
    ]
    result = adversarial_proposal_test(gold, n_fake=10)
    assert result["fp_rate"] < 1.0, \
        f"Proposal FP ({result['fp_rate']}) should be < 1.0 (entity FP = 1.0). " \
        f"The proposal object must be harder to fake than entities."


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
