#!/usr/bin/env python3
"""
Test: NLP Pipeline and Mechanism Extraction (Gen 2-4).

Per P2: "Untested code is unverified code, permanently."
Per P27: "Read the assertion, not the test name."
Per P28: "Test with 3+ inputs: exact, variation, edge case."
"""
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nlp_pipeline import NLPPipeline, ExtractedEntity, ExtractedRelation
from scripts.mechanism_extraction import MechanismExtractor, CausalChain, CausalStep


class TestNLPPipeline:
    """Test the Gen 2-3 NLP pipeline."""

    def test_entity_extraction_returns_list(self):
        """Entities are extracted as a list of ExtractedEntity objects."""
        pipeline = NLPPipeline()
        entities = pipeline.extract_entities("Graphene oxide membranes exhibit selective permeability.")
        assert isinstance(entities, list)
        assert len(entities) > 0

    def test_entity_extraction_has_canonical_types(self):
        """Entities have canonical types (material, mechanism, property, application)."""
        pipeline = NLPPipeline()
        entities = pipeline.extract_entities("Electrospinning produces nanofiber membrane with controlled pore size.")
        valid_types = {"material", "mechanism", "property", "application", "entity", "concept"}
        for ent in entities:
            assert ent.label in valid_types, f"Invalid type: {ent.label}"

    def test_entity_extraction_excludes_stopwords(self):
        """Per cycle 101: stopwords are not extracted as entities."""
        pipeline = NLPPipeline()
        entities = pipeline.extract_entities("The material is used for the application.")
        entity_texts = [e.text.lower() for e in entities]
        assert "the" not in entity_texts
        assert "for" not in entity_texts

    def test_relation_extraction_returns_list(self):
        """Relations are extracted using dependency parsing."""
        pipeline = NLPPipeline()
        text = "Electrospinning produces nanofiber membranes. The pore size governs selective permeability."
        entities = pipeline.extract_entities(text)
        relations = pipeline.extract_relations(text, entities)
        assert isinstance(relations, list)

    def test_relation_extraction_has_confidence(self):
        """Each relation has a confidence score."""
        pipeline = NLPPipeline()
        text = "Electrospinning produces nanofiber membranes."
        entities = pipeline.extract_entities(text)
        relations = pipeline.extract_relations(text, entities)
        for rel in relations:
            assert 0.0 <= rel.confidence <= 1.0

    def test_process_to_graph_returns_dict(self):
        """process_to_graph returns a graph-compatible structure."""
        pipeline = NLPPipeline()
        result = pipeline.process_to_graph("Electrospinning produces nanofiber membrane.")
        assert "nodes" in result
        assert "edges" in result
        assert "entity_count" in result
        assert "relation_count" in result


class TestMechanismExtraction:
    """Test the Gen 4 mechanism extraction — THE HARDEST JUMP."""

    def test_extract_chains_returns_list(self):
        """Causal chains are extracted from relations."""
        extractor = MechanismExtractor()
        relations = [
            {"source": "A", "relation": "produces", "target": "B", "confidence": 0.9},
            {"source": "B", "relation": "enables", "target": "C", "confidence": 0.8},
        ]
        chains = extractor.extract_chains(relations, apply_quality_filter=False)
        assert isinstance(chains, list)
        assert len(chains) > 0

    def test_chain_has_multiple_steps(self):
        """A causal chain connects multiple steps (not just a single edge)."""
        extractor = MechanismExtractor()
        relations = [
            {"source": "A", "relation": "produces", "target": "B", "confidence": 0.9},
            {"source": "B", "relation": "enables", "target": "C", "confidence": 0.8},
            {"source": "C", "relation": "governs", "target": "D", "confidence": 0.85},
        ]
        chains = extractor.extract_chains(relations, apply_quality_filter=False)
        # At least one chain should have multiple steps
        max_steps = max(len(c.steps) for c in chains)
        assert max_steps >= 2, "No multi-step chain found"

    def test_contradiction_detection(self):
        """Contradictions are detected when same source has opposing effects."""
        extractor = MechanismExtractor()
        relations = [
            {"source": "X", "relation": "increases", "target": "Y", "confidence": 0.8},
            {"source": "X", "relation": "reduces", "target": "Y", "confidence": 0.7},
        ]
        contradictions = extractor.detect_contradictions(relations)
        assert len(contradictions) > 0, "Contradiction not detected"

    def test_counterfactual_reasoning(self):
        """Counterfactual: if entity did not exist, what effects would be lost?"""
        extractor = MechanismExtractor()
        relations = [
            {"source": "A", "relation": "produces", "target": "B", "confidence": 0.9},
            {"source": "B", "relation": "enables", "target": "C", "confidence": 0.8},
        ]
        cf = extractor.counterfactual("A", relations)
        assert cf["entity"] == "A"
        assert "B" in cf["effects_lost"]
        assert "interpretation" in cf

    def test_extract_mechanisms_full_pipeline(self):
        """Full mechanism extraction returns chains, contradictions, counterfactuals."""
        extractor = MechanismExtractor()
        relations = [
            {"source": "electrospinning", "relation": "produces", "target": "nanofiber", "confidence": 0.9},
            {"source": "nanofiber", "relation": "enables", "target": "filtration", "confidence": 0.8},
        ]
        result = extractor.extract_mechanisms(relations)
        assert "chains" in result
        assert "contradictions" in result
        assert "counterfactuals" in result
        assert "stats" in result

    def test_non_causal_relations_excluded(self):
        """Non-causal relations (e.g., 'has', 'is') are excluded from chains."""
        extractor = MechanismExtractor()
        relations = [
            {"source": "A", "relation": "has", "target": "B", "confidence": 0.9},
            {"source": "A", "relation": "produces", "target": "C", "confidence": 0.8},
        ]
        chains = extractor.extract_chains(relations)
        # "has" should not appear in any chain
        for chain in chains:
            for step in chain.steps:
                assert step.relation != "has", "'has' relation should be excluded from chains"


class TestModuleContract:
    """Test module importability and interface."""

    def test_nlp_pipeline_importable(self):
        from scripts.nlp_pipeline import NLPPipeline
        assert hasattr(NLPPipeline, "extract_entities")
        assert hasattr(NLPPipeline, "extract_relations")
        assert hasattr(NLPPipeline, "process_to_graph")

    def test_mechanism_extractor_importable(self):
        from scripts.mechanism_extraction import MechanismExtractor
        assert hasattr(MechanismExtractor, "extract_chains")
        assert hasattr(MechanismExtractor, "detect_contradictions")
        assert hasattr(MechanismExtractor, "counterfactual")
        assert hasattr(MechanismExtractor, "extract_mechanisms")
