# Graph Snapshot Specification (Issue #5, Phase 5)

Generated: 2026-08-13T00:58:41.628035+00:00

## Live vs Frozen Separation

- **Live ingestion**: continuous, mutable, growing. The 'evidence fabric'.
- **Frozen experimental snapshots**: immutable, content-addressed, time-anchored.

A live update can **never** mutate a frozen experimental snapshot.

## Required Snapshot Fields (per directive)

Every snapshot MUST include:

1. `source_registry_hash` — SHA-256 of the SOURCE_REGISTRY.json content
2. `connector_versions` — version string of each connector used
3. `query_manifest` — the queries that produced this snapshot
4. `retrieval_timestamps` — when each source was last harvested
5. `cursors` — per-source cursor for resumability
6. `source_hashes` — per-record raw payload hashes
7. `normalized_hashes` — per-record normalized content hashes
8. `provenance` — full provenance chain per record
9. `cutoff` — the temporal cutoff (evidence must be strictly before this)
10. `snapshot_hash` — SHA-256 of the entire snapshot manifest

## Patent Normalization (Phase 6)

14 distinct fields kept separate. A patent family is NEVER collapsed into one record.

## Paper Normalization (Phase 7)

12 distinct fields kept separate. A work may have multiple preprint versions and published articles.

## Cross-Corpus Edge Types (Phase 8)

8 explicit edge types. NO generic RELATED_TO:

- `AFFILIATION_MATCH`
- `AUTHOR_INVENTOR_MATCH`
- `BIBLIOGRAPHIC_MATCH`
- `DIRECT_ID_MATCH`
- `INFERRED_BRIDGE`
- `OFFICE_CITATION`
- `SEMANTIC_MATCH`
- `TOPIC_ALIGNMENT`

## Integrity Firewall (Phase 10)

12 test scenarios. Every failure quarantines the record.

- `APP_PUB_GRANT_CONFUSION`
- `IMPOSSIBLE_CHRONOLOGY`
- `PROVENANCE_LOSS`
- `TRANSLATION_CORRUPTION`
- `HYPOTHESIS_OBSERVATION_CONFLATION`
- `CITATION_DIRECTION_ERROR`
- `FAMILY_MERGE_ERROR`
- `CLAIM_EXPERIMENT_CONFLATION`
- `SEMANTIC_AS_DIRECT`
- `POST_FREEZE_MUTATION`
- `CUTOFF_LEAKAGE`
- `DUPLICATE_ID`

## Intersection Engine (Phase 9)

11 indexed search patterns with beam search + budget tracking:

- `1p1pat`
- `2p1pat`
- `1p2pat`
- `2p2pat`
- `p_pat_report`
- `p_pat_dataset`
- `p_pat_code`
- `p_pat_standard`
- `pfail_pwork`
- `platlim_sci_anom`
- `oldp_newpat`

Budget defaults: max_nodes_visited=10000, max_candidates=1000, beam_width=50.