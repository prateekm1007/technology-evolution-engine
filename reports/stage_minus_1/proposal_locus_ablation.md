# Proposal-Locus Ablation

## Current scorer (with fallback)
- TP=8, FP=0, FN=12, Precision=1.0000, Recall=0.4000, F1=0.5714

## Proposal-locus only (no fallback)
- TP=6, FP=0, FN=14, Precision=1.0000, Recall=0.3000, F1=0.4615

## Lost hits (disappear under proposal-locus-only)
DISC-GOLD-004, DISC-GOLD-005

## F1 inflation from fallback: +0.1099
