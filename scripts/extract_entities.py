#!/usr/bin/env python3
"""
extract_entities.py — DR-40: Zero-shot entity extraction and canonicalization.

Per docs/EXTRACTION_ARCHITECTURE.md step 3:
  Replace fixed entity patterns with zero-shot or schema-based entity
  extraction and canonicalization.

This module wraps the existing NLP pipeline (scripts/nlp_pipeline.py) with:
  1. A clean interface: ingest CanonicalDocument → extract entities
  2. Entity canonicalization (linking) applied post-extraction
  3. Noise filtering (stopwords, POS tags, generic scientific words)
  4. Provenance: every entity traces to source section + char offset
  5. Schema-based entity types: material, mechanism, property, application

Exit criterion: The system can extract and normalize domain entities
without manual target vocabularies.
"""
import sys
import re
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.nlp_pipeline import NLPPipeline, ExtractedEntity, ENTITY_STOPWORDS
from scripts.ingest_documents import CanonicalDocument


@dataclass
class CanonicalEntity:
    """An entity with canonical form, type, and provenance (DR-40 + DR-43)."""
    canonical_id: str        # linked canonical form (e.g., "permeability")
    raw_text: str            # original text as extracted
    entity_type: str         # material, mechanism, property, application
    confidence: float
    # Provenance (DR-43)
    source_id: str = ""      # document source_id
    source_section: str = "" # which section it came from
    char_start: int = 0
    char_end: int = 0
    aliases: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "canonical_id": self.canonical_id,
            "raw_text": self.raw_text,
            "entity_type": self.entity_type,
            "confidence": self.confidence,
            "source_id": self.source_id,
            "source_section": self.source_section,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "aliases": self.aliases,
        }


class EntityExtractor:
    """DR-40: Zero-shot entity extraction and canonicalization.
    
    Uses SciSpacy NER as the primary extractor (not regex).
    Applies:
      1. POS-tag filtering (nouns only)
      2. Stopword filtering (300+ generic scientific words)
      3. Entity linking (canonical forms via prefix/suffix stripping)
      4. Provenance attachment (source_id, section, offsets)
    """
    
    def __init__(self):
        self.pipeline = NLPPipeline()
    
    def extract_from_document(self, doc: CanonicalDocument) -> List[CanonicalEntity]:
        """Extract entities from a CanonicalDocument.
        
        Processes each section separately, attaches provenance.
        Returns a list of CanonicalEntity objects.
        """
        entities = []
        seen_canonical = set()
        
        for section_name, section_text in doc.sections.items():
            if not section_text or len(section_text) < 50:
                continue
            
            # Extract entities using the NLP pipeline
            raw_entities = self.pipeline.extract_entities(section_text)
            
            for ent in raw_entities:
                # Apply entity linking (canonicalization)
                canonical = self._canonicalize(ent.text)
                
                # Skip if already seen (deduplicate by canonical form)
                if canonical in seen_canonical:
                    # Add as alias to existing entity
                    for existing in entities:
                        if existing.canonical_id == canonical:
                            if ent.text not in existing.aliases:
                                existing.aliases.append(ent.text)
                            break
                    continue
                
                seen_canonical.add(canonical)
                
                entities.append(CanonicalEntity(
                    canonical_id=canonical,
                    raw_text=ent.text,
                    entity_type=ent.label,
                    confidence=ent.confidence,
                    source_id=doc.source_id,
                    source_section=section_name,
                    char_start=ent.start,
                    char_end=ent.end,
                    aliases=ent.aliases,
                ))
        
        return entities
    
    def extract_from_text(self, text: str, source_id: str = "",
                          source_section: str = "full_text") -> List[CanonicalEntity]:
        """Extract entities from raw text."""
        doc = CanonicalDocument(
            source_id=source_id,
            sections={source_section: text},
            full_text=text,
        )
        return self.extract_from_document(doc)
    
    def _canonicalize(self, text: str) -> str:
        """Canonicalize an entity text to its core form.
        
        Per cycle 110: strip common prefixes/suffixes to find the core term.
        E.g., "membrane_permeability" → "permeability"
              "permeability_values" → "permeability"
        """
        clean = re.sub(r'\s+', '_', text.strip()).lower()
        canonical = clean
        
        # Strip prefixes
        for prefix in ["lower_", "higher_", "zero_", "physical_", "membrane_",
                       "water_", "surface_", "thermal_", "electrical_",
                       "ionic_", "bulk_", "intrinsic_", "apparent_"]:
            if canonical.startswith(prefix):
                remainder = canonical[len(prefix):]
                if len(remainder) >= 4:
                    canonical = remainder
                    break
        
        # Strip suffixes
        for suffix in ["_values", "_p", "_size", "_sizes", "_spaces", "_with",
                       "_measurements", "_measurement", "_constant", "_level",
                       "_levels", "_ratio", "_index"]:
            if canonical.endswith(suffix):
                remainder = canonical[:-len(suffix)]
                if len(remainder) >= 4:
                    canonical = remainder
                    break
        
        return canonical
    
    def find_shared_entities(self, ents_a: List[CanonicalEntity],
                              ents_b: List[CanonicalEntity]) -> List[Dict]:
        """Find entities shared between two entity lists.
        
        Uses canonical_id for matching (not raw text).
        Returns list of shared entity info.
        """
        a_ids = {e.canonical_id for e in ents_a}
        b_ids = {e.canonical_id for e in ents_b}
        shared_ids = a_ids & b_ids
        
        shared = []
        for sid in shared_ids:
            ent_a = next((e for e in ents_a if e.canonical_id == sid), None)
            ent_b = next((e for e in ents_b if e.canonical_id == sid), None)
            if ent_a and ent_b:
                shared.append({
                    "canonical_id": sid,
                    "label_a": ent_a.raw_text,
                    "label_b": ent_b.raw_text,
                    "type": ent_a.entity_type,
                    "source_a": ent_a.source_section,
                    "source_b": ent_b.source_section,
                })
        
        return shared


if __name__ == "__main__":
    # Test on a real PDF
    import glob
    
    extractor = EntityExtractor()
    
    pdfs = glob.glob("/tmp/arxiv_pdfs/*.pdf")[:2]
    if pdfs:
        from scripts.ingest_documents import ingest_pdf
        
        for pdf_path in pdfs:
            doc = ingest_pdf(pdf_path)
            entities = extractor.extract_from_document(doc)
            
            print(f"\n{doc.source_id}:")
            print(f"  Sections: {list(doc.sections.keys())}")
            print(f"  Entities: {len(entities)}")
            print(f"  Sample entities:")
            for e in entities[:10]:
                print(f"    {e.entity_type:12s} {e.raw_text:30s} → {e.canonical_id} "
                      f"(section={e.source_section}, conf={e.confidence})")
