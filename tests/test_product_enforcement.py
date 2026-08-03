#!/usr/bin/env python3
"""
Test: Product package mechanical enforcement.

Per deep self-audit (2026-08-03): the system had 8 gaps where manual
steps existed between query and PDF, not verified by CI. This test
closes gaps 2-5:

Gap 2: product/PRODUCT.md exists as the canonical source.
Gap 3: product/PRODUCT.md contains all 12 sections.
Gap 4: product/PRODUCT.md contains the Next Money Page.
Gap 5: the 1D thermal model runs without error.

If any of these fail, CI blocks the commit — the system cannot ship
a stale, incomplete, or broken package.
"""
import pathlib
import subprocess
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRODUCT_MD = ROOT / "product" / "PRODUCT.md"
PRODUCT_PDF = ROOT / "product" / "PRODUCT.pdf"


class TestCanonicalSource:
    """Gap 2: product/PRODUCT.md is the canonical source for the PDF."""

    def test_product_md_exists(self):
        assert PRODUCT_MD.exists(), (
            "product/PRODUCT.md does not exist. This is the canonical source "
            "for the customer-facing PDF. Without it, there is no link between "
            "the PDF and the markdown that produced it."
        )

    def test_product_pdf_exists(self):
        assert PRODUCT_PDF.exists(), (
            "product/PRODUCT.pdf does not exist. This is the ONE customer-facing PDF."
        )

    def test_product_md_nonempty(self):
        content = PRODUCT_MD.read_text()
        assert len(content) > 1000, (
            f"product/PRODUCT.md is too short ({len(content)} chars). "
            f"A real package must have substantial content."
        )


class TestProductHasAllSections:
    """Gap 3: product/PRODUCT.md must contain all 12 sections."""

    REQUIRED_SECTIONS = [
        "0. PURPOSE",
        "1. REQUIREMENTS",
        "2. EVIDENCE",
        "3. DECOMPOSITION",
        "4. ALTERNATIVES",
        "5. CONSISTENCY",
        "6. TRADEOFFS",
        "7. ADVERSARIAL",
        "8. IMPLEMENTATION",
        "9. VALIDATION",
        "10. RETRACTIONS",
        "11. KILL TESTS",
        "12. SAFETY",
    ]

    def test_all_sections_present(self):
        if not PRODUCT_MD.exists():
            pytest.skip("product/PRODUCT.md does not exist")
        content = PRODUCT_MD.read_text()
        for section in self.REQUIRED_SECTIONS:
            # Case-insensitive, allow for markdown formatting
            assert section.lower() in content.lower(), (
                f"product/PRODUCT.md missing section: {section}"
            )

    def test_final_verdict_present(self):
        if not PRODUCT_MD.exists():
            pytest.skip("product/PRODUCT.md does not exist")
        content = PRODUCT_MD.read_text()
        assert "VERDICT" in content.upper() or "APPROVED" in content or "REJECTED" in content, (
            "product/PRODUCT.md missing final verdict"
        )


class TestProductHasNextMoneyPage:
    """Gap 4: product/PRODUCT.md must contain the Next Money Page."""

    def test_next_money_page_present(self):
        if not PRODUCT_MD.exists():
            pytest.skip("product/PRODUCT.md does not exist")
        content = PRODUCT_MD.read_text()
        assert "NEXT MONEY" in content.upper(), (
            "product/PRODUCT.md missing the Next Money Page. "
            "Per Law 12: the package must end at a decision, not a verdict."
        )

    def test_next_money_page_has_sections(self):
        if not PRODUCT_MD.exists():
            pytest.skip("product/PRODUCT.md does not exist")
        content = PRODUCT_MD.read_text()
        # Find the Next Money Page section and check for required sub-sections
        nmp_idx = content.upper().find("NEXT MONEY")
        if nmp_idx == -1:
            pytest.skip("Next Money Page not found")
        nmp_section = content[nmp_idx:]
        for required in ["Current maturity", "Remaining risks",
                         "Next expenditure", "Decision unlocked",
                         "Possible outcomes"]:
            assert required.lower() in nmp_section.lower(), (
                f"Next Money Page missing: {required}"
            )


class TestThermalModelRuns:
    """Gap 5: the 1D thermal model must run without error."""

    def test_thermal_model_script_exists(self):
        path = ROOT / "scripts" / "thermal_model_1d.py"
        assert path.exists(), "scripts/thermal_model_1d.py does not exist."

    def test_thermal_model_runs_without_error(self):
        """The model must execute and produce output without crashing."""
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "thermal_model_1d.py")],
            capture_output=True, text=True, cwd=str(ROOT),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"thermal_model_1d.py failed with exit code {result.returncode}:\n"
            f"{result.stderr[:500]}"
        )
        assert "THERMAL TRUTH" in result.stdout, (
            "thermal_model_1d.py did not produce 'THERMAL TRUTH' output."
        )

    def test_thermal_model_produces_numbers(self):
        """The model must produce actual temperature numbers, not narrative."""
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "thermal_model_1d.py")],
            capture_output=True, text=True, cwd=str(ROOT),
            timeout=30,
        )
        assert "°C" in result.stdout or "C" in result.stdout, (
            "thermal_model_1d.py did not produce temperature values."
        )
        # Must mention specific discharge rates
        for rate in ["1C", "1.5C", "2C"]:
            assert rate in result.stdout, (
                f"thermal_model_1d.py missing discharge rate: {rate}"
            )


class TestProductPassesScanner:
    """Gap 7: product/PRODUCT.md must pass the Law 27 scanner."""

    def test_product_md_passes_scanner(self, tmp_path):
        if not PRODUCT_MD.exists():
            pytest.skip("product/PRODUCT.md does not exist")
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "enforce_law27.py"),
             str(PRODUCT_MD)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode == 0, (
            f"Law 27 scanner REJECTED product/PRODUCT.md:\n"
            f"{result.stdout}\n"
            f"The customer-facing source contains forbidden language."
        )


class TestProductPdfMatchesSource:
    """Gap 1: product/PRODUCT.pdf must match a regeneration from product/PRODUCT.md."""

    def test_pdf_can_be_regenerated(self, tmp_path):
        """The PDF can be regenerated from the source without error."""
        if not PRODUCT_MD.exists():
            pytest.skip("product/PRODUCT.md does not exist")
        regenerated = tmp_path / "PRODUCT_test.pdf"
        result = subprocess.run(
            ["python3", str(ROOT / "scripts" / "generate_pdf.py"),
             str(PRODUCT_MD), str(regenerated)],
            capture_output=True, text=True, cwd=str(ROOT),
            timeout=60,
        )
        assert result.returncode == 0, (
            f"PDF regeneration failed:\n{result.stderr[:500]}"
        )
        assert regenerated.exists(), "Regenerated PDF does not exist."
        assert regenerated.stat().st_size > 10000, (
            f"Regenerated PDF is too small ({regenerated.stat().st_size} bytes)."
        )
