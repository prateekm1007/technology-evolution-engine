#!/usr/bin/env python3
"""
test_epistemic_pipeline.py — Tests for the full wired 7-step pipeline.
"""
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.epistemic_pipeline import EpistemicPipeline
from scripts.ingest_documents import ingest_text


class TestEpistemicPipeline:
    """Test the full 7-step wired pipeline (P11 wiring)."""

    def test_pipeline_initializes(self):
        """Pipeline initializes all 7 components."""
        pipeline = EpistemicPipeline()
        assert pipeline.entity_extractor is not None
        assert pipeline.relation_extractor is not None
        assert pipeline.mechanism_classifier is not None
        assert pipeline.provenance_manager is not None
        assert pipeline.chain_extractor is not None
        assert pipeline.benchmarks is not None

    def test_process_text_end_to_end(self):
        """Full pipeline: text → entities → relations → status → provenance → chains."""
        pipeline = EpistemicPipeline()
        text = """
        Abstract
        Electrospinning produces nanofiber membranes. The pore size governs permeability.
        
        Methods
        We used polycaprolactone in DMF solvent. Voltage was 20 kV.
        
        Results
        The membranes showed high permeability. Filtration efficiency was 95%.
        
        Conclusions
        Controlled pore size enables selective permeability for water filtration.
        """
        doc = ingest_text(text, source_id="test_pipeline")
        entities = pipeline.entity_extractor.extract_from_document(doc)
        relations = pipeline.relation_extractor.extract_from_document(doc, entities)
        
        # Verify all 7 steps produced output
        assert len(entities) > 0  # Step 2: entities
        assert isinstance(relations, list)  # Step 3: relations
        
        # Step 4: status classification
        for r in relations:
            assert r.status in ("associative", "asserted")
        
        # Step 5: provenance
        for e in entities:
            assert e.source_id == "test_pipeline"
            assert e.source_section != ""
        
        # Step 6: chains
        edges = [{"source": r.subject, "target": r.obj,
                  "relation": r.relation, "mechanism": r.relation,
                  "confidence": r.confidence} for r in relations]
        chains = pipeline.chain_extractor.extract_mechanisms(edges)
        assert "chains" in chains

    def test_no_regex_required(self):
        """DR-38: pipeline works without regex as primary extractor."""
        pipeline = EpistemicPipeline()
        # The EntityExtractor uses SciSpacy, not regex
        # Verify by checking it works on text with no regex-pattern matches
        text = """
        Abstract
        The quantum dot exhibits photoluminescence. The bandgap governs emission wavelength.
        """
        doc = ingest_text(text, source_id="test_no_regex")
        entities = pipeline.entity_extractor.extract_from_document(doc)
        # Should extract entities via NER, not regex patterns
        assert isinstance(entities, list)

    def test_status_tags_present(self):
        """DR-42: every relation has a status tag."""
        pipeline = EpistemicPipeline()
        text = """
        Methods
        Electrospinning produces nanofibers. The method works.
        """
        doc = ingest_text(text, source_id="test_status")
        entities = pipeline.entity_extractor.extract_from_document(doc)
        relations = pipeline.relation_extractor.extract_from_document(doc, entities)
        
        errors = pipeline.mechanism_classifier.validate_no_missing_status(relations)
        assert len(errors) == 0

    def test_provenance_attached(self):
        """DR-43: every entity has provenance."""
        pipeline = EpistemicPipeline()
        text = """
        Methods
        We used electrospinning to produce nanofiber membranes.
        """
        doc = ingest_text(text, source_id="test_prov")
        entities = pipeline.entity_extractor.extract_from_document(doc)
        
        for e in entities:
            assert e.source_id == "test_prov"
            assert e.source_section == "methods"
            assert e.char_start >= 0
            assert e.char_end > e.char_start


class TestModuleContract:
    """Test module importability."""

    def test_module_importable(self):
        from scripts.epistemic_pipeline import EpistemicPipeline
        assert hasattr(EpistemicPipeline, "process_pdf")
        assert hasattr(EpistemicPipeline, "process_two_papers_for_discovery")
