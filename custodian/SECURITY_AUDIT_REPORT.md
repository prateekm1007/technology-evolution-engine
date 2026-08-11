# Custodian Security Audit — Forensic Report

**Date:** 2026-08-10
**Commit audited:** f308b3c
**Auditor:** Super Z (coder), under CTO direction
**Test suite:** 84 tests (40 happy-path + 44 adversarial) — ALL PASS

---

## Threat Model

> **Assume the TEE team is curious, the benchmark constructor makes mistakes, files can be inspected, APIs can be called incorrectly, and developers can accidentally leak information. Can the custodian still preserve the blind experiment?**

### Adversary Capabilities
- TEE team can inspect all files on the filesystem
- TEE team can call any Python API
- TEE team can read serialized JSON files
- TEE team can modify Python objects in memory (bypassing state machine)
- Benchmark constructor can make mistakes (duplicate cases, wrong domain labels)
- Developers can accidentally include answer-key fields in blind fixtures

### Adversary Motivations
- TEE team wants to see the answer key to improve their system
- TEE team wants to influence case selection to favor their system
- Benchmark constructor wants to make the benchmark "work" (even if it means cutting corners)

---

## Attack Results (12 Vectors)

### Attack 1: Can TEE obtain answer key through any channel? — **DEFENDED**

| Channel | Result |
|---------|--------|
| TEE package (get_tee_package()) | ✅ No answer key (automated safety check) |
| Blind fixture (get_blind_fixture()) | ✅ No ground_truth field |
| Blind fixture content (mechanism text) | ✅ Secret mechanisms not present |
| Answer key vs blind fixture hash | ✅ Different hashes (different content) |
| Exception messages | ✅ No ground truth in error strings |
| Audit trail | ✅ No ground truth in audit events |

**Verdict:** The TEE package and blind fixture are clean. The answer key is structurally separated.

### Attack 2: Can construction indirectly consume TEE outputs? — **DEFENDED**

| Attack | Result |
|--------|--------|
| `tee_score` in params | ✅ Rejected (TEEDependencyError) |
| `tee_outputs` in params | ✅ Rejected |
| `tee_rankings` in params | ✅ Rejected |
| `tee_model_identity` in params | ✅ Rejected |
| Nested TEE reference | ✅ Detected (recursive check) |
| TEE in list of dicts | ✅ Detected |
| Case-insensitive (`TEE_SCORE`) | ✅ Detected |

**Verdict:** All TEE references are detected and rejected, including nested and case-variant forms.

### Attack 3: Can seed be manipulated after seeing candidates? — **DEFENDED**

| Property | Result |
|----------|--------|
| Seed hash computed from external seed | ✅ Not from candidates |
| Different seeds → different hashes | ✅ |
| Seed hash independent of candidates | ✅ Same seed, different candidates → same hash |
| Empty seed rejected | ✅ |

**Verdict:** The seed is committed before selection and cannot be manipulated by candidate content.

### Attack 4: Can sealed benchmark be mutated? — **PARTIALLY DEFENDED**

| Attack | Result |
|--------|--------|
| Add case after seal | ✅ Blocked (SealStateError) |
| State transition from SEALED | ✅ Blocked |
| Shallow copy mutation | ✅ Original unaffected |
| Deep copy mutation | ✅ Original unaffected + hash unchanged |
| Direct attribute mutation (case_id) | ✅ Manifest hash detects change |
| Direct attribute mutation (sealed_at) | ✅ Manifest hash detects change |

**⚠️ KNOWN WEAKNESS:** Python allows direct attribute assignment (`bm.cases[0].case_id = "TAMPERED"`). The state machine cannot prevent this. However, any such mutation invalidates the manifest hash, so a verifier recomputing the hash would detect the tampering. **The defense is cryptographic (hash verification), not access control.**

### Attack 5: Can blind fixture be reconstructed into answer key? — **DEFENDED**

| Channel | Result |
|---------|--------|
| verification_method field | ✅ Describes method, not answer |
| Provenance metadata | ✅ No ground truth content |
| Blind fixture hash | ✅ Cannot reverse SHA-256 to get answer key |

**Verdict:** The blind fixture contains insufficient information to reconstruct the answer key.

### Attack 6: Can provenance be altered without invalidating manifest? — **DEFENDED**

| Attack | Result |
|--------|--------|
| Change provenance constructor | ✅ Manifest hash changes |
| Change source content | ✅ Content hash mismatch detected |

**Verdict:** Any provenance change invalidates the manifest hash.

### Attack 7-8: Can duplicates/near-duplicates evade independence? — **PARTIALLY DEFENDED**

| Attack | Result |
|--------|--------|
| Same independence_group, different case_id | ✅ Detected (DEPENDENT_CASE_CLUSTER) |
| Same input_material, different independence_group | ⚠️ **NOT DETECTED** |
| Near-identical problems with different groups | ⚠️ **NOT DETECTED** |

**⚠️ KNOWN WEAKNESS:** The validator checks `independence_group` labels, not content similarity. A constructor could create 20 cases with identical source documents but different `independence_group` labels, and they would pass validation. **This is a semantic gap that must be addressed by custodian discipline, not code alone.**

### Attack 9: Can domain labels be manipulated? — **PARTIALLY DEFENDED**

| Attack | Result |
|--------|--------|
| "physics" vs "Physics" vs "PHYSICS" | ⚠️ **Treated as 3 different domains** |
| "fluid_mechanics" vs "fluid-mechanics" | ⚠️ **Treated as 2 different domains** |

**⚠️ KNOWN WEAKNESS:** Domain labels are string-compared with no canonicalization. A constructor could manufacture the ≥4-domain requirement by using trivial label variants. **This must be addressed by custodian discipline and domain-label review.**

### Attack 10: Can benchmark be sealed without all 9 requirements? — **PARTIALLY DEFENDED**

| Attack | Result |
|--------|--------|
| Seal from DRAFT (skip VALIDATED) | ✅ Blocked |
| Seal from VALIDATED (skip CONSTRUCTED) | ✅ Blocked |
| Seal without hashes (bypass state machine) | ⚠️ **Possible if state set directly** |
| Seal with leaked blind fixture | ✅ Blocked (safety check before sealing) |

**⚠️ KNOWN WEAKNESS:** If someone sets `bm.seal_state = CONSTRUCTED` directly (bypassing `transition_to_constructed`), the blind_fixture_hash and answer_key_hash would be empty. `seal_benchmark` would still seal it. **The defense against this is the custodian's discipline in using the state machine correctly, not the code alone.**

### Attack 11: Can TEE performance influence selection implicitly? — **DEFENDED**

| Attack | Result |
|--------|--------|
| Deeply nested TEE reference | ✅ Detected (recursive check) |
| TEE in list of dicts | ✅ Detected |
| TEE-related sampler parameter names | ✅ None exist (inspected) |

**Verdict:** The sampler has no TEE-related parameters, and all construction params are recursively checked.

### Attack 12: Does filesystem enforce separation? — **NOT DEFENDED BY CODE**

**⚠️ CRITICAL KNOWN WEAKNESS:** The custodian provides **logical separation** (different data structures, different hashes, automated safety checks) but NOT **physical separation** (filesystem permissions, separate directories, access control lists).

If the TEE process has filesystem access to the directory where the answer key is stored, it can read it. The custodian cannot enforce filesystem permissions from Python.

**Mitigation:** The deployment architecture must ensure:
- The answer key is stored in a directory the TEE process cannot read
- The blind fixture is stored in a directory the TEE process CAN read
- Filesystem permissions (chmod 600, separate user accounts) enforce the boundary
- OR: the custodian and TEE run on separate machines with no shared filesystem

**This is a deployment responsibility, not a code responsibility.**

---

## Summary of Findings

### Defended (7 of 12)
1. ✅ Answer key leakage through API/objects
2. ✅ TEE output consumption in construction
3. ✅ Seed manipulation
4. ✅ Sealed benchmark mutation (cryptographic detection)
5. ✅ Blind-to-answer-key reconstruction
6. ✅ Provenance tampering
7. ✅ Implicit TEE dependency

### Known Weaknesses (5 of 12)
8. ⚠️ Near-duplicate content with different independence_groups not detected
9. ⚠️ Domain label variants not canonicalized
10. ⚠️ State machine bypass possible (direct attribute assignment)
11. ⚠️ Empty hash sealing possible if state set directly
12. ⚠️ Filesystem separation not enforced by code (deployment responsibility)

### Severity Assessment

| Weakness | Severity | Mitigation |
|----------|----------|------------|
| Near-duplicate evasion | MEDIUM | Custodian must manually review for content similarity. Add semantic similarity check in future version. |
| Domain label manipulation | MEDIUM | Custodian must use canonical domain labels. Add domain-label whitelist in future version. |
| State machine bypass | LOW | Manifest hash detects any mutation. Custodian must use state machine correctly. |
| Empty hash sealing | LOW | Custodian must use transition_to_constructed (not direct state assignment). Add hash-non-empty check in future version. |
| Filesystem separation | HIGH | **Deployment must enforce filesystem permissions.** Code cannot do this alone. |

---

## Verdict

> **Can the custodian preserve the blind experiment against a curious TEE team, a mistake-prone constructor, and accident-prone developers?**

**YES, with caveats:**

1. **Against API-level attacks:** YES. The TEE package, blind fixture, and all exported data are clean. Answer key fields are structurally excluded and automatically detected.

2. **Against TEE-output contamination:** YES. All TEE references in construction parameters are recursively detected and rejected.

3. **Against sealed-state mutation:** YES (cryptographically). Any mutation invalidates the manifest hash. A verifier recomputing the hash would detect tampering.

4. **Against filesystem-level attacks:** **NO — this is a deployment responsibility.** The code provides logical separation but not physical separation. The deployment must enforce filesystem permissions.

5. **Against semantic attacks (near-duplicates, domain variants):** **PARTIALLY.** The code detects structural duplicates but not semantic ones. Custodian discipline is required.

### Custody-Ready?

**YES, with deployment requirements:**
- The answer key must be stored in a location the TEE process cannot access
- The custodian must use the state machine correctly (not bypass it)
- The custodian must manually review for content similarity and domain-label validity
- The custodian must use canonical domain labels

**The code is custody-ready. The deployment must be custody-enforcing.**

---

## Test Results

```
84 tests, 0 failures, 0 errors, 0.15s

Happy-path tests: 40/40 PASS
Adversarial tests: 44/44 PASS
```
