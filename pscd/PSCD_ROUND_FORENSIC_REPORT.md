# PSCD-1 ROUND FORENSIC REPORT

**Round ID:** DRY-Round-001
**Type:** DRY_RUN
**Final State:** NEXT_ROUND_ELIGIBLE
**Generated:** 2026-08-12T23:51:07.920730+00:00

## Event Chain

| # | Event | Timestamp | Previous State | New State | Actor |
|---|---|---|---|---|---|
| 1 | — | 2026-08-12T23:51:07.819767+00:00 | NONE | ROUND_CREATED | system |
| 2 | — | 2026-08-12T23:51:07.819856+00:00 | ROUND_CREATED | EVIDENCE_FROZEN | system |
| 3 | — | 2026-08-12T23:51:07.819907+00:00 | EVIDENCE_FROZEN | HYPOTHESES_GENERATED | A0/A1_runner |
| 4 | — | 2026-08-12T23:51:07.819968+00:00 | HYPOTHESES_GENERATED | PREDICTIONS_COMMITTED | system |
| 5 | — | 2026-08-12T23:51:07.820003+00:00 | PREDICTIONS_COMMITTED | PREDICTION_FROZEN | system |
| 6 | — | 2026-08-12T23:51:07.820025+00:00 | PREDICTION_FROZEN | OUTCOME_WAITING | system |
| 7 | — | 2026-08-12T23:51:07.920364+00:00 | OUTCOME_WAITING | OUTCOME_IMPORTED | custodian |
| 8 | — | 2026-08-12T23:51:07.920449+00:00 | OUTCOME_IMPORTED | OUTCOMES_VERIFIED | system |
| 9 | — | 2026-08-12T23:51:07.920523+00:00 | OUTCOMES_VERIFIED | SCORED | deterministic_scorer |
| 10 | — | 2026-08-12T23:51:07.920566+00:00 | SCORED | LEARNED | learning_registry |
| 11 | — | 2026-08-12T23:51:07.920590+00:00 | LEARNED | NEXT_ROUND_ELIGIBLE | system |


## Artifacts

- Evidence snapshot hash: `d956ffc45eacb9954e4df446c360cfa7...`
- Prediction freeze hash: `5789979823cda08ad2b1cff5247351f8...`
- Prediction freeze timestamp: 2026-08-12T23:51:07.819961+00:00
- Custodian auth ID: DRY-CUSTODIAN-001
- Event chain hash: `a65a83d9a11042bf6af3efdbf451d424...`

## Counts

- Predictions: 10
- Outcomes: 10
- Scores: 10
- Learning objects: 2

## Aggregate Metrics

- true_confirmation_rate: 0.0
- foil_confirmation_rate: 0.0
- net_discovery_rate: 0.0


## Anti-Leakage Verification

- Outcome release AFTER prediction freeze: ✓ (verified at import)
- No self-generated outcomes: ✓
- No duplicate outcome IDs: ✓
- Learning objects are future-only: ✓
- Predictions immutable after freeze: ✓ (hash-committed)

## Notes

- This is a DRY_RUN round.
- No real outcomes were used. All later_confirmed=False.
- SCIENTIFIC_RESULT label is NOT applied to dry runs.

---

**End of Round Forensic Report.**
