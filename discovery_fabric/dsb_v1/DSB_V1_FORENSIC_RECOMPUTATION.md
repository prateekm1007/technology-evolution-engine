# DSB V1 — FORENSIC RECOMPUTATION

**Date:** 2026-08-12T17:58:46.531977+00:00
**Source:** Frozen receipts only. No new modules. No interpretation.
**Purpose:** Recompute all DSB V1 outcomes from frozen artifacts; verify counts, hashes, and selections.

---

## 1. Inputs (Frozen Artifacts)

- Real cases: **10** files
  - `DSB-R-001.json` — SHA-256: `1ea2b20b265118b9c2834f076c23d94c...`
  - `DSB-R-002.json` — SHA-256: `64504ab27f7117e2052fc6ab09160032...`
  - `DSB-R-003.json` — SHA-256: `58fe924702b328554c0e2cb3d258d5a6...`
  - `DSB-R-004.json` — SHA-256: `75c29da174a5386ac73252d2bd29d78c...`
  - `DSB-R-005.json` — SHA-256: `bd1c2eb15034c6bc5ee546f13066c075...`
  - `DSB-R-006.json` — SHA-256: `00198c1fdb5a9afffda244be4ae9a717...`
  - `DSB-R-007.json` — SHA-256: `96f5f0185b038c8c1429f16612f00f0d...`
  - `DSB-R-008.json` — SHA-256: `269efd60d4f9f0d7e3849c24f319ed2b...`
  - `DSB-R-009.json` — SHA-256: `f88b1378ea5456828c9aaf2713a1391b...`
  - `DSB-R-010.json` — SHA-256: `f8a338e7e9c7d0eedf744a91a4846316...`
- Fabricated cases: **10** files
  - `DSB-F-001.json` — SHA-256: `926c1e29cc8056999376dec6eeafa9e8...`
  - `DSB-F-002.json` — SHA-256: `1ca929c9aad6719b60ce556955400bee...`
  - `DSB-F-003.json` — SHA-256: `788caa52d5729de7920bb9d36b651519...`
  - `DSB-F-004.json` — SHA-256: `f0580ec70cfcb3ba14b37973e10e4a84...`
  - `DSB-F-005.json` — SHA-256: `82b660afec3aeee7e1d15dff1187cb23...`
  - `DSB-F-006.json` — SHA-256: `1d8cc26d7c84af9257e2c499dc5923f6...`
  - `DSB-F-007.json` — SHA-256: `1cd86e0a14b3c8785d3d694a925ff0b0...`
  - `DSB-F-008.json` — SHA-256: `ac79e884d9b43dcff1dbf008201a29c2...`
  - `DSB-F-009.json` — SHA-256: `8477bfca37c00052bfecb4c6907a78b2...`
  - `DSB-F-010.json` — SHA-256: `1f5a47f9bf31642f65798848e7df5f0d...`
- Receipts: **80** files
  - (all 80 receipt hashes verified in §3 below)

## 2. Freeze Manifest Verification

- Manifest hash: `cadf54bfe27adff978d82311799ac9e5...`
- Frozen at: `2026-08-12T17:36:09.862837+00:00`
- Total frozen artifacts: **111**
- Unchanged: **111**
- Modified: **0**
- Missing: **0**
- All artifacts unchanged after freeze: **True**

## 3. Receipt Integrity (stored hash vs recomputed hash)

- Total receipts: **80**
- Valid (hash matches): **80**
- Invalid (hash mismatch): **0**
- All valid: **True**

## 4. Recomputed Scorer Outcomes (80 receipts)

- Total scores recomputed: **80**

### Per-arm summary (recomputed)

| Arm | N | Real N | Fab N | Recovered | Real Recovered | Fab Recovered | Mech Reconstructed | Disc Score Mean | Mech Score Mean |
|---|---|---|---|---|---|---|---|---|---|
| LLM_only | 20 | 10 | 10 | 3 | 0 | 3 | 0 | 0.3324 | 0.2243 |
| combination | 20 | 10 | 10 | 6 | 2 | 4 | 0 | 0.3561 | 0.2037 |
| full_system | 20 | 10 | 10 | 2 | 0 | 2 | 0 | 0.3487 | 0.2336 |
| mechanism_only | 20 | 10 | 10 | 2 | 1 | 1 | 0 | 0.2996 | 0.1356 |

## 5. Independently Regenerated 13-Recovery List

- Total recoveries: **13**
- By case type: **{'fabricated': 10, 'real': 3}**

### Recovery list (sorted by score descending)

| Receipt ID | Case ID | Case Type | Arm | Score |
|---|---|---|---|---|
| RECEIPT-DSB-F-005-LLM_only | DSB-F-005 | fabricated | LLM_only | 0.6705 |
| RECEIPT-DSB-F-005-full_system | DSB-F-005 | fabricated | full_system | 0.6705 |
| RECEIPT-DSB-R-001-combination | DSB-R-001 | real | combination | 0.6205 |
| RECEIPT-DSB-F-006-mechanism_only | DSB-F-006 | fabricated | mechanism_only | 0.6167 |
| RECEIPT-DSB-F-006-combination | DSB-F-006 | fabricated | combination | 0.5833 |
| RECEIPT-DSB-F-001-combination | DSB-F-001 | fabricated | combination | 0.5784 |
| RECEIPT-DSB-F-010-full_system | DSB-F-010 | fabricated | full_system | 0.5607 |
| RECEIPT-DSB-F-001-LLM_only | DSB-F-001 | fabricated | LLM_only | 0.5536 |
| RECEIPT-DSB-F-006-LLM_only | DSB-F-006 | fabricated | LLM_only | 0.5521 |
| RECEIPT-DSB-R-007-combination | DSB-R-007 | real | combination | 0.5486 |
| RECEIPT-DSB-F-005-combination | DSB-F-005 | fabricated | combination | 0.5278 |
| RECEIPT-DSB-R-007-mechanism_only | DSB-R-007 | real | mechanism_only | 0.525 |
| RECEIPT-DSB-F-007-combination | DSB-F-007 | fabricated | combination | 0.5122 |

## 6. Count Verification: 10 Fabricated + 3 Real = 13

- Fabricated recoveries: **10** (expected 10) — match: **True**
- Real recoveries: **3** (expected 3) — match: **True**
- Total recoveries: **13** (expected 13) — match: **True**
- Fabricated + Real = Total: **True**

## 7. Regenerated 14 Focused-Review Packet IDs

### Selection criteria (NO human outcomes used)

- Criterion A (all RECOVERED receipts): **13** receipts
  - `RECEIPT-DSB-F-001-LLM_only`
  - `RECEIPT-DSB-F-001-combination`
  - `RECEIPT-DSB-F-005-LLM_only`
  - `RECEIPT-DSB-F-005-combination`
  - `RECEIPT-DSB-F-005-full_system`
  - `RECEIPT-DSB-F-006-LLM_only`
  - `RECEIPT-DSB-F-006-combination`
  - `RECEIPT-DSB-F-006-mechanism_only`
  - `RECEIPT-DSB-F-007-combination`
  - `RECEIPT-DSB-F-010-full_system`
  - `RECEIPT-DSB-R-001-combination`
  - `RECEIPT-DSB-R-007-combination`
  - `RECEIPT-DSB-R-007-mechanism_only`
- Criterion B (top-2 fabricated per arm by discovery score): **8** receipts
  - `RECEIPT-DSB-F-001-LLM_only`
  - `RECEIPT-DSB-F-001-combination`
  - `RECEIPT-DSB-F-005-LLM_only`
  - `RECEIPT-DSB-F-005-full_system`
  - `RECEIPT-DSB-F-006-combination`
  - `RECEIPT-DSB-F-006-mechanism_only`
  - `RECEIPT-DSB-F-007-mechanism_only`
  - `RECEIPT-DSB-F-010-full_system`
- Union: **14** receipts
- Selection used human outcomes: **False**

### Union packet IDs (14 expected)

- `ADJ-14c575431919`
- `ADJ-2e76e1b7ae11`
- `ADJ-468cd7a18409`
- `ADJ-4b11123c3a05`
- `ADJ-6929d8048064`
- `ADJ-6cbd765bedab`
- `ADJ-70b907f34a6b`
- `ADJ-86b6ffe2d7e7`
- `ADJ-9639681e0f8b`
- `ADJ-a3b0a2dfcdb4`
- `ADJ-a47da0123180`
- `ADJ-bf469e26b83d`
- `ADJ-ce7257999e1b`
- `ADJ-f8171e1ff471`

## 8. Focused-Review Packet ID Match Verification

- Frozen packet IDs count: **14**
- Regenerated packet IDs count: **14**
- Match (frozen == regenerated): **True**

### Frozen packet IDs (from focused_review_packets_BLIND.json)

- `ADJ-14c575431919`
- `ADJ-2e76e1b7ae11`
- `ADJ-468cd7a18409`
- `ADJ-4b11123c3a05`
- `ADJ-6929d8048064`
- `ADJ-6cbd765bedab`
- `ADJ-70b907f34a6b`
- `ADJ-86b6ffe2d7e7`
- `ADJ-9639681e0f8b`
- `ADJ-a3b0a2dfcdb4`
- `ADJ-a47da0123180`
- `ADJ-bf469e26b83d`
- `ADJ-ce7257999e1b`
- `ADJ-f8171e1ff471`

### Regenerated packet IDs

- `ADJ-14c575431919`
- `ADJ-2e76e1b7ae11`
- `ADJ-468cd7a18409`
- `ADJ-4b11123c3a05`
- `ADJ-6929d8048064`
- `ADJ-6cbd765bedab`
- `ADJ-70b907f34a6b`
- `ADJ-86b6ffe2d7e7`
- `ADJ-9639681e0f8b`
- `ADJ-a3b0a2dfcdb4`
- `ADJ-a47da0123180`
- `ADJ-bf469e26b83d`
- `ADJ-ce7257999e1b`
- `ADJ-f8171e1ff471`

## 9. Summary of All Forensic Checks

| Check | Result |
|---|---|
| Freeze manifest — all artifacts unchanged | **PASS** |
| Receipt integrity — all 80 hashes valid | **PASS** |
| Recomputed scores — 80/80 | **PASS** |
| Recovery count — 13 total | **PASS** |
| Recovery split — 10 fabricated + 3 real | **PASS** |
| Focused-review — 14 packet IDs | **PASS** |
| Focused-review — regenerated matches frozen | **PASS** |
| Focused-review — no human outcomes used in selection | **PASS** |

---

**End of forensic recomputation. No interpretation. STOP.**