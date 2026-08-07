"""CI gate: measurement trace exists and has required fields."""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def test_measurement_trace_exists():
    """reports/measurement_trace.json exists with per-hit explanations."""
    repo = Path(__file__).resolve().parents[1]
    trace_path = repo / "reports" / "measurement_trace.json"
    assert trace_path.exists(), "measurement_trace.json must exist"
    with open(trace_path) as f:
        traces = json.load(f)
    assert len(traces) > 0, "Trace must have at least one entry"
    for t in traces:
        assert "bridge" in t
        assert "locus_classification" in t
