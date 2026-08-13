# Source Discovery & Connector Fabric — Preregistration (Issue #5)

**Status:** INFRASTRUCTURE COMPLETE (offline mode). LIVE_INGEST = FALSE.
**PSCD-1:** FROZEN. NOT TOUCHED.
**A2:** NOT AUTHORIZED.
**North Star:** UNPROVEN.

---

## 1. Objective

Build a **living evidence fabric** that continuously discovers, validates,
and connects independent evidence ecosystems — papers, patents, technical
reports, standards, datasets, code, experiments, clinical trials, products,
and failure records — into a single graph with typed provenance.

Per CEO directive: "don't optimize for the maximum number of domains.
Optimize for the maximum number of **independent evidence systems that can
constrain one another**."

This fabric is the substrate on which the cross-corpus pilot (Issue #4)
and PSCD-1 (frozen) operate. It does NOT claim discovery. It does NOT
modify frozen artifacts.

---

## 2. Architecture

```
100+ REAL source candidates
  (papers, patents, tech reports, standards, datasets, code,
   experiments, clinical trials, products, failure records)
         |
         v
    source_validator
    (structural + live)
         |
    +----------------+----------------+
    |                |                |
    v                v                v
 connector_base   provenance      multilingual
 (resumable,      (20 typed        (originals retained
  idempotent,      predicates,      + translations,
  content-         no RELATED_TO)    language-tagged)
  addressed)
         |
         v
    failure_recorder
    (append-only; API blocks,
     schema changes, license issues)
         |
         v
    snapshot_manager
    (LIVE ingestion vs FROZEN
     experimental snapshots —
     separate worlds, AES-GCM,
     content-addressed, tamper-evident)
         |
         v
    domain_map (30 domains,
     6 universes: Matter/Energy/Life/
     Machine/Information/Planet)
         |
         v
    knowledge_distance
    (6 dimensions; search
     prioritization ONLY,
     NOT evidence of truth)
         |
         v
    cross_evidence_motifs
    (10 motifs: paper+patent+standard,
     paper+patent+dataset, ...)
         |
         v
    forensic_audit (12 checks)
```

---

## 3. The 132 Real Source Candidates

By evidence type:
| Type | Count |
|------|-------|
| paper | 23 |
| patent | 13 |
| technical_report | 12 |
| standard | 11 |
| dataset | 28 |
| code | 13 |
| experiment | 12 |
| clinical_trial | 6 |
| product | 7 |
| failure_record | 7 |
| **Total** | **132** |

Primary sources: 107. Aggregators/secondary: 21. Archive/federation: 4.

Each source carries: name, URL, access_method, license, evidence_tier
(A-I per CONSTITUTION), universes, coverage_notes, auth_required,
rate_limit, metadata_format, primary_or_secondary, status.

---

## 4. The 30-Domain / 6-Universe Map

| Universe | Domains |
|----------|---------|
| **Matter** (7) | materials, chemistry, metallurgy, polymers, textiles, packaging, nanotechnology |
| **Energy** (6) | batteries, nuclear, renewables, power_electronics, combustion, hydrogen |
| **Life** (6) | biotechnology, pharmaceuticals, medicine, medical_devices, agriculture, food_science |
| **Machine** (6) | mechanical, robotics, manufacturing, aerospace, transportation, civil_engineering |
| **Information** (7) | computing, ai, semiconductors, electronics, photonics, telecom, quantum |
| **Planet** (6) | climate, environmental, water, ocean, geoscience, atmospheric |

The killer graph is the cross-product: Matter × Life × Machine × Information × Planet × Energy.

---

## 5. Typed Provenance Vocabulary (20 predicates — NO RELATED_TO)

| Predicate | Meaning | Cross-corpus? | Empirical? |
|-----------|---------|---------------|-----------|
| cites | document A cites B (with EPO role) | yes | no |
| uses_material | A uses material B | no | no |
| uses_mechanism | A invokes mechanism B | no | no |
| uses_process | A uses process B | no | no |
| validates | A experimentally validates B | no | **yes** |
| refutes | A experimentally refutes B | no | **yes** |
| implements | code A implements algorithm B | yes | no |
| extends | A extends work B | yes | no |
| derived_from | A derived from B | yes | no |
| reproduced_from | A reproduces result B | yes | **yes** |
| failed_to_reproduce | A failed to reproduce B | yes | **yes** |
| cites_standard | A cites standard B as constraint | yes | no |
| uses_dataset | A uses dataset B | yes | no |
| cites_failure | A cites failure record B | yes | no |
| product_of | product A is product of patent B | yes | no |
| regulatory_basis_of | standard A is basis of product B | yes | no |
| funded | grant A funded document B | yes | no |
| author_of | researcher A authored document B | no | no |
| affiliated_with | researcher A affiliated with org B | no | no |
| translation_of | document A is translation of B | yes | no |

---

## 6. Connector Discipline (4 enforced invariants)

1. **Resumable**: a failed/partial harvest can be continued via HarvestState.
2. **Idempotent**: re-running the same query yields the same canonical records
   (same `normalized_hash` set).
3. **Provenance-preserving**: every HarvestedRecord carries `source_id`,
   `harvested_at`, `raw_payload_hash`.
4. **No silent substitution**: if a primary source fails, raise HarvestError
   — do NOT fall back to a secondary source. The failure_recorder captures
   the error; the gap is reported honestly.

---

## 7. Live vs Frozen Separation

- **LIVE ingestion**: continuous, mutable, growing. The "evidence fabric".
  Records are added, updated, re-harvested.
- **FROZEN experimental snapshots**: immutable, content-addressed,
  time-anchored. Created at a specific UTC cutoff. Used for any discovery
  claim. A snapshot is what a pilot runs against.

A snapshot is created by:
1. Content-hash-indexed copy of the live corpus at cutoff.
2. Immutable manifest (snapshot.json) listing every record's hash.
3. Root hash (SHA-256 of all record hashes joined).
4. SHA-256 sidecar for tamper detection.
5. Sealing (AES-GCM in production; placeholder in offline pilot).

`verify_snapshot` performs 6 checks: SNAPSHOT_EXISTS, HASH_SIDECAR_EXISTS,
HASH_MATCHES, ROOT_HASH_VALID, ALL_RECORDS_PRESENT,
RECORD_HASHES_MATCH_FILENAMES, RECORD_COUNT_CONSISTENT.

---

## 8. Failure Recording (append-only)

10 failure types: API_BLOCKED, RATE_LIMITED, LICENSE_BLOCKED, SCHEMA_CHANGED,
AUTH_REQUIRED, SOURCE_DEPRECATED, NETWORK_ERROR, PARSE_ERROR, PARTIAL_HARVEST,
UNAVAILABLE, UNKNOWN.

Failures are NEVER silently dropped. The log is JSONL, append-only.

---

## 9. Multilingual Handling

- Original-language text is ALWAYS retained. Never overwritten.
- Translations stored as separate records linked via `translation_of`.
- Every record carries `language` (ISO 639-1) and `original_language`.
- 29 supported languages.
- A translation must declare its engine and (optionally) confidence.

---

## 10. Knowledge Distance (search prioritization, NOT evidence)

6 dimensions:
- domain_distance (0-5)
- mechanism_distance (Jaccard, 0.0-1.0)
- temporal_distance (years)
- evidence_distance (0 or 1)
- implementation_distance (Jaccard)
- constraint_distance (Jaccard)

Aggregate = weighted sum (weights sum to 1.0). Used ONLY for ranking
candidates by "interestingness" — NEVER as evidence that a candidate is correct.

Per CEO directive: "do not call high-distance candidates discoveries."

---

## 11. Cross-Evidence Motifs (10 new motifs)

| # | Motif | Evidence layers |
|---|-------|-----------------|
| C01 | paper + patent + standard | standard constrains what patent can claim |
| C02 | paper + patent + dataset | dataset adjudicates paper's claim |
| C03 | paper + patent + tech_report | report has detail neither has |
| C04 | paper + patent + code | code reveals what was actually implemented |
| C05 | paper + patent + failure | failure contradicts patent's success claim |
| C06 | paper + paper + patent + dataset | two papers disagree; dataset adjudicates |
| C07 | paper + patent + material + process | unclaimed (material, process) combo |
| C08 | paper + patent + clinical_trial | trial tests patent's medical claim |
| C09 | paper + patent + product | product exists but no paper validates |
| C10 | paper + patent + experiment | experimental DB can falsify patent |

Each motif produces a CrossEvidenceCandidate with typed ProvenanceEdges,
falsifiable prediction, and knowledge_distance score.

---

## 12. Forensic Audit (12 checks)

1. REPORT_EXISTS
2. HASH_SIDECAR_EXISTS
3. HASH_MATCHES (tamper detection)
4. LIVE_CHECK_HONEST (must be False in offline mode)
5. REAL_DATA_SEAL_HONEST (must be False without live ingest)
6. NOT_CLAIMED_AS_SCIENTIFIC (must be False)
7. MIN_100_SOURCES
8. ALL_SOURCES_STRUCTURALLY_VALID
9. SNAPSHOT_VERIFIED
10. MIN_30_DOMAINS
11. SIX_UNIVERSES
12. PROVENANCE_VOCAB_RICH (>=15 predicates)

---

## 13. Honest Boundaries

| Item | Status |
|------|--------|
| 132 real source candidates | COMPLETE |
| 30-domain / 6-universe map | COMPLETE |
| 20 typed provenance predicates | COMPLETE |
| 10 cross-evidence motifs | COMPLETE |
| Snapshot discipline (live vs frozen) | COMPLETE |
| Failure recorder (append-only) | COMPLETE |
| Multilingual handler | COMPLETE |
| Knowledge distance (search only) | COMPLETE |
| 57/57 tests | PASS |
| 12/12 forensic audit checks | PASS |
| LIVE_INGEST | FALSE (no credentials; framework ready) |
| REAL_DATA_SEAL | FALSE (no live ingest) |
| IS_SCIENTIFIC_RESULT | FALSE (always) |
| PSCD-1 frozen | YES (not touched) |
| A2 authorized | NO |

---

## 14. What This Fabric Does NOT Do

- Does NOT make live HTTP calls (offline mode only).
- Does NOT ingest real data (no credentials).
- Does NOT claim scientific discovery.
- Does NOT modify frozen PSCD-1 artifacts.
- Does NOT authorize A2.
- Does NOT use knowledge_distance as evidence of truth.
- Does NOT use generic RELATED_TO edges (forbidden in vocabulary).
- Does NOT silently substitute secondary for primary sources.
- Does NOT hide source failures (all recorded).

---

## 15. The Only Path to Live Ingest

1. Operator sets environment variables:
   `OPENALEX_EMAIL`, `CROSSREF_API_TOKEN`, `EPO_OPS_KEY`, `EPO_OPS_SECRET`,
   `GITHUB_TOKEN`, `ZENODO_TOKEN`, `NIST_API_KEY`, ...
2. Run `python -m source_fabric.run_fabric --live`.
3. Each connector performs live HTTP harvest, records HarvestedRecord objects
   with raw_payload_hash + normalized_hash.
4. Failures recorded in `failure_log.jsonl` (append-only).
5. Snapshot taken at cutoff → cross_corpus pilot (Issue #4) runs on snapshot.
6. REAL_DATA_SEAL issued by external custodian.
7. Cross-corpus motifs + cross-evidence motifs run on real snapshot.
8. If STRUCTURAL_PASS: predictions sealed, outcomes awaited, results audited.

---

## 16. File Manifest

```
source_fabric/
  __init__.py
  source_registry.py       # 132 real source candidates
  domain_map.py            # 30 domains, 6 universes
  connector_base.py        # Connector, HarvestState, HarvestedRecord, HarvestError
  provenance.py            # 20 typed predicates, ProvenanceEdge, validation
  multilingual.py          # MultilingualText, translation pair validation
  failure_recorder.py      # append-only JSONL failure log (10 types)
  snapshot_manager.py      # live vs frozen separation, 6-check verification
  source_validator.py      # structural validation, concrete connectors
  knowledge_distance.py    # 6-dimension distance (search only, not evidence)
  cross_evidence_motifs.py # 10 cross-evidence-type motifs
  orchestrator.py          # end-to-end pipeline + forensic audit
  run_fabric.py            # CLI entrypoint
  tests/
    test_fabric.py         # 57 negative-test-style tests
  reports/
    fabric_state.json      # immutable state report
    fabric_state.json.sha256
    source_validation_report.json
    empty_snapshot/        # snapshot machinery exercised (empty in offline)
    failure_log.jsonl      # empty in offline mode
```
