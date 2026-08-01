#!/usr/bin/env python3
"""
Patent Wedge CLI

Usage:
    python scripts/run_wedge.py --text "patent text here" --title "My Patent"
    python scripts/run_wedge.py --file path/to/patent.json
    python scripts/run_wedge.py --file path/to/patent.txt
    python scripts/run_wedge.py --batch path/to/patents_directory/
    python scripts/run_wedge.py --dd-summary

Outputs:
    Full discovery report with Discovery Delta score.
    Results printed to stdout and saved to benchmarks/outputs/.
"""

import argparse
import json
import os
import sys
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from product.discovery.wedge import PatentWedge


def main():
    parser = argparse.ArgumentParser(description="Patent Wedge: discover everything a patent could become")
    parser.add_argument("--text", type=str, help="Raw patent text to analyze")
    parser.add_argument("--title", type=str, default="Untitled Patent", help="Patent title")
    parser.add_argument("--file", type=str, help="Path to patent file (JSON or text)")
    parser.add_argument("--batch", type=str, help="Directory of patent files to batch analyze")
    parser.add_argument("--dd-summary", action="store_true", help="Print DD summary from previous runs")
    parser.add_argument("--output", type=str, default=None, help="Output file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    wedge = PatentWedge()

    if args.dd_summary:
        dd_path = os.path.join("benchmarks", "outputs", "dd_history.json")
        if os.path.exists(dd_path):
            with open(dd_path) as f:
                data = json.load(f)
            print(json.dumps(data.get("summary", {}), indent=2))
        else:
            print("No DD history found. Run some analyses first.")
        return

    if args.text:
        result = wedge.analyze_text(args.text, args.title)
        _print_result(result, args.verbose)
        _save_result(result, args.output)

    elif args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        result = wedge.analyze_file(args.file)
        _print_result(result, args.verbose)
        _save_result(result, args.output)

    elif args.batch:
        if not os.path.isdir(args.batch):
            print(f"Error: Directory not found: {args.batch}")
            sys.exit(1)
        files = sorted(
            glob.glob(os.path.join(args.batch, "*.json"))
            + glob.glob(os.path.join(args.batch, "*.txt"))
        )
        if not files:
            print(f"No .json or .txt files found in {args.batch}")
            sys.exit(1)

        inputs = []
        for f in files:
            if f.endswith(".json"):
                with open(f) as fh:
                    inputs.append(json.load(fh))
            else:
                with open(f) as fh:
                    inputs.append({
                        "id": os.path.basename(f).replace(".txt", ""),
                        "title": os.path.basename(f),
                        "text": fh.read(),
                        "source": "batch_upload",
                    })

        result = wedge.batch_analyze(inputs)
        print(f"Batch analysis complete: {result['total']} patents")
        print(f"DD Summary: {json.dumps(result['dd_summary'], indent=2)}")
        _save_result(result, args.output)

    else:
        parser.print_help()
        sys.exit(1)

    # Export DD history
    dd_path = os.path.join("benchmarks", "outputs", "dd_history.json")
    os.makedirs(os.path.dirname(dd_path), exist_ok=True)
    wedge.export_dd(dd_path)


def _print_result(result, verbose=False):
    print("=" * 60)
    print(f"PATENT WEDGE ANALYSIS")
    print(f"Patent: {result.get('title', 'Unknown')}")
    print(f"Domain: {result.get('domain', 'Unknown')}")
    print(f"Duration: {result.get('duration_seconds', 0)}s")
    print("=" * 60)

    dd = result.get("discovery_delta", {})
    print(f"\nDiscovery Delta: {dd.get('dd', 0)}")
    print(f"Interpretation: {dd.get('interpretation', 'N/A')}")
    print(f"\nDimensions:")
    for dim, score in dd.get("dimensions", {}).items():
        print(f"  {dim}: {score}")

    print(f"\nPermutations generated: {result.get('permutation_count', 0)}")
    print(f"Scored candidates: {result.get('scored_candidate_count', 0)}")
    print(f"Cemetery matches: {len(result.get('cemetery_matches', []))}")
    print(f"Blueprints: {len(result.get('blueprints', []))}")

    if verbose:
        print(f"\nAssumptions:")
        for a in result.get("assumptions", []):
            print(f"  - {a}")
        print(f"\nWarnings:")
        for w in result.get("warnings", []):
            print(f"  - {w}")

    print("=" * 60)


def _save_result(result, output_path=None):
    if output_path is None:
        os.makedirs("benchmarks/outputs", exist_ok=True)
        pid = result.get("patent_id", result.get("total", "batch"))
        output_path = f"benchmarks/outputs/wedge_{pid}.json"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
