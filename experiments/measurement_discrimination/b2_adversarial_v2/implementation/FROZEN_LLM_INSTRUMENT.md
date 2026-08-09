# FROZEN LLM INSTRUMENT — B-2 Detector

**Frozen at:** 2026-08-10
**Per:** REPAIR_SPEC.md §5.7 (commit `1c9d869`, accepted round-80)
**Schema version:** `b2-trace-v3`
**Inference-rule taxonomy:** `inference-rules-v1`

## Frozen dimensions (per §5.7 table)

| Dimension | Value |
|-----------|-------|
| Model provider | Zhipu AI (via `z-ai-web-dev-sdk`) |
| Model identifier | `glm-4-plus` |
| System / developer prompt | `b2-system-prompt-v1` — full text at `SYSTEM_PROMPT.md` |
| User prompt template | See `b2_detector.mjs` `buildUserPrompt()` — exact text with placeholders `{id}`, `{candidate}`, `{source_a}`, `{source_b}` |
| Temperature | Not exposed by SDK; majority vote N≥5 used per §5.7 requirement 4 |
| Tool availability | `none` |
| Retrieval corpus | `none` (no web search, no external KB) |
| Context construction | Candidate + sources formatted with labeled delimiters (`CANDIDATE:`, `SOURCE A:`, `SOURCE B:`); system prompt passed as `assistant` role message; user prompt passed as `user` role message |
| Output schema | `b2-trace-v3` JSON (exact schema at REPAIR_SPEC.md §3.7.1) |
| Retry policy | 3 retries on JSON parse failure; exponential backoff (1s, 2s, 3s); fall back to `UNSUPPORTED` trace if all retries fail |
| Deterministic seed | Not supported by SDK |
| Runtime / dependency versions | Node.js ≥ 20; `z-ai-web-dev-sdk@0.0.18` (installed at `/home/z/.bun/install/global/node_modules/z-ai-web-dev-sdk`) |
| N for majority vote | 5 (per §5.7 requirement 4; ties counted as failures) |

## System prompt version

The system prompt is frozen at `b2-system-prompt-v1` and stored verbatim in `SYSTEM_PROMPT.md`. The detector loads it at runtime by stripping the markdown header and passing the prompt body as the `assistant` role message.

The system prompt encodes:
- The four-state ontology (`ISS_one` / `ISS_both` / `REDUNDANT_SUPPORT` / `UNSUPPORTED`)
- The two support types (`SOURCE_LOCAL` / `JOINT_CROSS_SOURCE`)
- The frozen inference-rule taxonomy (`inference-rules-v1`: 8 rules + `OTHER`)
- The counterfactual test and support-entry survival matrix
- The `b2-trace-v3` output schema
- The critical rules (span verbatim, consistency, honesty)
- The principle that classification ≠ validity (§2.6.9)

## Determinism and reproducibility

The Zhipu AI SDK (`z-ai-web-dev-sdk@0.0.18`) does not expose `temperature` or `seed` parameters. Per §5.7 requirement 4, the detector runs N=5 times per case and uses majority vote for the canonical label. Ties (two labels with equal counts) are reported as ambiguous and counted as failures for qualification purposes.

The label distribution across the N runs is reported in the output for each case, so the auditor can assess stability.

## Drift monitoring (per §8.6)

If the provider updates `glm-4-plus` (weight changes, safety filter changes, deprecation), the held-out results may become invalid. The auditor must:

1. Re-run the held-out set against the drifted instrument.
2. Compare per-category pass rates to the original frozen-run pass rates.
3. If any category's pass rate drops by more than 1 case, the instrument is materially changed and downstream results are invalidated.

The model identifier is recorded in every trace's `_model` metadata (if available from the API response) to detect silent provider-side changes.

## What this instrument does NOT do

- Does NOT access external knowledge bases or web search.
- Does NOT use tools or function calling.
- Does NOT cache or store intermediate results beyond the trace JSON.
- Does NOT modify the production substrate (`_check_leakage` at commit `20ac268` remains frozen).
- Does NOT access held-out material during development (only the public 13-case calibration set was used).

## Files

- `SYSTEM_PROMPT.md` — frozen system prompt (`b2-system-prompt-v1`)
- `b2_detector.mjs` — detector implementation
- `b2_trace_validator.mjs` — schema validator
- `run_public_set.mjs` — public 13-case calibration harness
- `run_heldout_set.mjs` — held-out set evaluation harness (accepts path; blind to content during development)
- `FROZEN_LLM_INSTRUMENT.md` — this file
