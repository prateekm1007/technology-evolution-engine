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


# ===== TEST 6: Canonical DXP-005 runner matches frozen provider =====

def test_canonical_dxp005_runner_matches_frozen_provider():
    """The canonical scripts/run_dxp005.py must use the preregistered ZAI
    provider, NOT Nemotron/OpenRouter. This is the structural invariant
    the auditor required (round 3):

        "The canonical DXP-005 runner needs to be restored to the actual
         frozen protocol: ZAI, glm-4-plus, z-ai CLI, frozen protocol."

    This test verifies structurally that:
    1. The canonical runner imports ZAIReasoningProvider
    2. The canonical runner does NOT import OpenRouterProvider
    3. The canonical runner does NOT reference Nemotron model names
    4. The canonical runner does NOT read OPENROUTER_API_KEY
    5. The canonical runner does NOT contain the 'protocol amendment' comment
       that justified the provider substitution

    If any of these fail, the canonical runner has drifted from the frozen
    protocol and must be restored.
    """
    canonical_runner = REPO / "scripts" / "run_dxp005.py"
    assert canonical_runner.exists(), "scripts/run_dxp005.py must exist"
    content = canonical_runner.read_text()

    # 1. Must import ZAIReasoningProvider
    assert "ZAIReasoningProvider" in content, (
        "scripts/run_dxp005.py must import ZAIReasoningProvider (the "
        "preregistered provider). Audit finding round 3."
    )

    # 2. Must NOT import OpenRouterProvider (except in comments explaining
    #    what was removed — we allow the word in comments but not as an
    #    actual import)
    # Strip comments for the import check
    import_lines = [line for line in content.split("\n")
                    if line.strip().startswith("from ") or line.strip().startswith("import ")]
    for line in import_lines:
        assert "openrouter" not in line.lower(), (
            f"scripts/run_dxp005.py must NOT import OpenRouterProvider. "
            f"Found import: {line.strip()}. The canonical runner uses ZAI only. "
            f"Audit finding round 3."
        )

    # 3. Must NOT reference Nemotron model names in executable code
    #    (comments explaining what was removed are allowed)
    nemotron_patterns = [
        'nvidia/nemotron',
        'nemotron-3-ultra',
        'nemotron-3-super',
        'nemotron-nano',
    ]
    for pattern in nemotron_patterns:
        # Check if the pattern appears in a non-comment, non-string line
        for line_num, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            # Skip comments
            if stripped.startswith("#"):
                continue
            # Skip docstrings (rough heuristic: lines inside triple quotes)
            # We check if the pattern appears as a string literal
            if pattern in stripped:
                # Allow if it's inside a string (for documentation)
                # but flag if it's in an actual provider config
                if 'model=' in stripped and pattern in stripped:
                    pytest.fail(
                        f"scripts/run_dxp005.py line {line_num} configures a "
                        f"Nemotron model: {stripped}. The canonical runner must "
                        f"use ZAI only. Audit finding round 3."
                    )

    # 4. Must NOT read OPENROUTER_API_KEY
    assert "OPENROUTER_API_KEY" not in content, (
        "scripts/run_dxp005.py must NOT read OPENROUTER_API_KEY. "
        "The canonical runner uses ZAI (z-ai CLI), which does not require "
        "an API key environment variable. Audit finding round 3."
    )

    # 5. Must NOT contain the 'protocol amendment' justification comment
    #    (the old comment said "ZAI API rate-limited (429). Using OpenRouter...")
    assert "Protocol amendment: ZAI API rate-limited" not in content, (
        "scripts/run_dxp005.py must NOT contain the 'Protocol amendment' comment "
        "that justified the Nemotron provider substitution. That substitution "
        "was an Amendment 14 violation and has been reverted. "
        "Audit finding round 3."
    )


# ===== TEST 7: Quarantined runners write only to quarantine namespace =====

def test_quarantined_runners_write_only_to_quarantine_namespace():
    """The quarantined Nemotron pilot runners must write ONLY to the
    quarantine namespace (experiments/dxp005_pilots/nemotron/ENGINE_OUTPUT/),
    never to the primary DXP-005 output directory
    (discovery_experiment/ENGINE_OUTPUT/DXP-005/).

    This is the structural invariant for audit finding B (round 3):
    the output-dir lock must be on the execution path, not just in tests.
    """
    pilot_dir = REPO / "experiments" / "dxp005_pilots" / "nemotron" / "runner_scripts"
    primary_output = "discovery_experiment/ENGINE_OUTPUT/DXP-005"

    # Check all Python runners in the quarantine
    for runner in pilot_dir.glob("run_dxp005*.py"):
        content = runner.read_text()

        # The runner must NOT set OUTPUT_DIR to the primary path
        for line_num, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "OUTPUT_DIR" in stripped and "=" in stripped:
                # Check if this line sets OUTPUT_DIR to the primary path
                if primary_output in stripped:
                    pytest.fail(
                        f"{runner.name} line {line_num} sets OUTPUT_DIR to the "
                        f"primary DXP-005 output path: {stripped}. Quarantined "
                        f"runners must write ONLY to the quarantine namespace. "
                        f"Audit finding B round 3."
                    )

        # The runner must contain assert_output_dir_writable on the execution path
        assert "assert_output_dir_writable" in content, (
            f"{runner.name} must call assert_output_dir_writable() on the "
            f"execution path (not just in tests). Audit finding B round 3."
        )

    # Check the shell script
    sh_runner = pilot_dir / "run_dxp005_all.sh"
    if sh_runner.exists():
        content = sh_runner.read_text()
        # The shell script must NOT reference the primary output path for writing
        # (it can reference it in comments/error messages, but not for OUTPUT_DIR)
        for line_num, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Check for RESULT_FILE or UPSTREAM_HASH pointing to primary output
            if primary_output in stripped and ("RESULT_FILE=" in stripped or "UPSTREAM_HASH=" in stripped):
                pytest.fail(
                    f"{sh_runner.name} line {line_num} references the primary "
                    f"DXP-005 output path: {stripped}. Quarantined runners must "
                    f"write ONLY to the quarantine namespace. Audit finding B round 3."
                )


# ===== TEST 8: DXP-005 runners have zero import-time side effects (round 4) =====

def test_dxp005_runner_no_import_time_side_effects():
    """Importing any DXP-005 runner must perform ZERO experiment-state mutation.

    The auditor found (round 4) that OUTPUT_DIR.mkdir() was called at module
    load time, BEFORE the protocol lock in main(). This means merely importing
    the runner creates the output directory — an experiment-state side effect
    that occurs before authorization is checked.

    The invariant (P21: all-paths trigger rule):
        import runner → zero state mutation

    This test verifies structurally that no DXP-005 runner calls mkdir()
    at module level. The mkdir() must occur only inside main() or a
    function called after the protocol lock.
    """
    # Check the canonical runner
    canonical = REPO / "scripts" / "run_dxp005.py"
    assert canonical.exists()
    _assert_no_module_level_mkdir(canonical)

    # Check the quarantined runners
    pilot_dir = REPO / "experiments" / "dxp005_pilots" / "nemotron" / "runner_scripts"
    if pilot_dir.exists():
        for runner in pilot_dir.glob("run_dxp005*.py"):
            _assert_no_module_level_mkdir(runner)


def _assert_no_module_level_mkdir(runner_path: Path):
    """Verify that the given runner file does not call mkdir() at module level.

    Module-level = any line that is NOT inside a function/class definition
    and NOT a comment.
    """
    import ast
    source = runner_path.read_text()
    tree = ast.parse(source)

    # Walk top-level statements only (not inside function/class defs)
    for node in ast.iter_child_nodes(tree):
        # Skip function and class definitions — their bodies are not module-level
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        # Check for calls to .mkdir() in top-level expressions
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                # Check if it's a method call named "mkdir"
                if isinstance(sub.func, ast.Attribute) and sub.func.attr == "mkdir":
                    pytest.fail(
                        f"{runner_path.name} calls .mkdir() at module level "
                        f"(line {node.lineno}). Importing this module creates "
                        f"the output directory BEFORE the protocol lock runs. "
                        f"This violates P21 (all-paths trigger rule). "
                        f"Move the mkdir() inside main() after the protocol lock. "
                        f"Audit finding round 4."
                    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))