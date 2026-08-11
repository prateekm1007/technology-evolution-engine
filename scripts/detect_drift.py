#!/usr/bin/env python3
"""Drift Detection Script (Discipline 3)."""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from benchmarks.drift.detector import create_baseline, detect_drift, load_baseline

def main():
    parser = argparse.ArgumentParser(description="TEE Drift Detection")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if not args.baseline and not args.compare and not args.report: args.compare = True
    print("=" * 60)
    print("TEE DRIFT DETECTION (Discipline 3)")
    print("=" * 60)
    if args.baseline:
        b = create_baseline()
        print(f"  Baseline created: {b['created_at']}")
        print(f"  Graph: {b['graph_signature']['nodes']} nodes, {b['graph_signature']['edges']} edges")
        print("  Immutable (Law 7).")
        return 0
    report = detect_drift()
    if report["status"] == "no_baseline":
        print(f"  {report['message']}")
        return 1
    print(f"  Status: {report['status']}")
    print(f"  Drifts: {report['total_drifts']} (H:{report['high']} M:{report['medium']} L:{report['low']})")
    for d in report.get("drifts",[]):
        print(f"    [{d['severity'][0].upper()}] {d['type']}: {d['detail']}")
    if args.report:
        p = ROOT / "benchmarks" / "drift" / "latest_report.json"
        with open(p, "w") as f: json.dump(report, f, indent=2)
        print(f"  Report: {p}")
    return 0 if report["status"] == "stable" else 1

if __name__ == "__main__":
    sys.exit(main())
