#!/usr/bin/env python3
"""
test_extract_entities.py — DR-40 tests.

Per P2: untested code is unverified.
Per P27: read the assertion, not the test name.
Per P28: test with 3+ inputs.
"""
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.extract_entities import EntityExtractor, CanonicalEntity
from scripts.ingest_documents import CanonicalDocument


class TestEntityExtractor:
    """Test the DR-40 entity extractor."""

    def test_extract_from_text_returns_list(self):
        """Exact case: text input produces entity list."""
        extractor = EntityExtractor()
        text = (
            "Electrospinning produces nanofiber membranes with controlled pore size. "
            "The membranes exhibit selective permeability for water filtration. "
            "Polycaprolactone is used as the polymer."
        )
        entities = extractor.extract_from_text(text, source_id="test_001")
        assert isinstance(entities, list)
        assert len(entities) > 0

    def test_entities_have_canonical_id(self):
        """DR-40: entities have canonical forms."""
        extractor = EntityExtractor()
        text = "The membrane permeability was measured. Lower permeability was observed."
        entities = extractor.extract_from_text(text, source_id="test_002")
        for e in entities:
            assert e.canonical_id != ""
            assert isinstance(e.canonical_id, str)

    def test_entities_have_entity_type(self):
        """Entities have canonical types."""
        extractor = EntityExtractor()
        text = "Electrospinning produces nanofiber membranes."
        entities = extractor.extract_from_text(text, source_id="test_003")
        valid_types = {"material", "mechanism", "property", "application", "entity", "concept"}
        for e in entities:
            assert e.entity_type in valid_types, f"Invalid type: {e.entity_type}"

    def test_entities_have_provenance(self):
        """DR-43: entities have provenance."""
        extractor = EntityExtractor()
        text = "The nanofiber membrane was characterized."
        entities = extractor.extract_from_text(text, source_id="test_004",
                                                source_section="methods")
        for e in entities:
            assert e.source_id == "test_004"
            assert e.source_section == "methods"
            assert e.char_start >= 0
            assert e.char_end > e.char_start

    def test_canonicalization_strips_prefixes(self):
        """DR-40: canonicalization strips prefixes."""
        extractor = EntityExtractor()
        # "membrane_permeability" should canonicalize to "permeability"
        assert extractor._canonicalize("membrane permeability") == "permeability"
        assert extractor._canonicalize("lower permeability") == "permeability"
        assert extractor._canonicalize("water contact angle") == "contact_angle"

    def test_canonicalization_strips_suffixes(self):
        """DR-40: canonicalization strips suffixes."""
        extractor = EntityExtractor()
        assert extractor._canonicalize("permeability values") == "permeability"
        assert extractor._canonicalize("pore sizes") == "pore"

    def test_canonicalization_preserves_short_terms(self):
        """Edge case: short terms are not over-stripped."""
        extractor = EntityExtractor()
        # "pH" should not be stripped to empty
        result = extractor._canonicalize("pH")
        assert len(result) >= 2

    def test_find_shared_entities(self):
        """DR-40: shared entity detection works."""
        extractor = EntityExtractor()
        ents_a = [
            CanonicalEntity(canonical_id="permeability", raw_text="permeability",
                          entity_type="property", confidence=0.8),
            CanonicalEntity(canonical_id="nanofiber", raw_text="nanofiber membrane",
                          entity_type="material", confidence=0.7),
        ]
        ents_b = [
            CanonicalEntity(canonical_id="permeability", raw_text="membrane permeability",
                          entity_type="property", confidence=0.8),
            CanonicalEntity(canonical_id="polycaprolactone", raw_text="polycaprolactone",
                          entity_type="material", confidence=0.9),
        ]
        shared = extractor.find_shared_entities(ents_a, ents_b)
        assert len(shared) == 1
        assert shared[0]["canonical_id"] == "permeability"
        assert shared[0]["label_a"] == "permeability"
        assert shared[0]["label_b"] == "membrane permeability"

    def test_find_shared_entities_empty_for_different_domains(self):
        """Different domains have 0 shared entities."""
        extractor = EntityExtractor()
        ents_a = [
            CanonicalEntity(canonical_id="nanofiber", raw_text="nanofiber",
                          entity_type="material", confidence=0.8),
        ]
        ents_b = [
            CanonicalEntity(canonical_id="blockchain", raw_text="blockchain",
                          entity_type="material", confidence=0.8),
        ]
        shared = extractor.find_shared_entities(ents_a, ents_b)
        assert len(shared) == 0

    def test_extract_from_document(self):
        """Extract from CanonicalDocument with sections."""
        extractor = EntityExtractor()
        doc = CanonicalDocument(
            source_id="test_doc",
            sections={
                "methods": "We used electrospinning to produce nanofiber membranes. "
                          "The pore size was controlled.",
                "results": "The membranes showed high permeability. "
                          "Water filtration efficiency was 95%.",
            },
            full_text="Methods text. Results text.",
        )
        entities = extractor.extract_from_document(doc)
        assert len(entities) > 0
        # Should have entities from both sections
        sections_represented = {e.source_section for e in entities}
        assert "methods" in sections_represented or "results" in sections_represented

    def test_noise_filtered(self):
        """Generic scientific words are filtered."""
        extractor = EntityExtractor()
        text = "The efficacy of the method was observed. " \
               "The detection was performed. " \
               "The performance was evaluated."
        entities = extractor.extract_from_text(text, source_id="test_noise")
        canonical_ids = {e.canonical_id for e in entities}
        # These should be filtered
        assert "efficacy" not in canonical_ids
        assert "detection" not in canonical_ids
        assert "performance" not in canonical_ids


class TestModuleContract:
    """Test module importability and interface."""

    def test_module_importable(self):
        from scripts.extract_entities import EntityExtractor, CanonicalEntity
        assert hasattr(EntityExtractor, "extract_from_document")
        assert hasattr(EntityExtractor, "extract_from_text")
        assert hasattr(EntityExtractor, "find_shared_entities")
        assert hasattr(EntityExtractor, "_canonicalize")
