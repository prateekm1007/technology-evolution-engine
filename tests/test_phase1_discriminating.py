"""
Discriminating tests for Phase 1 bug fixes (cycle 54).

Per External Auditor Phase 1: "Add a discriminating test that asserts
two structurally-different chains score differently — the current test
suite can't catch this bug because no test checks that the score varies."

These tests verify:
  1. Gentner systematicity is NOT constant — chains with different edge-type
     sequences score differently.
  2. Swanson score is NOT constant — bridges with different edge tiers
     score differently.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.discovery_graph import (
    DiscoveryGraph, DiscoveryNode, DiscoveryEdge, Evidence, RelationType,
    SwansonBridgeSearch, GentnerStructureMapping,
)


class TestGentnerSystematicityIsNonConstant:
    """Verify Gentner systematicity varies across different chain structures."""

    def test_chains_with_different_edge_types_score_differently(self):
        """Two chains with different edge-type sequences must score differently.

        Per Auditor: "the current test suite can't catch this bug because
        no test checks that the score varies."

        We create 3 chains:
        - Chain 1: A→B→C with [mechanism, mechanism]
        - Chain 2: X→Y→Z with [mechanism, mechanism] (same as Chain 1)
        - Chain 3: P→Q→R with [association, association] (different)

        Analogies:
        - Chain 1 vs Chain 2: systematicity = 1.0 (all match)
        - Chain 1 vs Chain 3: systematicity = 0.0 (none match)
        So systematicity is NOT constant.
        """
        dg = DiscoveryGraph()

        # Chain 1: A→B→C with MECHANISM edges
        for nid in ['A', 'B', 'C']:
            dg.add_node(DiscoveryNode(node_id=nid, node_type='concept', label=nid,
                                       layers={RelationType.MECHANISM}))
        dg.add_edge(DiscoveryEdge(source='A', target='B', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))
        dg.add_edge(DiscoveryEdge(source='B', target='C', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))

        # Chain 2: X→Y→Z with MECHANISM edges (same type as Chain 1)
        for nid in ['X', 'Y', 'Z']:
            dg.add_node(DiscoveryNode(node_id=nid, node_type='concept', label=nid,
                                       layers={RelationType.MECHANISM}))
        dg.add_edge(DiscoveryEdge(source='X', target='Y', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))
        dg.add_edge(DiscoveryEdge(source='Y', target='Z', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))

        # Chain 3: P→Q→R with ASSOCIATION edges (different from Chains 1, 2)
        for nid in ['P', 'Q', 'R']:
            dg.add_node(DiscoveryNode(node_id=nid, node_type='concept', label=nid,
                                       layers={RelationType.ASSOCIATION}))
        dg.add_edge(DiscoveryEdge(source='P', target='Q', relation_type=RelationType.ASSOCIATION,
                                  evidence=Evidence(provenance='test', source_count=1)))
        dg.add_edge(DiscoveryEdge(source='Q', target='R', relation_type=RelationType.ASSOCIATION,
                                  evidence=Evidence(provenance='test', source_count=1)))

        analogies = GentnerStructureMapping.find_analogous_chains(dg, min_chain_length=2)
        assert len(analogies) > 0, "should find at least one analogy"

        # The systematicity values should NOT all be the same
        systematicities = [a['systematicity'] for a in analogies]
        unique_values = set(systematicities)
        assert len(unique_values) > 1, (
            f"Gentner systematicity is constant ({unique_values}) — "
            f"the Phase 1 bug is NOT fixed. All analogies score the same."
        )

    def test_identical_edge_type_sequences_score_high(self):
        """Two chains with the same edge-type sequence score systematicity=1.0."""
        dg = DiscoveryGraph()
        # Two chains, both all-MECHANISM
        for nid in ['A', 'B', 'C', 'X', 'Y', 'Z']:
            dg.add_node(DiscoveryNode(node_id=nid, node_type='concept', label=nid,
                                       layers={RelationType.MECHANISM}))
        dg.add_edge(DiscoveryEdge(source='A', target='B', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))
        dg.add_edge(DiscoveryEdge(source='B', target='C', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))
        dg.add_edge(DiscoveryEdge(source='X', target='Y', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))
        dg.add_edge(DiscoveryEdge(source='Y', target='Z', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))

        analogies = GentnerStructureMapping.find_analogous_chains(dg, min_chain_length=2)
        # Find the A→B→C vs X→Y→Z analogy
        for a in analogies:
            if set(a['chain_a']) == {'A', 'B', 'C'} and set(a['chain_b']) == {'X', 'Y', 'Z'}:
                assert a['systematicity'] == 1.0, (
                    f"identical edge-type sequences should score 1.0, got {a['systematicity']}"
                )
                return
        # If we didn't find it, the test setup is wrong
        assert False, "did not find the A→B→C vs X→Y→Z analogy"


class TestSwansonScoreIsNonConstant:
    """Verify Swanson bridge scores vary by edge tier."""

    def test_bridges_with_different_edge_tiers_score_differently(self):
        """Bridges built from MECHANISM edges should score higher than
        bridges built from ASSOCIATION edges."""
        dg = DiscoveryGraph()

        # Path 1: A→B→C with MECHANISM edges (high weight)
        for nid in ['A', 'B', 'C']:
            dg.add_node(DiscoveryNode(node_id=nid, node_type='concept', label=nid,
                                       layers={RelationType.MECHANISM}))
        dg.add_edge(DiscoveryEdge(source='A', target='B', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))
        dg.add_edge(DiscoveryEdge(source='B', target='C', relation_type=RelationType.MECHANISM,
                                  evidence=Evidence(provenance='test', source_count=1)))

        # Path 2: X→Y→Z with ASSOCIATION edges (low weight)
        for nid in ['X', 'Y', 'Z']:
            dg.add_node(DiscoveryNode(node_id=nid, node_type='concept', label=nid,
                                       layers={RelationType.ASSOCIATION}))
        dg.add_edge(DiscoveryEdge(source='X', target='Y', relation_type=RelationType.ASSOCIATION,
                                  evidence=Evidence(provenance='test', source_count=1)))
        dg.add_edge(DiscoveryEdge(source='Y', target='Z', relation_type=RelationType.ASSOCIATION,
                                  evidence=Evidence(provenance='test', source_count=1)))

        bridges = SwansonBridgeSearch.search(dg)
        assert len(bridges) >= 2

        scores = [b['score'] for b in bridges]
        unique_scores = set(scores)
        assert len(unique_scores) > 1, (
            f"Swanson score is constant ({unique_scores}) — "
            f"the Phase 1 bug is NOT fixed. All bridges score the same."
        )

        # The MECHANISM bridge (A→B→C) should score higher than the
        # ASSOCIATION bridge (X→Y→Z)
        mechanism_bridge = [b for b in bridges if b['a'] == 'A' and b['c'] == 'C']
        association_bridge = [b for b in bridges if b['a'] == 'X' and b['c'] == 'Z']
        if mechanism_bridge and association_bridge:
            assert mechanism_bridge[0]['score'] > association_bridge[0]['score'], (
                f"MECHANISM bridge ({mechanism_bridge[0]['score']}) should outrank "
                f"ASSOCIATION bridge ({association_bridge[0]['score']})"
            )
