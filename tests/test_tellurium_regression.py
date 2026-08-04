"""
Tellurium Test regression fixture — Phase I of the Discovery Roadmap.

Per F-049: the old parser extracted ['alloy', 'carbon'] from the Bi₂Te₃
paper. The edge extractor must now extract:
  - 'bismuth telluride' (the actual material, not 'alloy')
  - 'thermoelectric' (the mechanism, not 'carbon')
  - 'hot pressing' and 'spark-plasma sintering' (manufacturing methods)
  - 'power_output' and 'efficiency' (performance metrics)

The test verifies that the edge extractor produces a causal graph with
the correct nodes and edges, all tagged at the ASSERTED tier (mechanism
present in text but not evaluated against a formula — that's Phase III).

NOTE: 'Seebeck' and 'ZT' do NOT appear in the paper's abstract text.
They are implicit in the thermoelectric mechanism. The extractor correctly
identifies the thermoelectric mechanism without requiring terms that
aren't in the text. This is honest extraction — the parser extracts what
IS, not what it assumes should be.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.edge_extractor import EdgeExtractor
from invention_compiler.causal_graph import CausalGraph, EdgeTier, MechanismStatus


@pytest.fixture
def bi2te3_graph():
    """Extract a causal graph from the Bi₂Te₃ paper (arXiv 2507.06101)."""
    extractor = EdgeExtractor()
    content = (ROOT / "data" / "ingestion" / "papers" / "2507.06101.txt").read_text()
    return extractor.extract(content, "2507.06101",
                             "https://arxiv.org/abs/2507.06101", "2026-08-04")


class TestTelluriumTestRegression:
    """The Tellurium Test as a regression fixture.

    Before F-049 closure: parser extracted ['alloy', 'carbon'] — missed everything.
    After Phase I: parser extracts Bi₂Te₃, thermoelectric, hot pressing, etc.
    """

    def test_extracts_bismuth_telluride_not_alloy(self, bi2te3_graph):
        """The extractor must find 'Bi2Te3' (bismuth telluride), not 'alloy'."""
        assert "Bi2Te3" in bi2te3_graph.nodes, (
            "Bi₂Te₃ node missing — the old parser extracted 'alloy' instead. "
            "The edge extractor must identify the actual material."
        )
        node = bi2te3_graph.nodes["Bi2Te3"]
        assert node.node_type == "material"
        assert "bismuth" in node.label.lower() or "Bi2Te3" in node.label

    def test_extracts_thermoelectric_mechanism_not_carbon(self, bi2te3_graph):
        """The extractor must find 'thermoelectric' (the mechanism), not 'carbon'."""
        assert "thermoelectric" in bi2te3_graph.nodes, (
            "Thermoelectric mechanism node missing — the old parser extracted "
            "'carbon' instead. The edge extractor must identify the actual mechanism."
        )
        node = bi2te3_graph.nodes["thermoelectric"]
        assert node.node_type == "mechanism"

    def test_extracts_hot_pressing(self, bi2te3_graph):
        """The extractor must find 'hot pressing' as a manufacturing method."""
        assert "hot_pressing" in bi2te3_graph.nodes, (
            "Hot pressing manufacturing method missing."
        )
        node = bi2te3_graph.nodes["hot_pressing"]
        assert node.node_type == "manufacturing"

    def test_extracts_spark_plasma_sintering(self, bi2te3_graph):
        """The extractor must find 'spark-plasma sintering'."""
        assert "spark_plasma_sintering" in bi2te3_graph.nodes, (
            "Spark-plasma sintering manufacturing method missing."
        )
        node = bi2te3_graph.nodes["spark_plasma_sintering"]
        assert node.node_type == "manufacturing"

    def test_extracts_power_output(self, bi2te3_graph):
        """The extractor must find 'power_output' with the reported value."""
        assert "power_output" in bi2te3_graph.nodes, (
            "Power output property missing."
        )
        node = bi2te3_graph.nodes["power_output"]
        assert node.node_type == "property"

    def test_extracts_efficiency(self, bi2te3_graph):
        """The extractor must find 'efficiency' with the reported value."""
        assert "efficiency" in bi2te3_graph.nodes, (
            "Efficiency property missing."
        )
        node = bi2te3_graph.nodes["efficiency"]
        assert node.node_type == "property"

    def test_extracts_temperature_difference(self, bi2te3_graph):
        """The extractor must find 'temperature_difference' (120 K)."""
        assert "temperature_difference" in bi2te3_graph.nodes, (
            "Temperature difference property missing."
        )

    def test_extracts_application(self, bi2te3_graph):
        """The extractor must find 'te_power_generation' as an application."""
        assert "te_power_generation" in bi2te3_graph.nodes, (
            "Thermoelectric power generation application missing."
        )
        node = bi2te3_graph.nodes["te_power_generation"]
        assert node.node_type == "application"

    def test_all_edges_are_asserted_tier(self, bi2te3_graph):
        """All extracted edges should be ASSERTED (mechanism present, not evaluated).

        This is correct for Phase I — the mechanism is described in the text
        but not yet evaluated against a formula (that's Phase III).
        """
        counts = bi2te3_graph.tier_counts()
        assert counts["associative"] == 0, (
            f"Found {counts['associative']} associative edges — should be 0. "
            f"All edges should have a mechanism (ASSERTED tier)."
        )
        assert counts["asserted"] > 0, "Should have at least some asserted edges"

    def test_bi2te3_has_what_does_this_change(self, bi2te3_graph):
        """DR-13: Bi₂Te₃ node must have what_does_this_change populated."""
        node = bi2te3_graph.nodes["Bi2Te3"]
        assert len(node.what_does_this_change) > 0, (
            "Bi₂Te₃ node has empty what_does_this_change — dead information per DR-13."
        )

    def test_bi2te3_connected_to_thermoelectric(self, bi2te3_graph):
        """Bi₂Te₃ should be connected to the thermoelectric mechanism."""
        connected = [
            e for e in bi2te3_graph.edges
            if e.source == "Bi2Te3" and e.target == "thermoelectric"
        ]
        assert len(connected) > 0, (
            "No edge from Bi₂Te₃ to thermoelectric — the material should "
            "be connected to its mechanism."
        )

    def test_no_keyword_extraction_artifacts(self, bi2te3_graph):
        """The old parser's outputs ('alloy', 'carbon') should NOT appear as nodes."""
        assert "alloy" not in bi2te3_graph.nodes, (
            "'alloy' found as a node — this is the old keyword-extraction artifact."
        )
        assert "carbon" not in bi2te3_graph.nodes, (
            "'carbon' found as a node — this is the old keyword-extraction artifact."
        )


class TestCorpusExtraction:
    """Test extraction across the full 20-document corpus."""

    def test_corpus_extraction_produces_graph(self):
        """Extract from both patent and paper corpora."""
        extractor = EdgeExtractor()

        # Extract from papers
        papers_graph = extractor.extract_from_corpus(
            str(ROOT / "data" / "ingestion" / "papers")
        )
        assert len(papers_graph.nodes) > 0, "Paper corpus extraction produced no nodes"
        assert len(papers_graph.edges) > 0, "Paper corpus extraction produced no edges"

        # Extract from patents
        patents_graph = extractor.extract_from_corpus(
            str(ROOT / "data" / "ingestion" / "patents")
        )
        assert len(patents_graph.nodes) > 0, "Patent corpus extraction produced no nodes"
        assert len(patents_graph.edges) > 0, "Patent corpus extraction produced no edges"

    def test_corpus_has_no_associative_edges(self):
        """All edges in the extracted graph should have a mechanism (ASSERTED+)."""
        extractor = EdgeExtractor()
        graph = extractor.extract_from_corpus(
            str(ROOT / "data" / "ingestion" / "papers")
        )
        counts = graph.tier_counts()
        assert counts["associative"] == 0, (
            f"Found {counts['associative']} associative edges — all should have mechanisms."
        )

    def test_corpus_has_materials(self):
        """The corpus extraction should find real materials (not just keywords)."""
        extractor = EdgeExtractor()
        graph = extractor.extract_from_corpus(
            str(ROOT / "data" / "ingestion" / "papers")
        )
        material_nodes = [
            n for n in graph.nodes.values() if n.node_type == "material"
        ]
        assert len(material_nodes) >= 3, (
            f"Expected at least 3 materials, found {len(material_nodes)}"
        )
