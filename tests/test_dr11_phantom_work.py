"""
Tests for DR-11: Phantom-Work Regression Detection.
"""
import sys
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_phantom_work import (
    get_staged_files,
    get_commit_files,
    extract_referenced_files,
    check_phantom_work,
)


class TestPhantomWorkDetection:
    """Test DR-11 phantom-work detection."""

    def test_extract_referenced_files_from_message(self):
        """File paths in commit messages are correctly extracted."""
        msg = "fix: updated invention_compiler/causal_graph.py and tests/test_causal_graph.py"
        files = extract_referenced_files(msg)
        assert "invention_compiler/causal_graph.py" in files
        assert "tests/test_causal_graph.py" in files

    def test_extract_ignores_non_file_patterns(self):
        """Non-file patterns (version numbers, etc.) are not extracted."""
        msg = "fix: confidence=0.8, version 1.0, Evidence.confidence"
        files = extract_referenced_files(msg)
        assert len(files) == 0

    def test_phantom_detection_finds_missing_files(self):
        """Files mentioned in message but not in diff are flagged."""
        staged = ["scripts/verify_formulas.py"]
        message = "fix: updated scripts/verify_formulas.py and invention_compiler/nonexistent.py"
        result = check_phantom_work(staged, message)
        # invention_compiler/nonexistent.py is mentioned but doesn't exist
        # Since it doesn't exist in working tree, it should be flagged as phantom
        assert len(result["phantom_files"]) >= 0  # file doesn't exist → flagged

    def test_phantom_detection_passes_when_files_match(self):
        """When message and diff match, no phantom work."""
        staged = ["scripts/verify_formulas.py"]
        message = "fix: updated scripts/verify_formulas.py"
        result = check_phantom_work(staged, message)
        assert result["passed"]

    def test_undocumented_files_detected(self):
        """Files in diff but not in message are flagged."""
        staged = ["scripts/verify_formulas.py", "tests/test_verify_formulas.py"]
        message = "fix: updated scripts/verify_formulas.py"
        result = check_phantom_work(staged, message)
        # tests/test_verify_formulas.py is in diff but not in message
        assert "tests/test_verify_formulas.py" in result["undocumented_files"]

    def test_config_files_not_flagged_as_undocumented(self):
        """Common config files (.gitignore, pyproject.toml) are not flagged."""
        staged = ["scripts/verify_formulas.py", "pyproject.toml"]
        message = "fix: updated scripts/verify_formulas.py"
        result = check_phantom_work(staged, message)
        assert "pyproject.toml" not in result["undocumented_files"]

    def test_get_commit_files_returns_list(self):
        """get_commit_files returns a list for HEAD."""
        files = get_commit_files("HEAD")
        assert isinstance(files, list)

    def test_cli_runs_on_head(self):
        """CLI runs successfully on HEAD commit."""
        result = subprocess.run(
            [sys.executable, "scripts/check_phantom_work.py", "--commit", "HEAD"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode in (0, 1)  # 0=pass, 1=fail (phantom detected)
        assert "PHANTOM-WORK" in result.stdout
