"""rediscovery_detection.py — Phase 6: is the hypothesis novel or rediscovery?"""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import Hypothesis, ProvenanceGraph, ProvenanceNode
from engine.providers import ReasoningProvider, ProviderCallManifest


class RediscoveryClass(str, Enum):
    EXPLICITLY_PRESENT = "EXPLICITLY_PRESENT"
    PARAPHRASED_IN_INPUT = "PARAPHRASED_IN_INPUT"
    DIRECT_COMPOSITION = "DIRECT_COMPOSITION"
    STRUCTURAL_INFERENCE = "STRUCTURAL_INFERENCE"
    NON_TRIVIAL_TRANSFER = "NON_TRIVIAL_TRANSFER"
    UNKNOWN = "UNKNOWN"

    @property
    def is_rediscovery(self) -> bool:
        return self in {RediscoveryClass.EXPLICITLY_PRESENT,
                        RediscoveryClass.PARAPHRASED_IN_INPUT,
                        RediscoveryClass.DIRECT_COMPOSITION}


@dataclass
class RediscoveryReport:
    hypothesis_id: str
    classification: RediscoveryClass = RediscoveryClass.UNKNOWN
    evidence: str = ""
    is_rediscovery: bool = False
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"hypothesis_id": self.hypothesis_id,
                "classification": self.classification.value,
                "evidence": self.evidence,
                "is_rediscovery": self.is_rediscovery,
                "provenance": self.provenance.to_dict(),
                "manifests": [m.to_dict() for m in self.manifests],
                "failures": self.failures}


_REDISCOVERY_PROMPT = """You are a rediscovery detector. Given a hypothesis and the source documents it was derived from, classify how the hypothesis relates to the source.

Classifications:
  EXPLICITLY_PRESENT — stated verbatim or near-verbatim in source
  PARAPHRASED_IN_INPUT — restatement of source content
  DIRECT_COMPOSITION — entity intersection / composition of source entities
  STRUCTURAL_INFERENCE — structural reasoning beyond source text, within source domain
  NON_TRIVIAL_TRANSFER — genuine cross-domain transfer not reducible to source
  UNKNOWN — cannot determine

Be strict. If the hypothesis could be produced by a retrieval system reading the source, it is NOT NON_TRIVIAL_TRANSFER.

Output JSON only:
{{
  "classification": "...",
  "evidence": "..."
}}

HYPOTHESIS CLAIM:
{claim}

HYPOTHESIS MECHANISM:
{mechanism}

SOURCE DOCUMENTS:
{sources}

Output JSON only."""


class RediscoveryDetector:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def classify(self, hypothesis: Hypothesis,
                 source_documents: List[Dict[str, str]]) -> RediscoveryReport:
        result = RediscoveryReport(hypothesis_id=hypothesis.hypothesis_id)
        sources_text = "\n\n---\n\n".join(
            f"TITLE: {d.get('title','')}\nTEXT: {d.get('text','')[:2000]}"
            for d in source_documents)[:5000]
        prompt = _REDISCOVERY_PROMPT.format(
            claim=hypothesis.claim, mechanism=hypothesis.mechanism, sources=sources_text)
        response, manifest = self._provider.generate(
            prompt, system="You are a rediscovery detector. Be strict. Output JSON only.",
            temperature=0.1)
        result.manifests.append(manifest)
        result.provenance.add_node(ProvenanceNode(
            node_id=f"rediscovery:{hypothesis.hypothesis_id}",
            node_type="rediscovery_analysis", content_hash=_sha(prompt[:500])))
        if not manifest.success or not response.strip():
            result.failures.append({"type": "PROVIDER_FAILURE", "detail": manifest.error})
            return result
        parsed = _parse_json_tolerant(response)
        if not parsed:
            result.failures.append({"type": "MALFORMED_JSON", "detail": response[:200]})
            return result
        cls_str = parsed.get("classification", "UNKNOWN").upper()
        try:
            result.classification = RediscoveryClass(cls_str)
        except ValueError:
            result.classification = RediscoveryClass.UNKNOWN
        result.evidence = parsed.get("evidence", "")
        result.is_rediscovery = result.classification.is_rediscovery
        return result


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _parse_json_tolerant(text: str) -> Optional[Dict]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
    first = text.find("{"); last = text.rfind("}")
    if first == -1 or last == -1 or last <= first: return None
    try: return json.loads(text[first:last + 1])
    except json.JSONDecodeError: return None


__all__ = ["RediscoveryDetector", "RediscoveryReport", "RediscoveryClass"]
