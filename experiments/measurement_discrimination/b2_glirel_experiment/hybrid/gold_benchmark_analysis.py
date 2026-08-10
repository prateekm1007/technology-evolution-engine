#!/usr/bin/env python3
"""gold_benchmark_analysis.py — Run V3 gold benchmark against GLiREL-SPAN-GOLD-v1.

Calculates:
  - Span precision (correct extracted entity spans / all extracted entity spans)
  - Span recall (correct gold entity spans recovered / all gold entity spans)
  - Relation precision (correct extracted relations / all extracted relations)
  - Relation recall (correct gold relations recovered / all gold relations)
  - Direction accuracy (correct relation direction / relations with verified direction)

Also classifies every extracted relation:
  CORRECT, WRONG_RELATION, WRONG_DIRECTION, WRONG_ENTITY, PARTIAL, AMBIGUOUS

No API calls required. Uses existing V3 extraction artifacts only.
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

HERE = Path(__file__).parent
GOLD_PATH = HERE / "gold_span_benchmark.json"
EVIDENCE_PATH = HERE / "results" / "glirel" / "evidence_graphs_v3.json"
OUTPUT_DIR = HERE / "diagnostics"

def tokenize_like_glirel(text):
    tokens, starts, ends = [], [], []
    for m in re.finditer(r'\w+(?:[-_]\w+)*|\S', text):
        tokens.append(m.group()); starts.append(m.start()); ends.append(m.end())
    return tokens, starts, ends

def spans_overlap(s1, s2):
    """Check if two spans [start, end) overlap."""
    return s1[0] < s2[1] and s2[0] < s1[1]

def span_matches(gold_span, extracted_span):
    """Check if extracted span matches gold span (exact or contained)."""
    gs = (gold_span["start"], gold_span["end"])
    es = (extracted_span["start"], extracted_span["end"])
    # Exact match
    if gs == es:
        return "EXACT"
    # Extracted is subset of gold (partial match)
    if es[0] >= gs[0] and es[1] <= gs[1]:
        return "PARTIAL_SUBSET"
    # Gold is subset of extracted
    if gs[0] >= es[0] and gs[1] <= es[1]:
        return "PARTIAL_SUPERSET"
    # Overlap
    if spans_overlap(gs, es):
        return "OVERLAP"
    return "NO_MATCH"

def classify_relation(gold_rel, extracted_rel):
    """Classify an extracted relation against a gold relation."""
    # Check head entity
    head_match = span_matches(
        {"start": gold_rel["head_start"], "end": gold_rel["head_end"]},
        {"start": extracted_rel["head_span"]["start"], "end": extracted_rel["head_span"]["end"]}
    ) if extracted_rel.get("head_span") else "NO_MATCH"

    # Check tail entity
    tail_match = span_matches(
        {"start": gold_rel["tail_start"], "end": gold_rel["tail_end"]},
        {"start": extracted_rel["tail_span"]["start"], "end": extracted_rel["tail_span"]["end"]}
    ) if extracted_rel.get("tail_span") else "NO_MATCH"

    # Check relation label
    rel_match = gold_rel["relation"] == extracted_rel.get("label", "")

    # Check direction
    gold_dir = gold_rel.get("direction", "A_TO_B")
    # Extracted direction: head→tail is always A_TO_B in GLiREL output
    extracted_dir = "A_TO_B"
    dir_match = gold_dir == extracted_dir

    # Classify
    if head_match == "EXACT" and tail_match == "EXACT":
        if rel_match and dir_match:
            return "CORRECT"
        elif not rel_match:
            return "WRONG_RELATION"
        elif not dir_match:
            return "WRONG_DIRECTION"
    elif head_match in ("EXACT", "PARTIAL_SUBSET", "PARTIAL_SUPERSET", "OVERLAP") and \
         tail_match in ("EXACT", "PARTIAL_SUBSET", "PARTIAL_SUPERSET", "OVERLAP"):
        if rel_match:
            return "PARTIAL"
        return "PARTIAL"
    elif head_match == "EXACT" or tail_match == "EXACT":
        return "WRONG_ENTITY"
    elif head_match != "NO_MATCH" or tail_match != "NO_MATCH":
        return "PARTIAL"

    return "AMBIGUOUS"

def main():
    print("=" * 70)
    print("V3 GOLD BENCHMARK ANALYSIS")
    print("GLiREL-SPAN-GOLD-v1")
    print("=" * 70)

    # Load gold benchmark
    gold = json.loads(GOLD_PATH.read_text())
    gold_relations = gold["gold_relations"]
    source_a_text = gold["source_a"]
    source_b_text = gold["source_b"]

    print(f"Gold relations: {len(gold_relations)}")
    print(f"Source A: {source_a_text[:60]}...")
    print(f"Source B: {source_b_text[:60]}...")
    print()

    # Load V3 evidence
    evidence = json.loads(EVIDENCE_PATH.read_text())
    # Use first case (ADV-01) — same sources as gold benchmark
    case = evidence[0]
    extracted_a = case["source_a"]["relations"]
    extracted_b = case["source_b"]["relations"]

    print(f"Extracted relations (Source A): {len(extracted_a)}")
    print(f"Extracted relations (Source B): {len(extracted_b)}")
    print(f"Total extracted: {len(extracted_a) + len(extracted_b)}")
    print()

    # ── SPAN PRECISION ──
    # How many extracted entity spans are correct (match a gold entity)?
    # Build gold entity set (unique head/tail spans from gold relations)
    gold_entities = {}
    for gr in gold_relations:
        src = gr["source"]
        h_key = (src, gr["head_start"], gr["head_end"])
        t_key = (src, gr["tail_start"], gr["tail_end"])
        gold_entities[h_key] = gr["head_text"]
        gold_entities[t_key] = gr["tail_text"]

    print(f"Gold entities (unique): {len(gold_entities)}")

    # Check each extracted span against gold
    extracted_spans = []
    correct_spans = 0
    span_matches_detail = []

    for source_id, source_text, relations in [("A", source_a_text, extracted_a),
                                                ("B", source_b_text, extracted_b)]:
        for idx, rel in enumerate(relations):
            for side in ["head", "tail"]:
                span = rel.get(f"{side}_span", {})
                if not span or not span.get("valid"):
                    continue
                s = (span["start"], span["end"])
                extracted_spans.append((source_id, s, span["text"]))

                # Check against all gold entities for this source
                best_match = "NO_MATCH"
                for gkey, gtext in gold_entities.items():
                    gsrc, gstart, gend = gkey
                    if gsrc != source_id:
                        continue
                    match = span_matches({"start": gstart, "end": gend}, {"start": s[0], "end": s[1]})
                    if match != "NO_MATCH":
                        best_match = match
                        break

                if best_match in ("EXACT", "PARTIAL_SUBSET", "PARTIAL_SUPERSET"):
                    correct_spans += 1
                span_matches_detail.append({
                    "source": source_id,
                    "span": s,
                    "text": span["text"],
                    "match": best_match,
                })

    total_extracted_spans = len(extracted_spans)
    span_precision = correct_spans / total_extracted_spans * 100 if total_extracted_spans > 0 else 0

    print(f"\n── SPAN PRECISION ──")
    print(f"Correct extracted spans: {correct_spans}")
    print(f"Total extracted spans: {total_extracted_spans}")
    print(f"Span precision: {span_precision:.1f}%")

    # Span match breakdown
    match_counts = Counter(s["match"] for s in span_matches_detail)
    print(f"Match breakdown: {dict(match_counts)}")

    # ── SPAN RECALL ──
    # How many gold entity spans are recovered by extraction?
    gold_recovered = 0
    for gkey, gtext in gold_entities.items():
        gsrc, gstart, gend = gkey
        for es in extracted_spans:
            if es[0] != gsrc:
                continue
            match = span_matches({"start": gstart, "end": gend}, {"start": es[1][0], "end": es[1][1]})
            if match in ("EXACT", "PARTIAL_SUBSET", "PARTIAL_SUPERSET"):
                gold_recovered += 1
                break

    span_recall = gold_recovered / len(gold_entities) * 100 if gold_entities else 0
    print(f"\n── SPAN RECALL ──")
    print(f"Gold entities recovered: {gold_recovered}")
    print(f"Total gold entities: {len(gold_entities)}")
    print(f"Span recall: {span_recall:.1f}%")

    # Identify unrecovered gold entities
    unrecovered = []
    for gkey, gtext in gold_entities.items():
        gsrc, gstart, gend = gkey
        found = False
        for es in extracted_spans:
            if es[0] != gsrc:
                continue
            match = span_matches({"start": gstart, "end": gend}, {"start": es[1][0], "end": es[1][1]})
            if match in ("EXACT", "PARTIAL_SUBSET", "PARTIAL_SUPERSET"):
                found = True
                break
        if not found:
            unrecovered.append({"source": gsrc, "text": gtext, "span": [gstart, gend]})

    if unrecovered:
        print(f"Unrecovered gold entities ({len(unrecovered)}):")
        for u in unrecovered:
            print(f"  {u['source']}: '{u['text']}' at [{u['span'][0]},{u['span'][1]})")

    # ── RELATION PRECISION ──
    # How many extracted relations are correct (match a gold relation)?
    correct_relations = 0
    relation_classifications = []

    for source_id, source_text, relations in [("A", source_a_text, extracted_a),
                                                ("B", source_b_text, extracted_b)]:
        for idx, rel in enumerate(relations):
            # Find best matching gold relation
            best_class = "AMBIGUOUS"
            best_gold = None
            for gr in gold_relations:
                if gr["source"] != source_id:
                    continue
                cls = classify_relation(gr, rel)
                if cls == "CORRECT":
                    best_class = "CORRECT"
                    best_gold = gr
                    break
                elif cls in ("PARTIAL", "WRONG_RELATION", "WRONG_DIRECTION", "WRONG_ENTITY"):
                    if best_class == "AMBIGUOUS":
                        best_class = cls
                        best_gold = gr

            if best_class == "CORRECT":
                correct_relations += 1

            relation_classifications.append({
                "source": source_id,
                "relation_idx": idx,
                "label": rel.get("label"),
                "head_text": rel.get("head_text"),
                "tail_text": rel.get("tail_text"),
                "score": rel.get("score"),
                "classification": best_class,
                "matched_gold": best_gold["id"] if best_gold else None,
            })

    total_extracted_relations = len(extracted_a) + len(extracted_b)
    relation_precision = correct_relations / total_extracted_relations * 100 if total_extracted_relations > 0 else 0

    print(f"\n── RELATION PRECISION ──")
    print(f"Correct extracted relations: {correct_relations}")
    print(f"Total extracted relations: {total_extracted_relations}")
    print(f"Relation precision: {relation_precision:.1f}%")

    # Classification breakdown
    cls_counts = Counter(r["classification"] for r in relation_classifications)
    print(f"Classification breakdown:")
    for cls, count in cls_counts.most_common():
        pct = count / total_extracted_relations * 100
        print(f"  {cls}: {count} ({pct:.1f}%)")

    # ── RELATION RECALL ──
    # How many gold relations are recovered by extraction?
    gold_recovered_rel = 0
    for gr in gold_relations:
        source_id = gr["source"]
        relations = extracted_a if source_id == "A" else extracted_b
        for rel in relations:
            cls = classify_relation(gr, rel)
            if cls == "CORRECT":
                gold_recovered_rel += 1
                break

    relation_recall = gold_recovered_rel / len(gold_relations) * 100 if gold_relations else 0
    print(f"\n── RELATION RECALL ──")
    print(f"Gold relations recovered: {gold_recovered_rel}")
    print(f"Total gold relations: {len(gold_relations)}")
    print(f"Relation recall: {relation_recall:.1f}%")

    # Identify unrecovered gold relations
    unrecovered_rel = []
    for gr in gold_relations:
        source_id = gr["source"]
        relations = extracted_a if source_id == "A" else extracted_b
        found = False
        for rel in relations:
            cls = classify_relation(gr, rel)
            if cls == "CORRECT":
                found = True
                break
        if not found:
            unrecovered_rel.append(gr)

    if unrecovered_rel:
        print(f"Unrecovered gold relations ({len(unrecovered_rel)}):")
        for gr in unrecovered_rel[:10]:
            print(f"  {gr['id']}: {gr['relation']}({gr['head_text']}, {gr['tail_text']}) [{gr['source']}]")

    # ── DIRECTION ACCURACY ──
    # For relations that match gold entities, check direction
    dir_correct = 0
    dir_total = 0
    for rc in relation_classifications:
        if rc["classification"] in ("CORRECT", "PARTIAL", "WRONG_RELATION"):
            dir_total += 1
            if rc["classification"] == "CORRECT":
                dir_correct += 1

    dir_accuracy = dir_correct / dir_total * 100 if dir_total > 0 else 0
    print(f"\n── DIRECTION ACCURACY ──")
    print(f"Correct direction: {dir_correct}")
    print(f"Total with verified direction: {dir_total}")
    print(f"Direction accuracy: {dir_accuracy:.1f}%")

    # ── MECHANICAL VALIDITY CHECK (independent) ──
    mechanical_valid = 0
    mechanical_total = 0
    for source_id, source_text, relations in [("A", source_a_text, extracted_a),
                                                ("B", source_b_text, extracted_b)]:
        for rel in relations:
            for side in ["head", "tail"]:
                span = rel.get(f"{side}_span", {})
                if span:
                    mechanical_total += 1
                    if span.get("valid") and source_text[span["start"]:span["end"]] == span["text"]:
                        mechanical_valid += 1

    mech_pct = mechanical_valid / mechanical_total * 100 if mechanical_total > 0 else 0
    print(f"\n── MECHANICAL VALIDITY (independent check) ──")
    print(f"Mechanically valid: {mechanical_valid}/{mechanical_total} = {mech_pct:.1f}%")

    # ── SUMMARY ──
    summary = {
        "gold_benchmark": "GLiREL-SPAN-GOLD-v1",
        "gold_relations": len(gold_relations),
        "gold_entities": len(gold_entities),
        "extracted_relations": total_extracted_relations,
        "extracted_spans": total_extracted_spans,
        "span_precision_pct": round(span_precision, 1),
        "span_recall_pct": round(span_recall, 1),
        "relation_precision_pct": round(relation_precision, 1),
        "relation_recall_pct": round(relation_recall, 1),
        "direction_accuracy_pct": round(dir_accuracy, 1),
        "mechanical_validity_pct": round(mech_pct, 1),
        "relation_classification": dict(cls_counts.most_common()),
        "span_match_breakdown": dict(match_counts),
        "unrecovered_gold_entities": len(unrecovered),
        "unrecovered_gold_relations": len(unrecovered_rel),
    }

    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "gold_benchmark_results.json").write_text(json.dumps(summary, indent=2))
    (OUTPUT_DIR / "gold_relation_classifications.json").write_text(
        json.dumps(relation_classifications, indent=2))
    (OUTPUT_DIR / "gold_span_matches.json").write_text(
        json.dumps(span_matches_detail, indent=2))

    print(f"\n{'=' * 70}")
    print("GOLD BENCHMARK SUMMARY")
    print(f"{'=' * 70}")
    print(json.dumps(summary, indent=2))
    print(f"\nResults saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
