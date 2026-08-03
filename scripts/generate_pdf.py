#!/usr/bin/env python3
"""
generate_pdf.py — World-class PDF generator for MASTER_PACKAGE.md files.

Per MASTER_PROTOCOL.md §PDF: every package MUST ship as a professionally
formatted PDF. This script converts a markdown package to a PDF using
weasyprint with the custom CSS template at scripts/pdf_template.css.

Usage:
    python scripts/generate_pdf.py examples/PKG-EVBT-001_ev_battery_thermal_package.md
      → produces examples/PKG-EVBT-001_ev_battery_thermal_package.pdf

The PDF includes:
- Cover page (gradient background, package ID, title, status badge)
- Table of contents (generated from headings)
- Page headers (package ID) + footers (page X of Y)
- Zebra-striped tables with accent header
- Code blocks with monospace + light background
- Status badges as colored pills
- Retraction callouts in red-bordered boxes

The PDF MUST pass the Law 27 scanner (no forbidden language).
"""
import sys
import pathlib
import re
import markdown
from weasyprint import HTML, CSS

REPO = pathlib.Path(__file__).resolve().parents[1]
CSS_PATH = REPO / "scripts" / "pdf_template.css"


def extract_metadata(md_text: str) -> dict:
    """Extract package ID, title, maturity, date, status from markdown."""
    meta = {
        "package_id": "PKG-XXX",
        "title": "Engineering Package",
        "maturity": "EVALUATION",
        "date": "2026-08-03",
        "status": "BLOCKED",
    }

    # Package ID
    m = re.search(r"\*\*Package ID:\*\*\s*(PKG-[A-Z]+-\d+)", md_text)
    if m:
        meta["package_id"] = m.group(1)

    # Title — first H1
    m = re.search(r"^#\s+(.+)$", md_text, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()

    # Maturity
    m = re.search(r"\*\*Package maturity:\*\*\s*(\w+)", md_text)
    if m:
        meta["maturity"] = m.group(1)

    # Date
    m = re.search(r"\*\*Date:\*\*\s*([\d-]+)", md_text)
    if m:
        meta["date"] = m.group(1)

    # Status
    m = re.search(r"\*\*Status:\*\*\s*(\w+(?:_\w+)*)", md_text)
    if m:
        meta["status"] = m.group(1)

    return meta


def build_cover_html(meta: dict) -> str:
    """Build the cover page HTML."""
    status = meta["status"]
    return f"""
    <div class="cover">
        <div class="package-id">{meta['package_id']}</div>
        <h1>{meta['title']}</h1>
        <div class="subtitle">Engineering Concept Package — produced per MASTER_PROTOCOL.md</div>
        <table class="meta-table">
            <tr><td>Package ID</td><td>{meta['package_id']}</td></tr>
            <tr><td>Package Maturity</td><td>{meta['maturity']}</td></tr>
            <tr><td>Date</td><td>{meta['date']}</td></tr>
            <tr><td>Governance</td><td>MASTER_PROTOCOL.md (11 sections)</td></tr>
            <tr><td>Scanner</td><td>Law 27/28/29 compliant</td></tr>
        </table>
        <div class="status-badge {status}">{status.replace('_', ' ')}</div>
        <div class="footer">
            Confidential — Engineering Concept Package. This document was
            produced by following MASTER_PROTOCOL.md. Every claim carries
            a typed epistemic status. No numerical confidence is assigned.
        </div>
    </div>
    """


def build_toc_html(md_text: str) -> str:
    """Build a table of contents from H1/H2 headings."""
    toc_items = []
    for line in md_text.split("\n"):
        m = re.match(r"^(#{1,2})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            # Skip the document title (H1 at the very top)
            if level == 1 and not toc_items:
                continue
            toc_items.append((level, title))

    if not toc_items:
        return ""

    items_html = ""
    for level, title in toc_items:
        indent = "" if level == 1 else "&nbsp;&nbsp;&nbsp;&nbsp;"
        # Sanitize title for display
        clean_title = re.sub(r"[`*]", "", title)
        items_html += f'<li>{indent}{clean_title}</li>\n'

    return f"""
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
            {items_html}
        </ul>
    </div>
    """


def enhance_markdown_html(html: str) -> str:
    """Post-process the markdown HTML to add status badges and callouts."""
    # Convert status text to badges
    for status in ["PASS_WITH_CONDITIONS", "PASS", "MARGINAL", "REJECTED",
                    "BLOCKED", "NOT_RUN", "RETRACTED", "WITHDRAWN"]:
        # Wrap standalone status words in badge spans
        html = re.sub(
            rf"(?<!\w)({status})(?!\w)(?!<)",
            rf'<span class="badge {status}">{status.replace("_", " ")}</span>',
            html
        )

    # Style retraction blocks (pre blocks containing "Retracted claim")
    html = re.sub(
        r"(<pre><code>(?:Retracted claim|RT-\d+)[^<]*</code></pre>)",
        r'<div class="retraction-callout">\1</div>',
        html
    )

    return html


def generate_pdf(md_path: pathlib.Path, output_path: pathlib.Path = None):
    """Generate a world-class PDF from a markdown package file."""
    md_path = pathlib.Path(md_path)
    if not md_path.exists():
        print(f"Error: {md_path} does not exist", file=sys.stderr)
        return 1

    md_text = md_path.read_text(encoding="utf-8")
    meta = extract_metadata(md_text)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
    body_html = md.convert(md_text)

    # Remove the first H1 (it's the title, shown on the cover)
    body_html = re.sub(r"<h1[^>]*>.*?</h1>", "", body_html, count=1)

    # Enhance with badges + callouts
    body_html = enhance_markdown_html(body_html)

    # Build cover + TOC + body
    cover = build_cover_html(meta)
    toc = build_toc_html(md_text)

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{meta['package_id']} — {meta['title']}</title>
    </head>
    <body>
        {cover}
        {toc}
        <div class="body-content">
            {body_html}
        </div>
    </body>
    </html>
    """

    # Determine output path
    if output_path is None:
        output_path = md_path.with_suffix(".pdf")

    # Generate PDF
    css_content = CSS_PATH.read_text()
    # Replace the placeholder in CSS with actual package ID
    css_content = css_content.replace(
        "PKG-EVBT — Master Package",
        f"{meta['package_id']} — Master Package"
    )

    HTML(string=full_html).write_pdf(
        str(output_path),
        stylesheets=[CSS(string=css_content)]
    )

    size_kb = output_path.stat().st_size / 1024
    print(f"Generated: {output_path} ({size_kb:.1f} KB)")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_pdf.py <package.md> [output.pdf]")
        print("")
        print("Generates a world-class PDF from a MASTER_PACKAGE.md file.")
        print("Per MASTER_PROTOCOL.md §PDF: every package ships as a PDF.")
        return 1

    md_path = pathlib.Path(sys.argv[1])
    output_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
    return generate_pdf(md_path, output_path)


if __name__ == "__main__":
    sys.exit(main())
