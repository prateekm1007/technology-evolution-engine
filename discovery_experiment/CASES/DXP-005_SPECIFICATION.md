# DXP-005 — Preregistered Generator-Ablation Experiment

**Status:** FROZEN (pre-execution)
**Date:** 2026-08-08
**Engine commit:** 4ae90bc1fd3d1d4bec984a0189b0b2e7be6aa371
**Type:** Ablation — 3 conditions × 10 cases = 30 runs

---

## Hypothesis

**H-GEN-1:** Preserving the source mechanism graph alongside the abstraction improves recovery of the correct target-domain causal mechanism, rather than merely increasing lexical overlap or forcing quantitative output.

## Three Conditions

### A — Baseline
transfer → hypothesis generation (no mechanism graph)

### B — H-GEN-1
mechanism graph + transfer → hypothesis generation (current intervention)

### C — Mechanism-null
mechanism graph with SAME structure/density but IRRELEVANT causal edges + transfer → hypothesis generation

If B improves while C does not → specific mechanism information caused the improvement (not just "more context").

## 10 Cases

### 5 Known-Positive Transfers

| ID | Source | Target | Known mechanism |
|---|---|---|---|
| P1 | Shark skin denticles | Pipe drag reduction | Riblet vortex lifting, 5-10% reduction |
| P2 | Bat echolocation | Radar waveform design | Adaptive pulse duration, range-dependent |
| P3 | Woodpecker shock absorption | Helmet design | Tongue-route force distribution, ~20-30% force reduction |
| P4 | Spider silk | Bulletproof vest | Hierarchical nanostructure energy dissipation |
| P5 | Dolphin blubber | Acoustic insulation | Viscoelastic impedance matching |

### 5 Hard-Negative Transfers

| ID | Source | Target | Why it's wrong |
|---|---|---|---|
| N1 | Gecko adhesion | Underwater adhesive | Dry van der Waals adhesion fails in water — completely different physics |
| N2 | Bird wing lift | Submarine hull design | Aerodynamic lift ≠ hydrodynamic displacement; wrong mechanism |
| N3 | Cactus water storage | Battery electrolyte | Osmotic water storage ≠ electrochemical storage; no mechanism transfer |
| N4 | Chameleon color change | LED display | Structural color vs electroluminescence; no causal mechanism overlap |
| N5 | Firefly luminescence | Solar cell efficiency | Chemical bioluminescence ≠ photovoltaic conversion; wrong physics |

## Information Boundary

The mechanism graph may contain the SOURCE mechanism.
It must NOT contain the source→target transfer.

## Scoring

### Primary endpoints
1. Correct causal mechanism (YES/NO/PARTIAL)
2. Correct causal variable (YES/NO/PARTIAL)
3. Correct direction (YES/NO)
4. Mechanistic traceability (can the hypothesis be traced to source causal edges?)
5. Target-domain physical validity (YES/NO/QUESTIONABLE)

### Secondary endpoint
6. Quantitative prediction accuracy:
   - NO NUMBER
   - NUMBER BUT WRONG
   - ORDER-OF-MAGNITUDE CORRECT
   - RANGE CORRECT
   - PARAMETER + RANGE + CONDITIONS CORRECT

### Lexical copy test
- source mechanism lexical overlap score
- mechanism-specific terminology overlap score

### Adversarial classification (per objection)
- VALID_FATAL
- VALID_NONFATAL
- FACTUALLY_WRONG
- UNSUPPORTED
- DUPLICATIVE

## Success Criteria

### H-GEN-1 supported if (on positive cases):
- Correct mechanism rate: B > A AND B > C
- Correct causal variable: B > A AND B > C
- Physical validity: B > A AND B > C
- Quantitative accuracy: B > A AND B > C

### H-GEN-1 NOT harmful if (on negative cases):
- False transfer rate: B ≤ A + 1
- False mechanism rate: B ≤ A + 1
- No increase in adversarially undetectable nonsense

### Filter behavior:
- Adversarial gate UNCHANGED across all conditions
- False-positive kill rate calculated separately
- True-positive rejection rate calculated separately

## Hard Stop

- H-GEN-1 fails → generator hypothesis rejected
- H-GEN-1 improves positives but increases false positives → insufficient
- H-GEN-1 improves positives AND preserves negatives AND filter stable → supported → then test prediction generation
