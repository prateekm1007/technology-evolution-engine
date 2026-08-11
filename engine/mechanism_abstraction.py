"""mechanism_abstraction.py — Phase 2: MechanismGraph → MechanismPattern."""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import MechanismGraph, ProvenanceGraph, ProvenanceNode
from engine.providers import ReasoningProvider, ProviderCallManifest


@dataclass
class MechanismPattern:
    pattern_id: str
    source_domain: str = ""
    causal_structure: str = ""
    inputs: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    operations: List[str] = field(default_factory=list)
    intermediate_state: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    failure_conditions: List[str] = field(default_factory=list)
    abstract_principle: str = ""
    source_graph_summary: str = ""

    def to_dict(self) -> Dict:
        return {k: getattr(self, k) for k in [
            "pattern_id", "source_domain", "causal_structure", "inputs",
            "conditions", "operations", "intermediate_state", "outputs",
            "constraints", "failure_conditions", "abstract_principle",
            "source_graph_summary"]}


@dataclass
class AbstractionResult:
    pattern: MechanismPattern
    provenance: ProvenanceGraph
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)


_ABSTRACTION_PROMPT = """You are a scientific abstraction engine. Given a mechanism graph from a specific domain, produce a DOMAIN-ABSTRACTED mechanism pattern.

Strip domain-specific vocabulary. Preserve the CAUSAL ROLE of each component. A "wax papillae" in botany and a "nano-pillar coating" in materials science both become "structural element creating hierarchical roughness."

Output JSON only:
{{
  "abstract_principle": "one-sentence core idea, domain-neutral",
  "causal_structure": "X enables Y under Z, producing W",
  "inputs": ["..."], "conditions": ["..."], "operations": ["..."],
  "intermediate_state": ["..."], "outputs": ["..."],
  "constraints": ["..."], "failure_conditions": ["..."]
}}

SOURCE DOMAIN: {domain}
SOURCE TITLE: {title}
MECHANISM GRAPH (JSON):
{graph_json}

Output JSON only."""


class MechanismAbstractionEngine:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def abstract(self, graph: MechanismGraph, *, source_domain: str,
                 source_title: str, pattern_id: str) -> AbstractionResult:
        graph_json = json.dumps(graph.to_dict(), indent=2)[:6000]
        prompt = _ABSTRACTION_PROMPT.format(domain=source_domain, title=source_title, graph_json=graph_json)
        response, manifest = self._provider.generate(
            prompt, system="You are a mechanism abstraction engine. Output JSON only.",
            temperature=0.15)
        provenance = ProvenanceGraph()
        provenance.add_node(ProvenanceNode(
            node_id=f"pattern:{pattern_id}", node_type="mechanism_pattern",
            content_hash=_sha(response[:500]), metadata={"source_domain": source_domain}))
        result = AbstractionResult(pattern=MechanismPattern(
            pattern_id=pattern_id, source_domain=source_domain,
            source_graph_summary=f"{len(graph.nodes)} nodes, {len(graph.edges)} edges"),
            provenance=provenance, manifests=[manifest])
        if not manifest.success or not response.strip():
            result.failures.append({"type": "PROVIDER_FAILURE", "detail": manifest.error})
            return result
        parsed = _parse_json_tolerant(response)
        if not parsed:
            result.failures.append({"type": "MALFORMED_JSON", "detail": response[:200]})
            return result
        p = result.pattern
        p.abstract_principle = parsed.get("abstract_principle", "")
        p.causal_structure = parsed.get("causal_structure", "")
        p.inputs = _as_str_list(parsed.get("inputs", []))
        p.conditions = _as_str_list(parsed.get("conditions", []))
        p.operations = _as_str_list(parsed.get("operations", []))
        p.intermediate_state = _as_str_list(parsed.get("intermediate_state", []))
        p.outputs = _as_str_list(parsed.get("outputs", []))
        p.constraints = _as_str_list(parsed.get("constraints", []))
        p.failure_conditions = _as_str_list(parsed.get("failure_conditions", []))
        if not p.abstract_principle:
            result.failures.append({"type": "MISSING_PRINCIPLE"})
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


__all__ = ["MechanismAbstractionEngine", "MechanismPattern", "AbstractionResult"]
