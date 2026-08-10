#!/usr/bin/env python3
"""verify_520_inverted.py — Independently verify the 520 "inverted" span claim.

For every span where pos[0] > pos[1] (classified as "invalid_inverted" in v2):
1. Recover the original token sequence
2. Identify returned [p0, p1]
3. Identify GLiREL's intended head span from the model output (head_text/tail_text)
4. Map both positions independently
5. Classify the inversion as:
   - MODEL_OUTPUT_INVERSION (GLiREL returned [end, start])
   - HEAD_TAIL_ORDERING_ARTIFACT (head and tail positions were swapped)
   - RELATION_DIRECTION_ARTIFACT (relation direction implies reversal)
   - TOKENIZER_INDEXING_ARTIFACT (off-by-one in a different direction)
   - ADAPTER_INTERPRETATION_ERROR (our adapter is wrong)
   - UNKNOWN

The danger: accidentally calling something a "model error" that is actually
another coordinate-system problem.
"""
import json, re, sys
from collections import Counter

def tokenize_like_glirel(text):
    tokens, starts, ends = [], [], []
    for m in re.finditer(r'\w+(?:[-_]\w+)*|\S', text):
        tokens.append(m.group()); starts.append(m.start()); ends.append(m.end())
    return tokens, starts, ends

def verify_inverted_spans(evidence_path):
    """Verify all inverted spans in the evidence graphs."""
    with open(evidence_path) as f:
        evidence = json.load(f)

    classifications = []
    category_counts = Counter()

    for case in evidence:
        for source_key, source_text in [("source_a_text", case["source_a_text"]),
                                         ("source_b_text", case["source_b_text"])]:
            tokens, tok_starts, tok_ends = tokenize_like_glirel(source_text)
            num_tokens = len(tokens)
            edges_key = "edges_a" if "a" in source_key else "edges_b"
            source_id = "A" if "a" in source_key else "B"

            for idx, rel in enumerate(case[edges_key]):
                for side in ["head", "tail"]:
                    pos = rel.get(f"{side}_pos", [])
                    text_returned = rel.get(f"{side}_text", "")
                    span_info = rel.get(f"{side}_span", {})
                    fix_method = rel.get("span_fix_methods", {}).get(side, "unknown")

                    if fix_method != "invalid_inverted":
                        continue

                    # This is one of the 520 inverted spans
                    p0, p1 = pos[0], pos[1]

                    # Check 1: Is this a head/tail swap?
                    # If head_pos == [a, b] and tail_pos == [b, a], they're swapped
                    other_side = "tail" if side == "head" else "head"
                    other_pos = rel.get(f"{other_side}_pos", [])
                    other_text = rel.get(f"{other_side}_text", "")
                    other_fix = rel.get("span_fix_methods", {}).get(other_side, "unknown")

                    is_swap = False
                    if other_pos and len(other_pos) >= 2:
                        if pos[0] == other_pos[1] and pos[1] == other_pos[0]:
                            is_swap = True
                        # Also check if positions are reversed (accounting for +1)
                        if pos[0] == other_pos[0] and pos[1] == other_pos[1] - 1:
                            is_swap = True

                    # Check 2: Can we recover the correct span by swapping?
                    # Swap [p0, p1] → [p1, p0] and try standard fix
                    swapped_pos = [p1, p0]
                    token_start = swapped_pos[0]
                    token_end = swapped_pos[1] - 1  # Reverse +1
                    swapped_text = ""
                    swapped_valid = False
                    if 0 <= token_start < num_tokens and 0 <= token_end < num_tokens and token_start <= token_end:
                        char_start = tok_starts[token_start]
                        char_end = tok_ends[token_end]
                        swapped_text = source_text[char_start:char_end]
                        swapped_valid = len(swapped_text) > 0

                    # Check 3: Can we recover by NOT reversing (treating as direct token indices)?
                    # pos = [p0, p1] where p0 > p1. Try: token_start=p1, token_end=p0-1
                    alt_token_start = p1
                    alt_token_end = p0 - 1
                    alt_text = ""
                    alt_valid = False
                    if 0 <= alt_token_start < num_tokens and 0 <= alt_token_end < num_tokens and alt_token_start <= alt_token_end:
                        char_start = tok_starts[alt_token_start]
                        char_end = tok_ends[alt_token_end]
                        alt_text = source_text[char_start:char_end]
                        alt_valid = len(alt_text) > 0

                    # Check 4: Does the returned text match any token?
                    text_matches_token = text_returned in tokens if text_returned else False

                    # Classify
                    if is_swap and swapped_valid:
                        category = "HEAD_TAIL_ORDERING_ARTIFACT"
                        reason = f"Swapped with {other_side}: pos={pos}, other={other_pos}, swapped_text='{swapped_text}'"
                    elif swapped_valid and swapped_text:
                        category = "MODEL_OUTPUT_INVERSION"
                        reason = f"Swapping [{p0},{p1}]→[{p1},{p0}] gives valid span: '{swapped_text}'"
                    elif alt_valid and alt_text:
                        category = "TOKENIZER_INDEXING_ARTIFACT"
                        reason = f"Using [{p1},{p0-1}] (no +1 reversal) gives valid span: '{alt_text}'"
                    elif text_matches_token:
                        # The returned text IS a valid token, just the positions are wrong
                        tok_idx = tokens.index(text_returned) if text_returned in tokens else -1
                        category = "MODEL_OUTPUT_INVERSION"
                        reason = f"text='{text_returned}' matches token {tok_idx}, but pos={pos} is inverted"
                    else:
                        category = "UNKNOWN"
                        reason = f"pos={pos}, text='{text_returned}', swapped='{swapped_text}', alt='{alt_text}'"

                    category_counts[category] += 1
                    classifications.append({
                        "case_id": case["case_id"],
                        "source_id": source_id,
                        "relation_idx": idx,
                        "side": side,
                        "pos": pos,
                        "text_returned": text_returned,
                        "swapped_text": swapped_text,
                        "swapped_valid": swapped_valid,
                        "alt_text": alt_text,
                        "alt_valid": alt_valid,
                        "is_head_tail_swap": is_swap,
                        "category": category,
                        "reason": reason,
                    })

    return classifications, category_counts


def main():
    evidence_path = sys.argv[1] if len(sys.argv) > 1 else "hybrid_v2/evidence_graphs_v2.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "hybrid_v2/inverted_verification.json"

    classifications, counts = verify_inverted_spans(evidence_path)

    with open(output_path, "w") as f:
        json.dump({
            "total_inverted": len(classifications),
            "category_counts": dict(counts.most_common()),
            "classifications": classifications,
        }, f, indent=2)

    print("=" * 60)
    print("INVERTED SPAN VERIFICATION")
    print("=" * 60)
    print(f"Total inverted spans: {len(classifications)}")
    print()
    print("CATEGORY BREAKDOWN:")
    for cat, count in counts.most_common():
        pct = count / len(classifications) * 100 if classifications else 0
        print(f"  {cat}: {count} ({pct:.1f}%)")
    print()

    # Check if any are recoverable
    recoverable = sum(1 for c in classifications
                     if c["category"] in ["HEAD_TAIL_ORDERING_ARTIFACT",
                                          "MODEL_OUTPUT_INVERSION",
                                          "TOKENIZER_INDEXING_ARTIFACT"])
    truly_invalid = sum(1 for c in classifications if c["category"] == "UNKNOWN")
    print(f"Recoverable by swap/alt-index: {recoverable}")
    print(f"Truly unknown: {truly_invalid}")
    print()

    # Show examples of each category
    shown = set()
    for c in classifications:
        if c["category"] not in shown:
            shown.add(c["category"])
            print(f"Example ({c['category']}):")
            print(f"  case={c['case_id']}, source={c['source_id']}, side={c['side']}")
            print(f"  pos={c['pos']}, text='{c['text_returned']}'")
            print(f"  reason: {c['reason']}")
            print()


if __name__ == "__main__":
    main()
