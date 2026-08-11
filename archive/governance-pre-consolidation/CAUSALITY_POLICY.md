# CAUSALITY_POLICY — Phase 7C.1 Constitutional Document

**Status:** constitutional document (causality rules for the CAPABILITY_MODEL).
**Location:** repo root (peer of CAPABILITY_ONTOLOGY.md, EVIDENCE_PROTOCOL.md).
**Phase:** 7C.1 (per CEO ruling, commit `3922a3d`).

> classification ≠ capability
> capability ≠ enablement
> enablement ≠ prediction
>
> That is the chain that prevents the entire project from collapsing
> into an increasingly sophisticated form of pattern matching.
> — CEO ruling, Phase 7C.1

This document defines what counts as causality, enablement, and
substitutability in the CAPABILITY_MODEL. It defines what evidence is
admissible and inadmissible. It defines the confidence scale and
reviewer responsibilities. It is the guardrail that prevents the
graph from becoming "an increasingly sophisticated form of pattern
matching."

---

## 1. Definition of causality

**Causality** means: A → B because A *makes B possible* (not because
A *co-occurs with* B).

### The distinction

| Pattern | NOT causal | Causal |
|---|---|---|
| A and B appear in the same patent | co-occurrence | — |
| A and B are classified under the same CPC code | classification | — |
| A appears before B historically | temporal precedence | — |
| A's removal prevents B | — | causality |
| A's presence is necessary for B | — | causality |
| A creates the physical conditions for B | — | causality |

### The test

A causal claim "A causes B" must answer:

> If A did not exist, would B be impossible or significantly harder?

If the answer is "no" (B would still happen without A), the
relationship is NOT causal. It may be correlation, co-occurrence, or
classification — but it is not causality.

### What this means for the graph

Only edges of type REQUIRES can express causal claims in the current
(frozen, reduced) edge set. REQUIRES means: A *cannot function* without B.
This is a necessity claim, which is the strongest form of causal claim.

ENABLES and SUBSTITUTES_FOR are **suspended** per CEO Decision 2
(Phase 7C.1). They require more evidence than is currently available.

---

## 2. Definition of enablement

**Enablement** means: A *creates the conditions* for B to exist.

### The distinction from REQUIRES

- REQUIRES: A cannot function without B. (B is necessary for A.)
- ENABLES: A makes B possible. (A is sufficient for B.)

ENABLES is a **stronger** causal claim than REQUIRES, because:
- REQUIRES says "without B, A fails" — testable by removing B.
- ENABLES says "because of A, B can exist" — testable only by
  historical counterfactual (would B have appeared without A?).

### Why ENABLES is suspended

ENABLES requires **historical counterfactual evidence**: the claim
"A enabled B" means B would NOT have appeared without A. This is:
1. Hard to establish from patent text alone.
2. Susceptible to post hoc reasoning (the CEO's forbidden methodology).
3. Not yet supported by the frozen-time backtest (Phase 7D not executed).

Until the backtest demonstrates that ENABLES edges have predictive
validity (they predict what becomes possible), ENABLES is suspended.

### What ENABLES would require (for future authorization)

1. A historical case where A appeared, then B became possible within
   a defensible time window (T → T+n).
2. No other plausible explanation for B's appearance (no confounding
   variable C that also could have enabled B).
3. A human reviewer's assessment that the counterfactual holds.
4. Evidence recorded in the EdgeJustification schema (Decision 4).

---

## 3. Definition of substitutability

**Substitutability** means: A can replace B in *some specific context*
without loss of function.

### The distinction from co-occurrence

| Pattern | NOT substitutability | Substitutability |
|---|---|---|
| A and B are both batteries | similarity | — |
| A and B co-occur in patents | co-occurrence | — |
| A and B have similar embeddings | linguistic similarity | — |
| A can serve B's function in a specific design | — | substitutability |

### Why SUBSTITUTES_FOR is suspended

Substitutability is "notoriously difficult to establish" (per auditor
correction). It requires:
1. A specific context (what design? what application?).
2. Evidence that A serves B's function in that context.
3. Evidence that the substitution doesn't introduce unacceptable
   degradation.
4. A human reviewer's assessment that the substitution is real.

The current graph has 1 SUBSTITUTES_FOR edge (CONVERSION_REACTION
SUBSTITUTES_FOR INTERCALATION). This edge was FLAGGED in
EDGE_JUSTIFICATION.md because conversion reactions and intercalation
are fundamentally different mechanisms. You choose one or the other —
they are alternatives, not substitutes in the same design.

### What SUBSTITUTES_FOR would require (for future authorization)

1. A documented case where A was used in place of B in a real product.
2. Evidence that the substitution maintained function (possibly with
   trade-offs).
3. A human reviewer's assessment.
4. The context must be specified (not "A substitutes for B" but
   "A substitutes for B in context C under conditions D").

---

## 4. Admissible evidence

The following types of evidence are **admissible** for creating
edges:

| Evidence type | Confidence | When admissible |
|---|---|---|
| Patent CPC code | 1.0 (Explicitly stated) | The patent's CPC code directly maps to the capability per CPC_MAPPING.md |
| Patent claim text | 0.8 (Directly implied) | The claim text explicitly describes the relationship |
| Structural invariant | 0.5 (Structurally inferred) | The relationship is a structural necessity of the domain (e.g., electrochemical storage REQUIRES ion transport — ions must move for the reaction to occur) |
| Regulatory standard | 1.0 (Explicitly stated) | A regulation explicitly governs the capability |

### Admissibility rules

1. **CPC codes are admissible for EMBODIED_IN edges only.** A CPC
   code tells you a patent *is about* a capability; it does NOT tell
   you that capability A *REQUIRES* capability B. For REQUIRES edges,
   you need claim text or structural invariant evidence.

2. **Structural invariants are admissible for REQUIRES edges** at
   confidence 0.5 — but ONLY when the relationship is a physical
   necessity (not merely common practice). "Electrochemical storage
   REQUIRES ion transport" is admissible because ions must move for
   the reaction to occur — it's physics, not convention. "Battery
   REQUIRES thermal management" is NOT a structural invariant —
   many batteries operate without active thermal management. The
   latter would need claim-text evidence (0.8) not structural-
   invariant evidence (0.5).

3. **Claim text is admissible** when the patent or paper explicitly
   states the relationship. E.g., a patent claim that says "the
   anode requires an electrolyte" directly implies a REQUIRES edge.

4. **Regulatory standards are admissible** for REGULATED_BY edges
   at confidence 1.0 — regulations are explicit, externally
   validated, and legally binding.

---

## 5. Inadmissible evidence

The following types of evidence are **inadmissible** for creating
edges:

| Evidence type | Why inadmissible |
|---|---|
| Embedding similarity | Linguistic similarity ≠ functional substitutability. Per external review: "embedding similarity without a constraint layer will increase false-positive rate." |
| Co-occurrence in text | Co-occurrence ≠ causality. Two capabilities mentioned in the same patent may be alternatives, not dependencies. |
| Keyword overlap | Keyword matching is the CO_OCCURRENCE_MODEL's primitive. Using it in the CAPABILITY_MODEL would reproduce the saturation problem. |
| LLM-generated edges | LLM reasoning is opaque — no way to audit why an edge was created. Violates Law 8 (replayable evidence). |
| Temporal precedence alone | "A appeared before B" does not mean "A caused B." Post hoc ergo propter hoc is forbidden methodology. |
| Inventor hindsight | The inventor's stated intent is not available to the system at time T. Using it in the backtest is information leakage. |
| Retrospective explanation | "Of course it would predict X" is not a prediction. It's a rationalization. |
| Manual cherry-picking | Selecting only successful cases inflates precision. The system must report ALL flagged combinations. |

### The embedding policy (reinforced)

Per CEO Phase 6 Section 10 and this policy:

```
FORBIDDEN:
  embedding_similarity > threshold → create_edge

PERMITTED (only for candidate generation, not edge creation):
  embedding_similarity > threshold → generate_candidate
  candidate → constraint_evaluation (this policy)
  constraint_evaluation passes → human_review
  human_review approves → create_edge with admissible evidence
```

An embedding may suggest a candidate, but the edge must be created
with ADMISSIBLE evidence (Section 4), not with the embedding itself.

---

## 6. Confidence assignment

Per CEO Decision 5 (Phase 7C.1):

| Confidence | Meaning | When to use |
|---|---|---|
| 1.0 | Explicitly stated | Patent CPC code maps to capability; regulation explicitly governs capability |
| 0.8 | Directly implied | Patent claim text or paper abstract explicitly describes the relationship |
| 0.5 | Structurally inferred | Physical necessity of the domain (ions must move, electrons must be collected) |
| 0.2 | Speculative | Human reviewer's judgment without direct textual or structural evidence |

### Rules

1. **CPC-based EMBODIED_IN edges:** confidence 1.0. The CPC code
   is an explicit, externally validated classification.

2. **Claim-text-based edges:** confidence 0.8. The relationship is
   directly stated in the source text. The reviewer must quote the
   claim in the justification field.

3. **Structural-invariant REQUIRES edges:** confidence 0.5. The
   relationship is a physical necessity. The reviewer must explain
   the physical principle in the justification field.

4. **Speculative edges:** confidence 0.2. The reviewer believes the
   relationship holds but has no direct evidence. These edges should
   be rare and must be flagged for future validation. They cannot
   be used in the frozen-time backtest (which requires confidence
   ≥ 0.5).

5. **No edge below 0.2.** If the confidence is below 0.2, the edge
   is not created. It remains a candidate, not an edge.

---

## 7. Reviewer responsibilities

Every edge must have a reviewer. The reviewer is a human who:

1. **Reads the source document** (patent, paper, regulation) or
   verifies the structural invariant.

2. **Verifies the relationship type** is correct (EMBODIED_IN,
   REQUIRES, CONSTRAINS, or REGULATED_BY — the 4 authorized types).

3. **Verifies the evidence is admissible** per Section 4 (not
   embedding, not co-occurrence, not keyword overlap).

4. **Assigns confidence** per Section 6.

5. **Writes the justification** — a 1-2 sentence explanation of
   WHY this edge exists, citing the specific evidence (CPC code,
   claim text, physical principle, or regulation).

6. **Records their identity** (reviewer ID + date) in the
   EdgeJustification object.

### What the reviewer must NOT do

- Create ENABLES or SUBSTITUTES_FOR edges (suspended per CEO
  Decision 2).
- Accept embedding similarity as evidence.
- Accept co-occurrence as evidence of causality.
- Assign confidence > 0.5 without direct textual or structural
  evidence.
- Create edges without reading the source or verifying the
  invariant.

### Audit trail

The auditor will verify:
1. Every edge has an EdgeJustification with all required fields.
2. Every confidence is justified by the evidence type.
3. Every justification is specific (not generic boilerplate).
4. No ENABLES or SUBSTITUTES_FOR edges exist (suspended).
5. No edge was created from inadmissible evidence.

---

## Constitutional rules (per CEO Decisions 6-7)

The following rules are now constitutional:

```text
No edge exists without evidence.
```

```text
No capability exists without evidence.
No constraint exists without evidence.
No prediction exists without explanation.
```

These rules are enforced by this document and by the EVIDENCE_PROTOCOL.md.
A violation is a constitutional breach, not a code bug.

---

## The question has changed

The CEO's final instruction (Decision 10):

> The objective is no longer: 'Can we build the graph?'
> The objective is now: 'Can we trust the graph?'

This document is the trust framework. It defines what trust means
(admissible evidence + correct confidence + human review), what
trust doesn't mean (co-occurrence, embeddings, speculation), and
what happens when trust is violated (the edge is removed or the
graph is not used for prediction).

The next experiment is 5 patents. The question is not whether the
graph can be built — it can. The question is whether each edge
in it can be trusted.
