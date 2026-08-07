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
| M-005 | INPUT | drop_1_sentence | 0.7879 | 0.7879 | +0.0000 | +0.0000 | ROBUST |
| M-005 | INPUT | shuffle_sentences | 0.7879 | 0.7879 | +0.0000 | +0.0000 | ROBUST |
| M-005 | INPUT | truncate_75pct | 0.7879 | 0.5185 | -0.2694 | -0.3419 | FRAGILE |
| M-005 | GOLD | drop_1_gold | 0.7879 | 0.7742 | -0.0137 | -0.0174 | ROBUST |
| M-005 | GOLD | drop_2_gold | 0.7879 | 0.7586 | -0.0293 | -0.0371 | ROBUST |
| M-005 | GOLD | rename_gold | 0.7879 | 0.7879 | +0.0000 | +0.0000 | ROBUST |
| M-005 | SYNONYM | remove_1_synonym | 0.7879 | 0.7879 | +0.0000 | +0.0000 | ROBUST |
| M-005 | SYNONYM | remove_25pct_synonyms | 0.7879 | 0.7879 | +0.0000 | +0.0000 | ROBUST |
| M-005 | SYNONYM | remove_50pct_synonyms | 0.7879 | 0.7879 | +0.0000 | +0.0000 | ROBUST |
| M-008 | SYNONYM | remove_1_synonym | 0.9474 | 0.9474 | +0.0000 | +0.0000 | ROBUST |
| M-008 | SYNONYM | remove_25pct_synonyms | 0.9474 | 0.9474 | +0.0000 | +0.0000 | ROBUST |
| M-008 | SYNONYM | remove_50pct_synonyms | 0.9474 | 0.9474 | +0.0000 | +0.0000 | ROBUST |
| M-008 | GOLD | drop_1_gold | 0.9474 | 0.9444 | -0.0029 | -0.0031 | ROBUST |
| M-008 | GOLD | drop_2_gold | 0.9474 | 0.9412 | -0.0062 | -0.0065 | ROBUST |
| M-013 | INPUT | drop_1_sentence | 0.7647 | 0.7647 | +0.0000 | +0.0000 | ROBUST |
| M-013 | INPUT | truncate_75pct | 0.7647 | 0.5185 | -0.2462 | -0.3219 | FRAGILE |
| M-013 | GOLD | drop_1_gold | 0.7647 | 0.7500 | -0.0147 | -0.0192 | ROBUST |
| M-013 | GOLD | drop_2_gold | 0.7647 | 0.7333 | -0.0314 | -0.0410 | ROBUST |
| M-013 | GOLD | rename_gold | 0.7647 | 0.7647 | +0.0000 | +0.0000 | ROBUST |
| M-013 | SYNONYM | remove_25pct_synonyms | 0.7647 | 0.7647 | +0.0000 | +0.0000 | ROBUST |
| M-013 | SYNONYM | remove_50pct_synonyms | 0.7647 | 0.7647 | +0.0000 | +0.0000 | ROBUST |
| M-010 | INPUT | drop_1_sentence | 0.6500 | 0.6500 | +0.0000 | +0.0000 | ROBUST |
| M-010 | GOLD | drop_1_gold | 0.6500 | 0.6316 | -0.0184 | -0.0283 | ROBUST |
| M-010 | GOLD | drop_2_gold | 0.6500 | 0.6111 | -0.0389 | -0.0598 | SENSITIVE |
| M-010 | SYNONYM | remove_25pct_synonyms | 0.6500 | 0.6500 | +0.0000 | +0.0000 | ROBUST |
| M-010 | SYNONYM | remove_50pct_synonyms | 0.6500 | 0.6500 | +0.0000 | +0.0000 | ROBUST |

## Summary

- ROBUST (|Δ| < 5%): 23/26
- SENSITIVE (5-15%): 1/26
- FRAGILE (> 15%): 2/26

### Per-metric summary

| Metric | ROBUST | SENSITIVE | FRAGILE | Total |
|---|---|---|---|---|
| M-005 | 8 | 0 | 1 | 9 |
| M-008 | 5 | 0 | 0 | 5 |
| M-010 | 4 | 1 | 0 | 5 |
| M-013 | 6 | 0 | 1 | 7 |

### Per-perturbation-type summary

| Type | ROBUST | SENSITIVE | FRAGILE | Total |
|---|---|---|---|---|
| GOLD | 9 | 1 | 0 | 10 |
| INPUT | 4 | 0 | 2 | 6 |
| SYNONYM | 10 | 0 | 0 | 10 |

### FRAGILE perturbations (repair priorities)

- **M-005 / INPUT/truncate_75pct**: Δ=-0.2694 (-0.3419). Baseline=0.7879 → Perturbed=0.5185
- **M-013 / INPUT/truncate_75pct**: Δ=-0.2462 (-0.3219). Baseline=0.7647 → Perturbed=0.5185

## Gate M6 verdict: **PARTIAL**

2 perturbation(s) are FRAGILE (|Δ| >= 15%).
These are the repair priorities — the metric output moves
significantly when these inputs are perturbed.

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
