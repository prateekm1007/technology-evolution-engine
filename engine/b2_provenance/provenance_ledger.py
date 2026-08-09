#!/usr/bin/env python3
"""b2_provenance/provenance_ledger.py — Append-only hash-chained provenance ledger.

Per B2_REVISION_R5.md (Section 10), B2_REVISION_R5_1.md (FATAL 2 fix),
and audit round 46 (FATAL: ledger must be truly append-only):

    The ledger stores TWO types of immutable events:
    1. CANDIDATE_GENERATED — records that a candidate was generated
       (created BEFORE adjudication, committed to git, never modified)
    2. ADJUDICATION_RECORDED — records adjudication results
       (appended AFTER adjudication, linked to the generation event)

    The generation entry is NEVER mutated. Adjudication is a SEPARATE
    event that references the generation event by candidate_id.

    The hash chain:
        GENESIS
           ↓
        CANDIDATE_GENERATED (entry_hash = H(genesis + generation fields))
           ↓
        ADJUDICATION_RECORDED (entry_hash = H(prev_entry_hash + adjudication fields))
           ↓
        ... next event ...

    This ensures:
    - The generation record is cryptographically immutable
    - Adjudication cannot modify the generation entry
    - The chain proves temporal ordering (generation before adjudication)
    - Tampering with any entry breaks the chain

This module provides:
    - ProvenanceLedger class with append_generation_event and append_adjudication_event
    - Hash-chain verification
    - Tamper detection (any modification breaks the chain)
    - Query methods for retrieving events by case_id, arm, candidate_id
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


# Event type constants
EVENT_TYPE_CANDIDATE_GENERATED = "CANDIDATE_GENERATED"
EVENT_TYPE_ADJUDICATION_RECORDED = "ADJUDICATION_RECORDED"


class ProvenanceLedger:
    """Append-only hash-chained provenance ledger with immutable events.

    The ledger stores a sequence of events. Each event is immutable:
    once appended, it cannot be modified. Adjudication is a separate
    event type (ADJUDICATION_RECORDED) that references the original
    generation event (CANDIDATE_GENERATED) by candidate_id.

    The generation entry's hash is NEVER recomputed after creation.
    Adjudication creates a NEW entry linked to the previous one via
    prev_entry_hash.
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
        """Get the hash of the last entry, or 'GENESIS' if ledger is empty."""
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
        """Append a CANDIDATE_GENERATED event to the ledger.

        This event records that a candidate was generated. It is
        created BEFORE adjudication and is NEVER modified.

        The generation entry is immutable: once appended, its fields
        (including its entry_hash) cannot change. Adjudication is
        recorded as a separate ADJUDICATION_RECORDED event.

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
            The created generation event dict.

        Raises:
            ValueError: if a generation event for this candidate_id
                        already exists (append-only, no overwrite).
        """
        candidate_id = f"{case_id}-{arm.upper()}-CAND-{candidate_rank:03d}"

        # Check for duplicate generation event (append-only).
        for existing in self._entries:
            if (existing.get("event_type") == EVENT_TYPE_CANDIDATE_GENERATED
                    and existing.get("candidate_id") == candidate_id):
                raise ValueError(
                    f"Generation event already exists for {candidate_id}. "
                    f"The ledger is append-only — cannot overwrite."
                )

        prev_hash = self._get_prev_hash()

        # The generation event contains ONLY generation fields.
        # No adjudication fields — those go in a separate event.
        entry = {
            "event_type": EVENT_TYPE_CANDIDATE_GENERATED,
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
        """Append an ADJUDICATION_RECORDED event to the ledger.

        This creates a NEW ledger event — it does NOT modify the
        original CANDIDATE_GENERATED event. The generation entry
        remains immutable.

        The adjudication event references the candidate by candidate_id
        and is linked to the chain via prev_entry_hash.

        Args:
            candidate_id: the candidate being adjudicated
            adjudication fields...

        Returns:
            The created adjudication event.

        Raises:
            KeyError: if no CANDIDATE_GENERATED event exists for candidate_id.
            ValueError: if an ADJUDICATION_RECORDED event already exists
                        for this candidate_id (no double-adjudication).
        """
        # Verify the generation event exists.
        generation_exists = any(
            e.get("event_type") == EVENT_TYPE_CANDIDATE_GENERATED
            and e.get("candidate_id") == candidate_id
            for e in self._entries
        )
        if not generation_exists:
            raise KeyError(
                f"No CANDIDATE_GENERATED event found for {candidate_id}. "
                f"Cannot adjudicate a candidate that was never generated."
            )

        # Check for duplicate adjudication event (no double-adjudication).
        for existing in self._entries:
            if (existing.get("event_type") == EVENT_TYPE_ADJUDICATION_RECORDED
                    and existing.get("candidate_id") == candidate_id):
                raise ValueError(
                    f"Adjudication event already exists for {candidate_id}. "
                    f"Cannot adjudicate twice (append-only)."
                )

        prev_hash = self._get_prev_hash()

        # The adjudication event references the candidate but does NOT
        # modify the generation entry.
        entry = {
            "event_type": EVENT_TYPE_ADJUDICATION_RECORDED,
            "candidate_id": candidate_id,
            "adjudication_input_sha256": adjudication_input_sha256,
            "gate_a_classification": gate_a_classification,
            "gate_a_adjudicator_ids": gate_a_adjudicator_ids,
            "gate_a_agreement": gate_a_agreement,
            "gate_c_classification": gate_c_classification,
            "gate_c_adjudicator_ids": gate_c_adjudicator_ids,
            "gate_c_agreement": gate_c_agreement,
            "prior_art_search_id": prior_art_search_id,
            "prior_art_channel_a_result": prior_art_channel_a_result,
            "prior_art_channel_b_result": prior_art_channel_b_result,
            "prior_art_final": prior_art_final,
            "case_success": case_success,
            "adjudication_timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_entry_hash": prev_hash,
        }

        # Compute and add the entry hash.
        entry["entry_hash"] = self._compute_entry_hash(entry)

        self._entries.append(entry)
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
                f"Hash chain broken at entry {i} "
                f"({entry.get('event_type')}, {entry.get('candidate_id')}): "
                f"prev_entry_hash={entry['prev_entry_hash'][:16]}... but "
                f"expected {prev_hash[:16]}..."
            )

            # Check entry_hash integrity.
            recomputed_hash = self._compute_entry_hash(entry)
            assert entry["entry_hash"] == recomputed_hash, (
                f"Entry hash mismatch at entry {i} "
                f"({entry.get('event_type')}, {entry.get('candidate_id')}): "
                f"stored={entry['entry_hash'][:16]}... but "
                f"recomputed={recomputed_hash[:16]}... "
                f"The entry has been modified after hashing."
            )

            prev_hash = entry["entry_hash"]

        return True

    def verify_generation_immutability(self, candidate_id: str) -> bool:
        """Verify that a candidate's generation event has not been modified
        after adjudication was recorded.

        This checks that:
        1. A CANDIDATE_GENERATED event exists for candidate_id
        2. Its entry_hash matches the recomputed hash
        3. If an ADJUDICATION_RECORDED event exists, it is a SEPARATE
           entry (not a mutation of the generation entry)

        Args:
            candidate_id: the candidate to check

        Returns:
            True if the generation event is immutable.

        Raises:
            AssertionError: if the generation event was mutated.
            KeyError: if no generation event exists.
        """
        generation_entry = None
        adjudication_entry = None

        for entry in self._entries:
            if entry.get("candidate_id") != candidate_id:
                continue
            if entry.get("event_type") == EVENT_TYPE_CANDIDATE_GENERATED:
                generation_entry = entry
            elif entry.get("event_type") == EVENT_TYPE_ADJUDICATION_RECORDED:
                adjudication_entry = entry

        if generation_entry is None:
            raise KeyError(
                f"No CANDIDATE_GENERATED event for {candidate_id}"
            )

        # Verify the generation entry's hash is intact.
        recomputed = self._compute_entry_hash(generation_entry)
        assert generation_entry["entry_hash"] == recomputed, (
            f"Generation entry for {candidate_id} has been MODIFIED. "
            f"stored hash={generation_entry['entry_hash'][:16]}... but "
            f"recomputed={recomputed[:16]}... "
            f"The generation record is supposed to be immutable."
        )

        # Verify the generation entry does NOT contain adjudication fields.
        adjudication_fields = [
            "adjudication_input_sha256", "gate_a_classification",
            "gate_c_classification", "case_success",
        ]
        for field in adjudication_fields:
            assert field not in generation_entry, (
                f"Generation entry for {candidate_id} contains adjudication "
                f"field '{field}'. The generation record should NOT contain "
                f"adjudication data — that belongs in a separate "
                f"ADJUDICATION_RECORDED event."
            )

        return True

    def get_generation_event(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get the CANDIDATE_GENERATED event for a candidate."""
        for entry in self._entries:
            if (entry.get("event_type") == EVENT_TYPE_CANDIDATE_GENERATED
                    and entry.get("candidate_id") == candidate_id):
                return entry
        return None

    def get_adjudication_event(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get the ADJUDICATION_RECORDED event for a candidate (if any)."""
        for entry in self._entries:
            if (entry.get("event_type") == EVENT_TYPE_ADJUDICATION_RECORDED
                    and entry.get("candidate_id") == candidate_id):
                return entry
        return None

    def get_entry(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get the generation event for a candidate (backward-compatible
        with the old API). Returns the CANDIDATE_GENERATED event."""
        return self.get_generation_event(candidate_id)

    def get_combined_record(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get a combined view of generation + adjudication for a candidate.

        This merges the generation event and adjudication event (if any)
        into a single dict for convenience. The underlying events remain
        separate and immutable.

        Args:
            candidate_id: the candidate

        Returns:
            Combined dict, or None if no generation event exists.
        """
        gen = self.get_generation_event(candidate_id)
        if gen is None:
            return None
        adj = self.get_adjudication_event(candidate_id)

        combined = dict(gen)
        if adj is not None:
            # Add adjudication fields (excluding event_type and
            # candidate_id which are already in gen, and prev_entry_hash
            # and entry_hash which are chain-specific).
            for k, v in adj.items():
                if k not in ("event_type", "candidate_id", "prev_entry_hash",
                             "entry_hash"):
                    combined[k] = v
        return combined

    def get_entries_for_case(self, case_id: str, arm: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all generation events for a given case (optionally filtered by arm).

        Returns only CANDIDATE_GENERATED events (not adjudication events).
        """
        results = []
        for entry in self._entries:
            if entry.get("event_type") != EVENT_TYPE_CANDIDATE_GENERATED:
                continue
            if entry.get("case_id") != case_id:
                continue
            if arm is not None and entry.get("arm") != arm:
                continue
            results.append(entry)
        return results

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Get all entries (for audit). Includes both event types."""
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
        """Number of entries in the ledger (all event types)."""
        return len(self._entries)

    def n_generation_events(self) -> int:
        """Number of CANDIDATE_GENERATED events."""
        return sum(
            1 for e in self._entries
            if e.get("event_type") == EVENT_TYPE_CANDIDATE_GENERATED
        )

    def n_adjudication_events(self) -> int:
        """Number of ADJUDICATION_RECORDED events."""
        return sum(
            1 for e in self._entries
            if e.get("event_type") == EVENT_TYPE_ADJUDICATION_RECORDED
        )
