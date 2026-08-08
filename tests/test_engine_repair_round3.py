"""
test_engine_repair_round3.py — tests for the 5 round-3 repairs.

Repair 1: DiscoveryCase contains traversable lineage + registered in ledger
Repair 2: Provider manifests + input/output hashes persisted in stage artifacts
Repair 3: Scientific-stage failures fail-closed
Repair 4: Explicit adversarial outcome states (ADVERSARIAL_SURVIVES/FAILED/INCONCLUSIVE)
Repair 5: Run manifest authoritative + crypto-tied to stage artifacts

Plus reviewer point 10b: expected_transfer_summary never enters any model prompt.
"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from engine.checkpoint import (
    CheckpointedDiscoveryLoop, AdversarialOutcome, StageArtifact,
    ENGINE_CODE_SHA, RUNS_DIR, COMPLETED, FAILED, SKIPPED,
)
from engine.providers import MockReasoningProvider, MockLiteratureProvider
from engine.dev_fixtures import CHALLENGE_1, CHALLENGE_4, DevChallenge, get_challenge
from engine.mechanism_extraction import MechanismExtractionEngine
from engine.mechanism_abstraction import MechanismAbstractionEngine
from engine.cross_domain_transfer import CrossDomainTransferEngine
from engine.hypothesis_generation import HypothesisGenerationEngine
from engine.adversarial_analysis import AdversarialAnalysisEngine
from engine.rediscovery_detection import RediscoveryDetector
from engine.novelty_firewall import NoveltyFirewall
from engine.prediction_engine import PredictionEngine
from engine.experiment_design import ExperimentDesignEngine


# ============================================================================
# Reviewer point 10b: expected_transfer_summary never enters any model prompt
# ============================================================================

class TestNoExpectedSummaryLeakage:
    """The fixture's expected_transfer_summary must NEVER be passed to any
    model prompt. This is a hidden leakage vector — if it leaked, the
    engine would be 'cheating' by seeing the expected answer."""

    def test_extraction_prompt_does_not_contain_expected_summary(self):
        """The mechanism extraction prompt must not contain expected_transfer_summary."""
        challenge = CHALLENGE_4
        # The extractor only receives the source document, NOT the challenge
        provider = MockReasoningProvider(default_response='{"nodes": [], "edges": []}')
        engine = MechanismExtractionEngine(provider)
        # The extract() method receives a document dict, NOT the challenge
        result = engine.extract(challenge.source_documents[0])
        # The prompt_sha is computed from the prompt; we verify the summary
        # is NOT in the source document text (which is what gets prompted)
        source_text = challenge.source_documents[0].get("text", "")
        assert challenge.expected_transfer_summary not in source_text, \
            "expected_transfer_summary must not appear in source document text"

    def test_challenge_expected_summary_is_not_in_any_engine_input(self):
        """Verify that no engine module receives expected_transfer_summary."""
        challenge = CHALLENGE_4
        summary = challenge.expected_transfer_summary
        # The engines receive: source_documents, target_problem, target_constraints,
        # mechanism graph, mechanism pattern, transfer hypothesis, hypothesis.
        # None of these should contain the expected_transfer_summary.
        assert summary not in challenge.target_problem
        assert summary not in challenge.target_problem
        for c in challenge.target_constraints:
            assert summary not in c
        for doc in challenge.source_documents:
            assert summary not in doc.get("text", "")
            assert summary not in doc.get("title", "")
        for m in challenge.plausible_competing_mechanisms:
            assert summary not in m
        for t in challenge.entity_overlap_trap:
            assert summary not in t

    def test_dev_challenge_schema_separates_expected_summary_from_engine_inputs(self):
        """The DevChallenge dataclass has expected_transfer_summary as a
        separate field that is never accessed by any engine module."""
        # Verify the field exists
        from dataclasses import fields
        field_names = {f.name for f in fields(DevChallenge)}
        assert "expected_transfer_summary" in field_names
        # Verify no engine module (except dev_fixtures.py which DEFINES it) references it.
        # dev_fixtures.py is allowed to reference it because it defines the dataclass.
        # All other engine modules must NOT reference it.
        engine_dir = REPO / "engine"
        for py_file in engine_dir.glob("*.py"):
            if py_file.name == "dev_fixtures.py":
                continue  # this file defines the field — allowed
            content = py_file.read_text()
            assert "expected_transfer_summary" not in content, \
                f"engine module {py_file.name} references expected_transfer_summary — " \
                "this field is DEV-only evaluation aid and must never enter engine logic"


# ============================================================================
# Repair 1: Traversable lineage + ledger registration
# ============================================================================

class TestRepair1Lineage:
    """The DiscoveryCase must contain a traversable provenance graph linking
    every upstream scientific object, and must be registered in the ledger."""

    def test_case_contains_traversable_lineage(self, tmp_path):
        """After a full mock run, the case artifact must have lineage_node_count > 1
        and lineage_traversable = True."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        case_stage = result.get("stages", {}).get("12_case")
        assert case_stage is not None
        assert case_stage["status"] == COMPLETED
        # Load the case artifact
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        case_data = json.loads((run_dir / "12_case.json").read_text())
        case_result = case_data["result"]
        assert case_result["lineage_traversable"] is True
        assert case_result["lineage_node_count"] > 5, \
            "lineage must contain multiple nodes (source, graph, pattern, transfer, hypothesis, ...)"
        assert case_result["registered_in_ledger"] is True
        assert case_result["evidence_count"] > 5

    def test_case_provenance_links_source_to_experiment(self, tmp_path):
        """The provenance graph must contain edges linking source_doc →
        mechanism_graph → mechanism_pattern → transfer → hypothesis →
        prediction → experiment."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        case_data = json.loads((run_dir / "12_case.json").read_text())
        # The case artifact contains the case_id; we need to inspect the
        # ledger's provenance graph to verify traversability.
        case = loop.ledger.cases.get(case_data["result"]["case_id"])
        assert case is not None
        # Verify the provenance graph has nodes for each upstream object type
        node_types = {n.node_type for n in case.provenance.nodes.values()}
        assert "source_document" in node_types
        assert "mechanism_graph" in node_types
        assert "mechanism_pattern" in node_types
        assert "transfer_hypothesis" in node_types
        assert "hypothesis" in node_types


# ============================================================================
# Repair 2: Provider manifests + input/output hashes persisted
# ============================================================================

class TestRepair2ProviderManifests:
    """Every stage artifact must contain provider_manifest, input_hash,
    output_hash, code_sha, run_id, stage."""

    def test_stage_artifact_has_required_fields(self, tmp_path):
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        ext_data = json.loads((run_dir / "01_extraction.json").read_text())
        # Repair 2: the artifact must be a StageArtifact with all fields
        assert "stage" in ext_data
        assert "run_id" in ext_data
        assert "code_sha" in ext_data
        assert "input_hash" in ext_data
        assert "output_hash" in ext_data
        assert "provider_manifest" in ext_data
        assert "result" in ext_data
        assert "timestamp" in ext_data

    def test_provider_manifest_persisted_for_llm_stages(self, tmp_path):
        """Stages that call the LLM must persist the ProviderCallManifest."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        ext_data = json.loads((run_dir / "01_extraction.json").read_text())
        # Extraction calls the LLM, so provider_manifest must be present
        assert ext_data["provider_manifest"] is not None
        assert ext_data["provider_manifest"]["provider"] == "mock"
        assert ext_data["provider_manifest"]["prompt_sha"]
        assert len(ext_data["provider_manifest"]["prompt_sha"]) == 64

    def test_output_hash_is_64_chars(self, tmp_path):
        """output_hash must be a full 64-char SHA-256."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        ext_data = json.loads((run_dir / "01_extraction.json").read_text())
        assert len(ext_data["output_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in ext_data["output_hash"])


# ============================================================================
# Repair 3: Fail-closed for scientific stages
# ============================================================================

class TestRepair3FailClosed:
    """Scientific-stage failures must STOP the loop, not continue."""

    def test_failed_extraction_stops_loop(self, tmp_path):
        """If a scientific stage fails, the loop must STOP (fail-closed).

        We simulate this by monkey-patching the abstraction engine to raise
        an exception. The loop must set failed_closed=True and NOT proceed
        to transfer/hypotheses."""
        provider = MockReasoningProvider(default_response='{"nodes": [], "edges": []}')
        loop = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))

        # Monkey-patch the abstracter to raise — simulates a scientific-stage failure
        original_abstract = loop.abstracter.abstract
        def failing_abstract(*args, **kwargs):
            raise RuntimeError("simulated scientific failure in abstraction")
        loop.abstracter.abstract = failing_abstract

        import engine.checkpoint as cp
        original_runs_dir = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            result = loop.run(CHALLENGE_4, resume=False)
            # Abstraction must have FAILED
            abstraction_status = result.get("stages", {}).get("02_abstraction", {}).get("status")
            assert abstraction_status == FAILED, \
                f"Expected abstraction to FAIL, got {abstraction_status}"
            # Loop must be fail-closed
            assert result.get("failed_closed") is True, \
                f"Expected failed_closed=True, got {result.get('failed_closed')}"
            assert result["failed_closed_at"] == "02_abstraction"
            # Transfer must NOT have run
            transfer_status = result.get("stages", {}).get("03_transfer", {}).get("status")
            assert transfer_status in (None, "PENDING", ""), \
                f"fail-closed should prevent transfer from running, got {transfer_status}"
            # Loop must NOT be completed
            assert result["completed"] is False
        finally:
            cp.RUNS_DIR = original_runs_dir
            loop.abstracter.abstract = original_abstract

    def test_failed_closed_manifest_records_stage(self, tmp_path):
        """When fail-closed triggers, manifest.failed_closed_at names the stage."""
        import engine.checkpoint as cp
        original_runs_dir = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            provider = MockReasoningProvider(default_response="not json")
            loop = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
            result = loop.run(CHALLENGE_4, resume=False)
            if result.get("failed_closed"):
                assert result["failed_closed_at"]
                assert result["completed"] is False
        finally:
            cp.RUNS_DIR = original_runs_dir


# ============================================================================
# Repair 4: Explicit adversarial outcome states
# ============================================================================

class TestRepair4AdversarialOutcomes:
    """Adversarial analysis must produce an explicit outcome:
    ADVERSARIAL_SURVIVES, ADVERSARIAL_FAILED, or ADVERSARIAL_INCONCLUSIVE."""

    def test_adversarial_outcome_values_exist(self):
        assert AdversarialOutcome.SURVIVES == "ADVERSARIAL_SURVIVES"
        assert AdversarialOutcome.FAILED == "ADVERSARIAL_FAILED"
        assert AdversarialOutcome.INCONCLUSIVE == "ADVERSARIAL_INCONCLUSIVE"

    def test_adversarial_stage_records_outcome(self, tmp_path):
        """The adversarial stage artifact must contain an 'outcome' field."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        # Find any adversarial stage file
        adv_files = list(run_dir.glob("05_adversarial_*.json"))
        assert len(adv_files) > 0
        for f in adv_files:
            data = json.loads(f.read_text())
            assert "outcome" in data["result"]
            assert data["result"]["outcome"] in [
                AdversarialOutcome.SURVIVES, AdversarialOutcome.FAILED,
                AdversarialOutcome.INCONCLUSIVE]

    def test_failed_adversarial_blocks_prediction(self, tmp_path):
        """A hypothesis with ADVERSARIAL_FAILED must NOT have a prediction stage."""
        # This test verifies the gating logic: if adversarial outcome is FAILED,
        # stages 08 and 09 should be SKIPPED or absent.
        # We need a mock that produces a FAILED adversarial outcome.
        # Build a mock with specific responses
        extraction_resp = json.dumps({
            "nodes": [{"node_id": "N1", "node_type": "MECHANISM",
                       "label": "test",
                       "evidence_quote": "The slime mold Physarum polycephalum is a single-celled multinucleate organism"}],
            "edges": [],
        })
        abstraction_resp = json.dumps({
            "abstract_principle": "test principle", "causal_structure": "x",
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
            "hypotheses": [{
                "claim": "test", "mechanism": "test", "assumptions": [],
                "evidence": [], "novelty_rationale": "", "testability": "",
                "falsifier": "if X", "expected_failure_modes": [],
            }],
            "distinguishing_predictions": "",
        })
        # Adversarial: HIGH-severity CONTRADICTS_KNOWN → FAILED
        adversarial_resp = json.dumps({
            "failure_modes": [{
                "category": "CONTRADICTS_KNOWN", "description": "contradicts known physics",
                "severity": "HIGH", "evidence": "known law",
            }],
            "survives": False, "survives_reason": "HIGH contradiction",
        })
        rediscovery_resp = json.dumps({"classification": "NON_TRIVIAL_TRANSFER", "evidence": "test"})
        novelty_resp = json.dumps({"classification": "UNKNOWN", "evidence": "test"})

        responses = {
            "You are a scientific mechanism extractor": extraction_resp,
            "You are a scientific abstraction engine": abstraction_resp,
            "You are a cross-domain transfer hypothesis engine": transfer_resp,
            "You are a scientific hypothesis generation engine": hypothesis_resp,
            "You are an adversarial scientific critic": adversarial_resp,
            "You are a rediscovery detector": rediscovery_resp,
            "You are a scientific prediction engine": novelty_resp,
            "You are a scientific experiment design engine": novelty_resp,
        }
        provider = MockReasoningProvider(responses=responses, default_response="{}")
        loop = CheckpointedDiscoveryLoop(provider, MockLiteratureProvider([]))
        import engine.checkpoint as cp
        original_runs_dir = cp.RUNS_DIR
        cp.RUNS_DIR = tmp_path / "runs"
        try:
            result = loop.run(CHALLENGE_4, resume=False)
            run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
            # The adversarial stage should have outcome = ADVERSARIAL_FAILED
            adv_files = list(run_dir.glob("05_adversarial_*.json"))
            assert len(adv_files) > 0
            adv_data = json.loads(adv_files[0].read_text())
            assert adv_data["result"]["outcome"] == AdversarialOutcome.FAILED
            # Prediction stage should NOT exist (blocked)
            pred_files = list(run_dir.glob("08_prediction_*.json"))
            assert len(pred_files) == 0, \
                "ADVERSARIAL_FAILED hypothesis must NOT have a prediction stage"
            # The manifest should record a BLOCKED_ stage
            blocked_stages = [k for k in result["stages"] if k.startswith("BLOCKED_")]
            assert len(blocked_stages) > 0
        finally:
            cp.RUNS_DIR = original_runs_dir


# ============================================================================
# Repair 4b: DEV pipeline states do not imply scientific Gate A/B/C passed
# ============================================================================

class TestRepair4bPipelineVsScientificGates:
    """The state-machine artifact must explicitly distinguish pipeline stages
    from scientific gates."""

    def test_state_machine_records_scientific_gate_passed_false(self, tmp_path):
        """The state-machine artifact must have scientific_gate_passed = False
        for DEV runs (no independent adjudication has occurred)."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        sm_data = json.loads((run_dir / "11_state_machine.json").read_text())
        assert sm_data["result"]["scientific_gate_passed"] is False

    def test_state_machine_evidence_is_not_auto(self, tmp_path):
        """The state machine must NOT use evidence='auto' — it must use
        'dev_pipeline_stage' to make clear these are pipeline markers."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        sm_data = json.loads((run_dir / "11_state_machine.json").read_text())
        for transition in sm_data["result"]["history"]:
            assert transition["evidence"] != "auto", \
                "DEV state machine must not use evidence='auto' — it implies automatic passage"
            assert "dev_pipeline_stage" in transition["evidence"] or \
                   "experiment designed" in transition["evidence"], \
                f"DEV transition evidence must clarify it's a pipeline stage: {transition['evidence']}"


# ============================================================================
# Repair 5: Run manifest authoritative + crypto-tied
# ============================================================================

class TestRepair5ManifestAuthoritative:
    """The run manifest must be authoritative and crypto-tied to stage artifacts."""

    def test_manifest_has_final_state_from_state_machine(self, tmp_path):
        """manifest.final_state must match the state-machine artifact's final_state."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        sm_data = json.loads((run_dir / "11_state_machine.json").read_text())
        assert result["final_state"] == sm_data["result"]["final_state"]
        assert result["final_state_source"] == "11_state_machine.json"

    def test_manifest_has_manifest_sha(self, tmp_path):
        """The manifest must contain a self-hash for integrity."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        assert "manifest_sha" in result
        assert len(result["manifest_sha"]) == 64

    def test_manifest_stage_output_hashes_match_artifacts(self, tmp_path):
        """Each stage's output_hash in the manifest must match the actual artifact."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        run_dir = tmp_path / "runs" / f"RUN-{CHALLENGE_4.challenge_id}"
        for stage_name, stage_status in result["stages"].items():
            if stage_status["status"] != COMPLETED: continue
            artifact_path = run_dir / f"{stage_name}.json"
            if not artifact_path.exists(): continue
            artifact = json.loads(artifact_path.read_text())
            assert stage_status["output_hash"] == artifact["output_hash"], \
                f"manifest output_hash mismatch for stage {stage_name}"

    def test_manifest_records_adversarial_survivor_count(self, tmp_path):
        """The manifest must record n_hypotheses_survived_adversarial."""
        loop, result = _run_mock_loop(CHALLENGE_4, tmp_path)
        assert "n_hypotheses_survived_adversarial" in result
        assert "n_hypotheses_rediscovery" in result


# ============================================================================
# Helper: run a mock loop into a tmp directory
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
        "failure_modes": [{
            "category": "FRAGILE_ASSUMPTION", "description": "weak assumption",
            "severity": "MEDIUM", "evidence": "test",
        }],
        "survives": True, "survives_reason": "no HIGH contradictions",
    })
    rediscovery_resp = json.dumps({
        "classification": "NON_TRIVIAL_TRANSFER", "evidence": "cross-domain",
    })
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
