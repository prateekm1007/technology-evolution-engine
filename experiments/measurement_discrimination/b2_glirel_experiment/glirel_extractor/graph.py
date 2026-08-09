#!/usr/bin/env python3
"""graph.py — Evidence graph construction.

Merges Source A and Source B evidence edges into a cross-source
evidence graph. Every edge preserves provenance.
"""
import json
from dataclasses import dataclass, field
from typing import List
from extractor import EvidenceEdge


@dataclass
class EvidenceGraph:
    """A cross-source evidence graph for a single candidate."""
    source_a_text: str
    source_b_text: str
    candidate: str
    case_id: str
    edges: List[EvidenceEdge] = field(default_factory=list)
    cross_source_edges: List[EvidenceEdge] = field(default_factory=list)
    source_local_edges_a: List[EvidenceEdge] = field(default_factory=list)
    source_local_edges_b: List[EvidenceEdge] = field(default_factory=list)

    def add_edge(self, edge: EvidenceEdge):
        """Add an edge and classify it."""
        self.edges.append(edge)
        if edge.source_id == "A":
            self.source_local_edges_a.append(edge)
        elif edge.source_id == "B":
            self.source_local_edges_b.append(edge)

    def to_dict(self) -> dict:
        return {
            "source_a_text": self.source_a_text,
            "source_b_text": self.source_b_text,
            "candidate": self.candidate,
            "case_id": self.case_id,
            "edges": [e.to_dict() for e in self.edges],
            "cross_source_edges": [e.to_dict() for e in self.cross_source_edges],
            "source_local_edges_a": [e.to_dict() for e in self.source_local_edges_a],
            "source_local_edges_b": [e.to_dict() for e in self.source_local_edges_b],
            "summary": {
                "total_edges": len(self.edges),
                "source_a_edges": len(self.source_local_edges_a),
                "source_b_edges": len(self.source_local_edges_b),
                "cross_source_edges": len(self.cross_source_edges),
            },
        }

    def get_relations_by_source(self, source_id: str) -> List[EvidenceEdge]:
        """Get all edges from a specific source."""
        return [e for e in self.edges if e.source_id == source_id]

    def get_relations_by_label(self, label: str) -> List[EvidenceEdge]:
        """Get all edges with a specific relation label."""
        return [e for e in self.edges if e.relation == label]

    def has_cross_source_evidence(self) -> bool:
        """Check if there are edges from both sources (necessary for ISS_both)."""
        return len(self.source_local_edges_a) > 0 and len(self.source_local_edges_b) > 0


def build_graph(
    case_id: str,
    candidate: str,
    source_a_text: str,
    source_b_text: str,
    edges_a: List[EvidenceEdge],
    edges_b: List[EvidenceEdge],
) -> EvidenceGraph:
    """Build a cross-source evidence graph from per-source edges."""
    graph = EvidenceGraph(
        source_a_text=source_a_text,
        source_b_text=source_b_text,
        candidate=candidate,
        case_id=case_id,
    )
    for edge in edges_a:
        graph.add_edge(edge)
    for edge in edges_b:
        graph.add_edge(edge)
    return graph
