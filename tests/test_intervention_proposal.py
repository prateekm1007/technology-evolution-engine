#!/usr/bin/env python3
"""
Test: Intervention Proposal Module (Phase V).

Per P2: "Untested code is unverified code, permanently. Every fix to an
untested module MUST include a new test."

Per P27: "Read the assertion, not the test name."
Per P28: "Test with 3+ inputs: exact, variation, edge case."

This test file locks the contract of scripts/intervention_proposal.py.
"""
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.intervention_proposal import (
    InterventionProposal,
    propose_intervention,
    log_proposal,
)


class TestInterventionProposal:
    """Test the InterventionProposal class."""

    def test_proposal_for_exp_blind_003(self):
        """Exact case: proposal for EXP-BLIND-003 (nanofiber -> BBB)."""
        proposal = propose_intervention(
            experiment_id="EXP-BLIND-003",
            bridge={"a": "nanofiber_membrane", "c": "selective_permeability", "b": "BBB_tight_junction"},
            mechanism="selective permeability via pore size control",
        )
        assert proposal["type"] == "intervention_proposal"
        assert proposal["experiment_id"] == "EXP-BLIND-003"
        assert "intervention" in proposal
        assert "prediction" in proposal
        assert "falsification" in proposal
        assert "experiment_protocol" in proposal
        assert "pearl_do_operator" in proposal
        assert proposal["class"] == "B"
        # Per cycle-54 rule: must be <$1000 and <30 days
        assert proposal["experiment_protocol"]["estimated_cost_usd"] < 1000
        assert proposal["experiment_protocol"]["duration_days"] < 30
        assert len(proposal["experiment_protocol"]["steps"]) >= 3
        assert len(proposal["experiment_protocol"]["materials"]) >= 3

    def test_proposal_for_exp_blind_022(self):
        """Variation: proposal for EXP-BLIND-022 (pitcher plant -> agriculture)."""
        proposal = propose_intervention(
            experiment_id="EXP-BLIND-022",
            bridge={"a": "pitcher_plant", "c": "controlled_release", "b": "fertilizer"},
            mechanism="controlled_release_membrane",
        )
        assert proposal["experiment_id"] == "EXP-BLIND-022"
        assert proposal["experiment_protocol"]["estimated_cost_usd"] < 1000
        assert proposal["experiment_protocol"]["duration_days"] < 30
        assert "SLIPS" in proposal["intervention"] or "liquid-infused" in proposal["intervention"]

    def test_generic_proposal_for_unknown_experiment(self):
        """Edge case: unknown experiment_id produces generic proposal."""
        proposal = propose_intervention(
            experiment_id="EXP-UNKNOWN-999",
            bridge={"a": "X", "c": "Y", "b": "Z"},
            mechanism="some mechanism",
        )
        assert proposal["type"] == "intervention_proposal"
        assert proposal["experiment_id"] == "EXP-UNKNOWN-999"
        assert "intervention" in proposal
        assert "TBD" in proposal["experiment_protocol"]["steps"][0]


class TestProposalContract:
    """Test that every proposal satisfies the DR-20 and cycle-54 constraints."""

    @pytest.mark.parametrize("exp_id,bridge,mechanism", [
        ("EXP-BLIND-003", {"a": "nanofiber", "c": "selective_permeability", "b": "BBB"}, "selective permeability"),
        ("EXP-BLIND-022", {"a": "pitcher", "c": "controlled_release", "b": "fertilizer"}, "controlled release"),
    ])
    def test_proposal_has_required_fields(self, exp_id, bridge, mechanism):
        """Every proposal must have all DR-20 fields."""
        proposal = propose_intervention(exp_id, bridge, mechanism)
        required = [
            "type", "experiment_id", "timestamp", "writer",
            "bridge", "shared_mechanism", "discovery",
            "intervention", "prediction", "falsification",
            "experiment_protocol", "pearl_do_operator", "class", "closes_loop",
        ]
        for field in required:
            assert field in proposal, f"Missing required field: {field}"

    @pytest.mark.parametrize("exp_id,bridge,mechanism", [
        ("EXP-BLIND-003", {"a": "nanofiber", "c": "selective_permeability", "b": "BBB"}, "selective permeability"),
        ("EXP-BLIND-022", {"a": "pitcher", "c": "controlled_release", "b": "fertilizer"}, "controlled release"),
    ])
    def test_proposal_meets_cycle54_constraints(self, exp_id, bridge, mechanism):
        """Per cycle-54: must be <$1000, <30 days, measurable, reproducible."""
        proposal = propose_intervention(exp_id, bridge, mechanism)
        proto = proposal["experiment_protocol"]
        assert proto["estimated_cost_usd"] < 1000, f"Cost ${proto['estimated_cost_usd']} exceeds $1000 limit"
        assert proto["duration_days"] < 30, f"Duration {proto['duration_days']} days exceeds 30-day limit"
        assert "measurement" in proto
        assert proto["measurement"] != "TBD" or exp_id == "EXP-UNKNOWN-999"
        assert "success_criterion" in proto

    def test_proposal_class_is_B(self):
        """Per CTO review #6: Class B proposals test invention, not just infrastructure."""
        proposal = propose_intervention(
            "EXP-BLIND-003",
            {"a": "nanofiber", "c": "selective_permeability", "b": "BBB"},
            "selective permeability",
        )
        assert proposal["class"] == "B"

    def test_proposal_has_pearl_do_operator(self):
        """Per DR-23 Pearl test: the proposal must specify the do(X=x) intervention."""
        proposal = propose_intervention(
            "EXP-BLIND-003",
            {"a": "nanofiber", "c": "selective_permeability", "b": "BBB"},
            "selective permeability",
        )
        assert proposal["pearl_do_operator"].startswith("do(")
        assert proposal["pearl_do_operator"].endswith(")")

    def test_proposal_has_falsification(self):
        """Per Popper/DR-23: the proposal must be falsifiable."""
        proposal = propose_intervention(
            "EXP-BLIND-003",
            {"a": "nanofiber", "c": "selective_permeability", "b": "BBB"},
            "selective permeability",
        )
        assert len(proposal["falsification"]) > 50
        assert "false analogy" in proposal["falsification"].lower() or "not" in proposal["falsification"].lower()


class TestModuleContract:
    """Test the module is importable and has the right interface."""

    def test_module_importable(self):
        from scripts import intervention_proposal
        assert hasattr(intervention_proposal, "InterventionProposal")
        assert hasattr(intervention_proposal, "propose_intervention")
        assert hasattr(intervention_proposal, "log_proposal")

    def test_intervention_proposal_class_instantiable(self):
        proposal = InterventionProposal(
            "EXP-BLIND-003",
            {"a": "nanofiber", "c": "selective_permeability", "b": "BBB"},
            "selective permeability",
        )
        d = proposal.to_dict()
        assert d["experiment_id"] == "EXP-BLIND-003"
        assert "intervention" in d
