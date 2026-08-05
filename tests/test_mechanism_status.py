#!/usr/bin/env python3
"""
test_mechanism_status.py — DR-42 tests.

Per DR-42 test requirements:
  - every edge gets a status
  - status is never missing
  - weakest-step rule works for chains
  - contradicted edges do not get promoted
  - verified requires provenance
"""
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.classify_mechanisms import MechanismClassifier
from scripts.mechanism_extraction import CausalStep
from scripts.extract_relations import ExtractedRelationWithProvenance


class TestEdgeClassification:
    """Test single-edge status classification."""

    def test_causal_verb_gets_asserted(self):
        """Causal verbs (produces, enables, governs) get 'asserted'."""
        clf = MechanismClassifier()
        assert clf.classify_edge("produces") == "asserted"
        assert clf.classify_edge("enables") == "asserted"
        assert clf.classify_edge("governs") == "asserted"

    def test_non_causal_verb_gets_associative(self):
        """Non-causal verbs get 'associative'."""
        clf = MechanismClassifier()
        # "reflect" is in CAUSAL_RELATIONS (added cycle 104), so use truly non-causal verbs
        assert clf.classify_edge("combine") == "associative"
        assert clf.classify_edge("contain") == "associative"

    def test_unknown_verb_gets_associative(self):
        """Unknown verbs default to 'associative'."""
        clf = MechanismClassifier()
        assert clf.classify_edge("unknown_verb_xyz") == "associative"


class TestChainClassification:
    """Test chain-level status (weakest step rule)."""

    def test_weakest_step_rule(self):
        """Chain status = weakest step."""
        clf = MechanismClassifier()
        steps = [
            CausalStep(cause="A", effect="B", relation="produces", confidence=0.9, status="asserted"),
            CausalStep(cause="B", effect="C", relation="enables", confidence=0.8, status="associative"),
        ]
        assert clf.classify_chain(steps) == "associative"

    def test_all_asserted_chain_is_asserted(self):
        """All asserted steps → chain is asserted."""
        clf = MechanismClassifier()
        steps = [
            CausalStep(cause="A", effect="B", relation="produces", confidence=0.9, status="asserted"),
            CausalStep(cause="B", effect="C", relation="enables", confidence=0.8, status="asserted"),
        ]
        assert clf.classify_chain(steps) == "asserted"

    def test_contradicted_never_promotes(self):
        """DR-42: contradicted edges never promote."""
        clf = MechanismClassifier()
        steps = [
            CausalStep(cause="A", effect="B", relation="produces", confidence=0.9, status="asserted"),
            CausalStep(cause="B", effect="C", relation="enables", confidence=0.8, status="contradicted"),
            CausalStep(cause="C", effect="D", relation="governs", confidence=0.85, status="verified"),
        ]
        assert clf.classify_chain(steps) == "contradicted"

    def test_empty_chain_is_associative(self):
        """Empty chain defaults to associative."""
        clf = MechanismClassifier()
        assert clf.classify_chain([]) == "associative"


class TestPromotion:
    """Test status promotion rules."""

    def test_asserted_to_plausibility_checked(self):
        """Asserted can be promoted to plausibility-checked."""
        clf = MechanismClassifier()
        assert clf.promote_to_plausibility_checked("asserted", True) == "plausibility-checked"

    def test_asserted_not_promoted_without_check(self):
        """Asserted stays asserted if physics check fails."""
        clf = MechanismClassifier()
        assert clf.promote_to_plausibility_checked("asserted", False) == "asserted"

    def test_contradicted_never_promoted(self):
        """DR-42: contradicted edges never promote."""
        clf = MechanismClassifier()
        assert clf.promote_to_plausibility_checked("contradicted", True) == "contradicted"
        assert clf.promote_to_verified("contradicted", True, True) == "contradicted"

    def test_verified_requires_provenance(self):
        """DR-42: verified requires provenance."""
        clf = MechanismClassifier()
        # Without provenance → can't verify
        assert clf.promote_to_verified("asserted", True, False) == "asserted"
        # With provenance + observation → verified
        assert clf.promote_to_verified("asserted", True, True) == "verified"

    def test_mark_contradicted(self):
        """Once contradicted, always contradicted."""
        clf = MechanismClassifier()
        assert clf.mark_contradicted("asserted") == "contradicted"
        assert clf.mark_contradicted("verified") == "contradicted"


class TestValidation:
    """Test edge validation."""

    def test_no_missing_status(self):
        """Every edge has a status."""
        clf = MechanismClassifier()
        edges = [
            ExtractedRelationWithProvenance(
                subject="A", subject_label="A", relation="produces",
                obj="B", obj_label="B", confidence=0.9, status="asserted"
            ),
            ExtractedRelationWithProvenance(
                subject="B", subject_label="B", relation="enables",
                obj="C", obj_label="C", confidence=0.8, status="associative"
            ),
        ]
        errors = clf.validate_no_missing_status(edges)
        assert len(errors) == 0

    def test_missing_status_detected(self):
        """Missing status is detected."""
        clf = MechanismClassifier()
        edges = [
            ExtractedRelationWithProvenance(
                subject="A", subject_label="A", relation="produces",
                obj="B", obj_label="B", confidence=0.9, status=""
            ),
        ]
        errors = clf.validate_no_missing_status(edges)
        assert len(errors) > 0

    def test_invalid_status_detected(self):
        """Invalid status is detected."""
        clf = MechanismClassifier()
        edges = [
            ExtractedRelationWithProvenance(
                subject="A", subject_label="A", relation="produces",
                obj="B", obj_label="B", confidence=0.9, status="invalid_status"
            ),
        ]
        errors = clf.validate_no_missing_status(edges)
        assert len(errors) > 0


class TestModuleContract:
    """Test module importability."""

    def test_module_importable(self):
        from scripts.classify_mechanisms import MechanismClassifier
        assert hasattr(MechanismClassifier, "classify_edge")
        assert hasattr(MechanismClassifier, "classify_chain")
        assert hasattr(MechanismClassifier, "promote_to_plausibility_checked")
        assert hasattr(MechanismClassifier, "promote_to_verified")
        assert hasattr(MechanismClassifier, "validate_no_missing_status")
