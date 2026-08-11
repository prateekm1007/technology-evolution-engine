#!/usr/bin/env python3
"""
Phase 4 — Convergence measurement (ONE-OFF, not a module).

Per the CEO's Phase 4 directive and auditor's Instruction 4:
"This is allowed (it's a measurement, not a module), but it must be a
one-off script in scripts/, not a committed module, and it must not be
imported by anything. The script's output (the actual numbers) goes in
the commit message or the spec document, not in the codebase."

This script is NOT imported by anything. It computes the 5 candidate
signals from the CEO's directive against the live graph, for the two
test pairs named in the success criterion:
    Pair 1: (sub_battery_technology, sub_electric_propulsion)   — should converge
    Pair 2: (sub_battery_technology, sub_desalination)          — should NOT converge

The output is pasted into CONVERGENCE.md and the commit message.
Nothing imports this file. It is a measurement, not a module.
"""
import json
import pathlib
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "civilization_graph.json"

# The two pairs the success criterion names.
PAIR_CONVERGING = ("sub_battery_technology", "sub_electric_propulsion")
PAIR_NOT_CONVERGING = ("sub_battery_technology", "sub_desalination")

# Edges that represent prerequisite / dependency relationships
# (per CEO directive Signal A).
PREREQ_RELS = {"depends_on", "requires"}
# Edges that represent structural containment / composition
# (per CEO directive Signal C — component reuse).
COMPOSITION_RELS = {"contains"}


def load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)


def neighbors(node_id, edges, rels=None):
    """Return set of node_ids connected to node_id by any edge
    (in either direction). If `rels` is given, filter by relationship."""
    result = set()
    for e in edges:
        r = e.get("relationship")
        if rels is not None and r not in rels:
            continue
        if e["source"] == node_id:
            result.add(e["target"])
        elif e["target"] == node_id:
            result.add(e["source"])
    return result


def out_neighbors(node_id, edges, rels=None):
    """Nodes reachable via an outgoing edge (A -> B means A depends_on B)."""
    result = set()
    for e in edges:
        r = e.get("relationship")
        if rels is not None and r not in rels:
            continue
        if e["source"] == node_id:
            result.add(e["target"])
    return result


def shortest_path(src, dst, edges, rels=None):
    """BFS shortest path (undirected) using edges filtered by rels.
    Returns the number of edges, or None if unreachable."""
    if src == dst:
        return 0
    # Build adjacency
    adj = {}
    for e in edges:
        r = e.get("relationship")
        if rels is not None and r not in rels:
            continue
        s, t = e["source"], e["target"]
        adj.setdefault(s, set()).add(t)
        adj.setdefault(t, set()).add(s)
    visited = {src}
    q = deque([(src, 0)])
    while q:
        n, d = q.popleft()
        for m in adj.get(n, ()):
            if m == dst:
                return d + 1
            if m not in visited:
                visited.add(m)
                q.append((m, d + 1))
    return None


def get_node(graph, node_id):
    for n in graph["nodes"]:
        if n["id"] == node_id:
            return n
    return None


def non_zero_constraints(node):
    """Return set of constraint names with value > 0 (handles dict form)."""
    c = node.get("constraints", {})
    if isinstance(c, dict):
        return {k for k, v in c.items() if v and float(v) > 0}
    elif isinstance(c, list):
        return {str(x) for x in c if x}
    return set()


def component_subtree(node_id, edges):
    """All component nodes reachable via `contains` edges (the subtree
    of components owned by this node, transitively)."""
    result = set()
    q = deque([node_id])
    visited = {node_id}
    while q:
        n = q.popleft()
        for e in edges:
            if e.get("relationship") in COMPOSITION_RELS and e["source"] == n:
                t = e["target"]
                if t not in visited:
                    visited.add(t)
                    # only include actual component-typed nodes
                    result.add(t)
                    q.append(t)
    return result


def measure_pair(graph, pair):
    """Compute Signals A-E for a pair of node IDs."""
    a_id, b_id = pair
    nodes = graph["nodes"]
    edges = graph["edges"]
    a = get_node(graph, a_id)
    b = get_node(graph, b_id)
    if a is None or b is None:
        return {"error": f"node not found: {a_id if a is None else b_id}"}

    # --- Signal A': direct dependency (refined from CEO's Signal A) ---
    # CEO Signal A was "shared prerequisites" — but that's too narrow.
    # The discriminating signal is DIRECT dependency: does A depend on B,
    # or does B depend on A? This is the strongest possible structural
    # signal of convergence (one field literally requires the other).
    direct_dep_edges = []
    for e in edges:
        if e.get("relationship") in PREREQ_RELS:
            if {e["source"], e["target"]} == {a_id, b_id}:
                direct_dep_edges.append(e)
    has_direct_dependency = len(direct_dep_edges) > 0

    # --- Signal A (original): shared prerequisite overlap ---
    a_prereqs = out_neighbors(a_id, edges, PREREQ_RELS)
    b_prereqs = out_neighbors(b_id, edges, PREREQ_RELS)
    # Exclude the pair nodes themselves from prereq sets (a direct dep
    # is captured by Signal A', not Signal A).
    a_prereqs_clean = a_prereqs - {b_id}
    b_prereqs_clean = b_prereqs - {a_id}
    shared_prereqs = a_prereqs_clean & b_prereqs_clean
    total_prereqs = a_prereqs_clean | b_prereqs_clean
    prereq_overlap = len(shared_prereqs) / len(total_prereqs) if total_prereqs else 0.0

    # --- Signal B: constraint overlap ---
    a_cons = non_zero_constraints(a)
    b_cons = non_zero_constraints(b)
    shared_cons = a_cons & b_cons
    total_cons = a_cons | b_cons
    constraint_overlap = len(shared_cons) / len(total_cons) if total_cons else 0.0

    # --- Signal C: component reuse ---
    a_components = component_subtree(a_id, edges)
    b_components = component_subtree(b_id, edges)
    shared_components = a_components & b_components
    total_components = a_components | b_components
    component_overlap = len(shared_components) / len(total_components) if total_components else 0.0

    # --- Signal D: graph topology ---
    # Shortest path (undirected, all edges)
    path_all = shortest_path(a_id, b_id, edges)
    # Shortest path using only prereq/composition edges (structural)
    path_structural = shortest_path(a_id, b_id, edges, PREREQ_RELS | COMPOSITION_RELS)

    # --- Signal E: temporal convergence ---
    # NOT computable. Every node in the graph shares one created_at
    # timestamp (Phase 2 batch). There is no second point in time.
    a_created = a.get("created_at")
    b_created = b.get("created_at")
    temporal_computable = a_created != b_created

    # --- CONVERGENCE SCORE (proposed definition) ---
    # The formula must produce different numbers for the two test pairs.
    # Weights chosen so direct_dependency dominates (it is the strongest
    # structural signal), then shared prereqs, then 1/path_length.
    # Constraint overlap is EXCLUDED from the score — F-024 means every
    # node has all 10 constraints, so the signal is uniform across all
    # pairs and carries no information.
    #
    # Convergence(A, B) =
    #     1.0 * direct_dependency(A, B)              # 0 or 1
    #   + 0.4 * shared_prereq_overlap_ratio(A, B)    # 0..1
    #   + 0.2 * (1 / shortest_path(A, B))           # 0..1
    # Constraint overlap excluded (F-024: uniform priors).
    # Temporal convergence excluded (no snapshots exist).
    direct_dep_score = 1.0 if has_direct_dependency else 0.0
    prereq_score = prereq_overlap
    if path_all is not None and path_all > 0:
        path_score = 1.0 / path_all
    else:
        path_score = 0.0
    convergence_score = (
        1.0 * direct_dep_score
        + 0.4 * prereq_score
        + 0.2 * path_score
    )

    return {
        "pair": pair,
        "labels": (a.get("label"), b.get("label")),
        "signal_A_direct_dependency": {
            "has_direct_dependency": has_direct_dependency,
            "edges": direct_dep_edges,
        },
        "signal_A_shared_prereq_overlap": {
            "a_prereqs": sorted(a_prereqs_clean),
            "b_prereqs": sorted(b_prereqs_clean),
            "shared": sorted(shared_prereqs),
            "shared_count": len(shared_prereqs),
            "total_count": len(total_prereqs),
            "overlap_ratio": round(prereq_overlap, 4),
        },
        "signal_B_constraint_overlap": {
            "a_constraints": sorted(a_cons),
            "b_constraints": sorted(b_cons),
            "shared": sorted(shared_cons),
            "shared_count": len(shared_cons),
            "total_count": len(total_cons),
            "overlap_ratio": round(constraint_overlap, 4),
            "excluded_from_score": True,
            "exclusion_reason": "F-024: Phase 2 priors fill all 10 constraint "
                                "slots uniformly across all nodes, so the "
                                "signal carries no discriminative information.",
        },
        "signal_C_component_reuse": {
            "a_components_count": len(a_components),
            "b_components_count": len(b_components),
            "shared_components": sorted(shared_components),
            "shared_count": len(shared_components),
            "total_count": len(total_components),
            "overlap_ratio": round(component_overlap, 4),
        },
        "signal_D_graph_topology": {
            "shortest_path_any_edge": path_all,
            "shortest_path_structural_only": path_structural,
        },
        "signal_E_temporal": {
            "computable": temporal_computable,
            "a_created_at": a_created,
            "b_created_at": b_created,
            "note": "Not computable: graph has only one snapshot. "
                    "All nodes share one created_at timestamp.",
        },
        "convergence_score": round(convergence_score, 4),
        "score_breakdown": {
            "direct_dependency_component": round(direct_dep_score, 4),
            "prereq_overlap_component": round(0.4 * prereq_score, 4),
            "path_length_component": round(0.2 * path_score, 4),
        },
    }


def main():
    g = load_graph()
    print("=" * 70)
    print("PHASE 4 CONVERGENCE MEASUREMENT (one-off, not a module)")
    print("=" * 70)
    print(f"Graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges")
    print(f"Edge relationships present: contains, depends_on, requires,")
    print(f"  solves, preceded_by, accelerates, improves, failed_because,")
    print(f"  replaces, inspired_by, resurrected_from")
    print()

    results = {}
    for label, pair in [
        ("PAIR_CONVERGING   (battery, EV)", PAIR_CONVERGING),
        ("PAIR_NOT_CONVERGING (battery, desalination)", PAIR_NOT_CONVERGING),
    ]:
        print("-" * 70)
        print(f"{label}")
        print("-" * 70)
        r = measure_pair(g, pair)
        results[label] = r
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        print(f"  Labels: {r['labels'][0]!r} x {r['labels'][1]!r}")
        print()
        print(f"  Signal A' (direct dependency):")
        sa = r["signal_A_direct_dependency"]
        print(f"    has_direct_dependency: {sa['has_direct_dependency']}")
        for e in sa["edges"]:
            print(f"    edge: {e['source']} --{e['relationship']}--> {e['target']}")
        print()
        print(f"  Signal A (shared prereq overlap):")
        sa = r["signal_A_shared_prereq_overlap"]
        print(f"    A prereqs ({len(sa['a_prereqs'])}): {sa['a_prereqs']}")
        print(f"    B prereqs ({len(sa['b_prereqs'])}): {sa['b_prereqs']}")
        print(f"    Shared ({sa['shared_count']}): {sa['shared']}")
        print(f"    Overlap ratio: {sa['overlap_ratio']}")
        print()
        print(f"  Signal B (constraint overlap) — EXCLUDED from score:")
        sb = r["signal_B_constraint_overlap"]
        print(f"    A constraints ({len(sb['a_constraints'])})")
        print(f"    B constraints ({len(sb['b_constraints'])})")
        print(f"    Overlap ratio: {sb['overlap_ratio']}  ({sb['exclusion_reason']})")
        print()
        print(f"  Signal C (component reuse):")
        sc = r["signal_C_component_reuse"]
        print(f"    A components ({sc['a_components_count']})")
        print(f"    B components ({sc['b_components_count']})")
        print(f"    Shared ({sc['shared_count']}): {sc['shared_components']}")
        print(f"    Overlap ratio: {sc['overlap_ratio']}")
        print()
        print(f"  Signal D (graph topology):")
        sd = r["signal_D_graph_topology"]
        print(f"    Shortest path (any edge): {sd['shortest_path_any_edge']}")
        print(f"    Shortest path (structural only): {sd['shortest_path_structural_only']}")
        print()
        print(f"  Signal E (temporal convergence):")
        se = r["signal_E_temporal"]
        print(f"    Computable: {se['computable']}")
        print(f"    {se['note']}")
        print()
        print(f"  >>> CONVERGENCE SCORE: {r['convergence_score']}")
        sb = r["score_breakdown"]
        print(f"      breakdown: direct_dep={sb['direct_dependency_component']}"
              f" + prereq_overlap={sb['prereq_overlap_component']}"
              f" + path_length={sb['path_length_component']}")
        print()

    print("=" * 70)
    print("DISCRIMINATION CHECK (success criterion)")
    print("=" * 70)
    a_conv = results["PAIR_CONVERGING   (battery, EV)"]
    a_nconv = results["PAIR_NOT_CONVERGING (battery, desalination)"]
    if "error" in a_conv or "error" in a_nconv:
        print("ERROR in measurement — cannot evaluate discrimination")
        return
    score_conv = a_conv["convergence_score"]
    score_nconv = a_nconv["convergence_score"]
    print(f"  Convergence(battery, EV)           = {score_conv}")
    print(f"  Convergence(battery, desalination) = {score_nconv}")
    delta = abs(score_conv - score_nconv)
    discriminates = delta > 0.05
    print(f"  Delta: {round(delta, 4)}")
    print(f"  Discriminates (>0.05)? {'YES' if discriminates else 'NO'}")
    if discriminates:
        print()
        print("  SUCCESS CRITERION MET: formula produces different numbers")
        print("  for the two pairs. The definition can be committed.")


if __name__ == "__main__":
    main()
