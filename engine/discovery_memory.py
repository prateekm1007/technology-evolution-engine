"""discovery_memory.py — Phase 11: long-term scientific memory."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List
from discovery_infrastructure.discovery_substrate import (
    TransferHypothesis, DiscoveryFailure, ProvenanceGraph, ProvenanceNode)


@dataclass
class SuccessfulMechanism:
    mechanism: str
    source_domain: str
    conditions: List[str]
    successful_transfer_id: str


@dataclass
class FailedTransfer:
    mechanism: str
    target_domain: str
    failure_condition: str
    evidence: List[str]
    failure_id: str


@dataclass
class BrokenAnalogy:
    apparent_similarity: str
    reason_failed: str
    source_mechanism: str
    target_mechanism: str


@dataclass
class SuccessfulTransformation:
    source_mechanism: str
    abstraction: str
    target_mechanism: str
    validated_result_id: str


class DiscoveryMemory:
    """In-process long-term scientific memory."""

    def __init__(self):
        self.successful: List[SuccessfulMechanism] = []
        self.failed: List[FailedTransfer] = []
        self.broken_analogies: List[BrokenAnalogy] = []
        self.transformations: List[SuccessfulTransformation] = []
        self.provenance = ProvenanceGraph()

    def record_success(self, transfer: TransferHypothesis) -> None:
        self.successful.append(SuccessfulMechanism(
            mechanism=transfer.source_mechanism, source_domain=transfer.source_domain,
            conditions=transfer.source_conditions, successful_transfer_id=transfer.transfer_id))
        self.provenance.add_node(ProvenanceNode(
            node_id=f"memory:success:{transfer.transfer_id}",
            node_type="memory_success", content_hash=_sha(transfer.transfer_id)))

    def record_failure(self, transfer: TransferHypothesis, failure: DiscoveryFailure) -> None:
        self.failed.append(FailedTransfer(
            mechanism=transfer.source_mechanism, target_domain=transfer.target_domain,
            failure_condition=failure.failure_mode, evidence=failure.evidence,
            failure_id=failure.failure_id))
        if "boundary" in failure.failure_mode.lower() or "analogy" in failure.failure_mode.lower():
            self.broken_analogies.append(BrokenAnalogy(
                apparent_similarity=transfer.transferred_principle,
                reason_failed=failure.reusable_lesson,
                source_mechanism=transfer.source_mechanism,
                target_mechanism=transfer.target_problem))
        self.provenance.add_node(ProvenanceNode(
            node_id=f"memory:failure:{failure.failure_id}",
            node_type="memory_failure", content_hash=_sha(failure.failure_id)))

    def record_transformation(self, source_mech: str, abstraction: str,
                              target_mech: str, validated_id: str) -> None:
        self.transformations.append(SuccessfulTransformation(
            source_mechanism=source_mech, abstraction=abstraction,
            target_mechanism=target_mech, validated_result_id=validated_id))

    def query_mechanisms_for_domain(self, domain: str) -> List[SuccessfulMechanism]:
        return [s for s in self.successful if s.source_domain == domain]

    def query_failures_for_target(self, target_domain: str) -> List[FailedTransfer]:
        return [f for f in self.failed if f.target_domain == target_domain]

    def query_broken_analogies(self, similarity: str) -> List[BrokenAnalogy]:
        s_lower = similarity.lower()
        return [b for b in self.broken_analogies
                if s_lower in b.apparent_similarity.lower()]

    def to_dict(self) -> Dict:
        return {"successful": [s.__dict__ for s in self.successful],
                "failed": [f.__dict__ for f in self.failed],
                "broken_analogies": [b.__dict__ for b in self.broken_analogies],
                "transformations": [t.__dict__ for t in self.transformations],
                "n_success": len(self.successful), "n_failure": len(self.failed),
                "n_broken": len(self.broken_analogies),
                "n_transformations": len(self.transformations)}


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = ["DiscoveryMemory", "SuccessfulMechanism", "FailedTransfer",
           "BrokenAnalogy", "SuccessfulTransformation"]
