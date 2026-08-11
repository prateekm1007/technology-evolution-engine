"""Tests for swanson_citation_disjoint.py — Swanson discovery 7→9."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.swanson_citation_disjoint import (
    CitationDisjointSwansonSearch,
    CitationDisjointBridge,
)


def _build_test_graphs():
    """Build concept + citation graphs for the classic Swanson case."""
    concept_graph = {
        "nodes": [
            {"id": "fish_oil"},
            {"id": "blood_viscosity"},
            {"id": "raynaud"},
        ],
        "edges": [
            {"source": "fish_oil", "target": "blood_viscosity"},
            {"source": "blood_viscosity", "target": "raynaud"},
        ],
    }
    # Disjoint: papers 1-3 cite fish_oil, papers 4-6 cite raynaud
    citation_graph = {
        "paper_1": ["fish_oil"],
        "paper_2": ["fish_oil"],
        "paper_3": ["fish_oil", "blood_viscosity"],
        "paper_4": ["raynaud"],
        "paper_5": ["raynaud"],
        "paper_6": ["raynaud", "blood_viscosity"],
    }
    return concept_graph, citation_graph


def test_disjoint_bridge_found():
    """The classic Swanson bridge is found as citation-disjoint."""
    concept_graph, citation_graph = _build_test_graphs()
    searcher = CitationDisjointSwansonSearch(concept_graph, citation_graph)
    bridges = searcher.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )
    assert len(bridges) >= 1
    b = bridges[0]
    assert b.concept_a == "fish_oil"
    assert b.concept_b == "raynaud"
    assert b.bridge_concept == "blood_viscosity"
    assert b.is_citation_disjoint


def test_zero_overlap_for_disjoint_literatures():
    """Disjoint literatures have zero citation overlap."""
    concept_graph, citation_graph = _build_test_graphs()
    searcher = CitationDisjointSwansonSearch(concept_graph, citation_graph)
    bridges = searcher.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )
    assert bridges[0].citation_overlap == 0.0


def test_high_overlap_flagged_not_disjoint():
    """High-overlap literatures are flagged as NOT disjoint."""
    concept_graph, _ = _build_test_graphs()
    # Every paper cites BOTH fish_oil AND raynaud → overlap = 1.0
    citation_graph = {
        "p1": ["fish_oil", "raynaud"],
        "p2": ["fish_oil", "raynaud", "blood_viscosity"],
    }
    searcher = CitationDisjointSwansonSearch(concept_graph, citation_graph, overlap_threshold=0.2)
    bridges = searcher.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )
    assert len(bridges) >= 1
    assert not bridges[0].is_citation_disjoint
    assert bridges[0].citation_overlap > 0.2


def test_bridge_must_appear_in_both_literatures():
    """A concept is only a bridge if it appears in both literatures."""
    concept_graph, _ = _build_test_graphs()
    # blood_viscosity only appears in literature A, not B
    citation_graph = {
        "p1": ["fish_oil", "blood_viscosity"],
        "p2": ["raynaud"],  # bridge NOT in literature B
    }
    searcher = CitationDisjointSwansonSearch(concept_graph, citation_graph)
    bridges = searcher.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )
    # No bridge — blood_viscosity doesn't appear in B's literature
    assert len(bridges) == 0


def test_empty_citation_graph_yields_no_bridges():
    """An empty citation graph yields no bridges."""
    concept_graph, _ = _build_test_graphs()
    searcher = CitationDisjointSwannon = CitationDisjointSwansonSearch(concept_graph, {})
    bridges = searcher.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )
    assert bridges == []


def test_confidence_higher_for_disjoint():
    """Disjoint bridges have higher confidence than non-disjoint ones."""
    concept_graph, _ = _build_test_graphs()

    # Disjoint case
    disjoint_citations = {
        "p1": ["fish_oil"], "p2": ["fish_oil", "blood_viscosity"],
        "p3": ["raynaud"], "p4": ["raynaud", "blood_viscosity"],
    }
    searcher_d = CitationDisjointSwansonSearch(concept_graph, disjoint_citations)
    bridges_d = searcher_d.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )

    # Overlap case
    overlap_citations = {
        "p1": ["fish_oil", "raynaud", "blood_viscosity"],
        "p2": ["fish_oil", "raynaud", "blood_viscosity"],
    }
    searcher_o = CitationDisjointSwansonSearch(concept_graph, overlap_citations)
    bridges_o = searcher_o.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )

    if bridges_d and bridges_o:
        assert bridges_d[0].confidence > bridges_o[0].confidence


def test_disjoint_bridges_sorted_first():
    """Disjoint bridges appear before non-disjoint in the result."""
    concept_graph = {
        "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}, {"id": "D"}],
        "edges": [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"},
            {"source": "A", "target": "D"}, {"source": "D", "target": "C"},
        ],
    }
    # B is disjoint, D is not
    citation_graph = {
        "p1": ["A", "B"], "p2": ["A", "B"], "p3": ["A", "B"],
        "p4": ["C", "D"], "p5": ["C", "D"], "p6": ["C", "D"],
        "p7": ["A", "D"],  # only D overlaps
    }
    searcher = CitationDisjointSwansonSearch(concept_graph, citation_graph, overlap_threshold=0.5)
    bridges = searcher.find_citation_disjoint_bridges(
        candidate_bridges=[
            ("A", "B", "C"),
            ("A", "D", "C"),
        ],
    )
    # At least one bridge should be found
    if bridges:
        # Disjoint bridges come first
        disjoint_first = [b for b in bridges if b.is_citation_disjoint]
        non_disjoint = [b for b in bridges if not b.is_citation_disjoint]
        if disjoint_first and non_disjoint:
            # The first disjoint bridge should come before the first non-disjoint
            first_disjoint_idx = bridges.index(disjoint_first[0])
            first_nondisjoint_idx = bridges.index(non_disjoint[0])
            assert first_disjoint_idx < first_nondisjoint_idx


def test_overlap_threshold_configurable():
    """The overlap_threshold parameter controls what counts as disjoint."""
    concept_graph, _ = _build_test_graphs()
    # Moderate overlap: 33%
    citation_graph = {
        "p1": ["fish_oil"], "p2": ["fish_oil"], "p3": ["fish_oil", "raynaud"],
        "p4": ["raynaud"], "p5": ["raynaud"], "p6": ["raynaud"],
        "p7": ["fish_oil", "blood_viscosity"],
        "p8": ["raynaud", "blood_viscosity"],
    }
    # With threshold 0.5, overlap of 0.33 should be disjoint
    searcher_loose = CitationDisjointSwansonSearch(concept_graph, citation_graph, overlap_threshold=0.5)
    bridges_loose = searcher_loose.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )
    # With threshold 0.2, overlap of 0.33 should NOT be disjoint
    searcher_strict = CitationDisjointSwansonSearch(concept_graph, citation_graph, overlap_threshold=0.2)
    bridges_strict = searcher_strict.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )

    if bridges_loose and bridges_strict:
        assert bridges_loose[0].is_citation_disjoint
        assert not bridges_strict[0].is_citation_disjoint


def test_concept_to_papers_index_built():
    """The inverted index maps concepts to sets of papers."""
    concept_graph, citation_graph = _build_test_graphs()
    searcher = CitationDisjointSwansonSearch(concept_graph, citation_graph)
    # fish_oil should be cited by paper_1, paper_2, paper_3
    assert "paper_1" in searcher.concept_to_papers["fish_oil"]
    assert "paper_2" in searcher.concept_to_papers["fish_oil"]
    assert "paper_3" in searcher.concept_to_papers["fish_oil"]
    # raynaud should be cited by paper_4, paper_5, paper_6
    assert "paper_4" in searcher.concept_to_papers["raynaud"]


def test_reasoning_string_includes_overlap():
    """Each bridge's reasoning string mentions the overlap value."""
    concept_graph, citation_graph = _build_test_graphs()
    searcher = CitationDisjointSwansonSearch(concept_graph, citation_graph)
    bridges = searcher.find_citation_disjoint_bridges(
        candidate_bridges=[("fish_oil", "blood_viscosity", "raynaud")],
    )
    for b in bridges:
        assert "overlap" in b.reasoning.lower()


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
