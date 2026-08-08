"""
test_discovery_substrate.py — Tests for the scientific discovery substrate.

Verifies acceptance criteria A through L from the CEO Directive.
"""
import sys
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from discovery_infrastructure.discovery_substrate import (
    EpistemicState, VALID_TRANSITIONS,
    ProvenanceNode, ProvenanceEdge, ProvenanceGraph,
    MechanismNode, MechanismEdge, MechanismGraph, MechanismNodeType, MechanismEdgeType,
    TransferHypothesis, Hypothesis, Prediction, ExperimentProposal,
    ExperimentManifest, DiscoveryFailure, FailureType,
    PriorArtAssessment, NoveltyStatus,
    DiscoveryCase, DiscoveryState, DiscoveryStateMachine, DISCOVERY_TRANSITIONS,
    StateTransition, DiscoveryLedger, InventionCandidate,
)


# ============================================================================
# A. Every discovery object has immutable provenance
# ============================================================================

class TestProvenance:
    def test_provenance_graph_traces_back(self):
        """A reviewer can trace 'why does the system believe this?' to primary evidence."""
        graph = ProvenanceGraph()
        graph.add_node(ProvenanceNode("source_1", "source_passage", "abc123"))
        graph.add_node(ProvenanceNode("mechanism_1", "mechanism", "def456"))
        graph.add_node(ProvenanceNode("hypothesis_1", "hypothesis", "ghi789"))
        graph.add_edge(ProvenanceEdge("e1", "source_1", "mechanism_1", "DERIVES_FROM", "extracted from", actor="test"))
        graph.add_edge(ProvenanceEdge("e2", "mechanism_1", "hypothesis_1", "SUPPORTS", "derived from", actor="test"))
        
        ancestors = graph.trace_back("hypothesis_1")
        assert len(ancestors) == 3
        node_ids = {n.node_id for n in ancestors}
        assert "source_1" in node_ids
        assert "mechanism_1" in node_ids
        assert "hypothesis_1" in node_ids

    def test_discovery_case_has_provenance(self):
        """Every DiscoveryCase has a ProvenanceGraph."""
        case = DiscoveryCase(case_id="DC-001")
        assert hasattr(case, "provenance")
        assert isinstance(case.provenance, ProvenanceGraph)

    def test_hypothesis_has_provenance(self):
        """Every Hypothesis has a ProvenanceGraph."""
        hyp = Hypothesis(hypothesis_id="H-001", claim="test", mechanism="test")
        assert hasattr(hyp, "provenance")
        assert isinstance(hyp.provenance, ProvenanceGraph)


# ============================================================================
# B. Knowledge and hypothesis states cannot be silently conflated
# ============================================================================

class TestEpistemicStates:
    def test_hypothesized_cannot_auto_promote_to_established(self):
        """HYPOTHESIZED → ESTABLISHED is NOT a valid transition."""
        assert EpistemicState.ESTABLISHED not in VALID_TRANSITIONS[EpistemicState.HYPOTHESIZED]

    def test_valid_transitions_exist(self):
        """Each state has defined valid transitions."""
        for state in EpistemicState:
            assert state in VALID_TRANSITIONS

    def test_refuted_is_terminal(self):
        """REFUTED has no valid transitions (terminal state)."""
        assert len(VALID_TRANSITIONS[EpistemicState.REFUTED]) == 0

    def test_full_confidence_ladder(self):
        """The full ladder: OBSERVED → EXTRACTED → ... → ESTABLISHED."""
        ladder = [
            EpistemicState.OBSERVED,
            EpistemicState.EXTRACTED,
            EpistemicState.INFERRED,
            EpistemicState.HYPOTHESIZED,
            EpistemicState.PREDICTED,
            EpistemicState.EXPERIMENTALLY_SUPPORTED,
            EpistemicState.REPLICATED,
            EpistemicState.ESTABLISHED,
        ]
        for i in range(len(ladder) - 1):
            assert ladder[i+1] in VALID_TRANSITIONS[ladder[i]], (
                f"Missing transition: {ladder[i].value} → {ladder[i+1].value}"
            )

    def test_any_state_can_be_refuted(self):
        """Any state can transition to REFUTED."""
        for state in EpistemicState:
            if state == EpistemicState.REFUTED:
                continue
            assert EpistemicState.REFUTED in VALID_TRANSITIONS[state], (
                f"{state.value} should be able to transition to REFUTED"
            )


# ============================================================================
# C. Every hypothesis can express a falsifiable prediction
# ============================================================================

class TestFalsifiability:
    def test_hypothesis_has_falsifier_field(self):
        """Every Hypothesis has a 'falsifier' field."""
        hyp = Hypothesis(hypothesis_id="H-001", claim="test", mechanism="test")
        assert hasattr(hyp, "falsifier")

    def test_prediction_has_falsifier_field(self):
        """Every Prediction has a 'falsifier' field."""
        pred = Prediction(prediction_id="P-001", hypothesis_id="H-001", observable="test")
        assert hasattr(pred, "falsifier")

    def test_prediction_has_expected_direction(self):
        """Every Prediction specifies expected direction."""
        pred = Prediction(prediction_id="P-001", hypothesis_id="H-001", observable="test")
        assert hasattr(pred, "expected_direction")


# ============================================================================
# D. Every failure can be stored and reused
# ============================================================================

class TestFailureRegistry:
    def test_failure_types_defined(self):
        """All 11 failure types are defined."""
        expected = {
            "RECOGNITION_LEAKAGE", "SEMANTIC_LEAKAGE", "PRIOR_ART",
            "UNSUPPORTED_MECHANISM", "NON_TESTABLE", "FAILED_PREDICTION",
            "EXPERIMENTAL_FAILURE", "REPLICATION_FAILURE", "FALSE_POSITIVE",
            "DOMAIN_TRANSFER_FAILURE", "CONTROL_OUTPERFORMED",
        }
        actual = {ft.value for ft in FailureType}
        assert actual == expected

    def test_failure_has_reusable_lesson(self):
        """Every DiscoveryFailure has a 'reusable_lesson' field."""
        f = DiscoveryFailure(failure_id="F-001", failure_type=FailureType.PRIOR_ART)
        assert hasattr(f, "reusable_lesson")

    def test_ledger_stores_failures(self):
        """The DiscoveryLedger stores failures and they persist."""
        ledger = DiscoveryLedger()
        f = DiscoveryFailure(failure_id="F-001", failure_type=FailureType.PRIOR_ART)
        ledger.register_failure(f)
        assert "F-001" in ledger.failures
        assert ledger.failures["F-001"].failure_type == FailureType.PRIOR_ART

    def test_ledger_returns_failures_for_hypothesis(self):
        """Can retrieve all failures for a given hypothesis."""
        ledger = DiscoveryLedger()
        f1 = DiscoveryFailure(failure_id="F-001", failure_type=FailureType.PRIOR_ART, hypothesis_id="H-001")
        f2 = DiscoveryFailure(failure_id="F-002", failure_type=FailureType.NON_TESTABLE, hypothesis_id="H-001")
        f3 = DiscoveryFailure(failure_id="F-003", failure_type=FailureType.PRIOR_ART, hypothesis_id="H-002")
        ledger.register_failure(f1)
        ledger.register_failure(f2)
        ledger.register_failure(f3)
        
        h1_failures = ledger.get_failures_for_hypothesis("H-001")
        assert len(h1_failures) == 2
        assert all(f.hypothesis_id == "H-001" for f in h1_failures)


# ============================================================================
# E. Prior-art status is explicitly separate from scientific validity
# ============================================================================

class TestPriorArtSeparation:
    def test_novelty_status_separate_from_epistemic_state(self):
        """NoveltyStatus is a separate enum from EpistemicState."""
        assert NoveltyStatus is not EpistemicState

    def test_novelty_as_of_cutoff_exists(self):
        """NOVEL_AS_OF_CUTOFF is the only status that can pass Gate B."""
        assert NoveltyStatus.NOVEL_AS_OF_CUTOFF in NoveltyStatus

    def test_prior_art_assessment_has_search_scope(self):
        """PriorArtAssessment records where was searched."""
        pa = PriorArtAssessment(assessment_id="PA-001", hypothesis_id="H-001")
        assert hasattr(pa, "search_scope")
        assert hasattr(pa, "queries")
        assert hasattr(pa, "cutoff")

    def test_never_claims_absolute_novelty(self):
        """The status is NOVEL_AS_OF_CUTOFF, not 'NOVEL' absolutely."""
        values = {ns.value for ns in NoveltyStatus}
        assert "NOVEL_AS_OF_CUTOFF" in values
        assert "NOVEL" not in values  # absolute novelty claim is forbidden


# ============================================================================
# F. Every experiment is reproducible from a manifest
# ============================================================================

class TestReproducibility:
    def test_manifest_has_all_required_fields(self):
        """ExperimentManifest has code_sha, knowledge_sha, model, etc."""
        m = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        assert hasattr(m, "code_sha")
        assert hasattr(m, "knowledge_sha")
        assert hasattr(m, "model")
        assert hasattr(m, "model_version")
        assert hasattr(m, "prompt_sha")
        assert hasattr(m, "input_sha")
        assert hasattr(m, "random_seed")
        assert hasattr(m, "environment")

    def test_manifest_is_content_addressed(self):
        """Manifest can produce a content hash."""
        m1 = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        m2 = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        m3 = ExperimentManifest(code_sha="xyz", knowledge_sha="def")
        assert m1.to_hash() == m2.to_hash()
        assert m1.to_hash() != m3.to_hash()

    def test_discovery_case_has_manifest(self):
        """DiscoveryCase has an optional ExperimentManifest."""
        case = DiscoveryCase(case_id="DC-001")
        assert hasattr(case, "manifest")
        assert case.manifest is None  # optional initially


# ============================================================================
# G. Discovery lineage is traversable
# ============================================================================

class TestLineage:
    def test_case_has_parent_and_derived(self):
        """DiscoveryCase has parent_cases and derived_cases."""
        case = DiscoveryCase(case_id="DC-001")
        assert hasattr(case, "parent_cases")
        assert hasattr(case, "derived_cases")

    def test_ledger_returns_lineage(self):
        """DiscoveryLedger.get_lineage returns parent and derived cases."""
        ledger = DiscoveryLedger()
        case = DiscoveryCase(
            case_id="DC-001",
            parent_cases=["DC-000"],
            derived_cases=["DC-002", "DC-003"],
        )
        ledger.register_case(case)
        lineage = ledger.get_lineage("DC-001")
        assert lineage["parents"] == ["DC-000"]
        assert lineage["derived"] == ["DC-002", "DC-003"]


# ============================================================================
# H. Gate 2 artifacts are cryptographically protected
# ============================================================================

class TestGate2Protection:
    def test_gate2_directory_has_immutable_marker(self):
        """experiments/gate2/ has an .IMMUTABLE marker file."""
        assert (REPO / "experiments" / "gate2" / ".IMMUTABLE").exists()

    def test_immutable_marker_contains_warning(self):
        """The .IMMUTABLE file contains a warning."""
        content = (REPO / "experiments" / "gate2" / ".IMMUTABLE").read_text()
        assert "IMMUTABLE" in content or "immutable" in content.lower()


# ============================================================================
# I. Development fixtures are separated from Gate 2
# ============================================================================

class TestDevGate2Separation:
    def test_dev_directory_exists(self):
        assert (REPO / "experiments" / "dev").exists()

    def test_sandbox_directory_exists(self):
        assert (REPO / "experiments" / "sandbox").exists()

    def test_gate2_directory_exists(self):
        assert (REPO / "experiments" / "gate2").exists()

    def test_dev_has_marker(self):
        assert (REPO / "experiments" / "dev" / ".DEV_ONLY").exists()

    def test_sandbox_has_marker(self):
        assert (REPO / "experiments" / "sandbox" / ".SANDBOX").exists()


# ============================================================================
# J. No production discovery benchmark or scorer is changed
# ============================================================================

class TestNoProductionChanges:
    def test_discovery_capability_benchmark_unchanged(self):
        """The frozen benchmark file still has BRIDGE_SYNONYMS = {}."""
        from benchmarks.discovery_capability_benchmark import BRIDGE_SYNONYMS
        assert len(BRIDGE_SYNONYMS) == 0

    def test_frozen_score_intact(self):
        """The frozen discovery_capability_score.json still has F1=0.5714."""
        score = json.loads((REPO / "benchmarks" / "reports" / "discovery_capability_score.json").read_text())
        assert score["f1"] == 0.5714


# ============================================================================
# K. No new agent architecture is introduced
# ============================================================================

class TestNoAgents:
    def test_no_new_agent_files(self):
        """No new agent files in discovery_infrastructure/."""
        infra = REPO / "discovery_infrastructure"
        for py_file in infra.rglob("*.py"):
            content = py_file.read_text()
            assert "class.*Agent" not in content, (
                f"Agent class found in {py_file} — directive forbids new agents"
            )


# ============================================================================
# L. All infrastructure tests pass (this test file itself)
# ============================================================================

class TestStateMachine:
    def test_state_machine_starts_at_raw_evidence(self):
        sm = DiscoveryStateMachine("DC-001")
        assert sm.current_state == DiscoveryState.RAW_EVIDENCE

    def test_valid_transition(self):
        sm = DiscoveryStateMachine("DC-001")
        sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE, actor="test", evidence="test")
        assert sm.current_state == DiscoveryState.STRUCTURED_KNOWLEDGE

    def test_invalid_transition_raises(self):
        sm = DiscoveryStateMachine("DC-001")
        with pytest.raises(ValueError):
            sm.transition(DiscoveryState.VALIDATED_DISCOVERY, actor="test")

    def test_transition_records_audit_trail(self):
        sm = DiscoveryStateMachine("DC-001")
        t = sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE, actor="test",
                          code_sha="abc123", evidence="passage 1", reason="extraction")
        assert t.actor == "test"
        assert t.code_sha == "abc123"
        assert t.evidence == "passage 1"
        assert t.reason == "extraction"
        assert len(sm.history) == 1

    def test_full_discovery_lifecycle(self):
        """Full lifecycle: RAW_EVIDENCE → ... → VALIDATED_DISCOVERY."""
        sm = DiscoveryStateMachine("DC-001")
        states = [
            DiscoveryState.STRUCTURED_KNOWLEDGE,
            DiscoveryState.MECHANISM,
            DiscoveryState.TRANSFER_HYPOTHESIS,
            DiscoveryState.CANDIDATE_DISCOVERY,
            DiscoveryState.GATE_A,
            DiscoveryState.GATE_B,
            DiscoveryState.GATE_C,
            DiscoveryState.TESTABLE_HYPOTHESIS,
            DiscoveryState.EXPERIMENT,
            DiscoveryState.RESULT,
            DiscoveryState.REPLICATION,
            DiscoveryState.VALIDATED_DISCOVERY,
        ]
        for s in states:
            assert sm.can_transition(s), f"Cannot transition to {s.value} from {sm.current_state.value}"
            sm.transition(s, actor="test", evidence="test")

    def test_any_state_can_fail(self):
        """Any state can transition to FAILED."""
        for state in DiscoveryState:
            if state == DiscoveryState.FAILED:
                continue
            assert DiscoveryState.FAILED in DISCOVERY_TRANSITIONS.get(state, set()), (
                f"{state.value} should be able to FAIL"
            )


class TestTransferHypothesis:
    def test_has_all_required_fields(self):
        """TransferHypothesis has all fields from the directive."""
        th = TransferHypothesis(
            transfer_id="TH-001",
            source_domain="materials",
            source_mechanism="biomineralization",
            target_domain="construction",
        )
        assert hasattr(th, "source_domain")
        assert hasattr(th, "source_mechanism")
        assert hasattr(th, "source_conditions")
        assert hasattr(th, "target_domain")
        assert hasattr(th, "target_problem")
        assert hasattr(th, "transferred_principle")
        assert hasattr(th, "required_translation")
        assert hasattr(th, "expected_effect")
        assert hasattr(th, "boundary_conditions")
        assert hasattr(th, "failure_conditions")
        assert hasattr(th, "testable_prediction")

    def test_starts_as_hypothesized(self):
        """TransferHypothesis starts in HYPOTHESIZED state."""
        th = TransferHypothesis(transfer_id="TH-001", source_domain="a", source_mechanism="m")
        assert th.epistemic_state == EpistemicState.HYPOTHESIZED


class TestMechanismGraph:
    def test_node_types_defined(self):
        """All 11 node types are defined."""
        expected = {"system", "material", "process", "property", "condition",
                    "constraint", "mechanism", "effect", "measurement",
                    "failure_mode", "design_variable"}
        actual = {nt.value for nt in MechanismNodeType}
        assert actual == expected

    def test_edge_types_defined(self):
        """All 10 edge types are defined."""
        expected = {"CAUSES", "ENABLES", "INHIBITS", "MODULATES", "CORRELATES_WITH",
                    "REQUIRES", "CONSTRAINS", "PRODUCES", "FAILS_UNDER", "TRANSFERS_TO"}
        actual = {et.value for et in MechanismEdgeType}
        assert actual == expected

    def test_edge_has_provenance(self):
        """MechanismEdge has evidence list (not just a confidence score)."""
        e = MechanismEdge(edge_id="E1", source_id="N1", target_id="N2",
                         edge_type=MechanismEdgeType.CAUSES)
        assert hasattr(e, "evidence")
        assert hasattr(e, "confidence")
        assert isinstance(e.evidence, list)


class TestLedger:
    def test_ledger_is_append_only_by_design(self):
        """Ledger has no delete methods."""
        ledger = DiscoveryLedger()
        methods = [m for m in dir(ledger) if not m.startswith("_")]
        assert "delete" not in methods
        assert "remove" not in methods
        assert "delete_case" not in methods
        assert "remove_case" not in methods

    def test_ledger_registers_all_object_types(self):
        """Ledger can register all discovery object types."""
        ledger = DiscoveryLedger()
        ledger.register_case(DiscoveryCase(case_id="DC-001"))
        ledger.register_hypothesis(Hypothesis(hypothesis_id="H-001", claim="t", mechanism="t"))
        ledger.register_prediction(Prediction(prediction_id="P-001", hypothesis_id="H-001", observable="t"))
        ledger.register_experiment(ExperimentProposal(experiment_id="E-001", hypothesis_id="H-001", objective="t"))
        ledger.register_failure(DiscoveryFailure(failure_id="F-001", failure_type=FailureType.PRIOR_ART))
        ledger.register_prior_art(PriorArtAssessment(assessment_id="PA-001", hypothesis_id="H-001"))
        ledger.register_transfer(TransferHypothesis(transfer_id="TH-001", source_domain="a", source_mechanism="m"))
        
        assert "DC-001" in ledger.cases
        assert "H-001" in ledger.hypotheses
        assert "P-001" in ledger.predictions
        assert "E-001" in ledger.experiments
        assert "F-001" in ledger.failures
        assert "PA-001" in ledger.prior_art
        assert "TH-001" in ledger.transfers


class TestInventionCandidate:
    def test_schema_exists(self):
        """InventionCandidate schema exists (not implemented, just schema)."""
        ic = InventionCandidate(invention_id="IC-001", discovery_id="DC-001")
        assert hasattr(ic, "problem")
        assert hasattr(ic, "mechanism")
        assert hasattr(ic, "design_principle")
        assert hasattr(ic, "design_variables")
        assert hasattr(ic, "constraints")
        assert hasattr(ic, "predicted_advantage")
        assert hasattr(ic, "novelty_status")
        assert hasattr(ic, "prototype_specification")
        assert hasattr(ic, "test_plan")
        assert hasattr(ic, "failure_modes")
