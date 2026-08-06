#!/usr/bin/env python3
"""
extract_relations.py — DR-41: Open-domain relation extraction.

Per docs/EXTRACTION_ARCHITECTURE.md step 4:
  Replace flat relation matching with dependency-path extraction.
  Regex-first extraction retired as primary mechanism.

This module wraps the existing NLP pipeline's relation extraction with:
  1. A clean interface: CanonicalDocument → extract relations
  2. Dependency-path extraction (primary, not regex)
  3. Provenance: every relation traces to source sentence + section
  4. Status tagging (DR-42): associative | asserted
  5. Confidence scoring

Exit criterion: A new domain can produce candidate relations without
hand-authored phrase templates.
"""
import sys
import re
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.nlp_pipeline import NLPPipeline, ExtractedEntity, ExtractedRelation
from scripts.ingest_documents import CanonicalDocument
from scripts.extract_entities import EntityExtractor, CanonicalEntity


@dataclass
class ExtractedRelationWithProvenance:
    """A relation with full provenance (DR-41 + DR-42 + DR-43)."""
    subject: str           # canonical entity ID
    subject_label: str     # raw text
    relation: str          # verb (lemmatized)
    obj: str               # canonical entity ID
    obj_label: str         # raw text
    confidence: float
    # DR-42: mechanism status
    status: str = "associative"  # associative | asserted
    # DR-43: provenance
    source_id: str = ""
    source_section: str = ""
    source_sentence: str = ""
    char_start: int = 0
    char_end: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "subject": self.subject,
            "subject_label": self.subject_label,
            "relation": self.relation,
            "object": self.obj,
            "object_label": self.obj_label,
            "confidence": self.confidence,
            "status": self.status,
            "source_id": self.source_id,
            "source_section": self.source_section,
            "source_sentence": self.source_sentence[:100],
        }


# DR-42: Relations that indicate causation
CAUSAL_RELATIONS = {
    "cause": "causal", "causes": "causal",
    "enable": "enabling", "enables": "enabling",
    "produce": "productive", "produces": "productive",
    "govern": "governing", "governs": "governing",
    "control": "governing", "controls": "governing",
    "increase": "enhancing", "increases": "enhancing",
    "improve": "enhancing", "improves": "enhancing",
    "enhance": "enhancing", "reduces": "inhibiting",
    "degrade": "inhibiting", "inhibit": "inhibiting",
    "prevent": "inhibiting", "block": "inhibiting",
    # Scientific process verbs
    "perform": "productive", "disperse": "productive",
    "exhibit": "causal", "demonstrate": "causal",
    "separate": "productive", "measure": "productive",
    "detect": "productive", "record": "productive",
    "reflect": "productive",
    # Cycle 125: additional scientific causal verbs
    "affects": "causal", "influences": "causal", "impacts": "causal",
    "requires": "enabling", "depends_on": "enabling",
    "correlates_with": "causal", "inversely_correlates": "inhibiting",
    "contains": "productive", "transforms": "productive",
    "applied_to": "enabling",
}


class RelationExtractor:
    """DR-41: Open-domain relation extraction.
    
    Uses dependency-path extraction (via spaCy) as the primary mechanism.
    No regex patterns. No hardcoded phrase templates.
    
    The approach:
    1. Parse text with spaCy dependency parser
    2. Find entity pairs in each sentence
    3. Find the dependency path connecting them (LCA in dep tree)
    4. Extract the relation verb from the path
    5. Assign confidence based on path length
    6. Tag status (associative vs asserted) based on verb type
    """
    
    def __init__(self):
        self.pipeline = NLPPipeline()
        self.entity_extractor = EntityExtractor()
    
    def extract_from_document(self, doc: CanonicalDocument,
                               entities: List[CanonicalEntity] = None) -> List[ExtractedRelationWithProvenance]:
        """Extract relations from a CanonicalDocument.
        
        If entities are provided, uses them. Otherwise extracts first.
        Returns relations with provenance.
        """
        if entities is None:
            entities = self.entity_extractor.extract_from_document(doc)
        
        relations = []
        
        for section_name, section_text in doc.sections.items():
            if not section_text or len(section_text) < 50:
                continue
            
            # Get entities in this section
            section_entities = [e for e in entities if e.source_section == section_name]
            if not section_entities:
                continue
            
            # Extract relations using the NLP pipeline
            raw_relations = self.pipeline.extract_relations(section_text, 
                [ExtractedEntity(
                    text=e.raw_text, label=e.entity_type,
                    start=e.char_start, end=e.char_end,
                    confidence=e.confidence, aliases=e.aliases,
                ) for e in section_entities]
            )
            
            # Convert to provenance-aware relations
            for rel in raw_relations:
                # Canonicalize subject and object
                subj_canonical = self.entity_extractor._canonicalize(rel.subject.text)
                obj_canonical = self.entity_extractor._canonicalize(rel.obj.text)
                
                # Determine status (DR-42)
                relation_verb = rel.relation.lower()
                relation_type = CAUSAL_RELATIONS.get(relation_verb)
                if relation_type:
                    status = "asserted"
                else:
                    status = "associative"
                
                relations.append(ExtractedRelationWithProvenance(
                    subject=subj_canonical,
                    subject_label=rel.subject.text,
                    relation=relation_verb,
                    obj=obj_canonical,
                    obj_label=rel.obj.text,
                    confidence=rel.confidence,
                    status=status,
                    source_id=doc.source_id,
                    source_section=section_name,
                    source_sentence=rel.source_sentence,
                ))
        
        return relations
    
    def extract_from_text(self, text: str, source_id: str = "",
                          source_section: str = "full_text") -> List[ExtractedRelationWithProvenance]:
        """Extract relations from raw text."""
        doc = CanonicalDocument(
            source_id=source_id,
            sections={source_section: text},
            full_text=text,
        )
        return self.extract_from_document(doc)


if __name__ == "__main__":
    # Test on a real PDF
    import glob
    from scripts.ingest_documents import ingest_pdf
    
    extractor = RelationExtractor()
    
    pdfs = glob.glob("/tmp/arxiv_pdfs/*.pdf")[:1]
    if pdfs:
        doc = ingest_pdf(pdfs[0])
        entities = extractor.entity_extractor.extract_from_document(doc)
        relations = extractor.extract_from_document(doc, entities)
        
        print(f"\n{doc.source_id}:")
        print(f"  Entities: {len(entities)}")
        print(f"  Relations: {len(relations)}")
        print(f"  Asserted: {sum(1 for r in relations if r.status == 'asserted')}")
        print(f"  Associative: {sum(1 for r in relations if r.status == 'associative')}")
        print(f"\n  Sample relations:")
        for r in relations[:10]:
            print(f"    {r.subject:20s} --{r.relation:12s}--> {r.obj:20s} "
                  f"(status={r.status}, conf={r.confidence}, section={r.source_section})")
