# ADV-06 — Rationale

## Candidate

> xenomineralization

## Category

(3) Source-local derivative disguised as a cross-domain term.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Single token, 18 characters.

Token indices: `x(0)e(1)n(2)o(3)m(4)i(5)n(6)e(7)r(8)a(9)l(10)i(11)z(12)a(13)t(14)i(15)o(16)n(17)`.

8-character substrings of `xenomineralization` (starting at i=0..10):
`xenomine`, `enominer`, `nominera`, `omineral`, `minerali`, `ineraliz`,
`neralizi`, `eralizin`, `ralizing`, ...

`minerali` (at i=4) is a substring of `mineralization` in Source A.

**Detector-visible overlap: Source A only.** The detector enters the single-token
special case, identical to ADV-05:
- `longest_a_match = 14` (matches `mineralization` starting at i=4)
- `longest_b_match = 0`
- `excess_str = token[14:]` = chars 14-17 = `"ation"` (length 5)
- Suffix check: `excess_str` ends with `"tion"`. `len(excess_str) = 5 ≤
  len("tion") + 1 = 5`? YES. → `is_morphological = True`.
- Branch fails (`is_morphological = True`). Falls through to `return True` →
  **REJECT**.

## Semantic content of the candidate

`xenomineralization` is morphologically:
- `xeno-` (prefix meaning "foreign" or "strange" — used in biology to denote
  foreign-body phenomena, e.g. xenograft, xenobiotic)
- `mineralization` (deposition of minerals)

The term denotes: *mineral deposition associated with a foreign body or foreign
substance.* It is a Source-A-style process concept (mineralization) with a
modifier specifying the trigger context (foreign).

## Semantic mapping to Source A

The `mineralization` base is Source A's literal token. The `xeno-` prefix is a
modifier that qualifies the type of mineralization (foreign-body-associated) but
introduces no new mechanism, mediator, or mineral system beyond what Source A
already describes.

## Semantic mapping to Source B

The candidate has no element that refers to anything in Source B. `xeno-` does
not denote silicatein, silica, diatoms, or enzymatic catalysis — it denotes
"foreign" in a generic biological sense.

## Cross-source synthesis argument

The candidate does not combine content from both sources. It is fully explainable
from Source A alone (Source A's `mineralization` + a foreign-body modifier).
Removing Source B leaves the candidate's meaning completely intact.

## Independent semantic verdict

The candidate is a source-local derivative of Source A. Per B-2, this constitutes
morphological leakage and must be **REJECTED**.

**Expected disposition: REJECT (leakage detected).**

## Detector behavior prediction

The detector applies the same `len(suffix) + 1` heuristic as in ADV-05. The
excess `"ation"` (5 chars) matches the `"tion"` suffix with the +1 slack, so
`is_morphological = True`, and the detector falls through to `return True` →
**REJECT**.

The right answer (REJECT) is produced by accident — the suffix list happens to
contain `"tion"` and the threshold happens to be 5. See ADV-13 for a
source-local derivative whose excess (`"zation"`, 6 chars) does NOT fit the
threshold, defeating the heuristic.

## Why this case is adversarial (revised after diagnostic)

ADV-05 and ADV-06 form a pair. Both are source-local derivatives whose excess
happens to be the 5-char string `"ation"`, which fits the `"tion"` suffix with
the `+1` slack. The detector correctly rejects both, but for purely lexical
parameter-tuning reasons — not because it recognizes that `hyper-` and `xeno-`
are degree/foreign modifiers that do not bridge to Source B.

The pair is retained to document the boundary of the round-72 heuristic: it
catches source-local derivatives whose excess matches a suffix in
`COMMON_SUFFIXES` with the `+1` slack, and misses those whose excess doesn't.
ADV-13 demonstrates the missing-coverage side of that boundary.
