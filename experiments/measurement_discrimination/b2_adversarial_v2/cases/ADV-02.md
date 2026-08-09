# ADV-02 — Rationale

## Candidate

> calcified matrix in osseous structures

## Category

(1) No substantial lexical overlap with either source, but a genuine source-local paraphrase.

## Source A (frozen)

> Calcium phosphate forms crystalline deposits in bone tissue through osteoblast-mediated mineralization.

## Source B (frozen)

> Marine diatoms precipitate silica-based cell walls using enzymatic silicatein proteins.

## Lexical overlap audit

For the candidate `calcified matrix in osseous structures`:

| token        | in source_a? | in source_b? | 8-char substrings matched? |
|--------------|--------------|--------------|----------------------------|
| calcified    | no           | no           | `calcifie`, `alcified` — Source A has `calcium phosphate` (no `calcif`). No match. |
| matrix       | no           | no           | `matrix` itself, 6 chars; no 8-char check. |
| osseous      | no           | no           | 7 chars; no 8-char check. (Source A has `bone`, not `osseous`.) |
| structures   | no           | no           | `structur`, `tructure`, `ructures` — none in either source. |

(Stopword `in` is dropped by the tokenizer.)

**Detector-visible overlap: NONE.** The detector falls through to the
"genuinely novel → NOT leaked" branch and will ALLOW.

## Semantic content of the candidate

`calcified matrix in osseous structures` denotes:
- **calcified matrix** — a mineralized extracellular matrix (i.e. a tissue whose
  organic scaffold has been impregnated with a calcium mineral phase)
- **osseous structures** — bone structures (osseous = bony)

The phrase as a whole denotes: *a mineralized matrix present in bone structures.*

## Semantic mapping to Source A

Source A asserts that calcium phosphate forms crystalline deposits in bone tissue
through osteoblast-mediated mineralization.

The candidate is a structural re-description of the same phenomenon:

| Source A literal     | Candidate synonym          |
|----------------------|-----------------------------|
| bone tissue          | osseous structures          |
| crystalline deposits (in) | calcified matrix       |
| (calcium phosphate) mineralization | (calcified matrix — same mineral deposition event) |

Every referent in the candidate is in Source A. The candidate introduces no new
concept that is not already present in Source A.

## Semantic mapping to Source B

Source B is about silica, diatoms, silicatein, enzymatic proteins. None of these
appear in the candidate. The candidate is exclusively about calcium-based, skeletal
mineralization — Source A's domain.

## Independent semantic verdict

The candidate is a synonym-substituted paraphrase of Source A. It does no
cross-source work. Per B-2, it constitutes paraphrase leakage and must be REJECTED.

**Expected disposition: REJECT (leakage detected).**

## Detector behavior prediction

The detector sees no lexical overlap and will ALLOW. Wrong answer.

## Why this case is adversarial

This case is a stronger variant of ADV-01: every content word in the candidate is a
deliberate synonym chosen to defeat 8-character substring matching while preserving
the source-local meaning. The detector's overlap test cannot see the synonymy, so it
falls through to the "novel → allow" branch — which is exactly the failure mode the
auditor identified.
