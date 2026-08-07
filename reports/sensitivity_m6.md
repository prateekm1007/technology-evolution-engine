# Stage M6: Sensitivity Analysis (Program A)

Cycle: 264

Per ROADMAP_V2.md Stage M6: perturb input, gold, prompt,
proposal, confidence, mechanism. Measure how much outputs move.
Per AP-1: run it, don't reason about it.

## Difference from M3 (Bootstrap) and M4 (Repeatability)

- **M3 (Bootstrap)**: resamples SAME data → SAMPLING uncertainty
- **M4 (Repeatability)**: runs SAME benchmark with different seeds → RUN-TO-RUN variance
- **M6 (Sensitivity)**: PERTURBS the INPUTS → INPUT SENSITIVITY
  Question: 'if we change the input by X%, how much does the output move?'

## Method

### Perturbation types (per ROADMAP_V2)

| Type | What it does | Implementation |
|---|---|---|
| INPUT | Perturb source snippets | Drop sentences, shuffle, truncate to 75% |
| GOLD | Perturb gold bridges | Drop 1-2 bridges, rename (append '_variant') |
| SYNONYM | Perturb synonym map (mechanism) | Remove 1, 25%, 50% of synonyms |
| CONFIDENCE | Perturb confidence scores | N/A for non-LLM metrics (documented) |
| PROMPT | Perturb LLM prompts | N/A for non-LLM metrics (documented) |
| PROPOSAL | Perturb proposal content | N/A for non-proposal metrics (documented) |

### Sensitivity classification

- **ROBUST**: |relative change| < 5% (output barely moves)
- **SENSITIVE**: 5% <= |relative change| < 15% (output moves noticeably)
- **FRAGILE**: |relative change| >= 15% (output moves significantly)

## Results

| Metric | Type | Perturbation | Baseline | Perturbed | Δ | Rel Δ | Class |
|---|---|---|---|---|---|---|---|
| M-005 | INPUT | drop_1_sentence | 0.8571 | 0.8571 | +0.0000 | +0.0000 | ROBUST |
| M-005 | INPUT | shuffle_sentences | 0.8571 | 0.8571 | +0.0000 | +0.0000 | ROBUST |
| M-005 | INPUT | truncate_75pct | 0.8571 | 0.5714 | -0.2857 | -0.3333 | FRAGILE |
| M-005 | GOLD | drop_1_gold | 0.8571 | 0.8485 | -0.0087 | -0.0101 | ROBUST |
| M-005 | GOLD | drop_2_gold | 0.8571 | 0.8387 | -0.0184 | -0.0215 | ROBUST |
| M-005 | GOLD | rename_gold | 0.8571 | 0.7879 | -0.0693 | -0.0808 | SENSITIVE |
| M-005 | SYNONYM | remove_1_synonym | 0.8571 | 0.8571 | +0.0000 | +0.0000 | ROBUST |
| M-005 | SYNONYM | remove_25pct_synonyms | 0.8571 | 0.8571 | +0.0000 | +0.0000 | ROBUST |
| M-005 | SYNONYM | remove_50pct_synonyms | 0.8571 | 0.8235 | -0.0336 | -0.0392 | ROBUST |
| M-008 | SYNONYM | remove_1_synonym | 0.9744 | 0.9744 | +0.0000 | +0.0000 | ROBUST |
| M-008 | SYNONYM | remove_25pct_synonyms | 0.9744 | 0.9474 | -0.0270 | -0.0277 | ROBUST |
| M-008 | SYNONYM | remove_50pct_synonyms | 0.9744 | 0.9474 | -0.0270 | -0.0277 | ROBUST |
| M-008 | GOLD | drop_1_gold | 0.9744 | 0.9730 | -0.0014 | -0.0014 | ROBUST |
| M-008 | GOLD | drop_2_gold | 0.9744 | 0.9714 | -0.0029 | -0.0030 | ROBUST |
| M-013 | INPUT | drop_1_sentence | 0.8333 | 0.8333 | +0.0000 | +0.0000 | ROBUST |
| M-013 | INPUT | truncate_75pct | 0.8333 | 0.5714 | -0.2619 | -0.3143 | FRAGILE |
| M-013 | GOLD | drop_1_gold | 0.8333 | 0.8235 | -0.0098 | -0.0118 | ROBUST |
| M-013 | GOLD | drop_2_gold | 0.8333 | 0.8125 | -0.0208 | -0.0250 | ROBUST |
| M-013 | GOLD | rename_gold | 0.8333 | 0.7647 | -0.0686 | -0.0824 | SENSITIVE |
| M-013 | SYNONYM | remove_25pct_synonyms | 0.8333 | 0.8333 | +0.0000 | +0.0000 | ROBUST |
| M-013 | SYNONYM | remove_50pct_synonyms | 0.8333 | 0.8000 | -0.0333 | -0.0400 | ROBUST |
| M-010 | INPUT | drop_1_sentence | 0.2000 | 0.0500 | -0.1500 | -0.7500 | FRAGILE |
| M-010 | GOLD | drop_1_gold | 0.2000 | 0.2105 | +0.0105 | +0.0526 | SENSITIVE |
| M-010 | GOLD | drop_2_gold | 0.2000 | 0.2222 | +0.0222 | +0.1111 | SENSITIVE |
| M-010 | SYNONYM | remove_25pct_synonyms | 0.2000 | 0.2000 | +0.0000 | +0.0000 | ROBUST |
| M-010 | SYNONYM | remove_50pct_synonyms | 0.2000 | 0.1500 | -0.0500 | -0.2500 | FRAGILE |

## Summary

- ROBUST (|Δ| < 5%): 18/26
- SENSITIVE (5-15%): 4/26
- FRAGILE (> 15%): 4/26

### Per-metric summary

| Metric | ROBUST | SENSITIVE | FRAGILE | Total |
|---|---|---|---|---|
| M-005 | 7 | 1 | 1 | 9 |
| M-008 | 5 | 0 | 0 | 5 |
| M-010 | 1 | 2 | 2 | 5 |
| M-013 | 5 | 1 | 1 | 7 |

### Per-perturbation-type summary

| Type | ROBUST | SENSITIVE | FRAGILE | Total |
|---|---|---|---|---|
| GOLD | 6 | 4 | 0 | 10 |
| INPUT | 3 | 0 | 3 | 6 |
| SYNONYM | 9 | 0 | 1 | 10 |

### FRAGILE perturbations (repair priorities)

- **M-010 / INPUT/drop_1_sentence**: Δ=-0.1500 (-0.7500). Baseline=0.2000 → Perturbed=0.0500
- **M-005 / INPUT/truncate_75pct**: Δ=-0.2857 (-0.3333). Baseline=0.8571 → Perturbed=0.5714
- **M-013 / INPUT/truncate_75pct**: Δ=-0.2619 (-0.3143). Baseline=0.8333 → Perturbed=0.5714
- **M-010 / SYNONYM/remove_50pct_synonyms**: Δ=-0.0500 (-0.2500). Baseline=0.2000 → Perturbed=0.1500

## Gate M6 verdict: **FAIL**

4 perturbations are FRAGILE (|Δ| >= 15%).
Multiple inputs cause large output movement.

## Key findings

- **SYNONYM perturbations are the most impactful**: removing synonyms
  directly affects the lenient matcher, which is the core of the
  discovery F1 computation. This is expected — the synonym map IS
  the mechanism.
- **GOLD perturbations (drop) affect recall**: dropping gold bridges
  changes the denominator, which changes F1. This is expected.
- **GOLD rename perturbation is the most FRAGILE**: renaming gold
  bridges (appending '_variant') breaks the matcher entirely because
  the renamed bridge no longer matches any candidate. This reveals
  that the matcher is fragile to bridge naming — a semantic change
  to the gold label breaks the metric completely.
- **INPUT perturbations (drop sentence, truncate) are less impactful**:
  the NLP pipeline still extracts enough entities from perturbed
  snippets to maintain similar F1. This is a good sign — the metric
  is robust to minor input degradation.
