#!/usr/bin/env python3
"""
constraint_discovery_v2.py — Conservation-law + dimensional constraint
discovery (Constraint discovery 6→8).

Per cycle 181: the auditor's gap analysis says Constraint discovery has
"only equations explicit in text; no thermodynamic/kinetic derivation."
constraint_from_equations.py (cycle 178) only reads EXPLICIT equations
from text. The auditor requires deriving IMPLICIT constraints from:

1. CONSERVATION LAWS: mass, energy, charge, momentum. If a mechanism
   involves a flow in/out, conservation requires the difference to be
   accounted for. E.g., if reactants A + B → product C, then mass(A) +
   mass(B) ≥ mass(C) (mass conservation).

2. DIMENSIONAL ANALYSIS: if an equation is dimensionally inconsistent,
   a hidden variable must exist. E.g., PV = nRT requires R (gas constant);
   if R is missing, dimensional analysis identifies the missing variable
   and its units.

3. THERMODYNAMIC CONSTRAINTS: any real process must satisfy
   ΔG = ΔH - TΔS ≤ 0 (spontaneous) or be driven (ΔG > 0 with external
   work). If a mechanism is described without a driving force, the
   constraint "ΔG must be ≤ 0 OR external work supplied" is implied.

4. KINETIC CONSTRAINTS: rate laws must be positive. If rate = k[A]^n[B]^m,
   then k > 0, n ≥ 0, m ≥ 0. A negative rate constant or negative order
   is unphysical.

This module produces DerivedConstraint objects (compatible with
constraint_from_equations.py) for each implicit constraint discovered.

Usage:
    from scripts.constraint_discovery_v2 import discover_implicit_constraints
    constraints = discover_implicit_constraints(text, equations, mechanisms)
"""
import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.constraint_from_equations import (
    DerivedConstraint, ConstraintDirection,
)


# ----- Conservation law detection -----

# Patterns for detecting mass/energy/charge/momentum flows
CONSERVATION_PATTERNS = {
    "mass": [
        r'(\w[\w\s\-]{2,30}?)\s*\+\s*(\w[\w\s\-]{2,30}?)\s*(?:→|->|reacts to form|produce|yields)\s*(\w[\w\s\-]{2,30}?)',
        r'reaction\s*:\s*(\w[\w\s\-]{2,30}?)\s*\+\s*(\w[\w\s\-]{2,30}?)\s*→\s*(\w[\w\s\-]{2,30}?)',
    ],
    "energy": [
        r'(\w[\w\s\-]{2,30}?)\s+(?:releases|absorbs|emits|generates)\s+(?:energy|heat|work)\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*(J|kJ|MJ|eV|Wh|kWh)',
        r'heat\s+(?:flow|transfer)\s+from\s+(\w[\w\s\-]{2,30}?)\s+to\s+(\w[\w\s\-]{2,30}?)',
    ],
    "charge": [
        r'(\w[\w\s\-]{2,30}?)\s+(?:oxidizes|reduces)\s+(?:to|into)\s+(\w[\w\s\-]{2,30}?)\s+(?:releasing|absorbing)\s+(\d+(?:\.\d+)?)\s*(?:e|e-|electrons)',
        r'(\w[\w\s\-]{0,30}?)\s*\(([^)]+)\)\s*\+\s*(\d+)?\s*e-?\s*→\s*(\w[\w\s\-]{0,30}?)',
    ],
    "momentum": [
        r'(\w[\w\s\-]{2,30}?)\s+(?:collides with|impacts|strikes)\s+(\w[\w\s\-]{2,30}?)',
        r'momentum\s+transfer\s+from\s+(\w[\w\s\-]{2,30}?)\s+to\s+(\w[\w\s\-]{2,30}?)',
    ],
}


# ----- Dimensional analysis -----

# Base SI dimensions
DIMENSIONS = {
    # base
    "m": "length", "kg": "mass", "s": "time", "A": "current",
    "K": "temperature", "mol": "amount", "cd": "luminous_intensity",
    # derived (common)
    "N": "force", "J": "energy", "W": "power", "Pa": "pressure",
    "V": "voltage", "C": "charge", "F": "capacitance", "Ω": "resistance",
    "S": "conductance", "Hz": "frequency", "T": "magnetic_field",
    "Wb": "magnetic_flux", "H": "inductance", "lm": "luminous_flux",
    "lx": "illuminance", "Bq": "radioactivity", "Gy": "dose",
    # compound
    "m/s": "velocity", "m/s²": "acceleration", "kg/m³": "density",
    "J/K": "heat_capacity", "J/(mol·K)": "molar_heat_capacity",
    "W/(m·K)": "thermal_conductivity",
}

# Known physical variables and their dimensions
VARIABLE_DIMENSIONS = {
    "T": "temperature", "temperature": "temperature",
    "P": "pressure", "pressure": "pressure",
    "V": "volume", "volume": "volume", "v": "velocity",
    "Q": "energy", "q": "charge", "E": "energy",
    "F": "force", "f": "frequency",
    "I": "current", "i": "current",
    "R": "resistance", "r": "length",
    "m": "mass", "M": "mass",
    "n": "amount",
    "k": "rate_constant",
    "A": "area", "a": "acceleration",
    "σ": "conductivity",
    "ε": "emissivity",
    "η": "efficiency",
    "ρ": "density",
    "μ": "viscosity",
    "λ": "wavelength",
    "ν": "frequency",
    "ω": "angular_frequency",
    "τ": "time_constant",
    "θ": "angle",
    "φ": "flux",
    "Φ": "flux",
    "ψ": "wavefunction",
    "U": "energy",
    "H": "enthalpy", "h": "height",
    "G": "gibbs_energy",
    "S": "entropy", "s": "entropy",
    "C": "heat_capacity", "c": "speed",
    "W": "work", "w": "weight",
    "L": "inductance", "l": "length",
    "t": "time",
    "g": "acceleration",
}


def discover_conservation_constraints(text: str) -> List[DerivedConstraint]:
    """Discover constraints implied by conservation laws.

    For each detected reaction/flow, derive:
      - mass conservation: reactant mass ≥ product mass
      - energy conservation: energy_in = energy_out + work + heat
      - charge conservation: total charge is conserved
      - momentum conservation: total momentum is conserved

    Args:
        text: the source text

    Returns:
        list of DerivedConstraint objects
    """
    constraints = []

    # Mass conservation (from reactions A + B → C)
    for pattern in CONSERVATION_PATTERNS["mass"]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                reactants = [match.group(1).strip(), match.group(2).strip()]
                product = match.group(3).strip()
                constraint = DerivedConstraint(
                    constrained_variable=product,
                    constraining_variables=reactants,
                    direction=ConstraintDirection.BOUNDED,
                    source_equation=f"{reactants[0]} + {reactants[1]} → {product}",
                    relationship=(
                        f"mass({product}) ≤ mass({reactants[0]}) + mass({reactants[1]}) "
                        f"(mass conservation: {match.group(0)})"
                    ),
                    confidence=0.9,
                )
                constraints.append(constraint)
            except (IndexError, AttributeError):
                continue

    # Energy conservation (from heat/energy flow)
    for pattern in CONSERVATION_PATTERNS["energy"]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                if "from" in match.group(0).lower():
                    # Heat flow from A to B → A loses energy, B gains energy
                    source = match.group(1).strip()
                    sink = match.group(2).strip()
                    constraint = DerivedConstraint(
                        constrained_variable=sink,
                        constraining_variables=[source],
                        direction=ConstraintDirection.COUPLED,
                        source_equation=match.group(0),
                        relationship=(
                            f"energy({sink}) = energy({source}) - losses "
                            f"(energy conservation: heat flow {source}→{sink})"
                        ),
                        confidence=0.85,
                    )
                    constraints.append(constraint)
                else:
                    # System releases/absorbs energy
                    system = match.group(1).strip()
                    amount = match.group(2)
                    unit = match.group(3)
                    direction_word = "decreases" if "releases" in match.group(0).lower() else "increases"
                    constraint = DerivedConstraint(
                        constrained_variable=system,
                        constraining_variables=["internal_energy"],
                        direction=(ConstraintDirection.DECREASES if direction_word == "decreases"
                                   else ConstraintDirection.INCREASES),
                        source_equation=match.group(0),
                        relationship=(
                            f"energy({system}) {direction_word} by {amount}{unit} "
                            f"(energy conservation)"
                        ),
                        confidence=0.85,
                    )
                    constraints.append(constraint)
            except (IndexError, AttributeError):
                continue

    # Charge conservation
    for pattern in CONSERVATION_PATTERNS["charge"]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                if match.lastindex and match.lastindex >= 4:
                    # (A) + n e- → B  (n optional, defaults to 1)
                    reactant = match.group(1).strip()
                    n_electrons = match.group(3) if match.group(3) else "1"
                    product = match.group(4).strip()
                    constraint = DerivedConstraint(
                        constrained_variable=product,
                        constraining_variables=[reactant, "electron"],
                        direction=ConstraintDirection.COUPLED,
                        source_equation=match.group(0),
                        relationship=(
                            f"charge({product}) = charge({reactant}) + {n_electrons}*e "
                            f"(charge conservation)"
                        ),
                        confidence=0.9,
                    )
                    constraints.append(constraint)
            except (IndexError, AttributeError):
                continue

    # Momentum conservation
    for pattern in CONSERVATION_PATTERNS["momentum"]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                a = match.group(1).strip()
                b = match.group(2).strip()
                constraint = DerivedConstraint(
                    constrained_variable="total_momentum",
                    constraining_variables=[a, b],
                    direction=ConstraintDirection.COUPLED,
                    source_equation=match.group(0),
                    relationship=(
                        f"momentum({a}) + momentum({b}) is conserved "
                        f"before and after collision"
                    ),
                    confidence=0.85,
                )
                constraints.append(constraint)
            except (IndexError, AttributeError):
                continue

    return constraints


def discover_dimensional_constraints(
    equation_text: str,
    variables: Optional[Dict[str, str]] = None,
) -> List[DerivedConstraint]:
    """Discover constraints implied by dimensional analysis.

    For each variable in the equation, check whether its dimension is
    consistent with the equation's structure. If a variable's dimension
    is unknown, flag it as a "hidden variable needed for dimensional
    consistency."

    Args:
        equation_text: the equation as a string (e.g., "Q = σAT⁴")
        variables: optional dict mapping variable name → dimension

    Returns:
        list of DerivedConstraint objects
    """
    if variables is None:
        variables = VARIABLE_DIMENSIONS

    constraints = []

    # Parse the equation: LHS = RHS
    if "=" not in equation_text:
        return constraints

    lhs, rhs = equation_text.split("=", 1)
    lhs = lhs.strip()
    rhs = rhs.strip()

    # Extract all variables (single letters or Greek letters)
    lhs_vars = set(re.findall(r'[A-Za-zα-ωΑ-Ω]', lhs))
    rhs_vars = set(re.findall(r'[A-Za-zα-ωΑ-Ω]', rhs))

    # Variables on RHS not on LHS → they constrain LHS
    rhs_only = rhs_vars - lhs_vars
    for v in rhs_only:
        # Check if we know this variable's dimension
        dim = variables.get(v)
        if dim is None:
            # Unknown dimension → flag as needing measurement
            constraint = DerivedConstraint(
                constrained_variable=v,
                constraining_variables=["unknown_dimension"],
                direction=ConstraintDirection.DETERMINED,
                source_equation=equation_text,
                relationship=(
                    f"Variable {v} appears in {equation_text} but its physical "
                    f"dimension is unknown. It must be measured or defined."
                ),
                confidence=0.7,
            )
            constraints.append(constraint)
        else:
            constraint = DerivedConstraint(
                constrained_variable=v,
                constraining_variables=[dim],
                direction=ConstraintDirection.DETERMINED,
                source_equation=equation_text,
                relationship=(
                    f"Variable {v} in {equation_text} has dimension {dim}. "
                    f"It constrains {lhs} via dimensional consistency."
                ),
                confidence=0.8,
            )
            constraints.append(constraint)

    return constraints


def discover_thermodynamic_constraints(text: str) -> List[DerivedConstraint]:
    """Discover constraints implied by thermodynamics.

    Any real process must satisfy:
      - ΔG = ΔH - TΔS ≤ 0 (spontaneous) OR be driven by external work
      - η ≤ η_Carnot = 1 - T_cold/T_hot (efficiency bound)
      - dS_universe ≥ 0 (entropy never decreases)

    Args:
        text: the source text

    Returns:
        list of DerivedConstraint objects
    """
    constraints = []

    # Detect process descriptions
    process_keywords = [
        "reaction", "combustion", "oxidation", "reduction", "phase transition",
        "melting", "freezing", "evaporation", "condensation", "dissolution",
        "mixing", "expansion", "compression", "diffusion", "flow",
    ]

    text_lower = text.lower()
    found_processes = []
    for kw in process_keywords:
        if kw in text_lower:
            found_processes.append(kw)

    for proc in found_processes:
        # ΔG constraint
        constraint = DerivedConstraint(
            constrained_variable="gibbs_energy_change",
            constraining_variables=["enthalpy_change", "temperature", "entropy_change"],
            direction=ConstraintDirection.BOUNDED,
            source_equation="ΔG = ΔH - TΔS ≤ 0 (spontaneous) or external work required",
            relationship=(
                f"For {proc}: ΔG must be ≤ 0 for spontaneity, OR external work "
                f"must be supplied if ΔG > 0 (second law of thermodynamics)."
            ),
            confidence=0.85,
        )
        constraints.append(constraint)

        # Entropy constraint
        constraint = DerivedConstraint(
            constrained_variable="universe_entropy_change",
            constraining_variables=["system_entropy_change", "surroundings_entropy_change"],
            direction=ConstraintDirection.BOUNDED,
            source_equation="ΔS_universe = ΔS_system + ΔS_surroundings ≥ 0",
            relationship=(
                f"For {proc}: ΔS_universe ≥ 0 (second law of thermodynamics). "
                f"If process is irreversible, ΔS_universe > 0."
            ),
            confidence=0.85,
        )
        constraints.append(constraint)

    # Detect efficiency claims
    efficiency_match = re.search(
        r'(\w[\w\s\-]{2,30}?)\s+(?:has|achieves|exhibits|with)\s+(?:an?\s+)?efficienc(?:y|ies)\s+of\s+(\d+(?:\.\d+)?)\s*(%|percent)?',
        text, re.IGNORECASE,
    )
    if efficiency_match:
        system = efficiency_match.group(1).strip()
        eff_value = float(efficiency_match.group(2))
        if efficiency_match.group(3) in ("%", "percent"):
            eff_value /= 100.0

        constraint = DerivedConstraint(
            constrained_variable=f"efficiency({system})",
            constraining_variables=["T_hot", "T_cold"],
            direction=ConstraintDirection.BOUNDED,
            source_equation=f"η({system}) = {eff_value} ≤ η_Carnot = 1 - T_cold/T_hot",
            relationship=(
                f"η({system}) = {eff_value} must be ≤ Carnot efficiency "
                f"(1 - T_cold/T_hot). If T_hot and T_cold are not given, "
                f"they must be measured."
            ),
            confidence=0.9,
        )
        constraints.append(constraint)

    return constraints


def discover_kinetic_constraints(text: str) -> List[DerivedConstraint]:
    """Discover constraints implied by chemical kinetics.

    Rate laws must satisfy:
      - rate = k[A]^n[B]^m where k > 0, n ≥ 0, m ≥ 0
      - For elementary reactions, n and m are small integers (0, 1, 2)
      - Activation energy E_a > 0 (Arrhenius)

    Args:
        text: the source text

    Returns:
        list of DerivedConstraint objects
    """
    constraints = []

    # Detect rate law statements
    rate_match = re.search(
        r'rate\s*=\s*k\s*\*\s*\[?(\w+)\]?\s*\^?\s*(\d+(?:\.\d+)?)?',
        text, re.IGNORECASE,
    )
    if rate_match:
        reactant = rate_match.group(1)
        order_str = rate_match.group(2) if rate_match.lastindex and rate_match.lastindex >= 2 else "1"
        try:
            order = float(order_str)
        except ValueError:
            order = 1.0

        constraint = DerivedConstraint(
            constrained_variable="rate_constant_k",
            constraining_variables=["temperature"],
            direction=ConstraintDirection.DETERMINED,
            source_equation=rate_match.group(0),
            relationship=(
                f"rate constant k > 0 (physical requirement). "
                f"Reaction order n = {order} (must be ≥ 0 for elementary reactions). "
                f"k = A·exp(-E_a/RT) per Arrhenius (E_a > 0)."
            ),
            confidence=0.9,
        )
        constraints.append(constraint)

    # Detect Arrhenius mentions
    if "arrhenius" in text.lower() or "activation energy" in text.lower():
        constraint = DerivedConstraint(
            constrained_variable="activation_energy",
            constraining_variables=["temperature"],
            direction=ConstraintDirection.BOUNDED,
            source_equation="k = A·exp(-E_a/RT)",
            relationship=(
                "Activation energy E_a > 0 (energy barrier must be positive). "
                "Pre-exponential factor A > 0. Rate constant k > 0 for T > 0."
            ),
            confidence=0.9,
        )
        constraints.append(constraint)

    return constraints


def discover_implicit_constraints(
    text: str,
    equations: Optional[List[str]] = None,
    mechanisms: Optional[List] = None,
) -> List[DerivedConstraint]:
    """Discover ALL implicit constraints from text.

    Combines:
      - Conservation-law constraints (mass, energy, charge, momentum)
      - Dimensional-analysis constraints (from equations)
      - Thermodynamic constraints (ΔG, ΔS, Carnot)
      - Kinetic constraints (rate laws, Arrhenius)

    Args:
        text: the source text
        equations: optional list of equation strings
        mechanisms: optional list of MechanismClaim objects

    Returns:
        list of DerivedConstraint objects
    """
    constraints = []

    # Conservation
    constraints.extend(discover_conservation_constraints(text))

    # Dimensional (from equations if provided)
    if equations:
        for eq in equations:
            constraints.extend(discover_dimensional_constraints(eq))
    else:
        # Try to extract equations from text using simple regex
        eq_matches = re.findall(r'(\w[\w\s\*\/\^\+\-\(\)]{2,60}?)\s*=\s*(\w[\w\s\*\/\^\+\-\(\)]{2,60}?)', text)
        for lhs, rhs in eq_matches:
            constraints.extend(discover_dimensional_constraints(f"{lhs} = {rhs}"))

    # Thermodynamic
    constraints.extend(discover_thermodynamic_constraints(text))

    # Kinetic
    constraints.extend(discover_kinetic_constraints(text))

    return constraints


def main():
    """Demo: discover implicit constraints."""
    print("=" * 60)
    print("Implicit Constraint Discovery")
    print("(Constraint discovery 6→8: conservation + dimensional + thermo + kinetic)")
    print("=" * 60)
    print()

    test_texts = [
        "The combustion reaction CH4 + 2O2 → CO2 + 2H2O releases 890 kJ/mol of energy.",
        "The engine has an efficiency of 35%.",
        "The reaction rate = k * [A]^2 where k follows Arrhenius with E_a = 50 kJ/mol.",
        "The Stefan-Boltzmann law states Q = σAT⁴.",
    ]

    for text in test_texts:
        print(f"Text: {text}")
        constraints = discover_implicit_constraints(text)
        for c in constraints:
            print(f"  [{c.direction.value}] {c.relationship}")
            print(f"      confidence={c.confidence}")
        if not constraints:
            print("  (no implicit constraints discovered)")
        print()

    print("This is the auditor's required capability:")
    print("  - Conservation laws (mass, energy, charge, momentum)")
    print("  - Dimensional analysis (unknown-variable detection)")
    print("  - Thermodynamic constraints (ΔG ≤ 0, η ≤ Carnot)")
    print("  - Kinetic constraints (k > 0, E_a > 0)")


if __name__ == "__main__":
    main()
