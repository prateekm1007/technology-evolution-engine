#!/usr/bin/env python3
"""
capability_composer.py — DR-69: Compose capabilities across domains.

If material A has capability X and material B has capability Y, what
capability does the COMBINATION have?

The composer uses composition rules grounded in physics and chemistry:

  - conducts_electricity (A) + transfers_heat (B) → heterojunction_thermoelectric
  - catalyzes_reaction (A) + conducts_electricity (B) → bifunctional_electrocatalyst
  - absorbs_light (A) + stores_charge (B) → photo_supercapacitor
  - resists_corrosion (A) + conducts_electricity (B) → protective_electrode
  - emits_light (A) + transfers_heat (B) → high_power_emitter
  - absorbs_gas (A) + catalyzes_reaction (B) → gas_conversion_catalyst

Each rule is bi-directional in A and B (the composition is commutative
unless explicitly ordered).

Usage:
    from scripts.capability_composer import CapabilityComposer
    cc = CapabilityComposer()
    result = cc.compose(
        material_a="bismuth_telluride", caps_a=["conducts_electricity"],
        material_b="graphene", caps_b=["transfers_heat"])
"""
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class CompositionRule:
    """A rule for composing capabilities across two materials."""
    rule_id: str
    caps_a: List[str]       # capabilities required from material A
    caps_b: List[str]       # capabilities required from material B
    composite_capability: str
    mechanism: str
    ordered: bool = False   # if True, A and B are not interchangeable
    evidence_rank: str = "A"


@dataclass
class ComposedCapability:
    """A capability that emerges from combining two materials."""
    capability: str
    rule_id: str
    material_a: str
    material_b: str
    caps_from_a: List[str]
    caps_from_b: List[str]
    mechanism: str
    evidence_rank: str = "A"


@dataclass
class CompositionResult:
    """The output of CapabilityComposer.compose()."""
    material_a: str
    material_b: str
    caps_a: List[str] = field(default_factory=list)
    caps_b: List[str] = field(default_factory=list)
    composed: List[ComposedCapability] = field(default_factory=list)
    n_rules_evaluated: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_a": self.material_a,
            "material_b": self.material_b,
            "caps_a": self.caps_a,
            "caps_b": self.caps_b,
            "composed": [
                {"capability": cc.capability, "rule_id": cc.rule_id,
                 "material_a": cc.material_a, "material_b": cc.material_b,
                 "caps_from_a": cc.caps_from_a, "caps_from_b": cc.caps_from_b,
                 "mechanism": cc.mechanism, "evidence_rank": cc.evidence_rank}
                for cc in self.composed
            ],
            "n_rules_evaluated": self.n_rules_evaluated,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Built-in composition rules.
# ---------------------------------------------------------------------------
DEFAULT_RULES: List[CompositionRule] = [
    CompositionRule(
        rule_id="C-001",
        caps_a=["conducts_electricity"],
        caps_b=["transfers_heat"],
        composite_capability="heterojunction_thermoelectric",
        mechanism="An electrically conducting material in thermal contact with a "
                  "heat-transferring material forms a heterojunction supporting "
                  "thermoelectric generation across the interface.",
        evidence_rank="A",
    ),
    CompositionRule(
        rule_id="C-002",
        caps_a=["catalyzes_reaction"],
        caps_b=["conducts_electricity"],
        composite_capability="bifunctional_electrocatalyst",
        mechanism="A catalyst layered on an electrically conductive support acts as "
                  "a bifunctional electrocatalyst (e.g., ORR/OER on NiFe oxyhydroxide).",
        evidence_rank="A",
    ),
    CompositionRule(
        rule_id="C-003",
        caps_a=["absorbs_light"],
        caps_b=["stores_charge"],
        composite_capability="photo_supercapacitor",
        mechanism="A photo-absorber connected to a charge-storage electrode creates "
                  "a photo-supercapacitor that stores solar energy directly.",
        evidence_rank="D",
    ),
    CompositionRule(
        rule_id="C-004",
        caps_a=["resists_corrosion"],
        caps_b=["conducts_electricity"],
        composite_capability="protective_electrode",
        mechanism="A corrosion-resistant coating on a conductive substrate yields "
                  "a durable electrode for harsh environments.",
        evidence_rank="A",
    ),
    CompositionRule(
        rule_id="C-005",
        caps_a=["emits_light"],
        caps_b=["transfers_heat"],
        composite_capability="high_power_emitter",
        mechanism="A light emitter thermally coupled to a heat-transfer substrate "
                  "supports high-power operation without thermal runaway.",
        evidence_rank="A",
    ),
    CompositionRule(
        rule_id="C-006",
        caps_a=["absorbs_gas"],
        caps_b=["catalyzes_reaction"],
        composite_capability="gas_conversion_catalyst",
        mechanism="A gas sorbent doped with a catalytic phase captures and converts "
                  "the gas in one step (e.g., CO2 capture + hydrogenation).",
        evidence_rank="D",
    ),
    CompositionRule(
        rule_id="C-007",
        caps_a=["conducts_electricity"],
        caps_b=["conducts_electricity"],
        composite_capability="electrical_junction",
        mechanism="Two conductors with different work functions in contact form an "
                  "electrical junction (ohmic or Schottky).",
        evidence_rank="A",
    ),
    CompositionRule(
        rule_id="C-008",
        caps_a=["transfers_heat"],
        caps_b=["resists_thermal_shock"],
        composite_capability="durable_heat_sink",
        mechanism="A heat-transfer material backed by a thermal-shock-resistant "
                  "support yields a durable heat sink.",
        evidence_rank="A",
    ),
]


class CapabilityComposer:
    """DR-69: composes capabilities across materials."""

    def __init__(self, rules: Optional[List[CompositionRule]] = None):
        self.rules: List[CompositionRule] = list(rules) if rules is not None else list(DEFAULT_RULES)

    # ----- public API ---------------------------------------------------
    def compose(self, material_a: str, caps_a: List[str],
                material_b: str, caps_b: List[str]) -> CompositionResult:
        """Compose capabilities from two materials.

        Args:
            material_a: name of material A
            caps_a: capabilities of A
            material_b: name of material B
            caps_b: capabilities of B

        Returns:
            CompositionResult with composed capabilities
        """
        composed: List[ComposedCapability] = []
        for rule in self.rules:
            if (all(c in caps_a for c in rule.caps_a) and
                    all(c in caps_b for c in rule.caps_b)):
                composed.append(ComposedCapability(
                    capability=rule.composite_capability,
                    rule_id=rule.rule_id,
                    material_a=material_a,
                    material_b=material_b,
                    caps_from_a=list(rule.caps_a),
                    caps_from_b=list(rule.caps_b),
                    mechanism=rule.mechanism,
                    evidence_rank=rule.evidence_rank,
                ))
            elif not rule.ordered:
                # Try the swapped assignment (A↔B)
                if (all(c in caps_b for c in rule.caps_a) and
                        all(c in caps_a for c in rule.caps_b)):
                    composed.append(ComposedCapability(
                        capability=rule.composite_capability,
                        rule_id=rule.rule_id,
                        material_a=material_b,
                        material_b=material_a,
                        caps_from_a=list(rule.caps_a),
                        caps_from_b=list(rule.caps_b),
                        mechanism=rule.mechanism + " (materials swapped)",
                        evidence_rank=rule.evidence_rank,
                    ))

        # Dedupe by (capability, material_a, material_b)
        seen = set()
        unique: List[ComposedCapability] = []
        for cc in composed:
            key = (cc.capability, cc.material_a, cc.material_b)
            if key not in seen:
                seen.add(key)
                unique.append(cc)

        return CompositionResult(
            material_a=material_a,
            material_b=material_b,
            caps_a=list(caps_a),
            caps_b=list(caps_b),
            composed=unique,
            n_rules_evaluated=len(self.rules),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def add_rule(self, rule: CompositionRule) -> None:
        self.rules.append(rule)


def main():
    print("=" * 60)
    print("CAPABILITY COMPOSER (DR-69)")
    print("=" * 60)
    print()

    cc = CapabilityComposer()

    print("Demo 1: bismuth_telluride + graphene")
    r = cc.compose(
        material_a="bismuth_telluride", caps_a=["conducts_electricity"],
        material_b="graphene", caps_b=["transfers_heat"])
    print(f"  A: {r.material_a} caps={r.caps_a}")
    print(f"  B: {r.material_b} caps={r.caps_b}")
    for comp in r.composed:
        print(f"  → {comp.capability} (rule {comp.rule_id}): {comp.mechanism}")
    print()

    print("Demo 2: TiO2 (catalyst + absorbs light) + carbon (conducts)")
    r = cc.compose(
        material_a="tio2", caps_a=["catalyzes_reaction", "absorbs_light"],
        material_b="carbon", caps_b=["conducts_electricity"])
    for comp in r.composed:
        print(f"  → {comp.capability}: {comp.mechanism}")
    print()

    print("Demo 3: no composition possible")
    r = cc.compose(
        material_a="rubber", caps_a=["damps_vibration"],
        material_b="glass", caps_b=["reflects_light"])
    print(f"  composed = {[c.capability for c in r.composed]} (expected empty)")


if __name__ == "__main__":
    main()
