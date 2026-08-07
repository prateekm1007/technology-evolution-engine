#!/usr/bin/env python3
"""
dr91_phase6_7.py — DR-91 Phase VI (Component Attribution) + Phase VII (Adversarial) (cycle 244).

Per CTO review (post-243):
  "Phase VI: Component Attribution. Disable each component, measure
   ΔFP and ΔRecall. Eventually you'll produce a table showing exactly
   where the disease lives.

   Phase VII: Adversarial Benchmark Construction. Don't repair the
   benchmark. Try to destroy it. Intentionally."

Phase VI — Component Attribution:
  For each component (synonyms, token overlap, proposal inflation,
  background entities), disable it and measure the change in:
  - FP floor (false-positive rate)
  - Recall (true discovery rate)
  This isolates WHICH component causes the catastrophic FP=1.0.

Phase VII — Adversarial Benchmark:
  Generate fake bridges designed to fool the benchmark:
  - Scientifically plausible nonsense (real words, no real bridge)
  - Cross-domain distractors (real concepts from wrong domains)
  - Nearly identical bridges (1-token edits of real gold)
  - Bridges with identical nouns, different mechanisms
  Measure how many fake bridges "pass" — this is the adversarial FP rate.
"""
import sys
import re
import json
import math
import random
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from audit.measurement_integrity.dr91_measurement_audit import (
    canon, m_exact, m_token, m_fuzzy, m_synonym, m_reference,
    score, false_positive_audit,
)


# ============================================================================
# PHASE VI — COMPONENT ATTRIBUTION
# ============================================================================

def component_attribution(gold: List[Dict], all_entities: List[str],
                           shared_entities: List[str],
                           synmap: Dict[str, Set[str]]) -> List[Dict]:
    """Disable each component and measure ΔFP and ΔRecall.

    Components tested:
    1. Synonyms (disable synonym map)
    2. Token overlap (require exact match only)
    3. Proposal inflation (use shared entities only, not all)
    4. Background entities (remove entities that appear in only one document)

    For each, measure:
    - FP floor (false-positive rate with shuffled gold)
    - Recall (true discovery rate)
    - ΔFP and ΔRecall vs full system
    """
    results = []

    # Baseline: full system (all entities + synonyms)
    baseline_recall = score(gold, all_entities,
                            lambda e, c: m_synonym(e, c, synmap), "baseline").recall
    baseline_fp = false_positive_audit(gold, all_entities,
                                        lambda e, c: m_synonym(e, c, synmap),
                                        n_shuffles=200)["fp_floor"]

    results.append({
        "component": "BASELINE (all + synonyms)",
        "fp_floor": baseline_fp,
        "recall": baseline_recall,
        "delta_fp": 0.0,
        "delta_recall": 0.0,
    })

    # 1. Disable synonyms (token only)
    r1_recall = score(gold, all_entities, m_token, "no_synonyms").recall
    r1_fp = false_positive_audit(gold, all_entities, m_token, n_shuffles=200)["fp_floor"]
    results.append({
        "component": "Disable synonyms (token only)",
        "fp_floor": r1_fp,
        "recall": r1_recall,
        "delta_fp": round(r1_fp - baseline_fp, 4),
        "delta_recall": round(r1_recall - baseline_recall, 4),
    })

    # 2. Disable token overlap (exact only)
    r2_recall = score(gold, all_entities, m_exact, "exact_only").recall
    r2_fp = false_positive_audit(gold, all_entities, m_exact, n_shuffles=200)["fp_floor"]
    results.append({
        "component": "Disable token overlap (exact only)",
        "fp_floor": r2_fp,
        "recall": r2_recall,
        "delta_fp": round(r2_fp - baseline_fp, 4),
        "delta_recall": round(r2_recall - baseline_recall, 4),
    })

    # 3. Disable proposal inflation (shared only + synonyms)
    r3_recall = score(gold, shared_entities,
                      lambda e, c: m_synonym(e, c, synmap), "shared_only").recall
    r3_fp = false_positive_audit(gold, shared_entities,
                                  lambda e, c: m_synonym(e, c, synmap),
                                  n_shuffles=200)["fp_floor"]
    results.append({
        "component": "Disable proposal inflation (shared only)",
        "fp_floor": r3_fp,
        "recall": r3_recall,
        "delta_fp": round(r3_fp - baseline_fp, 4),
        "delta_recall": round(r3_recall - baseline_recall, 4),
    })

    # 4. Disable proposal inflation AND synonyms (shared + exact)
    r4_recall = score(gold, shared_entities, m_exact, "shared_exact").recall
    r4_fp = false_positive_audit(gold, shared_entities, m_exact, n_shuffles=200)["fp_floor"]
    results.append({
        "component": "Disable BOTH (shared + exact only)",
        "fp_floor": r4_fp,
        "recall": r4_recall,
        "delta_fp": round(r4_fp - baseline_fp, 4),
        "delta_recall": round(r4_recall - baseline_recall, 4),
    })

    # 5. Fuzzy only (no token, no synonym)
    r5_recall = score(gold, all_entities, m_fuzzy, "fuzzy_only").recall
    r5_fp = false_positive_audit(gold, all_entities, m_fuzzy, n_shuffles=200)["fp_floor"]
    results.append({
        "component": "Fuzzy only (no token, no synonym)",
        "fp_floor": r5_fp,
        "recall": r5_recall,
        "delta_fp": round(r5_fp - baseline_fp, 4),
        "delta_recall": round(r5_recall - baseline_recall, 4),
    })

    return results


# ============================================================================
# PHASE VII — ADVERSARIAL BENCHMARK CONSTRUCTION
# ============================================================================

def generate_adversarial_bridges(gold: List[Dict], all_entities: List[str],
                                  n_per_type: int = 20) -> Dict[str, List[str]]:
    """Generate fake bridges designed to fool the benchmark.

    5 adversarial types:
    1. PLAUSIBLE_NONSENSE: real scientific words, no real bridge
    2. CROSS_DOMAIN_DISTRACTORS: real concepts from wrong domains
    3. NEAR_IDENTICAL: 1-token edits of real gold bridges
    4. SAME_NOUN_DIFFERENT_MECHANISM: same noun, wrong verb/context
    5. RANDOM_ENTITIES: pure random (control)
    """
    rng = random.Random(42)

    # Collect real scientific words from entities
    all_words = set()
    for e in all_entities:
        for w in canon(e).split("_"):
            if len(w) >= 4:
                all_words.add(w)
    all_words = list(all_words)

    # Collect gold bridges
    gold_bridges = [g["bridge"] for g in gold]

    adversarial = {}

    # 1. PLAUSIBLE_NONSENSE: combine 2 random scientific words
    adversarial["plausible_nonsense"] = []
    for _ in range(n_per_type):
        w1, w2 = rng.sample(all_words, 2)
        adversarial["plausible_nonsense"].append(f"{w1}_{w2}")

    # 2. CROSS_DOMAIN_DISTRACTORS: entities from gold snippets
    # (these are real concepts but NOT the gold bridge)
    gold_bridges_set = {canon(b) for b in gold_bridges}
    distractors = [e for e in all_entities if canon(e) not in gold_bridges_set]
    rng.shuffle(distractors)
    adversarial["cross_domain_distractors"] = distractors[:n_per_type]

    # 3. NEAR_IDENTICAL: 1-token edits of gold bridges
    adversarial["near_identical"] = []
    for bridge in gold_bridges:
        tokens = canon(bridge).split("_")
        if len(tokens) >= 2:
            # Replace one token with a random word
            idx = rng.randint(0, len(tokens) - 1)
            new_tok = rng.choice(all_words)
            modified = tokens[:idx] + [new_tok] + tokens[idx+1:]
            adversarial["near_identical"].append("_".join(modified))
    # Trim to n_per_type
    adversarial["near_identical"] = adversarial["near_identical"][:n_per_type]

    # 4. SAME_NOUN_DIFFERENT_MECHANISM: same first noun, different second
    adversarial["same_noun_different"] = []
    for bridge in gold_bridges:
        tokens = canon(bridge).split("_")
        if len(tokens) >= 2:
            # Keep first token, replace rest with random
            new_rest = [rng.choice(all_words) for _ in tokens[1:]]
            modified = [tokens[0]] + new_rest
            adversarial["same_noun_different"].append("_".join(modified))
    adversarial["same_noun_different"] = adversarial["same_noun_different"][:n_per_type]

    # 5. RANDOM_ENTITIES: pure random (control)
    adversarial["random_entities"] = []
    for _ in range(n_per_type):
        adversarial["random_entities"].append(rng.choice(all_entities))

    return adversarial


def adversarial_test(adversarial_bridges: Dict[str, List[str]],
                      all_entities: List[str],
                      synmap: Dict[str, Set[str]]) -> List[Dict]:
    """Test how many adversarial bridges 'pass' the benchmark.

    If the benchmark is trustworthy, adversarial bridges should NOT match.
    If they DO match, the benchmark is foolable.
    """
    results = []
    for atype, bridges in adversarial_bridges.items():
        fake_gold = [{"bridge": b, "id": f"ADV-{i}"} for i, b in enumerate(bridges)]
        r = score(fake_gold, all_entities,
                  lambda e, c: m_synonym(e, c, synmap), f"adv_{atype}")
        # FP rate = recall on fake gold (should be ~0 if trustworthy)
        fp_rate = r.recall
        results.append({
            "adversarial_type": atype,
            "n_bridges": len(bridges),
            "n_matched": r.tp,
            "fp_rate": round(fp_rate, 4),
            "verdict": "PASS" if fp_rate < 0.05 else "FAIL",
        })
    return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DR-91 Phase VI+VII: Component Attribution + Adversarial (cycle 244)")
    print("=" * 80)
    print()

    from benchmarks.discovery_capability_benchmark import GOLD_DISCOVERIES, BRIDGE_SYNONYMS
    from scripts.nlp_pipeline import NLPPipeline

    pipeline = NLPPipeline()
    all_ents_a, all_ents_b, all_shared = [], [], []
    for gold in GOLD_DISCOVERIES:
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])
        lit_a = [(e.text.lower().replace(" ", "_"), e.label, e.text) for e in ents_a]
        lit_b = [(e.text.lower().replace(" ", "_"), e.label, e.text) for e in ents_b]
        a_labels = {e[0] for e in lit_a}
        b_labels = {e[0] for e in lit_b}
        shared = a_labels & b_labels
        all_ents_a.extend([e.text for e in ents_a])
        all_ents_b.extend([e.text for e in ents_b])
        all_shared.extend(shared)

    all_entities = list(set(all_ents_a + all_ents_b))
    shared_entities = list(set(all_shared))

    canon_syn = {}
    for k, v in BRIDGE_SYNONYMS.items():
        canon_syn[canon(k)] = {canon(s) for s in v}

    # === PHASE VI: Component Attribution ===
    print("=" * 80)
    print("PHASE VI: Component Attribution")
    print("Disable each component, measure ΔFP and ΔRecall")
    print("=" * 80)
    print()

    attr_results = component_attribution(GOLD_DISCOVERIES, all_entities,
                                          shared_entities, canon_syn)

    print(f"{'Component':<45} {'FP Floor':<10} {'Recall':<10} {'ΔFP':<10} {'ΔRecall':<10}")
    print("-" * 85)
    for r in attr_results:
        print(f"{r['component']:<45} {r['fp_floor']:<10.4f} {r['recall']:<10.4f} "
              f"{r['delta_fp']:>+10.4f} {r['delta_recall']:>+10.4f}")

    # Identify the disease
    print()
    worst_fp = max(attr_results[1:], key=lambda x: x["delta_fp"])
    best_fp = min(attr_results[1:], key=lambda x: x["delta_fp"])
    print(f"Component that reduces FP MOST when disabled: {best_fp['component']}")
    print(f"  ΔFP = {best_fp['delta_fp']:+.4f} (reduces FP by {abs(best_fp['delta_fp']):.4f})")
    print(f"  ΔRecall = {best_fp['delta_recall']:+.4f}")
    print()
    print(f"Component that reduces FP LEAST when disabled: {worst_fp['component']}")
    print(f"  ΔFP = {worst_fp['delta_fp']:+.4f}")

    # === PHASE VII: Adversarial Benchmark ===
    print()
    print("=" * 80)
    print("PHASE VII: Adversarial Benchmark Construction")
    print("Try to DESTROY the benchmark with fake bridges")
    print("=" * 80)
    print()

    adv_bridges = generate_adversarial_bridges(GOLD_DISCOVERIES, all_entities, n_per_type=20)
    adv_results = adversarial_test(adv_bridges, all_entities, canon_syn)

    print(f"{'Adversarial Type':<30} {'N':<6} {'Matched':<10} {'FP Rate':<10} {'Verdict':<8}")
    print("-" * 70)
    for r in adv_results:
        print(f"{r['adversarial_type']:<30} {r['n_bridges']:<6} {r['n_matched']:<10} "
              f"{r['fp_rate']:<10.4f} {r['verdict']:<8}")

    # Summary
    print()
    print("=" * 80)
    print("ADVERSARIAL SUMMARY")
    print("=" * 80)
    n_fail = sum(1 for r in adv_results if r["verdict"] == "FAIL")
    n_pass = sum(1 for r in adv_results if r["verdict"] == "PASS")
    print(f"Adversarial types that PASS (FP < 5%): {n_pass}/{len(adv_results)}")
    print(f"Adversarial types that FAIL (FP ≥ 5%): {n_fail}/{len(adv_results)}")
    print()
    if n_fail > 0:
        print("The benchmark CAN be fooled by:")
        for r in adv_results:
            if r["verdict"] == "FAIL":
                print(f"  {r['adversarial_type']}: {r['n_matched']}/{r['n_bridges']} fake bridges matched (FP={r['fp_rate']:.4f})")
    print()

    # Save reports
    reports_dir = Path(__file__).resolve().parents[2] / "reports"
    reports_dir.mkdir(exist_ok=True)

    with open(reports_dir / "component_attribution.json", "w") as f:
        json.dump(attr_results, f, indent=2)
    with open(reports_dir / "adversarial_results.json", "w") as f:
        json.dump({"bridges": adv_bridges, "results": adv_results}, f, indent=2)
    print(f"Saved to reports/component_attribution.json + adversarial_results.json")


if __name__ == "__main__":
    main()
