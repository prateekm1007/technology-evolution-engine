"""hypothesis_generation.py — Phase 4: TransferHypothesis → competing Hypotheses.

H-GEN-1 intervention: the original mechanism graph is preserved alongside
the abstraction and passed to the hypothesis generator. Every proposed
mechanism must cite specific causal edges from the mechanism graph.
This prevents the abstraction from erasing mechanism-specific causal
information (the confirmed bottleneck identified by DXP-001 through DXP-004).
"""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    Hypothesis, TransferHypothesis, ProvenanceGraph, ProvenanceNode, EpistemicState,
    MechanismGraph)
from engine.providers import ReasoningProvider, ProviderCallManifest


@dataclass
class HypothesisSet:
    transfer_id: str
    hypotheses: List[Hypothesis] = field(default_factory=list)
    distinguishing_predictions: str = ""
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[Dict] = field(default_factory=list)


# Original prompt (used when no mechanism graph is provided — backward compat)
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
      "expected_failure_modes": ["..."],
      "source_causal_edges": ["cite specific edges from the mechanism graph that this hypothesis is derived from"],
      "predicted_magnitude": "a specific quantitative prediction with a number (e.g. '5-10% reduction', '15 mm increase')"
    }}
  ],
  "distinguishing_predictions": "..."
}}

TRANSFER HYPOTHESIS:
{transfer_json}

Output JSON only. Every hypothesis MUST have a non-empty falsifier."""


# H-GEN-1 intervention prompt: mechanism graph preserved alongside abstraction
_HYPOTHESIS_PROMPT_WITH_MECHANISM = """You are a scientific hypothesis generation engine.

You are given:
1. A MECHANISM GRAPH from the source domain — containing specific causal edges that describe HOW the source mechanism works.
2. A TRANSFER HYPOTHESIS that maps the abstract principle to the target domain.

Your task: generate 2-4 COMPETING hypotheses about how the SPECIFIC CAUSAL MECHANISM from the source domain operates in the target domain.

CRITICAL REQUIREMENTS:
- Each hypothesis must identify a SPECIFIC physical mechanism, not a generic category.
- Each hypothesis must cite which specific causal edges from the mechanism graph it is derived from (use the edge descriptions).
- Do NOT propose mechanisms that are not traceable to the source mechanism graph.
- Do NOT substitute generic terms (like "directional features reduce resistance") for specific mechanisms (like "riblets lift streamwise vortices away from the surface, reducing shear stress transfer").
- Each hypothesis MUST include a quantitative prediction with a specific number (e.g. "5-10% drag reduction", "0.3 mm wavelength").
- Each hypothesis MUST include a falsifier: an observation that would prove it WRONG.

The hypotheses must be MATERIALLY DIFFERENT — not restatements of the same idea.

Also describe: what observations would DISTINGUISH the hypotheses from each other?

Output (JSON only):
{{
  "hypotheses": [
    {{
      "claim": "specific falsifiable statement",
      "mechanism": "specific causal mechanism — must reference the physical principle from the source mechanism graph, not a generic abstraction",
      "source_causal_edges": ["cite the specific edges from the mechanism graph that this mechanism is derived from"],
      "predicted_magnitude": "specific quantitative prediction with a number",
      "assumptions": ["..."],
      "evidence": ["..."],
      "novelty_rationale": "...",
      "testability": "...",
      "falsifier": "what observation would prove it WRONG — REQUIRED, non-empty",
      "expected_failure_modes": ["..."]
    }}
  ],
  "distinguishing_predictions": "..."
}}

SOURCE MECHANISM GRAPH (specific causal edges):
{mechanism_graph_json}

TRANSFER HYPOTHESIS (abstract mapping):
{transfer_json}

Output JSON only. Every hypothesis MUST have a non-empty falsifier and a specific quantitative prediction."""


class HypothesisGenerationEngine:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def generate(self, transfer: TransferHypothesis, *,
                 id_prefix: str = "H",
                 mechanism_graph: Optional[MechanismGraph] = None) -> HypothesisSet:
        """Generate competing hypotheses from a transfer.

        H-GEN-1 intervention: if mechanism_graph is provided, the original
        mechanism graph (with its specific causal edges) is passed to the
        hypothesis generator ALONGSIDE the abstraction. This prevents the
        abstraction from erasing mechanism-specific causal information.

        If mechanism_graph is None, falls back to the original behavior
        (backward compatibility with DXP-001 through DXP-004).
        """
        result = HypothesisSet(transfer_id=transfer.transfer_id)
        transfer_json = json.dumps(transfer.to_dict(), indent=2)[:4000]

        if mechanism_graph is not None:
            # H-GEN-1: mechanism-preserving prompt
            mechanism_graph_json = self._format_mechanism_graph(mechanism_graph)
            prompt = _HYPOTHESIS_PROMPT_WITH_MECHANISM.format(
                transfer_json=transfer_json,
                mechanism_graph_json=mechanism_graph_json)
        else:
            # Original prompt (backward compat)
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

    def _format_mechanism_graph(self, graph: MechanismGraph) -> str:
        """Format the mechanism graph as a list of specific causal edges.

        This is the key H-GEN-1 intervention: the specific causal edges
        (not the abstracted pattern) are passed to the hypothesis generator.
        """
        edges = []
        for e in graph.edges:
            source_node = graph.nodes.get(e.source_id)
            target_node = graph.nodes.get(e.target_id)
            source_label = source_node.label if source_node else e.source_id
            target_label = target_node.label if target_node else e.target_id
            evidence = e.evidence[0] if e.evidence else ""
            edges.append({
                "edge_id": e.edge_id,
                "source": source_label,
                "target": target_label,
                "causal_type": e.edge_type.value,
                "evidence": evidence,
            })
        return json.dumps(edges, indent=2)[:6000]


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
