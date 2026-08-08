# Task 2: Traceability Audit

Generated: 2026-08-08T00:40:18.315238+00:00
Commit: a2eab271e943

## Discovery Capability F1 = 0.5714

```
benchmarks/discovery_capability_benchmark.py (GOLD_DISCOVERIES + _bridge_matches)
  ↓ python3 -m benchmarks.discovery_capability_benchmark
benchmarks/reports/discovery_capability_score.json (F1=0.5714)
  ↓ scripts/generate_auditor_scorecard.py
AUDITOR_SCORECARD.md (6/10, F1=0.5714)
```

- **Manual links:** NONE
- **Stale:** NO
- **Provenance:** VERIFIED

## Discovery F1 (shared, DR-91) = 0.7879

```
benchmarks/discovery_capability_benchmark.py (GOLD_DISCOVERIES)
  ↓ programs/A_metrology/bootstrap_statistics.py (independent matchers)
reports/bootstrap_statistics.json (M-005: 0.7879 ± 0.0809)
  ↓ programs/A_metrology/measurement_provenance.py (ScoredValue)
PRELIMINARY_MEASUREMENT_VERDICT.md (current evidence table)
```

- **Manual links:** NONE
- **Stale:** NO
- **Provenance:** VERIFIED

## FP floor = 0.9189

```
benchmarks/discovery_capability_benchmark.py (GOLD_DISCOVERIES + all_entities)
  ↓ programs/A_metrology/bootstrap_statistics.py (M-008, random candidates)
reports/bootstrap_statistics.json (M-008: 0.9189 ± 0.0978)
  ↓ PRELIMINARY_MEASUREMENT_VERDICT.md (current evidence table)
```

- **Manual links:** NONE
- **Stale:** NO
- **Provenance:** VERIFIED (point estimate is seed-dependent, CI [0.667, 1.0])

## Per-proposal F1 = 0.6500

```
benchmarks/discovery_capability_benchmark.py (GOLD_DISCOVERIES + shared_entities)
  ↓ programs/A_metrology/bootstrap_statistics.py (M-010, ALL shared entities)
reports/bootstrap_statistics.json (M-010: 0.6500 ± 0.1081)
  ↓ PRELIMINARY_MEASUREMENT_VERDICT.md
```

- **Manual links:** NONE
- **Stale:** NO
- **Provenance:** VERIFIED

## Gen 1-5 scores (9/10, 9/10, 9/10, 9/10, 9/10)

```
benchmarks/*.py (gen1-gen5 benchmarks)
  ↓ python3 -m benchmarks.* (execution)
benchmarks/reports/gen{1-5}_pr_score.json
  ↓ scripts/generate_auditor_scorecard.py
AUDITOR_SCORECARD.md
```

- **Manual links:** NONE
- **Stale:** NO (gen5 uses different benchmark than discovery_capability)
- **Provenance:** VERIFIED (gen5 F1=0.9375 is connection-finding, NOT discovery capability)

## Discovery F1 = 0.9189 (HISTORICAL)

```
Was: benchmarks/discovery_capability_benchmark.py (with circular BRIDGE_SYNONYMS)
  → discovery_capability_score.json (stale, F1=0.9189)
  → AUDITOR_SCORECARD.md (stale, 9/10)
Now: BRIDGE_SYNONYMS = {} (cycle 270), score regenerated to 0.5714
Historical value preserved in: PRELIMINARY_MEASUREMENT_VERDICT.md (labeled HISTORICAL)
  docs/INVENTION_CONSTITUTION.md (labeled HISTORICAL)
  docs/DR-90_REPRESENTATION_DISCOVERY.md (labeled HISTORICAL)
  docs/MEASUREMENT_SPECIFICATION.md (labeled HISTORICAL)
  FAILURES.md (F-158, append-only)
```

- **Manual links:** Historical value is intentionally preserved for before/after comparison
- **Stale:** NO (labeled HISTORICAL)
- **Provenance:** VERIFIED as historical

## Discovery F1 = 0.8571 (HISTORICAL)

```
Was: DR-91 audit (with circular BRIDGE_SYNONYMS, shared entities + synonyms)
  → PRELIMINARY_MEASUREMENT_VERDICT.md (was current, now historical)
  → audit/measurement_integrity/dr97_external_baselines.py (was production_f1 default)
Now: production_f1=0.7879 (fixed), PRELIMINARY has historical table (labeled)
Historical value preserved in: PRELIMINARY_MEASUREMENT_VERDICT.md (labeled HISTORICAL)
  audit/measurement_integrity/dr98_historical_recalibration.py (intentionally hardcoded as historical claim)
  FAILURES.md (F-158, append-only)
```

- **Manual links:** dr98 hardcodes 0.8571 as claimed_f1 — this is the HISTORICAL claim being re-calibrated
- **Stale:** NO (labeled HISTORICAL or used as historical input)
- **Provenance:** VERIFIED as historical
