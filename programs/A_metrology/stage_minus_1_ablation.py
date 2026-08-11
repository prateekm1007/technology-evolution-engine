#!/usr/bin/env python3
"""
stage_minus1_ablation.py — Stage −1 Ablation: Proposal-Locus Measurement

Per the auditor's directive (cycle 272):
  "Do not fix the scorer yet. First measure the magnitude of the problem
   and record it. Changing the scorer before the ablation would destroy
   the very evidence we need."

This module measures the proposal-locus vulnerability WITHOUT fixing it.
It runs the existing scorer and records:
  1. How many TPs come from SHARED entities (genuine discovery)
  2. How many TPs come from the ALL-entities fallback (ambient presence)
  3. What the F1 would be if only shared-entity hits counted
  4. What the F1 would be if the ALL-entities fallback were removed
  5. What the precision would be if wrong proposals were counted as FP

This is measurement, not repair. The scorer is not modified.
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
REPO = Path(__file__).resolve().parents[2]

def _canon(text):
    t = text.lower().strip()
    t = re.sub(r'[\s\-]+', '_', t)
    t = re.sub(r'[^a-z0-9_]', '', t)
    t = re.sub(r'_+', '_', t)
    return t.strip('_')


def main():
    print("=" * 80)
    print("Stage −1 Ablation: Proposal-Locus Measurement")
    print("Per auditor directive: MEASURE, DO NOT FIX")
    print("=" * 80)
    print()

    from benchmarks.discovery_capability_benchmark import (
        GOLD_DISCOVERIES, BRIDGE_SYNONYMS, _bridge_matches
    )
    from scripts.nlp_pipeline import NLPPipeline
    from scripts.blind_test_runner import discover_shared_entities

    pipeline = NLPPipeline()

    # Reproduce the exact scoring logic from discovery_capability_benchmark.py
    # but with INSTRUMENTATION to record WHERE each hit came from
    tp_shared = 0       # hit from shared entities (genuine discovery)
    tp_fallback = 0     # hit from ALL-entities fallback (ambient presence)
    fn = 0              # missed entirely
    tp_total = 0        # current scorer's TP count

    per_gold = []

    for gold in GOLD_DISCOVERIES:
        # Extract entities (same as the benchmark)
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])

        lit_a_entities = [(e.text.lower().replace(" ", "_"), e.label, e.text) for e in ents_a]
        lit_b_entities = [(e.text.lower().replace(" ", "_"), e.label, e.text) for e in ents_b]

        shared = discover_shared_entities(lit_a_entities, lit_b_entities)

        # Check 1: SHARED entities (genuine discovery path)
        bridge_found_shared = False
        matched_label = None
        for nid, ntype, label in shared:
            if _bridge_matches(gold["bridge"], label):
                bridge_found_shared = True
                matched_label = label
                break

        # Check 2: ALL-entities fallback (ambient presence path)
        bridge_found_fallback = False
        fallback_label = None
        if not bridge_found_shared:
            for e in ents_a + ents_b:
                if _bridge_matches(gold["bridge"], e.text):
                    bridge_found_fallback = True
                    fallback_label = e.text
                    break

        # Current scorer counts either as TP
        bridge_found = bridge_found_shared or bridge_found_fallback

        locus = "SHARED" if bridge_found_shared else ("FALLBACK" if bridge_found_fallback else "MISSED")

        if bridge_found_shared:
            tp_shared += 1
            tp_total += 1
        elif bridge_found_fallback:
            tp_fallback += 1
            tp_total += 1
        else:
            fn += 1

        per_gold.append({
            "id": gold["id"],
            "bridge": gold["bridge"],
            "locus": locus,
            "matched_label": matched_label or fallback_label,
            "n_shared": len(shared),
            "n_ents_a": len(ents_a),
            "n_ents_b": len(ents_b),
        })

    n = len(GOLD_DISCOVERIES)

    # Current scorer metrics (with fallback)
    current_recall = tp_total / n
    current_precision = 1.0  # by construction (fp never incremented)
    current_f1 = 2 * current_precision * current_recall / (current_precision + current_recall) if (current_precision + current_recall) > 0 else 0

    # Proposal-only metrics (shared entities only, no fallback)
    proposal_recall = tp_shared / n
    proposal_precision = 1.0  # still by construction (no FP counting)
    proposal_f1 = 2 * proposal_precision * proposal_recall / (proposal_precision + proposal_recall) if (proposal_precision + proposal_recall) > 0 else 0

    # What if we counted ALL non-matching entities as FP?
    # (This is the "proper" FP accounting the scorer doesn't do)
    # For each gold, count all extracted entities that DON'T match as potential FPs
    # This is a CONSERVATIVE FP count — not all non-matching entities are wrong proposals
    total_non_matching_entities = 0
    for gold in GOLD_DISCOVERIES:
        ents_a = pipeline.extract_entities(gold["source_snippet_a"])
        ents_b = pipeline.extract_entities(gold["source_snippet_b"])
        for e in ents_a + ents_b:
            if not _bridge_matches(gold["bridge"], e.text):
                total_non_matching_entities += 1

    # Print results
    print(f"Gold discoveries: {n}")
    print(f"BRIDGE_SYNONYMS: {len(BRIDGE_SYNONYMS)} entries (empty = non-circular)")
    print()
    print(f"{'ID':<16} {'Bridge':<28} {'Locus':<10} {'Matched':<30} {'Shared':<7} {'Ents A':<7} {'Ents B'}")
    print("-" * 110)
    for g in per_gold:
        print(f"{g['id']:<16} {g['bridge']:<28} {g['locus']:<10} "
              f"{(g['matched_label'] or '-')[:30]:<30} {g['n_shared']:<7} {g['n_ents_a']:<7} {g['n_ents_b']}")

    print()
    print("=" * 80)
    print("ABLATION RESULTS")
    print("=" * 80)
    print()
    print(f"  Current scorer (with fallback):")
    print(f"    TP = {tp_total} ({tp_shared} shared + {tp_fallback} fallback)")
    print(f"    FP = 0 (by construction — never incremented)")
    print(f"    FN = {fn}")
    print(f"    Precision = {current_precision:.4f} (by construction)")
    print(f"    Recall = {current_recall:.4f}")
    print(f"    F1 = {current_f1:.4f}")
    print()
    print(f"  Proposal-only (shared entities, NO fallback):")
    print(f"    TP = {tp_shared}")
    print(f"    FP = 0 (still by construction)")
    print(f"    FN = {n - tp_shared}")
    print(f"    Precision = {proposal_precision:.4f} (still by construction)")
    print(f"    Recall = {proposal_recall:.4f}")
    print(f"    F1 = {proposal_f1:.4f}")
    print()
    print(f"  Fallback contribution: {tp_fallback} hits ({tp_fallback}/{tp_total} = {tp_fallback/max(1,tp_total)*100:.1f}% of TPs)")
    print(f"  These {tp_fallback} hits received discovery credit from AMBIENT ENTITY PRESENCE,")
    print(f"  not from the system proposing the bridge.")
    print()
    print(f"  Total non-matching extracted entities (potential FPs): {total_non_matching_entities}")
    print(f"  If these were counted as FP, precision would be:")
    if tp_total + total_non_matching_entities > 0:
        hypothetical_precision = tp_total / (tp_total + total_non_matching_entities)
        print(f"    {hypothetical_precision:.4f} (vs current 1.0000 by construction)")
        hypothetical_f1 = 2 * hypothetical_precision * current_recall / (hypothetical_precision + current_recall) if (hypothetical_precision + current_recall) > 0 else 0
        print(f"    F1 would be: {hypothetical_f1:.4f} (vs current {current_f1:.4f})")
    print()
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print(f"The proposal-locus vulnerability is REAL and MEASURED:")
    print(f"  - {tp_fallback}/{tp_total} TPs ({tp_fallback/max(1,tp_total)*100:.1f}%) come from ambient entity presence,")
    print(f"    not from the system proposing the bridge as a discovery")
    print(f"  - FP is always 0 by construction — the scorer never counts wrong proposals")
    print(f"  - Precision is always 1.0 by construction — this is NOT a measurement")
    print(f"  - The F1 of {current_f1:.4f} is inflated by both the fallback and the FP=0 construction")
    print()
    print(f"The honest F1 (proposal-only, shared entities, no fallback): {proposal_f1:.4f}")
    print(f"The current F1 (with fallback and FP=0): {current_f1:.4f}")
    print(f"The inflation from the fallback alone: {current_f1 - proposal_f1:.4f}")
    print()

    # Save report
    reports_dir = REPO / "reports"
    reports_dir.mkdir(exist_ok=True)

    report = {
        "cycle": 272,
        "type": "stage_minus_1_ablation",
        "directive": "MEASURE, DO NOT FIX",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "findings": {
            "proposal_locus_vulnerability": True,
            "fp_zero_by_construction": True,
            "fallback_hits": tp_fallback,
            "fallback_percentage_of_tps": round(tp_fallback / max(1, tp_total) * 100, 1),
            "shared_hits": tp_shared,
            "total_tps": tp_total,
            "false_negatives": fn,
            "current_f1": round(current_f1, 4),
            "proposal_only_f1": round(proposal_f1, 4),
            "f1_inflation_from_fallback": round(current_f1 - proposal_f1, 4),
            "total_non_matching_entities": total_non_matching_entities,
            "hypothetical_precision_with_fp": round(tp_total / max(1, tp_total + total_non_matching_entities), 4) if total_non_matching_entities > 0 else 1.0,
        },
        "per_gold": per_gold,
        "verdict": (
            "NOT TRUSTWORTHY for claims of independent discovery. "
            f"{tp_fallback}/{tp_total} TPs come from ambient entity presence. "
            "FP=0 by construction. Precision=1.0 by construction. "
            "The scorer does not require the system to propose the bridge."
        ),
    }
    with open(reports_dir / "stage_minus_1_ablation.json", "w") as f:
        json.dump(report, f, indent=2)

    # Markdown
    lines = []
    lines.append("# Stage −1 Ablation: Proposal-Locus Measurement")
    lines.append("")
    lines.append(f"Cycle: 272")
    lines.append(f"Directive: MEASURE, DO NOT FIX")
    lines.append(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    lines.append(f"1. **Proposal-locus vulnerability: CONFIRMED**")
    lines.append(f"   - {tp_fallback}/{tp_total} TPs ({tp_fallback/max(1,tp_total)*100:.1f}%) come from the")
    lines.append(f"     ALL-entities fallback, not from shared entities (genuine discovery)")
    lines.append(f"   - The scorer grants discovery credit when the gold bridge appears as an")
    lines.append(f"     extracted entity in either input paper — the system does not need to")
    lines.append(f"     PROPOSE the bridge")
    lines.append(f"")
    lines.append(f"2. **FP = 0 by construction: CONFIRMED**")
    lines.append(f"   - The `fp` variable is initialized to 0 and never incremented")
    lines.append(f"   - The scoring loop only does `tp += 1` or `fn += 1`")
    lines.append(f"   - Precision is always 1.0 — this is NOT a measurement, it's a tautology")
    lines.append(f"")
    lines.append(f"3. **0.9189 is NOT an FP floor: CONFIRMED**")
    lines.append(f"   - The 0.9189 in the old discovery_capability_score.json was the")
    lines.append(f"     circular-synonym F1, not an empirically established FP floor")
    lines.append(f"   - The M-008 'FP floor' in the bootstrap is a separate measurement")
    lines.append(f"     (random candidates against gold) — it was incorrectly conflated")
    lines.append(f"")
    lines.append("## Per-gold breakdown")
    lines.append("")
    lines.append("| ID | Bridge | Locus | Matched | Shared | Ents A | Ents B |")
    lines.append("|---|---|---|---|---|---|---|")
    for g in per_gold:
        lines.append(f"| {g['id']} | {g['bridge']} | {g['locus']} | {g['matched_label'] or '-'} | {g['n_shared']} | {g['n_ents_a']} | {g['n_ents_b']} |")
    lines.append("")
    lines.append("## Metrics comparison")
    lines.append("")
    lines.append("| Metric | Current (with fallback) | Proposal-only (no fallback) | Inflation |")
    lines.append("|---|---|---|---|")
    lines.append(f"| TP | {tp_total} | {tp_shared} | +{tp_fallback} |")
    lines.append(f"| Recall | {current_recall:.4f} | {proposal_recall:.4f} | +{current_recall - proposal_recall:.4f} |")
    lines.append(f"| Precision | 1.0000 (by construction) | 1.0000 (by construction) | 0 |")
    lines.append(f"| F1 | {current_f1:.4f} | {proposal_f1:.4f} | +{current_f1 - proposal_f1:.4f} |")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"**NOT TRUSTWORTHY for claims of independent discovery.**")
    lines.append(f"")
    lines.append(f"- {tp_fallback}/{tp_total} TPs come from ambient entity presence")
    lines.append(f"- FP=0 by construction (precision is a tautology, not a measurement)")
    lines.append(f"- The scorer does not require the system to propose the bridge")
    lines.append(f"- The F1 of {current_f1:.4f} is inflated by both the fallback and the FP=0 construction")
    lines.append(f"- The honest proposal-only F1 is {proposal_f1:.4f}")
    lines.append("")
    lines.append("## What NOT to do")
    lines.append("")
    lines.append("Do NOT fix the scorer yet. This ablation is the evidence. Changing")
    lines.append("the scorer before recording this measurement would destroy the")
    lines.append("audit trail.")
    lines.append("")
    with open(reports_dir / "stage_minus_1_ablation.md", "w") as f:
        f.write("\n".join(lines))

    print(f"Saved reports/stage_minus_1_ablation.json")
    print(f"Saved reports/stage_minus_1_ablation.md")
    print()
    print("=" * 80)
    print(f"VERDICT: NOT TRUSTWORTHY for claims of independent discovery")
    print(f"  {tp_fallback}/{tp_total} TPs from ambient presence, FP=0 by construction")
    print(f"  Current F1={current_f1:.4f}, Proposal-only F1={proposal_f1:.4f}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
