# Phase II — Dimensional Reasoning Design Document

**Date:** 2026-08-05
**Status:** DESIGN (per Auditor cycle 69: "Do NOT start Phase II. Scope it, implement in cycle 71+.")
**Target:** "Impossible laws disappear automatically."

---

## The Problem

The system currently treats all numbers as dimensionless. Stefan-Boltzmann's T⁴ (K⁴) and PCM's linear (kg/W) are fit identically. BACON cannot prune impossible laws like P = T + m (adding temperature to mass is dimensionally wrong). The system reasons about words, not dimensions.

---

## The Solution

### 1. Dimension Dataclass

```python
class Dimension:
    mass: int           # kg exponent (e.g., 1 for kg, 0 for dimensionless)
    length: int         # m exponent
    time: int           # s exponent
    current: int        # A exponent
    temperature: int    # K exponent
    amount: int         # mol exponent
```

Examples:
- Force (N) = kg·m·s⁻² → Dimension(1, 1, -2, 0, 0, 0)
- Power (W) = kg·m²·s⁻³ → Dimension(1, 2, -3, 0, 0, 0)
- Temperature (K) = Dimension(0, 0, 0, 0, 1, 0)

### 2. Unit Registry

A mapping from unit strings to Dimension objects:

```python
UNIT_DIMENSIONS = {
    "K": Dimension(0, 0, 0, 0, 1, 0),      # temperature
    "W": Dimension(1, 2, -3, 0, 0, 0),     # power
    "W/m2": Dimension(0, 0, -3, 0, 0, 0),   # power density
    "J": Dimension(1, 2, -2, 0, 0, 0),      # energy
    "kg": Dimension(1, 0, 0, 0, 0, 0),      # mass
    "m": Dimension(0, 1, 0, 0, 0, 0),       # length
    "s": Dimension(0, 0, 1, 0, 0, 0),       # time
    "V/K": Dimension(1, 2, -3, -1, -1, 0),  # Seebeck (V/K)
    "%": Dimension(0, 0, 0, 0, 0, 0),       # dimensionless
    "dimensionless": Dimension(0, 0, 0, 0, 0, 0),
}
```

### 3. Dimensional Consistency Check

```python
def check_dimensional_consistency(formula: str, input_dims: Dict[str, Dimension], output_dim: Dimension) -> bool:
    """Check if a candidate law is dimensionally consistent.

    For y = a*x + b: x and y must have the same dimension.
    For y = a*x^b: output_dim = input_dim^b.
    For y = a*x1*x2: output_dim = input_dim1 * input_dim2.
    For y = a*exp(b*x): x must be dimensionless (b has 1/x dimension).
    """
```

### 4. Buckingham π Theorem

Given n variables with k independent dimensions, there are n-k dimensionless groups. The system should:
1. Compute the dimensionless groups for each dataset
2. Search for laws in dimensionless space (fewer variables → simpler laws)
3. Convert dimensionless laws back to dimensional form

### 5. Integration with BACON

BACON's candidate law forms should be filtered by dimensional consistency:
- `y = a*x + b` → x and y must have same dimension
- `y = a*x^b` → output_dim = input_dim^b (b must be integer for simple cases)
- `y = a*exp(b*x)` → x must be dimensionless
- `y = a*log(x)` → x must be dimensionless
- `y = a*sin(b*x)` → b*x must be dimensionless

Impossible laws are pruned BEFORE fitting, reducing the search space.

---

## Implementation Plan (cycle 71+)

1. Add Dimension dataclass to `invention_compiler/dimensional_reasoning.py` (new file)
2. Add UNIT_DIMENSIONS registry
3. Add `check_dimensional_consistency()` function
4. Add `buckingham_pi()` function
5. Integrate with BACON: filter candidate forms by dimensional consistency
6. Tests: verify that P = T + m is rejected, P = a*T⁴ is accepted
7. Tests: verify that Buckingham π reduces variables correctly

---

## Success Criterion

"Impossible laws disappear automatically."

When BACON tries to fit P = T + m (adding temperature to mass), the dimensional consistency check rejects it BEFORE fitting. When BACON tries P = εσT⁴, the check passes. The search space is reduced by ~50% (removing all dimensionally impossible forms).
