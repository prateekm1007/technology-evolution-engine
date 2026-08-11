# ADV-08 — Rationale

## Candidate

> protein-catalyzed biogenic oxide precipitation

## Category

(4) Minimal-overlap cross-source synthesis (no lexical anchor in Source A; partial
overlap in Source B that is insufficient to establish cross-source work).

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Tokenizer splits on `[\s\-_]+`, yielding five tokens: `protein`, `catalyzed`,
`biogenic`, `oxide`, `precipitation`.

| token          | in source_a? | in source_b? | 8-char substring matched? |
|----------------|--------------|--------------|---------------------------|
| protein        | no           | **yes** (literal token in `silicatein proteins`) | — |
| catalyzed      | no           | no           | `catalyze`, `atalyzed` — Source B has `enzymatic` (no `catalyz`). No match. |
| biogenic       | no           | no           | `biogenic` itself, 8 chars; not in either source. |
| oxide          | no           | no           | 5 chars; no 8-char check. (Source B has `silica` — `oxide` is not a substring of `silica`.) |
| precipitation  | no           | **yes** (via 8-char substring `precipit` of `precipitate`) | — |

**Detector-visible overlap: Source B only**, via two tokens (`protein`,
`precipitation`).

The detector enters the "overlap with B only" branch:
- `unshared_tokens = {"catalyzed", "biogenic", "oxide"}`
- Check whether any unshared token appears in Source A. None do.
- Conclude: source-local derivative → REJECT.

## Semantic content of the candidate

`protein-catalyzed biogenic oxide precipitation` denotes:
- **protein-catalyzed** — catalyzed by a protein (i.e. an enzyme)
- **biogenic** — produced by a biological organism
- **oxide** — a mineral oxide (calcium phosphate contains oxide anions; silica is
  silicon dioxide, an oxide)
- **precipitation** — deposition from solution

The phrase as a whole denotes: *the deposition of a mineral oxide, catalyzed by a
protein enzyme, produced by a biological organism.*

## Semantic mapping to Source A

Source A describes calcium phosphate (a calcium-bearing mineral oxide) deposited in
bone by osteoblasts. The candidate's `biogenic oxide precipitation` portion subsumes
Source A's mineral system: calcium phosphate is a biogenic oxide, and its deposition
in bone is its precipitation.

However, Source A's mediator (osteoblasts) is a cell, not a protein catalyst. The
candidate's `protein-catalyzed` portion does not map to Source A.

## Semantic mapping to Source B

Source B describes silica (a silicon oxide) precipitated by diatoms via silicatein
(an enzymatic protein). The candidate maps cleanly to Source B:
- `protein-catalyzed` ↔ silicatein (enzymatic protein)
- `biogenic oxide` ↔ silica (a biogenic oxide)
- `precipitation` ↔ precipitate

## Cross-source synthesis argument

The candidate is an **umbrella term** that subsumes both sources:
- Source A's instance: biogenic calcium oxide (calcium phosphate) precipitation by
  osteoblasts (cells, not enzymes — so the candidate does not perfectly fit Source
  A's mediator, but the mineral system and the biogenic precipitation concept fit)
- Source B's instance: biogenic silicon oxide (silica) precipitation by silicatein
  (a protein catalyst — fits perfectly)

The candidate generalizes over both: it identifies the shared concept of
"biologically produced mineral oxide deposition." Even though the `protein-catalyzed`
qualifier fits Source B more directly than Source A, the umbrella concept
(`biogenic oxide precipitation`) spans both sources — neither source alone
exhausts the candidate's scope.

A human adjudicator would weigh this carefully: the candidate is more Source-B-flavored
than Source-A-flavored, but its umbrella scope (biogenic oxide precipitation) is
genuinely cross-source. The candidate is therefore an ALLOW under B-2's bridging
criterion, though it is a weaker ALLOW than ADV-07.

## Independent semantic verdict

The candidate is a cross-source umbrella term whose scope spans both sources,
though its lexical surface is closer to Source B. Per B-2, it must be **ALLOWED**.

**Expected disposition: ALLOW (no leakage).**

## Detector behavior prediction

The detector sees lexical overlap with Source B only (via `protein` and
`precipitation`), finds that the unshared tokens do not appear in Source A, and
concludes "source-local derivative → REJECT."

This is the wrong answer. The detector cannot recognize that `biogenic oxide
precipitation` is an umbrella term that subsumes Source A's calcium phosphate
deposition, because it has no semantic bridge between `oxide` and `calcium phosphate`
(or between `biogenic` and `bone`).

## Why this case is adversarial

This case pairs with ADV-04 (`silicatein-guided calcification`) to probe both
directions of the asymmetry:
- ADV-04: overlap on Source B only, semantic bridge to Source A via `calcification`.
- ADV-08: overlap on Source B only (different tokens), semantic bridge to Source A
  via umbrella scope (`biogenic oxide precipitation` subsumes calcium phosphate).

Both fail for the same reason as ADV-03 and ADV-04: the detector's "check unshared
tokens in the other source" rule is purely lexical and cannot detect hypernymy,
umbrella scope, or concept-level reference.
