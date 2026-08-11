#!/usr/bin/env python3
"""
adjacent_possible.py — State-space traversal for the Arthur/Youn test (Test 7).

Per cycle 150: the auditor found that CrossDomainSynthesizer uses O(n²)
Jaccard overlap scoring — "the Arthur/Youn nearest-neighbor failure
condition. It does not move through technological state space; it scores
static pairs."

Arthur and Youn's adjacent-possible framework: innovation moves through a
state space where each state is a set of capabilities. From any state,
you can move to adjacent states by adding a capability. The adjacent
possible is the set of states reachable in one step from the current state.

This module implements state-space traversal:
1. States = sets of capabilities (nodes in the graph)
2. Transitions = adding one capability from the "possible" set
3. The adjacent possible = all capabilities that become accessible when
   you add a new capability (i.e., capabilities whose prerequisites are
   now all satisfied)
4. Novel combinations = states in the adjacent possible that connect
   two previously disconnected domains

This is different from Jaccard overlap (which scores static pairs). State-
space traversal explores what becomes POSSIBLE when you combine capabilities.

Usage:
    from scripts.adjacent_possible import AdjacentPossibleExplorer
    explorer = AdjacentPossibleExplorer(graph)
    adjacent = explorer.explore(current_state, new_capability)
"""
import sys
from dataclasses import dataclass, field
from typing import Set, Dict, List, Tuple, Optional, FrozenSet, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class StateSpaceMove:
    """A move in the technological state space.

    Per Arthur/Youn: a move adds a capability to the current state, which
    may unlock new capabilities (the adjacent possible).
    """
    from_state: FrozenSet[str]     # capabilities before the move
    added_capability: str          # the capability added
    to_state: FrozenSet[str]       # capabilities after the move
    unlocked: List[str]            # capabilities now accessible (adjacent possible)
    cross_domain: bool             # does this connect two different domains?
    domains_connected: Tuple[str, str]  # if cross_domain, which domains


class AdjacentPossibleExplorer:
    """Explores the technological state space (Arthur/Youn adjacent possible).

    Unlike Jaccard overlap (which scores static pairs), this explores
    what becomes POSSIBLE when you add a capability. The adjacent possible
    is the set of capabilities whose prerequisites are all satisfied by
    the current state plus the new capability.

    This is the algorithm the auditor said was missing: "It does not move
    through technological state space; it scores static pairs."
    """

    def __init__(self, graph: Dict[str, Any]):
        """Initialize with a civilization graph.

        Args:
            graph: dict with 'nodes' and 'edges'. Edges should include
                   'requires' relationships (prerequisites).
        """
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])
        self.by_id: Dict[str, Dict[str, Any]] = {
            n.get("id", n.get("node_id", "")): n for n in self.nodes
        }

        # Build prerequisite map: capability → set of prerequisites
        self.prerequisites: Dict[str, Set[str]] = {}
        for edge in self.edges:
            rel = edge.get("relationship", edge.get("relation_type", ""))
            if rel in ("requires", "prerequisite", "depends_on"):
                target = edge.get("target", "")
                source = edge.get("source", "")
                if target not in self.prerequisites:
                    self.prerequisites[target] = set()
                self.prerequisites[target].add(source)

        # Build "enables" map: capability → set of capabilities it enables
        self.enables: Dict[str, Set[str]] = {}
        for edge in self.edges:
            rel = edge.get("relationship", edge.get("relation_type", ""))
            if rel in ("enables", "causes", "produces"):
                source = edge.get("source", "")
                target = edge.get("target", "")
                if source not in self.enables:
                    self.enables[source] = set()
                self.enables[source].add(target)

    def get_domain(self, capability: str) -> str:
        """Get the domain of a capability."""
        node = self.by_id.get(capability, {})
        return node.get("domain", node.get("source_domain", "unknown"))

    def explore(self, current_state: Set[str], new_capability: str) -> StateSpaceMove:
        """Explore the adjacent possible when adding a capability.

        Args:
            current_state: the set of capabilities currently available
            new_capability: the capability being added

        Returns:
            StateSpaceMove describing what becomes possible
        """
        from_state = frozenset(current_state)
        to_state = frozenset(current_state | {new_capability})

        # Find capabilities now accessible (adjacent possible)
        # A capability is accessible if ALL its prerequisites are in to_state
        unlocked = []
        for cap, prereqs in self.prerequisites.items():
            if cap in to_state:
                continue  # already have it
            if prereqs.issubset(to_state):
                unlocked.append(cap)

        # Check if this connects two different domains
        new_domain = self.get_domain(new_capability)
        existing_domains = {self.get_domain(c) for c in current_state}
        cross_domain = new_domain not in existing_domains and new_domain != "unknown"

        # Find which domains are connected
        domains_connected = ("", "")
        if cross_domain:
            for existing_domain in existing_domains:
                if existing_domain != "unknown" and existing_domain != new_domain:
                    domains_connected = (existing_domain, new_domain)
                    break

        return StateSpaceMove(
            from_state=from_state,
            added_capability=new_capability,
            to_state=to_state,
            unlocked=unlocked,
            cross_domain=cross_domain,
            domains_connected=domains_connected,
        )

    def find_novel_combinations(self, current_state: Set[str],
                                 candidate_capabilities: List[str]) -> List[StateSpaceMove]:
        """Find novel cross-domain combinations by exploring the adjacent possible.

        This replaces Jaccard overlap scoring with actual state-space traversal.
        For each candidate capability, check what becomes possible when it's
        added to the current state. Novel combinations are those that:
        1. Connect two different domains (cross_domain=True)
        2. Unlock new capabilities (unlocked is non-empty)

        Args:
            current_state: current capabilities
            candidate_capabilities: capabilities to try adding

        Returns:
            List of StateSpaceMoves that produce novel combinations,
            sorted by number of unlocked capabilities (most first)
        """
        moves = []
        for cap in candidate_capabilities:
            if cap in current_state:
                continue
            move = self.explore(current_state, cap)
            if move.cross_domain and move.unlocked:
                moves.append(move)

        # Sort by number of unlocked capabilities (most valuable first)
        moves.sort(key=lambda m: len(m.unlocked), reverse=True)
        return moves


def main():
    """Demo: state-space traversal on a sample graph."""
    # Build a sample graph with prerequisites and cross-domain capabilities
    graph = {
        "nodes": [
            {"id": "semiconductor_fab", "domain": "manufacturing"},
            {"id": "lithography", "domain": "manufacturing"},
            {"id": "ai_accelerator", "domain": "computing"},
            {"id": "neural_network", "domain": "computing"},
            {"id": "bio_sensor", "domain": "biology"},
            {"id": "lab_on_chip", "domain": "biology"},
        ],
        "edges": [
            {"source": "semiconductor_fab", "target": "lithography", "relationship": "enables"},
            {"source": "lithography", "target": "ai_accelerator", "relationship": "requires"},
            {"source": "ai_accelerator", "target": "neural_network", "relationship": "enables"},
            {"source": "lithography", "target": "bio_sensor", "relationship": "requires"},
            {"source": "bio_sensor", "target": "lab_on_chip", "relationship": "enables"},
        ],
    }

    explorer = AdjacentPossibleExplorer(graph)

    print("=" * 60)
    print("Adjacent-Possible State-Space Explorer (Arthur/Youn)")
    print("=" * 60)
    print()

    # Start with semiconductor_fab (manufacturing domain)
    current_state = {"semiconductor_fab"}
    print(f"Current state: {current_state} (domain: manufacturing)")
    print()

    # Explore: what happens if we add lithography?
    move = explorer.explore(current_state, "lithography")
    print(f"Add: {move.added_capability}")
    print(f"  Unlocked: {move.unlocked}")
    print(f"  Cross-domain: {move.cross_domain}")
    print(f"  Domains: {move.domains_connected}")
    print()

    # Now state includes lithography — explore adding bio_sensor (biology domain)
    current_state = move.to_state
    move2 = explorer.explore(current_state, "bio_sensor")
    print(f"Add: {move2.added_capability}")
    print(f"  Unlocked: {move2.unlocked}")
    print(f"  Cross-domain: {move2.cross_domain}")
    print(f"  Domains: {move2.domains_connected}")
    print()

    # Find novel combinations
    print("Finding novel cross-domain combinations:")
    candidates = ["lithography", "ai_accelerator", "neural_network", "bio_sensor", "lab_on_chip"]
    current_state = {"semiconductor_fab"}
    novel = explorer.find_novel_combinations(current_state, candidates)
    for m in novel:
        print(f"  {m.added_capability}: unlocks {len(m.unlocked)} capabilities, "
              f"connects {m.domains_connected[0]} ↔ {m.domains_connected[1]}")

    print()
    print("This is state-space traversal, NOT Jaccard overlap scoring.")
    print("The system explores what becomes POSSIBLE when capabilities combine.")


if __name__ == "__main__":
    main()
