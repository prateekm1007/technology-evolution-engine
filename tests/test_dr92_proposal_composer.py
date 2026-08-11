"""Tests for DR-92: Proposal Composer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest


def test_dr92_imports():
    from audit.measurement_integrity.dr92_proposal_composer import (
        BridgeProposal, ProposalComposer,
    )
    assert BridgeProposal is not None
    assert ProposalComposer is not None


def test_bridge_proposal_has_all_fields():
    """BridgeProposal has all 10 required fields."""
    from audit.measurement_integrity.dr92_proposal_composer import BridgeProposal
    bp = BridgeProposal(
        proposal_id="TEST-001",
        source_cluster_a=["a1"],
        source_cluster_b=["b1"],
        shared_mechanism="X connects A to B",
        necessary_assumptions=["X is real"],
        prediction="if X then Y",
        alternative_explanations=["coincidence"],
        counterexample="if not-X then not-Y",
        falsification_experiment="test X",
        confidence=0.5,
        provenance={"a": "s1"},
    )
    assert bp.proposal_id
    assert bp.source_cluster_a
    assert bp.source_cluster_b
    assert bp.shared_mechanism
    assert bp.necessary_assumptions
    assert bp.prediction
    assert bp.alternative_explanations
    assert bp.counterexample
    assert bp.falsification_experiment
    assert 0 <= bp.confidence <= 1
    assert bp.provenance


def test_composer_produces_proposals_from_shared_entities():
    """Composer produces BridgeProposals from shared entities."""
    from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer
    composer = ProposalComposer()
    # Two lists with a shared entity
    ents_a = ["thermal_emission", "battery", "catalyst"]
    ents_b = ["thermal_emission", "solar_cell", "photon"]
    proposals = composer.compose(ents_a, ents_b)
    assert len(proposals) >= 1
    assert proposals[0].shared_mechanism
    assert proposals[0].prediction
    assert proposals[0].falsification_experiment


def test_composer_produces_no_proposals_without_shared():
    """Composer produces nothing when there are no shared entities."""
    from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer
    composer = ProposalComposer()
    ents_a = ["alpha", "beta"]
    ents_b = ["gamma", "delta"]
    proposals = composer.compose(ents_a, ents_b)
    assert len(proposals) == 0


def test_composer_proposals_are_structured():
    """Each proposal has mechanism, prediction, falsification — the fields
    that richer matchers (Phase VI.6 Objects B-E) expect."""
    from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer
    composer = ProposalComposer()
    ents_a = ["thermal_conductivity", "battery"]
    ents_b = ["thermal_conductivity", "solar"]
    proposals = composer.compose(ents_a, ents_b)
    assert len(proposals) >= 1
    p = proposals[0]
    # Must have the fields that Object B (BridgeProposal) expects
    assert len(p.shared_mechanism) > 20
    assert len(p.prediction) > 20
    assert len(p.falsification_experiment) > 20
    assert len(p.necessary_assumptions) >= 1
    assert len(p.alternative_explanations) >= 1


def test_composer_runs_on_gold_discoveries():
    """Composer runs on the actual gold discovery snippets."""
    from audit.measurement_integrity.dr92_proposal_composer import ProposalComposer
    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES
    from scripts.nlp_pipeline import NLPPipeline

    pipeline = NLPPipeline()
    composer = ProposalComposer()
    gold = GOLD_DISCOVERIES[0]
    ents_a = [e.text for e in pipeline.extract_entities(gold["source_snippet_a"])]
    ents_b = [e.text for e in pipeline.extract_entities(gold["source_snippet_b"])]
    proposals = composer.compose(ents_a, ents_b)
    # May or may not produce proposals (depends on extraction)
    assert isinstance(proposals, list)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
