#!/usr/bin/env python3
"""
Phase 5 — Snapshot capture utility (ONE-OFF, not a module).

Creates a snapshot of the current graph state with computed metrics,
following the schema the CEO specified in the Phase 5 directive:

    snapshot_id:    str
    timestamp:      ISO8601 UTC
    nodes:          int (count)
    edges:          int (count)
    constraints:    summary (total non-zero, distribution by type)
    provenance:     summary (counts by source_type)
    metrics:        convergence scores for the validation pairs

This is a MEASUREMENT utility, not a module. It is NOT imported by
anything. It serializes a point-in-time state of the graph to
data/snapshots/snapshot_<N>.json so that delta analysis can be
performed between snapshots.

Per the CEO directive:
  'Step 3 — Define the snapshot schema. Each snapshot should contain:
   snapshot_id, timestamp, nodes, edges, constraints, provenance, metrics.'
"""
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "civilization_graph.json"
SNAPSHOTS_DIR = ROOT / "data" / "snapshots"

# Same pairs as in measure_convergence.py — the CEO's success-criterion pairs.
PAIR_CONVERGING = ("sub_battery_technology", "sub_electric_propulsion")
PAIR_NOT_CONVERGING = ("sub_battery_technology", "sub_desalination")


def load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)


def non_zero_constraint_count(node):
    c = node.get("constraints", {})
    if isinstance(c, dict):
        return sum(1 for v in c.values() if v and float(v) > 0)
    elif isinstance(c, list):
        return len([x for x in c if x])
    return 0


def constraint_distribution(graph):
    """Distribution of constraint types across all nodes."""
    dist = {}
    total_non_zero = 0
    for n in graph["nodes"]:
        c = n.get("constraints", {})
        if isinstance(c, dict):
            for k, v in c.items():
                if v and float(v) > 0:
                    dist[k] = dist.get(k, 0) + 1
                    total_non_zero += 1
    return {"total_non_zero": total_non_zero, "by_type": dist}


def provenance_summary(graph):
    """Counts by provenance source_type."""
    counts = {}
    for n in graph["nodes"]:
        st = n.get("provenance", {}).get("source_type")
        if st:
            counts[st] = counts.get(st, 0) + 1
    counts["total_without_provenance"] = sum(
        1 for n in graph["nodes"] if not n.get("provenance")
    )
    return counts


def compute_convergence_score(graph, pair):
    """Inline copy of the formula from CONVERGENCE.md Section 3."""
    from collections import deque
    a_id, b_id = pair
    nodes = graph["nodes"]
    edges = graph["edges"]
    PREREQ_RELS = {"depends_on", "requires"}
    COMPOSITION_RELS = {"contains"}

    def out_neighbors(node_id, rels):
        result = set()
        for e in edges:
            r = e.get("relationship")
            if rels is not None and r not in rels:
                continue
            if e["source"] == node_id:
                result.add(e["target"])
        return result

    def shortest_path(src, dst):
        if src == dst:
            return 0
        adj = {}
        for e in edges:
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

    # Signal A': direct dependency
    direct_dep = 0
    for e in edges:
        if e.get("relationship") in PREREQ_RELS:
            if {e["source"], e["target"]} == {a_id, b_id}:
                direct_dep = 1
                break

    # Signal A: shared prereq overlap (excluding the pair themselves)
    a_prereqs = out_neighbors(a_id, PREREQ_RELS) - {b_id}
    b_prereqs = out_neighbors(b_id, PREREQ_RELS) - {a_id}
    shared = a_prereqs & b_prereqs
    total = a_prereqs | b_prereqs
    prereq_overlap = len(shared) / len(total) if total else 0.0

    # Signal D: 1/shortest_path
    sp = shortest_path(a_id, b_id)
    path_score = 1.0 / sp if sp and sp > 0 else 0.0

    # Signal C: component reuse (transitive contains-subtree overlap)
    COMPOSITION_RELS = {"contains"}
    def component_subtree(node_id):
        result = set()
        from collections import deque as _dq
        q = _dq([node_id])
        visited = {node_id}
        while q:
            n = q.popleft()
            for e in edges:
                if e.get("relationship") in COMPOSITION_RELS and e["source"] == n:
                    t = e["target"]
                    if t not in visited:
                        visited.add(t)
                        result.add(t)
                        q.append(t)
        return result

    a_components = component_subtree(a_id)
    b_components = component_subtree(b_id)
    shared_c = a_components & b_components
    total_c = a_components | b_components
    component_overlap = len(shared_c) / len(total_c) if total_c else 0.0

    score = (
        1.0 * direct_dep
        + 0.4 * prereq_overlap
        + 0.2 * component_overlap
        + 0.2 * path_score
    )

    return {
        "pair": list(pair),
        "score": round(score, 4),
        "breakdown": {
            "direct_dependency": direct_dep,
            "prereq_overlap_ratio": round(prereq_overlap, 4),
            "component_overlap_ratio": round(component_overlap, 4),
            "component_subtree_a_size": len(a_components),
            "component_subtree_b_size": len(b_components),
            "shared_components_count": len(shared_c),
            "1_over_shortest_path": round(path_score, 4),
            "shortest_path": sp,
        },
    }


def capture_snapshot(snapshot_id):
    """Capture a snapshot of the current graph state + metrics."""
    graph = load_graph()
    snapshot = {
        "snapshot_id": snapshot_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "graph_version": graph.get("metadata", {}).get("version", "unknown"),
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "constraints": constraint_distribution(graph),
        "provenance": provenance_summary(graph),
        "metrics": {
            "convergence_scores": {
                "battery_ev": compute_convergence_score(graph, PAIR_CONVERGING),
                "battery_desalination": compute_convergence_score(graph, PAIR_NOT_CONVERGING),
            },
            "discrimination_delta": round(
                abs(compute_convergence_score(graph, PAIR_CONVERGING)["score"]
                    - compute_convergence_score(graph, PAIR_NOT_CONVERGING)["score"]),
                4
            ),
        },
    }
    return snapshot


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Capture a graph snapshot.")
    parser.add_argument("snapshot_id", help="Snapshot identifier (e.g., 'snapshot_1')")
    args = parser.parse_args()

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = capture_snapshot(args.snapshot_id)
    out_path = SNAPSHOTS_DIR / f"{args.snapshot_id}.json"
    with open(out_path, "w") as f:
        json.dump(snapshot, f, indent=2)
        f.write("\n")
    print(f"Snapshot captured: {out_path}")
    print(f"  snapshot_id: {snapshot['snapshot_id']}")
    print(f"  timestamp:   {snapshot['timestamp']}")
    print(f"  graph_version: {snapshot['graph_version']}")
    print(f"  nodes:       {snapshot['nodes']}")
    print(f"  edges:       {snapshot['edges']}")
    print(f"  constraints: {snapshot['constraints']['total_non_zero']} non-zero entries")
    print(f"  provenance:  {json.dumps(snapshot['provenance'], indent=4)}")
    print(f"  Convergence(battery, EV)           = {snapshot['metrics']['convergence_scores']['battery_ev']['score']}")
    print(f"  Convergence(battery, desalination) = {snapshot['metrics']['convergence_scores']['battery_desalination']['score']}")
    print(f"  Discrimination delta:              = {snapshot['metrics']['discrimination_delta']}")


if __name__ == "__main__":
    main()
