# CAPABILITY_ONTOLOGY — Phase 6 Constitutional Document

**Status:** constitutional document (new architecture's ontology definition).
**Location:** repo root (peer of CONSTITUTION.md, CONVERGENCE.md, INVENTION_COMPILER.md).
**Phase:** 6 (architectural investigation; implementation NOT yet authorized).
**Authorization scope:** defines the new architecture. Implementation (Phase 7) requires separate explicit authorization.

> Do not ask: "Which labels are shared?"
> Ask:
>   Which capabilities exist?
>   Which constraints remain?
>   Which dependencies are missing?
>   Which combinations have become reachable?
>   Which combinations are becoming reachable?
> — CEO directive, Phase 6, Section 15

This document is the founding constitutional document of the capability-
centric architecture. It defines the node types, edge types, evidence
schema, temporal schema, scope restriction, embedding policy, and the
three independent scores. It is a peer of CONVERGENCE.md (which
remains the definition of the Phase 5 baseline architecture).

**This document does NOT authorize implementation.** It defines what
the new architecture IS. Building it (Phase 7) requires separate
explicit CEO authorization.

---

## 1. The founding question

The Phase 5 architecture asked:

> Why are batteries and electric vehicles converging while batteries
> and desalination are not?

The Phase 6 architecture asks:

> Which capabilities exist?
> Which constraints remain?
> Which dependencies are missing?
> Which combinations have become reachable?
> Which combinations are becoming reachable?

The shift: from **co-occurrence** (shared labels) to **enablement**
(one capability unlocking another). Convergence is an emergent
property of capabilities + constraints + time, not a primitive to
be optimized directly.

---

## 2. The scientific model

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

Or, rewritten as the core theorem:

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

This replaces the Phase 5 theorem (shared labels → convergence →
invention). The old theorem is preserved as the experimental baseline
(see Section 14).

---

## 3. Documents as evidence (the single biggest change)

Patents are not the truth. Papers are not the truth. Products are not
the truth. Documents provide **evidence** of capabilities, constraints,
and their relationships.

### Old architecture

```text
patent → node
```

### New architecture

```text
patent → evidence → capability
```

### Evidence schema

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

Every capability, constraint, and edge must cite the evidence that
justifies it. An assertion without evidence is a hypothesis, not a
fact (per Law 6: expose assumptions).

---

## 4. Node type system

The Phase 5 "component" type was too ambiguous — it conflated
materials, processes, capabilities, products, and institutions under
one label. The new model introduces a type system.

### NodeType enum

```typescript
enum NodeType {
    CAPABILITY,       // what a technology can do (e.g., ENERGY_STORAGE)
    CONSTRAINT,       // what limits a capability (e.g., ENERGY_DENSITY_LIMIT)
    MATERIAL,         // the physical substrate (e.g., LITHIUM_COBALT_OXIDE)
    PROCESS,          // how something is made (e.g., VACUUM_DEPOSITION)
    PRODUCT,          // a concrete artifact (e.g., TESLA_4680_CELL)
    MARKET,           // an economic context (e.g., EV_BATTERY_MARKET)
    ORGANIZATION,     // a company/institution (e.g., PANASONIC)
    INSTITUTION,      // a regulatory/standards body (e.g., UL, IEC)
    REGULATION,       // a rule (e.g., UN38_3_SHIPPING)
    INFRASTRUCTURE    // shared physical capability (e.g., POWER_GRID)
}
```

### Why the type system matters

Per the external review:

> The goal is NOT synonym replacement. The goal is structural
> reasoning. Anode and cathode aren't just electrodes — they're
> electrodes with opposite polarity that only compose correctly with
> each other. Pure taxonomic collapsing loses that. You want typed
> nodes with typed relations, not a bag of synonyms.

The type system enables structural reasoning: a CAPABILITY can
REQUIRE another CAPABILITY, but a MATERIAL cannot REQUIRE a MARKET.
The types constrain which edges are meaningful, which prevents the
ontology explosion the CEO warns about.

---

## 5. Capability-centered architecture

A CAPABILITY is the primitive. Document-extracted labels (anode,
cathode, battery, supercapacitor) are evidence of capabilities, not
capabilities themselves.

### Example: anode/cathode

Instead of co-occurrence:

```text
anode ↔ cathode
```

Represent the underlying capability:

```text
anode → NEGATIVE_ELECTRODE_CAPABILITY ← cathode
```

### Example: battery/supercapacitor

Instead of:

```text
battery ↔ supercapacitor
```

Represent:

```text
battery → ENERGY_STORAGE_CAPABILITY ← supercapacitor
```

### Type system example (structural reasoning)

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

The polarity and the electrolyte requirement are structural facts
that determine what can compose with what. They are not taxonomy —
they are constraints on composition.

---

## 6. Edge system

### Removed edge types (from Phase 5)

```text
related_to
similar_to
connected_to
```

These are too undirected and too ambiguous. They measure co-occurrence,
not causation.

### EdgeType enum

```typescript
enum EdgeType {
    REQUIRES,           // A needs B to function
    ENABLES,            // A makes B possible
    SUBSTITUTES_FOR,    // A can replace B in some context
    BLOCKS,             // A prevents B
    CONSTRAINS,         // A limits B's performance
    DEPENDS_ON,         // A's existence depends on B's existence
    EMBODIED_IN,        // A capability is physically realized by B
    REGULATED_BY,       // A is subject to regulation B
    REDUCES_COST_OF    // A lowers the cost of B
}
```

### Edge schema

```typescript
interface Edge {
    source: string;
    target: string;
    type: EdgeType;
    confidence: number;
    evidence: string[];   // mandatory — no edge without evidence
}
```

The `evidence` field is mandatory. No edge is created without citing
the document(s) that justify it. An embedding-generated candidate is
NOT evidence (see Section 10).

---

## 7. CPC and IPC as foundational layers

Per the external review and Youn et al. (2015):

> Before building your own ontology layer, check how much of H2 is
> already solved by ingesting CPC/IPC codes instead of raw extracted
> text labels.

The USPTO's classification system (now CPC, historically IPC) is a
human-curated, decades-refined, globally-consistent controlled
vocabulary. It already solves the anode/cathode/electrode taxonomy
problem. Building a custom ontology from scratch would duplicate
decades of work.

### Mandatory ingestion targets

- CPC (Cooperative Patent Classification)
- IPC (International Patent Classification)
- USPTO classifications

### PatentEvidence schema

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
PROCESSES OR MEANS, e.g. BATTERIES, FOR THE DIRECT CONVERSION OF
CHEMICAL ENERGY INTO ELECTRICAL ENERGY
  ↓
ENERGY_STORAGE_CAPABILITY (electrochemical)
```

The CPC backbone does the taxonomy work that Phase 5's keyword
extraction was failing to do.

---

## 8. Three independent scoring systems

The single Phase 5 convergence score is **deprecated**. It conflated
three independent questions. The new model separates them.

### Score A — Readiness

**Question:** Can it exist?

**Definition document:** `READINESS.md`

**Inputs:**
- TRL (Technology Readiness Level)
- manufacturing maturity
- infrastructure maturity
- scientific maturity
- cost curves

### Score B — Novelty

**Question:** Has this combination already been explored?

**Definition document:** `NOVELTY.md`

**Inputs:**
- combinatorial distance
- exploration score
- historical rarity
- exploitation score

**Per Fleming (2001):** recombining familiar components reliably
produces incremental invention (refinement), not breakthrough. If
the system is meant to find breakthroughs, high novelty (productive
unfamiliarity) may be the right signal — not high convergence.

### Score C — Feasibility

**Question:** Would reality allow it?

**Definition document:** `FEASIBILITY.md`

**Inputs:**
- regulations
- economics
- manufacturing
- infrastructure
- physical constraints

**Feasibility gates are boolean/threshold conditions, not similarity
scores.** Blending them into a continuous number is why "premature"
and "impossible" inventions currently look the same to the Phase 5
system.

---

## 9. Embedding policy (hard guardrail)

Embeddings are **forbidden as truth generators**.

### Forbidden

```text
embedding_similarity > threshold → create_edge
```

### Permitted

```text
embedding_similarity > threshold → generate_candidate
candidate → constraint_evaluation
constraint_evaluation passes → human_review
human_review approves → create_edge with evidence[] citing the review
```

### Why

Per the external review:

> Generic embeddings will happily tell you `battery`, `capacitor`,
> `fuel cell`, and `generator` are all "close" because they co-occur
> in energy-storage-and-conversion text, which is true linguistically
> and false functionally (a fuel cell and a capacitor are not
> substitutable in almost any design). Embedding similarity without a
> constraint layer on top will increase your false-positive rate even
> as it fixes your false-negative rate.

If used at all, embeddings generate candidate edges for a downstream
functional/causal filter. They NEVER serve as the edge weight itself.

### Enforcement

This policy is encoded as a constitutional rule in this document.
A future test (Phase 7) will assert that no edge in the new graph
was created solely by embedding similarity — every edge must carry
evidence[] citing a human review or a document.

---

## 10. Temporal state (time as first-class infrastructure)

The Phase 5 architecture treated time as metadata. That is incorrect.
Time is a first-class dimension.

### TemporalState schema

```typescript
interface TemporalState {
    validFrom: Date;
    validTo: Date | null;
    confidence: number;
}
```

Every object (capability, constraint, edge, evidence) must support
temporal state. Every investigation must answer:

> What existed?
> What changed?
> What became possible?

This is what enables the frozen-time backtest (Section 11).

---

## 11. Frozen-time backtesting (mandatory validation)

### Incorrect

```text
Could we predict the transistor?
```

This is hindsight-shaped pattern matching.

### Correct

```text
State = year T
Input = information available at year T
Prediction = ranked possibilities at year T
Validation = what actually happened at T+n
```

### Required metrics

```text
precision    (of the things flagged, how many happened?)
recall       (of the things that happened, how many were flagged?)
false positives  (flagged but didn't happen)
false negatives  (happened but weren't flagged)
```

### Why precision matters

Per the external review:

> Given the transistor's inputs existed, you can construct hundreds
> of other component-combinations from 1946 that look equally
> convergent by any component-overlap or embedding-similarity metric
> and that never became anything. If you don't measure how many of
> those your system also flags, a positive result on the transistor
> tells you almost nothing.

The real test is precision, not just recall.

---

## 12. Scope restriction (the brutal constraint)

**Do not attempt to model the world. Model one vertical. Only one.**

This is the guardrail against ontology explosion (the CEO's warning:
"everything → ontology explosion → collapse"). It is encoded here as
a constitutional rule.

### The one vertical (frozen)

```text
electrochemical energy storage
```

### Maximum initial scope

| Entity       | Maximum |
|--------------|--------:|
| Patents      |      50 |
| Papers       |      50 |
| Products     |      10 |
| Capabilities |      20 |
| Constraints  |      10 |
| Edge types   |       6 |

Nothing else. This is the cap. If the new architecture cannot
demonstrate value within this scope, it does not get to expand.

### Enforcement

This restriction is encoded as a constitutional rule in this
document. A future test (Phase 7) will assert:
- `len(capabilities) <= 20`
- `len(constraints) <= 10`
- `len(edge_types_used) <= 6`
- `len(patents) <= 50`
- `len(papers) <= 50`
- `len(products) <= 10`

The test fails if any cap is exceeded. This is the structural
enforcement of the brutal constraint.

---

## 13. Mandatory prior art (prerequisite, not suggestion)

The following works define the theoretical foundation of the new
model. They must be read (or their key claims absorbed) before
implementation begins. The reading is recorded in
`evidence/reading_log.md`.

1. **Youn, Strumsky, Bettencourt, Lobo — *Invention as a Combinatorial Process* (2015)**
   - CPC as taxonomy backbone; exploitation vs exploration invariant rate.

2. **Lee Fleming — *Recombinant Uncertainty in Technological Search* (2001)**
   - Unfamiliar combinations ≠ reduced uncertainty; inverts convergence target.

3. **Brian Arthur — *The Nature of Technology* (2009)**
   - Recursive combination; capability graph, not component graph.

4. **Stuart Kauffman — *The Adjacent Possible***
   - What's reachable in one combinatorial step; not what exists now.

5. **Martin Weitzman — *Recombinant Growth* (1998 QJE)**
   - Limits to growth lie in processing, not generation; economic grounding.

6. **Hidalgo & Hausmann — *Economic Complexity / Product Space* (2009)**
   - Reachable product set depends on capabilities held; ECI predicts growth.

**Status:** the reading log exists at `evidence/reading_log.md`. Key
claims absorbed via web-search; full papers not yet read (recorded
honestly per principle #8). Full reading is a prerequisite for Phase 7
authorization, not for Phase 6 investigation.

---

## 14. Relationship to Phase 5 baseline

The Phase 5 architecture (CONVERGENCE.md, the convergence formula,
the component-centric graph, snapshots 1-4) is **preserved as the
experimental baseline**. It is NOT deleted. It is NOT modified.

### What the Phase 5 baseline is for

- **Replay:** re-running the convergence measurement against the
  frozen graph.
- **Auditing:** verifying that the Phase 5 claims (37.5% signal loss,
  +0.1091 perfect normalization gain, d(shared)/d(total)=0.00) hold.
- **Comparison:** comparing the new architecture's predictions against
  the old architecture's predictions on the same input data.
- **Backtesting:** the frozen-time backtest (Section 11) requires a
  baseline. The Phase 5 architecture is that baseline.
- **Failure analysis:** if the new architecture also saturates, the
  Phase 5 baseline shows whether the saturation is at the same point
  (suggesting the bottleneck is deeper than either architecture) or
  at a different point (suggesting the new architecture moved it).

### What the Phase 5 baseline is NOT

- It is NOT the primary architecture anymore. The capability-centric
  model is the primary investigation.
- It is NOT being extended. No new Phase 5 ingestion cycles are
  authorized (the Phase 5.F freeze holds).
- It is NOT being normalized. H1/H2/H3 are moot — the architecture
  is changing, not the matching.

### Constitutional status

CONVERGENCE.md remains in the mandatory read list. It is the
definition of the baseline architecture. CAPABILITY_ONTOLOGY.md
(this document) is added to the mandatory read list as the definition
of the new architecture. Both are authoritative for their respective
architectures. The read list grows; it doesn't replace.

---

## 15. What this document does NOT do

- It does NOT authorize implementation (Phase 7 requires separate
  explicit authorization).
- It does NOT modify the Phase 5 baseline (preserved as experimental
  baseline).
- It does NOT close F-039 (the saturation finding stands as a
  measurement of the Phase 5 baseline).
- It does NOT override the CEO's "do not build semantic matching"
  instruction (the embedding policy in Section 9 reinforces it).
- It does NOT define the three scores' formulas (those are in
  READINESS.md, NOVELTY.md, FEASIBILITY.md, each grounded in real
  data from the one vertical before the formula is committed).

---

## 16. What this document DOES do

- It defines the new architecture's ontology (node types, edge types).
- It defines the evidence schema (documents as evidence, not nodes).
- It defines the temporal state schema (time as first-class).
- It defines the scope restriction (one vertical, max counts).
- It defines the embedding policy (forbidden as truth generators).
- It defines the three independent scores (at the question level;
  formulas are in the separate definition documents).
- It defines the relationship to the Phase 5 baseline (preserved,
  not deleted).
- It records the mandatory prior art status (reading log exists).

---

## 17. Implementation status

| Item | Status |
|---|---|
| CAPABILITY_ONTOLOGY.md (this document) | COMPLETE |
| READINESS.md | PENDING (Instruction 3) |
| NOVELTY.md | PENDING (Instruction 3) |
| FEASIBILITY.md | PENDING (Instruction 3) |
| One vertical frozen | COMPLETE (electrochemical energy storage, Section 12) |
| Scope restriction encoded | COMPLETE (constitutional rule, Section 12; test in Phase 7) |
| Embedding policy encoded | COMPLETE (constitutional rule, Section 9; test in Phase 7) |
| Prior art reading log | COMPLETE (`evidence/reading_log.md`) |
| Phase 5 baseline preserved | VERIFIED (untouched) |
| Phase 7 implementation | NOT AUTHORIZED |
| Parser changes | NONE (forbidden) |
| Formula changes | NONE (forbidden) |
| Graph changes | NONE (forbidden) |

**The next steps (per auditor Instructions 3-8):**
1. Write READINESS.md, NOVELTY.md, FEASIBILITY.md (5-section structure each).
2. Add CAPABILITY_ONTOLOGY.md to the mandatory read list (grow, don't replace).
3. Encode the scope restriction and embedding policy as tests (Phase 7, after authorization).
4. Stand down — CEO decides whether to authorize Phase 7.

No implementation work is authorized. This document is a definition,
not a build instruction.
