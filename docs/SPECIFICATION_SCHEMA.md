# SPECIFICATION_SCHEMA.md

## Specification Schema (Stage I)

A **Specification** is the machine-checkable input to the invention
pipeline. It is produced by `scripts/specification.py::SpecificationEngine`
from a natural-language objective, and consumed by Stage II
(`scripts/artifact_generator.py`) to drive candidate generation.

### Specification

```python
@dataclass
class Specification:
    objective: str                    # the goal, e.g. "improve thermoelectric efficiency of bismuth telluride"
    domain: str                       # one of: thermoelectric, photovoltaic, supercapacitor, battery, thermal, unknown
    hard_constraints: List[Dict]      # must-satisfy constraints
    soft_constraints: List[Dict]      # should-satisfy constraints
    acceptance_criteria: List[Dict]   # pass/fail tests
    capability_targets: List[str]     # required capabilities (e.g. "generates_voltage")
    target_material: Optional[str]    # base material, e.g. "bismuth_telluride"
```

### Hard Constraint

A hard constraint is a numeric inequality the candidate MUST satisfy.
A candidate that violates any hard constraint is rejected at the
scoring stage.

```python
{
    "name": "temperature_range",       # canonical name
    "operator": ">=" | "<=" | "==" | ">" | "<",
    "value": 300,                      # numeric threshold
    "units": "K",                      # SI units
    "description": "Must operate at or above room temperature"
}
```

### Soft Constraint

A soft constraint is an objective to minimize or maximize. Soft
constraints do not gate acceptance but affect ranking.

```python
{
    "name": "weight",
    "operator": "minimize" | "maximize",
    "value": None,                     # may be None for direction-only
    "units": "kg",
    "description": "Minimize weight"
}
```

### Acceptance Criterion

An acceptance criterion is the binary pass/fail test the candidate's
predicted (or measured) properties must pass. Acceptance is required
for a candidate to be promoted from "generated" to "validated".

```python
{
    "metric": "ZT",                    # must match a key in predicted_properties
    "operator": ">" | ">=" | "<" | "<=" | "==",
    "threshold": 1.0,
    "units": "dimensionless",          # optional
    "description": "Figure of merit ZT > 1.0"
}
```

### Capability Targets

Capability targets are the names from `docs/CAPABILITY_SCHEMA.md` that
the candidate must exhibit. The artifact generator selects materials
from the capability graph that possess these capabilities.

Common capability names:

| Domain | Capability targets |
|---|---|
| thermoelectric | generates_voltage, conducts_electricity, transfers_heat |
| photovoltaic | absorbs_light, generates_voltage |
| supercapacitor | stores_charge, conducts_electricity |
| battery | stores_charge, conducts_electricity |
| thermal | emits_thermal_radiation, transfers_heat, resists_thermal_shock |

### Provenance

Every Specification carries implicit provenance via its `objective`
string (the natural-language input). Stage II generators MUST attach
the originating Specification's objective to every Configuration
they produce, so the chain `objective → spec → configuration →
prediction → measurement` is traceable end-to-end.

### Determinism

Specifications are deterministic: the same objective string compiles
to the same Specification (no RNG). Randomness enters only at Stage II
(candidate generation), where it is controlled by a seed.

### PASS criteria

- A Specification can be compiled from a natural-language objective.
- A candidate Configuration can be scored against a Specification
  (hard constraints + acceptance criteria).
- The scoring function returns a structured result, not a boolean.
