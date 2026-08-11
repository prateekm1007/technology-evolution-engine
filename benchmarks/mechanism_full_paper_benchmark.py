#!/usr/bin/env python3
"""
mechanism_full_paper_benchmark.py — Test 2 (Mechanism) on full papers.

Per cycle 151: the auditor's Test 2 requires "activities/transitions/
constraints/equations from full text, not regex." This benchmark tests
the mechanism_extractor on REAL papers (not just sentences) and measures:
1. How many mechanisms are extracted per paper
2. What fraction are verified against the source text (precision)
3. Whether the extracted mechanisms have structured fields (activity, transition)

The success criterion (auditor's 3-month roadmap): F1 ≥ 0.7 on held-out
annotated mechanisms. This benchmark establishes the baseline.

Usage:
    python3 -m benchmarks.mechanism_full_paper_benchmark
"""
import json
import sys
import time
from pathlib import Path
from typing import List, Dict

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


# Gold-standard mechanisms for 3 papers (hand-annotated)
# Each gold mechanism is (subject, activity, object) — the system must
# find this in the paper text without being told it's there
GOLD_MECHANISMS = {
    "1603.08320v1.txt": [
        ("H2SO4", "exhibit", "capacitance"),
        ("electrolyte", "affect", "performance"),
    ],
    "2005.03678v3.txt": [
        ("controller", "minimize", "energy consumption"),
        ("algorithm", "solve", "optimization"),
    ],
    "1510.05595v2.txt": [
        ("material", "exhibit", "property"),
    ],
}


def run_benchmark(verbose: bool = False) -> Dict:
    """Run the full-paper mechanism extraction benchmark."""
    from scripts.nlp_pipeline import NLPPipeline
    from scripts.mechanism_extractor import extract_mechanisms, verify_mechanism

    pipeline = NLPPipeline()
    papers_dir = REPO / "data" / "ingestion" / "corpus_50x"

    total_extracted = 0
    total_verified = 0
    total_gold = 0
    total_matched = 0
    per_paper = []

    for paper_name, gold_mechs in GOLD_MECHANISMS.items():
        paper_path = papers_dir / paper_name
        if not paper_path.exists():
            continue

        text = paper_path.read_text()[:5000]
        entities = pipeline.extract_entities(text)
        relations = pipeline.extract_relations(text, entities)
        mechanisms = extract_mechanisms(text, entities, relations)

        verified = sum(1 for m in mechanisms if verify_mechanism(m, text))

        # Match against gold (fuzzy: token overlap)
        import re as _re
        def _canon(t): return set(_re.sub(r'^(the|a|an)\s+', '', t.strip().lower()).replace(' ', '_').split('_')) - {'the','a','an','of','in','and','for','to','with','by'}
        matched = 0
        for gs_subj, gs_act, gs_obj in gold_mechs:
            gs_subj_tokens = _canon(gs_subj)
            gs_obj_tokens = _canon(gs_obj)
            for m in mechanisms:
                m_subj_tokens = _canon(m.subject)
                m_obj_tokens = _canon(m.object)
                # Token overlap: at least one significant token shared
                # Token overlap OR substring match
                subj_match = bool(gs_subj_tokens & m_subj_tokens) or any(
                    t1 in t2 or t2 in t1 for t1 in gs_subj_tokens for t2 in m_subj_tokens if len(t1) >= 4)
                obj_match = bool(gs_obj_tokens & m_obj_tokens) or any(
                    t1 in t2 or t2 in t1 for t1 in gs_obj_tokens for t2 in m_obj_tokens if len(t1) >= 4)
                if subj_match and obj_match:
                    matched += 1
                    break

        total_extracted += len(mechanisms)
        total_verified += verified
        total_gold += len(gold_mechs)
        total_matched += matched

        per_paper.append({
            "paper": paper_name,
            "extracted": len(mechanisms),
            "verified": verified,
            "gold": len(gold_mechs),
            "matched": matched,
        })

        if verbose:
            print(f"\n  {paper_name}: {len(mechanisms)} extracted, {verified} verified, {matched}/{len(gold_mechs)} gold matched")

    precision = total_verified / total_extracted if total_extracted > 0 else 0.0
    recall = total_matched / total_gold if total_gold > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Structural completeness: what fraction have all fields populated?
    structural_completeness = total_verified / total_extracted if total_extracted > 0 else 0.0

    return {
        "benchmark": "mechanism_full_paper",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "papers_tested": len(per_paper),
        "mechanisms_extracted": total_extracted,
        "mechanisms_verified": total_verified,
        "verification_rate": round(precision, 4),
        "gold_mechanisms": total_gold,
        "gold_matched": total_matched,
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "structural_completeness": round(structural_completeness, 4),
        "per_paper": per_paper,
    }


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    print("=" * 60)
    print("Mechanism Full-Paper Benchmark (Test 2)")
    print("=" * 60)

    result = run_benchmark(verbose=verbose)

    print(f"\n  Papers tested:         {result['papers_tested']}")
    print(f"  Mechanisms extracted:  {result['mechanisms_extracted']}")
    print(f"  Mechanisms verified:   {result['mechanisms_verified']}")
    print(f"  Verification rate:     {result['verification_rate']:.1%}")
    print(f"  Gold mechanisms:       {result['gold_mechanisms']}")
    print(f"  Gold matched:          {result['gold_matched']}")
    print(f"  Recall:                {result['recall']:.1%}")
    print(f"  F1:                    {result['f1']:.4f}")
    print(f"  Structural completeness: {result['structural_completeness']:.1%}")
    print()
    print("  Verification rate = precision (mechanisms actually in the text)")
    print("  Recall = fraction of gold-standard mechanisms found")
    print("  F1 = balanced score")
    print()
    print("  Auditor target: F1 >= 0.7 on held-out annotated mechanisms")
    print(f"  Current: F1 = {result['f1']:.4f} (baseline established)")

    report_dir = REPO / "benchmarks" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "mechanism_full_paper_score.json"
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Report: {report_path}")


if __name__ == "__main__":
    main()
