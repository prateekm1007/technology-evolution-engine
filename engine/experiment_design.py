"""experiment_design.py — Phase 9: Hypothesis + Prediction → ExperimentProposal."""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    Hypothesis, Prediction, ExperimentProposal, ProvenanceGraph, ProvenanceNode, UnfalsifiableError)
from engine.providers import ReasoningProvider, ProviderCallManifest


@dataclass
class ExperimentResult:
    hypothesis_id: str
    proposal: Optional[ExperimentProposal] = None
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)


_EXPERIMENT_PROMPT = """You are a scientific experiment design engine. Given a hypothesis and its prediction, design the cheapest experiment that could distinguish this hypothesis from its competitors.

Required:
  - objective, independent_variables, dependent_variables
  - controls (REQUIRED — at least one)
  - baseline, procedure, expected_result
  - falsification_condition (REQUIRED, non-empty)
  - sample_requirements, safety_constraints
  - estimated_cost (low/medium/high), estimated_duration
  - information_gain

Output JSON only:
{{
  "objective": "...", "independent_variables": ["..."],
  "dependent_variables": ["..."], "controls": ["..."],
  "baseline": "...", "procedure": "...", "expected_result": "...",
  "falsification_condition": "...", "sample_requirements": "...",
  "safety_constraints": ["..."], "estimated_cost": "...",
  "estimated_duration": "...", "information_gain": "..."
}}

HYPOTHESIS:
{hypothesis_json}

PREDICTION:
{prediction_json}

Output JSON only. falsification_condition MUST be non-empty."""


class ExperimentDesignEngine:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def design(self, hypothesis: Hypothesis, prediction: Prediction,
               *, experiment_id: str = "E-001") -> ExperimentResult:
        result = ExperimentResult(hypothesis_id=hypothesis.hypothesis_id)
        hyp_json = json.dumps({"claim": hypothesis.claim, "mechanism": hypothesis.mechanism}, indent=2)
        pred_json = json.dumps(prediction.to_dict(), indent=2)
        prompt = _EXPERIMENT_PROMPT.format(hypothesis_json=hyp_json, prediction_json=pred_json)
        response, manifest = self._provider.generate(
            prompt, system="You are an experiment design engine. Output JSON only.",
            temperature=0.2)
        result.manifests.append(manifest)
        result.provenance.add_node(ProvenanceNode(
            node_id=f"experiment-design:{hypothesis.hypothesis_id}",
            node_type="experiment_design_attempt", content_hash=_sha(prompt[:500])))
        if not manifest.success or not response.strip():
            result.failures.append({"type": "PROVIDER_FAILURE", "detail": manifest.error})
            return result
        parsed = _parse_json_tolerant(response)
        if not parsed:
            result.failures.append({"type": "MALFORMED_JSON", "detail": response[:200]})
            return result
        falsification = (parsed.get("falsification_condition") or "").strip()
        if not falsification:
            result.failures.append({"type": "MISSING_FALSIFICATION"})
            return result
        controls = _as_str_list(parsed.get("controls", []))
        if not controls:
            result.failures.append({"type": "MISSING_CONTROLS"})
            return result
        try:
            result.proposal = ExperimentProposal(
                experiment_id=experiment_id, hypothesis_id=hypothesis.hypothesis_id,
                objective=parsed.get("objective", ""),
                independent_variables=_as_str_list(parsed.get("independent_variables", [])),
                dependent_variables=_as_str_list(parsed.get("dependent_variables", [])),
                controls=controls, baseline=parsed.get("baseline", ""),
                procedure=parsed.get("procedure", ""),
                expected_result=parsed.get("expected_result", ""),
                falsification_condition=falsification,
                sample_requirements=parsed.get("sample_requirements", ""),
                safety_constraints=_as_str_list(parsed.get("safety_constraints", [])),
                estimated_cost=parsed.get("estimated_cost", ""),
                estimated_duration=parsed.get("estimated_duration", ""),
                information_gain=parsed.get("information_gain", ""),
                is_testable=True)
        except UnfalsifiableError as e:
            result.failures.append({"type": "UNFALSIFIABLE_EXPERIMENT", "detail": str(e)})
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


__all__ = ["ExperimentDesignEngine", "ExperimentResult"]
