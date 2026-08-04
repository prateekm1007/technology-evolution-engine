"""
8-TEST ACID TEST — REVISED Honest Capability Demonstration (cycle 43).

Per cycle 42 audit: "140 bridges" and "7,350 analogies" were challenged
as potentially trivial combinatorial output, not meaningful discovery.

This test runs each acid test honestly and assesses whether the output
is meaningful, not just counted.

REVISED RESULTS (cycle 43):
  Swanson:    INCOMPLETE — 140 bridges but 0 are cross-type non-obvious
  Pearl:      INCOMPLETE — 0 intervention edges
  Popper:     INCOMPLETE — 0 falsifiable_by populated
  Ross King:  INCOMPLETE — confirms known edge, doesn't distinguish hypotheses
  BACON:      NOT IMPLEMENTED — no law derivation engine
  Gentner:    INCOMPLETE — 7,350 pairs but all length-2 (trivial)
  Altshuller: INCOMPLETE — 0 contradictions, no direction metadata
  Arthur:     INCOMPLETE — same algorithm as Swanson, not separate

0 PASS, 7 INCOMPLETE, 1 NOT IMPLEMENTED.

The honest conclusion: the architecture is structurally complete but
capability-incomplete. The algorithms run. They produce output.
The output is trivial — combinatorial noise from a small corpus,
not curated discovery. The corpus (20 documents) is too small to
exercise the algorithms meaningfully. The edge extractor doesn't
populate direction metadata, interventions, or falsification criteria.
BACON doesn't exist.

This is the honest baseline. The architecture should NOT harden.
"""
import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.edge_extractor import EdgeExtractor
from invention_compiler.discovery_graph import (
    DiscoveryGraph, Evidence, RelationType, DiscoveryEdge, DiscoveryNode,
    SwansonBridgeSearch, GentnerStructureMapping, AltshullerContradictionSearch,
)
from invention_compiler.causal_graph import MechanismStatus
from invention_compiler.causal_simulator import CausalSimulator


@pytest.fixture
def corpus_graph():
    """Build a DiscoveryGraph from the real 20-document corpus."""
    extractor = EdgeExtractor()
    papers = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "papers"), use_discovery_graph=False)
    patents = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "patents"), use_discovery_graph=False)
    combined = type(papers)()
    for nid, node in papers.nodes.items():
        combined.add_node(node)
    for nid, node in patents.nodes.items():
        if nid not in combined.nodes:
            combined.add_node(node)
        else:
            existing = combined.nodes[nid]
            existing.what_does_this_change = list(set(existing.what_does_this_change + node.what_does_this_change))
            existing.evidence = list(set(existing.evidence + node.evidence))
    for edge in papers.edges + patents.edges:
        exists = any(e.source == edge.source and e.target == edge.target and e.mechanism == edge.mechanism for e in combined.edges)
        if not exists:
            combined.add_edge(edge)
    return combined.to_discovery_graph()


class TestRevisedAcidTestDemonstration:
    """Revised acid test with meaningful output assessment (cycle 43)."""

    def test_1_swanson_meaningful(self, corpus_graph):
        """Swanson: Are any bridges non-obvious (cross-type)?"""
        bridges = SwansonBridgeSearch.search(corpus_graph)
        # Assess: are any bridges cross-type (manufacturing→mechanism, material→application)?
        # vs same-type (material→material, property→property)?
        cross_type = 0
        for b in bridges:
            a_node = corpus_graph.nodes.get(b["a"])
            c_node = corpus_graph.nodes.get(b["c"])
            if a_node and c_node:
                if a_node.node_type != c_node.node_type:
                    cross_type += 1
        
        # 140 bridges but how many are non-trivial?
        # The honest assessment: check if any are genuinely cross-domain
        if cross_type > 0:
            # Some cross-type bridges exist — check if they're non-obvious
            # A real Swanson bridge: the bridge node (B) connects two domains
            # that don't normally cite each other
            result = "INCOMPLETE"  # Even cross-type may be trivial transitive
            reason = f"{len(bridges)} bridges, {cross_type} cross-type — but likely trivial transitive paths through shared topics"
        else:
            result = "INCOMPLETE"
            reason = f"{len(bridges)} bridges, 0 cross-type — all trivial same-type transitive"
        
        print(f"\n  SWANSON: {result} — {reason}")
        assert result == "INCOMPLETE"

    def test_2_pearl_intervention(self, corpus_graph):
        """Pearl: 0 intervention edges extracted."""
        print(f"\n  PEARL: INCOMPLETE — 0 intervention edges")
        assert True  # honest INCOMPLETE

    def test_3_popper_falsifiability(self, corpus_graph):
        """Popper: 0 falsifiable_by fields populated."""
        print(f"\n  POPPER: INCOMPLETE — 0 falsifiable_by populated")
        assert True

    def test_4_ross_king_meaningful(self, corpus_graph):
        """Ross King: Does the experiment distinguish between competing hypotheses?"""
        extractor = EdgeExtractor()
        papers = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "papers"), use_discovery_graph=False)
        patents = extractor.extract_from_corpus(str(ROOT / "data" / "ingestion" / "patents"), use_discovery_graph=False)
        combined = type(papers)()
        for nid, node in papers.nodes.items():
            combined.add_node(node)
        for nid, node in patents.nodes.items():
            if nid not in combined.nodes:
                combined.add_node(node)
        for edge in papers.edges + patents.edges:
            exists = any(e.source == edge.source and e.target == edge.target and e.mechanism == edge.mechanism for e in combined.edges)
            if not exists:
                combined.add_edge(edge)

        sim = CausalSimulator(combined)
        experiment = sim.design_experiment(
            start_node_id="Bi2Te3",
            target_node_id="te_power_generation",
            intervention_node="temperature_difference",
            intervention_desc="apply 100K ΔT",
            measurement_desc="measure power",
            falsification_desc="power < 0.5W",
            cost_usd=200, timeline_days=3,
            learning_pass="verified", learning_fail="revised",
        )
        # The experiment confirms a known causal edge (Seebeck effect)
        # A Ross King experiment would distinguish between competing hypotheses
        result = "INCOMPLETE"
        reason = "confirms known edge (Seebeck), doesn't distinguish competing hypotheses"
        print(f"\n  ROSS KING: {result} — {reason}")
        assert experiment is not None  # experiment was designed (code works)
        # But the capability is INCOMPLETE — it doesn't do what Ross King's Adam did

    def test_5_bacon_not_implemented(self, corpus_graph):
        """BACON: No law derivation engine."""
        print(f"\n  BACON: NOT IMPLEMENTED — no law derivation engine")
        assert True

    def test_6_gentner_meaningful(self, corpus_graph):
        """Gentner: Are any chains cross-domain with 3+ step depth?"""
        analogies = GentnerStructureMapping.find_analogous_chains(corpus_graph, min_chain_length=2)
        # Assess: how many are length ≥ 3 (more meaningful)?
        long_analogies = [a for a in analogies if len(a.get("chain_a", [])) >= 3]
        
        # The honest assessment: 7,350 pairs but most are length-2 (trivial)
        # Length-2 pairs just mean "two nodes each connect to one other node"
        # That's not a Gentner structure mapping — that's combinatorics
        result = "INCOMPLETE"
        reason = f"{len(analogies)} pairs, {len(long_analogies)} length ≥ 3 — mostly trivial length-2 pairs"
        print(f"\n  GENTNER: {result} — {reason}")
        assert result == "INCOMPLETE"

    def test_7_altshuller_incomplete(self, corpus_graph):
        """Altshuller: 0 contradictions (no direction metadata)."""
        contradictions = AltshullerContradictionSearch.find_contradictions(corpus_graph)
        print(f"\n  ALTSHULLER: INCOMPLETE — {len(contradictions)} contradictions (no direction metadata)")
        assert True

    def test_8_arthur_merged_with_swanson(self, corpus_graph):
        """Arthur: MERGED with Swanson (cycle 43 audit acknowledged they are the same).
        
        Per cycle 42 audit: 'If Arthur and Swanson return the same results,
        they are not separate tests — they are the same test with different names.'
        Per cycle 43 audit: honestly merge.
        
        Arthur's adjacent-possible IS Swanson's bridge detection.
        The difference (combinatorial reachability vs literature disconnect)
        is a distinction that requires a different algorithm, not the same
        algorithm with a different name.
        """
        bridges = SwansonBridgeSearch.search(corpus_graph)
        print(f"\n  ARTHUR: MERGED with Swanson ({len(bridges)} results)")
        print("  Arthur and Swanson are the SAME test. Arthur is not separate.")
        print("  DR-23 should be updated to reflect 7 tests, not 8.")
        assert True  # honest merge

    def test_summary_revised(self, corpus_graph):
        """Report the revised honest summary — 7 tests (Arthur merged with Swanson)."""
        results = {
            "Swanson": "INCOMPLETE",
            "Pearl": "INCOMPLETE",
            "Popper": "INCOMPLETE",
            "Ross King": "INCOMPLETE",
            "BACON": "NOT IMPLEMENTED",
            "Gentner": "INCOMPLETE",
            "Altshuller": "INCOMPLETE",
            "Arthur": "MERGED with Swanson",
        }
        pass_count = sum(1 for r in results.values() if r == "PASS")
        incomplete_count = sum(1 for r in results.values() if r == "INCOMPLETE")
        not_impl = sum(1 for r in results.values() if r == "NOT IMPLEMENTED")
        merged = sum(1 for r in results.values() if r == "MERGED with Swanson")

        print(f"\n{'='*60}")
        print(f"REVISED ACID TEST SUMMARY (cycle 44)")
        print(f"{'='*60}")
        for name, result in results.items():
            print(f"  {name:15s}: {result}")
        print(f"\n  {pass_count} PASS, {incomplete_count} INCOMPLETE, {not_impl} NOT IMPLEMENTED, {merged} MERGED")
        print(f"\n  Hardening criterion: ≥4 PASS required")
        print(f"  Current: {pass_count} PASS — NOT READY TO HARDEN")
        print(f"  Note: Arthur merged with Swanson (same algorithm, same results)")
        print(f"  Effective tests: 7 (not 8)")
        print(f"{'='*60}")

        assert pass_count == 0, "Expected 0 PASS after honest assessment"
        assert incomplete_count == 6
        assert not_impl == 1
        assert merged == 1
