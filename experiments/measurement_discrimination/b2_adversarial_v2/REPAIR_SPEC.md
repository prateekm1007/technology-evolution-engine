# B-2 REPAIR SPECIFICATION — Independent Semantic Support

**Status:** FROZEN FOR INDEPENDENT ADJUDICATION
**Frozen at:** 2026-08-09
**Frozen by:** protocol-B implementer (this agent)
**Adjudication status:** PENDING — no implementation work may begin until this
spec is independently adjudicated by the external auditor.

**Supersedes:** The lexical detector at commit `20ac268`
(`b1_b2_verification._check_leakage`). That detector's 6/6 result on the
round-72 fixture is retained as an **engineering regression result only** and
must NOT be promoted to scientific evidence that paraphrase leakage has been
solved.

**Authority:** This spec is issued in response to the external auditor's
round-73 verdict, which adjudicated the B-2 v2 adversarial diagnostic
(6/13 mismatches across three semantic failure modes) and directed that a
repair specification be drafted and independently adjudicated before any
implementation work begins.

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
The mismatches cluster into three failure modes, each of which is a
**semantic** failure that no lexical detector can solve.

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
adversarially robust; it is tuned to a specific test fixture.

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
- Is kept blind to the implementer until the implementation freeze.
- Each case ships its own rationale file, so the auditor can independently
  verify the expected label without consulting the implementer.

The implementer's detector must achieve ≥ 11/12 on the held-out set to
qualify for the implementation freeze. A score below 11/12 means the
implementation has not established the semantic property.

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

---

## 6. Implementation-agnostic specification

This spec is silent on the implementation approach. The following approaches
are all acceptable in principle:

- **LLM-based:** an LLM is prompted with the candidate, Source A, and Source
  B, and is asked to produce the justification trace specified in Section
  3.3.
- **Symbolic:** a knowledge graph or ontology is used to evaluate hypernymy,
  umbrella scope, and concept-level reference.
- **Hybrid:** an LLM is used for the counterfactual evaluation; a symbolic
  checker is used to verify the LLM's trace.
- **Other:** any approach that produces the justification trace and passes
  the held-out set.

The spec does NOT prescribe:

- which LLM to use (if any),
- which ontology to use (if any),
- which prompt template to use (if any),
- which similarity metric to use (if any).

The spec prescribes ONLY:

- the property to be evaluated (Section 2),
- the decision criterion (Section 2.4),
- the justification trace format (Section 3.3),
- the held-out set performance requirement (Section 3.2),
- the anti-tuning safeguards (Section 5).

An implementation that satisfies these prescriptions is acceptable,
regardless of its internal approach.

---

## 7. Workflow

The workflow is sequential. Each stage gates the next.

### 7.1 Spec freeze (this document)

This document is frozen at the date above. No further edits may be made to
it without the auditor's explicit approval. The spec is now the canonical
reference for the B-2 repair.

### 7.2 Independent adjudication of spec (auditor)

The auditor reviews this spec and either:

- **Accepts** the spec as the canonical repair specification, OR
- **Rejects** the spec with specific objections, OR
- **Accepts with conditions** (e.g. changes to the held-out set size, the
  pass threshold, the justification trace format).

Implementation work may NOT begin until the auditor accepts the spec
(unconditionally or with conditions). The acceptance is recorded in
`worklog.md` as a new task entry.

### 7.3 Held-out set construction (auditor)

After the spec is accepted, the auditor constructs the held-out adversarial
set per Section 3.2. The held-out set:

- Is constructed using the same rationale-template as the public set.
- Contains at least 12 cases, distributed across Modes A/B/C.
- Is kept blind to the implementer until the implementation freeze.
- Each case ships its own rationale file.

The held-out set is stored at a path the auditor controls and is not
committed to the implementer's repository until the implementation freeze.

### 7.4 Implementation (engineer)

The engineer implements a detector that satisfies Sections 2, 3.3, 5, and 6.
The engineer may use the public adversarial set (`test_fixture.json`, 13
cases) as a calibration set during development. The engineer may NOT access
the held-out set.

The engineer produces:

- The detector implementation.
- A test harness that runs the detector against the public set and produces
  per-case justification traces.
- A test harness that accepts a held-out set (path TBD by auditor) and
  produces per-case justification traces.

### 7.5 Adversarial audit (auditor)

The auditor runs the engineer's detector against the held-out set and
inspects the justification traces per Section 3.4. The auditor either:

- **Accepts** the implementation (≥ 11/12 on held-out set, no anti-tuning
  red flags), OR
- **Rejects** the implementation with specific objections.

### 7.6 Implementation freeze

If the auditor accepts the implementation, the detector is frozen at its
current commit. No further tuning is permitted. The frozen detector is the
canonical B-2 detector for Protocol B.

### 7.7 Protocol B discrimination run

After the implementation freeze, Protocol B may proceed. The frozen detector
is used as the B-2 component of the Protocol B discrimination run.

If the discrimination run produces a positive result (engine arm
outperforms null arm), the result is **scientific evidence** that the
engine performs cross-source discovery — provided the detector has been
adjudicated per this spec.

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

---

## 9. Open questions for adjudication

The auditor must resolve the following open questions before implementation
may begin. The implementer may NOT make these decisions.

### 9.1 Held-out set size and pass threshold

This spec proposes ≥ 12 cases and ≥ 11/12 pass threshold (Section 3.2).
The auditor may adjust these numbers. The trade-off: a smaller set is
easier to construct but provides less statistical power; a larger set
provides more power but is more expensive to construct.

**Question:** Is ≥ 12 cases with ≥ 11/12 pass threshold acceptable?

### 9.2 Justification trace format

This spec proposes a 5-element justification trace (Section 3.3): candidate
semantic content, Source A coverage, Source B coverage, counterfactual
evaluation, decision. The auditor may require additional elements (e.g.
confidence scores, alternative interpretations) or may simplify the format.

**Question:** Is the 5-element justification trace format acceptable?

### 9.3 LLM-based implementation

This spec is implementation-agnostic (Section 6). However, the most natural
implementation is LM-based. The auditor may rule on whether an LLM-based
implementation is acceptable, and if so, what constraints apply (e.g.
model choice, prompt template disclosure, determinism requirements).

**Question:** Is an LLM-based implementation acceptable? If so, what
constraints apply?

### 9.4 Determinism and reproducibility

A semantic detector (especially an LLM-based one) may produce different
outputs on different runs. The auditor may rule on whether the detector
must be deterministic, and if not, how reproducibility is established
(e.g. via majority vote across N runs, via temperature 0, via seed
pinning).

**Question:** Must the detector be deterministic? If not, how is
reproducibility established?

### 9.5 Scope of the held-out set

The held-out set is constructed from the same source pair (bone
mineralization + diatom silica shell formation) as the public set. The
auditor may rule on whether the held-out set should use a different source
pair (to test generalization across domains) or the same source pair (to
test generalization across cases within a domain).

**Question:** Should the held-out set use the same source pair as the
public set, or a different source pair?

### 9.6 Adjudication of borderline cases

Some candidates may be genuinely ambiguous (e.g. a candidate that has
weak semantic support from both sources, but strong support from one).
The auditor may rule on how borderline cases are adjudicated (e.g. the
auditor's judgment is final; the candidate is excluded from the held-out
set; the candidate is included with a "borderline" label that the
detector may answer either way).

**Question:** How are borderline candidates adjudicated in the held-out
set?

### 9.7 Re-freeze criteria

If the implementation is rejected at the adversarial audit (Section 7.5),
the spec may be revised and re-frozen, or the implementation may be
re-attempted against the same spec. The auditor may rule on the
re-freeze criteria.

**Question:** Under what conditions may the spec be revised after
implementation has begun? Under what conditions may the implementation
be re-attempted without spec revision?

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
Spec status:                    FROZEN FOR INDEPENDENT ADJUDICATION
Implementation status:          NOT STARTED — blocked on spec adjudication
Production substrate status:    UNCHANGED — no modifications made
Protocol B status:              BLOCKED — blocked on implementation freeze
Lexical detector status:        FROZEN at commit 20ac268 — no re-tuning
                                permitted
Adversarial v2 diagnostic:      6/13 mismatches (3/9 adversarial matches)
                                — canonical evidence that lexical detector
                                does NOT solve paraphrase leakage
```

This spec is now awaiting the auditor's adjudication per Section 7.2.
