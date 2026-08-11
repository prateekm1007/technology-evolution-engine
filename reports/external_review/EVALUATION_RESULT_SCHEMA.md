# Evaluation Result Schema

Every external evaluator should report results in the following format for each test case:

```yaml
case_id: DISC-GOLD-XXX
input_domains:
  - "domain A description"
  - "domain B description"
input_sources:
  - "source A snippet or reference"
  - "source B snippet or reference"
engine_proposal: "the bridge concept the engine proposed"
proposal_timestamp: "ISO 8601"
known_prior_art:
  - "citation or URL of prior publication"
  - "or 'none found'"
novelty_status: NOVEL | PREVIOUSLY_KNOWN | PARTIAL_PRECEDENT | AMBIGUOUS | UNSUPPORTED
mechanistic_plausibility: PLAUSIBLE | PARTIAL | UNSUPPORTED | NOT_ASSESSED
independent_expert_assessment:
  expert_id: "anonymized"
  non_obvious: YES | NO | UNCLEAR
  scientifically_meaningful: YES | NO | UNCLEAR
  already_known: YES | NO | UNCLEAR
  mechanism_makes_sense: YES | NO | UNCLEAR
recognition_leakage: YES | NO
  # YES = bridge concept is explicitly present in input text
terminology_leakage: YES | NO
  # YES = match depends on token overlap, not semantic understanding
benchmark_leakage: YES | NO
  # YES = gold answer appears to have influenced the system
human_baseline:
  human_found_same_connection: YES | NO
  human_found_additional: "list"
  human_found_contradictory: "list"
final_classification: NOVEL | PREVIOUSLY_KNOWN | PARTIAL_PRECEDENT | AMBIGUOUS | UNSUPPORTED
evidence:
  - "evidence item 1"
  - "evidence item 2"
```

## Permitted final classifications

```
NOVEL — not previously published, non-obvious, supported by mechanism
PREVIOUSLY_KNOWN — published before benchmark construction
PARTIAL_PRECEDENT — related but not identical to existing work
AMBIGUOUS — unclear whether novel or known
UNSUPPORTED — no evidence for the claimed relationship
```

## Aggregate report

After evaluating all cases, the evaluator should produce:

```yaml
total_cases: N
classification_counts:
  NOVEL: X
  PREVIOUSLY_KNOWN: Y
  PARTIAL_PRECEDENT: Z
  AMBIGUOUS: W
  UNSUPPORTED: V
recognition_leakage_count: A
terminology_leakage_count: B
ambient_fallback_count: C
expert_agreement_rate: D
human_baseline_overlap: E
```
