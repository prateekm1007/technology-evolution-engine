# Shuffled-Gold FP Floor Experiment

## Method
- N trials: 1000
- Seed: 270
- For each trial: permute gold bridge assignments across cases, score with current matcher

## Results
- Current observed hits: 8
- Mean shuffled hits: 2.75
- Median shuffled hits: 3
- P05: 1
- P95: 5
- Min: 0
- Max: 9
- Mean hit rate: 0.1374
- P(shuffled >= current): 0.0020

## Interpretation
The shuffled-gold mean hit rate (0.1374) is the empirical FP floor.
This is the rate at which random bridge assignments produce matches.
Current hit rate: 0.4000
The gap between current and shuffled is the signal above noise.

Note: This is NOT the old 0.9189 value. That was a circular-synonym F1.
This is an actual empirical null experiment with N=1000 permutations.
