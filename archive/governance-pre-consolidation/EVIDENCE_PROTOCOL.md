# EVIDENCE_PROTOCOL — Phase 7C

**Status:** evidence protocol (constitutional).
**Phase:** 7C.

This document defines how evidence is recorded, stored, and traced
for every node and edge in the CAPABILITY_MODEL graph.

---

## 1. The evidence principle

> Patents are not the truth. Papers are not the truth. Products are
> not the truth. Documents merely provide evidence.
> — CEO directive, Phase 6, Section 3

Every capability, constraint, and edge in the graph must cite the
document(s) that justify it. An assertion without evidence is a
hypothesis, not a fact (per Law 6: expose assumptions).

---

## 2. Evidence object

```typescript
interface Evidence {
    id: string;           // unique evidence ID
    sourceType:           // what kind of document
        | "PATENT"
        | "PAPER"
        | "PRODUCT"
        | "REGULATION";
    sourceId: string;     // patent number, DOI, product SKU, etc.
    publicationDate: Date;
    confidence: number;   // 0.0-1.0
    claims: string[];     // verbatim claim text from the document
    citations: string[];  // what this evidence supports (node/edge IDs)
}
```

---

## 3. Evidence levels (per CEO Phase 7C.1 Decision 5)

| Level | Confidence | Meaning | Example |
|---|---|---|---|
| EXPLICIT | 1.0 | Explicitly stated | Patent CPC code maps to capability; regulation explicitly governs capability |
| IMPLIED | 0.8 | Directly implied | Patent claim text explicitly describes the relationship |
| INFERRED | 0.5 | Structurally inferred | Physical necessity of the domain (ions must move) |
| SPECULATIVE | 0.2 | Speculative | Human reviewer's judgment without direct evidence |

**Per CEO Phase 7C.1 Decision 5.** The previous 0.7/0.3 levels are
superseded by the CEO-approved 0.8/0.2 levels. Evidence at 0.3
(CANDIDATE) is now 0.2 (SPECULATIVE) and cannot create edges.

- Only EXPLICIT (1.0), IMPLIED (0.8), and INFERRED (0.5) evidence
  may be used to create nodes or edges (after human review).
- SPECULATIVE (0.2) evidence exists only as a record — it CANNOT
  create edges or nodes. It flags a relationship for future
  investigation.
- No edge below confidence 0.5 may be used in the frozen-time
  backtest (Phase 7D).

---

## 4. Evidence tracing

Every node and edge must be traceable to its source document(s).

### For a CAPABILITY node

```text
CAPABILITY: FAST_CHARGING
  ← evidence:
    E-001: US20240194939A1, claim 3, "fast charging at 4C rate"
    E-002: arxiv:2307.03620, abstract, "high-rate charging capability"
```

### For an EDGE

```text
EDGE: FAST_CHARGING → REQUIRES → THERMAL_MANAGEMENT
  ← evidence:
    E-003: US20240194939A1, claim 7, "thermal management layer
            configured to dissipate heat during fast charging"
    E-004: human review by [reviewer_id] on [date]
```

### For a CONSTRAINT node

```text
CONSTRAINT: THERMAL_RUNAWAY_THRESHOLD
  ← evidence:
    E-005: IEC 62133 standard, Section 7.3.2
    E-006: US4039440A, claim 2, "temperature not exceeding 150°C"
```

---

## 5. What is FORBIDDEN

- **No node or edge without evidence.** Every graph element must
  cite at least 1 evidence entry.
- **No evidence without a source document.** Evidence must reference
  a real document (patent, paper, product spec, regulation).
- **No CANDIDATE-level evidence used for creation.** Only
  EXPLICIT/IMPLIED/INFERRED (after human review) may create
  nodes/edges.
- **No evidence without a confidence level.** Every evidence entry
  must state its level.

---

## 6. Audit trail

The auditor will verify:
1. Every node has ≥1 evidence entry with confidence ≥ 0.5.
2. Every edge has ≥1 evidence entry with confidence ≥ 0.5.
3. Every evidence entry references a real source document.
4. The evidence chain is replayable: given the same documents + the
   same extraction protocol, the same nodes/edges would be created.

This is Law 8 (verification standard) applied to the evidence layer.

---

## 7. EdgeJustification schema (per CEO Phase 7C.1 Decision 4)

Every edge must satisfy this schema:

```typescript
interface EdgeJustification {
    edgeId: string;          // unique edge identifier
    sourcePatent: string;    // patent ID (or "structural_invariant" for domain knowledge)
    cpcCode: string;         // the CPC code that maps to the capability
    sourceNode: string;      // source node ID
    targetNode: string;      // target node ID
    relationship: string;    // edge type (EMBODIED_IN, REQUIRES, CONSTRAINS, REGULATED_BY)
    justification: string;   // 1-2 sentence explanation of WHY this edge exists
    reviewer: string;        // reviewer ID + date
    confidence: number;      // 1.0 / 0.8 / 0.5 / 0.2 (per CEO Decision 5)
}
```

### Fields

- **edgeId**: unique identifier for the edge (e.g., "EDGE-001").
- **sourcePatent**: the patent that provides evidence for this edge.
  For structural invariants (domain knowledge), use "structural_invariant".
- **cpcCode**: the specific CPC code that maps to the capability. For
  structural invariants, use "N/A (structural)".
- **sourceNode / targetNode**: the node IDs connected by this edge.
- **relationship**: one of the 4 authorized edge types (EMBODIED_IN,
  REQUIRES, CONSTRAINS, REGULATED_BY). ENABLES and SUBSTITUTES_FOR
  are SUSPENDED per CEO Decision 2.
- **justification**: a specific, 1-2 sentence explanation citing the
  evidence. Generic boilerplate ("these are related") is NOT acceptable.
  Must reference the CPC code, claim text, or physical principle.
- **reviewer**: the human reviewer's ID and the date of review.
- **confidence**: per the CEO-approved scale (1.0/0.8/0.5/0.2).

### Enforcement

The auditor will verify:
1. Every edge has an EdgeJustification with ALL fields populated.
2. No edge uses ENABLES or SUBSTITUTES_FOR (suspended).
3. Every justification is specific (not boilerplate).
4. Every confidence matches the evidence type per CAUSALITY_POLICY.md.
5. Every reviewer field is populated with a human ID + date.
