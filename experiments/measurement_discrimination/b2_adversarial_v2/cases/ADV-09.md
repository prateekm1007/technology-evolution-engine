# ADV-09 — Rationale

## Candidate

> quantum entanglement

## Category

(control) No overlap with either source, and genuinely unrelated to either source.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Tokens: `quantum`, `entanglement`. Neither appears in either source. No 8-char
substring matches.

**Detector-visible overlap: NONE.** The detector falls through to "novel → allow."

## Semantic content

`quantum entanglement` is a concept in quantum physics, completely unrelated to
biomineralization, osteoblasts, diatoms, or silicatein.

## Independent semantic verdict

The candidate is genuinely novel and unrelated to either source. Per B-2, it must
be **ALLOWED**.

**Expected disposition: ALLOW (no leakage).**

## Detector behavior prediction

The detector will ALLOW. Right answer.

## Why this case is included

This is the canonical "clean bridge" control. It exists to confirm that the
detector's "no overlap → allow" branch produces the correct answer when the
candidate is genuinely unrelated to both sources.

The contrast between ADV-09 (no overlap → ALLOW, correct) and ADV-01 (no overlap →
ALLOW, incorrect) is the central exhibit: the detector's no-overlap branch cannot
distinguish a genuinely novel candidate from a synonym-substituted source-local
paraphrase.
