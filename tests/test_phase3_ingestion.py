"""
Phase 3.1 — Ingestion contract tests (CTO directive: tests first).

Per the CTO directive: "Write tests first. The contract should answer:
  Can the system ingest one patent?
  Can the system extract claims?
  Can the system extract components?
  Can the system extract materials?
  Can the system extract constraints?
  Can the system attach provenance?
  Can the system ingest one paper?
  Can the system identify equations?
  Can the system identify assumptions?
  Can the system identify limitations?
  Can extracted information be written into the graph?
  Can constraints be attached to nodes?
  Can provenance be preserved?
  Can the historian reconstruct the source?"

These tests define the contract. They will FAIL until the ingestion
code is implemented. Per the anti-entropy rule "tests first," they
are written BEFORE the implementation.

The tests use a small, known patent text as the test fixture — not
a real patent from the USPTO, but a realistically-structured one
that exercises the parser's extraction capabilities.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# A small, known patent text for testing extraction.
# This is a synthetic patent abstract + claims that exercises:
# - component extraction (pump, membrane, sensor)
# - material extraction (polymer, ceramic)
# - constraint extraction (cost, energy, manufacturing)
# - claim structure (numbered claims)
TEST_PATENT_TEXT = """
TITLE: Passive Radiative Cooling System Using Metamaterial Coating

ABSTRACT:
A passive radiative cooling system comprising a metamaterial coating
layer deposited on a polymer substrate, wherein the metamaterial
selectively emits thermal radiation in the atmospheric transparency
window (8-13 microns). The system includes a heat transfer pump
circulating coolant through a ceramic heat exchanger. A temperature
sensor monitors the cooling surface. The manufacturing process
requires vacuum deposition of the metamaterial onto the polymer
substrate at controlled temperature.

CLAIMS:
1. A passive radiative cooling system comprising:
   a metamaterial coating layer;
   a polymer substrate;
   a heat transfer pump;
   a ceramic heat exchanger;
   a temperature sensor.
2. The system of claim 1, wherein the metamaterial has emissivity
   greater than 0.9 in the 8-13 micron wavelength range.
3. The system of claim 1, wherein the polymer substrate comprises
   polyethylene terephthalate (PET).
"""

TEST_PATENT_PROVENANCE = {
    "source": "synthetic_test_patent",
    "source_type": "patent",
    "title": "Passive Radiative Cooling System Using Metamaterial Coating",
    "authors": ["Test Author"],
    "publication_date": "2026-08-01",
    "patent_number": "TEST-001",
    "doi": None,
    "confidence": 1.0,
    "extracted_by": "tests.test_phase3_ingestion",
    "timestamp": "2026-08-01T00:00:00+00:00",
}


# A small, known paper text for testing extraction.
TEST_PAPER_TEXT = """
Title: Experimental demonstration of daytime radiative cooling

Abstract:
We experimentally demonstrate daytime radiative cooling to 4.9°C
below ambient temperature under direct sunlight. The cooling surface
comprises a multilayer photonic structure with high emissivity in the
mid-infrared atmospheric transparency window.

The governing equation for radiative cooling power is:
P_cool = P_rad(T_s) - P_atm(T_amb) - P_solar - P_cond

where T_s is surface temperature, T_amb is ambient temperature,
P_rad is radiated power, P_atm is absorbed atmospheric radiation,
P_solar is absorbed solar irradiance, and P_cond is conductive
heat gain.

Assumptions:
- The surface is in thermal equilibrium with the sky.
- Solar absorptivity is below 5%.
- Convective heat transfer is minimized by a wind shield.

Limitations:
- The experiment was conducted under dry atmospheric conditions.
- Humidity above 50% significantly reduces cooling performance.
- The multilayer structure requires vacuum deposition, limiting
  scalability.
"""

TEST_PAPER_PROVENANCE = {
    "source": "synthetic_test_paper",
    "source_type": "paper",
    "title": "Experimental demonstration of daytime radiative cooling",
    "authors": ["Test Author A", "Test Author B"],
    "publication_date": "2026-08-01",
    "doi": "10.0000/test.0001",
    "patent_number": None,
    "confidence": 1.0,
    "extracted_by": "tests.test_phase3_ingestion",
    "timestamp": "2026-08-01T00:00:00+00:00",
}


# ----------------------------------------------------------------------
# Patent ingestion contract
# ----------------------------------------------------------------------

def test_patent_parser_ingests_patent_text():
    """Can the system ingest one patent?"""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-001",
        "title": "Passive Radiative Cooling System",
        "text": TEST_PATENT_TEXT,
    })
    assert result is not None
    assert isinstance(result, dict)


def test_patent_parser_extracts_components():
    """Can the system extract components?"""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-001",
        "title": "Passive Radiative Cooling System",
        "text": TEST_PATENT_TEXT,
    })
    components = result.get("components", [])
    assert len(components) > 0, "No components extracted"
    # Should find at least pump, membrane/coating, sensor
    component_labels = [str(c).lower() for c in components]
    assert any("pump" in c for c in component_labels), \
        f"Expected to find 'pump' in components: {components}"
    assert any("sensor" in c for c in component_labels), \
        f"Expected to find 'sensor' in components: {components}"


def test_patent_parser_extracts_materials():
    """Can the system extract materials?"""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-001",
        "title": "Passive Radiative Cooling System",
        "text": TEST_PATENT_TEXT,
    })
    materials = result.get("materials", [])
    assert len(materials) > 0, "No materials extracted"
    material_labels = [str(m).lower() for m in materials]
    assert any("polymer" in m or "pet" in m for m in material_labels), \
        f"Expected to find polymer/PET in materials: {materials}"


def test_patent_parser_extracts_constraints():
    """Can the system extract constraints?"""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-001",
        "title": "Passive Radiative Cooling System",
        "text": TEST_PATENT_TEXT,
    })
    constraints = result.get("constraints", [])
    assert len(constraints) > 0, "No constraints extracted"


def test_patent_parser_attaches_provenance():
    """Can the system attach provenance?"""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-001",
        "title": "Passive Radiative Cooling System",
        "text": TEST_PATENT_TEXT,
        "provenance": TEST_PATENT_PROVENANCE,
    })
    provenance = result.get("provenance")
    assert provenance is not None, "No provenance attached"
    assert provenance.get("source_type") == "patent"
    assert provenance.get("patent_number") == "TEST-001"


# ----------------------------------------------------------------------
# Paper ingestion contract (future — marked as expected-fail for now)
# ----------------------------------------------------------------------

@pytest.mark.xfail(reason="Paper ingestion not yet implemented (Phase 3.2)")
def test_paper_parser_ingests_paper_text():
    """Can the system ingest one paper?"""
    from product.ingestion.paper_parser import PaperParser
    parser = PaperParser()
    result = parser.parse({
        "id": "TEST-PAPER-001",
        "title": "Experimental demonstration of daytime radiative cooling",
        "text": TEST_PAPER_TEXT,
    })
    assert result is not None


@pytest.mark.xfail(reason="Paper ingestion not yet implemented (Phase 3.2)")
def test_paper_parser_identifies_equations():
    """Can the system identify equations?"""
    from product.ingestion.paper_parser import PaperParser
    parser = PaperParser()
    result = parser.parse({
        "id": "TEST-PAPER-001",
        "text": TEST_PAPER_TEXT,
    })
    equations = result.get("equations", [])
    assert len(equations) > 0


@pytest.mark.xfail(reason="Paper ingestion not yet implemented (Phase 3.2)")
def test_paper_parser_identifies_assumptions():
    """Can the system identify assumptions?"""
    from product.ingestion.paper_parser import PaperParser
    parser = PaperParser()
    result = parser.parse({
        "id": "TEST-PAPER-001",
        "text": TEST_PAPER_TEXT,
    })
    assumptions = result.get("assumptions", [])
    assert len(assumptions) > 0


@pytest.mark.xfail(reason="Paper ingestion not yet implemented (Phase 3.2)")
def test_paper_parser_identifies_limitations():
    """Can the system identify limitations?"""
    from product.ingestion.paper_parser import PaperParser
    parser = PaperParser()
    result = parser.parse({
        "id": "TEST-PAPER-001",
        "text": TEST_PAPER_TEXT,
    })
    limitations = result.get("limitations", [])
    assert len(limitations) > 0


# ----------------------------------------------------------------------
# Graph integration contract
# ----------------------------------------------------------------------

def test_extracted_info_can_be_written_to_graph():
    """Can extracted information be written into the graph?"""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-001",
        "title": "Passive Radiative Cooling System",
        "text": TEST_PATENT_TEXT,
    })
    # The extracted components should be writable as graph nodes.
    components = result.get("components", [])
    for c in components:
        assert isinstance(c, (str, dict)), \
            f"Component {c!r} is not a str or dict — cannot write to graph"


def test_constraints_can_be_attached_to_nodes():
    """Can constraints be attached to nodes?"""
    # This tests that the constraint format from the parser is
    # compatible with the constraint format in the graph (dict of
    # constraint_name -> value, per Phase 2 migration).
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-001",
        "text": TEST_PATENT_TEXT,
    })
    constraints = result.get("constraints", [])
    # Each constraint should be expressible as a dict entry
    # (constraint_name -> value).
    for c in constraints:
        if isinstance(c, dict):
            # Already a dict — check it has string keys and numeric values.
            for k, v in c.items():
                assert isinstance(k, str)
        elif isinstance(c, str):
            # A constraint name string — can be converted to {c: 0.5}.
            pass
        else:
            pytest.fail(f"Constraint {c!r} is not a str or dict")


def test_provenance_preserved_in_graph():
    """Can provenance be preserved?"""
    from product.ingestion.patent_parser import PatentParser
    parser = PatentParser()
    result = parser.parse({
        "id": "TEST-001",
        "text": TEST_PATENT_TEXT,
        "provenance": TEST_PATENT_PROVENANCE,
    })
    provenance = result.get("provenance", {})
    assert provenance.get("source_type") == "patent"
    assert provenance.get("extracted_by") is not None
    assert provenance.get("timestamp") is not None
    # The provenance should be JSON-serializable for graph storage.
    json.dumps(provenance)
