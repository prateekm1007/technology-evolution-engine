# CPC_MAPPING — Phase 7B

**Status:** CPC classification mapping (definition, not yet populated with data).
**Phase:** 7B (per CEO authorization CEO-7A-7D).

> Replace hand-built terminology with established classification
> systems. Not embeddings. Not LLM reasoning. Just classifications.
> — CEO authorization, Phase 7B

This document defines how CPC (Cooperative Patent Classification)
codes map to the CAPABILITY_MODEL's node types. It is a definition
document — the actual CPC codes from real patents will be populated
during Phase 7B ingestion (authorized but not yet executed).

---

## 1. The CPC hierarchy for electrochemical energy storage

The primary CPC code for this vertical is:

```text
H01M — PROCESSES OR MEANS, e.g. BATTERIES, FOR THE DIRECT
       CONVERSION OF CHEMICAL ENERGY INTO ELECTRICAL ENERGY
```

### Key subclasses

| CPC code | Description | Maps to capabilities |
|---|---|---|
| H01M 4/00 | Electrodes | INTERCALATION, ELECTRON_COLLECTION, CONVERSION_REACTION |
| H01M 10/00 | Secondary cells (rechargeable) | ELECTROCHEMICAL_ENERGY_STORAGE, LONG_CYCLE_LIFE_STORAGE |
| H01M 12/00 | Fuel cells | (out of scope — generation, not storage) |
| H01M 50/00 | Constructional details | CELL_ASSEMBLY, THERMAL_MANAGEMENT |
| H01M 50/40 | Separators | SELECTIVE_ION_TRANSPORT |
| H01M 50/41 | Separator materials | MATERIAL nodes (polymer, ceramic) |
| H01M 50/60 | Manufacture of separators | PROCESS nodes |
| H01M 50/70 | Assembling cells | CELL_ASSEMBLY |
| H01M 50/80 | Arrangements in cells | THERMAL_MANAGEMENT, SAFETY_PROTECTION |
| H01M 10/0525 | Rocking-chair batteries (Li-ion) | ELECTROCHEMICAL_ENERGY_STORAGE, ION_TRANSPORT |
| H01M 10/0565 | Polymer electrolyte cells | ION_TRANSPORT, SOLID_ELECTROLYTE_SINTERING |
| H01M 10/0562 | Solid electrolyte cells | ION_TRANSPORT, SOLID_ELECTROLYTE_SINTERING |
| H01M 10/44 | Methods for charging | FAST_CHARGING |
| H01M 10/48 | Accumulators with monitoring | STATE_OF_CHARGE_MONITORING, CELL_BALANCING, SAFETY_PROTECTION |

---

## 2. CPC → Capability mapping

Each CPC code maps to one or more CAPABILITY nodes via the
EMBODIED_IN edge type. The mapping is:

```text
Patent (with CPC code H01M 4/00)
    → evidence of
        → CAPABILITY: INTERCALATION
        → CAPABILITY: ELECTRON_COLLECTION
```

The CPC code does not BECOME a node — it is EVIDENCE that the patent
describes capabilities. The evidence linkage is:

```text
PatentEvidence {
    patentId: "US...",
    cpcCodes: ["H01M 4/00", "H01M 10/0525"],
    claims: [...],
    citations: [...]
}
→ evidence for
    → CAPABILITY: INTERCALATION (because H01M 4/00 covers electrodes)
    → CAPABILITY: ELECTROCHEMICAL_ENERGY_STORAGE (because H01M 10/0525 covers Li-ion)
    → CAPABILITY: ION_TRANSPORT (because H01M 10/0525 covers rocking-chair)
```

---

## 3. Why CPC instead of hand-built taxonomy

Per Youn et al. (2015) and the external review:

> Before building your own ontology layer, check how much of H2 is
> already solved by ingesting CPC/IPC codes instead of raw extracted
> text labels.

The CPC system is:
- **Human-curated** by patent examiners at USPTO, EPO, and other
  patent offices
- **Decades-refined** (CPC launched 2013, built on the earlier
  ECLA and USPC systems)
- **Globally consistent** (used by 30+ patent offices worldwide)
- **Hierarchical** (section → class → subclass → group → subgroup)

Building a custom taxonomy from keyword extraction (as the
CO_OCCURRENCE_MODEL did in Phase 5) duplicates this work at lower
quality. CPC is the established backbone.

---

## 4. What this document does NOT do

- It does NOT contain the actual CPC codes from the 50 patents
  (those will be ingested in Phase 7B execution).
- It does NOT create edges (edges require evidence + human review
  per the embedding policy and EVIDENCE_PROTOCOL.md).
- It does NOT replace the CAPABILITY_CATALOG — CPC codes are
  EVIDENCE for capabilities, not capabilities themselves.
