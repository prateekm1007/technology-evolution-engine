# ADV-12 — Rationale

## Candidate

> mineralizing

## Category

(control) Source-local morphological derivative — the case the round-72 fix was
designed to reject.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Single token, 12 characters.

8-character substrings of `mineralizing`:
`minerali`, `ineraliz`, `neralizi`, `eralizin`, `ralizing`.

`minerali` is a substring of `mineralization` in Source A. None match Source B.

**Detector-visible overlap: Source A only.** Single-token special case:
- `longest_a_match = 8` (matches `minerali` only — the `z` at index 8 of
  `mineralizing` doesn't match the `z` at index 8 of `mineralization`? Wait —
  let me re-check. `mineralizing` = m-i-n-e-r-a-l-i-z-i-n-g. `mineralization` =
  m-i-n-e-r-a-l-i-z-a-t-i-o-n. The first 9 chars are identical: `mineraliz`. So
  the match extends to length 9.)
- Actually, re-tracing: the detector extends the match while
  `token[i:i+match_len+1] in source_a_lower`. Starting at i=0, match_len=8 →
  `token[0:9]` = `mineraliz` → is this in source_a_lower? Yes
  (`mineralization` starts with `mineraliz`). match_len=9.
  - `token[0:10]` = `mineralizi` → is this in source_a_lower?
    `mineralization` has `mineraliza` at position 0-9. `mineralizi` is NOT a
    substring of `mineralization`. So extension stops at match_len=9.
- `longest_a_match = 9`.
- `excess_str = token[9:] = "ing"` (length 3).
- Suffix check: `excess_str` ends with `ing` (last 3 chars). `len(excess_str) = 3
  ≤ len("ing") + 1 = 4`. So `is_morphological = True`.
- Branch: `if excess_str and not is_morphological and len(excess_str) >= 3`
  fails (because `is_morphological = True`). Falls through to `return True` →
  **REJECT**.

## Semantic content of the candidate

`mineralizing` is the present participle of `mineralize` — a grammatical inflection
of `mineralization` (Source A's literal token).

## Semantic mapping to Source A

Direct morphological derivative of Source A's `mineralization`. Adds nothing.

## Semantic mapping to Source B

No reference to anything in Source B.

## Independent semantic verdict

Source-local morphological derivative. Per B-2, must be **REJECTED**.

**Expected disposition: REJECT (leakage detected).**

## Detector behavior prediction

The detector will REJECT — via the `is_morphological = True` branch (because
`excess_str = "ing"` is a short suffix).

## Why this case is included

This is the case the round-72 fix successfully rejects. It is included to confirm
that the fix's morphological-suffix branch is intact, and to make the contrast with
ADV-05/ADV-06 explicit:

- `mineralizing` (excess = `ing`, 3 chars) → suffix detected → REJECT ✓
- `hypermineralization` (excess = `ization`, 7 chars) → suffix check fails → ALLOW ✗
- `xenomineralization` (excess = `ization`, 7 chars) → suffix check fails → ALLOW ✗

The round-72 fix's suffix heuristic only catches short suffixes (`-ing`, `-ed`,
`-tion` as exact 3-4 char excesses). It cannot catch longer morphological
derivations (`-ization` as a 7-char excess) — those bypass the heuristic and are
allowed as if they were meaningful cross-source prefixes.

This case therefore demonstrates the **boundary** of the round-72 fix's suffix
heuristic: it works for short suffixes and fails for long ones. The boundary is
not semantically motivated — it is a side effect of the `len(excess) ≤ len(suffix)
+ 1` threshold.
