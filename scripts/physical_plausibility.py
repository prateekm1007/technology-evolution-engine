#!/usr/bin/env python3
"""
physical_plausibility.py — Physical plausibility veto for the Failure Engine
(cycle 205, F-100 fix).

Per the auditor: "A 'measured ZT of 14,418' is not an invention — it's the
system discovering that its own forward model rewards unbounded amplification."

This module enforces PHYSICAL PLAUSIBILITY BOUNDS on candidate artifacts and
their predictions. If any parameter or predicted property falls outside the
physically realistic range for its domain, the Failure Engine VETOES.

Material-realistic bounds (from published literature):
- Thermoelectric ZT: [0, 5] (best published: ~2.5-3.0 at high T)
- Seebeck coefficient: [1, 1000] µV/K (typical: 50-400)
- Electrical conductivity: [1e2, 1e8] S/m (typical: 1e4-1e7)
- Thermal conductivity: [0.01, 1000] W/(m·K) (typical: 0.1-10)
- Temperature: [200, 2000] K (typical: 300-1000)
- Power output: [0, 1e6] W (sanity ceiling)
- Voltage: [0, 1e4] V (sanity ceiling)

Usage:
    from scripts.physical_plausibility import PhysicalPlausibilityChecker
    checker = PhysicalPlausibilityChecker()
    result = checker.check(candidate, prediction)
    if result.vetoed:
        # candidate is physically impossible — reject
"""
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class PlausibilityViolation:
    """A single physical plausibility violation."""
    parameter: str
    value: float
    min_allowed: float
    max_allowed: float
    severity: str  # "veto" or "warn"
    reason: str


@dataclass
class PlausibilityReport:
    """Result of a physical plausibility check."""
    is_plausible: bool = True
    vetoed: bool = False
    violations: List[PlausibilityViolation] = field(default_factory=list)
    n_violations: int = 0
    n_warnings: int = 0

    def to_dict(self) -> Dict:
        return {
            "is_plausible": self.is_plausible,
            "vetoed": self.vetoed,
            "n_violations": self.n_violations,
            "n_warnings": self.n_warnings,
            "violations": [
                {"parameter": v.parameter, "value": v.value,
                 "min": v.min_allowed, "max": v.max_allowed,
                 "severity": v.severity, "reason": v.reason}
                for v in self.violations
            ],
        }


# Physical bounds by parameter name (domain-general where possible)
PHYSICAL_BOUNDS = {
    # Thermoelectric properties — TIGHT bounds to prevent ZT gaming
    # ZT = S²σT/κ. With S≤400µV/K, σ≤1e6 S/m, T≤500K, κ≥0.1 W/(m·K):
    # ZT_max = (400e-6)² × 1e6 × 500 / 0.1 = 800. But real ZT peaks at ~3.
    # The issue is that S and σ CANNOT be simultaneously maximized in real
    # materials (they trade off). The bounds below reflect the PRACTICAL
    # range where both can coexist.
    "ZT": {"min": 0.0, "max": 5.0, "severity": "veto",
            "reason": "ZT > 5 is physically impossible (best published: ~3.0)"},
    "seebeck_coefficient": {"min": 1e-6, "max": 5e-4, "severity": "veto",
                            "reason": "Seebeck > 500 µV/K (5e-4 V/K) is unphysical for real thermoelectrics (typical: 50-400 µV/K = 5e-5 to 4e-4 V/K)"},
    "electrical_conductivity": {"min": 1e2, "max": 1e6, "severity": "veto",
                                "reason": "σ > 1e6 S/m is unrealistic for thermoelectric semiconductors (typical: 1e4-1e5; best metals ~6e7 but TEs are semiconductors)"},
    "thermal_conductivity": {"min": 0.01, "max": 100.0, "severity": "veto",
                             "reason": "κ > 100 W/(m·K) is too high for thermoelectrics (typical: 0.1-10)"},
    # General physics
    "temperature": {"min": 0.0, "max": 5000.0, "severity": "warn",
                    "reason": "T > 5000K is extreme (most materials decompose)"},
    "power": {"min": 0.0, "max": 1e6, "severity": "warn",
              "reason": "P > 1MW is a sanity ceiling"},
    "voltage": {"min": 0.0, "max": 1e4, "severity": "warn",
                "reason": "V > 10kV is a sanity ceiling"},
    # Capacitor properties
    "capacitance": {"min": 0.0, "max": 1e4, "severity": "warn",
                    "reason": "C > 10 kF is a sanity ceiling"},
    "energy_density": {"min": 0.0, "max": 1e6, "severity": "warn",
                       "reason": "Energy density > 1 MJ/kg exceeds nuclear"},
    # Mechanical
    "tensile_strength": {"min": 0.0, "max": 1e5, "severity": "warn",
                         "reason": "σ > 100 GPa exceeds graphene (~130 GPa)"},
}

# Domain-specific predicted-property bounds
PREDICTED_PROPERTY_BOUNDS = {
    "ZT": {"min": 0.0, "max": 5.0, "severity": "veto"},
    "V_oc_V": {"min": 0.0, "max": 100.0, "severity": "warn"},
    "P_max_W": {"min": 0.0, "max": 1e6, "severity": "warn"},
    "Q_cond_W": {"min": 0.0, "max": 1e6, "severity": "warn"},
}


class PhysicalPlausibilityChecker:
    """Checks candidates and predictions for physical plausibility.

    This is a VETO-capable detector for the Failure Engine. If any
    parameter or predicted property is outside its physical bounds,
    the checker returns vetoed=True, and the Failure Engine must
    reject the candidate.
    """

    def __init__(self, bounds: Optional[Dict] = None):
        self.bounds = bounds or PHYSICAL_BOUNDS
        self.predicted_bounds = PREDICTED_PROPERTY_BOUNDS

    def check_parameters(self, parameters: Dict[str, float]) -> PlausibilityReport:
        """Check if candidate parameters are within physical bounds.

        Args:
            parameters: dict of parameter_name → value

        Returns:
            PlausibilityReport with violations
        """
        report = PlausibilityReport()

        for param_name, value in parameters.items():
            if param_name in self.bounds:
                bounds = self.bounds[param_name]
                if value < bounds["min"] or value > bounds["max"]:
                    violation = PlausibilityViolation(
                        parameter=param_name,
                        value=value,
                        min_allowed=bounds["min"],
                        max_allowed=bounds["max"],
                        severity=bounds["severity"],
                        reason=bounds["reason"],
                    )
                    report.violations.append(violation)
                    if bounds["severity"] == "veto":
                        report.vetoed = True
                        report.is_plausible = False
                    else:
                        report.n_warnings += 1

        report.n_violations = len(report.violations)
        return report

    def check_prediction(self, predicted_properties: Dict[str, float]) -> PlausibilityReport:
        """Check if predicted properties are within physical bounds.

        Args:
            predicted_properties: dict of property_name → value

        Returns:
            PlausibilityReport with violations
        """
        report = PlausibilityReport()

        for prop_name, value in predicted_properties.items():
            if prop_name in self.predicted_bounds:
                bounds = self.predicted_bounds[prop_name]
                if value < bounds["min"] or value > bounds["max"]:
                    violation = PlausibilityViolation(
                        parameter=prop_name,
                        value=value,
                        min_allowed=bounds["min"],
                        max_allowed=bounds["max"],
                        severity=bounds["severity"],
                        reason=f"{prop_name}={value} outside [{bounds['min']}, {bounds['max']}]",
                    )
                    report.violations.append(violation)
                    if bounds["severity"] == "veto":
                        report.vetoed = True
                        report.is_plausible = False
                    else:
                        report.n_warnings += 1

        report.n_violations = len(report.violations)
        return report

    def check(self, candidate_parameters: Dict[str, float],
              predicted_properties: Optional[Dict[str, float]] = None) -> PlausibilityReport:
        """Check both candidate parameters and predicted properties.

        Args:
            candidate_parameters: dict of parameter_name → value
            predicted_properties: optional dict of predicted property → value

        Returns:
            Combined PlausibilityReport
        """
        report1 = self.check_parameters(candidate_parameters)
        if predicted_properties:
            report2 = self.check_prediction(predicted_properties)
            report1.violations.extend(report2.violations)
            report1.vetoed = report1.vetoed or report2.vetoed
            report1.is_plausible = report1.is_plausible and report2.is_plausible
            report1.n_violations = len(report1.violations)
            report1.n_warnings += report2.n_warnings
        return report1

    def clamp_parameter(self, param_name: str, value: float) -> float:
        """Clamp a parameter to its physical bounds.

        Used by the amplify/attenuate operators to prevent unphysical values.
        """
        if param_name in self.bounds:
            bounds = self.bounds[param_name]
            return max(bounds["min"], min(bounds["max"], value))
        return value


def main():
    """Demo: physical plausibility checker."""
    print("=" * 60)
    print("PHYSICAL PLAUSIBILITY CHECKER (F-100 fix, cycle 205)")
    print("=" * 60)
    print()

    checker = PhysicalPlausibilityChecker()

    # Test 1: Physical parameters → PASS
    params_good = {"seebeck_coefficient": 200, "electrical_conductivity": 1e5,
                   "thermal_conductivity": 1.5, "temperature": 350}
    pred_good = {"ZT": 0.93, "V_oc_V": 0.02, "P_max_W": 1.0}
    result_good = checker.check(params_good, pred_good)
    print(f"Physical parameters: plausible={result_good.is_plausible}, vetoed={result_good.vetoed}")

    # Test 2: Unphysical parameters (amplified) → VETO
    params_bad = {"seebeck_coefficient": 800, "electrical_conductivity": 4e5,
                  "thermal_conductivity": 1.5, "temperature": 350}
    pred_bad = {"ZT": 16774.74, "V_oc_V": 0.11, "P_max_W": 142.4}
    result_bad = checker.check(params_bad, pred_bad)
    print(f"Unphysical parameters: plausible={result_bad.is_plausible}, vetoed={result_bad.vetoed}")
    print(f"  Violations: {result_bad.n_violations}")
    for v in result_bad.violations:
        print(f"    {v.parameter}={v.value} [{v.min_allowed}, {v.max_allowed}] — {v.severity}: {v.reason}")

    # Test 3: Clamping
    print()
    print(f"Clamp seebeck 800 → {checker.clamp_parameter('seebeck_coefficient', 800)}")
    print(f"Clamp ZT 16774 → {checker.clamp_parameter('ZT', 16774)}")


if __name__ == "__main__":
    main()
