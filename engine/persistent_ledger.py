"""
persistent_ledger.py — Repair B: persistent, reloadable, hash-verifiable ledger.

Reviewer directive:
    "Persist: ledger/cases/, ledger/hypotheses/, ledger/predictions/,
     ledger/prior_art/, ledger/index.json. Or create a deterministic ledger
     manifest containing the object IDs and hashes. Then an external auditor
     can execute: load ledger, verify registration, verify object hash,
     verify provenance root, verify parent relationships — without rerunning
     the discovery engine."

This module provides a PersistentLedger that:
  1. saves every registered object to disk as JSON
  2. writes an index.json with object IDs + content hashes
  3. can be reloaded by an external auditor
  4. supports verification: object_hash matches file content, provenance
     root hash matches, registration is confirmed

The on-disk layout:
    <ledger_dir>/
        cases/<case_id>.json
        hypotheses/<hypothesis_id>.json
        predictions/<prediction_id>.json
        experiments/<experiment_id>.json
        prior_art/<assessment_id>.json
        transfers/<transfer_id>.json
        failures/<failure_id>.json
        index.json  # {object_type: {id: {content_hash, file, registered_at}}}

An external auditor can:
    1. Load index.json
    2. For each object, load the file and verify its content_hash
    3. Verify the provenance root hash of each case
    4. Traverse the lineage using the case's provenance graph
...without rerunning the engine.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from discovery_infrastructure.discovery_substrate import (
    DiscoveryLedger, DiscoveryCase, Hypothesis, Prediction,
    ExperimentProposal, TransferHypothesis, DiscoveryFailure,
    PriorArtAssessment, DuplicateRegistrationError,
    ProvenanceGraph, ProvenanceNode, ProvenanceEdge,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _object_hash(obj_dict: Dict) -> str:
    """Deterministic content hash of an object's dict representation."""
    return _sha(json.dumps(obj_dict, sort_keys=True, default=str))


@dataclass
class LedgerEntry:
    """A single entry in the ledger index."""
    object_type: str  # case, hypothesis, prediction, etc.
    object_id: str
    content_hash: str  # SHA-256 of the object's JSON
    file: str  # relative path to the JSON file
    registered_at: str
    provenance_root_hash: str = ""  # for cases

    def to_dict(self) -> Dict:
        return {"object_type": self.object_type, "object_id": self.object_id,
                "content_hash": self.content_hash, "file": self.file,
                "registered_at": self.registered_at,
                "provenance_root_hash": self.provenance_root_hash}


class LedgerIntegrityError(Exception):
    """Raised when the persistent ledger's integrity is compromised.

    Round-6 (per reviewer directive): corruption must NEVER produce an
    empty ledger. A corrupted index, missing object, or hash mismatch
    must raise this error so the caller can fail-closed rather than
    silently treating the ledger as empty.
    """
    pass


class PersistentLedger:
    """A discovery ledger that persists every object to disk.

    Round-6 FAIL-CLOSED semantics (per reviewer directive):
        - Corrupted index.json → raise LedgerIntegrityError (NOT "start fresh")
        - Missing index.json on an existing ledger → raise LedgerIntegrityError
        - Object file missing → verification reports the failure
        - Hash mismatch → verification reports the failure
        - NEVER silently treat corruption as an empty ledger

    An empty ledger is ONLY valid if it was just created (no index.json
    exists yet). Once any object has been registered, the index MUST
    exist and MUST be valid. Any corruption is a hard failure.
    """

    def __init__(self, ledger_dir: Path):
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        # Create subdirectories
        for subdir in ["cases", "hypotheses", "predictions", "experiments",
                       "prior_art", "transfers", "failures"]:
            (self.ledger_dir / subdir).mkdir(exist_ok=True)
        # In-memory ledger (for runtime use)
        self._memory = DiscoveryLedger()
        # Index: {object_type: {object_id: LedgerEntry}}
        self._index: Dict[str, Dict[str, LedgerEntry]] = {}
        self._index_path = self.ledger_dir / "index.json"
        self._load_index_fail_closed()

    # ========================================================================
    # Registration (delegates to in-memory ledger + persists to disk)
    # ========================================================================

    def register_case(self, case: DiscoveryCase) -> None:
        self._memory.register_case(case)
        self._persist("case", case.case_id, case.to_dict(),
                       "cases", provenance_root_hash=case.provenance_root_hash)

    def register_hypothesis(self, hyp: Hypothesis) -> None:
        self._memory.register_hypothesis(hyp)
        self._persist("hypothesis", hyp.hypothesis_id, hyp.to_dict(), "hypotheses")

    def register_prediction(self, pred: Prediction) -> None:
        self._memory.register_prediction(pred)
        self._persist("prediction", pred.prediction_id, pred.to_dict(), "predictions")

    def register_experiment(self, exp: ExperimentProposal) -> None:
        self._memory.register_experiment(exp)
        self._persist("experiment", exp.experiment_id, exp.to_dict(), "experiments")

    def register_transfer(self, transfer: TransferHypothesis) -> None:
        self._memory.register_transfer(transfer)
        self._persist("transfer", transfer.transfer_id, transfer.to_dict(), "transfers")

    def register_failure(self, failure: DiscoveryFailure) -> None:
        self._memory.register_failure(failure)
        self._persist("failure", failure.failure_id, failure.to_dict(), "failures")

    def register_prior_art(self, assessment: PriorArtAssessment) -> None:
        self._memory.register_prior_art(assessment)
        self._persist("prior_art", assessment.assessment_id, assessment.to_dict(), "prior_art")

    # ========================================================================
    # Persistence
    # ========================================================================

    def _persist(self, object_type: str, object_id: str,
                 obj_dict: Dict, subdir: str,
                 provenance_root_hash: str = "") -> None:
        """Write an object to disk and update the index."""
        content_hash = _object_hash(obj_dict)
        file_path = self.ledger_dir / subdir / f"{object_id}.json"
        file_path.write_text(json.dumps(obj_dict, indent=2, default=str))
        entry = LedgerEntry(
            object_type=object_type, object_id=object_id,
            content_hash=content_hash,
            file=f"{subdir}/{object_id}.json",
            registered_at=_now(),
            provenance_root_hash=provenance_root_hash)
        self._index.setdefault(object_type, {})[object_id] = entry
        self._save_index()

    def _save_index(self) -> None:
        """Write the index to disk."""
        index_data = {otype: {oid: e.to_dict() for oid, e in entries.items()}
                      for otype, entries in self._index.items()}
        index_data["_meta"] = {
            "ledger_dir": str(self.ledger_dir),
            "last_updated": _now(),
            "total_objects": sum(len(entries) for entries in self._index.values()),
        }
        self._index_path.write_text(json.dumps(index_data, indent=2, default=str))

    def _load_index_fail_closed(self) -> None:
        """Load the index from disk. FAIL-CLOSED on corruption.

        Round-6 (per reviewer directive):
            - If the ledger directory exists but index.json is missing →
              check if any object files exist. If they do, this is a
              corrupted ledger → raise LedgerIntegrityError.
            - If index.json exists but is not valid JSON → raise
              LedgerIntegrityError.
            - If index.json exists but has unexpected structure → raise
              LedgerIntegrityError.
            - An empty index (no index.json, no object files) is ONLY
              valid for a freshly-created ledger.
        """
        if not self._index_path.exists():
            # Check if any object files exist in subdirectories
            object_files_exist = any(
                any(self.ledger_dir.glob(f"{subdir}/*.json"))
                for subdir in ["cases", "hypotheses", "predictions",
                               "experiments", "prior_art", "transfers", "failures"]
            )
            if object_files_exist:
                raise LedgerIntegrityError(
                    f"Ledger index.json missing but object files exist in {self.ledger_dir}. "
                    "This indicates a corrupted ledger — the index was deleted but objects remain. "
                    "Cannot start fresh: evidence would be lost.")
            # Fresh ledger with no objects — this is valid
            return

        # Index exists — parse it
        try:
            data = json.loads(self._index_path.read_text())
        except json.JSONDecodeError as e:
            raise LedgerIntegrityError(
                f"Ledger index.json is corrupted (invalid JSON): {e}. "
                "Cannot start fresh: corruption must be investigated, not hidden.") from e

        if not isinstance(data, dict):
            raise LedgerIntegrityError(
                f"Ledger index.json is corrupted (not a JSON object). "
                "Cannot start fresh: corruption must be investigated.")

        for otype, entries in data.items():
            if otype == "_meta":
                continue
            if not isinstance(entries, dict):
                raise LedgerIntegrityError(
                    f"Ledger index.json has invalid structure: '{otype}' is not a dict. "
                    "Cannot start fresh: corruption must be investigated.")
            self._index[otype] = {}
            for oid, e_dict in entries.items():
                try:
                    self._index[otype][oid] = LedgerEntry(**e_dict)
                except TypeError as e:
                    raise LedgerIntegrityError(
                        f"Ledger index.json entry '{otype}/{oid}' has invalid fields: {e}. "
                        "Cannot start fresh: corruption must be investigated.") from e

    # ========================================================================
    # Verification (for external auditors)
    # ========================================================================

    def verify_registration(self, object_type: str, object_id: str) -> Dict:
        """Verify that an object is registered and its file hash matches.

        Returns a dict with:
          - registered: bool (is the object in the index?)
          - file_exists: bool
          - content_hash_matches: bool (does the file hash match the index?)
          - content_hash: the hash from the index
          - actual_hash: the hash computed from the file
          - file: the relative path to the file
        """
        result = {"registered": False, "file_exists": False,
                  "content_hash_matches": False,
                  "content_hash": "", "actual_hash": "", "file": ""}
        entries = self._index.get(object_type, {})
        entry = entries.get(object_id)
        if not entry:
            return result
        result["registered"] = True
        result["content_hash"] = entry.content_hash
        result["file"] = entry.file
        file_path = self.ledger_dir / entry.file
        if not file_path.exists():
            return result
        result["file_exists"] = True
        try:
            obj_dict = json.loads(file_path.read_text())
            actual_hash = _object_hash(obj_dict)
            result["actual_hash"] = actual_hash
            result["content_hash_matches"] = (actual_hash == entry.content_hash)
        except json.JSONDecodeError:
            pass
        return result

    def verify_all(self) -> Dict:
        """Verify every object in the ledger.

        Returns a summary dict:
          - total: total objects in index
          - verified: objects whose file hash matches
          - missing_files: objects whose file doesn't exist
          - hash_mismatches: objects whose file hash doesn't match
          - details: per-object results
        """
        total = 0
        verified = 0
        missing_files = []
        hash_mismatches = []
        details = []
        for otype, entries in self._index.items():
            for oid, entry in entries.items():
                total += 1
                v = self.verify_registration(otype, oid)
                details.append({"object_type": otype, "object_id": oid, **v})
                if not v["file_exists"]:
                    missing_files.append(f"{otype}/{oid}")
                elif not v["content_hash_matches"]:
                    hash_mismatches.append(f"{otype}/{oid}")
                else:
                    verified += 1
        return {"total": total, "verified": verified,
                "missing_files": missing_files,
                "hash_mismatches": hash_mismatches,
                "details": details}

    def get_case(self, case_id: str) -> Optional[DiscoveryCase]:
        """Load a case from disk with COMPLETE provenance graph reconstruction.

        Repair B (round-5): an external auditor can call this method to load
        a persisted case and independently traverse its provenance graph
        without rerunning the engine. The reconstructed DiscoveryCase has:
          - case_id, input_sources, input_domains, evidence
          - provenance_root_hash
          - a fully populated ProvenanceGraph (nodes + edges)
          - verify_provenance() works
          - LineageValidator().verify(case) works

        This is NOT a simplified reconstruction — it rebuilds the complete
        ProvenanceGraph from the persisted JSON.
        """
        file_path = self.ledger_dir / "cases" / f"{case_id}.json"
        if not file_path.exists():
            return None
        d = json.loads(file_path.read_text())

        # Reconstruct the DiscoveryCase with all fields
        case = DiscoveryCase(case_id=d["case_id"])
        case.input_sources = d.get("input_sources", [])
        case.input_domains = d.get("input_domains", [])
        case.evidence = d.get("evidence", [])
        case.provenance_root_hash = d.get("provenance_root_hash", "")

        # Reconstruct the complete ProvenanceGraph
        prov_data = d.get("provenance", {})
        case.provenance = ProvenanceGraph()
        # Reconstruct nodes
        for node_data in prov_data.get("nodes", {}).values():
            case.provenance.add_node(ProvenanceNode(
                node_id=node_data["node_id"],
                node_type=node_data["node_type"],
                content_hash=node_data.get("content_hash", ""),
                metadata=node_data.get("metadata", {}),
            ))
        # Reconstruct edges (preserve original timestamp so content_hash matches)
        for edge_data in prov_data.get("edges", []):
            edge = ProvenanceEdge(
                edge_id=edge_data["edge_id"],
                source_node_id=edge_data["source_node_id"],
                target_node_id=edge_data["target_node_id"],
                edge_type=edge_data["edge_type"],
                evidence=edge_data.get("evidence", ""),
                actor=edge_data.get("actor", ""),
            )
            # Preserve the original timestamp so the reconstructed graph's
            # content_hash matches the original committed hash.
            edge.timestamp = edge_data.get("timestamp", edge.timestamp)
            case.provenance.add_edge(edge)
        # Re-commit the provenance graph so verify_provenance() works.
        # The committed hash is deterministic (content-addressed), so
        # re-committing produces the same hash as the original — IF the
        # graph content is identical. If the persisted JSON was tampered,
        # the re-committed hash will differ from case.provenance_root_hash,
        # and verify_provenance() will return False (which is the correct
        # behavior for detecting tampering).
        stored_hash = case.provenance_root_hash
        recomputed_hash = case.provenance.commit()
        # If the recomputed hash doesn't match the stored hash, the
        # persisted provenance was tampered. Leave provenance_root_hash
        # as the stored value so verify_provenance() detects the mismatch.
        case.provenance_root_hash = stored_hash
        case.provenance._committed_hash = recomputed_hash

        return case

    def to_dict(self) -> Dict:
        """Summary of the ledger for inspection."""
        return {
            "ledger_dir": str(self.ledger_dir),
            "object_counts": {otype: len(entries) for otype, entries in self._index.items()},
            "total_objects": sum(len(entries) for entries in self._index.values()),
            "index_file": str(self._index_path),
        }


__all__ = ["PersistentLedger", "LedgerEntry"]
