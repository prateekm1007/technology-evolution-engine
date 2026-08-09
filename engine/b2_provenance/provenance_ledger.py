#!/usr/bin/env python3
"""b2_provenance/provenance_ledger.py — Append-only hash-chained provenance ledger.

Per B2_REVISION_R5.md (Section 10) and B2_REVISION_R5_1.md (FATAL 2 fix):

    For every candidate, an immutable provenance record is maintained.

    The ledger is:
    - Append-only (no modification or deletion of entries)
    - Hash-chained (each entry references the previous entry's hash)
    - SHA-256 committed to git before adjudication
    - Finalized and re-committed after adjudication

    Any discrepancy between pre-adjudication and post-adjudication ledger
    (other than adding adjudication results) is a FATAL integrity violation.

This module provides:
    - ProvenanceLedger class with append, verify, and finalize methods
    - Hash-chain verification
    - Tamper detection

The ledger is the central artifact that answers:
    "Can an independent auditor reconstruct exactly what information existed
     at every stage and prove that the final candidate was not selected or
     altered after the fact?"
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .frozen_parser import (
    get_parser_sha256,
    get_parser_config_sha256,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "provenance" / "ledger.json"


class ProvenanceLedger:
    """Append-only hash-chained provenance ledger.

    The ledger stores one entry per candidate. Each entry contains:
    - case_id, arm, candidate_id
    - raw_output_sha256, raw_output_blob_path
    - parser_sha256, parser_config_sha256
    - candidate_rank, candidate_sha256
    - adjudication results (added after adjudication)
    - prev_entry_hash (hash chain)
    - entry_hash (hash of this entry, excluding itself)

    The hash chain ensures any modification to an entry breaks the chain
    and is detectable.
    """

    def __init__(self, ledger_path: Path = LEDGER_PATH):
        self.ledger_path = ledger_path
        self._entries: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        """Load the ledger from disk if it exists."""
        if self.ledger_path.exists():
            data = json.loads(self.ledger_path.read_text())
            self._entries = data.get("entries", [])
        else:
            self._entries = []

    def _save(self):
        """Save the ledger to disk."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ledger_type": "B2_PROVENANCE_LEDGER",
            "entries": self._entries,
            "n_entries": len(self._entries),
        }
        self.ledger_path.write_text(json.dumps(data, indent=2))

    def _compute_entry_hash(self, entry: Dict[str, Any]) -> str:
        """Compute the hash of an entry (excluding the entry_hash field).

        The hash is computed over the canonical JSON serialization
        (sorted keys, compact separators) of the entry with entry_hash
        removed.
        """
        entry_without_hash = {k: v for k, v in entry.items() if k != "entry_hash"}
        entry_str = json.dumps(entry_without_hash, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(entry_str.encode("utf-8")).hexdigest()

    def _get_prev_hash(self) -> str:
        """Get the hash of the last entry, or "GENESIS" if ledger is empty."""
        if not self._entries:
            return "GENESIS"
        return self._entries[-1]["entry_hash"]

    def append_candidate_entry(
        self,
        case_id: str,
        arm: str,
        candidate_rank: int,
        raw_output_sha256: str,
        raw_output_blob_path: str,
        candidate_sha256: str,
        candidate_text: str,
        generation_timestamp: str,
        engine_version: str,
        provider: str,
        model: str,
        prompt_hash: str,
        source_pair_sha256: str,
        invocation_seed: str,
    ) -> Dict[str, Any]:
        """Append a candidate entry to the ledger.

        This is called BEFORE adjudication. The entry records that a
        candidate was generated and its derivation is verifiable.

        Args:
            case_id: e.g., "CASE-001"
            arm: "engine" or "null"
            candidate_rank: 1, 2, or 3
            raw_output_sha256: SHA-256 of the raw output
            raw_output_blob_path: path to the content-addressed blob
            candidate_sha256: SHA-256 of the parsed candidate text
            candidate_text: the candidate text (for audit)
            generation_timestamp: ISO 8601 timestamp
            engine_version: git commit SHA of the engine
            provider: e.g., "ZAI"
            model: e.g., "glm-4-plus"
            prompt_hash: SHA-256 of the frozen prompt
            source_pair_sha256: SHA-256 of (source_a, source_b)
            invocation_seed: the universal seed used for generation

        Returns:
            The created entry dict.

        Raises:
            ValueError: if an entry with the same (case_id, arm, candidate_rank)
                        already exists (append-only, no overwrite).
        """
        # Check for duplicate (append-only means no overwrite).
        candidate_id = f"{case_id}-{arm.upper()}-CAND-{candidate_rank:03d}"
        for existing in self._entries:
            if existing.get("candidate_id") == candidate_id:
                raise ValueError(
                    f"Entry already exists for {candidate_id}. "
                    f"The ledger is append-only — cannot overwrite."
                )

        prev_hash = self._get_prev_hash()

        entry = {
            "candidate_id": candidate_id,
            "case_id": case_id,
            "arm": arm,
            "candidate_rank": candidate_rank,
            "raw_output_sha256": raw_output_sha256,
            "raw_output_blob_path": raw_output_blob_path,
            "parser_sha256": get_parser_sha256(),
            "parser_config_sha256": get_parser_config_sha256(),
            "candidate_sha256": candidate_sha256,
            "candidate_text": candidate_text,
            "generation_timestamp": generation_timestamp,
            "engine_version": engine_version,
            "provider": provider,
            "model": model,
            "prompt_hash": prompt_hash,
            "source_pair_sha256": source_pair_sha256,
            "invocation_seed": invocation_seed,
            "prev_entry_hash": prev_hash,
            # Adjudication fields (filled later)
            "adjudication_input_sha256": None,
            "gate_a_classification": None,
            "gate_a_adjudicator_ids": None,
            "gate_a_agreement": None,
            "gate_c_classification": None,
            "gate_c_adjudicator_ids": None,
            "gate_c_agreement": None,
            "prior_art_search_id": None,
            "prior_art_channel_a_result": None,
            "prior_art_channel_b_result": None,
            "prior_art_final": None,
            "case_success": None,
            "case_success_timestamp": None,
        }

        # Compute and add the entry hash.
        entry["entry_hash"] = self._compute_entry_hash(entry)

        self._entries.append(entry)
        self._save()
        return entry

    def append_adjudication_result(
        self,
        candidate_id: str,
        adjudication_input_sha256: str,
        gate_a_classification: str,
        gate_a_adjudicator_ids: List[str],
        gate_a_agreement: bool,
        gate_c_classification: str,
        gate_c_adjudicator_ids: List[str],
        gate_c_agreement: bool,
        prior_art_search_id: str,
        prior_art_channel_a_result: str,
        prior_art_channel_b_result: str,
        prior_art_final: str,
        case_success: bool,
    ) -> Dict[str, Any]:
        """Append adjudication results to an existing candidate entry.

        This is called AFTER adjudication. It fills in the adjudication
        fields and recomputes the entry hash.

        Args:
            candidate_id: the candidate to update
            adjudication fields...

        Returns:
            The updated entry.

        Raises:
            KeyError: if the candidate_id is not found.
            ValueError: if adjudication results already exist (no overwrite).
        """
        entry = None
        for e in self._entries:
            if e.get("candidate_id") == candidate_id:
                entry = e
                break

        if entry is None:
            raise KeyError(f"Candidate {candidate_id} not found in ledger")

        if entry.get("case_success") is not None:
            raise ValueError(
                f"Adjudication results already exist for {candidate_id}. "
                f"Cannot overwrite (append-only)."
            )

        # Update adjudication fields.
        entry["adjudication_input_sha256"] = adjudication_input_sha256
        entry["gate_a_classification"] = gate_a_classification
        entry["gate_a_adjudicator_ids"] = gate_a_adjudicator_ids
        entry["gate_a_agreement"] = gate_a_agreement
        entry["gate_c_classification"] = gate_c_classification
        entry["gate_c_adjudicator_ids"] = gate_c_adjudicator_ids
        entry["gate_c_agreement"] = gate_c_agreement
        entry["prior_art_search_id"] = prior_art_search_id
        entry["prior_art_channel_a_result"] = prior_art_channel_a_result
        entry["prior_art_channel_b_result"] = prior_art_channel_b_result
        entry["prior_art_final"] = prior_art_final
        entry["case_success"] = case_success
        entry["case_success_timestamp"] = datetime.now(timezone.utc).isoformat()

        # Recompute entry hash (the entry has changed).
        entry["entry_hash"] = self._compute_entry_hash(entry)

        self._save()
        return entry

    def verify_hash_chain(self) -> bool:
        """Verify the hash chain integrity of the entire ledger.

        Each entry's prev_entry_hash must match the previous entry's
        entry_hash. Each entry's entry_hash must match the recomputed
        hash of its content.

        Returns:
            True if the chain is intact.

        Raises:
            AssertionError: if any entry's hash does not match (tampering).
        """
        prev_hash = "GENESIS"
        for i, entry in enumerate(self._entries):
            # Check prev_entry_hash linkage.
            assert entry["prev_entry_hash"] == prev_hash, (
                f"Hash chain broken at entry {i} ({entry.get('candidate_id')}): "
                f"prev_entry_hash={entry['prev_entry_hash'][:16]}... but "
                f"expected {prev_hash[:16]}..."
            )

            # Check entry_hash integrity.
            recomputed_hash = self._compute_entry_hash(entry)
            assert entry["entry_hash"] == recomputed_hash, (
                f"Entry hash mismatch at entry {i} ({entry.get('candidate_id')}): "
                f"stored={entry['entry_hash'][:16]}... but "
                f"recomputed={recomputed_hash[:16]}... "
                f"The entry has been modified after hashing."
            )

            prev_hash = entry["entry_hash"]

        return True

    def get_entry(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get an entry by candidate_id."""
        for entry in self._entries:
            if entry.get("candidate_id") == candidate_id:
                return entry
        return None

    def get_entries_for_case(self, case_id: str, arm: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all entries for a given case (optionally filtered by arm)."""
        results = []
        for entry in self._entries:
            if entry.get("case_id") != case_id:
                continue
            if arm is not None and entry.get("arm") != arm:
                continue
            results.append(entry)
        return results

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Get all entries (for audit)."""
        return list(self._entries)

    def get_ledger_sha256(self) -> str:
        """Compute SHA-256 of the entire ledger (for git commitment)."""
        data = {
            "ledger_type": "B2_PROVENANCE_LEDGER",
            "entries": self._entries,
            "n_entries": len(self._entries),
        }
        ledger_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(ledger_str.encode("utf-8")).hexdigest()

    def n_entries(self) -> int:
        """Number of entries in the ledger."""
        return len(self._entries)
