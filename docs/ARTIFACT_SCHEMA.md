# ARTIFACT_SCHEMA.md

## Configuration / Artifact Schema (Stage II+)

A **Configuration** (also called a candidate artifact) is the structured
output of `scripts/artifact_generator.py::ArtifactGenerator`. It is the
canonical object that flows through Stages II → VII of the invention
loop:

```text
Specification → ArtifactGenerator.generate() → Configuration
                                                  ↓
                                       ForwardModel.predict()
                                                  ↓
                                       NoveltyEngine.check()
                                                  ↓
                                  ContradictionSolver.resolve()  (optional)
                                                  ↓
                                  PrototypeCompiler.compile()
                                                  ↓
                                  MeasurementEngine.run()
```

### Component

A Component is one material in one role within a Configuration.

```python
@dataclass
class Component:
    material: str                       # canonical material name, e.g. "bismuth_telluride"
    role: str                           # "active" | "secondary" | "electrode" | "substrate" | "dopant" | "stabilizer"
    capabilities: List[str]             # capability names (see CAPABILITY_SCHEMA.md)
    parameters: Dict[str, float]        # physical parameters in SI units
```

`parameters` is a flat dict of physical properties keyed by canonical
name. Recognized keys (not all need be present for every material):

| Key | Units | Meaning |
|---|---|---|
| seebeck_coefficient | V/K | Seebeck coefficient S |
| electrical_conductivity | S/m | σ |
| thermal_conductivity | W/(m·K) | κ |
| density | kg/m³ | ρ |
| cost_per_kg | USD/kg | catalog cost |
| max_temp | K | max operating temperature |
| porosity | dimensionless | fraction (0-1) |
| substitution_fraction | dimensionless | alloy fraction x (0-1) |

### Configuration

```python
@dataclass
class Configuration:
    config_id: str                      # "CONFIG-{seed:04d}-{i:03d}"
    spec_objective: str                 # originating Specification.objective (provenance)
    domain: str                         # thermoelectric, photovoltaic, etc.
    components: List[Component]
    structure: str                      # "monolithic" | "layered_N" | "segmented_N" | "composite" | "dispersed"
    parameters: Dict[str, float]        # global parameters (thickness, area, T_hot, T_cold, n_layers, ...)
    design_operator_chain: List[str]    # operators applied, e.g. ["init", "layer", "amplify", "substitute"]
    source_capabilities: List[str]      # capability names the spec required
    provenance: Dict[str, Any]          # {"generator", "seed", "timestamp", "base_material"}
    config_hash: str                    # canonical content hash (see below)
```

### config_hash — the canonicality invariant

The `config_hash` is a SHA-256 (truncated to 16 hex chars) of the
canonical JSON serialization of:

- `domain`
- `structure`
- `parameters` (sorted by key, floats rounded to 8 decimals)
- `components` (sorted by `(material, role)`, with `parameters` sorted and rounded)

The hash **deliberately excludes**:
- `config_id`
- `spec_objective` (prose, may be reworded)
- `design_operator_chain` (the path to the configuration, not the configuration itself)
- `provenance` (timestamps, seeds — metadata, not content)
- `source_capabilities` (which capabilities the spec asked for — not the artifact)

This means:

> Two Configurations with the same components, structure, and parameters
> produce the same `config_hash`, regardless of wording, generator seed,
> or operator chain that produced them.

This invariant is enforced by `tests/test_novelty_engine.py` and is
the foundation of configuration-level novelty checking.

### Design Operators (Stage II)

The 12 design operators that may appear in `design_operator_chain`:

| Operator | Effect on Configuration |
|---|---|
| `init` | Create the base monolithic Configuration |
| `combine` | Append a second material as a secondary-role component |
| `replace` | Replace one component's material with another |
| `invert` | Flip a parameter (e.g., reduce thermal_conductivity via porosity) |
| `amplify` | Scale up a parameter (e.g., ×2 seebeck_coefficient) |
| `attenuate` | Scale down a parameter (e.g., ×0.5 thermal_conductivity) |
| `split` | Set n_segments; structure becomes `segmented_N` |
| `merge` | Merge two components into one |
| `layer` | Set n_layers; structure becomes `layered_N` |
| `stabilize` | Add a stabilizer component |
| `modulate` | Set a modulation frequency parameter |
| `substitute` | Partial substitution: blend parameters by substitution_fraction (Vegard's law) |
| `parameterize` | Set a specific parameter (e.g., thickness_m) |

### Determinism

Generation is deterministic under a seed:

```python
gen_a = ArtifactGenerator(seed=42)
gen_b = ArtifactGenerator(seed=42)
assert [c.config_hash for c in gen_a.generate(spec, cg, n=5)] \
    == [c.config_hash for c in gen_b.generate(spec, cg, n=5)]
```

### PASS criteria

- A Configuration has at least one Component with non-empty `parameters`.
- A Configuration has a non-empty `config_hash` of 16 hex chars.
- A Configuration's `config_hash` is invariant under rewording of `spec_objective`.
- A Configuration's `design_operator_chain` records every operator applied.
- Two runs of the generator with the same seed produce identical hashes.
