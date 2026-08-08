# Protocol Freeze Record

## Protocol
Scientific Gate 2 Protocol v1.2

## SHA
32691a78dc3bc963937fb21380c9df9c4f1f6c33

## Baseline tag
stage-1-measurement-integrity-baseline → 777cb6d

## Status
APPROVED FOR EXECUTION

## Independent reviewer status
Protocol v1.2 independently reviewed and approved.
Two final corrections applied (LLM wording, CI method).
All components approved.

## What is now immutable
- Protocol v1.2
- Evaluation criteria
- Primary hypothesis (engine yield > generic-LLM yield, α=0.05, one-sided)
- Primary comparator (generic-LLM baseline)
- Gate A A0–A4 rubric (only A4 passes)
- Gate B novelty procedure (NOVEL_AS_OF_CUTOFF)
- Gate C expert procedure (minimum 2 experts, disagreement handling)
- Control definitions (retrieval, LLM, human, matched null)
- Statistical methodology (Fisher's exact, Clopper-Pearson, Newcombe Wilson)
- Failure conditions (4 pre-registered)
- N=20 pilot interpretation
- Stage 2B expansion criterion

## Execution rules
1. Prospective cases must be independently selected and frozen before engine sees them
2. Case selection must document HOW cases were sampled, not merely provide examples
3. Artifacts must be separated: GATE2_CASES/ → GATE2_OUTPUTS/ → GATE2_EVALUATION/
4. Do not let the same artifact define cases, generate answers, and judge answers
5. If engine produces weak proposals: do not help it (no prompt changes, reruns, case selection, temperature adjustment, retrieval addition, architecture modification)
6. A weak result is a result
7. A failed Gate 2 is more valuable than an optimized benchmark
8. Do not celebrate proposals before Gate B and Gate C
9. Only complete A+B+C chain earns discovery designation

## Scientific state
```
Stage −1: Measurement integrity FAILED / NOT TRUSTWORTHY
    ↓
External review: Construct validity PREMATURE
    ↓
Gate 2 protocol: Independently reviewed
    ↓
v1.2 (32691a7): FROZEN
    ↓
EXECUTION
    ↓
A: Novel proposal?
    ↓
B: Novel knowledge?
    ↓
C: Valid knowledge?
    ↓
Scientific conclusion
```

No conclusion about whether TEE is an AI discovery engine should be made before the final node.
