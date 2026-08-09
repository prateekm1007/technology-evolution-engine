# B-2 REPAIR SPECIFICATION — Independent Semantic Support

**Status:** AMENDED SPEC — FROZEN FOR RE-ADJUDICATION (round 74)
**Original freeze:** 2026-08-09 (commit `8a84fdc`)
**Amended freeze:** 2026-08-10 (this revision)
**Frozen by:** protocol-B implementer (this agent)
**Adjudication status:** Round-73 verdict ACCEPT WITH CONDITIONS. This amended
revision resolves all 7 conditions + the wording correction. Awaiting
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
implementation work begins. The round-74 verdict (ACCEPT WITH CONDITIONS)
directed that this spec be amended to resolve 7 conditions before
re-adjudication.

**Adjudication history:**

| Round | Verdict | Action |
|-------|---------|--------|
| 73 | — | Spec drafted and frozen at commit `8a84fdc` |
| 74 | ACCEPT WITH CONDITIONS | This amended revision resolves all 7 conditions + wording correction; frozen for re-adjudication |
| 75+ | PENDING | Re-adjudication by external auditor |

**Round-74 conditions resolved by this amendment:**

1. Operational definition of `Justified()` (new Section 2.6).
2. Justification trace is an auditable claim, not evidence (new Section 3.5).
3. LLM instrument freezing requirements (new Section 5.7).
4. Held-out set must be genuinely blind — no rationale exposure (Section 3.2
   strengthened).
5. Held-out set must use multiple source pairs, at least one unrelated to
   mineralization — MANDATORY (Section 3.2 + 9.5 revised).
6. 11/12 is qualification threshold only; must report TP/TN/FP/FN/precision/
   recall/FPR/FNR by category (Section 3.2 + 9.1 revised).
7. B-2 is a leakage instrument, NOT a novelty detector (new Section 2.7 +
   Section 8.5).

**Wording correction:** "semantic failure that no lexical detector can solve"
→ "not reliably resolved by the current lexical feature set" (Sections 1.1,
1.5, 6).

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

A candidate has independent semantic support from **neither** source iff:

```
ISS_neither(c, {A, B})  :=  NOT IndependentSemanticSupport(c, A, {A, B})  AND  NOT IndependentSemanticSupport(c, B, {A, B})
```

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

The B-2 detector's decision criterion is:

```
                ┌─ ALLOW    if ISS_both(c, {A, B})    (cross-source synthesis)
detector(c) ───┼─ ALLOW    if ISS_neither(c, {A, B})  (genuinely novel)
                └─ REJECT   if ISS_one(c, {A, B})      (source-local — leakage)
```

Equivalently: REJECT iff the candidate has independent semantic support from
exactly one source.

This criterion is **counterfactual**: it requires evaluating whether the
candidate would still be justified if one source were removed. A lexical
detector cannot compute this counterfactual, because the counterfactual
depends on the candidate's *meaning*, not its surface form.

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
| ADV-09 | `quantum entanglement` | NO | NO | ISS_neither | ALLOW |
| ADV-10 | `calcium phosphate` | YES (literal quote) | NO | ISS_one | REJECT |
| ADV-11 | `biomineralization` | YES (Source A's bone mineralization is an instance) | YES (Source B's diatom silica shell formation is an instance) | ISS_both | ALLOW |
| ADV-12 | `mineralizing` | YES (morphological inflection of Source A's `mineralization`) | NO | ISS_one | REJECT |
| ADV-13 | `pseudomineralization` | YES (falsity modifier on Source A's `mineralization`) | NO | ISS_one | REJECT |

The rationale files at `cases/ADV-NN.md` contain the full semantic
justification for each row's ISS determination.

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

#### 2.6.2 Span-mapped evidence

A candidate `c` is `Justified(c, corpus)` iff **every** atomic claim in
`Atoms(c)` has a **supporting span** in the corpus.

A **supporting span** for atomic claim `a` in source `S` is a contiguous
substring of `S` that an independent adjudicator can identify as asserting
`a` (either literally or via standard scientific inference — synonymy,
hypernymy, or direct implication). The supporting span is recorded as a
character-offset range `(start, end)` into `S`.

Concretely, the detector's trace must include, for each atomic claim:

- the claim itself (e.g. `{mediator: enzyme_catalyst}`),
- the source it is mapped to (`A` or `B`),
- the supporting span as a verbatim quote from that source,
- the character offsets of the span in the source.

A claim with no supporting span in either source is **unsupported**. A
candidate with any unsupported atomic claim is `NOT Justified(c, {A, B})`,
which (per Section 2.4) places it in `ISS_neither` and yields ALLOW —
**but** the unsupported claim is reported in the trace, and the auditor
may flag it for downstream discovery adjudication (Section 2.7).

#### 2.6.3 The counterfactual test, operationalized

With `Justified()` defined via span-mapped evidence, the counterfactual
`NOT Justified(c, {A, B} \ {S})` becomes operationally testable:

> Remove source `S` from the corpus. Re-evaluate every atomic claim in
> `Atoms(c)`. If any atomic claim that was previously supported by `S` now
> has no supporting span in the remaining source, then `c` is NOT justified
> by `{A, B} \ {S}` — i.e. `c` has independent semantic support from `S`.

The detector's trace must include, for each source `S`:

- the set of atomic claims supported by `S`,
- the set of atomic claims supported by the other source,
- the set of atomic claims supported by neither source (unsupported),
- the counterfactual verdict: "removing `S` would leave claims {…}
  unsupported, therefore `c` is [NOT] justified by `{A,B}\{S}`."

#### 2.6.4 Independent adjudication of the span map

The span map is the detector's **claimed** evidence. It is not proof. The
auditor (or an independent adjudicator) must verify, for each atomic claim
in a held-out case, that:

1. The supporting span is actually present in the cited source at the cited
   offsets.
2. The supporting span actually asserts the atomic claim (i.e. the
   claim-to-span mapping is semantically valid).
3. No atomic claim has been silently dropped or fabricated.

A trace whose span map fails verification on any atomic claim is rejected,
regardless of the detector's label. This is the operational mechanism that
prevents the detector from generating coherent false explanations
(Section 3.5).

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

#### 2.6.6 What this does NOT rule out

This operational definition does not rule out:

- **Synonymy and hypernymy in span mapping.** The supporting span may
  assert the atomic claim via synonymy (`skeletal` ↔ `bone`) or hypernymy
  (`enzyme` ↔ `silicatein`). The adjudicator's judgment applies.
- **Multi-span support.** An atomic claim may be supported by the
  conjunction of two spans in the same source (e.g. one span asserting
  the substrate, another asserting the mediator). The trace must cite
  both spans.
- **Inference from context.** An atomic claim may be supported by the
  source's overall context rather than a single sentence. The adjudicator's
  judgment applies, but the trace must still cite the specific spans that
  ground the inference.

### 2.7 B-2 is a leakage instrument, NOT a novelty detector (round-74 condition 7)

The B-2 decision criterion (Section 2.4) places `ISS_neither` candidates
in the ALLOW branch. This means: a candidate whose atomic claims are not
independently supported by either source is allowed to pass B-2.

This is correct **for leakage detection** — B-2's job is to reject
source-local derivatives, not to evaluate whether a candidate is a good
invention. But it creates a subtle failure mode: `ISS_neither` does not
mean "this is a good invention." It could simply be nonsense.

Therefore B-2 must remain distinct from **discovery adjudication** (Gate B /
Gate C in the engine's gate hierarchy). The two gates evaluate different
properties:

| Gate | Question | Outcome |
|------|----------|---------|
| B-2 (this spec) | Is the candidate leaked from one source? | REJECT iff `ISS_one`; ALLOW otherwise |
| Gate B / discovery | Is the candidate a valid, meaningful mechanism? | Separate adjudication, separate criteria |

A candidate that passes B-2 via `ISS_neither` is **not blocked by B-2**,
but it may still be rejected by Gate B for being nonsensical, untestable,
or otherwise invalid as a mechanism proposal. B-2 must not quietly become
a novelty detector by absorbing Gate B's responsibilities.

**Implementation requirement:** The detector's trace must explicitly flag
`ISS_neither` cases as "passed B-2 leakage check; not adjudicated for
discovery validity." The downstream Gate B adjudicator must receive this
flag and must NOT treat B-2 passage as evidence of discovery validity.

**Anti-regression requirement (Section 8.5):** The spec, the implementation,
and the audit must all preserve the B-2 / Gate B distinction. Any attempt
to expand B-2's criterion to include novelty evaluation (e.g. "REJECT if
`ISS_neither` because the candidate is nonsense") is a scope creep that
must be rejected by the auditor.

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
- Contains at least 12 cases, distributed across Modes A/B/C.
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
the held-out set. A drop of more than 1 case in any category is evidence of
tuning and triggers rejection of the implementation.

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
adjudicated per this spec AND the `ISS_neither` candidates are reported
separately from `ISS_both` candidates (Section 8.5).

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

### 8.5 B-2 must remain a leakage instrument, NOT a novelty detector (round-74 condition 7)

Per Section 2.7, B-2 evaluates leakage (does the candidate derive from one
source alone?), NOT discovery validity (is the candidate a good invention?).
The two gates must remain distinct.

Anti-regression safeguards:

- The B-2 criterion must NOT be expanded to include novelty evaluation. Any
  proposal to add "REJECT if `ISS_neither` because the candidate is
  nonsense" is scope creep and must be rejected by the auditor.
- The B-2 trace's `ISS_neither` flag must be preserved end-to-end and
  forwarded to the downstream Gate B adjudicator. The downstream gate must
  NOT treat B-2 passage as evidence of discovery validity.
- The Protocol B discrimination run must report `ISS_neither` cases
  separately from `ISS_both` cases. A positive discrimination run driven
  entirely by `ISS_neither` candidates (i.e. candidates that pass B-2
  because they are unsupported by either source) is NOT evidence that the
  engine performs cross-source discovery — it is evidence that the engine
  produces unsupported candidates that the detector correctly declines to
  flag as leakage.

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

### 9.2 Justification trace format — PARTIALLY RESOLVED (round-74)

**Resolved:** The 5-element trace (Section 3.3) is retained. The trace must
be machine-parseable into the structured format specified in Section 3.5
(atomic claim decomposition, span map, counterfactual evaluation). Free-text
traces are not acceptable.

**Remaining question:** Is the machine-parseable schema in Section 3.5
sufficient, or should the spec prescribe a concrete JSON schema (field
names, types, nesting)? The auditor may direct that a concrete JSON schema
be added before implementation.

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

### 9.9 NEW (round-74) — B-2 / Gate B boundary preservation

Section 2.7 and Section 8.5 specify that B-2 must remain a leakage
instrument and must not absorb Gate B's discovery-validity
responsibilities. The auditor must adjudicate whether the safeguards are
sufficient.

**Question:** Are the safeguards in Section 8.5 sufficient to prevent B-2
from quietly becoming a novelty detector? Or should the spec prescribe a
concrete interface contract between B-2 and Gate B (e.g. a structured
handoff format that forces the `ISS_neither` flag to be preserved
end-to-end)?

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
Spec status:                    AMENDED — FROZEN FOR RE-ADJUDICATION (round 74)
Original freeze:                commit 8a84fdc, 2026-08-09
Amended freeze:                 this revision, 2026-08-10
Implementation status:          NOT STARTED — blocked on amended-spec re-adjudication
Production substrate status:    UNCHANGED — no modifications made
Protocol B status:              BLOCKED — blocked on implementation freeze + final
                                independent adjudication (Section 7.7)
Lexical detector status:        FROZEN at commit 20ac268 — no re-tuning
                                permitted
Adversarial v2 diagnostic:      6/13 mismatches (3/9 adversarial matches)
                                — canonical evidence that lexical detector
                                does NOT solve paraphrase leakage

Round-74 conditions resolved:
  1. Operational Justified()          — new Section 2.6
  2. Trace != evidence                — new Section 3.5
  3. LLM instrument freezing          — new Section 5.7 + Section 8.6
  4. Held-out genuinely blind         — Section 3.2.2
  5. Multiple source pairs (mandatory)— Section 3.2.1
  6. TP/TN/FP/FN by category          — Section 3.2.3
  7. B-2 vs discovery separation      — new Section 2.7 + Section 8.5
  +  Wording correction               — Sections 1.1, 1.5, 6

Open questions remaining for auditor:
  9.1  catastrophic-failure definition refinement
  9.2  concrete JSON schema for trace (yes/no)
  9.3  acceptable LLM providers
  9.4  N for majority vote (5 vs 10)
  9.7  re-freeze criteria (proposed default in Section 9.7)
  9.8  operational Justified() adequacy (NEW)
  9.9  B-2 / Gate B boundary preservation (NEW)
```

This amended spec is now awaiting the auditor's re-adjudication per
Section 7.2. No implementation work may begin until the auditor accepts
the amended spec (unconditionally or with conditions).
