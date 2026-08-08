# Discovery Experiment Specification — DXP-002

**Status:** FROZEN (pre-execution)
**Date:** 2026-08-08
**Engine commit:** f8e3f2ac136e3b03acc0b3314dc901fc614ae4a8
**Predecessor:** DXP-001 (NOT DISCOVERY — bottleneck: adversarial filtering, but failure mode undiagnosed)

---

## Purpose

DXP-002 is designed to distinguish between two hypotheses about DXP-001's failure:

**H1: Challenge-design mismatch.** DXP-001's HVAC constraints (no ML, no cloud, tunable by non-expert) were hostile to bio-inspired approaches. Any bio-inspired transfer would violate those constraints.

**H2: Generator weakness.** The engine systematically generates shallow analogies that don't survive scientific scrutiny, regardless of the challenge.

DXP-002 uses a different scientific geometry with constraints that are NOT hostile to bio-inspired approaches. If DXP-002 also fails at adversarial filtering, H2 is supported. If DXP-002 passes adversarial filtering, H1 is supported.

---

## 1. Challenge Selection

**Source domain:** Entomology — Namib Desert fog-basking beetle (Physosterna cribripes) surface morphology and fog-harvesting mechanism.

**Target domain:** Materials engineering — dew condenser surface design for atmospheric water generation (AWG) in arid coastal regions.

**Why this challenge:**

1. **Different geometry from DXP-001:** DXP-001 was biology → control theory (mechanism → algorithm). DXP-002 is biology → materials science (mechanism → physical surface design). This tests a different type of transfer.

2. **Not hostile to bio-inspired approaches:** Unlike DXP-001's "no ML infrastructure" constraint, the target domain (materials engineering) actively welcomes bio-inspired surface designs. There are no constraints that would make any bio-inspired approach infeasible by construction.

3. **Measurable outcome:** Water collection rate (mL/m²/hour) is a standard metric in the AWG literature.

4. **Minimal lexical overlap:** The source uses "elytra," "hydrophilic bumps," "fog-basking," "Stenocara." The target uses "condenser surface," "nucleation rate," "dropwise condensation," "heat transfer coefficient."

5. **Validation path:** The prediction can be checked against established condensation physics (nucleation theory, heat transfer) and published AWG performance data.

6. **Prior-art richness:** There IS published work on beetle-inspired fog harvesting (e.g., Parker & Lawrence 2001, Zhai et al. 2006). This makes prior-art checking meaningful — a true novel contribution must go beyond "copy the beetle bumps."

---

## 2. Frozen Input Package

### Document A: Source mechanism (Namib beetle fog harvesting)

A 1000-word technical description of:
- The beetle's fog-basking behavior (climbing dunes at dawn, facing fog-laden wind)
- The elytra surface morphology (hydrophilic bumps on hydrophobic background)
- The physical mechanism (fog droplets nucleate on bumps, grow, roll off hydrophobic valleys)
- The role of bump size, spacing, and wettability contrast
- Known failure modes (wind speed dependence, contamination, temperature effects)
- What is NOT known (optimal bump geometry, scaling laws)

This document does NOT reference materials engineering, condensers, or atmospheric water generation.

### Document B: Target problem (dew condenser design)

A 800-word description of:
- The AWG problem (collecting water from humid air in arid coastal regions)
- Current approaches (radiative cooling surfaces, active refrigeration)
- Limitations (low yield, high energy cost, surface degradation)
- The specific context (coastal desert, fog events 200 days/year, average 0.3 g/m³ liquid water content)
- Constraints (passive system only, no energy input, surface area ≤ 10 m², must survive 5+ years outdoors)
- What is needed (higher collection rate than flat surfaces, durability, low maintenance)

This document does NOT reference beetles, insects, or biology.

### SHA-256 manifest

Both documents are hashed and recorded in `INPUTS/MANIFEST.sha256` before execution.

---

## 3. Information Boundary

### What is in the input
- Detailed beetle fog-harvesting mechanism (entomology)
- AWG condenser design problem (materials engineering)
- Physical constraints on both systems

### What is deliberately withheld
- Any reference connecting the two domains
- Any hint that the beetle morphology might apply to condenser design
- The evaluation criteria
- Any prior work on beetle-inspired fog harvesting (Parker & Lawrence 2001, etc.)
- The expected prediction

### What constitutes "recoverable from input"
- Direct restatement of beetle morphology applied to condenser surface
- Simple entity overlap ("both involve water collection")
- Paraphrase of the source mechanism with "condenser" substituted for "elytra"

### What constitutes a genuine discovery
- A transfer that identifies a SPECIFIC aspect of the beetle mechanism (not just "bumpy surface") that maps to a SPECIFIC design parameter of the condenser, AND
- Produces a quantitative prediction about condenser performance that is NOT obvious from either domain alone, AND
- The prediction is physically testable against condensation physics

---

## 4. Controls

Same as DXP-001:
- C1: Retrieval-only (TF-IDF/entity overlap)
- C2: Generic LLM (same model, no pipeline)
- C3: Matched null (target problem only, no source mechanism)
- C4: Human control (experimenter with both documents)

---

## 5. Discovery Test

### Success conditions (ALL must be met)

1. Candidate transfer produced (not rejected at transfer stage)
2. At least one hypothesis classified as NON_TRIVIAL_TRANSFER
3. At least one hypothesis survives adversarial analysis (ADVERSARIAL_SURVIVES or INCONCLUSIVE)
4. A falsifiable prediction is produced (observable, baseline, magnitude, falsifier)
5. The prediction is physically plausible (does not violate thermodynamics or heat transfer principles)

### Failure conditions (ANY one)

1. No transfer produced
2. All hypotheses classified as rediscovery
3. All hypotheses fail adversarial analysis
4. No falsifiable prediction
5. Prediction is physically implausible
6. Output indistinguishable from retrieval baseline

---

## 6. Generator-vs-Filter Diagnostic

For EVERY candidate, record:

```
candidate_id
generated_claim
constraint_check: PASS/FAIL (does it violate target constraints?)
rediscovery_check: classification
adversarial_outcome: SURVIVES/FAILED/INCONCLUSIVE
death_reason: (if killed, the specific reason)
failure_classification: GENERATION_DEFECT / TARGET_CONSTRAINT_DEFECT / KNOWN_ART_DEFECT / MECHANISTIC_DEFECT / FALSIFIABILITY_DEFECT / EXPERIMENTAL_DEFECT / OTHER
```

### Failure classifications

| Classification | Meaning |
|---|---|
| GENERATION_DEFECT | The hypothesis is shallow, generic, or not mechanistically specific. The generator produced a surface analogy, not a mechanism transfer. |
| TARGET_CONSTRAINT_DEFECT | The hypothesis violates a stated constraint of the target problem. |
| KNOWN_ART_DEFECT | The proposed transfer already exists in published literature. |
| MECHANISTIC_DEFECT | The proposed mechanism is physically incorrect or incomplete. |
| FALSIFIABILITY_DEFECT | The hypothesis lacks a falsifiable prediction. |
| EXPERIMENTAL_DEFECT | The proposed experiment is infeasible or cannot distinguish the hypothesis. |
| OTHER | Failure for a reason not in the above categories. |

This diagnostic distinguishes "the generator is weak" from "the filter is too aggressive" from "the challenge is hostile."

---

## 7. Negative Science Preservation

All killed candidates from DXP-001 and DXP-002 are preserved as reusable negative-science objects:

```
source_mechanism
→ proposed_transfer
→ rejection_reason
→ evidence_supporting_rejection
→ failure_classification
→ lesson
```

The engine's DiscoveryMemory stores these so future runs can ask: "Have we attempted this type of transfer before, and why did it fail?"

---

## 8. Pre-registration

Frozen before execution:
- Challenge (beetle fog harvesting → dew condenser design)
- Input documents
- Evaluation criteria
- Success/failure conditions
- Controls
- Failure classification scheme
- Blinding protocol
- Statistical analysis (descriptive)

Cannot be changed after execution:
- The challenge
- The input documents
- The definition of "discoverable from input"
- The definition of "novel"
- The success/failure conditions
- The failure classification scheme

---

## 9. Stop Conditions

Same as DXP-001:
1. No retroactive tuning
2. No changing the challenge
3. No redefining novelty
4. No converting "interesting" into "discovery"
5. No calling a failed experiment a success

Plus:
6. **Never optimize the engine to pass a discovery case it has already seen.**

---

## 10. Binary Outcome

### DISCOVERY (ALL must be met)
1. Non-trivial transfer (not recoverable from input)
2. Survives adversarial analysis
3. Produces a falsifiable prediction
4. Prediction is physically plausible
5. Prediction is not produced by retrieval-only baseline

### NOT DISCOVERY (ANY one)
1. No transfer produced
2. Transfer is recoverable from input
3. All candidates fail adversarial
4. No falsifiable prediction
5. Prediction is physically implausible
6. Output indistinguishable from retrieval baseline

### If NOT DISCOVERY, the failure map must include:
- Which stage failed
- The failure classification (GENERATION_DEFECT, TARGET_CONSTRAINT_DEFECT, etc.)
- Whether this supports H1 (challenge mismatch) or H2 (generator weakness)
