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
    ProvenanceImmutableError, DuplicateRegistrationError, UnfalsifiableError,
    SCIENTIFIC_PIPELINE_STATES,
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
        sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE,
                      actor="test", code_sha="abc123",
                      evidence="passage 1", reason="extraction")
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
        """Full lifecycle: RAW_EVIDENCE → ... → VALIDATED_DISCOVERY.

        Per Repair #6-extended, transitions into SCIENTIFIC_PIPELINE_STATES
        (TESTABLE_HYPOTHESIS and beyond) require a hypothesis with a
        non-empty falsifier. This test now passes such a hypothesis.
        """
        sm = DiscoveryStateMachine("DC-001")
        # A hypothesis with a non-empty falsifier — required to enter the
        # scientific evaluation pipeline (TESTABLE_HYPOTHESIS and beyond).
        hyp = Hypothesis(
            hypothesis_id="H-001", claim="test claim", mechanism="test mechanism",
            falsifier="If X is observed under conditions Y, the hypothesis is refuted.",
        )
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
            sm.transition(s, actor="test", code_sha="abc123",
                          evidence="passage 1", reason="extraction",
                          hypothesis=hyp)

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


# ============================================================================
# ADVERSARIAL TESTS — substrate integrity invariants (Repair #9)
# ============================================================================
# Each test attempts to violate an invariant and asserts that the substrate
# REJECTS the violation. These tests exist to make invalid scientific states
# unrepresentable, not merely documented.
#
# Reviewer's standard:
#     NOT "the system has a field for provenance."
#     BUT "the system cannot silently alter provenance."
#
#     NOT "the system has a falsifier field."
#     BUT "a testable hypothesis cannot exist without a falsifier."
#
#     NOT "there is an immutable marker."
#     BUT "the repository can prove the frozen artifact has not changed."


class TestAdversarialProvenanceImmutability:
    """Repair #1: provenance is content-addressed and immutable after commit."""

    def test_add_node_after_commit_raises(self):
        """Cannot add a node to a committed (frozen) ProvenanceGraph."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        g.commit()
        with pytest.raises(ProvenanceImmutableError):
            g.add_node(ProvenanceNode("n2", "mechanism", "def"))

    def test_add_edge_after_commit_raises(self):
        """Cannot add an edge to a committed (frozen) ProvenanceGraph."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        g.add_node(ProvenanceNode("n2", "mechanism", "def"))
        g.commit()
        with pytest.raises(ProvenanceImmutableError):
            g.add_edge(ProvenanceEdge("e1", "n1", "n2", "DERIVES_FROM", "x", actor="t"))

    def test_committed_hash_is_full_sha256(self):
        """The committed hash is the full 64-character SHA-256."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        h = g.commit()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_committed_hash_is_deterministic(self):
        """Two graphs with the same content produce the same hash."""
        g1 = ProvenanceGraph()
        g1.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        g2 = ProvenanceGraph()
        g2.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        assert g1.commit() == g2.commit()

    def test_modified_graph_fails_verification(self):
        """A graph modified after commit fails verification against the original hash."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g.commit()
        # Tamper: bypass the immutability check by directly mutating internal state
        # (this simulates what an attacker with code access might do)
        g.nodes["n1"] = ProvenanceNode("n1", "TAMPERED", "xyz")
        # verify() must detect the tampering
        assert not g.verify(original_hash)

    def test_commit_is_idempotent(self):
        """Calling commit() twice returns the same hash; graph stays frozen."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        h1 = g.commit()
        h2 = g.commit()
        assert h1 == h2
        with pytest.raises(ProvenanceImmutableError):
            g.add_node(ProvenanceNode("n2", "mechanism", "def"))

    def test_fork_creates_mutable_copy(self):
        """fork() creates a mutable copy; the original stays frozen."""
        g1 = ProvenanceGraph()
        g1.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g1.commit()
        # Fork must be mutable
        g2 = g1.fork()
        assert not g2.is_committed
        g2.add_node(ProvenanceNode("n2", "mechanism", "def"))
        # Original must be unchanged
        assert g1.verify(original_hash)
        # Fork must have a different content hash
        assert g2.content_hash() != original_hash

    def test_case_commit_provenance_records_root_hash(self):
        """DiscoveryCase.commit_provenance() records the root hash and freezes the graph."""
        case = DiscoveryCase(case_id="DC-001")
        case.provenance.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        h = case.commit_provenance()
        assert case.provenance_root_hash == h
        assert len(h) == 64
        # Subsequent mutation must fail
        with pytest.raises(ProvenanceImmutableError):
            case.provenance.add_node(ProvenanceNode("n2", "mechanism", "def"))

    def test_case_verify_provenance_detects_tampering(self):
        """verify_provenance() returns False after tampering."""
        case = DiscoveryCase(case_id="DC-001")
        case.provenance.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        case.commit_provenance()
        assert case.verify_provenance()
        # Tamper
        case.provenance.nodes["n1"] = ProvenanceNode("n1", "TAMPERED", "xyz")
        assert not case.verify_provenance()

    def test_hypothesis_commit_provenance_works(self):
        """Hypothesis.commit_provenance() works the same way."""
        hyp = Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m")
        hyp.provenance.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        h = hyp.commit_provenance()
        assert hyp.provenance_root_hash == h
        assert hyp.verify_provenance()

    def test_transfer_commit_provenance_works(self):
        """TransferHypothesis.commit_provenance() works the same way."""
        th = TransferHypothesis(transfer_id="TH-001", source_domain="a", source_mechanism="m")
        th.provenance.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        h = th.commit_provenance()
        assert th.provenance_root_hash == h
        assert th.verify_provenance()


class TestAdversarialLedgerAppendOnly:
    """Repair #2: ledger register_*() reject duplicate IDs."""

    def test_register_case_duplicate_raises(self):
        ledger = DiscoveryLedger()
        ledger.register_case(DiscoveryCase(case_id="DC-001"))
        with pytest.raises(DuplicateRegistrationError):
            ledger.register_case(DiscoveryCase(case_id="DC-001"))

    def test_register_hypothesis_duplicate_raises(self):
        ledger = DiscoveryLedger()
        ledger.register_hypothesis(Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m"))
        with pytest.raises(DuplicateRegistrationError):
            ledger.register_hypothesis(Hypothesis(hypothesis_id="H-001", claim="c2", mechanism="m2"))

    def test_register_prediction_duplicate_raises(self):
        ledger = DiscoveryLedger()
        ledger.register_prediction(Prediction(prediction_id="P-001", hypothesis_id="H-001"))
        with pytest.raises(DuplicateRegistrationError):
            ledger.register_prediction(Prediction(prediction_id="P-001", hypothesis_id="H-002"))

    def test_register_experiment_duplicate_raises(self):
        ledger = DiscoveryLedger()
        ledger.register_experiment(ExperimentProposal(experiment_id="E-001", hypothesis_id="H-001", objective="o"))
        with pytest.raises(DuplicateRegistrationError):
            ledger.register_experiment(ExperimentProposal(experiment_id="E-001", hypothesis_id="H-001", objective="o2"))

    def test_register_failure_duplicate_raises(self):
        ledger = DiscoveryLedger()
        ledger.register_failure(DiscoveryFailure(failure_id="F-001", failure_type=FailureType.PRIOR_ART))
        with pytest.raises(DuplicateRegistrationError):
            ledger.register_failure(DiscoveryFailure(failure_id="F-001", failure_type=FailureType.FALSE_POSITIVE))

    def test_register_prior_art_duplicate_raises(self):
        ledger = DiscoveryLedger()
        ledger.register_prior_art(PriorArtAssessment(assessment_id="PA-001", hypothesis_id="H-001"))
        with pytest.raises(DuplicateRegistrationError):
            ledger.register_prior_art(PriorArtAssessment(assessment_id="PA-001", hypothesis_id="H-002"))

    def test_register_transfer_duplicate_raises(self):
        ledger = DiscoveryLedger()
        ledger.register_transfer(TransferHypothesis(transfer_id="TH-001", source_domain="a", source_mechanism="m"))
        with pytest.raises(DuplicateRegistrationError):
            ledger.register_transfer(TransferHypothesis(transfer_id="TH-001", source_domain="b", source_mechanism="n"))

    def test_duplicate_registration_does_not_overwrite(self):
        """Critical: a failed duplicate registration must NOT replace the original."""
        ledger = DiscoveryLedger()
        original = DiscoveryCase(case_id="DC-001", engine_version="v1.0")
        ledger.register_case(original)
        # Attempt to overwrite with a different object
        with pytest.raises(DuplicateRegistrationError):
            ledger.register_case(DiscoveryCase(case_id="DC-001", engine_version="v2.0-TAMPER"))
        # Original must still be intact
        assert ledger.cases["DC-001"].engine_version == "v1.0"

    def test_versioned_revision_via_unique_id_is_allowed(self):
        """The intended revision path: register a new versioned ID, not overwrite."""
        ledger = DiscoveryLedger()
        ledger.register_case(DiscoveryCase(case_id="DC-001", parent_cases=[]))
        # Revision: new ID, linked to original
        ledger.register_case(DiscoveryCase(case_id="DC-001.v2", parent_cases=["DC-001"]))
        assert "DC-001" in ledger.cases
        assert "DC-001.v2" in ledger.cases
        lineage = ledger.get_lineage("DC-001.v2")
        assert lineage["parents"] == ["DC-001"]


class TestAdversarialFalsifiability:
    """Repair #4: testable scientific objects require non-empty falsifiers."""

    def test_testable_hypothesis_without_falsifier_raises(self):
        """Cannot construct a testable hypothesis without a falsifier."""
        with pytest.raises(UnfalsifiableError):
            Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m", is_testable=True)

    def test_testable_hypothesis_with_empty_falsifier_raises(self):
        """Whitespace-only falsifier is rejected."""
        with pytest.raises(UnfalsifiableError):
            Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m",
                       falsifier="   ", is_testable=True)

    def test_exploratory_hypothesis_without_falsifier_allowed(self):
        """An explicitly EXPLORATORY hypothesis (is_testable=False) is allowed without a falsifier."""
        hyp = Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m", is_testable=False)
        assert hyp.is_testable is False
        assert hyp.falsifier == ""

    def test_testable_hypothesis_with_falsifier_allowed(self):
        """A testable hypothesis WITH a falsifier is constructible."""
        hyp = Hypothesis(
            hypothesis_id="H-001", claim="c", mechanism="m",
            falsifier="If X is observed, the hypothesis is refuted.",
            is_testable=True,
        )
        assert hyp.is_testable is True
        assert hyp.falsifier != ""

    def test_testable_prediction_without_falsifier_raises(self):
        """Cannot construct a testable prediction without a falsifier."""
        with pytest.raises(UnfalsifiableError):
            Prediction(prediction_id="P-001", hypothesis_id="H-001", is_testable=True)

    def test_testable_experiment_without_falsification_condition_raises(self):
        """Cannot construct a testable experiment without a falsification_condition."""
        with pytest.raises(UnfalsifiableError):
            ExperimentProposal(
                experiment_id="E-001", hypothesis_id="H-001",
                objective="o", is_testable=True,
            )

    def test_exploratory_prediction_without_falsifier_allowed(self):
        """An explicitly EXPLORATORY prediction is allowed without a falsifier."""
        pred = Prediction(prediction_id="P-001", hypothesis_id="H-001", is_testable=False)
        assert pred.is_testable is False

    def test_exploratory_experiment_without_falsification_condition_allowed(self):
        """An explicitly EXPLORATORY experiment is allowed without a falsification_condition."""
        exp = ExperimentProposal(
            experiment_id="E-001", hypothesis_id="H-001",
            objective="o", is_testable=False,
        )
        assert exp.is_testable is False


class TestAdversarialUnknownTransition:
    """Repair #6: UNKNOWN cannot jump directly to ESTABLISHED (or any late-ladder state)."""

    def test_unknown_cannot_jump_to_established(self):
        """The escape hatch: UNKNOWN → ESTABLISHED is forbidden."""
        assert EpistemicState.ESTABLISHED not in VALID_TRANSITIONS[EpistemicState.UNKNOWN]

    def test_unknown_cannot_jump_to_replicated(self):
        """UNKNOWN → REPLICATED is forbidden."""
        assert EpistemicState.REPLICATED not in VALID_TRANSITIONS[EpistemicState.UNKNOWN]

    def test_unknown_cannot_jump_to_experimentally_supported(self):
        """UNKNOWN → EXPERIMENTALLY_SUPPORTED is forbidden."""
        assert EpistemicState.EXPERIMENTALLY_SUPPORTED not in VALID_TRANSITIONS[EpistemicState.UNKNOWN]

    def test_unknown_cannot_jump_to_predicted(self):
        """UNKNOWN → PREDICTED is forbidden."""
        assert EpistemicState.PREDICTED not in VALID_TRANSITIONS[EpistemicState.UNKNOWN]

    def test_unknown_can_reenter_early_states(self):
        """UNKNOWN can re-enter OBSERVED, EXTRACTED, INFERRED, HYPOTHESIZED."""
        for s in [EpistemicState.OBSERVED, EpistemicState.EXTRACTED,
                  EpistemicState.INFERRED, EpistemicState.HYPOTHESIZED]:
            assert s in VALID_TRANSITIONS[EpistemicState.UNKNOWN]

    def test_unknown_can_be_refuted(self):
        """UNKNOWN → REFUTED is allowed (a hypothesis can be abandoned)."""
        assert EpistemicState.REFUTED in VALID_TRANSITIONS[EpistemicState.UNKNOWN]

    def test_unknown_cannot_self_loop(self):
        """UNKNOWN → UNKNOWN is forbidden (no-op self-transition)."""
        assert EpistemicState.UNKNOWN not in VALID_TRANSITIONS[EpistemicState.UNKNOWN]


class TestAdversarialTransitionAuditTrail:
    """Repair #7: consequential transitions require non-empty actor/code_sha/evidence/reason."""

    def _full_kwargs(self):
        return dict(actor="test", code_sha="abc123", evidence="passage 1", reason="extraction")

    def test_empty_actor_rejected(self):
        sm = DiscoveryStateMachine("DC-001")
        kw = self._full_kwargs(); kw["actor"] = ""
        with pytest.raises(ValueError, match="actor"):
            sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE, **kw)

    def test_whitespace_actor_rejected(self):
        sm = DiscoveryStateMachine("DC-001")
        kw = self._full_kwargs(); kw["actor"] = "   "
        with pytest.raises(ValueError, match="actor"):
            sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE, **kw)

    def test_empty_code_sha_rejected(self):
        sm = DiscoveryStateMachine("DC-001")
        kw = self._full_kwargs(); kw["code_sha"] = ""
        with pytest.raises(ValueError, match="code_sha"):
            sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE, **kw)

    def test_empty_evidence_rejected(self):
        sm = DiscoveryStateMachine("DC-001")
        kw = self._full_kwargs(); kw["evidence"] = ""
        with pytest.raises(ValueError, match="evidence"):
            sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE, **kw)

    def test_empty_reason_rejected(self):
        sm = DiscoveryStateMachine("DC-001")
        kw = self._full_kwargs(); kw["reason"] = ""
        with pytest.raises(ValueError, match="reason"):
            sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE, **kw)

    def test_all_empty_rejected_with_all_field_names(self):
        """Error message names ALL missing fields, not just the first."""
        sm = DiscoveryStateMachine("DC-001")
        with pytest.raises(ValueError) as exc_info:
            sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE,
                          actor="", code_sha="", evidence="", reason="")
        msg = str(exc_info.value)
        assert "actor" in msg
        assert "code_sha" in msg
        assert "evidence" in msg
        assert "reason" in msg

    def test_failed_transition_also_requires_audit_trail(self):
        """Even FAILED transitions require a full audit trail."""
        sm = DiscoveryStateMachine("DC-001")
        with pytest.raises(ValueError, match="audit trail"):
            sm.transition(DiscoveryState.FAILED, actor="test")

    def test_full_audit_trail_succeeds(self):
        """A transition with all four fields populated succeeds."""
        sm = DiscoveryStateMachine("DC-001")
        sm.transition(DiscoveryState.STRUCTURED_KNOWLEDGE, **self._full_kwargs())
        assert sm.current_state == DiscoveryState.STRUCTURED_KNOWLEDGE
        t = sm.history[-1]
        assert t.actor == "test"
        assert t.code_sha == "abc123"
        assert t.evidence == "passage 1"
        assert t.reason == "extraction"


class TestAdversarialConfidenceBounds:
    """Repair #8: mechanism-edge confidence must be in [0.0, 1.0]."""

    def test_negative_confidence_rejected(self):
        with pytest.raises(ValueError, match="confidence"):
            MechanismEdge(
                edge_id="E1", source_id="N1", target_id="N2",
                edge_type=MechanismEdgeType.CAUSES, confidence=-0.01,
            )

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValueError, match="confidence"):
            MechanismEdge(
                edge_id="E1", source_id="N1", target_id="N2",
                edge_type=MechanismEdgeType.CAUSES, confidence=1.01,
            )

    def test_extreme_confidence_rejected(self):
        """17.3 (the reviewer's example) must be rejected."""
        with pytest.raises(ValueError, match="confidence"):
            MechanismEdge(
                edge_id="E1", source_id="N1", target_id="N2",
                edge_type=MechanismEdgeType.CAUSES, confidence=17.3,
            )

    def test_zero_confidence_allowed(self):
        e = MechanismEdge(
            edge_id="E1", source_id="N1", target_id="N2",
            edge_type=MechanismEdgeType.CAUSES, confidence=0.0,
        )
        assert e.confidence == 0.0

    def test_one_confidence_allowed(self):
        e = MechanismEdge(
            edge_id="E1", source_id="N1", target_id="N2",
            edge_type=MechanismEdgeType.CAUSES, confidence=1.0,
        )
        assert e.confidence == 1.0

    def test_half_confidence_allowed(self):
        e = MechanismEdge(
            edge_id="E1", source_id="N1", target_id="N2",
            edge_type=MechanismEdgeType.CAUSES, confidence=0.5,
        )
        assert e.confidence == 0.5

    def test_prediction_uncertainty_bounds_enforced(self):
        """Prediction.uncertainty is also a declared invariant [0, 1]."""
        with pytest.raises(ValueError, match="uncertainty"):
            Prediction(prediction_id="P-001", hypothesis_id="H-001", uncertainty=-0.1)
        with pytest.raises(ValueError, match="uncertainty"):
            Prediction(prediction_id="P-002", hypothesis_id="H-001", uncertainty=1.5)


class TestAdversarialManifestHash:
    """Repair #5: manifest content addressing uses full SHA-256."""

    def test_manifest_hash_is_64_chars(self):
        """ExperimentManifest.to_hash() returns the full 64-char SHA-256."""
        m = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        h = m.to_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_manifest_hash_is_not_truncated(self):
        """The hash is NOT 16 chars (the previous truncated form)."""
        m = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        h = m.to_hash()
        assert len(h) != 16
        assert len(h) > 32  # well above the old 64-bit truncation

    def test_manifest_hash_deterministic(self):
        m1 = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        m2 = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        assert m1.to_hash() == m2.to_hash()

    def test_manifest_hash_distinguishes_content(self):
        m1 = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        m2 = ExperimentManifest(code_sha="xyz", knowledge_sha="def")
        assert m1.to_hash() != m2.to_hash()


class TestAdversarialGate2Manifest:
    """Repair #3: Gate 2 has a real cryptographic manifest, not just a marker."""

    def test_manifest_file_exists(self):
        """experiments/gate2/MANIFEST.sha256 exists."""
        assert (REPO / "experiments" / "gate2" / "MANIFEST.sha256").exists()

    def test_manifest_contains_protocol_sha(self):
        """The manifest records the frozen Gate 2 protocol SHA."""
        content = (REPO / "experiments" / "gate2" / "MANIFEST.sha256").read_text()
        assert "32691a78dc3bc963937fb21380c9df9c4f1f6c33" in content

    def test_manifest_lists_immutable_marker(self):
        """The manifest hashes the .IMMUTABLE marker."""
        content = (REPO / "experiments" / "gate2" / "MANIFEST.sha256").read_text()
        assert ".IMMUTABLE" in content

    def test_verifier_passes_on_clean_repo(self):
        """The verifier script exits 0 on a clean, untampered repo."""
        import subprocess
        result = subprocess.run(
            ["python", "scripts/verify_gate2_manifest.py"],
            cwd=REPO, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"verifier failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_verifier_detects_tampering(self, tmp_path, monkeypatch):
        """The verifier exits non-zero when a frozen artifact is modified."""
        import subprocess
        # Tamper with .IMMUTABLE
        marker = REPO / "experiments" / "gate2" / ".IMMUTABLE"
        original = marker.read_bytes()
        try:
            marker.write_bytes(original + b"\nTAMPERED FOR TEST\n")
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1, "verifier should have FAILED on tampering"
            assert "FAIL" in result.stdout
        finally:
            marker.write_bytes(original)

    def test_immutable_marker_remains_as_human_signal(self):
        """The .IMMUTABLE marker is preserved (it is now a human signal, not the protection)."""
        assert (REPO / "experiments" / "gate2" / ".IMMUTABLE").exists()


# ============================================================================
# REVISED ACCEPTANCE MATRIX (per independent reviewer)
# Each criterion has an adversarial test proving the invariant is ENFORCED,
# not merely documented.
# ============================================================================

class TestRevisedAcceptanceMatrix:
    """Verify that the reviewer's revised acceptance criteria are met by enforcement."""

    def test_A_immutable_provenance_enforced(self):
        """A: 'the system cannot silently alter provenance' — enforced by ProvenanceImmutableError."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g.commit()
        # Attempt silent mutation
        with pytest.raises(ProvenanceImmutableError):
            g.add_node(ProvenanceNode("n2", "mechanism", "def"))
        # Hash unchanged
        assert g.verify(original_hash)

    def test_C_falsifiable_hypotheses_enforced(self):
        """C: 'a testable hypothesis cannot exist without a falsifier' — enforced by UnfalsifiableError."""
        with pytest.raises(UnfalsifiableError):
            Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m", is_testable=True)

    def test_H_gate2_cryptographic_protection_enforced(self):
        """H: 'the repository can prove the frozen artifact has not changed' — enforced by manifest."""
        import subprocess
        result = subprocess.run(
            ["python", "scripts/verify_gate2_manifest.py"],
            cwd=REPO, capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_B_epistemic_ladder_enforced(self):
        """B: UNKNOWN cannot bypass the epistemic ladder to ESTABLISHED."""
        assert EpistemicState.ESTABLISHED not in VALID_TRANSITIONS[EpistemicState.UNKNOWN]

    def test_F_full_sha256_enforced(self):
        """F: manifest content addressing uses full 64-char SHA-256."""
        m = ExperimentManifest(code_sha="abc", knowledge_sha="def")
        assert len(m.to_hash()) == 64

    def test_G_lineage_traversable_enforced(self):
        """G: lineage is structurally traversable and survives duplicate-registration protection."""
        ledger = DiscoveryLedger()
        ledger.register_case(DiscoveryCase(case_id="DC-001", parent_cases=[]))
        ledger.register_case(DiscoveryCase(case_id="DC-002", parent_cases=["DC-001"]))
        lineage = ledger.get_lineage("DC-002")
        assert lineage["parents"] == ["DC-001"]


# ============================================================================
# SECOND-ROUND ADVERSARIAL TESTS — per independent reviewer's directive
# ============================================================================
# These tests address the four additional issues raised in the second
# independent review:
#
#   #4-extended: Gate 2 freeze-record identity (manifest anchored)
#   #5-extended: out-of-band provenance mutation through retained references
#   #6-extended: state transition enforces falsifier (not just is_testable)
#   #7-extended: verifier fails closed on every tamper scenario


class TestAdversarialOutOfBandProvenanceMutation:
    """Repair #5-extended: out-of-band mutation through retained Python references.

    Python 'immutability' is frequently implemented at the API level while
    the underlying objects remain mutable. These tests mutate the provenance
    graph through retained references to the underlying dict/list, bypassing
    the add_node/add_edge API. The verify() method must detect this.
    """

    def test_mutate_node_via_retained_dict_reference(self):
        """Mutate a node through the retained `g.nodes` dict; verify() must fail."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g.commit()
        # Retain a reference to the underlying dict and mutate out-of-band
        nodes_ref = g.nodes
        nodes_ref["n1"] = ProvenanceNode("n1", "TAMPERED", "xyz")
        assert not g.verify(original_hash), "verify() must detect out-of-band node mutation"

    def test_mutate_node_fields_via_retained_reference(self):
        """Mutate a node's fields through the retained reference; verify() must fail."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g.commit()
        # Mutate the node object in-place through the retained reference
        g.nodes["n1"].node_type = "TAMPERED"
        g.nodes["n1"].content_hash = "xyz"
        assert not g.verify(original_hash), "verify() must detect in-place node field mutation"

    def test_delete_node_via_retained_dict_reference(self):
        """Delete a node through the retained dict; verify() must fail."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g.commit()
        del g.nodes["n1"]
        assert not g.verify(original_hash), "verify() must detect node deletion"

    def test_clear_nodes_via_retained_dict_reference(self):
        """Clear all nodes through the retained dict; verify() must fail."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g.commit()
        g.nodes.clear()
        assert not g.verify(original_hash), "verify() must detect nodes.clear()"

    def test_add_node_via_retained_dict_reference(self):
        """Add a node through the retained dict (bypassing add_node API)."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g.commit()
        # Bypass the immutability check by writing directly to the dict
        g.nodes["n2"] = ProvenanceNode("n2", "sneaky", "def")
        assert not g.verify(original_hash), "verify() must detect out-of-band node addition"

    def test_mutate_edge_list_via_retained_reference(self):
        """Mutate the edge list through the retained reference; verify() must fail."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        g.add_node(ProvenanceNode("n2", "mechanism", "def"))
        g.add_edge(ProvenanceEdge("e1", "n1", "n2", "DERIVES_FROM", "x", actor="t"))
        original_hash = g.commit()
        # Append an edge out-of-band
        g.edges.append(ProvenanceEdge("e2", "n1", "n2", "SUPPORTS", "sneaky", actor="t"))
        assert not g.verify(original_hash), "verify() must detect out-of-band edge addition"

    def test_clear_edges_via_retained_reference(self):
        """Clear all edges through the retained reference; verify() must fail."""
        g = ProvenanceGraph()
        g.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        g.add_node(ProvenanceNode("n2", "mechanism", "def"))
        g.add_edge(ProvenanceEdge("e1", "n1", "n2", "DERIVES_FROM", "x", actor="t"))
        original_hash = g.commit()
        g.edges.clear()
        assert not g.verify(original_hash), "verify() must detect edges.clear()"

    def test_case_verify_detects_out_of_band_node_mutation(self):
        """DiscoveryCase.verify_provenance() detects out-of-band mutation."""
        case = DiscoveryCase(case_id="DC-001")
        case.provenance.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        case.commit_provenance()
        assert case.verify_provenance()
        # Out-of-band mutation through retained reference
        case.provenance.nodes["n1"].content_hash = "TAMPERED"
        assert not case.verify_provenance()

    def test_fork_does_not_allow_mutation_of_original(self):
        """A fork's mutations must not propagate back to the original graph."""
        g1 = ProvenanceGraph()
        g1.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g1.commit()
        g2 = g1.fork()
        # Mutate the fork
        g2.add_node(ProvenanceNode("n2", "mechanism", "def"))
        # Original must be unaffected
        assert g1.verify(original_hash), "fork mutation must not affect original"
        assert g1.content_hash() == original_hash

    def test_fork_node_objects_are_independent(self):
        """Fork must deep-copy node objects so in-place mutation of the fork
        does not affect the original's nodes."""
        g1 = ProvenanceGraph()
        g1.add_node(ProvenanceNode("n1", "source_passage", "abc"))
        original_hash = g1.commit()
        g2 = g1.fork()
        # Mutate the fork's node in-place
        g2.nodes["n1"].content_hash = "TAMPERED"
        # Original must be unaffected
        assert g1.verify(original_hash), "fork in-place mutation must not affect original"
        assert g1.nodes["n1"].content_hash == "abc"


class TestAdversarialPipelineEntryFalsifier:
    """Repair #6-extended: transition INTO scientific-pipeline states requires a falsifier.

    The construction-time check on is_testable is NOT sufficient. A future
    engine could construct an exploratory Hypothesis (is_testable=False,
    falsifier="") and later attempt to move it into the scientific pipeline.
    The transition itself must reject that.
    """

    def _advance_to_gate_c(self, sm, hyp=None):
        """Advance a state machine from RAW_EVIDENCE to GATE_C."""
        for s in [DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.MECHANISM,
                  DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.CANDIDATE_DISCOVERY,
                  DiscoveryState.GATE_A, DiscoveryState.GATE_B, DiscoveryState.GATE_C]:
            sm.transition(s, actor="test", code_sha="abc123",
                          evidence="passage 1", reason="extraction",
                          hypothesis=hyp)

    def test_testable_hypothesis_transition_requires_hypothesis_arg(self):
        """Transition to TESTABLE_HYPOTHESIS without hypothesis arg is rejected."""
        sm = DiscoveryStateMachine("DC-001")
        self._advance_to_gate_c(sm)
        with pytest.raises(UnfalsifiableError, match="hypothesis"):
            sm.transition(DiscoveryState.TESTABLE_HYPOTHESIS,
                          actor="test", code_sha="abc123",
                          evidence="passage 1", reason="extraction")

    def test_testable_hypothesis_transition_rejects_unfalsifiable_hypothesis(self):
        """Transition to TESTABLE_HYPOTHESIS with an exploratory (no-falsifier) hypothesis is rejected."""
        sm = DiscoveryStateMachine("DC-001")
        self._advance_to_gate_c(sm)
        # An exploratory hypothesis (is_testable=False, falsifier="")
        hyp = Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m", is_testable=False)
        with pytest.raises(UnfalsifiableError, match="no falsifier"):
            sm.transition(DiscoveryState.TESTABLE_HYPOTHESIS,
                          actor="test", code_sha="abc123",
                          evidence="passage 1", reason="extraction",
                          hypothesis=hyp)

    def test_testable_hypothesis_transition_rejects_whitespace_falsifier(self):
        """Transition to TESTABLE_HYPOTHESIS with whitespace-only falsifier is rejected."""
        sm = DiscoveryStateMachine("DC-001")
        self._advance_to_gate_c(sm)
        hyp = Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m",
                         falsifier="   ", is_testable=False)
        with pytest.raises(UnfalsifiableError, match="no falsifier"):
            sm.transition(DiscoveryState.TESTABLE_HYPOTHESIS,
                          actor="test", code_sha="abc123",
                          evidence="passage 1", reason="extraction",
                          hypothesis=hyp)

    def test_testable_hypothesis_transition_accepts_falsifiable_hypothesis(self):
        """Transition to TESTABLE_HYPOTHESIS with a valid falsifier succeeds."""
        sm = DiscoveryStateMachine("DC-001")
        self._advance_to_gate_c(sm)
        hyp = Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m",
                         falsifier="If X is observed, the hypothesis is refuted.")
        sm.transition(DiscoveryState.TESTABLE_HYPOTHESIS,
                      actor="test", code_sha="abc123",
                      evidence="passage 1", reason="extraction",
                      hypothesis=hyp)
        assert sm.current_state == DiscoveryState.TESTABLE_HYPOTHESIS

    def test_experiment_transition_requires_hypothesis_with_falsifier(self):
        """Every pipeline state (EXPERIMENT and beyond) requires a falsifiable hypothesis."""
        sm = DiscoveryStateMachine("DC-001")
        self._advance_to_gate_c(sm)
        hyp = Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m",
                         falsifier="If X is observed, the hypothesis is refuted.")
        sm.transition(DiscoveryState.TESTABLE_HYPOTHESIS,
                      actor="test", code_sha="abc123",
                      evidence="passage 1", reason="extraction",
                      hypothesis=hyp)
        # Now try to advance to EXPERIMENT without hypothesis — must fail
        with pytest.raises(UnfalsifiableError, match="hypothesis"):
            sm.transition(DiscoveryState.EXPERIMENT,
                          actor="test", code_sha="abc123",
                          evidence="passage 1", reason="extraction")

    def test_experiment_transition_with_unfalsifiable_hypothesis_rejected(self):
        """Even mid-pipeline, swapping to an unfalsifiable hypothesis is rejected."""
        sm = DiscoveryStateMachine("DC-001")
        self._advance_to_gate_c(sm)
        good_hyp = Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m",
                              falsifier="If X is observed, refuted.")
        sm.transition(DiscoveryState.TESTABLE_HYPOTHESIS,
                      actor="test", code_sha="abc123",
                      evidence="passage 1", reason="extraction",
                      hypothesis=good_hyp)
        # Now try EXPERIMENT with a BAD hypothesis
        bad_hyp = Hypothesis(hypothesis_id="H-002", claim="c2", mechanism="m2",
                             is_testable=False)
        with pytest.raises(UnfalsifiableError, match="no falsifier"):
            sm.transition(DiscoveryState.EXPERIMENT,
                          actor="test", code_sha="abc123",
                          evidence="passage 1", reason="extraction",
                          hypothesis=bad_hyp)

    def test_non_pipeline_states_do_not_require_hypothesis(self):
        """States before TESTABLE_HYPOTHESIS (RAW_EVIDENCE through GATE_C) do NOT require a hypothesis."""
        sm = DiscoveryStateMachine("DC-001")
        # These should all succeed without a hypothesis argument
        for s in [DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.MECHANISM,
                  DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.CANDIDATE_DISCOVERY,
                  DiscoveryState.GATE_A, DiscoveryState.GATE_B, DiscoveryState.GATE_C]:
            sm.transition(s, actor="test", code_sha="abc123",
                          evidence="passage 1", reason="extraction")
        assert sm.current_state == DiscoveryState.GATE_C

    def test_failed_transition_does_not_require_hypothesis(self):
        """Transition to FAILED does not require a hypothesis (failure can happen at any stage)."""
        sm = DiscoveryStateMachine("DC-001")
        sm.transition(DiscoveryState.FAILED,
                      actor="test", code_sha="abc123",
                      evidence="passage 1", reason="early failure")
        assert sm.current_state == DiscoveryState.FAILED

    def test_scientific_pipeline_states_set_is_correct(self):
        """SCIENTIFIC_PIPELINE_STATES contains exactly the post-GATE_C evaluation states."""
        expected = {
            DiscoveryState.TESTABLE_HYPOTHESIS,
            DiscoveryState.EXPERIMENT,
            DiscoveryState.RESULT,
            DiscoveryState.REPLICATION,
            DiscoveryState.VALIDATED_DISCOVERY,
            DiscoveryState.INVENTION_CANDIDATE,
        }
        assert SCIENTIFIC_PIPELINE_STATES == expected


class TestAdversarialGate2FreezeRecord:
    """Repair #4-extended + #7-extended: freeze-record anchoring + fail-closed verifier."""

    def test_freeze_record_file_exists(self):
        """experiments/gate2/FREEZE_RECORD.json exists."""
        assert (REPO / "experiments" / "gate2" / "FREEZE_RECORD.json").exists()

    def test_freeze_record_is_valid_json(self):
        """FREEZE_RECORD.json is valid JSON."""
        import json
        record = json.loads((REPO / "experiments" / "gate2" / "FREEZE_RECORD.json").read_text())
        assert isinstance(record, dict)

    def test_freeze_record_has_required_fields(self):
        """FREEZE_RECORD.json has all required fields."""
        import json
        record = json.loads((REPO / "experiments" / "gate2" / "FREEZE_RECORD.json").read_text())
        for field in ["schema_version", "protocol_sha", "cases_sha", "manifest_sha"]:
            assert field in record, f"freeze record missing {field}"

    def test_freeze_record_manifest_sha_matches_actual_manifest(self):
        """The manifest_sha in the freeze record matches the actual manifest content hash."""
        import json
        import hashlib
        record = json.loads((REPO / "experiments" / "gate2" / "FREEZE_RECORD.json").read_text())
        manifest_content = (REPO / "experiments" / "gate2" / "MANIFEST.sha256").read_text()
        actual_manifest_sha = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()
        assert record["manifest_sha"] == actual_manifest_sha

    def test_freeze_record_protocol_sha_matches_expected(self):
        """The protocol_sha in the freeze record matches the frozen protocol."""
        import json
        record = json.loads((REPO / "experiments" / "gate2" / "FREEZE_RECORD.json").read_text())
        assert record["protocol_sha"] == "32691a78dc3bc963937fb21380c9df9c4f1f6c33"

    def test_verifier_passes_on_clean_repo(self):
        """Verifier exits 0 on a clean, untampered repo."""
        import subprocess
        result = subprocess.run(
            ["python", "scripts/verify_gate2_manifest.py"],
            cwd=REPO, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"verifier failed: {result.stderr}"
        assert "PASS" in result.stdout

    def test_verifier_detects_artifact_modification(self):
        """Verifier fails when an artifact is modified."""
        import subprocess
        marker = REPO / "experiments" / "gate2" / ".IMMUTABLE"
        original = marker.read_bytes()
        try:
            marker.write_bytes(original + b"\nTAMPERED\n")
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "FAIL" in result.stdout
            assert "modified" in result.stdout.lower()
        finally:
            marker.write_bytes(original)

    def test_verifier_detects_artifact_deletion(self):
        """Verifier fails when an artifact is deleted."""
        import subprocess
        marker = REPO / "experiments" / "gate2" / ".IMMUTABLE"
        original = marker.read_bytes()
        try:
            marker.unlink()
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "FAIL" in result.stdout
            assert "missing" in result.stdout.lower()
        finally:
            marker.write_bytes(original)

    def test_verifier_detects_unexpected_artifact(self):
        """Verifier fails when an unexpected artifact is present."""
        import subprocess
        unexpected = REPO / "experiments" / "gate2" / "UNEXPECTED_TEST_FILE.txt"
        try:
            unexpected.write_text("sneaky")
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "FAIL" in result.stdout
            assert "unexpected" in result.stdout.lower()
        finally:
            if unexpected.exists():
                unexpected.unlink()

    def test_verifier_detects_manifest_substitution(self):
        """Verifier fails when manifest is regenerated to bless a tampered artifact.

        This is the key attack vector: an attacker modifies an artifact AND
        regenerates the manifest (but not the freeze record). The verifier
        must detect the manifest_sha mismatch.
        """
        import subprocess
        import sys
        marker = REPO / "experiments" / "gate2" / ".IMMUTABLE"
        manifest = REPO / "experiments" / "gate2" / "MANIFEST.sha256"
        freeze = REPO / "experiments" / "gate2" / "FREEZE_RECORD.json"
        marker_orig = marker.read_bytes()
        manifest_orig = manifest.read_bytes()
        freeze_orig = freeze.read_bytes()
        try:
            # Tamper the artifact
            marker.write_bytes(marker_orig + b"\nTAMPERED\n")
            # Regenerate ONLY the manifest (not the freeze record)
            sys.path.insert(0, str(REPO / "scripts"))
            from verify_gate2_manifest import generate_manifest_content
            content, _ = generate_manifest_content()
            manifest.write_text(content)
            # The freeze record still has the OLD manifest_sha
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1, "verifier should detect manifest substitution"
            assert "MANIFEST SUBSTITUTION" in result.stdout
        finally:
            marker.write_bytes(marker_orig)
            manifest.write_bytes(manifest_orig)
            freeze.write_bytes(freeze_orig)
            # Clean up sys.path
            if str(REPO / "scripts") in sys.path:
                sys.path.remove(str(REPO / "scripts"))

    def test_verifier_detects_freeze_record_deletion(self):
        """Verifier fails when the freeze record is deleted."""
        import subprocess
        freeze = REPO / "experiments" / "gate2" / "FREEZE_RECORD.json"
        original = freeze.read_bytes()
        try:
            freeze.unlink()
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "FAIL" in result.stdout
        finally:
            freeze.write_bytes(original)

    def test_verifier_detects_manifest_deletion(self):
        """Verifier fails when the manifest is deleted."""
        import subprocess
        manifest = REPO / "experiments" / "gate2" / "MANIFEST.sha256"
        original = manifest.read_bytes()
        try:
            manifest.unlink()
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "FAIL" in result.stdout
        finally:
            manifest.write_bytes(original)

    def test_verifier_detects_malformed_manifest_bad_hash(self):
        """Verifier fails when the manifest has a malformed hash line."""
        import subprocess
        manifest = REPO / "experiments" / "gate2" / "MANIFEST.sha256"
        original = manifest.read_bytes()
        try:
            manifest.write_text("nothexhash  somefile\n")
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "malformed" in result.stdout.lower()
        finally:
            manifest.write_bytes(original)

    def test_verifier_detects_duplicate_manifest_entries(self):
        """Verifier fails when the manifest has duplicate entries."""
        import subprocess
        manifest = REPO / "experiments" / "gate2" / "MANIFEST.sha256"
        original = manifest.read_bytes()
        try:
            content = manifest.read_text()
            for line in content.splitlines():
                if ".IMMUTABLE" in line and not line.startswith("#"):
                    content = content + line + "\n"
                    break
            manifest.write_text(content)
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "duplicate" in result.stdout.lower()
        finally:
            manifest.write_bytes(original)

    def test_verifier_detects_protocol_sha_mismatch(self):
        """Verifier fails when the freeze record has the wrong protocol SHA."""
        import subprocess
        import json
        freeze = REPO / "experiments" / "gate2" / "FREEZE_RECORD.json"
        original = freeze.read_bytes()
        try:
            record = json.loads(freeze.read_text())
            record["protocol_sha"] = "0" * 40
            freeze.write_text(json.dumps(record, indent=2) + "\n")
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "protocol SHA mismatch" in result.stdout
        finally:
            freeze.write_bytes(original)

    def test_verifier_detects_malformed_freeze_record_missing_field(self):
        """Verifier fails when the freeze record is missing a required field."""
        import subprocess
        import json
        freeze = REPO / "experiments" / "gate2" / "FREEZE_RECORD.json"
        original = freeze.read_bytes()
        try:
            record = json.loads(freeze.read_text())
            del record["manifest_sha"]
            freeze.write_text(json.dumps(record, indent=2) + "\n")
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "missing" in result.stdout.lower()
        finally:
            freeze.write_bytes(original)

    def test_verifier_detects_manifest_edited_by_hand(self):
        """Verifier fails when the manifest is edited by hand (manifest_sha mismatch)."""
        import subprocess
        manifest = REPO / "experiments" / "gate2" / "MANIFEST.sha256"
        original = manifest.read_bytes()
        try:
            content = manifest.read_text()
            content = "# TAMPERED COMMENT\n" + content
            manifest.write_text(content)
            result = subprocess.run(
                ["python", "scripts/verify_gate2_manifest.py"],
                cwd=REPO, capture_output=True, text=True,
            )
            assert result.returncode == 1
            assert "MANIFEST SUBSTITUTION" in result.stdout
        finally:
            manifest.write_bytes(original)


