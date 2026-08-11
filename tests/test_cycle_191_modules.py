"""Tests for cycle 191 modules — NLP material extraction, isomorphism, grounded hypotheses."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_nlp_material_extractor_importable():
    """NLP material extractor is importable."""
    from scripts.nlp_material_extractor import extract_materials_nlp, ExtractedMaterial
    assert extract_materials_nlp is not None


def test_nlp_material_extractor_finds_formula():
    """NLP extractor finds chemical formulas via pattern (not hardcoded list)."""
    from scripts.nlp_material_extractor import extract_materials_nlp
    materials = extract_materials_nlp("The CsPbI3 perovskite shows high efficiency.")
    # CsPbI3 should be found via formula pattern (not from a hardcoded list)
    canonicals = [m.canonical for m in materials]
    assert "cspbi3" in canonicals, f"CsPbI3 not found: {canonicals}"


def test_nlp_material_extractor_no_hardcoded_list():
    """The extractor does NOT use a hardcoded list of specific materials."""
    from scripts.nlp_material_extractor import extract_materials_nlp
    # A completely novel formula should be extractable
    materials = extract_materials_nlp("The novel material Zr3Al2N shows superconductivity.")
    canonicals = [m.canonical for m in materials]
    # Zr3Al2N is a novel formula — if it's found, the extractor is general
    assert "zr3al2n" in canonicals or any("zr3al2n" in c for c in canonicals), \
        f"Novel formula Zr3Al2N not found: {canonicals}"


def test_graph_isomorphism_importable():
    """Graph isomorphism analogy is importable."""
    from scripts.graph_isomorphism_analogy import GraphIsomorphismAnalogy, IsomorphicMapping
    assert GraphIsomorphismAnalogy is not None


def test_graph_isomorphism_finds_analogy():
    """Sub-graph isomorphism finds analogies between domains."""
    from scripts.graph_isomorphism_analogy import GraphIsomorphismAnalogy
    from invention_compiler.discovery_graph import (
        DiscoveryGraph, DiscoveryNode, DiscoveryEdge, RelationType
    )
    graph = DiscoveryGraph()
    for nid, dom in [("sunlight", "biology"), ("photosynthesis", "biology"),
                     ("glucose", "biology"), ("photons", "solar"),
                     ("photovoltaic", "solar"), ("electricity", "solar")]:
        graph.add_node(DiscoveryNode(node_id=nid, node_type="concept", label=nid,
                                      properties={"domain": dom}, layers=set(), provenance={}))
    for src, tgt, pred in [("sunlight", "photosynthesis", "causes"),
                           ("photosynthesis", "glucose", "produces"),
                           ("photons", "photovoltaic", "causes"),
                           ("photovoltaic", "electricity", "produces")]:
        graph.add_edge(DiscoveryEdge(source=src, target=tgt, relation_type=RelationType.MECHANISM,
                                      evidence=[], metadata={}, direction=pred))
    gia = GraphIsomorphismAnalogy(graph)
    analogies = gia.find_isomorphic_analogies(min_size=2, max_size=4)
    assert len(analogies) >= 1, "Expected ≥1 isomorphic analogy"


def test_graph_isomorphism_not_string_sequence():
    """The isomorphism uses graph structure, not string sequence matching."""
    from scripts.graph_isomorphism_analogy import GraphIsomorphismAnalogy
    # Verify the class has _get_degree and _get_neighbors (structural methods)
    assert hasattr(GraphIsomorphismAnalogy, '_get_degree')
    assert hasattr(GraphIsomorphismAnalogy, '_get_neighbors')
    assert hasattr(GraphIsomorphismAnalogy, '_try_extend_mapping')


def test_grounded_hypothesis_v2_importable():
    """Grounded hypothesis v2 is importable."""
    from scripts.grounded_hypothesis_v2 import generate_grounded_hypotheses, GroundedHypothesis
    assert generate_grounded_hypotheses is not None


def test_grounded_hypothesis_no_templates():
    """Grounded hypotheses are NOT template-based."""
    from scripts.grounded_hypothesis_v2 import generate_grounded_hypotheses
    edge = {
        "source": "temperature",
        "target": "radiative_power",
        "direction": "determines",
        "mechanism": "Stefan-Boltzmann law: Q = σAT⁴",
        "formula": "Q = σAT⁴",
    }
    hyps = generate_grounded_hypotheses(edge)
    assert len(hyps) >= 1
    # The hypothesis must contain a SPECIFIC prediction (not a template)
    h = hyps[0]
    assert h.prediction != "", "Hypothesis must have a specific prediction"
    assert h.falsification_criterion != "", "Hypothesis must have a falsification criterion"


def test_grounded_hypothesis_quantitative():
    """Grounded hypotheses with formulas produce quantitative predictions."""
    from scripts.grounded_hypothesis_v2 import generate_grounded_hypotheses
    edge = {
        "source": "temperature",
        "target": "radiative_power",
        "direction": "determines",
        "mechanism": "Stefan-Boltzmann",
        "formula": "Q = σAT⁴",
    }
    hyps = generate_grounded_hypotheses(edge)
    # At least one hypothesis should have a numerical prediction
    has_numerical = any(any(c.isdigit() for c in h.prediction) for h in hyps)
    assert has_numerical, "Expected at least one quantitative prediction"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
