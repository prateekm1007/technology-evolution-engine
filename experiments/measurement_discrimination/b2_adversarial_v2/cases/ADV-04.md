# ADV-04 — Rationale

## Candidate

> silicatein-guided calcification

## Category

(2) Genuine cross-source synthesis, with terminology overlap on ONE source only.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Tokenizer splits on `[\s\-_]+`, yielding three tokens: `silicatein`, `guided`,
`calcification`.

| token          | in source_a? | in source_b? | 8-char substring matched? |
|----------------|--------------|--------------|---------------------------|
| silicatein     | no           | **yes** (literal token) | — |
| guided         | no           | no           | 6 chars; no 8-char check. |
| calcification  | no           | no           | `calcific`, `alcifica`, `lificati`, `ificatio`, `fication` — Source A has `calcium` (no `calcif`). No match. |

**Detector-visible overlap: Source B only, via the token `silicatein`.**

The detector's logic for "overlap with B only" branch:
- `unshared_tokens = {"guided", "calcification"}`
- Check whether any unshared token appears in Source A. None do.
- Conclude: source-local derivative → REJECT.

## Semantic content of the candidate

`silicatein-guided calcification` denotes:
- **silicatein-guided** — directed by the enzyme silicatein
- **calcification** — deposition of a calcium-based mineral phase

The phrase as a whole denotes: *calcium-based mineral deposition directed by the
enzyme silicatein.*

## Semantic mapping to Source A

Source A describes **calcium phosphate deposition in bone** — i.e. calcification.
The `calcification` portion of the candidate maps directly to Source A's mineral
system and process. Source A's mediator is osteoblasts (cells), not silicatein.

## Semantic mapping to Source B

Source B describes **silicatein** as the enzymatic mediator of silica precipitation.
The `silicatein-guided` portion of the candidate maps directly to Source B's
mediator. Source B's mineral is silica, not calcium.

## Cross-source synthesis argument

The candidate **explicitly combines**:
- the **enzymatic mediator** from Source B (silicatein), and
- the **calcium mineral system** from Source A (calcification, i.e. calcium
  phosphate deposition).

This is a textbook cross-source transfer: take the catalyst identified in one domain
(silicatein from diatom silica precipitation) and propose its application to the
mineral system identified in the other domain (calcium-based mineralization in
bone). Such a transfer is exactly the kind of cross-source hypothesis that B-2 is
supposed to permit — it could not be constructed from either source alone.

## Independent semantic verdict

The candidate is a genuine cross-source synthesis. Per B-2, it must be **ALLOWED**.

**Expected disposition: ALLOW (no leakage).**

## Detector behavior prediction

The detector sees lexical overlap with Source B only (via `silicatein`), finds that
the unshared tokens (`guided`, `calcification`) do not appear in Source A, and
concludes "source-local derivative → REJECT."

This is the wrong answer. The detector cannot recognize that `calcification` is a
hypernym of `calcium phosphate deposition` (the Source A event), because the
detector has no semantic bridge between `calcification` and `calcium phosphate`.

## Why this case is adversarial

This is the symmetric counterpart of ADV-03. ADV-03 had overlap on Source A and a
semantic bridge to Source B; ADV-04 has overlap on Source B and a semantic bridge
to Source A. Both fail for the same reason: the detector's "check unshared tokens
in the other source" rule is purely lexical and cannot detect hypernymy or
concept-level reference.
