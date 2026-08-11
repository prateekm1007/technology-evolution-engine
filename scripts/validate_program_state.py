#!/usr/bin/env python3
"""validate_program_state.py — Validate PROGRAM_STATE.json against actual repo state.

Per external audit finding D (2026-08-08):

    "A machine-generated state document is currently reporting a repository
     state that demonstrably predates the commit it lives in. That
     invalidates it as an authoritative snapshot."

    "Create a validator: validate_program_state.py that fails if
     described repository state != actual described commit."

This validator independently verifies:

1. SELF-REFERENCE: PROGRAM_STATE.json's `describes_commit` must equal
   `git rev-parse HEAD~1` (the parent of the commit containing this file).
   This breaks the circular dependency — the file describes its parent
   commit, not itself.

2. PHASE STATUS INTEGRITY: No phase status file may have
   `commit = "pending"` or `commit = "UNKNOWN"`. A COMPLETE phase must
   have a real commit SHA.

3. DXP-005 LOCK CONSISTENCY: If PROGRAM_STATE.json says DXP-005 is PAUSED,
   the protocol lock must deny execution.

4. QUARANTINE CONSISTENCY: All unregistered pilots must have
   `valid_for_primary_analysis = false`.

5. WORKING TREE HONESTY: The working_tree field must match actual
   `git status --porcelain` output.

Exit codes:
  0 = VALID
  1 = INVALID (validation failed)
  2 = ERROR (could not perform validation)

Usage:
  python3 scripts/validate_program_state.py
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # so 'engine' module is importable
STATE_PATH = REPO / "reports" / "program_state" / "PROGRAM_STATE.json"


def git(args, cwd=REPO):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def fail(msg):
    print(f"INVALID: {msg}", file=sys.stderr)
    return 1


def main():
    if not STATE_PATH.exists():
        return fail(f"PROGRAM_STATE.json not found at {STATE_PATH}")

    try:
        state = json.loads(STATE_PATH.read_text())
    except json.JSONDecodeError as e:
        return fail(f"PROGRAM_STATE.json is not valid JSON: {e}")

    errors = []

    # ===== CHECK 1: Self-reference (parent-commit convention) =====
    describes_commit = state.get("state_snapshot", {}).get("describes_commit")
    if not describes_commit:
        errors.append("state_snapshot.describes_commit is missing")
    else:
        # The file describes its parent commit (HEAD~1), not itself.
        # This is because the file cannot truthfully contain its own SHA
        # (it didn't exist when the commit was created).
        head_parent = git(["rev-parse", "HEAD~1"])
        head = git(["rev-parse", "HEAD"])
        if not head or not head_parent:
            errors.append(f"cannot determine HEAD or HEAD~1")
        elif describes_commit == head:
            # describes_commit == HEAD means the file was generated but
            # not yet committed (or was committed without regeneration).
            # This is the stale state the auditor found.
            errors.append(
                f"state_snapshot.describes_commit ({describes_commit[:12]}) == HEAD. "
                f"The file describes the current commit, but it lives IN that commit. "
                f"This is the self-reference problem. The file is stale. "
                f"Regenerate with generate_program_state.py and recommit."
            )
        elif describes_commit != head_parent:
            errors.append(
                f"state_snapshot.describes_commit ({describes_commit[:12]}) != "
                f"HEAD~1 ({head_parent[:12] if head_parent else 'UNKNOWN'}). "
                f"The file describes a commit that is not the parent of the current HEAD. "
                f"Either the file is stale, or HEAD has advanced without regeneration. "
                f"Regenerate with generate_program_state.py and recommit."
            )
        # If describes_commit == head_parent, this check PASSES.

    # ===== CHECK 2: Phase status commit integrity =====
    for phase_key in ["phase_0", "phase_1", "phase_2", "phase_3"]:
        phase = state.get(phase_key)
        if phase is None:
            continue  # phase not yet started
        if phase.get("status") == "COMPLETE":
            commit = phase.get("commit", "")
            if commit in ("pending", "UNKNOWN", "", "INVALID_PENDING_OR_UNKNOWN"):
                errors.append(
                    f"{phase_key}.status=COMPLETE but commit={repr(commit)}. "
                    f"A COMPLETE phase must have a real commit SHA. "
                    f"This is internally contradictory (audit finding C)."
                )

    # ===== CHECK 3: DXP-005 lock consistency =====
    dxp = state.get("dxp005", {})
    dxp_status = dxp.get("status", "UNKNOWN")
    if dxp_status == "PAUSED":
        # Verify the protocol lock denies execution
        from engine.protocol_lock import get_experiment_status
        lock_status = get_experiment_status("DXP-005")
        if lock_status != "PAUSED":
            errors.append(
                f"dxp005.status=PAUSED in PROGRAM_STATE.json but protocol_lock "
                f"returns {repr(lock_status)}. The lock must be consistent with "
                f"the state file."
            )

    # ===== CHECK 4: Quarantine consistency =====
    for pilot in state.get("unregistered_pilots", []):
        if pilot.get("valid_for_primary_analysis") is not False:
            errors.append(
                f"unregistered_pilot {pilot.get('id')} has "
                f"valid_for_primary_analysis={pilot.get('valid_for_primary_analysis')}. "
                f"All unregistered pilots must have valid_for_primary_analysis=false."
            )

    # ===== CHECK 5: Working tree honesty (tightened, audit finding D round 3) =====
    # The auditor flagged the previous >50 tolerance as too permissive. The
    # state file describes a parent commit, so the working tree at validation
    # time may differ from the working tree at generation time. We separate
    # two concerns:
    #
    # 1. state_at_described_commit: the working_tree field records the state
    #    AS OF the described commit. This is historical and should match
    #    exactly what `git status --porcelain` showed at generation time.
    #    We cannot re-verify this exactly (the working tree has moved on),
    #    but we record it for audit trail.
    #
    # 2. working_tree_at_validation: the current working tree state. This
    #    is what we check now. If the file claims working_tree_clean=true
    #    but the tree is dirty, that's a contradiction. If the file claims
    #    a specific dirty count, we allow small drift (working tree changes
    #    between generation and validation) but reject large discrepancies.
    #
    # The tolerance is now ZERO for the clean/dirty boundary and TIGHT
    # (≤5) for the count. The previous >50 tolerance was too permissive.
    wt = state.get("working_tree", {})
    if wt:
        actual_dirty = git(["status", "--porcelain"])
        actual_count = len(actual_dirty.split("\n")) if actual_dirty else 0
        recorded_total = wt.get("total_dirty", -1)
        recorded_clean = wt.get("working_tree_clean", None)

        # Check 5a: clean/dirty boundary must be exact
        actual_clean = (actual_count == 0)
        if recorded_clean is not None and recorded_clean != actual_clean:
            errors.append(
                f"working_tree.working_tree_clean={recorded_clean} but actual "
                f"clean state is {actual_clean} (actual dirty count={actual_count}). "
                f"The clean/dirty boundary must be exact. The state file claims "
                f"the tree is {'clean' if recorded_clean else 'dirty'} but reality "
                f"is {'clean' if actual_clean else 'dirty'}. "
                f"Regenerate with generate_program_state.py."
            )

        # Check 5b: dirty count must be within 5 (tight tolerance)
        # The working tree may change slightly between generation and validation
        # (e.g., new untracked files, minor edits), but large discrepancies
        # indicate staleness.
        if recorded_total >= 0 and abs(actual_count - recorded_total) > 5:
            errors.append(
                f"working_tree.total_dirty={recorded_total} but actual dirty "
                f"count is {actual_count}. Difference > 5 suggests the file "
                f"is stale (tightened from >50 per audit finding D round 3). "
                f"Regenerate with generate_program_state.py."
            )

    # ===== REPORT =====
    if errors:
        print("INVALID: PROGRAM_STATE.json has consistency errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("VALID: PROGRAM_STATE.json is consistent with actual repository state.")
    print(f"  describes_commit: {describes_commit[:12] if describes_commit else 'MISSING'}")
    print(f"  dxp005.status: {dxp_status}")
    print(f"  unregistered_pilots: {len(state.get('unregistered_pilots', []))}")
    print(f"  north_star: {state.get('north_star', 'UNKNOWN')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
