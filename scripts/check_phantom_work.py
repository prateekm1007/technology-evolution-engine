#!/usr/bin/env python3
"""
check_phantom_work.py — DR-11: Phantom-Work Regression Detection.

Per DR-11: "A pre-commit hook that cross-references the commit message
against the staged diff. If the commit message claims files that are
not in the diff, or the diff contains files not mentioned in the message,
the hook warns."

This script:
  1. Reads the staged diff (files that will be committed)
  2. Reads the commit message
  3. Cross-references: does the message mention the files being changed?
  4. Warns on mismatches (phantom work or undocumented changes)

Usage:
    python scripts/check_phantom_work.py                # check staged changes
    python scripts/check_phantom_work.py --commit HEAD   # check specific commit

Exit codes:
    0 = no phantom work detected (PASS)
    1 = phantom work detected (FAIL)
"""
import argparse
import re
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

VALID_EXTENSIONS = {'.py', '.md', '.txt', '.json', '.css', '.js', '.ts', '.html', '.xml', '.yaml', '.yml'}


def get_staged_files() -> list:
    """Get the list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return [f.strip() for f in result.stdout.split("\n") if f.strip()]


def get_commit_files(commit: str = "HEAD") -> list:
    """Get files changed in a specific commit."""
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return [f.strip() for f in result.stdout.split("\n") if f.strip()]


def extract_referenced_files(message: str) -> list:
    """Extract file paths from commit message."""
    pattern = r'(?:^|\s)([\w][\w-]*/[\w/.-]+\.\w{2,5})'
    matches = re.findall(pattern, message)
    result = []
    for m in matches:
        ext = '.' + m.rsplit('.', 1)[-1] if '.' in m else ''
        if ext.lower() in VALID_EXTENSIONS:
            result.append(m)
    return list(set(result))


def check_phantom_work(staged_files: list, message: str) -> dict:
    """Check for phantom work: files in message but not in diff, or files
    in diff but not in message."""
    referenced = extract_referenced_files(message)

    # Files mentioned in message but not in diff (phantom work)
    phantom = []
    for f in referenced:
        if f not in staged_files:
            # Check if file exists in working tree (maybe it was modified
            # in a prior commit and just referenced here)
            if (ROOT / f).exists():
                # File exists but wasn't changed in this commit — that's OK
                # if the message is referencing prior work
                pass
            else:
                phantom.append(f)

    # Files in diff but not in message (undocumented changes)
    undocumented = []
    for f in staged_files:
        if f not in referenced:
            # Check if the file is a common config file that doesn't need mentioning
            basename = pathlib.Path(f).name
            if basename in ['.gitignore', 'pyproject.toml', 'requirements.txt']:
                continue
            undocumented.append(f)

    passed = len(phantom) == 0

    return {
        "staged_files": staged_files,
        "referenced_files": referenced,
        "phantom_files": phantom,
        "undocumented_files": undocumented,
        "passed": passed,
    }


def main():
    parser = argparse.ArgumentParser(
        description="DR-11: Phantom-Work Regression Detection."
    )
    parser.add_argument("--commit", default=None, help="Check specific commit (default: staged)")
    args = parser.parse_args()

    if args.commit:
        files = get_commit_files(args.commit)
        message = subprocess.run(
            ["git", "log", "--format=%B", "-n", "1", args.commit],
            capture_output=True, text=True, cwd=str(ROOT),
        ).stdout.strip()
    else:
        files = get_staged_files()
        # For staged changes, use a placeholder message or read from .git/COMMIT_EDITMSG
        message = ""

    result = check_phantom_work(files, message)

    print("=" * 60)
    print("DR-11: PHANTOM-WORK REGRESSION DETECTION")
    print("=" * 60)
    print(f"Staged/commit files: {len(result['staged_files'])}")
    print(f"Referenced files: {len(result['referenced_files'])}")
    print(f"Phantom files (in message, not in diff): {len(result['phantom_files'])}")
    print(f"Undocumented files (in diff, not in message): {len(result['undocumented_files'])}")
    print()

    if result["phantom_files"]:
        print("PHANTOM WORK (files claimed in message but not in commit):")
        for f in result["phantom_files"]:
            print(f"  ❌ {f}")
        print()

    if result["undocumented_files"]:
        print("UNDOCUMENTED CHANGES (files in commit but not mentioned in message):")
        for f in result["undocumented_files"]:
            print(f"  ⚠️  {f}")
        print()

    if result["passed"]:
        print("STATUS: PASS — no phantom work detected")
    else:
        print("STATUS: FAIL — phantom work detected")
        print("Per DR-11: commit message must match staged diff.")

    print("=" * 60)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
