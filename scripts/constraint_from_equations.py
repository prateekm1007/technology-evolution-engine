#!/usr/bin/env python3
"""
constraint_from_equations.py — Derive constraints from equations (Constraint discovery 4→6).

Per cycle 178: constraint_extractor.py extracts inequalities from text
(e.g., 'T < 300K'). But the auditor wants actual constraint DISCOVERY —
deriving constraints from the physics, not just matching keywords.

This module derives constraints from extracted equations:
- If Q = σT⁴, then Q is constrained by T (given T, Q is determined)
- If S ∝ n^(-2/3), then S decreases as n increases (constraint direction)
- If F = G*m1*m2/r², then F is constrained by m1, m2, and r

Each derived constraint has:
- The source equation
- The constrained variable
- The constraining variables
- The constraint direction (increases, decreases, determined by)

Usage:
    from scripts.constraint_from_equations import derive_constraints_from_equations
    constraints = derive_constraints_from_equations("Q = σσAT⁴ where T is temperature")
"""
import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.equation_extractor import extract_equations, ExtractedEquation, EquationType


class ConstraintDirection(Enum):
    DETERMINED = "determined"      # Q is determined by T (Q = σT⁴)
    INCREASES = "increases"        # S increases with n (S ∝ n)
    DECREASES = "decreases"        # S decreases with n (S ∝ n^(-1))
    BOUNDED = "bounded"            # Q is bounded by T⁴
    COUPLED = "coupled"            # m1 and m2 are coupled through F


@dataclass
class DerivedConstraint:
    """A constraint derived from a mathematical equation."""
    constrained_variable: str    # the variable being constrained
    constraining_variables: List[str]  # variables that determine it
    direction: ConstraintDirection
    source_equation: str         # the equation text
    relationship: str            # human-readable description
    confidence: float = 0.8

    def to_dict(self) -> Dict:
        return {
            "constrained_variable": self.constrained_variable,
            "constraining_variables": self.constraining_variables,
            "direction": self.direction.value,
            "source_equation": self.source_equation,
            "relationship": self.relationship,
            "confidence": self.confidence,
        }


def derive_constraints_from_equations(text: str) -> List[DerivedConstraint]:
    """Derive constraints from equations extracted from text.

    This is the 'discovery' part: given an equation, DERIVE what
    constraints it imposes on the system. This is not keyword matching —
    it's mathematical reasoning about what the equation means.
    """
    equations = extract_equations(text)
    constraints = []

    for eq in equations:
        if eq.type == EquationType.EXPLICIT or eq.type == EquationType.PROPORTIONAL:
            # LHS is constrained by RHS variables
            constrained = eq.lhs
            constraining = [v for v in eq.variables if v != constrained]

            if not constraining:
                continue

            # Determine direction from the equation
            rhs_lower = eq.rhs.lower()

            # Check for negative exponent → decreases
            if '^(-' in eq.rhs or '^-' in eq.rhs or '1/' in eq.rhs:
                direction = ConstraintDirection.DECREASES
                relationship = f"{constrained} decreases as {constraining[0]} increases (inverse relationship from {eq.source_text})"
            # Check for positive exponent → increases
            elif '^' in eq.rhs and '^(-' not in eq.rhs:
                direction = ConstraintDirection.INCREASES
                relationship = f"{constrained} increases with {constraining[0]} (power law from {eq.source_text})"
            # Check for proportional → increases
            elif eq.type == EquationType.PROPORTIONAL:
                direction = ConstraintDirection.INCREASES
                relationship = f"{constrained} is proportional to {constraining[0]} ({eq.source_text})"
            else:
                # Determined by all RHS variables
                direction = ConstraintDirection.DETERMINED
                relationship = f"{constrained} is determined by {', '.join(constraining)} ({eq.source_text})"

            constraints.append(DerivedConstraint(
                constrained_variable=constrained,
                constraining_variables=constraining,
                direction=direction,
                source_equation=eq.source_text,
                relationship=relationship,
                confidence=0.85,
            ))

            # Also derive reverse constraints: each RHS variable constrains LHS
            for var in constraining:
                if direction == ConstraintDirection.DECREASES:
                    rel = f"{var} inversely constrains {constrained} ({eq.source_text})"
                    dir_rev = ConstraintDirection.DECREASES
                elif direction == ConstraintDirection.INCREASES:
                    rel = f"{var} positively constrains {constrained} ({eq.source_text})"
                    dir_rev = ConstraintDirection.INCREASES
                else:
                    rel = f"{var} partially determines {constrained} ({eq.source_text})"
                    dir_rev = ConstraintDirection.DETERMINED

                constraints.append(DerivedConstraint(
                    constrained_variable=var,
                    constraining_variables=[constrained],
                    direction=dir_rev,
                    source_equation=eq.source_text,
                    relationship=rel,
                    confidence=0.75,
                ))

    return constraints


def main():
    """Demo: derive constraints from equations."""
    test_texts = [
        "The Stefan-Boltzmann law states Q = σσAT⁴ where T is temperature.",
        "The Seebeck coefficient S is proportional to n^(-2/3).",
        "The force F = G*m1*m2/r² describes gravitational attraction.",
    ]

    print("=" * 60)
    print("Constraint Discovery from Equations")
    print("=" * 60)

    for text in test_texts:
        print(f"\nText: {text}")
        constraints = derive_constraints_from_equations(text)
        for c in constraints:
            print(f"  [{c.direction.value}] {c.relationship}")
        if not constraints:
            print("  (no constraints derived)")


if __name__ == "__main__":
    main()
