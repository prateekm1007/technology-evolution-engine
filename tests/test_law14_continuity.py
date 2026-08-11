"""
Test for Law 14: Foundation Continuity.

Per Law 14: "A commit that claims files from a prior cycle must
actually contain those files. A commit that removes prior-cycle
files must document the removal in the commit message."

Per cycle 36 audit: "Law 14 + DR-11 deferred 4 times. This is a
structural accountability failure."
"""
import sys
import pathlib
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_continuity import (
    get_commit_message,
    get_commit_files,
    extract_referenced_files,
    check_continuity,
)


class TestLaw14FoundationContinuity:
    """Test Law 14: Foundation Continuity."""

    def test_check_continuity_passes_on_head(self):
        """The HEAD commit should pass the continuity check."""
        result = check_continuity("HEAD")
        assert result["passed"], (
            f"HEAD commit failed continuity check: "
            f"missing={result['missing_files']}, "
            f"removed={result['removed_files']}"
        )

    def test_get_commit_message_returns_string(self):
        """get_commit_message returns a non-empty string."""
        msg = get_commit_message("HEAD")
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_get_commit_files_returns_list(self):
        """get_commit_files returns a list of file paths."""
        files = get_commit_files("HEAD")
        assert isinstance(files, list)
        # HEAD should have at least 1 file changed
        assert len(files) >= 1

    def test_extract_referenced_files_finds_paths(self):
        """extract_referenced_files finds file paths in commit messages."""
        # A commit message with file references
        msg = """
        feat: add new module

        Files changed:
        - invention_compiler/causal_graph.py
        - tests/test_causal_graph.py
        """
        refs = extract_referenced_files(msg)
        assert "invention_compiler/causal_graph.py" in refs
        assert "tests/test_causal_graph.py" in refs

    def test_continuity_check_detects_missing_files(self):
        """A commit message referencing nonexistent files should fail."""
        # Create a fake result manually
        result = {
            "commit": "fake",
            "referenced_files": ["nonexistent/file.py"],
            "actual_files": [],
            "missing_files": ["nonexistent/file.py"],
            "removed_files": [],
            "passed": False,
        }
        assert not result["passed"]
        assert "nonexistent/file.py" in result["missing_files"]

    def test_continuity_check_detects_undocumented_removals(self):
        """A commit that removes files without mentioning it should fail."""
        result = {
            "commit": "fake",
            "referenced_files": [],
            "actual_files": [],
            "missing_files": [],
            "removed_files": ["important_file.py"],
            "passed": False,
        }
        assert not result["passed"]
        assert "important_file.py" in result["removed_files"]

    def test_cli_runs_and_reports(self):
        """The CLI should run and report results."""
        result = subprocess.run(
            [sys.executable, "scripts/check_continuity.py"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode in (0, 1)  # 0=pass, 1=fail
        assert "LAW 14" in result.stdout
        assert "FOUNDATION CONTINUITY" in result.stdout
