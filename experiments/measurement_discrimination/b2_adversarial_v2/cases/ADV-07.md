# ADV-07 — Rationale

## Candidate

> enzyme-templated inorganic lattice formation

## Category

(4) Minimal-overlap cross-source synthesis (no lexical anchor).

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

Tokenizer splits on `[\s\-_]+`, yielding five tokens: `enzyme`, `templated`,
`inorganic`, `lattice`, `formation`.

| token      | in source_a? | in source_b? | 8-char substring matched? |
|------------|--------------|--------------|---------------------------|
| enzyme     | no           | no           | 6 chars; no 8-char check. (Source B has `enzymatic`; `enzyme` is not a substring of `enzymatic`.) |
| templated  | no           | no           | `template`, `emplated` — none in either source. |
| inorganic  | no           | no           | `inorgani`, `norganic` — none in either source. |
| lattice    | no           | no           | 6 chars; no 8-char check. |
| formation  | no           | no           | 8-char `formation` itself; Source A has `forms` (4 chars), Source B has nothing matching. No match. |

**Detector-visible overlap: NONE.** The detector falls through to the
"genuinely novel → NOT leaked" branch and will ALLOW.

## Semantic content of the candidate

`enzyme-templated inorganic lattice formation` denotes:
- **enzyme-templated** — guided/shaped by an enzyme catalyst
- **inorganic** — non-organic (mineral)
- **lattice** — a structured crystalline arrangement
- **formation** — the process of being formed

The phrase as a whole denotes: *the formation of a structured inorganic crystalline
arrangement, guided by an enzyme catalyst.*

## Semantic mapping to Source A

Source A describes:
- A **mineral** (`calcium phosphate`) → maps to `inorganic lattice`
- Formed as a **crystalline deposit** → maps to `lattice formation`
- Via a **biological mediator** (osteoblasts — cells, not enzymes)

The candidate's `inorganic lattice formation` portion is a generic abstraction of
Source A's calcium phosphate crystalline deposit formation.

## Semantic mapping to Source B

Source B describes:
- A **mineral** (`silica`) → also an `inorganic lattice`
- Precipitated as a **cell wall** (a structured scaffold) → maps to `lattice formation`
- Via an **enzyme catalyst** (`enzymatic silicatein proteins`)

The candidate's `enzyme-templated` portion is a direct abstraction of Source B's
enzymatic silicatein-mediated mechanism.

## Cross-source synthesis argument

The candidate generalizes over **both** sources:
- Source A's instance: calcium phosphate (inorganic lattice) formed by osteoblasts
  (cells, not enzymes)
- Source B's instance: silica (inorganic lattice) formed by silicatein (an enzyme)

The unified abstraction is `enzyme-templated inorganic lattice formation` — a
phrase that subsumes Source B's specific instance and proposes the same template
for Source A's mineral system. The candidate is a textbook cross-source
generalization: it abstracts the enzyme-templating mechanism from Source B and
applies it to the inorganic-lattice-formation concept that spans both sources.

Removing Source A: the candidate loses its connection to "inorganic lattice
formation" as a phenomenon (Source B's term is "cell wall," not "lattice
formation" — that phrasing is closer to Source A's "crystalline deposits").
Removing Source B: the candidate loses its connection to enzyme templating
(Source A's mediators are cells, not enzymes). Both sources contribute meaning
that the candidate requires.

## Independent semantic verdict

The candidate is a genuine cross-source synthesis with no lexical anchor in either
source. Per B-2, it must be **ALLOWED**.

**Expected disposition: ALLOW (no leakage).**

## Detector behavior prediction

The detector sees no lexical overlap and falls through to the "novel → allow"
branch. It will ALLOW — which is the right answer.

## Why this case is adversarial (despite the detector getting the right answer)

This case is paired with ADV-01 (`skeletal calcification process`), which is also a
no-overlap candidate. ADV-01 is a true REJECT; ADV-07 is a true ALLOW. The detector
gives the **same answer** (ALLOW) for both, because it has no mechanism to
distinguish them.

The detector's "no overlap → allow" rule is structurally unable to distinguish
between:
- a synonym-substituted source-local paraphrase (ADV-01: REJECT), and
- a cross-source generalization with no lexical anchor (ADV-07: ALLOW).

This case therefore demonstrates that the detector's ALLOW for ADV-07 is not
evidence of correct cross-source justification — it is evidence of the detector
defaulting to ALLOW when it has no signal. A detector that gets the right answer
on ADV-07 by accident cannot be claimed to "establish cross-source justification."
