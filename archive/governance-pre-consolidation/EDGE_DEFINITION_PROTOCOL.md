# EDGE_DEFINITION_PROTOCOL — Phase 7C

**Status:** edge creation protocol (constitutional).
**Phase:** 7C.

This document defines the mandatory procedure for creating edges
in the CAPABILITY_MODEL graph. Every edge requires evidence + human
review. No automated edge creation.

---

## 1. The edge creation pipeline

```text
candidate edge (from extraction or candidate generation)
      ↓
edge type assignment (which of the 6 used edge types?)
      ↓
constraint evaluation (does this edge make structural sense?)
      ↓
human review (a human verifies the edge)
      ↓
edge creation (with evidence[] citing the review)
```

---

## 2. Edge types (6 used in this vertical)

| Edge type | Meaning | Source → Target | Example |
|---|---|---|---|
| REQUIRES | A needs B to function | CAPABILITY → CAPABILITY | FAST_CHARGING REQUIRES THERMAL_MANAGEMENT |
| ENABLES | A makes B possible | CAPABILITY → CAPABILITY | FAST_CHARGING ENABLES EV_ADOPTION |
| SUBSTITUTES_FOR | A can replace B in some context | CAPABILITY → CAPABILITY | SUPERCAPACITOR SUBSTITUTES_FOR BATTERY (high-power, low-energy) |
| CONSTRAINS | A limits B's performance | CONSTRAINT → CAPABILITY | ENERGY_DENSITY_LIMIT CONSTRAINS HIGH_ENERGY_DENSITY_STORAGE |
| EMBODIED_IN | A capability is realized by B | CAPABILITY → MATERIAL/PROCESS | ION_TRANSPORT EMBODIED_IN LITHIUM_ELECTROLYTE |
| REGULATED_BY | A is subject to regulation B | CAPABILITY → REGULATION | BATTERY_SHIPPING REGULATED_BY UN38_3 |

### Edge type validation rules

- REQUIRES: source and target must both be CAPABILITY nodes.
- ENABLES: source and target must both be CAPABILITY nodes.
- SUBSTITUTES_FOR: source and target must both be CAPABILITY nodes.
- CONSTRAINS: source must be CONSTRAINT; target must be CAPABILITY.
- EMBODIED_IN: source must be CAPABILITY; target must be MATERIAL or PROCESS.
- REGULATED_BY: source must be CAPABILITY; target must be REGULATION.

These rules are structural invariants. An edge that violates them
is a bug.

---

## 3. Edge creation procedure

### Step 1: Candidate generation

- Candidates come from:
  - The CAPABILITY_EXTRACTION_PROTOCOL (a document evidences
    both capabilities + their relationship).
  - Embedding-based candidate generation (FORBIDDEN as edge creator;
    PERMITTED as candidate generator per the embedding policy).
  - Human domain expertise (a reviewer notices a relationship not
    evidenced in any single document).

### Step 2: Edge type assignment

- Determine which of the 6 edge types the candidate represents.
- Verify the source/target node types are compatible (Section 2
  rules).
- If no edge type fits, the candidate is discarded (not forced into
  a wrong type).

### Step 3: Constraint evaluation

- Does this edge make structural sense?
  - Is the dependency real? (e.g., does FAST_CHARGING really
    REQUIRE THERMAL_MANAGEMENT, or is it just common?)
  - Is the substitution valid? (e.g., can a supercapacitor really
    SUBSTITUTE_FOR a battery in the stated context?)
  - Is the constraint binding? (e.g., does ENERGY_DENSITY_LIMIT
    actually CONSTRAIN this specific capability?)

### Step 4: Human review

- A human (not the extractor) reviews the edge.
- The reviewer verifies:
  - the edge type is correct
  - the source/target types are compatible
  - the constraint evaluation passes
  - the evidence is sufficient
- The reviewer records their ID + date.

### Step 5: Edge creation

- Create the edge with:
  - source, target, type
  - confidence (0.0-1.0)
  - evidence[] (array of evidence IDs, each citing a document +
    claim + reviewer)

---

## 4. What is FORBIDDEN

- **No edge without evidence.** Every edge must have at least 1
  evidence entry.
- **No edge without human review.** Even if an embedding suggests
  an edge, a human must review and approve it.
- **No edge without a compatible type.** An edge that doesn't fit
  one of the 6 types is not created.
- **No new edge types.** The 6 types are frozen per
  ONTOLOGY_FREEZE.md.

---

## 5. Embedding policy (reinforced)

```text
FORBIDDEN:
  embedding_similarity > threshold → create_edge

PERMITTED:
  embedding_similarity > threshold → generate_candidate
  candidate → constraint_evaluation (this protocol)
  constraint_evaluation passes → human_review
  human_review approves → create_edge with evidence[] citing the review
```

Embeddings are candidate generators. They are NEVER edge creators.
The edge creation path always goes through this protocol.
