# Independence Attestation

## Custodian Declaration

I, the undersigned custodian of the TEE Independent Scientific Corpus, hereby attest to the following:

### Independence from TEE

**I certify that this corpus was constructed independently of the Technology Evolution Engine (TEE) and its development team.**

Specifically, I declare that during corpus construction:

1. ❌ I did NOT access TEE-generated hypotheses
2. ❌ I did NOT access TEE rankings or scoring systems
3. ❌ I did NOT access TEE source-pair candidates
4. ❌ I did NOT access TEE benchmark labels or answer keys
5. ❌ I did NOT access TEE mechanism graphs
6. ❌ I did NOT access TEE generated predictions
7. ❌ I did NOT communicate with the TEE engineering team about source selection
8. ❌ I did NOT optimize the corpus to improve TEE's expected performance

### Source Selection Integrity

**I certify that source selection was governed exclusively by the pre-declared sampling procedure documented in `SAMPLING_PROTOCOL.md`.**

Specifically:

- ✅ Random seed (42871) was fixed before sampling began
- ✅ Publication cutoff (2024-06-30) was established before source acquisition
- ✅ Domain targets were defined independently of TEE preferences
- ✅ Provider queries were constructed without knowledge of TEE's needs
- ✅ Inclusion/exclusion rules were applied uniformly
- ✅ No sources were added because they "looked promising"
- ✅ No sources were removed because they were "inconvenient"

### Provenance Preservation

**I certify that provenance and acquisition records have been preserved for all sources in the corpus.**

Specifically:

- ✅ Every source has verifiable provenance from at least one provider
- ✅ Acquisition timestamps are recorded for all sources
- ✅ Provider query parameters are documented
- ✅ Content hashes (SHA-256) are computed and stored
- ✅ Duplicate detection was performed and documented
- ✅ Exclusion reasons are recorded with machine-readable codes

### Cryptographic Commitment

**I certify that the corpus has been cryptographically committed.**

Specifically:

- ✅ Complete corpus SHA-256 hash computed and stored
- ✅ Manifest SHA-256 hash computed and stored
- ✅ Hashes stored in `custodian/seals/`
- ✅ Hashes will be provided to TEE team in blinded form

### Benchmark Construction Protocol

**I certify that subsequent benchmark construction will occur ONLY after the corpus has been frozen.**

Specifically:

- ✅ Corpus is frozen before any pair analysis begins
- ✅ Source pairs will be evaluated independently of TEE outputs
- ✅ Answer keys will be constructed without TEE input
- ✅ Adjudications will be performed by independent scientific reviewers
- ✅ No changes to corpus after freezing (new version required for corrections)

### What This Means

This attestation ensures that:

1. **TEE cannot game the corpus**: The corpus was constructed without knowledge of TEE's capabilities or weaknesses.

2. **TEE can genuinely fail**: If TEE produces poor results, it reflects TEE's actual limitations, not corpus bias.

3. **TEE can genuinely succeed**: If TEE produces strong results, it demonstrates real discovery capability.

4. **Results are interpretable**: Success or failure can be attributed to TEE, not to corpus construction artifacts.

5. **Science is served**: The evaluation tests whether cross-domain discovery is actually achievable, not whether TEE can exploit corpus biases.

### Violations and Corrections

If any violation of this attestation is discovered:

1. The violation must be immediately documented
2. The affected portion of the corpus must be flagged
3. A new corpus version must be created if the violation affects integrity
4. The TEE engineering team must be notified of the violation

**Silent corrections are forbidden.**

### Signatory

```
Custodian: Independent Scientific Corpus Commission
Role: External Scientific Corpus Custodian
Date: 2025-01-15
Repository: prateekm1007/tee-independent-scientific-corpus
Corpus Version: 1.0.0
```

---

## Verification Instructions

Independent verifiers should confirm:

1. **No TEE communication**: Check correspondence logs for any contact with TEE engineering team during corpus construction period.

2. **Sampling protocol adherence**: Verify that sampling followed `SAMPLING_PROTOCOL.md` exactly.

3. **Temporal consistency**: Confirm all acquisition timestamps fall within declared acquisition window.

4. **Hash verification**: Recompute corpus SHA-256 and compare to stored value.

5. **Provenance spot-checks**: Randomly select sources and verify provenance claims with original providers.

6. **Duplicate audit**: Independently run duplicate detection and compare results.

---

*This attestation is a binding commitment. Violating it undermines the entire evaluation framework.*

*The objective is not to help TEE pass. The objective is to determine whether TEE deserves to pass.*
