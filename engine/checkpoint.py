"""checkpoint.py — checkpointed execution for the discovery loop.

Reviewer directive:
    "Build checkpointed execution. Every stage should be independently
     resumable. If stage 6 times out, restart at stage 6. Do not rerun
     stages 1-5."

Layout:
    experiments/dev/runs/<run_id>/
        ├── manifest.json
        ├── 01_extraction.json
        ├── 02_abstraction.json
        ├── 03_transfer.json
        ├── 04_hypotheses.json
        ├── 05_adversarial_<hyp_id>.json
        ├── 06_rediscovery_<hyp_id>.json
        ├── 07_novelty_<hyp_id>.json
        ├── 08_prediction_<hyp_id>.json
        ├── 09_experiment_<hyp_id>.json
        ├── 10_rankings.json
        ├── 11_state_machine.json
        └── 12_case.json

DEV_ONLY: never used on Gate 2.
"""
from __future__ import annotations
import json, time, hashlib, traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from discovery_infrastructure.discovery_substrate import (
    DiscoveryCase, DiscoveryLedger, DiscoveryState, DiscoveryStateMachine,
    Hypothesis, TransferHypothesis, Prediction, ExperimentProposal,
    ProvenanceGraph, ProvenanceNode, EpistemicState, MechanismGraph,
    MechanismNode, MechanismEdge, MechanismNodeType, MechanismEdgeType,
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

PENDING = "PENDING"; RUNNING = "RUNNING"; COMPLETED = "COMPLETED"
FAILED = "FAILED"; SKIPPED = "SKIPPED"


@dataclass
class StageStatus:
    stage: str
    status: str = PENDING
    started_at: str = ""
    completed_at: str = ""
    latency_ms: Optional[int] = None
    error: str = ""
    manifest: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RunManifest:
    run_id: str
    challenge_id: str
    started_at: str
    last_updated: str
    resume_from: str = "01_extraction"
    stages: Dict[str, StageStatus] = field(default_factory=dict)
    n_hypotheses: int = 0
    final_state: str = ""
    completed: bool = False

    def to_dict(self) -> Dict:
        return {"run_id": self.run_id, "challenge_id": self.challenge_id,
                "started_at": self.started_at, "last_updated": self.last_updated,
                "resume_from": self.resume_from,
                "stages": {k: v.to_dict() for k, v in self.stages.items()},
                "n_hypotheses": self.n_hypotheses,
                "final_state": self.final_state,
                "completed": self.completed}


class CheckpointedDiscoveryLoop:
    """Discovery loop with per-stage checkpointing and resume."""

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

        # Stage 01: Extraction
        if not self._is_completed(manifest, "01_extraction"):
            self._run_stage(manifest, "01_extraction", manifest_path, run_dir,
                            lambda: self._stage_extraction(challenge))

        # Stage 02: Abstraction
        if not self._is_completed(manifest, "02_abstraction"):
            self._run_stage(manifest, "02_abstraction", manifest_path, run_dir,
                            lambda: self._stage_abstraction(challenge, run_dir))

        # Stage 03: Transfer
        if not self._is_completed(manifest, "03_transfer"):
            self._run_stage(manifest, "03_transfer", manifest_path, run_dir,
                            lambda: self._stage_transfer(challenge, run_dir))

        # Stage 04: Hypotheses
        if not self._is_completed(manifest, "04_hypotheses"):
            self._run_stage(manifest, "04_hypotheses", manifest_path, run_dir,
                            lambda: self._stage_hypotheses(challenge, run_dir))

        # Stages 05-09: per-hypothesis pipeline
        hyp_data = self._load_stage(run_dir, "04_hypotheses")
        if hyp_data and hyp_data.get("hypotheses"):
            testable_hyps = [h for h in hyp_data["hypotheses"] if h.get("is_testable")]
            manifest.n_hypotheses = len(testable_hyps)
            for hyp_dict in testable_hyps:
                hyp_id = hyp_dict["hypothesis_id"]
                for stage_num, stage_fn in [
                    ("05", lambda h: self._stage_adversarial(h, run_dir)),
                    ("06", lambda h: self._stage_rediscovery(h, challenge, run_dir)),
                    ("07", lambda h: self._stage_novelty(h, run_dir)),
                    ("08", lambda h: self._stage_prediction(h, run_dir)),
                ]:
                    stage = f"{stage_num}_adversarial_{hyp_id}" if stage_num == "05" else \
                            f"{stage_num}_rediscovery_{hyp_id}" if stage_num == "06" else \
                            f"{stage_num}_novelty_{hyp_id}" if stage_num == "07" else \
                            f"{stage_num}_prediction_{hyp_id}"
                    if not self._is_completed(manifest, stage):
                        h = self._reconstruct_hypothesis(hyp_dict)
                        if h:
                            self._run_stage(manifest, stage, manifest_path, run_dir,
                                            lambda fn=stage_fn, hh=h: fn(hh))
                # Stage 09: experiment (needs prediction from 08)
                stage09 = f"09_experiment_{hyp_id}"
                if not self._is_completed(manifest, stage09):
                    h = self._reconstruct_hypothesis(hyp_dict)
                    if h:
                        self._run_stage(manifest, stage09, manifest_path, run_dir,
                                        lambda hh=h, hid=hyp_id: self._stage_experiment(hh, hid, run_dir))

        # Stage 10: Rankings
        if not self._is_completed(manifest, "10_rankings"):
            self._run_stage(manifest, "10_rankings", manifest_path, run_dir,
                            lambda: self._stage_rankings(challenge, run_dir))

        # Stage 11: State machine
        if not self._is_completed(manifest, "11_state_machine"):
            self._run_stage(manifest, "11_state_machine", manifest_path, run_dir,
                            lambda: self._stage_state_machine(challenge, run_dir))

        # Stage 12: Case
        if not self._is_completed(manifest, "12_case"):
            self._run_stage(manifest, "12_case", manifest_path, run_dir,
                            lambda: self._stage_case(challenge, run_dir))

        manifest.completed = all(s.status == COMPLETED for s in manifest.stages.values())
        manifest.last_updated = _now()
        self._save_manifest(manifest, manifest_path)
        return manifest.to_dict()

    # ===== Stage implementations =====

    def _stage_extraction(self, challenge: DevChallenge) -> Dict:
        result = self.extractor.extract(challenge.source_documents[0])
        return {"ok": result.ok, "source_document_id": result.source_document_id,
                "source_document_title": result.source_document_title,
                "graph": result.graph.to_dict(),
                "n_nodes": len(result.graph.nodes), "n_edges": len(result.graph.edges),
                "n_failures": len(result.failures),
                "failures": [f.__dict__ for f in result.failures]}

    def _stage_abstraction(self, challenge: DevChallenge, run_dir: Path) -> Dict:
        ext = self._load_stage(run_dir, "01_extraction")
        if not ext: raise RuntimeError("extraction stage output missing")
        graph = MechanismGraph()
        for n in ext["graph"]["nodes"].values():
            graph.add_node(MechanismNode(
                node_id=n["node_id"], node_type=MechanismNodeType(n["node_type"]),
                label=n["label"], description=n.get("description", ""),
                provenance=n.get("provenance", [])))
        for e in ext["graph"]["edges"]:
            graph.add_edge(MechanismEdge(
                edge_id=e["edge_id"], source_id=e["source_id"], target_id=e["target_id"],
                edge_type=MechanismEdgeType(e["edge_type"]),
                confidence=e.get("confidence", 0.5), evidence=e.get("evidence", [])))
        result = self.abstracter.abstract(
            graph, source_domain=challenge.source_domain,
            source_title=challenge.source_documents[0].get("title", ""),
            pattern_id=f"MP-{challenge.challenge_id}")
        return {"pattern": result.pattern.to_dict(),
                "failures": result.failures}

    def _stage_transfer(self, challenge: DevChallenge, run_dir: Path) -> Dict:
        pat_data = self._load_stage(run_dir, "02_abstraction")
        pattern = MechanismPattern(**pat_data["pattern"])
        result = self.transfer_engine.generate(
            pattern, target_domain=challenge.target_domain,
            target_problem=challenge.target_problem,
            target_constraints=challenge.target_constraints,
            transfer_id_prefix=f"TH-{challenge.challenge_id}")
        return {"transfers": [t.to_dict() for t in result.transfers],
                "rejected": result.rejected,
                "n_accepted": len(result.transfers),
                "n_rejected": len(result.rejected)}

    def _stage_hypotheses(self, challenge: DevChallenge, run_dir: Path) -> Dict:
        transfer_data = self._load_stage(run_dir, "03_transfer")
        if not transfer_data["transfers"]:
            return {"hypotheses": [], "distinguishing_predictions": ""}
        t = transfer_data["transfers"][0]
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
        return {"hypotheses": [h.to_dict() for h in result.hypotheses],
                "distinguishing_predictions": result.distinguishing_predictions,
                "transfer_id": transfer.transfer_id}

    def _stage_adversarial(self, hypothesis: Hypothesis, run_dir: Path) -> Dict:
        result = self.adversarial_engine.analyze(hypothesis)
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "failure_modes": [f.__dict__ for f in result.failure_modes],
                "survives": result.survives}

    def _stage_rediscovery(self, hypothesis: Hypothesis, challenge: DevChallenge, run_dir: Path) -> Dict:
        result = self.rediscovery_detector.classify(hypothesis, challenge.source_documents)
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "classification": result.classification.value,
                "evidence": result.evidence,
                "is_rediscovery": result.is_rediscovery}

    def _stage_novelty(self, hypothesis: Hypothesis, run_dir: Path) -> Dict:
        result = self.novelty_firewall.assess(hypothesis, assessment_id=f"PA-{hypothesis.hypothesis_id}")
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "status": result.assessment.status.value,
                "similarity": result.assessment.similarity,
                "matched_prior_art": result.assessment.matched_prior_art,
                "review_required": result.assessment.review_required}

    def _stage_prediction(self, hypothesis: Hypothesis, run_dir: Path) -> Dict:
        result = self.prediction_engine.predict(hypothesis, prediction_id=f"P-{hypothesis.hypothesis_id}")
        return {"hypothesis_id": hypothesis.hypothesis_id,
                "prediction": result.prediction.to_dict() if result.prediction else None,
                "failed": result.prediction is None,
                "failures": result.failures}

    def _stage_experiment(self, hypothesis: Hypothesis, hyp_id: str, run_dir: Path) -> Dict:
        pred_data = self._load_stage(run_dir, f"08_prediction_{hyp_id}")
        if not pred_data or not pred_data.get("prediction"):
            return {"hypothesis_id": hyp_id, "experiment": None,
                    "skipped_reason": "no prediction"}
        p = pred_data["prediction"]
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
        return {"hypothesis_id": hyp_id,
                "experiment": result.proposal.to_dict() if result.proposal else None,
                "failed": result.proposal is None,
                "failures": result.failures}

    def _stage_rankings(self, challenge: DevChallenge, run_dir: Path) -> Dict:
        hyp_data = self._load_stage(run_dir, "04_hypotheses")
        transfer_data = self._load_stage(run_dir, "03_transfer")
        if not hyp_data or not transfer_data or not transfer_data.get("transfers"):
            return {"rankings": {}}
        t = transfer_data["transfers"][0]
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
        for h_dict in hyp_data["hypotheses"]:
            if not h_dict.get("is_testable"): continue
            hyp = self._reconstruct_hypothesis(h_dict)
            if not hyp: continue
            ranking = self.ranker.rank(hyp, transfer)
            rankings[hyp.hypothesis_id] = ranking.to_dict()
        return {"rankings": rankings}

    def _stage_state_machine(self, challenge: DevChallenge, run_dir: Path) -> Dict:
        hyp_data = self._load_stage(run_dir, "04_hypotheses")
        if not hyp_data:
            return {"final_state": "RAW_EVIDENCE"}
        testable = [h for h in hyp_data["hypotheses"] if h.get("is_testable")]
        sm = DiscoveryStateMachine(f"DC-{challenge.challenge_id}")
        try:
            if not testable:
                for s in [DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.MECHANISM,
                          DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.CANDIDATE_DISCOVERY,
                          DiscoveryState.GATE_A, DiscoveryState.GATE_B, DiscoveryState.GATE_C]:
                    sm.transition(s, actor="loop", code_sha="engine-v0.1",
                                  evidence="auto", reason="phase advance")
            else:
                canonical = self._reconstruct_hypothesis(testable[0])
                for s in [DiscoveryState.STRUCTURED_KNOWLEDGE, DiscoveryState.MECHANISM,
                          DiscoveryState.TRANSFER_HYPOTHESIS, DiscoveryState.CANDIDATE_DISCOVERY,
                          DiscoveryState.GATE_A, DiscoveryState.GATE_B, DiscoveryState.GATE_C,
                          DiscoveryState.TESTABLE_HYPOTHESIS]:
                    sm.transition(s, actor="loop", code_sha="engine-v0.1",
                                  evidence="auto", reason="phase advance",
                                  hypothesis=canonical if s == DiscoveryState.TESTABLE_HYPOTHESIS else None)
                exp_data = self._load_stage(run_dir, f"09_experiment_{canonical.hypothesis_id}")
                if exp_data and exp_data.get("experiment"):
                    sm.transition(DiscoveryState.EXPERIMENT,
                                  actor="loop", code_sha="engine-v0.1",
                                  evidence="experiment designed", reason="ready",
                                  hypothesis=canonical)
            return {"final_state": sm.current_state.value,
                    "history": [t.to_dict() for t in sm.history]}
        except Exception as e:
            return {"final_state": sm.current_state.value,
                    "history": [t.to_dict() for t in sm.history],
                    "error": str(e)}

    def _stage_case(self, challenge: DevChallenge, run_dir: Path) -> Dict:
        sm_data = self._load_stage(run_dir, "11_state_machine")
        case = DiscoveryCase(
            case_id=f"DC-{challenge.challenge_id}",
            input_sources=[d.get("title", "") for d in challenge.source_documents],
            input_domains=[challenge.source_domain, challenge.target_domain],
            evidence=[f"run:{challenge.challenge_id}"])
        case.provenance.add_node(ProvenanceNode(
            node_id=f"run:{challenge.challenge_id}",
            node_type="checkpointed_run",
            content_hash=_sha(challenge.challenge_id)))
        try: case.commit_provenance()
        except Exception: pass
        return {"case_id": case.case_id,
                "provenance_root_hash": case.provenance_root_hash,
                "verify_provenance": case.verify_provenance(),
                "final_state": sm_data.get("final_state", "") if sm_data else ""}

    # ===== Checkpoint helpers =====

    def _run_stage(self, manifest: RunManifest, stage: str,
                   manifest_path: Path, run_dir: Path, fn) -> None:
        if stage not in manifest.stages:
            manifest.stages[stage] = StageStatus(stage=stage)
        ss = manifest.stages[stage]
        ss.status = RUNNING; ss.started_at = _now()
        manifest.last_updated = _now(); manifest.resume_from = stage
        self._save_manifest(manifest, manifest_path)
        start = time.time()
        try:
            output = fn()
            ss.latency_ms = int((time.time() - start) * 1000)
            ss.completed_at = _now(); ss.status = COMPLETED
            (run_dir / f"{stage}.json").write_text(json.dumps(output, indent=2, default=str))
        except Exception as e:
            ss.latency_ms = int((time.time() - start) * 1000)
            ss.completed_at = _now(); ss.status = FAILED
            ss.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        manifest.last_updated = _now()
        self._save_manifest(manifest, manifest_path)

    def _is_completed(self, manifest: RunManifest, stage: str) -> bool:
        s = manifest.stages.get(stage)
        return s is not None and s.status == COMPLETED

    def _load_stage(self, run_dir: Path, stage: str) -> Optional[Dict]:
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
                        resume_from=d.get("resume_from", "01_extraction"),
                        n_hypotheses=d.get("n_hypotheses", 0),
                        final_state=d.get("final_state", ""),
                        completed=d.get("completed", False))
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


__all__ = ["CheckpointedDiscoveryLoop", "RunManifest", "StageStatus",
           "PENDING", "RUNNING", "COMPLETED", "FAILED", "SKIPPED", "RUNS_DIR"]
