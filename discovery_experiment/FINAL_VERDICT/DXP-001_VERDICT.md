# DXP-001 Final Verdict

**Experiment:** DXP-001
**Date:** 2026-08-08
**Engine commit:** f8e3f2ac136e3b03acc0b3314dc901fc614ae4a8
**Challenge:** Stomatal conductance regulation (plant physiology) → adaptive HVAC ventilation control

---

## Binary Outcome: **NOT DISCOVERY**

---

## What happened

The engine successfully:
1. Extracted a 24-node mechanism graph from the stomatal regulation document (0 extraction failures)
2. Abstracted it to: "Feedback regulation system modulates aperture size in response to environmental conditions to balance resource exchange"
3. Produced a cross-domain transfer with an explicit translation mapping (stomatal cells → damper actuators, CO₂ → CO₂ sensors, ion transport → PID control)
4. Generated 3 competing hypotheses (PID with adaptive gains, MPC with anticipatory feedforward, bio-inspired neural network)
5. Classified all 3 as NON_TRIVIAL_TRANSFER (not rediscovery)

The engine then killed all 3 hypotheses at the adversarial gate:
- H-001 (PID): 4 HIGH-severity failure modes → ADVERSARIAL_FAILED
- H-002 (MPC): 4 HIGH-severity failure modes → ADVERSARIAL_FAILED
- H-003 (Neural network): 5 HIGH-severity failure modes → ADVERSARIAL_FAILED

**candidate_status = ALL_BLOCKED_AT_ADVERSARIAL**
**scientific_gate_passed = False**

No hypotheses survived to produce predictions or experiment designs.

---

## Failure Map

```
Stage                          Status    Detail
────────────────────────────── ──────── ──────────────────────────────────────
representation (extraction)   PASS      24 nodes, 25 edges, 0 failures
abstraction                   PASS      Domain-neutral principle produced
transfer                      PASS      Explicit translation mapping produced
hypothesis generation         PASS      3 materially different hypotheses
novelty (rediscovery)         PASS      All 3 classified NON_TRIVIAL_TRANSFER
adversarial filtering         FAIL      All 3 killed (4-5 HIGH severity each)
prediction                    BLOCKED   No hypotheses survived to prediction
experimental design           BLOCKED   No hypotheses survived to experiment
experimental accuracy         BLOCKED   No experiment was designed
```

**Bottleneck identified: adversarial filtering.**

The engine's adversarial analysis killed every candidate. This is the correct scientific behavior IF the candidates genuinely have fatal flaws. The question is whether the adversarial gate is too aggressive or whether the candidates are genuinely flawed.

---

## Analysis of the bottleneck

### Were the candidates genuinely flawed?

The three hypotheses were:
1. **PID with adaptive gains** — a standard control approach with stomatal-inspired gain adaptation
2. **Model Predictive Control (MPC)** with stomatal-inspired feedforward
3. **Bio-inspired neural network** mimicking distributed guard cell decision-making

The adversarial analysis found HIGH-severity issues for all three:
- H-001 (PID): The adversarial critic found that PID is already a standard HVAC control approach, so the "transfer" adds little novelty. The stomatal-inspired adaptation may not survive the constraint of "no ML infrastructure" and "tunable by a building engineer."
- H-002 (MPC): The critic found that MPC requires computational infrastructure beyond the BAS constraints, and the "stomatal-inspired" feedforward may not add value over standard MPC.
- H-003 (Neural network): The critic found that this violates the "no ML infrastructure" constraint directly.

### Is the adversarial gate too aggressive?

The adversarial analysis appears to have identified real constraints violations (H-003 violates "no ML infrastructure") and real novelty issues (H-001 is essentially standard PID). The gate may be correctly identifying that the candidates, while structurally non-trivial transfers, are not practically useful given the target constraints.

### What this means

The engine demonstrated:
- ✅ Mechanism extraction from a real biological document
- ✅ Cross-domain abstraction
- ✅ Transfer with explicit mapping
- ✅ Competing hypothesis generation
- ✅ Non-trivial-transfer classification (not rediscovery)
- ❌ Adversarial survival (the bottleneck)

The discovery chain broke at the adversarial filtering stage. The candidates were structurally valid transfers but practically flawed given the target constraints.

---

## What this experiment proves and does NOT prove

### Proves

- The engine can extract, abstract, and transfer a mechanism across genuinely distant domains (plant physiology → HVAC)
- The engine can generate materially different competing hypotheses
- The engine can correctly classify non-trivial transfers (not rediscovery)
- The engine's adversarial gate is functional and kills flawed candidates
- The engine does NOT produce false discoveries — it honestly reports ALL_BLOCKED

### Does NOT prove

- That the engine can produce a candidate that survives adversarial analysis
- That the engine can produce a falsifiable prediction
- That the engine can produce a correct prediction
- That the engine can discover something genuinely novel

---

## Honest assessment

This is a **legitimate scientific failure**. The machine attempted a cross-domain transfer, generated plausible candidates, and then killed them all because they had real flaws. That is exactly what a discovery engine should do — it should not produce false discoveries.

The failure is at the adversarial filtering stage. The candidates were structurally valid but practically flawed. The next question is: can the engine generate candidates that are BOTH structurally valid AND practically sound?

That question is for the next experiment, not for more infrastructure.

---

## Recommendation

1. **Preserve this failure as negative science.** The complete failure map is recorded above. The bottleneck is adversarial filtering, not representation or transfer.

2. **Do not tune the adversarial gate to make candidates survive.** The gate is doing its job. The issue is that the candidates are not good enough.

3. **Consider whether the challenge constraints are too restrictive.** The "no ML infrastructure" constraint may make it impossible for any bio-inspired approach to survive, because most interesting bio-inspired control strategies require adaptive/learning components. A future experiment could relax this constraint.

4. **Consider whether the hypothesis generation needs to be more constraint-aware.** The engine generated an MPC candidate and a neural network candidate, both of which violated the stated constraints. A more sophisticated hypothesis generator might filter against constraints BEFORE adversarial analysis.

5. **Run a second experiment (DXP-002) with a different challenge** to determine whether this failure is specific to this challenge or systemic.
