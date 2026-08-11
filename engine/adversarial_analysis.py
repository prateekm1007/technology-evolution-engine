"""adversarial_analysis.py — Phase 5: Hypothesis → failure modes."""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import Hypothesis, ProvenanceGraph, ProvenanceNode
from engine.providers import ReasoningProvider, ProviderCallManifest


@dataclass
class AdversarialFailureMode:
    category: str
    description: str
    severity: str
    evidence: str = ""


@dataclass
class AdversarialAnalysis:
    hypothesis_id: str
    failure_modes: List[AdversarialFailureMode] = field(default_factory=list)
    survives: bool = True
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"hypothesis_id": self.hypothesis_id,
                "failure_modes": [f.__dict__ for f in self.failure_modes],
                "survives": self.survives,
                "provenance": self.provenance.to_dict(),
                "manifests": [m.to_dict() for m in self.manifests],
                "failures": self.failures}


_ADVERSARIAL_PROMPT = """You are an adversarial scientific critic. Find reasons the following hypothesis should FAIL. Do not be polite. Find the weakest points.

For each failure mode, classify as one of:
  FRAGILE_ASSUMPTION, CONTRADICTS_KNOWN, BOUNDARY_BREAKS, PRIOR_ART_EXISTS, FALSIFIER_TRIGGERED, INCOMPATIBLE_TARGET

Severity: HIGH (likely wrong), MEDIUM (significant concern), LOW (minor).

Output JSON only:
{{
  "failure_modes": [
    {{"category": "...", "description": "...", "severity": "HIGH|MEDIUM|LOW", "evidence": "..."}}
  ],
  "survives": true | false,
  "survives_reason": "..."
}}

HYPOTHESIS:
{hypothesis_json}

Be adversarial. Find real weaknesses. Do not rubber-stamp."""


class AdversarialAnalysisEngine:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def analyze(self, hypothesis: Hypothesis) -> AdversarialAnalysis:
        result = AdversarialAnalysis(hypothesis_id=hypothesis.hypothesis_id)
        hyp_json = json.dumps(hypothesis.to_dict(), indent=2)[:3000]
        prompt = _ADVERSARIAL_PROMPT.format(hypothesis_json=hyp_json)
        response, manifest = self._provider.generate(
            prompt, system="You are an adversarial scientific critic. Output JSON only.",
            temperature=0.2)
        result.manifests.append(manifest)
        result.provenance.add_node(ProvenanceNode(
            node_id=f"adversarial:{hypothesis.hypothesis_id}",
            node_type="adversarial_analysis", content_hash=_sha(prompt[:500])))
        if not manifest.success or not response.strip():
            result.failures.append({"type": "PROVIDER_FAILURE", "detail": manifest.error})
            return result
        parsed = _parse_json_tolerant(response)
        if not parsed:
            result.failures.append({"type": "MALFORMED_JSON", "detail": response[:200]})
            return result
        for raw in parsed.get("failure_modes", []):
            if not isinstance(raw, dict): continue
            result.failure_modes.append(AdversarialFailureMode(
                category=raw.get("category", "UNKNOWN"),
                description=raw.get("description", ""),
                severity=raw.get("severity", "MEDIUM").upper(),
                evidence=raw.get("evidence", "")))
        result.survives = bool(parsed.get("survives", True))
        if any(f.severity == "HIGH" and f.category == "CONTRADICTS_KNOWN"
               for f in result.failure_modes):
            result.survives = False
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


__all__ = ["AdversarialAnalysisEngine", "AdversarialAnalysis", "AdversarialFailureMode"]
