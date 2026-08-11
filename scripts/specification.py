#!/usr/bin/env python3
"""
specification.py — Specification engine (Stage I).

Compiles a natural-language objective into a machine-checkable Specification
with: objective, hard constraints, soft constraints, acceptance criteria,
domain, and capability target vector.

Usage:
    from scripts.specification import SpecificationEngine
    engine = SpecificationEngine()
    spec = engine.compile("improve thermoelectric efficiency of bismuth telluride")
"""
import sys
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class Specification:
    """A machine-checkable specification for an invention target."""
    objective: str                    # the goal (e.g., "improve thermoelectric efficiency")
    domain: str                       # e.g., "thermoelectric"
    hard_constraints: List[Dict]      # must-satisfy (e.g., cost < $100/kg)
    soft_constraints: List[Dict]      # should-satisfy (e.g., minimize weight)
    acceptance_criteria: List[Dict]   # pass/fail tests (e.g., ZT > 1.0)
    capability_targets: List[str]     # required capabilities (e.g., "generates_voltage")
    target_material: Optional[str]    # base material (e.g., "bismuth_telluride")


class SpecificationEngine:
    """Compiles natural-language objectives into machine-checkable specs."""

    # Domain keywords → domain name
    DOMAIN_KEYWORDS = {
        "thermoelectric": ["thermoelectric", "seebeck", "bismuth telluride", "ZT", "figure of merit"],
        "photovoltaic": ["photovoltaic", "solar cell", "bandgap", "photocurrent"],
        "supercapacitor": ["supercapacitor", "capacitance", "energy density", "power density"],
        "battery": ["battery", "lithium", "anode", "cathode", "electrolyte"],
        "thermal": ["thermal", "heat", "cooling", "radiative", "insulation"],
    }

    # Objective keywords → capability targets
    OBJECTIVE_CAPABILITIES = {
        "efficiency": ["generates_voltage", "conducts_electricity"],
        "conductivity": ["conducts_electricity"],
        "stability": ["resists_corrosion", "resists_thermal_shock"],
        "capacity": ["stores_charge"],
        "power": ["generates_voltage", "conducts_electricity"],
        "cooling": ["emits_thermal_radiation", "transfers_heat"],
    }

    def compile(self, objective_text: str) -> Specification:
        """Compile a natural-language objective into a Specification.

        Args:
            objective_text: e.g., "improve thermoelectric efficiency of bismuth telluride"

        Returns:
            Specification object
        """
        text_lower = objective_text.lower()

        # Identify domain
        domain = "unknown"
        for dom, keywords in self.DOMAIN_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                domain = dom
                break

        # Identify target material
        target_material = None
        material_patterns = [
            r"bismuth telluride|bi2te3|bi₂te₃",
            r"graphene",
            r"mxene",
            r"perovskite",
            r"lithium iron phosphate|lifepo4",
            r"stefan.boltzmann",
        ]
        for pat in material_patterns:
            match = re.search(pat, text_lower)
            if match:
                target_material = match.group(0)
                break

        # Identify objective keyword
        objective = objective_text
        capability_targets = []
        for obj_kw, caps in self.OBJECTIVE_CAPABILITIES.items():
            if obj_kw in text_lower:
                capability_targets = caps
                break

        # Hard constraints (domain-specific defaults)
        hard_constraints = []
        if domain == "thermoelectric":
            hard_constraints = [
                {"name": "temperature_range", "operator": ">=", "value": 300, "units": "K",
                 "description": "Must operate at or above room temperature"},
                {"name": "stability", "operator": ">=", "value": 100, "units": "cycles",
                 "description": "Must survive 100 thermal cycles"},
            ]
        elif domain == "supercapacitor":
            hard_constraints = [
                {"name": "voltage", "operator": ">=", "value": 1.0, "units": "V",
                 "description": "Must operate at ≥1V"},
            ]
        else:
            hard_constraints = [
                {"name": "cost", "operator": "<=", "value": 1000, "units": "USD/kg",
                 "description": "Material cost must be reasonable"},
            ]

        # Soft constraints
        soft_constraints = [
            {"name": "weight", "operator": "minimize", "value": None, "units": "kg",
             "description": "Minimize weight"},
            {"name": "complexity", "operator": "minimize", "value": None, "units": "count",
             "description": "Minimize manufacturing complexity"},
        ]

        # Acceptance criteria (domain-specific)
        acceptance_criteria = []
        if domain == "thermoelectric":
            acceptance_criteria = [
                {"metric": "ZT", "operator": ">", "threshold": 1.0,
                 "description": "Figure of merit ZT > 1.0"},
                {"metric": "seebeck_coefficient", "operator": ">", "threshold": 200,
                 "units": "µV/K", "description": "Seebeck > 200 µV/K"},
            ]
        else:
            acceptance_criteria = [
                {"metric": "performance", "operator": ">", "threshold": 0.5,
                 "description": "Performance metric > 0.5"},
            ]

        return Specification(
            objective=objective,
            domain=domain,
            hard_constraints=hard_constraints,
            soft_constraints=soft_constraints,
            acceptance_criteria=acceptance_criteria,
            capability_targets=capability_targets,
            target_material=target_material,
        )

    def score_candidate(self, spec: Specification, candidate: Dict) -> Dict:
        """Score a candidate artifact against a specification.

        Args:
            spec: the Specification
            candidate: dict with predicted properties

        Returns:
            dict with hard_pass, soft_score, acceptance_pass, overall
        """
        # Check hard constraints
        hard_pass = True
        hard_results = []
        for hc in spec.hard_constraints:
            val = candidate.get(hc["name"], None)
            if val is None:
                hard_results.append({"constraint": hc["name"], "status": "MISSING"})
                hard_pass = False
            elif hc["operator"] == ">=" and val >= hc["value"]:
                hard_results.append({"constraint": hc["name"], "status": "PASS", "value": val})
            elif hc["operator"] == "<=" and val <= hc["value"]:
                hard_results.append({"constraint": hc["name"], "status": "PASS", "value": val})
            else:
                hard_results.append({"constraint": hc["name"], "status": "FAIL", "value": val})
                hard_pass = False

        # Check acceptance criteria
        acceptance_pass = True
        acceptance_results = []
        for ac in spec.acceptance_criteria:
            val = candidate.get(ac["metric"], None)
            if val is None:
                acceptance_results.append({"metric": ac["metric"], "status": "MISSING"})
                acceptance_pass = False
            elif ac["operator"] == ">" and val > ac["threshold"]:
                acceptance_results.append({"metric": ac["metric"], "status": "PASS", "value": val})
            else:
                acceptance_results.append({"metric": ac["metric"], "status": "FAIL", "value": val})
                acceptance_pass = False

        return {
            "hard_pass": hard_pass,
            "hard_results": hard_results,
            "acceptance_pass": acceptance_pass,
            "acceptance_results": acceptance_results,
            "overall": hard_pass and acceptance_pass,
        }


def main():
    """Demo: specification engine."""
    print("=" * 60)
    print("SPECIFICATION ENGINE (Stage I)")
    print("=" * 60)
    print()

    engine = SpecificationEngine()
    spec = engine.compile("improve thermoelectric efficiency of bismuth telluride")

    print(f"Objective: {spec.objective}")
    print(f"Domain: {spec.domain}")
    print(f"Target material: {spec.target_material}")
    print(f"Capability targets: {spec.capability_targets}")
    print(f"Hard constraints: {len(spec.hard_constraints)}")
    for hc in spec.hard_constraints:
        print(f"  {hc['name']} {hc['operator']} {hc['value']} {hc.get('units','')}")
    print(f"Acceptance criteria: {len(spec.acceptance_criteria)}")
    for ac in spec.acceptance_criteria:
        print(f"  {ac['metric']} {ac['operator']} {ac['threshold']}")
    print()

    # Score a candidate
    candidate = {"ZT": 1.2, "seebeck_coefficient": 250, "temperature_range": 350, "stability": 200}
    result = engine.score_candidate(spec, candidate)
    print(f"Candidate score: overall={result['overall']}")
    for r in result["hard_results"]:
        print(f"  Hard: {r}")
    for r in result["acceptance_results"]:
        print(f"  Acceptance: {r}")


if __name__ == "__main__":
    main()
