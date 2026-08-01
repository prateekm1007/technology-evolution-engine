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
