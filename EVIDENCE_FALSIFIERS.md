# EVIDENCE_FALSIFIERS

**Status:** Tracker for EP-4 falsification conditions.
**Location:** repo root.
**Phase:** Post-Phase-13 governance.

Every explanatory claim the project makes that uses the words
"necessary," "sufficient," "deep," "fundamental," "verified,"
"validated," or "confirmed" must have an entry here BEFORE the
analysis that tests it runs (per EP-4). Entries are append-only.

If a claim has no falsifier stated here, it cannot ship as a
finding — it ships as a hypothesis.

---

## Seed entries (Commit B, post-Phase-13 retrospective)

### FEC-001: Formula B ≈ velocity + adjacency

| Field | Value |
|---|---|
| claimId | FEC-001 |
| claimText | "Formula B (frozen, full) produces per-T precision arrays identical to velocity+adjacency without cost_bonus on the Li-ion 14-point backtest." |
| falsifierText | "Any per-T precision value at any T-point in `evidence/observations/ablation_results.json` that differs between `7. Formula B (frozen)` and `4. velocity + adjacency`." |
| statedAt | 2026-08-02 (Commit B of this governance pass) — retroactive, since the original ablation analysis ran in Phase 12 (Task 37) without a pre-stated falsifier. The falsifier is recorded here post-hoc to make future re-runs checkable. |
| testedAt | 2026-08-02 (Phase 13 retrospective in this conversation) |
| testResult | CONFIRMED — per-T arrays byte-identical across 14 T-points: `[0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.1, 0.2, 0.0, 0.0]`. Verified via direct read of `evidence/observations/ablation_results.json`. |
| caveat | The original analysis (Task 37) did not pre-state this falsifier. The claim was made and then verified retrospectively. Per EP-4, this should have been pre-registered. The verification is real; the process was not. |

### FEC-002: velocity is necessary for invention

| Field | Value |
|---|---|
| claimId | FEC-002 |
| claimText | "Every true positive (TP) in MECHANISM_REGISTRY.md has at least one rising capability with velocity > 0.20 TRL/year at T-1." |
| falsifierText | "A single TP in any future backtest whose rising-capability velocity at T-1 is below 0.20 TRL/year." |
| statedAt | 2026-08-02 (Commit B of this governance pass) — retroactive. The original NECESSITY_SUFFICIENCY.md (Phase 13D) made this claim without pre-stating the falsifier. |
| testedAt | null |
| testResult | PENDING — the existing 7 TPs in MECHANISM_REGISTRY.md are consistent with the claim (all 7 have velocity > 0.20), but since the falsifier was not pre-stated before Phase 13D, this is a retrospective consistency check on existing data, not a forward test. The next Phase 14 stress test will be the first forward test. |
| caveat | Per EP-4, this claim should be relabeled "hypothesis" until a forward test runs. The current `NECESSITY_SUFFICIENCY.md` labels it "finding," which violates EP-4. The retitling in Commit C corrects the document label but does not change the underlying data. |

### FEC-003: backward explanatory power (TIME_REVERSAL_PROTOCOL.md)

| Field | Value |
|---|---|
| claimId | FEC-003 |
| claimText | "For every event in EVENT_REGISTRY.md, the modeled preconditions were satisfied in the prior 5-year window." |
| falsifierText | "A single event in EVENT_REGISTRY.md whose modeled preconditions were NOT satisfied in the prior 5-year window." |
| statedAt | 2026-08-02 (Commit B of this governance pass) — retroactive. |
| testedAt | 2026-08-02 (Phase 13E) |
| testResult | The original TIME_REVERSAL_PROTOCOL.md reported 0 of 16 events UNEXPLAINED. This is technically CONFIRMED — but per EP-3, the verification is contaminated: the preconditions for each event were selected by a process that already knew the event occurred. The 100% backward fit is therefore a retrospective consistency check, not evidence. |
| caveat | This entry exists to make the contamination explicit. The claim is RETIRED — it cannot be cited as evidence in any future document. The TIME_REVERSAL_PROTOCOL.md document is retitled in Commit C to reflect this. |

### FEC-004: 2-of-4 cross-domain threshold

| Field | Value |
|---|---|
| claimId | FEC-004 |
| claimText | "If the model survives 2 of 4 structurally different stress tests (aviation, semiconductors, telecom, pharma), it is LOCAL with FUNDAMENTAL ASPIRATIONS." |
| falsifierText | "This is a threshold, not an explanatory claim — but per EP-6, it must be pre-registered before the test that uses it runs. The falsifier is: if the threshold is changed after seeing any Phase 14 result, the original is FALSIFIED." |
| statedAt | 2026-08-02 (Commit B of this governance pass) — retroactive, since CROSS_DOMAIN_STRESS_TEST.md was written in the same session as PHASE_13_SYNTHESIS.md (Phase 13) that uses the threshold. |
| testedAt | null |
| testResult | PENDING — no Phase 14 stress test has run. The threshold as written is also suspect per EP-6 (it was not committed before the synthesis that uses it). Per the user's review, a more honest threshold would be 3 of 4 for LOCAL and 4 of 4 for FUNDAMENTAL; 2 of 4 should be "M4 not yet transferred to structurally different domains." |
| caveat | The original CROSS_DOMAIN_STRESS_TEST.md threshold (2 of 4 → LOCAL) is relabeled "proposal" in Commit C. The binding threshold will be re-committed in a separate artifact before Phase 14A runs, per EP-6. |

---

## Future entries

Any future claim using "necessary," "sufficient," "deep," "fundamental,"
"verified," "validated," or "confirmed" must have a FEC-XXX entry
stated BEFORE the analysis runs. The entry must include `statedAt`
with a commit hash that pre-dates the test commit.

If a claim has no FEC entry, it ships as a hypothesis with the
label "HYPOTHESIS" in the document. It does not ship as a finding.
