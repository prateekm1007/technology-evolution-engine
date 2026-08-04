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
    CausalEdge, CausalNode, CausalGraph, EdgeTier, MechanismStatus,
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
        mechanism_status=MechanismStatus.DERIVED, intervention=None, counterfactual=None,
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
        mechanism_status=MechanismStatus.DERIVED, intervention=None, counterfactual=None,
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
        mechanism_status=None, intervention=None, counterfactual=None,
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
        what_does_this_change="X", mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="B", target="C", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="Y", mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="C", target="D", direction="related_to",
        mechanism=None, evidence=[], tier=EdgeTier.ASSOCIATIVE,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change=None, mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
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
        what_does_this_change="X", mechanism_status=MechanismStatus.DERIVED, intervention=None, counterfactual=None, created_at="", provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="B", target="C", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="Y", mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
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
            what_does_this_change="X", mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
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
            mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
        ))
    counts = graph.tier_counts()
    assert counts == {"verified": 2, "asserted": 1, "associative": 2, "contradicted": 0}


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
            what_does_this_change=f"enables {tgt}", mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
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
        what_does_this_change="X", mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
    ))

    # Edge from dead node to live node (verified)
    graph.add_edge(CausalEdge(
        source="dead_node", target="live_node", direction="causes",
        mechanism="test", evidence=[], tier=EdgeTier.VERIFIED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="X", mechanism_status=None, intervention=None, counterfactual=None, created_at="", provenance={},
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
        mechanism_status=MechanismStatus.DERIVED, intervention=None, counterfactual=None, created_at="", provenance={},
    ))
    graph.add_edge(CausalEdge(
        source="Bi2Te3", target="NRR", direction="causes",
        mechanism="Bi 6p orbitals back-donate to N2, weakening N≡N bond",
        evidence=["Liu_2021"], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None,
        falsifiable_by="DFT calculation of N2 adsorption energy on Bi2Te3",
        what_does_this_change="NRR catalytic activity",
        mechanism_status=None, intervention=None, counterfactual=None,
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


# ----------------------------------------------------------------------
# 6. DR-15 (revised): Four-state mechanism schema
# ----------------------------------------------------------------------

def test_mechanism_status_enum_has_four_values():
    """DR-15 (revised): observed, simulated, derived, asserted."""
    from invention_compiler.causal_graph import MechanismStatus
    assert MechanismStatus.OBSERVED.value == "observed"
    assert MechanismStatus.SIMULATED.value == "simulated"
    assert MechanismStatus.DERIVED.value == "derived"
    assert MechanismStatus.ASSERTED.value == "asserted"


def test_observed_mechanism_is_simulation_capable():
    """An observed mechanism (reproduced experimentally) can be simulated."""
    from invention_compiler.causal_graph import MechanismStatus
    edge = CausalEdge(
        source="A", target="B", direction="causes",
        mechanism="test", mechanism_status=MechanismStatus.OBSERVED,
        evidence=[], tier=EdgeTier.VERIFIED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="X", intervention=None, counterfactual=None,
        created_at="", provenance={},
    )
    assert edge.is_simulation_capable()


def test_asserted_mechanism_is_not_simulation_capable():
    """An asserted mechanism (described but not verified) cannot be simulated."""
    from invention_compiler.causal_graph import MechanismStatus
    edge = CausalEdge(
        source="A", target="B", direction="causes",
        mechanism="test", mechanism_status=MechanismStatus.ASSERTED,
        evidence=[], tier=EdgeTier.VERIFIED,  # tier is VERIFIED but status is ASSERTED
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="X", intervention=None, counterfactual=None,
        created_at="", provenance={},
    )
    # Even though tier=VERIFIED, the mechanism_status=ASSERTED means
    # this edge cannot be used in simulation (DR-15 revised).
    assert not edge.is_simulation_capable()


# ----------------------------------------------------------------------
# 7. DR-16: Intervention principle
# ----------------------------------------------------------------------

def test_intervention_dataclass():
    """DR-16: an intervention specifies what to change and what happens."""
    from invention_compiler.causal_graph import Intervention
    iv = Intervention(
        node="carrier_density",
        intervention="increase_5_percent",
        predicted_effect="increase_seebeck",
        expected_magnitude="2.5% increase in S",
        uncertainty="±0.5%",
    )
    assert iv.node == "carrier_density"
    assert iv.intervention == "increase_5_percent"
    assert iv.predicted_effect == "increase_seebeck"


def test_edge_with_intervention_is_causal():
    """DR-16: an edge with an intervention is causal (not just a mechanism)."""
    from invention_compiler.causal_graph import Intervention, Counterfactual
    edge = CausalEdge(
        source="carrier_density", target="seebeck_coefficient", direction="causes",
        mechanism="Mott relation", mechanism_status=None,
        evidence=[], tier=EdgeTier.VERIFIED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by="Mott relation evaluation",
        what_does_this_change="Seebeck coefficient",
        intervention=Intervention(
            node="carrier_density", intervention="increase_5_percent",
            predicted_effect="increase_seebeck", expected_magnitude="2.5%",
            uncertainty="±0.5%",
        ),
        counterfactual=Counterfactual(
            positive_case="If carrier density increases, Seebeck increases",
            negative_case="If carrier density does not change, Seebeck does not change",
        ),
        created_at="", provenance={},
    )
    assert edge.is_causal()


def test_edge_without_intervention_is_not_causal():
    """DR-16: an edge without intervention is a mechanism, not causality."""
    edge = CausalEdge(
        source="A", target="B", direction="causes",
        mechanism="test", mechanism_status=None,
        evidence=[], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="X",
        intervention=None,  # no intervention — mechanism, not causality
        counterfactual=None,
        created_at="", provenance={},
    )
    assert not edge.is_causal()


# ----------------------------------------------------------------------
# 8. DR-17: Counterfactual requirement
# ----------------------------------------------------------------------

def test_counterfactual_dataclass():
    """DR-17: a counterfactual has both positive and negative cases."""
    from invention_compiler.causal_graph import Counterfactual
    cf = Counterfactual(
        positive_case="If X changes: Y changes",
        negative_case="If X does not change: Y does not change",
    )
    assert "changes" in cf.positive_case
    assert "does not change" in cf.negative_case


def test_edge_with_counterfactual_but_no_intervention_is_not_causal():
    """DR-16 + DR-17: both intervention AND counterfactual are required for causality."""
    from invention_compiler.causal_graph import Counterfactual
    edge = CausalEdge(
        source="A", target="B", direction="causes",
        mechanism="test", mechanism_status=None,
        evidence=[], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change="X",
        intervention=None,  # missing intervention
        counterfactual=Counterfactual(
            positive_case="If A changes: B changes",
            negative_case="If A does not change: B does not change",
        ),
        created_at="", provenance={},
    )
    assert not edge.is_causal()  # needs BOTH intervention AND counterfactual


# ----------------------------------------------------------------------
# 9. DR-18: Experiment proposal (the system's primary output)
# ----------------------------------------------------------------------

def test_experiment_proposal_dataclass():
    """DR-18: the system's primary output is the next experiment."""
    from invention_compiler.causal_graph import ExperimentProposal, Intervention
    exp = ExperimentProposal(
        prediction="Bi2Te3 will catalyze NRR at FE > 30%",
        intervention=Intervention(
            node="Bi2Te3_loading", intervention="deposit_1mg_cm2",
            predicted_effect="NRR_catalysis", expected_magnitude="32 μg/h/mg",
            uncertainty="±5 μg/h/mg",
        ),
        measurement="NH3 yield via Nessler reagent colorimetry",
        falsification="NH3 yield < 10 μg/h/mg OR FE < 15%",
        cost_usd=500.0,
        timeline_days=3,
        learning_if_pass="Bi2Te3 is a viable dual-function material for passive NRR",
        learning_if_fail="Bi2Te3 thermoelectric properties do not translate to NRR catalysis in this configuration",
    )
    assert exp.prediction == "Bi2Te3 will catalyze NRR at FE > 30%"
    assert exp.cost_usd == 500.0
    assert exp.learning_if_fail != ""  # must learn from failure too


# ----------------------------------------------------------------------
# 10. The three-level distinction (relationship vs mechanism vs causality)
# ----------------------------------------------------------------------

def test_relationship_vs_mechanism_vs_causality():
    """CEO cycle 30: relationships, mechanisms, and causality are three
    different things. The schema must distinguish them.

    Relationship: what is connected? (no mechanism, no intervention)
    Mechanism: how is it connected? (mechanism present, no intervention)
    Causality: what changes when I intervene? (mechanism + intervention + counterfactual)
    """
    from invention_compiler.causal_graph import Intervention, Counterfactual

    # RELATIONSHIP: Bi2Te3 ↔ thermoelectrics (no mechanism, no intervention)
    relationship = CausalEdge(
        source="Bi2Te3", target="thermoelectrics", direction="related_to",
        mechanism=None, mechanism_status=None,
        evidence=[], tier=EdgeTier.ASSOCIATIVE,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by=None,
        what_does_this_change=None,
        intervention=None, counterfactual=None,
        created_at="", provenance={},
    )
    assert not relationship.is_discovery_capable()  # associative — excluded
    assert not relationship.is_causal()  # no intervention

    # MECHANISM: carrier mobility affects Seebeck (mechanism present, no intervention)
    mechanism_edge = CausalEdge(
        source="carrier_mobility", target="seebeck_coefficient", direction="causes",
        mechanism="Mott relation: S depends on d(ln σ)/dE",
        mechanism_status=None,
        evidence=["arXiv:2507.06101"], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by="Mott relation evaluation",
        what_does_this_change="Seebeck coefficient",
        intervention=None,  # no intervention — mechanism, not causality
        counterfactual=None,
        created_at="", provenance={},
    )
    assert mechanism_edge.is_discovery_capable()  # can be used for hypothesis
    assert not mechanism_edge.is_causal()  # no intervention — not causality

    # CAUSALITY: doping changes ammonia yield (mechanism + intervention + counterfactual)
    causal_edge = CausalEdge(
        source="doping_concentration", target="ammonia_yield", direction="causes",
        mechanism="Bi 6p back-donation to N2 weakens N≡N bond",
        mechanism_status=None,
        evidence=["Liu_2021"], tier=EdgeTier.ASSERTED,
        formula=None, formula_inputs=None, formula_output=None,
        expected_output=None, tolerance=None, falsifiable_by="DFT N2 adsorption energy",
        what_does_this_change="ammonia yield",
        intervention=Intervention(
            node="doping_concentration", intervention="increase_5_percent",
            predicted_effect="increase_ammonia_yield",
            expected_magnitude="3% increase in NH3 yield",
            uncertainty="±1%",
        ),
        counterfactual=Counterfactual(
            positive_case="If doping increases, ammonia yield increases",
            negative_case="If doping does not change, ammonia yield does not change",
        ),
        created_at="", provenance={},
    )
    assert causal_edge.is_discovery_capable()  # can be used for discovery
    assert causal_edge.is_causal()  # HAS intervention + counterfactual — true causality
