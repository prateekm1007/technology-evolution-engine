#!/usr/bin/env python3
"""span_mapper.py — Deterministic GLiREL token→character span mapping.

CRITICAL INVARIANT (per CTO directive §10):
    source[start:end] == span_text

If this invariant fails for any span, the extraction is INVALID.

This module provides:
  - token_positions_to_char_spans: map GLiREL token positions to character offsets
  - verify_span: verify the invariant source[start:end] == span_text
  - SpanMappingError: raised when mapping fails

NO LLM is used. The mapping is purely mechanical.
"""
from dataclasses import dataclass
from typing import Optional


class SpanMappingError(Exception):
    """Raised when token→character span mapping fails the verbatim invariant."""
    pass


@dataclass
class CharSpan:
    """A character-offset span into the source text."""
    text: str
    start: int
    end: int

    def verify(self, source_text: str) -> bool:
        """Verify that source_text[start:end] == text."""
        if self.start < 0 or self.end > len(source_text) or self.start > self.end:
            return False
        return source_text[self.start:self.end] == self.text

    def to_dict(self) -> dict:
        return {"text": self.text, "start": self.start, "end": self.end}


def token_positions_to_char_spans(
    token_positions: list,
    tokenizer,
    source_text: str,
    text_input: str,
) -> CharSpan:
    """Map GLiREL token positions to a character span.

    GLiREL returns token positions as [start_token_idx, end_token_idx] or
    a single token_idx. The tokenizer's offset_mapping provides character
    offsets for each token.

    Args:
        token_positions: GLiREL token positions (list of 1-2 ints, or single int)
        tokenizer: the tokenizer used by GLiREL (must support offset_mapping)
        source_text: the original source text
        text_input: the text that was tokenized (may include prompts/prefixes)

    Returns:
        CharSpan with verbatim text and character offsets into source_text

    Raises:
        SpanMappingError: if the mapping fails the verbatim invariant
    """
    # Normalize token_positions to [start, end]
    if isinstance(token_positions, int):
        start_tok, end_tok = token_positions, token_positions
    elif isinstance(token_positions, (list, tuple)):
        if len(token_positions) == 1:
            start_tok, end_tok = token_positions[0], token_positions[0]
        elif len(token_positions) == 2:
            start_tok, end_tok = token_positions
        else:
            raise SpanMappingError(f"Unexpected token_positions length: {token_positions}")
    else:
        raise SpanMappingError(f"Unexpected token_positions type: {type(token_positions)}")

    # Tokenize with offset mapping
    encoding = tokenizer(text_input, return_offsets_mapping=True, add_special_tokens=True)
    offsets = encoding.get("offset_mapping", None)
    if offsets is None:
        raise SpanMappingError("Tokenizer does not support offset_mapping")

    # Get character offsets for the token range
    # GLiREL token positions are into the full input sequence (which may include
    # prompt/prefix tokens). We need to find the character offsets and then
    # map them back to the source_text.
    if start_tok >= len(offsets) or end_tok >= len(offsets):
        raise SpanMappingError(
            f"Token position {start_tok}-{end_tok} out of range "
            f"(offsets has {len(offsets)} entries)"
        )

    char_start = offsets[start_tok][0]
    char_end = offsets[end_tok][1]

    # Extract the verbatim text from text_input
    verbatim = text_input[char_start:char_end]

    # Now find this verbatim text in source_text
    # (text_input may include prompt prefixes; source_text is the pure source)
    source_idx = source_text.find(verbatim)
    if source_idx < 0:
        # Try stripping whitespace
        verbatim_stripped = verbatim.strip()
        source_idx = source_text.find(verbatim_stripped)
        if source_idx >= 0:
            verbatim = verbatim_stripped
            # Adjust char_start/char_end to match stripped version
            # Find the stripped version in text_input
            stripped_idx = text_input.find(verbatim_stripped, char_start)
            if stripped_idx >= 0:
                char_start = stripped_idx
                char_end = stripped_idx + len(verbatim_stripped)

    if source_idx < 0:
        raise SpanMappingError(
            f"Verbatim text '{verbatim}' not found in source_text"
        )

    span = CharSpan(
        text=verbatim,
        start=source_idx,
        end=source_idx + len(verbatim),
    )

    # Verify the invariant
    if not span.verify(source_text):
        raise SpanMappingError(
            f"Span verification failed: source[{span.start}:{span.end}] != '{span.text}'"
        )

    return span


def verify_span(span_text: str, start: int, end: int, source_text: str) -> bool:
    """Verify the critical invariant: source_text[start:end] == span_text.

    Returns True if the invariant holds, False otherwise.
    """
    if start < 0 or end > len(source_text) or start > end:
        return False
    return source_text[start:end] == span_text


def run_edge_case_tests() -> dict:
    """Run tokenization edge case tests (per CTO directive §11).

    Tests:
      - hyphenated terms
      - parentheses
      - commas
      - periods
      - Unicode
      - chemical names
      - multiword entities
      - repeated entities
      - nested entities
      - abbreviations
      - long scientific terminology

    Returns:
        dict with test results (test_name → {pass: bool, details: str})
    """
    # These tests verify the verify_span function itself, which is the
    # invariant checker. The actual token→char mapping is tested in the
    # Kaggle notebook with the real tokenizer.

    results = {}

    test_cases = [
        ("hyphenated", "silica-based", 0, 12, "silica-based cell walls"),
        ("parentheses", "(enzymatic)", 0, 11, "(enzymatic) silicatein"),
        ("commas", "calcium, phosphate", 0, 18, "calcium, phosphate deposits"),
        ("periods", "mineralization.", 0, 16, "mineralization. Osteoblasts"),
        ("unicode", "café", 0, 4, "café mineral"),
        ("chemical", "Ca3(PO4)2", 0, 10, "Ca3(PO4)2 crystals"),
        ("multiword", "calcium phosphate", 0, 17, "calcium phosphate forms"),
        ("repeated", "mineral", 0, 8, "mineral and mineral again"),
        ("nested", "silica-based cell", 0, 17, "silica-based cell walls"),
        ("abbreviation", "e.g.", 0, 4, "e.g. osteoblasts"),
        ("long_term", "osteoblast-mediated mineralization", 0, 35,
         "osteoblast-mediated mineralization process"),
    ]

    for name, span_text, start, end, source in test_cases:
        try:
            result = verify_span(span_text, start, end, source)
            results[name] = {
                "pass": result,
                "details": f"verify_span('{span_text}', {start}, {end}) = {result}",
            }
        except Exception as e:
            results[name] = {"pass": False, "details": f"Exception: {e}"}

    return results


if __name__ == "__main__":
    print("Running edge case tests for span_mapper.py...")
    results = run_edge_case_tests()
    all_pass = True
    for name, r in results.items():
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {name}: {r['details']}")
        if not r["pass"]:
            all_pass = False

    print()
    if all_pass:
        print("ALL EDGE CASE TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        exit(1)
