# ADV-01 — Rationale

## Candidate

> skeletal calcification process

## Category

(1) No substantial lexical overlap with either source, but a genuine source-local paraphrase.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

The detector at commit `20ac268` tokenizes on `[\s\-_]+`, keeps tokens of length ≥ 4
that are not in a stopword list, and considers a token to "overlap" with a source
if either the token itself, or any 8-character substring of it, appears in that source.

For the candidate `skeletal calcification process`:

| token       | in source_a? | in source_b? | 8-char substrings matched? |
|-------------|--------------|--------------|----------------------------|
| skeletal    | no           | no           | none                       |
| calcification | no         | no           | `calcific`, `alcifica`, `lificati`, `ificatio`, `fication` — none appear in either source. Source A contains `calcium` (different substring). |
| process     | no           | no           | (token length 7, no 8-char check) |

**Detector-visible overlap: NONE.** The detector sees zero overlap with either
source and falls through to the "genuinely novel → NOT leaked" branch.

## Semantic content of the candidate

`skeletal calcification process` denotes:
- **skeletal** — pertaining to the skeleton (the structural framework of bone)
- **calcification** — the deposition of calcium salts as a mineral phase
- **process** — a biological mechanism

The phrase as a whole denotes: *the biological process by which calcium salts are
deposited in the skeleton.*

## Semantic mapping to Source A

Source A asserts: *Calcium phosphate forms crystalline deposits in bone tissue
through osteoblast-mediated mineralization.*

This is **the same claim** as the candidate, reworded via synonym substitution:

| Source A literal       | Candidate synonym  |
|------------------------|--------------------|
| bone tissue            | skeletal           |
| calcium phosphate (deposition) | calcification |
| mineralization (process) | process          |

Every element of the candidate maps to a single element of Source A. No element of
the candidate refers to anything in Source B — there is no silica, no diatom, no
silicatein, no enzyme, no protein catalyst.

## Semantic mapping to Source B

Source B asserts: *Marine diatoms precipitate silica-based cell walls using
enzymatic silicatein proteins.*

The candidate has no element that refers to anything in Source B. The candidate is
entirely about calcium-based mineralization in bone; Source B is entirely about
silica-based mineral deposition in diatoms.

## Independent semantic verdict

The candidate is a **paraphrase of Source A only**. It does no cross-source work.
Per the B-2 protocol, a candidate that is fully explainable by one source alone —
even when reworded — constitutes paraphrase leakage and must be **REJECTED**.

**Expected disposition: REJECT (leakage detected).**

## Detector behavior prediction

The detector's only signal for this candidate is "no lexical overlap with either
source." Its rule for that case is `return False` (NOT leaked, ALLOW).

Therefore the detector will **ALLOW** this candidate — which is the wrong answer.

The detector cannot distinguish this source-local paraphrase from a genuinely novel
term, because the detector has no mechanism to evaluate whether the candidate's
semantic content is derivable from one source alone.

## Why this case is adversarial

This case defeats the detector's "no overlap → allow" rule by being a true reject
that produces zero lexical overlap. The detector's allow is structurally guaranteed,
not contingent on the candidate's semantic content.
