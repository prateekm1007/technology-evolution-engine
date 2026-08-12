# V8.1 — FINAL BUNDLE IDENTITY CORRECTION

**Date:** 2026-08-12T20:24:25.488070+00:00

## 1. Host Path Removed

The `build_location` field (host filesystem path) has been **removed** from BUNDLE_MANIFEST.json. The bundle's identity is now **cryptographic**, not path-based.

## 2. Canonical Artifact Identity

The bundle is identified by three bound values:

| Field | Value |
|---|---|
| `build_id` | `ecc65ee8-878f-4fe5-be77-6c2588720156` |
| `bundle_hash` | `031491c2e1b09e7b2df3f6c97a2b9e8d...` |
| `manifest_hash` | `33196ad72e27a9f13a9b4939dca167c7...` |

The final adjudication ledger MUST bind all three. This proves the adjudicator operated on this exact bundle and prevents substitution.

## 3. Evaluator Access (Strictly One-Way)

- Adjudicator produces sealed ledger → evaluator consumes (after sealing)
- Evaluator CANNOT write to adjudicator workspace
- Adjudicator CANNOT read evaluator namespace
- Access is strictly one-way after ledger sealing

## 4. Bundle Self-Integrity Test

**10/10 checks PASS**

| Check | Result |
|---|---|
| FILE_HASH_cto_packets_BLIND.json | PASS |
| FILE_HASH_CTO_ADJUDICATION_INSTRUCTIONS.md | PASS |
| FILE_HASH_cto_adjudication_template.json | PASS |
| BUNDLE_HASH_MATCHES | PASS |
| MANIFEST_HASH_MATCHES | PASS |
| NO_HOST_PATH_IN_MANIFEST | PASS |
| NO_FORBIDDEN_CONTENT_IN_BUNDLE | PASS |
| NO_GIT_METADATA_IN_BUNDLE | PASS |
| NO_EXTERNAL_SYMLINKS | PASS |
| BUNDLE_HAS_EXACTLY_4_FILES | PASS |


## 5. V8 Hard Invariant

`adjudicator_bundle_path ∉ research_repo`: **PASS**
Git-tracked bundle files: none

## 6. Adjudication Status

- Bundle self-integrity: **PASS**
- V8 hard invariant: **PASS**
- adjudication_permitted: **FALSE** (B/C/D/P/O/Q still required)
- V8.1 bundle integrity is GREEN, but adjudication remains BLOCKED

## 7. What Was NOT Modified

- DSB V1 cases, prompts, receipts, scorer: NOT modified
- Research repository: NOT modified

---

**V8.1 bundle identity correction complete. Bundle self-integrity PASS. Adjudication remains BLOCKED. STOP coding permanently in this environment.**
