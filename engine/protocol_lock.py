"""protocol_lock.py — Machine-enforced experiment authorization.

Per external audit (2026-08-08):

    "Do not rely on the coder remembering 'I will not execute it.'
     The repository should enforce:
         DXP-005 PAUSED → runner invoked → HARD FAILURE"

This module provides the machine-enforced protocol lock. Every experiment
runner MUST call `assert_experiment_authorized(experiment_id)` before
doing any work. If the experiment is PAUSED or otherwise not authorized,
the call raises ExperimentNotAuthorized and the runner cannot proceed.

The authorization state is read from PROGRAM_STATE.json (the machine-
generated repository state file). If PROGRAM_STATE.json does not exist
or does not contain the experiment's status, the default is DENY.

Usage in a runner:

    from engine.protocol_lock import assert_experiment_authorized
    assert_experiment_authorized("DXP-005")  # raises if not authorized

The lock is fail-closed (P6: prefer "fail closed and broken" over "fail
open and silent"). If the state file is missing, malformed, or the
experiment is not explicitly AUTHORIZED, the lock denies execution.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional


REPO = Path(__file__).resolve().parents[1]
PROGRAM_STATE_PATH = REPO / "reports" / "program_state" / "PROGRAM_STATE.json"


class ExperimentNotAuthorized(Exception):
    """Raised when an experiment runner is invoked while the experiment
    is not in AUTHORIZED state.

    This is a hard failure. The runner cannot proceed. The error message
    explains why and what would need to change to authorize the experiment.
    """


def _load_program_state() -> dict:
    """Load PROGRAM_STATE.json. Return empty dict if missing or malformed."""
    if not PROGRAM_STATE_PATH.exists():
        return {}
    try:
        return json.loads(PROGRAM_STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def get_experiment_status(experiment_id: str) -> str:
    """Get the authorization status of an experiment.

    Returns one of:
        "AUTHORIZED" — experiment may be executed
        "PAUSED" — experiment is paused, execution prohibited
        "QUARANTINED" — experiment data is quarantined, execution prohibited
        "UNKNOWN" — experiment not found in PROGRAM_STATE.json

    The default for any unknown experiment is "UNKNOWN", which is treated
    as NOT authorized (fail-closed).
    """
    state = _load_program_state()

    # Normalize experiment_id for comparison
    eid = experiment_id.upper().replace("_", "-")

    # Check DXP-005
    if eid == "DXP-005":
        dxp = state.get("dxp005", {})
        status = dxp.get("status", "UNKNOWN").upper()
        if status == "PAUSED":
            return "PAUSED"
        if status == "AUTHORIZED":
            return "AUTHORIZED"
        return "UNKNOWN"

    # Check quarantined pilots
    for pilot in state.get("unregistered_pilots", []):
        pid = pilot.get("id", "").upper().replace("_", "-")
        if pid == eid:
            return "QUARANTINED"

    return "UNKNOWN"


def assert_experiment_authorized(experiment_id: str) -> None:
    """Assert that an experiment is authorized for execution.

    Raises ExperimentNotAuthorized if the experiment is not in AUTHORIZED
    state. This is the machine-enforced protocol lock.

    Every experiment runner MUST call this at the top of main() before
    doing any work. The lock is fail-closed: missing state file, unknown
    experiment, paused experiment, or quarantined pilot all raise.
    """
    status = get_experiment_status(experiment_id)

    if status == "AUTHORIZED":
        return  # Execution permitted

    # Build a descriptive error message
    state = _load_program_state()
    eid_display = experiment_id.upper()

    if status == "PAUSED":
        dxp = state.get("dxp005", {})
        reason = dxp.get("pause_reason", "UNKNOWN")
        resume_conditions = dxp.get("resume_conditions", [])
        msg = (
            f"EXPERIMENT NOT AUTHORIZED: {eid_display} is PAUSED.\n"
            f"  pause_reason: {reason}\n"
            f"  resume_conditions: {resume_conditions}\n"
            f"  preregistered_provider: {dxp.get('preregistered_provider', 'UNKNOWN')}\n"
            f"  valid_scientific_runs: {dxp.get('valid_scientific_runs', 0)}\n\n"
            f"This is a machine-enforced protocol lock (engine/protocol_lock.py). "
            f"The experiment cannot be executed while PAUSED. To resume, all "
            f"resume_conditions must be met AND PROGRAM_STATE.json must be "
            f"updated to status=AUTHORIZED by an authorized operator."
        )
    elif status == "QUARANTINED":
        msg = (
            f"EXPERIMENT NOT AUTHORIZED: {eid_display} is QUARANTINED.\n"
            f"  This experiment's data has been quarantined as an "
            f"unpreregistered exploratory pilot.\n"
            f"  valid_for_primary_analysis: false\n\n"
            f"This is a machine-enforced protocol lock. Quarantined pilots "
            f"cannot be re-executed under their parent protocol. A new "
            f"experiment (e.g., {eid_display}b) must be separately "
            f"preregistered if execution is desired."
        )
    else:  # UNKNOWN
        msg = (
            f"EXPERIMENT NOT AUTHORIZED: {eid_display} is UNKNOWN.\n"
            f"  PROGRAM_STATE.json does not contain an AUTHORIZED status for "
            f"this experiment.\n"
            f"  state_file: {PROGRAM_STATE_PATH}\n\n"
            f"This is a machine-enforced protocol lock (fail-closed). Unknown "
            f"experiments cannot be executed. If this is a new experiment, it "
            f"must be preregistered and added to PROGRAM_STATE.json with "
            f"status=AUTHORIZED before execution."
        )

    raise ExperimentNotAuthorized(msg)


def assert_output_dir_writable(experiment_id: str, output_path: Path) -> None:
    """Assert that writing to an experiment's output directory is permitted.

    This prevents quarantined pilots from writing to the primary experiment's
    output directory (audit finding: 'nemotron pilot cannot write to dxp005
    output').

    For DXP-005 (PAUSED): the primary output directory is locked.
    For quarantined pilots: they may only write to their own quarantine dir.
    """
    eid = experiment_id.upper().replace("_", "-")
    output_str = str(output_path)

    # DXP-005 primary output directory is locked while PAUSED
    if eid == "DXP-005":
        status = get_experiment_status("DXP-005")
        if status != "AUTHORIZED":
            # The canonical DXP-005 output path
            dxp_output = str(REPO / "discovery_experiment" / "ENGINE_OUTPUT" / "DXP-005")
            if dxp_output in output_str or output_str.startswith(dxp_output):
                raise ExperimentNotAuthorized(
                    f"OUTPUT DIRECTORY LOCKED: {output_path}\n"
                    f"  DXP-005 is {status}. Writing to the primary DXP-005 "
                    f"output directory is prohibited while the experiment is "
                    f"not AUTHORIZED.\n"
                    f"  Quarantined pilots must write to their own directory "
                    f"under experiments/dxp005_pilots/."
                )

    # Quarantined pilots may only write to their quarantine directory
    if eid.startswith("DXP005-NEMOTRON") or eid.startswith("DXP-005-NEMOTRON"):
        quarantine_dir = str(REPO / "experiments" / "dxp005_pilots" / "nemotron")
        if quarantine_dir not in output_str and not output_str.startswith(quarantine_dir):
            raise ExperimentNotAuthorized(
                f"OUTPUT DIRECTORY VIOLATION: {output_path}\n"
                f"  Quarantined pilot {eid} may only write to {quarantine_dir}\n"
                f"  Attempted to write to: {output_str}\n"
                f"  Quarantined pilots cannot write to the primary experiment "
                f"output directory."
            )


__all__ = [
    "ExperimentNotAuthorized",
    "get_experiment_status",
    "assert_experiment_authorized",
    "assert_output_dir_writable",
]


if __name__ == "__main__":
    # CLI: python3 -m engine.protocol_lock <experiment_id>
    # Exits 0 if authorized, 1 if not.
    if len(sys.argv) < 2:
        print("Usage: python3 -m engine.protocol_lock <experiment_id>")
        sys.exit(2)
    eid = sys.argv[1]
    try:
        assert_experiment_authorized(eid)
        print(f"AUTHORIZED: {eid}")
        sys.exit(0)
    except ExperimentNotAuthorized as e:
        print(f"NOT AUTHORIZED: {eid}")
        print(str(e))
        sys.exit(1)
