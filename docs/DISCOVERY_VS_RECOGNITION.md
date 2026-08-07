# Discovery vs Recognition

## Status: DEFINITIVE SEPARATION — never combine again

## Definitions

**Recognition**: An entity (noun) appears in the extracted entity pool.
- Measures: can the system FIND a concept in text?
- Object: Entity (noun phrase)
- FP floor: 1.0 (any noun matches something with 143 entities)

**Discovery**: The system PROPOSES a cross-domain bridge with a mechanism, prediction, and falsifier.
- Measures: can the system GENERATE a scientific hypothesis?
- Object: BridgeProposal (mechanism + shared_variables + prediction + falsification)
- FP floor: 0.45 (still too high, but better than entity)

## Why They Were Confused

The original benchmark (cycle 196-197) scored entity recognition as if it were discovery. The pipeline extracted entities (nouns), and the benchmark checked if the gold bridge noun appeared in the extracted entities. This measured RECOGNITION, not DISCOVERY.

## The Correction (DR-91 Phase V)

Recognition F1 and Discovery F1 are now **permanently separated**:
- Recognition F1 = 1.0000 (all entities + synonyms)
- Discovery F1 = 0.8571 (shared entities + synonyms)
- Inflation = +0.1429

## Rule

**Never combine Recognition and Discovery into one score.** They measure different capabilities. Recognition is necessary but not sufficient for Discovery.
