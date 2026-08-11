# INTERFACES

Documents the actual live behavior of the two FastAPI surfaces in this repo, as
observed by running them, not as designed. Where behavior diverges from the
code's apparent intent, that divergence is noted explicitly.

Two separate, currently-disconnected apps exist:

- `web/backend/main.py` — served at `/`, has the frontend, the verification
  contract (`stamp()`), and is the one end users will actually hit.
- `product/api/app.py` — a second FastAPI app with different routes
  (`/api/v1/business/analyze`, `/api/v1/consumer/solve`), no verification
  contract, no frontend. Not currently reachable from the UI. Kept only
  because `product/business/pipeline.py` / `product/consumer/pipeline.py`
  are exercised by it and by `tests/test_product.py`.

These should be merged into one surface; see FAILURES.md F-002.

---

## `web/backend/main.py`

### `GET /api/v1/health`
Returns `{"status":"ok","core_bound":bool,"backend_status":str,"graph_nodes":int}`.
Live-verified: `graph_nodes: 577`.

### `POST /api/v1/analyze`
Request body (`AnalyzeRequest`):
```json
{"mode": "consumer" | "business", "input_type": str, "title": str | null, "text": str | null}
```
**Field mapping caveat (load-bearing):** internally this maps `text` → both
`raw_text` and `problem_statement` before calling the pipeline, because
`TextNormalizer`/`PatentParser` read those keys, not `text`/`title`. If you
add a field to `AnalyzeRequest`, it will silently not reach the pipeline
unless you also add it to the mapping block in `analyze()`. This exact class
of bug (schema key not matching consumer key) already happened once — see
FAILURES.md F-003.

Response: whatever `ConsumerPipeline.run()` / `BusinessPipeline.run()`
returns (see their respective `product/schemas/*_output.py`), plus a
`verification` object:
```json
{"level": "integrated" | "implemented", "is_fact": bool, "note": str}
```
The `"verified"` value is reserved by Law 8 — it cannot be honestly
claimed until the ledger contains at least one successful prediction,
one failed prediction, and replayable evidence. As of the F-005
follow-up audit, those criteria are now met for the *historical*
verification cycle (`scripts/run_verification_cycle.py`) but not for
live `/api/v1/analyze` predictions, so this endpoint continues to
stamp `"integrated"`. See `evidence/reports/verification_report.json`
for the current Law 8 verdict.
Live-verified example (`mode: consumer`, `text: "reduce household water consumption"`):
`report_id`, `detected_domains: ["water"]`, non-empty `solutions`. Confirmed
two different `text` inputs produce different `report_id`/`detected_domains`.

Falls back to a hardcoded `SPECIMEN["analysis"]` stub with
`fallback_reason` set on any exception from the pipeline layer — this is
intentional graceful degradation, not a bug, but callers should check
`fallback_reason` before trusting the response.

### `POST /api/v1/simulate`
`{"constraint": str, "direction": "decrease"|"increase", "magnitude": str}` →
`DeepOracle.simulate()` output, stamped `integrated`/`implemented`.

### `GET /api/v1/graph`
Returns `{"nodes": [...], "edges": [...], "node_count": int, "edge_count": int, ...}`.
Live-verified: 577 nodes.

### `GET /api/v1/evidence`
Returns `{"ledger": [...], "malformed_lines": [...], "entry_count": int}`.
Live-verified: `predictions.jsonl` is currently corrupted (see FAILURES.md
F-005) — expect `entry_count: 0` and a large `malformed_lines` array until
that's fixed at the source.

### `GET /api/v1/benchmarks`
Returns hardcoded `SPECIMEN["benchmarks"]`, stamped `implemented`. Honestly
labeled — see `evidence/reports/benchmark_report.json`: zero real benchmark
runs exist in this repo yet.

---

## `product/api/app.py` (secondary, unwired)

### `GET /health` → `{"status":"ok","engine":"TEE","version":"0.1.0"}`

### `POST /api/v1/business/analyze`
`{"raw_text": str, "patent_id": str|null, "title": str|null}` → full business
report (adjacency map, permutation candidates, blueprints). Live-verified
working on properly claim-formatted patent text. On loosely-formatted patent
prose, `PatentParser` silently returns zero components → empty report,
`confidence: 0.0`, still `200 OK`. See FAILURES.md F-001.

### `POST /api/v1/consumer/solve`
`{"problem_statement": str, "budget_usd": float|null, "timeline_days": int|null, "skill_level": str, "domain": str|null}`
→ consumer report. Live-verified working, but scoring is a static formula
keyed only on operator type + element count — different problem statements
with similar element counts produce near-duplicate ranked results. See
FAILURES.md F-004.

### `POST /api/v1/analyze`
Generic mode-detecting entry point, delegates to `Orchestrator`.
