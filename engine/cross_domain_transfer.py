"""cross_domain_transfer.py — Phase 3: pattern + target → TransferHypothesis."""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    TransferHypothesis, ProvenanceGraph, ProvenanceNode, EpistemicState)
from engine.mechanism_abstraction import MechanismPattern
from engine.providers import ReasoningProvider, ProviderCallManifest


@dataclass
class TransferResult:
    transfers: List[TransferHypothesis] = field(default_factory=list)
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)
    rejected: List[Dict] = field(default_factory=list)


_TRANSFER_PROMPT = """You are a cross-domain transfer hypothesis engine.

Given a source mechanism pattern (from domain A) and a target problem (in domain B), propose ONE plausible mechanism transfer. The transfer must NOT be a mere entity overlap — it must map the abstract causal structure of the source onto the target system.

If you cannot produce a plausible translation mapping that explains HOW the source mechanism would operate in the target system, output {{"reject": true, "reason": "..."}}.

Otherwise output (JSON only):
{{
  "source_mechanism": "...",
  "source_conditions": ["..."],
  "transferred_principle": "...",
  "required_translation": "what must change for the mechanism to operate in the target — be specific about physical/material substitutions",
  "expected_effect": "...",
  "boundary_conditions": ["..."],
  "failure_conditions": ["..."],
  "testable_prediction": "a specific, falsifiable prediction"
}}

SOURCE PATTERN (from domain A):
{pattern_json}

TARGET PROBLEM (in domain B):
{problem}

TARGET CONSTRAINTS:
{constraints}

Output JSON only. If no plausible mapping exists, reject."""


class CrossDomainTransferEngine:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def generate(self, pattern: MechanismPattern, *,
                 target_domain: str, target_problem: str,
                 target_constraints: List[str],
                 transfer_id_prefix: str = "TH") -> TransferResult:
        result = TransferResult()
        pattern_json = json.dumps(pattern.to_dict(), indent=2)[:4000]
        prompt = _TRANSFER_PROMPT.format(
            pattern_json=pattern_json, problem=target_problem,
            constraints="\n".join(f"- {c}" for c in target_constraints))
        response, manifest = self._provider.generate(
            prompt, system="You are a cross-domain transfer engine. Output JSON only.",
            temperature=0.25)
        result.manifests.append(manifest)
        result.provenance.add_node(ProvenanceNode(
            node_id=f"transfer-attempt:{transfer_id_prefix}",
            node_type="transfer_attempt", content_hash=_sha(prompt[:500])))
        if not manifest.success or not response.strip():
            result.failures.append({"type": "PROVIDER_FAILURE", "detail": manifest.error})
            return result
        parsed = _parse_json_tolerant(response)
        if not parsed:
            result.failures.append({"type": "MALFORMED_JSON", "detail": response[:200]})
            return result
        if parsed.get("reject"):
            result.rejected.append({"reason": parsed.get("reason", "no reason"),
                                    "source_pattern": pattern.pattern_id})
            return result
        required = ["transferred_principle", "required_translation",
                    "expected_effect", "testable_prediction"]
        missing = [f for f in required if not (parsed.get(f) or "").strip()]
        if missing:
            result.failures.append({"type": "MISSING_REQUIRED_FIELD", "detail": f"missing {missing}"})
            return result
        transfer = TransferHypothesis(
            transfer_id=f"{transfer_id_prefix}-001",
            source_domain=pattern.source_domain,
            source_mechanism=parsed.get("source_mechanism", pattern.abstract_principle),
            source_conditions=_as_str_list(parsed.get("source_conditions", [])),
            target_domain=target_domain,
            target_problem=target_problem,
            transferred_principle=parsed["transferred_principle"],
            required_translation=parsed["required_translation"],
            expected_effect=parsed["expected_effect"],
            boundary_conditions=_as_str_list(parsed.get("boundary_conditions", [])),
            failure_conditions=_as_str_list(parsed.get("failure_conditions", [])),
            testable_prediction=parsed["testable_prediction"],
            epistemic_state=EpistemicState.HYPOTHESIZED)
        result.transfers.append(transfer)
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


__all__ = ["CrossDomainTransferEngine", "TransferResult"]
