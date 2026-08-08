# Task 3: Repository Consistency Audit

Generated: 2026-08-08T00:00:08.659717+00:00
Commit: 808654db911b

## Search methodology

**BUG count (stale values presented as current): 186**

Searched all .md, .py, .json files for the following values.
Each occurrence classified as:
- **CURRENT**: the value is the actual current measurement (verified by execution)
- **HISTORICAL**: the value is a past measurement, clearly labeled as historical
- **EXAMPLE**: the value is used as an example or illustration, not as a claim
- **BUG**: the value is stale and presented as current (needs fixing)

## 0.9189
**Description:** Old discovery capability F1 (circular, cycle 201-270)

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 3081 | inflated. The honest F1 is 0.9189 (recall=0.85) after de-circularization. | HISTORICAL |
| FAILURES.md | 3087 | Honest result: F1=0.9189, recall=0.85, 17 TP, 3 FN. | HISTORICAL |
| FAILURES.md | 5712 | The F1=0.9189 (reported since cycle 201) may be overstated: | HISTORICAL |
| FAILURES.md | 5729 | However, the discovery F1=0.9189 (used in scorecards and maturity | HISTORICAL |
| FAILURES.md | 5758 | The F1=0.9189 that has been reported since cycle 201 may be inflated | HISTORICAL |
| FAILURES.md | 5821 | - The discovery F1=0.9189 reported since cycle 201 is NOT reliable. | HISTORICAL |
| FAILURES.md | 5831 | - Discovery scorecard (9.0/10): AFFECTED. Rests on F1=0.9189 which | HISTORICAL |
| FAILURES.md | 6001 | | Discovery F1=0.9189 | YES — INVALID | Measured entity recognition, not bridge  | HISTORICAL |
| FAILURES.md | 6702 | - HC-005 (cycle 201 F1=0.9189) ERODED — already documented in DR-91 | HISTORICAL |
| FAILURES.md | 7046 | | M-008 FP floor | 0.9189 ± 0.0559 | [0.7879, 1.0000] | Confirms DR-91 finding:  | HISTORICAL |
| FAILURES.md | 7100 | - The FP floor=1.0000 is now FP floor=0.9189 ± 0.0559 (95% CI: 0.7879, | HISTORICAL |
| FAILURES.md | 8350 | | M-008 FP floor | 0.9189 | 0.9189 | unchanged | | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 31 | | FP floor (synonym) | 0.9189 ± 0.0559 | [0.7879, 1.0000] | 20 | 200 | | BUG |
| docs/MEASUREMENT_REASSESSMENT.md | 21 | | Discovery F1=0.9189 | Entity recognition | YES — INVALID | Measured recognitio | HISTORICAL |
| docs/MEASUREMENT_REASSESSMENT.md | 22 | | Discovery scorecard 9.0/10 | F1=0.9189 | YES — UNVERIFIED | True F1 unknown | | HISTORICAL |
| docs/MEASUREMENT_HISTORY.md | 11 | | 201 | 0.9189 | Entity (20-gold, non-circular) | INVALID | F-099 fixed circular | HISTORICAL |
| docs/DR-90_REPRESENTATION_DISCOVERY.md | 40 | - Discovery Engine (F1=0.9189) | HISTORICAL |
| docs/MEASUREMENT_SPECIFICATION.md | 33 | - **Discovery F1 = 0.9189**: INVALID (measured entity recognition, not discovery | HISTORICAL |
| docs/INVENTION_CONSTITUTION.md | 27 | | Discovery | Find relationships not explicitly stated | ✅ Done (F1=0.9189, non- | HISTORICAL |
| docs/INVENTION_CONSTITUTION.md | 59 | it continuously. The current honest discovery F1=0.9189 is defensible but | HISTORICAL |
| docs/DISCOVERY_OBJECT_AUDIT.md | 123 | 1. **Discovery F1=0.9189** becomes meaningless — it measured entity | HISTORICAL |
| docs/DISCOVERY_OBJECT_AUDIT.md | 171 | Previous claim: "Discovery F1 = 0.9189" | HISTORICAL |
| reports/bootstrap_statistics.md | 28 | | M-005 | Discovery F1 (shared, syn, DR-91) | 0.7879 ± 0.0809 | [0.6207, 0.9189] | CURRENT |
| reports/bootstrap_statistics.md | 29 | | M-006 | Recognition F1 (all, syn, DR-91) | 0.9744 ± 0.0252 | [0.9189, 1.0000]  | CURRENT |
| reports/bootstrap_statistics.md | 31 | | M-008 | FP floor (synonym) | 0.9189 ± 0.0978 | [0.6667, 1.0000] | 20 | 200 | n | CURRENT |
| reports/bootstrap_statistics.md | 35 | | M-012 | Aggregate F1 (DR-91) | 0.7879 ± 0.0809 | [0.6207, 0.9189] | 20 | 500 | | CURRENT |
| reports/measurement_constitution_m8.json | 388 | "evidence": "M3 bootstrap exists: True (CI=0.6207, 0.9189)", | BUG |
| reports/measurement_constitution_m8.json | 452 | "evidence": "M3 bootstrap exists: True (CI=0.9189, 1.0)", | BUG |
| reports/measurement_constitution_m8.json | 836 | "evidence": "M3 bootstrap exists: True (CI=0.6207, 0.9189)", | BUG |
| reports/calibration_documented_m2e1.json | 44 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 76 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 92 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 108 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 124 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 139 | "fp_floor": 0.9189, | BUG |
| reports/calibration_documented_m2e1.json | 140 | "notes": "FP floor = 0.9189. CATASTROPHIC (>5% threshold). The metric IS the cal | BUG |
| reports/calibration_documented_m2e1.json | 172 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 204 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 220 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 236 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 252 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/calibration_documented_m2e1.json | 268 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exists but FP floor blo | BUG |
| reports/bootstrap_statistics.json | 87 | "ci_95_upper": 0.9189, | CURRENT |
| reports/bootstrap_statistics.json | 103 | "ci_95_lower": 0.9189, | CURRENT |
| reports/bootstrap_statistics.json | 133 | "point_estimate": 0.9189, | CURRENT |
| reports/bootstrap_statistics.json | 206 | "ci_95_upper": 0.9189, | CURRENT |
| reports/calibration_documented_m2e1.md | 23 | | M-002 | Token F1 (all entities) | PARTIALLY_CALIBRATED | YES | DR-91 independe | BUG |
| reports/calibration_documented_m2e1.md | 25 | | M-004 | Synonym F1 (all entities) | PARTIALLY_CALIBRATED | YES | DR-91 indepen | BUG |
| reports/calibration_documented_m2e1.md | 26 | | M-005 | Discovery F1 (shared, syn, DR-91) | PARTIALLY_CALIBRATED | YES | DR-91 | BUG |
| reports/calibration_documented_m2e1.md | 27 | | M-006 | Recognition F1 (all, syn, DR-91) | PARTIALLY_CALIBRATED | YES | DR-91  | BUG |
| reports/calibration_documented_m2e1.md | 28 | | M-007 | Proposal-locus inflation | PARTIALLY_CALIBRATED | YES | DR-91 independ | BUG |
| reports/calibration_documented_m2e1.md | 29 | | M-008 | FP floor (synonym) | PARTIALLY_CALIBRATED | YES | DR-91 adversarial te | BUG |
| reports/calibration_documented_m2e1.md | 31 | | M-010 | Per-proposal F1 (honest, lenient, A | PARTIALLY_CALIBRATED | YES | DR- | BUG |
| reports/calibration_documented_m2e1.md | 33 | | M-012 | Aggregate F1 (DR-91) | PARTIALLY_CALIBRATED | YES | DR-91 independent  | BUG |
| reports/calibration_documented_m2e1.md | 34 | | M-013 | Aggregate F1 (honest) | PARTIALLY_CALIBRATED | YES | DR-91 independent | BUG |
| reports/calibration_documented_m2e1.md | 35 | | M-014 | BM25 recall@1 (lenient) | PARTIALLY_CALIBRATED | YES | DR-91 independe | BUG |
| reports/calibration_documented_m2e1.md | 36 | | M-015 | Random baseline F1 (lenient) | PARTIALLY_CALIBRATED | YES | DR-91 inde | BUG |
| reports/calibration_documented_m2e1.md | 37 | | M-016 | Frequency baseline F1 (lenient) | PARTIALLY_CALIBRATED | YES | DR-91 i | BUG |
| reports/discovery_score_recalibration.md | 15 | - F1 = 0.9189 | BUG |
| reports/discovery_score_recalibration.md | 16 | - Score = 9/10 (round(10 × 0.9189) = 9) | BUG |
| reports/discovery_score_recalibration.md | 30 | The score dropped from 9/10 (F1=0.9189) to 6/10 (F1=0.5714) because: | BUG |
| reports/discovery_score_recalibration.md | 38 | the code said BRIDGE_SYNONYMS = {} but the scorecard said F1=0.9189. | BUG |
| reports/discovery_score_recalibration.md | 50 | bridges matched (F1=0.9189). With the empty synonym map (non-circular), | BUG |
| reports/historical_recalibration.md | 29 | | HC-005 | 201 | Discovery F1 (the headline number, reported since cycle 201) |  | BUG |
| reports/failure_envelope_m7.json | 166 | 0.9189 | HISTORICAL |
| reports/failure_envelope_m7.json | 216 | 0.9189, | HISTORICAL |
| reports/failure_envelope_m7.json | 282 | "baseline_value": 0.9189, | HISTORICAL |
| reports/failure_envelope_m7.json | 293 | "FP floor = 0.9189 \u00b1 0.0559 [0.7879, 1.0000] \u2014 CATASTROPHIC", | HISTORICAL |
| reports/failure_envelope_m7.json | 431 | 0.9189 | HISTORICAL |
| reports/failure_envelope_m7.json | 770 | "THIS IS THE METRIC DR-91 INVALIDATED (F1=0.9189 was measuring recognition, not  | HISTORICAL |
| reports/failure_envelope_m7.json | 781 | "DR-91 invalidation: headline F1=0.9189 was recognition, not discovery" | HISTORICAL |
| reports/historical_recalibration.json | 112 | "claimed_f1": 0.9189, | BUG |
| reports/historical_recalibration.json | 122 | "delta_vs_claimed_strict": -0.9189, | BUG |
| reports/failure_envelope_m7.md | 45 | | M-008 | FP floor (synonym) | 0.9189 | False | STABLE | 0 | | HISTORICAL |
| tests/test_dr98_historical_recalibration.py | 173 | """HC-005 (cycle 201 F1=0.9189) was invalidated by DR-91; should NOT SURVIVE.""" | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 16 | - cycle 201: F1=0.9189 (discovery F1, reported since) | BUG |
| audit/measurement_integrity/dr98_historical_recalibration.py | 19 | DR-91 already showed F1=0.9189 was invalid (it measured entity | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 225 | claimed_f1=0.9189, | BUG |
| audit/measurement_integrity/dr98_historical_recalibration.py | 440 | # HC-005 (cycle 201 F1=0.9189) was already invalidated by DR-91. | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 451 | print(f"  - HC-005 (cycle 201 F1=0.9189) is {hc005['verdict_dr91_convention']} a | BUG |
| audit/measurement_integrity/dr98_historical_recalibration.py | 611 | lines.append("F1=0.9189 (HC-005) is ERODED — already documented in DR-91.") | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 70 | old_score = 0.9189  # the known stale value | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 99 | lines.append(f"- Score = 9/10 (round(10 × 0.9189) = 9)") | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 113 | lines.append("The score dropped from 9/10 (F1=0.9189) to " | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 122 | lines.append("   the code said BRIDGE_SYNONYMS = {} but the scorecard said F1=0. | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 134 | lines.append("bridges matched (F1=0.9189). With the empty synonym map (non-circu | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 243 | "0.9189": "Old discovery capability F1 (circular, cycle 201-270)", | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 463 | lines.append(f"- Was: F1=0.9189, Score=9/10 (stale, circular)") | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 500 | lines.append("DISCOVERY_OBJECT_AUDIT.md, etc.) cite old values (0.9189) and are  | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 511 | lines.append("- PRELIMINARY_MEASUREMENT_VERDICT.md: **NO** — still contains 0.85 | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 514 | lines.append("- dr98_historical_recalibration.py: **NO** — hardcoded `claimed_f1 | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 517 | lines.append("- docs/ files: **NO** — multiple files cite 0.9189 as current") | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 522 | lines.append("3. docs/INVENTION_CONSTITUTION.md: mark 0.9189 as historical") | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 532 | lines.append("2. **docs/INVENTION_CONSTITUTION.md**: claims 'Discovery F1=0.9189 | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 536 | lines.append("4. **docs/DR-90_REPRESENTATION_DISCOVERY.md**: cites 'F1=0.9189'") | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 537 | lines.append("5. **docs/MEASUREMENT_SPECIFICATION.md**: cites 'F1=0.9189' as cur | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 549 | lines.append("  (was 0.9189 with circular synonyms)") | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 559 | lines.append("1. **'Discovery F1 = 0.9189'** — this was circular. Current honest | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 578 | lines.append(f"1. Regenerated discovery_capability_score.json: F1 0.9189 → {task | BUG |
| programs/A_metrology/measurement_provenance.py | 457 | value=0.9189, | EXAMPLE |
| programs/A_metrology/failure_envelope_m7.py | 354 | "FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 585 | "THIS IS THE METRIC DR-91 INVALIDATED (F1=0.9189 was measuring recognition, not  | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 596 | "DR-91 invalidation: headline F1=0.9189 was recognition, not discovery", | HISTORICAL |
| programs/A_metrology/MeasurementEngineSpecification.md | 803 | - THIS IS THE METRIC DR-91 INVALIDATED. The F1=0.9189 reported since | HISTORICAL |
| reports/failure_envelopes/M-005.md | 8 | - **95% CI:** [0.6207, 0.9189] | HISTORICAL |
| reports/failure_envelopes/M-105.md | 15 | - THIS IS THE METRIC DR-91 INVALIDATED (F1=0.9189 was measuring recognition, not | HISTORICAL |
| reports/failure_envelopes/M-105.md | 28 | - DR-91 invalidation: headline F1=0.9189 was recognition, not discovery | HISTORICAL |
| reports/failure_envelopes/M-006.md | 8 | - **95% CI:** [0.9189, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-012.md | 8 | - **95% CI:** [0.6207, 0.9189] | HISTORICAL |
| reports/failure_envelopes/M-008.md | 7 | - **Baseline value:** 0.9189 | HISTORICAL |
| reports/failure_envelopes/M-008.md | 15 | - FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC | HISTORICAL |

## 0.8571
**Description:** Old discovery F1 shared/synonym (circular, cycle 243-270)

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 5685 | 3. **Proposal-only F1 = 0.8571 (shared entities + synonyms)** | HISTORICAL |
| FAILURES.md | 5777 | | synonym | 1.0000 | 0.8571 | | HISTORICAL |
| FAILURES.md | 5794 | Discovery F1 = 0.8571 | HISTORICAL |
| FAILURES.md | 5822 | - The honest Discovery F1 (shared entities, synonyms) = 0.8571. | HISTORICAL |
| FAILURES.md | 6700 | - HC-006 (production F1=0.8571) SURVIVES under DR-91 convention | HISTORICAL |
| FAILURES.md | 6712 | aggregate F1=0.8571 in PRELIMINARY — different metrics) | HISTORICAL |
| FAILURES.md | 6750 | production F1=0.8571 in PRELIMINARY_MEASUREMENT_VERDICT.md is | HISTORICAL |
| FAILURES.md | 6753 | 0.1500 — much lower than the aggregate F1 of 0.8571. These | HISTORICAL |
| FAILURES.md | 6856 | F1 disclosure (0.1500 vs aggregate 0.8571) | HISTORICAL |
| FAILURES.md | 7045 | | M-005 Discovery F1 (DR-91) | 0.8571 ± 0.0635 | [0.7097, 0.9474] | The headline | HISTORICAL |
| FAILURES.md | 7097 | - The headline F1=0.8571 is now F1=0.8571 ± 0.0635 (95% CI: 0.7097, | HISTORICAL |
| FAILURES.md | 7384 | "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500, | HISTORICAL |
| FAILURES.md | 7454 | # "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500, | HISTORICAL |
| FAILURES.md | 7524 | | M-005 Discovery F1 (DR-91) | 0.8571 | 0.0000 | 0.0000 | 0.0000 | STABLE (DETER | HISTORICAL |
| FAILURES.md | 7552 | same value (0.8571 for DR-91, 0.8333 for honest). | HISTORICAL |
| FAILURES.md | 8015 | | M-005 Discovery F1 | 0.8571 | 0.0000 | 0.0000 | STABLE (DETERMINISTIC) | | HISTORICAL |
| FAILURES.md | 8348 | | M-005 Discovery F1 | 0.8571 | 0.7879 | ↓ (honest drop) | | HISTORICAL |
| FAILURES.md | 8358 | HC-006 (production F1=0.8571) is now ERODED (not SURVIVES) under | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 28 | | Discovery F1 (shared, syn, DR-91) | 0.8571 ± 0.0635 | [0.7097, 0.9474] | 20 |  | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 34 | | Aggregate F1 (DR-91) | 0.8571 ± 0.0635 | [0.7097, 0.9474] | 20 | 500 | | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 56 | | Discovery F1 (shared, synonyms) | 0.8571 | | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 87 | The aggregate F1 of 0.8571 above is the system-level score. The | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 91 | - Aggregate F1 = 0.8571: "of the 20 gold bridges, 17/20 are matched | BUG |
| docs/MATCHING_SPECIFICATION.md | 23 | | synonym | Token + synonym map | 1.0000 | 0.8571 | | HISTORICAL |
| docs/MATCHING_SPECIFICATION.md | 28 | - **Discovery F1** (shared entities + synonyms): 0.8571 | HISTORICAL |
| docs/MEASUREMENT_HISTORY.md | 13 | | 242 | 0.8571 | Entity (shared + synonyms, proposal-only) | INVALID | Still ent | HISTORICAL |
| docs/DISCOVERY_VS_RECOGNITION.md | 25 | - Discovery F1 = 0.8571 (shared entities + synonyms) | HISTORICAL |
| reports/bootstrap_statistics.md | 97 | numbers (F1=0.8571, etc.) must be updated to include bootstrap CIs. | CURRENT |
| reports/final_verdict_eligibility.json | 11 | "production_f1_lenient": 0.8571, | BUG |
| reports/final_verdict_eligibility.json | 17 | "production_f1": 0.8571, | BUG |
| reports/final_verdict_eligibility.json | 24 | "production_f1": 0.8571, | BUG |
| reports/final_verdict_eligibility.json | 31 | "production_f1": 0.8571, | BUG |
| reports/repeatability_m4.md | 35 | | M-005 | Discovery F1 (DR-91, shared, syn) | 0.8571 | 0.0000 | 0.0000 | 0.8571  | BUG |
| reports/repeatability_m4.md | 36 | | M-008 | FP floor (synonym) | 0.9595 | 0.0405 | 0.0422 | 0.8571 | 1.0000 | 0.14 | BUG |
| reports/repeatability_m4.md | 60 | - **M-005** (Discovery F1 (DR-91, shared, syn)): DETERMINISTIC — produces the sa | BUG |
| reports/historical_recalibration.md | 30 | | HC-006 | 243 | Proposal-only F1 (shared entities + synonyms, DR-91 audit) | 0. | BUG |
| reports/historical_recalibration.md | 53 | DR-91-convention F1. This means the production F1=0.8571 reported | BUG |
| reports/failure_envelope_m7.json | 196 | "F1 drops from 0.8571 to 0.5714 when snippets truncated (M6)", | HISTORICAL |
| reports/failure_envelope_m7.json | 446 | "F1 = 0.8571 (same as M-005)", | HISTORICAL |
| reports/failure_envelope_m7.json | 570 | "Production (0.8571) beats this by \u0394=+0.76 \u2014 but comparison is oracle- | HISTORICAL |
| reports/failure_envelope_m7.json | 777 | "The gen5 F1 (0.9375) is DIFFERENT from M-005 (0.8571) \u2014 not interchangeabl | HISTORICAL |
| reports/external_baselines.json | 6 | "production_f1_lenient": 0.8571, | BUG |
| reports/external_baselines.json | 631 | "production_f1": 0.8571, | BUG |
| reports/external_baselines.json | 638 | "production_f1": 0.8571, | BUG |
| reports/external_baselines.json | 645 | "production_f1": 0.8571, | BUG |
| reports/external_baselines.md | 14 | Production under lenient mode scores F1=0.8571, but the FP floor | BUG |
| reports/external_baselines.md | 34 | | Production (lenient) | 0.8571 | — | reference | | BUG |
| reports/historical_recalibration.json | 133 | "claimed_f1": 0.8571, | BUG |
| reports/historical_recalibration.json | 143 | "delta_vs_claimed_strict": -0.8571, | BUG |
| reports/repeatability_m4.json | 37 | 0.8571, | BUG |
| reports/repeatability_m4.json | 38 | 0.8571, | BUG |
| reports/repeatability_m4.json | 39 | 0.8571, | BUG |
| reports/repeatability_m4.json | 40 | 0.8571, | BUG |
| reports/repeatability_m4.json | 41 | 0.8571, | BUG |
| reports/repeatability_m4.json | 42 | 0.8571, | BUG |
| reports/repeatability_m4.json | 43 | 0.8571, | BUG |
| reports/repeatability_m4.json | 44 | 0.8571, | BUG |
| reports/repeatability_m4.json | 45 | 0.8571, | BUG |
| reports/repeatability_m4.json | 46 | 0.8571 | BUG |
| reports/repeatability_m4.json | 48 | "mean": 0.8571, | BUG |
| reports/repeatability_m4.json | 51 | "min": 0.8571, | BUG |
| reports/repeatability_m4.json | 52 | "max": 0.8571, | BUG |
| reports/repeatability_m4.json | 80 | 0.8571, | BUG |
| reports/repeatability_m4.json | 90 | "min": 0.8571, | BUG |
| tests/test_bootstrap_statistics.py | 187 | point_estimate=0.8571, bootstrap_mean=0.85, bootstrap_std=0.0635, | HISTORICAL |
| tests/test_bootstrap_statistics.py | 194 | assert "0.8571" in s | HISTORICAL |
| tests/test_bootstrap_statistics.py | 360 | Note: was 0.8571 before cycle 270 (circular synonyms removed). | HISTORICAL |
| tests/test_measurement_provenance.py | 49 | value=0.8571, metric_id="M-005", metric_name="Discovery F1", | EXAMPLE |
| tests/test_measurement_provenance.py | 58 | assert d["value"] == 0.8571 | EXAMPLE |
| tests/test_measurement_provenance.py | 67 | value=0.8571, metric_id="M-005", metric_name="Discovery F1", | EXAMPLE |
| tests/test_measurement_provenance.py | 76 | assert "0.8571" in s | EXAMPLE |
| tests/test_measurement_provenance.py | 156 | value=0.8571, metric_id="M-005", metric_name="Discovery F1", | EXAMPLE |
| tests/test_measurement_provenance.py | 160 | assert sv.value == 0.8571 | EXAMPLE |
| tests/test_measurement_provenance.py | 207 | return 0.8571 | EXAMPLE |
| tests/test_measurement_provenance.py | 211 | assert result.value == 0.8571 | EXAMPLE |
| tests/test_measurement_provenance.py | 291 | assert is_naked_number(0.8571) is True | EXAMPLE |
| tests/test_measurement_provenance.py | 335 | return 0.8571 | EXAMPLE |
| tests/test_measurement_provenance.py | 340 | assert result.ci_95_lower < 0.8571 | EXAMPLE |
| tests/test_measurement_provenance.py | 341 | assert result.ci_95_upper > 0.8571 | EXAMPLE |
| tests/test_dr101_final_verdict_eligibility.py | 30 | "production_f1_strict": 0.0, "production_f1_lenient": 0.8571, | BUG |
| tests/test_dr98_historical_recalibration.py | 154 | # (was 0.8571 with circular synonyms). Delta = -0.069 → ERODED | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 17 | - DR-91 audit: F1=0.8571 (proposal-only, shared/synonym) | BUG |
| audit/measurement_integrity/dr98_historical_recalibration.py | 236 | claimed_f1=0.8571, | BUG |
| audit/measurement_integrity/dr98_historical_recalibration.py | 267 | historical headline numbers (0.8571, 1.0000). It assumes precision = | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 449 | print(f"  - HC-006 (production F1=0.8571) SURVIVES at {hc006['rescored_lenient_f | BUG |
| audit/measurement_integrity/dr98_historical_recalibration.py | 581 | lines.append("DR-91-convention F1. This means the production F1=0.8571 reported" | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 546 | def compare_to_production(baseline_results: Dict, production_f1: float = 0.8571) | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 552 | (default 0.8571 = proposal-locus shared/synonym F1) | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 594 | print(f"Production F1 (PRELIMINARY verdict, shared/synonym): 0.8571") | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 625 | print("Reference: production LENIENT F1 = 0.8571; FP floor = 1.0000") | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 637 | print(f"{'Production (lenient, DR-91)':<40} {0.8571:<10.4f}") | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 648 | compare_to_production(bm25_len, production_f1=0.8571), | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 649 | compare_to_production(rnd_len, production_f1=0.8571), | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 650 | compare_to_production(freq_len, production_f1=0.8571), | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 665 | print(f"CRITICAL: production (0.8571) does NOT meaningfully beat the") | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 669 | print(f"random candidates. Production F1=0.8571 is NOT a discovery") | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 714 | "production_f1_lenient": 0.8571, | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 755 | lines.append("  Production under lenient mode scores F1=0.8571, but the FP floor | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 774 | lines.append(f"| Production (lenient) | 0.8571 | — | reference |") | BUG |
| audit/measurement_integrity/dr101_final_verdict_eligibility.py | 292 | lines.append(f"- Aggregate (PRELIMINARY): {gate_a.get('production_f1_lenient', 0 | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 244 | "0.8571": "Old discovery F1 shared/synonym (circular, cycle 243-270)", | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 438 | "M-005": ("Discovery F1 (shared, DR-91)", 0.8571), | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 511 | lines.append("- PRELIMINARY_MEASUREMENT_VERDICT.md: **NO** — still contains 0.85 | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 513 | lines.append("- dr97_external_baselines.py: **NO** — hardcoded `production_f1=0. | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 514 | lines.append("- dr98_historical_recalibration.py: **NO** — hardcoded `claimed_f1 | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 521 | lines.append("2. dr97_external_baselines.py: update production_f1 default from 0 | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 530 | lines.append("1. **PRELIMINARY_MEASUREMENT_VERDICT.md**: reports F1=0.8571 (was  | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 534 | lines.append("3. **dr97_external_baselines.py**: uses production_f1=0.8571 as de | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 561 | lines.append("3. **'Discovery F1 = 0.8571'** — this was inflated by circular syn | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 585 | lines.append("- Update dr97 production_f1 default from 0.8571 to 0.7879") | BUG |
| programs/A_metrology/bootstrap_statistics.py | 1300 | lines.append("numbers (F1=0.8571, etc.) must be updated to include bootstrap CIs | BUG |
| programs/A_metrology/measurement_provenance.py | 43 | "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500, | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 62 | # "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500, | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 68 | value=0.8571, | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 172 | """Canonical string: 'M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=5 | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 186 | """Short string: 'M-005 = 0.8571 ± 0.0635 [0.7097, 0.9474]'""" | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 393 | "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=500, | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 400 | """Short format: 'M-005 = 0.8571 ± 0.0635 [0.7097, 0.9474]'""" | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 443 | value=0.8571, | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 494 | return 0.8571 | EXAMPLE |
| programs/A_metrology/measurement_provenance.py | 519 | print(f"  is_naked_number(0.8571) = {is_naked_number(0.8571)}") | EXAMPLE |
| programs/A_metrology/failure_envelope_m7.py | 311 | "F1 drops from 0.8571 to 0.5714 when snippets truncated (M6)", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 435 | "F1 = 0.8571 (same as M-005)", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 493 | "Production (0.8571) beats this by Δ=+0.76 — but comparison is oracle-assisted", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 592 | "The gen5 F1 (0.9375) is DIFFERENT from M-005 (0.8571) — not interchangeable", | HISTORICAL |
| programs/A_metrology/MeasurementEngineSpecification.md | 205 | - Returns 0.8571 (current value) under DR-91 formula | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 383 | - Returns 0.8571 for current gold | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 406 | - Returns 0.8333 for current gold (lower than M-012's 0.8571) | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 472 | - Production (0.8571) beats this by Δ=+0.76 — but the comparison is | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 805 | (F-143, F-145). The honest F1 is 0.8571 (DR-91 convention) or | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 818 | F1=0.8571). The gen5 metric measures connection-finding (retrieval + | BUG |
| reports/failure_envelopes/M-005.md | 27 | - F1 drops from 0.8571 to 0.5714 when snippets truncated (M6) | HISTORICAL |
| reports/failure_envelopes/M-015.md | 31 | - Production (0.8571) beats this by Δ=+0.76 — but comparison is oracle-assisted | HISTORICAL |
| reports/failure_envelopes/M-105.md | 23 | - The gen5 F1 (0.9375) is DIFFERENT from M-005 (0.8571) — not interchangeable | HISTORICAL |
| reports/failure_envelopes/M-012.md | 24 | - F1 = 0.8571 (same as M-005) | HISTORICAL |

## 1.0000
**Description:** Old recognition F1 (circular, cycle 243-270)

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 5677 | 2. **Production F1 = 1.0000 (all entities + synonyms)** | HISTORICAL |
| FAILURES.md | 5682 | - 20/20 synonym matches (F1=1.0000) | HISTORICAL |
| FAILURES.md | 5691 | 4. **Shuffled gold FP floor = 1.0000** | HISTORICAL |
| FAILURES.md | 5777 | | synonym | 1.0000 | 0.8571 | | HISTORICAL |
| FAILURES.md | 5793 | Recognition F1 = 1.0000 | HISTORICAL |
| FAILURES.md | 5799 | ALL modes: FP floor = 1.0000, verdict = FAIL | HISTORICAL |
| FAILURES.md | 5805 | 1. FP floor = 1.0000 (>5% threshold) — CATASTROPHIC | HISTORICAL |
| FAILURES.md | 5823 | - The Recognition F1 (all entities, synonyms) = 1.0000. | HISTORICAL |
| FAILURES.md | 5861 | | BASELINE (all + synonyms) | 1.0000 | 1.0000 | — | — | | HISTORICAL |
| FAILURES.md | 5862 | | Disable synonyms (token only) | 1.0000 | 0.9500 | +0.00 | -0.05 | | HISTORICAL |
| FAILURES.md | 5863 | | Disable token overlap (exact only) | 1.0000 | 0.0000 | +0.00 | -1.00 | | HISTORICAL |
| FAILURES.md | 5864 | | Disable proposal inflation (shared only) | 1.0000 | 0.7500 | +0.00 | -0.25 | | HISTORICAL |
| FAILURES.md | 5865 | | Disable BOTH (shared + exact) | 1.0000 | 0.0000 | +0.00 | -1.00 | | HISTORICAL |
| FAILURES.md | 5866 | | Fuzzy only | 1.0000 | 0.0000 | +0.00 | -1.00 | | HISTORICAL |
| FAILURES.md | 5868 | **CRITICAL FINDING: FP floor = 1.0000 regardless of which component is disabled. | HISTORICAL |
| FAILURES.md | 5879 | | plausible_nonsense | 20 | 20 | 1.0000 | FAIL | | HISTORICAL |
| FAILURES.md | 5880 | | cross_domain_distractors | 20 | 20 | 1.0000 | FAIL | | HISTORICAL |
| FAILURES.md | 5881 | | near_identical | 18 | 18 | 1.0000 | FAIL | | HISTORICAL |
| FAILURES.md | 5882 | | same_noun_different | 18 | 18 | 1.0000 | FAIL | | HISTORICAL |
| FAILURES.md | 5883 | | random_entities | 20 | 20 | 1.0000 | FAIL | | HISTORICAL |
| FAILURES.md | 5968 | | Entity (noun) | 1.0000 | FAIL — any noun matches | | HISTORICAL |
| FAILURES.md | 6038 | | A: Entity | 0.9500 | 0.1000 | 1.0000 | 9.50 | FAIL | | HISTORICAL |
| FAILURES.md | 6701 | - HC-007 (recognition F1=1.0000) SURVIVES under DR-91 convention | HISTORICAL |
| FAILURES.md | 7046 | | M-008 FP floor | 0.9189 ± 0.0559 | [0.7879, 1.0000] | Confirms DR-91 finding:  | HISTORICAL |
| FAILURES.md | 7100 | - The FP floor=1.0000 is now FP floor=0.9189 ± 0.0559 (95% CI: 0.7879, | HISTORICAL |
| FAILURES.md | 7101 | 1.0000; N=20, B=200). The CI touches 1.0, confirming the | HISTORICAL |
| FAILURES.md | 7281 | - M-101 Gen 1 Document Parsing F1: 1.0000 ± 0.0000 [1.0000, 1.0000] | HISTORICAL |
| FAILURES.md | 7287 | - M-104 Gen 4 Mechanism Extraction F1: 0.9091 ± 0.0677 [0.7368, 1.0000] | HISTORICAL |
| FAILURES.md | 7289 | - M-105 Gen 5 Discovery Layer F1: 0.9375 ± 0.0464 [0.8276, 1.0000] | HISTORICAL |
| FAILURES.md | 7293 | - M-201 L5a held-out: 0.9000 ± 0.0891 [0.7000, 1.0000] N=10 B=100 | HISTORICAL |
| FAILURES.md | 7298 | - M-203 L5b+Synthesis: 0.9000 ± 0.0891 [0.7000, 1.0000] | HISTORICAL |
| FAILURES.md | 7303 | - M-205 Composite selection rate: 1.0000 ± 0.0000 [1.0000, 1.0000] | HISTORICAL |
| FAILURES.md | 8349 | | M-006 Recognition F1 | 1.0000 (DEGENERATE) | 0.9744 (NOT degenerate) | ↑ IMPRO | HISTORICAL |
| FAILURES.md | 8354 | Key improvement: M-006 is NO LONGER DEGENERATE. Was 1.0000 (always | HISTORICAL |
| FAILURES.md | 8391 | circular synonyms (everything matched → 1.0000). | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 29 | | Recognition F1 (all, syn, DR-91) | 1.0000 ± 0.0000 | [1.0000, 1.0000] | 20 | 5 | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 31 | | FP floor (synonym) | 0.9189 ± 0.0559 | [0.7879, 1.0000] | 20 | 200 | | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 55 | | Synonym F1 (all entities) | 1.0000 | | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 57 | | Recognition F1 (all, synonyms) | 1.0000 | | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 59 | | FP floor (synonym match) | 1.0000 | | BUG |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 64 | - FP floor = 1.0000 (>5% threshold) | BUG |
| AUDITOR_SCORECARD.md | 17 | | Gen 1: Document Parsing | **10/10** | F1 | 1.0000 | `benchmarks/reports/gen1_p | CURRENT |
| scripts/run_rival_formulas_backtest.py | 394 | print(f"    All:    prec={prec_all:.4f} rec={'1.0000' if len(tp_all)==len(actual | BUG |
| docs/MATCHING_SPECIFICATION.md | 23 | | synonym | Token + synonym map | 1.0000 | 0.8571 | | HISTORICAL |
| docs/MATCHING_SPECIFICATION.md | 27 | - **Recognition F1** (all entities + synonyms): 1.0000 | HISTORICAL |
| docs/MEASUREMENT_HISTORY.md | 10 | | 197 | 1.0000 | Entity (20-gold, synonyms) | INVALID | Synonym map inflated sco | HISTORICAL |
| docs/MEASUREMENT_HISTORY.md | 12 | | 242 | 1.0000 | Entity (all + synonyms, independent) | INVALID | FP floor = 1.0 | HISTORICAL |
| docs/DISCOVERY_VS_RECOGNITION.md | 24 | - Recognition F1 = 1.0000 (all entities + synonyms) | HISTORICAL |
| reports/bootstrap_statistics.md | 29 | | M-006 | Recognition F1 (all, syn, DR-91) | 0.9744 ± 0.0252 | [0.9189, 1.0000]  | CURRENT |
| reports/bootstrap_statistics.md | 31 | | M-008 | FP floor (synonym) | 0.9189 ± 0.0978 | [0.6667, 1.0000] | 20 | 200 | n | CURRENT |
| reports/bootstrap_statistics.md | 43 | | M-303-D2 | AI surrogate D2 mean | 1.1667 ± 0.1485 | [1.0000, 1.5000] | 6 | 500 | CURRENT |
| reports/bootstrap_statistics.md | 49 | | M-101 | Gen 1 Document Parsing F1 | 1.0000 ± 0.0000 | [1.0000, 1.0000] | 5 | 5 | CURRENT |
| reports/bootstrap_statistics.md | 52 | | M-104 | Gen 4 Mechanism Extraction F1 | 0.9091 ± 0.0677 | [0.7368, 1.0000] | 1 | CURRENT |
| reports/bootstrap_statistics.md | 53 | | M-105 | Gen 5 Discovery Layer F1 | 0.9375 ± 0.0464 | [0.8276, 1.0000] | 17 | 5 | CURRENT |
| reports/bootstrap_statistics.md | 54 | | M-201 | L5a held-out beats (count / 10) | 0.9000 ± 0.0891 | [0.7000, 1.0000] | | CURRENT |
| reports/bootstrap_statistics.md | 55 | | M-202 | L5b held-out beats (count / 10) — same data as M-201 | 0.9000 ± 0.0891 | CURRENT |
| reports/bootstrap_statistics.md | 56 | | M-203 | L5b+Synthesis held-out beats (count / 10, single seed) | 0.9000 ± 0.08 | CURRENT |
| reports/bootstrap_statistics.md | 58 | | M-205 | Composite selection rate | 1.0000 ± 0.0000 | [1.0000, 1.0000] | 43 | 5 | CURRENT |
| reports/bootstrap_statistics.md | 80 | - M-303-D1 (AI surrogate D1 mean): width = 1.0000 | CURRENT |
| reports/bootstrap_statistics.md | 90 | - M-101 (Gen 1 Document Parsing F1): point = 1.0000 | CURRENT |
| reports/bootstrap_statistics.md | 91 | - M-205 (Composite selection rate): point = 1.0000 | CURRENT |
| reports/proposal_evaluation_n30.md | 15 | | Lenient + DR-91 F1 | 40 | 0.1500 | 0.0000 | 0.3571 | 0.0000 | 1.0000 | 0.0000  | BUG |
| reports/proposal_evaluation_n30.md | 16 | | Lenient + Honest F1 | 40 | 0.1500 | 0.0000 | 0.3571 | 0.0000 | 1.0000 | 0.0000 | BUG |
| reports/calibration_documented_m2e1.json | 284 | "notes": "Degenerate: produces constant value 1.0000. No calibration possible." | BUG |
| reports/calibration_documented_m2e1.json | 428 | "notes": "Degenerate: produces constant value 1.0000. No calibration possible." | BUG |
| reports/calibration_documented_m2e1.md | 38 | | M-101 | Gen 1 Document Parsing F1 | DEGENERATE | no | M3 bootstrap (degenerate | BUG |
| reports/calibration_documented_m2e1.md | 47 | | M-205 | Composite selection rate | DEGENERATE | no | M3 bootstrap (degenerate: | BUG |
| reports/repeatability_m4.md | 35 | | M-005 | Discovery F1 (DR-91, shared, syn) | 0.8571 | 0.0000 | 0.0000 | 0.8571  | BUG |
| reports/repeatability_m4.md | 36 | | M-008 | FP floor (synonym) | 0.9595 | 0.0405 | 0.0422 | 0.8571 | 1.0000 | 0.14 | BUG |
| reports/repeatability_m4.md | 37 | | M-013 | Aggregate F1 (honest) | 0.8333 | 0.0000 | 0.0000 | 0.8333 | 0.8333 | 0 | BUG |
| reports/repeatability_m4.md | 38 | | M-201 | L5a held-out beats (/10) | 0.8300 | 0.1100 | 0.1325 | 0.7000 | 1.0000  | BUG |
| reports/repeatability_m4.md | 39 | | M-203 | L5b+Synthesis held-out beats (/10) | 0.8400 | 0.0800 | 0.0952 | 0.7000 | BUG |
| reports/repeatability_m4.md | 41 | | M-305 | Self-validation bias (E1) | 2.4917 | 0.0312 | 0.0125 | 2.4583 | 2.5417 | BUG |
| reports/repeatability_m4.md | 42 | | M-306 | Expected Calibration Error / ECE (E1) | 0.8983 | 0.0062 | 0.0069 | 0.8 | BUG |
| reports/historical_recalibration.md | 31 | | HC-007 | 243 | Recognition F1 (all entities + synonyms, DR-91 audit) | 1.0000  | BUG |
| reports/failure_envelope_m7.json | 136 | "Returns 1.0000 \u2014 every gold bridge matches some entity via synonyms", | HISTORICAL |
| reports/failure_envelope_m7.json | 145 | "F1 = 1.0000 (ceiling effect)", | HISTORICAL |
| reports/failure_envelope_m7.json | 225 | "Always returns 1.0000 \u2014 synonym matcher matches everything (degenerate)", | HISTORICAL |
| reports/failure_envelope_m7.json | 232 | "F1 = 1.0000 (degenerate, no variance)" | HISTORICAL |
| reports/failure_envelope_m7.json | 293 | "FP floor = 0.9189 \u00b1 0.0559 [0.7879, 1.0000] \u2014 CATASTROPHIC", | HISTORICAL |
| reports/failure_envelope_m7.json | 629 | "Degenerate: all 5 benchmark files have perfect F1 (1.0000)", | HISTORICAL |
| reports/failure_envelope_m7.json | 637 | "F1 = 1.0000 (degenerate, CI [1.0, 1.0])" | HISTORICAL |
| reports/failure_envelope_m7.json | 743 | "F1 = 0.9091 \u00b1 0.0677 [0.7368, 1.0000]" | HISTORICAL |
| reports/failure_envelope_m7.json | 780 | "F1 = 0.9375 \u00b1 0.0464 [0.8276, 1.0000]", | HISTORICAL |
| reports/failure_envelope_m7.json | 962 | "Selection rate = 1.0000 (degenerate, CI [1.0, 1.0])" | HISTORICAL |
| reports/external_baselines.md | 15 | is 1.0000 (per DR-91 audit). The fair bar is: production must beat | BUG |
| reports/external_baselines.md | 35 | | FP floor (lenient, DR-91) | 1.0000 | +0.1429 | ceiling | | BUG |
| reports/failure_envelope_m7.md | 54 | | M-101 | Gen 1 Document Parsing F1 | 1.0000 | True | NOT_TESTED | 0 | | HISTORICAL |
| reports/failure_envelope_m7.md | 63 | | M-205 | Composite selection rate | 1.0000 | True | NOT_TESTED | 0 | | HISTORICAL |
| reports/failure_envelope_m7.md | 95 | - **M-101** (Gen 1 Document Parsing F1): baseline = 1.0000 (no variance) | HISTORICAL |
| reports/failure_envelope_m7.md | 96 | - **M-205** (Composite selection rate): baseline = 1.0000 (no variance) | HISTORICAL |
| reports/synonym_audit.md | 21 | | tensile_strength | mechanical_strength, mechanical_properties, tensile... | Tr | BUG |
| tests/test_bacon_engine.py | 141 | discover the linear law with R² = 1.0000 (no residual). | HISTORICAL |
| tests/test_calibration_documented_m2e1.py | 151 | # M-006 was degenerate (1.0000) before cycle 270 (circular synonyms | HISTORICAL |
| tests/test_phase5_capabilities.py | 159 | """5-fold CV on PCM: all folds R²=1.0000, std=0.""" | HISTORICAL |
| evidence/observations/RIVAL_FORMULAS_BACKTEST_RESULTS.md | 11 | Best formula: None (precision -1.0000) | BUG |
| evidence/observations/BACKTEST_RESULTS.md | 16 | | **Recall** | **1.0000** | **0.0000** | | BUG |
| archive/governance-pre-consolidation/CONVERGENCE.md | 361 | direct_dependency      = 1.0       (1.0 * 1.0 = 1.0000) | BUG |
| archive/governance-pre-consolidation/PHASE_13_OPEN_ITEMS_RESOLUTION.md | 227 | | CE-001 | 1991 | {ELECTRODE_COATING, ELECTRON_COLLECTION} | 1.0000 | "already e | BUG |
| archive/governance-pre-consolidation/PHASE_13_OPEN_ITEMS_RESOLUTION.md | 235 | | CE-001 | 1991 | 0.8576 | 0.8000 | 0.8000 | 1.0000 | 0.8576 | 0.0 (tied) | No ( | BUG |
| archive/governance-pre-consolidation/PHASE_13_OPEN_ITEMS_RESOLUTION.md | 265 | first 10. Its claimed score of 1.0000 still cannot be reproduced; | BUG |
| archive/governance-pre-consolidation/COUNTEREXAMPLE_REGISTRY.md | 35 | | Score | 1.0000 | | BUG |
| benchmarks/reports/bacon_real_data_results.md | 12 | **DISCOVERED: power law, a=5.39e-8, b=4.0000, R²=1.0000** | BUG |
| benchmarks/reports/bacon_real_data_results.md | 29 | **DISCOVERED: power law, a=0.144, b=1.0, R²=1.0000** | BUG |
| audit/measurement_integrity/dr98_historical_recalibration.py | 246 | claimed_f1=1.0000, | BUG |
| audit/measurement_integrity/dr98_historical_recalibration.py | 267 | historical headline numbers (0.8571, 1.0000). It assumes precision = | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 450 | print(f"  - HC-007 (recognition F1=1.0000) SURVIVES at {hc007['rescored_lenient_ | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 595 | print(f"FP floor (DR-91 audit): 1.0000  ← THIS IS THE REAL BAR") | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 625 | print("Reference: production LENIENT F1 = 0.8571; FP floor = 1.0000") | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 638 | print(f"{'FP floor (lenient, DR-91)':<40} {1.0000:<10.4f}") | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 715 | "fp_floor_lenient": 1.0000, | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 756 | lines.append("  is 1.0000 (per DR-91 audit). The fair bar is: production must be | BUG |
| audit/measurement_integrity/dr97_external_baselines.py | 775 | lines.append(f"| FP floor (lenient, DR-91) | 1.0000 | +0.1429 | ceiling |") | BUG |
| audit/measurement_integrity/dr91_phase6_5.py | 223 | print("Entity-level FP floor: 1.0000 (from Phase VI)") | BUG |
| audit/measurement_integrity/dr91_phase6_5.py | 257 | print(f"  Entity FP:     1.0000 (any noun matches)") | BUG |
| audit/measurement_integrity/dr91_phase6_5.py | 297 | print("  Entity-level FP = 1.0000 (cannot discriminate)") | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 245 | "1.0000": "Old recognition F1 (circular, cycle 243-270)", | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 439 | "M-006": ("Recognition F1 (all, DR-91)", 1.0000), | BUG |
| programs/A_metrology/measurement_verification_sprint.py | 563 | lines.append("4. **'Recognition F1 = 1.0000'** — was degenerate (circular). Curr | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 281 | "Returns 1.0000 — every gold bridge matches some entity via synonyms", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 290 | "F1 = 1.0000 (ceiling effect)", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 322 | "Always returns 1.0000 — synonym matcher matches everything (degenerate)", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 329 | "F1 = 1.0000 (degenerate, no variance)", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 354 | "FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 516 | "Degenerate: all 5 benchmark files have perfect F1 (1.0000)", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 524 | "F1 = 1.0000 (degenerate, CI [1.0, 1.0])", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 576 | "F1 = 0.9091 ± 0.0677 [0.7368, 1.0000]", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 595 | "F1 = 0.9375 ± 0.0464 [0.8276, 1.0000]", | HISTORICAL |
| programs/A_metrology/failure_envelope_m7.py | 687 | "Selection rate = 1.0000 (degenerate, CI [1.0, 1.0])", | HISTORICAL |
| programs/A_metrology/MeasurementEngineSpecification.md | 177 | - Returns 1.0000 — every gold bridge matches some entity via synonyms | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 188 | - The 1.0000 value is an artifact of lenient matching, not a discovery | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 232 | - Returns 1.0000 — this IS the FP floor | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 283 | - Returns 1.0000 — every random candidate set matches the gold pool | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 293 | - Current value (1.0000) blocks all discovery claims. | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 611 | - Bootstrap quantified (cycle 261): 1.0000 ± 0.0000 (95% CI: 1.0000, | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 612 | 1.0000; N=5, B=500). DEGENERATE — all 5 files have perfect F1. | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 761 | 1.0000; N=12, B=500). Synthetic reconstruction from aggregate TP/FP/FN. | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 762 | - The CI is wide (0.7368 to 1.0000) because N=12 is small and the F1 | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 814 | 1.0000; N=17, B=500). Per-hit resampled (15 TPs + 2 FNs). | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 874 | 1.0000; N=10, B=100). Per-problem beats resampled. | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 875 | - The CI is wide (0.7000 to 1.0000) because N=10 is small and the | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 925 | 1.0000; N=10, B=100). Same data as M-201 — see M-201 for details. | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 977 | 1.0000; N=10, B=100). Per-problem beats resampled. | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 1082 | - Bootstrap quantified (cycle 261): 1.0000 ± 0.0000 (95% CI: 1.0000, | BUG |
| programs/A_metrology/MeasurementEngineSpecification.md | 1083 | 1.0000; N=43, B=500). DEGENERATE — all 43 composites have | BUG |
| reports/failure_envelopes/M-303-D2.md | 8 | - **95% CI:** [1.0000, 1.5000] | HISTORICAL |
| reports/failure_envelopes/M-205.md | 7 | - **Baseline value:** 1.0000 | HISTORICAL |
| reports/failure_envelopes/M-205.md | 8 | - **95% CI:** [1.0000, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-205.md | 26 | - Selection rate = 1.0000 (degenerate, CI [1.0, 1.0]) | HISTORICAL |
| reports/failure_envelopes/M-101.md | 7 | - **Baseline value:** 1.0000 | HISTORICAL |
| reports/failure_envelopes/M-101.md | 8 | - **95% CI:** [1.0000, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-101.md | 15 | - Degenerate: all 5 benchmark files have perfect F1 (1.0000) | HISTORICAL |
| reports/failure_envelopes/M-101.md | 25 | - F1 = 1.0000 (degenerate, CI [1.0, 1.0]) | HISTORICAL |
| reports/failure_envelopes/M-105.md | 8 | - **95% CI:** [0.8276, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-105.md | 27 | - F1 = 0.9375 ± 0.0464 [0.8276, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-006.md | 8 | - **95% CI:** [0.9189, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-006.md | 15 | - Always returns 1.0000 — synonym matcher matches everything (degenerate) | HISTORICAL |
| reports/failure_envelopes/M-006.md | 24 | - F1 = 1.0000 (degenerate, no variance) | HISTORICAL |
| reports/failure_envelopes/M-202.md | 8 | - **95% CI:** [0.7000, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-203.md | 8 | - **95% CI:** [0.7000, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-004.md | 15 | - Returns 1.0000 — every gold bridge matches some entity via synonyms | HISTORICAL |
| reports/failure_envelopes/M-004.md | 26 | - F1 = 1.0000 (ceiling effect) | HISTORICAL |
| reports/failure_envelopes/M-008.md | 8 | - **95% CI:** [0.6667, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-008.md | 15 | - FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC | HISTORICAL |
| reports/failure_envelopes/M-201.md | 8 | - **95% CI:** [0.7000, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-104.md | 8 | - **95% CI:** [0.7368, 1.0000] | HISTORICAL |
| reports/failure_envelopes/M-104.md | 26 | - F1 = 0.9091 ± 0.0677 [0.7368, 1.0000] | HISTORICAL |
