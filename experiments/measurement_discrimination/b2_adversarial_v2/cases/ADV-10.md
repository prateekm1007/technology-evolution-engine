# ADV-10 — Rationale

## Candidate

> calcium phosphate

## Category

(control) Exact-string leakage.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

The candidate string `calcium phosphate` appears literally in Source A (first two
words). The detector's Rule 1 (`if bridge_lower in source_a_lower or bridge_lower in
source_b_lower`) fires immediately and returns True (leakage detected).

## Independent semantic verdict

The candidate is a literal quote from Source A. Per B-2, this is exact-string
leakage and must be **REJECTED**.

**Expected disposition: REJECT (leakage detected).**

## Detector behavior prediction

The detector will REJECT. Right answer.

## Why this case is included

Sanity check. Confirms the detector's exact-match rule is intact. If this case
fails, the detector is broken in a more fundamental way than the round-72 critique
addresses.
