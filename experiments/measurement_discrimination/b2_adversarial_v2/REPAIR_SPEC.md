# B-2 REPAIR SPECIFICATION — Independent Semantic Support

**Status:** AMENDED SPEC (round-79) — FROZEN FOR RE-ADJUDICATION
**Original freeze:** 2026-08-09 (commit `8a84fdc`, round-73)
**First amended freeze:** 2026-08-10 (commit `4bc945d`, round-74)
**Second amended freeze:** 2026-08-10 (commit `3076d3a`, round-75)
**Third amended freeze:** 2026-08-10 (commit `9b4d843`, round-76)
**Fourth amended freeze:** 2026-08-10 (commit `7f2977a`, round-77)
**Fifth amended freeze:** 2026-08-10 (commit `015b735`, round-78)
**Sixth amended freeze:** 2026-08-10 (this revision, round-79)
**Frozen by:** protocol-B implementer (this agent)
**Adjudication status:** Round-78 verdict REJECT WITH TWO MANDATORY
CONDITIONS → round-79 verdict ACCEPT WITH ONE CONDITION. This sixth
amended revision resolves the round-79 condition: explicitly state
that inference-rule classification does not establish derivation
validity, and freeze the 8-step verification ordering. Awaiting
re-adjudication before any implementation work may begin.

**Supersedes:** The lexical detector at commit `20ac268`
(`b1_b2_verification._check_leakage`). That detector's 6/6 result on the
round-72 fixture is retained as an **engineering regression result only** and
must NOT be promoted to scientific evidence that paraphrase leakage has been
solved.

**Authority:** This spec is issued in response to the external auditor's
round-73 verdict, which adjudicated the B-2 v2 adversarial diagnostic
(6/13 mismatches across three semantic failure modes) and directed that a
repair specification be drafted and independently adjudicated before any
implementation work begins. Subsequent verdicts (round-74 through
round-79) each directed amendments to resolve specific defects. This
sixth amended revision resolves the round-79 condition.

**Adjudication history:**

| Round | Verdict | Action |
|-------|---------|--------|
| 73 | — | Spec drafted and frozen at commit `8a84fdc` |
| 74 | ACCEPT WITH CONDITIONS | First amended revision (commit `4bc945d`) resolves 7 conditions + wording correction |
| 75 | ACCEPT WITH CONDITIONS | Second amended revision (commit `3076d3a`) resolves 3 conditions + Section 5.1 refinement |
| 76 | REJECT WITH ONE MANDATORY CONDITION | Third amended revision (commit `9b4d843`) eliminates non-constructible `ISS_neither`, replaces with `REDUNDANT_SUPPORT` |
| 77 | REJECT WITH ONE MANDATORY CONDITION | Fourth amended revision (commit `7f2977a`) adds `JOINT_CROSS_SOURCE` support for cross-source synthesis relations |
| 78 | REJECT WITH TWO MANDATORY CONDITIONS | Fifth amended revision (commit `015b735`) decouples `ISS_both` from `JOINT_CROSS_SOURCE` and freezes the inference-rule taxonomy |
| 79 | ACCEPT WITH ONE CONDITION | This sixth amended revision adds the 8-step verification ordering (classification is not validity) |
| 80+ | PENDING | Re-adjudication by external auditor |

**Round-79 condition resolved by this amendment:**

1. **Explicitly state that inference-rule classification does not
   establish derivation validity, and freeze the verification
   ordering** (new Section 2.6.9; Section 2.7 anti-regression item 7;
   Section 8.5 anti-regression).

   The round-78 spec froze the inference-rule taxonomy
   (`inference-rules-v1`), which prevents the detector from inventing
   rule labels. But the taxonomy is a **classification ontology**, not
   an **inference engine** — selecting `COMPOSITION`,
   `ABSTRACTION`, etc. must never itself imply that the derived claim
   is true. Without an explicit verification ordering, an
   implementation could accept a `JOINT_CROSS_SOURCE` entry based
   solely on classification ("LLM says this is COMPOSITION →
   COMPOSITION accepted → derived claim accepted"), recreating the
   semantic-leakage problem the spec is trying to eliminate.

   The round-79 amendment adds Section 2.6.9: a mandatory 8-step
   verification ordering for every `JOINT_CROSS_SOURCE` entry. Each
   step must pass before the next is evaluated; failure at any step
   rejects the entry. Step 5 (independently judge whether the derived
   claim actually follows under the stated rule) is the operational
   mechanism that prevents misapplication of real labels.

   This is a small specification clarification, not another
   architecture round. The auditor stated: "Once that sentence/order
   is frozen and re-adjudicated, I would consider the specification
   sufficiently closed to move out of design."

---

## 0. Reading guide

This document is a **specification**, not an implementation. It defines:

1. The property the B-2 detector must establish (Section 2).
2. The decision criterion that maps the property to a REJECT/ALLOW label
   (Section 2.4).
3. The adversarial test oracles that any implementation must pass, including
   the keystone ADV-11 vs ADV-13 distinction (Section 3).
4. The required detector properties — including the anti-tuning safeguards
   that prevent the implementer from adapting the detector to the public test
   set (Section 5).
5. The workflow: spec freeze → independent adjudication → held-out set
   construction → implementation → adversarial audit → implementation freeze
   → Protocol B discrimination run (Section 7).
6. The open questions that the auditor must resolve before implementation
   may begin (Section 9).

The spec is **implementation-agnostic** (Section 6): it does not prescribe
LLM-based, symbolic, or hybrid approaches. It prescribes the **evidence** the
detector must produce and the **properties** it must demonstrate.

---

## 1. Problem statement

### 1.1 What is broken

The current B-2 detector at commit `20ac268` is purely lexical. Its decision
procedure consists of:

- exact-string match,
- token overlap (≥ 4 chars, non-stopword),
- 8-character substring overlap,
- a single-token special case with a `COMMON_SUFFIXES` list and a
  `len(suffix) + 1` threshold,
- a "non-suffix excess ≥ 3 chars → ALLOW" branch.

The round-72 fix replaced an earlier pure-substring rule with this procedure
and produced a 6/6 result on a 6-case fixture. The round-73 adversarial
diagnostic (13 cases, 9 adversarial + 4 controls) produced 6/13 mismatches.
The mismatches cluster into three failure modes that are **not reliably
resolved by the current lexical feature set**. (Per round-74 wording
correction: this is a statement about the current lexical detector, not a
universal theoretical claim about all possible lexical or symbolic systems.)

### 1.2 Mode A — paraphrase leakage (false negative)

A candidate paraphrases a source-local concept without reusing its vocabulary.
The detector sees no lexical overlap and falls through to its "novel → allow"
branch, producing a false ALLOW.

**Cases:** ADV-01 (`skeletal calcification process`), ADV-02 (`calcified matrix
in osseous structures`).

**Why tuning cannot fix this:** for any lexical-overlap threshold the
implementer chooses, a paraphrase can be constructed that falls below it. The
detector has no mechanism to evaluate whether the candidate's *meaning* is
derivable from one source alone.

### 1.3 Mode B — genuine synthesis (false positive)

A legitimate cross-domain mechanism contains terminology from one source
while doing its conceptual work by combining that source with information
from the other. The detector sees overlap with one source only, fails to find
the unshared tokens in the other source (literally or via 8-char substring),
and falls through to its "source-local derivative → reject" branch, producing
a false REJECT.

**Cases:** ADV-03 (`enzyme-templated mineral deposition`), ADV-04
(`silicatein-guided calcification`), ADV-08 (`protein-catalyzed biogenic oxide
precipitation`).

**Why tuning cannot fix this:** the cross-source connection in these cases is
**semantic** — `enzyme` is a hypernym of `silicatein`; `calcification` is a
hypernym of `calcium phosphate deposition`; `biogenic oxide precipitation` is
an umbrella term subsuming both sources' mineral systems. No lexical overlap
threshold can detect hypernymy or umbrella scope.

### 1.4 Mode C — morphological gaming (false negative)

A source-local derivative is constructed whose excess (the part of the token
that extends beyond the longest source-A or source-B match) does not match
any suffix in `COMMON_SUFFIXES` with the `+1` slack. The detector's
"non-suffix excess ≥ 3 chars → ALLOW" branch fires, producing a false ALLOW.

**Case:** ADV-13 (`pseudomineralization`, excess `"zation"` length 6, exceeds
`len("tion") + 1 = 5`).

**Why tuning cannot fix this:** for any suffix list and any slack threshold,
a source-local derivative can be constructed whose excess falls outside the
list's coverage. The boundary between ADV-11 (`biomineralization`, true ALLOW,
excess `"ion"` length 3) and ADV-13 (`pseudomineralization`, true REJECT,
excess `"zation"` length 6) is the **length of the excess string**, not any
semantic property. The detector cannot distinguish a meaningful cross-source
prefix (`bio-`) from a degree/falsity modifier (`pseudo-`, `hyper-`, `xeno-`)
without semantic analysis.

### 1.5 The keystone falsification

The strongest single piece of evidence that the current B-2 mechanism does
**not** perform cross-source justification is the ADV-11 vs ADV-13 pair:

| Case | Candidate | Excess | True disposition | Detector disposition |
|------|-----------|--------|------------------|----------------------|
| ADV-11 | `biomineralization` | `"ion"` (3 chars) | ALLOW | ALLOW ✓ |
| ADV-13 | `pseudomineralization` | `"zation"` (6 chars) | REJECT | ALLOW ✗ |

Both candidates reach the same `non-suffix excess ≥ 3 chars → ALLOW` branch.
The branch gives the correct answer on ADV-11 (because `biomineralization`
happens to be a true cross-source umbrella) and the wrong answer on ADV-13
(because `pseudomineralization` is a source-local derivative whose excess
doesn't fit a suffix in the list). The distinguishing factor is the length
of the excess string, not any semantic property of the candidate.

This is parameter-tuning, not semantic analysis. The round-72 fix is not
adversarially robust; it is tuned to a specific test fixture. (Per round-74
wording correction: this is a statement about the current lexical detector,
not a universal theoretical claim about all possible lexical or symbolic
systems.)

---

## 2. Property definition — Independent Semantic Support (ISS)

### 2.1 The core definition

A candidate `c` has **independent semantic support from source `S`** if and
only if removing `S` from the corpus would make `c` unjustified — i.e. the
candidate's claim depends on content that only `S` asserts.

Formally, let `Justified(c, {A, B})` denote the proposition that `c` is a
justified inference from the corpus `{A, B}`. Then:

```
IndependentSemanticSupport(c, S, {A, B})  :=  Justified(c, {A, B})  AND  NOT Justified(c, {A, B} \ {S})
```

That is: `c` is justified by the full corpus, AND `c` would NOT be justified
if `S` were removed.

A candidate has independent semantic support from **both** sources iff:

```
ISS_both(c, {A, B})  :=  IndependentSemanticSupport(c, A, {A, B})  AND  IndependentSemanticSupport(c, B, {A, B})
```

A candidate has independent semantic support from **exactly one** source iff:

```
ISS_one(c, {A, B})  :=  (IndependentSemanticSupport(c, A, {A, B})  XOR  IndependentSemanticSupport(c, B, {A, B}))
```

A candidate has **redundant support** iff it is justified by the combined
corpus AND each source alone independently justifies it:

```
REDUNDANT_SUPPORT(c, {A, B})  :=  Justified(c, {A, B})
                                  AND  Justified(c, {A})
                                  AND  Justified(c, {B})
```

A candidate is **unsupported** iff it is NOT justified by the full corpus
(i.e. at least one atomic claim has no supporting span in either source,
alone or in combination):

```
UNSUPPORTED(c, {A, B})  :=  NOT Justified(c, {A, B})
```

**Critical distinction (round-76 condition, superseding round-75):** the
round-75 amendment introduced a state called `ISS_neither`, defined as
`Justified(c,{A,B}) AND NOT ISS_A AND NOT ISS_B`, and described it as
"genuinely novel relative to the sources, requiring both sources' combined
context but not attributable to either source alone." This description was
**mathematically inconsistent** with the operational `Justified()`
definition (Section 2.6.2, span-mapped to individual sources).

The inconsistency: under the span-map definition, `NOT ISS_A` means
"removing A does NOT make the candidate unjustified," which means B alone
is sufficient to justify the candidate. `NOT ISS_B` means A alone is
sufficient. So `ISS_neither` (as defined in round-75) was mathematically
equivalent to "both A alone and B alone independently justify the
candidate" — i.e. **redundant support**, not "jointly necessary but not
independently attributable." The "true ISS_neither" category (jointly
necessary, not independently attributable) was **non-constructible**
under the span-map definition, because the span-map cannot represent
joint inference that requires both sources together.

The round-76 amendment resolves this by eliminating `ISS_neither` and
renaming the state to `REDUNDANT_SUPPORT`, which accurately describes
what the mathematics actually computes. B-2 now has four clean,
mutually-exclusive, collectively-exhaustive, constructible states:

| State | Definition | Label |
|-------|-----------|-------|
| `UNSUPPORTED` | `NOT Justified(c,{A,B})` | `NOT_ADJUDICATED_BY_B2` |
| `ISS_one` | `Justified(c,{A,B})` AND exactly one of {`Justified(c,{A})`, `Justified(c,{B})`} | `REJECT` |
| `ISS_both` | `Justified(c,{A,B})` AND NOT `Justified(c,{A})` AND NOT `Justified(c,{B})` | `ALLOW` |
| `REDUNDANT_SUPPORT` | `Justified(c,{A,B})` AND `Justified(c,{A})` AND `Justified(c,{B})` | `ALLOW` (reported separately) |

- `ISS_one` (source-local leakage): the candidate is justified by the
  corpus, and one source alone is sufficient. The other source
  contributes nothing unique. REJECT.
- `ISS_both` (cross-source synthesis): the candidate is justified by
  the corpus, and neither source alone is sufficient — removing either
  source leaves the candidate unjustified. Both sources contribute
  unique supporting evidence. ALLOW.

  **Important (round-78, decoupling):** `ISS_both` is a property of the
  **candidate**, determined purely by the counterfactual test
  (`Justified(c,{A,B})` AND NOT `Justified(c,{A})` AND NOT
  `Justified(c,{B})`). It does NOT require any individual atomic claim
  to be supported by `JOINT_CROSS_SOURCE` evidence. The cross-source
  property can emerge from the **combination of independently supported
  atoms** (e.g. atom `a1` supported only by Source A, atom `a2`
  supported only by Source B — neither source alone justifies the whole
  candidate, so the candidate is `ISS_both`). `JOINT_CROSS_SOURCE` is
  one possible evidence path for an individual atomic claim (Section
  2.6.2), not a necessary condition for `ISS_both`. See Section 2.7 for
  the full decoupling.
- `REDUNDANT_SUPPORT`: the candidate is justified by the corpus, and
  each source alone independently justifies it. Both sources say the
  same thing about this candidate. ALLOW (reported separately for
  downstream transparency). This is NOT leakage (not source-local to
  one), and NOT cross-source synthesis (no unique contribution from
  either). It is simply a candidate that both sources independently
  support.
- `UNSUPPORTED`: the candidate contains at least one atomic claim with
  no supporting span in either source. NOT_ADJUDICATED_BY_B2
  (forwarded to Gate B).

**B-2 never has to decide whether something is "novel"** (round-76,
per auditor's directive). The responsibility for novelty adjudication
stays with the discovery gates (Gate B / Gate C). B-2 is a leakage AND
support instrument — it detects whether a candidate is source-local
(leakage) or unsupported (fabricated), and passes everything else
through to Gate B.

### 2.2 Source-local explainability

A candidate is **source-local explainable** iff it has independent semantic
support from exactly one source. This is the formalization of "the candidate
is fully derivable from one source alone, even if reworded, inflected, or
prefixed."

Source-local explainability is the **negation** of cross-source synthesis. A
source-local candidate does not perform the bridging work that B-2 requires.

### 2.3 Cross-source synthesis

A candidate performs **cross-source synthesis** iff it has independent
semantic support from both sources. The candidate's claim depends on content
from Source A AND content from Source B; removing either source leaves the
candidate unjustified.

Cross-source synthesis is the property B-2 is supposed to **permit**. A
candidate that performs cross-source synthesis is a legitimate discovery and
must be ALLOWED.

### 2.4 The decision criterion

The B-2 detector's decision criterion (round-76 amended to replace
non-constructible `ISS_neither` with `REDUNDANT_SUPPORT`):

```
                ┌─ REJECT                  if ISS_one(c, {A, B})             (source-local — leakage)
                ├─ ALLOW                   if ISS_both(c, {A, B})           (cross-source synthesis — both sources contribute uniquely)
detector(c) ───┼─ ALLOW                   if REDUNDANT_SUPPORT(c, {A, B})  (both sources independently justify — reported separately)
                └─ NOT_ADJUDICATED_BY_B2  if UNSUPPORTED(c, {A, B})        (contains claims not justified by either source — forwarded to Gate B)
```

Equivalently:

- REJECT iff the candidate has independent semantic support from exactly
  one source (source-local leakage; one source alone is sufficient, the
  other contributes nothing unique).
- ALLOW iff the candidate is justified by the combined corpus AND neither
  source alone is sufficient (cross-source synthesis; both sources
  contribute unique supporting spans).
- ALLOW iff the candidate is justified by the combined corpus AND each
  source alone independently justifies it (redundant support; both
  sources say the same thing). Reported separately from `ISS_both` for
  downstream transparency, but treated as ALLOW by B-2.
- NOT_ADJUDICATED_BY_B2 iff the candidate is NOT justified by the combined
  corpus (contains at least one unsupported atomic claim). B-2 does not
  issue an ALLOW or REJECT for such candidates; they are forwarded to
  Gate B for discovery adjudication.

This criterion is **counterfactual**: it requires evaluating whether the
candidate would still be justified if one source were removed. A lexical
detector cannot compute this counterfactual, because the counterfactual
depends on the candidate's *meaning*, not its surface form.

**Why REDUNDANT_SUPPORT is ALLOW (not REJECT or NOT_ADJUDICATED):**
`REDUNDANT_SUPPORT` is not leakage (the candidate is not source-local to
one source — both sources independently support it). It is also not
unsupported (the candidate IS justified by the corpus). B-2's job is to
detect leakage and unsupported claims; `REDUNDANT_SUPPORT` is neither.
Whether a redundantly-supported candidate is a "good invention" is Gate
B's responsibility. B-2 reports it separately from `ISS_both` so that
downstream gates can distinguish "cross-source synthesis" (unique
contribution from both) from "redundant support" (both say the same
thing) — these are scientifically different even though B-2 treats both
as ALLOW.

**Mathematical note (round-76):** the four states are mutually
exclusive and collectively exhaustive given the span-map definition of
`Justified()` (Section 2.6.2). Every candidate falls into exactly one
state. The previous round-75 `ISS_neither` state was non-constructible
under the span-map definition because it claimed to represent "jointly
necessary but not independently attributable" — which is actually
`ISS_both` under the span-map definition. See Section 2.1 for the full
derivation.

**Why UNSUPPORTED is not an ALLOW (round-75, retained):** the round-75
amendment closed the loophole where a candidate combining a legitimate
mechanism with an invented unsupported mechanism would be ALLOWED.
`UNSUPPORTED` candidates are forwarded to Gate B as
`NOT_ADJUDICATED_BY_B2`, NOT ALLOWED. B-2 is a leakage AND support
instrument; it must not quietly become a novelty detector that approves
fabricated candidates (Section 2.7, 8.5).

### 2.5 Worked examples (mapping the criterion to the adversarial set)

| Case | Candidate | ISS from A? | ISS from B? | Criterion | Label |
|------|-----------|-------------|-------------|-----------|-------|
| ADV-01 | `skeletal calcification process` | YES (paraphrases Source A's bone calcification) | NO | ISS_one | REJECT |
| ADV-02 | `calcified matrix in osseous structures` | YES (paraphrases Source A) | NO | ISS_one | REJECT |
| ADV-03 | `enzyme-templated mineral deposition` | YES (`mineral deposition` requires Source A's mineral system) | YES (`enzyme-templated` requires Source B's silicatein) | ISS_both | ALLOW |
| ADV-04 | `silicatein-guided calcification` | YES (`calcification` requires Source A's calcium phosphate) | YES (`silicatein-guided` requires Source B's enzyme) | ISS_both | ALLOW |
| ADV-05 | `hypermineralization` | YES (degree modifier on Source A's `mineralization`) | NO | ISS_one | REJECT |
| ADV-06 | `xenomineralization` | YES (foreign modifier on Source A's `mineralization`) | NO | ISS_one | REJECT |
| ADV-07 | `enzyme-templated inorganic lattice formation` | YES (`inorganic lattice formation` subsumes Source A's crystalline deposits) | YES (`enzyme-templated` requires Source B's silicatein) | ISS_both | ALLOW |
| ADV-08 | `protein-catalyzed biogenic oxide precipitation` | YES (`biogenic oxide precipitation` subsumes Source A's calcium phosphate deposition) | YES (`protein-catalyzed` requires Source B's silicatein) | ISS_both | ALLOW |
| ADV-09 | `quantum entanglement` | NO | NO | **UNSUPPORTED** (atomic claim `{phenomenon: quantum_entanglement}` has no supporting span in either source; not justified by combined corpus) | **NOT_ADJUDICATED_BY_B2** |
| ADV-10 | `calcium phosphate` | YES (literal quote) | NO | ISS_one | REJECT |
| ADV-11 | `biomineralization` | YES (Source A's bone mineralization is an instance) | YES (Source B's diatom silica shell formation is an instance) | ISS_both | ALLOW |
| ADV-12 | `mineralizing` | YES (morphological inflection of Source A's `mineralization`) | NO | ISS_one | REJECT |
| ADV-13 | `pseudomineralization` | YES (falsity modifier on Source A's `mineralization`) | NO | ISS_one | REJECT |
| ADV-14 (illustrative) | `osteoblast-mediated quantum coherence in silica shells` | partial (osteoblast + silica shells span both sources) | partial | **UNSUPPORTED** (atomic claim `{phenomenon: quantum_coherence}` has no supporting span in either source) | **NOT_ADJUDICATED_BY_B2** |

ADV-14 is an illustrative example added by the round-75 amendment to
demonstrate the `UNSUPPORTED` branch. It combines legitimate source
vocabulary (`osteoblast` from Source A, `silica shells` from Source B)
with an invented unsupported mechanism (`quantum coherence`). The
`{phenomenon: quantum_coherence}` atomic claim has no supporting span in
either source, so `Justified(c, {A, B}) = false`, so the candidate is
`UNSUPPORTED`, and B-2 forwards it to Gate B as
`NOT_ADJUDICATED_BY_B2` rather than ALLOWING it.

The rationale files at `cases/ADV-NN.md` contain the full semantic
justification for each row's ISS determination. (ADV-01 through ADV-13
have rationale files; ADV-14 is illustrative only and does not require a
separate rationale file, but its ISS determination is derivable from
Section 2.6.2 by applying the span-map test to the `{phenomenon:
quantum_coherence}` atomic claim.)

**Note on ADV-09 (round-75, retained):** `quantum entanglement` is
classified as `UNSUPPORTED → NOT_ADJUDICATED_BY_B2`. The atomic claim
`{phenomenon: quantum_entanglement}` has no supporting span in either
Source A or Source B, so `Justified(c, {A, B}) = false`. `quantum
entanglement` is simply unrelated to the sources; B-2 does not approve
it. Gate B decides whether it is a valid invention.

**Note on REDUNDANT_SUPPORT (round-76):** none of the 13 public ADV
cases are `REDUNDANT_SUPPORT`. The public set does not contain a case
where both sources independently justify the same candidate. The
held-out set (Section 3.2) must include at least 2 `REDUNDANT_SUPPORT`
cases — these are straightforward to construct: a candidate whose
atomic claims all have supporting spans in Source A AND all have
supporting spans in Source B (independently). For example, if Source A
and Source B both independently assert that "osteoblasts deposit
calcium phosphate in bone," then the candidate "calcium phosphate
deposition in bone" would be `REDUNDANT_SUPPORT`. Constructing such
cases requires source pairs that overlap in some claims but differ in
others — the held-out set's multiple source pairs (Section 3.2.1)
should be designed with this in mind.

**Note on the removed `ISS_neither` state (round-76):** the round-75
amendment introduced `ISS_neither` and reclassified ADV-09 from
`ISS_neither → ALLOW` to `UNSUPPORTED → NOT_ADJUDICATED_BY_B2`. The
round-76 amendment eliminates `ISS_neither` entirely (it was
non-constructible under the span-map definition of `Justified()`).
ADV-09 remains `UNSUPPORTED → NOT_ADJUDICATED_BY_B2` (unchanged from
round-75). No reclassification of ADV-09 is needed for round-76; the
only change is that the `ISS_neither` state no longer exists as a
target for any candidate. See Section 2.1 for the mathematical
derivation of why `ISS_neither` was non-constructible.

**Note on `JOINT_CROSS_SOURCE` support for cross-source synthesis cases
(round-77, NEW):** the cross-source synthesis cases (ADV-03, ADV-04,
ADV-07, ADV-08, ADV-11) each contain a relation atom that is not
asserted by either source alone but emerges from their combination.
Under the round-76 spec, these relation atoms would have been
misclassified as `UNSUPPORTED` (the contradiction the round-77
amendment resolves). Under the round-77 amended spec, these relation
atoms are supported by `JOINT_CROSS_SOURCE` entries:

- **ADV-03** `enzyme-templated mineral deposition`: the relation
  `enzyme_templates_mineral_deposition` is supported by A-spans for
  mineral deposition + B-spans for enzyme/silicatein, derived via the
  inference rule "composition" (enzyme catalyst applied to mineral
  deposition process).
- **ADV-04** `silicatein-guided calcification`: the relation
  `silicatein_guides_calcification` is supported by A-spans for
  calcification + B-spans for silicatein, derived via "causal
  attribution."
- **ADV-07** `enzyme-templated inorganic lattice formation`: the
  relation is supported by A-spans for inorganic lattice formation +
  B-spans for enzyme-templating, derived via "composition."
- **ADV-08** `protein-catalyzed biogenic oxide precipitation`: the
  relation is supported by A-spans for biogenic oxide precipitation +
  B-spans for protein catalysis, derived via "causal attribution."
- **ADV-11** `biomineralization`: the relation
  `biological_mineral_deposition` is supported by A-spans for bone
  mineralization + B-spans for diatom silica shell formation, derived
  via "abstraction" (both are instances of biologically-controlled
  mineral deposition).

The `inference_rule` values above ("composition," "causal attribution,"
"abstraction") are illustrative, not prescriptive. The taxonomy of
permitted inference rules is an open question (Section 9.12).

### 2.6 Operational definition of `Justified()` (round-74 condition 1)

The counterfactual definition of ISS in Section 2.1 relies on a `Justified()`
predicate. If the implementation is allowed to decide for itself what counts
as "justified," the ambiguity has merely moved one level down: an LLM could
generate a persuasive explanation for its own decision, and the system would
have produced a coherent false explanation rather than an adjudication. This
section gives an independent operational definition.

#### 2.6.1 Atomic claim decomposition

A candidate `c` is decomposed into a set of **atomic claims** `Atoms(c)`. An
atomic claim is a single predicate-argument assertion that cannot be further
decomposed without loss of meaning. For example:

- `enzyme-templated mineral deposition` →
  - `{process: mineral_deposition}`
  - `{mediator: enzyme_catalyst}`
  - `{relation: enzyme_templates_mineral_deposition}`
- `silicatein-guided calcification` →
  - `{process: calcification}`
  - `{mediator: silicatein}`
  - `{relation: silicatein_guides_calcification}`

The decomposition is part of the detector's output (Section 3.3, element 1).
The auditor must be able to inspect the decomposition and confirm that each
atom is a meaningful claim about the candidate's content. A decomposition
that is materially incomplete (e.g. omits a key relation) or materially
inflated (e.g. adds atoms not present in the candidate) is grounds for
rejection of the trace.

#### 2.6.2 Span-mapped evidence (round-77 amended: two support types)

A candidate `c` is `Justified(c, corpus)` iff **every** atomic claim in
`Atoms(c)` has at least one **support entry** in the corpus.

A **support entry** is one of two types (round-77 amendment):

**Type 1: `SOURCE_LOCAL` support.** A `SOURCE_LOCAL` support entry for
atomic claim `a` in source `S` is a contiguous substring of `S` that an
independent adjudicator can identify as asserting `a` (either literally
or via standard scientific inference — synonymy, hypernymy, or direct
implication). The supporting span is recorded as a character-offset
range `(start, end)` into `S`.

**Type 2: `JOINT_CROSS_SOURCE` support (round-77, NEW).** A
`JOINT_CROSS_SOURCE` support entry for atomic claim `a` is a structured
derivation in which:

- one or more spans from Source A support a **component** `a_A`,
- one or more spans from Source B support a **component** `a_B`,
- the atomic claim `a` is the **derived claim** that follows from
  combining `a_A` and `a_B` under a stated **inference rule**,
- neither Source A alone nor Source B alone asserts `a`.

`JOINT_CROSS_SOURCE` support is the mechanism that represents
**cross-source synthesis relations** — the new relationships that emerge
from combining capabilities in Source A and Source B, which neither
source asserts independently. This is the type of support that
distinguishes a genuine cross-source invention (which should be
`ISS_both → ALLOW`) from a fabricated claim (which should be
`UNSUPPORTED → NOT_ADJUDICATED_BY_B2`).

**Why `JOINT_CROSS_SOURCE` is necessary (round-77 condition):**
without it, the span-map definition of `Justified()` cannot represent
the relation atom in a cross-source synthesis. For example, the
candidate `enzyme-templated mineral deposition` has atoms:

```
a1 = {process: mineral_deposition}         → SOURCE_LOCAL(A)
a2 = {mediator: enzyme_catalyst}           → SOURCE_LOCAL(B)
a3 = {relation: enzyme_templates_mineral_deposition}  → ???
```

The relation `a3` is not asserted by Source A (which describes
osteoblast-mediated mineralization, not enzyme-templated
mineralization). It is not asserted by Source B (which describes
silicatein-mediated silica precipitation, not mineral deposition).
It is the new relationship created by combining the enzyme concept
from Source B with the mineral deposition concept from Source A.

Under the round-76 spec (without `JOINT_CROSS_SOURCE`), `a3` has no
supporting span in either source → `UNSUPPORTED` →
`NOT_ADJUDICATED_BY_B2`. But the candidate should be `ISS_both →
ALLOW`. This is the contradiction the round-77 amendment resolves.

With `JOINT_CROSS_SOURCE` support, `a3` is supported by:

```
source_a_spans: [spans supporting mineral_deposition]
source_b_spans: [spans supporting enzyme_catalyst / silicatein]
derived_claim: enzyme_templates_mineral_deposition
inference_rule: composition (enzyme catalyst applied to mineral deposition process)
```

Neither source alone asserts the derived claim; both sources together
support it via the stated inference rule.

**Critical boundary (round-77):** `JOINT_CROSS_SOURCE` support is NOT
a license for the detector to claim "the LLM thinks A and B together
imply the relation." That would recreate the exact problem the prior
rounds eliminated. `JOINT_CROSS_SOURCE` support is an **auditable
structure** with mandatory fields and mandatory adjudicator
verification (Section 2.6.7).

Concretely, the detector's trace must include, for each atomic claim:

- the claim itself (e.g. `{relation: enzyme_templates_mineral_deposition}`),
- a list of support entries, each with:
  - `support_type`: `SOURCE_LOCAL` or `JOINT_CROSS_SOURCE`
  - for `SOURCE_LOCAL`: the source (`A` or `B`), the supporting span
    as a verbatim quote, the character offsets `(start, end)`
  - for `JOINT_CROSS_SOURCE`: the `source_a_spans`, `source_b_spans`,
    `derived_claim`, `inference_rule`, `counterfactual_a`,
    `counterfactual_b` (full structure in Section 2.6.7 and Section 3.7)

A claim with no support entry of either type is **unsupported**. A
candidate with any unsupported atomic claim is `NOT Justified(c,
{A, B})`, which (per Section 2.4) places it in `UNSUPPORTED` and yields
`NOT_ADJUDICATED_BY_B2` — the candidate is forwarded to Gate B for
discovery adjudication, NOT allowed as a B-2 pass.

**Critical (round-75 condition 1, round-76 finalized, round-77
extended):** the round-74 version of this section (commit `4bc945d`)
said an unsupported candidate "places it in `ISS_neither` and yields
ALLOW." That was the loophole the round-75 amendment closed by
introducing `UNSUPPORTED` as a separate state. The round-76 amendment
eliminated the non-constructible `ISS_neither` and replaced it with
`REDUNDANT_SUPPORT`. The round-77 amendment adds `JOINT_CROSS_SOURCE`
support so that cross-source synthesis relations are representable
(rather than being misclassified as `UNSUPPORTED`). Under the current
(round-77) criterion, an unsupported candidate is `UNSUPPORTED` (NOT
`REDUNDANT_SUPPORT`, NOT `ISS_both`, NOT `ISS_one`).

#### 2.6.3 The counterfactual test, operationalized (round-77 amended for joint support)

With `Justified()` defined via support entries (Section 2.6.2), the
counterfactual `NOT Justified(c, {A, B} \ {S})` becomes operationally
testable:

> Remove source `S` from the corpus. Re-evaluate every atomic claim in
> `Atoms(c)`. For each atomic claim, check whether it still has at least
> one support entry that survives the removal. A `SOURCE_LOCAL(S)`
> entry is destroyed by removing `S`. A `SOURCE_LOCAL(other)` entry
> survives. A `JOINT_CROSS_SOURCE` entry is destroyed by removing
> **either** source (because joint support requires both). If any atomic
> claim has no surviving support entry, then `c` is NOT justified by
> `{A, B} \ {S}` — i.e. `c` has independent semantic support from `S`.

**Support entry survival matrix (round-77):**

| Support entry type | Remove A | Remove B |
|--------------------|----------|----------|
| `SOURCE_LOCAL(A)` | destroyed | survives |
| `SOURCE_LOCAL(B)` | survives | destroyed |
| `JOINT_CROSS_SOURCE` | destroyed | destroyed |

An atomic claim is **unsupported without `S`** iff ALL of its support
entries are destroyed by removing `S`. For example:

- An atom with only `SOURCE_LOCAL(A)` support → unsupported without A,
  supported without B.
- An atom with only `JOINT_CROSS_SOURCE` support → unsupported without
  A AND unsupported without B.
- An atom with both `SOURCE_LOCAL(A)` and `SOURCE_LOCAL(B)` support →
  supported without A (via B) AND supported without B (via A). This
  atom contributes to `REDUNDANT_SUPPORT` classification.
- An atom with `SOURCE_LOCAL(A)` and `JOINT_CROSS_SOURCE` support →
  unsupported without A (both entries destroyed), supported without B
  (via the local A entry).

The detector's trace must include, for each source `S`:

- the set of atomic claims supported by `S` (via `SOURCE_LOCAL(S)` or
  `JOINT_CROSS_SOURCE`),
- the set of atomic claims supported by the other source,
- the set of atomic claims that become unsupported when `S` is removed
  (all support entries destroyed),
- the set of atomic claims supported by neither source (unsupported
  even with both sources present),
- the counterfactual verdict: "removing `S` would leave claims {…}
  unsupported, therefore `c` is [NOT] justified by `{A,B}\{S}`."

**Why this matters for `ISS_both` (round-77):** a candidate is `ISS_both`
iff `Justified(c,{A,B})` is true AND removing A leaves it unjustified
AND removing B leaves it unjustified. This requires at least one atomic
claim that is unsupported without A, AND at least one atomic claim that
is unsupported without B. `JOINT_CROSS_SOURCE` entries are the primary
mechanism by which this happens for cross-source synthesis: the
relation atom (e.g. `enzyme_templates_mineral_deposition`) is destroyed
by removing either source, making the candidate `ISS_both`.

#### 2.6.4 Independent adjudication of the support map (round-77 amended for joint support)

The support map is the detector's **claimed** evidence. It is not proof. The
auditor (or an independent adjudicator) must verify, for each atomic claim
in a held-out case, that:

**For `SOURCE_LOCAL` support entries:**

1. The supporting span is actually present in the cited source at the cited
   offsets.
2. The supporting span actually asserts the atomic claim (i.e. the
   claim-to-span mapping is semantically valid).

**For `JOINT_CROSS_SOURCE` support entries (round-77, NEW):**

3. The `source_a_spans` are actually present in Source A at the cited
   offsets.
4. The `source_b_spans` are actually present in Source B at the cited
   offsets.
5. Source A genuinely supports the A-component of the derivation (i.e.
   the spans assert what the detector claims they assert).
6. Source B genuinely supports the B-component of the derivation.
7. The `derived_claim` actually follows from combining the A-component
   and the B-component under the stated `inference_rule`. (The
   adjudicator's judgment applies; the permitted inference rules are
   an open question — see Section 9.12.)
8. Neither Source A alone nor Source B alone asserts the `derived_claim`.
   (If either source independently asserts the derived claim, the
   support entry should be `SOURCE_LOCAL`, not `JOINT_CROSS_SOURCE`.)
9. Removing either source destroys the justification (i.e. the
   `counterfactual_a` and `counterfactual_b` fields correctly identify
   the derived claim as unsupported without the respective source).

**For all support entries:**

10. No atomic claim has been silently dropped or fabricated.
11. Every atomic claim has at least one support entry, OR is explicitly
    listed as unsupported in the counterfactual evaluation.

A trace whose support map fails verification on any atomic claim is rejected,
regardless of the detector's label. This is the operational mechanism that
prevents the detector from generating coherent false explanations
(Section 3.5) — including false `JOINT_CROSS_SOURCE` derivations that
manufacture a plausible "A + B = invention" explanation without genuine
cross-source support.

#### 2.6.5 What this rules out

This operational definition rules out:

- **Persuasive-only explanations.** A trace that says "Source A supports
  mineral deposition because…" without citing a specific span is rejected.
- **Fabricated spans.** A trace that cites a span not present in the source
  is rejected.
- **Semantic overreach.** A trace that maps an atomic claim to a span that
  does not actually assert it (e.g. mapping `{mediator: enzyme_catalyst}`
  to a span that mentions `osteoblasts` but not enzymes) is rejected.
- **Silent decomposition gaps.** A trace that omits an atomic claim to
  avoid an unsupported-claim flag is rejected.
- **False `JOINT_CROSS_SOURCE` derivations (round-77, NEW).** A trace
  that claims `JOINT_CROSS_SOURCE` support for a derived claim that
  does not actually follow from the A and B components under the stated
  inference rule is rejected. A trace that claims
  `JOINT_CROSS_SOURCE` support when one of the sources independently
  asserts the derived claim (i.e. it should be `SOURCE_LOCAL`) is
  rejected. A trace that cites `JOINT_CROSS_SOURCE` support without
  specifying the `inference_rule` is rejected.

#### 2.6.6 What this does NOT rule out

This operational definition does not rule out:

- **Synonymy and hypernymy in span mapping.** The supporting span may
  assert the atomic claim via synonymy (`skeletal` ↔ `bone`) or hypernymy
  (`enzyme` ↔ `silicatein`). The adjudicator's judgment applies.
- **Multi-span support within a single source.** An atomic claim may be
  supported by the conjunction of two spans in the same source (e.g. one
  span asserting the substrate, another asserting the mediator). The
  trace must cite both spans. (This is a `SOURCE_LOCAL` entry with
  multiple spans; the schema in Section 3.7 supports this via a list of
  spans per support entry.)
- **Inference from context.** An atomic claim may be supported by the
  source's overall context rather than a single sentence. The adjudicator's
  judgment applies, but the trace must still cite the specific spans that
  ground the inference.
- **Cross-source synthesis relations (round-77, NEW).** An atomic claim
  that represents a relationship emerging from the combination of Source
  A and Source B (e.g. `enzyme_templates_mineral_deposition`) may be
  supported by a `JOINT_CROSS_SOURCE` entry. This is the primary
  mechanism for representing cross-source invention. The trace must
  include the full joint-support structure (Section 2.6.7).

#### 2.6.7 `JOINT_CROSS_SOURCE` support structure and anti-cheating conditions (round-77, NEW)

A `JOINT_CROSS_SOURCE` support entry must contain the following fields,
all mandatory:

```
{
  "support_type": "JOINT_CROSS_SOURCE",
  "source_a_spans": [
    { "span_text": "<verbatim substring of Source A>",
      "start": <integer>,
      "end": <integer> }
  ],
  "source_b_spans": [
    { "span_text": "<verbatim substring of Source B>",
      "start": <integer>,
      "end": <integer> }
  ],
  "derived_claim": "<the atomic claim that follows from combining A and B>",
  "inference_rule": "<the rule under which the derivation is valid>",
  "counterfactual_a": "<why removing Source A leaves derived_claim unsupported>",
  "counterfactual_b": "<why removing Source B leaves derived_claim unsupported>"
}
```

**Mandatory anti-cheating conditions (round-77):**

The adjudicator must verify ALL of the following for every
`JOINT_CROSS_SOURCE` entry (per Section 2.6.4, items 3-9):

1. **A genuinely supports its component.** The `source_a_spans` are
   present in Source A at the cited offsets and assert what the detector
   claims they assert.
2. **B genuinely supports its component.** The `source_b_spans` are
   present in Source B at the cited offsets and assert what the detector
   claims they assert.
3. **The derived claim actually follows from the combination.** The
   `derived_claim` is a valid inference from the A-component and
   B-component under the stated `inference_rule`. The adjudicator's
   judgment applies; the permitted inference rules are an open question
   (Section 9.12).
4. **Neither source alone supports the complete relation.** Neither
   Source A nor Source B independently asserts the `derived_claim`. If
   either source does, the support entry should be `SOURCE_LOCAL`, not
   `JOINT_CROSS_SOURCE`.
5. **Removing either source destroys the justification.** The
   `counterfactual_a` and `counterfactual_b` fields correctly identify
   the derived claim as unsupported without the respective source.

**Why these conditions are mandatory:** without them, an LLM-based
detector could manufacture a plausible "A + B = invention" explanation
for any candidate — citing real spans from A and B, claiming a
derivation, and asserting `JOINT_CROSS_SOURCE` support. This would
recreate the exact problem the prior rounds eliminated: a coherent
false explanation accepted as evidence. The five conditions above are
the operational mechanism that prevents this.

**Boundary between B-2 and Gate B (round-77 clarified):**

`JOINT_CROSS_SOURCE` support establishes **provenance topology**: the
candidate's relation is genuinely derived from both sources, not
fabricated. This is what B-2 adjudicates.

Whether the derived relation is a **valid mechanism or invention** —
i.e. whether it is scientifically meaningful, testable, and non-obvious
— is **Gate B's responsibility**, not B-2's. B-2 does not evaluate
whether the `inference_rule` produces a "good" invention; it evaluates
whether the `inference_rule` is honestly applied to real evidence from
both sources.

This preserves the B-2 / Gate B separation (Section 2.7): B-2
establishes provenance topology; Gate B establishes discovery validity.

#### 2.6.8 Frozen inference-rule taxonomy (round-78, NEW)

The `inference_rule` field in `JOINT_CROSS_SOURCE` entries (Section
2.6.7) must use a value from the **frozen taxonomy** below. Free-form
values are NOT permitted. This is mandatory because
`JOINT_CROSS_SOURCE` is decision-critical (it can establish `ISS_both`
via pathway 2 in Section 2.7); an uncontrolled `inference_rule` field
would create a "semantic-rule tuning" optimization surface — the
detector could emit any plausible-sounding rule label to justify a
derivation, and the system would have delegated the definition of
valid cross-source inference to the LLM/adjudicator.

**Frozen taxonomy (version `inference-rules-v1`, round-78):**

| Rule | Definition | Admissibility criteria |
|------|-----------|----------------------|
| `COMPOSITION` | The derived claim combines a process/capability from one source with a substrate/mediator from the other, asserting that the process applies to the substrate. | (1) Source A asserts process/capability P; (2) Source B asserts substrate/mediator M (or vice versa); (3) the derived claim asserts "P applied to M"; (4) neither source alone asserts "P applied to M". |
| `ABSTRACTION` | The derived claim identifies a shared abstract category that subsumes specific instances in both sources. | (1) Source A asserts instance I_A of category C; (2) Source B asserts instance I_B of category C; (3) the derived claim asserts C as a unifying concept; (4) neither source alone asserts C as a unifying concept (only its own instance). |
| `SPECIALIZATION` | The derived claim applies a general principle from one source to a specific case identified in the other. | (1) Source A asserts general principle G; (2) Source B asserts specific case S (or vice versa); (3) the derived claim asserts "G applied to S"; (4) neither source alone asserts "G applied to S". |
| `GENERALIZATION` | The derived claim generalizes from two specific instances (one per source) to a broader rule. | (1) Source A asserts specific instance I_A; (2) Source B asserts specific instance I_B; (3) the derived claim asserts a general rule R subsuming both; (4) neither source alone asserts R. |
| `CAUSAL_TRANSFER` | The derived claim transfers a causal mechanism from one source to a system described in the other. | (1) Source A asserts causal mechanism M causes effect E in system S_A; (2) Source B describes system S_B (or vice versa); (3) the derived claim asserts "M causes E in S_B"; (4) neither source alone asserts the transfer. |
| `MECHANISTIC_ANALOGY` | The derived claim asserts that a mechanism in one source is structurally analogous to a mechanism in the other, supporting a transferred claim. | (1) Source A describes mechanism M_A with structure S_A; (2) Source B describes mechanism M_B with structure S_B; (3) S_A and S_B share a structural isomorphism; (4) the derived claim asserts M_A and M_B are mechanistically analogous; (5) neither source alone asserts the analogy. |
| `STRUCTURAL_ANALOGY` | The derived claim asserts a structural correspondence between entities/processes in the two sources. | (1) Source A describes entity/process E_A with structural features F_A; (2) Source B describes E_B with F_B; (3) F_A and F_B share a structural correspondence; (4) the derived claim asserts the correspondence; (5) neither source alone asserts it. |
| `FUNCTIONAL_ANALOGY` | The derived claim asserts a functional correspondence (similar role/function) between entities/processes in the two sources. | (1) Source A describes E_A serving function F; (2) Source B describes E_B serving function F (or a functionally equivalent F'); (3) the derived claim asserts E_A and E_B are functionally analogous; (4) neither source alone asserts the analogy. |
| `OTHER` | The derivation does not fit any of the above rules. | (1) The detector must provide a free-text `inference_rule_other` explanation; (2) the entry is flagged `UNCLASSIFIED_INFERENCE`; (3) **cannot automatically qualify as a B-2 pass** — requires independent adjudication; (4) reported separately in the audit. |

**Examples (illustrative, mapped to public ADV cases):**

- ADV-03 `enzyme-templated mineral deposition`: `COMPOSITION`
  (enzyme catalyst from B applied to mineral deposition from A).
- ADV-04 `silicatein-guided calcification`: `CAUSAL_TRANSFER`
  (silicatein causal mechanism from B transferred to calcification system from A).
- ADV-07 `enzyme-templated inorganic lattice formation`: `COMPOSITION`
  + `ABSTRACTION` (enzyme-templating from B composed with inorganic
  lattice formation, which abstracts over both sources' mineral systems).
  If a single rule must be chosen, `COMPOSITION` is primary.
- ADV-08 `protein-catalyzed biogenic oxide precipitation`: `ABSTRACTION`
  (biogenic oxide precipitation abstracts over calcium phosphate and
  silica; protein-catalyzed from B).
- ADV-11 `biomineralization`: `ABSTRACTION`
  (both sources' processes are instances of biologically-controlled
  mineral deposition).

**Adversarial counterexamples (what each rule does NOT justify):**

- `COMPOSITION` does NOT justify a claim where the process and substrate
  come from the same source (that would be `SOURCE_LOCAL`).
- `ABSTRACTION` does NOT justify a claim so abstract it loses specific
  content from both sources (that would be `UNSUPPORTED` — the
  abstract claim is not asserted by either source).
- `CAUSAL_TRANSFER` does NOT justify transferring a mechanism to a
  system where it is already known to apply (that would be
  `REDUNDANT_SUPPORT` if both sources assert it).
- `MECHANISTIC_ANALOGY` / `STRUCTURAL_ANALOGY` / `FUNCTIONAL_ANALOGY`
  do NOT justify a claim based on superficial similarity without a
  genuine structural/functional correspondence. The adjudicator
  verifies the correspondence is real, not asserted.
- `OTHER` does NOT automatically justify anything. It routes the entry
  to independent adjudication.

**Treatment of `OTHER` (round-78, critical):**

`OTHER` is NOT an automatic pass. When the detector emits
`inference_rule = "OTHER"`:

1. The entry is flagged `UNCLASSIFIED_INFERENCE` in the trace.
2. The entry CANNOT automatically qualify the `JOINT_CROSS_SOURCE`
   claim as valid support. The atom is treated as **provisionally
   unsupported** pending independent adjudication.
3. The independent adjudicator (Section 3.6) must review the
   `inference_rule_other` explanation and determine whether the
   derivation is valid under a rule that should be added to the
   taxonomy in a future revision.
4. If the adjudicator approves, the entry is marked
   `ADJUDICATED_OTHER` and the atom is supported. If not, the atom
   is unsupported.
5. `OTHER` entries are reported separately in the audit. A detector
   that emits `OTHER` for more than 20% of its `JOINT_CROSS_SOURCE`
   entries is flagged for review — the taxonomy may be incomplete,
   or the detector may be using `OTHER` as an escape hatch.

**Why this taxonomy is frozen:**

Without a frozen taxonomy, the detector could emit any
plausible-sounding `inference_rule` label ("conceptual transfer,"
"semantic bridging," "cross-domain unification," etc.) to justify a
derivation. The adjudicator would have no principled basis to reject
these labels, and the system would have delegated the definition of
valid cross-source inference to the LLM. The frozen taxonomy ensures
that the detector's derivations are evaluated against a fixed,
auditor-approved set of rules with explicit admissibility criteria.

The taxonomy is versioned (`inference-rules-v1`). Future revisions
require a new version number, a new adjudication cycle, and
re-verification of all held-out results.

#### 2.6.9 Verification ordering — classification is not validity (round-79, NEW)

**Critical principle (round-79):** the inference taxonomy is a
**classification ontology**, NOT an **inference engine**. Selecting
`COMPOSITION`, `ABSTRACTION`, `CAUSAL_TRANSFER`, etc. must **never
itself imply that the derived claim is true**.

The taxonomy labels the *type* of inference the detector claims to be
performing. It does NOT establish that the inference is valid. A
detector that emits `inference_rule = "COMPOSITION"` has only
*classified* its derivation; it has not *proven* the derivation. The
adjudicator must independently verify that the derived claim actually
follows under the stated rule.

**Mandatory verification ordering (round-79, normative):**

For every `JOINT_CROSS_SOURCE` support entry, the adjudicator must
execute the following 8-step sequence **in order**. Each step must
pass before the next is evaluated. Failure at any step rejects the
support entry (the atom is treated as unsupported).

```
Step 1: Identify inference_rule
        — Confirm the entry's inference_rule field is from the frozen
          taxonomy (Section 2.6.8). If OTHER, flag
          UNCLASSIFIED_INFERENCE and route to independent adjudication
          (cannot auto-qualify).

Step 2: Verify rule admissibility conditions
        — Confirm the entry satisfies the admissibility criteria for
          the stated rule (Section 2.6.8 table). E.g. for COMPOSITION:
          Source A asserts process/capability P, Source B asserts
          substrate/mediator M (or vice versa), the derived claim
          asserts "P applied to M", neither source alone asserts
          "P applied to M".

Step 3: Verify A-component evidence
        — Confirm source_a_spans are present in Source A at the cited
          offsets and actually assert the A-component.

Step 4: Verify B-component evidence
        — Confirm source_b_spans are present in Source B at the cited
          offsets and actually assert the B-component.

Step 5: Independently judge whether the derived claim actually follows
        under the stated rule
        — The adjudicator independently evaluates: given the A-component
          and B-component as verified in steps 3-4, does the
          derived_claim actually follow under the inference_rule
          verified in step 2? This is a semantic judgment, NOT a
          mechanical check. The adjudicator must NOT accept the
          detector's assertion that the derivation is valid; the
          adjudicator must independently confirm it.

Step 6: Verify neither source independently asserts the complete
        derived claim
        — Confirm the derived_claim is NOT asserted by Source A alone
          and NOT asserted by Source B alone. If either source
          independently asserts it, the support entry should be
          SOURCE_LOCAL, not JOINT_CROSS_SOURCE.

Step 7: Verify counterfactual destruction
        — Confirm counterfactual_a (removing Source A leaves
          derived_claim unsupported) and counterfactual_b (removing
          Source B leaves derived_claim unsupported) are correct.

Step 8: Only then accept JOINT_CROSS_SOURCE support
        — If and only if all 7 preceding steps pass, the
          JOINT_CROSS_SOURCE entry is accepted as valid support for
          the atom. The atom is supported.
```

**Why the ordering is mandatory (round-79):**

Without this explicit ordering, an implementation could effectively
do:

```
LLM: "This looks like COMPOSITION."
       ↓
COMPOSITION accepted
       ↓
derived claim accepted
```

That would recreate the exact semantic-leakage problem this
specification is trying to eliminate. The frozen taxonomy prevents
the detector from inventing rule labels, but it does NOT prevent the
detector from misapplying a real label. Step 5 (independent judgment
that the derived claim actually follows) is the operational mechanism
that prevents misapplication.

**Relationship to existing requirements:**

This ordering consolidates requirements already present in §2.6.4
(adjudicator verification) and §2.6.7 (anti-cheating conditions) into
a single normative sequence. The consolidation is necessary because
the taxonomy is now frozen and decision-critical — the ordering must
be an explicit normative requirement rather than something inferred
from several sections.

**Anti-regression (Section 8.5):** any implementation that accepts a
`JOINT_CROSS_SOURCE` entry without executing all 8 steps in order is
non-compliant. Specifically, accepting an entry based solely on
`inference_rule` classification (steps 1-2) without independent
judgment of derivation validity (step 5) is a critical regression
and must be rejected by the auditor.

### 2.7 B-2 establishes provenance topology, Gate B establishes discovery validity (round-74 condition 7; round-75 strengthened; round-76 finalized; round-77 clarified; round-78 decoupled)

The B-2 decision criterion (Section 2.4, round-76 amended, round-77
extended with `JOINT_CROSS_SOURCE` support) has four states: `ISS_one`
(REJECT), `ISS_both` (ALLOW), `REDUNDANT_SUPPORT` (ALLOW, reported
separately), and `UNSUPPORTED` (NOT_ADJUDICATED_BY_B2).

B-2's job is to establish **provenance topology** — i.e. to classify
the candidate's relationship to the sources:

- **source-local leakage** (`ISS_one`): the candidate is fully
  attributable to one source. REJECT.
- **cross-source synthesis** (`ISS_both`): the candidate is justified
  by the corpus, AND removing either source leaves the candidate
  unjustified. Both sources contribute unique supporting evidence.
  ALLOW.

  **Round-78 decoupling (critical):** `ISS_both` is determined purely
  by the counterfactual test on the **candidate** — it does NOT require
  any individual atomic claim to be supported by `JOINT_CROSS_SOURCE`
  evidence. The cross-source property can emerge in two ways:
  1. **Combination of independently supported atoms:** atom `a1`
     supported only by Source A, atom `a2` supported only by Source B.
     Neither source alone justifies the whole candidate (each is
     missing the other's atom), so the candidate is `ISS_both`. No
     `JOINT_CROSS_SOURCE` evidence is needed.
  2. **Joint cross-source evidence for a relation atom:** atom `a3`
     (a relation) supported by `JOINT_CROSS_SOURCE` evidence combining
     A-spans and B-spans. Removing either source destroys `a3`, so the
     candidate is `ISS_both`.

  Both pathways yield `ISS_both`. `JOINT_CROSS_SOURCE` is one possible
  evidence path for an atomic claim, not a necessary condition for
  `ISS_both`. The key principle: **evidence type determines how an
  atomic claim is supported; counterfactuals determine the candidate's
  ISS state.** Do not conflate those two levels.

- **redundant support** (`REDUNDANT_SUPPORT`): both sources
  independently justify the candidate (all claims have `SOURCE_LOCAL`
  support from both sources). ALLOW (reported separately).
- **unsupported claims** (`UNSUPPORTED`): the candidate contains at
  least one atomic claim with no support entry of any type
  (`SOURCE_LOCAL` or `JOINT_CROSS_SOURCE`). Forward to Gate B as
  `NOT_ADJUDICATED_BY_B2`.

B-2 does NOT adjudicate:

- whether a candidate is a "good invention" (Gate B's job)
- whether a candidate is "novel" (Gate B's job)
- whether a candidate is "scientifically meaningful" (Gate B's job)
- whether a `JOINT_CROSS_SOURCE` derivation produces a "valid"
  mechanism (Gate B's job — B-2 only verifies the derivation is
  honestly applied to real evidence, per Section 2.6.7)

B-2 must remain distinct from **discovery adjudication** (Gate B /
Gate C in the engine's gate hierarchy). The two gates evaluate
different properties:

| Gate | Question | Outcome |
|------|----------|---------|
| B-2 (this spec) | What is the candidate's provenance topology? (source-local / cross-source synthesis / redundant / unsupported) | REJECT iff `ISS_one`; ALLOW iff `ISS_both` or `REDUNDANT_SUPPORT`; `NOT_ADJUDICATED_BY_B2` iff `UNSUPPORTED` |
| Gate B / discovery | Is the candidate a valid, meaningful mechanism? (is the jointly-supported relationship actually a valid invention?) | Separate adjudication, separate criteria |

A candidate that passes B-2 via `ISS_both` (cross-source synthesis,
determined by the counterfactual test — may or may not involve
`JOINT_CROSS_SOURCE` evidence at the atomic level) or
`REDUNDANT_SUPPORT` (both sources independently justify) is **not
blocked by B-2**, but it may still be rejected by Gate B for being
untestable, obvious, or otherwise invalid as a mechanism proposal. A
candidate that B-2 routes to `NOT_ADJUDICATED_BY_B2` (UNSUPPORTED) is
also forwarded to Gate B — Gate B may reject it for being nonsensical
or fabricated, OR may adjudicate it as a valid invention if the
unsupported claim is independently defensible. B-2 does not pre-judge
either case.

**Implementation requirement:** The detector's trace must explicitly
report the `iss_state` for every candidate
(`ISS_one` / `ISS_both` / `REDUNDANT_SUPPORT` / `UNSUPPORTED`), per
the frozen JSON schema (Section 3.7.1, `b2-trace-v3`). The
downstream Gate B adjudicator must receive this `iss_state` and the
full support map (including `JOINT_CROSS_SOURCE` entries) and must
NOT treat B-2 passage (ALLOW) as evidence of discovery validity, and
must NOT treat B-2's `NOT_ADJUDICATED_BY_B2` as a B-2 REJECT.

**Anti-regression requirement (Section 8.5):** The spec, the
implementation, and the audit must all preserve:
1. The B-2 / Gate B distinction (B-2 = provenance topology, Gate B =
   discovery validity).
2. The four-state ontology (`ISS_one` / `ISS_both` / `REDUNDANT_SUPPORT`
   / `UNSUPPORTED`).
3. The two support types (`SOURCE_LOCAL` / `JOINT_CROSS_SOURCE`).
4. The five anti-cheating conditions for `JOINT_CROSS_SOURCE` (Section
   2.6.7).
5. **The decoupling of `ISS_both` from `JOINT_CROSS_SOURCE` (round-78,
   NEW):** `ISS_both` is a property of the candidate determined by the
   counterfactual test; `JOINT_CROSS_SOURCE` is a property of an
   evidence path for an atomic claim. The latter is NOT a necessary
   condition for the former. A candidate can be `ISS_both` via a
   combination of independently supported atoms (pathway 1) OR via a
   joint cross-source relation atom (pathway 2). Any attempt to make
   `JOINT_CROSS_SOURCE` a necessary condition for `ISS_both` is
   regression and must be rejected.
6. **The frozen inference-rule taxonomy (round-78, NEW):** the
   `inference_rule` field in `JOINT_CROSS_SOURCE` entries must use a
   value from the frozen taxonomy (Section 2.6.8). The `OTHER` value
   exists but cannot automatically qualify a `JOINT_CROSS_SOURCE` claim
   as a B-2 pass — it requires independent adjudication and is reported
   separately.
7. **The 8-step verification ordering (round-79, NEW):** every
   `JOINT_CROSS_SOURCE` entry must pass the 8-step verification
   sequence (Section 2.6.9) in order. Inference-rule classification
   (steps 1-2) does NOT establish derivation validity; the adjudicator
   must independently judge that the derived claim follows (step 5).
   Accepting an entry based solely on classification without
   independent judgment of validity is a critical regression.

Any attempt to (a) expand B-2's criterion to include novelty
evaluation, (b) collapse `UNSUPPORTED` into an ALLOW state, (c)
re-introduce the non-constructible `ISS_neither` state, (d) allow
`JOINT_CROSS_SOURCE` support without the five anti-cheating
conditions, (e) make `JOINT_CROSS_SOURCE` a necessary condition for
`ISS_both`, (f) allow free-form `inference_rule` values outside the
frozen taxonomy, or (g) accept `JOINT_CROSS_SOURCE` support without
the 8-step verification ordering (especially step 5: independent
judgment of derivation validity), is regression and must be rejected
by the auditor.

---

## 3. Test oracles — anti-tuning mechanism

The round-72 fix's failure mode was that it tuned its heuristic against a
public test fixture. The implementer had access to the expected labels and
could adjust parameters until the fixture passed. This is the failure mode
the repair spec must prevent.

### 3.1 The ADV-11 vs ADV-13 keystone

Any implementation of this spec must produce **opposite** labels for ADV-11
and ADV-13:

- `biomineralization` → ALLOW (true cross-source umbrella)
- `pseudomineralization` → REJECT (source-local derivative)

These two candidates reach the same lexical machinery (both are
`<prefix>mineralization` compounds with non-suffix excess). An implementation
that gives the same label for both has not established the semantic property
and is rejected.

The keystone is the **minimal falsification test**: an implementation that
cannot pass it cannot pass any adversarial set.

### 3.2 The held-out adversarial set

The public adversarial set (`test_fixture.json`, 13 cases) is **not** the
final test set. It is a calibration set that the implementer may use during
development.

The **held-out adversarial set** is constructed by the auditor after the spec
is frozen and before implementation begins. The held-out set:

- Is constructed using the same rationale-template as the public set
  (`cases/ADV-NN.md` format).
- Contains at least 12 cases, distributed across Modes A/B/C **and**
  the `REDUNDANT_SUPPORT` and `UNSUPPORTED` categories.
- Contains at least 2 cases in each of the following sub-categories:
  - Mode A: source-local paraphrase with zero lexical overlap.
  - Mode A: source-local paraphrase with partial lexical overlap that does
    not trigger the lexical detector.
  - Mode B: cross-source synthesis with one-source overlap, where the
    cross-source connection is hypernymy.
  - Mode B: cross-source synthesis with one-source overlap, where the
    cross-source connection is umbrella scope.
  - Mode C: source-local derivative whose excess fits a suffix in
    `COMMON_SUFFIXES` (calibration — should REJECT).
  - Mode C: source-local derivative whose excess does NOT fit a suffix in
    `COMMON_SUFFIXES` (the ADV-13 pattern — should REJECT).
  - **`REDUNDANT_SUPPORT` (round-76, NEW):** a candidate whose atomic
    claims all have supporting spans in Source A AND all have supporting
    spans in Source B independently. Should be ALLOW, reported as
    `REDUNDANT_SUPPORT` (not `ISS_both`). At least 2 cases required.
  - **`UNSUPPORTED` (round-75, retained):** a candidate containing at
    least one atomic claim with no supporting span in either source
    (fabricated or nonsensical content mixed with legitimate source
    vocabulary, per the ADV-14 pattern). Should be
    `NOT_ADJUDICATED_BY_B2`. At least 2 cases required.

#### 3.2.1 Multiple source pairs — MANDATORY (round-74 condition 5)

The held-out set MUST contain **multiple source pairs**, with at least one
pair whose terminology and mechanisms are **completely unrelated to
mineralization** (e.g. one pair about photosynthesis and one about acoustic
wave propagation, or one about neural spike-timing-dependent plasticity
and one about corrosion kinetics).

The rationale: if every held-out case uses the calcium-phosphate/diatom
source pair, the implementation can learn the domain rather than the
operation. The test would then answer "can the detector understand this
example" rather than "can the detector perform the required operation."

The public calibration set uses the mineralization source pair. The held-out
set must include at least one source pair from a different scientific domain,
with different vocabulary, different relationship types, and different kinds
of paraphrase. Ideally the held-out set contains 2–4 source pairs spanning
unrelated domains.

#### 3.2.2 Genuinely blind — no rationale exposure (round-74 condition 4)

The implementation session must NOT receive the semantic rationales for the
held-out set before the implementation freeze. The implementer receives:

- The candidate strings.
- The source texts.
- The case IDs.

The implementer does NOT receive:

- The expected labels (REJECT/ALLOW).
- The rationale files (`cases/ADV-NN.md` for held-out cases).
- The ISS determinations.
- The atomic claim decompositions.
- Any indication of which cases are Mode A, B, or C.

The rationale: if the implementer has access to the semantic rationales, the
model can learn the conceptual distinction directly from the public
rationales and reproduce it on the held-out set without actually possessing
a general semantic capability. The held-out set must remain genuinely blind
until the implementation freeze.

The auditor retains the rationale files in a separate, access-controlled
location. After the implementation freeze, the auditor reveals the
rationale files for adjudication of the detector's traces.

#### 3.2.3 Qualification threshold — 11/12 is engineering qualification only (round-74 condition 6)

The implementer's detector must achieve ≥ 11/12 on the held-out set to
qualify for the implementation freeze. A score below 11/12 means the
implementation has not established the semantic property.

**However, 11/12 must NOT be called "B-2 validated."** It is an engineering
qualification threshold, not scientific validation. One failure out of
twelve could be:

- a harmless borderline case,
- a catastrophic false negative (a real discovery suppressed),
- a catastrophic false positive (a source-local derivative allowed as a
  discovery).

Those are not equivalent. The audit must report, at minimum:

```
TP  (true positive: correctly REJECTED source-local derivative)
TN  (true negative: correctly ALLOWED cross-source synthesis / novel)
FP  (false positive: incorrectly REJECTED cross-source synthesis)
FN  (false negative: incorrectly ALLOWED source-local derivative)

precision   = TP / (TP + FP)
recall      = TP / (TP + FN)
FPR         = FP / (FP + TN)   (false-positive rate)
FNR         = FN / (FN + TP)   (false-negative rate)
```

And the results must be reported **by adversarial category**:

```
Mode A (source-local paraphrase):      TP/TN/FP/FN, precision, recall
Mode B (cross-source synthesis):       TP/TN/FP/FN, precision, recall
Mode C (morphologically deceptive):    TP/TN/FP/FN, precision, recall
```

A detector that scores 11/12 by correctly handling every Mode A case while
failing the only Mode B case is scientifically different from one that
misses one easy Mode C case. The category-level reporting makes this
visible.

**Qualification thresholds:**

- ≥ 11/12 overall: necessary for implementation freeze.
- Zero catastrophic failures (FP or FN on a non-borderline case): necessary
  for implementation freeze.
- No category with 0% recall or 0% precision: necessary for implementation
  freeze.

A detector that meets the 11/12 overall threshold but has a catastrophic
failure in any category is NOT qualified for freeze. The auditor's judgment
applies for borderline cases.

#### 3.2.4 Borderline cases

Some candidates may be genuinely ambiguous (e.g. a candidate that has weak
semantic support from both sources, but strong support from one). The
auditor may mark a held-out case as **borderline** in the rationale file.
A borderline case:

- Is included in the held-out set.
- Has an expected label, but the rationale explicitly notes the ambiguity.
- The detector may answer either way without it counting as a catastrophic
  failure.
- The detector's trace for a borderline case is still audited for span-map
  validity (Section 2.6.4).

Borderline cases must be ≤ 20% of the held-out set.

### 3.3 Required evidence: justification trace, not just a label

The detector must output a **justification trace** for each decision, not just
a REJECT/ALLOW label. The justification trace must include:

1. **Candidate semantic content** — a structured representation of what the
   candidate denotes (e.g. `enzyme-templated mineral deposition` →
   `{process: mineral_deposition, mediator: enzyme_catalyst}`).
2. **Source A coverage** — which elements of the candidate's semantic content
   are supported by Source A, and the specific span of Source A that supports
   each element.
3. **Source B coverage** — same for Source B.
4. **Counterfactual evaluation** — for each source, the detector must state
   whether removing that source would leave the candidate unjustified, and
   why.
5. **Decision** — REJECT or ALLOW, derived from the counterfactual evaluation
   per Section 2.4.

A detector that produces only a label without the trace is not acceptable,
because the trace is the only mechanism the auditor has to verify that the
detector is doing semantic analysis rather than parameter-tuning.

### 3.4 The "no-tuning" verification

After the implementation freeze, the auditor will run the detector against
the held-out set and inspect the justification traces. The auditor will
reject the implementation if any of the following are observed:

- The detector's justification trace for a held-out case is inconsistent
  with its label (e.g. the trace says "ISS_both" but the label is REJECT).
- The detector's justification trace for a held-out case is materially
  shorter or less specific than its trace for the corresponding public case
  (suggesting the implementer tuned the trace format to the public set).
- The detector fails on any held-out case in a category where it passed on
  the public set (suggesting the implementer tuned to the public cases
  rather than to the property).

### 3.5 The trace is an auditable claim, NOT evidence of correctness (round-74 condition 2)

The five-element justification trace (Section 3.3) is valuable, but it is
**not sufficient** to establish that the detector is doing semantic
analysis. An LLM can generate a perfectly coherent false explanation — a
trace that reads persuasively but does not correspond to the actual corpus
content or to the candidate's actual meaning.

Therefore the following pipeline is **acceptable**:

```
candidate
   ↓
semantic analysis
   ↓
justification trace (claimed evidence + claimed reasoning)
   ↓
independent adjudication of trace (auditor verifies span map per Section 2.6.4)
   ↓
accepted or rejected
```

But the following pipeline is **NOT acceptable**:

```
candidate
   ↓
LLM
   ↓
"here is why I'm right" (persuasive explanation)
   ↓
accepted
```

The trace must be treated as an **auditable claim about the detector's
reasoning**, not proof that the reasoning is correct. Correctness of the
trace is established independently on the held-out set by:

1. **Span-map verification** (Section 2.6.4). For each atomic claim, the
   auditor verifies that the cited supporting span is actually present in
   the cited source at the cited offsets and actually asserts the claim.
2. **Counterfactual verification.** For each source `S`, the auditor
   verifies that the detector's claim "removing `S` would leave claims
   {…} unsupported" is correct — i.e. that the claims cited as `S`-supported
   are indeed not supported by the other source.
3. **Label-trace consistency.** The auditor verifies that the detector's
   label (REJECT/ALLOW) follows from its trace per Section 2.4's decision
   criterion.

A trace that fails any of these verifications is rejected, regardless of
whether the detector's label happens to match the expected label. A detector
that produces the right label via a trace that does not survive verification
has not established the semantic property — it has produced a lucky guess
wrapped in a plausible-sounding explanation.

**Implementation requirement:** The detector's output must be structured
enough to support the three verifications above. Specifically, the trace
must include:

- The atomic claim decomposition (Section 2.6.1) as a structured list, not
  free text.
- The span map (Section 2.6.2) as a structured list of (claim, source,
  span_text, span_offsets) tuples, not free text.
- The counterfactual evaluation (Section 2.6.3) as a structured list of
  (source, claims_supported_by_source, claims_left_unsupported_if_removed,
  verdict) tuples, not free text.

Free-text traces that cannot be machine-parsed into these structures are
not acceptable, because the auditor cannot verify them at scale.

### 3.6 Independent double-adjudication + disagreement resolution (round-75 condition 2)

The operational `Justified()` definition (Section 2.6) relies on
adjudicator judgment for synonymy, hypernymy, umbrella scope, and
contextual inference. Two competent adjudicators can legitimately
produce different ISS determinations on the same candidate. The spec
must measure whether the supposed ground truth is itself stable;
otherwise the detector is being evaluated against a moving human oracle.

#### 3.6.1 Two independent adjudicators

Every held-out trace is evaluated by **two independent adjudicators**.
Both adjudicators:

- Are competent in the scientific domain of the source pair (or, for
  source pairs spanning multiple domains, jointly competent across
  them).
- Work **blind to the detector's final label** wherever practical. Each
  adjudicator receives the candidate, the sources, and the detector's
  atomic claim decomposition + span map (Section 3.7), but NOT the
  detector's REJECT/ALLOW/NOT_ADJUDICATED_BY_B2 label.
- Independently produce their own ISS determination
  (`ISS_one` / `ISS_both` / `REDUNDANT_SUPPORT` / `UNSUPPORTED`) and their
  own label.
- Record their reasoning in the same rationale-template format as the
  public set (`cases/ADV-NN.md`).

The two adjudicators must not communicate about specific cases until
both have submitted their determinations. After submission, their
determinations are compared.

#### 3.6.2 Disagreement resolution

If the two adjudicators agree on the label, that label is the canonical
expected label for the case.

If they disagree, a **predefined resolution procedure** applies:

1. The two adjudicators exchange their rationale files (still blind to
   the detector's label).
2. Each adjudicator may revise their determination once, after reading
   the other's rationale.
3. If they still disagree, a **third adjudicator** (the auditor or a
   designated tie-breaker) reviews both rationales and issues the
   canonical label. The third adjudicator's determination is final.
4. The case is marked as **adjudicator-disputed** in the held-out set
   metadata, regardless of the final label.

#### 3.6.3 Raw agreement reporting

The audit must report **raw agreement**, not just resolved labels:

- **Per-case agreement:** for each held-out case, whether the two
  adjudicators agreed on the label before resolution.
- **Per-category agreement:** raw agreement rate broken down by Mode
  A / B / C / UNSUPPORTED.
- **Overall raw agreement rate:** (cases where adjudicators agreed
  without resolution) / (total cases).
- **Disagreement cases:** the list of cases where adjudicators
  disagreed, with both rationales and the final resolution.

**Qualification threshold (round-75):** the overall raw agreement rate
must be ≥ 80% for the held-out set to be considered usable. A rate
below 80% means the ground truth is itself unstable, and the held-out
set must be revised (the cases are too ambiguous) before the detector
can be evaluated against it.

#### 3.6.4 Why this matters

Without double-adjudication, the detector is being evaluated against a
single human's judgment. If that human's judgment differs from another
competent human's judgment by, say, 25%, then a detector that achieves
11/12 against the first human might achieve only 9/12 against the
second — and we would have no way to know which (if either) is the
"correct" ground truth. Double-adjudication makes this uncertainty
visible and forces the spec to either (a) accept the ambiguity
(borderline cases, Section 3.2.4) or (b) revise the cases to be less
ambiguous.

This is especially important for Mode B (cross-source synthesis), where
the cross-source connection may be hypernymy or umbrella scope — both
of which are adjudicator-dependent judgments.

### 3.7 Frozen concrete trace JSON schema (round-75 condition 3; round-77 amended for JOINT_CROSS_SOURCE)

The spec previously said the trace must be "machine-parseable" but left
the exact JSON schema as an open question. Two implementations could
satisfy "machine parseable" while producing incompatible evidence. The
round-75 amendment freezes a concrete JSON schema that all
implementations must produce. The round-77 amendment extends the schema
to support `JOINT_CROSS_SOURCE` support entries (Section 2.6.2, 2.6.7).

#### 3.7.1 The schema (b2-trace-v3, round-77)

Every detector decision must produce a JSON object matching the
following schema. Field names are exact; types are mandatory;
free-form structural variation is NOT permitted.

The `source_support` array contains entries of two types
(discriminated by `support_type`): `SOURCE_LOCAL` and
`JOINT_CROSS_SOURCE`. An atom may have multiple support entries of
either type.

```json
{
  "schema_version": "b2-trace-v3",
  "candidate": {
    "id": "<string, the case ID>",
    "text": "<string, the candidate phrase>",
    "source_a": "<string, verbatim Source A text>",
    "source_b": "<string, verbatim Source B text>"
  },
  "atoms": [
    {
      "atom_id": "<string, unique within this trace, e.g. 'a1'>",
      "claim": "<string, the atomic claim, e.g. '{relation: enzyme_templates_mineral_deposition}'>",
      "source_support": [
        {
          "support_type": "SOURCE_LOCAL",
          "source_id": "<string, 'A' or 'B'>",
          "spans": [
            {
              "span_text": "<string, verbatim substring of the cited source>",
              "start": "<integer, character offset into the source text>",
              "end": "<integer, character offset (exclusive)>"
            }
          ]
        },
        {
          "support_type": "JOINT_CROSS_SOURCE",
          "source_a_spans": [
            {
              "span_text": "<string, verbatim substring of Source A>",
              "start": "<integer, character offset into Source A>",
              "end": "<integer, character offset (exclusive)>"
            }
          ],
          "source_b_spans": [
            {
              "span_text": "<string, verbatim substring of Source B>",
              "start": "<integer, character offset into Source B>",
              "end": "<integer, character offset (exclusive)>"
            }
          ],
          "derived_claim": "<string, the atomic claim that follows from combining A and B components>",
          "inference_rule": "<string, one of: 'COMPOSITION' | 'ABSTRACTION' | 'SPECIALIZATION' | 'GENERALIZATION' | 'CAUSAL_TRANSFER' | 'MECHANISTIC_ANALOGY' | 'STRUCTURAL_ANALOGY' | 'FUNCTIONAL_ANALOGY' | 'OTHER' — from frozen taxonomy inference-rules-v1, Section 2.6.8>",
          "inference_rule_other": "<string, required iff inference_rule == 'OTHER'; free-text explanation of the derivation>",
          "counterfactual_a": "<string, why removing Source A leaves derived_claim unsupported>",
          "counterfactual_b": "<string, why removing Source B leaves derived_claim unsupported>"
        }
      ]
    }
  ],
  "counterfactuals": [
    {
      "removed_source": "<string, 'A' or 'B'>",
      "unsupported_atoms": ["<string, atom_id>", "..."],
      "justified_without_source": "<boolean, whether the candidate remains Justified(c, {A,B}\\{S})>"
    }
  ],
  "classification": {
    "justified_by_corpus": "<boolean, Justified(c, {A,B})>",
    "iss_a": "<boolean, IndependentSemanticSupport(c, A, {A,B})>",
    "iss_b": "<boolean, IndependentSemanticSupport(c, B, {A,B})>",
    "iss_state": "<string, one of: 'ISS_one' | 'ISS_both' | 'REDUNDANT_SUPPORT' | 'UNSUPPORTED'>",
    "label": "<string, one of: 'REJECT' | 'ALLOW' | 'NOT_ADJUDICATED_BY_B2'>"
  }
}
```

**Note on `SOURCE_LOCAL` spans:** the `spans` array (for `SOURCE_LOCAL`
entries) contains one or more span objects. Multiple spans are used
when an atomic claim is supported by a conjunction of spans in the
same source (Section 2.6.6, multi-span support). A single-span entry
has a `spans` array with one element.

**Note on `JOINT_CROSS_SOURCE` entries:** the `source_a_spans` and
`source_b_spans` arrays each contain one or more span objects from the
respective source. The `derived_claim` is the atomic claim that follows
from combining the A and B components. The `inference_rule` states the
rule under which the derivation is valid (open question 9.12 for
taxonomy). The `counterfactual_a` and `counterfactual_b` fields explain
why removing the respective source leaves the derived claim unsupported.

#### 3.7.2 Schema requirements (round-77 amended)

1. **Every atomic claim must have at least one entry in `source_support`
   OR be listed in `counterfactuals[].unsupported_atoms` for at least
   one removed source.** An atom with no support entry of any type AND
   not listed as unsupported is a silent decomposition gap and is
   grounds for trace rejection (Section 2.6.5).

2. **`source_support` may be an empty list** for an atom that has no
   support entry of any type in either source. Such an atom is
   unsupported and must appear in `counterfactuals[].unsupported_atoms`
   for both removed sources (since removing either source still leaves
   it unsupported).

3. **`counterfactuals` must contain exactly two entries**, one for
   `removed_source: "A"` and one for `removed_source: "B"`.

4. **`classification.iss_state` must be consistent with
   `classification.justified_by_corpus`, `iss_a`, and `iss_b`**
   (round-76 amended):
   - `UNSUPPORTED` iff `justified_by_corpus == false`.
   - `ISS_one` iff `justified_by_corpus == true` AND exactly one of
     `iss_a`, `iss_b` is true.
   - `ISS_both` iff `justified_by_corpus == true` AND both `iss_a` and
     `iss_b` are true.
   - `REDUNDANT_SUPPORT` iff `justified_by_corpus == true` AND neither
     `iss_a` nor `iss_b` is true.

   (Note: `iss_a` = `IndependentSemanticSupport(c, A, {A,B})` =
   `Justified(c,{A,B}) AND NOT Justified(c,{B})`. So `iss_a == false`
   when `Justified(c,{A}) == true` (given `Justified(c,{A,B}) == true`).
   `REDUNDANT_SUPPORT` is the case where both `iss_a` and `iss_b` are
   false, meaning both `Justified(c,{A})` and `Justified(c,{B})` are
   true — i.e. both sources independently justify the candidate.)

5. **`classification.label` must be consistent with `iss_state`** per
   Section 2.4 (round-76 amended):
   - `ISS_one` → `REJECT`
   - `ISS_both` → `ALLOW`
   - `REDUNDANT_SUPPORT` → `ALLOW`
   - `UNSUPPORTED` → `NOT_ADJUDICATED_BY_B2`

6. **`span_text` must be the verbatim substring of the cited source at
   the cited offsets.** The auditor's verification (Section 2.6.4)
   checks `source_text[start:end] == span_text`. Any mismatch is
   grounds for trace rejection. This applies to `SOURCE_LOCAL.spans`,
   `JOINT_CROSS_SOURCE.source_a_spans`, and
   `JOINT_CROSS_SOURCE.source_b_spans` equally.

7. **`JOINT_CROSS_SOURCE` entries must contain all mandatory fields**
   (round-77, NEW; round-78 amended): `source_a_spans` (non-empty),
   `source_b_spans` (non-empty), `derived_claim` (non-empty),
   `inference_rule` (non-empty, from frozen taxonomy — see requirement
   8), `counterfactual_a` (non-empty), `counterfactual_b` (non-empty).
   If `inference_rule == "OTHER"`, `inference_rule_other` (non-empty)
   is also required. Any missing or empty field is grounds for trace
   rejection.

8. **`inference_rule` must be from the frozen taxonomy** (round-78,
   NEW): the value must be one of `COMPOSITION`, `ABSTRACTION`,
   `SPECIALIZATION`, `GENERALIZATION`, `CAUSAL_TRANSFER`,
   `MECHANISTIC_ANALOGY`, `STRUCTURAL_ANALOGY`, `FUNCTIONAL_ANALOGY`,
   `OTHER` (Section 2.6.8, taxonomy version `inference-rules-v1`).
   Free-form values are NOT permitted. If the value is `OTHER`, the
   entry is flagged `UNCLASSIFIED_INFERENCE` and cannot automatically
   qualify the `JOINT_CROSS_SOURCE` claim as valid support — it
   requires independent adjudication (Section 2.6.8, treatment of
   `OTHER`).

9. **`JOINT_CROSS_SOURCE` entries must satisfy the five anti-cheating
   conditions** (Section 2.6.7). The adjudicator verifies:
   - A genuinely supports its component (spans present and assertive).
   - B genuinely supports its component.
   - The derived claim follows from the combination under the stated
     inference rule (from the frozen taxonomy, per requirement 8).
   - Neither source alone supports the complete relation (else it
     should be `SOURCE_LOCAL`).
   - Removing either source destroys the justification.

10. **No free-form structural variation is permitted.** All fields are
    mandatory; no additional top-level fields are allowed without
    auditor approval (except `schema_version`); no fields may be
    renamed.

#### 3.7.3 Why a frozen schema

A frozen schema ensures:

- Two implementations produce comparable evidence.
- The auditor's verification (Section 2.6.4, 3.5) can be automated.
- The double-adjudication protocol (Section 3.6) receives a uniform
  input format.
- The downstream Gate B adjudicator receives a uniform handoff format
  (preserving the four-state ontology — `ISS_one` / `ISS_both` /
  `REDUNDANT_SUPPORT` / `UNSUPPORTED` — and the two support types —
  `SOURCE_LOCAL` / `JOINT_CROSS_SOURCE` — end-to-end, per Section 8.5).

#### 3.7.4 Schema versioning

This schema is frozen at version `b2-trace-v3` (round-77). The version
was bumped from `b2-trace-v2` (round-76) to `b2-trace-v3` because the
`source_support` structure changed: `SOURCE_LOCAL` entries now use a
`spans` array (instead of a single `span_text`/`start`/`end` triple),
and `JOINT_CROSS_SOURCE` entries are new. This is a breaking schema
change; traces produced under `b2-trace-v2` are NOT valid under
`b2-trace-v3` (and vice versa), because the `source_support` structure
is materially different.

Version history:
- `b2-trace-v1` (round-75): initial frozen schema.
- `b2-trace-v2` (round-76): `iss_state` enum changed (`ISS_neither`
  removed, `REDUNDANT_SUPPORT` added).
- `b2-trace-v3` (round-77): `source_support` structure changed
  (`SOURCE_LOCAL` now uses `spans` array; `JOINT_CROSS_SOURCE` type
  added with mandatory fields).

Any future revision requires a new version number, a new adjudication
cycle, and re-verification of all held-out results against the new
schema. The schema version is recorded in the trace:

```json
{
  "schema_version": "b2-trace-v3",
  ...
}
```

(The `schema_version` field is the only additional top-level field
permitted without auditor approval.)

---

## 4. Adversarial example categories

This section restates the three failure modes as **categories of adversarial
examples** that any implementation must handle. Each category lists the
public cases that exemplify it and the property the implementation must
demonstrate.

### 4.1 Mode A — source-local paraphrase (required REJECT)

**Definition:** A candidate that paraphrases a claim from one source only,
using synonym substitution, hypernym substitution, or structural rewording,
such that the candidate's meaning is fully derivable from that source alone.

**Public cases:** ADV-01, ADV-02, ADV-10 (exact-string, trivial case).

**Required property:** The detector must REJECT these candidates. The
detector must NOT reject them via lexical overlap (which fails for ADV-01
and ADV-02); it must reject them via the counterfactual evaluation: "removing
Source A would leave the candidate unjustified; removing Source B would not;
therefore ISS_one; therefore REJECT."

**Anti-tuning check:** The held-out set will include at least 2 Mode-A cases
with zero lexical overlap and at least 2 Mode-A cases with partial lexical
overlap that does not trigger the lexical detector. The implementer must not
be able to predict which cases are in the held-out set.

### 4.2 Mode B — legitimate cross-source synthesis (required ALLOW)

**Definition:** A candidate whose semantic content draws meaningfully on
both sources and could not be constructed from either source alone. The
candidate's terminology may overlap with one source lexically; the
cross-source connection may be hypernymy, umbrella scope, or concept-level
reference.

**Public cases:** ADV-03, ADV-04, ADV-07, ADV-08, ADV-11.

**Required property:** The detector must ALLOW these candidates. The
detector must NOT reject them via the "overlap with one source → check
unshared tokens in other source" rule (which fails for all five cases); it
must allow them via the counterfactual evaluation: "removing Source A would
leave the candidate unjustified; removing Source B would leave the candidate
unjustified; therefore ISS_both; therefore ALLOW."

**Anti-tuning check:** The held-out set will include at least 2 Mode-B cases
where the cross-source connection is hypernymy and at least 2 Mode-B cases
where the cross-source connection is umbrella scope. The implementer must
not be able to predict which cases are in the held-out set.

### 4.3 Mode C — morphologically deceptive derivatives (required REJECT)

**Definition:** A candidate that is a morphological derivative of one
source's literal vocabulary (typically via prefixation), constructed such
that the derivative does not perform cross-source synthesis. The candidate
may appear to be a cross-domain term (because of the prefix) but is in fact
a source-local derivative (because the prefix is a degree, falsity, or
foreign modifier, not a cross-source bridge).

**Public cases:** ADV-05, ADV-06, ADV-12, ADV-13.

**Required property:** The detector must REJECT these candidates. The
detector must NOT reject them via the `COMMON_SUFFIXES` list (which fails
for ADV-13); it must reject them via the counterfactual evaluation: "the
prefix is a modifier on Source A's content, not a reference to Source B's
content; removing Source A would leave the candidate unjustified; removing
Source B would not; therefore ISS_one; therefore REJECT."

**Anti-tuning check:** The held-out set will include at least 2 Mode-C cases
whose excess fits a suffix in `COMMON_SUFFIXES` (calibration — should
REJECT) and at least 2 Mode-C cases whose excess does NOT fit a suffix in
`COMMON_SUFFIXES` (the ADV-13 pattern — should REJECT). The implementer
must not be able to predict which cases are in the held-out set.

### 4.4 The keystone pair (Section 3.1 restated)

Any implementation must produce opposite labels for `biomineralization`
(ALLOW) and `pseudomineralization` (REJECT). This is the minimal
falsification test. An implementation that cannot pass it cannot pass any
adversarial set.

---

## 5. Required detector properties

### 5.1 Must not be tunable against the public test set

The detector's behavior on the held-out set must be **no worse** than its
behavior on the public set, modulo sampling variance. A material drop in
performance on the held-out set is evidence that the implementer tuned the
detector to the public set rather than to the property.

The auditor will compare the per-category pass rates on the public set vs.
the held-out set. **A drop of more than 1 case in any category is an
audit trigger, NOT proof of tuning** (round-75 refinement). With tiny
category counts (e.g. 2-4 cases per category), a single-case drop is
statistically weak evidence; it is a useful warning condition that
warrants investigation, but it is not by itself sufficient to reject
the implementation.

When an audit trigger fires, the auditor must:

1. Inspect the specific held-out case(s) that failed.
2. Inspect the corresponding public cases in the same category.
3. Determine whether the failure pattern suggests tuning (e.g. the
   detector passed public cases by exploiting a lexical artifact that
   the held-out cases do not share) or is a genuine borderline
   disagreement (e.g. an adjudicator-disputed case per Section 3.6).
4. If tuning is confirmed, reject the implementation. If the failure
   is a borderline disagreement, document it and proceed.

**Anti-regression note:** the previous version of this section (commit
`4bc945d`) said a drop of more than 1 case "is evidence of tuning and
triggers rejection of the implementation." The round-75 amendment
weakens this to "audit trigger" to reflect the statistical reality of
tiny category counts.

### 5.2 Must produce a justification trace (Section 3.3)

The detector must output the 5-element justification trace specified in
Section 3.3 for every decision. The trace is the auditor's only mechanism
for verifying that the detector is doing semantic analysis.

### 5.3 Must distinguish Mode A from "no overlap" ALLOW

A detector that gives the same label (ALLOW) for ADV-01 (true REJECT,
no-overlap paraphrase) and ADV-09 (true ALLOW, no-overlap novel) has not
established the semantic property. The detector must distinguish them via
the counterfactual evaluation: ADV-01's meaning is derivable from Source A
alone; ADV-09's meaning is derivable from neither source.

### 5.4 Must distinguish Mode B from "one-source overlap" REJECT

A detector that gives the same label (REJECT) for ADV-03 (true ALLOW,
one-source overlap with semantic bridge to Source B) and ADV-12 (true
REJECT, one-source morphological derivative) has not established the
semantic property. The detector must distinguish them via the counterfactual
evaluation: ADV-03's `enzyme` component requires Source B's silicatein;
ADV-12's `mineralizing` requires only Source A's `mineralization`.

### 5.5 Must distinguish Mode C from "non-suffix excess" ALLOW

A detector that gives the same label (ALLOW) for ADV-11 (true ALLOW,
`biomineralization`) and ADV-13 (true REJECT, `pseudomineralization`) has
not established the semantic property. This is the keystone falsification
test (Section 3.1). The detector must distinguish them via the
counterfactual evaluation: `bio-` is a cross-source prefix (denoting the
biological context that both sources instantiate); `pseudo-` is a falsity
modifier on Source A's `mineralization`.

### 5.6 Must be implementation-agnostic (Section 6)

The spec does not prescribe an implementation approach. The detector may be
LLM-based, symbolic, hybrid, or any other approach — provided it produces
the justification trace and passes the held-out set.

### 5.7 LLM instrument freezing requirements (round-74 condition 3)

If the implementation uses an LLM (whether as the primary detector, as a
component of a hybrid detector, or as a verifier), the LLM-based instrument
must be **frozen as experimental substrate**. An LLM-based implementation
cannot be considered frozen merely because its Python source is hashed.

The following must be frozen and recorded at the implementation freeze:

| Dimension | What must be recorded |
|-----------|----------------------|
| Model provider | e.g. OpenAI, Anthropic, Z.ai, local |
| Model identifier | exact model name + version (e.g. `gpt-4-turbo-2024-04-09`, `claude-3-opus-20240229`) |
| System / developer prompt | full text, frozen |
| User prompt template | full text, frozen, with placeholder variables identified |
| Temperature | exact value (e.g. `0.0`) |
| Tool availability | which tools the LLM can call (must be `none` unless auditor approves) |
| Retrieval corpus | what the LLM can retrieve (must be `none` unless auditor approves — no web search, no external KB) |
| Context construction | how the candidate + sources are formatted into the prompt (exact ordering, delimiters, escaping) |
| Output schema | exact JSON schema or structured format the LLM must produce |
| Retry policy | how malformed outputs are handled (e.g. retry up to N times, fall back to deterministic label) |
| Deterministic seed | if the provider supports seeding, the exact seed value |
| Runtime / dependency versions | Python version, SDK version, HTTP library version |

**Rationale:** the project has a documented history of reward-hacking risk
(see ANTI_ENTROPY.md). An unfrozen LLM instrument is a moving experimental
substrate: the provider can change the model's behavior silently (via
weight updates, prompt-injection mitigations, or safety filters), and the
detector's results would change underneath the audit. Freezing the Python
source does not freeze the model.

**Implementation requirements:**

1. At the implementation freeze, the engineer must produce a
   `FROZEN_LLM_INSTRUMENT.md` file recording all dimensions above.
2. The auditor must verify that the recorded values match the actual
   runtime configuration by inspecting the engineer's code and (if
   applicable) the provider's API logs.
3. Any change to the recorded dimensions after the freeze — including
   provider-side model updates — triggers a re-audit. The auditor must be
   notified if the provider deprecates or updates the frozen model
   identifier.
4. If the provider does not support deterministic seeding, the engineer
   must run the detector N≥5 times per held-out case and report the
   distribution of labels. Majority vote is the canonical label; ties are
   reported as ambiguous and counted as failures for qualification
   purposes.

**Anti-regression requirement (Section 8.6):** If the LLM instrument drifts
(provider-side update, silent behavior change) between the implementation
freeze and the Protocol B discrimination run, the discrimination run's
results are INVALIDATED. The auditor must re-run the held-out set to confirm
the instrument's behavior has not changed before trusting any Protocol B
result.

---

## 6. Implementation-agnostic specification

This spec is silent on the implementation approach. The following approaches
are all acceptable in principle:

- **LLM-based:** an LLM is prompted with the candidate, Source A, and Source
  B, and is asked to produce the justification trace specified in Section
  3.3. If this approach is chosen, the LLM instrument must be frozen per
  Section 5.7.
- **Symbolic:** a knowledge graph or ontology is used to evaluate hypernymy,
  umbrella scope, and concept-level reference. The ontology version and
  configuration must be frozen analogously to Section 5.7.
- **Hybrid:** an LLM is used for the counterfactual evaluation; a symbolic
  checker is used to verify the LLM's trace. Both components must be frozen
  per Section 5.7 (or its symbolic analogue).
- **Other:** any approach that produces the justification trace and passes
  the held-out set.

The spec does NOT prescribe:

- which LLM to use (if any),
- which ontology to use (if any),
- which prompt template to use (if any),
- which similarity metric to use (if any).

The spec prescribes ONLY:

- the property to be evaluated (Section 2),
- the operational definition of `Justified()` (Section 2.6),
- the decision criterion (Section 2.4),
- the justification trace format (Section 3.3) and its machine-parseable
  structure (Section 3.5),
- the held-out set performance requirement (Section 3.2),
- the anti-tuning safeguards (Section 5),
- the LLM/symbolic instrument freezing requirements (Section 5.7).

An implementation that satisfies these prescriptions is acceptable,
regardless of its internal approach. Note (per round-74 wording correction):
the spec's silence on implementation approach is a deliberate design choice,
not a claim that no symbolic or hybrid system could solve the semantic
problems identified in Section 1. The actual evidence (Section 1) establishes
that the **current lexical feature set** does not solve them; it does not
establish that no possible lexical/symbolic/hybrid system could.

---

## 7. Workflow

The workflow is sequential. Each stage gates the next. The round-74
amendment inserts a re-adjudication step after the spec amendment, per the
auditor's directive: "AMENDED SPEC → INDEPENDENT ADJUDICATION → HELD-OUT
SET SEALED → IMPLEMENTATION → ADVERSARIAL AUDIT → IMPLEMENTATION FREEZE →
INDEPENDENT ADJUDICATION → PROTOCOL B."

### 7.1 Spec freeze (original, round-73)

The original spec was frozen at commit `8a84fdc` on 2026-08-09. That freeze
is superseded by the round-74 amended freeze (Section 7.1a).

### 7.1a Amended spec freeze (this revision, round-74)

This amended spec is frozen at the date in the document header. No further
edits may be made to it without the auditor's explicit approval. The
amended spec is the canonical reference for the B-2 repair; the original
spec at `8a84fdc` is retained in git history for reference only.

The amendment resolves all 7 round-74 conditions + the wording correction
(documented in the document header and in each amended section).

### 7.2 Independent adjudication of amended spec (auditor) — RE-ADJUDICATION

The auditor reviews this amended spec and either:

- **Accepts** the amended spec as the canonical repair specification, OR
- **Rejects** the amended spec with specific objections, OR
- **Accepts with conditions** (further amendments required).

Implementation work may NOT begin until the auditor accepts the amended
spec (unconditionally or with conditions). The acceptance is recorded in
`worklog.md` as a new task entry.

The auditor must specifically adjudicate the new open questions 9.8
(operational `Justified()` adequacy) and 9.9 (B-2 / Gate B boundary
preservation), as these were introduced by the round-74 amendment.

### 7.3 Held-out set construction (auditor)

After the amended spec is accepted, the auditor constructs the held-out
adversarial set per Section 3.2 (as strengthened by 3.2.1, 3.2.2, 3.2.3,
3.2.4). The held-out set:

- Is constructed using the same rationale-template as the public set.
- Contains at least 12 cases, distributed across Modes A/B/C.
- Uses multiple source pairs, with at least one pair unrelated to
  mineralization (Section 3.2.1 — MANDATORY).
- Is kept genuinely blind to the implementer — no rationale exposure
  (Section 3.2.2).
- Each case ships its own rationale file.
- Borderline cases are marked and ≤ 20% of the set (Section 3.2.4).

The held-out set is stored at a path the auditor controls and is not
committed to the implementer's repository until the implementation freeze.

### 7.4 Implementation (engineer)

The engineer implements a detector that satisfies Sections 2 (including
2.6 operational `Justified()` and 2.7 B-2 vs discovery), 3 (including 3.5
trace structure), 5 (including 5.7 LLM instrument freezing), and 6.

The engineer may use the public adversarial set (`test_fixture.json`, 13
cases) as a calibration set during development. The engineer may NOT access
the held-out set or its rationale files (Section 3.2.2).

The engineer produces:

- The detector implementation.
- A test harness that runs the detector against the public set and produces
  per-case justification traces in the machine-parseable format of Section
  3.5.
- A test harness that accepts a held-out set (path TBD by auditor) and
  produces per-case justification traces in the same format.
- If LLM-based: a `FROZEN_LLM_INSTRUMENT.md` file recording all dimensions
  in Section 5.7.

### 7.5 Adversarial audit (auditor)

The auditor runs the engineer's detector against the held-out set and
inspects the justification traces per Sections 2.6.4 (span-map
verification), 3.4 (no-tuning verification), and 3.5 (trace ≠ evidence).
The auditor reports:

- TP/TN/FP/FN/precision/recall/FPR/FNR by adversarial category (Section
  3.2.3).
- Per-case span-map verification results.
- Per-case trace-structure verification results.
- Any anti-tuning red flags (Section 3.4).

The auditor either:

- **Accepts** the implementation (≥ 11/12 overall, zero catastrophic
  failures, no category with 0% recall or 0% precision, all span maps
  verified, no tuning red flags), OR
- **Rejects** the implementation with specific objections.

### 7.6 Implementation freeze

If the auditor accepts the implementation, the detector is frozen at its
current commit. No further tuning is permitted. The frozen detector is the
canonical B-2 detector for Protocol B.

If LLM-based, the frozen instrument configuration (Section 5.7) is recorded
in `FROZEN_LLM_INSTRUMENT.md` and any drift from this configuration
invalidates downstream results (Section 8.6).

### 7.7 Independent adjudication of frozen implementation (auditor)

Before Protocol B may proceed, the auditor performs a final independent
adjudication of the frozen implementation. This is a re-confirmation that:

- The frozen detector still passes the held-out set (no drift since the
  adversarial audit).
- The frozen LLM instrument (if applicable) matches the recorded
  configuration.
- The B-2 / Gate B boundary (Section 2.7, 8.5) is preserved in the
  detector's output format.

This step was added by the round-74 amendment per the auditor's directive:
"AMENDED SPEC → INDEPENDENT ADJUDICATION → HELD-OUT SET SEALED →
IMPLEMENTATION → ADVERSARIAL AUDIT → IMPLEMENTATION FREEZE → INDEPENDENT
ADJUDICATION → PROTOCOL B."

### 7.8 Protocol B discrimination run

After the independent adjudication of the frozen implementation, Protocol B
may proceed. The frozen detector is used as the B-2 component of the
Protocol B discrimination run.

If the discrimination run produces a positive result (engine arm
outperforms null arm), the result is **scientific evidence** that the
engine performs cross-source discovery — provided the detector has been
adjudicated per this spec AND the `REDUNDANT_SUPPORT` candidates are
reported separately from `ISS_both` candidates (Section 8.5). A
positive run driven by `ISS_both` candidates is evidence of cross-source
synthesis; a positive run driven by `REDUNDANT_SUPPORT` candidates is
evidence of redundant candidate generation (both sources independently
support the same candidates), which is scientifically weaker.

If the discrimination run produces a null result, the result is evidence
that the engine does NOT perform cross-source discovery, OR that the
detector is over-blocking. The auditor's judgment is required to
distinguish these cases.

---

## 8. Anti-regression safeguards

### 8.1 The 6/6 lexical-detector result

The 6/6 result from the round-72 lexical test suite (`b1_b2_verification.py`
at commit `20ac268`) is retained as an **engineering regression result**.
It may be used to verify that future detectors do not regress on the
exact-string and short-suffix cases that the lexical detector handles.

It must NOT be promoted to scientific evidence that paraphrase leakage has
been solved. The 6/13 adversarial diagnostic (this document) is the
canonical evidence that the lexical detector does NOT solve paraphrase
leakage.

### 8.2 The 6/13 adversarial diagnostic

The 6/13 mismatch result (this document, Section 1) is the new baseline.
Any future detector must be evaluated against this diagnostic AND the
held-out set. A detector that regresses on the diagnostic (e.g. produces
7/13 mismatches) is rejected, even if it passes the held-out set.

### 8.3 No re-tuning of the lexical detector

The lexical detector at commit `20ac268` is **frozen**. It must NOT be
re-tuned. Any attempt to improve the lexical detector (e.g. by adding
more suffixes to `COMMON_SUFFIXES`, adjusting the `+1` slack, or adding
new heuristics) is a violation of this spec and must be rejected by the
auditor.

The lexical detector may be replaced by a semantic detector that
satisfies this spec. It may not be incrementally improved.

### 8.4 No promotion of engineering regression to scientific evidence

The 6/6 lexical-detector result, the 4/4 B-1 result, and any future
engineering regression results must NOT be promoted to scientific evidence
of discovery capability. Scientific evidence requires:

1. A semantic detector that satisfies this spec (Sections 2, 3, 5).
2. A positive Protocol B discrimination run (Section 7.7).
3. Independent adjudication of the discrimination run by the auditor.

Anything short of these three is engineering evidence, not scientific
evidence.

### 8.5 B-2 establishes provenance topology, Gate B establishes discovery validity (round-74 → round-77 finalized)

Per Section 2.7, B-2 establishes **provenance topology**: is the
candidate source-local (`ISS_one`), cross-source synthesis
(`ISS_both` via `JOINT_CROSS_SOURCE` support), redundantly supported
(`REDUNDANT_SUPPORT`), or unsupported (`UNSUPPORTED`)? Gate B
establishes **discovery validity**: is the candidate a valid, meaningful
mechanism? The two gates must remain distinct, AND the four-state
ontology AND the two support types must be preserved end-to-end.

Anti-regression safeguards:

- The B-2 criterion must NOT be expanded to include novelty evaluation.
  Any proposal to add "REJECT if `REDUNDANT_SUPPORT` because the
  candidate is not novel" is scope creep and must be rejected by the
  auditor. B-2 does not adjudicate novelty; Gate B does.
- The B-2 criterion must NOT collapse `UNSUPPORTED` into an ALLOW state.
  Any proposal to "ALLOW unsupported candidates because they're novel"
  is a re-opening of the round-75 loophole and must be rejected by the
  auditor. `UNSUPPORTED` candidates are forwarded to Gate B as
  `NOT_ADJUDICATED_BY_B2`, NOT ALLOWED.
- The B-2 criterion must NOT re-introduce the non-constructible
  `ISS_neither` state (round-76 elimination). Any proposal to add a
  fifth state for "jointly necessary but not independently attributable"
  must be rejected — under the span-map definition of `Justified()`,
  that category IS `ISS_both`, not a separate state. See Section 2.1
  for the mathematical derivation.
- `JOINT_CROSS_SOURCE` support must NOT be used without the five
  anti-cheating conditions (round-77, Section 2.6.7). Any proposal
  to allow `JOINT_CROSS_SOURCE` support without verifying (1) A
  genuinely supports its component, (2) B genuinely supports its
  component, (3) the derived claim follows from the combination,
  (4) neither source alone supports the complete relation, (5)
  removing either source destroys the justification, is a re-opening
  of the "LLM manufactures plausible A+B=invention" problem and must
  be rejected by the auditor.
- **Inference-rule classification does NOT establish derivation
  validity (round-79, NEW).** The frozen taxonomy
  (`inference-rules-v1`, Section 2.6.8) is a classification ontology,
  NOT an inference engine. Selecting `COMPOSITION`,
  `ABSTRACTION`, `CAUSAL_TRANSFER`, etc. must never itself imply
  that the derived claim is true. Every `JOINT_CROSS_SOURCE` entry
  must pass the 8-step verification ordering (Section 2.6.9),
  including step 5: the adjudicator must **independently judge**
  whether the derived claim actually follows under the stated rule.
  Accepting an entry based solely on classification (steps 1-2)
  without independent judgment of validity (step 5) is a critical
  regression and must be rejected by the auditor.
- The B-2 criterion must NOT evaluate whether a
  `JOINT_CROSS_SOURCE` derivation produces a "valid" or "good"
  invention (round-77). B-2 only verifies the derivation is honestly
  applied to real evidence from both sources. Whether the derived
  relation is a valid mechanism is Gate B's responsibility.
- The B-2 trace's `iss_state` field AND the full support map
  (including `JOINT_CROSS_SOURCE` entries) must be preserved
  end-to-end and forwarded to the downstream Gate B adjudicator
  (Section 3.7.1, schema `b2-trace-v3`). The downstream gate must
  receive the full classification (`ISS_one` / `ISS_both` /
  `REDUNDANT_SUPPORT` / `UNSUPPORTED`) AND the support entries
  (`SOURCE_LOCAL` / `JOINT_CROSS_SOURCE`), NOT just the B-2 label.
- The Protocol B discrimination run must report `REDUNDANT_SUPPORT`
  candidates and `UNSUPPORTED` candidates separately from `ISS_both`
  candidates. A positive discrimination run driven entirely by
  `REDUNDANT_SUPPORT` candidates (i.e. candidates that pass B-2 because
  both sources independently justify them) is scientifically different
  from one driven by `ISS_both` candidates (i.e. candidates that pass
  B-2 because they perform cross-source synthesis via
  `JOINT_CROSS_SOURCE` support). The former is evidence of redundant
  candidate generation; the latter is evidence of cross-source
  discovery. A positive run driven by `UNSUPPORTED` candidates (which
  should NOT happen, since they are `NOT_ADJUDICATED_BY_B2`) would
  indicate a B-2 implementation bug.

### 8.6 LLM instrument drift invalidates downstream results (round-74 condition 3)

Per Section 5.7, if the implementation uses an LLM, the LLM instrument must
be frozen at the implementation freeze. If the instrument drifts between
the freeze and any downstream run (Protocol B discrimination run, re-audit,
etc.), the downstream results are INVALIDATED.

Drift includes:

- Provider-side model weight updates.
- Provider-side prompt-injection mitigations or safety filter changes.
- Provider-side deprecation of the frozen model identifier.
- Engineer-side changes to any of the dimensions recorded in
  `FROZEN_LLM_INSTRUMENT.md` (Section 5.7).

If drift is detected, the auditor must:

1. Re-run the held-out set against the drifted instrument.
2. Compare the per-category pass rates to the original frozen-run pass
   rates.
3. If any category's pass rate drops by more than 1 case, the instrument is
   considered materially changed. The downstream run's results are
   invalidated. The engineer must either roll back to the frozen
   configuration or re-freeze with a new adjudication cycle.

This safeguard exists because the project has a documented history of
reward-hacking risk. An unfrozen LLM instrument is a moving measurement
device; results from a moving device cannot be trusted as scientific
evidence.

---

## 9. Open questions for adjudication

The round-74 amendment resolves open questions 9.5 (held-out source pairs —
now mandatory, see Section 3.2.1) and partially resolves 9.1 (qualification
threshold — see Section 3.2.3), 9.6 (borderline cases — see Section 3.2.4).
The remaining open questions are listed below. The implementer may NOT make
these decisions.

### 9.1 Held-out set size and pass threshold — PARTIALLY RESOLVED (round-74)

**Resolved:** 11/12 is the engineering qualification threshold
(Section 3.2.3). It must NOT be called "B-2 validated." The audit must
report TP/TN/FP/FN/precision/recall/FPR/FNR by adversarial category
(Mode A/B/C). Zero catastrophic failures and no category with 0% recall or
0% precision are necessary for freeze.

**Remaining question:** Is the catastrophic-failure definition (Section
3.2.3) precise enough? Specifically: a "catastrophic failure" is defined as
an FP or FN on a non-borderline case. The auditor may refine this
definition (e.g. by adding severity tiers, or by specifying which
categories' failures are more catastrophic).

### 9.2 Justification trace format — RESOLVED (round-75, updated round-77)

**Resolved (round-75, updated round-77):** The concrete JSON schema is
now frozen at Section 3.7. All implementations must produce traces
matching the `b2-trace-v3` schema (Section 3.7.1, 3.7.2; round-77
bumped from v2 due to `source_support` structure change:
`SOURCE_LOCAL` now uses `spans` array, `JOINT_CROSS_SOURCE` type
added). Free-text traces are not acceptable. The schema includes:
`candidate`, `atoms[]` (with `atom_id`, `claim`, `source_support[]`
where each entry has `support_type` of `SOURCE_LOCAL` or
`JOINT_CROSS_SOURCE`), `counterfactuals[]` (with `removed_source`,
`unsupported_atoms[]`, `justified_without_source`), and
`classification` (with `justified_by_corpus`, `iss_a`, `iss_b`,
`iss_state`, `label`). Schema versioning is via the `schema_version`
field (currently `b2-trace-v3`).

### 9.3 LLM-based implementation — RESOLVED (round-74)

**Resolved:** An LLM-based implementation is acceptable, provided the LLM
instrument is frozen per Section 5.7. The frozen instrument must record
model provider, model identifier, prompts, temperature, tool availability,
retrieval corpus, context construction, output schema, retry policy,
deterministic seed, and runtime/dependency versions.

**Remaining question:** Which LLM providers are acceptable? The auditor
may rule on whether specific providers (e.g. providers with documented
silent model updates, or providers without deterministic seeding) are
excluded.

### 9.4 Determinism and reproducibility — RESOLVED (round-74)

**Resolved:** If the provider supports deterministic seeding, the engineer
must pin a seed and record it per Section 5.7. If the provider does NOT
support deterministic seeding, the engineer must run the detector N≥5
times per held-out case and report the label distribution; majority vote
is the canonical label, ties are reported as ambiguous and counted as
failures (Section 5.7, implementation requirement 4).

**Remaining question:** Is N≥5 sufficient for stable majority vote? The
auditor may direct a higher N (e.g. N≥10) for cases near the decision
boundary.

### 9.5 Scope of the held-out set — RESOLVED (round-74)

**Resolved:** The held-out set MUST use multiple source pairs, with at
least one pair whose terminology and mechanisms are completely unrelated to
mineralization (Section 3.2.1). This is mandatory, not optional. Ideally
the held-out set contains 2–4 source pairs spanning unrelated domains.

### 9.6 Adjudication of borderline cases — RESOLVED (round-74)

**Resolved:** Borderline cases are marked in the rationale file, included
in the held-out set, and the detector may answer either way without it
counting as a catastrophic failure (Section 3.2.4). Borderline cases must
be ≤ 20% of the held-out set. The detector's trace for a borderline case
is still audited for span-map validity.

### 9.7 Re-freeze criteria — OPEN

If the implementation is rejected at the adversarial audit (Section 7.5),
the spec may be revised and re-frozen, or the implementation may be
re-attempted against the same spec. The auditor must rule on the
re-freeze criteria.

**Question:** Under what conditions may the spec be revised after
implementation has begun? Under what conditions may the implementation
be re-attempted without spec revision?

**Proposed default (for auditor approval):**

- If the implementation fails on > 1 held-out case in a single category,
  the spec may be revised (the category may be under-specified).
- If the implementation fails on exactly 1 held-out case and the failure
  is a borderline case, the implementation may be re-attempted without
  spec revision.
- If the implementation fails the span-map verification (Section 2.6.4)
  on any case, the implementation must be re-attempted (the trace
  generation is broken, not the spec).
- If the auditor detects tuning (Section 3.4) on any case, the
  implementation is rejected and the engineer is removed from the
  implementation role.

### 9.8 NEW (round-74) — Operational definition of `Justified()` adequacy

Section 2.6 introduces an operational definition of `Justified()` based on
atomic claim decomposition and span-mapped evidence. The auditor must
adjudicate whether this definition is operationally adequate.

**Question:** Is the atomic-claim decomposition + span-mapped evidence
approach (Section 2.6) sufficient to make `Justified()` falsifiable? Or
are additional operational tests required (e.g. inter-annotator agreement
on span maps, a formal claim taxonomy, an ontology of permitted inference
types)?

### 9.9 B-2 / Gate B boundary preservation — RESOLVED (round-76)

Section 2.7 and Section 8.5 specify that B-2 must remain a leakage and
support instrument and must not absorb Gate B's discovery-validity
responsibilities. The round-75 amendment strengthened this by
separating `UNSUPPORTED` from the (now-eliminated) `ISS_neither`. The
round-76 amendment finalized this by eliminating the non-constructible
`ISS_neither` state entirely and replacing it with `REDUNDANT_SUPPORT`,
producing a clean four-state ontology (`ISS_one` / `ISS_both` /
`REDUNDANT_SUPPORT` / `UNSUPPORTED`).

**Resolved (round-76, extended round-77):** The four-state ontology is
explicit in the decision criterion (Section 2.4), the trace schema
(Section 3.7.1, `b2-trace-v3`, `classification.iss_state`), and the
anti-regression safeguards (Section 8.5). The downstream Gate B
adjudicator receives the full `iss_state` and the full support map
(including `JOINT_CROSS_SOURCE` entries), not just the B-2 label. B-2
never adjudicates novelty (Section 2.7).

**Remaining question:** Is the Section 8.5 safeguard ("the B-2 trace's
`iss_state` field must be preserved end-to-end and forwarded to the
downstream Gate B adjudicator") sufficient, or should the spec also
prescribe a concrete Gate B handoff format (i.e. the JSON schema that
Gate B receives)? The auditor may direct that a Gate B handoff schema
be added before implementation.

### 9.10 Double-adjudicator qualification (round-75, retained)

Section 3.6 introduces a double-adjudication protocol with a ≥ 80% raw
agreement threshold. The auditor must adjudicate whether this threshold
and protocol are adequate.

**Question:** Is ≥ 80% raw agreement the right threshold? If the
agreement rate is, say, 75%, should the held-out set be revised (cases
too ambiguous) or should the protocol be strengthened (e.g. triple
adjudication, or a formal ontology of permitted inferences)? The auditor
may direct a different threshold or protocol.

### 9.11 RESOLVED (round-76) — formerly "true ISS_neither control category"

**Resolved (round-76):** the round-75 open question 9.11 asked whether
the "true `ISS_neither`" control category was constructible. The
round-76 verdict established that `ISS_neither` (as defined in
round-75) was **non-constructible** under the span-map definition of
`Justified()` — it was mathematically equivalent to `REDUNDANT_SUPPORT`,
not to "jointly necessary but not independently attributable" (which is
`ISS_both`). The round-76 amendment eliminates `ISS_neither` and
replaces it with `REDUNDANT_SUPPORT`, which IS constructible: a
candidate whose atomic claims all have supporting spans in Source A AND
all have supporting spans in Source B independently.

The held-out set (Section 3.2) now requires at least 2
`REDUNDANT_SUPPORT` cases (instead of the non-constructible "true
`ISS_neither`" cases). No open question remains on this topic.

### 9.12 Inference rule taxonomy for JOINT_CROSS_SOURCE — RESOLVED (round-78)

**Resolved (round-78):** the frozen taxonomy is now defined at Section
2.6.8 (taxonomy version `inference-rules-v1`). The taxonomy contains 8
named rules (`COMPOSITION`, `ABSTRACTION`, `SPECIALIZATION`,
`GENERALIZATION`, `CAUSAL_TRANSFER`, `MECHANISTIC_ANALOGY`,
`STRUCTURAL_ANALOGY`, `FUNCTIONAL_ANALOGY`) plus `OTHER`. Each rule
has a definition, admissibility criteria, examples (mapped to public
ADV cases), and adversarial counterexamples. `OTHER` cannot
automatically qualify a `JOINT_CROSS_SOURCE` claim as a B-2 pass — it
requires independent adjudication and is reported separately. A
detector that emits `OTHER` for more than 20% of its
`JOINT_CROSS_SOURCE` entries is flagged for review.

The schema (Section 3.7.1, `b2-trace-v3`) enforces the enum via
requirement 8 (Section 3.7.2).

**Remaining question:** is the initial 8-rule taxonomy adequate, or
should additional rules be added before implementation? The auditor
may direct additions based on the held-out set construction. The
taxonomy is versioned (`inference-rules-v1`); future additions require
a new version number and re-adjudication.

---

## 10. Files

This spec refers to the following files in the adversarial v2 directory:

- `sources.md` — canonical source_a, source_b, definition of cross-source
  synthesis.
- `cases/ADV-01.md` through `cases/ADV-13.md` — per-case semantic
  rationales. Each rationale walks through the lexical overlap audit,
  semantic content, mapping to Source A, mapping to Source B, cross-source
  synthesis argument, and independent semantic verdict.
- `test_fixture.json` — bare test cases (candidate + sources + expected
  label), used as the public calibration set.
- `diagnostic_runner.py` — runs the current lexical detector against the
  fixture as a diagnostic.
- `diagnostic_results.json` — machine-readable diagnostic output.
- `diagnostic_results.md` — human-readable diagnostic report.

The spec itself is at:

- `REPAIR_SPEC.md` (this document).

The spec is **not** committed to the engine repository. It lives in the
audit directory until the auditor accepts it, at which point the auditor
may direct that it be promoted to the engine repository's
`experiments/measurement_discrimination/` directory alongside the existing
R5.1 design revision document.

---

## 11. Status

```text
Spec status:                    AMENDED (round-79) — FROZEN FOR RE-ADJUDICATION
Original freeze:                commit 8a84fdc, 2026-08-09 (round-73)
First amended freeze:           commit 4bc945d, 2026-08-10 (round-74)
Second amended freeze:          commit 3076d3a, 2026-08-10 (round-75)
Third amended freeze:           commit 9b4d843, 2026-08-10 (round-76)
Fourth amended freeze:          commit 7f2977a, 2026-08-10 (round-77)
Fifth amended freeze:           commit 015b735, 2026-08-10 (round-78)
Sixth amended freeze:           this revision, 2026-08-10 (round-79)
Implementation status:          NOT STARTED — blocked on round-79 re-adjudication
Production substrate status:    UNCHANGED — no modifications made
Protocol B status:              BLOCKED — blocked on implementation freeze + final
                                independent adjudication (Section 7.7)
Lexical detector status:        FROZEN at commit 20ac268 — no re-tuning
                                permitted
Adversarial v2 diagnostic:      6/13 mismatches (3/9 adversarial matches)
                                — canonical evidence that lexical detector
                                does NOT solve paraphrase leakage
Trace schema version:           b2-trace-v3 (round-77; source_support structure
                                with SOURCE_LOCAL + JOINT_CROSS_SOURCE)
Inference-rule taxonomy:        inference-rules-v1 (round-78; 8 named rules
                                + OTHER; frozen at Section 2.6.8)
Verification ordering:          8-step mandatory sequence (round-79; frozen
                                at Section 2.6.9; classification ≠ validity)

Round-74 conditions resolved (commit 4bc945d):
  1. Operational Justified()          — new Section 2.6
  2. Trace != evidence                — new Section 3.5
  3. LLM instrument freezing          — new Section 5.7 + Section 8.6
  4. Held-out genuinely blind         — Section 3.2.2
  5. Multiple source pairs (mandatory)— Section 3.2.1
  6. TP/TN/FP/FN by category          — Section 3.2.3
  7. B-2 vs discovery separation      — new Section 2.7 + Section 8.5
  +  Wording correction               — Sections 1.1, 1.5, 6

Round-75 conditions resolved (commit 3076d3a):
  1. Separate UNSUPPORTED from ISS_neither
  2. Independent double-adjudication  — new Section 3.6
  3. Freeze concrete trace JSON schema — new Section 3.7 (b2-trace-v1)
  +  Section 5.1 refinement: audit trigger, not proof of tuning

Round-76 condition resolved (commit 9b4d843):
  1. Eliminate non-constructible ISS_neither; replace with REDUNDANT_SUPPORT

Round-77 condition resolved (commit 7f2977a):
  1. Add JOINT_CROSS_SOURCE support mechanism (Section 2.6.2-2.6.7, 3.7)

Round-78 conditions resolved (commit 015b735):
  1. Decouple ISS_both from JOINT_CROSS_SOURCE
  2. Freeze inference-rule taxonomy (inference-rules-v1)

Round-79 condition resolved (this revision):
  1. Explicitly state that inference-rule classification does not
     establish derivation validity; freeze the 8-step verification
     ordering.
     — new Section 2.6.9 (8-step mandatory verification sequence;
       classification is classification ontology, not inference engine;
       step 5 = independent judgment of derivation validity)
     — Section 2.7 anti-regression item 7 (8-step ordering mandatory;
       accepting based solely on classification is critical regression)
     — Section 8.5 anti-regression (classification ≠ validity rule;
       step 5 independent judgment required)
     — Section 11 status (verification ordering line added)

Four-state ontology (round-76, retained; round-78 decoupled):
  ISS_one            → REJECT                  (source-local leakage)
  ISS_both           → ALLOW                   (cross-source synthesis — COUNTERFACTUAL, not tied to JOINT_CROSS_SOURCE)
  REDUNDANT_SUPPORT  → ALLOW (reported separately) (both sources independently justify)
  UNSUPPORTED        → NOT_ADJUDICATED_BY_B2   (forwarded to Gate B)

Two support types (round-77):
  SOURCE_LOCAL         — single-source span(s) asserting the claim
  JOINT_CROSS_SOURCE   — A-spans + B-spans + inference_rule → derived claim
                         (5 anti-cheating conditions mandatory, Section 2.6.7)
                         (inference_rule from frozen taxonomy, Section 2.6.8)

Key principle (round-78):
  Evidence type determines how an atomic claim is supported.
  Counterfactuals determine the candidate's ISS state.
  Do not conflate those two levels.
  ISS_both is a property of the CANDIDATE.
  JOINT_CROSS_SOURCE is a property of an EVIDENCE PATH for an atomic claim.
  The latter is NOT a necessary condition for the former.

Boundary (round-77, retained; round-78 clarified):
  B-2 establishes provenance topology (source-local / cross-source / redundant / unsupported)
  Gate B establishes discovery validity (is the jointly-supported relationship a valid mechanism?)
  B-2 never adjudicates novelty or invention quality.
  B-2 adjudicates: "Does this relationship follow from the specified source
  components under a frozen inference rule?" — NOT "Is this a good invention?"

Open questions remaining for auditor:
  9.1  catastrophic-failure definition refinement
  9.3  acceptable LLM providers
  9.4  N for majority vote (5 vs 10)
  9.7  re-freeze criteria (proposed default in Section 9.7)
  9.8  operational Justified() adequacy
  9.9  B-2 / Gate B boundary preservation — RESOLVED (round-76):
       remaining question is whether a concrete Gate B handoff schema
       is needed
  9.10 double-adjudicator qualification: is ≥80% raw agreement the
       right threshold?
  9.11 RESOLVED (round-76) — formerly "true ISS_neither control category,"
       now moot
  9.12 RESOLVED (round-78) — inference rule taxonomy frozen at
       inference-rules-v1 (Section 2.6.8); remaining question: is the
       initial 8-rule taxonomy adequate, or should additions be made
       before implementation?
```

This amended spec is now awaiting the auditor's re-adjudication per
Section 7.2. No implementation work may begin until the auditor accepts
the amended spec (unconditionally or with conditions).

Per the round-79 verdict: "Once that sentence/order is frozen and
re-adjudicated, I would consider the specification sufficiently closed
to move out of design: **blind held-out construction → implementation
→ adversarial audit → freeze → discrimination execution → independent
adjudication.**" The auditor also noted: "The next phase should
finally generate **evidence about the engine**, rather than another
increasingly elaborate specification." If the auditor accepts this
round-79 amended spec, the workflow proceeds to held-out set
construction (Section 7.3) and implementation (Section 7.4).
