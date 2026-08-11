#!/usr/bin/env python3
"""
capability_reasoner.py — DR-69: Reason about capabilities.

Given a set of capabilities, infer what OTHER capabilities are implied
(e.g., conducts_electricity → can_generate_current). Uses a rule-based
inference engine with forward chaining.

Rules are explicit and grounded in physics:
  - conducts_electricity + temperature_gradient → can_generate_current (Seebeck)
  - transfers_heat + temperature_gradient → can_drive_heat_pump (Peltier)
  - absorbs_light + generates_voltage → photovoltaic_effect
  - stores_charge + high_surface_area → supercapacitor
  - conducts_electricity + low_thermal_conductivity → thermoelectric_candidate
  - catalyzes_reaction + conducts_electricity → electrocatalyst
  - emits_thermal_radiation + high_emissivity → radiative_cooling
  - resists_corrosion + conducts_electricity → stable_electrode
  - absorbs_gas + high_surface_area → gas_storage

Usage:
    from scripts.capability_reasoner import CapabilityReasoner
    cr = CapabilityReasoner()
    inferred = cr.infer(["conducts_electricity", "transfers_heat"])
    # inferred = [InferredCapability(name="can_generate_current", rule="..."), ...]
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Set, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class InferenceRule:
    """A forward-chaining inference rule over capabilities."""
    rule_id: str
    premises: List[str]          # capabilities that must ALL be present
    conclusion: str              # capability that is inferred
    mechanism: str               # the physics mechanism
    evidence_rank: str = "A"     # A=physics, D=lit, etc.


@dataclass
class InferredCapability:
    """A capability inferred by the reasoner."""
    name: str
    rule_id: str
    mechanism: str
    premises: List[str]
    evidence_rank: str = "A"


@dataclass
class ReasoningResult:
    """The output of CapabilityReasoner.infer()."""
    input_capabilities: List[str] = field(default_factory=list)
    inferred: List[InferredCapability] = field(default_factory=list)
    closure: List[str] = field(default_factory=list)  # input + inferred
    n_iterations: int = 0
    rules_fired: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_capabilities": self.input_capabilities,
            "inferred": [
                {"name": ic.name, "rule_id": ic.rule_id, "mechanism": ic.mechanism,
                 "premises": ic.premises, "evidence_rank": ic.evidence_rank}
                for ic in self.inferred
            ],
            "closure": self.closure,
            "n_iterations": self.n_iterations,
            "rules_fired": self.rules_fired,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Built-in inference rules (grounded in physics, evidence rank A or D).
# ---------------------------------------------------------------------------
DEFAULT_RULES: List[InferenceRule] = [
    InferenceRule(
        rule_id="R-001",
        premises=["conducts_electricity", "transfers_heat"],
        conclusion="can_generate_current",
        mechanism="Seebeck effect: a temperature gradient across a conductor "
                  "with finite thermal conductivity generates a voltage/current.",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-002",
        premises=["conducts_electricity", "stores_thermal_energy"],
        conclusion="thermoelectric_candidate",
        mechanism="A material that conducts electricity and stores/transport thermal "
                  "energy can support thermoelectric effects (ZT > 0).",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-003",
        premises=["absorbs_light", "generates_voltage"],
        conclusion="photovoltaic_effect",
        mechanism="Photon absorption creating electron-hole pairs separated by "
                  "a built-in field yields photovoltaic power generation.",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-004",
        premises=["stores_charge", "absorbs_light"],
        conclusion="supercapacitor_candidate",
        mechanism="High-surface-area charge storage combined with photo-absorption "
                  "enables photo-supercapacitor architectures.",
        evidence_rank="D",
    ),
    InferenceRule(
        rule_id="R-005",
        premises=["catalyzes_reaction", "conducts_electricity"],
        conclusion="electrocatalyst",
        mechanism="A catalyst that also conducts electricity can serve as an "
                  "electrocatalytic electrode (e.g., for water splitting).",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-006",
        premises=["emits_thermal_radiation", "transfers_heat"],
        conclusion="radiative_cooling_candidate",
        mechanism="High-emissivity surfaces radiating into a cold sink while "
                  "transferring heat away from a load enable passive radiative cooling.",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-007",
        premises=["resists_corrosion", "conducts_electricity"],
        conclusion="stable_electrode",
        mechanism="Corrosion resistance plus electrical conductivity is the prerequisite "
                  "for a durable electrode in electrochemical cells.",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-008",
        premises=["absorbs_gas", "stores_charge"],
        conclusion="gas_sensor_candidate",
        mechanism="Gas absorption that perturbs charge storage capacitance is the "
                  "basis of capacitive gas sensors (MOF-based).",
        evidence_rank="D",
    ),
    InferenceRule(
        rule_id="R-009",
        premises=["can_generate_current", "stable_electrode"],
        conclusion="energy_harvesting_device",
        mechanism="Current generation in a stable electrode system yields a usable "
                  "energy-harvesting device.",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-010",
        premises=["thermoelectric_candidate", "can_generate_current"],
        conclusion="thermoelectric_generator",
        mechanism="A material exhibiting thermoelectric behavior AND measurable "
                  "current generation under a gradient is a thermoelectric generator.",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-011",
        premises=["emits_light", "conducts_electricity"],
        conclusion="led_candidate",
        mechanism="Electroluminescence: electrical injection into a light-emitting "
                  "material yields an LED.",
        evidence_rank="A",
    ),
    InferenceRule(
        rule_id="R-012",
        premises=["photovoltaic_effect", "stable_electrode"],
        conclusion="solar_cell_candidate",
        mechanism="A photovoltaic effect with a stable electrode yields a "
                  "functional solar cell.",
        evidence_rank="A",
    ),
]


class CapabilityReasoner:
    """DR-69: rule-based forward-chaining capability reasoner."""

    def __init__(self, rules: Optional[List[InferenceRule]] = None,
                 max_iterations: int = 20):
        self.rules: List[InferenceRule] = list(rules) if rules is not None else list(DEFAULT_RULES)
        self.max_iterations = max_iterations

    # ----- public API ---------------------------------------------------
    def infer(self, capabilities: List[str]) -> ReasoningResult:
        """Run forward-chaining inference to a fixpoint.

        Args:
            capabilities: the initial set of capabilities (names)

        Returns:
            ReasoningResult with inferred capabilities and closure
        """
        known: Set[str] = set(c for c in capabilities if c)
        inferred: List[InferredCapability] = []
        rules_fired: List[str] = []
        n_iter = 0

        for _ in range(self.max_iterations):
            n_iter += 1
            newly_inferred: List[InferredCapability] = []
            for rule in self.rules:
                if rule.conclusion in known:
                    continue
                if all(p in known for p in rule.premises):
                    newly_inferred.append(InferredCapability(
                        name=rule.conclusion,
                        rule_id=rule.rule_id,
                        mechanism=rule.mechanism,
                        premises=list(rule.premises),
                        evidence_rank=rule.evidence_rank,
                    ))
                    rules_fired.append(rule.rule_id)
            if not newly_inferred:
                break
            for ic in newly_inferred:
                if ic.name not in known:
                    known.add(ic.name)
                    inferred.append(ic)

        return ReasoningResult(
            input_capabilities=list(capabilities),
            inferred=inferred,
            closure=sorted(known),
            n_iterations=n_iter,
            rules_fired=rules_fired,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, capability: str, result: ReasoningResult) -> Optional[str]:
        """Explain WHY a capability was inferred (returns the mechanism)."""
        for ic in result.inferred:
            if ic.name == capability:
                return (f"{capability} inferred by rule {ic.rule_id} from "
                        f"{ic.premises}. Mechanism: {ic.mechanism}")
        return None

    def add_rule(self, rule: InferenceRule) -> None:
        """Add a custom rule (used in tests)."""
        self.rules.append(rule)


def main():
    print("=" * 60)
    print("CAPABILITY REASONER (DR-69)")
    print("=" * 60)
    print()

    cr = CapabilityReasoner()

    # Demo 1: thermoelectric reasoning
    print("Demo 1: thermoelectric chain")
    result = cr.infer(["conducts_electricity", "transfers_heat",
                       "stores_thermal_energy"])
    print(f"  Input: {result.input_capabilities}")
    print(f"  Inferred:")
    for ic in result.inferred:
        print(f"    - {ic.name} (rule {ic.rule_id}): {ic.mechanism}")
    print(f"  Closure: {result.closure}")
    print(f"  Iterations: {result.n_iterations}")
    print()

    # Demo 2: solar cell reasoning
    print("Demo 2: solar-cell chain")
    result = cr.infer(["absorbs_light", "generates_voltage",
                       "resists_corrosion", "conducts_electricity"])
    print(f"  Input: {result.input_capabilities}")
    print(f"  Inferred:")
    for ic in result.inferred:
        print(f"    - {ic.name} (rule {ic.rule_id}): {ic.mechanism}")
    print(f"  Closure: {result.closure}")
    print()

    # Demo 3: no inference possible
    print("Demo 3: no inference")
    result = cr.infer(["damps_vibration"])
    print(f"  Input: {result.input_capabilities}")
    print(f"  Inferred: {[ic.name for ic in result.inferred]} (expected empty)")


if __name__ == "__main__":
    main()
