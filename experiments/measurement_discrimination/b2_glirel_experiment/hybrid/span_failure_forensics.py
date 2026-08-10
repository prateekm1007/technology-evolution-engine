#!/usr/bin/env python3
"""span_failure_forensics.py — Classify all invalid GLiREL spans into failure categories.

Takes evidence_graphs.json from Phase 1 and produces:
  - diagnostics/span_failure_taxonomy.json
  - diagnostics/span_failure_summary.json

Categories (mutually exclusive):
  TOKEN_TO_CHAR_MAPPING_ERROR — GLiREL used token pos as char pos
  OFF_BY_ONE — +1 adjustment causes boundary error
  INCLUSIVE_EXCLUSIVE_ERROR — inclusive/exclusive end boundary mismatch
  SUBWORD_BOUNDARY — tokenizer split entity across subwords
  PUNCTUATION_BOUNDARY — punctuation attached/detached differently
  HYPHEN_BOUNDARY — hyphenated term split differently
  UNDERSCORE_BOUNDARY — underscore term split differently
  NORMALIZATION_MISMATCH — text was normalized (case, whitespace)
  MULTIPLE_OCCURRENCE_AMBIGUITY — entity text appears multiple times
  GLiREL_OUTPUT_POSITION_ERROR — GLiREL returned wrong position entirely
  WRONG_ENTITY_TEXT — GLiREL returned text that doesn't match any entity
  WRONG_SOURCE_MAPPING — position maps to wrong source
  UNKNOWN — cannot classify
"""
import json, re, os, sys
from collections import Counter, defaultdict

def tokenize_like_glirel(text):
    tokens, starts, ends = [], [], []
    for m in re.finditer(r'\w+(?:[-_]\w+)*|\S', text):
        tokens.append(m.group())
        starts.append(m.start())
        ends.append(m.end())
    return tokens, starts, ends

def classify_span_failure(source_text, glirel_pos, glirel_text, fixed_span):
    """Classify a single invalid span into a failure category."""
    if not glirel_pos or len(glirel_pos) < 2:
        return "GLiREL_OUTPUT_POSITION_ERROR", "No position data"

    token_start = glirel_pos[0]
    token_end_adjusted = glirel_pos[1] - 1  # Reverse +1

    tokens, tok_starts, tok_ends = tokenize_like_glirel(source_text)
    num_tokens = len(tokens)

    # Check if positions are out of token range
    if token_start >= num_tokens or token_end_adjusted >= num_tokens or token_start < 0:
        # Check if it's an off-by-one at the boundary
        if token_end_adjusted == num_tokens:
            return "OFF_BY_ONE", f"token_end={token_end_adjusted} == num_tokens={num_tokens}"
        if token_end_adjusted > num_tokens:
            return "OFF_BY_ONE", f"token_end={token_end_adjusted} > num_tokens={num_tokens}"
        return "GLiREL_OUTPUT_POSITION_ERROR", f"pos [{token_start},{token_end_adjusted}] out of range [0,{num_tokens-1}]"

    if token_start > token_end_adjusted:
        return "INCLUSIVE_EXCLUSIVE_ERROR", f"start={token_start} > end={token_end_adjusted}"

    # Get what the CORRECT text should be
    correct_start = tok_starts[token_start]
    correct_end = tok_ends[token_end_adjusted]
    correct_text = source_text[correct_start:correct_end]

    # Get what GLiREL's original (buggy) extraction would produce
    # GLiREL does: text[head_pos[0]:head_pos[1]+1]  (but +1 already applied in output)
    # Actually GLiREL does: text[head_pos[0]:head_pos[1]] where head_pos[1] already has +1
    # So the buggy extraction is: text[glirel_pos[0]:glirel_pos[1]]
    glirel_extracted = source_text[glirel_pos[0]:glirel_pos[1]] if glirel_pos[1] <= len(source_text) else ""

    # Compare
    if glirel_text == correct_text:
        # Fixed span matches — this shouldn't be invalid unless our fix is wrong
        return "NORMALIZATION_MISMATCH", f"fixed matches but marked invalid"

    if glirel_extracted == glirel_text:
        # GLiREL extracted what it says it extracted — the issue is the position mapping
        return "TOKEN_TO_CHAR_MAPPING_ERROR", f"GLiREL used char idx [{glirel_pos[0]}:{glirel_pos[1]}]='{glirel_extracted}' but correct is token [{token_start}:{token_end_adjusted}]='{correct_text}'"

    # Check if it's a punctuation boundary issue
    if glirel_text.rstrip('.,;:!?') == correct_text.rstrip('.,;:!?'):
        return "PUNCTUATION_BOUNDARY", f"GLiREL='{glirel_text}' vs correct='{correct_text}'"

    # Check hyphen
    if '-' in glirel_text or '-' in correct_text:
        if glirel_text.replace('-','') == correct_text.replace('-',''):
            return "HYPHEN_BOUNDARY", f"GLiREL='{glirel_text}' vs correct='{correct_text}'"

    # Check underscore
    if '_' in glirel_text or '_' in correct_text:
        if glirel_text.replace('_','') == correct_text.replace('_',''):
            return "UNDERSCORE_BOUNDARY", f"GLiREL='{glirel_text}' vs correct='{correct_text}'"

    # Check if it's a subword issue
    if len(glirel_text) < len(correct_text) and correct_text.startswith(glirel_text):
        return "SUBWORD_BOUNDARY", f"GLiREL='{glirel_text}' is prefix of correct='{correct_text}'"
    if len(glirel_text) > len(correct_text) and glirel_text.startswith(correct_text):
        return "SUBWORD_BOUNDARY", f"GLiREL='{glirel_text}' extends correct='{correct_text}'"

    # Check normalization (case/whitespace)
    if glirel_text.lower().strip() == correct_text.lower().strip():
        return "NORMALIZATION_MISMATCH", f"case/whitespace: GLiREL='{glirel_text}' vs correct='{correct_text}'"

    # Check multiple occurrence
    occurrences = [m.start() for m in re.finditer(re.escape(glirel_text), source_text)]
    if len(occurrences) > 1:
        return "MULTIPLE_OCCURRENCE_AMBIGUITY", f"'{glirel_text}' appears {len(occurrences)} times"

    # Check if the text exists anywhere in source
    if glirel_text not in source_text and correct_text not in glirel_text:
        return "WRONG_ENTITY_TEXT", f"GLiREL='{glirel_text}' not in source; correct='{correct_text}'"

    return "UNKNOWN", f"GLiREL='{glirel_text}' vs correct='{correct_text}' (pos={glirel_pos})"


def main():
    evidence_path = sys.argv[1] if len(sys.argv) > 1 else "results/glirel/evidence_graphs.json"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "diagnostics"

    with open(evidence_path) as f:
        evidence = json.load(f)

    failures = []
    head_valid = 0
    head_invalid = 0
    tail_valid = 0
    tail_invalid = 0
    both_valid = 0
    both_invalid = 0
    total_relations = 0
    category_counts = Counter()

    for case in evidence:
        source_a = case["source_a_text"]
        source_b = case["source_b_text"]
        case_id = case["case_id"]

        for source_id, edges, source_text in [("A", case["edges_a"], source_a), ("B", case["edges_b"], source_b)]:
            for idx, rel in enumerate(edges):
                total_relations += 1

                head_span = rel.get("head_span", {})
                tail_span = rel.get("tail_span", {})
                head_valid_flag = head_span.get("valid", False)
                tail_valid_flag = tail_span.get("valid", False)

                if head_valid_flag:
                    head_valid += 1
                else:
                    head_invalid += 1
                    cat, reason = classify_span_failure(
                        source_text, rel.get("head_pos", []),
                        rel.get("head_text", ""), head_span
                    )
                    category_counts[cat] += 1
                    failures.append({
                        "case_id": case_id,
                        "source_id": source_id,
                        "relation_id": f"{case_id}-{source_id}-{idx}",
                        "side": "head",
                        "raw_glirel_output": {
                            "head_pos": rel.get("head_pos"),
                            "head_text": rel.get("head_text"),
                            "label": rel.get("label"),
                            "score": rel.get("score"),
                        },
                        "expected_text": head_span.get("text", ""),
                        "mapped_text": rel.get("head_text", ""),
                        "failure_category": cat,
                        "failure_reason": reason,
                        "source_excerpt": source_text[:100] + "...",
                    })

                if tail_valid_flag:
                    tail_valid += 1
                else:
                    tail_invalid += 1
                    cat, reason = classify_span_failure(
                        source_text, rel.get("tail_pos", []),
                        rel.get("tail_text", ""), tail_span
                    )
                    category_counts[cat] += 1
                    failures.append({
                        "case_id": case_id,
                        "source_id": source_id,
                        "relation_id": f"{case_id}-{source_id}-{idx}",
                        "side": "tail",
                        "raw_glirel_output": {
                            "tail_pos": rel.get("tail_pos"),
                            "tail_text": rel.get("tail_text"),
                            "label": rel.get("label"),
                            "score": rel.get("score"),
                        },
                        "expected_text": tail_span.get("text", ""),
                        "mapped_text": rel.get("tail_text", ""),
                        "failure_category": cat,
                        "failure_reason": reason,
                        "source_excerpt": source_text[:100] + "...",
                    })

                if head_valid_flag and tail_valid_flag:
                    both_valid += 1
                else:
                    both_invalid += 1

    # Summary
    summary = {
        "total_relations": total_relations,
        "head_span_fidelity": {
            "valid": head_valid,
            "invalid": head_invalid,
            "total": head_valid + head_invalid,
            "pct": round(head_valid / (head_valid + head_invalid) * 100, 1) if (head_valid + head_invalid) > 0 else 0,
        },
        "tail_span_fidelity": {
            "valid": tail_valid,
            "invalid": tail_invalid,
            "total": tail_valid + tail_invalid,
            "pct": round(tail_valid / (tail_valid + tail_invalid) * 100, 1) if (tail_valid + tail_invalid) > 0 else 0,
        },
        "both_span_fidelity": {
            "valid": both_valid,
            "invalid": both_invalid,
            "total": both_valid + both_invalid,
            "pct": round(both_valid / (both_valid + both_invalid) * 100, 1) if (both_valid + both_invalid) > 0 else 0,
        },
        "failure_categories": dict(category_counts.most_common()),
        "total_invalid_spans": len(failures),
    }

    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "span_failure_taxonomy.json"), "w") as f:
        json.dump(failures, f, indent=2)

    with open(os.path.join(output_dir, "span_failure_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print("=" * 60)
    print("SPAN FAILURE FORENSIC ANALYSIS")
    print("=" * 60)
    print(f"Total relations: {total_relations}")
    print()
    print("HEAD SPAN FIDELITY:")
    print(f"  Valid: {head_valid} ({summary['head_span_fidelity']['pct']}%)")
    print(f"  Invalid: {head_invalid}")
    print()
    print("TAIL SPAN FIDELITY:")
    print(f"  Valid: {tail_valid} ({summary['tail_span_fidelity']['pct']}%)")
    print(f"  Invalid: {tail_invalid}")
    print()
    print("BOTH SPANS FIDELITY:")
    print(f"  Valid: {both_valid} ({summary['both_span_fidelity']['pct']}%)")
    print(f"  Invalid: {both_invalid}")
    print()
    print("FAILURE CATEGORY BREAKDOWN:")
    for cat, count in category_counts.most_common():
        pct = count / len(failures) * 100 if failures else 0
        print(f"  {cat}: {count} ({pct:.1f}%)")
    print()
    print(f"Total invalid spans classified: {len(failures)}")
    print(f"Taxonomy saved: {output_dir}/span_failure_taxonomy.json")
    print(f"Summary saved: {output_dir}/span_failure_summary.json")


if __name__ == "__main__":
    main()
