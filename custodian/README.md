# Custodian Package — Independent Benchmark Custody Infrastructure

**Status:** INFRASTRUCTURE READY — BENCHMARK NOT SEALED
**Custodian Version:** 1.0.0

---

## What This Is

The custodian package implements an independent benchmark-custody pipeline for the TEE evaluation system. TEE must never control benchmark construction, sampling, answer keys, or sealing.

This is **custody infrastructure**, not a benchmark. No real benchmark has been constructed or sealed.

---

## Lifecycle

```
SOURCE CORPUS → SOURCE REGISTRY → CASE CANDIDATE GENERATOR →
EXTERNAL SEED / DETERMINISTIC SAMPLER → BENCHMARK CONSTRUCTION →
INDEPENDENT ANSWER / VERIFICATION KEY → BLIND FIXTURE →
MANIFEST + HASHES → SEALED BENCHMARK → TEE
```

---

## State Machine

```
DRAFT → VALIDATED → CONSTRUCTED → SEALED
```

Once `SEALED`: cases cannot be added/removed, sampling cannot change, answer key cannot change, blind fixture cannot change, manifest cannot change. Any modification must produce a new benchmark version.

---

## Architecture

```
custodian/
├── README.md                           (this file)
├── schema/
│   ├── source.schema.json              (JSON schema for source registry entries)
│   ├── case.schema.json                (JSON schema for benchmark cases)
│   └── manifest.schema.json            (JSON schema for sealed benchmark manifest)
├── src/
│   ├── __init__.py
│   ├── hasher.py                       (SHA-256 for all artifacts, canonical JSON)
│   ├── source_registry.py              (source provenance tracking)
│   ├── case_schema.py                  (case validation + blind fixture safety)
│   ├── sampler.py                      (deterministic seeded sampling, no TEE dependency)
│   ├── benchmark_builder.py            (state machine: DRAFT → VALIDATED → CONSTRUCTED → SEALED)
│   ├── seal.py                         (sealing + attestation generation)
│   └── audit_trail.py                  (append-only audit trail)
├── tests/
│   ├── __init__.py
│   └── test_custodian.py               (40 tests, all passing)
└── fixtures/
    └── synthetic/
        └── synthetic_fixture.py        (SYNTHETIC_TEST_FIXTURE_ONLY, NOT_FOR_EVALUATION)
```

---

## Tests (40/40 PASS)

| Test Category | Tests | Status |
|---------------|-------|--------|
| Hasher (determinism, canonical JSON, tamper detection) | 5 | ✅ PASS |
| Source Registry (register, verify, provenance) | 5 | ✅ PASS |
| Case Schema (validation, blind safety, leak detection) | 6 | ✅ PASS |
| Sampler (determinism, seed sensitivity, insufficient corpus, TEE rejection) | 7 | ✅ PASS |
| Benchmark Builder (state machine, immutability, blind/answer separation) | 7 | ✅ PASS |
| Sealing (attestation, infrastructure state) | 2 | ✅ PASS |
| Audit Trail (append-only, no nondeterministic timestamps) | 2 | ✅ PASS |
| Tamper Detection (blind fixture, answer key, source content) | 3 | ✅ PASS |
| Independence (dependent cluster detection) | 1 | ✅ PASS |
| Provenance (source tracing, missing provenance) | 2 | ✅ PASS |
| **Total** | **40** | **✅ ALL PASS** |

---

## Critical Properties

1. **TEE cannot control construction** — sampler has no dependency on TEE output
2. **Answer key never in blind fixture** — automated tests prove this
3. **Deterministic** — same corpus + seed + config = same benchmark
4. **Immutable after sealing** — sealed benchmarks cannot be modified
5. **Insufficient corpus fails loudly** — no padding to N≥100
6. **Independence enforced** — max 1 case per independence_group
7. **Domain coverage enforced** — <4 domains rejected
8. **No nondeterministic timestamps in canonical proof** — externally provided

---

## How to Construct a Real Benchmark (When Corpus Arrives)

```python
from custodian.src.source_registry import SourceRegistry
from custodian.src.case_schema import BenchmarkCase
from custodian.src.benchmark_builder import Benchmark
from custodian.src.seal import seal_benchmark

# 1. Register sources
registry = SourceRegistry()
for source in corpus_sources:
    registry.register(
        source_id=source["id"],
        domain=source["domain"],
        title=source["title"],
        origin=source["origin"],
        source_uri=source["uri"],
        content=source["content"],
        version=source["version"],
    )

# 2. Create benchmark in DRAFT state
benchmark = Benchmark(benchmark_id="TEE-BENCHMARK-0001")

# 3. Add cases (must be >=100, >=4 domains, independent)
for case_data in corpus_cases:
    benchmark.add_case(BenchmarkCase(**case_data))

# 4. Validate (DRAFT → VALIDATED)
benchmark.transition_to_validated()

# 5. Construct (VALIDATED → CONSTRUCTED)
benchmark.transition_to_constructed(
    source_manifest_hash=registry.manifest_hash(),
    seed_hash=external_seed_hash,
    corpus_hash=corpus_hash,
    construction_parameters={"target_n": 100, "min_domains": 4},
)

# 6. Seal (CONSTRUCTED → SEALED)
attestation = seal_benchmark(benchmark)

# 7. Export TEE package (blind fixture only)
tee_package = benchmark.get_tee_package()
```

---

## Remaining Dependency

**Real corpus.** The custodian machinery is built and tested, but no real benchmark has been constructed or sealed. The next phase begins only when a real corpus is supplied.
