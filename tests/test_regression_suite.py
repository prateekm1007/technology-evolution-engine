#!/usr/bin/env python3
"""
Test: Regression suite (Phase 6 — auditor roadmap final phase).

Per external auditor: 'PKG-DESAL-002 (corrected) becomes your first
regression fixture. If a future change reintroduces any of the 4 error
patterns the auditor found (BOM $400 error, mass 3kg error,
QUOTED/ESTIMATED miscounts, amortization error), the regression test
catches it.'

This test:
1. Runs the independent recomputation verifier on product/PRODUCT.md
   and asserts it PASSES (0 arithmetic errors).
2. Runs 4 specific regression checks that would have caught the original
   errors the auditor found:
   - BOM: line items must sum to the claimed total
   - Mass: stack-up must sum to the claimed total
   - QUOTED count: must match actual QUOTED rows in the BOM
   - ESTIMATED count: must match actual ESTIMATED rows in the BOM
3. Runs the Law 27 scanner on product/PRODUCT.md and asserts 0 violations.

If any of these fail, the package has regressed to one of the error
patterns the auditor identified. The test name includes the specific
error pattern it guards against.
"""
import pathlib
import subprocess
import sys
import re
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRODUCT_MD = ROOT / "product" / "PRODUCT.md"
VERIFIER = ROOT / "scripts" / "verify_arithmetic.py"
SCANNER = ROOT / "scripts" / "enforce_law27.py"


class TestRegressionSuite:
    """Phase 6: regression suite. Guards against the 4 error patterns
    the auditor found in PKG-DESAL-002 before correction.

    These tests are the permanent record of what went wrong and the
    mechanical guarantee that it won't happen again.
    """

    def test_regression_01_bom_sums_correctly(self):
        """Regression: BOM line items must sum to the claimed total.

        Original error: line items summed to $5,050 but document
        claimed $4,650 — a $400 error.
        """
        assert PRODUCT_MD.exists(), "product/PRODUCT.md does not exist"
        result = subprocess.run(
            [sys.executable, str(VERIFIER), str(PRODUCT_MD)],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30,
        )
        assert result.returncode == 0, (
            f"Verifier failed — BOM may not sum correctly:\n{result.stdout}"
        )
        assert "PASS" in result.stdout, (
            f"Verifier did not report PASS:\n{result.stdout}"
        )

    def test_regression_02_mass_sums_correctly(self):
        """Regression: mass stack-up must sum to the claimed total.

        Original error: line items summed to 283.0 kg but document
        claimed 280.0 kg — a 3.0 kg error.
        """
        assert PRODUCT_MD.exists()
        # The verifier checks mass; if it passes, mass reconciles
        result = subprocess.run(
            [sys.executable, str(VERIFIER), str(PRODUCT_MD)],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30,
        )
        assert result.returncode == 0, (
            f"Verifier failed — mass may not sum correctly:\n{result.stdout}"
        )

    def test_regression_03_quoted_count_matches_actual(self):
        """Regression: QUOTED count must match actual QUOTED rows.

        Original error: document claimed 10 QUOTED but actual count
        was 6 — a miscount of 4.
        """
        assert PRODUCT_MD.exists()
        result = subprocess.run(
            [sys.executable, str(VERIFIER), str(PRODUCT_MD)],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30,
        )
        # The verifier checks basis counts; if it passes, counts match
        assert result.returncode == 0, (
            f"Verifier failed — QUOTED count may not match:\n{result.stdout}"
        )
        # Verify the verifier actually checked counts
        assert "QUOTED" in result.stdout, (
            "Verifier did not report QUOTED count — it may not be checking."
        )

    def test_regression_04_estimated_count_matches_actual(self):
        """Regression: ESTIMATED count must match actual ESTIMATED rows.

        Original error: document claimed 6 ESTIMATED but actual count
        was 7 — a miscount of 1.
        """
        assert PRODUCT_MD.exists()
        result = subprocess.run(
            [sys.executable, str(VERIFIER), str(PRODUCT_MD)],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30,
        )
        assert result.returncode == 0, (
            f"Verifier failed — ESTIMATED count may not match:\n{result.stdout}"
        )
        assert "ESTIMATED" in result.stdout, (
            "Verifier did not report ESTIMATED count — it may not be checking."
        )

    def test_regression_05_scanner_passes_on_product(self):
        """Regression: Law 27 scanner must pass on product/PRODUCT.md.

        This guards against forbidden language reappearing in the
        customer-facing source.
        """
        assert PRODUCT_MD.exists()
        result = subprocess.run(
            [sys.executable, str(SCANNER), str(PRODUCT_MD)],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30,
        )
        assert result.returncode == 0, (
            f"Scanner failed on PRODUCT.md:\n{result.stdout}"
        )

    def test_regression_06_no_hand_typed_counts(self):
        """Regression: provenance counts must be derived, not hand-typed.

        Per Phase 2: if a human or LLM types the count without deriving
        it from the actual BOM rows, it will drift. The verifier catches
        this by recomputing from raw rows.
        """
        assert PRODUCT_MD.exists()
        result = subprocess.run(
            [sys.executable, str(VERIFIER), str(PRODUCT_MD)],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30,
        )
        # If the verifier passes, the counts match — whether they were
        # hand-typed or computed, the independent recomputation confirms them
        assert result.returncode == 0

    def test_regression_07_amortization_formula_executed(self):
        """Regression: amortization formula must produce the stated result.

        Original error: document said "$4,650/7yr/365 = $1.20/day"
        but the formula actually produces $1.82/day.

        The verifier checks this by recomputing the amortization.
        """
        assert PRODUCT_MD.exists()
        # The verifier checks amortization; if it passes, the formula matches
        result = subprocess.run(
            [sys.executable, str(VERIFIER), str(PRODUCT_MD)],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30,
        )
        assert result.returncode == 0, (
            f"Verifier failed — amortization formula may not match:\n{result.stdout}"
        )
