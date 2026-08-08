"""novelty_firewall.py — Phase 7: DEV_ONLY prior-art check.

CRITICAL INVARIANT: "no match found" → NOT_EVALUATED, NEVER NOVEL_AS_OF_CUTOFF.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    Hypothesis, PriorArtAssessment, NoveltyStatus, ProvenanceGraph, ProvenanceNode)
from engine.providers import ReasoningProvider, ProviderCallManifest, LiteratureProvider


@dataclass
class NoveltyReport:
    hypothesis_id: str
    assessment: Optional[PriorArtAssessment] = None
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"hypothesis_id": self.hypothesis_id,
                "assessment": self.assessment.to_dict() if self.assessment else None,
                "provenance": self.provenance.to_dict(),
                "manifests": [m.to_dict() for m in self.manifests],
                "failures": self.failures}


class NoveltyFirewall:
    """DEV_ONLY prior-art check.

    Uses the LiteratureProvider to search a development corpus.
    CRITICAL: if the literature search returns NO matches, status is
    NOT_EVALUATED — NEVER NOVEL_AS_OF_CUTOFF. "No evidence found" is
    not proof of novelty.
    """

    def __init__(self, provider: ReasoningProvider, literature: LiteratureProvider):
        self._provider = provider
        self._literature = literature

    def assess(self, hypothesis: Hypothesis, *, cutoff: str = "2026-08-08",
               assessment_id: str = "PA-001") -> NoveltyReport:
        result = NoveltyReport(hypothesis_id=hypothesis.hypothesis_id)
        result.provenance.add_node(ProvenanceNode(
            node_id=f"novelty:{hypothesis.hypothesis_id}",
            node_type="novelty_assessment",
            content_hash=hashlib.sha256(hypothesis.claim.encode()).hexdigest()))
        query = f"{hypothesis.claim} {hypothesis.mechanism}"
        results, lit_manifest = self._literature.search(query, cutoff=cutoff, k=10)
        result.manifests.append(lit_manifest)
        if not results:
            status = NoveltyStatus.NOT_EVALUATED
            similarity = "no matches in dev corpus — NOT proof of novelty"
            review_required = True
        elif _any_strong_match(results, hypothesis):
            status = NoveltyStatus.PRIOR_ART_FOUND
            similarity = "strong match found in dev corpus"
            review_required = False
        elif _any_partial_match(results, hypothesis):
            status = NoveltyStatus.PARTIAL_PRECEDENT
            similarity = "partial precedent found in dev corpus"
            review_required = True
        else:
            status = NoveltyStatus.AMBIGUOUS
            similarity = "weak matches in dev corpus"
            review_required = True
        # We NEVER return NOVEL_AS_OF_CUTOFF from a DEV_ONLY literature search.
        result.assessment = PriorArtAssessment(
            assessment_id=assessment_id,
            hypothesis_id=hypothesis.hypothesis_id,
            status=status, search_scope=["dev_corpus"], queries=[query],
            sources=[r.get("title", "") for r in results],
            matched_prior_art=[r.get("title", "") for r in results
                               if _any_strong_match([r], hypothesis)],
            similarity=similarity, review_required=review_required,
            confidence=0.3 if status == NoveltyStatus.NOT_EVALUATED else 0.7,
            cutoff=cutoff, reviewer="novelty_firewall_v0")
        return result


def _any_strong_match(results: List[Dict], hypothesis: Hypothesis) -> bool:
    sig_tokens = {t.lower() for t in hypothesis.mechanism.split()
                  if len(t) > 4 and t.isalpha()}
    if not sig_tokens: return False
    for r in results:
        text = (r.get("title", "") + " " + r.get("abstract", "")).lower()
        overlap = sum(1 for t in sig_tokens if t in text)
        if overlap >= 4: return True
    return False


def _any_partial_match(results: List[Dict], hypothesis: Hypothesis) -> bool:
    sig_tokens = {t.lower() for t in hypothesis.mechanism.split()
                  if len(t) > 4 and t.isalpha()}
    if not sig_tokens: return False
    for r in results:
        text = (r.get("title", "") + " " + r.get("abstract", "")).lower()
        overlap = sum(1 for t in sig_tokens if t in text)
        if 2 <= overlap < 4: return True
    return False


__all__ = ["NoveltyFirewall", "NoveltyReport"]
