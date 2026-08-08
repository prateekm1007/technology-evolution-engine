"""hypothesis_generation.py — Phase 4: TransferHypothesis → competing Hypotheses."""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    Hypothesis, TransferHypothesis, ProvenanceGraph, ProvenanceNode, EpistemicState)
from engine.providers import ReasoningProvider, ProviderCallManifest


@dataclass
class HypothesisSet:
    transfer_id: str
    hypotheses: List[Hypothesis] = field(default_factory=list)
    distinguishing_predictions: str = ""
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)


_HYPOTHESIS_PROMPT = """You are a scientific hypothesis generation engine.

Given a transfer hypothesis, generate 2-4 COMPETING hypotheses that explain how the transferred mechanism might operate in the target system. The hypotheses must be MATERIALLY DIFFERENT — not restatements of the same idea.

For each hypothesis, you MUST provide a falsifier: an observation that would prove the hypothesis WRONG.

Also describe: what observations would DISTINGUISH the hypotheses from each other?

Output (JSON only):
{{
  "hypotheses": [
    {{
      "claim": "...", "mechanism": "...", "assumptions": ["..."],
      "evidence": ["..."], "novelty_rationale": "...",
      "testability": "...", "falsifier": "... (REQUIRED non-empty)",
      "expected_failure_modes": ["..."]
    }}
  ],
  "distinguishing_predictions": "..."
}}

TRANSFER HYPOTHESIS:
{transfer_json}

Output JSON only. Every hypothesis MUST have a non-empty falsifier."""


class HypothesisGenerationEngine:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def generate(self, transfer: TransferHypothesis, *, id_prefix: str = "H") -> HypothesisSet:
        result = HypothesisSet(transfer_id=transfer.transfer_id)
        transfer_json = json.dumps(transfer.to_dict(), indent=2)[:4000]
        prompt = _HYPOTHESIS_PROMPT.format(transfer_json=transfer_json)
        response, manifest = self._provider.generate(
            prompt, system="You are a scientific hypothesis engine. Output JSON only.",
            temperature=0.3)
        result.manifests.append(manifest)
        result.provenance.add_node(ProvenanceNode(
            node_id=f"hypothesis-set:{transfer.transfer_id}",
            node_type="hypothesis_set", content_hash=_sha(prompt[:500])))
        if not manifest.success or not response.strip():
            result.failures.append({"type": "PROVIDER_FAILURE", "detail": manifest.error})
            return result
        parsed = _parse_json_tolerant(response)
        if not parsed:
            result.failures.append({"type": "MALFORMED_JSON", "detail": response[:200]})
            return result
        result.distinguishing_predictions = parsed.get("distinguishing_predictions", "")
        for i, raw in enumerate(parsed.get("hypotheses", []), start=1):
            if not isinstance(raw, dict): continue
            falsifier = (raw.get("falsifier") or "").strip()
            if not falsifier:
                result.failures.append({"type": "UNFALSIFIABLE_HYPOTHESIS_REJECTED",
                    "detail": f"hypothesis {i} no falsifier — recorded as EXPLORATORY"})
                try:
                    hyp = Hypothesis(
                        hypothesis_id=f"{id_prefix}-{i:03d}",
                        claim=raw.get("claim", ""), mechanism=raw.get("mechanism", ""),
                        assumptions=_as_str_list(raw.get("assumptions", [])),
                        evidence=_as_str_list(raw.get("evidence", [])),
                        novelty_rationale=raw.get("novelty_rationale", ""),
                        testability=raw.get("testability", ""), falsifier="",
                        expected_failure_modes=_as_str_list(raw.get("expected_failure_modes", [])),
                        is_testable=False)
                    result.hypotheses.append(hyp)
                except Exception as e:
                    result.failures.append({"type": "CONSTRUCTION_FAILED", "detail": str(e)})
                continue
            try:
                hyp = Hypothesis(
                    hypothesis_id=f"{id_prefix}-{i:03d}",
                    claim=raw.get("claim", ""), mechanism=raw.get("mechanism", ""),
                    assumptions=_as_str_list(raw.get("assumptions", [])),
                    evidence=_as_str_list(raw.get("evidence", [])),
                    novelty_rationale=raw.get("novelty_rationale", ""),
                    testability=raw.get("testability", ""), falsifier=falsifier,
                    expected_failure_modes=_as_str_list(raw.get("expected_failure_modes", [])),
                    is_testable=True)
                result.hypotheses.append(hyp)
            except Exception as e:
                result.failures.append({"type": "CONSTRUCTION_FAILED", "detail": str(e)})
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


__all__ = ["HypothesisGenerationEngine", "HypothesisSet"]
