# CAPABILITY_SCHEMA.md

## Capability Graph Schema

A **capability** is an intermediate object between discovery and invention.
It represents what a material or system CAN DO, not what it IS.

### Capability

```python
@dataclass
class Capability:
    capability_id: str        # unique ID
    name: str                 # e.g., "conducts_electricity"
    category: str             # electrical, thermal, mechanical, chemical, optical
    direction: str            # "enable" or "prevent"
    measured_by: str          # how to verify (e.g., "conductivity_measurement")
    units: str                # SI units (e.g., "S/m")
    typical_range: tuple      # (min, max) typical values
```

### CapabilityEdge

```python
@dataclass
class CapabilityEdge:
    source: str               # entity/material that HAS the capability
    capability: str           # capability name
    target: str               # what the capability acts ON (optional)
    confidence: float         # 0-1
    provenance: str           # source document + extraction method
```

### Capability Categories

| Category | Examples |
|---|---|
| electrical | conducts_electricity, stores_charge, generates_voltage |
| thermal | transfers_heat, stores_thermal_energy, resists_thermal_shock |
| mechanical | bears_load, resists_deformation, damps_vibration |
| chemical | resists_corrosion, catalyzes_reaction, absorbs_gas |
| optical | absorbs_light, emits_light, reflects_light |

### Derivation from Discovery Graph

Capabilities are DERIVED from extracted entities and relations:
- "graphene --conducts--> electricity" → capability(graphene, conducts_electricity)
- "PCM --absorbs--> heat" → capability(PCM, stores_thermal_energy)
- "coating --prevents--> corrosion" → capability(coating, resists_corrosion)

### PASS criteria

- Capabilities are derived from the discovery graph, not hand-listed
- Capability extraction is test-covered
- At least one known domain compiles into capability form
