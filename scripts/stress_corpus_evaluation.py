#!/usr/bin/env python3
"""
stress_corpus_evaluation.py — Run the full 15-step pipeline on ALL 100 papers
and record per-paper metrics (cycle 193).

Per the CTO's directive: "I would create a stress corpus. Then I would execute
the entire pipeline against all 100 papers and record: entities per paper,
relations per paper, mechanisms per paper, constraints per paper, contradictions
per paper, interventions per paper, audit-overturn rates, execution time,
memory consumption."

This script does exactly that. It runs scripts/tee_full_pipeline.py on every
document in data/ingestion/corpus_50x/ and produces:
1. Per-paper metrics (JSONL)
2. Aggregate summary (JSON)
3. Per-domain breakdown (if domain hints available)
4. Honest report of weaknesses

Usage:
    python3 -m scripts.stress_corpus_evaluation
"""
import sys
import json
import time
import tracemalloc
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.nlp_pipeline import NLPPipeline
from scripts.tee_full_pipeline import run_full_pipeline

REPO = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO / "data" / "ingestion" / "corpus_50x"
OUTPUT_DIR = REPO / "benchmarks" / "reports"


def run_stress_evaluation(max_papers: int = 100) -> dict:
    """Run the full pipeline on all papers and collect metrics.

    Args:
        max_papers: maximum number of papers to process (default 100)

    Returns:
        dict with aggregate summary + per-paper results
    """
    pipeline = NLPPipeline()
    papers = sorted(CORPUS_DIR.glob("*.txt"))[:max_papers]

    per_paper_results = []
    domain_stats = defaultdict(lambda: {
        "papers": 0, "entities": 0, "relations": 0, "mechanisms": 0,
        "constraints": 0, "contradictions": 0, "interventions": 0,
        "laws": 0, "experiments": 0, "upheld": 0, "overturned": 0,
        "unresolved": 0, "total_time": 0, "total_memory_mb": 0,
        "total_confidence": 0,
    })

    total_start = time.time()
    tracemalloc.start()

    for i, doc_path in enumerate(papers):
        doc_start = time.time()
        tracemalloc.reset_peak()

        try:
            result = run_full_pipeline(doc_path, pipeline)
            elapsed = time.time() - doc_start
            current, peak = tracemalloc.get_traced_memory()
            peak_mb = peak / 1024 / 1024

            # Extract domain hint from the document
            text = doc_path.read_text()
            domain = "unknown"
            for line in text.split("\n"):
                if line.startswith("DOMAIN HINT:"):
                    domain = line.replace("DOMAIN HINT:", "").strip().lower()
                    break

            # Record per-paper metrics
            paper_metrics = {
                "document_id": result.document_id,
                "title": result.title[:100],
                "domain": domain,
                "execution_time_seconds": round(elapsed, 4),
                "peak_memory_mb": round(peak_mb, 4),
                "confidence": result.confidence,
                "entities": len(result.entities),
                "relations": len(result.relations),
                "mechanisms": len(result.mechanisms),
                "constraints": len(result.constraints),
                "contradictions": len(result.contradictions),
                "governing_laws": len(result.governing_laws),
                "missing_prerequisites": len(result.missing_prerequisites),
                "cross_domain_analogies": len(result.cross_domain_analogies),
                "candidate_interventions": len(result.candidate_interventions),
                "alternative_hypotheses": len(result.alternative_hypotheses),
                "counterexamples": len(result.counterexamples),
                "falsification_experiments": len(result.falsification_experiments),
                "locked_predictions": len(result.locked_predictions),
                "reaudit_verdict": result.reaudit_results.get("verdict", "UNKNOWN"),
                "failure_modes": len(result.failure_modes),
                "unresolved_questions": len(result.unresolved_questions),
            }
            per_paper_results.append(paper_metrics)

            # Update domain stats
            ds = domain_stats[domain]
            ds["papers"] += 1
            ds["entities"] += len(result.entities)
            ds["relations"] += len(result.relations)
            ds["mechanisms"] += len(result.mechanisms)
            ds["constraints"] += len(result.constraints)
            ds["contradictions"] += len(result.contradictions)
            ds["interventions"] += len(result.candidate_interventions)
            ds["laws"] += len(result.governing_laws)
            ds["experiments"] += len(result.falsification_experiments)
            ds["total_time"] += elapsed
            ds["total_memory_mb"] += peak_mb
            ds["total_confidence"] += result.confidence
            verdict = result.reaudit_results.get("verdict", "UNKNOWN")
            if verdict == "UPHELD":
                ds["upheld"] += 1
            elif verdict == "OVERTURNED":
                ds["overturned"] += 1
            else:
                ds["unresolved"] += 1

        except Exception as e:
            elapsed = time.time() - doc_start
            per_paper_results.append({
                "document_id": doc_path.stem,
                "title": "(error)",
                "domain": "unknown",
                "execution_time_seconds": round(elapsed, 4),
                "error": str(e)[:200],
                "entities": 0, "relations": 0, "mechanisms": 0,
                "constraints": 0, "contradictions": 0, "governing_laws": 0,
                "candidate_interventions": 0, "falsification_experiments": 0,
                "reaudit_verdict": "ERROR",
                "failure_modes": 1,
            })

        if (i + 1) % 10 == 0:
            print(f"  Processed {i+1}/{len(papers)} papers...")

    tracemalloc.stop()
    total_elapsed = time.time() - total_start

    # Compute aggregates
    n = len(per_paper_results)
    total_entities = sum(r.get("entities", 0) for r in per_paper_results)
    total_relations = sum(r.get("relations", 0) for r in per_paper_results)
    total_mechanisms = sum(r.get("mechanisms", 0) for r in per_paper_results)
    total_constraints = sum(r.get("constraints", 0) for r in per_paper_results)
    total_contradictions = sum(r.get("contradictions", 0) for r in per_paper_results)
    total_interventions = sum(r.get("candidate_interventions", 0) for r in per_paper_results)
    total_experiments = sum(r.get("falsification_experiments", 0) for r in per_paper_results)
    upheld = sum(1 for r in per_paper_results if r.get("reaudit_verdict") == "UPHELD")
    overturned = sum(1 for r in per_paper_results if r.get("reaudit_verdict") == "OVERTURNED")
    unresolved = sum(1 for r in per_paper_results if r.get("reaudit_verdict") == "UNRESOLVED")
    errors = sum(1 for r in per_paper_results if r.get("reaudit_verdict") == "ERROR")
    avg_confidence = sum(r.get("confidence", 0) for r in per_paper_results) / n if n else 0

    # Per-domain averages
    domain_averages = {}
    for domain, ds in domain_stats.items():
        n_dom = ds["papers"]
        if n_dom > 0:
            domain_averages[domain] = {
                "papers": n_dom,
                "avg_entities": round(ds["entities"] / n_dom, 1),
                "avg_relations": round(ds["relations"] / n_dom, 1),
                "avg_mechanisms": round(ds["mechanisms"] / n_dom, 1),
                "avg_constraints": round(ds["constraints"] / n_dom, 1),
                "avg_contradictions": round(ds["contradictions"] / n_dom, 1),
                "avg_interventions": round(ds["interventions"] / n_dom, 1),
                "avg_laws": round(ds["laws"] / n_dom, 1),
                "avg_experiments": round(ds["experiments"] / n_dom, 1),
                "avg_time_seconds": round(ds["total_time"] / n_dom, 4),
                "avg_memory_mb": round(ds["total_memory_mb"] / n_dom, 4),
                "avg_confidence": round(ds["total_confidence"] / n_dom, 4),
                "upheld": ds["upheld"],
                "overturned": ds["overturned"],
                "unresolved": ds["unresolved"],
            }

    summary = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_papers": n,
        "total_execution_time_seconds": round(total_elapsed, 2),
        "avg_time_per_paper_seconds": round(total_elapsed / n, 4) if n else 0,

        # Aggregate counts
        "total_entities": total_entities,
        "total_relations": total_relations,
        "total_mechanisms": total_mechanisms,
        "total_constraints": total_constraints,
        "total_contradictions": total_contradictions,
        "total_interventions": total_interventions,
        "total_experiments": total_experiments,

        # Per-paper averages
        "avg_entities_per_paper": round(total_entities / n, 1) if n else 0,
        "avg_relations_per_paper": round(total_relations / n, 1) if n else 0,
        "avg_mechanisms_per_paper": round(total_mechanisms / n, 1) if n else 0,
        "avg_constraints_per_paper": round(total_constraints / n, 1) if n else 0,
        "avg_contradictions_per_paper": round(total_contradictions / n, 1) if n else 0,
        "avg_interventions_per_paper": round(total_interventions / n, 1) if n else 0,
        "avg_experiments_per_paper": round(total_experiments / n, 1) if n else 0,
        "avg_confidence": round(avg_confidence, 4),

        # Re-audit verdicts
        "reaudit_upheld": upheld,
        "reaudit_overturned": overturned,
        "reaudit_unresolved": unresolved,
        "reaudit_errors": errors,
        "audit_overturn_rate": round(overturned / n, 4) if n else 0,

        # Per-domain breakdown
        "domain_breakdown": domain_averages,

        # Weaknesses (honest)
        "weaknesses": [],
    }

    # Identify weaknesses
    if summary["avg_relations_per_paper"] < 3:
        summary["weaknesses"].append(
            f"Low relation density: {summary['avg_relations_per_paper']:.1f} per paper (target: ≥3)"
        )
    if summary["avg_mechanisms_per_paper"] < 1:
        summary["weaknesses"].append(
            f"Low mechanism density: {summary['avg_mechanisms_per_paper']:.1f} per paper"
        )
    if summary["avg_constraints_per_paper"] < 1:
        summary["weaknesses"].append(
            f"Low constraint density: {summary['avg_constraints_per_paper']:.1f} per paper"
        )
    if summary["avg_confidence"] < 0.5:
        summary["weaknesses"].append(
            f"Low average confidence: {summary['avg_confidence']:.2f}"
        )

    # Write outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Per-paper results (JSONL)
    with (OUTPUT_DIR / "stress_corpus_per_paper.jsonl").open("w") as f:
        for r in per_paper_results:
            f.write(json.dumps(r, default=str) + "\n")

    # Summary (JSON)
    with (OUTPUT_DIR / "stress_corpus_summary.json").open("w") as f:
        json.dump(summary, f, indent=2, default=str)

    return summary


def main():
    print("=" * 70)
    print("STRESS CORPUS EVALUATION — 100 Papers, Full 15-Step Pipeline")
    print("=" * 70)
    print()

    summary = run_stress_evaluation(max_papers=100)

    print()
    print("=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Papers processed:      {summary['total_papers']}")
    print(f"Total execution time:  {summary['total_execution_time_seconds']}s")
    print(f"Avg time per paper:    {summary['avg_time_per_paper_seconds']}s")
    print()
    print("AGGREGATE COUNTS:")
    print(f"  Total entities:      {summary['total_entities']}")
    print(f"  Total relations:     {summary['total_relations']}")
    print(f"  Total mechanisms:    {summary['total_mechanisms']}")
    print(f"  Total constraints:   {summary['total_constraints']}")
    print(f"  Total contradictions:{summary['total_contradictions']}")
    print(f"  Total interventions: {summary['total_interventions']}")
    print(f"  Total experiments:   {summary['total_experiments']}")
    print()
    print("PER-PAPER AVERAGES:")
    print(f"  Entities/paper:      {summary['avg_entities_per_paper']}")
    print(f"  Relations/paper:     {summary['avg_relations_per_paper']}")
    print(f"  Mechanisms/paper:    {summary['avg_mechanisms_per_paper']}")
    print(f"  Constraints/paper:   {summary['avg_constraints_per_paper']}")
    print(f"  Interventions/paper: {summary['avg_interventions_per_paper']}")
    print(f"  Confidence:          {summary['avg_confidence']}")
    print()
    print("RE-AUDIT VERDICTS:")
    print(f"  Upheld:              {summary['reaudit_upheld']}")
    print(f"  Overturned:          {summary['reaudit_overturned']}")
    print(f"  Unresolved:          {summary['reaudit_unresolved']}")
    print(f"  Errors:              {summary['reaudit_errors']}")
    print(f"  Overturn rate:       {summary['audit_overturn_rate']:.4f}")
    print()
    print("PER-DOMAIN BREAKDOWN:")
    for domain, stats in sorted(summary["domain_breakdown"].items()):
        print(f"  {domain}: {stats['papers']} papers, "
              f"ent={stats['avg_entities']}, rel={stats['avg_relations']}, "
              f"mech={stats['avg_mechanisms']}, conf={stats['avg_confidence']}")
    print()
    if summary["weaknesses"]:
        print("WEAKNESSES (honest):")
        for w in summary["weaknesses"]:
            print(f"  ⚠ {w}")
    print()
    print("Outputs:")
    print(f"  Per-paper: benchmarks/reports/stress_corpus_per_paper.jsonl")
    print(f"  Summary:   benchmarks/reports/stress_corpus_summary.json")


if __name__ == "__main__":
    main()
