# EVIDENCE_LINEAGE_ENGINE

**Status:** Honesty Loop Priority 1 engine (specification).
**Location:** repo root.
**Phase:** Honesty Loop v1.0 / P1.
**Triggered by:** Consolidated review finding — "The blueprint contains
evidence. It does not yet contain ancestry."

> Evidence without ancestry is a citation, not a lineage.
> A piece of evidence that cannot say where IT came from is
> no better than an unsourced claim.
> — Consolidated review, post-BP-2

---

## Purpose

The Evidence Lineage Engine extends the existing `Evidence` schema
(EP-13) with a `dependencies[]` field that traces each piece of
evidence back to its upstream sources. Evidence is no longer a
flat list — it is a directed acyclic graph (DAG) of provenance.

This is Priority 1 because every other engine depends on evidence
lineage. Mass stack-up without lineage is a number; with lineage
it is a chain of measurements, each traceable to a calibrated
instrument and a dated quotation.

---

## Schema

```typescript
interface Evidence {
    id: string                // EV-XXX identifier
    title: string             // human-readable title
    source: string            // URL, DOI, or document path
    sourceType: "paper" | "patent" | "regulation" | "supplier" | "market" | "measurement" | "standard"
    date: string              // ISO 8601 — when the evidence was produced or retrieved
    url: string               // direct link, if retrievable
    quotation: string         // the exact text being cited (verbatim)
    claim: string             // the claim this evidence supports
    rank: "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I"   // EP-13
    confidence: number        // DEPRECATED per Law 27 — retained for backward compat, must be 0
    dependencies: string[]    // EV-XXX IDs of upstream evidence this evidence derives from
    derivation?: string       // if derived: the operation applied to dependencies (e.g. "weighted average", "unit conversion", "translation")
    retrievalMethod: "manual" | "automated_scrape" | "api" | "supplier_quotation"
    retrievalDate: string     // ISO 8601
    retrievalAgent: string    // who/what retrieved it
    decayDate?: string        // ISO 8601 — when this evidence is expected to decay (per Principle 10)
    decayTrigger?: string     // event that would invalidate this evidence (e.g. "supplier price list revision")
}
```

### Field semantics

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique EV-XXX identifier within the blueprint. |
| `title` | yes | Short human-readable label. |
| `source` | yes | Canonical reference (DOI, URL, document path, supplier quote ID). |
| `sourceType` | yes | The kind of source — drives the rank floor. |
| `date` | yes | When the evidence was produced (not when it was retrieved). |
| `url` | yes (if retrievable) | Direct deep link. Empty string if not retrievable. |
| `quotation` | yes | Verbatim text from the source. Paraphrases are forbidden — paraphrase loses precision. |
| `claim` | yes | The claim this evidence supports. Must reference a Claim ID (Law 29e). |
| `rank` | yes | EP-13 evidence rank. Drives EVIDENCE_STRENGTH (Law 29c). |
| `confidence` | DEPRECATED | Per Law 27, must be 0 in new artifacts. Retained for backward compat. |
| `dependencies` | yes | Upstream EV-XXX IDs. Empty array `[]` for primary evidence (no upstream). |
| `derivation` | required if `dependencies` non-empty | The operation applied to derive this evidence from its dependencies. |
| `retrievalMethod` | yes | How the evidence was obtained. |
| `retrievalDate` | yes | When the evidence was retrieved (independent of `date`). |
| `retrievalAgent` | yes | The agent (human name, script name, or LLM model ID). |
| `decayDate` | optional | When this evidence is expected to become stale. |
| `decayTrigger` | optional | The event that would invalidate this evidence. |

---

## Lineage DAG rules

1. **Primary evidence has `dependencies: []`.** A direct
   measurement, a direct quotation from a paper, a direct supplier
   quote — these are primary. They have no upstream.

2. **Derived evidence has `dependencies: [EV-XXX, ...]`.** A
   weighted average of three measurements, a unit conversion of
   a manufacturer spec, a translation of a foreign-language
   patent — these are derived. The derivation must be stated.

3. **The DAG must be acyclic.** If `EV-001 → EV-002 → EV-001`
   is detected, the lineage is invalid. The evidence graph is
   a tree (or forest), not a graph with cycles.

4. **Rank cannot exceed the minimum rank of dependencies.** A
   derived piece of evidence with one rank-D and one rank-F
   dependency may be at most rank F. Derivation never improves
   rank; it can only preserve or degrade it.

5. **Decay propagates.** If a dependency's `decayDate` is past,
   all downstream evidence is marked `STALE` and the claim it
   supports is downgraded one validation level (e.g. L2 → L1).

---

## Example lineage

```
EV-001  (rank A — physics measurement)
   "LFP cell energy density: 172 Wh/kg (measured)"
   dependencies: []
   │
   ▼  (derivation: scale by pack overhead factor 0.93)
EV-002  (rank A — derived)
   "LFP pack energy density: 160 Wh/kg (derived from EV-001)"
   dependencies: [EV-001]
   │
   ▼  (derivation: multiply by pack volume 0.47 m³)
EV-003  (rank A — derived)
   "Pack energy: 75.2 kWh (derived from EV-002)"
   dependencies: [EV-002]
```

Without this DAG, the claim "75.2 kWh pack energy" is a bare
number. With it, the claim is traceable to a single calibrated
cell measurement — and any future revision of that measurement
propagates automatically.

---

## What this engine does NOT do

- It does not retrieve evidence. Retrieval is upstream (the
  research gate, Gate 2 of AEP).
- It does not rank evidence. Rank is assigned at retrieval per
  EP-13. This engine only propagates rank through derivation.
- It does not compute confidence. Per Law 27, confidence is
  forbidden. This engine computes validation_level (P5) and
  evidence_strength (Law 29c) — both typed, not numeric.

---

## Pre-stated falsifier (EP-4)

**Claim:** Every piece of evidence in a Blueprint can be traced
through a DAG to primary sources.

**Falsifier:** A piece of evidence in a Blueprint that has no
upstream dependencies AND no primary source — i.e., a number
with no quotation, no date, and no retrieval record. Such
evidence is forbidden; the engine must mark the claim
`STATUS: BLOCKED` until lineage is supplied.

**Status:** PENDING. Engine specified; implementation awaits
AEP Gate 1 for the engine itself.
