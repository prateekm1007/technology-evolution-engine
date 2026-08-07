#!/usr/bin/env python3
"""
capability_constraints.py — DR-69: Derive physics constraints from capabilities.

Each capability implies one or more quantitative physics constraints on
the material's parameters. For example:

  conducts_electricity  → resistivity < 1e-2 Ω·m  (σ > 1e2 S/m)
  transfers_heat        → thermal_conductivity > 1e-3 W/(m·K)
  emits_thermal_radiation → emissivity > 0.5
  absorbs_light         → optical_absorption_coeff > 1e2 cm^-1
  stores_charge         → capacitance > 1e-6 F/g
  catalyzes_reaction    → overpotential < 1.0 V
  resists_corrosion     → corrosion_rate < 0.1 mm/year
  bears_load            → yield_strength > 10 MPa

These constraints are then enforced by the constraint-pruning step of
the search engine (DR-73) and the prototype compiler (Stage VI).

Usage:
    from scripts.capability_constraints import CapabilityConstraints
    cc = CapabilityConstraints()
    constraints = cc.derive(["conducts_electricity", "transfers_heat"])
    # constraints = [CapabilityConstraint(...), ...]
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class CapabilityConstraint:
    """A physics constraint implied by a capability."""
    capability: str
    parameter: str           # the parameter being constrained
    operator: str            # '<', '>', '<=', '>=', '=='
    threshold: float         # the bound
    units: str               # SI units
    rationale: str           # why this bound
    evidence_rank: str = "A"


@dataclass
class ConstraintDerivationResult:
    """The output of CapabilityConstraints.derive()."""
    input_capabilities: List[str] = field(default_factory=list)
    constraints: List[CapabilityConstraint] = field(default_factory=list)
    n_capabilities: int = 0
    n_constraints: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_capabilities": self.input_capabilities,
            "constraints": [
                {"capability": c.capability, "parameter": c.parameter,
                 "operator": c.operator, "threshold": c.threshold,
                 "units": c.units, "rationale": c.rationale,
                 "evidence_rank": c.evidence_rank}
                for c in self.constraints
            ],
            "n_capabilities": self.n_capabilities,
            "n_constraints": self.n_constraints,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Built-in capability → constraint table (evidence rank A = physics, D = lit).
# ---------------------------------------------------------------------------
DEFAULT_CONSTRAINT_TABLE: Dict[str, List[CapabilityConstraint]] = {
    "conducts_electricity": [
        CapabilityConstraint(
            capability="conducts_electricity",
            parameter="electrical_conductivity", operator=">",
            threshold=1.0e2, units="S/m",
            rationale="Materials conventionally classed as electrical conductors "
                      "have σ > 100 S/m (e.g., semiconductors at the lower bound).",
            evidence_rank="A",
        ),
        CapabilityConstraint(
            capability="conducts_electricity",
            parameter="resistivity", operator="<",
            threshold=1.0e-2, units="Ω·m",
            rationale="Resistivity ρ = 1/σ. Conductor implies ρ < 0.01 Ω·m.",
            evidence_rank="A",
        ),
    ],
    "transfers_heat": [
        CapabilityConstraint(
            capability="transfers_heat",
            parameter="thermal_conductivity", operator=">",
            threshold=1.0e-3, units="W/(m·K)",
            rationale="A heat-transfer material must have κ > 1e-3 W/(m·K); "
                      "below this the material is effectively an insulator.",
            evidence_rank="A",
        ),
    ],
    "emits_thermal_radiation": [
        CapabilityConstraint(
            capability="emits_thermal_radiation",
            parameter="emissivity", operator=">",
            threshold=0.5, units="dimensionless",
            rationale="A useful thermal emitter has emissivity > 0.5 "
                      "(a blackbody is 1.0).",
            evidence_rank="A",
        ),
    ],
    "absorbs_light": [
        CapabilityConstraint(
            capability="absorbs_light",
            parameter="optical_absorption_coeff", operator=">",
            threshold=1.0e2, units="cm^-1",
            rationale="An optically absorbing material has α > 100 cm^-1 over "
                      "the relevant band.",
            evidence_rank="A",
        ),
    ],
    "stores_charge": [
        CapabilityConstraint(
            capability="stores_charge",
            parameter="specific_capacitance", operator=">",
            threshold=1.0e-6, units="F/g",
            rationale="A charge-storage material has C > 1 µF/g (supercapacitor "
                      "materials have 10–1000 F/g).",
            evidence_rank="A",
        ),
    ],
    "catalyzes_reaction": [
        CapabilityConstraint(
            capability="catalyzes_reaction",
            parameter="overpotential", operator="<",
            threshold=1.0, units="V",
            rationale="A useful electrocatalyst operates at overpotential < 1.0 V.",
            evidence_rank="A",
        ),
    ],
    "resists_corrosion": [
        CapabilityConstraint(
            capability="resists_corrosion",
            parameter="corrosion_rate", operator="<",
            threshold=0.1, units="mm/year",
            rationale="Materials with corrosion rate < 0.1 mm/year are classed "
                      "as 'outstanding' per ASTM G31.",
            evidence_rank="D",
        ),
    ],
    "bears_load": [
        CapabilityConstraint(
            capability="bears_load",
            parameter="yield_strength", operator=">",
            threshold=10.0, units="MPa",
            rationale="A load-bearing material has σ_y > 10 MPa "
                      "(structural polymers start near 20 MPa).",
            evidence_rank="A",
        ),
    ],
    "absorbs_gas": [
        CapabilityConstraint(
            capability="absorbs_gas",
            parameter="specific_surface_area", operator=">",
            threshold=100.0, units="m²/g",
            rationale="Useful gas sorbents (MOFs, zeolites) have BET > 100 m²/g.",
            evidence_rank="D",
        ),
    ],
    "emits_light": [
        CapabilityConstraint(
            capability="emits_light",
            parameter="photoluminescence_quantum_yield", operator=">",
            threshold=0.01, units="dimensionless",
            rationale="A practical light emitter has PLQY > 1%.",
            evidence_rank="D",
        ),
    ],
}


class CapabilityConstraints:
    """DR-69: derive physics constraints from capabilities."""

    def __init__(self, table: Optional[Dict[str, List[CapabilityConstraint]]] = None):
        self.table: Dict[str, List[CapabilityConstraint]] = (
            dict(table) if table is not None
            else {k: list(v) for k, v in DEFAULT_CONSTRAINT_TABLE.items()}
        )

    # ----- public API ---------------------------------------------------
    def derive(self, capabilities: List[str]) -> ConstraintDerivationResult:
        """Derive all physics constraints implied by a set of capabilities.

        Args:
            capabilities: list of capability names

        Returns:
            ConstraintDerivationResult with all implied constraints
        """
        constraints: List[CapabilityConstraint] = []
        seen = set()
        for cap in capabilities:
            for c in self.table.get(cap, []):
                key = (c.capability, c.parameter, c.operator, c.threshold)
                if key not in seen:
                    seen.add(key)
                    constraints.append(c)

        return ConstraintDerivationResult(
            input_capabilities=list(capabilities),
            constraints=constraints,
            n_capabilities=len(capabilities),
            n_constraints=len(constraints),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def check_candidate(self, capabilities: List[str],
                        candidate_params: Dict[str, float]) -> Dict[str, Any]:
        """Check whether a candidate's parameters satisfy the constraints
        implied by its claimed capabilities.

        Args:
            capabilities: the candidate's claimed capabilities
            candidate_params: the candidate's parameter values

        Returns:
            dict with 'pass' (bool), 'violations' (list), 'n_checked' (int)
        """
        result = self.derive(capabilities)
        violations = []
        n_checked = 0
        for c in result.constraints:
            val = candidate_params.get(c.parameter)
            if val is None:
                # Missing parameter is a soft skip (not necessarily a violation)
                continue
            n_checked += 1
            ops = {">": lambda a, b: a > b,
                   "<": lambda a, b: a < b,
                   ">=": lambda a, b: a >= b,
                   "<=": lambda a, b: a <= b,
                   "==": lambda a, b: a == b}
            check = ops.get(c.operator)
            if check is None:
                continue
            if not check(val, c.threshold):
                violations.append({
                    "capability": c.capability,
                    "parameter": c.parameter,
                    "operator": c.operator,
                    "threshold": c.threshold,
                    "value": val,
                    "units": c.units,
                    "rationale": c.rationale,
                })
        return {
            "pass": len(violations) == 0,
            "violations": violations,
            "n_checked": n_checked,
            "n_constraints": result.n_constraints,
        }

    def add_constraint(self, capability: str, constraint: CapabilityConstraint) -> None:
        self.table.setdefault(capability, []).append(constraint)


def main():
    print("=" * 60)
    print("CAPABILITY CONSTRAINTS (DR-69)")
    print("=" * 60)
    print()

    cc = CapabilityConstraints()

    print("Demo 1: derive constraints")
    caps = ["conducts_electricity", "transfers_heat"]
    result = cc.derive(caps)
    print(f"  Capabilities: {caps}")
    for c in result.constraints:
        print(f"  {c.capability} → {c.parameter} {c.operator} "
              f"{c.threshold} {c.units} ({c.evidence_rank})")
    print()

    print("Demo 2: check candidate (PASS)")
    check = cc.check_candidate(
        ["conducts_electricity", "transfers_heat"],
        {"electrical_conductivity": 1.0e5,
         "thermal_conductivity": 1.5})
    print(f"  pass = {check['pass']}, violations = {check['violations']}")
    print()

    print("Demo 3: check candidate (FAIL)")
    check = cc.check_candidate(
        ["conducts_electricity"],
        {"electrical_conductivity": 1.0e-3})  # way too low
    print(f"  pass = {check['pass']}")
    for v in check["violations"]:
        print(f"  VIOLATION: {v['parameter']} {v['operator']} "
              f"{v['threshold']} {v['units']} (got {v['value']})")


if __name__ == "__main__":
    main()
