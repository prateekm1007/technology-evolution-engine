# CAPABILITY_EXTRACTION_PROTOCOL — Phase 7C

**Status:** extraction protocol (constitutional).
**Phase:** 7C.

> Human understanding precedes automation.
> — CEO authorization, Phase 7C

This document defines the mandatory procedure for extracting
capabilities from patent/paper text. No automation. No embeddings.
No LLM-generated edges. Humans read, humans decide, humans record.

---

## 1. The extraction pipeline

```text
document
      ↓
claim (what does this document assert?)
      ↓
capability (what CAN this technology DO?)
      ↓
constraint (what limits this capability?)
      ↓
evidence (which document, which claim, which page?)
      ↓
review (a second human verifies the extraction)
```

Each step is manual. Each step produces a record. No step is
automated.

---

## 2. Step-by-step procedure

### Step 1: Document selection

- Select a patent or paper from the CORPUS_MANIFEST.
- Record its ID, date, CPC/IPC codes, and source.

### Step 2: Claim extraction

- Read the document (claims section for patents, abstract + results
  for papers).
- For each claim, record:
  - the claim text (verbatim, with page/line reference)
  - the claim type (capability claim, constraint claim, material
    claim, process claim)
  - the CPC/IPC code(s) that correspond to this claim

### Step 3: Capability identification

- For each capability claim, identify which capability from
  CAPABILITY_CATALOG.md the claim evidences.
- If the claim doesn't map to any existing capability:
  - DO NOT create a new capability (ONTOLOGY_FREEZE.md).
  - Record the claim as "unmapped" with a note explaining why.
  - If the unmapped claim represents a genuinely missing capability,
    record a proposal for CEO review (but do not add it).

### Step 4: Constraint identification

- For each constraint claim, identify which constraint from
  CONSTRAINT_CATALOG.md the claim evidences.
- Same unmapped-handling as Step 3.

### Step 5: Evidence recording

- For each capability or constraint identified, record:
  - document ID
  - claim text (verbatim)
  - page/line reference
  - CPC/IPC code
  - confidence (1.0 = explicit claim; 0.7 = implied; 0.5 = inferred)
  - reviewer ID

### Step 6: Review

- A second human reviews the extraction.
- The reviewer verifies:
  - the capability/constraint mapping is correct
  - the confidence is appropriate
  - the evidence is sufficient (claim text + reference)
- The reviewer signs off (records their ID + date).
- If the reviewer disagrees, the extraction is revised and
  re-reviewed.

---

## 3. What is FORBIDDEN

- **No LLM-generated capabilities.** An LLM may summarize text, but
  a human must decide which capability it evidences.
- **No embedding-based mapping.** Embeddings may suggest candidates,
  but a human must verify and record the evidence.
- **No automatic edge creation.** Every edge must go through this
  protocol.
- **No capability creation.** The 20 capabilities are frozen per
  ONTOLOGY_FREEZE.md. If a claim doesn't map, it's unmapped.

---

## 4. Quality control

- **Minimum:** every capability/constraint node in the graph must
  have at least 1 evidence entry with confidence ≥ 0.7.
- **Target:** every capability has ≥2 evidence entries from
  different documents (cross-evidence).
- **Audit:** the auditor will spot-check extractions by reading the
  source documents and verifying the capability mapping.
