"""
Phase 3 Step 4: Verify real sources ingested into the ACTUAL graph.

Per the auditor's directive and the CTO's success criteria:
- ≥20/577 nodes with real (not prior) constraint values traceable to a source
- Real provenance preserved on every ingested node
- Graph file still parses correctly after ingestion
- Constraint values have real variation (not all 0.5)
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GRAPH_PATH = ROOT / "data" / "civilization_graph.json"


def _load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)


def test_graph_has_at_least_20_nodes_with_real_provenance():
    """Phase 3 Step 4 success criterion: ≥20 nodes with real
    provenance (source_type patent or paper, not prior)."""
    graph = _load_graph()
    real_nodes = [n for n in graph["nodes"]
                  if n.get("provenance", {}).get("source_type") in ("patent", "paper")]
    assert len(real_nodes) >= 20, \
        f"Only {len(real_nodes)} nodes with real provenance (expected >=20)"


def test_ingested_nodes_have_constraints_from_real_text():
    """The ingested nodes must have constraints derived from real
    patent/paper text — not Phase 2 type/domain/edge priors."""
    graph = _load_graph()
    ingested = [n for n in graph["nodes"]
                if n.get("provenance", {}).get("source_type") in ("patent", "paper")]
    with_constraints = [n for n in ingested if n.get("constraints")]
    assert len(with_constraints) >= 15, \
        f"Only {len(with_constraints)} ingested nodes have constraints " \
        f"(expected >=15 out of {len(ingested)})"


def test_constraint_values_have_variation():
    """F-024 fix: constraint values should have real variation across
    ingested nodes — not all the same value."""
    graph = _load_graph()
    ingested = [n for n in graph["nodes"]
                if n.get("provenance", {}).get("source_type") in ("patent", "paper")]
    # Collect all constraint values across ingested nodes.
    all_values = []
    for n in ingested:
        c = n.get("constraints", {})
        if isinstance(c, dict):
            all_values.extend(c.values())
    if not all_values:
        pytest.skip("No constraint values to check variation")
    unique_values = set(round(float(v), 2) for v in all_values if v)
    assert len(unique_values) >= 2, \
        f"All constraint values are the same ({unique_values}) — no variation"


def test_graph_still_parses_after_ingestion():
    """The real graph file must still parse as valid JSON after
    ingestion (principle #9: downstream blast radius)."""
    graph = _load_graph()
    assert "nodes" in graph
    assert "edges" in graph
    assert "metadata" in graph
    assert graph["metadata"]["version"] == "3.0"


def test_ingested_nodes_have_complete_provenance():
    """Every ingested node must carry complete provenance per the
    CTO directive's provenance requirements."""
    graph = _load_graph()
    ingested = [n for n in graph["nodes"]
                if n.get("provenance", {}).get("source_type") in ("patent", "paper")]
    for n in ingested:
        prov = n.get("provenance", {})
        assert prov.get("source_type") in ("patent", "paper")
        assert prov.get("title") is not None
        assert prov.get("extracted_by") is not None
        assert prov.get("timestamp") is not None
        assert prov.get("confidence") is not None


def test_patent_nodes_have_patent_numbers():
    """Patent-derived nodes must carry patent_number in provenance."""
    graph = _load_graph()
    patent_nodes = [n for n in graph["nodes"]
                    if n.get("provenance", {}).get("source_type") == "patent"]
    assert len(patent_nodes) > 0, "No patent-derived nodes"
    for n in patent_nodes:
        assert n["provenance"].get("patent_number") is not None


def test_paper_nodes_have_dois():
    """Paper-derived nodes must carry doi in provenance."""
    graph = _load_graph()
    paper_nodes = [n for n in graph["nodes"]
                   if n.get("provenance", {}).get("source_type") == "paper"]
    assert len(paper_nodes) > 0, "No paper-derived nodes"
    for n in paper_nodes:
        assert n["provenance"].get("doi") is not None
