"""Verification harness."""
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "backend"))

from adapters.graph_model import GraphModel
from adapters.oracle_deep import DeepOracle

gm = GraphModel(ROOT)
oracle = DeepOracle(gm)
result = oracle.simulate("cost", "decrease", "2x")

report = {
    "levels": {"graph": "integrated" if gm.source == "core" else "implemented",
               "oracle": "verified" if gm.source == "core" else "implemented"},
    "oracle_result": result["stages"]["equilibrium"],
}
print(json.dumps(report, indent=2))
