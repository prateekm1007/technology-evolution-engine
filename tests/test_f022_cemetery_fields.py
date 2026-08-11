"""
Maestro Loop Cycle 6 — F-022 regression tests.

F-022 (auditor finding, post-Phase 2 verification): the 9 cemetery_entry
nodes in civilization_graph.json carry metadata.lesson and
metadata.why_it_failed but NOT the top-level is_cemetery / lesson /
failed_because fields the GraphModel adapter reads at
web/backend/adapters/graph_model.py:54-63.

Without these top-level fields, the adapter's classification at line 54
(`ntype = "cemetery" if (n.get("is_cemetery") or ntype == "failure")
else "component"`) falls through to "component" — the cemetery nodes are
misclassified, and the Oracle's resurrection check at
oracle_deep.py:115 (`if n.get("is_cemetery") and up:`) never fires.

This test file verifies:
  1. Every cemetery_entry node has is_cemetery=True at top level.
  2. Every cemetery_entry node has a non-empty lesson.
  3. Every cemetery_entry node has a non-empty failed_because.
  4. The GraphModel adapter correctly classifies these nodes as
     type="cemetery" (which is what makes the Oracle's check fire).
  5. The Oracle's resurrection list CAN be non-empty when a cemetery
     node is forced across the viability threshold (this validates
     that the detection path works end-to-end after the F-022 fix).

Per principle #2 (fix the thing, don't loosen the check): the tests
assert the actual fields, not a softer "key is present" check.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "web" / "backend"))

GRAPH_PATH = ROOT / "data" / "civilization_graph.json"


def _load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)


def _cemetery_nodes(graph):
    return [n for n in graph["nodes"] if n.get("type") == "cemetery_entry"]


def test_every_cemetery_node_has_is_cemetery_true():
    """F-022: every cemetery_entry node MUST carry is_cemetery=True at
    top level (not just nested under metadata). The GraphModel adapter
    reads n.get('is_cemetery') directly."""
    graph = _load_graph()
    cem = _cemetery_nodes(graph)
    assert len(cem) >= 9, f"Expected >=9 cemetery nodes, got {len(cem)}"
    for n in cem:
        assert n.get("is_cemetery") is True, (
            f"{n['id']} ({n['label']}): is_cemetery is "
            f"{n.get('is_cemetery')!r}, expected True"
        )


def test_every_cemetery_node_has_nonempty_lesson():
    """F-022: every cemetery_entry node MUST carry a non-empty lesson
    at top level. The Oracle reads n.get('lesson') in its resurrection
    output (oracle_deep.py:116). An empty lesson produces a null entry
    in the output, which is the same as 'no resurrection' for a
    consumer that displays the result."""
    graph = _load_graph()
    cem = _cemetery_nodes(graph)
    for n in cem:
        lesson = n.get("lesson")
        assert isinstance(lesson, str) and lesson.strip(), (
            f"{n['id']} ({n['label']}): lesson is {lesson!r}, expected non-empty str"
        )


def test_every_cemetery_node_has_nonempty_failed_because():
    """F-022: every cemetery_entry node MUST carry a non-empty
    failed_because at top level. This is what the resurrection logic
    uses to explain WHY the original failed — the counterfactual
    'would it succeed now?' requires knowing what changed."""
    graph = _load_graph()
    cem = _cemetery_nodes(graph)
    for n in cem:
        fb = n.get("failed_because")
        assert isinstance(fb, str) and fb.strip(), (
            f"{n['id']} ({n['label']}): failed_because is {fb!r}, expected non-empty str"
        )


def test_graph_model_adapter_classifies_cemetery_nodes_correctly():
    """The GraphModel adapter at web/backend/adapters/graph_model.py:54
    uses `n.get("is_cemetery") or ntype == "failure"` to decide whether
    a node is cemetery. Before F-022 fix, is_cemetery was None and the
    type was "cemetery_entry" (not "failure"), so the OR was False and
    the node was misclassified as "component". After F-022 fix,
    is_cemetery=True triggers the OR and the node is correctly
    classified as "cemetery"."""
    from adapters.graph_model import GraphModel
    gm = GraphModel(repo_root=str(ROOT))
    cemetery_in_adapter = [n for n in gm.nodes if n.get("type") == "cemetery"]
    assert len(cemetery_in_adapter) >= 9, (
        f"GraphModel adapter classified only {len(cemetery_in_adapter)} "
        f"nodes as type='cemetery'. Expected >=9 (the cemetery_entry "
        f"nodes from the raw graph). This means the F-022 fix didn't "
        f"propagate to the adapter — check graph_model.py:54."
    )
    # All of them should have is_cemetery=True in the adapter output.
    for n in cemetery_in_adapter:
        assert n.get("is_cemetery") is True, (
            f"{n['id']} ({n['label']}): adapter set type='cemetery' but "
            f"is_cemetery={n.get('is_cemetery')!r}. Inconsistent — check "
            f"graph_model.py:61."
        )


def test_oracle_resurrection_detection_can_fire():
    """The Oracle's resurrection check at oracle_deep.py:115 is
    `if n.get("is_cemetery") and up:`. Before F-022 fix, n.get("is_cemetery")
    was None/False for every node, so the check never fired.

    This test verifies that AFTER the F-022 fix, the Oracle's
    resurrection list CAN be non-empty when a cemetery node is pushed
    across the viability threshold.

    Approach: directly manipulate a cemetery node's constraints to give
    it exactly 4 non-zero constraints (load=4). This makes:
      base_viability = 1.0 - 4*0.15 = 0.4   (< threshold 0.5)
    Then we apply a 10x decrease on "energy" (delta=-0.9), which makes:
      binding_response = -delta * (1/load) = 0.9 * 0.25 = 0.225
      new_viability = base + state*gain = 0.4 + 0.225*0.5 = 0.5125  (>= threshold)
    The resurrection condition `base < thr <= new_v` is satisfied.

    This is a forced test — we are not testing whether the Oracle
    naturally produces resurrections (which depends on graph dynamics
    we have not yet tuned). We are testing that the DETECTION PATH
    works after F-022. The difference matters: a forced test confirms
    the code path is no longer structurally inert.
    """
    from adapters.graph_model import GraphModel
    from adapters.oracle_deep import DeepOracle

    gm = GraphModel(repo_root=str(ROOT))
    # Pick a cemetery node and force its constraints to exactly 4
    # non-zero entries (including "energy"). This makes load=4, so
    # base_viability = 0.4 (below threshold 0.5), but a 10x decrease
    # on "energy" pushes new_viability to 0.5125 (above threshold).
    cemetery_node = next((n for n in gm.nodes if n.get("is_cemetery")), None)
    assert cemetery_node is not None, "No cemetery node in GraphModel — F-022 fix not landed"
    forced_constraints = {"energy": 0.9, "cost": 0.7, "material": 0.6, "manufacturing": 0.5}
    cemetery_node["constraints"] = forced_constraints
    gm.by_id[cemetery_node["id"]]["constraints"] = forced_constraints

    oracle = DeepOracle(gm)
    # delta=-0.9 (10x decrease on energy). This makes the binding
    # response on the cemetery node = 0.9 * (1/4) = 0.225, which
    # pushes viability from 0.4 (base, below threshold) to 0.5125
    # (above threshold) — a crossing event.
    result = oracle.simulate("energy", "decrease", "10x")

    # The equilibrium stage should have run and the resurrections list
    # should now contain the cemetery node.
    eq = result["stages"]["equilibrium"]
    assert "resurrections" in eq, "Oracle output missing 'resurrections' key"
    resurrection_ids = {r["id"] for r in eq["resurrections"]}
    assert cemetery_node["id"] in resurrection_ids, (
        f"Cemetery node {cemetery_node['id']} ({cemetery_node['label']}) "
        f"was forced across the viability threshold (load=4, base=0.4, "
        f"new_v=0.5125 after 10x energy decrease) but did NOT appear in "
        f"the Oracle's resurrections list. Resurrections observed: "
        f"{resurrection_ids}. This means the F-022 fix is incomplete — "
        f"check oracle_deep.py:115 `if n.get('is_cemetery') and up:`."
    )

