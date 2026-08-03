# ONTOLOGY_FREEZE — Phase 6 Constitutional Guardrail (updated Phase 7C.1)

**Status:** constitutional guardrail (frozen ontology caps, REDUCED per CEO ruling).
**Location:** repo root.
**Phase:** 7C.1 (caps reduced per CEO ruling, commit `3922a3d`).

> Right now you have ten node types and nine edge types. That's
> already dangerous.
> — CEO directive, Phase 6, correction 3

> The scope reduction is approved. ENABLES and SUBSTITUTES_FOR are
> temporarily suspended.
> — CEO ruling, Phase 7C.1, Decisions 1-3

This document freezes the ontology at its reduced size (per CEO
Phase 7C.1 ruling). Any addition requires explicit CEO authorization.

---

## Frozen caps (REDUCED per CEO Phase 7C.1)

| Object       | Previous cap | NEW cap (CEO 7C.1) | Current count | Status |
|---|---:|---:|---:|---|
| Node types   | 10 | 10 | 3 (CAPABILITY, CONSTRAINT, PRODUCT) | FROZEN |
| Edge types   | 9 | **4** (ENABLES + SUBSTITUTES_FOR SUSPENDED) | 4 | FROZEN |
| Verticals    | 1 | 1 | 1 | FROZEN |
| Capabilities | 20 | **10** | 0 (rebuild pending) | Available |
| Constraints  | 10 | **5** | 0 (rebuild pending) | Available |
| Patents      | 50 | **5** | 0 (rebuild pending) | Available |

### Node types (frozen at 10)

```text
CAPABILITY
CONSTRAINT
MATERIAL
PROCESS
PRODUCT
MARKET
ORGANIZATION
INSTITUTION
REGULATION
INFRASTRUCTURE
```

Any proposal to add an 11th node type requires:
1. A recorded justification citing the specific failure mode that
   the current 10 types cannot address.
2. An attempt to model the concept using an existing type + an edge
   (e.g., "this concept is a CAPABILITY with a REQUIRES edge to a
   CONSTRAINT" rather than a new type).
3. Explicit CEO authorization.

### Edge types (4 AUTHORIZED, 2 SUSPENDED per CEO 7C.1)

**Authorized (4):**
```text
EMBODIED_IN
REQUIRES
CONSTRAINS
REGULATED_BY
```

**Suspended (per CEO Decision 2, Phase 7C.1):**
```text
ENABLES          — requires historical counterfactual evidence (not yet available)
SUBSTITUTES_FOR  — notoriously difficult to establish (not yet available)
```

**Not used in this vertical (3 of original 9):**
```text
BLOCKS
DEPENDS_ON
REDUCES_COST_OF
```

Any proposal to re-enable ENABLES or SUBSTITUTES_FOR requires:
1. A recorded justification citing the specific evidence available.
2. A human reviewer's assessment per CAUSALITY_POLICY.md.
3. Explicit CEO authorization.

### Verticals (frozen at 1)

```text
electrochemical energy storage
```

Any proposal to add a 2nd vertical requires:
1. A recorded justification citing the specific limitation of the
   one-vertical scope.
2. Evidence that the CAPABILITY_MODEL works within the first vertical
   (frozen-time backtest results).
3. Explicit CEO authorization.

### Capabilities (cap at 20)

The one vertical may have at most 20 CAPABILITY nodes. Any proposal
to add a 21st requires:
1. A recorded justification citing the specific capability that
   cannot be modeled by combining existing capabilities.
2. Explicit CEO authorization.

### Constraints (cap at 10)

The one vertical may have at most 10 CONSTRAINT nodes. Any proposal
to add an 11th requires:
1. A recorded justification citing the specific constraint that
   cannot be modeled by refining an existing constraint.
2. Explicit CEO authorization.

---

## Why this freeze matters

Per CEO v3.5:

> The most common failure mode in projects like this is:
> interesting concept → new node type → new edge type → exception →
> ontology explosion → collapse.

The freeze prevents the first step of this cascade. Every addition
must prove it's necessary, not just interesting. The burden of proof
is on the addition, not the status quo — the same H0 principle from
Phase 5.F, applied to the ontology.

This is the structural guardrail against the "everything → ontology
explosion → collapse" failure mode the CEO warned about in the
Phase 6 preamble.

---

## Enforcement

This freeze is encoded as a constitutional rule. A future test
(Phase 7) will assert:
- `len(node_types) <= 10`
- `len(edge_types) <= 9`
- `len(verticals) <= 1`
- `len(capabilities) <= 20`
- `len(constraints) <= 10`

The test fails if any cap is exceeded. This is the structural
enforcement of the ontology freeze.

Until Phase 7 implementation, the freeze is a constitutional
commitment, not yet a test. The commitment is binding — any commit
that adds a node type, edge type, or vertical without explicit
justification violates this document.
