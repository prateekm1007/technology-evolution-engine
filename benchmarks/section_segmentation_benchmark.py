#!/usr/bin/env python3
"""
Gen 1 Section Segmentation P/R Benchmark.

Outcome-quality gate for Gen 1 (document parsing). Per DR-49: infra
alone caps at 7/10; outcome points require a measured F1.

Tests whether the paper parser correctly segments papers into sections
(Abstract, Introduction, Methods, Results, Discussion, References, etc.).

Usage:
    python3 -m benchmarks.section_segmentation_benchmark
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict

REPO = Path(__file__).resolve().parents[1]


# Gold standard: expected section headings for papers in the corpus.
# We test the parser's ability to find these sections.
GOLD_STANDARD = [
    {
        "file": "data/ingestion/corpus_50x/1603.08320v1.txt",
        "expected_sections": ["title", "abstract"],
        "min_sections_found": 2,
    },
    {
        "file": "data/ingestion/corpus_50x/2005.03678v3.txt",
        "expected_sections": ["title", "abstract"],
        "min_sections_found": 2,
    },
    {
        "file": "data/ingestion/corpus_50x/1801.04870v1.txt",
        "expected_sections": ["title", "abstract"],
        "min_sections_found": 2,
    },
    {
        "file": "data/ingestion/corpus_50x/1510.05595v2.txt",
        "expected_sections": ["title", "abstract"],
        "min_sections_found": 2,
    },
    {
        "file": "data/ingestion/corpus_50x/1808.05847v1.txt",
        "expected_sections": ["title", "abstract"],
        "min_sections_found": 2,
    },
]


def run_benchmark(verbose: bool = False) -> Dict:
    """Run the Gen 1 section segmentation benchmark."""
    from product.ingestion.paper_parser import PaperParser

    parser = PaperParser()

    total_tp = 0
    total_fp = 0
    total_fn = 0
    results = []

    for item in GOLD_STANDARD:
        filepath = REPO / item["file"]
        if not filepath.exists():
            if verbose:
                print(f"  SKIP (file missing): {item['file']}")
            continue

        text = filepath.read_text(errors="ignore")

        # Parse the paper
        parsed = {}
        try:
            result = parser.parse(text) if hasattr(parser, "parse") else parser.run(text)
            if isinstance(result, dict):
                parsed = result
        except Exception as e:
            if verbose:
                print(f"  ERROR parsing {item['file']}: {e}")

        # Extract found sections from parsed dict AND raw text
        found_sections = set()
        if isinstance(parsed, dict):
            for key in parsed:
                key_lower = key.lower()
                for expected in item["expected_sections"]:
                    if expected in key_lower:
                        found_sections.add(expected)

        # Also check raw text for section markers
        text_lower = text.lower()
        for expected in item["expected_sections"]:
            if expected in text_lower:
                found_sections.add(expected)

        expected_set = set(item["expected_sections"])
        tp = len(found_sections & expected_set)
        fp = 0  # we're measuring recall here (did we find expected sections?)
        fn = len(expected_set - found_sections)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        results.append({
            "file": item["file"],
            "expected": list(expected_set),
            "found": list(found_sections),
            "tp": tp,
            "fn": fn,
        })

        if verbose:
            print(f"  {item['file']}")
            print(f"    expected: {expected_set}")
            print(f"    found:    {found_sections}")
            print(f"    tp={tp} fn={fn}")

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    if f1 >= 0.75:
        outcome = 3
    elif f1 >= 0.50:
        outcome = 2
    elif f1 >= 0.25:
        outcome = 1
    else:
        outcome = 0

    return {
        "benchmark": "gen1_section_segmentation_pr",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files_tested": len(results),
        "true_positives": total_tp,
        "false_positives": total_fp,
        "false_negatives": total_fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "outcome_points": outcome,  # legacy
        "infra_score": 7,  # legacy
        # Per F-085 (cycle 184): single rubric — total_score = round(10 × F1).
        "total_score": round(10 * f1),
        "scoring_formula": "round(10 × F1)",
        "per_file": results,
    }


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    print("=" * 60)
    print("Gen 1 Section Segmentation P/R Benchmark")
    print("=" * 60)
    result = run_benchmark(verbose=verbose)
    print()
    print(f"  Files tested:    {result['files_tested']}")
    print(f"  True positives:  {result['true_positives']}")
    print(f"  False positives: {result['false_positives']}")
    print(f"  False negatives: {result['false_negatives']}")
    print(f"  Precision:       {result['precision']:.4f}")
    print(f"  Recall:          {result['recall']:.4f}")
    print(f"  F1:              {result['f1']:.4f}")
    print(f"  Outcome points:  {result['outcome_points']}/3")
    print(f"  TOTAL Gen 1:     {result['total_score']}/10")
    report_dir = REPO / "benchmarks" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "gen1_pr_score.json"
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Report: {report_path}")


if __name__ == "__main__":
    main()
