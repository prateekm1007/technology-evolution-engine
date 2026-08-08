"""prediction_engine.py — Phase 8: Hypothesis → Prediction (no vague predictions)."""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    Hypothesis, Prediction, ProvenanceGraph, ProvenanceNode, UnfalsifiableError)
from engine.providers import ReasoningProvider, ProviderCallManifest


@dataclass
class PredictionResult:
    hypothesis_id: str
    prediction: Optional[Prediction] = None
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)


_PREDICTION_PROMPT = """You are a scientific prediction engine. Given a hypothesis, produce a SPECIFIC, falsifiable prediction.

Required:
  - observable: what to measure (a concrete quantity)
  - baseline: comparison baseline
  - expected_direction: increase/decrease/appear/disappear/etc.
  - expected_magnitude: estimated size (e.g. "10-30% improvement")
  - conditions: under what conditions
  - uncertainty: number in [0,1]
  - falsifier: what observation would refute — REQUIRED, non-empty

DO NOT produce vague predictions like "performance may improve."

Output JSON only:
{{
  "observable": "...", "baseline": "...", "expected_direction": "...",
  "expected_magnitude": "...", "conditions": ["..."],
  "uncertainty": 0.0, "falsifier": "..."
}}

HYPOTHESIS:
{hypothesis_json}

Output JSON only."""


class PredictionEngine:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def predict(self, hypothesis: Hypothesis, *, prediction_id: str = "P-001") -> PredictionResult:
        result = PredictionResult(hypothesis_id=hypothesis.hypothesis_id)
        hyp_json = json.dumps({"claim": hypothesis.claim, "mechanism": hypothesis.mechanism,
                               "falsifier": hypothesis.falsifier}, indent=2)
        prompt = _PREDICTION_PROMPT.format(hypothesis_json=hyp_json)
        response, manifest = self._provider.generate(
            prompt, system="You are a scientific prediction engine. Output JSON only.",
            temperature=0.15)
        result.manifests.append(manifest)
        result.provenance.add_node(ProvenanceNode(
            node_id=f"prediction-attempt:{hypothesis.hypothesis_id}",
            node_type="prediction_attempt", content_hash=_sha(prompt[:500])))
        if not manifest.success or not response.strip():
            result.failures.append({"type": "PROVIDER_FAILURE", "detail": manifest.error})
            return result
        parsed = _parse_json_tolerant(response)
        if not parsed:
            result.failures.append({"type": "MALFORMED_JSON", "detail": response[:200]})
            return result
        falsifier = (parsed.get("falsifier") or "").strip()
        if not falsifier:
            result.failures.append({"type": "UNFALSIFIABLE_PREDICTION"})
            return result
        try:
            uncertainty = float(parsed.get("uncertainty", 0.5))
            if not 0.0 <= uncertainty <= 1.0: uncertainty = 0.5
        except (TypeError, ValueError):
            uncertainty = 0.5
        try:
            result.prediction = Prediction(
                prediction_id=prediction_id, hypothesis_id=hypothesis.hypothesis_id,
                observable=parsed.get("observable", ""),
                expected_direction=parsed.get("expected_direction", ""),
                expected_magnitude=parsed.get("expected_magnitude", ""),
                conditions=_as_str_list(parsed.get("conditions", [])),
                baseline=parsed.get("baseline", ""), falsifier=falsifier,
                uncertainty=uncertainty, is_testable=True)
        except UnfalsifiableError as e:
            result.failures.append({"type": "UNFALSIFIABLE_PREDICTION", "detail": str(e)})
        except ValueError as e:
            result.failures.append({"type": "BOUNDS_VIOLATION", "detail": str(e)})
        return result


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _as_str_list(x: Any) -> List[str]:
    if isinstance(x, list): return [str(i) for i in x if i]
    if isinstance(x, str): return [x]
    return []

def _parse_json_tolerant(text: str) -> Optional[Dict]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
    first = text.find("{"); last = text.rfind("}")
    if first == -1 or last == -1 or last <= first: return None
    try: return json.loads(text[first:last + 1])
    except json.JSONDecodeError: return None


__all__ = ["PredictionEngine", "PredictionResult"]
