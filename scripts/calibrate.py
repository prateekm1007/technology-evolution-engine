"""Calibration runner. python scripts/calibrate.py"""
import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "backend"))
from adapters.calibration import C
def main():
    lp = ROOT / "data" / "ledger" / "predictions.jsonl"
    ledger = [json.loads(l) for l in lp.read_text().splitlines() if l.strip()] if lp.exists() else []
    result = C.calibrate_from_ledger(ledger)
    report = {"calibration": result, "constants": C.status(), "ledger_entries": len(ledger)}
    dest = ROOT / "logs" / "calibration_report.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
if __name__ == "__main__": main()
