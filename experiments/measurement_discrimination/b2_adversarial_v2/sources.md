# B-2 Adversarial Test Set v2 — Canonical Sources

These two source texts are frozen for the entire adversarial set. Every test case
in `cases/` and every entry in `test_fixture.json` is evaluated against these
exact strings.

## Source A — bone mineralization

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

**Semantic content (what the source actually claims):**
- Mineral system: calcium phosphate (a calcium-bearing inorganic mineral)
- Physical form: crystalline deposits
- Anatomical site: bone tissue
- Cellular agent: osteoblasts
- Process: biologically-mediated mineral deposition (mineralization)

## Source B — diatom silica shell formation

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

**Semantic content (what the source actually claims):**
- Organism: marine diatoms
- Mineral system: silica (a silicon-bearing inorganic mineral)
- Physical form: cell walls (i.e. a structured inorganic scaffold)
- Cellular agent: silicatein (an enzyme — a protein catalyst)
- Process: enzymatically-catalyzed mineral precipitation

## What "cross-source synthesis" means here

A candidate term or phrase performs **genuine cross-source synthesis** if and only if
its semantic content draws meaningfully on **both** sources and could not be
constructed from either source alone.

For this source pair, both sources describe **biologically-controlled deposition of
an inorganic mineral** — bone (calcium phosphate, by osteoblasts) and diatom shells
(silica, by silicatein). A cross-source synthesis would unify these two instances
under a shared concept: e.g. "biologically-controlled mineral deposition,"
"enzyme-templated inorganic lattice formation," or "protein-catalyzed biogenic oxide
precipitation."

A candidate that draws on only one source — even when reworded, inflected, or
prefixed — is **source-local** and constitutes leakage.
