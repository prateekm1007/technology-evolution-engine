# BACON Scoping Document

## What BACON Is

BACON (Langley, Simon, Bradshaw, Zytkow 1987) is a system that rediscovers
scientific laws from raw data. It rediscovered:
- Kepler's third law (T² ∝ R³) from planetary motion data
- Boyle's law (PV = constant) from gas pressure-volume data
- Ohm's law (V = IR) from electrical measurements

## What BACON Does

1. Takes raw measurement data (pairs of variables)
2. Searches over functional forms (linear, power, logarithmic)
3. Checks if a form fits the data within tolerance
4. If found, declares a law
5. Uses prior laws as constraints on new searches

## What Our System Needs

### Data Requirements
- Pairs of measured variables (e.g., temperature vs Seebeck coefficient)
- Multiple data points per pair (≥5 for statistical significance)
- Units and uncertainty bands

### Algorithm Requirements
- Functional form search: linear, power, logarithmic, exponential, polynomial
- Units consistency checking (Law 2: arithmetic closure)
- Prior law application (use known laws to constrain search)
- Tolerance-based acceptance (not exact match)

### Integration Points
- Input: measurement data from ExperimentGraph (Layer 5)
- Output: Law objects in the object-centric model (DR-21)
- Connection: derived laws can promote CausalEdge from ASSERTED to DERIVED

### Why This Is Phase III

BACON requires:
1. A corpus of measurement data (not just text descriptions)
2. A functional form search engine (not just pattern matching)
3. Units-aware arithmetic (not just float comparison)
4. Prior law integration (not just standalone derivation)

The current system has none of these. The formula verifier
(scripts/verify_formulas.py) executes KNOWN laws against stated inputs
but does not DERIVE new laws from data. Building BACON is a Phase III
(18-30 month) capability per the Discovery Roadmap.

### What Can Be Done In Cycle 44

- Scope the data requirements (what measurements are needed)
- Specify the functional form search space
- Design the Law → CausalEdge promotion path
- Do NOT implement the derivation engine itself
