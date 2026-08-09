# ADV-03 — Rationale

## Candidate

> enzyme-templated mineral deposition

## Category

(2) Genuine cross-source synthesis, with terminology overlap on ONE source only.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Tokenizer splits on `[\s\-_]+`, so the candidate yields four tokens: `enzyme`,
`templated`, `mineral`, `deposition`.

| token      | in source_a? | in source_b? | 8-char substring matched? |
|------------|--------------|--------------|---------------------------|
| enzyme     | no           | no           | 6 chars; no 8-char check. (Source B has `enzymatic` — `enzyme` is not a substring of `enzymatic`.) |
| templated  | no           | no           | `template`, `emplated` — none in either source. |
| mineral    | **yes** (substring of `mineralization`) | no | `mineral` is a 7-char substring of `mineralization` in Source A. The detector's `if token in source_a_lower` test catches this. |
| deposition | no           | no           | `depositi`, `epositio`, `position` — Source A has `deposits` (ends at `s`), so `depositi` is NOT a substring. No match. |

**Detector-visible overlap: Source A only, via the token `mineral`.**

The detector's logic for "overlap with A only" branch:
- `unshared_tokens = {"enzyme", "templated", "deposition"}`
- Check whether any unshared token appears in Source B (literally or via 8-char substring). None do.
- Conclude: source-local derivative → REJECT.

## Semantic content of the candidate

`enzyme-templated mineral deposition` denotes:
- **enzyme-templated** — shaped/guided by an enzyme (a protein catalyst)
- **mineral deposition** — the laying down of an inorganic mineral phase

The phrase as a whole denotes: *the laying down of a mineral phase, guided by an
enzyme catalyst.*

## Semantic mapping to Source A

Source A describes a mineral deposition event (calcium phosphate → crystalline
deposits in bone). The "mineral deposition" portion of the candidate maps directly
to Source A's process.

However, Source A's mineral deposition is mediated by **osteoblasts** — entire cells,
not enzymes. Source A says nothing about an enzyme template.

## Semantic mapping to Source B

Source B describes silica precipitation mediated by **silicatein**, which is
explicitly identified as an enzymatic protein. The "enzyme-templated" portion of
the candidate maps directly to Source B's enzymatic mechanism.

However, Source B's mineral is silica, not the generic "mineral" of the candidate.

## Cross-source synthesis argument

The candidate **explicitly combines**:
- the **enzyme-catalyst mechanism** from Source B (silicatein), and
- the **mineral deposition process** that Source A instantiates with calcium phosphate.

The candidate is a generalization that requires both sources to construct: it
abstracts over osteoblast-mediated calcium phosphate deposition (Source A) and
silicatein-mediated silica deposition (Source B), arriving at the unified concept
of enzyme-templated mineral deposition.

Removing Source A: the candidate loses its connection to "mineral" as a deposited
phase (Source B's term is "precipitate," and the silica is a "cell wall" rather
than a "deposit" in the Source A sense). Removing Source B: the candidate loses its
connection to the enzyme-catalyst mechanism (Source A's mediators are cells, not
enzymes). Both sources contribute meaning that the candidate requires.

## Independent semantic verdict

The candidate is a genuine cross-source synthesis. Per B-2, it does NOT constitute
leakage and must be **ALLOWED**.

**Expected disposition: ALLOW (no leakage).**

## Detector behavior prediction

The detector sees lexical overlap with Source A only (via `mineral`), finds that
the unshared tokens (`enzyme`, `templated`, `deposition`) do not appear in Source B
literally or via 8-char substring, and concludes "source-local derivative → REJECT."

This is the wrong answer. The detector cannot recognize that `enzyme` is a
concept-level reference to Source B's silicatein (silicatein IS an enzyme), because
the detector has no semantic bridge between `enzyme` and `enzymatic silicatein
proteins`.

## Why this case is adversarial

This case defeats the detector's "overlap with one source only → check unshared
tokens in other source" rule by being a true allow whose cross-source connection
is semantic, not lexical. The unshared token `enzyme` is a hypernym of `silicatein`
(a specific enzyme), but the detector cannot detect hypernymy.
