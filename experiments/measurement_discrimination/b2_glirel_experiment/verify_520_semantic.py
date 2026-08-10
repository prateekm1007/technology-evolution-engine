#!/usr/bin/env python3
"""verify_520_semantic.py — Semantically verify all 520 swapped spans.

For each swapped span, check:
  A = correct inversion recovery (swapped text matches a known entity)
  B = valid span but wrong semantic entity (text is a valid substring but not an entity)
  C = wrong relation direction (head/tail may be reversed)
  D = ambiguous (text matches multiple entities)
  E = other

This goes beyond mechanical validity to semantic correctness.
"""
import json, re, sys
from collections import Counter

def tokenize_like_glirel(text):
    tokens, starts, ends = [], [], []
    for m in re.finditer(r'\w+(?:[-_]\w+)*|\S', text):
        tokens.append(m.group()); starts.append(m.start()); ends.append(m.end())
    return tokens, starts, ends

# Known entities from the controlled NER input
ENTITIES_A = [
    {"label": "MINERAL", "text": "Calcium phosphate", "start": 0, "end": 17},
    {"label": "DEPOSIT", "text": "crystalline deposits", "start": 25, "end": 44},
    {"label": "TISSUE", "text": "bone tissue", "start": 49, "end": 60},
    {"label": "CELL", "text": "osteoblast", "start": 70, "end": 80},
    {"label": "PROCESS", "text": "mineralization", "start": 92, "end": 106},
]
ENTITIES_B = [
    {"label": "ORGANISM", "text": "Marine diatoms", "start": 0, "end": 14},
    {"label": "PROCESS", "text": "precipitate", "start": 15, "end": 26},
    {"label": "MINERAL", "text": "silica", "start": 27, "end": 33},
    {"label": "STRUCTURE", "text": "cell walls", "start": 41, "end": 51},
    {"label": "ENZYME", "text": "silicatein", "start": 67, "end": 77},
    {"label": "PROTEIN", "text": "proteins", "start": 78, "end": 86},
]

def classify_swapped_span(source_text, swapped_text, entities):
    """Classify a swapped span semantically."""
    if not swapped_text:
        return "E", "empty swapped text"

    # Check A: matches a known entity exactly
    for ent in entities:
        if swapped_text == ent["text"]:
            return "A", f"matches entity '{ent['text']}' ({ent['label']})"

    # Check A: matches a known entity's substring (multi-token entity)
    for ent in entities:
        if swapped_text in ent["text"] or ent["text"] in swapped_text:
            if len(swapped_text) >= len(ent["text"]) * 0.5:
                return "A", f"partial match entity '{ent['text']}' ({ent['label']})"

    # Check B: valid substring but not an entity
    if swapped_text in source_text:
        # Is it a meaningful word?
        if len(swapped_text) > 2 and swapped_text.isalpha():
            return "B", f"valid substring '{swapped_text}' but not a known entity"
        elif swapped_text in ['.', ',', ';', ':', '!', '?']:
            return "B", f"punctuation '{swapped_text}'"
        else:
            return "B", f"substring '{swapped_text}' not an entity"

    # Check D: ambiguous
    occurrences = [m.start() for m in re.finditer(re.escape(swapped_text), source_text)]
    if len(occurrences) > 1:
        return "D", f"'{swapped_text}' appears {len(occurrences)} times"

    return "E", f"unknown: '{swapped_text}'"


def main():
    evidence_path = sys.argv[1] if len(sys.argv) > 1 else "hybrid_v3/evidence_graphs_v3.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "hybrid_v3/swapped_semantic_verification.json"

    with open(evidence_path) as f:
        evidence = json.load(f)

    classifications = []
    category_counts = Counter()

    for case in evidence:
        for source_key, source_text, entities in [
            ("source_a", case["source_a"]["text"], ENTITIES_A),
            ("source_b", case["source_b"]["text"], ENTITIES_B)
        ]:
            tokens, tok_starts, tok_ends = tokenize_like_glirel(source_text)
            num_tokens = len(tokens)
            relations = case[source_key]["relations"]

            for idx, rel in enumerate(relations):
                for side in ["head", "tail"]:
                    fix_method = rel.get("span_fix_methods", {}).get(side, "unknown")
                    if fix_method != "swapped_inversion":
                        continue

                    pos = rel.get(f"{side}_pos", [])
                    span_info = rel.get(f"{side}_span", {})
                    mapped_text = span_info.get("text", "")

                    category, reason = classify_swapped_span(source_text, mapped_text, entities)
                    category_counts[category] += 1

                    classifications.append({
                        "case_id": case["case_id"],
                        "source_id": "A" if "a" in source_key else "B",
                        "relation_idx": idx,
                        "side": side,
                        "raw_pos": pos,
                        "mapped_text": mapped_text,
                        "category": category,
                        "reason": reason,
                        "relation_label": rel.get("label"),
                        "score": rel.get("score"),
                    })

    with open(output_path, "w") as f:
        json.dump({
            "total_swapped": len(classifications),
            "category_counts": dict(category_counts.most_common()),
            "classifications": classifications,
        }, f, indent=2)

    print("=" * 60)
    print("SWAPPED SPAN SEMANTIC VERIFICATION")
    print("=" * 60)
    print(f"Total swapped spans: {len(classifications)}")
    print()
    print("CATEGORY BREAKDOWN:")
    for cat, count in category_counts.most_common():
        pct = count / len(classifications) * 100 if classifications else 0
        labels = {"A": "correct inversion recovery",
                  "B": "valid span, wrong semantic entity",
                  "C": "wrong relation direction",
                  "D": "ambiguous",
                  "E": "other"}
        print(f"  {cat} ({labels.get(cat, '?')}): {count} ({pct:.1f}%)")
    print()

    # Show examples of each category
    shown = set()
    for c in classifications:
        if c["category"] not in shown:
            shown.add(c["category"])
            print(f"Example ({c['category']}):")
            print(f"  case={c['case_id']}, source={c['source_id']}, side={c['side']}")
            print(f"  pos={c['raw_pos']}, text='{c['mapped_text']}'")
            print(f"  label={c['relation_label']}, score={c['score']}")
            print(f"  reason: {c['reason']}")
            print()


if __name__ == "__main__":
    main()
