"""
F-030 fix tests: paper parser bugs on realistic text (L3).

The auditor found two bugs:
1. Equation regex requires line to START with a variable name —
   misses inline equations like "The cooling power is P_cool = P_rad - ..."
2. Limitations section regex over-captures prose lines after bullet points.

These tests use the auditor's exact repro to verify the fixes.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# The auditor's exact repro — realistic arXiv-style text with
# inline equation and prose after bullet points.
REALISTIC_PAPER_TEXT = """Title: Test
Abstract: We report X.

Assumptions:
- The system is in equilibrium.

Limitations:
- Humidity degrades performance.

The cooling power is P_cool = P_rad - P_atm.
"""


def test_inline_equation_is_extracted():
    """F-030 fix: equation appearing inline with prose (not at
    line start) must be extracted. Before the fix, the regex required
    the line to start with a variable name — 'P_cool = ...' on its
    own line worked, but 'The cooling power is P_cool = ...' did not."""
    from product.ingestion.paper_parser import PaperParser
    parser = PaperParser()
    result = parser.parse({"id": "T", "text": REALISTIC_PAPER_TEXT})
    equations = result.get("equations", [])
    # GROUND-TRUTH: the text contains "P_cool = P_rad - P_atm".
    eq_text = " ".join(str(e) for e in equations).lower()
    assert "p_cool" in eq_text, \
        f"Expected 'p_cool' in equations from inline equation: {equations}"


def test_limitations_section_does_not_capture_prose():
    """F-030 fix: the limitations section must stop at the first
    non-bullet line after the section header. Before the fix, prose
    lines after the bullet points were captured as limitations."""
    from product.ingestion.paper_parser import PaperParser
    parser = PaperParser()
    result = parser.parse({"id": "T", "text": REALISTIC_PAPER_TEXT})
    limitations = result.get("limitations", [])
    # GROUND-TRUTH: there should be exactly 1 limitation (the bullet point).
    # The prose line "The cooling power is..." should NOT be captured.
    limitation_text = " ".join(str(l) for l in limitations).lower()
    assert "cooling power" not in limitation_text, \
        f"Prose line captured as limitation: {limitations}"
    assert len(limitations) == 1, \
        f"Expected 1 limitation (the bullet), got {len(limitations)}: {limitations}"
    assert "humidity" in limitation_text, \
        f"Expected 'humidity' in limitations: {limitations}"
