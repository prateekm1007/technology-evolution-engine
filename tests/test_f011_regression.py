"""
F-011 regression tests: ensure historian/*.json and mode4_constraint_
leverage.json parse as valid JSON.

These files were corrupted at the byte level (same character-per-line
pattern as F-005) since the initial commit 090d3cf. An external audit
discovered them. The fix: salvage by stripping newlines, re-serialize
as clean JSON, and add this regression test so any future corruption
is caught at commit time.

Per the Maestro Loop: this is NOT a feature modification cycle — it's
a critical data-integrity fix that overrides the architecture freeze.
The CTO directed: "I would immediately freeze all additional feature
work until the root cause is understood." The root cause is the same
lost writer that produced F-005 (born outside version control, frozen
into the initial commit). No current code writes these files.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


CORRUPTED_FILES = [
    "data/historian/0001_APRM_historian.json",
    "data/historian/0002_DAM_historian.json",
    "data/historian/0003_ACWPS_historian.json",
    "data/ledger/mode4_constraint_leverage.json",
]


@pytest.mark.parametrize("filepath", CORRUPTED_FILES)
def test_file_parses_as_json(filepath):
    """F-011 regression: every file must parse as valid JSON."""
    f = ROOT / filepath
    assert f.exists(), f"{filepath} missing"
    with open(f) as fh:
        d = json.load(fh)
    assert isinstance(d, dict), f"{filepath} did not parse as a dict"


@pytest.mark.parametrize("filepath", CORRUPTED_FILES)
def test_file_not_corrupted_char_per_line(filepath):
    """F-011 regression: no file should exhibit the character-per-line
    corruption signature (line_count > 100 AND max_line_length < 5)."""
    f = ROOT / filepath
    text = f.read_text()
    lines = text.splitlines()
    non_empty = [ln for ln in lines if ln.strip()]
    if len(non_empty) > 100:
        max_len = max(len(ln) for ln in non_empty)
        assert max_len >= 5, (
            f"F-011 regression: {filepath} has the character-per-line "
            f"corruption signature ({len(non_empty)} non-empty lines, "
            f"max_line_length={max_len})"
        )


def test_historian_files_have_expected_schema():
    """F-011 regression: historian files must have the Historian-
    agent schema keys."""
    for filepath in CORRUPTED_FILES[:3]:  # first 3 are historian files
        f = ROOT / filepath
        d = json.load(open(f))
        for key in ("candidate_id", "technology", "emergence_story",
                     "analogues", "failure_chain"):
            assert key in d, f"{filepath} missing key {key!r}"


def test_mode4_file_has_expected_schema():
    """F-011 regression: mode4_constraint_leverage.json must have
    its expected schema keys."""
    f = ROOT / "data/ledger/mode4_constraint_leverage.json"
    d = json.load(open(f))
    for key in ("analysis_date", "description", "high_leverage_constraints"):
        assert key in d, f"mode4_constraint_leverage.json missing key {key!r}"
