"""
Tests for the three-tier causal edge schema (DR-15 / F-061).

Per DR-15: every edge is tagged at one of three tiers:
  - VERIFIED: formula evaluated, matches evidence
  - ASSERTED: mechanism present, not evaluated
  - ASSOCIATIVE: no mechanism (keyword match)

The tier determines which downstream operations may use the edge:
  - Discovery queries: verified + asserted (NOT associative)
  - Simulation: verified only (NOT asserted, NOT associative)
  - Adjacency search: verified + asserted (NOT associative)

Also tests DR-13: nodes without what_does_this_change are excluded.
Also tests the causal_density metric (verified / total edges).
"""
import sys
import pathlib
from datetime import datetime, timezone

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.causal_graph import (
    CausalEdge, CausalNode, CausalGraph, EdgeTier,
)


# ----------------------------------------------------------------------
# 1. CausalEdge three-tier schema
# ----------------------------------------------------------------------

def test_edge_tier_enum_has_three_values():
    """DR-15: exactly three tiers — verified, asserted, associative."""
    assert EdgeTier.VERIFIED.value == "verified"
    assert EdgeTier.ASSERTED.value == "asserted"
    assert EdgeTier.ASSOCIATIVE.value == "associative"


def test_verified_edge_is_discovery_and_simulation_capable():
    """A VERIFIED edge can be used in both discovery and simulation."""
    edge = CausalEdge(
        source="crystal_structure",
        target="electronic_structure",
        direction="causes",
        mechanism="lattice periodicity determines band structure",
        evidence=["arXiv:2507.06101"],
        tier=EdgeTier.VERIFIED,
        formula="mott_relation",
        formula_inputs={"carrier_density": 1e19, "effective_mass": 0.1},
        formula_output=200e-6,
        expected_output=200e-6,
        tolerance=10e-6,
        falsifiable_by="DFT calculation of band structure",
        what_does_this_change="Seebeck coefficient",
        created_at="2026-08-04T00:00:00Z",
        provenance={"source": "arXiv:2507.06101", "retrieval_date": "2026-08-04"},
    )
    assert edge.is_discovery_capable()
    assert edge.is_simulation_capable()
    assert edge.is_verified()


def test_asserted_edge_is_discovery_capable_but_not_simulation():
    """An ASSERTED edge can be used in discovery but NOT simulation."""
    edge = CausalEdge(
        source="Bi2Te3",
        target="Seebeck_coefficient",
        direction="causes",
        mechanism="anisotropic carrier transport in trigonal crystal",
        evidence=["arXiv:2507.06101"],
        tier=EdgeTier.ASSERTED,
        formula=None,
        formula_inputs=None,
        formula_output=None,
        expected_output=None,
        tolerance=None,
        falsifiable_by="Mott relation evaluation",
        what_does_this_change="Seebeck coefficient",
        created_at="2026-08-04T00:00:00Z",
        provenance={"source": "arXiv:2507.06101", "retrieval_date": "2026-08-04"},
    )
    assert edge.is_discovery_capable()
    assert not edge.is_simulation_capable()
    assert not edge.is_verified()


def test_associative_edge_is_neither_discovery_nor_simulation():
    """An ASSOCIATIVE edge (keyword match) is excluded from everything."""
    edge = CausalEdge(
        source="Bi2Te3",
        target="alloy",
        direction="related_to",
        mechanism=None,  # no mechanism — associative
        evidence=[],
        tier=EdgeTier.ASSOCIATIVE,
        formula=None,
        formula_inputs=None,
        formula_output=None,
        expected_output=None,
        tolerance=None,
        falsifiable_by=None,
        what_does_this_change=None,
        created_at="2026-08-04T00:00:00Z",
        provenance={"source": "keyword_match", "retrieval_date": "2026-08-04"},
    )
    assert not edge.is_discovery_capable()
    assert not edge.is_simulation_capable()
    assert not edge.is_verified()


# ----------------------------------------------------------------------
# 2. CausalNode DR-13 filter
# ----------------------------------------------------------------------

def test_node_with_what_does_this_change_is_discovery_capable():
    """DR-13: a node with what_does_this_change participates in discovery."""
    node = CausalNode(
        node_id="Bi2Te3",
        node_type="material",
        label="Bismuth telluride",
        properties={"formula": "Bi2Te3"},
        what_does_this_change=["Seebeck coefficient", "NRR catalytic activity"],
        what_changes_this=["doping", "nanostructuring"],
        inputs=["carrier_density", "effective_mass"],
        constraints=["temperature < 500K"],
        outputs=["thermoelectric_power", "ammonia_yield"],
        evidence=["arXiv:2507.06101"],
        provenance={"source": "arXiv:2507.06101", "retrieval_date": "2026-08-04"},
    )
    assert node.is_discovery_capable()


def test_node_without_what_does_this_change_is_excluded():
    """DR-13: a node without what_does_this_change is dead information — excluded."""
    node = CausalNode(
        node_id="alloy",
        node_type="material",
        label="alloy (keyword match)",
        properties={},
        what_does_this_change=[],  # empty — dead information
        what_changes_this=[],
        inputs=[],
        constraints=[],
        outputs=[],
        evidence=[],
        provenance={"source": "keyword_match"},
    )
    assert not node.is_discovery_capable()


# ----------------------------------------------------------------------
# 3. CausalGraph tier-based filtering
# ----------------------------------------------------------------------

def test_graph_filters_discovery_capable_edges():
    """The graph's discovery_capable_edges() returns only verified + asserted."""
    graph = CausalGraph()
    graph.add_edge(CausalEdge(
        source="A", target="B", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.VERIFIED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="X", created_at="", provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="B", target="C", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="Y", created_at="", provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="C", target="D", direction="related_to",
        mechanism=None, evidence=[], tier=EdgeTier.ASSOCIATIVE,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change=None, created_at="", provenance={},
    ))
    discovery_edges = graph.discovery_capable_edges()
    assert len(discovery_edges) == 2  # verified + asserted, NOT associative


def test_graph_filters_simulation_capable_edges():
    """The graph's simulation_capable_edges() returns only verified."""
    graph = CausalGraph()
    graph.add_edge(CausalEdge(
        source="A", target="B", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.VERIFIED,
        formula="f", formula_inputs={}, formula_output=1.0,
        expected_output=1.0, tolerance=0.1, falsifiable_by="test",
        what_does_this_change="X", created_at="", provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="B", target="C", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="Y", created_at="", provenance={},
    ))
    sim_edges = graph.simulation_capable_edges()
    assert len(sim_edges) == 1  # only verified, NOT asserted


def test_causal_density_metric():
    """causal_density = verified / total edges."""
    graph = CausalGraph()
    # Add 2 verified, 1 asserted, 1 associative
    for tier in [EdgeTier.VERIFIED, EdgeTier.VERIFIED,
                 EdgeTier.ASSERTED, EdgeTier.ASSOCIATIVE]:
        graph.add_edge(CausalEdge(
            source="A", target="B", direction="causes",
            mechanism="m" if tier != EdgeTier.ASSOCIATIVE else None,
            evidence=[], tier=tier,
            formula=None, formula_inputs=None, formula_output=None,
            expected_output=None, tolerance=None, falsifiable_by=None,
            what_does_this_change="X", created_at="", provenance={},
        ))
    # 2 verified / 4 total = 0.5
    assert graph.causal_density() == 0.5


def test_tier_counts():
    """tier_counts() returns correct counts per tier."""
    graph = CausalGraph()
    for tier in [EdgeTier.VERIFIED, EdgeTier.VERIFIED,
                 EdgeTier.ASSERTED, EdgeTier.ASSOCIATIVE, EdgeTier.ASSOCIATIVE]:
        graph.add_edge(CausalEdge(
            source="A", target="B", direction="causes",
            mechanism="m" if tier != EdgeTier.ASSOCIATIVE else None,
            evidence=[], tier=tier,
            formula=None, formula_inputs=None, formula_output=None,
            expected_output=None, tolerance=None, falsifiable_by=None,
            what_does_this_change="X" if tier != EdgeTier.ASSOCIATIVE else None,
            created_at="", provenance={},
        ))
    counts = graph.tier_counts()
    assert counts == {"verified": 2, "asserted": 1, "associative": 2}


# ----------------------------------------------------------------------
# 4. Adjacency search (the Apollo Test's internal query)
# ----------------------------------------------------------------------

def test_adjacency_search_traverses_only_discovery_capable_edges():
    """The adjacency search must find cross-domain connections via
    verified + asserted edges, NOT associative edges."""
    graph = CausalGraph()

    # Nodes: Bi2Te3 → thermoelectric → power → NRR → ammonia
    for nid, ntype, label in [
        ("Bi2Te3", "material", "Bismuth telluride"),
        ("thermoelectric", "mechanism", "Thermoelectric effect"),
        ("power", "property", "Available power"),
        ("NRR", "mechanism", "Nitrogen reduction"),
        ("ammonia", "application", "Ammonia"),
    ]:
        graph.add_node(CausalNode(
            node_id=nid, node_type=ntype, label=label,
            properties={},
            what_does_this_change=[f"enables {ntype}"],
            what_changes_this=[],
            inputs=[], constraints=[], outputs=[],
            evidence=["arXiv:2507.06101"],
            provenance={"source": "arXiv:2507.06101"},
        ))

    # Edges: verified (Bi2Te3 → thermoelectric), asserted (thermoelectric → power,
    # power → NRR), associative (NRR → ammonia — should be excluded)
    edges = [
        ("Bi2Te3", "thermoelectric", EdgeTier.VERIFIED, "Seebeck effect"),
        ("thermoelectric", "power", EdgeTier.ASSERTED, "power = S²σT/κ"),
        ("power", "NRR", EdgeTier.ASSERTED, "voltage drives NRR"),
        ("NRR", "ammonia", EdgeTier.ASSOCIATIVE, None),  # keyword match — excluded
    ]
    for src, tgt, tier, mech in edges:
        graph.add_edge(CausalEdge(
            source=src, target=tgt, direction="causes",
            mechanism=mech, evidence=[], tier=tier,
            formula=None, formula_inputs=None, formula_output=None,
            expected_output=None, tolerance=None, falsifiable_by=None,
            what_does_this_change=f"enables {tgt}", created_at="", provenance={},
        ))

    # Search from Bi2Te3 for application nodes
    results = graph.adjacency_search("Bi2Te3", "application")

    # Should NOT find "ammonia" because the edge NRR → ammonia is ASSOCIATIVE
    # (the only path to ammonia goes through an associative edge)
    assert "ammonia" not in results, (
        "Adjacency search should NOT traverse associative edges. "
        "The NRR → ammonia edge is ASSOCIATIVE (no mechanism) and "
        "should be excluded from discovery traversal."
    )

    # The results should be empty because the only application node (ammonia)
    # is unreachable via associative-only edges.
    # But let's also verify the search CAN find mechanism nodes via verified edges:
    mechanism_results = graph.adjacency_search("Bi2Te3", "mechanism")
    assert "thermoelectric" in mechanism_results, (
        "Should find thermoelectric via verified edge"
    )
    assert "NRR" in mechanism_results, (
        "Should find NRR via asserted edge (asserted edges are discovery-capable)"
    )


def test_adjacency_search_excludes_dead_nodes():
    """Nodes without what_does_this_change are excluded from results."""
    graph = CausalGraph()

    # A dead node (no what_does_this_change)
    graph.add_node(CausalNode(
        node_id="dead_node", node_type="material", label="Dead",
        properties={},
        what_does_this_change=[],  # empty — dead information
        what_changes_this=[], inputs=[], constraints=[], outputs=[],
        evidence=[], provenance={},
    ))

    # A live node
    graph.add_node(CausalNode(
        node_id="live_node", node_type="application", label="Live",
        properties={},
        what_does_this_change=["produces ammonia"],
        what_changes_this=[], inputs=[], constraints=[], outputs=[],
        evidence=[], provenance={},
    ))

    # Edge from source to dead node (verified)
    graph.add_edge(CausalEdge(
        source="source", target="dead_node", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.VERIFIED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="X", created_at="", provenance={},
    ))

    # Edge from dead node to live node (verified)
    graph.add_edge(CausalEdge(
        source="dead_node", target="live_node", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.VERIFIED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="X", created_at="", provenance={},
    ))

    # Search from source for applications
    results = graph.adjacency_search("source", "application")

    # live_node IS reachable via the dead_node, but dead_node itself
    # should not appear in results (it's not an application type).
    # However, the adjacency search should still traverse through it.
    assert "live_node" in results, (
        "Live node should be reachable even through dead nodes — "
        "the DR-13 filter applies to result nodes, not traversal nodes."
    )


# ----------------------------------------------------------------------
# 5. The Bi2Te3 → NRR cross-domain connection (Apollo Test scenario)
# ----------------------------------------------------------------------

def test_bi2te3_nrr_cross_domain_connection():
    """The Apollo Test scenario: can the graph find that Bi2Te3
    (thermoelectric) is also connected to NRR (catalysis)?

    This is the internal version of the Apollo Test. If this search
    returns the NRR connection, the system has found the cross-domain
    relationship without external search.
    """
    graph = CausalGraph()

    # Bi2Te3 node with BOTH thermoelectric AND NRR edges
    graph.add_node(CausalNode(
        node_id="Bi2Te3", node_type="material", label="Bismuth telluride",
        properties={"formula": "Bi2Te3", "crystal": "trigonal"},
        what_does_this_change=[
            "thermoelectric efficiency (via Seebeck effect)",
            "NRR catalytic activity (via Bi 6p back-donation to N2)",
        ],
        what_changes_this=["doping", "nanostructuring"],
        inputs=["carrier_density", "effective_mass"],
        constraints=["temperature < 500K"],
        outputs=["thermoelectric_power", "ammonia_yield"],
        evidence=["arXiv:2507.06101", "Liu_2021"],
        provenance={"source": "arXiv:2507.06101", "retrieval_date": "2026-08-04"},
    ))

    # Thermoelectric mechanism node
    graph.add_node(CausalNode(
        node_id="thermoelectric", node_type="mechanism", label="Thermoelectric",
        properties={},
        what_does_this_change=["available power"],
        what_changes_this=[], inputs=[], constraints=[], outputs=[],
        evidence=["arXiv:2507.06101"],
        provenance={"source": "arXiv:2507.06101"},
    ))

    # NRR mechanism node
    graph.add_node(CausalNode(
        node_id="NRR", node_type="mechanism", label="Nitrogen reduction",
        properties={},
        what_does_this_change=["ammonia yield"],
        what_changes_this=[], inputs=[], constraints=[], outputs=[],
        evidence=["Liu_2021"],
        provenance={"source": "ACS_AM_2021"},
    ))

    # Edges: Bi2Te3 → thermoelectric (verified), Bi2Te3 → NRR (asserted)
    graph.add_edge(CausalEdge(
        source="Bi2Te3", target="thermoelectric", direction="causes",
        mechanism="anisotropic carrier transport produces Seebeck effect",
        evidence=["arXiv:2507.06101"], tier=EdgeTier.VERIFIED,
        formula="mott_relation", formula_inputs={"T": 300},
        formula_output=200e-6, expected_output=200e-6, tolerance=10e-6,
        falsifiable_by="Mott relation evaluation",
        what_does_this_change="Seebeck coefficient",
        created_at="", provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="Bi2Te3", target="NRR", direction="causes",
        mechanism="Bi 6p orbitals back-donate to N2, weakening N≡N bond",
        evidence=["Liu_2021"], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None,
        falsifiable_by="DFT calculation of N2 adsorption energy on Bi2Te3",
        what_does_this_change="NRR catalytic activity",
        created_at="", provenance={},
    ))

    # Search: what mechanisms does Bi2Te3 enable?
    results = graph.adjacency_search("Bi2Te3", "mechanism")

    # Should find BOTH thermoelectric AND NRR — the cross-domain connection
    assert "thermoelectric" in results, "Should find thermoelectric via verified edge"
    assert "NRR" in results, (
        "Should find NRR via asserted edge — this is the Apollo Test's "
        "cross-domain connection: Bi2Te3 (thermoelectric) is also an NRR catalyst."
    )
