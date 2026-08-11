# Measurement History

## Status: APPEND-ONLY (Law 7)

## Discovery F1 Timeline

| Cycle | Reported F1 | Object | Verdict | Notes |
|-------|------------|--------|---------|-------|
| 196 | 0.3333 | Entity (5-gold) | INVALID | Small gold set |
| 197 | 1.0000 | Entity (20-gold, synonyms) | INVALID | Synonym map inflated score |
| 201 | 0.9189 | Entity (20-gold, non-circular) | INVALID | F-099 fixed circularity but matching still loose |
| 242 | 1.0000 | Entity (all + synonyms, independent) | INVALID | FP floor = 1.0 |
| 242 | 0.8571 | Entity (shared + synonyms, proposal-only) | INVALID | Still entity-based |
| 245 | 0.0000 | Exact match (all) | N/A | Exact extraction never matches gold |
| 245 | 0.1000 | BridgeProposal (Gen0) | EXPLORATORY | Only 6/20 gold produce proposals |

## Key Measurement Events

| Cycle | Event | Impact |
|-------|-------|--------|
| 197 | DR-51: synonym map added | +0.68 F1 (inflated) |
| 201 | F-099: circular gold killed | F1 1.0→0.92 (honest) |
| 242 | DR-91: independent audit | FP=1.0 discovered, verdict NOT TRUSTWORTHY |
| 243 | DR-91 Phase VI: component attribution | FP=1.0 regardless of component |
| 245 | DR-91 Phase VI.5: discovery object audit | Entity≠Proposal identified |
| 247 | DR-92: Proposal Composer built | 6 proposals, recall=0.10 |
| 248 | DR-93: internal evaluation | 6/6 "valid" (self-grading) |
| 249 | DR-93.5: independent LLM | 0/6 accepted, 4/6 rejected |
| 250 | DR-94: calibration study | bias=+2.50, 100% overestimate |
| 251 | DR-95: multi-evaluator | judges disagree 83%, ECE=0.433 |
| 252 | DR-96: evaluation science | Goodhart vulnerability, adversarial judge=33% |

## Recalibration Status

**NOT YET DONE.** Historical recalibration (Phase IX) requires:
1. Trustworthy benchmark object (not yet established)
2. Bootstrap CIs on all scores
3. Independent verification
4. Delta documentation for every cycle

No historical score has been recomputed. All prior F1 values remain as originally reported but are marked INVALID.
