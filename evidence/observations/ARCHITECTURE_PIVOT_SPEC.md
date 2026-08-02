# ARCHITECTURE_PIVOT_SPEC — Phase 6 Architectural Investigation

**Status:** architectural spec (investigation, NOT implementation).
**Location:** `evidence/observations/` (per CEO v3.1: observation layer, not constitutional layer — this is a proposed architecture, not yet a rule).
**Phase:** 6 (architectural investigation authorized per CEO directive).
**Authorization scope:** investigation only. Implementation (Phase 7) requires separate explicit authorization.

> Status: Approved for architectural investigation.
> Objective: Replace the document/component/co-occurrence architecture
> with a capability/constraint architecture.
> Important: This is not a refactor. This is a change in the underlying
> scientific model.
> — CEO directive, Phase 6

This document captures the CEO's Phase 6 architectural directive as a
reviewable specification. It does NOT authorize implementation. It
sequences the investigation, applies the one-vertical constraint
concretely, and preserves the Phase 5 baseline. The CEO must
explicitly authorize Phase 7 (implementation) before any code is
written for the new architecture.

---

## 1. The decision: H0-architectural is defeated

The external review (Phase 5.F post-freeze) provided evidence that
defeated H0-architectural:

> Reject H0. Something is wrong beyond "insufficient data" —
> Observation 2 (shared components not scaling with total components)
> is the tell. If convergence were the right primitive, more ingestion
> should produce *more* overlap as the space fills in, not flatten.
> That's a signature of a representation problem, not a data problem.

The CEO's Phase 6 directive confirms: the document/component/co-
occurrence architecture is now an **experimental baseline only**.
The new working model is:

```text
capabilities
       +
constraints
       +
institutions
       +
economics
       +
time
       =
reachable possibilities
```

This is a change in the underlying scientific model, not a refactor.

### What H0-architectural's defeat authorizes

- Investigation of the capability-centric architecture.
- Reading the mandatory prior art.
- Defining the architectural spec (this document).
- Evaluating the CPC backbone against the one-vertical constraint.

### What H0-architectural's defeat does NOT authorize

- Writing code for the new architecture.
- Modifying the parser, formula, ontology, or graph.
- Building new ingestion pipelines.
- Adding embeddings, normalization rules, or synonyms.
- Deleting or modifying the Phase 5 baseline.

---

## 2. The old model (now baseline only)

The Phase 5 architecture remains available for:
- replay
- auditing
- comparison
- backtesting
- failure analysis

It is NOT deleted. It is NOT modified. It is the experimental
baseline against which the new architecture will eventually be
compared.

```text
documents
        ↓
components
        ↓
shared labels
        ↓
convergence
        ↓
invention
```

**Why it saturated (per external review):** Signal C measures
*co-occurrence* (shared vocabulary), not *enablement* (one capability
unlocking another). Two patents can share "electrode" and have nothing
causally to do with each other; two patents can share zero vocabulary
and be one unlock apart. Normalization (H1/H2/H3) would move the
plateau slightly higher and then it would reappear, because the
plateau is structural — the primitive is wrong.

---

## 3. The new scientific model

```text
capabilities
       +
constraints
       +
institutions
       +
economics
       +
time
       =
reachable possibilities
```

### The core theorem (rewritten)

```text
available capabilities
           +
removed constraints
           +
economic viability
           +
time
           =
reachable possibilities
```

This replaces the old theorem:

```text
shared labels → convergence → invention
```

The old theorem asked "Which labels are shared?"
The new theorem asks:

> Which capabilities exist?
> Which constraints remain?
> Which dependencies are missing?
> Which combinations have become reachable?
> Which combinations are becoming reachable?

---

## 4. Documents as evidence (the single biggest change)

Patents are not the truth. Papers are not the truth. Products are not
the truth. Documents provide **evidence**.

### Old architecture

```text
patent → node
```

### New architecture

```text
patent → evidence → capability
```

### Evidence object (spec)

```typescript
interface Evidence {
    id: string;
    sourceType:
        | "PATENT"
        | "PAPER"
        | "PRODUCT"
        | "REGULATION";
    sourceId: string;
    publicationDate: Date;
    confidence: number;
    claims: string[];
    citations: string[];
}
```

---

## 5. Node type system (replacing "component")

The existing concept of a "component" is too ambiguous. It conflates
materials, processes, capabilities, products, and institutions under
one label. The new model introduces a type system.

### NodeType enum (spec)

```typescript
enum NodeType {
    CAPABILITY,
    CONSTRAINT,
    MATERIAL,
    PROCESS,
    PRODUCT,
    MARKET,
    ORGANIZATION,
    INSTITUTION,
    REGULATION,
    INFRASTRUCTURE
}
```

### Why the type system matters (per external review)

> The goal is NOT synonym replacement. The goal is structural
> reasoning. Anode and cathode aren't just electrodes — they're
> electrodes with opposite polarity that only compose correctly with
> each other. Pure taxonomic collapsing loses that. You want typed
> nodes with typed relations, not a bag of synonyms.

### Capability-centered architecture (examples)

Instead of co-occurrence:

```text
anode ↔ cathode
```

Represent the underlying capability:

```text
anode → NEGATIVE_ELECTRODE_CAPABILITY ← cathode
```

Instead of:

```text
battery ↔ supercapacitor
```

Represent:

```text
battery → ENERGY_STORAGE_CAPABILITY ← supercapacitor
```

The capability is the primitive; the document-extracted label is
evidence of the capability, not the capability itself.

---

## 6. Edge system redesign

### Removed edge types

```text
related_to
similar_to
connected_to
```

These are too undirected and too ambiguous. They measure co-occurrence,
not causation.

### New EdgeType enum (spec)

```typescript
enum EdgeType {
    REQUIRES,
    ENABLES,
    SUBSTITUTES_FOR,
    BLOCKS,
    CONSTRAINS,
    DEPENDS_ON,
    EMBODIED_IN,
    REGULATED_BY,
    REDUCES_COST_OF
}
```

### Edge object (spec)

Every edge must contain:

```typescript
interface Edge {
    source: string;
    target: string;
    type: EdgeType;
    confidence: number;
    evidence: string[];
}
```

The `evidence` field is mandatory — no edge is created without
citing the document(s) that justify it. This is the "documents as
evidence" principle applied to the edge layer.

### Type system example (anode/cathode)

Incorrect (pure synonym collapsing):

```text
anode → electrode
cathode → electrode
```

Correct (structural reasoning):

```text
ANODE ─────► NEGATIVE_POLARITY
CATHODE ────► POSITIVE_POLARITY
ANODE ─────► REQUIRES_ELECTROLYTE
CATHODE ────► REQUIRES_ELECTROLYTE
```

The polarity and the electrolyte requirement are structural facts,
not taxonomy. They determine what can compose with what.

---

## 7. CPC and IPC as foundational layers

Per the external review:

> Before building your own ontology layer, check how much of H2 is
> already solved by ingesting CPC/IPC codes instead of raw extracted
> text labels. That alone could close a meaningful chunk of your
> 37.5% loss for free.

The USPTO's own classification system (now CPC, historically IPC)
is a human-curated, decades-refined, globally-consistent controlled
vocabulary. It already solves the anode/cathode/electrode taxonomy
problem. Building a custom ontology from scratch would duplicate
decades of work.

### Mandatory ingestion targets

- CPC (Cooperative Patent Classification)
- IPC (International Patent Classification)
- USPTO classifications

### PatentEvidence object (spec)

```typescript
interface PatentEvidence {
    patentId: string;
    cpcCodes: string[];
    ipcCodes: string[];
    claims: string[];
    citations: string[];
}
```

### Example: CPC hierarchy → capability

```text
H01M
  ↓
electrochemical systems
  ↓
energy storage capability
```

This is the CPC backbone doing the taxonomy work that Phase 5's
keyword extraction was failing to do.

---

## 8. Three independent scoring systems

The single convergence score is **deprecated**. It conflated three
independent questions. The new model separates them.

### Score A — Readiness

**Question:** Can it exist?

Inputs:
- TRL (Technology Readiness Level)
- manufacturing maturity
- infrastructure maturity
- scientific maturity
- cost curves

### Score B — Novelty

**Question:** Has this combination already been explored?

Inputs:
- combinatorial distance
- exploration score
- historical rarity
- exploitation score

**Per external review (Fleming):** recombining familiar components
reliably produces *incremental* invention (refinement), not
breakthrough. If the system is meant to find breakthroughs, high
novelty (productive unfamiliarity) may be the right signal — not
high convergence. This inverts the Phase 5 optimization target.

### Score C — Feasibility

**Question:** Would reality allow it?

Inputs:
- regulations
- economics
- manufacturing
- infrastructure
- physical constraints

**Per external review:** feasibility gates are boolean/threshold
conditions, not similarity scores. Blending them into a continuous
convergence number is why "premature" inventions and "impossible"
inventions currently look the same to the system.

---

## 9. Embedding policy

Embeddings are **forbidden as truth generators**.

### Forbidden

```text
embedding similarity → edge creation
```

### Permitted

```text
embedding similarity
    ↓
candidate generation
    ↓
constraint evaluation
    ↓
human review
    ↓
edge creation
```

**Per external review:** generic embeddings will increase false-
positive rate even as they fix false-negative rate, because linguistic
similarity and functional substitutability are different. A fuel cell
and a capacitor co-occur in energy-storage text and would share
embeddings, but they are not substitutable in almost any design. If
used at all, embeddings generate candidate edges for a downstream
functional/causal filter — they never serve as the edge weight itself.

---

## 10. Time as first-class infrastructure

The current architecture treats time as metadata. That is incorrect.
Time is a first-class dimension.

### TemporalState (spec)

```typescript
interface TemporalState {
    validFrom: Date;
    validTo: Date | null;
    confidence: number;
}
```

Every object must support temporal state. Every investigation must
answer:

> What existed?
> What changed?
> What became possible?

This is what enables the frozen-time backtest (Section 11).

---

## 11. Frozen-time backtesting (mandatory)

### Incorrect

```text
Could we predict the transistor?
```

This is hindsight-shaped pattern matching. Given 1946 inputs, hundreds
of component-combinations look equally convergent and never became
anything.

### Correct

```text
State = 1945
Input = information available in 1945
Prediction = ranked possibilities
Validation = 1946–1960
```

### Required metrics

```text
precision
recall
false positives
false negatives
```

**Per external review:** the real test is precision, not just recall.
How many things did the system flag at T that never happened at T+n?
A positive result on the transistor tells you almost nothing without
measuring how many false positives the system would also have
produced. This is the same discipline applied to MaestroAgent audits
internally — don't accept a claimed success without checking what it
would also have claimed falsely.

---

## 12. Scope restriction (the brutal constraint)

**Do not attempt to model the world. Model one vertical. Only one.**

This is the guardrail against ontology explosion. Per the CEO's
previous message: large systems rarely fail because of a single bug.
They fail because a series of small assumptions gradually become
unquestioned truths. The one-vertical constraint prevents the new
architecture from becoming "everything → ontology explosion →
collapse."

### Recommended domain

```text
electrochemical energy storage
```

### Maximum initial scope

| Entity       | Count |
|--------------|------:|
| Patents      |    50 |
| Papers       |    50 |
| Products     |    10 |
| Capabilities |    20 |
| Constraints  |    10 |
| Edge types   |     6 |

Nothing else. This is the cap. If the new architecture cannot
demonstrate value within this scope, it does not get to expand.

---

## 13. Mandatory reading (before implementation begins)

The team must study the following before implementation (Phase 7)
begins. Investigation (Phase 6) includes reading these.

1. **Youn, Strumsky, Bettencourt, Lobo — *Invention as a Combinatorial Process***
   - Used US patent records 1790–2010 to formally characterize
     invention as combinatorial process.
   - Found stable rate of "exploitation" (refining existing
     combinations) vs "exploration" (creating new combinations).
   - Used USPTO technology-code system (now CPC) as the node type —
     did not build an ontology from scratch.
   - **Direct relevance:** this is prior art for the exact system,
     run at patent-office scale, with published results.

2. **Lee Fleming — *Recombinant Uncertainty in Technological Search***
   - Builds on Schumpeterian innovation-as-recombination.
   - Argues technological uncertainty comes from combining unfamiliar
     components.
   - Empirical finding: recombining familiar components does NOT
     reliably reduce inventive uncertainty; refining already-used
     combinations does.
   - **Direct relevance:** if the system is meant to find
     breakthroughs, high convergence (familiar combination) predicts
     the wrong thing. The system may need to score for productive
     unfamiliarity.

3. **Brian Arthur — *The Nature of Technology***
   - Technology as recursive combination of existing technology to
     satisfy a purpose.
   - **Direct relevance:** this is where the "capability graph, not
     component graph" framing comes from.

4. **Stuart Kauffman — *The Adjacent Possible***
   - What's reachable in one combinatorial step from the current
     state, not what exists now.
   - **Direct relevance:** the "reachable possibilities" primitive
     in the new model.

5. **Martin Weitzman — *Recombinant Growth* (1998 QJE)**
   - Formal economic model of ideas-combining-into-ideas.
   - Growth-rate implications.
   - **Direct relevance:** the economics dimension of the new model.

6. **Hidalgo & Hausmann — *Economic Complexity / Product Space***
   - Capability space where a country's/firm's reachable product set
     depends on which capabilities it already holds.
   - **Direct relevance:** same structure as the "which inventions
     are premature" question, applied to nations instead of
     technologies.

---

## 14. Investigation sequence

This is the proposed sequence for Phase 6 investigation. Each step
produces a reviewable artifact. No step writes code for the new
architecture.

### Step 1: Read the mandatory prior art

Read all 6 works (Section 13). Produce a brief reading note for
each, capturing:
- the formal result
- the method
- the direct relevance to this architecture
- any caveats or limitations

**Deliverable:** `evidence/observations/prior_art_notes.md`

### Step 2: Evaluate the CPC backbone

Fetch a small sample of USPTO patents in the electrochemical energy
storage vertical. Check whether their CPC codes provide a more
grounded taxonomy than Phase 5's keyword extraction. Quantify: how
many of the 37.5% signal-loss gaps would CPC close for free?

**Deliverable:** `evidence/observations/cpc_backbone_evaluation.md`

### Step 3: Scope the one vertical

Define what electrochemical energy storage looks like under the new
model:
- Which 50 patents? (CPC code H01M and subclasses)
- Which 50 papers? (arXiv + Nature/Science in the domain)
- Which 10 products? (commercial batteries, supercapacitors, fuel cells)
- Which 20 capabilities? (energy storage, charge/discharge, etc.)
- Which 10 constraints? (energy density, cost, safety, etc.)
- Which 6 edge types? (from the EdgeType enum, pick the 6 most relevant)

**Deliverable:** `evidence/observations/vertical_scope_electrochemical.md`

### Step 4: Define the migration path

Document how the Phase 5 baseline maps to the Phase 7 target:
- What gets preserved (the graph, the snapshots, the measurement
  infrastructure)
- What gets deprecated (the convergence formula, the single-score
  model, the component-as-catch-all type)
- What gets added (the type system, the three scores, the temporal
  state, the CPC backbone)
- What gets replaced (the parser, the formula, the ontology)

**Deliverable:** `evidence/observations/migration_path.md`

### Step 5: Produce the Phase 7 authorization request

Synthesize Steps 1-4 into a single document that the CEO can review
to decide whether to authorize Phase 7 (implementation). This
document must answer:
- Has the prior art confirmed the architecture?
- Does the CPC backbone close enough of the gap to justify the
  migration cost?
- Is the one-vertical scope well-defined enough to start?
- What is the constitutional risk of the migration?
- What is the expected gain?

**Deliverable:** `evidence/observations/phase7_authorization_request.md`

### Step 6: Stand down

After Step 5, stand down. The CEO decides whether to authorize
Phase 7. No implementation work begins without explicit authorization.

---

## 15. Discipline constraints (carried from Phase 5)

The Phase 5 discipline applies to Phase 6 investigation:

1. **measurement ≠ explanation ≠ intervention.** The new architecture
   is currently an explanation. The investigation (Steps 1-5) produces
   measurements. Phase 7 (implementation) is intervention, which
   requires explicit authorization.

2. **observation ≠ governance.** This spec document is in
   `evidence/observations/`, NOT in the constitutional layer. It is
   a proposed architecture, not yet a rule. If/when the CEO
   authorizes Phase 7, the spec might get promoted to constitutional
   (replacing or amending INVENTION_COMPILER.md). Until then, it
   remains an observation.

3. **H0 as default.** H0-architectural is defeated. But H0-
   implementation is a separate question: "Is the current codebase
   sufficient, and does the migration to the new architecture justify
   the implementation cost?" That question is not yet answered. It
   will be addressed in Step 5 (the Phase 7 authorization request).

4. **the brutal constraint.** One vertical. Scope caps (50/50/10/20/10/6).
   No ontology explosion. No modeling the world.

5. **no premature implementation.** No code for the new architecture
   until Phase 7 is authorized. No parser changes. No formula changes.
   No graph changes. No new modules.

6. **baseline preservation.** The Phase 5 architecture is NOT deleted.
   It remains available for replay, auditing, comparison, backtesting,
   and failure analysis. It is the experimental baseline against
   which the new architecture will eventually be compared.

---

## 16. What this document does NOT do

- It does NOT authorize implementation.
- It does NOT modify the parser, formula, ontology, or graph.
- It does NOT delete or modify the Phase 5 baseline.
- It does NOT write any code for the new architecture.
- It does NOT promote itself to the constitutional layer.
- It does NOT close F-039 (the saturation finding stands as a
  measurement of the Phase 5 baseline).
- It does NOT override the CEO's "do not build semantic matching"
  instruction (the embedding policy in Section 9 reinforces it).

---

## 17. What this document DOES do

- It captures the CEO's Phase 6 directive as a reviewable spec.
- It sequences the investigation into 6 steps with concrete deliverables.
- It applies the one-vertical constraint (electrochemical energy storage).
- It preserves the Phase 5 baseline as experimental baseline.
- It carries the Phase 5 discipline forward.
- It produces the artifacts the CEO needs to decide whether to
  authorize Phase 7 (implementation).

---

## Implementation status

| Item | Status |
|---|---|
| H0-architectural | DEFEATED (per external review + CEO directive) |
| Phase 6 investigation | AUTHORIZED (this document) |
| Phase 7 implementation | NOT AUTHORIZED (requires separate explicit CEO directive) |
| Phase 5 baseline | PRESERVED (experimental baseline, not deleted) |
| Parser | FROZEN (no changes) |
| Formula | FROZEN (no changes) |
| Ontology | FROZEN (no changes) |
| Graph | FROZEN (no changes) |
| Constitutional layer | UNCHANGED (7 mandatory reads) |
| This document | evidence/observations/ (observation layer, NOT constitutional) |

**The next step is Step 1: read the mandatory prior art.** The CEO
has authorized investigation. The investigation has a sequence. The
sequence produces reviewable artifacts. No implementation begins
until Phase 7 is explicitly authorized.
