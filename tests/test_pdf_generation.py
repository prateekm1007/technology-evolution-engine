#!/usr/bin/env python3
"""
Test: PDF generation enforcement.

Per MASTER_PROTOCOL.md §PDF (CEO directive: "A world-class edited PDF
is non-negotiable. It SHOULD BE PUSHED TO THE GITHUB."):

Every package in examples/ MUST have a corresponding .pdf file. A
markdown file without its PDF is an incomplete deliverable.

This test verifies:
1. scripts/generate_pdf.py exists.
2. scripts/pdf_template.css exists.
3. Every examples/PKG-*.md has a corresponding .pdf.
4. The PDFs are valid (non-zero bytes, PDF header).
5. MASTER_PROTOCOL.md mentions the PDF requirement.
"""
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class TestPdfGeneration:
    """Verify PDF generation infrastructure exists and is used."""

    def test_generate_pdf_script_exists(self):
        path = ROOT / "scripts" / "generate_pdf.py"
        assert path.exists(), "scripts/generate_pdf.py does not exist."

    def test_pdf_template_css_exists(self):
        path = ROOT / "scripts" / "pdf_template.css"
        assert path.exists(), "scripts/pdf_template.css does not exist."

    def test_master_protocol_mentions_pdf(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "PDF" in content, "MASTER_PROTOCOL.md does not mention PDF."
        assert "non-negotiable" in content.lower(), (
            "MASTER_PROTOCOL.md does not state PDF is non-negotiable."
        )

    def test_css_has_cover_page(self):
        css = (ROOT / "scripts" / "pdf_template.css").read_text()
        assert ".cover" in css, "CSS template missing cover page styling."
        assert "@page" in css, "CSS template missing @page rules."
        assert "counter(page)" in css, "CSS template missing page numbering."

    def test_css_has_status_badges(self):
        css = (ROOT / "scripts" / "pdf_template.css").read_text()
        assert ".status-badge" in css or ".badge" in css
        assert "APPROVED" in css
        assert "REJECTED" in css

    def test_css_has_retraction_callout(self):
        css = (ROOT / "scripts" / "pdf_template.css").read_text()
        assert ".retraction-callout" in css, (
            "CSS template missing retraction callout styling."
        )


class TestEveryPackageHasPdf:
    """Every examples/PKG-*.md MUST have a corresponding .pdf file.

    Per MASTER_PROTOCOL.md §PDF: 'A markdown file without its PDF is
    an incomplete deliverable.'
    """

    def _packages_without_pdf(self):
        """Find all PKG-*.md files without a corresponding .pdf."""
        missing = []
        for md_file in EXAMPLES.glob("PKG-*.md"):
            pdf_file = md_file.with_suffix(".pdf")
            if not pdf_file.exists():
                missing.append(md_file.name)
        return missing

    def test_all_packages_have_pdfs(self):
        missing = self._packages_without_pdf()
        assert not missing, (
            f"Packages without PDFs (MASTER_PROTOCOL.md §PDF violation):\n"
            + "\n".join(f"  - {m}" for m in missing)
        )

    def test_pdfs_are_valid(self):
        """Every PDF must be non-empty and have a valid PDF header."""
        for pdf_file in EXAMPLES.glob("PKG-*.pdf"):
            size = pdf_file.stat().st_size
            assert size > 1000, (
                f"{pdf_file.name} is too small ({size} bytes) — likely corrupt."
            )
            # Check PDF header
            header = pdf_file.read_bytes()[:5]
            assert header == b"%PDF-", (
                f"{pdf_file.name} does not have a valid PDF header."
            )

    def test_pdf_count_matches_md_count(self):
        """The number of PDFs should match the number of markdown packages."""
        md_files = list(EXAMPLES.glob("PKG-*.md"))
        pdf_files = list(EXAMPLES.glob("PKG-*.pdf"))
        assert len(md_files) == len(pdf_files), (
            f"Mismatch: {len(md_files)} .md files but {len(pdf_files)} .pdf files. "
            f"Every package must have its PDF (MASTER_PROTOCOL.md §PDF)."
        )
