# ADV-05 — Rationale

## Candidate

> hypermineralization

## Category

(3) Source-local derivative disguised as a cross-domain term.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Single token, 19 characters.

Token indices: `h(0)y(1)p(2)e(3)r(4)m(5)i(6)n(7)e(8)r(9)a(10)l(11)i(12)z(13)a(14)t(15)i(16)o(17)n(18)`.

8-character substrings of `hypermineralization` (starting at i=0..11):
`hypermin`, `ypermine`, `perminer`, `erminera`, `rmineral`, `minerali`,
`ineraliz`, `neralizi`, `eralizin`, `ralizing`, ...

Of these, `minerali` (at i=5) is a substring of `mineralization` in Source A.

**Detector-visible overlap: Source A only, via the single-token substring match.**

The detector enters the single-token special case (`unshared_tokens == set()` and
`len(bridge_tokens) == 1`):
- `has_a_substring = True`, `has_b_substring = False`
- Compute `longest_a_match`: starting at i=5, the match extends from `minerali`
  (8 chars) through `mineralization` (14 chars). So `longest_a_match = 14`.
- `longest_b_match = 0`.
- `excess_str = token[14:]` = chars 14-18 = `"ation"` (length 5).
- Suffix check: scan `COMMON_SUFFIXES`. `excess_str` ends with `"tion"` (last 4
  chars). `len(excess_str) = 5 ≤ len("tion") + 1 = 5`? YES. So
  `is_morphological = True`.
- Branch: `if excess_str and not is_morphological and len(excess_str) >= 3`
  fails (because `is_morphological = True`).
- Falls through to `return True` → **REJECT**.

## Semantic content of the candidate

`hypermineralization` is morphologically:
- `hyper-` (prefix meaning "excessive" or "above normal")
- `mineralization` (the process of depositing minerals)

The term denotes: *excessive mineral deposition.* It is a standard English
compound used in clinical and biological contexts to describe pathological
over-mineralization of tissue (e.g. vascular calcification, dental hypermineralization).

## Semantic mapping to Source A

Source A describes `mineralization` of bone by osteoblasts. The candidate is a
direct morphological derivative of Source A's `mineralization`, with a degree
modifier (`hyper-`) that quantifies the intensity. The candidate adds no new
concept beyond Source A — it is a degree modifier on Source A's process.

## Semantic mapping to Source B

The candidate has no element that refers to anything in Source B. There is no
silica, no diatom, no silicatein, no enzyme. The `hyper-` prefix is a degree
modifier, not a reference to Source B's biological system.

## Cross-source synthesis argument

The candidate does **not** combine content from both sources. It is fully
explainable from Source A alone (Source A's `mineralization` + a degree prefix).
Removing Source B leaves the candidate's meaning completely intact.

## Independent semantic verdict

The candidate is a source-local derivative of Source A. The `hyper-` prefix is a
degree modifier, not a cross-source bridge. Per B-2, this constitutes morphological
leakage and must be **REJECTED**.

**Expected disposition: REJECT (leakage detected).**

## Detector behavior prediction

The detector's single-token branch sees:
- `excess_str = "ation"` (5 chars)
- `excess_str` ends with `"tion"`, and `len(excess_str) = 5 ≤ len("tion") + 1 = 5`
- → `is_morphological = True`
- → falls through to `return True` → **REJECT**

The detector produces the right answer (REJECT) by accident: the `len(suffix) + 1`
threshold happens to be `5` for the `"tion"` suffix, which exactly matches the
length of `"ation"`. Any longer non-suffix excess would bypass the check.

The detector still cannot establish the SEMANTIC reason for rejection (that
`hyper-` is a degree modifier and not a cross-source bridge). It just happens that
the `-ation` tail fits the morphological-suffix heuristic.

## Why this case is adversarial (revised after diagnostic)

This case is included to expose the **boundary** of the round-72 fix's suffix
heuristic. The diagnostic confirmed that `hypermineralization` is correctly
rejected, but for a purely lexical reason (the 5-char excess `"ation"` matches the
`"tion"` suffix with the `+1` slack).

The case still serves the auditor's argument because:

1. It is a TRUE REJECT (source-local derivative), and the detector's REJECT is
   not evidence of cross-source-justification competence — it is evidence that
   the suffix list happens to contain `"tion"`.

2. Paired with ADV-11 (`biomineralization`, true ALLOW, detector ALLOWS because
   `excess_str = "ion"` does NOT match any suffix), ADV-05 shows that the
   detector's allow/reject decision on source-local-vs-cross-source compounds
   is determined entirely by whether the excess string happens to fit a suffix
   in `COMMON_SUFFIXES`. There is no semantic reasoning.

3. A trivially modified source-local derivative whose excess does NOT match a
   suffix (e.g. `pseudomineralization`, where the excess would be `"ization"`
   if the longest match were `minerali` — but actually the longest match
   extends to `mineralization`, leaving excess `"ization"` of length 7, which
   does NOT fit `len("tion")+1=5`, so `is_morphological = False`, so the
   detector would WRONGLY ALLOW) would defeat the heuristic. The auditor's
   argument does not depend on this specific case failing — it depends on the
   fact that the detector's decision is parameter-tuning, not semantics.

For an immediate demonstration of (3), see ADV-06b below — added after the
diagnostic revealed that the original ADV-05/ADV-06 pair happens to land inside
the suffix list's coverage.
