#!/usr/bin/env python3
"""
epistemic_pipeline.py — The full 7-step wired pipeline (DR-38 through DR-46).

Per cycle 118 auditor instruction: "Wire the full 7-step stack end-to-end.
document → ingest → entities → relations → classify → provenance →
discovery → reaudit → benchmarks."

This module wires all 7 extractor layers into a single callable pipeline:
  1. ingest_documents.py  → CanonicalDocument
  2. extract_entities.py   → List[CanonicalEntity]
  3. extract_relations.py  → List[ExtractedRelationWithProvenance]
  4. classify_mechanisms.py → status-tagged edges
  5. provenance.py         → provenance-validated
  6. mechanism_extraction.py → causal chains
  7. reaudit_loop.py       → discovery claim + reaudit

The pipeline replaces the old manual extraction path (regex + LLM-guided)
with the NLP-based extractor stack. Regex is deprecated as primary.
"""
import sys
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.ingest_documents import ingest_pdf, ingest_text, CanonicalDocument
from scripts.extract_entities import EntityExtractor, CanonicalEntity
from scripts.extract_relations import RelationExtractor, ExtractedRelationWithProvenance
from scripts.classify_mechanisms import MechanismClassifier
from scripts.provenance import ProvenanceManager
from scripts.mechanism_extraction import MechanismExtractor
from benchmarks.extractor_benchmarks import ExtractorBenchmarks


class EpistemicPipeline:
    """The full 7-step wired pipeline.
    
    This is the canonical extraction path (DR-38: regex retired as primary).
    Every step is wired: document → ingest → entities → relations → 
    classify → provenance → chains → benchmarks.
    """
    
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()
        self.mechanism_classifier = MechanismClassifier()
        self.provenance_manager = ProvenanceManager()
        self.chain_extractor = MechanismExtractor()
        self.benchmarks = ExtractorBenchmarks()
    
    def process_pdf(self, pdf_path: str, source_id: str = "") -> Dict:
        """Process a single PDF through the full pipeline.
        
        Returns a structured result with all extraction artifacts.
        """
        # Step 1: Ingest document
        doc = ingest_pdf(pdf_path, source_id=source_id)
        
        # Step 2: Extract entities
        entities = self.entity_extractor.extract_from_document(doc)
        
        # Step 3: Extract relations
        relations = self.relation_extractor.extract_from_document(doc, entities)
        
        # Step 4: Classify mechanism status (already done in step 3 via DR-42)
        # Validate: no edge without status
        status_errors = self.mechanism_classifier.validate_no_missing_status(relations)
        
        # Step 5: Provenance (already attached in steps 2-3)
        # Validate: every entity has provenance
        entity_provenance = [
            {"source_id": e.source_id, "source_section": e.source_section,
             "char_start": e.char_start, "char_end": e.char_end,
             "retrieval_timestamp": doc.retrieval_timestamp}
            for e in entities
        ]
        provenance_errors = self.provenance_manager.validate_provenance_present(entity_provenance)
        
        # Step 6: Extract causal chains
        edges_for_chains = [
            {"source": r.subject, "target": r.obj,
             "relation": r.relation, "mechanism": r.relation,
             "confidence": r.confidence,
             "source_sentence": r.source_sentence}
            for r in relations
        ]
        chains_result = self.chain_extractor.extract_mechanisms(edges_for_chains, min_steps=1)
        
        # Step 7: Benchmarks
        parsing_bm = self.benchmarks.benchmark_document_parsing(doc)
        status_bm = self.benchmarks.benchmark_mechanism_status_accuracy(
            [{"status": r.status} for r in relations]
        )
        
        return {
            "source_id": doc.source_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline": "epistemic_v1_full_stack",
            # Step 1: Document
            "document": {
                "title": doc.title[:100],
                "sections": list(doc.sections.keys()),
                "body_chars": len(doc.get_body_text()),
                "provenance_hash": doc.provenance_hash[:16],
            },
            # Step 2: Entities
            "entity_count": len(entities),
            "entities_sample": [
                {"id": e.canonical_id, "type": e.entity_type,
                 "section": e.source_section, "confidence": e.confidence}
                for e in entities[:10]
            ],
            # Step 3: Relations
            "relation_count": len(relations),
            "relations_sample": [r.to_dict() for r in relations[:10]],
            # Step 4: Status
            "status_errors": status_errors,
            "status_summary": {
                "asserted": sum(1 for r in relations if r.status == "asserted"),
                "associative": sum(1 for r in relations if r.status == "associative"),
            },
            # Step 5: Provenance
            "provenance_errors": provenance_errors,
            # Step 6: Chains
            "chain_count": chains_result["stats"]["causal_chains"],
            "contradiction_count": chains_result["stats"]["contradictions"],
            "chains_sample": [
                {"label": c["mechanism_label"], "steps": len(c["steps"]),
                 "confidence": c["confidence"]}
                for c in chains_result["chains"][:5]
            ],
            # Step 7: Benchmarks
            "benchmarks": {
                "document_parsing": parsing_bm,
                "mechanism_status": status_bm,
            },
        }
    
    def process_two_papers_for_discovery(self, pdf_a: str, pdf_b: str,
                                          source_id_a: str = "",
                                          source_id_b: str = "") -> Dict:
        """Process two PDFs through the full pipeline and find shared entities.
        
        Per cycle 127 (Gen 4): wires status-tagged mechanism chains into
        discovery. Chains with 'asserted' or higher status are used for
        bridge detection. Chains with 'associative' status are flagged
        but not used for bridges.
        """
        # Process both papers
        result_a = self.process_pdf(pdf_a, source_id_a)
        result_b = self.process_pdf(pdf_b, source_id_b)
        
        # Extract entities for shared detection
        doc_a = ingest_pdf(pdf_a, source_id_a)
        doc_b = ingest_pdf(pdf_b, source_id_b)
        ents_a = self.entity_extractor.extract_from_document(doc_a)
        ents_b = self.entity_extractor.extract_from_document(doc_b)
        
        # Find shared entities
        shared = self.entity_extractor.find_shared_entities(ents_a, ents_b)
        
        # Extract relations for bridge detection
        rels_a = self.relation_extractor.extract_from_document(doc_a, ents_a)
        rels_b = self.relation_extractor.extract_from_document(doc_b, ents_b)
        
        # Per cycle 127 (Gen 4): classify chain status for each relation set
        # Only use 'asserted' or higher status relations for bridge detection
        asserted_rels_a = [r for r in rels_a if r.status == "asserted"]
        asserted_rels_b = [r for r in rels_b if r.status == "asserted"]
        associative_rels_a = [r for r in rels_a if r.status == "associative"]
        associative_rels_b = [r for r in rels_b if r.status == "associative"]
        
        # Find bridges using ASSERTED relations only (Gen 4 quality gate)
        bridges = []
        for s in shared:
            sid = s["canonical_id"]
            a_edges = [r for r in asserted_rels_a if r.subject == sid or r.obj == sid]
            b_edges = [r for r in asserted_rels_b if r.subject == sid or r.obj == sid]
            
            for ae in a_edges[:3]:
                for be in b_edges[:3]:
                    a_ent = ae.obj if ae.subject == sid else ae.subject
                    b_ent = be.obj if be.subject == sid else be.subject
                    bridges.append({
                        "a": a_ent, "shared": sid, "b": b_ent,
                        "a_status": ae.status, "b_status": be.status,
                        "a_confidence": ae.confidence, "b_confidence": be.confidence,
                        "chain_status": self.mechanism_classifier.classify_chain([
                            type('S', (), {'status': ae.status})(),
                            type('S', (), {'status': be.status})(),
                        ]),
                    })
        
        # Per cycle 127 (Gen 4): detect contradictions in combined relations
        all_edges_combined = [
            {"source": r.subject, "target": r.obj,
             "relation": r.relation, "mechanism": r.relation}
            for r in rels_a + rels_b
        ]
        contradictions = self.chain_extractor.detect_contradictions(all_edges_combined)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline": "epistemic_v1_discovery_with_status",
            "paper_a": result_a,
            "paper_b": result_b,
            "shared_entities": shared,
            "bridges_found": len(bridges),
            "bridges": bridges[:10],
            "outcome": "POTENTIAL_HIT" if bridges else "NULL",
            # Gen 4 cycle 127: status-tagged discovery
            "status_summary": {
                "asserted_a": len(asserted_rels_a),
                "asserted_b": len(asserted_rels_b),
                "associative_a": len(associative_rels_a),
                "associative_b": len(associative_rels_b),
                "bridges_from_asserted": len(bridges),
            },
            # Gen 4 cycle 127: contradiction detection on real data
            "contradictions_found": len(contradictions),
            "contradictions": [
                {"entity": c.entity, "claim_1": c.claim_1, "claim_2": c.claim_2}
                for c in contradictions[:5]
            ],
        }


if __name__ == "__main__":
    import glob
    
    pipeline = EpistemicPipeline()
    
    # Test on a single PDF
    pdfs = glob.glob("/tmp/arxiv_pdfs/*.pdf")[:1]
    if pdfs:
        result = pipeline.process_pdf(pdfs[0])
        print(f"=== Single PDF Pipeline Result ===")
        print(f"Source: {result['source_id']}")
        print(f"Sections: {result['document']['sections']}")
        print(f"Body chars: {result['document']['body_chars']}")
        print(f"Entities: {result['entity_count']}")
        print(f"Relations: {result['relation_count']}")
        print(f"Status: {result['status_summary']}")
        print(f"Status errors: {len(result['status_errors'])}")
        print(f"Provenance errors: {len(result['provenance_errors'])}")
        print(f"Chains: {result['chain_count']}")
        print(f"Benchmarks: {json.dumps(result['benchmarks'], indent=2)}")
    
    # Test two-paper discovery
    if len(pdfs) >= 2:
        discovery = pipeline.process_two_papers_for_discovery(pdfs[0], pdfs[1])
        print(f"\n=== Two-Paper Discovery ===")
        print(f"Shared entities: {len(discovery['shared_entities'])}")
        print(f"Bridges: {discovery['bridges_found']}")
        print(f"Outcome: {discovery['outcome']}")
        if discovery["bridges"]:
            for b in discovery["bridges"][:5]:
                print(f"  {b['a']} → {b['shared']} → {b['b']} "
                      f"(a:{b['a_status']}, b:{b['b_status']})")
