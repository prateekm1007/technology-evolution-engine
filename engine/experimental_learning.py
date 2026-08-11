"""experimental_learning.py — Phase 10: result → learning + failure record."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    Hypothesis, Prediction, ExperimentProposal, DiscoveryFailure, FailureType,
    ProvenanceGraph, ProvenanceNode)


@dataclass
class ExperimentalResult:
    experiment_id: str
    actual_result: str = ""
    prediction_error: str = ""
    supported: bool = False
    falsified: bool = False
    unexpected_observation: str = ""
    new_constraints: List[str] = field(default_factory=list)
    new_hypotheses: List[str] = field(default_factory=list)
    reusable_lesson: str = ""


@dataclass
class LearningRecord:
    result: ExperimentalResult
    failure: Optional[DiscoveryFailure] = None
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)

    def to_dict(self) -> Dict:
        return {"result": self.result.__dict__,
                "failure": self.failure.to_dict() if self.failure else None,
                "provenance": self.provenance.to_dict()}


class ExperimentalLearningEngine:
    """Record experimental results. Convert failures into knowledge."""

    def record(self, hypothesis: Hypothesis, prediction: Prediction,
               experiment: ExperimentProposal,
               result: ExperimentalResult) -> LearningRecord:
        record = LearningRecord(result=result)
        record.provenance.add_node(ProvenanceNode(
            node_id=f"result:{experiment.experiment_id}",
            node_type="experimental_result",
            content_hash=_sha(result.actual_result)))
        if not result.prediction_error:
            if result.falsified:
                result.prediction_error = "actual result contradicted prediction"
            elif result.supported:
                result.prediction_error = "actual result matched prediction direction"
            else:
                result.prediction_error = "inconclusive"
        if result.falsified:
            failure_type = FailureType.FAILED_PREDICTION
            if "boundary" in result.unexpected_observation.lower():
                failure_type = FailureType.DOMAIN_TRANSFER_FAILURE
            elif "prior" in result.unexpected_observation.lower():
                failure_type = FailureType.PRIOR_ART
            record.failure = DiscoveryFailure(
                failure_id=f"F-{experiment.experiment_id}",
                failure_type=failure_type,
                hypothesis_id=hypothesis.hypothesis_id,
                why_rejected=result.unexpected_observation or "falsified by experiment",
                evidence=[experiment.experiment_id, prediction.prediction_id],
                conditions=result.new_constraints,
                failure_mode=result.prediction_error,
                reusable_lesson=result.reusable_lesson or _default_lesson(hypothesis, result),
                related_hypotheses=result.new_hypotheses)
        return record


def _default_lesson(hypothesis: Hypothesis, result: ExperimentalResult) -> str:
    return (f"Hypothesis '{hypothesis.hypothesis_id}' was falsified. "
            f"Mechanism that did not transfer: {hypothesis.mechanism[:200]}. "
            f"Reason: {result.prediction_error}. "
            f"Constraints to avoid: {', '.join(result.new_constraints) or 'none recorded'}.")


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = ["ExperimentalLearningEngine", "ExperimentalResult", "LearningRecord"]
