"""
Tests for the prose-consistency linter (DR-9 / F-053).

Per F-053 (FAILURES.md): the vaccine fridge package stated "ESTIMATE
count: 3" but listed 4 items in the parenthetical. This linter catches
that contradiction mechanically.

Tests verify:
  1. count_colon pattern: "count: N (items)" checks len(items) == N
  2. N_of_M pattern: "N of M lines are X" checks against BOM table
  3. The linter catches the exact F-053 contradiction
  4. The linter passes when counts are correct
  5. CLI exit codes (0 on PASS, 1 on FAIL)
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verify_prose_consistency import (
    extract_count_assertions,
    extract_bom_basis_counts,
    check_assertions,
)


# ----------------------------------------------------------------------
# 1. count_colon pattern extraction
# ----------------------------------------------------------------------

def test_count_colon_pattern_extracted():
    """The 'count: N (items)' pattern is extracted correctly."""
    text = "ESTIMATE count: 3 (BL-003, BL-007, BL-009, BL-011)."
    assertions = extract_count_assertions(text)
    assert len(assertions) == 1
    a = assertions[0]
    assert a.pattern_type == "count_colon"
    assert a.asserted_count == 3
    assert len(a.actual_list) == 4  # 4 items in parenthetical
    assert "BL-003" in a.actual_list
    assert "BL-011" in a.actual_list


def test_count_colon_with_correct_count_passes():
    """When count matches len(items), the assertion passes."""
    text = "ESTIMATE count: 4 (BL-003, BL-007, BL-009, BL-011)."
    assertions = extract_count_assertions(text)
    bom_counts = {"ESTIMATED": 4, "QUOTED": 3, "CATALOG": 4}
    results = check_assertions(assertions, bom_counts)
    assert len(results) == 1
    a, passed, msg = results[0]
    assert passed is True
    assert "MATCH" in msg


def test_count_colon_with_wrong_count_fails():
    """When count != len(items), the assertion fails (F-053 scenario)."""
    # This is the exact F-053 contradiction: count says 3, but 4 items listed
    text = "ESTIMATE count: 3 (BL-003, BL-007, BL-009, BL-011)."
    assertions = extract_count_assertions(text)
    bom_counts = {"ESTIMATED": 4, "QUOTED": 3, "CATALOG": 4}
    results = check_assertions(assertions, bom_counts)
    assert len(results) == 1
    a, passed, msg = results[0]
    assert passed is False
    assert "Asserted=3" in msg
    assert "Actual=4" in msg


def test_count_colon_with_single_item():
    """count: 1 with 1 item in parenthetical passes."""
    text = "QUOTED count: 1 (BL-001)."
    assertions = extract_count_assertions(text)
    assert len(assertions) == 1
    assert assertions[0].asserted_count == 1
    assert len(assertions[0].actual_list) == 1


# ----------------------------------------------------------------------
# 2. N_of_M pattern extraction
# ----------------------------------------------------------------------

def test_n_of_m_pattern_extracted():
    """The 'N of M lines are X' pattern is extracted."""
    text = "4 of 11 lines are ESTIMATED."
    assertions = extract_count_assertions(text)
    assert len(assertions) == 1
    a = assertions[0]
    assert a.pattern_type == "N_of_M"
    assert a.asserted_count == 4


def test_n_of_m_checked_against_bom():
    """'4 of 11 lines are ESTIMATED' is checked against BOM basis count."""
    text = "4 of 11 lines are ESTIMATED."
    assertions = extract_count_assertions(text)
    bom_counts = {"ESTIMATED": 4, "QUOTED": 3, "CATALOG": 4}
    results = check_assertions(assertions, bom_counts)
    assert len(results) == 1
    a, passed, msg = results[0]
    assert passed is True


def test_n_of_m_wrong_count_fails():
    """'3 of 11 lines are ESTIMATED' when BOM has 4 ESTIMATED fails."""
    text = "3 of 11 lines are ESTIMATED."
    assertions = extract_count_assertions(text)
    bom_counts = {"ESTIMATED": 4, "QUOTED": 3, "CATALOG": 4}
    results = check_assertions(assertions, bom_counts)
    assert len(results) == 1
    a, passed, msg = results[0]
    assert passed is False
    assert "Asserted=3" in msg
    assert "Actual=4" in msg


# ----------------------------------------------------------------------
# 3. BOM basis count extraction
# ----------------------------------------------------------------------

def test_bom_basis_counts_extracted():
    """The linter extracts ESTIMATED/QUOTED/CATALOG counts from BOM tables."""
    text = """| Component | Spec | Unit cost | Qty | Subtotal | Basis |
|---|---|---|---|---|---|
| Item A | spec | $10 | 1 | $10 | ESTIMATED |
| Item B | spec | $20 | 1 | $20 | QUOTED |
| Item C | spec | $30 | 1 | $30 | ESTIMATED |
| Item D | spec | $40 | 1 | $40 | CATALOG |
"""
    counts = extract_bom_basis_counts(text)
    assert counts["ESTIMATED"] == 2
    assert counts["QUOTED"] == 1
    assert counts["CATALOG"] == 1


# ----------------------------------------------------------------------
# 4. The exact F-053 scenario (vaccine fridge package)
# ----------------------------------------------------------------------

def test_f053_exact_scenario():
    """The exact F-053 contradiction: 'count: 3' but 4 items listed,
    followed by '4 of 11 lines are ESTIMATED' (correct)."""
    text = """**ESTIMATE count:** 3 (BL-003, BL-007, BL-009, BL-011). 4 of 11 lines are ESTIMATED.

| Component | Basis |
|---|---|
| BL-001 | QUOTED |
| BL-002 | CATALOG |
| BL-003 | ESTIMATED |
| BL-004 | CATALOG |
| BL-005 | QUOTED |
| BL-006 | CATALOG |
| BL-007 | ESTIMATED |
| BL-008 | CATALOG |
| BL-009 | ESTIMATED |
| BL-010 | QUOTED |
| BL-011 | ESTIMATED |
"""
    assertions = extract_count_assertions(text)
    # Should find 2 assertions: count_colon (3) and N_of_M (4)
    assert len(assertions) == 2

    bom_counts = extract_bom_basis_counts(text)
    # BOM has 4 ESTIMATED rows
    assert bom_counts["ESTIMATED"] == 4

    results = check_assertions(assertions, bom_counts)
    # The count_colon assertion should FAIL (says 3, has 4 items)
    count_colon_results = [r for r in results if r[0].pattern_type == "count_colon"]
    assert len(count_colon_results) == 1
    assert count_colon_results[0][1] is False  # FAIL

    # The N_of_M assertion should PASS (says 4, BOM has 4)
    n_of_m_results = [r for r in results if r[0].pattern_type == "N_of_M"]
    assert len(n_of_m_results) == 1
    assert n_of_m_results[0][1] is True  # PASS


# ----------------------------------------------------------------------
# 5. CLI exit codes
# ----------------------------------------------------------------------

def test_cli_returns_0_on_pass(tmp_path):
    """CLI returns 0 when no contradictions found."""
    text = "ESTIMATE count: 4 (BL-003, BL-007, BL-009, BL-011)."
    f = tmp_path / "pkg.md"
    f.write_text(text)
    result = subprocess.run(
        [sys.executable, "scripts/verify_prose_consistency.py", str(f)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 0, f"Expected 0, got {result.returncode}\n{result.stdout}"


def test_cli_returns_1_on_fail(tmp_path):
    """CLI returns 1 when contradictions found (F-053 scenario)."""
    text = "ESTIMATE count: 3 (BL-003, BL-007, BL-009, BL-011)."
    f = tmp_path / "pkg.md"
    f.write_text(text)
    result = subprocess.run(
        [sys.executable, "scripts/verify_prose_consistency.py", str(f)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 1, f"Expected 1, got {result.returncode}\n{result.stdout}"
    assert "FAIL" in result.stdout
    assert "Asserted=3" in result.stdout
    assert "Actual=4" in result.stdout


def test_cli_json_output(tmp_path):
    """--json flag emits valid JSON with expected structure."""
    text = "ESTIMATE count: 3 (BL-003, BL-007, BL-009, BL-011)."
    f = tmp_path / "pkg.md"
    f.write_text(text)
    result = subprocess.run(
        [sys.executable, "scripts/verify_prose_consistency.py", str(f), "--json"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["status"] == "FAIL"
    assert output["total_assertions"] == 1
    assert output["contradictions"] == 1
    assert output["contradiction_details"][0]["asserted"] == 3
    assert output["contradiction_details"][0]["actual"] == 4


# ----------------------------------------------------------------------
# 6. No assertions found (clean package)
# ----------------------------------------------------------------------

def test_no_assertions_found_passes(tmp_path):
    """A package with no count assertions passes cleanly."""
    text = "This package has no count assertions in its prose."
    f = tmp_path / "pkg.md"
    f.write_text(text)
    result = subprocess.run(
        [sys.executable, "scripts/verify_prose_consistency.py", str(f)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 0
    assert "No count contradictions found" in result.stdout


# ----------------------------------------------------------------------
# 7. Multiple contradictions in one document
# ----------------------------------------------------------------------

def test_multiple_contradictions(tmp_path):
    """Multiple count contradictions are all reported."""
    text = """
ESTIMATE count: 3 (BL-001, BL-002, BL-003, BL-004).
QUOTED count: 2 (BL-005, BL-006, BL-007).
"""
    f = tmp_path / "pkg.md"
    f.write_text(text)
    result = subprocess.run(
        [sys.executable, "scripts/verify_prose_consistency.py", str(f)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 1
    assert "Contradictions: 2" in result.stdout
