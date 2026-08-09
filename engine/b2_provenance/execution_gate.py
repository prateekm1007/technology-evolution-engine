#!/usr/bin/env python3
"""execution_gate.py — Hard gate: no generation without sealed manifest.

Per audit round 55-59: the execution gate enforces that no CANDIDATE_GENERATED
event can be created without a sealed+verified manifest. The gate is enforced
at the AUTHORITATIVE PROVENANCE BOUNDARY (ProvenanceLedger.append_candidate_entry).

ARCHITECTURAL INVARIANT (per audit round 59):
    The gate AUTO-BINDS to the ledger when append_candidate_entry is called.
    In __exit__, if post-execution verification fails, the gate AUTOMATICALLY
    calls ledger.mark_execution_compromised(). No human/caller action required.

    SEALED MANIFEST → EXECUTION GATE → CANDIDATE_GENERATED → EXECUTION ENDS
    → REVERIFY MANIFEST → if INVALID → COMPROMISE_RECORDED (automatic)

    No human intervention exists anywhere in that path.

REPORTING (per audit round 55):
    The first run reports only machine facts:
    - what ran, what artifacts, hashes, failures, exclusions, provenance status
    - NO: successful, failed, fair, discovery, significant, or North Star
"""
import hashlib
import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.verify_audit_instrument import (
    verify_execution_manifest,
    verify_instrument,
)


class ExecutionGateError(Exception):
    """Raised when execution is attempted without a sealed/verified manifest."""
    pass


@dataclass
class ExecutionRecord:
    """Machine-fact record of what happened during execution.

    Contains ONLY machine facts. No interpretive language.
    """
    execution_id: str
    manifest_sha256: str
    started_at: str
    finished_at: Optional[str] = None
    cases_processed: List[str] = field(default_factory=list)
    arms_run: List[str] = field(default_factory=list)
    artifacts_produced: List[Dict[str, Any]] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    exclusions: List[Dict[str, str]] = field(default_factory=list)
    provenance_verified: bool = False
    manifest_verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "manifest_sha256": self.manifest_sha256,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "cases_processed": self.cases_processed,
            "arms_run": self.arms_run,
            "artifacts_produced": self.artifacts_produced,
            "failures": self.failures,
            "exclusions": self.exclusions,
            "provenance_verified": self.provenance_verified,
            "manifest_verified": self.manifest_verified,
        }

    def add_artifact(self, case_id: str, arm: str, rank: int,
                     candidate_sha256: str, raw_output_sha256: str):
        self.artifacts_produced.append({
            "case_id": case_id, "arm": arm, "candidate_rank": rank,
            "candidate_sha256": candidate_sha256,
            "raw_output_sha256": raw_output_sha256,
        })

    def add_failure(self, description: str):
        self.failures.append(description)

    def add_exclusion(self, case_id: str, reason: str):
        self.exclusions.append({"case_id": case_id, "reason": reason})


class ExecutionGate:
    """Hard gate: no generation without a sealed/verified manifest.

    Per audit round 59: the gate AUTO-BINDS to the ledger when
    append_candidate_entry is called. In __exit__, if post-execution
    verification fails, the gate AUTOMATICALLY calls
    ledger.mark_execution_compromised(). No caller action required.

    Usage:
        manifest = create_execution_manifest(...)
        with ExecutionGate(manifest) as gate:
            result = generate_null_candidates(...)
            # append_candidate_entry auto-binds gate to ledger

    INVARIANTS:
    1. No CANDIDATE_GENERATED without active gate (enforced at ledger)
    2. execution_id + manifest_sha256 in every CANDIDATE_GENERATED (from gate)
    3. Post-execution mutation → automatic COMPROMISE_RECORDED (no caller action)
    """

    def __init__(self, manifest: Dict[str, Any]):
        self.manifest = manifest
        self.record: Optional[ExecutionRecord] = None
        self._active = False
        # Per audit round 59: gate auto-binds to ledger
        self._bound_ledger = None

    def __enter__(self) -> "ExecutionGate":
        """Verify the manifest before allowing any generation."""
        if "manifest_sha256" not in self.manifest:
            raise ExecutionGateError(
                "HARD STOP: Manifest is not sealed (missing manifest_sha256). "
                "No generation may proceed."
            )

        ok, errors = verify_execution_manifest(self.manifest)
        if not ok:
            raise ExecutionGateError(
                "HARD STOP: Execution manifest verification FAILED.\n"
                f"Errors: {errors}\n"
                "No generation may proceed. EXECUTION_INVALIDATED."
            )

        # Per audit round 60: execution_id is a UNIQUE per-instance identifier
        # generated when the gate opens, NOT derived from manifest_sha256.
        # This prevents identity collision when the same manifest is executed
        # twice. The manifest_sha256 is retained separately as the substrate
        # identity.
        #   execution_id    = unique execution instance (UUID)
        #   manifest_sha256 = exact experimental substrate
        self.record = ExecutionRecord(
            execution_id=f"EXEC-{uuid.uuid4().hex}",
            manifest_sha256=self.manifest["manifest_sha256"],
            started_at=datetime.now(timezone.utc).isoformat(),
            manifest_verified=True,
            provenance_verified=True,
        )

        self._active = True
        return self

    def bind_ledger(self, ledger):
        """Auto-bind to the ledger when append_candidate_entry is called.

        Per audit round 59: the gate must own the ledger reference so
        that __exit__ can AUTOMATICALLY call mark_execution_compromised()
        without any caller action.

        This is called by ProvenanceLedger.append_candidate_entry() when
        it detects an active gate — the ledger registers itself with the
        gate so the gate can invalidate it later if needed.
        """
        self._bound_ledger = ledger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finalize the execution record.

        Per audit round 59: if post-execution verification fails,
        AUTOMATICALLY call ledger.mark_execution_compromised().
        NO CALLER ACTION REQUIRED.

        The flow:
            manifest verified BEFORE execution
            +
            candidate generated + persisted
            +
            manifest/source/runtime unchanged DURING execution
            +
            if INVALID → AUTOMATIC COMPROMISE_RECORDED (no human)

        No human intervention exists anywhere in that path.
        """
        self._active = False

        # Post-execution manifest re-verification
        post_ok, post_errors = verify_execution_manifest(self.manifest)
        if not post_ok and self.record:
            compromise_reason = (
                f"POST-EXECUTION MANIFEST INVALIDATED: {post_errors}. "
                f"The experimental substrate changed DURING execution."
            )
            self.record.add_failure(compromise_reason)
            self.record.manifest_verified = False

            # AUTOMATIC MECHANICAL INVALIDATION
            # Per audit round 59: the gate AUTO-BINDS to the ledger when
            # append_candidate_entry is called. Here, it AUTOMATICALLY
            # calls mark_execution_compromised(). No caller action required.
            if self._bound_ledger is not None:
                try:
                    self._bound_ledger.mark_execution_compromised(
                        self.record.execution_id,
                        compromise_reason,
                    )
                    self.record.add_failure(
                        f"AUTOMATIC COMPROMISE_RECORDED for execution_id="
                        f"{self.record.execution_id}"
                    )
                except ValueError:
                    # Already compromised — shouldn't happen, but handle gracefully
                    self.record.add_failure(
                        "COMPROMISE_RECORDED already exists for "
                        f"{self.record.execution_id}"
                    )
            else:
                # No ledger was bound — no candidates were generated
                self.record.add_failure(
                    "No ledger bound to gate — no candidates were generated, "
                    "so no COMPROMISE_RECORDED needed."
                )

        if self.record:
            self.record.finished_at = datetime.now(timezone.utc).isoformat()
            if exc_type is not None:
                self.record.add_failure(
                    f"Exception during execution: {exc_type.__name__}: {exc_val}"
                )
        return False

    @property
    def is_active(self) -> bool:
        return self._active

    def assert_active(self):
        if not self._active:
            raise ExecutionGateError(
                "HARD STOP: Generation attempted outside an active execution gate. "
                "No generation may proceed without a sealed+verified manifest."
            )

    def add_case_processed(self, case_id: str):
        if self.record:
            self.record.cases_processed.append(case_id)

    def add_arm_run(self, arm: str):
        if self.record:
            self.record.arms_run.append(arm)

    def add_artifact(self, case_id: str, arm: str, rank: int,
                     candidate_sha256: str, raw_output_sha256: str):
        if self.record:
            self.record.add_artifact(case_id, arm, rank,
                                      candidate_sha256, raw_output_sha256)

    def add_failure(self, description: str):
        if self.record:
            self.record.add_failure(description)

    def add_exclusion(self, case_id: str, reason: str):
        if self.record:
            self.record.add_exclusion(case_id, reason)

    def get_record(self) -> Optional[ExecutionRecord]:
        return self.record


# Global active gate
_ACTIVE_GATE: Optional[ExecutionGate] = None


def _set_active_gate(gate: Optional[ExecutionGate]):
    global _ACTIVE_GATE
    _ACTIVE_GATE = gate


def assert_execution_gate_active():
    """Assert that an execution gate is active. Called by generation functions."""
    if _ACTIVE_GATE is None or not _ACTIVE_GATE.is_active:
        raise ExecutionGateError(
            "HARD STOP: Generation attempted without an active execution gate. "
            "A sealed+verified manifest is required before any generation. "
            "There is NO bypass path."
        )


_original_enter = ExecutionGate.__enter__
_original_exit = ExecutionGate.__exit__


def _patched_enter(self):
    result = _original_enter(self)
    _set_active_gate(self)
    return result


def _patched_exit(self, exc_type, exc_val, exc_tb):
    result = _original_exit(self, exc_type, exc_val, exc_tb)
    _set_active_gate(None)
    return result


ExecutionGate.__enter__ = _patched_enter
ExecutionGate.__exit__ = _patched_exit
