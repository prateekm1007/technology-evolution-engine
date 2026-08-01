"""
Forensic audit findings — regression tests.

Per ANTI_ENTROPY.md rule 1 (Write tests first), these tests are written
BEFORE the fixes land. Each test asserts the expected (post-fix)
behavior of a specific finding from the forensic audit
(`AUDIT.md`). The tests are intentionally named F-AUD-* to match the
finding IDs in the audit report, so a failure points the reader at the
exact finding being violated.

Findings covered (see AUDIT.md for full context):

  F-AUD-001  dependency_module walrus-operator bug — _classify_edge_causally
             was called with source == target, producing wrong causal
             classifications.
  F-AUD-002  web/backend/adapters/core.py::read_evidence() crashes on a
             corrupted ledger (F-013 — duplicate of the F-006 fix that
             landed in only one of two readers).
  F-AUD-003  scripts/calibrate.py crashes on a corrupted ledger (F-015 —
             same class as F-013).
  F-AUD-004  FAILURES.md is out of sync with reality — F-005 and F-014
             are marked OPEN but the ledger was remediated and the
             regression tests pass. Law 7 (historical permanence) requires
             the failure taxonomy to track reality.
  F-AUD-007  product/retrieval/graph_retriever.py::_cem() reads files
             with bare open() — resource leak.
  F-AUD-012  invention_compiler/orchestrator.py hardcodes
             verification_status="integrated" in _chain_summary instead
             of deriving it from the verification engine's output.

Findings documented in AUDIT.md but NOT covered by tests here (because
the fix is out of scope for an audit PR — see AUDIT.md "Recommendations"
section):

  F-AUD-005  verification_engine is named "engine" but does not satisfy
             ANTI_ENTROPY.md's three-condition bar (explicit model +
             empirical validation + reproducible results). The naming
             test (test_only_verification_engine_is_called_engine) only
             checks file globs, not whether the file meets the bar.
  F-AUD-006  physics/chemistry/mathematics modules claim in their
             docstrings to be "upgraded from keyword matching to encoding
             actual [scientific principles]" but the upgrade is
             documentation (dict of strings), not encoding. The
             check_consistency() "dimensional analysis" is a 6-line
             hardcoded dict lookup.
  F-AUD-008  product/api/routes.py leaks raw exception strings into
             HTTP 500 responses.
  F-AUD-009  requirements.txt uses >= soft floors with no lockfile —
             violates "Lock dependencies" anti-entropy rule.
  F-AUD-010  web/backend/main.py mounts StaticFiles at import time —
             F-007 regression risk if frontend dir is missing.
  F-AUD-011  product/orchestration/pipeline.py writes logs to
             logs/pipeline_runs.jsonl with no schema validation, no
             rotation, no integrity check — same class as F-005.
"""
import json
import pathlib
import sys
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ----------------------------------------------------------------------
# F-AUD-001 — dependency_module walrus-operator bug
# ----------------------------------------------------------------------

def _graph_for_causal_test():
    """Build a tiny graph where the expected causal classifications are
    unambiguous, so the test can assert against ground truth rather than
    against the module's own output.

    Per the LineageMapper convention (``A --requires--> B`` means
    "A requires B", i.e., B is A's prerequisite — see
    ``product/lineage/mapper.py::_walk_prereqs`` which walks
    ``self.out[node_id]``), the target's prerequisites are edges where
    the target is the SOURCE.

    Layout (target = system_T):
      system_T  --requires-->    principle_X    (single prereq path => necessary)
      system_T  --requires-->    principle_Y    (now multiple => but principle => necessary)
      system_T  --depends_on-->  component_A    (component, depends_on => contributing)
      system_T  --depends_on-->  component_B    (component, depends_on => contributing)

    Expected causal_classifications:
      necessary:    2  (principle_X, principle_Y — both are principle type)
      contributing: 2  (component_A, component_B — both are component type, depends_on)
      sufficient:   0
      unknown:      0
    """
    return {
        "nodes": [
            {"id": "system_T", "label": "Target System", "type": "system",
             "domain": "test", "constraints": ["energy"]},
            {"id": "principle_X", "label": "Underlying Principle", "type": "principle",
             "domain": "test", "constraints": []},
            {"id": "principle_Y", "label": "Second Principle", "type": "principle",
             "domain": "test", "constraints": []},
            {"id": "component_A", "label": "Component A", "type": "component",
             "domain": "test", "constraints": ["material"]},
            {"id": "component_B", "label": "Component B", "type": "component",
             "domain": "test", "constraints": ["material"]},
        ],
        "edges": [
            {"source": "system_T", "target": "principle_X", "relationship": "requires", "weight": 1.0},
            {"source": "system_T", "target": "principle_Y", "relationship": "requires", "weight": 1.0},
            {"source": "system_T", "target": "component_A", "relationship": "depends_on", "weight": 1.0},
            {"source": "system_T", "target": "component_B", "relationship": "depends_on", "weight": 1.0},
        ],
    }


def test_F_AUD_001_causal_classification_uses_target_not_source():
    """F-AUD-001 regression.

    _classify_edge_causally(source, target, rel) must classify the edge
    source->target. Before the fix, a walrus-operator bug passed
    source == target, so the function classified edges pointing INTO
    the prereq rather than edges pointing INTO the target. The
    'necessary'/'contributing' counts were therefore computed against
    the wrong node's prerequisite set.

    Ground truth for the test graph:
      - principle_X -> system_T (requires, source is principle): necessary
      - principle_Y -> system_T (requires, source is principle): necessary
      - component_A -> system_T (depends_on, source is component): contributing
      - component_B -> system_T (depends_on, source is component): contributing

    Expected counts: necessary=2, contributing=2, sufficient=0, unknown=0.
    """
    from invention_compiler.dependency_module import DependencyModule
    dm = DependencyModule(graph=_graph_for_causal_test())
    out = dm.analyze({"domain": "test"}, target_node_id="system_T")
    counts = out["evidence"]["causal_classifications"]
    assert counts["necessary"] == 2, (
        f"F-AUD-001 regression: expected 2 necessary edges (the two "
        f"principle->system requires edges), got {counts}. The walrus-"
        f"operator bug classifies against the prereq's prereqs instead "
        f"of the target's prereqs."
    )
    assert counts["contributing"] == 2, (
        f"F-AUD-001 regression: expected 2 contributing edges (the two "
        f"component->system depends_on edges), got {counts}."
    )
    assert counts["sufficient"] == 0
    assert counts["unknown"] == 0


def test_F_AUD_001_causal_classification_label_is_correct_per_prereq():
    """F-AUD-001 regression (per-edge assertion).

    Each prereq in the output must carry a `causal_classification` field
    matching the ground-truth classification for that specific edge, not
    a classification derived from the prereq's own incoming edges.
    """
    from invention_compiler.dependency_module import DependencyModule
    dm = DependencyModule(graph=_graph_for_causal_test())
    out = dm.analyze({"domain": "test"}, target_node_id="system_T")
    by_id = {p["id"]: p["causal_classification"] for p in out["prerequisites"]}
    assert by_id["principle_X"] == "necessary"
    assert by_id["principle_Y"] == "necessary"
    assert by_id["component_A"] == "contributing"
    assert by_id["component_B"] == "contributing"


# ----------------------------------------------------------------------
# F-AUD-002 — CoreAdapter.read_evidence() crashes on corrupted ledger
# ----------------------------------------------------------------------

def test_F_AUD_002_core_adapter_read_evidence_handles_corrupted_ledger(tmp_path):
    """F-AUD-002 regression (also closes F-013).

    CoreAdapter.read_evidence() must not raise on a corrupted ledger
    (one-char-per-line, the F-005 failure mode). Before the fix, the
    method did `[json.loads(l) for l in ...]` with no try/except —
    the same crash that F-006 fixed in web/backend/main.py::evidence(),
    but the fix landed in only one of the two readers.
    """
    # Build a fake repo root with a corrupted ledger.
    graph_dir = tmp_path / "data"
    graph_dir.mkdir()
    (graph_dir / "civilization_graph.json").write_text(
        json.dumps({"nodes": [], "edges": []}))
    ledger_dir = tmp_path / "data" / "ledger"
    ledger_dir.mkdir()
    # 50 real entries, then write the file one-char-per-line.
    real = "\n".join(json.dumps({"id": str(i), "outcome": "pending"})
                     for i in range(50))
    corrupted = "\n".join(list(real)) + "\n"
    (ledger_dir / "predictions.jsonl").write_text(corrupted, encoding="utf-8")

    # Add product layer so CoreAdapter can import it.
    sys.path.insert(0, str(ROOT))
    from web.backend.adapters.core import CoreAdapter
    core = CoreAdapter(repo_root=tmp_path)
    # Must not raise.
    result = core.read_evidence()
    assert isinstance(result, dict)
    assert "ledger" in result
    # The corrupted file must not produce spurious entries.
    assert result["ledger"] == [] or len(result["ledger"]) == 0, (
        "F-AUD-002 regression: read_evidence() should return zero "
        "entries on a totally-corrupted ledger, not spurious single-"
        "character JSON values."
    )
    # And it should surface the corruption signal.
    assert result.get("malformed_lines"), (
        "F-AUD-002 regression: read_evidence() should report the "
        "corruption in malformed_lines, not silently return empty."
    )


# ----------------------------------------------------------------------
# F-AUD-003 — scripts/calibrate.py crashes on corrupted ledger
# ----------------------------------------------------------------------

def test_F_AUD_003_calibrate_handles_corrupted_ledger(tmp_path, monkeypatch):
    """F-AUD-003 regression (also closes F-015).

    scripts/calibrate.py must not raise on a corrupted ledger. Before
    the fix, it did the same unguarded list comprehension as F-013.
    """
    # Build a fake repo root with a corrupted ledger.
    ledger_dir = tmp_path / "data" / "ledger"
    ledger_dir.mkdir(parents=True)
    real = "\n".join(json.dumps({"id": str(i), "outcome": "pending"})
                     for i in range(50))
    corrupted = "\n".join(list(real)) + "\n"
    (ledger_dir / "predictions.jsonl").write_text(corrupted, encoding="utf-8")

    # Import the calibrate module by file path (it's a script, not a package).
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "calibrate", str(ROOT / "scripts" / "calibrate.py"))
    calibrate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calibrate)

    # calibrate.read_ledger() (or whatever the public read fn is) must
    # not raise on the corrupted ledger. We accept any return shape that
    # does not crash; the contract is "fail loudly with a message, not
    # with a traceback" (per FAILURES.md F-015).
    try:
        result = calibrate.read_ledger(str(ledger_dir / "predictions.jsonl"))
    except Exception as e:
        pytest.fail(
            f"F-AUD-003 regression: calibrate.read_ledger() raised {type(e).__name__}: {e} "
            "on a corrupted ledger. Per FAILURES.md F-015, it should fail loudly "
            "with a message, not a traceback."
        )
    # The result must surface the corruption (not return spurious entries).
    if isinstance(result, list):
        assert len(result) == 0, (
            "F-AUD-003 regression: calibrate should not return spurious "
            "entries from a corrupted ledger."
        )
    elif isinstance(result, dict):
        entries = result.get("entries") or result.get("ledger") or []
        assert len(entries) == 0
        assert result.get("malformed_lines") or result.get("corruption_detected"), (
            "F-AUD-003 regression: calibrate should surface the corruption signal."
        )


# ----------------------------------------------------------------------
# F-AUD-004 — FAILURES.md in sync with reality
# ----------------------------------------------------------------------

def test_F_AUD_004_failures_md_marks_remediated_entries_resolved():
    """F-AUD-004 regression (Law 7 — historical permanence).

    FAILURES.md must track reality. F-005 (ledger corruption) and
    F-014 (regression tests failing on corrupted state) are marked OPEN
    in the committed FAILURES.md, but the ledger has been regenerated
    (10 parseable entries) and the regression tests pass. This is a
    Law 7 violation: the failure taxonomy is the canonical record of
    what's broken; if it lies, future readers can't trust it.
    """
    failures_path = ROOT / "FAILURES.md"
    text = failures_path.read_text(encoding="utf-8")

    # F-005 must be marked RESOLVED (the ledger is clean).
    assert "F-005" in text
    f005_block = _extract_failure_block(text, "F-005")
    assert "RESOLVED" in f005_block, (
        "F-AUD-004 regression: F-005 is marked OPEN in FAILURES.md but "
        "the ledger has been regenerated (10 parseable entries, F-014 "
        "tests pass). Law 7 requires the failure taxonomy to track "
        "reality. Update F-005's status line to RESOLVED with the "
        "remediating commit."
    )

    # F-014 must be marked RESOLVED (the regression tests pass).
    assert "F-014" in text
    f014_block = _extract_failure_block(text, "F-014")
    assert "RESOLVED" in f014_block, (
        "F-AUD-004 regression: F-014 is marked OPEN but the regression "
        "tests (test_every_committed_jsonl_line_parses, "
        "test_no_one_char_per_line_pattern) pass on the current "
        "ledger state. Update F-014's status line to RESOLVED."
    )


def _extract_failure_block(text, fid):
    """Return the text between the `### F-XXX` heading and the next
    `### ` heading (or end of file)."""
    import re
    m = re.search(rf"### {fid}\b.*?(?=\n### |\Z)", text, re.DOTALL)
    return m.group(0) if m else ""


# ----------------------------------------------------------------------
# F-AUD-007 — graph_retriever resource leak
# ----------------------------------------------------------------------

def test_F_AUD_007_graph_retriever_cemetery_scan_uses_context_manager(tmp_path, monkeypatch):
    """F-AUD-007 regression.

    product/retrieval/graph_retriever.py::_cem() must read cemetery
    files with a context manager (``with open(...)``) rather than bare
    ``open(...).read()``. Bare open() leaks file descriptors when the
    read raises (e.g., on a permissions error or a binary file).

    We strip docstrings and comments before checking, so the test
    only inspects actual code lines.
    """
    import ast
    import inspect
    import textwrap
    from product.retrieval import graph_retriever
    src = inspect.getsource(graph_retriever.GraphRetriever._cem)
    # Dedent so ast.parse sees it as module-level code, then strip the
    # docstring so the test only inspects actual code lines.
    src = textwrap.dedent(src)
    tree = ast.parse(src)
    # Find the first Expr that's a string literal — that's the docstring.
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) \
                    and isinstance(node.body[0].value, ast.Constant) \
                    and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
            break
    # Re-serialize to source without the docstring.
    import ast
    code_only = ast.unparse(tree)
    assert "with open(" in code_only, (
        "F-AUD-007 regression: graph_retriever._cem() must use a "
        "`with open(...) as f:` context manager rather than bare "
        "`open(...).read()` to avoid leaking file descriptors."
    )
    # And there must be no bare open(...).read() pattern left in the code.
    import re
    bare_pattern = re.search(r"open\([^)]*\)\.read\(\)", code_only)
    assert not bare_pattern, (
        "F-AUD-007 regression: graph_retriever._cem() still uses "
        f"bare open(...).read() at: {bare_pattern.group(0)!r}. "
        "Convert to a context manager."
    )


# ----------------------------------------------------------------------
# F-AUD-012 — orchestrator hardcodes verification_status
# ----------------------------------------------------------------------

def test_F_AUD_012_chain_summary_derives_verification_status():
    """F-AUD-012 regression.

    _chain_summary() must NOT hardcode verification_status="integrated"
    as a string literal. The status must be derived from the
    verification engine's actual output (or the layer-8 output), so
    that if the verification layer ever produces a different status,
    the chain summary reflects it.

    Before the fix, the chain summary always said "integrated"
    regardless of what layer 8 actually concluded — a hardcoded
    string that lies about the system's state. We catch this by AST-
    inspecting _chain_summary: the value assigned to
    `verification_status` must NOT be a Constant (i.e., a literal).
    """
    import ast
    import inspect
    from invention_compiler.orchestrator import InventionCompiler

    src = inspect.getsource(InventionCompiler._chain_summary)
    # Dedent so ast.parse sees it as module-level code.
    import textwrap
    tree = ast.parse(textwrap.dedent(src))

    # Walk the AST. Find any dict literal that has a key
    # "verification_status" whose value is a Constant.
    hardcoded_literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if (isinstance(k, ast.Constant) and k.value == "verification_status"
                        and isinstance(v, ast.Constant)):
                    hardcoded_literals.append(v.value)
    assert not hardcoded_literals, (
        "F-AUD-012 regression: _chain_summary() hardcodes "
        f"verification_status={hardcoded_literals!r} as a string literal. "
        "This ignores the verification engine's actual output. Derive "
        "the status from layers[8] (or the verification_output dict) "
        "so the chain summary reflects what layer 8 concluded, not a "
        "constant."
    )
