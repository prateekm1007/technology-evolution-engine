"""
Tests for the PDF rendering template fixes (F-054 through F-059).

Per external audit cycle 27: the PDF had 7 rendering defects that text
extraction missed because text is blind to layout. These tests verify
the CSS and generate_pdf.py fixes.

F-054: ASCII diagrams must not wrap (white-space: pre, not pre-wrap)
F-055: Equations get proper typesetting (.equation class)
F-056: Cover page contrast meets WCAG AA (4.5:1 minimum)
F-057: TOC has page-number leaders + internal links
F-058: Page-break rules don't inflate page count
F-059: Render-time consistency check catches table/prose contradictions
"""
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CSS_PATH = ROOT / "scripts" / "pdf_template.css"
GENERATE_PDF_PATH = ROOT / "scripts" / "generate_pdf.py"


# ----------------------------------------------------------------------
# F-054: ASCII diagrams must not wrap
# ----------------------------------------------------------------------

def test_pre_blocks_use_white_space_pre_not_pre_wrap():
    """F-054: pre blocks must use white-space: pre (not pre-wrap) to
    prevent ASCII diagram breakage."""
    css = CSS_PATH.read_text()
    # Find the pre block rule
    pre_match = re.search(r'pre\s*\{([^}]+)\}', css)
    assert pre_match, "pre block CSS rule not found"
    pre_rule = pre_match.group(1)
    # Check the actual white-space property (not comments)
    ws_match = re.search(r'white-space:\s*(\w+)', pre_rule)
    assert ws_match, f"white-space property not found in pre rule: {pre_rule}"
    ws_value = ws_match.group(1)
    assert ws_value == "pre", (
        f"pre block white-space must be 'pre', got '{ws_value}'"
    )


def test_pre_blocks_do_not_have_word_wrap_break_word():
    """F-054: word-wrap: break-word is incompatible with white-space: pre
    and must be removed from pre blocks (as an active property, not in comments)."""
    css = CSS_PATH.read_text()
    pre_match = re.search(r'pre\s*\{([^}]+)\}', css)
    assert pre_match
    pre_rule = pre_match.group(1)
    # Check for word-wrap as an active property (not in a comment)
    # Remove CSS comments first
    pre_rule_no_comments = re.sub(r'/\*.*?\*/', '', pre_rule, flags=re.DOTALL)
    assert "word-wrap: break-word" not in pre_rule_no_comments, (
        "word-wrap: break-word must be removed from pre blocks (as active property)"
    )


# ----------------------------------------------------------------------
# F-055: Equation typesetting
# ----------------------------------------------------------------------

def test_equation_class_exists_in_css():
    """F-055: the .equation CSS class must exist for proper equation
    typesetting (serif font, centered, subscript/superscript support)."""
    css = CSS_PATH.read_text()
    assert ".equation" in css, (
        ".equation CSS class not found — equations need proper typesetting"
    )
    # Check for serif font (engineering convention)
    eq_match = re.search(r'\.equation\s*\{([^}]+)\}', css)
    assert eq_match
    eq_rule = eq_match.group(1)
    assert "serif" in eq_rule.lower(), (
        ".equation should use serif font (engineering convention)"
    )
    assert "text-align: center" in eq_rule, (
        ".equation should be centered"
    )


def test_equation_has_subscript_superscript_support():
    """F-055: the .equation class must support <sub> and <sup> tags."""
    css = CSS_PATH.read_text()
    assert ".equation sub" in css, "subscript support missing"
    assert ".equation sup" in css, "superscript support missing"


# ----------------------------------------------------------------------
# F-056: Cover page contrast (WCAG AA 4.5:1)
# ----------------------------------------------------------------------

def _luminance(r, g, b):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def _contrast_ratio(hex1, hex2):
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    l1 = _luminance(*hex_to_rgb(hex1))
    l2 = _luminance(*hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def test_cover_footer_contrast_meets_wcag_aa():
    """F-056: the cover footer text must meet WCAG AA 4.5:1 contrast
    against the dark cover background."""
    css = CSS_PATH.read_text()
    # Find the cover footer color
    footer_match = re.search(r'\.cover\s+\.footer\s*\{[^}]*color:\s*(#[0-9a-fA-F]{6})', css, re.DOTALL)
    assert footer_match, "cover footer color not found"
    footer_color = footer_match.group(1)

    # Cover background is #0a2540 (gradient start)
    bg_color = "#0a2540"
    ratio = _contrast_ratio(footer_color, bg_color)
    assert ratio >= 4.5, (
        f"cover footer color {footer_color} on {bg_color} has contrast "
        f"{ratio:.2f}:1 — WCAG AA requires 4.5:1"
    )


def test_cover_label_contrast_meets_wcag_aa():
    """F-056: the cover meta-table label text must meet WCAG AA 4.5:1."""
    css = CSS_PATH.read_text()
    label_match = re.search(
        r'\.cover\s+\.meta-table\s+td:first-child\s*\{[^}]*color:\s*(#[0-9a-fA-F]{6})',
        css, re.DOTALL
    )
    assert label_match, "cover meta-table label color not found"
    label_color = label_match.group(1)

    bg_color = "#0a2540"
    ratio = _contrast_ratio(label_color, bg_color)
    assert ratio >= 4.5, (
        f"cover label color {label_color} on {bg_color} has contrast "
        f"{ratio:.2f}:1 — WCAG AA requires 4.5:1"
    )


# ----------------------------------------------------------------------
# F-057: TOC has page-number leaders + internal links
# ----------------------------------------------------------------------

def test_toc_entries_are_anchored_links():
    """F-057: TOC entries must be <a href="#section-N"> links, not plain
    text. This enables CSS target-counter() for page-number leaders."""
    gen_py = GENERATE_PDF_PATH.read_text()
    # Check that build_toc_html creates <a href="#..."> links
    assert 'href="#{anchor}"' in gen_py or "href=\"#section-" in gen_py, (
        "TOC entries must be anchored links for page-number resolution"
    )


def test_toc_css_has_target_counter():
    """F-057: the CSS must use target-counter(attr(href), page) for
    TOC page-number leaders."""
    css = CSS_PATH.read_text()
    assert "target-counter" in css, (
        "CSS must use target-counter() for TOC page-number leaders"
    )


def test_headings_get_id_attributes():
    """F-057: headings in the body must get id attributes so the TOC
    anchored links resolve."""
    gen_py = GENERATE_PDF_PATH.read_text()
    assert "add_heading_id" in gen_py or 'id="section-' in gen_py, (
        "Headings must get id attributes for TOC anchor resolution"
    )


# ----------------------------------------------------------------------
# F-058: Page-break rules tightened
# ----------------------------------------------------------------------

def test_only_h1_gets_page_break_before_always():
    """F-058: only h1 should have page-break-before: always. h2/h3
    should flow naturally to reduce whitespace inflation."""
    css = CSS_PATH.read_text()
    # Find all page-break-before: always rules
    pb_always_rules = re.findall(r'([^{]+)\{[^}]*page-break-before:\s*always', css)
    # Check that h2 and h3 do NOT have page-break-before: always
    for rule in pb_always_rules:
        rule = rule.strip()
        if rule.startswith("h2") or rule.startswith("h3"):
            # h2/h3 should not force page breaks
            # (they may appear in a combined selector, but not alone)
            if rule in ["h2", "h3"]:
                pytest.fail(
                    f"{rule} has page-break-before: always — only h1 should force new pages"
                )


def test_h1_has_page_break_before():
    """F-058: h1 (top-level sections) should have page-break-before: always."""
    css = CSS_PATH.read_text()
    # Find the h1 rule in the page-break section
    h1_match = re.search(r'h1\s*\{[^}]*page-break-before:\s*always', css, re.DOTALL)
    assert h1_match, "h1 should have page-break-before: always"


# ----------------------------------------------------------------------
# F-059: Render-time consistency check
# ----------------------------------------------------------------------

def test_check_table_prose_consistency_function_exists():
    """F-059: the check_table_prose_consistency function must exist in
    generate_pdf.py."""
    gen_py = GENERATE_PDF_PATH.read_text()
    assert "def check_table_prose_consistency" in gen_py, (
        "check_table_prose_consistency function not found"
    )


def test_check_table_prose_consistency_catches_contradiction():
    """F-059: the function must catch when a table GRAND TOTAL is
    immediately overridden by prose with a different value."""
    # Import the function
    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_pdf import check_table_prose_consistency

    # Simulate the F-053/F-059 pattern: table says $100.50, prose says $98.10
    md_text = """| GRAND TOTAL | $100.50 |

**Wait — the total is $100.50, which exceeds $100.** The corrected total is $98.10.
"""
    errors = check_table_prose_consistency(md_text)
    assert len(errors) > 0, (
        "Should detect the table/prose contradiction: table says $100.50, "
        "prose says $98.10 with correction language"
    )


def test_check_table_prose_consistency_passes_clean_text():
    """F-059: the function must not flag text without contradictions."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_pdf import check_table_prose_consistency

    md_text = """| GRAND TOTAL | $98.10 |

The total is $98.10, which meets the $100 target.
"""
    errors = check_table_prose_consistency(md_text)
    assert len(errors) == 0, (
        f"Should not flag consistent text, but got: {errors}"
    )
