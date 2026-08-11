# DXP-002 Final Verdict

**Experiment:** DXP-002
**Date:** 2026-08-08
**Engine commit:** f8e3f2ac136e3b03acc0b3314dc901fc614ae4a8
**Challenge:** Namib beetle fog-harvesting morphology → dew condenser surface design

---

## Binary Outcome: **NOT DISCOVERY**

---

## What happened

The engine successfully:
1. Extracted a 23-node mechanism graph from the beetle fog-harvesting document (1 extraction failure)
2. Abstracted it to: "Hierarchical surface structure with differential wettability enables directional transport of condensed water droplets from atmosphere to collection point"
3. Produced a cross-domain transfer with explicit translation mapping (insect exoskeleton → food-grade polymer, microstructured wettability pattern → laser ablation/nanoimprint)
4. Generated 4 competing hypotheses about the transport mechanism (capillary forces, asymmetric coalescence, Marangoni effect, Laplace pressure + pinning/depinning)
5. One hypothesis (H-003, Marangoni effect) was classified as STRUCTURAL_INFERENCE (not rediscovery)

The engine then killed all 4 hypotheses at the adversarial gate:
- H-001 (capillary): 4 HIGH → ADVERSARIAL_FAILED + classified as PARAPHRASED_IN_INPUT
- H-002 (coalescence): 4 HIGH → ADVERSARIAL_FAILED + classified as PARAPHRASED_IN_INPUT
- H-003 (Marangoni): 3 HIGH → ADVERSARIAL_FAILED + classified as STRUCTURAL_INFERENCE
- H-004 (Laplace + pinning): 3 HIGH → ADVERSARIAL_FAILED + classified as PARAPHRASED_IN_INPUT

**candidate_status = ALL_BLOCKED_AT_ADVERSARIAL**
**scientific_gate_passed = False**

---

## Failure Map

```
Stage                          Status    Detail
────────────────────────────── ──────── ──────────────────────────────────────
representation (extraction)   PASS      23 nodes, 19 edges, 1 failure
abstraction                   PASS      Domain-neutral principle produced
transfer                      PASS      Explicit translation mapping produced
hypothesis generation         PASS      4 materially different hypotheses
novelty (rediscovery)         MIXED     3/4 PARAPHRASED_IN_INPUT, 1/4 STRUCTURAL_INFERENCE
adversarial filtering         FAIL      All 4 killed (3-4 HIGH severity each)
prediction                    BLOCKED   No hypotheses survived
experimental design           BLOCKED   No hypotheses survived
accuracy                      BLOCKED   No experiment was designed
```

**Bottleneck: adversarial filtering (again).** But the diagnostic reveals a more nuanced picture.

---

## Generator-vs-Filter Diagnostic

| Candidate | Claim | Rediscovery | Adversarial | Death Reason | Failure Classification |
|---|---|---|---|---|---|
| H-001 | Capillary forces pull droplets to hydrophilic regions | PARAPHRASED_IN_INPUT | FAILED (4 HIGH) | Contradicts surface physics: hydrophilic regions don't "pull" droplets; contact angle hysteresis drives motion | **MECHANISTIC_DEFECT** + **GENERATION_DEFECT** |
| H-002 | Asymmetric coalescence events drive directional transport | PARAPHRASED_IN_INPUT | FAILED (4 HIGH) | Coalescence is random/isotropic at small scales; no mechanism for asymmetry | **MECHANISTIC_DEFECT** + **GENERATION_DEFECT** |
| H-003 | Marangoni effect (surface tension gradients) drives transport | STRUCTURAL_INFERENCE | FAILED (3 HIGH) | Marangoni effects too weak at this scale; diffusion homogenizes gradients | **MECHANISTIC_DEFECT** |
| H-004 | Laplace pressure + pinning/depinning drives transport | PARAPHRASED_IN_INPUT | FAILED (3 HIGH) | Laplace pressure differences unquantified; contradicts contact-line-driven motion | **MECHANISTIC_DEFECT** + **GENERATION_DEFECT** |

### Pattern analysis

**3 of 4 candidates are classified as PARAPHRASED_IN_INPUT.** The engine is restating the beetle mechanism ("hydrophilic bumps on hydrophobic background") with "condenser surface" substituted. This is a GENERATION_DEFECT — the generator is producing surface-level analogies, not deep mechanism transfers.

**All 4 candidates have MECHANISTIC_DEFECT.** The proposed mechanisms are physically incorrect or unquantified. The adversarial critic correctly identifies that:
- Capillary forces don't "pull" droplets (H-001)
- Coalescence is random, not directional (H-002)
- Marangoni effects are too weak at this scale (H-003)
- Laplace pressure differences are unquantified (H-004)

**1 of 4 (H-003) is classified as STRUCTURAL_INFERENCE** — it went beyond paraphrase to propose a mechanism (Marangoni effect) not explicitly in the source document. But the mechanism is physically wrong for this scale.

---

## DXP-001 vs DXP-002 comparison

| Dimension | DXP-001 (biology → HVAC) | DXP-002 (entomology → materials) |
|---|---|---|
| Extraction | 24 nodes, 25 edges | 23 nodes, 19 edges |
| Transfer accepted | Yes | Yes |
| Hypotheses generated | 3 | 4 |
| Non-trivial transfer | 3/3 (100%) | 1/4 (25%) |
| Adversarial survival | 0/3 (0%) | 0/4 (0%) |
| Primary failure | TARGET_CONSTRAINT_DEFECT (violated "no ML") | MECHANISTIC_DEFECT (physically wrong) |
| Challenge hostile? | Yes (no-ML constraint) | No (materials welcomes bio-inspired) |

### Key finding

DXP-002 was designed to NOT be hostile to bio-inspired approaches. The target domain (materials engineering) actively welcomes bio-inspired surface designs. There are no constraints that make bio-inspired approaches infeasible.

**Yet the engine still failed.** And the failure mode is different:
- DXP-001: candidates were structurally valid but violated target constraints (TARGET_CONSTRAINT_DEFECT)
- DXP-002: candidates were physically incorrect (MECHANISTIC_DEFECT) and mostly paraphrases (GENERATION_DEFECT)

This supports **H2: generator weakness** over H1: challenge-design mismatch. The engine systematically generates shallow analogies that:
1. Restate the source mechanism with target-domain vocabulary (PARAPHRASED_IN_INPUT)
2. Propose mechanisms that are physically incorrect at the target scale (MECHANISTIC_DEFECT)

---

## What this experiment proves and does NOT prove

### Proves
- The engine can extract, abstract, and transfer mechanisms across distant domains (both DXP-001 and DXP-002)
- The engine's adversarial gate is functional and catches both constraint violations and physical errors
- The engine does NOT produce false discoveries
- The failure is NOT challenge-specific: DXP-002 was designed to be favorable to bio-inspired transfer, and it still failed
- The failure pattern is consistent: GENERATION_DEFECT (shallow analogies) + MECHANISTIC_DEFECT (physically wrong mechanisms)

### Does NOT prove
- That the engine can produce a candidate that survives adversarial analysis
- That the engine can produce a physically correct non-obvious mechanism transfer
- That the engine can produce a falsifiable prediction
- That the engine can discover anything

---

## Honest assessment

**The engine's bottleneck is hypothesis generation quality, not infrastructure.** Two experiments with different scientific geometries both fail at the same stage: the generated hypotheses are either shallow paraphrases of the source mechanism or physically incorrect at the target scale.

The adversarial gate is NOT too aggressive — it is correctly identifying real flaws. The problem is upstream: the hypothesis generator does not deeply understand the target domain's physics. It substitutes vocabulary without verifying that the proposed mechanism is physically valid at the target scale.

### What would need to change (for future consideration, not for this experiment)

1. **Scale-awareness:** The generator needs to check whether the proposed mechanism operates at the right physical scale. Marangoni effects that work at the microliter scale may not work at the milliliter scale. Capillary forces that work in plant xylem may not work on a 10 m² condenser surface.

2. **Constraint-awareness:** The generator needs to filter against target constraints BEFORE adversarial analysis. DXP-001's H-003 (neural network) violated "no ML infrastructure" — this should have been caught at generation time, not at adversarial time.

3. **Physical verification:** The generator needs to quantify the proposed mechanism's expected effect size. "Capillary forces pull droplets" is not enough — how strong are the forces? Are they sufficient to move a 2 mm droplet on a 10° slope?

These are generator improvements, not infrastructure improvements. The substrate is working correctly. The engine's reasoning is the bottleneck.

---

## Recommendation

1. **Preserve this failure as negative science.** The pattern is clear: GENERATION_DEFECT + MECHANISTIC_DEFECT across two different challenge geometries.

2. **Do NOT tune the adversarial gate.** It is correctly identifying real flaws.

3. **Do NOT change the challenge to make it easier.** That would be post-hoc optimization.

4. **The next improvement should be to the hypothesis generator**, specifically:
   - Scale-awareness: check whether the proposed mechanism is physically valid at the target scale
   - Constraint-awareness: filter against target constraints before adversarial analysis
   - Physical quantification: require the generator to estimate the magnitude of the proposed effect

5. **Run DXP-003 only after the generator is improved.** Running the same engine on a third challenge would likely produce the same result.

---

## North Star status

```
DXP-001:  NOT DISCOVERY (bottleneck: adversarial — TARGET_CONSTRAINT_DEFECT)
DXP-002:  NOT DISCOVERY (bottleneck: adversarial — MECHANISTIC_DEFECT + GENERATION_DEFECT)
Pattern:  Generator produces shallow analogies + physically incorrect mechanisms
          across two different challenge geometries
Supports: H2 (generator weakness) over H1 (challenge mismatch)

Discovery capability:  NOT ESTABLISHED
North Star:            NOT ACHIEVED

The substrate is trustworthy. The engine is not yet a discovery engine.
The bottleneck is now clearly identified: hypothesis generation quality.
