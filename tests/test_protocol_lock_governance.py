"""Repository-level protocol lock tests (audit finding E, 2026-08-08).

The auditor specified 5 tests:
  1. test_dxp005_cannot_execute_while_paused
  2. test_nemotron_pilot_cannot_write_to_dxp005_output
  3. test_quarantined_pilot_excluded_from_primary_analysis
  4. test_program_state_matches_repository_snapshot
  5. test_phase_status_commit_is_not_pending

These are governance tests, not unit tests. They verify that the
repository is physically incapable of violating the rules it claims
to enforce.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.protocol_lock import (
    ExperimentNotAuthorized,
    get_experiment_status,
    assert_experiment_authorized,
    assert_output_dir_writable,
)


REPO = Path(__file__).resolve().parents[1]


# ===== TEST 1: DXP-005 cannot execute while PAUSED =====

def test_dxp005_cannot_execute_while_paused():
    """The protocol lock must deny DXP-005 execution while PROGRAM_STATE.json
    says status=PAUSED. This is the machine-enforced prohibition — not a
    documentary one.
    """
    status = get_experiment_status("DXP-005")
    assert status == "PAUSED", (
        f"DXP-005 status should be PAUSED (PROGRAM_STATE.json says so), "
        f"got {repr(status)}. If DXP-005 is no longer PAUSED, update "
        f"PROGRAM_STATE.json and this test."
    )

    with pytest.raises(ExperimentNotAuthorized, match="DXP-005 is PAUSED"):
        assert_experiment_authorized("DXP-005")


# ===== TEST 2: Nemotron pilot cannot write to DXP-005 output =====

def test_nemotron_pilot_cannot_write_to_dxp005_output():
    """A quarantined pilot must not be able to write to the primary DXP-005
    output directory. The output directory lock must prevent this.
    """
    dxp005_output = REPO / "discovery_experiment" / "ENGINE_OUTPUT" / "DXP-005"
    with pytest.raises(ExperimentNotAuthorized, match="OUTPUT DIRECTORY LOCKED"):
        assert_output_dir_writable("DXP-005", dxp005_output)


def test_nemotron_pilot_restricted_to_quarantine_dir():
    """A Nemotron pilot may only write to its own quarantine directory."""
    quarantine_dir = REPO / "experiments" / "dxp005_pilots" / "nemotron"
    # Should NOT raise — writing to quarantine dir is allowed
    assert_output_dir_writable("DXP005-NEMOTRON-PILOT", quarantine_dir / "test.json")

    # Should raise — writing outside quarantine dir is denied
    with pytest.raises(ExperimentNotAuthorized, match="OUTPUT DIRECTORY VIOLATION"):
        assert_output_dir_writable("DXP005-NEMOTRON-PILOT", REPO / "discovery_experiment" / "ENGINE_OUTPUT")


# ===== TEST 3: Quarantined pilot excluded from primary analysis =====

def test_quarantined_pilot_excluded_from_primary_analysis():
    """The Nemotron pilot must be marked valid_for_primary_analysis=false
    in both PROGRAM_STATE.json and the QUARANTINE_MANIFEST.json.
    """
    state_path = REPO / "reports" / "program_state" / "PROGRAM_STATE.json"
    assert state_path.exists(), "PROGRAM_STATE.json must exist"

    state = json.loads(state_path.read_text())
    pilots = state.get("unregistered_pilots", [])
    assert len(pilots) >= 1, "At least 1 quarantined pilot should be recorded"

    nemotron_pilot = None
    for p in pilots:
        if "NEMOTRON" in p.get("id", "").upper():
            nemotron_pilot = p
            break

    assert nemotron_pilot is not None, "Nemotron pilot must be in unregistered_pilots"
    assert nemotron_pilot["valid_for_primary_analysis"] is False, (
        "Nemotron pilot must have valid_for_primary_analysis=false"
    )

    # Also check the QUARANTINE_MANIFEST.json
    manifest_path = REPO / "experiments" / "dxp005_pilots" / "nemotron" / "QUARANTINE_MANIFEST.json"
    assert manifest_path.exists(), "QUARANTINE_MANIFEST.json must exist"
    manifest = json.loads(manifest_path.read_text())
    qm = manifest.get("quarantine_manifest", {})
    assert qm.get("valid_for_dxp005_primary_analysis") is False, (
        "QUARANTINE_MANIFEST must have valid_for_dxp005_primary_analysis=false"
    )
    assert qm.get("valid_for_hgen1_evaluation") is False, (
        "QUARANTINE_MANIFEST must have valid_for_hgen1_evaluation=false"
    )


# ===== TEST 4: PROGRAM_STATE matches repository snapshot =====

def test_program_state_matches_repository_snapshot():
    """PROGRAM_STATE.json must be consistent with actual repository state.
    This test runs the validator script and requires it to pass.

    Per audit finding D: 'A machine-generated state document is currently
    reporting a repository state that demonstrably predates the commit
    it lives in. That invalidates it as an authoritative snapshot.'
    """
    validator = REPO / "scripts" / "validate_program_state.py"
    assert validator.exists(), "validate_program_state.py must exist"

    result = subprocess.run(
        ["python3", str(validator)],
        cwd=REPO, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"validate_program_state.py FAILED (exit {result.returncode}):\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}\n"
        f"PROGRAM_STATE.json is not consistent with repository state. "
        f"Run scripts/generate_program_state.py and recommit."
    )


# ===== TEST 5: Phase status commit is not pending =====

def test_phase_status_commit_is_not_pending():
    """No COMPLETE phase status file may have commit='pending' or 'UNKNOWN'.
    A COMPLETE phase must have a real commit SHA. This is the internal
    consistency check per audit finding C.
    """
    disc_dir = REPO / "experiments" / "measurement_discrimination"
    for phase_num in range(10):
        phase_file = disc_dir / f"PHASE_STATUS_phase{phase_num}.json"
        if not phase_file.exists():
            continue
        data = json.loads(phase_file.read_text())
        status = data.get("status", "UNKNOWN")
        commit = data.get("commit", "UNKNOWN")
        if status == "COMPLETE":
            assert commit not in ("pending", "UNKNOWN", "", None), (
                f"PHASE_STATUS_phase{phase_num}.json has status=COMPLETE but "
                f"commit={repr(commit)}. A COMPLETE phase must have a real "
                f"commit SHA (audit finding C)."
            )
            # Verify the commit actually exists in git history
            git_check = subprocess.run(
                ["git", "cat-file", "-t", commit],
                cwd=REPO, capture_output=True, text=True, timeout=5,
            )
            assert git_check.returncode == 0 and git_check.stdout.strip() == "commit", (
                f"PHASE_STATUS_phase{phase_num}.json commit {commit} does not "
                f"exist in git history. The commit field must reference a real commit."
            )


# ===== BONUS TEST: All DXP-005 runners contain the protocol lock =====

def test_all_dxp005_runners_have_protocol_lock():
    """Every DXP-005 runner script must contain the protocol lock check.
    This ensures no runner can bypass the machine-enforced prohibition.
    """
    # The frozen runner in scripts/
    frozen_runner = REPO / "scripts" / "run_dxp005.py"
    assert frozen_runner.exists(), "scripts/run_dxp005.py must exist (frozen runner)"
    content = frozen_runner.read_text()
    assert "assert_experiment_authorized" in content, (
        "scripts/run_dxp005.py must contain the protocol lock call "
        "(assert_experiment_authorized). Audit finding A."
    )

    # The quarantined runner scripts
    pilot_dir = REPO / "experiments" / "dxp005_pilots" / "nemotron" / "runner_scripts"
    if pilot_dir.exists():
        for runner in pilot_dir.glob("run_dxp005*.py"):
            content = runner.read_text()
            assert "assert_experiment_authorized" in content, (
                f"{runner} must contain the protocol lock call. "
                f"Even quarantined runners must be locked (audit finding A)."
            )
        # Check the shell script too
        sh_runner = pilot_dir / "run_dxp005_all.sh"
        if sh_runner.exists():
            content = sh_runner.read_text()
            assert "protocol_lock" in content, (
                f"{sh_runner} must invoke the protocol lock. "
                f"Audit finding A."
            )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
