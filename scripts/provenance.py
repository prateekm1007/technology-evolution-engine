#!/usr/bin/env python3
"""
provenance.py — DR-43: Provenance and temporal guards.

Per docs/EXTRACTION_ARCHITECTURE.md step 6:
  Make every entity/relation edge traceable.

Per EPISTEMIC_ENGINE.md §2.2:
  publication_date < prediction_lock_time invariant.
  retrieval_timestamp <= verification_timestamp.

Every extracted item must carry:
  - source_id
  - source_section
  - character offsets
  - retrieval timestamp
  - provenance hash
"""
import sys
import hashlib
import pathlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProvenanceRecord:
    """DR-43: Provenance for an extracted entity or relation."""
    source_id: str          # arxiv_id, filename, or URL
    source_section: str     # methods, results, discussion
    char_start: int         # character offset in source text
    char_end: int           # character offset end
    retrieval_timestamp: str  # ISO 8601 timestamp of retrieval
    provenance_hash: str    # hash of source content at retrieval time
    source_text_snippet: str = ""  # snippet of source text (first 100 chars)
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "source_section": self.source_section,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "retrieval_timestamp": self.retrieval_timestamp,
            "provenance_hash": self.provenance_hash[:16],
            "source_text_snippet": self.source_text_snippet[:100],
        }


class ProvenanceManager:
    """DR-43: Manage provenance for extracted items.
    
    Provides:
    1. Provenance creation (attach to entities/relations)
    2. Temporal invariant validation (publication_date < prediction_lock_time)
    3. Provenance hash computation
    4. Validation that all items have provenance
    """
    
    def create_provenance(self, source_id: str, source_section: str,
                          char_start: int, char_end: int,
                          source_text: str = "",
                          retrieval_timestamp: str = "") -> ProvenanceRecord:
        """Create a provenance record for an extracted item."""
        if not retrieval_timestamp:
            retrieval_timestamp = datetime.now(timezone.utc).isoformat()
        
        provenance_hash = hashlib.sha256(source_text.encode()).hexdigest() if source_text else ""
        snippet = source_text[:100] if source_text else ""
        
        return ProvenanceRecord(
            source_id=source_id,
            source_section=source_section,
            char_start=char_start,
            char_end=char_end,
            retrieval_timestamp=retrieval_timestamp,
            provenance_hash=provenance_hash,
            source_text_snippet=snippet,
        )
    
    def validate_temporal_invariant(self, publication_date: str,
                                     prediction_lock_time: str) -> List[str]:
        """Validate EPISTEMIC_ENGINE.md §2.2 invariant:
        publication_date < prediction_lock_time
        
        Returns list of errors (empty if valid).
        """
        errors = []
        
        if not publication_date:
            errors.append("publication_date is missing")
            return errors
        if not prediction_lock_time:
            errors.append("prediction_lock_time is missing")
            return errors
        
        try:
            pub = datetime.fromisoformat(publication_date.replace("Z", "+00:00"))
            lock = datetime.fromisoformat(prediction_lock_time.replace("Z", "+00:00"))
            
            if pub >= lock:
                errors.append(
                    f"F-064 class violation: publication_date ({publication_date}) "
                    f">= prediction_lock_time ({prediction_lock_time}). "
                    f"Evidence published after the prediction it verifies "
                    f"cannot be independent confirmation."
                )
        except ValueError as e:
            errors.append(f"date parse error: {e}")
        
        return errors
    
    def validate_retrieval_before_verification(self, retrieval_timestamp: str,
                                                 verification_timestamp: str) -> List[str]:
        """Validate EPISTEMIC_ENGINE.md §2.2 invariant:
        retrieval_timestamp <= verification_timestamp
        """
        errors = []
        
        if not retrieval_timestamp or not verification_timestamp:
            errors.append("missing timestamp")
            return errors
        
        try:
            retrieval = datetime.fromisoformat(retrieval_timestamp.replace("Z", "+00:00"))
            verification = datetime.fromisoformat(verification_timestamp.replace("Z", "+00:00"))
            
            if retrieval > verification:
                errors.append(
                    f"retrieval_timestamp ({retrieval_timestamp}) > "
                    f"verification_timestamp ({verification_timestamp})"
                )
        except ValueError as e:
            errors.append(f"date parse error: {e}")
        
        return errors
    
    def validate_provenance_present(self, items: List[Dict]) -> List[str]:
        """Validate that every item has provenance.
        
        Each item must have: source_id, source_section, char_start, char_end,
        retrieval_timestamp.
        """
        errors = []
        required_fields = ["source_id", "source_section", "char_start", "char_end",
                          "retrieval_timestamp"]
        
        for i, item in enumerate(items):
            for field_name in required_fields:
                if field_name not in item or item[field_name] is None:
                    errors.append(f"Item {i}: missing required field '{field_name}'")
        
        return errors
    
    def compute_provenance_hash(self, text: str) -> str:
        """Compute a hash of source content for provenance."""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def hash_changes_with_content(self, text1: str, text2: str) -> bool:
        """Check if provenance hash changes when content changes."""
        return self.compute_provenance_hash(text1) != self.compute_provenance_hash(text2)
