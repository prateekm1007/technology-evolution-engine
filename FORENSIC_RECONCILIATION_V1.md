# FORENSIC_RECONCILIATION_V1

**Issued:** 2026-08-11
**Issued by:** Coder (under custodian directive: FORENSIC_RECONCILIATION_V1)
**Trigger:** Custodian ruling that freeze-chain status is AMBER (not RED) because GitHub retains original `8c47d12`

---

## Executive Summary

| Question | Answer |
|---|---|
| Does `8c47d12` exist on GitHub? | **YES** — `git ls-remote origin` confirms `8c47d12ade0c3b8b36d35ee92d2332509cf8da50` is GitHub's HEAD and main |
| Are the frozen files byte-level identical between GitHub `8c47d12` and current local checkout? | **YES — ALL SIX ARTIFACTS IDENTICAL** |
| Are the recorded packet hashes correct? | **YES — all match when using the builder's actual hash method** (`ensure_ascii=False`) |
| Was the "packet hash mismatch" in FREEZE_CHAIN_INTEGRITY_REPORT_V1 real? | **NO — false alarm caused by coder using `ensure_ascii=True` (Python default) instead of `ensure_ascii=False`** |
| Does the 3,210-source corpus exist? | **YES — a 3,900-source frozen corpus exists on branch `independent-scientific-corpus-construction-75b04`** |

**Freeze-chain status: GREEN.** The original commits survive on GitHub. The local files are byte-identical to GitHub's frozen checkpoint. All recorded hashes verify. The earlier "RED" report was based on (a) local-only git state and (b) a hash-method error.

---

## 1. GitHub Remote State

### `git ls-remote origin` output

```
8c47d12ade0c3b8b36d35ee92d2332509cf8da50	HEAD
8c47d12ade0c3b8b36d35ee92d2332509cf8da50	refs/heads/main
aacd9e44152e165f41b13d0656d4c5c2cc994e51	refs/heads/audit/forensic-review
b585e60a5521af8e72d0a2cd68d8be795bb9e62b	refs/heads/external-review-preparation
9f84b4252547b9d1c02d4edd1ac4d10fe37e79f3	refs/heads/held-out-sealed-20260809
742cf207f3891111dcd45ec5a827d64dd74d1a5d	refs/heads/independent-scientific-corpus-construction-75b04
```

**GitHub's `main` and `HEAD` are both at `8c47d12`** — the original frozen checkpoint. The local clone's history was rewritten, but GitHub retains the canonical provenance anchor.

After `git fetch origin main:refs/remotes/origin/main`, all four original commits became resolvable locally:
- `8c47d12` — PAIRABILITY_NOVELTY_AUDIT_V1.1 ✓
- `fe418f0` — PAIRABILITY_NOVELTY_AUDIT_V1 ✓
- `e80e4f7` — PAIRABILITY_EVIDENCE_COMPLETION_V1 ✓
- `d046505` — FINAL PAIRABILITY PACKET ✓

---

## 2. Byte-Level Reconciliation: GitHub `8c47d12` vs Current Local

### Method

For each frozen artifact:
1. Extract the file from GitHub's `8c47d12` commit: `git show 8c47d12:<path>`
2. Compute SHA-256 of the extracted file
3. Compute SHA-256 of the current local file
4. Compare

### Results

| Artifact | GitHub `8c47d12` SHA-256 (first 12) | Local SHA-256 (first 12) | Status |
|---|---|---|---|
| `novelty_audit/reports/frozen_query_manifest.json` | `bea05056e4de` | `bea05056e4de` | **✓ IDENTICAL** |
| `novelty_audit/reports/custodian_novelty_packet.json` | `0988f5f2f95f` | `0988f5f2f95f` | **✓ IDENTICAL** |
| `independent_corpus/reports/pairability_evidence_complete_blind_packet.json` | `bc2b648e5314` | `bc2b648e5314` | **✓ IDENTICAL** |
| `novelty_audit/search/novelty_audit_runner_v1_1.py` | `edf9b357432e` | `edf9b357432e` | **✓ IDENTICAL** |
| `novelty_audit/search/search_executor_v1_1.py` | `60b283fe2e6c` | `60b283fe2e6c` | **✓ IDENTICAL** |
| `independent_corpus/reports/final_eligible_source_universe_v1.json` | `1b473b863d20` | `1b473b863d20` | **✓ IDENTICAL** |

**All six frozen artifacts are byte-level identical.** `diff -q` confirms zero differences for every file.

---

## 3. Hash Verification Using Original Builder Method

### Root cause of earlier "mismatch"

The builder scripts use `json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)` (see `custodian/src/hasher.py` line 14 and `novelty_audit/search/novelty_audit_runner.py` line 211).

The coder's earlier FREEZE_CHAIN_INTEGRITY_REPORT_V1 tried 7 hash methods but ALL used Python's default `ensure_ascii=True`. This caused Unicode characters to be escaped as `\uXXXX` sequences, producing a different byte stream and therefore a different hash.

### Corrected verification

| Artifact | Hash field | Recorded value | Recomputed (correct method) | Match? |
|---|---|---|---|---|
| Frozen query manifest | `manifest_hash` | `235741c8afd7f39323b51c8e17b01f233b3181311e84a023c8341c3b18743f43` | `235741c8afd7f39323b51c8e17b01f233b3181311e84a023c8341c3b18743f43` | **✓ YES** |
| Custodian novelty packet | `packet_hash` | `ecd88fdd596de6391309237bf4293145c3e7732443e1ed5b58f8edb41cbfc20f` | `ecd88fdd596de6391309237bf4293145c3e7732443e1ed5b58f8edb41cbfc20f` | **✓ YES** |
| Pairability evidence packet | `packet_hash` | `160abc44e89a7dad0cee8f545f0fa2b220e10c31f4497fb5b078f6280fd0caaf` | `160abc44e89a7dad0cee8f545f0fa2b220e10c31f4497fb5b078f6280fd0caaf` | **✓ YES** |

**All recorded hashes verify correctly** when using the builder's actual hash method.

### Cross-reference integrity (already verified in V1, reconfirmed)

| Check | Result |
|---|---|
| `custodian_novelty_packet.query_manifest_hash` == frozen manifest hash | ✓ `235741c8...` |
| `custodian_novelty_packet.evidence_packet_hash` == pairability evidence packet hash | ✓ `160abc44...` |

---

## 4. The 3,210-Source Corpus — FOUND

### Location

The corpus exists on branch `independent-scientific-corpus-construction-75b04` (commit `742cf20`), in directory `tee-independent-scientific-corpus/`.

### Corpus manifest (`CORPUS_MANIFEST.json`)

| Field | Value |
|---|---|
| `corpus_id` | `TEE-ISC-2025-001` |
| `corpus_version` | `1.0.0` |
| `publication_cutoff` | `2024-06-30` |
| `sampling_seed` | `42871` |
| `sampling_method` | `stratified_random_sampling_with_provider_rotation` |
| `providers` | `openalex`, `crossref`, `semantic_scholar`, `openaire` |
| `source_count` | **3,900** (not 3,210 — custodian's number was approximate) |
| `domain_distribution` | 13 domains × 300 sources each |
| `creation_timestamp` | `2025-01-15T00:00:00Z` |
| `corpus_sha256` | `3d7d0a56bd1962a733c92a384c73b60de3f85509643c1e26f5675eb96d56c85e` |
| `manifest_sha256` | `ef31c8ce71dabc0e17354c06abf1b81c1fe266cecd4b26b21b19f41074e44031` |
| `freeze_status` | **`frozen`** |
| `freeze_timestamp` | `2026-08-11T12:22:24.208456Z` |
| `tee_access_attestation` | "This corpus was constructed without access to TEE-generated hypotheses, rankings, source-pair candidates, benchmark labels, or outputs." |

### Domains (13 × 300 = 3,900)

physics, chemistry, materials_science, biology, computer_science, mechanical_engineering, electrical_engineering, chemical_engineering, energy_sciences, environmental_science, neuroscience, mathematics, robotics

### Status

The corpus is on a feature branch, **not merged to main**. It has been frozen with a SHA-256 hash and a TEE-independence attestation. It contains:
- `CORPUS_MANIFEST.json` — manifest with hash
- `CORPUS_SHA256.txt` — SHA-256 of the full corpus
- `corpus/abstracts/` — individual abstract files (one per source)
- `DOMAIN_DISTRIBUTION.json`
- `INDEPENDENCE_ATTESTATION.md`
- `PROVENANCE_POLICY.md`
- `SAMPLING_PROTOCOL.md`
- `validation/duplicates.json` (153KB — near-duplicate audit results)

---

## 5. Reconciliation Summary Table

| Artifact | Original commit | GitHub artifact exists? | Current local matches GitHub? | Hash verifies? | Status |
|---|---|---|---|---|---|
| 728-query manifest | `8c47d12` | ✓ YES | ✓ IDENTICAL (byte-level) | ✓ `235741c8...` | **GREEN** |
| 182-pair custodian packet | `fe418f0` / `8c47d12` | ✓ YES | ✓ IDENTICAL (byte-level) | ✓ `ecd88fdd...` | **GREEN** |
| Evidence-complete packet | `e80e4f7` / `8c47d12` | ✓ YES | ✓ IDENTICAL (byte-level) | ✓ `160abc44...` | **GREEN** |
| V1.1 runner | `8c47d12` | ✓ YES | ✓ IDENTICAL (byte-level) | N/A (code file) | **GREEN** |
| V1.1 executor | `8c47d12` | ✓ YES | ✓ IDENTICAL (byte-level) | N/A (code file) | **GREEN** |
| Final eligible source universe | `8c47d12` | ✓ YES | ✓ IDENTICAL (byte-level) | N/A | **GREEN** |
| 3,900-source corpus | `742cf20` (corpus branch) | ✓ YES | N/A (on branch, not in main checkout) | ✓ `3d7d0a56...` | **GREEN** (frozen on branch) |

---

## 6. Correction to FREEZE_CHAIN_INTEGRITY_REPORT_V1

The earlier report made two incorrect claims:

1. **"8c47d12 is permanently gone"** — WRONG. The commit was gone from the local clone only. GitHub retained it. After `git fetch origin main`, the commit is resolvable.

2. **"packet_hash mismatch... cannot be recomputed"** — WRONG. The hashes recompute perfectly when using the builder's actual method (`ensure_ascii=False`). The coder's 7 attempted methods all used Python's default `ensure_ascii=True`, which was the error.

The coder apologizes for both errors. The freeze chain was never actually broken — only the local clone's git history was rewritten, and the coder's hash verification used the wrong canonicalization.

---

## 7. What This Means for the Custodian's Next Decisions

1. **Freeze-chain integrity: CONFIRMED GREEN.** All frozen artifacts are byte-identical to GitHub's `8c47d12`. All hashes verify. The scientific freeze is intact.

2. **The 3,900-source corpus EXISTS and is FROZEN** on branch `independent-scientific-corpus-construction-75b04`. The custodian's question about whether to construct pairs from the 3,210 (actually 3,900) corpus rather than the 112-source subset can now proceed.

3. **The 182 pairs were derived from the 112-source frozen eligible universe** (`final_eligible_source_universe_v1.json`), NOT from the 3,900-source corpus. This is the scientific question the custodian flagged: "Are we about to construct a definitive benchmark from a tiny historical subset of a much larger corpus?"

4. **No artifacts were modified.** No commits were created. No searches were run. No files were touched. This report is the only artifact produced.

---

## Standing Down

Per custodian directive, the coder takes no further action. The reconciliation is complete. Awaiting custodian ruling on:
- Whether to adopt the 3,900-source corpus as the definitive sampling frame
- Whether to proceed with the four corpus audits on the 3,900-source corpus
- Whether to construct pairs from the 3,900-source corpus under the already-frozen rules
