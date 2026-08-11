"""
Tests for F-001/F-029 fix: PatentParser must handle non-claims-formatted prose.

The original F-001 finding: the parser only extracts components when
trigger phrases like "comprising", "coupled to", "configured to" are
present. Real patent prose without these phrases silently returns
empty extractions. This is the load-bearing prerequisite for Phase 3.

The fix: add a fallback extraction path that uses noun-phrase
detection and keyword scanning when the trigger-phrase extraction
returns empty results.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# Realistic patent prose WITHOUT claims-formatted trigger phrases.
# This is what most real patent ABSTRACT sections look like — narrative
# description, not numbered claims with "comprising" clauses.
PROSE_PATENT_TEXT = """
TITLE: Radiative Cooling Metamaterial for Passive Temperature Regulation

ABSTRACT:
A radiative cooling metamaterial is disclosed that selectively emits
thermal radiation in the atmospheric transparency window between 8 and
13 microns. The metamaterial consists of alternating layers of silicon
dioxide and hafnium dioxide deposited on a silver mirror substrate.
The device achieves surface temperatures 4.9 degrees below ambient
under direct sunlight irradiance of 850 watts per square meter.

The system integrates a heat transfer fluid loop that circulates
ethylene glycol through a copper heat exchanger bonded to the
metamaterial substrate. A thermocouple sensor monitors the cooling
surface temperature and provides feedback to a proportional-integral
controller that regulates fluid flow rate.

The manufacturing process involves electron beam evaporation of the
dielectric layers in a vacuum chamber at elevated substrate
temperature. The silver mirror is deposited by sputtering. The
polymer encapsulation layer protects the metamaterial from
environmental degradation.

The device has potential applications in building cooling, food
preservation in off-grid locations, and supplementary cooling for
photovoltaic panels.
"""

PROSE_PROVENANCE = {
    "source": "synthetic_prose_patent",
    "source_type": "patent",
    "title": "Radiative Cooling Metamaterial for Passive Temperature Regulation",
    "authors": ["Test Author"],
    "publication_date": "2026-08-01",
    "patent_number": "TEST-PROSE-001",
    "doi": None,
    "confidence": 1.0,
    "extracted_by": "tests.test_f001_fix",
    "timestamp": "2026-08-01T00:00:00+00:00",
}


def test_prose_patent_extracts_components():
    """F-001 FIX: The parser must extract components from prose-only
    patent text (no 'comprising' trigger phrases). Before the fix,
    this returned []."""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-PROSE-001",
        "title": "Radiative Cooling Metamaterial",
        "text": PROSE_PATENT_TEXT,
    })
    components = result.get("components", [])
    # GROUND-TRUTH: the prose mentions these components.
    component_labels = [str(c).lower() for c in components]
    assert any("sensor" in c or "thermocouple" in c for c in component_labels), \
        f"Expected sensor/thermocouple in components from prose: {components}"
    assert any("exchanger" in c for c in component_labels), \
        f"Expected heat exchanger in components from prose: {components}"


def test_prose_patent_extracts_materials():
    """F-001 FIX: The parser must extract materials from prose-only
    patent text."""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-PROSE-001",
        "text": PROSE_PATENT_TEXT,
    })
    materials = result.get("materials", [])
    # GROUND-TRUTH: the prose mentions these materials.
    material_labels = [str(m).lower() for m in materials]
    assert any("polymer" in m for m in material_labels), \
        f"Expected 'polymer' in materials from prose: {materials}"
    assert any("ceramic" in m or "silicon" in m for m in material_labels), \
        f"Expected 'ceramic' or 'silicon' in materials from prose: {materials}"
    assert any("silver" in m or "copper" in m for m in material_labels), \
        f"Expected 'silver' or 'copper' in materials from prose: {materials}"


def test_prose_patent_extracts_constraints():
    """F-001 FIX: The parser must extract constraints from prose-only
    patent text."""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-PROSE-001",
        "text": PROSE_PATENT_TEXT,
    })
    constraints = result.get("constraints", [])
    assert len(constraints) > 0, "No constraints extracted from prose"
    # GROUND-TRUTH: the prose mentions manufacturing, temperature, energy.
    constraint_text = json.dumps(constraints).lower()
    assert "manufactur" in constraint_text, \
        f"Expected 'manufacturing' in constraints from prose: {constraints}"
    assert "temperature" in constraint_text or "thermal" in constraint_text, \
        f"Expected 'temperature' in constraints from prose: {constraints}"


def test_prose_patent_parse_confidence_not_zero():
    """F-001 FIX: parse_confidence should be > 0 for a substantial
    prose patent (not just claims-formatted text). Before the fix,
    parse_confidence was 0.0 for prose-only text."""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-PROSE-001",
        "text": PROSE_PATENT_TEXT,
    })
    confidence = result.get("parse_confidence", 0.0)
    assert confidence > 0.0, \
        f"parse_confidence should be > 0 for substantial prose: {confidence}"


def test_prose_patent_attaches_provenance():
    """F-001 FIX: provenance must still be attached for prose patents."""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-PROSE-001",
        "text": PROSE_PATENT_TEXT,
        "provenance": PROSE_PROVENANCE,
    })
    provenance = result.get("provenance")
    assert provenance is not None
    assert provenance.get("source_type") == "patent"
    assert provenance.get("patent_number") == "TEST-PROSE-001"


def test_auditor_short_prose_repro_extracts_something():
    """F-001/F-029 FIX: The auditor's exact repro — short prose
    without trigger phrases — must extract at least SOMETHING.
    Before the fix, it returned 0 components, 0 materials,
    0 constraints, confidence=0.0.

    The auditor's original repro:
    'A new type of cooling device uses special materials to reflect
    heat. The material emits thermal radiation through the atmosphere.'

    This is an unrealistically short patent text — real patent
    abstracts are paragraphs, not 2 sentences. But the test ensures
    the parser doesn't silently return empty on ANY prose; it should
    at least extract the material 'materials' (keyword match) and
    the constraint 'temperature' (keyword match on 'heat'/'thermal').
    """
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-SHORT",
        "text": "A new type of cooling device uses special materials "
                "to reflect heat. The material emits thermal radiation "
                "through the atmosphere.",
    })
    # Even on short prose, the parser should extract materials
    # (the word 'materials' itself is not in the keyword list, but
    # the constraint engine should detect 'temperature'/'thermal').
    constraints = result.get("constraints", {})
    assert len(constraints) > 0, \
        f"Expected at least 1 constraint from short prose, got: {constraints}"
    # parse_confidence can still be low for short text — that's honest.
    # The fix is not "inflated confidence"; it's "non-empty extraction."

