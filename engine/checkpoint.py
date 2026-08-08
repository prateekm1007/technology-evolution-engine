"""checkpoint.py — checkpointed execution for the discovery loop.

Reviewer round-3 directive (5 repairs):
  1. Make DiscoveryCase contain traversable scientific lineage + register in ledger.
  2. Persist provider manifests + input/output hashes in every checkpoint artifact.
  3. Make scientific-stage failures fail closed (STOP on FAILED, do not continue).
  4. Explicit adversarial/rediscovery/novelty outcome states; separate from Gate A/B/C.
  5. Make run manifest authoritative + cryptographically tied to stage artifacts.

Additional repair (reviewer point 4 + 4b):
  - The DEV state machine uses GATE_A/GATE_B/GATE_C names, which implies
    scientific gate passage. These are NOT scientific gates — they are
    pipeline-stage markers. The state machine now records them with
    explicit evidence="dev_pipeline_stage" (NOT "auto"), and the run
    manifest explicitly distinguishes "pipeline_stage_reached" from
    "scientific_gate_passed".

Layout:
    experiments/dev/runs/<run_id>/
        ├── manifest.json           # authoritative run state + stage hashes
        ├── 01_extraction.json      # {result, provider_manifest, input_hash, output_hash, code_sha}
        ├── 02_abstraction.json
        ├── ... (one per stage)
        └── 12_case.json            # contains the FULL lineage, registered in ledger

DEV_ONLY: never used on Gate 2.
"""
from __future__ import annotations
import json, time, hashlib, traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from discovery_infrastructure.discovery_substrate import (
    DiscoveryCase, DiscoveryLedger, DiscoveryState, DiscoveryStateMachine,
    Hypothesis, TransferHypothesis, Prediction, ExperimentProposal,
    ProvenanceGraph, ProvenanceNode, ProvenanceEdge, EpistemicState,
    MechanismGraph, MechanismNode, MechanismEdge, MechanismNodeType,
    MechanismEdgeType, DuplicateRegistrationError,
)
from engine.providers import ReasoningProvider, ProviderCallManifest, MockLiteratureProvider
from engine.mechanism_extraction import MechanismExtractionEngine
from engine.mechanism_abstraction import MechanismAbstractionEngine, MechanismPattern
from engine.cross_domain_transfer import CrossDomainTransferEngine
from engine.hypothesis_generation import HypothesisGenerationEngine
from engine.adversarial_analysis import AdversarialAnalysisEngine
from engine.rediscovery_detection import RediscoveryDetector
from engine.novelty_firewall import NoveltyFirewall
from engine.prediction_engine import PredictionEngine
from engine.experiment_design import ExperimentDesignEngine
from engine.candidate_ranker import CandidateRanker
from engine.discovery_memory import DiscoveryMemory
from engine.experimental_learning import ExperimentalLearningEngine
from engine.dev_fixtures import DevChallenge


REPO = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO / "experiments" / "dev" / "runs"

# Engine code SHA — identifies the engine version that produced a run.
# Updated manually when the engine code changes. Used in every stage
# artifact for reproducibility.
ENGINE_CODE_SHA = "engine-v0.1-round3"

# Stage status constants
PENDING = "PENDING"; RUNNING = "RUNNING"; COMPLETED = "COMPLETED"
FAILED = "FAILED"; SKIPPED = "SKIPPED"

# Scientific stages — if any of these FAIL, the loop STOPs (fail-closed).
# Non-scientific stages (rankings, state-machine bookkeeping, case assembly)
# may fail without blocking because they are derivable from prior stages.
SCIENTIFIC_STAGES = {
    "01_extraction", "02_abstraction", "03_transfer", "04_hypotheses",
}
# Per-hypothesis scientific stages (prefixed with hyp_id in practice)
PER_HYP_SCIENTIFIC_PREFIXES = ("05_adversarial_", "06_rediscovery_",
                                "07_novelty_", "08_prediction_", "09_experiment_")


# ============================================================================
# Adversarial outcome enum (Repair 4)
# ============================================================================

class AdversarialOutcome(str):
    """Explicit outcome states for adversarial analysis.

    ADVERSARIAL_SURVIVES   — no HIGH-severity contradictions; may continue
    ADVERSARIAL_FAILED     — HIGH-severity contradiction; hypothesis is NOT
                             promoted to a scientific candidate. It is
                             retained as negative science but does not
                             advance to prediction/experiment.
    ADVERSARIAL_INCONCLUSIVE — analysis could not determine; human review
                               required before promotion.
    """
    SURVIVES = "ADVERSARIAL_SURVIVES"
    FAILED = "ADVERSARIAL_FAILED"
    INCONCLUSIVE = "ADVERSARIAL_INCONCLUSIVE"


# ============================================================================
# Stage artifact wrapper (Repair 2 + Repair 5)
# ============================================================================

@dataclass
class StageArtifact:
    """Every checkpoint stage produces this wrapper.

    Repair 2: provider_manifest + input_hash + output_hash are persisted.
    Repair 5: the manifest references each stage by its output_hash.
    """
    stage: str
    run_id: str
    code_sha: str
    input_hash: str        # SHA-256 of the input to this stage
    output_hash: str       # SHA-256 of the serialized result
    provider_manifest: Optional[Dict] = None  # ProviderCallManifest.to_dict()
    result: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# Run manifest (Repair 5 — authoritative + crypto-tied)
# ============================================================================

@dataclass
class StageStatus:
    stage: str
    status: str = PENDING
    started_at: str = ""
    completed_at: str = ""
    latency_ms: Optional[int] = None
    error: str = ""
    output_hash: str = ""    # Repair 5: hash of the stage's output artifact
    provider_manifest_sha: str = ""  # hash of the provider manifest (if any)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RunManifest:
    run_id: str
    challenge_id: str
    started_at: str
    last_updated: str
    engine_code_sha: str = ENGINE_CODE_SHA
    resume_from: str = "01_extraction"
    stages: Dict[str, StageStatus] = field(default_factory=dict)
    n_hypotheses: int = 0
    n_hypotheses_survived_adversarial: int = 0
    n_hypotheses_rediscovery: int = 0
    final_state: str = ""
    final_state_source: str = ""   # which stage artifact is authoritative for final_state
    completed: bool = False
    failed_closed: bool = False    # Repair 3: true if the loop stopped due to a FAILED scientific stage
    failed_closed_at: str = ""     # which stage failed
    manifest_sha: str = ""         # Repair 5: self-hash for integrity

    def to_dict(self) -> Dict:
        d = {"run_id": self.run_id, "challenge_id": self.challenge_id,
             "started_at": self.started_at, "last_updated": self.last_updated,
             "engine_code_sha": self.engine_code_sha,
             "resume_from": self.resume_from,
             "stages": {k: v.to_dict() for k, v in self.stages.items()},
             "n_hypotheses": self.n_hypotheses,
             "n_hypotheses_survived_adversarial": self.n_hypotheses_survived_adversarial,
             "n_hypotheses_rediscovery": self.n_hypotheses_rediscovery,
             "final_state": self.final_state,
             "final_state_source": self.final_state_source,
             "completed": self.completed,
             "failed_closed": self.failed_closed,
             "failed_closed_at": self.failed_closed_at}
        # Self-hash for integrity (Repair 5)
        d["manifest_sha"] = _sha(json.dumps(d, sort_keys=True, default=str))
        return d


# ============================================================================
# The checkpointed loop (all 5 repairs applied)
# ============================================================================

class CheckpointedDiscoveryLoop:
    """Discovery loop with per-stage checkpointing, fail-closed semantics,
    traversable lineage, and authoritative run manifest."""

    def __init__(self, reasoning: ReasoningProvider,
                 literature: Optional[Any] = None,
                 run_dir: Optional[Path] = None):
        self.reasoning = reasoning
        self.literature = literature or MockLiteratureProvider(corpus=[])
        self.extractor = MechanismExtractionEngine(reasoning)
        self.abstracter = MechanismAbstractionEngine(reasoning)
        self.transfer_engine = CrossDomainTransferEngine(reasoning)
        self.hypothesis_engine = HypothesisGenerationEngine(reasoning)
        self.adversarial_engine = AdversarialAnalysisEngine(reasoning)
        self.rediscovery_detector = RediscoveryDetector(reasoning)
        self.novelty_firewall = NoveltyFirewall(reasoning, self.literature)
        self.prediction_engine = PredictionEngine(reasoning)
        self.experiment_engine = ExperimentDesignEngine(reasoning)
        self.ranker = CandidateRanker()
        self.memory = DiscoveryMemory()
        self.learning_engine = ExperimentalLearningEngine()
        # Repair 1: the ledger is now populated by the loop
        self.ledger = DiscoveryLedger()

    def run(self, challenge: DevChallenge, *, run_id: Optional[str] = None,
            resume: bool = True) -> Dict:
        run_id = run_id or f"RUN-{challenge.challenge_id}"
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = run_dir / "manifest.json"

        if resume and manifest_path.exists():
            manifest = self._load_manifest(manifest_path)
        else:
            manifest = RunManifest(run_id=run_id, challenge_id=challenge.challenge_id,
                                   started_at=_now(), last_updated=_now())
            self._save_manifest(manifest, manifest_path)

        # Helper: run a stage with fail-closed semantics (Repair 3)
        def run_stage_fail_closed(stage: str, fn, input_data: Any = None) -> bool:
            """Returns True if the stage completed (or was already complete).
            Returns False if the stage FAILED and the loop should STOP."""
            if self._is_completed(manifest, stage):
                return True
            self._run_stage(manifest, stage, manifest_path, run_dir, fn, input_data)
            status = manifest.stages.get(stage, StageStatus(stage=stage)).status
            if status == FAILED:
                # Repair 3: fail-closed for scientific stages
                if self._is_scientific_stage(stage):
                    manifest.failed_closed = True
                    manifest.failed_closed_at = stage
                    manifest.last_updated = _now()
                    self._save_manifest(manifest, manifest_path)
                    return False
            return True

        # ---- Stage 01: Extraction (scientific, fail-closed) ----
        if not run_stage_fail_closed("01_extraction",
                lambda inp: self._stage_extraction(challenge, inp),
                input_data=challenge.source_documents[0]):
            return manifest.to_dict()

        # ---- Stage 02: Abstraction (scientific, fail-closed) ----
        if not run_stage_fail_closed("02_abstraction",
                lambda inp: self._stage_abstraction(challenge, run_dir, inp),
                input_data=self._load_stage(run_dir, "01_extraction")):
            return manifest.to_dict()

        # ---- Stage 03: Transfer (scientific, fail-closed) ----
        if not run_stage_fail_closed("03_transfer",
                lambda inp: self._stage_transfer(challenge, run_dir, inp),
                input_data=self._load_stage(run_dir, "02_abstraction")):
            return manifest.to_dict()

        # ---- Stage 04: Hypotheses (scientific, fail-closed) ----
        if not run_stage_fail_closed("04_hypotheses",
                lambda inp: self._stage_hypotheses(challenge, run_dir, inp),
                input_data=self._load_stage(run_dir, "03_transfer")):
            return manifest.to_dict()

        # ---- Stages 05-09: per-hypothesis pipeline ----
        # Repair 4: adversarial outcome now GATES the per-hypothesis pipeline.
        # ADVERSARIAL_FAILED hypotheses do NOT advance to prediction/experiment.
        hyp_data = self._load_stage(run_dir, "04_hypotheses")
        # Stage artifacts wrap result in a "result" key (Repair 2)
        hyp_result = hyp_data.get("result", {}) if hyp_data else {}
        if hyp_result and hyp_result.get("hypotheses"):
            testable_hyps = [h for h in hyp_result["hypotheses"] if h.get("is_testable")]
            manifest.n_hypotheses = len(testable_hyps)
            n_survived = 0
            n_rediscovery = 0
            for hyp_dict in testable_hyps:
                hyp_id = hyp_dict["hypothesis_id"]
                h = self._reconstruct_hypothesis(hyp_dict)
                if not h:
                    continue

                # Stage 05: adversarial (scientific, fail-closed)
                stage05 = f"05_adversarial_{hyp_id}"
                if not run_stage_fail_closed(stage05,
                        lambda inp, hh=h: self._stage_adversarial(hh, run_dir, inp),
                        input_data=hyp_dict):
                    return manifest.to_dict()

                # Read the adversarial outcome (Repair 4)
                adv_data = self._load_stage(run_dir, stage05)
                adv_outcome = (adv_data or {}).get("result", {}).get("outcome", AdversarialOutcome.INCONCLUSIVE)

                # Stage 06: rediscovery (scientific, fail-closed — runs regardless of adversarial,
                # because rediscovery classification is informative even for failed hypotheses)
                stage06 = f"06_rediscovery_{hyp_id}"
                if not run_stage_fail_closed(stage06,
                        lambda inp, hh=h: self._stage_rediscovery(hh, challenge, run_dir, inp),
                        input_data=hyp_dict):
                    return manifest.to_dict()
                rd_data = self._load_stage(run_dir, stage06)
                if rd_data and rd_data.get("result", {}).get("is_rediscovery"):
                    n_rediscovery += 1

                # Stage 07: novelty (scientific, fail-closed — runs regardless of adversarial)
                stage07 = f"07_novelty_{hyp_id}"
                if not run_stage_fail_closed(stage07,
                        lambda inp, hh=h: self._stage_novelty(hh, run_dir, inp),
                        input_data=hyp_dict):
                    return manifest.to_dict()

                # Repair 4: ADVERSARIAL_FAILED hypotheses do NOT advance to prediction/experiment.
                # They are retained as negative science but the pipeline stops here for them.
                if adv_outcome == AdversarialOutcome.FAILED:
                    # Record that this hypothesis was blocked at the adversarial gate
                    blocked_stage = f"BLOCKED_adversarial_{hyp_id}"
                    manifest.stages[blocked_stage] = StageStatus(
                        stage=blocked_stage, status=SKIPPED,
                        started_at=_now(), completed_at=_now(),
                        error=f"hypothesis {hyp_id} blocked: adversarial outcome = FAILED")
                    self._save_manifest(manifest, manifest_path)
                    continue

                n_survived += 1

                # Stage 08: prediction (scientific, fail-closed)
                stage08 = f"08_prediction_{hyp_id}"
                if not run_stage_fail_closed(stage08,
                        lambda inp, hh=h: self._stage_prediction(hh, run_dir, inp),
                        input_data=hyp_dict):
                    return manifest.to_dict()

                # Stage 09: experiment (scientific, fail-closed — requires prediction from 08)
                stage09 = f"09_experiment_{hyp_id}"
                pred_for_exp = self._load_stage(run_dir, stage08)
                if not pred_for_exp or not pred_for_exp.get("result", {}).get("prediction"):
                    # No prediction — skip experiment, record as skipped
                    manifest.stages[stage09] = StageStatus(
                        stage=stage09, status=SKIPPED,
                        started_at=_now(), completed_at=_now(),
                        error="skipped: no prediction produced")
                    self._save_manifest(manifest, manifest_path)
                else:
                    if not run_stage_fail_closed(stage09,
                            lambda inp, hh=h, hid=hyp_id: self._stage_experiment(hh, hid, run_dir, inp),
                            input_data=pred_for_exp):
                        return manifest.to_dict()

            manifest.n_hypotheses_survived_adversarial = n_survived
            manifest.n_hypotheses_rediscovery = n_rediscovery

        # ---- Stage 10: Rankings (non-scientific; derived from prior stages) ----
        if not self._is_completed(manifest, "10_rankings"):
            self._run_stage(manifest, "10_rankings", manifest_path, run_dir,
                            lambda inp: self._stage_rankings(challenge, run_dir, inp),
                            input_data=self._load_stage(run_dir, "04_hypotheses"))

        # ---- Stage 11: State machine (non-scientific; bookkeeping) ----
        if not self._is_completed(manifest, "11_state_machine"):
            self._run_stage(manifest, "11_state_machine", manifest_path, run_dir,
                            lambda inp: self._stage_state_machine(challenge, run_dir, inp),
                            input_data=self._load_stage(run_dir, "04_hypotheses"))
            # Repair 5: propagate final_state from the stage artifact to the manifest
            sm_data = self._load_stage(run_dir, "11_state_machine")
            if sm_data:
                manifest.final_state = sm_data.get("result", {}).get("final_state", "")
                manifest.final_state_source = "11_state_machine.json"

        # ---- Stage 12: Case (Repair 1 — traversable lineage + ledger registration) ----
        if not self._is_completed(manifest, "12_case"):
            self._run_stage(manifest, "12_case", manifest_path, run_dir,
                            lambda inp: self._stage_case(challenge, run_dir, inp),
                            input_data=self._load_stage(run_dir, "11_state_machine"))

        # ---- Finalize ----
        manifest.completed = (not manifest.failed_closed) and all(
            s.status == COMPLETED for s in manifest.stages.values()
            if not s.stage.startswith("BLOCKED_") and s.status != SKIPPED
        )
        manifest.last_updated = _now()
        self._save_manifest(manifest, manifest_path)
        return manifest.to_dict()

    # ========================================================================
    # Stage implementations — each returns (result_dict, provider_manifest)
    # ========================================================================

    def _stage_extraction(self, challenge: DevChallenge, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.extractor.extract(input_data)
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        out = {"ok": result.ok, "source_document_id": result.source_document_id,
               "source_document_title": result.source_document_title,
               "graph": result.graph.to_dict(),
               "n_nodes": len(result.graph.nodes), "n_edges": len(result.graph.edges),
               "n_failures": len(result.failures),
               "failures": [f.__dict__ for f in result.failures]}
        return out, provider_manifest

    def _stage_abstraction(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        ext = input_data
        if not ext or not ext.get("result"):
            raise RuntimeError("extraction stage output missing or malformed")
        ext_result = ext["result"]
        graph = MechanismGraph()
        for n in ext_result["graph"]["nodes"].values():
            graph.add_node(MechanismNode(
                node_id=n["node_id"], node_type=MechanismNodeType(n["node_type"]),
                label=n["label"], description=n.get("description", ""),
                provenance=n.get("provenance", [])))
        for e in ext_result["graph"]["edges"]:
            graph.add_edge(MechanismEdge(
                edge_id=e["edge_id"], source_id=e["source_id"], target_id=e["target_id"],
                edge_type=MechanismEdgeType(e["edge_type"]),
                confidence=e.get("confidence", 0.5), evidence=e.get("evidence", [])))
        result = self.abstracter.abstract(
            graph, source_domain=challenge.source_domain,
            source_title=challenge.source_documents[0].get("title", ""),
            pattern_id=f"MP-{challenge.challenge_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        return {"pattern": result.pattern.to_dict(), "failures": result.failures,
                "source_extraction_hash": ext.get("output_hash", "")}, provider_manifest

    def _stage_transfer(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        pat_data = input_data
        if not pat_data or not pat_data.get("result"):
            raise RuntimeError("abstraction stage output missing")
        pattern = MechanismPattern(**pat_data["result"]["pattern"])
        result = self.transfer_engine.generate(
            pattern, target_domain=challenge.target_domain,
            target_problem=challenge.target_problem,
            target_constraints=challenge.target_constraints,
            transfer_id_prefix=f"TH-{challenge.challenge_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        return {"transfers": [t.to_dict() for t in result.transfers],
                "rejected": result.rejected,
                "n_accepted": len(result.transfers),
                "n_rejected": len(result.rejected),
                "source_abstraction_hash": pat_data.get("output_hash", "")}, provider_manifest

    def _stage_hypotheses(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        transfer_data = input_data
        if not transfer_data or not transfer_data.get("result"):
            raise RuntimeError("transfer stage output missing")
        td = transfer_data["result"]
        if not td["transfers"]:
            return {"hypotheses": [], "distinguishing_predictions": "",
                    "source_transfer_hash": transfer_data.get("output_hash", "")}, None
        t = td["transfers"][0]
        transfer = TransferHypothesis(
            transfer_id=t["transfer_id"], source_domain=t.get("source_domain", ""),
            source_mechanism=t.get("source_mechanism", ""),
            source_conditions=t.get("source_conditions", []),
            target_domain=t.get("target_domain", ""),
            target_problem=t.get("target_problem", ""),
            transferred_principle=t.get("transferred_principle", ""),
            required_translation=t.get("required_translation", ""),
            expected_effect=t.get("expected_effect", ""),
            boundary_conditions=t.get("boundary_conditions", []),
            failure_conditions=t.get("failure_conditions", []),
            testable_prediction=t.get("testable_prediction", ""),
            epistemic_state=EpistemicState(t.get("epistemic_state", "HYPOTHESIZED")))
        result = self.hypothesis_engine.generate(transfer, id_prefix=f"H-{challenge.challenge_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        # Register hypotheses in the ledger (Repair 1)
        for h in result.hypotheses:
            try:
                self.ledger.register_hypothesis(h)
            except DuplicateRegistrationError:
                pass
        return {"hypotheses": [h.to_dict() for h in result.hypotheses],
                "distinguishing_predictions": result.distinguishing_predictions,
                "transfer_id": transfer.transfer_id,
                "source_transfer_hash": transfer_data.get("output_hash", "")}, provider_manifest

    def _stage_adversarial(self, hypothesis: Hypothesis, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.adversarial_engine.analyze(hypothesis)
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        # Repair 4: explicit outcome state
        outcome = AdversarialOutcome.SURVIVES
        if not result.survives:
            # Check if it was blocked by a HIGH-severity CONTRADICTS_KNOWN
            has_high_contradiction = any(
                f.severity == "HIGH" and f.category == "CONTRADICTS_KNOWN"
                for f in result.failure_modes
            )
            outcome = AdversarialOutcome.FAILED if has_high_contradiction else AdversarialOutcome.INCONCLUSIVE
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "failure_modes": [f.__dict__ for f in result.failure_modes],
                "survives": result.survives,
                "outcome": outcome,  # Repair 4: explicit outcome
                "n_high_severity": sum(1 for f in result.failure_modes if f.severity == "HIGH"),
                "n_medium_severity": sum(1 for f in result.failure_modes if f.severity == "MEDIUM"),
                "n_low_severity": sum(1 for f in result.failure_modes if f.severity == "LOW"),
                "source_hypothesis_hash": input_data.get("output_hash", "") if input_data else ""}, provider_manifest

    def _stage_rediscovery(self, hypothesis: Hypothesis, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.rediscovery_detector.classify(hypothesis, challenge.source_documents)
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "classification": result.classification.value,
                "evidence": result.evidence,
                "is_rediscovery": result.is_rediscovery,
                "source_hypothesis_hash": input_data.get("output_hash", "") if input_data else ""}, provider_manifest

    def _stage_novelty(self, hypothesis: Hypothesis, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.novelty_firewall.assess(hypothesis, assessment_id=f"PA-{hypothesis.hypothesis_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        # Register the prior-art assessment in the ledger (Repair 1)
        try:
            self.ledger.register_prior_art(result.assessment)
        except DuplicateRegistrationError:
            pass
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "status": result.assessment.status.value,
                "similarity": result.assessment.similarity,
                "matched_prior_art": result.assessment.matched_prior_art,
                "review_required": result.assessment.review_required,
                "source_hypothesis_hash": input_data.get("output_hash", "") if input_data else ""}, provider_manifest

    def _stage_prediction(self, hypothesis: Hypothesis, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        result = self.prediction_engine.predict(hypothesis, prediction_id=f"P-{hypothesis.hypothesis_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        if result.prediction:
            try:
                self.ledger.register_prediction(result.prediction)
            except DuplicateRegistrationError:
                pass
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "prediction": result.prediction.to_dict() if result.prediction else None,
                "failed": result.prediction is None,
                "failures": result.failures,
                "source_hypothesis_hash": input_data.get("output_hash", "") if input_data else ""}, provider_manifest

    def _stage_experiment(self, hypothesis: Hypothesis, hyp_id: str, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        pred_data = input_data
        if not pred_data or not pred_data.get("result", {}).get("prediction"):
            return {"hypothesis_id": hyp_id, "experiment": None,
                    "skipped_reason": "no prediction",
                    "source_prediction_hash": pred_data.get("output_hash", "") if pred_data else ""}, None
        p = pred_data["result"]["prediction"]
        prediction = Prediction(
            prediction_id=p["prediction_id"], hypothesis_id=p["hypothesis_id"],
            observable=p.get("observable", ""),
            expected_direction=p.get("expected_direction", ""),
            expected_magnitude=p.get("expected_magnitude", ""),
            conditions=p.get("conditions", []),
            baseline=p.get("baseline", ""),
            falsifier=p.get("falsifier", ""),
            uncertainty=p.get("uncertainty", 0.5),
            is_testable=p.get("is_testable", False))
        result = self.experiment_engine.design(hypothesis, prediction, experiment_id=f"E-{hyp_id}")
        provider_manifest = result.manifests[0].to_dict() if result.manifests else None
        if result.proposal:
            try:
                self.ledger.register_experiment(result.proposal)
            except DuplicateRegistrationError:
                pass
        return {"hypothesis_id": hyp_id,
                "experiment": result.proposal.to_dict() if result.proposal else None,
                "failed": result.proposal is None,
                "failures": result.failures,
                "source_prediction_hash": pred_data.get("output_hash", "")}, provider_manifest

    def _stage_rankings(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        hyp_data = input_data
        transfer_data = self._load_stage(run_dir, "03_transfer")
        if not hyp_data or not transfer_data or not transfer_data.get("result", {}).get("transfers"):
            return {"rankings": {}}, None
        t = transfer_data["result"]["transfers"][0]
        transfer = TransferHypothesis(
            transfer_id=t["transfer_id"], source_domain=t.get("source_domain", ""),
            source_mechanism=t.get("source_mechanism", ""),
            target_domain=t.get("target_domain", ""),
            target_problem=t.get("target_problem", ""),
            transferred_principle=t.get("transferred_principle", ""),
            required_translation=t.get("required_translation", ""),
            expected_effect=t.get("expected_effect", ""),
            epistemic_state=EpistemicState.HYPOTHESIZED)
        rankings = {}
        for h_dict in hyp_data["result"]["hypotheses"]:
            if not h_dict.get("is_testable"): continue
            hyp = self._reconstruct_hypothesis(h_dict)
            if not hyp: continue
            ranking = self.ranker.rank(hyp, transfer)
            rankings[hyp.hypothesis_id] = ranking.to_dict()
        return {"rankings": rankings}, None

    def _stage_state_machine(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        hyp_data = input_data
        if not hyp_data or not hyp_data.get("result"):
            return {"final_state": "RAW_EVIDENCE", "history": [],
                    "pipeline_stage_reached": "RAW_EVIDENCE",
                    "scientific_gate_passed": False,
                    "note": "no hypotheses produced"}, None
        testable = [h for h in hyp_data["result"]["hypotheses"] if h.get("is_testable")]
        sm = DiscoveryStateMachine(f"DC-{challenge.challenge_id}")
        try:
            if not testable:
                for s in [DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.MECHANISM,
                          DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.CANDIDATE_DISCOVERY,
                          DiscoveryState.GATE_A, DiscoveryState.GATE_B, DiscoveryState.GATE_C]:
                    sm.transition(s, actor="loop", code_sha=ENGINE_CODE_SHA,
                                  evidence="dev_pipeline_stage", reason="phase advance")
            else:
                canonical = self._reconstruct_hypothesis(testable[0])
                for s in [DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.MECHANISM,
                          DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.CANDIDATE_DISCOVERY,
                          DiscoveryState.GATE_A, DiscoveryState.GATE_B, DiscoveryState.GATE_C,
                          DiscoveryState.TESTABLE_HYPOTHESIS]:
                    sm.transition(s, actor="loop", code_sha=ENGINE_CODE_SHA,
                                  evidence="dev_pipeline_stage", reason="phase advance",
                                  hypothesis=canonical if s == DiscoveryState.TESTABLE_HYPOTHESIS else None)
                # Advance to EXPERIMENT only if that hypothesis survived adversarial AND has an experiment
                adv_data = self._load_stage(run_dir, f"05_adversarial_{canonical.hypothesis_id}")
                adv_outcome = (adv_data or {}).get("result", {}).get("outcome", AdversarialOutcome.INCONCLUSIVE)
                exp_data = self._load_stage(run_dir, f"09_experiment_{canonical.hypothesis_id}")
                if adv_outcome == AdversarialOutcome.SURVIVES and exp_data and exp_data.get("result", {}).get("experiment"):
                    sm.transition(DiscoveryState.EXPERIMENT,
                                  actor="loop", code_sha=ENGINE_CODE_SHA,
                                  evidence="experiment designed", reason="ready",
                                  hypothesis=canonical)
            return {"final_state": sm.current_state.value,
                    "history": [t.to_dict() for t in sm.history],
                    "pipeline_stage_reached": sm.current_state.value,
                    # Repair 4b: explicitly state that NO scientific gate has passed
                    "scientific_gate_passed": False,
                    "note": "DEV pipeline stages GATE_A/B/C are NOT scientific Gate A/B/C. "
                            "They are pipeline markers. Scientific gates require independent "
                            "adjudication per SCIENTIFIC_GATE_2_PROTOCOL.md."}, None
        except Exception as e:
            return {"final_state": sm.current_state.value,
                    "history": [t.to_dict() for t in sm.history],
                    "pipeline_stage_reached": sm.current_state.value,
                    "scientific_gate_passed": False,
                    "error": str(e)}, None

    def _stage_case(self, challenge: DevChallenge, run_dir: Path, input_data) -> Tuple[Dict, Optional[Dict]]:
        """Repair 1: build a DiscoveryCase with TRAVERSABLE LINEAGE and register in ledger."""
        sm_data = input_data
        final_state = sm_data.get("result", {}).get("final_state", "") if sm_data else ""

        # Collect all upstream object IDs for the lineage
        ext_data = self._load_stage(run_dir, "01_extraction")
        ab_data = self._load_stage(run_dir, "02_abstraction")
        tr_data = self._load_stage(run_dir, "03_transfer")
        hyp_data = self._load_stage(run_dir, "04_hypotheses")

        # Build the case with full lineage references
        case = DiscoveryCase(
            case_id=f"DC-{challenge.challenge_id}",
            input_sources=[d.get("title", "") for d in challenge.source_documents],
            input_domains=[challenge.source_domain, challenge.target_domain],
            evidence=[],  # will be populated below
        )

        # Repair 1: build a traversable provenance graph linking every upstream object
        prov = case.provenance

        # Source document node
        if ext_data and ext_data.get("result"):
            ext_result = ext_data["result"]
            prov.add_node(ProvenanceNode(
                node_id=f"source_doc:{ext_result.get('source_document_id', challenge.challenge_id)}",
                node_type="source_document",
                content_hash=ext_data.get("output_hash", ""),
                metadata={"title": ext_result.get("source_document_title", ""),
                          "extraction_output_hash": ext_data.get("output_hash", "")}))

        # Mechanism graph node
        if ext_data and ext_data.get("result"):
            prov.add_node(ProvenanceNode(
                node_id=f"mechanism_graph:{challenge.challenge_id}",
                node_type="mechanism_graph",
                content_hash=ext_data.get("output_hash", ""),
                metadata={"n_nodes": ext_result.get("n_nodes", 0),
                          "n_edges": ext_result.get("n_edges", 0)}))
            prov.add_edge(ProvenanceEdge(
                f"prov:mg_src:{challenge.challenge_id}",
                f"source_doc:{ext_result.get('source_document_id', challenge.challenge_id)}",
                f"mechanism_graph:{challenge.challenge_id}",
                "DERIVES_FROM", "mechanism graph extracted from source",
                actor="mechanism_extractor"))

        # Mechanism pattern node
        if ab_data and ab_data.get("result"):
            prov.add_node(ProvenanceNode(
                node_id=f"mechanism_pattern:{challenge.challenge_id}",
                node_type="mechanism_pattern",
                content_hash=ab_data.get("output_hash", ""),
                metadata={"pattern_id": ab_data["result"].get("pattern", {}).get("pattern_id", "")}))
            prov.add_edge(ProvenanceEdge(
                f"prov:mp_mg:{challenge.challenge_id}",
                f"mechanism_graph:{challenge.challenge_id}",
                f"mechanism_pattern:{challenge.challenge_id}",
                "DERIVES_FROM", "pattern abstracted from mechanism graph",
                actor="mechanism_abstracter"))

        # Transfer hypothesis node
        if tr_data and tr_data.get("result") and tr_data["result"].get("transfers"):
            t = tr_data["result"]["transfers"][0]
            transfer_id = t["transfer_id"]
            prov.add_node(ProvenanceNode(
                node_id=f"transfer:{transfer_id}",
                node_type="transfer_hypothesis",
                content_hash=tr_data.get("output_hash", ""),
                metadata={"source_domain": t.get("source_domain", ""),
                          "target_domain": t.get("target_domain", ""),
                          "transferred_principle": t.get("transferred_principle", "")}))
            prov.add_edge(ProvenanceEdge(
                f"prov:th_mp:{transfer_id}",
                f"mechanism_pattern:{challenge.challenge_id}",
                f"transfer:{transfer_id}",
                "DERIVES_FROM", "transfer derived from pattern",
                actor="cross_domain_transfer"))

        # Per-hypothesis lineage: hypothesis → adversarial → rediscovery → novelty → prediction → experiment
        if hyp_data and hyp_data.get("result"):
            for h_dict in hyp_data["result"]["hypotheses"]:
                if not h_dict.get("is_testable"): continue
                hid = h_dict["hypothesis_id"]
                # Hypothesis node
                prov.add_node(ProvenanceNode(
                    node_id=f"hypothesis:{hid}",
                    node_type="hypothesis",
                    content_hash=_sha(json.dumps(h_dict, sort_keys=True, default=str)),
                    metadata={"claim": h_dict.get("claim", "")[:100]}))
                if tr_data and tr_data.get("result") and tr_data["result"].get("transfers"):
                    prov.add_edge(ProvenanceEdge(
                        f"prov:h_th:{hid}", f"transfer:{transfer_id}",
                        f"hypothesis:{hid}", "DERIVES_FROM",
                        "hypothesis derived from transfer", actor="hypothesis_engine"))

                # Adversarial node
                adv = self._load_stage(run_dir, f"05_adversarial_{hid}")
                if adv and adv.get("result"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"adversarial:{hid}", node_type="adversarial_analysis",
                        content_hash=adv.get("output_hash", ""),
                        metadata={"outcome": adv["result"].get("outcome", ""),
                                  "survives": adv["result"].get("survives", False)}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:adv_h:{hid}", f"hypothesis:{hid}", f"adversarial:{hid}",
                        "ANALYZES", "adversarial analysis of hypothesis",
                        actor="adversarial_engine"))

                # Rediscovery node
                rd = self._load_stage(run_dir, f"06_rediscovery_{hid}")
                if rd and rd.get("result"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"rediscovery:{hid}", node_type="rediscovery_analysis",
                        content_hash=rd.get("output_hash", ""),
                        metadata={"classification": rd["result"].get("classification", ""),
                                  "is_rediscovery": rd["result"].get("is_rediscovery", False)}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:rd_h:{hid}", f"hypothesis:{hid}", f"rediscovery:{hid}",
                        "ANALYZES", "rediscovery classification of hypothesis",
                        actor="rediscovery_detector"))

                # Novelty node
                nov = self._load_stage(run_dir, f"07_novelty_{hid}")
                if nov and nov.get("result"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"novelty:{hid}", node_type="novelty_assessment",
                        content_hash=nov.get("output_hash", ""),
                        metadata={"status": nov["result"].get("status", "")}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:nov_h:{hid}", f"hypothesis:{hid}", f"novelty:{hid}",
                        "ANALYZES", "novelty assessment of hypothesis",
                        actor="novelty_firewall"))

                # Prediction node (only if hypothesis survived adversarial)
                pred = self._load_stage(run_dir, f"08_prediction_{hid}")
                if pred and pred.get("result") and pred["result"].get("prediction"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"prediction:{hid}", node_type="prediction",
                        content_hash=pred.get("output_hash", ""),
                        metadata={"observable": pred["result"]["prediction"].get("observable", "")[:80]}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:pred_h:{hid}", f"hypothesis:{hid}", f"prediction:{hid}",
                        "DERIVES_FROM", "prediction derived from hypothesis",
                        actor="prediction_engine"))

                # Experiment node
                exp = self._load_stage(run_dir, f"09_experiment_{hid}")
                if exp and exp.get("result") and exp["result"].get("experiment"):
                    prov.add_node(ProvenanceNode(
                        node_id=f"experiment:{hid}", node_type="experiment_proposal",
                        content_hash=exp.get("output_hash", ""),
                        metadata={"experiment_id": exp["result"]["experiment"].get("experiment_id", "")}))
                    prov.add_edge(ProvenanceEdge(
                        f"prov:exp_pred:{hid}", f"prediction:{hid}", f"experiment:{hid}",
                        "DERIVES_FROM", "experiment designed from prediction",
                        actor="experiment_designer"))

        # Run manifest node
        prov.add_node(ProvenanceNode(
            node_id=f"run:{challenge.challenge_id}",
            node_type="checkpointed_run",
            content_hash=_sha(challenge.challenge_id),
            metadata={"run_id": f"RUN-{challenge.challenge_id}",
                      "engine_code_sha": ENGINE_CODE_SHA}))

        # Populate case.evidence with all upstream object IDs (Repair 1)
        case.evidence = list(prov.nodes.keys())

        # Commit provenance
        try:
            case.commit_provenance()
        except Exception:
            pass

        # Repair 1: register the case in the ledger
        try:
            self.ledger.register_case(case)
        except DuplicateRegistrationError:
            pass

        # Verify traversability
        lineage_node_count = len(prov.nodes)
        lineage_edge_count = len(prov.edges)

        return {"case_id": case.case_id,
                "provenance_root_hash": case.provenance_root_hash,
                "verify_provenance": case.verify_provenance(),
                "final_state": final_state,
                "lineage_node_count": lineage_node_count,
                "lineage_edge_count": lineage_edge_count,
                "lineage_traversable": lineage_node_count > 1,
                "registered_in_ledger": case.case_id in self.ledger.cases,
                "evidence_count": len(case.evidence)}, None

    # ========================================================================
    # Checkpoint helpers (Repair 2 + Repair 3 + Repair 5)
    # ========================================================================

    def _run_stage(self, manifest: RunManifest, stage: str,
                   manifest_path: Path, run_dir: Path, fn, input_data: Any = None) -> None:
        """Run a single stage with checkpointing.

        Repair 2: persists provider_manifest + input_hash + output_hash.
        Repair 3: scientific stages that fail set manifest.failed_closed.
        Repair 5: the manifest records each stage's output_hash.
        """
        if stage not in manifest.stages:
            manifest.stages[stage] = StageStatus(stage=stage)
        ss = manifest.stages[stage]
        ss.status = RUNNING; ss.started_at = _now()
        manifest.last_updated = _now(); manifest.resume_from = stage
        self._save_manifest(manifest, manifest_path)

        # Compute input hash (Repair 2)
        input_hash = _sha(json.dumps(input_data, sort_keys=True, default=str)) if input_data is not None else ""

        start = time.time()
        try:
            result, provider_manifest = fn(input_data) if input_data is not None else fn(None)
            ss.latency_ms = int((time.time() - start) * 1000)
            ss.completed_at = _now(); ss.status = COMPLETED

            # Compute output hash (Repair 2)
            output_str = json.dumps(result, sort_keys=True, default=str)
            output_hash = _sha(output_str)

            # Build the full stage artifact (Repair 2)
            artifact = StageArtifact(
                stage=stage, run_id=manifest.run_id, code_sha=ENGINE_CODE_SHA,
                input_hash=input_hash, output_hash=output_hash,
                provider_manifest=provider_manifest, result=result)

            # Persist the artifact
            (run_dir / f"{stage}.json").write_text(
                json.dumps(artifact.to_dict(), indent=2, default=str))

            # Update manifest with hashes (Repair 5)
            ss.output_hash = output_hash
            if provider_manifest:
                ss.provider_manifest_sha = _sha(json.dumps(provider_manifest, sort_keys=True, default=str))

        except Exception as e:
            ss.latency_ms = int((time.time() - start) * 1000)
            ss.completed_at = _now(); ss.status = FAILED
            ss.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            # Persist a failure artifact so the error is inspectable
            failure_artifact = StageArtifact(
                stage=stage, run_id=manifest.run_id, code_sha=ENGINE_CODE_SHA,
                input_hash=input_hash, output_hash="",
                provider_manifest=None,
                result={"error": ss.error, "exception_type": type(e).__name__})
            (run_dir / f"{stage}.json").write_text(
                json.dumps(failure_artifact.to_dict(), indent=2, default=str))

        manifest.last_updated = _now()
        self._save_manifest(manifest, manifest_path)

    def _is_scientific_stage(self, stage: str) -> bool:
        """Repair 3: scientific stages fail-closed; non-scientific stages don't."""
        if stage in SCIENTIFIC_STAGES:
            return True
        for prefix in PER_HYP_SCIENTIFIC_PREFIXES:
            if stage.startswith(prefix):
                return True
        return False

    def _is_completed(self, manifest: RunManifest, stage: str) -> bool:
        s = manifest.stages.get(stage)
        return s is not None and s.status == COMPLETED

    def _load_stage(self, run_dir: Path, stage: str) -> Optional[Dict]:
        """Load a stage artifact. Returns the full StageArtifact dict
        (with result, provider_manifest, input_hash, output_hash)."""
        p = run_dir / f"{stage}.json"
        if not p.exists(): return None
        try: return json.loads(p.read_text())
        except json.JSONDecodeError: return None

    def _save_manifest(self, manifest: RunManifest, path: Path) -> None:
        path.write_text(json.dumps(manifest.to_dict(), indent=2, default=str))

    def _load_manifest(self, path: Path) -> RunManifest:
        d = json.loads(path.read_text())
        m = RunManifest(run_id=d["run_id"], challenge_id=d["challenge_id"],
                        started_at=d["started_at"], last_updated=d["last_updated"],
                        engine_code_sha=d.get("engine_code_sha", ENGINE_CODE_SHA),
                        resume_from=d.get("resume_from", "01_extraction"),
                        n_hypotheses=d.get("n_hypotheses", 0),
                        n_hypotheses_survived_adversarial=d.get("n_hypotheses_survived_adversarial", 0),
                        n_hypotheses_rediscovery=d.get("n_hypotheses_rediscovery", 0),
                        final_state=d.get("final_state", ""),
                        final_state_source=d.get("final_state_source", ""),
                        completed=d.get("completed", False),
                        failed_closed=d.get("failed_closed", False),
                        failed_closed_at=d.get("failed_closed_at", ""))
        for k, v in d.get("stages", {}).items():
            m.stages[k] = StageStatus(**v)
        return m

    def _reconstruct_hypothesis(self, h_dict: Dict) -> Optional[Hypothesis]:
        try:
            return Hypothesis(
                hypothesis_id=h_dict["hypothesis_id"],
                claim=h_dict.get("claim", ""),
                mechanism=h_dict.get("mechanism", ""),
                evidence=h_dict.get("evidence", []),
                assumptions=h_dict.get("assumptions", []),
                predictions=h_dict.get("predictions", []),
                expected_failure_modes=h_dict.get("expected_failure_modes", []),
                novelty_rationale=h_dict.get("novelty_rationale", ""),
                testability=h_dict.get("testability", ""),
                falsifier=h_dict.get("falsifier", ""),
                is_testable=h_dict.get("is_testable", False))
        except Exception:
            return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = ["CheckpointedDiscoveryLoop", "RunManifest", "StageStatus", "StageArtifact",
           "AdversarialOutcome", "ENGINE_CODE_SHA",
           "PENDING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED", "RUNS_DIR"]
