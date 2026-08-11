# Task 3: Repository Consistency Check

Generated: 2026-08-08T00:40:18.315238+00:00
Commit: a2eab271e943

Searching for every occurrence of key metric values.
Each classified as CURRENT, HISTORICAL, or BUG.

## 0.5714

| File | Line | Context | Classification |
|---|---|---|---|
| PRELIMINARY_MEASUREMENT_VERDICT.md | 15 | F1 dropped from 0.9189 to 0.5714. Discovery F1 (shared) drop | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 103 | - F1 = 0.5714 (was 0.9189 with circular synonyms) | CURRENT |
| AUDITOR_SCORECARD.md | 24 | | Discovery Capability (operator-blind) | **6/10** | F1 | 0. | CURRENT |
| docs/DR-90_REPRESENTATION_DISCOVERY.md | 40 | - Discovery Engine (F1=0.9189 HISTORICAL — current F1=0.5714 | HISTORICAL |
| docs/MEASUREMENT_SPECIFICATION.md | 33 | - **Discovery F1 = 0.9189** (HISTORICAL — was circular, curr | HISTORICAL |
| docs/INVENTION_CONSTITUTION.md | 27 | | Discovery | Find relationships not explicitly stated | ✅ D | HISTORICAL |
| docs/INVENTION_CONSTITUTION.md | 59 | it continuously. The current honest discovery F1=0.9189 was  | HISTORICAL |
| reports/discovery_score_recalibration.md | 15 | - F1 = 0.5714 | CURRENT |
| reports/discovery_score_recalibration.md | 22 | - F1 = 0.5714 | CURRENT |
| reports/discovery_score_recalibration.md | 23 | - Score = 6/10 (round(10 × 0.5714) = 6) | CURRENT |
| reports/discovery_score_recalibration.md | 30 | The score dropped from 9/10 (F1=0.9189) to 6/10 (F1=0.5714)  | CURRENT |
| reports/discovery_score_recalibration.md | 51 | only 8/20 gold bridges match via token overlap (F1=0.5714).  | CURRENT |
| reports/repository_truth_check.md | 10 | - AUDITOR_SCORECARD.md: regenerated from source via `scripts | CURRENT |
| reports/repository_truth_check.md | 11 | - discovery_capability_score.json: regenerated via `python3  | CURRENT |
| reports/repository_truth_check.md | 23 | | AUDITOR_SCORECARD.md | CURRENT | Discovery Capability row  | CURRENT |
| reports/repository_truth_check.md | 24 | | discovery_capability_score.json | CURRENT | F1=0.5714, TP= | CURRENT |
| reports/repository_truth_check.md | 28 | | docs/INVENTION_CONSTITUTION.md | HISTORICAL | 0.9189 label | CURRENT |
| reports/repository_truth_check.md | 29 | | docs/DR-90_REPRESENTATION_DISCOVERY.md | HISTORICAL | 0.91 | CURRENT |
| reports/repository_truth_check.md | 30 | | docs/MEASUREMENT_SPECIFICATION.md | HISTORICAL | 0.9189 la | CURRENT |
| reports/repository_truth_check.md | 50 | - The discovery_capability_score.json was regenerated from s | CURRENT |
| reports/repository_truth_check.md | 57 | - Current discovery F1 = 0.5714 (was 0.9189, circular) | CURRENT |
| reports/repository_truth_check.md | 66 | 1. discovery_capability_score.json: regenerated (F1 0.9189 → | CURRENT |
| reports/historical_metric_inventory.md | 34 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 15 | F1 dropped from  | CURRENT |
| reports/historical_metric_inventory.md | 41 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 103 | - F1 = 0.5714 ( | CURRENT |
| reports/historical_metric_inventory.md | 88 | | reports/discovery_score_recalibration.md | 30 | The score  | CURRENT |
| reports/historical_metric_inventory.md | 100 | | reports/repository_truth_check.md | 68 | 1. **'Discovery F | CURRENT |
| reports/historical_metric_inventory.md | 101 | | reports/repository_truth_check.md | 87 | 1. Regenerated di | CURRENT |
| reports/historical_metric_inventory.md | 343 | | reports/historical_metric_inventory.md | 176 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 432 | | reports/historical_metric_inventory.md | 270 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 447 | | reports/failure_envelope_m7.json | 196 | "F1 drops from 0. | CURRENT |
| reports/historical_metric_inventory.md | 513 | | programs/A_metrology/failure_envelope_m7.py | 311 | "F1 dr | CURRENT |
| reports/historical_metric_inventory.md | 523 | | reports/failure_envelopes/M-005.md | 27 | - F1 drops from  | CURRENT |
| reports/failure_envelope_m7.json | 196 | "F1 drops from 0.8571 to 0.5714 when snippets truncated (M6) | CURRENT |
| reports/failure_envelope_m7.json | 494 | "F1 drops from 0.8333 to 0.5714 when truncated" | CURRENT |
| reports/claim_traceability.md | 6 | ## Discovery Capability F1 = 0.5714 | CURRENT |
| reports/claim_traceability.md | 11 | benchmarks/reports/discovery_capability_score.json (F1=0.571 | CURRENT |
| reports/claim_traceability.md | 13 | AUDITOR_SCORECARD.md (6/10, F1=0.5714) | CURRENT |
| reports/claim_traceability.md | 80 | Now: BRIDGE_SYNONYMS = {} (cycle 270), score regenerated to  | CURRENT |
| reports/honest_scoreboard.md | 62 | - F1 = 0.5714 | CURRENT |
| reports/public_claim_inventory.md | 387 | | score_rating | reports/discovery_score_recalibration.md |  | CURRENT |
| reports/public_claim_inventory.md | 388 | | score_rating | reports/discovery_score_recalibration.md |  | CURRENT |
| reports/public_claim_inventory.md | 487 | | score_rating | programs/A_metrology/final_repository_verif | CURRENT |
| reports/public_claim_inventory.md | 492 | | score_rating | programs/A_metrology/final_repository_verif | CURRENT |
| reports/public_claim_inventory.md | 586 | | f1_value | PRELIMINARY_MEASUREMENT_VERDICT.md | 103 | - F1 | CURRENT |
| reports/public_claim_inventory.md | 598 | | f1_value | docs/DR-90_REPRESENTATION_DISCOVERY.md | 40 | - | CURRENT |
| reports/public_claim_inventory.md | 610 | | f1_value | reports/discovery_score_recalibration.md | 15 | | CURRENT |
| reports/public_claim_inventory.md | 611 | | f1_value | reports/discovery_score_recalibration.md | 22 | | CURRENT |
| reports/public_claim_inventory.md | 612 | | f1_value | reports/discovery_score_recalibration.md | 30 | | CURRENT |
| reports/public_claim_inventory.md | 615 | | f1_value | reports/discovery_score_recalibration.md | 51 | | CURRENT |
| reports/public_claim_inventory.md | 619 | | f1_value | reports/repository_truth_check.md | 24 | | disc | CURRENT |
| reports/public_claim_inventory.md | 625 | | f1_value | reports/repository_truth_check.md | 57 | - Curr | CURRENT |
| reports/public_claim_inventory.md | 634 | | f1_value | reports/historical_metric_inventory.md | 41 | | | CURRENT |
| reports/public_claim_inventory.md | 760 | | f1_value | reports/honest_scoreboard.md | 62 | - F1 = 0.57 | CURRENT |
| reports/public_claim_inventory.md | 817 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| reports/public_claim_inventory.md | 819 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| reports/public_claim_inventory.md | 826 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| benchmarks/reports/discovery_capability_score.json | 10 | "f1": 0.5714, | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 135 | lines.append("only 8/20 gold bridges match via token overlap | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 533 | lines.append("   (actual: 0.5714 after synonym removal)") | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 548 | lines.append("- The discovery_capability_score.json was rege | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 559 | lines.append("1. **'Discovery F1 = 0.9189'** — this was circ | CURRENT |
| programs/A_metrology/final_repository_verification.py | 130 | "claim": "Discovery Capability F1 = 0.5714", | CHECK |
| programs/A_metrology/final_repository_verification.py | 134 | "benchmarks/reports/discovery_capability_score.json (F1=0.57 | CHECK |
| programs/A_metrology/final_repository_verification.py | 136 | "AUDITOR_SCORECARD.md (6/10, F1=0.5714)", | CHECK |
| programs/A_metrology/final_repository_verification.py | 198 | "Now: BRIDGE_SYNONYMS = {} (cycle 270), score regenerated to | CHECK |
| programs/A_metrology/final_repository_verification.py | 251 | values_to_check = ["0.5714", "0.7879", "0.9189", "0.8571", " | CHECK |
| programs/A_metrology/final_repository_verification.py | 494 | "  - Discovery capability F1 = 0.5714 (6/10) — NOT 0.9189 (9 | CHECK |
| programs/A_metrology/final_repository_verification.py | 506 | "No stale 0.9189 in AUDITOR_SCORECARD (regenerated to 0.5714 | CHECK |
| programs/A_metrology/failure_envelope_m7.py | 311 | "F1 drops from 0.8571 to 0.5714 when snippets truncated (M6) | CURRENT |
| programs/A_metrology/failure_envelope_m7.py | 453 | "F1 drops from 0.8333 to 0.5714 when truncated", | CURRENT |
| reports/failure_envelopes/M-005.md | 27 | - F1 drops from 0.8571 to 0.5714 when snippets truncated (M6 | CURRENT |
| reports/failure_envelopes/M-013.md | 25 | - F1 drops from 0.8333 to 0.5714 when truncated | CURRENT |

## 0.7879

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 5775 | | token | 0.9744 | 0.7879 | | HISTORICAL |
| FAILURES.md | 7046 | | M-008 FP floor | 0.9189 ± 0.0559 | [0.7879, 1.0000] | Conf | HISTORICAL |
| FAILURES.md | 7100 | - The FP floor=1.0000 is now FP floor=0.9189 ± 0.0559 (95% C | HISTORICAL |
| FAILURES.md | 8348 | | M-005 Discovery F1 | 0.8571 | 0.7879 | ↓ (honest drop) | | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 16 | 0.8571 to 0.7879. These are the honest, non-circular values. | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 36 | | Discovery F1 (shared, syn, DR-91) | 0.7879 ± 0.0809 | [0.6 | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 42 | | Aggregate F1 (DR-91) | 0.7879 ± 0.0809 | [0.6207, 0.9189]  | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 70 | | Discovery F1 (shared, syn, DR-91) | 0.8571 | 0.7879 | | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 75 | | Aggregate F1 (DR-91) | 0.8571 | 0.7879 | | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 112 | The aggregate F1 of 0.7879 above is the system-level score.  | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 116 | - Aggregate F1 = 0.7879: "of the 20 gold bridges, ~15/20 are | CURRENT |
| docs/MATCHING_SPECIFICATION.md | 21 | | exact_token | Substring OR ≥1 shared 4+ char token | 0.974 | HISTORICAL |
| reports/bootstrap_statistics.md | 28 | | M-005 | Discovery F1 (shared, syn, DR-91) | 0.7879 ± 0.080 | CURRENT |
| reports/bootstrap_statistics.md | 35 | | M-012 | Aggregate F1 (DR-91) | 0.7879 ± 0.0809 | [0.6207,  | CURRENT |
| reports/bootstrap_statistics.json | 82 | "point_estimate": 0.7879, | CURRENT |
| reports/bootstrap_statistics.json | 201 | "point_estimate": 0.7879, | CURRENT |
| reports/final_verdict_eligibility.json | 11 | "production_f1_lenient": 0.7879, | CURRENT |
| reports/final_verdict_eligibility.json | 17 | "production_f1": 0.7879, | CURRENT |
| reports/final_verdict_eligibility.json | 24 | "production_f1": 0.7879, | CURRENT |
| reports/final_verdict_eligibility.json | 31 | "production_f1": 0.7879, | CURRENT |
| reports/repository_truth_check.md | 26 | | dr97_external_baselines.py | CURRENT | production_f1 defau | CURRENT |
| reports/repository_truth_check.md | 39 | 3. ~~dr97_external_baselines.py~~ — FIXED (production_f1=0.7 | CURRENT |
| reports/repository_truth_check.md | 59 | - Current discovery F1 (shared, DR-91) = 0.7879 (was 0.8571, | CURRENT |
| reports/repository_truth_check.md | 69 | 4. dr97_external_baselines.py: production_f1 updated (0.8571 | CURRENT |
| reports/repository_truth_check.md | 70 | 5. dr97 print statements: all 0.8571 references replaced wit | CURRENT |
| reports/historical_metric_inventory.md | 31 | | FAILURES.md | 7046 | | M-008 FP floor | 0.9189 ± 0.0559 |  | CURRENT |
| reports/historical_metric_inventory.md | 32 | | FAILURES.md | 7100 | - The FP floor=1.0000 is now FP floor | CURRENT |
| reports/historical_metric_inventory.md | 35 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 36 | | Discovery F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 38 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 42 | | Aggregate F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 51 | | reports/bootstrap_statistics.md | 28 | | M-005 | Discovery | CURRENT |
| reports/historical_metric_inventory.md | 54 | | reports/bootstrap_statistics.md | 35 | | M-012 | Aggregate | CURRENT |
| reports/historical_metric_inventory.md | 112 | | reports/historical_metric_inventory.md | 31 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 128 | | reports/historical_metric_inventory.md | 47 | | reports/bo | CURRENT |
| reports/historical_metric_inventory.md | 197 | | reports/historical_metric_inventory.md | 132 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 198 | | reports/historical_metric_inventory.md | 303 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 206 | | reports/historical_metric_inventory.md | 443 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 207 | | reports/measurement_provenance_audit.md | 85 | - **Value:* | CURRENT |
| reports/historical_metric_inventory.md | 210 | | reports/measurement_provenance_audit.md | 197 | - **Value: | CURRENT |
| reports/historical_metric_inventory.md | 215 | | reports/failure_envelope_m7.json | 293 | "FP floor = 0.918 | CURRENT |
| reports/historical_metric_inventory.md | 219 | | reports/honest_scoreboard.md | 15 | | M-005 | 0.7879 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 222 | | reports/honest_scoreboard.md | 22 | | M-012 | 0.7879 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 223 | | reports/honest_scoreboard.md | 54 | | M-005 Discovery F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 256 | | programs/A_metrology/failure_envelope_m7.py | 354 | "FP fl | CURRENT |
| reports/historical_metric_inventory.md | 266 | | reports/failure_envelopes/M-008.md | 15 | - FP floor = 0.9 | CURRENT |
| reports/historical_metric_inventory.md | 289 | | FAILURES.md | 8348 | | M-005 Discovery F1 | 0.8571 | 0.787 | CURRENT |
| reports/historical_metric_inventory.md | 291 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 16 | 0.8571 to 0.7879 | CURRENT |
| reports/historical_metric_inventory.md | 292 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 70 | | Discovery F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 293 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 75 | | Aggregate F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 306 | | reports/repository_truth_check.md | 94 | - Update dr97 pro | CURRENT |
| reports/historical_metric_inventory.md | 324 | | reports/historical_metric_inventory.md | 155 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 451 | | reports/honest_scoreboard.md | 54 | | M-005 Discovery F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 501 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 556 | | FAILURES.md | 7046 | | M-008 FP floor | 0.9189 ± 0.0559 |  | CURRENT |
| reports/historical_metric_inventory.md | 557 | | FAILURES.md | 7100 | - The FP floor=1.0000 is now FP floor | CURRENT |
| reports/historical_metric_inventory.md | 599 | | reports/historical_metric_inventory.md | 31 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 607 | | reports/historical_metric_inventory.md | 132 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 637 | | reports/historical_metric_inventory.md | 303 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 767 | | reports/historical_metric_inventory.md | 443 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 793 | | reports/failure_envelope_m7.json | 293 | "FP floor = 0.918 | CURRENT |
| reports/historical_metric_inventory.md | 834 | | audit/measurement_integrity/dr97_external_baselines.py | 6 | CURRENT |
| reports/historical_metric_inventory.md | 849 | | programs/A_metrology/failure_envelope_m7.py | 354 | "FP fl | CURRENT |
| reports/historical_metric_inventory.md | 889 | | reports/failure_envelopes/M-008.md | 15 | - FP floor = 0.9 | CURRENT |
| reports/measurement_provenance_audit.md | 85 | - **Value:** 0.7879 ± 0.0809 (95% CI: 0.6207, 0.9189) | CURRENT |
| reports/measurement_provenance_audit.md | 197 | - **Value:** 0.7879 ± 0.0809 (95% CI: 0.6207, 0.9189) | CURRENT |
| reports/historical_recalibration.md | 29 | | HC-005 | 201 | Discovery F1 (the headline number, reported | CURRENT |
| reports/historical_recalibration.md | 30 | | HC-006 | 243 | Proposal-only F1 (shared entities + synonym | CURRENT |
| reports/sensitivity_m6.md | 39 | | M-005 | INPUT | drop_1_sentence | 0.7879 | 0.7879 | +0.000 | CURRENT |
| reports/sensitivity_m6.md | 40 | | M-005 | INPUT | shuffle_sentences | 0.7879 | 0.7879 | +0.0 | CURRENT |
| reports/sensitivity_m6.md | 41 | | M-005 | INPUT | truncate_75pct | 0.7879 | 0.5185 | -0.2694 | CURRENT |
| reports/sensitivity_m6.md | 42 | | M-005 | GOLD | drop_1_gold | 0.7879 | 0.7742 | -0.0137 | - | CURRENT |
| reports/sensitivity_m6.md | 43 | | M-005 | GOLD | drop_2_gold | 0.7879 | 0.7586 | -0.0293 | - | CURRENT |
| reports/sensitivity_m6.md | 44 | | M-005 | GOLD | rename_gold | 0.7879 | 0.7879 | +0.0000 | + | CURRENT |
| reports/sensitivity_m6.md | 45 | | M-005 | SYNONYM | remove_1_synonym | 0.7879 | 0.7879 | +0. | CURRENT |
| reports/sensitivity_m6.md | 46 | | M-005 | SYNONYM | remove_25pct_synonyms | 0.7879 | 0.7879  | CURRENT |
| reports/sensitivity_m6.md | 47 | | M-005 | SYNONYM | remove_50pct_synonyms | 0.7879 | 0.7879  | CURRENT |
| reports/sensitivity_m6.md | 91 | - **M-005 / INPUT/truncate_75pct**: Δ=-0.2694 (-0.3419). Bas | CURRENT |
| reports/failure_envelope_m7.json | 163 | "baseline_value": 0.7879, | CURRENT |
| reports/failure_envelope_m7.json | 178 | "baseline_value": 0.7879, | CURRENT |
| reports/failure_envelope_m7.json | 293 | "FP floor = 0.9189 \u00b1 0.0559 [0.7879, 1.0000] \u2014 CAT | CURRENT |
| reports/failure_envelope_m7.json | 428 | "baseline_value": 0.7879, | CURRENT |
| reports/claim_traceability.md | 20 | ## Discovery F1 (shared, DR-91) = 0.7879 | CURRENT |
| reports/claim_traceability.md | 25 | reports/bootstrap_statistics.json (M-005: 0.7879 ± 0.0809) | CURRENT |
| reports/claim_traceability.md | 98 | Now: production_f1=0.7879 (fixed), PRELIMINARY has historica | CURRENT |
| reports/honest_scoreboard.md | 15 | | M-005 | 0.7879 ± 0.0809 | [0.6207, 0.9189] | 20 | 500 | B  | CURRENT |
| reports/honest_scoreboard.md | 22 | | M-012 | 0.7879 ± 0.0809 | [0.6207, 0.9189] | 20 | 500 | B  | CURRENT |
| reports/honest_scoreboard.md | 54 | | M-005 Discovery F1 (shared, DR-91) | 0.7879 | ± 0.0809 | [ | CURRENT |
| reports/external_baselines.json | 6 | "production_f1_lenient": 0.7879, | CURRENT |
| reports/external_baselines.json | 631 | "production_f1": 0.7879, | CURRENT |
| reports/external_baselines.json | 638 | "production_f1": 0.7879, | CURRENT |
| reports/external_baselines.json | 645 | "production_f1": 0.7879, | CURRENT |
| reports/external_baselines.md | 14 | Production under lenient mode scores F1=0.7879, but the FP f | CURRENT |
| reports/external_baselines.md | 34 | | Production (lenient) | 0.7879 | — | reference | | CURRENT |
| reports/historical_recalibration.json | 117 | "rescored_lenient_f1_dr91": 0.7879, | CURRENT |
| reports/historical_recalibration.json | 138 | "rescored_lenient_f1_dr91": 0.7879, | CURRENT |
| reports/failure_envelope_m7.md | 42 | | M-005 | Discovery F1 (shared, syn, DR-91) | 0.7879 | False | CURRENT |
| reports/failure_envelope_m7.md | 49 | | M-012 | Aggregate F1 (DR-91) | 0.7879 | False | NOT_TESTED | CURRENT |
| reports/sensitivity_m6.json | 12 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 13 | "perturbed_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 23 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 24 | "perturbed_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 34 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 45 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 56 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 67 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 68 | "perturbed_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 78 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 79 | "perturbed_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 89 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 90 | "perturbed_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 100 | "baseline_value": 0.7879, | CURRENT |
| reports/sensitivity_m6.json | 101 | "perturbed_value": 0.7879, | CURRENT |
| reports/public_claim_inventory.md | 587 | | f1_value | PRELIMINARY_MEASUREMENT_VERDICT.md | 116 | - Ag | CURRENT |
| reports/public_claim_inventory.md | 763 | | f1_value | reports/external_baselines.md | 14 | Production | CURRENT |
| reports/public_claim_inventory.md | 792 | | f1_value | audit/measurement_integrity/dr97_external_basel | CURRENT |
| reports/public_claim_inventory.md | 793 | | f1_value | audit/measurement_integrity/dr97_external_basel | CURRENT |
| reports/public_claim_inventory.md | 794 | | f1_value | audit/measurement_integrity/dr97_external_basel | CURRENT |
| reports/public_claim_inventory.md | 795 | | f1_value | audit/measurement_integrity/dr97_external_basel | CURRENT |
| reports/public_claim_inventory.md | 796 | | f1_value | audit/measurement_integrity/dr97_external_basel | CURRENT |
| reports/public_claim_inventory.md | 814 | | f1_value | programs/A_metrology/measurement_verification_s | CURRENT |
| reports/public_claim_inventory.md | 825 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| tests/test_bootstrap_statistics.py | 361 | Now 0.7879 with non-circular (empty) synonym map.""" | TEST |
| tests/test_dr98_historical_recalibration.py | 153 | # After cycle 270 (circular synonyms removed), DR-91 F1 is 0 | TEST |
| audit/measurement_integrity/dr97_external_baselines.py | 546 | def compare_to_production(baseline_results: Dict, production | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 552 | (default 0.7879 = post-cycle-270 non-circular shared/token F | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 594 | print(f"Production F1 (PRELIMINARY verdict, shared/synonym): | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 625 | print("Reference: production LENIENT F1 = 0.7879; FP floor = | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 637 | print(f"{'Production (lenient, DR-91)':<40} {0.7879:<10.4f}" | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 648 | compare_to_production(bm25_len, production_f1=0.7879), | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 649 | compare_to_production(rnd_len, production_f1=0.7879), | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 650 | compare_to_production(freq_len, production_f1=0.7879), | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 665 | print(f"CRITICAL: production (0.7879) does NOT meaningfully  | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 669 | print(f"random candidates. Production F1=0.7879 is NOT a dis | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 714 | "production_f1_lenient": 0.7879, | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 755 | lines.append("  Production under lenient mode scores F1=0.78 | CURRENT |
| audit/measurement_integrity/dr97_external_baselines.py | 774 | lines.append(f"| Production (lenient) | 0.7879 | — | referen | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 521 | lines.append("2. dr97_external_baselines.py: update producti | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 531 | lines.append("   circular synonyms; current honest value is  | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 535 | lines.append("   (actual: 0.7879)") | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 562 | lines.append("   Current honest F1 = 0.7879.") | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 585 | lines.append("- Update dr97 production_f1 default from 0.857 | CURRENT |
| programs/A_metrology/final_repository_verification.py | 143 | "claim": "Discovery F1 (shared, DR-91) = 0.7879", | CHECK |
| programs/A_metrology/final_repository_verification.py | 147 | "reports/bootstrap_statistics.json (M-005: 0.7879 ± 0.0809)" | CHECK |
| programs/A_metrology/final_repository_verification.py | 215 | "Now: production_f1=0.7879 (fixed), PRELIMINARY has historic | CHECK |
| programs/A_metrology/final_repository_verification.py | 251 | values_to_check = ["0.5714", "0.7879", "0.9189", "0.8571", " | CHECK |
| programs/A_metrology/final_repository_verification.py | 290 | cls = "CURRENT"  # already fixed to 0.7879 | CHECK |
| programs/A_metrology/failure_envelope_m7.py | 354 | "FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC" | CURRENT |
| reports/failure_envelopes/M-005.md | 7 | - **Baseline value:** 0.7879 | CURRENT |
| reports/failure_envelopes/M-005.md | 34 | | INPUT/truncate_75pct | 0.7879 | 0.5185 | -0.2694 | -0.3419 | CURRENT |
| reports/failure_envelopes/M-012.md | 7 | - **Baseline value:** 0.7879 | CURRENT |
| reports/failure_envelopes/M-008.md | 15 | - FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC | CURRENT |

## 0.9189

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 3081 | inflated. The honest F1 is 0.9189 (recall=0.85) after de-cir | HISTORICAL |
| FAILURES.md | 3087 | Honest result: F1=0.9189, recall=0.85, 17 TP, 3 FN. | HISTORICAL |
| FAILURES.md | 5712 | The F1=0.9189 (reported since cycle 201) may be overstated: | HISTORICAL |
| FAILURES.md | 5729 | However, the discovery F1=0.9189 (used in scorecards and mat | HISTORICAL |
| FAILURES.md | 5758 | The F1=0.9189 that has been reported since cycle 201 may be  | HISTORICAL |
| FAILURES.md | 5821 | - The discovery F1=0.9189 reported since cycle 201 is NOT re | HISTORICAL |
| FAILURES.md | 5831 | - Discovery scorecard (9.0/10): AFFECTED. Rests on F1=0.9189 | HISTORICAL |
| FAILURES.md | 6001 | | Discovery F1=0.9189 | YES — INVALID | Measured entity reco | HISTORICAL |
| FAILURES.md | 6702 | - HC-005 (cycle 201 F1=0.9189) ERODED — already documented i | HISTORICAL |
| FAILURES.md | 7046 | | M-008 FP floor | 0.9189 ± 0.0559 | [0.7879, 1.0000] | Conf | HISTORICAL |
| FAILURES.md | 7100 | - The FP floor=1.0000 is now FP floor=0.9189 ± 0.0559 (95% C | HISTORICAL |
| FAILURES.md | 8350 | | M-008 FP floor | 0.9189 | 0.9189 | unchanged | | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 15 | F1 dropped from 0.9189 to 0.5714. Discovery F1 (shared) drop | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 36 | | Discovery F1 (shared, syn, DR-91) | 0.7879 ± 0.0809 | [0.6 | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 37 | | Recognition F1 (all, syn, DR-91) | 0.9744 ± 0.0252 | [0.91 | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 39 | | FP floor (token, syn empty) | 0.9189 ± 0.0978 | [0.6667, 1 | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 42 | | Aggregate F1 (DR-91) | 0.7879 ± 0.0809 | [0.6207, 0.9189]  | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 72 | | FP floor (token, syn empty) | 0.9189 | 0.9189 (unchanged)  | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 80 | - FP floor = 0.9189 (CI touches 1.0) — still above 5% thresh | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 103 | - F1 = 0.5714 (was 0.9189 with circular synonyms) | CURRENT |
| docs/MEASUREMENT_REASSESSMENT.md | 21 | | Discovery F1=0.9189 | Entity recognition | YES — INVALID | | HISTORICAL |
| docs/MEASUREMENT_REASSESSMENT.md | 22 | | Discovery scorecard 9.0/10 | F1=0.9189 | YES — UNVERIFIED  | HISTORICAL |
| docs/MEASUREMENT_HISTORY.md | 11 | | 201 | 0.9189 | Entity (20-gold, non-circular) | INVALID |  | HISTORICAL |
| docs/DR-90_REPRESENTATION_DISCOVERY.md | 40 | - Discovery Engine (F1=0.9189 HISTORICAL — current F1=0.5714 | HISTORICAL |
| docs/MEASUREMENT_SPECIFICATION.md | 33 | - **Discovery F1 = 0.9189** (HISTORICAL — was circular, curr | HISTORICAL |
| docs/INVENTION_CONSTITUTION.md | 27 | | Discovery | Find relationships not explicitly stated | ✅ D | HISTORICAL |
| docs/INVENTION_CONSTITUTION.md | 59 | it continuously. The current honest discovery F1=0.9189 was  | HISTORICAL |
| docs/DISCOVERY_OBJECT_AUDIT.md | 123 | 1. **Discovery F1=0.9189** becomes meaningless — it measured | HISTORICAL |
| docs/DISCOVERY_OBJECT_AUDIT.md | 171 | Previous claim: "Discovery F1 = 0.9189" | HISTORICAL |
| reports/bootstrap_statistics.md | 28 | | M-005 | Discovery F1 (shared, syn, DR-91) | 0.7879 ± 0.080 | CURRENT |
| reports/bootstrap_statistics.md | 29 | | M-006 | Recognition F1 (all, syn, DR-91) | 0.9744 ± 0.0252 | CURRENT |
| reports/bootstrap_statistics.md | 31 | | M-008 | FP floor (synonym) | 0.9189 ± 0.0978 | [0.6667, 1. | CURRENT |
| reports/bootstrap_statistics.md | 35 | | M-012 | Aggregate F1 (DR-91) | 0.7879 ± 0.0809 | [0.6207,  | CURRENT |
| reports/measurement_constitution_m8.json | 388 | "evidence": "M3 bootstrap exists: True (CI=0.6207, 0.9189)", | CURRENT |
| reports/measurement_constitution_m8.json | 452 | "evidence": "M3 bootstrap exists: True (CI=0.9189, 1.0)", | CURRENT |
| reports/measurement_constitution_m8.json | 836 | "evidence": "M3 bootstrap exists: True (CI=0.6207, 0.9189)", | CURRENT |
| reports/calibration_documented_m2e1.json | 44 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 76 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 92 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 108 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 124 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 139 | "fp_floor": 0.9189, | CURRENT |
| reports/calibration_documented_m2e1.json | 140 | "notes": "FP floor = 0.9189. CATASTROPHIC (>5% threshold). T | CURRENT |
| reports/calibration_documented_m2e1.json | 172 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 204 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 220 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 236 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 252 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/calibration_documented_m2e1.json | 268 | "notes": "FP floor = 0.9189 (>5% threshold). DR-91 audit exi | CURRENT |
| reports/bootstrap_statistics.json | 87 | "ci_95_upper": 0.9189, | CURRENT |
| reports/bootstrap_statistics.json | 103 | "ci_95_lower": 0.9189, | CURRENT |
| reports/bootstrap_statistics.json | 133 | "point_estimate": 0.9189, | CURRENT |
| reports/bootstrap_statistics.json | 206 | "ci_95_upper": 0.9189, | CURRENT |
| reports/calibration_documented_m2e1.md | 23 | | M-002 | Token F1 (all entities) | PARTIALLY_CALIBRATED | Y | CURRENT |
| reports/calibration_documented_m2e1.md | 25 | | M-004 | Synonym F1 (all entities) | PARTIALLY_CALIBRATED | | CURRENT |
| reports/calibration_documented_m2e1.md | 26 | | M-005 | Discovery F1 (shared, syn, DR-91) | PARTIALLY_CALI | CURRENT |
| reports/calibration_documented_m2e1.md | 27 | | M-006 | Recognition F1 (all, syn, DR-91) | PARTIALLY_CALIB | CURRENT |
| reports/calibration_documented_m2e1.md | 28 | | M-007 | Proposal-locus inflation | PARTIALLY_CALIBRATED |  | CURRENT |
| reports/calibration_documented_m2e1.md | 29 | | M-008 | FP floor (synonym) | PARTIALLY_CALIBRATED | YES |  | CURRENT |
| reports/calibration_documented_m2e1.md | 31 | | M-010 | Per-proposal F1 (honest, lenient, A | PARTIALLY_CA | CURRENT |
| reports/calibration_documented_m2e1.md | 33 | | M-012 | Aggregate F1 (DR-91) | PARTIALLY_CALIBRATED | YES  | CURRENT |
| reports/calibration_documented_m2e1.md | 34 | | M-013 | Aggregate F1 (honest) | PARTIALLY_CALIBRATED | YES | CURRENT |
| reports/calibration_documented_m2e1.md | 35 | | M-014 | BM25 recall@1 (lenient) | PARTIALLY_CALIBRATED | Y | CURRENT |
| reports/calibration_documented_m2e1.md | 36 | | M-015 | Random baseline F1 (lenient) | PARTIALLY_CALIBRATE | CURRENT |
| reports/calibration_documented_m2e1.md | 37 | | M-016 | Frequency baseline F1 (lenient) | PARTIALLY_CALIBR | CURRENT |
| reports/discovery_score_recalibration.md | 16 | - Score = 9/10 (round(10 × 0.9189) = 9) | CURRENT |
| reports/discovery_score_recalibration.md | 30 | The score dropped from 9/10 (F1=0.9189) to 6/10 (F1=0.5714)  | CURRENT |
| reports/discovery_score_recalibration.md | 38 | the code said BRIDGE_SYNONYMS = {} but the scorecard said F1 | CURRENT |
| reports/discovery_score_recalibration.md | 50 | bridges matched (F1=0.9189). With the empty synonym map (non | CURRENT |
| reports/repository_truth_check.md | 27 | | dr98_historical_recalibration.py | CURRENT | Historical cl | CURRENT |
| reports/repository_truth_check.md | 28 | | docs/INVENTION_CONSTITUTION.md | HISTORICAL | 0.9189 label | CURRENT |
| reports/repository_truth_check.md | 29 | | docs/DR-90_REPRESENTATION_DISCOVERY.md | HISTORICAL | 0.91 | CURRENT |
| reports/repository_truth_check.md | 30 | | docs/MEASUREMENT_SPECIFICATION.md | HISTORICAL | 0.9189 la | CURRENT |
| reports/repository_truth_check.md | 38 | 2. ~~docs/INVENTION_CONSTITUTION.md~~ — FIXED (0.9189 labele | CURRENT |
| reports/repository_truth_check.md | 40 | 4. ~~docs/DR-90_REPRESENTATION_DISCOVERY.md~~ — FIXED (0.918 | CURRENT |
| reports/repository_truth_check.md | 41 | 5. ~~docs/MEASUREMENT_SPECIFICATION.md~~ — FIXED (0.9189 lab | CURRENT |
| reports/repository_truth_check.md | 57 | - Current discovery F1 = 0.5714 (was 0.9189, circular) | CURRENT |
| reports/repository_truth_check.md | 66 | 1. discovery_capability_score.json: regenerated (F1 0.9189 → | CURRENT |
| reports/repository_truth_check.md | 71 | 6. docs/ files: 4 occurrences of 0.9189 labeled as HISTORICA | CURRENT |
| reports/historical_metric_inventory.md | 17 | ## 0.9189 | CURRENT |
| reports/historical_metric_inventory.md | 22 | | FAILURES.md | 3081 | inflated. The honest F1 is 0.9189 (re | CURRENT |
| reports/historical_metric_inventory.md | 23 | | FAILURES.md | 3087 | Honest result: F1=0.9189, recall=0.85 | CURRENT |
| reports/historical_metric_inventory.md | 24 | | FAILURES.md | 5712 | The F1=0.9189 (reported since cycle 2 | CURRENT |
| reports/historical_metric_inventory.md | 25 | | FAILURES.md | 5729 | However, the discovery F1=0.9189 (use | CURRENT |
| reports/historical_metric_inventory.md | 26 | | FAILURES.md | 5758 | The F1=0.9189 that has been reported  | CURRENT |
| reports/historical_metric_inventory.md | 27 | | FAILURES.md | 5821 | - The discovery F1=0.9189 reported si | CURRENT |
| reports/historical_metric_inventory.md | 28 | | FAILURES.md | 5831 | - Discovery scorecard (9.0/10): AFFEC | CURRENT |
| reports/historical_metric_inventory.md | 29 | | FAILURES.md | 6001 | | Discovery F1=0.9189 | YES — INVALID | CURRENT |
| reports/historical_metric_inventory.md | 30 | | FAILURES.md | 6702 | - HC-005 (cycle 201 F1=0.9189) ERODED | CURRENT |
| reports/historical_metric_inventory.md | 31 | | FAILURES.md | 7046 | | M-008 FP floor | 0.9189 ± 0.0559 |  | CURRENT |
| reports/historical_metric_inventory.md | 32 | | FAILURES.md | 7100 | - The FP floor=1.0000 is now FP floor | CURRENT |
| reports/historical_metric_inventory.md | 33 | | FAILURES.md | 8350 | | M-008 FP floor | 0.9189 | 0.9189 |  | CURRENT |
| reports/historical_metric_inventory.md | 34 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 15 | F1 dropped from  | CURRENT |
| reports/historical_metric_inventory.md | 35 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 36 | | Discovery F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 36 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 37 | | Recognition F1 | CURRENT |
| reports/historical_metric_inventory.md | 37 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 39 | | FP floor (toke | CURRENT |
| reports/historical_metric_inventory.md | 38 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 42 | | Aggregate F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 39 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 72 | | FP floor (toke | CURRENT |
| reports/historical_metric_inventory.md | 40 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 80 | - FP floor = 0.9 | CURRENT |
| reports/historical_metric_inventory.md | 41 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 103 | - F1 = 0.5714 ( | CURRENT |
| reports/historical_metric_inventory.md | 42 | | docs/MEASUREMENT_REASSESSMENT.md | 21 | | Discovery F1=0.9 | CURRENT |
| reports/historical_metric_inventory.md | 43 | | docs/MEASUREMENT_REASSESSMENT.md | 22 | | Discovery scorec | CURRENT |
| reports/historical_metric_inventory.md | 44 | | docs/MEASUREMENT_HISTORY.md | 11 | | 201 | 0.9189 | Entity | CURRENT |
| reports/historical_metric_inventory.md | 45 | | docs/DR-90_REPRESENTATION_DISCOVERY.md | 40 | - Discovery  | CURRENT |
| reports/historical_metric_inventory.md | 46 | | docs/MEASUREMENT_SPECIFICATION.md | 33 | - **Discovery F1  | CURRENT |
| reports/historical_metric_inventory.md | 47 | | docs/INVENTION_CONSTITUTION.md | 27 | | Discovery | Find r | CURRENT |
| reports/historical_metric_inventory.md | 48 | | docs/INVENTION_CONSTITUTION.md | 59 | it continuously. The | CURRENT |
| reports/historical_metric_inventory.md | 49 | | docs/DISCOVERY_OBJECT_AUDIT.md | 123 | 1. **Discovery F1=0 | CURRENT |
| reports/historical_metric_inventory.md | 50 | | docs/DISCOVERY_OBJECT_AUDIT.md | 171 | Previous claim: "Di | CURRENT |
| reports/historical_metric_inventory.md | 51 | | reports/bootstrap_statistics.md | 28 | | M-005 | Discovery | CURRENT |
| reports/historical_metric_inventory.md | 52 | | reports/bootstrap_statistics.md | 29 | | M-006 | Recogniti | CURRENT |
| reports/historical_metric_inventory.md | 53 | | reports/bootstrap_statistics.md | 31 | | M-008 | FP floor  | CURRENT |
| reports/historical_metric_inventory.md | 54 | | reports/bootstrap_statistics.md | 35 | | M-012 | Aggregate | CURRENT |
| reports/historical_metric_inventory.md | 55 | | reports/measurement_constitution_m8.json | 388 | "evidence | CURRENT |
| reports/historical_metric_inventory.md | 56 | | reports/measurement_constitution_m8.json | 452 | "evidence | CURRENT |
| reports/historical_metric_inventory.md | 57 | | reports/measurement_constitution_m8.json | 836 | "evidence | CURRENT |
| reports/historical_metric_inventory.md | 58 | | reports/calibration_documented_m2e1.json | 44 | "notes": " | CURRENT |
| reports/historical_metric_inventory.md | 59 | | reports/calibration_documented_m2e1.json | 76 | "notes": " | CURRENT |
| reports/historical_metric_inventory.md | 60 | | reports/calibration_documented_m2e1.json | 92 | "notes": " | CURRENT |
| reports/historical_metric_inventory.md | 61 | | reports/calibration_documented_m2e1.json | 108 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 62 | | reports/calibration_documented_m2e1.json | 124 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 63 | | reports/calibration_documented_m2e1.json | 139 | "fp_floor | CURRENT |
| reports/historical_metric_inventory.md | 64 | | reports/calibration_documented_m2e1.json | 140 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 65 | | reports/calibration_documented_m2e1.json | 172 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 66 | | reports/calibration_documented_m2e1.json | 204 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 67 | | reports/calibration_documented_m2e1.json | 220 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 68 | | reports/calibration_documented_m2e1.json | 236 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 69 | | reports/calibration_documented_m2e1.json | 252 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 70 | | reports/calibration_documented_m2e1.json | 268 | "notes":  | CURRENT |
| reports/historical_metric_inventory.md | 71 | | reports/bootstrap_statistics.json | 87 | "ci_95_upper": 0. | CURRENT |
| reports/historical_metric_inventory.md | 72 | | reports/bootstrap_statistics.json | 103 | "ci_95_lower": 0 | CURRENT |
| reports/historical_metric_inventory.md | 73 | | reports/bootstrap_statistics.json | 133 | "point_estimate" | CURRENT |
| reports/historical_metric_inventory.md | 74 | | reports/bootstrap_statistics.json | 206 | "ci_95_upper": 0 | CURRENT |
| reports/historical_metric_inventory.md | 87 | | reports/discovery_score_recalibration.md | 16 | - Score =  | CURRENT |
| reports/historical_metric_inventory.md | 88 | | reports/discovery_score_recalibration.md | 30 | The score  | CURRENT |
| reports/historical_metric_inventory.md | 89 | | reports/discovery_score_recalibration.md | 38 | the code s | CURRENT |
| reports/historical_metric_inventory.md | 90 | | reports/discovery_score_recalibration.md | 50 | bridges ma | CURRENT |
| reports/historical_metric_inventory.md | 91 | | reports/repository_truth_check.md | 17 | DISCOVERY_OBJECT_ | CURRENT |
| reports/historical_metric_inventory.md | 92 | | reports/repository_truth_check.md | 26 | - PRELIMINARY_MEA | CURRENT |
| reports/historical_metric_inventory.md | 94 | | reports/repository_truth_check.md | 32 | - docs/ files: ** | CURRENT |
| reports/historical_metric_inventory.md | 95 | | reports/repository_truth_check.md | 37 | 3. docs/INVENTION | CURRENT |
| reports/historical_metric_inventory.md | 96 | | reports/repository_truth_check.md | 45 | 2. **docs/INVENTI | CURRENT |
| reports/historical_metric_inventory.md | 97 | | reports/repository_truth_check.md | 49 | 4. **docs/DR-90_R | CURRENT |
| reports/historical_metric_inventory.md | 98 | | reports/repository_truth_check.md | 50 | 5. **docs/MEASURE | CURRENT |
| reports/historical_metric_inventory.md | 99 | | reports/repository_truth_check.md | 60 | (was 0.9189 with  | CURRENT |
| reports/historical_metric_inventory.md | 100 | | reports/repository_truth_check.md | 68 | 1. **'Discovery F | CURRENT |
| reports/historical_metric_inventory.md | 101 | | reports/repository_truth_check.md | 87 | 1. Regenerated di | CURRENT |
| reports/historical_metric_inventory.md | 102 | | reports/historical_metric_inventory.md | 17 | ## 0.9189 |  | CURRENT |
| reports/historical_metric_inventory.md | 103 | | reports/historical_metric_inventory.md | 22 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 104 | | reports/historical_metric_inventory.md | 23 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 105 | | reports/historical_metric_inventory.md | 24 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 106 | | reports/historical_metric_inventory.md | 25 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 107 | | reports/historical_metric_inventory.md | 26 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 108 | | reports/historical_metric_inventory.md | 27 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 110 | | reports/historical_metric_inventory.md | 29 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 111 | | reports/historical_metric_inventory.md | 30 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 112 | | reports/historical_metric_inventory.md | 31 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 113 | | reports/historical_metric_inventory.md | 32 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 114 | | reports/historical_metric_inventory.md | 33 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 115 | | reports/historical_metric_inventory.md | 34 | | PRELIMINAR | CURRENT |
| reports/historical_metric_inventory.md | 116 | | reports/historical_metric_inventory.md | 35 | | docs/MEASU | CURRENT |
| reports/historical_metric_inventory.md | 118 | | reports/historical_metric_inventory.md | 37 | | docs/MEASU | CURRENT |
| reports/historical_metric_inventory.md | 119 | | reports/historical_metric_inventory.md | 38 | | docs/DR-90 | CURRENT |
| reports/historical_metric_inventory.md | 120 | | reports/historical_metric_inventory.md | 39 | | docs/MEASU | CURRENT |
| reports/historical_metric_inventory.md | 123 | | reports/historical_metric_inventory.md | 42 | | docs/DISCO | CURRENT |
| reports/historical_metric_inventory.md | 124 | | reports/historical_metric_inventory.md | 43 | | docs/DISCO | CURRENT |
| reports/historical_metric_inventory.md | 127 | | reports/historical_metric_inventory.md | 46 | | reports/bo | CURRENT |
| reports/historical_metric_inventory.md | 132 | | reports/historical_metric_inventory.md | 51 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 133 | | reports/historical_metric_inventory.md | 52 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 134 | | reports/historical_metric_inventory.md | 53 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 135 | | reports/historical_metric_inventory.md | 54 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 136 | | reports/historical_metric_inventory.md | 55 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 137 | | reports/historical_metric_inventory.md | 56 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 138 | | reports/historical_metric_inventory.md | 57 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 139 | | reports/historical_metric_inventory.md | 58 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 140 | | reports/historical_metric_inventory.md | 59 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 141 | | reports/historical_metric_inventory.md | 60 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 142 | | reports/historical_metric_inventory.md | 61 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 143 | | reports/historical_metric_inventory.md | 62 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 144 | | reports/historical_metric_inventory.md | 63 | | reports/ca | CURRENT |
| reports/historical_metric_inventory.md | 145 | | reports/historical_metric_inventory.md | 64 | | reports/bo | CURRENT |
| reports/historical_metric_inventory.md | 146 | | reports/historical_metric_inventory.md | 65 | | reports/bo | CURRENT |
| reports/historical_metric_inventory.md | 147 | | reports/historical_metric_inventory.md | 66 | | reports/bo | CURRENT |
| reports/historical_metric_inventory.md | 148 | | reports/historical_metric_inventory.md | 67 | | reports/bo | CURRENT |
| reports/historical_metric_inventory.md | 149 | | reports/historical_metric_inventory.md | 80 | | reports/di | CURRENT |
| reports/historical_metric_inventory.md | 153 | | reports/historical_metric_inventory.md | 84 | | reports/di | CURRENT |
| reports/historical_metric_inventory.md | 154 | | reports/historical_metric_inventory.md | 86 | | reports/fa | CURRENT |
| reports/historical_metric_inventory.md | 155 | | reports/historical_metric_inventory.md | 87 | | reports/fa | CURRENT |
| reports/historical_metric_inventory.md | 156 | | reports/historical_metric_inventory.md | 88 | | reports/fa | CURRENT |
| reports/historical_metric_inventory.md | 157 | | reports/historical_metric_inventory.md | 89 | | reports/fa | CURRENT |
| reports/historical_metric_inventory.md | 158 | | reports/historical_metric_inventory.md | 90 | | reports/fa | CURRENT |
| reports/historical_metric_inventory.md | 161 | | reports/historical_metric_inventory.md | 93 | | reports/hi | CURRENT |
| reports/historical_metric_inventory.md | 163 | | reports/historical_metric_inventory.md | 95 | | reports/fa | CURRENT |
| reports/historical_metric_inventory.md | 175 | | reports/historical_metric_inventory.md | 108 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 186 | | reports/historical_metric_inventory.md | 121 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 187 | | reports/historical_metric_inventory.md | 122 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 191 | | reports/historical_metric_inventory.md | 126 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 194 | | reports/historical_metric_inventory.md | 129 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 195 | | reports/historical_metric_inventory.md | 130 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 196 | | reports/historical_metric_inventory.md | 131 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 197 | | reports/historical_metric_inventory.md | 132 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 198 | | reports/historical_metric_inventory.md | 303 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 199 | | reports/historical_metric_inventory.md | 304 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 200 | | reports/historical_metric_inventory.md | 316 | | PRELIMINA | CURRENT |
| reports/historical_metric_inventory.md | 202 | | reports/historical_metric_inventory.md | 329 | | reports/b | CURRENT |
| reports/historical_metric_inventory.md | 203 | | reports/historical_metric_inventory.md | 359 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 204 | | reports/historical_metric_inventory.md | 403 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 205 | | reports/historical_metric_inventory.md | 435 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 206 | | reports/historical_metric_inventory.md | 443 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 207 | | reports/measurement_provenance_audit.md | 85 | - **Value:* | CURRENT |
| reports/historical_metric_inventory.md | 208 | | reports/measurement_provenance_audit.md | 101 | - **Value: | CURRENT |
| reports/historical_metric_inventory.md | 209 | | reports/measurement_provenance_audit.md | 133 | - **Value: | CURRENT |
| reports/historical_metric_inventory.md | 210 | | reports/measurement_provenance_audit.md | 197 | - **Value: | CURRENT |
| reports/historical_metric_inventory.md | 212 | | reports/failure_envelope_m7.json | 166 | 0.9189 | HISTORIC | CURRENT |
| reports/historical_metric_inventory.md | 213 | | reports/failure_envelope_m7.json | 216 | 0.9189, | HISTORI | CURRENT |
| reports/historical_metric_inventory.md | 214 | | reports/failure_envelope_m7.json | 282 | "baseline_value": | CURRENT |
| reports/historical_metric_inventory.md | 215 | | reports/failure_envelope_m7.json | 293 | "FP floor = 0.918 | CURRENT |
| reports/historical_metric_inventory.md | 216 | | reports/failure_envelope_m7.json | 431 | 0.9189 | HISTORIC | CURRENT |
| reports/historical_metric_inventory.md | 217 | | reports/failure_envelope_m7.json | 770 | "THIS IS THE METR | CURRENT |
| reports/historical_metric_inventory.md | 218 | | reports/failure_envelope_m7.json | 781 | "DR-91 invalidati | CURRENT |
| reports/historical_metric_inventory.md | 219 | | reports/honest_scoreboard.md | 15 | | M-005 | 0.7879 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 220 | | reports/honest_scoreboard.md | 16 | | M-006 | 0.9744 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 221 | | reports/honest_scoreboard.md | 18 | | M-008 | 0.9189 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 222 | | reports/honest_scoreboard.md | 22 | | M-012 | 0.7879 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 223 | | reports/honest_scoreboard.md | 54 | | M-005 Discovery F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 224 | | reports/honest_scoreboard.md | 55 | | M-006 Recognition F1 | CURRENT |
| reports/historical_metric_inventory.md | 225 | | reports/honest_scoreboard.md | 56 | | M-008 FP floor (syno | CURRENT |
| reports/historical_metric_inventory.md | 226 | | reports/honest_scoreboard.md | 65 | - Was: F1=0.9189, Scor | CURRENT |
| reports/historical_metric_inventory.md | 227 | | reports/historical_recalibration.json | 112 | "claimed_f1" | CURRENT |
| reports/historical_metric_inventory.md | 228 | | reports/historical_recalibration.json | 122 | "delta_vs_cl | CURRENT |
| reports/historical_metric_inventory.md | 229 | | reports/failure_envelope_m7.md | 45 | | M-008 | FP floor ( | CURRENT |
| reports/historical_metric_inventory.md | 230 | | tests/test_dr98_historical_recalibration.py | 173 | """HC- | CURRENT |
| reports/historical_metric_inventory.md | 231 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 232 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 233 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 234 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 235 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 236 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 237 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 238 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 239 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 241 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 242 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 243 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 244 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 247 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 248 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 249 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 250 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 251 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 252 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 253 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 254 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 255 | | programs/A_metrology/measurement_provenance.py | 457 | val | CURRENT |
| reports/historical_metric_inventory.md | 256 | | programs/A_metrology/failure_envelope_m7.py | 354 | "FP fl | CURRENT |
| reports/historical_metric_inventory.md | 257 | | programs/A_metrology/failure_envelope_m7.py | 585 | "THIS  | CURRENT |
| reports/historical_metric_inventory.md | 258 | | programs/A_metrology/failure_envelope_m7.py | 596 | "DR-91 | CURRENT |
| reports/historical_metric_inventory.md | 259 | | programs/A_metrology/MeasurementEngineSpecification.md | 8 | CURRENT |
| reports/historical_metric_inventory.md | 260 | | reports/failure_envelopes/M-005.md | 8 | - **95% CI:** [0. | CURRENT |
| reports/historical_metric_inventory.md | 261 | | reports/failure_envelopes/M-105.md | 15 | - THIS IS THE ME | CURRENT |
| reports/historical_metric_inventory.md | 262 | | reports/failure_envelopes/M-105.md | 28 | - DR-91 invalida | CURRENT |
| reports/historical_metric_inventory.md | 263 | | reports/failure_envelopes/M-006.md | 8 | - **95% CI:** [0. | CURRENT |
| reports/historical_metric_inventory.md | 264 | | reports/failure_envelopes/M-012.md | 8 | - **95% CI:** [0. | CURRENT |
| reports/historical_metric_inventory.md | 265 | | reports/failure_envelopes/M-008.md | 7 | - **Baseline valu | CURRENT |
| reports/historical_metric_inventory.md | 266 | | reports/failure_envelopes/M-008.md | 15 | - FP floor = 0.9 | CURRENT |
| reports/historical_metric_inventory.md | 299 | | reports/repository_truth_check.md | 26 | - PRELIMINARY_MEA | CURRENT |
| reports/historical_metric_inventory.md | 451 | | reports/honest_scoreboard.md | 54 | | M-005 Discovery F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 556 | | FAILURES.md | 7046 | | M-008 FP floor | 0.9189 ± 0.0559 |  | CURRENT |
| reports/historical_metric_inventory.md | 557 | | FAILURES.md | 7100 | - The FP floor=1.0000 is now FP floor | CURRENT |
| reports/historical_metric_inventory.md | 568 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 37 | | Recognition F1 | CURRENT |
| reports/historical_metric_inventory.md | 569 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 39 | | FP floor (toke | CURRENT |
| reports/historical_metric_inventory.md | 579 | | reports/bootstrap_statistics.md | 29 | | M-006 | Recogniti | CURRENT |
| reports/historical_metric_inventory.md | 580 | | reports/bootstrap_statistics.md | 31 | | M-008 | FP floor  | CURRENT |
| reports/historical_metric_inventory.md | 599 | | reports/historical_metric_inventory.md | 31 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 600 | | reports/historical_metric_inventory.md | 32 | | FAILURES.m | CURRENT |
| reports/historical_metric_inventory.md | 601 | | reports/historical_metric_inventory.md | 34 | | PRELIMINAR | CURRENT |
| reports/historical_metric_inventory.md | 603 | | reports/historical_metric_inventory.md | 46 | | reports/bo | CURRENT |
| reports/historical_metric_inventory.md | 604 | | reports/historical_metric_inventory.md | 89 | | reports/fa | CURRENT |
| reports/historical_metric_inventory.md | 605 | | reports/historical_metric_inventory.md | 122 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 606 | | reports/historical_metric_inventory.md | 129 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 607 | | reports/historical_metric_inventory.md | 132 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 637 | | reports/historical_metric_inventory.md | 303 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 638 | | reports/historical_metric_inventory.md | 304 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 650 | | reports/historical_metric_inventory.md | 316 | | PRELIMINA | CURRENT |
| reports/historical_metric_inventory.md | 663 | | reports/historical_metric_inventory.md | 329 | | reports/b | CURRENT |
| reports/historical_metric_inventory.md | 684 | | reports/historical_metric_inventory.md | 359 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 727 | | reports/historical_metric_inventory.md | 403 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 759 | | reports/historical_metric_inventory.md | 435 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 767 | | reports/historical_metric_inventory.md | 443 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 778 | | reports/measurement_provenance_audit.md | 101 | - **Value: | CURRENT |
| reports/historical_metric_inventory.md | 779 | | reports/measurement_provenance_audit.md | 133 | - **Value: | CURRENT |
| reports/historical_metric_inventory.md | 793 | | reports/failure_envelope_m7.json | 293 | "FP floor = 0.918 | CURRENT |
| reports/historical_metric_inventory.md | 799 | | reports/honest_scoreboard.md | 16 | | M-006 | 0.9744 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 800 | | reports/honest_scoreboard.md | 18 | | M-008 | 0.9189 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 809 | | reports/honest_scoreboard.md | 55 | | M-006 Recognition F1 | CURRENT |
| reports/historical_metric_inventory.md | 810 | | reports/honest_scoreboard.md | 56 | | M-008 FP floor (syno | CURRENT |
| reports/historical_metric_inventory.md | 849 | | programs/A_metrology/failure_envelope_m7.py | 354 | "FP fl | CURRENT |
| reports/historical_metric_inventory.md | 881 | | reports/failure_envelopes/M-006.md | 8 | - **95% CI:** [0. | CURRENT |
| reports/historical_metric_inventory.md | 889 | | reports/failure_envelopes/M-008.md | 15 | - FP floor = 0.9 | CURRENT |
| reports/measurement_provenance_audit.md | 85 | - **Value:** 0.7879 ± 0.0809 (95% CI: 0.6207, 0.9189) | CURRENT |
| reports/measurement_provenance_audit.md | 101 | - **Value:** 0.9744 ± 0.0252 (95% CI: 0.9189, 1.0000) | CURRENT |
| reports/measurement_provenance_audit.md | 133 | - **Value:** 0.9189 ± 0.0978 (95% CI: 0.6667, 1.0000) | CURRENT |
| reports/measurement_provenance_audit.md | 197 | - **Value:** 0.7879 ± 0.0809 (95% CI: 0.6207, 0.9189) | CURRENT |
| reports/historical_recalibration.md | 29 | | HC-005 | 201 | Discovery F1 (the headline number, reported | CURRENT |
| reports/failure_envelope_m7.json | 166 | 0.9189 | CURRENT |
| reports/failure_envelope_m7.json | 216 | 0.9189, | CURRENT |
| reports/failure_envelope_m7.json | 282 | "baseline_value": 0.9189, | CURRENT |
| reports/failure_envelope_m7.json | 293 | "FP floor = 0.9189 \u00b1 0.0559 [0.7879, 1.0000] \u2014 CAT | CURRENT |
| reports/failure_envelope_m7.json | 431 | 0.9189 | CURRENT |
| reports/failure_envelope_m7.json | 770 | "THIS IS THE METRIC DR-91 INVALIDATED (F1=0.9189 was measuri | CURRENT |
| reports/failure_envelope_m7.json | 781 | "DR-91 invalidation: headline F1=0.9189 was recognition, not | CURRENT |
| reports/claim_traceability.md | 34 | ## FP floor = 0.9189 | CURRENT |
| reports/claim_traceability.md | 39 | reports/bootstrap_statistics.json (M-008: 0.9189 ± 0.0978) | CURRENT |
| reports/claim_traceability.md | 74 | ## Discovery F1 = 0.9189 (HISTORICAL) | CURRENT |
| reports/claim_traceability.md | 78 | → discovery_capability_score.json (stale, F1=0.9189) | CURRENT |
| reports/honest_scoreboard.md | 15 | | M-005 | 0.7879 ± 0.0809 | [0.6207, 0.9189] | 20 | 500 | B  | CURRENT |
| reports/honest_scoreboard.md | 16 | | M-006 | 0.9744 ± 0.0252 | [0.9189, 1.0000] | 20 | 500 | B  | CURRENT |
| reports/honest_scoreboard.md | 18 | | M-008 | 0.9189 ± 0.0978 | [0.6667, 1.0000] | 20 | 200 | B  | CURRENT |
| reports/honest_scoreboard.md | 22 | | M-012 | 0.7879 ± 0.0809 | [0.6207, 0.9189] | 20 | 500 | B  | CURRENT |
| reports/honest_scoreboard.md | 54 | | M-005 Discovery F1 (shared, DR-91) | 0.7879 | ± 0.0809 | [ | CURRENT |
| reports/honest_scoreboard.md | 55 | | M-006 Recognition F1 (all, DR-91) | 0.9744 | ± 0.0252 | [0 | CURRENT |
| reports/honest_scoreboard.md | 56 | | M-008 FP floor (synonym) | 0.9189 | ± 0.0978 | [0.6667, 1. | CURRENT |
| reports/honest_scoreboard.md | 65 | - Was: F1=0.9189, Score=9/10 (stale, circular) | CURRENT |
| reports/historical_recalibration.json | 112 | "claimed_f1": 0.9189, | CURRENT |
| reports/historical_recalibration.json | 122 | "delta_vs_claimed_strict": -0.9189, | CURRENT |
| reports/failure_envelope_m7.md | 45 | | M-008 | FP floor (synonym) | 0.9189 | False | STABLE | 0 | | CURRENT |
| reports/public_claim_inventory.md | 241 | | score_rating | FAILURES.md | 5831 | - Discovery scorecard  | CURRENT |
| reports/public_claim_inventory.md | 360 | | score_rating | docs/MEASUREMENT_REASSESSMENT.md | 22 | | D | CURRENT |
| reports/public_claim_inventory.md | 386 | | score_rating | reports/discovery_score_recalibration.md |  | CURRENT |
| reports/public_claim_inventory.md | 388 | | score_rating | reports/discovery_score_recalibration.md |  | CURRENT |
| reports/public_claim_inventory.md | 401 | | score_rating | reports/historical_metric_inventory.md | 22 | CURRENT |
| reports/public_claim_inventory.md | 414 | | score_rating | reports/honest_scoreboard.md | 65 | - Was:  | CURRENT |
| reports/public_claim_inventory.md | 481 | | score_rating | programs/A_metrology/measurement_verificati | CURRENT |
| reports/public_claim_inventory.md | 482 | | score_rating | programs/A_metrology/measurement_verificati | CURRENT |
| reports/public_claim_inventory.md | 484 | | score_rating | programs/A_metrology/measurement_verificati | CURRENT |
| reports/public_claim_inventory.md | 492 | | score_rating | programs/A_metrology/final_repository_verif | CURRENT |
| reports/public_claim_inventory.md | 561 | | f1_value | FAILURES.md | 3087 | Honest result: F1=0.9189,  | CURRENT |
| reports/public_claim_inventory.md | 565 | | f1_value | FAILURES.md | 5712 | The F1=0.9189 (reported si | CURRENT |
| reports/public_claim_inventory.md | 566 | | f1_value | FAILURES.md | 5729 | However, the discovery F1= | CURRENT |
| reports/public_claim_inventory.md | 567 | | f1_value | FAILURES.md | 5758 | The F1=0.9189 that has bee | CURRENT |
| reports/public_claim_inventory.md | 569 | | f1_value | FAILURES.md | 5821 | - The discovery F1=0.9189  | CURRENT |
| reports/public_claim_inventory.md | 571 | | f1_value | FAILURES.md | 5831 | - Discovery scorecard (9.0 | CURRENT |
| reports/public_claim_inventory.md | 573 | | f1_value | FAILURES.md | 6001 | | Discovery F1=0.9189 | YE | CURRENT |
| reports/public_claim_inventory.md | 575 | | f1_value | FAILURES.md | 6702 | - HC-005 (cycle 201 F1=0.9 | CURRENT |
| reports/public_claim_inventory.md | 586 | | f1_value | PRELIMINARY_MEASUREMENT_VERDICT.md | 103 | - F1 | CURRENT |
| reports/public_claim_inventory.md | 596 | | f1_value | docs/MEASUREMENT_REASSESSMENT.md | 21 | | Disco | CURRENT |
| reports/public_claim_inventory.md | 597 | | f1_value | docs/MEASUREMENT_REASSESSMENT.md | 22 | | Disco | CURRENT |
| reports/public_claim_inventory.md | 598 | | f1_value | docs/DR-90_REPRESENTATION_DISCOVERY.md | 40 | - | CURRENT |
| reports/public_claim_inventory.md | 601 | | f1_value | docs/MEASUREMENT_SPECIFICATION.md | 33 | - **Di | CURRENT |
| reports/public_claim_inventory.md | 603 | | f1_value | docs/INVENTION_CONSTITUTION.md | 59 | it contin | CURRENT |
| reports/public_claim_inventory.md | 605 | | f1_value | docs/DISCOVERY_OBJECT_AUDIT.md | 123 | 1. **Dis | CURRENT |
| reports/public_claim_inventory.md | 606 | | f1_value | docs/DISCOVERY_OBJECT_AUDIT.md | 171 | Previous | CURRENT |
| reports/public_claim_inventory.md | 612 | | f1_value | reports/discovery_score_recalibration.md | 30 | | CURRENT |
| reports/public_claim_inventory.md | 614 | | f1_value | reports/discovery_score_recalibration.md | 50 | | CURRENT |
| reports/public_claim_inventory.md | 620 | | f1_value | reports/repository_truth_check.md | 28 | | docs | CURRENT |
| reports/public_claim_inventory.md | 622 | | f1_value | reports/repository_truth_check.md | 30 | | docs | CURRENT |
| reports/public_claim_inventory.md | 625 | | f1_value | reports/repository_truth_check.md | 57 | - Curr | CURRENT |
| reports/public_claim_inventory.md | 626 | | f1_value | reports/historical_metric_inventory.md | 23 | | | CURRENT |
| reports/public_claim_inventory.md | 627 | | f1_value | reports/historical_metric_inventory.md | 24 | | | CURRENT |
| reports/public_claim_inventory.md | 628 | | f1_value | reports/historical_metric_inventory.md | 25 | | | CURRENT |
| reports/public_claim_inventory.md | 629 | | f1_value | reports/historical_metric_inventory.md | 26 | | | CURRENT |
| reports/public_claim_inventory.md | 630 | | f1_value | reports/historical_metric_inventory.md | 27 | | | CURRENT |
| reports/public_claim_inventory.md | 632 | | f1_value | reports/historical_metric_inventory.md | 29 | | | CURRENT |
| reports/public_claim_inventory.md | 633 | | f1_value | reports/historical_metric_inventory.md | 30 | | | CURRENT |
| reports/public_claim_inventory.md | 670 | | f1_value | reports/historical_metric_inventory.md | 226 |  | CURRENT |
| reports/public_claim_inventory.md | 757 | | f1_value | reports/failure_envelope_m7.json | 770 | "THIS  | CURRENT |
| reports/public_claim_inventory.md | 759 | | f1_value | reports/failure_envelope_m7.json | 781 | "DR-91 | CURRENT |
| reports/public_claim_inventory.md | 761 | | f1_value | reports/honest_scoreboard.md | 65 | - Was: F1=0 | CURRENT |
| reports/public_claim_inventory.md | 770 | | f1_value | tests/test_dr98_historical_recalibration.py | 1 | CURRENT |
| reports/public_claim_inventory.md | 775 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 777 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 783 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 785 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 787 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 789 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 799 | | f1_value | programs/A_metrology/measurement_verification_s | CURRENT |
| reports/public_claim_inventory.md | 801 | | f1_value | programs/A_metrology/measurement_verification_s | CURRENT |
| reports/public_claim_inventory.md | 803 | | f1_value | programs/A_metrology/measurement_verification_s | CURRENT |
| reports/public_claim_inventory.md | 812 | | f1_value | programs/A_metrology/measurement_verification_s | CURRENT |
| reports/public_claim_inventory.md | 822 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| reports/public_claim_inventory.md | 823 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| reports/public_claim_inventory.md | 826 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| reports/public_claim_inventory.md | 842 | | f1_value | programs/A_metrology/failure_envelope_m7.py | 5 | CURRENT |
| reports/public_claim_inventory.md | 844 | | f1_value | programs/A_metrology/failure_envelope_m7.py | 5 | CURRENT |
| reports/public_claim_inventory.md | 847 | | f1_value | programs/A_metrology/MeasurementEngineSpecifica | CURRENT |
| reports/public_claim_inventory.md | 854 | | f1_value | reports/failure_envelopes/M-105.md | 15 | - THI | CURRENT |
| reports/public_claim_inventory.md | 856 | | f1_value | reports/failure_envelopes/M-105.md | 28 | - DR- | CURRENT |
| reports/public_claim_inventory.md | 871 | | recall_value | FAILURES.md | 3081 | inflated. The honest F | CURRENT |
| reports/public_claim_inventory.md | 872 | | recall_value | FAILURES.md | 3087 | Honest result: F1=0.91 | CURRENT |
| reports/public_claim_inventory.md | 880 | | recall_value | reports/historical_metric_inventory.md | 22 | CURRENT |
| reports/public_claim_inventory.md | 881 | | recall_value | reports/historical_metric_inventory.md | 23 | CURRENT |
| reports/public_claim_inventory.md | 4414 | | status_claim | docs/MEASUREMENT_REASSESSMENT.md | 22 | | D | CURRENT |
| reports/public_claim_inventory.md | 4649 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4652 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4654 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4656 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4658 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4662 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4665 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4667 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4669 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4671 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4673 | | status_claim | reports/calibration_documented_m2e1.json |  | CURRENT |
| reports/public_claim_inventory.md | 4737 | | status_claim | reports/historical_metric_inventory.md | 22 | CURRENT |
| reports/public_claim_inventory.md | 4738 | | status_claim | reports/historical_metric_inventory.md | 23 | CURRENT |
| reports/public_claim_inventory.md | 4739 | | status_claim | reports/historical_metric_inventory.md | 24 | CURRENT |
| reports/public_claim_inventory.md | 4740 | | status_claim | reports/historical_metric_inventory.md | 25 | CURRENT |
| reports/public_claim_inventory.md | 4741 | | status_claim | reports/historical_metric_inventory.md | 26 | CURRENT |
| reports/public_claim_inventory.md | 4742 | | status_claim | reports/historical_metric_inventory.md | 27 | CURRENT |
| reports/public_claim_inventory.md | 4744 | | status_claim | reports/historical_metric_inventory.md | 29 | CURRENT |
| reports/public_claim_inventory.md | 4745 | | status_claim | reports/historical_metric_inventory.md | 30 | CURRENT |
| reports/public_claim_inventory.md | 4746 | | status_claim | reports/historical_metric_inventory.md | 31 | CURRENT |
| reports/public_claim_inventory.md | 4748 | | status_claim | reports/historical_metric_inventory.md | 33 | CURRENT |
| reports/public_claim_inventory.md | 4786 | | status_claim | reports/historical_metric_inventory.md | 21 | CURRENT |
| reports/public_claim_inventory.md | 4787 | | status_claim | reports/historical_metric_inventory.md | 21 | CURRENT |
| reports/public_claim_inventory.md | 4790 | | status_claim | reports/historical_metric_inventory.md | 21 | CURRENT |
| reports/public_claim_inventory.md | 4888 | | status_claim | reports/historical_metric_inventory.md | 55 | CURRENT |
| tests/test_dr98_historical_recalibration.py | 173 | """HC-005 (cycle 201 F1=0.9189) was invalidated by DR-91; sh | TEST |
| audit/measurement_integrity/dr98_historical_recalibration.py | 16 | - cycle 201: F1=0.9189 (discovery F1, reported since) | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 19 | DR-91 already showed F1=0.9189 was invalid (it measured enti | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 225 | claimed_f1=0.9189, | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 440 | # HC-005 (cycle 201 F1=0.9189) was already invalidated by DR | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 451 | print(f"  - HC-005 (cycle 201 F1=0.9189) is {hc005['verdict_ | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 611 | lines.append("F1=0.9189 (HC-005) is ERODED — already documen | HISTORICAL |
| programs/A_metrology/measurement_verification_sprint.py | 70 | old_score = 0.9189  # the known stale value | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 99 | lines.append(f"- Score = 9/10 (round(10 × 0.9189) = 9)") | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 113 | lines.append("The score dropped from 9/10 (F1=0.9189) to " | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 122 | lines.append("   the code said BRIDGE_SYNONYMS = {} but the  | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 134 | lines.append("bridges matched (F1=0.9189). With the empty sy | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 243 | "0.9189": "Old discovery capability F1 (circular, cycle 201- | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 463 | lines.append(f"- Was: F1=0.9189, Score=9/10 (stale, circular | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 500 | lines.append("DISCOVERY_OBJECT_AUDIT.md, etc.) cite old valu | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 511 | lines.append("- PRELIMINARY_MEASUREMENT_VERDICT.md: **NO** — | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 514 | lines.append("- dr98_historical_recalibration.py: **NO** — h | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 517 | lines.append("- docs/ files: **NO** — multiple files cite 0. | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 522 | lines.append("3. docs/INVENTION_CONSTITUTION.md: mark 0.9189 | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 532 | lines.append("2. **docs/INVENTION_CONSTITUTION.md**: claims  | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 536 | lines.append("4. **docs/DR-90_REPRESENTATION_DISCOVERY.md**: | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 537 | lines.append("5. **docs/MEASUREMENT_SPECIFICATION.md**: cite | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 549 | lines.append("  (was 0.9189 with circular synonyms)") | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 559 | lines.append("1. **'Discovery F1 = 0.9189'** — this was circ | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 578 | lines.append(f"1. Regenerated discovery_capability_score.jso | CURRENT |
| programs/A_metrology/final_repository_verification.py | 156 | "claim": "FP floor = 0.9189", | CHECK |
| programs/A_metrology/final_repository_verification.py | 160 | "reports/bootstrap_statistics.json (M-008: 0.9189 ± 0.0978)" | CHECK |
| programs/A_metrology/final_repository_verification.py | 193 | "claim": "Discovery F1 = 0.9189 (HISTORICAL)", | CHECK |
| programs/A_metrology/final_repository_verification.py | 196 | "  → discovery_capability_score.json (stale, F1=0.9189)", | CHECK |
| programs/A_metrology/final_repository_verification.py | 251 | values_to_check = ["0.5714", "0.7879", "0.9189", "0.8571", " | CHECK |
| programs/A_metrology/final_repository_verification.py | 478 | "docs/: all 0.9189 occurrences labeled HISTORICAL", | CHECK |
| programs/A_metrology/final_repository_verification.py | 482 | q4 = "YES — FP floor = 0.9189 (CI touches 1.0)" | CHECK |
| programs/A_metrology/final_repository_verification.py | 485 | "FP floor = 0.9189 ± 0.0978 [0.667, 1.0] — still above 5% th | CHECK |
| programs/A_metrology/final_repository_verification.py | 494 | "  - Discovery capability F1 = 0.5714 (6/10) — NOT 0.9189 (9 | CHECK |
| programs/A_metrology/final_repository_verification.py | 497 | "  - FP floor = 0.9189 — the matcher cannot discriminate", | CHECK |
| programs/A_metrology/final_repository_verification.py | 506 | "No stale 0.9189 in AUDITOR_SCORECARD (regenerated to 0.5714 | CHECK |
| programs/A_metrology/final_repository_verification.py | 508 | "docs/ files with 0.9189 all labeled HISTORICAL", | CHECK |
| programs/A_metrology/measurement_provenance.py | 457 | value=0.9189, | CURRENT |
| programs/A_metrology/failure_envelope_m7.py | 354 | "FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC" | CURRENT |
| programs/A_metrology/failure_envelope_m7.py | 585 | "THIS IS THE METRIC DR-91 INVALIDATED (F1=0.9189 was measuri | CURRENT |
| programs/A_metrology/failure_envelope_m7.py | 596 | "DR-91 invalidation: headline F1=0.9189 was recognition, not | CURRENT |
| programs/A_metrology/MeasurementEngineSpecification.md | 803 | - THIS IS THE METRIC DR-91 INVALIDATED. The F1=0.9189 report | CHECK |
| reports/failure_envelopes/M-005.md | 8 | - **95% CI:** [0.6207, 0.9189] | CURRENT |
| reports/failure_envelopes/M-105.md | 15 | - THIS IS THE METRIC DR-91 INVALIDATED (F1=0.9189 was measur | CURRENT |
| reports/failure_envelopes/M-105.md | 28 | - DR-91 invalidation: headline F1=0.9189 was recognition, no | CURRENT |
| reports/failure_envelopes/M-006.md | 8 | - **95% CI:** [0.9189, 1.0000] | CURRENT |
| reports/failure_envelopes/M-012.md | 8 | - **95% CI:** [0.6207, 0.9189] | CURRENT |
| reports/failure_envelopes/M-008.md | 7 | - **Baseline value:** 0.9189 | CURRENT |
| reports/failure_envelopes/M-008.md | 15 | - FP floor = 0.9189 ± 0.0559 [0.7879, 1.0000] — CATASTROPHIC | CURRENT |

## 0.8571

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 5685 | 3. **Proposal-only F1 = 0.8571 (shared entities + synonyms)* | HISTORICAL |
| FAILURES.md | 5777 | | synonym | 1.0000 | 0.8571 | | HISTORICAL |
| FAILURES.md | 5794 | Discovery F1 = 0.8571 | HISTORICAL |
| FAILURES.md | 5822 | - The honest Discovery F1 (shared entities, synonyms) = 0.85 | HISTORICAL |
| FAILURES.md | 6700 | - HC-006 (production F1=0.8571) SURVIVES under DR-91 convent | HISTORICAL |
| FAILURES.md | 6712 | aggregate F1=0.8571 in PRELIMINARY — different metrics) | HISTORICAL |
| FAILURES.md | 6750 | production F1=0.8571 in PRELIMINARY_MEASUREMENT_VERDICT.md i | HISTORICAL |
| FAILURES.md | 6753 | 0.1500 — much lower than the aggregate F1 of 0.8571. These | HISTORICAL |
| FAILURES.md | 6856 | F1 disclosure (0.1500 vs aggregate 0.8571) | HISTORICAL |
| FAILURES.md | 7045 | | M-005 Discovery F1 (DR-91) | 0.8571 ± 0.0635 | [0.7097, 0. | HISTORICAL |
| FAILURES.md | 7097 | - The headline F1=0.8571 is now F1=0.8571 ± 0.0635 (95% CI:  | HISTORICAL |
| FAILURES.md | 7384 | "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=50 | HISTORICAL |
| FAILURES.md | 7454 | # "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B= | HISTORICAL |
| FAILURES.md | 7524 | | M-005 Discovery F1 (DR-91) | 0.8571 | 0.0000 | 0.0000 | 0. | HISTORICAL |
| FAILURES.md | 7552 | same value (0.8571 for DR-91, 0.8333 for honest). | HISTORICAL |
| FAILURES.md | 8015 | | M-005 Discovery F1 | 0.8571 | 0.0000 | 0.0000 | STABLE (DE | HISTORICAL |
| FAILURES.md | 8348 | | M-005 Discovery F1 | 0.8571 | 0.7879 | ↓ (honest drop) | | HISTORICAL |
| FAILURES.md | 8358 | HC-006 (production F1=0.8571) is now ERODED (not SURVIVES) u | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 16 | 0.8571 to 0.7879. These are the honest, non-circular values. | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 70 | | Discovery F1 (shared, syn, DR-91) | 0.8571 | 0.7879 | | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 75 | | Aggregate F1 (DR-91) | 0.8571 | 0.7879 | | CURRENT |
| docs/MATCHING_SPECIFICATION.md | 23 | | synonym | Token + synonym map | 1.0000 | 0.8571 | | HISTORICAL |
| docs/MATCHING_SPECIFICATION.md | 28 | - **Discovery F1** (shared entities + synonyms): 0.8571 | HISTORICAL |
| docs/MEASUREMENT_HISTORY.md | 13 | | 242 | 0.8571 | Entity (shared + synonyms, proposal-only) | | HISTORICAL |
| docs/DISCOVERY_VS_RECOGNITION.md | 25 | - Discovery F1 = 0.8571 (shared entities + synonyms) | HISTORICAL |
| reports/bootstrap_statistics.md | 97 | numbers (F1=0.8571, etc.) must be updated to include bootstr | CURRENT |
| reports/repository_truth_check.md | 26 | | dr97_external_baselines.py | CURRENT | production_f1 defau | CURRENT |
| reports/repository_truth_check.md | 27 | | dr98_historical_recalibration.py | CURRENT | Historical cl | CURRENT |
| reports/repository_truth_check.md | 59 | - Current discovery F1 (shared, DR-91) = 0.7879 (was 0.8571, | CURRENT |
| reports/repository_truth_check.md | 69 | 4. dr97_external_baselines.py: production_f1 updated (0.8571 | CURRENT |
| reports/repository_truth_check.md | 70 | 5. dr97 print statements: all 0.8571 references replaced wit | CURRENT |
| reports/historical_metric_inventory.md | 92 | | reports/repository_truth_check.md | 26 | - PRELIMINARY_MEA | CURRENT |
| reports/historical_metric_inventory.md | 93 | | reports/repository_truth_check.md | 29 | - dr98_historical | CURRENT |
| reports/historical_metric_inventory.md | 268 | ## 0.8571 | CURRENT |
| reports/historical_metric_inventory.md | 273 | | FAILURES.md | 5685 | 3. **Proposal-only F1 = 0.8571 (share | CURRENT |
| reports/historical_metric_inventory.md | 274 | | FAILURES.md | 5777 | | synonym | 1.0000 | 0.8571 | | HISTO | CURRENT |
| reports/historical_metric_inventory.md | 275 | | FAILURES.md | 5794 | Discovery F1 = 0.8571 | HISTORICAL | | CURRENT |
| reports/historical_metric_inventory.md | 276 | | FAILURES.md | 5822 | - The honest Discovery F1 (shared ent | CURRENT |
| reports/historical_metric_inventory.md | 277 | | FAILURES.md | 6700 | - HC-006 (production F1=0.8571) SURVI | CURRENT |
| reports/historical_metric_inventory.md | 278 | | FAILURES.md | 6712 | aggregate F1=0.8571 in PRELIMINARY —  | CURRENT |
| reports/historical_metric_inventory.md | 279 | | FAILURES.md | 6750 | production F1=0.8571 in PRELIMINARY_M | CURRENT |
| reports/historical_metric_inventory.md | 280 | | FAILURES.md | 6753 | 0.1500 — much lower than the aggregat | CURRENT |
| reports/historical_metric_inventory.md | 281 | | FAILURES.md | 6856 | F1 disclosure (0.1500 vs aggregate 0. | CURRENT |
| reports/historical_metric_inventory.md | 282 | | FAILURES.md | 7045 | | M-005 Discovery F1 (DR-91) | 0.8571 | CURRENT |
| reports/historical_metric_inventory.md | 283 | | FAILURES.md | 7097 | - The headline F1=0.8571 is now F1=0. | CURRENT |
| reports/historical_metric_inventory.md | 284 | | FAILURES.md | 7384 | "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7 | CURRENT |
| reports/historical_metric_inventory.md | 285 | | FAILURES.md | 7454 | # "M-005 = 0.8571 ± 0.0635 (95% CI: 0 | CURRENT |
| reports/historical_metric_inventory.md | 286 | | FAILURES.md | 7524 | | M-005 Discovery F1 (DR-91) | 0.8571 | CURRENT |
| reports/historical_metric_inventory.md | 287 | | FAILURES.md | 7552 | same value (0.8571 for DR-91, 0.8333  | CURRENT |
| reports/historical_metric_inventory.md | 288 | | FAILURES.md | 8015 | | M-005 Discovery F1 | 0.8571 | 0.000 | CURRENT |
| reports/historical_metric_inventory.md | 289 | | FAILURES.md | 8348 | | M-005 Discovery F1 | 0.8571 | 0.787 | CURRENT |
| reports/historical_metric_inventory.md | 290 | | FAILURES.md | 8358 | HC-006 (production F1=0.8571) is now  | CURRENT |
| reports/historical_metric_inventory.md | 291 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 16 | 0.8571 to 0.7879 | CURRENT |
| reports/historical_metric_inventory.md | 292 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 70 | | Discovery F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 293 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 75 | | Aggregate F1 ( | CURRENT |
| reports/historical_metric_inventory.md | 294 | | docs/MATCHING_SPECIFICATION.md | 23 | | synonym | Token +  | CURRENT |
| reports/historical_metric_inventory.md | 295 | | docs/MATCHING_SPECIFICATION.md | 28 | - **Discovery F1** ( | CURRENT |
| reports/historical_metric_inventory.md | 296 | | docs/MEASUREMENT_HISTORY.md | 13 | | 242 | 0.8571 | Entity | CURRENT |
| reports/historical_metric_inventory.md | 297 | | docs/DISCOVERY_VS_RECOGNITION.md | 25 | - Discovery F1 = 0 | CURRENT |
| reports/historical_metric_inventory.md | 298 | | reports/bootstrap_statistics.md | 97 | numbers (F1=0.8571, | CURRENT |
| reports/historical_metric_inventory.md | 299 | | reports/repository_truth_check.md | 26 | - PRELIMINARY_MEA | CURRENT |
| reports/historical_metric_inventory.md | 300 | | reports/repository_truth_check.md | 28 | - dr97_external_b | CURRENT |
| reports/historical_metric_inventory.md | 301 | | reports/repository_truth_check.md | 29 | - dr98_historical | CURRENT |
| reports/historical_metric_inventory.md | 302 | | reports/repository_truth_check.md | 36 | 2. dr97_external_ | CURRENT |
| reports/historical_metric_inventory.md | 303 | | reports/repository_truth_check.md | 43 | 1. **PRELIMINARY_ | CURRENT |
| reports/historical_metric_inventory.md | 304 | | reports/repository_truth_check.md | 47 | 3. **dr97_externa | CURRENT |
| reports/historical_metric_inventory.md | 305 | | reports/repository_truth_check.md | 70 | 3. **'Discovery F | CURRENT |
| reports/historical_metric_inventory.md | 306 | | reports/repository_truth_check.md | 94 | - Update dr97 pro | CURRENT |
| reports/historical_metric_inventory.md | 307 | | reports/historical_metric_inventory.md | 134 | ## 0.8571 | | CURRENT |
| reports/historical_metric_inventory.md | 308 | | reports/historical_metric_inventory.md | 139 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 309 | | reports/historical_metric_inventory.md | 140 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 310 | | reports/historical_metric_inventory.md | 141 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 312 | | reports/historical_metric_inventory.md | 143 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 313 | | reports/historical_metric_inventory.md | 144 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 314 | | reports/historical_metric_inventory.md | 145 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 315 | | reports/historical_metric_inventory.md | 146 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 316 | | reports/historical_metric_inventory.md | 147 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 317 | | reports/historical_metric_inventory.md | 148 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 318 | | reports/historical_metric_inventory.md | 149 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 319 | | reports/historical_metric_inventory.md | 150 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 320 | | reports/historical_metric_inventory.md | 151 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 321 | | reports/historical_metric_inventory.md | 152 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 322 | | reports/historical_metric_inventory.md | 153 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 323 | | reports/historical_metric_inventory.md | 154 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 324 | | reports/historical_metric_inventory.md | 155 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 325 | | reports/historical_metric_inventory.md | 156 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 327 | | reports/historical_metric_inventory.md | 158 | | PRELIMINA | CURRENT |
| reports/historical_metric_inventory.md | 329 | | reports/historical_metric_inventory.md | 160 | | PRELIMINA | CURRENT |
| reports/historical_metric_inventory.md | 330 | | reports/historical_metric_inventory.md | 161 | | PRELIMINA | CURRENT |
| reports/historical_metric_inventory.md | 333 | | reports/historical_metric_inventory.md | 164 | | docs/MEAS | CURRENT |
| reports/historical_metric_inventory.md | 334 | | reports/historical_metric_inventory.md | 165 | | docs/DISC | CURRENT |
| reports/historical_metric_inventory.md | 335 | | reports/historical_metric_inventory.md | 166 | | reports/b | CURRENT |
| reports/historical_metric_inventory.md | 336 | | reports/historical_metric_inventory.md | 167 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 337 | | reports/historical_metric_inventory.md | 168 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 338 | | reports/historical_metric_inventory.md | 169 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 339 | | reports/historical_metric_inventory.md | 170 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 343 | | reports/historical_metric_inventory.md | 176 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 344 | | reports/historical_metric_inventory.md | 177 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 345 | | reports/historical_metric_inventory.md | 178 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 347 | | reports/historical_metric_inventory.md | 180 | | reports/e | CURRENT |
| reports/historical_metric_inventory.md | 348 | | reports/historical_metric_inventory.md | 181 | | reports/e | CURRENT |
| reports/historical_metric_inventory.md | 349 | | reports/historical_metric_inventory.md | 182 | | reports/e | CURRENT |
| reports/historical_metric_inventory.md | 350 | | reports/historical_metric_inventory.md | 183 | | reports/e | CURRENT |
| reports/historical_metric_inventory.md | 352 | | reports/historical_metric_inventory.md | 185 | | reports/e | CURRENT |
| reports/historical_metric_inventory.md | 353 | | reports/historical_metric_inventory.md | 186 | | reports/h | CURRENT |
| reports/historical_metric_inventory.md | 355 | | reports/historical_metric_inventory.md | 188 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 356 | | reports/historical_metric_inventory.md | 189 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 357 | | reports/historical_metric_inventory.md | 190 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 358 | | reports/historical_metric_inventory.md | 191 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 359 | | reports/historical_metric_inventory.md | 192 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 360 | | reports/historical_metric_inventory.md | 193 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 361 | | reports/historical_metric_inventory.md | 194 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 362 | | reports/historical_metric_inventory.md | 195 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 363 | | reports/historical_metric_inventory.md | 196 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 364 | | reports/historical_metric_inventory.md | 197 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 365 | | reports/historical_metric_inventory.md | 198 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 366 | | reports/historical_metric_inventory.md | 199 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 367 | | reports/historical_metric_inventory.md | 200 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 368 | | reports/historical_metric_inventory.md | 201 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 369 | | reports/historical_metric_inventory.md | 202 | | reports/r | CURRENT |
| reports/historical_metric_inventory.md | 370 | | reports/historical_metric_inventory.md | 203 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 371 | | reports/historical_metric_inventory.md | 204 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 372 | | reports/historical_metric_inventory.md | 205 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 373 | | reports/historical_metric_inventory.md | 206 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 374 | | reports/historical_metric_inventory.md | 207 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 375 | | reports/historical_metric_inventory.md | 208 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 376 | | reports/historical_metric_inventory.md | 209 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 377 | | reports/historical_metric_inventory.md | 210 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 378 | | reports/historical_metric_inventory.md | 211 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 379 | | reports/historical_metric_inventory.md | 212 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 380 | | reports/historical_metric_inventory.md | 213 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 381 | | reports/historical_metric_inventory.md | 214 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 382 | | reports/historical_metric_inventory.md | 215 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 386 | | reports/historical_metric_inventory.md | 219 | | tests/tes | CURRENT |
| reports/historical_metric_inventory.md | 393 | | reports/historical_metric_inventory.md | 226 | | audit/mea | CURRENT |
| reports/historical_metric_inventory.md | 405 | | reports/historical_metric_inventory.md | 239 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 412 | | reports/historical_metric_inventory.md | 250 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 413 | | reports/historical_metric_inventory.md | 251 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 414 | | reports/historical_metric_inventory.md | 252 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 417 | | reports/historical_metric_inventory.md | 255 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 419 | | reports/historical_metric_inventory.md | 257 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 420 | | reports/historical_metric_inventory.md | 258 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 422 | | reports/historical_metric_inventory.md | 260 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 423 | | reports/historical_metric_inventory.md | 261 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 424 | | reports/historical_metric_inventory.md | 262 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 431 | | reports/historical_metric_inventory.md | 269 | | programs/ | CURRENT |
| reports/historical_metric_inventory.md | 432 | | reports/historical_metric_inventory.md | 270 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 433 | | reports/historical_metric_inventory.md | 271 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 435 | | reports/historical_metric_inventory.md | 273 | | reports/f | CURRENT |
| reports/historical_metric_inventory.md | 436 | | reports/historical_metric_inventory.md | 283 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 442 | | reports/repeatability_m4.md | 35 | | M-005 | Discovery F1  | CURRENT |
| reports/historical_metric_inventory.md | 443 | | reports/repeatability_m4.md | 36 | | M-008 | FP floor (syn | CURRENT |
| reports/historical_metric_inventory.md | 446 | | reports/historical_recalibration.md | 53 | DR-91-conventio | CURRENT |
| reports/historical_metric_inventory.md | 447 | | reports/failure_envelope_m7.json | 196 | "F1 drops from 0. | CURRENT |
| reports/historical_metric_inventory.md | 448 | | reports/failure_envelope_m7.json | 446 | "F1 = 0.8571 (sam | CURRENT |
| reports/historical_metric_inventory.md | 449 | | reports/failure_envelope_m7.json | 570 | "Production (0.85 | CURRENT |
| reports/historical_metric_inventory.md | 450 | | reports/failure_envelope_m7.json | 777 | "The gen5 F1 (0.9 | CURRENT |
| reports/historical_metric_inventory.md | 452 | | reports/historical_recalibration.json | 133 | "claimed_f1" | CURRENT |
| reports/historical_metric_inventory.md | 453 | | reports/historical_recalibration.json | 143 | "delta_vs_cl | CURRENT |
| reports/historical_metric_inventory.md | 454 | | reports/repeatability_m4.json | 37 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 455 | | reports/repeatability_m4.json | 38 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 456 | | reports/repeatability_m4.json | 39 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 457 | | reports/repeatability_m4.json | 40 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 458 | | reports/repeatability_m4.json | 41 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 459 | | reports/repeatability_m4.json | 42 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 460 | | reports/repeatability_m4.json | 43 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 461 | | reports/repeatability_m4.json | 44 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 462 | | reports/repeatability_m4.json | 45 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 463 | | reports/repeatability_m4.json | 46 | 0.8571 | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 464 | | reports/repeatability_m4.json | 48 | "mean": 0.8571, | BUG | CURRENT |
| reports/historical_metric_inventory.md | 465 | | reports/repeatability_m4.json | 51 | "min": 0.8571, | BUG  | CURRENT |
| reports/historical_metric_inventory.md | 466 | | reports/repeatability_m4.json | 52 | "max": 0.8571, | BUG  | CURRENT |
| reports/historical_metric_inventory.md | 467 | | reports/repeatability_m4.json | 80 | 0.8571, | BUG | | CURRENT |
| reports/historical_metric_inventory.md | 468 | | reports/repeatability_m4.json | 90 | "min": 0.8571, | BUG  | CURRENT |
| reports/historical_metric_inventory.md | 469 | | tests/test_bootstrap_statistics.py | 187 | point_estimate= | CURRENT |
| reports/historical_metric_inventory.md | 470 | | tests/test_bootstrap_statistics.py | 194 | assert "0.8571" | CURRENT |
| reports/historical_metric_inventory.md | 471 | | tests/test_bootstrap_statistics.py | 360 | Note: was 0.857 | CURRENT |
| reports/historical_metric_inventory.md | 472 | | tests/test_measurement_provenance.py | 49 | value=0.8571,  | CURRENT |
| reports/historical_metric_inventory.md | 473 | | tests/test_measurement_provenance.py | 58 | assert d["valu | CURRENT |
| reports/historical_metric_inventory.md | 474 | | tests/test_measurement_provenance.py | 67 | value=0.8571,  | CURRENT |
| reports/historical_metric_inventory.md | 475 | | tests/test_measurement_provenance.py | 76 | assert "0.8571 | CURRENT |
| reports/historical_metric_inventory.md | 476 | | tests/test_measurement_provenance.py | 156 | value=0.8571, | CURRENT |
| reports/historical_metric_inventory.md | 477 | | tests/test_measurement_provenance.py | 160 | assert sv.val | CURRENT |
| reports/historical_metric_inventory.md | 478 | | tests/test_measurement_provenance.py | 207 | return 0.8571 | CURRENT |
| reports/historical_metric_inventory.md | 479 | | tests/test_measurement_provenance.py | 211 | assert result | CURRENT |
| reports/historical_metric_inventory.md | 480 | | tests/test_measurement_provenance.py | 291 | assert is_nak | CURRENT |
| reports/historical_metric_inventory.md | 481 | | tests/test_measurement_provenance.py | 335 | return 0.8571 | CURRENT |
| reports/historical_metric_inventory.md | 482 | | tests/test_measurement_provenance.py | 340 | assert result | CURRENT |
| reports/historical_metric_inventory.md | 483 | | tests/test_measurement_provenance.py | 341 | assert result | CURRENT |
| reports/historical_metric_inventory.md | 484 | | tests/test_dr101_final_verdict_eligibility.py | 30 | "prod | CURRENT |
| reports/historical_metric_inventory.md | 485 | | tests/test_dr98_historical_recalibration.py | 154 | # (was | CURRENT |
| reports/historical_metric_inventory.md | 486 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 487 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 488 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 489 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 490 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/historical_metric_inventory.md | 492 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 493 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 498 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 499 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 500 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 501 | | programs/A_metrology/measurement_verification_sprint.py |  | CURRENT |
| reports/historical_metric_inventory.md | 502 | | programs/A_metrology/bootstrap_statistics.py | 1300 | line | CURRENT |
| reports/historical_metric_inventory.md | 503 | | programs/A_metrology/measurement_provenance.py | 43 | "M-0 | CURRENT |
| reports/historical_metric_inventory.md | 504 | | programs/A_metrology/measurement_provenance.py | 62 | # "M | CURRENT |
| reports/historical_metric_inventory.md | 505 | | programs/A_metrology/measurement_provenance.py | 68 | valu | CURRENT |
| reports/historical_metric_inventory.md | 506 | | programs/A_metrology/measurement_provenance.py | 172 | """ | CURRENT |
| reports/historical_metric_inventory.md | 507 | | programs/A_metrology/measurement_provenance.py | 186 | """ | CURRENT |
| reports/historical_metric_inventory.md | 508 | | programs/A_metrology/measurement_provenance.py | 393 | "M- | CURRENT |
| reports/historical_metric_inventory.md | 509 | | programs/A_metrology/measurement_provenance.py | 400 | """ | CURRENT |
| reports/historical_metric_inventory.md | 510 | | programs/A_metrology/measurement_provenance.py | 443 | val | CURRENT |
| reports/historical_metric_inventory.md | 511 | | programs/A_metrology/measurement_provenance.py | 494 | ret | CURRENT |
| reports/historical_metric_inventory.md | 512 | | programs/A_metrology/measurement_provenance.py | 519 | pri | CURRENT |
| reports/historical_metric_inventory.md | 513 | | programs/A_metrology/failure_envelope_m7.py | 311 | "F1 dr | CURRENT |
| reports/historical_metric_inventory.md | 514 | | programs/A_metrology/failure_envelope_m7.py | 435 | "F1 =  | CURRENT |
| reports/historical_metric_inventory.md | 515 | | programs/A_metrology/failure_envelope_m7.py | 493 | "Produ | CURRENT |
| reports/historical_metric_inventory.md | 516 | | programs/A_metrology/failure_envelope_m7.py | 592 | "The g | CURRENT |
| reports/historical_metric_inventory.md | 517 | | programs/A_metrology/MeasurementEngineSpecification.md | 2 | CURRENT |
| reports/historical_metric_inventory.md | 518 | | programs/A_metrology/MeasurementEngineSpecification.md | 3 | CURRENT |
| reports/historical_metric_inventory.md | 519 | | programs/A_metrology/MeasurementEngineSpecification.md | 4 | CURRENT |
| reports/historical_metric_inventory.md | 520 | | programs/A_metrology/MeasurementEngineSpecification.md | 4 | CURRENT |
| reports/historical_metric_inventory.md | 521 | | programs/A_metrology/MeasurementEngineSpecification.md | 8 | CURRENT |
| reports/historical_metric_inventory.md | 522 | | programs/A_metrology/MeasurementEngineSpecification.md | 8 | CURRENT |
| reports/historical_metric_inventory.md | 523 | | reports/failure_envelopes/M-005.md | 27 | - F1 drops from  | CURRENT |
| reports/historical_metric_inventory.md | 524 | | reports/failure_envelopes/M-015.md | 31 | - Production (0. | CURRENT |
| reports/historical_metric_inventory.md | 525 | | reports/failure_envelopes/M-105.md | 23 | - The gen5 F1 (0 | CURRENT |
| reports/historical_metric_inventory.md | 526 | | reports/failure_envelopes/M-012.md | 24 | - F1 = 0.8571 (s | CURRENT |
| reports/historical_metric_inventory.md | 536 | | FAILURES.md | 5777 | | synonym | 1.0000 | 0.8571 | | HISTO | CURRENT |
| reports/historical_metric_inventory.md | 574 | | docs/MATCHING_SPECIFICATION.md | 23 | | synonym | Token +  | CURRENT |
| reports/historical_metric_inventory.md | 608 | | reports/historical_metric_inventory.md | 140 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 617 | | reports/historical_metric_inventory.md | 283 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 771 | | reports/repeatability_m4.md | 35 | | M-005 | Discovery F1  | CURRENT |
| reports/historical_metric_inventory.md | 772 | | reports/repeatability_m4.md | 36 | | M-008 | FP floor (syn | CURRENT |
| reports/historical_metric_inventory.md | 831 | | audit/measurement_integrity/dr98_historical_recalibration. | CURRENT |
| reports/repeatability_m4.md | 35 | | M-005 | Discovery F1 (DR-91, shared, syn) | 0.8571 | 0.000 | CURRENT |
| reports/repeatability_m4.md | 36 | | M-008 | FP floor (synonym) | 0.9595 | 0.0405 | 0.0422 | 0. | CURRENT |
| reports/repeatability_m4.md | 60 | - **M-005** (Discovery F1 (DR-91, shared, syn)): DETERMINIST | CURRENT |
| reports/historical_recalibration.md | 30 | | HC-006 | 243 | Proposal-only F1 (shared entities + synonym | CURRENT |
| reports/historical_recalibration.md | 53 | DR-91-convention F1. This means the production F1=0.8571 rep | CURRENT |
| reports/failure_envelope_m7.json | 196 | "F1 drops from 0.8571 to 0.5714 when snippets truncated (M6) | CURRENT |
| reports/failure_envelope_m7.json | 446 | "F1 = 0.8571 (same as M-005)", | CURRENT |
| reports/failure_envelope_m7.json | 570 | "Production (0.8571) beats this by \u0394=+0.76 \u2014 but c | CURRENT |
| reports/failure_envelope_m7.json | 777 | "The gen5 F1 (0.9375) is DIFFERENT from M-005 (0.8571) \u201 | CURRENT |
| reports/claim_traceability.md | 92 | ## Discovery F1 = 0.8571 (HISTORICAL) | CURRENT |
| reports/claim_traceability.md | 104 | - **Manual links:** dr98 hardcodes 0.8571 as claimed_f1 — th | CURRENT |
| reports/honest_scoreboard.md | 54 | | M-005 Discovery F1 (shared, DR-91) | 0.7879 | ± 0.0809 | [ | CURRENT |
| reports/historical_recalibration.json | 133 | "claimed_f1": 0.8571, | CURRENT |
| reports/historical_recalibration.json | 143 | "delta_vs_claimed_strict": -0.8571, | CURRENT |
| reports/repeatability_m4.json | 37 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 38 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 39 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 40 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 41 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 42 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 43 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 44 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 45 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 46 | 0.8571 | CURRENT |
| reports/repeatability_m4.json | 48 | "mean": 0.8571, | CURRENT |
| reports/repeatability_m4.json | 51 | "min": 0.8571, | CURRENT |
| reports/repeatability_m4.json | 52 | "max": 0.8571, | CURRENT |
| reports/repeatability_m4.json | 80 | 0.8571, | CURRENT |
| reports/repeatability_m4.json | 90 | "min": 0.8571, | CURRENT |
| reports/public_claim_inventory.md | 564 | | f1_value | FAILURES.md | 5685 | 3. **Proposal-only F1 = 0. | CURRENT |
| reports/public_claim_inventory.md | 568 | | f1_value | FAILURES.md | 5794 | Discovery F1 = 0.8571 | HI | CURRENT |
| reports/public_claim_inventory.md | 574 | | f1_value | FAILURES.md | 6700 | - HC-006 (production F1=0. | CURRENT |
| reports/public_claim_inventory.md | 576 | | f1_value | FAILURES.md | 6712 | aggregate F1=0.8571 in PRE | CURRENT |
| reports/public_claim_inventory.md | 577 | | f1_value | FAILURES.md | 6750 | production F1=0.8571 in PR | CURRENT |
| reports/public_claim_inventory.md | 580 | | f1_value | FAILURES.md | 7097 | - The headline F1=0.8571 i | CURRENT |
| reports/public_claim_inventory.md | 585 | | f1_value | FAILURES.md | 8358 | HC-006 (production F1=0.85 | CURRENT |
| reports/public_claim_inventory.md | 604 | | f1_value | docs/DISCOVERY_VS_RECOGNITION.md | 25 | - Disco | CURRENT |
| reports/public_claim_inventory.md | 609 | | f1_value | reports/bootstrap_statistics.md | 97 | numbers  | CURRENT |
| reports/public_claim_inventory.md | 690 | | f1_value | reports/historical_metric_inventory.md | 273 |  | CURRENT |
| reports/public_claim_inventory.md | 691 | | f1_value | reports/historical_metric_inventory.md | 275 |  | CURRENT |
| reports/public_claim_inventory.md | 692 | | f1_value | reports/historical_metric_inventory.md | 277 |  | CURRENT |
| reports/public_claim_inventory.md | 693 | | f1_value | reports/historical_metric_inventory.md | 278 |  | CURRENT |
| reports/public_claim_inventory.md | 694 | | f1_value | reports/historical_metric_inventory.md | 279 |  | CURRENT |
| reports/public_claim_inventory.md | 695 | | f1_value | reports/historical_metric_inventory.md | 283 |  | CURRENT |
| reports/public_claim_inventory.md | 696 | | f1_value | reports/historical_metric_inventory.md | 290 |  | CURRENT |
| reports/public_claim_inventory.md | 698 | | f1_value | reports/historical_metric_inventory.md | 298 |  | CURRENT |
| reports/public_claim_inventory.md | 719 | | f1_value | reports/historical_metric_inventory.md | 448 |  | CURRENT |
| reports/public_claim_inventory.md | 730 | | f1_value | reports/historical_metric_inventory.md | 526 |  | CURRENT |
| reports/public_claim_inventory.md | 748 | | f1_value | reports/historical_recalibration.md | 53 | DR-9 | CURRENT |
| reports/public_claim_inventory.md | 749 | | f1_value | reports/failure_envelope_m7.json | 446 | "F1 =  | CURRENT |
| reports/public_claim_inventory.md | 776 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 784 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 786 | | f1_value | audit/measurement_integrity/dr98_historical_rec | CURRENT |
| reports/public_claim_inventory.md | 813 | | f1_value | programs/A_metrology/measurement_verification_s | CURRENT |
| reports/public_claim_inventory.md | 824 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| reports/public_claim_inventory.md | 833 | | f1_value | programs/A_metrology/bootstrap_statistics.py |  | CURRENT |
| reports/public_claim_inventory.md | 834 | | f1_value | programs/A_metrology/failure_envelope_m7.py | 4 | CURRENT |
| reports/public_claim_inventory.md | 849 | | f1_value | programs/A_metrology/MeasurementEngineSpecifica | CURRENT |
| reports/public_claim_inventory.md | 857 | | f1_value | reports/failure_envelopes/M-012.md | 24 | - F1  | CURRENT |
| reports/public_claim_inventory.md | 4804 | | status_claim | reports/historical_metric_inventory.md | 27 | CURRENT |
| reports/public_claim_inventory.md | 4805 | | status_claim | reports/historical_metric_inventory.md | 27 | CURRENT |
| reports/public_claim_inventory.md | 4806 | | status_claim | reports/historical_metric_inventory.md | 27 | CURRENT |
| reports/public_claim_inventory.md | 4808 | | status_claim | reports/historical_metric_inventory.md | 27 | CURRENT |
| reports/public_claim_inventory.md | 4809 | | status_claim | reports/historical_metric_inventory.md | 27 | CURRENT |
| reports/public_claim_inventory.md | 4810 | | status_claim | reports/historical_metric_inventory.md | 27 | CURRENT |
| reports/public_claim_inventory.md | 4813 | | status_claim | reports/historical_metric_inventory.md | 28 | CURRENT |
| reports/public_claim_inventory.md | 4814 | | status_claim | reports/historical_metric_inventory.md | 28 | CURRENT |
| reports/public_claim_inventory.md | 4815 | | status_claim | reports/historical_metric_inventory.md | 28 | CURRENT |
| reports/public_claim_inventory.md | 4816 | | status_claim | reports/historical_metric_inventory.md | 28 | CURRENT |
| reports/public_claim_inventory.md | 4817 | | status_claim | reports/historical_metric_inventory.md | 28 | CURRENT |
| reports/public_claim_inventory.md | 4818 | | status_claim | reports/historical_metric_inventory.md | 28 | CURRENT |
| reports/public_claim_inventory.md | 4819 | | status_claim | reports/historical_metric_inventory.md | 28 | CURRENT |
| reports/public_claim_inventory.md | 4820 | | status_claim | reports/historical_metric_inventory.md | 28 | CURRENT |
| reports/public_claim_inventory.md | 4821 | | status_claim | reports/historical_metric_inventory.md | 29 | CURRENT |
| reports/public_claim_inventory.md | 4854 | | status_claim | reports/historical_metric_inventory.md | 44 | CURRENT |
| reports/public_claim_inventory.md | 4864 | | status_claim | reports/historical_metric_inventory.md | 52 | CURRENT |
| reports/public_claim_inventory.md | 4868 | | status_claim | reports/historical_metric_inventory.md | 53 | CURRENT |
| reports/public_claim_inventory.md | 10656 | | status_claim | programs/A_metrology/final_repository_verif | CURRENT |
| tests/test_bootstrap_statistics.py | 187 | point_estimate=0.8571, bootstrap_mean=0.85, bootstrap_std=0. | TEST |
| tests/test_bootstrap_statistics.py | 194 | assert "0.8571" in s | TEST |
| tests/test_bootstrap_statistics.py | 360 | Note: was 0.8571 before cycle 270 (circular synonyms removed | TEST |
| tests/test_measurement_provenance.py | 49 | value=0.8571, metric_id="M-005", metric_name="Discovery F1", | TEST |
| tests/test_measurement_provenance.py | 58 | assert d["value"] == 0.8571 | TEST |
| tests/test_measurement_provenance.py | 67 | value=0.8571, metric_id="M-005", metric_name="Discovery F1", | TEST |
| tests/test_measurement_provenance.py | 76 | assert "0.8571" in s | TEST |
| tests/test_measurement_provenance.py | 156 | value=0.8571, metric_id="M-005", metric_name="Discovery F1", | TEST |
| tests/test_measurement_provenance.py | 160 | assert sv.value == 0.8571 | TEST |
| tests/test_measurement_provenance.py | 207 | return 0.8571 | TEST |
| tests/test_measurement_provenance.py | 211 | assert result.value == 0.8571 | TEST |
| tests/test_measurement_provenance.py | 291 | assert is_naked_number(0.8571) is True | TEST |
| tests/test_measurement_provenance.py | 335 | return 0.8571 | TEST |
| tests/test_measurement_provenance.py | 340 | assert result.ci_95_lower < 0.8571 | TEST |
| tests/test_measurement_provenance.py | 341 | assert result.ci_95_upper > 0.8571 | TEST |
| tests/test_dr101_final_verdict_eligibility.py | 30 | "production_f1_strict": 0.0, "production_f1_lenient": 0.8571 | TEST |
| tests/test_dr98_historical_recalibration.py | 154 | # (was 0.8571 with circular synonyms). Delta = -0.069 → EROD | TEST |
| audit/measurement_integrity/dr98_historical_recalibration.py | 17 | - DR-91 audit: F1=0.8571 (proposal-only, shared/synonym) | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 236 | claimed_f1=0.8571, | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 267 | historical headline numbers (0.8571, 1.0000). It assumes pre | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 449 | print(f"  - HC-006 (production F1=0.8571) SURVIVES at {hc006 | HISTORICAL |
| audit/measurement_integrity/dr98_historical_recalibration.py | 581 | lines.append("DR-91-convention F1. This means the production | HISTORICAL |
| audit/measurement_integrity/dr101_final_verdict_eligibility.py | 292 | lines.append(f"- Aggregate (PRELIMINARY): {gate_a.get('produ | CHECK |
| programs/A_metrology/measurement_verification_sprint.py | 244 | "0.8571": "Old discovery F1 shared/synonym (circular, cycle  | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 438 | "M-005": ("Discovery F1 (shared, DR-91)", 0.8571), | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 511 | lines.append("- PRELIMINARY_MEASUREMENT_VERDICT.md: **NO** — | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 513 | lines.append("- dr97_external_baselines.py: **NO** — hardcod | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 514 | lines.append("- dr98_historical_recalibration.py: **NO** — h | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 521 | lines.append("2. dr97_external_baselines.py: update producti | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 530 | lines.append("1. **PRELIMINARY_MEASUREMENT_VERDICT.md**: rep | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 534 | lines.append("3. **dr97_external_baselines.py**: uses produc | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 561 | lines.append("3. **'Discovery F1 = 0.8571'** — this was infl | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 585 | lines.append("- Update dr97 production_f1 default from 0.857 | CURRENT |
| programs/A_metrology/final_repository_verification.py | 210 | "claim": "Discovery F1 = 0.8571 (HISTORICAL)", | CHECK |
| programs/A_metrology/final_repository_verification.py | 220 | "manual_links": "dr98 hardcodes 0.8571 as claimed_f1 — this  | CHECK |
| programs/A_metrology/final_repository_verification.py | 251 | values_to_check = ["0.5714", "0.7879", "0.9189", "0.8571", " | CHECK |
| programs/A_metrology/final_repository_verification.py | 505 | "No stale 0.8571 remains in dr97 (verified: 0 occurrences)", | CHECK |
| programs/A_metrology/bootstrap_statistics.py | 1300 | lines.append("numbers (F1=0.8571, etc.) must be updated to i | CURRENT |
| programs/A_metrology/measurement_provenance.py | 43 | "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=50 | CURRENT |
| programs/A_metrology/measurement_provenance.py | 62 | # "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B= | CURRENT |
| programs/A_metrology/measurement_provenance.py | 68 | value=0.8571, | CURRENT |
| programs/A_metrology/measurement_provenance.py | 172 | """Canonical string: 'M-005 = 0.8571 ± 0.0635 (95% CI: 0.709 | CURRENT |
| programs/A_metrology/measurement_provenance.py | 186 | """Short string: 'M-005 = 0.8571 ± 0.0635 [0.7097, 0.9474]'" | CURRENT |
| programs/A_metrology/measurement_provenance.py | 393 | "M-005 = 0.8571 ± 0.0635 (95% CI: 0.7097, 0.9474; N=20, B=50 | CURRENT |
| programs/A_metrology/measurement_provenance.py | 400 | """Short format: 'M-005 = 0.8571 ± 0.0635 [0.7097, 0.9474]'" | CURRENT |
| programs/A_metrology/measurement_provenance.py | 443 | value=0.8571, | CURRENT |
| programs/A_metrology/measurement_provenance.py | 494 | return 0.8571 | CURRENT |
| programs/A_metrology/measurement_provenance.py | 519 | print(f"  is_naked_number(0.8571) = {is_naked_number(0.8571) | CURRENT |
| programs/A_metrology/failure_envelope_m7.py | 311 | "F1 drops from 0.8571 to 0.5714 when snippets truncated (M6) | CURRENT |
| programs/A_metrology/failure_envelope_m7.py | 435 | "F1 = 0.8571 (same as M-005)", | CURRENT |
| programs/A_metrology/failure_envelope_m7.py | 493 | "Production (0.8571) beats this by Δ=+0.76 — but comparison  | CURRENT |
| programs/A_metrology/failure_envelope_m7.py | 592 | "The gen5 F1 (0.9375) is DIFFERENT from M-005 (0.8571) — not | CURRENT |
| programs/A_metrology/MeasurementEngineSpecification.md | 205 | - Returns 0.8571 (current value) under DR-91 formula | CHECK |
| programs/A_metrology/MeasurementEngineSpecification.md | 383 | - Returns 0.8571 for current gold | CHECK |
| programs/A_metrology/MeasurementEngineSpecification.md | 406 | - Returns 0.8333 for current gold (lower than M-012's 0.8571 | CHECK |
| programs/A_metrology/MeasurementEngineSpecification.md | 472 | - Production (0.8571) beats this by Δ=+0.76 — but the compar | CHECK |
| programs/A_metrology/MeasurementEngineSpecification.md | 805 | (F-143, F-145). The honest F1 is 0.8571 (DR-91 convention) o | CHECK |
| programs/A_metrology/MeasurementEngineSpecification.md | 818 | F1=0.8571). The gen5 metric measures connection-finding (ret | CHECK |
| reports/failure_envelopes/M-005.md | 27 | - F1 drops from 0.8571 to 0.5714 when snippets truncated (M6 | CURRENT |
| reports/failure_envelopes/M-015.md | 31 | - Production (0.8571) beats this by Δ=+0.76 — but comparison | CURRENT |
| reports/failure_envelopes/M-105.md | 23 | - The gen5 F1 (0.9375) is DIFFERENT from M-005 (0.8571) — no | CURRENT |
| reports/failure_envelopes/M-012.md | 24 | - F1 = 0.8571 (same as M-005) | CURRENT |

## 0.6500

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 8351 | | M-010 Per-proposal F1 | 0.7500 | 0.6500 | ↓ (honest, still | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 20 | value: 0.6500 (was 0.7500 with circular synonyms, 0.10-0.20  | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 41 | | Per-proposal F1 (ALL shared, honest) | 0.6500 ± 0.1081 | [ | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 44 | | BM25 recall@1 (lenient) | 0.6500 ± 0.1044 | [0.4500, 0.850 | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 74 | | Per-proposal F1 (ALL shared) | 0.7500 | 0.6500 | | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 114 | entities as candidates) is 0.6500. These measure different t | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 119 | - Per-proposal F1 = 0.6500: "of 20 gold bridges, 65% are mat | CURRENT |
| reports/bootstrap_statistics.md | 33 | | M-010 | Per-proposal F1 (honest, lenient, ALL shared) | 0. | CURRENT |
| reports/measurement_provenance_audit.md | 165 | - **Value:** 0.6500 ± 0.1081 (95% CI: 0.4500, 0.8500) | CURRENT |
| reports/sensitivity_m6.md | 60 | | M-010 | INPUT | drop_1_sentence | 0.6500 | 0.6500 | +0.000 | CURRENT |
| reports/sensitivity_m6.md | 61 | | M-010 | GOLD | drop_1_gold | 0.6500 | 0.6316 | -0.0184 | - | CURRENT |
| reports/sensitivity_m6.md | 62 | | M-010 | GOLD | drop_2_gold | 0.6500 | 0.6111 | -0.0389 | - | CURRENT |
| reports/sensitivity_m6.md | 63 | | M-010 | SYNONYM | remove_25pct_synonyms | 0.6500 | 0.6500  | CURRENT |
| reports/sensitivity_m6.md | 64 | | M-010 | SYNONYM | remove_50pct_synonyms | 0.6500 | 0.6500  | CURRENT |
| reports/claim_traceability.md | 47 | ## Per-proposal F1 = 0.6500 | CURRENT |
| reports/claim_traceability.md | 52 | reports/bootstrap_statistics.json (M-010: 0.6500 ± 0.1081) | CURRENT |
| reports/honest_scoreboard.md | 20 | | M-010 | 0.6500 ± 0.1081 | [0.4500, 0.8500] | 20 | 500 | B  | CURRENT |
| reports/honest_scoreboard.md | 57 | | M-010 Per-proposal F1 (ALL shared) | 0.6500 | ± 0.1081 | [ | CURRENT |
| reports/failure_envelope_m7.md | 47 | | M-010 | Per-proposal F1 (honest, lenient, ALL sh | 0.6500  | CURRENT |
| reports/public_claim_inventory.md | 588 | | f1_value | PRELIMINARY_MEASUREMENT_VERDICT.md | 119 | - Pe | CURRENT |
| reports/public_claim_inventory.md | 816 | | f1_value | programs/A_metrology/measurement_verification_s | CURRENT |
| reports/public_claim_inventory.md | 820 | | f1_value | programs/A_metrology/final_repository_verificat | CURRENT |
| programs/A_metrology/measurement_verification_sprint.py | 565 | lines.append("   Current honest F1 = 0.6500.") | CURRENT |
| programs/A_metrology/final_repository_verification.py | 168 | "claim": "Per-proposal F1 = 0.6500", | CHECK |
| programs/A_metrology/final_repository_verification.py | 172 | "reports/bootstrap_statistics.json (M-010: 0.6500 ± 0.1081)" | CHECK |
| programs/A_metrology/final_repository_verification.py | 251 | values_to_check = ["0.5714", "0.7879", "0.9189", "0.8571", " | CHECK |
| programs/A_metrology/MeasurementEngineSpecification.md | 436 | - Returns 0.6500 (lenient) — production beats this by Δ=+0.2 | CHECK |
| reports/failure_envelopes/M-010.md | 7 | - **Baseline value:** 0.6500 | CURRENT |

## 0.7647

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 8352 | | M-013 Aggregate F1 (honest) | 0.8333 | 0.7647 | ↓ (honest  | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 43 | | Aggregate F1 (honest) | 0.7647 ± 0.0875 | [0.5455, 0.8947] | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 76 | | Aggregate F1 (honest) | 0.8333 | 0.7647 | | CURRENT |
| reports/bootstrap_statistics.md | 36 | | M-013 | Aggregate F1 (honest) | 0.7647 ± 0.0875 | [0.5455, | CURRENT |
| reports/bootstrap_statistics.json | 218 | "point_estimate": 0.7647, | CURRENT |
| reports/measurement_provenance_audit.md | 213 | - **Value:** 0.7647 ± 0.0875 (95% CI: 0.5455, 0.8947) | CURRENT |
| reports/historical_recalibration.md | 29 | | HC-005 | 201 | Discovery F1 (the headline number, reported | CURRENT |
| reports/historical_recalibration.md | 30 | | HC-006 | 243 | Proposal-only F1 (shared entities + synonym | CURRENT |
| reports/sensitivity_m6.md | 53 | | M-013 | INPUT | drop_1_sentence | 0.7647 | 0.7647 | +0.000 | CURRENT |
| reports/sensitivity_m6.md | 54 | | M-013 | INPUT | truncate_75pct | 0.7647 | 0.5185 | -0.2462 | CURRENT |
| reports/sensitivity_m6.md | 55 | | M-013 | GOLD | drop_1_gold | 0.7647 | 0.7500 | -0.0147 | - | CURRENT |
| reports/sensitivity_m6.md | 56 | | M-013 | GOLD | drop_2_gold | 0.7647 | 0.7333 | -0.0314 | - | CURRENT |
| reports/sensitivity_m6.md | 57 | | M-013 | GOLD | rename_gold | 0.7647 | 0.7647 | +0.0000 | + | CURRENT |
| reports/sensitivity_m6.md | 58 | | M-013 | SYNONYM | remove_25pct_synonyms | 0.7647 | 0.7647  | CURRENT |
| reports/sensitivity_m6.md | 59 | | M-013 | SYNONYM | remove_50pct_synonyms | 0.7647 | 0.7647  | CURRENT |
| reports/sensitivity_m6.md | 92 | - **M-013 / INPUT/truncate_75pct**: Δ=-0.2462 (-0.3219). Bas | CURRENT |
| reports/failure_envelope_m7.json | 463 | "baseline_value": 0.7647, | CURRENT |
| reports/failure_envelope_m7.json | 478 | "baseline_value": 0.7647, | CURRENT |
| reports/honest_scoreboard.md | 23 | | M-013 | 0.7647 ± 0.0875 | [0.5455, 0.8947] | 20 | 500 | B  | CURRENT |
| reports/honest_scoreboard.md | 58 | | M-013 Aggregate F1 (honest) | 0.7647 | ± 0.0875 | [0.5455, | CURRENT |
| reports/historical_recalibration.json | 118 | "rescored_lenient_f1_honest": 0.7647, | CURRENT |
| reports/historical_recalibration.json | 139 | "rescored_lenient_f1_honest": 0.7647, | CURRENT |
| reports/failure_envelope_m7.md | 50 | | M-013 | Aggregate F1 (honest) | 0.7647 | False | DETERMINI | CURRENT |
| reports/sensitivity_m6.json | 166 | "baseline_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 167 | "perturbed_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 177 | "baseline_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 188 | "baseline_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 199 | "baseline_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 210 | "baseline_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 211 | "perturbed_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 221 | "baseline_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 222 | "perturbed_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 232 | "baseline_value": 0.7647, | CURRENT |
| reports/sensitivity_m6.json | 233 | "perturbed_value": 0.7647, | CURRENT |
| programs/A_metrology/final_repository_verification.py | 251 | values_to_check = ["0.5714", "0.7879", "0.9189", "0.8571", " | CHECK |
| reports/failure_envelopes/M-013.md | 7 | - **Baseline value:** 0.7647 | CURRENT |
| reports/failure_envelopes/M-013.md | 31 | | INPUT/truncate_75pct | 0.7647 | 0.5185 | -0.2462 | -0.3219 | CURRENT |

## 0.9744

| File | Line | Context | Classification |
|---|---|---|---|
| FAILURES.md | 5681 | - 19/20 token overlap matches (F1=0.9744) | HISTORICAL |
| FAILURES.md | 5775 | | token | 0.9744 | 0.7879 | | HISTORICAL |
| FAILURES.md | 8349 | | M-006 Recognition F1 | 1.0000 (DEGENERATE) | 0.9744 (NOT d | HISTORICAL |
| FAILURES.md | 8355 | matched via circular synonyms), now 0.9744 (can discriminate | HISTORICAL |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 37 | | Recognition F1 (all, syn, DR-91) | 0.9744 ± 0.0252 | [0.91 | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 57 | Note: "Recognition F1" is now 0.9744 (was 1.0000 with circul | CURRENT |
| PRELIMINARY_MEASUREMENT_VERDICT.md | 71 | | Recognition F1 (all, syn, DR-91) | 1.0000 (DEGENERATE) | 0 | CURRENT |
| docs/MATCHING_SPECIFICATION.md | 21 | | exact_token | Substring OR ≥1 shared 4+ char token | 0.974 | HISTORICAL |
| reports/bootstrap_statistics.md | 29 | | M-006 | Recognition F1 (all, syn, DR-91) | 0.9744 ± 0.0252 | CURRENT |
| reports/bootstrap_statistics.json | 99 | "point_estimate": 0.9744, | CURRENT |
| reports/historical_metric_inventory.md | 36 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 37 | | Recognition F1 | CURRENT |
| reports/historical_metric_inventory.md | 52 | | reports/bootstrap_statistics.md | 29 | | M-006 | Recogniti | CURRENT |
| reports/historical_metric_inventory.md | 208 | | reports/measurement_provenance_audit.md | 101 | - **Value: | CURRENT |
| reports/historical_metric_inventory.md | 220 | | reports/honest_scoreboard.md | 16 | | M-006 | 0.9744 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 224 | | reports/honest_scoreboard.md | 55 | | M-006 Recognition F1 | CURRENT |
| reports/historical_metric_inventory.md | 565 | | FAILURES.md | 8349 | | M-006 Recognition F1 | 1.0000 (DEGE | CURRENT |
| reports/historical_metric_inventory.md | 568 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 37 | | Recognition F1 | CURRENT |
| reports/historical_metric_inventory.md | 570 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 57 | Note: "Recogniti | CURRENT |
| reports/historical_metric_inventory.md | 571 | | PRELIMINARY_MEASUREMENT_VERDICT.md | 71 | | Recognition F1 | CURRENT |
| reports/historical_metric_inventory.md | 579 | | reports/bootstrap_statistics.md | 29 | | M-006 | Recogniti | CURRENT |
| reports/historical_metric_inventory.md | 598 | | reports/repository_truth_check.md | 72 | 4. **'Recognition | CURRENT |
| reports/historical_metric_inventory.md | 646 | | reports/historical_metric_inventory.md | 312 | | FAILURES. | CURRENT |
| reports/historical_metric_inventory.md | 778 | | reports/measurement_provenance_audit.md | 101 | - **Value: | CURRENT |
| reports/historical_metric_inventory.md | 799 | | reports/honest_scoreboard.md | 16 | | M-006 | 0.9744 ± 0.0 | CURRENT |
| reports/historical_metric_inventory.md | 809 | | reports/honest_scoreboard.md | 55 | | M-006 Recognition F1 | CURRENT |
| reports/measurement_provenance_audit.md | 101 | - **Value:** 0.9744 ± 0.0252 (95% CI: 0.9189, 1.0000) | CURRENT |
| reports/historical_recalibration.md | 25 | | HC-001 | 145 | Relation extraction F1 (Gen 3 NLP pipeline) | CURRENT |
| reports/historical_recalibration.md | 26 | | HC-002 | 150 | Mechanism extraction F1 (early mechanism be | CURRENT |
| reports/historical_recalibration.md | 27 | | HC-003 | 170 | Connection-finding F1 (15 verified hits out | CURRENT |
| reports/historical_recalibration.md | 28 | | HC-004 | 188 | Mechanism chain F1 after de-circularization | CURRENT |
| reports/historical_recalibration.md | 31 | | HC-007 | 243 | Recognition F1 (all entities + synonyms, DR | CURRENT |
| reports/failure_envelope_m7.json | 214 | "baseline_value": 0.9744, | CURRENT |
| reports/honest_scoreboard.md | 16 | | M-006 | 0.9744 ± 0.0252 | [0.9189, 1.0000] | 20 | 500 | B  | CURRENT |
| reports/honest_scoreboard.md | 55 | | M-006 Recognition F1 (all, DR-91) | 0.9744 | ± 0.0252 | [0 | CURRENT |
| reports/historical_recalibration.json | 33 | "rescored_lenient_f1_dr91": 0.9744, | CURRENT |
| reports/historical_recalibration.json | 54 | "rescored_lenient_f1_dr91": 0.9744, | CURRENT |
| reports/historical_recalibration.json | 75 | "rescored_lenient_f1_dr91": 0.9744, | CURRENT |
| reports/historical_recalibration.json | 96 | "rescored_lenient_f1_dr91": 0.9744, | CURRENT |
| reports/historical_recalibration.json | 159 | "rescored_lenient_f1_dr91": 0.9744, | CURRENT |
| reports/repeatability_m4.json | 81 | 0.9744, | CURRENT |
| reports/repeatability_m4.json | 84 | 0.9744, | CURRENT |
| reports/failure_envelope_m7.md | 43 | | M-006 | Recognition F1 (all, syn, DR-91) | 0.9744 | False  | CURRENT |
| reports/synonym_audit.md | 5 | | biomineralization | biological_mineralization, calcium_car | CURRENT |
| reports/synonym_audit.md | 6 | | thermal_emission | radiative_heat, thermal_radiation, radi | CURRENT |
| reports/synonym_audit.md | 7 | | thermal_regulation | thermal_control, temperature_control, | CURRENT |
| reports/synonym_audit.md | 8 | | tight_junctions | paracellular_barrier, size_selective_bar | CURRENT |
| reports/synonym_audit.md | 9 | | contact_angle | contact_angles, wetting_angle... | True |  | CURRENT |
| reports/synonym_audit.md | 10 | | photon_absorption | absorb_photons, photon_capture, light_ | CURRENT |
| reports/synonym_audit.md | 11 | | heat_dissipation | cooling, heat_removal, thermal_manageme | CURRENT |
| reports/synonym_audit.md | 12 | | ion_selectivity | ion_screening, ion_filtering, pore_size_ | CURRENT |
| reports/synonym_audit.md | 13 | | electrocatalyst | catalytic_material, platinum_catalyst, c | CURRENT |
| reports/synonym_audit.md | 14 | | temperature_gradient | thermal_gradient, heat_gradient, te | CURRENT |
| reports/synonym_audit.md | 15 | | surface_functionization | surface_modification, surface_tr | CURRENT |
| reports/synonym_audit.md | 16 | | mechanical_strain | mechanical_deformation, elastic_strain | CURRENT |
| reports/synonym_audit.md | 17 | | spin_polarization | nuclear_spin, spin_alignment, electron | CURRENT |
| reports/synonym_audit.md | 18 | | ion_storage | ion_adsorption, ion_intercalation, charge_st | CURRENT |
| reports/synonym_audit.md | 19 | | bandgap_engineering | semiconductor_bandgap, quantum_confi | CURRENT |
| reports/synonym_audit.md | 20 | | high_surface_area | porous_structure, surface_area, large_ | CURRENT |
| reports/synonym_audit.md | 21 | | tensile_strength | mechanical_strength, mechanical_propert | CURRENT |
| reports/synonym_audit.md | 22 | | latent_heat | vaporization_heat, heat_of_vaporization, pha | CURRENT |
| reports/synonym_audit.md | 23 | | photon_energy | photon, light_harvesting, light_energy...  | CURRENT |
| reports/synonym_audit.md | 24 | | fiber_morphology | fiber_structure, nanofiber_structure, f | CURRENT |
| reports/public_claim_inventory.md | 563 | | f1_value | FAILURES.md | 5681 | - 19/20 token overlap matc | CURRENT |
| tests/test_calibration_documented_m2e1.py | 152 | # removed). Now 0.9744 — NOT degenerate. This is an improvem | TEST |
| tests/test_dr98_historical_recalibration.py | 166 | # After cycle 270 (circular synonyms removed), DR-91 F1 is 0 | TEST |
| programs/A_metrology/measurement_verification_sprint.py | 563 | lines.append("4. **'Recognition F1 = 1.0000'** — was degener | CURRENT |
| programs/A_metrology/final_repository_verification.py | 251 | values_to_check = ["0.5714", "0.7879", "0.9189", "0.8571", " | CHECK |
| programs/A_metrology/MeasurementEngineSpecification.md | 133 | - Returns 0.9744 (current value) because any 4+ char token o | CHECK |
| programs/A_metrology/MeasurementEngineSpecification.md | 143 | - The 0.9744 value is misleading without FP floor context. | CHECK |
| reports/failure_envelopes/M-006.md | 7 | - **Baseline value:** 0.9744 | CURRENT |

## Summary

- BUG count: 0
- All values in docs/ classified as HISTORICAL (docs describe past cycles)
- All values in reports/ classified as CURRENT (generated by execution)
- All values in PRELIMINARY classified as CURRENT (current table) or HISTORICAL (labeled table)
