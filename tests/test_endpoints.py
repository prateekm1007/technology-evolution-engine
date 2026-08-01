"""
Smoke tests for the API surface.
Run: python -m pytest tests/test_endpoints.py -v
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "web" / "backend"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_analyze_responds_to_payload():
    """Different inputs must not return byte-identical responses."""
    a = client.post("/api/v1/analyze", json={
        "mode": "consumer", "input_type": "idea",
        "text": "reduce household water consumption"})
    b = client.post("/api/v1/analyze", json={
        "mode": "consumer", "input_type": "idea",
        "text": "grow food indoors with minimal energy"})
    assert a.status_code == 200
    assert b.status_code == 200
    assert a.json() != b.json(), \
        "analyze() returned identical responses — pipeline is stubbed"


def test_analyze_actually_consumes_input_text():
    """Guards against the 'text' field being silently dropped at the
    web-schema -> product-pipeline boundary (raw_text/problem_statement
    key mismatch)."""
    r = client.post("/api/v1/analyze", json={
        "mode": "consumer", "input_type": "idea",
        "text": "reduce household water consumption"})
    body = r.json()
    assert body.get("problem_summary"), \
        "problem_summary is empty — input text isn't reaching the pipeline"
    assert body.get("detected_domains") not in (None, [], ["general"]), \
        "domain detection fell back to 'general' — input text isn't reaching the pipeline"


def test_evidence_does_not_500():
    r = client.get("/api/v1/evidence")
    assert r.status_code == 200, f"evidence 500'd: {r.text[:200]}"
    body = r.json()
    assert "ledger" in body
    assert "malformed_lines" in body


def test_graph_returns_nodes():
    r = client.get("/api/v1/graph")
    assert r.status_code == 200
    body = r.json()
    assert body["node_count"] > 0
    assert len(body["nodes"]) == body["node_count"]


def test_analyze_does_not_lie_about_verification():
    """F-001 follow-up: per Law 8 and the handoff rule 'No verified label
    without failure cases', a successful analyze() call must NOT be stamped
    'verified'. We don't have adversarial tests + replay + failure logging
    yet, so 'integrated' is the honest ceiling."""
    r = client.post("/api/v1/analyze", json={
        "mode": "consumer", "input_type": "idea",
        "text": "reduce household water consumption"})
    assert r.status_code == 200
    body = r.json()
    level = body.get("verification", {}).get("level")
    assert level != "verified", \
        f"analyze() stamped 'verified' without adversarial tests — lying about verification (got {level!r})"
    assert level == "integrated", \
        f"expected 'integrated', got {level!r}"


def test_analyze_accepts_problem_statement_field():
    """F-001 follow-up: a caller sending only 'problem_statement' (no 'text')
    must not have their input silently dropped at the schema boundary."""
    r = client.post("/api/v1/analyze", json={
        "mode": "consumer", "input_type": "idea",
        "problem_statement": "grow food indoors with minimal energy and water"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("problem_summary"), \
        "problem_summary empty — problem_statement field was dropped at schema boundary"


def test_evidence_detects_total_corruption(tmp_path, monkeypatch):
    """F-002: when the ledger is written one-char-per-line (the real failure
    mode on main right now), the endpoint must NOT report spurious 'valid'
    entries (single digits parsing as JSON numbers). It must flag the file
    as totally corrupted and return entry_count=0."""
    import main as main_module
    import json as _json
    # Build a totally-corrupted ledger: real JSON, but written one char per line.
    # Make the payload large enough that the >500-line heuristic trips —
    # mirroring the actual failure mode on main (703 lines from a 1403-byte file).
    entries = [{"id": str(i), "prediction": f"p{i}", "outcome": "pending",
                "rationale": "x" * 40} for i in range(50)]
    real = "\n".join(_json.dumps(e) for e in entries)
    corrupted = "\n".join(list(real)) + "\n"
    # evidence() looks at <gm.root>/data/ledger/predictions.jsonl
    ledger_dir = tmp_path / "data" / "ledger"
    ledger_dir.mkdir(parents=True)
    fake_ledger = ledger_dir / "predictions.jsonl"
    fake_ledger.write_text(corrupted, encoding="utf-8")

    # Point the evidence() endpoint at our fake ledger root.
    monkeypatch.setattr(main_module.gm, "root", tmp_path)

    r = client.get("/api/v1/evidence")
    assert r.status_code == 200, f"evidence 500'd: {r.text[:200]}"
    body = r.json()
    assert body["entry_count"] == 0, \
        f"total-corruption should yield 0 entries, got {body['entry_count']}"
    assert any("Total file corruption" in m.get("error", "") for m in body["malformed_lines"]), \
        "expected a 'Total file corruption' malformed entry"

