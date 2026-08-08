"""mechanism_extraction.py — Phase 1: document → MechanismGraph."""
from __future__ import annotations
import json, re, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from discovery_infrastructure.discovery_substrate import (
    MechanismGraph, MechanismNode, MechanismEdge, MechanismNodeType,
    MechanismEdgeType, ProvenanceNode, ProvenanceGraph, ProvenanceEdge,
)
from engine.providers import ReasoningProvider, ProviderCallManifest


NODE_TYPE_MAP: Dict[str, MechanismNodeType] = {
    "ENTITY": MechanismNodeType.SYSTEM, "PROPERTY": MechanismNodeType.PROPERTY,
    "STATE": MechanismNodeType.PROPERTY, "CONDITION": MechanismNodeType.CONDITION,
    "ACTION": MechanismNodeType.PROCESS, "PROCESS": MechanismNodeType.PROCESS,
    "MECHANISM": MechanismNodeType.MECHANISM, "EFFECT": MechanismNodeType.EFFECT,
    "CONSTRAINT": MechanismNodeType.CONSTRAINT, "FAILURE_MODE": MechanismNodeType.FAILURE_MODE,
    "MEASUREMENT": MechanismNodeType.MEASUREMENT, "DESIGN_VARIABLE": MechanismNodeType.DESIGN_VARIABLE,
}
EDGE_TYPE_MAP: Dict[str, MechanismEdgeType] = {
    "CAUSES": MechanismEdgeType.CAUSES, "ENABLES": MechanismEdgeType.ENABLES,
    "INHIBITS": MechanismEdgeType.INHIBITS, "MODULATES": MechanismEdgeType.MODULATES,
    "CORRELATES_WITH": MechanismEdgeType.CORRELATES_WITH, "REQUIRES": MechanismEdgeType.REQUIRES,
    "CONSTRAINS": MechanismEdgeType.CONSTRAINS, "PRODUCES": MechanismEdgeType.PRODUCES,
    "FAILS_UNDER": MechanismEdgeType.FAILS_UNDER, "TRANSFERS_TO": MechanismEdgeType.TRANSFERS_TO,
}


@dataclass
class ExtractionFailure:
    failure_type: str
    detail: str
    raw_llm_output: str = ""


@dataclass
class ExtractionResult:
    graph: MechanismGraph
    provenance: ProvenanceGraph
    manifests: List[ProviderCallManifest] = field(default_factory=list)
    failures: List[ExtractionFailure] = field(default_factory=list)
    source_document_id: str = ""
    source_document_title: str = ""

    @property
    def ok(self) -> bool:
        return len(self.graph.nodes) > 0


_EXTRACTION_PROMPT = """You are a scientific mechanism extractor. Read the source document and extract a structured mechanism graph.

Node types: ENTITY, PROPERTY, STATE, CONDITION, ACTION, PROCESS, MECHANISM, EFFECT, CONSTRAINT, FAILURE_MODE, MEASUREMENT, DESIGN_VARIABLE
Edge types: CAUSES, ENABLES, INHIBITS, MODULATES, CORRELATES_WITH, REQUIRES, CONSTRAINS, PRODUCES, FAILS_UNDER, TRANSFERS_TO

RULES:
1. Do NOT simply extract nouns. Extract causal structure.
2. Every node MUST have an evidence_quote: a verbatim quote from the source.
3. Every edge MUST express a causal or regulatory relationship.
4. Preserve causal DIRECTION.
5. Identify CONDITIONS, CONSTRAINTS, FAILURE_MODES.
6. Use MEASUREMENT for quantitative observations.

Output JSON only (no markdown fences):
{{
  "nodes": [{{"node_id": "N1", "node_type": "ENTITY", "label": "...", "description": "...", "evidence_quote": "verbatim quote"}}],
  "edges": [{{"edge_id": "E1", "source_id": "N1", "target_id": "N2", "edge_type": "CAUSES", "evidence_quote": "quote"}}]
}}

SOURCE TITLE: {title}
SOURCE TEXT:
{body}

Extract the mechanism graph now. JSON only."""


class MechanismExtractionEngine:
    def __init__(self, provider: ReasoningProvider):
        self._provider = provider

    def extract(self, document: Dict[str, str]) -> ExtractionResult:
        title = document.get("title", "untitled")
        text = document.get("text", "")
        doc_id = _doc_id(title)
        prompt = _EXTRACTION_PROMPT.format(title=title, body=text[:8000])
        response, manifest = self._provider.generate(
            prompt, system="You are a scientific mechanism extractor. Output JSON only.",
            temperature=0.1)
        result = ExtractionResult(
            graph=MechanismGraph(), provenance=ProvenanceGraph(),
            manifests=[manifest], source_document_id=doc_id,
            source_document_title=title)
        result.provenance.add_node(ProvenanceNode(
            node_id=f"doc:{doc_id}", node_type="source_document",
            content_hash=_sha(title + text), metadata={"title": title}))
        if not manifest.success or not response.strip():
            result.failures.append(ExtractionFailure("PROVIDER_FAILURE",
                f"no usable response: {manifest.error}", response[:500]))
            return result
        parsed = _parse_json_tolerant(response)
        if parsed is None:
            result.failures.append(ExtractionFailure("MALFORMED_JSON",
                "not valid JSON", response[:500]))
            return result
        raw_nodes = parsed.get("nodes", [])
        raw_edges = parsed.get("edges", [])
        valid_node_ids = set()
        for raw in raw_nodes:
            if not isinstance(raw, dict):
                result.failures.append(ExtractionFailure("MALFORMED_NODE", f"not a dict: {raw!r}"))
                continue
            node_id = raw.get("node_id", "")
            node_type_str = raw.get("node_type", "").upper()
            label = raw.get("label", "")
            evidence = raw.get("evidence_quote", "")
            if not node_id or not label:
                result.failures.append(ExtractionFailure("MISSING_FIELD", f"missing id/label: {raw!r}"))
                continue
            if node_type_str not in NODE_TYPE_MAP:
                result.failures.append(ExtractionFailure("INVALID_NODE_TYPE",
                    f"node '{node_id}' type '{node_type_str}' invalid. Valid: {sorted(NODE_TYPE_MAP.keys())}"))
                continue
            if not evidence.strip():
                result.failures.append(ExtractionFailure("MISSING_EVIDENCE",
                    f"node '{node_id}' no evidence_quote"))
                continue
            if not _evidence_in_source(evidence, text):
                result.failures.append(ExtractionFailure("EVIDENCE_NOT_IN_SOURCE",
                    f"node '{node_id}' evidence not in source (hallucination?): {evidence[:100]!r}"))
                continue
            node = MechanismNode(
                node_id=f"{doc_id}:{node_id}",
                node_type=NODE_TYPE_MAP[node_type_str],
                label=label, description=raw.get("description", ""),
                provenance=[f"doc:{doc_id}"])
            result.graph.add_node(node)
            result.provenance.add_node(ProvenanceNode(
                node_id=f"evidence:{doc_id}:{node_id}",
                node_type="evidence_span",
                content_hash=_sha(evidence),
                metadata={"quote": evidence, "node_id": node.node_id}))
            result.provenance.add_edge(ProvenanceEdge(
                f"pe:{doc_id}:{node_id}", f"doc:{doc_id}",
                f"evidence:{doc_id}:{node_id}", "DERIVES_FROM",
                f"evidence for {node_id}", actor="mechanism_extractor"))
            valid_node_ids.add(node.node_id)
        for raw in raw_edges:
            if not isinstance(raw, dict):
                continue
            edge_id = raw.get("edge_id", "")
            source_id = raw.get("source_id", "")
            target_id = raw.get("target_id", "")
            edge_type_str = raw.get("edge_type", "").upper()
            evidence = raw.get("evidence_quote", "")
            if not edge_id:
                continue
            full_source = f"{doc_id}:{source_id}"
            full_target = f"{doc_id}:{target_id}"
            if full_source not in valid_node_ids or full_target not in valid_node_ids:
                result.failures.append(ExtractionFailure("DANGLING_EDGE",
                    f"edge '{edge_id}' references non-existent node(s)"))
                continue
            if edge_type_str not in EDGE_TYPE_MAP:
                result.failures.append(ExtractionFailure("INVALID_EDGE_TYPE",
                    f"edge '{edge_id}' type '{edge_type_str}' invalid. Valid: {sorted(EDGE_TYPE_MAP.keys())}"))
                continue
            edge = MechanismEdge(
                edge_id=f"{doc_id}:{edge_id}",
                source_id=full_source, target_id=full_target,
                edge_type=EDGE_TYPE_MAP[edge_type_str],
                confidence=0.5,
                evidence=[evidence] if evidence else [f"doc:{doc_id}"])
            result.graph.add_edge(edge)
        return result


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _doc_id(title: str) -> str:
    return "doc_" + hashlib.sha256(title.encode("utf-8")).hexdigest()[:12]

def _parse_json_tolerant(text: str) -> Optional[Dict]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
    first = text.find("{"); last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return None
    try:
        return json.loads(text[first:last + 1])
    except json.JSONDecodeError:
        return None

def _evidence_in_source(quote: str, source: str) -> bool:
    if not quote or not source: return False
    q = quote.strip().lower(); s = source.lower()
    if q in s: return True
    fingerprint = q[:40]
    if len(fingerprint) >= 20 and fingerprint in s: return True
    q_tokens = [t for t in re.findall(r"\w+", q) if len(t) > 3]
    if not q_tokens: return False
    matches = sum(1 for t in q_tokens if t in s)
    return matches / len(q_tokens) >= 0.6


__all__ = ["MechanismExtractionEngine", "ExtractionResult", "ExtractionFailure",
           "NODE_TYPE_MAP", "EDGE_TYPE_MAP"]
