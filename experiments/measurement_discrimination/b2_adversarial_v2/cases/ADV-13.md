# ADV-13 — Rationale

## Candidate

> pseudomineralization

## Category

(3) Source-local derivative disguised as a cross-domain term. **Added after the
round-72 diagnostic revealed that ADV-05/ADV-06 happen to land inside the suffix
list's coverage.** ADV-13 is constructed to land OUTSIDE that coverage while
remaining a source-local derivative.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Single token, 20 characters.

Token indices: `p(0)s(1)e(2)u(3)d(4)o(5)m(6)i(7)n(8)e(9)r(10)a(11)l(12)i(13)z(14)a(15)t(16)i(17)o(18)n(19)`.

8-character substrings of `pseudomineralization` (starting at i=0..12):
`pseudomi`, `seudomin`, `eudomine`, `udominer`, `dominera`, `omineral`,
`minerali`, `ineraliz`, `neralizi`, `eralizin`, `ralizing`, ...

`minerali` (at i=6) is a substring of `mineralization` in Source A.

**Detector-visible overlap: Source A only.** Single-token special case:
- `longest_a_match = 14` (matches `mineralization` starting at i=6)
- `longest_b_match = 0`
- `excess_str = token[14:]` = chars 14-19 = `"zation"` (length 6)
- Suffix check: scan `COMMON_SUFFIXES` (`'ing', 'ed', 'tion', 'sion', 'ment',
  'ness', 'ance', 'ence', 'able', 'ible', 'ous', 'ive', 'al', 'ly', 'ize',
  'ise', 'ify', 'ate', 'ity'`).
  - `"zation"` ends with `"tion"`? Yes. `len(excess_str) = 6`, `len("tion") + 1
    = 5`. `6 ≤ 5`? **NO**.
  - `"zation"` ends with `"ation"`? `"ation"` is not in `COMMON_SUFFIXES`.
  - `"zation"` ends with `"ize"`? Last 3 chars are `"ion"`, not `"ize"`. No.
  - No other suffix matches.
- `is_morphological = False`.
- Branch: `if excess_str and not is_morphological and len(excess_str) >= 3`
  → True (6 ≥ 3). → `return False` → **ALLOW**.

## Semantic content of the candidate

`pseudomineralization` is morphologically:
- `pseudo-` (prefix meaning "false" or "fake" — used in science to denote
  phenomena that resemble a real process but are not, e.g. pseudomonas,
  pseudopodia, pseudoscience)
- `mineralization` (Source A's literal token — the deposition of minerals)

The term denotes: *a phenomenon that resembles mineralization but is not true
mineralization.* It is a modifier on Source A's mineralization concept,
introducing no new mechanism, mediator, or mineral system.

## Semantic mapping to Source A

The `mineralization` base is Source A's literal token. The `pseudo-` prefix is
a degree/truth modifier that qualifies whether the mineralization is genuine, but
introduces no new content beyond Source A.

## Semantic mapping to Source B

The candidate has no element that refers to anything in Source B. `pseudo-` does
not denote silicatein, silica, diatoms, or enzymatic catalysis — it denotes
"false" in a generic sense.

## Cross-source synthesis argument

The candidate does not combine content from both sources. It is fully explainable
from Source A alone (Source A's `mineralization` + a falsity modifier). Removing
Source B leaves the candidate's meaning completely intact.

## Independent semantic verdict

The candidate is a source-local derivative of Source A. The `pseudo-` prefix is
a falsity modifier, not a cross-source bridge. Per B-2, this constitutes
morphological leakage and must be **REJECTED**.

**Expected disposition: REJECT (leakage detected).**

## Detector behavior prediction

The detector will ALLOW — via the `non-suffix excess ≥ 3 chars → ALLOW` branch.
The excess `"zation"` (6 chars) ends with `"tion"` but exceeds the
`len("tion") + 1 = 5` threshold, so the morphological-suffix check fails, and
the excess is treated as a meaningful cross-source prefix.

This is the wrong answer.

## Why this case is adversarial

ADV-13 is the case that **breaks the round-72 fix** — cleanly, and without
depending on a specific suffix-list gap. The fix's suffix heuristic catches
source-local derivatives whose excess is short enough to fit a single suffix
(ADV-05 `hypermineralization` with excess `"ation"` length 5 = `len("tion")+1`;
ADV-06 `xenomineralization` with the same excess). It cannot catch derivatives
whose excess is one or two characters longer, because the `+1` slack is fixed
across all suffixes.

The boundary between ADV-05/ADV-06 (correctly rejected) and ADV-13 (wrongly
allowed) is **not semantic** — it is the difference between a 5-char excess and
a 6-char excess. The fix's correctness on ADV-05/ADV-06 is therefore not
evidence of semantic competence; it is evidence that the test fixture's source-
local derivatives happened to produce 5-char excesses.

ADV-13 is the smallest possible perturbation of ADV-05/ADV-06 that defeats the
heuristic while remaining a clear source-local derivative. It is the case the
auditor asked for in point (3) of the round-72 verdict: "source-local derivative
disguised as a cross-domain term" whose disposition "cannot be determined merely
from a hard-coded label in the test."
