# HYBRID LLM INSTRUMENT — B-2 GLiREL Hybrid Experiment

**Frozen at:** 2026-08-10
**Status:** EXPERIMENTAL ONLY — NOT the frozen B-2 instrument

## Model Selection

| Dimension | Value |
|-----------|-------|
| Requested model | GLM-5.2 |
| Actual model | glm-4-plus |
| Provider | Zhipu AI (via z-ai-web-dev-sdk) |
| GLM-5.2 available | NO |
| Fallback used | YES |
| Fallback reason | API accepts any model name without validation; response model field always returns glm-4-plus; cannot confirm GLM-5.2 is actually available |

## Instrument Dimensions

| Dimension | Value |
|-----------|-------|
| Model provider | Zhipu AI (via z-ai-web-dev-sdk) |
| Model identifier | glm-4-plus |
| SDK version | z-ai-web-dev-sdk@0.0.18 |
| System prompt | HYBRID_PROMPT (embedded in run_hybrid_phase2.mjs) |
| Temperature | not exposed by SDK |
| Top-p | not exposed by SDK |
| Tools | none |
| Retrieval | none |
| Context construction | Candidate + sources + GLiREL structured evidence (top 10 relations per source) |
| Retry policy | none (single attempt per case) |
| Output schema | b2-trace-v3 + evidence_assessment extension |
| Seed | not supported by SDK |
| Timestamp | 2026-08-10T01:40:00Z |
| Fallback behavior | glm-4-plus (same as frozen B-2 detector) |

## Difference from Frozen B-2 Instrument

The hybrid uses a SEPARATE system prompt (HYBRID_PROMPT) that:
1. Instructs the LLM to treat GLiREL evidence as extraction, NOT truth
2. Includes GLiREL's structured relations in the user prompt
3. Adds an `evidence_assessment` field to the output schema
4. Preserves the same four-state ontology (ISS_one/ISS_both/REDUNDANT_SUPPORT/UNSUPPORTED)
5. Preserves the same counterfactual semantics

The frozen B-2 detector (commit f905b68) is NOT modified. It is called as-is for baseline comparison.
