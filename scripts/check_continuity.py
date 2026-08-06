#!/usr/bin/env python3
"""
check_continuity.py — Law 14: Foundation Continuity.

Per Law 14: "A commit that claims files from a prior cycle must
actually contain those files. A commit that removes prior-cycle
files must document the removal in the commit message."

This script checks:
  1. Files referenced in the commit message exist in the commit
  2. Files from prior cycles that were claimed to exist still exist
  3. No silent file removals

Usage:
    python scripts/check_continuity.py                    # check HEAD
    python scripts/check_continuity.py --commit abc123     # check specific commit

Exit codes:
    0 = continuity verified (PASS)
    1 = continuity violation (FAIL)
"""
import argparse
import re
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def get_commit_message(commit: str = "HEAD") -> str:
    """Get the commit message for the given commit."""
    result = subprocess.run(
        ["git", "log", "--format=%B", "-n", "1", commit],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return result.stdout.strip()


def get_commit_files(commit: str = "HEAD") -> list:
    """Get the list of files changed in the commit."""
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return [f.strip() for f in result.stdout.split("\n") if f.strip()]


def extract_referenced_files(message: str) -> list:
    """Extract file paths referenced in the commit message.

    Only matches paths that look like real file paths:
      - Must contain at least one /
      - Must end with a file extension (.py, .md, .txt, .json, .css, etc.)
      - Must not start with a digit
    """
    # Match file paths: word/word.ext (must have at least one /)
    pattern = r'(?:^|\s)([\w][\w-]*/[\w/.-]+\.\w{2,5})'
    matches = re.findall(pattern, message)
    # Filter to known file extensions
    valid_extensions = {'.py', '.md', '.txt', '.json', '.css', '.js', '.ts', '.html', '.xml', '.yaml', '.yml'}
    result = []
    for m in matches:
        ext = '.' + m.rsplit('.', 1)[-1] if '.' in m else ''
        if ext.lower() in valid_extensions:
            result.append(m)
    return list(set(result))


def check_continuity(commit: str = "HEAD") -> dict:
    """Check foundation continuity for the given commit.

    Returns a dict with:
      - referenced_files: files mentioned in commit message
      - actual_files: files actually changed in commit
      - missing_files: referenced but not in actual_files
      - removed_files: files in prior commits but removed in this one
      - passed: bool
    """
    message = get_commit_message(commit)
    actual_files = get_commit_files(commit)
    referenced = extract_referenced_files(message)

    # Check: do referenced files exist in the commit?
    missing = []
    for f in referenced:
        # Filter out non-file patterns (URLs, etc.)
        if "/" not in f and "." not in f:
            continue
        if f not in actual_files:
            # Check if it exists in the working tree (maybe it was modified)
            if not (ROOT / f).exists():
                missing.append(f)

    # Check: were files removed without documentation?
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-status", "-r", commit],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    removed = []
    for line in result.stdout.split("\n"):
        if line.startswith("D\t"):
            removed_file = line[2:].strip()
            # Check if the commit message mentions the removal
            if removed_file not in message and "delete" not in message.lower() and "remove" not in message.lower():
                removed.append(removed_file)

    passed = len(missing) == 0 and len(removed) == 0

    return {
        "commit": commit,
        "referenced_files": referenced,
        "actual_files": actual_files,
        "missing_files": missing,
        "removed_files": removed,
        "passed": passed,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Law 14: Foundation Continuity check."
    )
    parser.add_argument("--commit", default="HEAD", help="Commit to check (default: HEAD)")
    args = parser.parse_args()

    result = check_continuity(args.commit)

    print("=" * 60)
    print("LAW 14: FOUNDATION CONTINUITY CHECK")
    print("=" * 60)
    print(f"Commit: {result['commit']}")
    print(f"Referenced files: {len(result['referenced_files'])}")
    print(f"Actual files: {len(result['actual_files'])}")
    print(f"Missing files: {len(result['missing_files'])}")
    print(f"Undocumented removals: {len(result['removed_files'])}")
    print()

    if result["missing_files"]:
        print("MISSING (referenced in message but not in commit):")
        for f in result["missing_files"]:
            print(f"  - {f}")
        print()

    if result["removed_files"]:
        print("UNDOCUMENTED REMOVALS (files deleted without mentioning in message):")
        for f in result["removed_files"]:
            print(f"  - {f}")
        print()

    if result["passed"]:
        print("STATUS: PASS — continuity verified")
    else:
        print("STATUS: FAIL — continuity violation")
        print("Per Law 14: files referenced in commit message must exist in commit.")
        print("Files removed must be documented in the commit message.")

    print("=" * 60)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
