#!/usr/bin/env python3
"""
swanson_real_citation_disjoint.py — Run citation-disjoint Swanson search
on the REAL 5-paper corpus (F-089 fix).

Per cycle 184 (auditor update #3): swanson_citation_disjoint.py was
tested only on a 3-node toy graph (fish_oil → blood_viscosity → raynaud).
The "627 disjoint bridges" claim in the scorecard was from a prior
aggregate, not reproducible from the cited module. F-089 is P1.

This module:
1. Loads the real 5-paper corpus.
2. Extracts entities from each paper (using NLP pipeline).
3. Builds a citation graph: paper_id → list of entities (concepts) it cites.
4. Builds a concept graph: entities connected if they co-occur in a paper.
5. Runs CitationDisjointSwansonSearch on the real graphs.
6. Reports the ACTUAL bridge count (not a prior aggregate).

Usage:
    python3 -m scripts.swanson_real_citation_disjoint
"""
import sys
import json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.nlp_pipeline import NLPPipeline
from scripts.swanson_citation_disjoint import (
    CitationDisjointSwansonSearch, CitationDisjointBridge,
)

REPO = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO / "data" / "ingestion" / "corpus_50x"


@dataclass
class RealCorpusSwansonResult:
    """Result of running citation-disjoint Swanson search on real corpus."""
    n_papers: int
    n_unique_concepts: int
    n_concept_edges: int
    n_candidate_bridges: int
    n_citation_disjoint_bridges: int
    top_bridges: List[Dict] = field(default_factory=list)
    reasoning: str = ""


def build_real_citation_and_concept_graphs(
    max_papers: int = 5,
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    """Build citation and concept graphs from the real corpus.

    Args:
        max_papers: max number of papers to process

    Returns:
        (citation_graph, concept_graph)
        citation_graph: paper_id → list of concept_ids (entities extracted from that paper)
        concept_graph: {nodes: [...], edges: [...]} where edges connect co-occurring concepts
    """
    pipeline = NLPPipeline()
    papers = sorted(CORPUS_DIR.glob("*.txt"))[:max_papers]

    citation_graph: Dict[str, List[str]] = {}
    concept_co_occurrence: Dict[Tuple[str, str], int] = defaultdict(int)
    all_concepts: Set[str] = set()

    for paper in papers:
        text = paper.read_text()[:3000]
        ents = pipeline.extract_entities(text)
        paper_id = paper.stem

        # Each paper "cites" the concepts it mentions
        paper_concepts = []
        for ent in ents:
            cid = ent.text.lower().replace(" ", "_").replace("/", "_")
            if len(cid) >= 3:
                paper_concepts.append(cid)
                all_concepts.add(cid)

        citation_graph[paper_id] = paper_concepts

        # Co-occurrence: every pair of concepts in the same paper
        for i, c1 in enumerate(paper_concepts):
            for c2 in paper_concepts[i + 1:]:
                key = tuple(sorted([c1, c2]))
                concept_co_occurrence[key] += 1

    # Build concept graph (edges where co-occurrence >= 1)
    nodes = [{"id": c} for c in all_concepts]
    edges = [
        {"source": k[0], "target": k[1], "weight": v}
        for k, v in concept_co_occurrence.items()
    ]

    concept_graph = {"nodes": nodes, "edges": edges}
    return citation_graph, concept_graph


def run_real_citation_disjoint_search(
    max_papers: int = 5,
    overlap_threshold: float = 0.5,
) -> RealCorpusSwansonResult:
    """Run the citation-disjoint Swanson search on the real corpus.

    Args:
        max_papers: number of papers to process
        overlap_threshold: citation overlap threshold for "disjoint"

    Returns:
        RealCorpusSwansonResult with measured counts
    """
    citation_graph, concept_graph = build_real_citation_and_concept_graphs(max_papers)

    n_papers = len(citation_graph)
    n_concepts = len(concept_graph["nodes"])
    n_edges = len(concept_graph["edges"])

    # Run the search
    searcher = CitationDisjointSwansonSearch(
        concept_graph, citation_graph, overlap_threshold=overlap_threshold,
    )

    # Generate candidates from the concept graph
    candidates = searcher._generate_candidates()
    n_candidates = len(candidates)

    # Find citation-disjoint bridges
    bridges = searcher.find_citation_disjoint_bridges(
        candidate_bridges=candidates,
        max_bridges=100,
    )
    n_disjoint = len(bridges)

    # Top bridges (convert to serializable)
    top = []
    for b in bridges[:5]:
        top.append({
            "concept_a": b.concept_a,
            "concept_b": b.concept_b,
            "bridge": b.bridge_concept,
            "overlap": b.citation_overlap,
            "is_disjoint": b.is_citation_disjoint,
            "confidence": b.confidence,
        })

    reasoning = (
        f"REAL CORPUS citation-disjoint search: {n_papers} papers, "
        f"{n_concepts} unique concepts, {n_edges} concept co-occurrence edges. "
        f"Generated {n_candidates} candidate bridges; "
        f"{n_disjoint} verified as citation-disjoint "
        f"(threshold={overlap_threshold}). "
        f"This is the MEASURED count, not a prior aggregate."
    )

    return RealCorpusSwansonResult(
        n_papers=n_papers,
        n_unique_concepts=n_concepts,
        n_concept_edges=n_edges,
        n_candidate_bridges=n_candidates,
        n_citation_disjoint_bridges=n_disjoint,
        top_bridges=top,
        reasoning=reasoning,
    )


def main():
    """Demo: real corpus citation-disjoint search."""
    print("=" * 60)
    print("REAL CORPUS Citation-Disjoint Swanson Search (F-089 fix)")
    print("=" * 60)
    print()

    result = run_real_citation_disjoint_search(max_papers=5, overlap_threshold=0.5)

    print(f"Papers processed:        {result.n_papers}")
    print(f"Unique concepts:         {result.n_unique_concepts}")
    print(f"Concept co-occurrences:  {result.n_concept_edges}")
    print(f"Candidate bridges:       {result.n_candidate_bridges}")
    print(f"Citation-disjoint bridges: {result.n_citation_disjoint_bridges}")
    print()

    if result.top_bridges:
        print("Top bridges:")
        for b in result.top_bridges:
            print(f"  {b['concept_a']} ↔ {b['bridge']} ↔ {b['concept_b']}")
            print(f"    overlap={b['overlap']:.3f}, disjoint={b['is_disjoint']}, conf={b['confidence']:.3f}")
    else:
        print("(no citation-disjoint bridges found in the real corpus)")
    print()

    print(f"Reasoning: {result.reasoning}")
    print()
    print("This is the F-089 fix:")
    print("  - Citation-disjoint search on the REAL 5-paper corpus (not toy graph)")
    print("  - ACTUAL bridge count reported (not a prior aggregate)")
    print("  - Honest: if 0 bridges found, that's the answer")


if __name__ == "__main__":
    main()
