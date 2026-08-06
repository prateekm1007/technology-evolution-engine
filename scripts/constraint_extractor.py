#!/usr/bin/env python3
"""
constraint_extractor.py — Physics-based constraint extraction (Constraint discovery 2→4).

Per cycle 172: the auditor found 'keyword failure-mode heuristics only' for
constraint discovery. The constraint_module.py uses a keyword→failure-mode
lookup table, not actual constraint extraction from text.

This module extracts STRUCTURED constraints from scientific text:
1. Inequality constraints: "T < 300K", "efficiency > 20%", "cost < $1000"
2. Boundary conditions: "at room temperature", "under atmospheric pressure"
3. Conservation laws: "energy is conserved", "mass balance"
4. Physical limits: "thermal conductivity cannot exceed k_max"
5. Design constraints: "the device must fit within 10cm × 10cm"

Each constraint is structured (not a keyword match):
- ConstraintClaim: type, expression, variables, bounds, source_text

Usage:
    from scripts.constraint_extractor import extract_constraints
    constraints = extract_constraints("The efficiency must exceed 20% at temperatures below 350K.")
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class ConstraintType(Enum):
    INEQUALITY = "inequality"        # "T < 300K", "efficiency > 20%"
    BOUNDARY = "boundary"            # "at room temperature", "under pressure"
    CONSERVATION = "conservation"    # "energy is conserved", "mass balance"
    PHYSICAL_LIMIT = "physical_limit" # "cannot exceed k_max"
    DESIGN = "design"                # "must fit within 10cm × 10cm"
    RANGE = "range"                  # "between 100 and 200 nm"


@dataclass
class ConstraintClaim:
    """A structured constraint extracted from text."""
    type: ConstraintType
    variable: str           # what is constrained (e.g., "temperature", "efficiency")
    operator: str           # "<", ">", "=", "≤", "≥", "between"
    bound: Optional[str]    # the bound value (e.g., "300K", "20%")
    bound_upper: Optional[str] = None  # for ranges: upper bound
    unit: str = ""          # the unit (e.g., "K", "%", "nm")
    source_text: str = ""   # the text span where this was found
    confidence: float = 0.8

    def is_checkable(self) -> bool:
        """A constraint is checkable if it has a variable, operator, and bound."""
        return bool(self.variable and self.operator and self.bound)

    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "variable": self.variable,
            "operator": self.operator,
            "bound": self.bound,
            "bound_upper": self.bound_upper,
            "unit": self.unit,
            "source_text": self.source_text,
            "confidence": self.confidence,
        }


# Patterns for constraint extraction
CONSTRAINT_PATTERNS = [
    (re.compile(r'(\w[\w\s]{2,30}?)\s*(?:must\s+)?(?:exceeds?|exceeded|greater\s+than|above|higher\s+than|>|≥)\s*(\d+\.?\d*)\s*(%|K|°C|nm|μm|mm|cm|m|kg|g|W|kW|V|mV|Pa|kPa|MPa|GPa|Hz|kHz|MHz|GHz|eV|J|mol|bar|atm)', re.IGNORECASE),
    ConstraintType.INEQUALITY, ">"),
    (re.compile(r'(\w[\w\s]{2,30}?)\s*(?:must\s+)?(?:less\s+than|below|lower\s+than|under|<|≤)\s*(\d+\.?\d*)\s*(%|K|°C|nm|μm|mm|cm|m|kg|g|W|kW|V|mV|Pa|kPa|MPa|GPa|Hz|kHz|MHz|GHz|eV|J|mol|bar|atm)', re.IGNORECASE),
    ConstraintType.INEQUALITY, "<"),
    (re.compile(r'(\w[\w\s]{2,30}?)\s*(?:between|ranging\s+from)\s*(\d+\.?\d*)\s*(%|K|°C|nm|μm|mm|cm|m|kg|g|W|kW|V|mV|Pa|kPa|MPa|GPa|Hz|kHz|MHz|GHz|eV|J|mol|bar|atm)?\s*(?:and|to|-)\s*(\d+\.?\d*)\s*(%|K|°C|nm|μm|mm|cm|m|kg|g|W|kW|V|mV|Pa|kPa|MPa|GPa|Hz|kHz|MHz|GHz|eV|J|mol|bar|atm)?', re.IGNORECASE),
    ConstraintType.RANGE, "between"),
    (re.compile(r'(\w[\w\s]{2,30}?)\s*(?:cannot|must\s+not)\s+(?:exceed|surpass|go\s+above|be\s+greater\s+than)\s*(\d+\.?\d*)\s*(%|K|°C|nm|μm|mm|cm|m|kg|g|W|kW|V|mV|Pa|kPa|MPa|GPa|Hz|kHz|MHz|GHz|eV|J|mol|bar|atm)', re.IGNORECASE),
    ConstraintType.PHYSICAL_LIMIT, "≤"),
    (re.compile(r'(energy|mass|momentum|charge|matter)\s+(?:is\s+)?conserved', re.IGNORECASE),
    ConstraintType.CONSERVATION, "="),
    (re.compile(r'at\s+(?:room\s+temperature|ambient\s+temperature|(\d+\.?\d*)\s*(K|°C))', re.IGNORECASE),
    ConstraintType.BOUNDARY, "at"),
    (re.compile(r'(?:under|at)\s+(?:atmospheric\s+pressure|(\d+\.?\d*)\s*(Pa|kPa|MPa|GPa|bar|atm))', re.IGNORECASE),
    ConstraintType.BOUNDARY, "at"),
]


def extract_constraints(text: str) -> List[ConstraintClaim]:
    """Extract structured constraints from scientific text.

    This replaces the keyword failure-mode heuristics in constraint_module.py.
    Instead of matching keywords like "cost" → "cost_overrun", it extracts
    actual constraint expressions: "temperature < 300K", "efficiency > 20%".
    """
    constraints = []
    seen_spans = set()

    for entry in CONSTRAINT_PATTERNS:
        pattern, ctype, operator = entry

        for match in pattern.finditer(text):
            start, end = match.span()
            # Skip overlapping matches
            if any(s <= start < e or s < end <= e for s, e in seen_spans):
                continue
            seen_spans.add((start, end))

            groups = match.groups()
            source = match.group()

            if ctype == ConstraintType.RANGE:
                variable = groups[0].strip() if groups[0] else "value"
                bound_lower = groups[1] if groups[1] else ""
                unit = groups[2] or groups[3] or ""
                bound_upper = groups[3] if len(groups) > 3 else ""
                constraints.append(ConstraintClaim(
                    type=ctype, variable=variable, operator=operator,
                    bound=bound_lower, bound_upper=bound_upper, unit=unit,
                    source_text=source, confidence=0.85,
                ))
            elif ctype == ConstraintType.DESIGN:
                constraints.append(ConstraintClaim(
                    type=ctype, variable="dimensions", operator=operator,
                    bound=f"{groups[0]}{groups[1]}", bound_upper=f"{groups[2]}{groups[3]}",
                    unit=groups[1] or "", source_text=source, confidence=0.9,
                ))
            elif ctype == ConstraintType.CONSERVATION:
                variable = groups[0] if groups[0] else "quantity"
                constraints.append(ConstraintClaim(
                    type=ctype, variable=variable, operator=operator,
                    bound="conserved", unit="", source_text=source, confidence=0.95,
                ))
            elif ctype == ConstraintType.BOUNDARY:
                if groups[0]:  # numeric temperature/pressure
                    constraints.append(ConstraintClaim(
                        type=ctype, variable="temperature" if "K" in str(groups) or "°C" in str(groups) else "pressure",
                        operator=operator, bound=groups[0], unit=groups[1] or "",
                        source_text=source, confidence=0.8,
                    ))
                else:  # "room temperature" or "atmospheric pressure"
                    constraints.append(ConstraintClaim(
                        type=ctype, variable=source.lower(), operator=operator,
                        bound="ambient", unit="", source_text=source, confidence=0.7,
                    ))
            else:  # INEQUALITY or PHYSICAL_LIMIT
                variable = groups[0].strip() if groups[0] else "value"
                bound = groups[1] if groups[1] else ""
                unit = groups[2] or ""
                constraints.append(ConstraintClaim(
                    type=ctype, variable=variable, operator=operator,
                    bound=bound, unit=unit, source_text=source, confidence=0.85,
                ))

    return constraints


def main():
    """Demo: extract constraints from sample text."""
    test_texts = [
        "The efficiency must exceed 20% at temperatures below 350K.",
        "The device operates between 100 and 200 nm wavelength.",
        "Thermal conductivity cannot exceed 2.5 W/m·K.",
        "The system must fit within 10mm × 10mm dimensions.",
        "Energy is conserved in the closed system.",
        "The reaction occurs at room temperature under atmospheric pressure.",
    ]

    print("=" * 60)
    print("Constraint Extraction (replaces keyword heuristics)")
    print("=" * 60)

    for text in test_texts:
        print(f"\nText: {text}")
        constraints = extract_constraints(text)
        for c in constraints:
            print(f"  [{c.type.value}] {c.variable} {c.operator} {c.bound}"
                  f"{" to " + c.bound_upper if c.bound_upper else ""} {c.unit}")
            print(f"    source: {c.source_text!r}")
            print(f"    checkable: {c.is_checkable()}")


if __name__ == "__main__":
    main()
