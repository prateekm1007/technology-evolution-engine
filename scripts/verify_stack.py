"""Verification harness."""
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "backend"))

from adapters.graph_model import GraphModel
from adapters.oracle_deep import DeepOracle

gm = GraphModel(ROOT)
oracle = DeepOracle(gm)
result = oracle.simulate("cost", "decrease", "2x")

# Law 8 honesty: gm.source == "core" means the static graph file
# loaded — that is presence-of-data, not verification. Downgraded from
# "verified" to "integrated" per the F-005 follow-up audit (F-011).
# The actual Law 8 verdict is produced by scripts/enforce_law8.py,
# which checks the ledger for >=1 successful prediction, >=1 failed
# prediction, and replayable evidence.
report = {
    "levels": {"graph": "integrated" if gm.source == "core" else "implemented",
               "oracle": "integrated" if gm.source == "core" else "implemented"},
    "oracle_result": result["stages"]["equilibrium"],
}
print(json.dumps(report, indent=2))
