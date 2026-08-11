# CORPUS_ARTIFACT_LOCATION_AUDIT_V1

**Issued:** 2026-08-11
**Issued by:** Coder (under custodian directive: CORPUS_ARTIFACT_LOCATION_AUDIT_V1)
**Target artifact:** `SOURCE_MANIFEST` with SHA-256 `67107f753251a1a0109a18dd2be8cc9c6c07e6e05514debfc1b52bb817e872ff`

---

## Executive Summary

**The source manifest artifact was NOT FOUND in any searched location.**

The claimed hash `67107f753251a1a0109a18dd2be8cc9c6c07e6e05514debfc1b52bb817e872ff` exists only as a CLAIM in manifest documents. No underlying source manifest file exists anywhere — not in any git branch, tag, release, LFS object, or commit history of either repository.

| Location searched | Found? | Details |
|---|---|---|
| Corpus repo branches | NO | Only `main` branch exists; contains manifest docs but no source data |
| Corpus repo tags | NO | Zero tags exist |
| Corpus repo releases | NO | Zero releases exist |
| Corpus repo Git LFS | NO | Git LFS not installed; no `.gitattributes` |
| Corpus repo all reachable objects | NO | Largest blob is 5,968 bytes — too small for 3,210 records |
| Corpus repo dangling commits | NO | No dangling commits |
| Main TEE repo branches | NO | 5 branches checked; none contain a 3,210-source manifest |
| Main TEE repo tags | NO | 2 tags exist; neither contains source manifest |
| Main TEE repo releases | NO | Zero releases exist |
| Main TEE repo Git LFS | NO | No `.gitattributes`, no LFS objects |
| Main TEE repo all reachable objects | NO | No blob matches the claimed hash |
| Hash as git object | NO | `67107f75` is not a valid object name in either repo |
| Hash as content in any file | NO | Only appears as a CLAIMED value in manifest documents |

**Conclusion: The 3,210-source manifest was specified but never preserved as an artifact.**

---

## 1. Repositories Searched

### Repository 1: `prateekm1007/tee-independent-scientific-corpus`
- **Clone location:** `/tmp/tee-corpus`
- **HEAD:** `d37c4563150b1fb5e940de745e67fd180858a7da`
- **Branches:** `main` only
- **Tags:** 0
- **Releases:** 0
- **Git LFS:** not installed, no `.gitattributes`
- **Total commits:** 25
- **Largest blob:** 5,968 bytes (CORPUS_READINESS_REPORT_V1.md)

### Repository 2: `prateekm1007/technology-evolution-engine`
- **Clone location:** `/home/z/my-project/audit/technology-evolution-engine`
- **Remote HEAD:** `8c47d12ade0c3b8b36d35ee92d2332509cf8da50`
- **Branches:** `main`, `audit/forensic-review`, `external-review-preparation`, `held-out-sealed-20260809`, `independent-scientific-corpus-construction-75b04`
- **Tags:** 2 (`proposal-composer-gen0`, `stage-1-measurement-integrity-baseline`)
- **Releases:** 0
- **Git LFS:** not installed, no `.gitattributes`

---

## 2. Detailed Search Results

### 2.1 Corpus repo (`tee-independent-scientific-corpus`)

**Branches:** Only `main`. No other branches exist locally or remotely.

**Tags:** Zero.

**Releases:** Zero (confirmed via GitHub API).

**Git LFS:** Not installed. No `.gitattributes` file. No LFS objects.

**All reachable git objects (via `git cat-file --batch-all-objects`):**
- Largest blob: 5,968 bytes
- No blob large enough to contain 3,210 source records
- No blob whose hash equals `67107f75...`

**File inventory (complete):**
```
CORPUS_MANIFEST.json                    1,596 bytes
CORPUS_READINESS_REPORT_V1.md           5,968 bytes
DOMAIN_DISTRIBUTION.json                  864 bytes
INDEPENDENCE_ATTESTATION.md             1,657 bytes
PROVENANCE_POLICY.md                    1,627 bytes
PROVENANCE_SUMMARY.json                 1,242 bytes
README.md                               1,930 bytes
SAMPLING_PROTOCOL.md                    3,384 bytes
corpus/abstracts/.gitkeep               0 bytes (EMPTY DIR)
corpus/fulltext/.gitkeep                0 bytes (EMPTY DIR)
corpus/hashes/.gitkeep                  0 bytes (EMPTY DIR)
corpus/metadata/.gitkeep                0 bytes (EMPTY DIR)
custodian/adjudications/.gitkeep        0 bytes (EMPTY DIR)
custodian/answer_keys/.gitkeep          0 bytes (EMPTY DIR)
custodian/benchmark_candidates/.gitkeep 0 bytes (EMPTY DIR)
custodian/seals/.gitkeep                0 bytes (EMPTY DIR)
provenance/.gitkeep                     0 bytes (EMPTY DIR)
validation/contamination_audit.json     1,510 bytes
validation/domain_audit.json            115 bytes
validation/duplicates.json              1,559 bytes
validation/exposure_audit.json          134 bytes
```

**No source manifest file. No source record files. No data files of any kind.**

### 2.2 Main TEE repo (`technology-evolution-engine`)

**Branches searched:** `main`, `audit/forensic-review`, `external-review-preparation`, `held-out-sealed-20260809`, `independent-scientific-corpus-construction-75b04`

**Files matching `source_manifest` pattern:** None found in any branch.

**Files containing the string `67107f75`:** None found in any branch of the main TEE repo.

**Files containing `source_manifest_sha256` field:**
- Found in `discovery_experiment/ENGINE_OUTPUT/RUN-DXP-*/RUN_INTEGRITY_ANCHOR.json` (these are TEE run anchors, not corpus manifests)
- The values in those files (`ac1ccedf...`, `e8a607b8...`) do NOT match `67107f75...`

**Branch `independent-scientific-corpus-construction-75b04`:**
- Contains `tee-independent-scientific-corpus/` directory with 11,722 files
- Contains 3,900 abstract files, 3,900 metadata files, 3,900 hash files
- **BUT the manifest explicitly says:** `source_count: 3900` and `notes: "Mock data generated for infrastructure testing. Replace with real API data for production use."`
- This is the REJECTED 3,900 mock corpus. **NOT the 3,210 real corpus.**
- Its `corpus_sha256` is `3d7d0a56bd1962a733c92a384c73b60de3f85509643c1e26f5675eb96d56c85e` — does NOT match `67107f75...`

**Acquisition log on corpus branch:**
- `tee-independent-scientific-corpus/provenance/acquisition_log_2026-08-11.jsonl` — 2,800 lines
- Contains 256 unique source IDs (255 accepted, 2,545 rejected)
- Part of the 3,900 MOCK corpus infrastructure test
- Does NOT contain 3,210 sources
- Does NOT match the claimed hash

**Tags:** 2 tags exist (`proposal-composer-gen0`, `stage-1-measurement-integrity-baseline`). Neither contains a source manifest.

**Releases:** 0 releases (confirmed via GitHub API).

### 2.3 Hash as git object

- `git cat-file -t 67107f75` in corpus repo → "fatal: Not a valid object name"
- `git cat-file -t 67107f75` in main TEE repo → "fatal: Not a valid object name"

The hash `67107f75` is not a git object (blob, tree, commit, or tag) in either repository.

### 2.4 Hash as content

- In the main TEE repo: the string `67107f75` does NOT appear in any file in any branch
- In the corpus repo: the string `67107f75` appears ONLY in:
  - `CORPUS_MANIFEST.json` (as the value of `source_manifest_sha256` field)
  - `CORPUS_READINESS_REPORT_V1.md` (as a quoted hash value)
  - `PROVENANCE_SUMMARY.json` (as the value of `source_manifest_sha256` field)

In all three cases, it appears as a CLAIM about a hash, never as the hash of an actual file that exists in the repository.

---

## 3. Attempted Hash Reproduction

Tried to reproduce `67107f753251a1a0109a18dd2be8cc9c6c07e6e05514debfc1b52bb817e872ff` from:

| Source | SHA-256 | Match? |
|---|---|---|
| CORPUS_MANIFEST.json (raw bytes) | `3df8a1fb...` | NO |
| CORPUS_MANIFEST.json (canonical JSON, sort_keys, compact, ensure_ascii=False) | `81293b26...` | NO |
| PROVENANCE_SUMMARY.json (canonical JSON) | `63b5daa2...` | NO |
| DOMAIN_DISTRIBUTION.json (raw bytes) | `7665bcc0...` | NO |
| All validation JSON files (raw + canonical) | various | NO |
| Concatenation of all manifest files | various | NO |
| String "3210" | `a7a057f8...` | NO |
| Empty bytes | `e3b0c448...` | NO |

**The claimed hash cannot be reproduced from any combination of files in the repository.**

---

## 4. Conclusion: NOT FOUND

The source manifest artifact with SHA-256 `67107f753251a1a0109a18dd2be8cc9c6c07e6e05514debfc1b52bb817e872ff` **does not exist in any searched location**:

- ❌ Not in the corpus repo's only branch (`main`)
- ❌ Not in the corpus repo's history (25 commits, all searched)
- ❌ Not in the corpus repo's git object database (all blobs checked)
- ❌ Not in the corpus repo's tags (zero tags)
- ❌ Not in the corpus repo's releases (zero releases)
- ❌ Not in the corpus repo's Git LFS (LFS not installed)
- ❌ Not in the main TEE repo's 5 branches
- ❌ Not in the main TEE repo's 2 tags
- ❌ Not in the main TEE repo's releases (zero releases)
- ❌ Not as a git object hash in either repo
- ❌ Not as content in any file in the main TEE repo

The hash exists only as a CLAIMED value in three manifest documents in the corpus repo. The underlying artifact it claims to represent **was never committed to any repository**.

---

## 5. Scientific Conclusion

Per the custodian's directive:

> If not found, then the scientific conclusion is:
> "The 3210 corpus was specified but not preserved."

**This is the conclusion.** The 3,210-source corpus was specified in manifest documents but the underlying source manifest file was never preserved in any accessible location.

The custodian's directive continues:

> The correct response is not to reconstruct it from memory or recreate from APIs because that changes the sampling event.
>
> It becomes:
> TEE-ISC-v0.2
> new acquisition
> new seed
> new provenance
> new freeze

**The coder concurs with this assessment.** The 3,210-source corpus as specified cannot be frozen because the underlying artifact does not exist. Any reconstruction would be a new sampling event with a new identity.

---

## 6. Summary of Both Repositories' Corpus State

| Corpus | Location | Source data exists? | Admissibility |
|---|---|---|---|
| 3,900-source corpus (TEE-ISC-2025-001) | Main TEE repo, branch `independent-scientific-corpus-construction-75b04` | YES (3,900 abstracts + 3,900 metadata + 3,900 hashes) | **REJECTED — MOCK / NON-ADMISSIBLE** (manifest says "Mock data generated for infrastructure testing") |
| 3,210-source corpus (tee-independent-scientific-corpus) | Corpus repo, branch `main` | **NO** (corpus dirs empty, no source manifest file) | **NOT FROZABLE** (artifact missing, hash unverifiable) |

**Neither corpus is currently admissible for North Star evaluation.**

---

## 7. Coder's Recommendation

The coder recommends the custodian authorize a **fresh acquisition** under a new identity:

```
TEE-ISC-v0.2
- new sampling seed
- new acquisition window
- new provenance chain
- source manifest committed to repository BEFORE any validation
- hash computed and recorded from the actual committed file
- validation executed against the committed artifact
- freeze only after artifact + hash + validation all reconcile
```

This ensures the artifact preservation problem that affected v0.1 does not recur.

---

## Standing Down

Per custodian directive:
- No modifications made ✓
- No benchmark work ✓
- No TEE exposure ✓
- No pairability ✓
- No new acquisition initiated ✓

This report is the only artifact produced. Awaiting custodian decision on whether to authorize TEE-ISC-v0.2 acquisition or pursue other locations for the v0.1 artifact.
