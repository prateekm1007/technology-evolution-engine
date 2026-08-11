# TEE Independent Scientific Corpus

## Overview

This repository contains an independently sourced scientific corpus for the Technology Evolution Engine (TEE) North Star evaluation.

**Critical**: This corpus was constructed *independently* of the TEE engineering team, without access to:
- TEE-generated hypotheses
- TEE rankings
- TEE source-pair candidates
- TEE benchmark labels
- TEE outputs or predictions

## Repository Structure

```
tee-independent-scientific-corpus/
│
├── README.md                          # This file
├── CORPUS_MANIFEST.json               # Corpus metadata and cryptographic commitment
├── PROVENANCE_POLICY.md               # Provenance collection and verification policy
├── SAMPLING_PROTOCOL.md               # Sampling methodology and reproducibility info
├── INDEPENDENCE_ATTESTATION.md        # Custodian independence attestation
│
├── corpus/
│   ├── metadata/                      # Source metadata records (JSON)
│   ├── abstracts/                     # Abstract texts
│   ├── fulltext/                      # Full-text URIs and content where available
│   └── hashes/                        # Content hashes (SHA-256)
│
├── provenance/                        # Acquisition logs and provider records
│
├── validation/
│   ├── duplicates.json                # Duplicate detection report
│   ├── exposure_audit.json            # Prior exposure audit
│   ├── contamination_audit.json       # Contamination risk audit
│   └── domain_audit.json              # Domain distribution audit
│
└── custodian/                         # CUSTODIAN ONLY - NOT FOR TEE ACCESS
    ├── benchmark_candidates/          # Candidate pair analysis
    ├── answer_keys/                   # Benchmark answer keys
    ├── adjudications/                 # Custodian adjudications
    └── seals/                         # Cryptographic seals
```

## Corpus Specifications

### Target Size
- **2,000–5,000** independently acquired source records
- Minimum **4 genuinely distinct scientific domains**
- Sufficient combinatorial material for 100+ legitimate cross-domain discovery problems

### Domain Coverage
The corpus spans multiple scientifically distinct disciplines including but not limited to:
- Physics
- Chemistry
- Materials Science
- Biology
- Computer Science
- Engineering (Mechanical, Electrical, Chemical)
- Energy Sciences
- Environmental Science
- Neuroscience
- Earth Science
- Mathematics
- Robotics

### Temporal Cutoff
A frozen publication cutoff date is documented in `CORPUS_MANIFEST.json`. All sources were published before this date.

### Data Sources
Primary providers:
1. OpenAlex
2. Crossref
3. Semantic Scholar
4. OpenAIRE
5. Institutional repositories
6. Discipline-specific repositories

## Access Levels

### Public-to-TEE Package
The TEE team receives only:
- `CORPUS_COMMITMENT.json`
- `CORPUS_SHA256.txt`
- `DOMAIN_DISTRIBUTION.json`
- `PROVENANCE_SUMMARY.json`
- `INDEPENDENCE_ATTESTATION.md`

### Custodian Package (Restricted)
Contains full corpus, answer keys, adjudications, and seals. **Never mounted into TEE execution environment.**

## Reproducibility

All sampling procedures are:
- Externally seeded
- Documented in `SAMPLING_PROTOCOL.md`
- Capable of independent reproduction

See `SAMPLING_PROTOCOL.md` for:
- Random seed
- Sampling algorithm
- Population queried
- Query parameters
- Provider information
- Acquisition timestamps
- Inclusion/exclusion rules

## Quality Assurance

Each source record includes:
- source_id
- title
- authors
- DOI
- publisher
- publication date
- source URI
- repository URI (where applicable)
- abstract
- full-text URI (where legally available)
- acquisition timestamp
- provider
- version
- SHA-256 content hash
- license/access information
- provenance information

Duplicate detection performed for:
- Exact content hashing
- DOI duplicates
- Bibliographic duplicates
- Title similarity
- Near-duplicates

All exclusions recorded with machine-readable reasons.

## Independence Attestation

This corpus was constructed without access to TEE-generated hypotheses, rankings, source-pair candidates, benchmark labels, or outputs. Source selection was governed by pre-declared sampling procedures.

See `INDEPENDENCE_ATTESTATION.md` for the full custodian attestation.

## Version Control

Any correction to the frozen corpus requires a **new corpus version**, not a silent edit.

Corpus version and cryptographic seal documented in `CORPUS_MANIFEST.json`.

## Contact

Custodian: Independent Scientific Corpus Commission
Repository: prateekm1007/tee-independent-scientific-corpus

---

*This corpus provides TEE with a genuine opportunity to demonstrate discovery capability—and an equally genuine opportunity to fail.*
