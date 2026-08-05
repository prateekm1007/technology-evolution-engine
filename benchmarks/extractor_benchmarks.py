#!/usr/bin/env python3
"""
extractor_benchmarks.py — DR-46: Extraction benchmarks.

Per docs/EXTRACTION_ARCHITECTURE.md step 8:
  Create a benchmark suite for the extractor itself, separate from
  discovery outcomes.

Benchmark buckets:
  - document parsing quality (sections found, paragraphs, citations)
  - entity precision/recall (against known entities)
  - relation precision/recall (against known relations)
  - mechanism-status accuracy (correct status assignments)
  - world-audit overturn rate (from reaudit log)

Key principle: extractor quality is measured INDEPENDENTLY from whether
a discovery is novel. A noisy extractor that happens to find a novel
bridge should score LOW on extraction quality, not HIGH on discovery.
"""
import sys
import json
import pathlib
from typing import Dict, List, Any
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@dataclass
class BenchmarkResult:
    """A single benchmark result."""
    benchmark_name: str
    metric: str  # precision, recall, f1, accuracy, count
    value: float
    sample_size: int
    details: str = ""


class ExtractorBenchmarks:
    """DR-46: Benchmark suite for the extractor pipeline.
    
    Measures extraction quality separately from discovery outcomes.
    """
    
    def benchmark_document_parsing(self, doc) -> Dict:
        """Benchmark: document parsing quality.
        
        Measures: sections found, paragraph count, citation count, table count.
        """
        return {
            "sections_found": len(doc.sections),
            "paragraph_count": sum(len(p) for p in doc.paragraphs.values()),
            "citation_count": len(doc.citations),
            "table_count": len(doc.tables),
            "body_text_chars": len(doc.get_body_text()),
            "has_provenance": bool(doc.provenance_hash),
            "has_timestamp": bool(doc.retrieval_timestamp),
        }
    
    def benchmark_entity_precision_recall(self, extracted_entities: List[Dict],
                                            known_entities: List[str]) -> Dict:
        """Benchmark: entity precision and recall.
        
        Args:
            extracted_entities: list of {"canonical_id": ...} dicts
            known_entities: list of known correct entity IDs (ground truth)
        
        Returns precision, recall, F1.
        """
        extracted_ids = {e["canonical_id"] for e in extracted_entities}
        known_set = set(known_entities)
        
        true_positives = extracted_ids & known_set
        false_positives = extracted_ids - known_set
        false_negatives = known_set - extracted_ids
        
        precision = len(true_positives) / max(len(extracted_ids), 1)
        recall = len(true_positives) / max(len(known_set), 1)
        f1 = 2 * precision * recall / max(precision + recall, 0.001)
        
        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "true_positives": len(true_positives),
            "false_positives": len(false_positives),
            "false_negatives": len(false_negatives),
            "sample_size": len(known_set),
        }
    
    def benchmark_relation_precision_recall(self, extracted_relations: List[Dict],
                                              known_relations: List[Dict]) -> Dict:
        """Benchmark: relation precision and recall.
        
        A relation matches if subject, relation, and object all match.
        """
        extracted_set = {(r["subject"], r["relation"], r["object"]) 
                         for r in extracted_relations}
        known_set = {(r["subject"], r["relation"], r["object"]) 
                     for r in known_relations}
        
        true_positives = extracted_set & known_set
        false_positives = extracted_set - known_set
        false_negatives = known_set - extracted_set
        
        precision = len(true_positives) / max(len(extracted_set), 1)
        recall = len(true_positives) / max(len(known_set), 1)
        f1 = 2 * precision * recall / max(precision + recall, 0.001)
        
        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "true_positives": len(true_positives),
            "false_positives": len(false_positives),
            "false_negatives": len(false_negatives),
            "sample_size": len(known_set),
        }
    
    def benchmark_mechanism_status_accuracy(self, edges: List[Dict]) -> Dict:
        """Benchmark: mechanism-status accuracy.
        
        Checks that every edge has a valid status.
        """
        valid_statuses = {"associative", "asserted", "plausibility-checked",
                         "verified", "contradicted"}
        
        total = len(edges)
        valid = sum(1 for e in edges if e.get("status") in valid_statuses)
        missing = sum(1 for e in edges if not e.get("status"))
        invalid = sum(1 for e in edges if e.get("status") and e["status"] not in valid_statuses)
        
        return {
            "accuracy": round(valid / max(total, 1), 3),
            "total_edges": total,
            "valid_status": valid,
            "missing_status": missing,
            "invalid_status": invalid,
        }
    
    def benchmark_world_audit_overturn_rate(self, reaudit_entries: List[Dict]) -> Dict:
        """Benchmark: world-audit overturn rate.
        
        Measures the percentage of reaudits that overturned the original claim.
        """
        total = len(reaudit_entries)
        overturned = sum(1 for r in reaudit_entries if r.get("overturned"))
        upheld = sum(1 for r in reaudit_entries if not r.get("overturned"))
        
        return {
            "overturn_rate": round(overturned / max(total, 1), 3),
            "total_audited": total,
            "overturned": overturned,
            "upheld": upheld,
        }
    
    def run_all_benchmarks(self, doc=None, extracted_entities=None,
                           known_entities=None, extracted_relations=None,
                           known_relations=None, edges=None,
                           reaudit_entries=None) -> Dict:
        """Run all benchmark buckets.
        
        Each parameter is optional — only run benchmarks for provided data.
        """
        results = {}
        
        if doc is not None:
            results["document_parsing"] = self.benchmark_document_parsing(doc)
        
        if extracted_entities is not None and known_entities is not None:
            results["entity_precision_recall"] = self.benchmark_entity_precision_recall(
                extracted_entities, known_entities
            )
        
        if extracted_relations is not None and known_relations is not None:
            results["relation_precision_recall"] = self.benchmark_relation_precision_recall(
                extracted_relations, known_relations
            )
        
        if edges is not None:
            results["mechanism_status"] = self.benchmark_mechanism_status_accuracy(edges)
        
        if reaudit_entries is not None:
            results["world_audit"] = self.benchmark_world_audit_overturn_rate(reaudit_entries)
        
        return results
