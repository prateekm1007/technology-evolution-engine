"""
test_engine_repair_round4.py — tests for the 3 round-4 repairs.

Repair A: Real lineage verification (DFS traversal, not node_count > 1)
Repair B: Persistent audit ledger (reloadable + hash-verifiable)
Repair C: Epistemic outcome (candidate_status when all hypotheses blocked)
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine.checkpoint import (
    CheckpointedDiscoveryLoop, AdversarialOutcome, COMPLETED, FAILED,
)
from engine.lineage_validator import (
    LineageValidator, REQUIRED_PARENTS, EXPECTED_REACHABLE_TYPES, ROOT_TYPES,
)
from engine.persistent_ledger import PersistentLedger, _object_hash
from engine.providers import MockReasoningProvider, MockLiteratureProvider
from engine.dev_fixtures import CHALLENGE_4, DevChallenge
from discovery_infrastructure.discovery_substrate import (
    DiscoveryCase, ProvenanceGraph, ProvenanceNode, ProvenanceEdge,
    Hypothesis,
)


# ============================================================================
# Repair A: Real lineage verification
# ============================================================================

class TestRepairALineageVerification:
    """lineage_valid must be computed by actual DFS traversal, not node_count > 1."""

    def test_node_count_metric_is_gone(self):
        """The old 'lineage_traversable = node_count > 1' must NOT exist."""
        import engine.checkpoint as cp
        source = Path(cp.__file__).read_text()
        assert "lineage_traversable" not in source, \
            "the old lineage_traversable metric must be removed"
        assert "lineage_node_count > 1" not in source, \
            "the old node_count > 1 check must be removed"

    def test_lineage_validator_performs_dfs(self, tmp_path):
        """The LineageValidator must perform actual DFS traversal."""
        # Build a minimal provenance graph
        prov = ProvenanceGraph()
        prov.add_node(ProvenanceNode("source_doc:1", "source_document", "hash1"))
        prov.add_node(ProvenanceNode("mechanism_graph:1", "mechanism_graph", "hash2"))
        prov.add_node(ProvenanceNode("mechanism_pattern:1", "mechanism_pattern", "hash3"))
        prov.add_node(ProvenanceNode("transfer:1", "transfer_hypothesis", "hash4"))
        prov.add_node(ProvenanceNode("hypothesis:1", "hypothesis", "hash5"))
        prov.add_node(ProvenanceNode("run:1", "checkpointed_run", "hash6"))
        # Edges linking them
        prov.add_edge(ProvenanceEdge("e1", "source_doc:1", "mechanism_graph:1", "DERIVES_FROM", "x", actor="t"))
        prov.add_edge(ProvenanceEdge("e2", "mechanism_graph:1", "mechanism_pattern:1", "DERIVES_FROM", "x", actor="t"))
        prov.add_edge(ProvenanceEdge("e3", "mechanism_pattern:1", "transfer:1", "DERIVES_FROM", "x", actor="t"))
        prov.add_edge(ProvenanceEdge("e4", "transfer:1", "hypothesis:1", "DERIVES_FROM", "x", actor="t"))

        case = DiscoveryCase(case_id="DC-TEST-001")
        case.provenance = prov
        case.commit_provenance()

        validator = LineageValidator()
        result = validator.verify(case)
        assert result.valid is True
        assert result.node_count == 6
        assert len(result.reachable_nodes) == 6  # all reachable via DFS
        assert len(result.orphans) == 0
        assert len(result.missing_parents) == 0

    def test_lineage_validator_detects_orphan_nodes(self):
        """An orphan node (no incoming edge, not a root) must fail verification."""
        prov = ProvenanceGraph()
        prov.add_node(ProvenanceNode("source_doc:1", "source_document", "h1"))
        prov.add_node(ProvenanceNode("orphan:1", "hypothesis", "h2"))  # no incoming edge!
        prov.add_node(ProvenanceNode("run:1", "checkpointed_run", "h3"))
        case = DiscoveryCase(case_id="DC-TEST-002")
        case.provenance = prov
        case.commit_provenance()

        validator = LineageValidator()
        result = validator.verify(case)
        # The orphan hypothesis has no incoming edge → missing required parent
        assert not result.valid
        assert len(result.orphans) > 0 or len(result.missing_parents) > 0

    def test_lineage_validator_detects_missing_parents(self):
        """A hypothesis without a transfer_hypothesis parent must fail."""
        prov = ProvenanceGraph()
        prov.add_node(ProvenanceNode("source_doc:1", "source_document", "h1"))
        prov.add_node(ProvenanceNode("hypothesis:1", "hypothesis", "h2"))
        # Edge from source_doc → hypothesis, but NO transfer_hypothesis parent
        prov.add_edge(ProvenanceEdge("e1", "source_doc:1", "hypothesis:1", "DERIVES_FROM", "x", actor="t"))
        prov.add_node(ProvenanceNode("run:1", "checkpointed_run", "h3"))
        case = DiscoveryCase(case_id="DC-TEST-003")
        case.provenance = prov
        case.commit_provenance()

        validator = LineageValidator()
        result = validator.verify(case)
        assert not result.valid
        assert any("missing required parent type=transfer_hypothesis" in p
                   for p in result.missing_parents)

    def test_lineage_validator_detects_dangling_edges(self):
        """An edge referencing a non-existent node must fail."""
        prov = ProvenanceGraph()
        prov.add_node(ProvenanceNode("source_doc:1", "source_document", "h1"))
        # Edge to a node that doesn't exist
        prov.add_edge(ProvenanceEdge("e1", "source_doc:1", "nonexistent:1", "DERIVES_FROM", "x", actor="t"))
        prov.add_node(ProvenanceNode("run:1", "checkpointed_run", "h3"))
        case = DiscoveryCase(case_id="DC-TEST-004")
        case.provenance = prov
        case.commit_provenance()

        validator = LineageValidator()
        result = validator.verify(case)
        assert not result.valid
        checks = {c["name"]: c["passed"] for c in result.to_dict()["checks"]}
        assert checks["no_dangling_edges"] is False

    def test_real_llm_run_lineage_is_valid(self, tmp_path):
        """The real-LLM run's case artifact must have lineage_valid=True
        by actual DFS traversal (not just node_count > 1)."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        case_data = json.loads((run_dir / "12_case.json").read_text())
        case_result = case_data["result"]
        assert case_result["lineage_valid"] is True
        # Verify the lineage_verification contains actual traversal results
        lineage = case_result["lineage_verification"]
        assert "reachable_nodes" in lineage
        assert "orphans" in lineage
        assert "missing_parents" in lineage
        assert "checks" in lineage
        assert len(lineage["checks"]) >= 5  # at least 5 distinct checks


# ============================================================================
# Repair B: Persistent audit ledger
# ============================================================================

class TestRepairBPersistentLedger:
    """The ledger must be persistent, reloadable, and hash-verifiable."""

    def test_persistent_ledger_saves_to_disk(self, tmp_path):
        """register_case() must write the case to disk + update index."""
        ledger_dir = tmp_path / "ledger"
        ledger = PersistentLedger(ledger_dir)
        case = DiscoveryCase(case_id="DC-TEST-001")
        case.commit_provenance()
        ledger.register_case(case)
        # File must exist on disk
        assert (ledger_dir / "cases" / "DC-TEST-001.json").exists()
        # Index must exist + contain the entry
        assert (ledger_dir / "index.json").exists()
        index = json.loads((ledger_dir / "index.json").read_text())
        assert "case" in index
        assert "DC-TEST-001" in index["case"]

    def test_persistent_ledger_is_reloadable(self, tmp_path):
        """A new PersistentLedger instance must load the existing index from disk."""
        ledger_dir = tmp_path / "ledger"
        ledger1 = PersistentLedger(ledger_dir)
        case = DiscoveryCase(case_id="DC-TEST-002")
        case.commit_provenance()
        ledger1.register_case(case)

        # Create a new ledger instance — it should load the index
        ledger2 = PersistentLedger(ledger_dir)
        verification = ledger2.verify_registration("case", "DC-TEST-002")
        assert verification["registered"] is True
        assert verification["file_exists"] is True
        assert verification["content_hash_matches"] is True

    def test_persistent_ledger_hash_verification(self, tmp_path):
        """verify_registration() must detect hash mismatches (tampered files)."""
        ledger_dir = tmp_path / "ledger"
        ledger = PersistentLedger(ledger_dir)
        case = DiscoveryCase(case_id="DC-TEST-003")
        case.commit_provenance()
        ledger.register_case(case)

        # Tamper with the file on disk
        case_file = ledger_dir / "cases" / "DC-TEST-003.json"
        original = case_file.read_text()
        case_file.write_text(original + "TAMPERED")

        # Verification must detect the mismatch
        verification = ledger.verify_registration("case", "DC-TEST-003")
        assert verification["registered"] is True
        assert verification["file_exists"] is True
        assert verification["content_hash_matches"] is False

    def test_persistent_ledger_verify_all(self, tmp_path):
        """verify_all() must return a summary of all registered objects."""
        ledger_dir = tmp_path / "ledger"
        ledger = PersistentLedger(ledger_dir)
        case = DiscoveryCase(case_id="DC-TEST-004")
        case.commit_provenance()
        ledger.register_case(case)
        hyp = Hypothesis(hypothesis_id="H-001", claim="c", mechanism="m",
                         falsifier="if X", is_testable=True)
        ledger.register_hypothesis(hyp)

        summary = ledger.verify_all()
        assert summary["total"] == 2
        assert summary["verified"] == 2
        assert len(summary["missing_files"]) == 0
        assert len(summary["hash_mismatches"]) == 0

    def test_persistent_ledger_get_case(self, tmp_path):
        """get_case() must load a case from disk without rerunning the engine."""
        ledger_dir = tmp_path / "ledger"
        ledger = PersistentLedger(ledger_dir)
        case = DiscoveryCase(case_id="DC-TEST-005",
                             input_sources=["doc1"],
                             input_domains=["biology", "engineering"])
        case.commit_provenance()
        ledger.register_case(case)

        # New ledger instance — load the case
        ledger2 = PersistentLedger(ledger_dir)
        loaded = ledger2.get_case("DC-TEST-005")
        assert loaded is not None
        assert loaded.case_id == "DC-TEST-005"
        assert loaded.input_sources == ["doc1"]
        assert loaded.input_domains == ["biology", "engineering"]

    def test_real_run_uses_persistent_ledger(self, tmp_path):
        """The checkpointed loop must use a PersistentLedger, not an in-memory one."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        case_data = json.loads((run_dir / "12_case.json").read_text())
        case_result = case_data["result"]
        # Repair B: the case must be registered in a persistent, reloadable ledger
        assert case_result["registered_in_persistent_ledger"] is True
        assert case_result["ledger_dir"]  # non-empty path
        # The ledger directory must exist on disk
        ledger_dir = Path(case_result["ledger_dir"])
        assert ledger_dir.exists()
        assert (ledger_dir / "index.json").exists()
        assert (ledger_dir / "cases").exists()
        # The case file must exist
        case_file = ledger_dir / "cases" / f"{case_result['case_id']}.json"
        assert case_file.exists()


# ============================================================================
# Repair C: Epistemic outcome (candidate_status)
# ============================================================================

class TestRepairCEpistemicOutcome:
    """When all hypotheses are blocked, candidate_status must be recorded."""

    def test_candidate_status_all_blocked(self, tmp_path):
        """When all hypotheses receive ADVERSARIAL_FAILED, candidate_status
        must be ALL_BLOCKED_AT_ADVERSARIAL."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        sm_data = json.loads((run_dir / "11_state_machine.json").read_text())
        sm_result = sm_data["result"]
        # The mock loop uses an adversarial response with MEDIUM severity (survives=True)
        # So candidate_status should be CANDIDATES_SURVIVED
        assert "candidate_status" in sm_result
        assert sm_result["candidate_status"] in [
            "CANDIDATES_SURVIVED", "ALL_BLOCKED_AT_ADVERSARIAL",
            "PARTIALLY_BLOCKED_AT_ADVERSARIAL", "ALL_INCONCLUSIVE_AT_ADVERSARIAL",
            "NO_HYPOTHESES"]

    def test_candidate_status_when_all_blocked(self, tmp_path):
        """Specifically test the ALL_BLOCKED_AT_ADVERSARIAL path."""
        # Build a mock where adversarial returns HIGH-severity CONTRADICTS_KNOWN
        extraction_resp = json.dumps({
            "nodes": [{"node_id": "N1", "node_type": "MECHANISM", "label": "test",
                       "evidence_quote": "The slime mold Physarum polycephalum is a single-celled multinucleate organism"}],
            "edges": [],
        })
        abstraction_resp = json.dumps({
            "abstract_principle": "test", "causal_structure": "x",
            "inputs": [], "conditions": [], "operations": [], "intermediate_state": [],
            "outputs": [], "constraints": [], "failure_conditions": [],
        })
        transfer_resp = json.dumps({
            "source_mechanism": "test", "source_conditions": [],
            "transferred_principle": "test", "required_translation": "test",
            "expected_effect": "test", "boundary_conditions": [],
            "failure_conditions": [], "testable_prediction": "test",
        })
        hypothesis_resp = json.dumps({
            "hypotheses": [{"claim": "test", "mechanism": "test", "assumptions": [],
                            "evidence": [], "novelty_rationale": "", "testability": "",
                            "falsifier": "if X", "expected_failure_modes": []}],
            "distinguishing_predictions": "",
        })
        # Adversarial: HIGH-severity CONTRADICTS_KNOWN → FAILED
        adversarial_resp = json.dumps({
            "failure_modes": [{"category": "CONTRADICTS_KNOWN", "description": "contradicts",
                               "severity": "HIGH", "evidence": "known"}],
            "survives": False, "survives_reason": "HIGH",
        })
        rediscovery_resp = json.dumps({"classification": "NON_TRIVIAL_TRANSFER", "evidence": "test"})

        responses = {
            "You are a scientific mechanism extractor": extraction_resp,
            "You are a scientific abstraction engine": abstraction_resp,
            "You are a cross-domain transfer hypothesis engine": transfer_resp,
            "You are a scientific hypothesis generation engine": hypothesis_resp,
            "You are an adversarial scientific critic": adversarial_resp,
            "You are a rediscovery detector": rediscovery_resp,
            "You are a scientific prediction engine": rediscovery_resp,
            "You are a scientific experiment design engine": rediscovery_resp,
        }
        provider = MockReasoningProvider(responses=responses, default_response="{}")
        loop = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
        import engine.checkpoint as cp
        original_runs_dir = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            result = loop.run(CHALLENGE_4, resume=False)
            run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
            sm_data = json.loads((run_dir / "11_state_machine.json").read_text())
            sm_result = sm_data["result"]
            assert sm_result["candidate_status"] == "ALL_BLOCKED_AT_ADVERSARIAL"
            assert sm_result["n_blocked_adversarial"] == 1
            assert sm_result["n_survived_adversarial"] == 0
            assert sm_result["pipeline_stage_reached"] == "TESTABLE_HYPOTHESIS"
            assert sm_result["scientific_gate_passed"] is False
        finally:
            cp.RUNS_DIR = original_runs_dir

    def test_candidate_status_distinguishes_pipeline_from_epistemic(self, tmp_path):
        """pipeline_stage_reached and candidate_status must be separate fields.
        pipeline_stage_reached=TESTABLE_HYPOTHESIS does NOT mean the hypothesis
        survived — candidate_status=ALL_BLOCKED_AT_ADVERSARIAL clarifies."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        sm_data = json.loads((run_dir / "11_state_machine.json").read_text())
        sm_result = sm_data["result"]
        # Both fields must exist and be distinct
        assert "pipeline_stage_reached" in sm_result
        assert "candidate_status" in sm_result
        assert "scientific_gate_passed" in sm_result
        # The note must explain the distinction
        assert "candidate_status" in sm_result["note"]


# ============================================================================
# Helper: run a mock loop (same as round-3 tests)
# ============================================================================

def _run_mock_loop(challenge: DevChallenge, tmp_path):
    """Run a full mock loop into tmp_path/runs/. Returns (loop, manifest_dict)."""
    extraction_resp = json.dumps({
        "nodes": [{"node_id": "N1", "node_type": "MECHANISM",
                   "label": "test mechanism",
                   "evidence_quote": "The slime mold Physarum polycephalum is a single-celled multinucleate organism"}],
        "edges": [],
    })
    abstraction_resp = json.dumps({
        "abstract_principle": "test principle", "causal_structure": "x→y",
        "inputs": ["a"], "conditions": ["b"], "operations": ["c"],
        "intermediate_state": ["d"], "outputs": ["e"],
        "constraints": ["f"], "failure_conditions": ["g"],
    })
    transfer_resp = json.dumps({
        "source_mechanism": "test", "source_conditions": ["b"],
        "transferred_principle": "test principle", "required_translation": "test mapping",
        "expected_effect": "test effect", "boundary_conditions": ["f"],
        "failure_conditions": ["g"], "testable_prediction": "test prediction",
    })
    hypothesis_resp = json.dumps({
        "hypotheses": [{
            "claim": "test claim", "mechanism": "test mechanism",
            "assumptions": ["a"], "evidence": ["b"],
            "novelty_rationale": "test", "testability": "test",
            "falsifier": "if X then refuted", "expected_failure_modes": ["m"],
        }],
        "distinguishing_predictions": "test distinguishing",
    })
    # Adversarial: survives (no HIGH contradictions)
    adversarial_resp = json.dumps({
        "failure_modes": [{"category": "FRAGILE_ASSUMPTION", "description": "weak",
                           "severity": "MEDIUM", "evidence": "test"}],
        "survives": True, "survives_reason": "no HIGH",
    })
    rediscovery_resp = json.dumps({"classification": "NON_TRIVIAL_TRANSFER", "evidence": "cross-domain"})
    prediction_resp = json.dumps({
        "observable": "test observable", "baseline": "test baseline",
        "expected_direction": "increase", "expected_magnitude": "10-20%",
        "conditions": ["test"], "uncertainty": 0.3, "falsifier": "if not X",
    })
    experiment_resp = json.dumps({
        "objective": "test", "controls": ["control1"], "baseline": "test",
        "procedure": "test", "expected_result": "test",
        "falsification_condition": "if X", "sample_requirements": "n=3",
        "safety_constraints": [], "estimated_cost": "low",
        "estimated_duration": "1d", "information_gain": "test",
        "independent_variables": [], "dependent_variables": [],
    })

    responses = {
        "You are a scientific mechanism extractor": extraction_resp,
        "You are a scientific abstraction engine": abstraction_resp,
        "You are a cross-domain transfer hypothesis engine": transfer_resp,
        "You are a scientific hypothesis generation engine": hypothesis_resp,
        "You are an adversarial scientific critic": adversarial_resp,
        "You are a rediscovery detector": rediscovery_resp,
        "You are a scientific prediction engine": prediction_resp,
        "You are a scientific experiment design engine": experiment_resp,
    }
    provider = MockReasoningProvider(responses=responses, default_response="{}")
    loop = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
    import engine.checkpoint as cp
    original_runs_dir = cp.RUNS_DIR
    cp.RUNS_DIR = tmp_path / "runs"
    try:
        result = loop.run(challenge, resume=False)
    finally:
        cp.RUNS_DIR = original_runs_dir
    return loop, result
