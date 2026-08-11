# Proposal Population

## A. Ambient entity exposure
- Total entities A: 79
- Total entities B: 77
- Unique entities A: 77
- Unique entities B: 76
- Total ambient candidates: 156
- Gold-matching ambient candidates: 14

## B. Shared discovery proposals
- Total proposals: 22
- Unique proposals: 21
- Correct proposals (match their gold bridge): 6
- Incorrect proposals (don't match their gold bridge): 16

## C. Strict proposal precision
- TP (correct proposals): 6
- FP (incorrect proposals): 16
- Precision: 0.2727
- Recall: 0.3000
- F1: 0.2857

Note: FP here = proposals that don't match their case's gold bridge.
This is proposal-level FP, NOT ambient-entity-level FP.
An extracted entity that was never proposed as a bridge is NOT counted as FP here.
