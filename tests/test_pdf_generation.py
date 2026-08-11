#!/usr/bin/env python3
"""
Test: PDF generation enforcement — ONE canonical product PDF.

Per MASTER_PROTOCOL.md §PDF (CEO directive: "As a rule produce one,
only 1 world class pdf. The one we will show our customers. People
will invest based on the quality of the pdf, after they submitted
their query."):

1. There is exactly ONE customer-facing PDF: product/PRODUCT.pdf.
2. examples/ must NOT contain any .pdf files (they are side documents).
3. The canonical PDF must be valid (non-zero, PDF header).
4. The generation infrastructure exists (script + CSS template).
5. MASTER_PROTOCOL.md states the one-PDF rule.

This test mechanically enforces the one-PDF rule. If someone adds
a second PDF to examples/ or product/, the test fails.
"""
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRODUCT_PDF = ROOT / "product" / "PRODUCT.pdf"
EXAMPLES = ROOT / "examples"


class TestPdfInfrastructure:
    """Verify PDF generation infrastructure exists."""

    def test_generate_pdf_script_exists(self):
        path = ROOT / "scripts" / "generate_pdf.py"
        assert path.exists(), "scripts/generate_pdf.py does not exist."

    def test_pdf_template_css_exists(self):
        path = ROOT / "scripts" / "pdf_template.css"
        assert path.exists(), "scripts/pdf_template.css does not exist."

    def test_master_protocol_states_one_pdf_rule(self):
        content = (ROOT / "MASTER_PROTOCOL.md").read_text()
        assert "ONE" in content and "PDF" in content, (
            "MASTER_PROTOCOL.md does not state the one-PDF rule."
        )
        assert "product/PRODUCT.pdf" in content, (
            "MASTER_PROTOCOL.md does not define the canonical product PDF path."
        )
        assert "non-negotiable" in content.lower()

    def test_css_has_cover_page(self):
        css = (ROOT / "scripts" / "pdf_template.css").read_text()
        assert ".cover" in css
        assert "@page" in css
        assert "counter(page)" in css

    def test_css_has_status_badges(self):
        css = (ROOT / "scripts" / "pdf_template.css").read_text()
        assert ".status-badge" in css or ".badge" in css
        assert "APPROVED" in css
        assert "REJECTED" in css

    def test_css_has_retraction_callout(self):
        css = (ROOT / "scripts" / "pdf_template.css").read_text()
        assert ".retraction-callout" in css


class TestOneCanonicalProductPdf:
    """Verify there is exactly ONE customer-facing PDF at product/PRODUCT.pdf.

    Per MASTER_PROTOCOL.md §PDF: 'One PDF per query. Not two. Not four.
    One.' This test enforces that rule mechanically.
    """

    def test_product_dir_exists(self):
        assert (ROOT / "product").exists(), (
            "product/ directory does not exist. The canonical product PDF "
            "must live at product/PRODUCT.pdf."
        )

    def test_canonical_product_pdf_exists(self):
        assert PRODUCT_PDF.exists(), (
            "product/PRODUCT.pdf does not exist. This is the ONE customer-facing "
            "PDF that customers, auditors, and investors see. "
            "Per MASTER_PROTOCOL.md §PDF: 'One PDF per query. Not two. Not four. One.'"
        )

    def test_canonical_pdf_is_valid(self):
        assert PRODUCT_PDF.exists()
        size = PRODUCT_PDF.stat().st_size
        assert size > 10000, (
            f"product/PRODUCT.pdf is too small ({size} bytes) — likely corrupt or empty."
        )
        header = PRODUCT_PDF.read_bytes()[:5]
        assert header == b"%PDF-", (
            f"product/PRODUCT.pdf does not have a valid PDF header. "
            f"Got: {header!r}"
        )

    def test_only_one_pdf_in_product_dir(self):
        """product/ must contain exactly ONE PDF: PRODUCT.pdf."""
        pdfs = list((ROOT / "product").glob("*.pdf"))
        assert len(pdfs) == 1, (
            f"product/ contains {len(pdfs)} PDFs. Expected exactly 1 (PRODUCT.pdf). "
            f"Found: {[p.name for p in pdfs]}. "
            f"Per MASTER_PROTOCOL.md: 'One PDF per query. Not two. Not four. One.'"
        )
        assert pdfs[0].name == "PRODUCT.pdf", (
            f"The single PDF must be named PRODUCT.pdf. Got: {pdfs[0].name}"
        )


class TestNoCompetingPdfs:
    """Verify examples/ and other non-product dirs do NOT contain PDFs.

    Per MASTER_PROTOCOL.md §PDF: 'Side documents are allowed but they
    are NOT customer-facing. The customer sees only the PDF.' Side
    documents are markdown — they do not need PDFs.
    """

    def test_examples_has_no_pdfs(self):
        pdfs = list(EXAMPLES.glob("*.pdf"))
        assert not pdfs, (
            f"examples/ contains {len(pdfs)} PDF(s). Side documents must NOT have "
            f"PDFs — only product/PRODUCT.pdf is customer-facing. "
            f"Found: {[p.name for p in pdfs]}. "
            f"Per MASTER_PROTOCOL.md §PDF: 'examples/ must NOT contain any .pdf files.'"
        )

    def test_no_pdfs_at_root(self):
        pdfs = list(ROOT.glob("*.pdf"))
        assert not pdfs, (
            f"Root directory contains PDF(s): {[p.name for p in pdfs]}. "
            f"Only product/PRODUCT.pdf may exist as a customer-facing PDF."
        )

    def test_archive_products_exists_for_historical_pdfs(self):
        """Old product PDFs are archived, not deleted (per Law 7)."""
        archive = ROOT / "archive" / "products"
        assert archive.exists(), (
            "archive/products/ does not exist. Old product PDFs must be "
            "archived here (per Law 7 — historical permanence)."
        )
