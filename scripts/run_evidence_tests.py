#!/usr/bin/env python3
"""
Evidence Benchmark Harness v1.0
================================

Usage:
    python scripts/run_evidence_tests.py [--patents] [--consumer] [--all] [--verbose]

Reproducibility: Same inputs + same code = same outputs. Always.
No hidden state. No manual intervention. No editing after execution.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmarks.scoring.scorer import EvidenceScorer, WEIGHTS

PATENT_INPUT_DIR = ROOT / "benchmarks" / "patents" / "input"
CONSUMER_INPUT_DIR = ROOT / "benchmarks" / "consumer" / "input"
OUTPUT_DIR = ROOT / "benchmarks" / "outputs"
REPORT_DIR = ROOT / "benchmarks" / "reports"
SCORING_DIR = ROOT / "benchmarks" / "scoring"
LEDGER_DIR = ROOT / "data" / "ledger"


def ensure_dirs():
    for d in [OUTPUT_DIR, REPORT_DIR, SCORING_DIR, LEDGER_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def run_business_pipeline(input_data):
    start = time.time()
    try:
        from product.business.pipeline import BusinessPipeline
        pipeline = BusinessPipeline()
        result = pipeline.run(input_data)
    except Exception as e:
        result = {"error": str(e), "report": {}, "blueprint": {}, "permutations": []}
    duration = time.time() - start
    return {
        "id": input_data.get("id", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 3),
        "pipeline": "business",
        "assumptions": result.get("assumptions", ["Graph contains seed nodes only","Scoring uses rule-based heuristics","No external API calls made"]),
        "confidence": result.get("confidence", 0.0),
        "adjacency_score": result.get("adjacency_score", 0.0),
        "pcs": result.get("pcs", 0.0),
        "rps": result.get("rps", 0.0),
        "blueprint_score": result.get("blueprint_score", 0.0),
        "destroyer_score": result.get("destroyer_score", 0.0),
        "warnings": result.get("warnings", []),
        "report": result.get("report", {}),
        "blueprint": result.get("blueprint", {}),
        "permutations": result.get("permutations", []),
        "metadata": {"input_domain": input_data.get("domain",""), "input_source": input_data.get("source",""),
                     "engine_version": "0.1.0", "assumptions": result.get("assumptions",[]),
                     "confidence": result.get("confidence",0.0), "warnings": result.get("warnings",[])},
    }


def run_consumer_pipeline(input_data):
    start = time.time()
    try:
        from product.consumer.pipeline import ConsumerPipeline
        pipeline = ConsumerPipeline()
        result = pipeline.run(input_data)
    except Exception as e:
        result = {"error": str(e), "report": {}, "blueprint": {}, "permutations": []}
    duration = time.time() - start
    return {
        "id": input_data.get("id", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(duration, 3),
        "pipeline": "consumer",
        "assumptions": result.get("assumptions", ["Graph contains seed nodes only","Scoring uses rule-based heuristics","No external API calls made"]),
        "confidence": result.get("confidence", 0.0),
        "adjacency_score": result.get("adjacency_score", 0.0),
        "pcs": result.get("pcs", 0.0),
        "rps": result.get("rps", 0.0),
        "blueprint_score": result.get("blueprint_score", 0.0),
        "destroyer_score": result.get("destroyer_score", 0.0),
        "warnings": result.get("warnings", []),
        "report": result.get("report", {}),
        "blueprint": result.get("blueprint", {}),
        "permutations": result.get("permutations", []),
        "metadata": {"input_domain": input_data.get("domain",""), "input_source": input_data.get("source",""),
                     "engine_version": "0.1.0", "assumptions": result.get("assumptions",[]),
                     "confidence": result.get("confidence",0.0), "warnings": result.get("warnings",[])},
    }


def load_inputs(input_dir):
    inputs = []
    if not input_dir.exists():
        return inputs
    for f in sorted(input_dir.glob("*.json")):
        with open(f, "r") as fh:
            inputs.append(json.load(fh))
    return inputs


def run_patent_benchmarks(verbose=False):
    inputs = load_inputs(PATENT_INPUT_DIR)
    results = []
    scorer = EvidenceScorer()
    print(f"\n{'='*60}")
    print(f"PATENT BENCHMARKS: {len(inputs)} inputs")
    print(f"{'='*60}")
    for i, inp in enumerate(inputs, 1):
        bid = inp.get("id", f"patent_{i:04d}")
        domain = inp.get("domain", "unknown")
        if verbose:
            print(f"\n[{i}/{len(inputs)}] {bid}: {inp.get('title','')} ({domain})")
        else:
            print(f"  [{i}/{len(inputs)}] {bid}...", end=" ", flush=True)
        output = run_business_pipeline(inp)
        score = scorer.score_business(inp, output)
        with open(OUTPUT_DIR / f"{bid}_output.json", "w") as f:
            json.dump(output, f, indent=2)
        with open(REPORT_DIR / f"{bid}_score.json", "w") as f:
            json.dump(score.to_dict(), f, indent=2)
        results.append({"id": bid, "domain": domain, "grade": score.grade,
                        "composite": round(score.composite_score, 4), "duration": output["duration_seconds"]})
        if verbose:
            print(f"    Grade: {score.grade} | Composite: {score.composite_score:.4f} | Time: {output['duration_seconds']}s")
            for dn, ds in score.dimensions.items():
                print(f"      {dn}: {ds.raw_score:.3f} (w={ds.weight})")
        else:
            print(f"Grade={score.grade} Score={score.composite_score:.3f}")
    return results


def run_consumer_benchmarks(verbose=False):
    inputs = load_inputs(CONSUMER_INPUT_DIR)
    results = []
    scorer = EvidenceScorer()
    print(f"\n{'='*60}")
    print(f"CONSUMER BENCHMARKS: {len(inputs)} inputs")
    print(f"{'='*60}")
    for i, inp in enumerate(inputs, 1):
        bid = inp.get("id", f"consumer_{i:04d}")
        domain = inp.get("domain", "unknown")
        if verbose:
            print(f"\n[{i}/{len(inputs)}] {bid}: \"{inp.get('prompt','')[:60]}...\" ({domain})")
        else:
            print(f"  [{i}/{len(inputs)}] {bid}...", end=" ", flush=True)
        output = run_consumer_pipeline(inp)
        score = scorer.score_consumer(inp, output)
        with open(OUTPUT_DIR / f"{bid}_output.json", "w") as f:
            json.dump(output, f, indent=2)
        with open(REPORT_DIR / f"{bid}_score.json", "w") as f:
            json.dump(score.to_dict(), f, indent=2)
        results.append({"id": bid, "domain": domain, "grade": score.grade,
                        "composite": round(score.composite_score, 4), "duration": output["duration_seconds"]})
        if verbose:
            print(f"    Grade: {score.grade} | Composite: {score.composite_score:.4f} | Time: {output['duration_seconds']}s")
            for dn, ds in score.dimensions.items():
                print(f"      {dn}: {ds.raw_score:.3f} (w={ds.weight})")
        else:
            print(f"Grade={score.grade} Score={score.composite_score:.3f}")
    return results


def generate_summary(patent_results, consumer_results):
    all_results = patent_results + consumer_results
    if not all_results:
        return {"error": "No benchmarks run"}
    composites = [r["composite"] for r in all_results]
    grades = [r["grade"] for r in all_results]
    grade_counts = {}
    for g in grades:
        grade_counts[g] = grade_counts.get(g, 0) + 1
    domain_scores = {}
    for r in all_results:
        d = r["domain"]
        if d not in domain_scores: domain_scores[d] = []
        domain_scores[d].append(r["composite"])
    domain_averages = {d: round(sum(s)/len(s), 4) for d, s in domain_scores.items()}
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_benchmarks": len(all_results),
        "patent_benchmarks": len(patent_results),
        "consumer_benchmarks": len(consumer_results),
        "overall_composite_mean": round(sum(composites)/len(composites), 4),
        "overall_composite_min": round(min(composites), 4),
        "overall_composite_max": round(max(composites), 4),
        "grade_distribution": grade_counts,
        "domain_averages": domain_averages,
        "weights": WEIGHTS,
        "results": all_results,
    }
    with open(SCORING_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def log_to_ledger(summary):
    ledger_path = LEDGER_DIR / "predictions.jsonl"
    entry = {
        "type": "benchmark_run",
        "timestamp": summary.get("timestamp", ""),
        "total_benchmarks": summary.get("total_benchmarks", 0),
        "overall_composite_mean": summary.get("overall_composite_mean", 0),
        "grade_distribution": summary.get("grade_distribution", {}),
        "assumptions": ["Rule-based scoring", "Seed graph only", "No external data"],
        "falsification_criteria": "Composite mean below 0.3 after 50 benchmarks indicates fundamental pipeline failure.",
        # Law 8 replayability: every entry MUST name the writer that
        # produced it. Without this field the entry is unprovenanced
        # and the Law 8 enforcement script will refuse to support any
        # "verified" claim that depends on it.
        "writer": "scripts.run_evidence_tests.log_to_ledger",
    }
    with open(ledger_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="TEE Evidence Benchmark Harness")
    parser.add_argument("--patents", action="store_true", help="Run patent benchmarks only")
    parser.add_argument("--consumer", action="store_true", help="Run consumer benchmarks only")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    if not args.patents and not args.consumer:
        args.all = True
    ensure_dirs()
    print("=" * 60)
    print("TEE EVIDENCE BENCHMARK HARNESS v1.0")
    print("=" * 60)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Root: {ROOT}")
    mode = "all" if args.all else ("patents" if args.patents else "consumer")
    print(f"Mode: {mode}")
    print()
    patent_results = []
    consumer_results = []
    if args.all or args.patents:
        patent_results = run_patent_benchmarks(verbose=args.verbose)
    if args.all or args.consumer:
        consumer_results = run_consumer_benchmarks(verbose=args.verbose)
    summary = generate_summary(patent_results, consumer_results)
    log_to_ledger(summary)
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total benchmarks:     {summary['total_benchmarks']}")
    print(f"Patent benchmarks:    {summary['patent_benchmarks']}")
    print(f"Consumer benchmarks:  {summary['consumer_benchmarks']}")
    print(f"Overall composite:    {summary['overall_composite_mean']}")
    print(f"Grade distribution:   {summary['grade_distribution']}")
    print(f"\nDomain averages:")
    for domain, avg in sorted(summary.get("domain_averages", {}).items()):
        print(f"  {domain:20s} {avg:.4f}")
    print(f"\nOutputs:   {OUTPUT_DIR}")
    print(f"Reports:   {REPORT_DIR}")
    print(f"Scoring:   {SCORING_DIR / 'summary.json'}")
    print(f"Ledger:    {LEDGER_DIR / 'predictions.jsonl'}")
    print(f"\n{'='*60}")
    print("BENCHMARK RUN COMPLETE")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
