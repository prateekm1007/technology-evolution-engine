"""
Maestro Loop Cycle 6 — regression tests for N3 + F-022.

N3 (auditor's finding on commit 53320bc): metadata.node_count was stale
(said 577, actual was 632) after the Step 4 ingestion script appended
55 nodes without updating the metadata field. The drift was not caught
by any test because no test asserted metadata.node_count == len(nodes).
This test file closes that gap.

Per principle #2 (fix the thing, don't loosen the check): the test
asserts the strong invariant (metadata.node_count == actual count),
not a weaker "is present" check.

Per principle #9 (downstream blast radius gets checked): the test also
asserts edge_count, since the ingestion script also bumps edges in some
scenarios and the same drift class could recur.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GRAPH_PATH = ROOT / "data" / "civilization_graph.json"


def _load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)


def test_metadata_node_count_matches_actual():
    """N3 regression: metadata.node_count MUST equal len(nodes).

    The Step 4 ingestion script (commit 53320bc) appended 55 nodes but
    never updated this field, leaving it stale at 577. This test catches
    that class of drift going forward.
    """
    graph = _load_graph()
    actual = len(graph["nodes"])
    reported = graph["metadata"].get("node_count")
    assert reported == actual, (
        f"metadata.node_count drift: metadata says {reported}, "
        f"actual is {actual}. Run scripts/fix_n3_f022.py to repair, "
        f"then ensure scripts/ingest_real_sources.py updates the field "
        f"on every future ingestion."
    )


def test_metadata_edge_count_matches_actual():
    """N3 sibling: metadata.edge_count MUST equal len(edges).

    Same drift class as node_count. No prior test caught it; this one
    will, if a future script modifies edges without updating metadata.
    """
    graph = _load_graph()
    actual = len(graph["edges"])
    reported = graph["metadata"].get("edge_count")
    assert reported == actual, (
        f"metadata.edge_count drift: metadata says {reported}, "
        f"actual is {actual}."
    )


def test_graph_metadata_includes_required_fields():
    """The metadata block MUST carry the fields a consumer would
    reasonably expect (name, version, node_count, edge_count). This is
    a contract assertion — it catches the case where a future
    refactor renames or drops a field.
    """
    graph = _load_graph()
    meta = graph["metadata"]
    for field in ("name", "version", "node_count", "edge_count"):
        assert field in meta, f"metadata.{field} missing from graph metadata"


def test_graph_version_is_at_least_3_1():
    """The graph version was bumped to 3.1 by the Cycle 6 patch.
    Future ingestion scripts may bump higher, but the version must
    never regress below 3.1 (which would indicate the patch was
    reverted without fixing the underlying drift)."""
    graph = _load_graph()
    version = graph["metadata"]["version"]
    major, minor = (int(x) for x in version.split("."))
    assert (major, minor) >= (3, 1), (
        f"graph version {version} < 3.1 — Cycle 6 patch appears reverted"
    )
