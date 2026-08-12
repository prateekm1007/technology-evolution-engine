# PAIRABILITY_NOVELTY_AUDIT_V1 — Search Protocol

**Status:** FROZEN — pre-registered before execution
**Date:** 2026-08-11
**Universe manifest hash:** `d04a0cdcdc91dcbe424e6e366f49ebe6fd3668dd0039ca76abd70b92425f0184`
**Frozen pairs:** 182

---

## Purpose

For each of the 182 frozen candidate pairs, execute an independent literature search to determine whether the cross-domain relationship between Source A and Source B is already explicitly established in the scientific literature.

The search produces EVIDENCE. It does NOT produce novelty labels. Those remain custodian decisions (D1-D4).

---

## Search Protocol (Pre-Registered)

### Step 1: Query Generation (Deterministic)

For each pair, generate queries from:
- Source A title + abstract mechanism terms
- Source B title + abstract mechanism terms
- Cross-domain relationship terms

Query generation is DETERMINISTIC from the pair evidence. No LLM. No TEE. No human judgment.

**Query types per pair:**
1. **Direct combination:** "Source A mechanism" AND "Source B mechanism"
2. **Reverse combination:** "Source B mechanism" AND "Source A mechanism"
3. **Domain bridge:** "Source A domain" AND "Source B domain" AND "mechanism"
4. **Mechanism transfer:** "transfer" OR "apply" OR "adapt" + Source A mechanism + Source B domain

### Step 2: Query Freezing

All queries are generated BEFORE any search execution. Queries are hashed and frozen. No post-hoc query modification.

### Step 3: Search Execution

Search databases (in order):
1. OpenAlex (broad scholarly)
2. Semantic Scholar (independent scholarly graph)
3. Crossref (DOI/metadata corroboration)

Each search records:
- search_id, pair_id, database, query, timestamp, result_count, result_ids, query_hash, result_manifest_hash

### Step 4: Result Freezing

Search results are hashed immediately after retrieval. No post-hoc result modification.

### Step 5: D1-D4 Evidence Package

For each pair, produce:
- D1: Retrieved literature (PENDING_CUSTODIAN — custodian reviews)
- D2: Search adequacy record (databases, queries, timestamps, result counts)
- D3: PENDING_CUSTODIAN (custodian decides: ESTABLISHED/NOT_ESTABLISHED/INDETERMINATE)
- D4: Search universe description (machine-readable)

### Step 6: Custodian Packet

Produce a custodian packet with all evidence. No automated NOVEL label.

---

## Anti-Cheating Controls

1. TEE cannot influence queries (no TEE input to query generation)
2. TEE cannot influence inclusion/exclusion (no TEE in search pipeline)
3. TEE cannot see search results before Gate A
4. Benchmark construction cannot modify queries
5. Query generation is deterministic from pair evidence
6. Search timestamps are real UTC
7. Result manifests are hashed
8. Post-search mutation is detectable
9. Search universe cannot silently expand after seeing results
10. Failed APIs are recorded as UNAVAILABLE, never treated as zero results
11. Search failures cannot be interpreted as novelty

---

## Hard Rules

- Do NOT optimize the search to find novelty
- Do NOT keep searching until a pair looks novel
- Do NOT use an LLM to decide novelty
- Do NOT use TEE-generated hypotheses in queries
- Do NOT declare anything NOVEL
- Do NOT construct benchmark questions
- Do NOT alter the 182 pairs
- Do NOT alter the taxonomy
- Do NOT run TEE
