# Stage −1 Ablation: Proposal-Locus Measurement

Cycle: 272
Directive: MEASURE, DO NOT FIX
Timestamp: 2026-08-08T01:10:13.301492+00:00

## Findings

1. **Proposal-locus vulnerability: CONFIRMED**
   - 2/8 TPs (25.0%) come from the
     ALL-entities fallback, not from shared entities (genuine discovery)
   - The scorer grants discovery credit when the gold bridge appears as an
     extracted entity in either input paper — the system does not need to
     PROPOSE the bridge

2. **FP = 0 by construction: CONFIRMED**
   - The `fp` variable is initialized to 0 and never incremented
   - The scoring loop only does `tp += 1` or `fn += 1`
   - Precision is always 1.0 — this is NOT a measurement, it's a tautology

3. **0.9189 is NOT an FP floor: CONFIRMED**
   - The 0.9189 in the old discovery_capability_score.json was the
     circular-synonym F1, not an empirically established FP floor
   - The M-008 'FP floor' in the bootstrap is a separate measurement
     (random candidates against gold) — it was incorrectly conflated

## Per-gold breakdown

| ID | Bridge | Locus | Matched | Shared | Ents A | Ents B |
|---|---|---|---|---|---|---|
| DISC-GOLD-001 | biomineralization | MISSED | - | 2 | 4 | 4 |
| DISC-GOLD-002 | tight junctions | MISSED | - | 2 | 5 | 3 |
| DISC-GOLD-003 | thermal emission | MISSED | - | 0 | 4 | 4 |
| DISC-GOLD-004 | thermal regulation | FALLBACK | stable thermal conditions | 0 | 4 | 3 |
| DISC-GOLD-005 | contact angle | FALLBACK | surface wettability angle | 0 | 4 | 3 |
| DISC-GOLD-006 | photon absorption | MISSED | - | 1 | 5 | 4 |
| DISC-GOLD-007 | heat dissipation | SHARED | heat | 2 | 4 | 4 |
| DISC-GOLD-008 | ion selectivity | SHARED | ion | 1 | 4 | 5 |
| DISC-GOLD-009 | electrocatalyst | MISSED | - | 1 | 4 | 5 |
| DISC-GOLD-010 | temperature gradient | MISSED | - | 1 | 4 | 5 |
| DISC-GOLD-011 | surface functionalization | SHARED | surface chemical modification | 1 | 4 | 4 |
| DISC-GOLD-012 | mechanical strain | MISSED | - | 1 | 4 | 3 |
| DISC-GOLD-013 | spin polarization | SHARED | Magnetic resonance imaging detects quantum spin alignment | 1 | 3 | 5 |
| DISC-GOLD-014 | ion storage | SHARED | ion | 2 | 4 | 3 |
| DISC-GOLD-015 | bandgap engineering | MISSED | - | 1 | 3 | 3 |
| DISC-GOLD-016 | high surface area | MISSED | - | 0 | 3 | 4 |
| DISC-GOLD-017 | tensile strength | MISSED | - | 1 | 3 | 4 |
| DISC-GOLD-018 | latent heat | MISSED | - | 3 | 4 | 5 |
| DISC-GOLD-019 | photon energy | SHARED | light quantum energy | 1 | 4 | 3 |
| DISC-GOLD-020 | fiber morphology | MISSED | - | 1 | 5 | 3 |

## Metrics comparison

| Metric | Current (with fallback) | Proposal-only (no fallback) | Inflation |
|---|---|---|---|
| TP | 8 | 6 | +2 |
| Recall | 0.4000 | 0.3000 | +0.1000 |
| Precision | 1.0000 (by construction) | 1.0000 (by construction) | 0 |
| F1 | 0.5714 | 0.4615 | +0.1099 |

## Verdict

**NOT TRUSTWORTHY for claims of independent discovery.**

- 2/8 TPs come from ambient entity presence
- FP=0 by construction (precision is a tautology, not a measurement)
- The scorer does not require the system to propose the bridge
- The F1 of 0.5714 is inflated by both the fallback and the FP=0 construction
- The honest proposal-only F1 is 0.4615

## What NOT to do

Do NOT fix the scorer yet. This ablation is the evidence. Changing
the scorer before recording this measurement would destroy the
audit trail.
