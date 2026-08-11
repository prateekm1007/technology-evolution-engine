# BACON on Real Data — Cycle 73 Results

**Date:** 2026-08-05
**Status:** Phase III progress (30% → 35%)

---

## Results

### 1. Stefan-Boltzmann (T → Q, 15 points, T_sky=0K)

**DISCOVERED: power law, a=5.39e-8, b=4.0000, R²=1.0000**

- Expected: a = εσA = 5.39e-8, b = 4.0
- Match: 0% error on both parameters
- The system discovered Stefan-Boltzmann from data without being told the formula
- Dimensional pruning reduced search space: only power form survived (5 of 6 pruned)

### 2. Stull wet-bulb (RH → T_wb at T=25°C, 25 points)

**DISCOVERED: power law, R²=0.9872** — but this is an approximation, not the true law.

- The true Stull formula involves atan and sqrt — functions NOT in BACON's candidate set
- The power form fits well (R²=0.99) but is NOT the true law
- **Boundary stated:** the true law is not in the candidate set. Per Constitution Rule 5.

### 3. PCM latent heat (Q → m, 10 points)

**DISCOVERED: power law, a=0.144, b=1.0, R²=1.0000**

- Expected: a = t*3600/L = 0.144, b = 1.0 (linear)
- Match: 0% error. The system correctly identified the linear law via the power form (b=1).

### 4. Real corpus data (CP → ΔT, 3 points)

**DISCOVERED: power law, R²=1.0** — but trivially fit (3 points, 2 parameters)

- The real corpus has too few measured values for meaningful law discovery
- The extractor captures values but assigns the same value to multiple materials (F-062)
- More extracted measurements needed

---

## Honest Assessment (Constitution Rule 5)

**What BACON CAN do:**
- Discover known laws from formula-generated data (Stefan-Boltzmann, PCM)
- Correctly identify the power exponent (b=4 for T⁴, b=1 for linear)
- Report 0% parameter error when the true form is in the candidate set
- State the boundary when the true form is not in the candidate set (Stull)

**What BACON CANNOT do:**
- Discover laws involving atan, sqrt, sin, cos (not in candidate set)
- Discover laws from real corpus data (too few data points — 3 per property)
- Distinguish between a good approximation (R²=0.99 power for Stull) and the true law (atan/sqrt)

**The boundary:** BACON's candidate set has 6 forms (linear, inverse, log, power, exponential, quadratic). The true Stull formula uses atan and sqrt. Adding these is Phase III work. The dimensional pruning correctly identifies which forms are physically possible; the remaining limitation is the candidate set's coverage.

---

## Phase III Status: 30% → 35%

- BACON discovers known laws from formula data (Stefan-Boltzmann, PCM) ✓
- BACON states the boundary when the true form is not in the candidate set ✓
- Next: add atan/sqrt/sin/cos to candidate forms
- Next: extract more real measurements from corpus papers
