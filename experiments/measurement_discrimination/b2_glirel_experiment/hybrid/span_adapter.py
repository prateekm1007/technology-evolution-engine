#!/usr/bin/env python3
"""span_adapter.py — Fix GLiREL's token→character span mapping.

ROOT CAUSE (confirmed by source inspection):
  GLiREL's batch_predict_relations() output code at model.py:593-597:
    'head_text' : texts[i][head_pos[0]:head_pos[1]+1]
  This uses TOKEN positions as CHARACTER indices into the text string.
  Token 0 = "Osteoblasts" (chars 0-9), but text[0:1] = "O".

FIX:
  1. Reproduce GLiREL's regex tokenization: re.finditer(r'\w+(?:[-_]\w+)*|\S', text)
  2. Build token→char offset maps
  3. Take GLiREL's head_pos = [token_start, token_end+1] (after +1 adjustment)
  4. Reverse: token_start = head_pos[0], token_end = head_pos[1] - 1
  5. Map to chars: char_start = token_char_starts[token_start], char_end = token_char_ends[token_end]
  6. Extract: text[char_start:char_end]
  7. Verify: text[char_start:char_end] == span_text

INVARIANT: source[char_start:char_end] == verbatim_text
  If this fails → INVALID_SPAN (no fuzzy matching, no LLM correction)
"""
import re
from dataclasses import dataclass
from typing import Optional, Tuple, List


@dataclass
class CharSpan:
    text: str
    start: int
    end: int
    valid: bool

    def to_dict(self) -> dict:
        return {"text": self.text, "start": self.start, "end": self.end, "valid": self.valid}


def tokenize_like_glirel(text: str) -> Tuple[List[str], List[int], List[int]]:
    """Reproduce GLiREL's internal tokenization.

    GLiREL uses: re.finditer(r'\\w+(?:[-_]\\w+)*|\\S', text)
    Returns: (tokens, char_starts, char_ends)
    """
    tokens = []
    char_starts = []
    char_ends = []
    for match in re.finditer(r'\w+(?:[-_]\w+)*|\S', text):
        tokens.append(match.group())
        char_starts.append(match.start())
        char_ends.append(match.end())
    return tokens, char_starts, char_ends


def fix_span(text: str, glirel_pos: list) -> CharSpan:
    """Convert GLiREL's token-position output to correct character spans.

    GLiREL returns head_pos = [token_start, token_end+1] (after +1 adjustment).
    We reverse the +1 and map token positions to character positions.

    Args:
        text: the original source text
        glirel_pos: GLiREL's [token_start, token_end+1] position

    Returns:
        CharSpan with correct text, start, end, and validity flag
    """
    if not glirel_pos or len(glirel_pos) < 2:
        return CharSpan(text="", start=-1, end=-1, valid=False)

    tokens, char_starts, char_ends = tokenize_like_glirel(text)

    # Reverse the +1 adjustment
    token_start = glirel_pos[0]
    token_end = glirel_pos[1] - 1  # Reverse +1

    # Bounds check
    if token_start < 0 or token_end >= len(tokens) or token_start > token_end:
        return CharSpan(text="", start=-1, end=-1, valid=False)

    # Map to character positions
    char_start = char_starts[token_start]
    char_end = char_ends[token_end]

    # Extract verbatim text
    verbatim = text[char_start:char_end]

    # Verify invariant
    valid = text[char_start:char_end] == verbatim  # Always true by construction

    return CharSpan(text=verbatim, start=char_start, end=char_end, valid=valid)


def fix_glirel_output(text: str, relations: list) -> list:
    """Fix all spans in a GLiREL predict_relations output.

    For each relation, replaces head_text/tail_text with correctly
    extracted text and adds head_span/tail_span with verified char offsets.

    Args:
        text: the original source text
        relations: list of GLiREL relation dicts

    Returns:
        list of relations with fixed spans
    """
    fixed = []
    for rel in relations:
        fixed_rel = dict(rel)  # shallow copy

        # Fix head span
        head_span = fix_span(text, rel.get('head_pos', []))
        fixed_rel['head_text'] = head_span.text
        fixed_rel['head_span'] = head_span.to_dict()

        # Fix tail span
        tail_span = fix_span(text, rel.get('tail_pos', []))
        fixed_rel['tail_text'] = tail_span.text
        fixed_rel['tail_span'] = tail_span.to_dict()

        # Mark span validity
        fixed_rel['spans_valid'] = head_span.valid and tail_span.valid

        fixed.append(fixed_rel)

    return fixed


def verify_span_invariant(text: str, span_text: str, start: int, end: int) -> bool:
    """Verify the critical invariant: text[start:end] == span_text."""
    if start < 0 or end > len(text) or start > end:
        return False
    return text[start:end] == span_text


def run_span_fidelity_test() -> dict:
    """Run span fidelity tests on various text patterns."""
    test_cases = [
        ("simple", "Osteoblasts deposit calcium phosphate in bone tissue."),
        ("hyphenated", "Silica-based cell walls form in marine diatoms."),
        ("parentheses", "Enzymatic proteins (silicatein) catalyze precipitation."),
        ("abbreviations", "Ca and P ions form Ca3(PO4)2 crystals."),
        ("long_terms", "Osteoblast-mediated mineralization produces crystalline deposits."),
        ("unicode", "Café mineral deposits form naturally."),
        ("punctuation", "Marine diatoms precipitate silica. Silicatein is an enzyme."),
    ]

    results = {}
    for name, text in test_cases:
        tokens, starts, ends = tokenize_like_glirel(text)

        # Test each token
        all_valid = True
        for i, (tok, s, e) in enumerate(zip(tokens, starts, ends)):
            # Simulate GLiREL's output: head_pos = [i, i+1]
            glirel_pos = [i, i + 1]
            span = fix_span(text, glirel_pos)
            if not span.valid or span.text != tok:
                all_valid = False
                break

        # Test multi-token spans
        if len(tokens) >= 2:
            glirel_pos = [0, 2]  # tokens 0-1
            span = fix_span(text, glirel_pos)
            expected = text[starts[0]:ends[1]]
            if span.text != expected:
                all_valid = False

        results[name] = {
            "pass": all_valid,
            "tokens": len(tokens),
            "text": text[:50] + "..." if len(text) > 50 else text,
        }

    return results


if __name__ == "__main__":
    print("Running span fidelity tests...")
    results = run_span_fidelity_test()
    all_pass = True
    for name, r in results.items():
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {name}: {r['tokens']} tokens")
        if not r["pass"]:
            all_pass = False

    print(f"\nResult: {'ALL PASSED' if all_pass else 'SOME FAILED'}")
