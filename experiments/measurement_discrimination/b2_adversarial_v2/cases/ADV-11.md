# ADV-11 — Rationale

## Candidate

> biomineralization

## Category

(control) The round-72 "true allow" case. Included to confirm that the current
detector still allows it — and to make explicit that the allow is a heuristic
artifact, not a demonstrated cross-source justification.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Single token, 17 characters.

Token indices: `b(0)i(1)o(2)m(3)i(4)n(5)e(6)r(7)a(8)l(9)i(10)z(11)a(12)t(13)i(14)o(15)n(16)`.

8-character substrings of `biomineralization` (starting at i=0..9):
`biominer`, `iominera`, `omineral`, `minerali`, `ineraliz`, `neralizi`,
`eralizin`, `ralizing`, ...

`minerali` (at i=3) is a substring of `mineralization` in Source A. None of the
substrings appear in Source B.

**Detector-visible overlap: Source A only.** Single-token special case:
- `longest_a_match = 14` (matches `mineralization` starting at i=3)
- `longest_b_match = 0`
- `excess_str = token[14:]` = chars 14-16 = `"ion"` (length 3)
- Suffix check: scan `COMMON_SUFFIXES`. Does `"ion"` end with any suffix in the
  list (`'ing', 'ed', 'tion', 'sion', 'ment', 'ness', 'ance', 'ence', 'able',
  'ible', 'ous', 'ive', 'al', 'ly', 'ize', 'ise', 'ify', 'ate', 'ity'`)?
  - `"ion"` ends with `"ing"`? No (last 3 chars are `"ion"`, not `"ing"`).
  - `"ion"` ends with `"ed"`? No.
  - `"ion"` ends with `"tion"`? No (length 3 < 4).
  - `"ion"` ends with `"al"`? No.
  - `"ion"` ends with `"ly"`? No.
  - No suffix matches.
- `is_morphological = False`.
- Branch: `if excess_str and not is_morphological and len(excess_str) >= 3`
  → True (3 ≥ 3). → `return False` → **ALLOW**.

## Semantic content of the candidate

`biomineralization` is morphologically:
- `bio-` (prefix meaning "biological" or "living")
- `mineralization` (deposition of minerals)

The term denotes: *mineral deposition by biological systems.* It is a standard
scientific umbrella term covering both bone mineralization (Source A) and diatom
silica shell formation (Source B), among many other instances (e.g. mollusk shell
formation, coral skeleton formation).

## Semantic mapping to Source A

Source A's `mineralization` (calcium phosphate deposition by osteoblasts in bone)
is an instance of biomineralization. The candidate is a hypernym of Source A's
process.

## Semantic mapping to Source B

Source B's silica precipitation by silicatein in diatom cell walls is also an
instance of biomineralization (silica is a biogenic mineral, silicatein is a
biological catalyst, diatoms are living organisms). The candidate is a hypernym
of Source B's process.

## Cross-source synthesis argument

The candidate is a textbook cross-source umbrella term: it generalizes over both
sources, identifying the shared concept (biologically-controlled mineral deposition)
that unifies them. It cannot be constructed from either source alone — Source A
alone would yield `mineralization` (without the `bio-` qualifier), and Source B
alone would yield `silica precipitation` (without the `mineral` noun). The `bio-`
prefix and the `mineralization` noun come from different sources' conceptual
contributions.

## Independent semantic verdict

The candidate is a genuine cross-source umbrella term. Per B-2, it must be
**ALLOWED**.

**Expected disposition: ALLOW (no leakage).**

## Detector behavior prediction

The detector will ALLOW — via the `excess_str = "ion"`, `is_morphological =
False`, `len(excess_str) >= 3` branch. The same branch is triggered by ADV-13
(`pseudomineralization`, true REJECT) where `excess_str = "zation"` (length 6).

## Why this case is included (and why it is NOT evidence of detector correctness)

The auditor's round-72 critique is precisely that this case's ALLOW is reached by
a heuristic, not by demonstrated cross-source justification. ADV-11 is included to
make that fact observable: ADV-11 is allowed by the same `non-suffix excess ≥ 3`
branch that **wrongly** allows ADV-13 (`pseudomineralization`, a true REJECT
disguised as a cross-domain term).

A detector that gives the right answer on ADV-11 by the same mechanism that gives
the wrong answer on ADV-13 cannot be claimed to "establish cross-source
justification." The right answer on ADV-11 is a coincidence of the heuristic's
parameter space — specifically, the coincidence that `excess_str = "ion"` (3 chars)
passes the `len(excess_str) >= 3` lower bound but does NOT match any suffix in
`COMMON_SUFFIXES`, triggering the ALLOW branch.

This case is the keystone of the round-72 critique: it is the case the round-72
fix was designed to allow, and the case whose allow is most clearly unjustified by
the detector's actual mechanism.
