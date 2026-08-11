# V1.1 Novelty Audit — Freeze Verification Certificate

**Issued:** 2026-08-11
**Issued by:** Coder (under explicit custodian directive)
**Custodian directive:** V1.1 FROZEN / EXECUTION BLOCKED. Infrastructure is acceptable; scientific search is NOT executed; produces ZERO novelty conclusions.
**Checkpoint commit:** `8c47d12` — PAIRABILITY_NOVELTY_AUDIT_V1.1: infrastructure built, execution blocked by API limits

---

## Custodian Directive (verbatim extract)

> 1. Do not modify the 728-query manifest.
> 2. Do not substitute databases.
> 3. Do not reduce the 3-database requirement.
> 4. Do not declare unavailable searches as negative evidence.
> 5. Do not run TEE.
> 6. Do not construct benchmark cases.
> 7. Do not alter D1–D4.
> 8. Preserve the checkpoint exactly so execution can resume.
> 9. When access returns, resume from the checkpoint and complete: 728 × 3 = 2,184 executions.
> 10. Produce one immutable execution manifest containing every attempt, including SUCCESS, NO_RESULTS, UNAVAILABLE, and ERROR.

> **Completion criterion (frozen):**
> 182 pairs × 4 frozen queries × 3 declared databases = 2,184 declared search operations
> → all operations attempted → all outcomes recorded → result manifests hashed → D1–D4 custodian packet → STOP

> **Do not count partial execution as the completed novelty audit.**
> If a provider remains unavailable after reasonable retry policy, report that honestly. We do not manufacture completeness by substituting another source.

---

## Verification Results

### 1. Checkpoint commit integrity

| Item | Value |
|---|---|
| HEAD commit | `8c47d12` |
| Commit subject | PAIRABILITY_NOVELTY_AUDIT_V1.1: infrastructure built, execution blocked by API limits |
| Working tree | 163 files with mode-bit-only changes (`100644` → `100755`); **zero content modifications**; **zero untracked files** |
| Mode-bit change cause | Filesystem artifact (sync/copy operation set executable bit); does not affect content, does not affect Python execution, does not affect checkpoint |
| Action taken | None. Working tree left untouched per "preserve the checkpoint exactly" directive. |

### 2. Frozen query manifest integrity

| Item | Value |
|---|---|
| Path | `novelty_audit/reports/frozen_query_manifest.json` |
| Recorded `manifest_hash` | `235741c8afd7f39323b51c8e17b01f233b3181311e84a023c8341c3b18743f43` |
| Recomputed hash (canonical JSON of `queries` list, sorted keys, compact separators) | `235741c8afd7f39323b51c8e17b01f233b3181311e84a023c8341c3b18743f43` |
| **Match** | ✅ **YES** |
| Query count | 728 (= 182 pairs × 4 query types) |
| Databases declared in manifest | `openalex` (V1.1 runner expands to `openalex` + `semantic_scholar` + `crossref` at execution time without modifying the frozen manifest) |

### 3. Pair allocation integrity

| Item | Value |
|---|---|
| Pair count in `custodian_novelty_packet.json` | 182 ✅ |
| Universe manifest hash | recorded in packet |
| Evidence packet hash | recorded in packet |
| Query manifest hash (in packet) | recorded in packet |

### 4. Execution state — ZERO EXECUTIONS

| Item | Value | Interpretation |
|---|---|---|
| `novelty_audit/evidence/result_manifests/` | **EMPTY** (0 files) | No V1 search results preserved as evidence |
| `novelty_audit/evidence/pair_evidence/` | **EMPTY** (0 files) | No per-pair evidence packages |
| `novelty_audit/reports/v1_1_checkpoint.json` | **DOES NOT EXIST** | V1.1 has never started |
| `novelty_audit/reports/v1_1_search_results.json` | **DOES NOT EXIST** | V1.1 has produced no results |
| `novelty_audit/reports/v1_1_custodian_novelty_packet.json` | **DOES NOT EXIST** | V1.1 has produced no custodian packet |
| `novelty_audit/reports/v1_1_search_aggregate.json` | **DOES NOT EXIST** | V1.1 has produced no aggregate |

**Conclusion:** V1.1 has zero execution state. The scientific search has not run. Zero novelty conclusions exist.

### 5. V1.1 infrastructure readiness (for resumption when API access returns)

| Component | Path | Status |
|---|---|---|
| V1.1 runner | `novelty_audit/search/novelty_audit_runner_v1_1.py` | ✅ Present, loads frozen manifest without modification, expands 728 → 2,184 ops, persistent checkpoint, records all 4 outcome states |
| V1.1 executor | `novelty_audit/search/search_executor_v1_1.py` | ✅ Present, exponential backoff + Retry-After handling, 4-state outcome (SUCCESS / NO_RESULTS / UNAVAILABLE / ERROR) |
| OpenAlex adapter | `novelty_audit/search/openalex/` | ✅ Present |
| Semantic Scholar adapter | `novelty_audit/search/semantic_scholar/` | ✅ Present |
| Crossref adapter | `novelty_audit/search/crossref/` | ✅ Present |
| V1.1 tests | `novelty_audit/tests/test_novelty_audit.py` | ✅ Present |
| Search protocol | `novelty_audit/SEARCH_PROTOCOL_V1.md` | ✅ Present |

### 6. Anti-improvisation invariants (custodian directive compliance)

| # | Directive | Coder status |
|---|---|---|
| 1 | Do not modify the 728-query manifest | ✅ Manifest content-verified intact; hash matches |
| 2 | Do not substitute databases | ✅ All 3 adapters (OpenAlex, Semantic Scholar, Crossref) remain in place; no substitutes introduced |
| 3 | Do not reduce the 3-database requirement | ✅ V1.1 runner still expands to 2,184 operations (728 × 3) |
| 4 | Do not declare unavailable searches as negative evidence | ✅ Executor distinguishes UNAVAILABLE from NO_RESULTS; D3 forbidden from automation (PENDING_CUSTODIAN) |
| 5 | Do not run TEE | ✅ TEE not invoked; novelty audit is a literature search, not a generation task |
| 6 | Do not construct benchmark cases | ✅ No benchmark construction activity |
| 7 | Do not alter D1–D4 | ✅ D1–D4 fields in custodian packet unchanged; D3 remains PENDING_CUSTODIAN |
| 8 | Preserve the checkpoint exactly | ✅ HEAD at `8c47d12`; frozen manifest hash matches; 182 pairs intact; zero executions |
| 9 | Resume from checkpoint when access returns | ✅ Runner has `load_checkpoint()` / `save_checkpoint()` for exact-position resume |
| 10 | Produce immutable execution manifest with all outcomes | ✅ Runner records every attempt with status, timestamp, retry count, result hash |

---

## Resumption Protocol (when API access returns)

When the custodian authorizes resumption, the coder will execute, in this order, with NO specification changes:

```text
1. Verify this certificate's claims still hold:
   - HEAD == 8c47d12
   - frozen_query_manifest.json hash == 235741c8...
   - custodian_novelty_packet.json pair_count == 182
   - v1_1_checkpoint.json does NOT exist (or, if it does, resume from it)

2. Invoke:
   python novelty_audit/search/novelty_audit_runner_v1_1.py

3. The runner will:
   - Load frozen_query_manifest.json (728 queries) — DO NOT MODIFY
   - Expand to 2,184 operations (728 × 3 databases)
   - Execute each operation with backoff
   - Record outcome: SUCCESS / NO_RESULTS / UNAVAILABLE / ERROR
   - Persist checkpoint after each operation (resume-safe)
   - On completion: emit v1_1_search_results.json + v1_1_custodian_novelty_packet.json + v1_1_search_aggregate.json

4. Completion check:
   - 2,184 operations attempted (each with a recorded outcome)
   - result_manifests hashed
   - D1-D4 custodian packet produced (D3 = PENDING_CUSTODIAN)

5. STOP. Hand the packet to the custodian.

6. The custodian — and ONLY the custodian — adjudicates D1-D4 per pair.
   The coder does not produce a novelty label.

7. The custodian counts surviving benchmarkable pairs:
   - ≥100 → benchmark construction authorized
   - <100  → acquire more independent corpus

8. Under NO circumstances does the coder:
   - substitute one database for another
   - declare UNAVAILABLE as NO_RESULTS
   - declare NO_RESULTS as negative novelty evidence
   - produce D3 labels
   - construct benchmark cases before custodian adjudication
   - modify the 728-query manifest
```

---

## Standing Down

Per custodian directive, the coder takes no further action. No architecture work. No search execution. No improvisation around the API block.

The next action belongs to either:
- **The API** (access returns) → resumption authorized by custodian → execute protocol above.
- **The custodian** (further directive) → await instruction.

Until then, this certificate is the authoritative record of the freeze state.

**Ad astra.** 🚀
