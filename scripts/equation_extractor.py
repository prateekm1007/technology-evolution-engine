#!/usr/bin/env python3
"""
equation_extractor.py — Extract mathematical equations from text (Mechanism 4→6).

Per cycle 175: the auditor wants 'activities/transitions/equations' not just
entities/keywords. I have mechanism_extractor.py (activities) and
property_extractor.py (values). Missing: EQUATION extraction.

This module extracts mathematical equations from scientific text:
1. Explicit equations: "Q = εσAT⁴", "y = mx + b"
2. Proportionalities: "S ∝ n^(-2/3)", "F ~ 1/r²"
3. Inequalities as constraints: "k < 2.5 W/m·K"
4. Variable definitions: "where T is temperature"

Each extracted equation is structured with variables, operators, and
the source text span.

Usage:
    from scripts.equation_extractor import extract_equations
    equations = extract_equations("The Stefan-Boltzmann law: Q = εσAT⁴ where T is temperature.")
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class EquationType(Enum):
    EXPLICIT = "explicit"          # "Q = εσAT⁴"
    PROPORTIONAL = "proportional"  # "S ∝ n^(-2/3)"
    SCALING = "scaling"            # "F ~ 1/r²"
    INEQUALITY = "inequality"      # "k < 2.5"
    DEFINITION = "definition"      # "where T is temperature"


@dataclass
class ExtractedEquation:
    """A mathematical equation extracted from text."""
    type: EquationType
    lhs: str               # left-hand side (e.g., "Q", "S", "F")
    rhs: str               # right-hand side (e.g., "εσAT⁴", "n^(-2/3)")
    variables: List[str]   # variables identified (e.g., ["Q", "ε", "σ", "A", "T"])
    operator: str          # "=", "∝", "~", "<", ">"
    source_text: str       # the text span
    confidence: float = 0.8
    variable_definitions: Dict[str, str] = field(default_factory=dict)

    def is_checkable(self) -> bool:
        return bool(self.lhs and self.rhs and self.operator)

    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "lhs": self.lhs,
            "rhs": self.rhs,
            "variables": self.variables,
            "operator": self.operator,
            "source_text": self.source_text,
            "variable_definitions": self.variable_definitions,
        }


# Patterns for equation extraction
EQUATION_PATTERNS = [
    # Explicit equation: "X = Y" (with math symbols)
    (re.compile(r'([A-Za-z][\w]*)\s*=\s*([^\s,;.]{2,50})', re.MULTILINE),
     EquationType.EXPLICIT, "="),
    # Proportionality: "X ∝ Y" or "X is proportional to Y"
    (re.compile(r'([A-Za-z][\w]*)\s*(?:∝|~|∝|is\s+proportional\s+to)\s*([^\s,;.]{2,50})', re.IGNORECASE),
     EquationType.PROPORTIONAL, "∝"),
    # Scaling: "X scales as Y" or "X ~ Y"
    (re.compile(r'([A-Za-z][\w]*)\s*(?:scales?\s+(?:as|with)|~)\s*([^\s,;.]{2,50})', re.IGNORECASE),
     EquationType.SCALING, "~"),
    # Definition: "where X is Y"
    (re.compile(r'where\s+([A-Za-z][\w]*)\s+is\s+([a-z][\w\s]{2,40})', re.IGNORECASE),
     EquationType.DEFINITION, "is"),
]

# Variable extraction from equation strings
VARIABLE_PATTERN = re.compile(r'[A-Za-z][\w]*')


def _extract_variables(equation_str: str) -> List[str]:
    """Extract variable names from an equation string."""
    # Remove numbers and operators, keep letters
    vars_found = VARIABLE_PATTERN.findall(equation_str)
    # Filter out common non-variables
    non_vars = {"the", "is", "are", "where", "and", "or", "of", "in", "to", "for",
                "with", "by", "as", "at", "on", "an", "a", "be", "from", "that"}
    return [v for v in vars_found if v.lower() not in non_vars and len(v) > 1]


def extract_equations(text: str) -> List[ExtractedEquation]:
    """Extract mathematical equations from scientific text.

    Finds explicit equations, proportionalities, scaling laws, and
    variable definitions. Each is structured with variables, operators,
    and source text.
    """
    equations = []
    seen_spans = set()

    for pattern, eq_type, operator in EQUATION_PATTERNS:
        for match in pattern.finditer(text):
            start, end = match.span()
            # Skip overlapping matches
            if any(s <= start < e or s < end <= e for s, e in seen_spans):
                continue
            seen_spans.add((start, end))

            lhs = match.group(1).strip()
            rhs = match.group(2).strip().rstrip(',;.')
            source = match.group().strip()

            # Skip trivial matches (single letter = single letter)
            if len(lhs) <= 1 and len(rhs) <= 1:
                continue
            # Skip if rhs is just a number (that's a property, not an equation)
            if rhs.replace('.', '').replace('-', '').replace('+', '').isdigit():
                continue
            # Skip if rhs contains too many common words (not a real equation)
            rhs_words = rhs.split()
            common_count = sum(1 for w in rhs_words if w.lower() in
                             {"the", "is", "are", "was", "were", "a", "an", "and", "or",
                              "of", "in", "to", "for", "with", "by", "as", "at", "on"})
            if common_count > len(rhs_words) * 0.5:
                continue

            variables = _extract_variables(f"{lhs} {rhs}")

            # Look for variable definitions nearby
            var_defs = {}
            for var in variables[:5]:  # check first 5 variables
                def_pattern = re.compile(rf'where\s+{re.escape(var)}\s+is\s+([a-z][\w\s]{{2,30}})', re.IGNORECASE)
                def_match = def_pattern.search(text[max(0, start-100):end+200])
                if def_match:
                    var_defs[var] = def_match.group(1).strip().rstrip(',;.')

            equations.append(ExtractedEquation(
                type=eq_type,
                lhs=lhs,
                rhs=rhs,
                variables=variables,
                operator=operator,
                source_text=source,
                confidence=0.85 if eq_type == EquationType.EXPLICIT else 0.75,
                variable_definitions=var_defs,
            ))

    return equations


def main():
    """Demo: extract equations from sample text."""
    test_texts = [
        "The Stefan-Boltzmann law states Q = εσAT⁴ where T is temperature and ε is emissivity.",
        "The Seebeck coefficient S is proportional to n^(-2/3) where n is carrier concentration.",
        "The force F scales as 1/r² for gravitational interactions.",
        "Thermal conductivity k < 2.5 W/m·K for this material.",
        "The efficiency η = P_out / P_in where P_out is output power.",
    ]

    print("=" * 60)
    print("Equation Extraction (adds equations to mechanism extraction)")
    print("=" * 60)

    for text in test_texts:
        print(f"\nText: {text}")
        equations = extract_equations(text)
        for eq in equations:
            print(f"  [{eq.type.value}] {eq.lhs} {eq.operator} {eq.rhs}")
            print(f"    variables: {eq.variables}")
            if eq.variable_definitions:
                print(f"    definitions: {eq.variable_definitions}")
            print(f"    source: {eq.source_text!r}")
            print(f"    checkable: {eq.is_checkable()}")


if __name__ == "__main__":
    main()
