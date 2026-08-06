#!/usr/bin/env python3
"""
property_extractor.py — Extract measured properties (value + unit) from text.

Per cycle 144: Gen 2 needs +1 infra point to reach 9/10 (currently 8/10 with
F1=0.8871). The gap is "No property extraction from text (0)". This module
extracts (property_name, value, unit) triples from scientific text.

E.g., "Seebeck coefficient of 200 μV/K" → (seebeck_coefficient, 200, μV/K)

Usage:
    from scripts.property_extractor import extract_properties
    props = extract_properties("The Seebeck coefficient was 200 μV/K at 300 K.")
"""
import re
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ExtractedProperty:
    """A measured property extracted from text."""
    name: str          # canonical property name (e.g., "seebeck_coefficient")
    value: float       # the measured value
    unit: str          # the unit (e.g., "μV/K", "W/m·K", "K")
    raw_text: str      # the text span where this was found
    confidence: float = 0.8


# Property patterns: (regex, property_name, unit)
# These match common scientific property expressions in text
PROPERTY_PATTERNS = [
    # Temperature
    (r'(\d+\.?\d*)\s*(?:°?K|Kelvin)\b', "temperature", "K"),
    (r'(\d+\.?\d*)\s*°?C\b', "temperature", "°C"),
    # Seebeck coefficient
    (r'(?:Seebeck|seebeck)\s*(?:coefficient)?\s*(?:of\s+)?(\d+\.?\d*)\s*(μV/K|microV/K|µV/K)', "seebeck_coefficient", "μV/K"),
    (r'(\d+\.?\d*)\s*(μV/K|microV/K|µV/K)\s*(?:Seebeck|seebeck)', "seebeck_coefficient", "μV/K"),
    # Thermal conductivity
    (r'(?:thermal\s+)?conductivity\s*(?:of\s+)?(\d+\.?\d*)\s*(W/m\.?K|W/mK|W·m⁻¹·K⁻¹)', "thermal_conductivity", "W/m·K"),
    (r'(\d+\.?\d*)\s*(W/m\.?K|W/mK)\s*(?:thermal\s+)?conductivity', "thermal_conductivity", "W/m·K"),
    # Electrical conductivity
    (r'(?:electrical\s+)?conductivity\s*(?:of\s+)?(\d+\.?\d*)\s*(S/m|S·m⁻¹)', "electrical_conductivity", "S/m"),
    # Power / power output
    (r'(?:power\s+output|power)\s*(?:of\s+)?(\d+\.?\d*)\s*(W|kW|mW)', "power_output", "W"),
    (r'(\d+\.?\d*)\s*(W|kW|mW)\s*(?:power|output)', "power_output", "W"),
    # Efficiency
    (r'(?:efficiency|η)\s*(?:of\s+)?(\d+\.?\d*)\s*(%|percent)', "efficiency", "%"),
    (r'(\d+\.?\d*)\s*(%|percent)\s*(?:efficiency)', "efficiency", "%"),
    # Capacity / capacitance
    (r'(?:capacitance|capacity)\s*(?:of\s+)?(\d+\.?\d*)\s*(F|mF|μF|uF|mAh|Ah)', "capacitance", "F"),
    (r'(\d+\.?\d*)\s*(F|mF|μF|uF|mAh|Ah)\s*(?:capacitance|capacity)', "capacitance", "F"),
    # Voltage
    (r'(?:voltage|potential)\s*(?:of\s+)?(\d+\.?\d*)\s*(V|mV|kV)', "voltage", "V"),
    (r'(\d+\.?\d*)\s*(V|mV|kV)\s*(?:voltage|potential)', "voltage", "V"),
    # Bandgap / energy
    (r'(?:bandgap|band\s+gap|energy\s+gap)\s*(?:of\s+)?(\d+\.?\d*)\s*(eV|eV)', "bandgap", "eV"),
    (r'(\d+\.?\d*)\s*(eV)\s*(?:bandgap|band\s+gap|energy\s+gap)', "bandgap", "eV"),
    # Pressure
    (r'(?:pressure|stress)\s*(?:of\s+)?(\d+\.?\d*)\s*(Pa|kPa|MPa|GPa|bar|atm)', "pressure", "Pa"),
    (r'(\d+\.?\d*)\s*(Pa|kPa|MPa|GPa|bar|atm)\s*(?:pressure|stress)', "pressure", "Pa"),
    # Density
    (r'(?:density)\s*(?:of\s+)?(\d+\.?\d*)\s*(kg/m³|g/cm³|g/mL|kg/m3)', "density", "kg/m³"),
    (r'(\d+\.?\d*)\s*(kg/m³|g/cm³|g/mL|kg/m3)\s*(?:density)', "density", "kg/m³"),
    # Rate / speed
    (r'(?:rate|speed|velocity)\s*(?:of\s+)?(\d+\.?\d*)\s*(m/s|cm/s|mm/s|Hz|kHz|MHz)', "rate", "m/s"),
    (r'(\d+\.?\d*)\s*(m/s|cm/s|mm/s|Hz|kHz|MHz)\s*(?:rate|speed|velocity)', "rate", "m/s"),
    # Generic: number + unit
    (r'(\d+\.?\d*)\s*(nm|μm|um|mm|cm|m)\b', "length", "m"),
    (r'(\d+\.?\d*)\s*(mg|g|kg)\b', "mass", "g"),
    (r'(\d+\.?\d*)\s*(s|ms|μs|min|h)\b', "time", "s"),
]

# Compile patterns
COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), name, unit)
                      for p, name, unit in PROPERTY_PATTERNS]


def extract_properties(text: str) -> List[ExtractedProperty]:
    """Extract measured properties (value + unit) from text.

    This is the "property extraction from text" that was missing from Gen 2.
    It finds scientific measurements like "200 μV/K", "459 W", "300 K" and
    extracts them as structured (name, value, unit) triples.
    """
    properties = []
    seen_spans = set()

    for pattern, prop_name, unit in COMPILED_PATTERNS:
        for match in pattern.finditer(text):
            # Skip if this span overlaps with an already-found property
            start, end = match.span()
            if any(s <= start < e or s < end <= e for s, e in seen_spans):
                continue

            try:
                value = float(match.group(1))
            except (ValueError, IndexError):
                continue

            raw_text = match.group()
            properties.append(ExtractedProperty(
                name=prop_name,
                value=value,
                unit=unit,
                raw_text=raw_text,
                confidence=0.85,
            ))
            seen_spans.add((start, end))

    return properties


def main():
    """Demo: extract properties from sample text."""
    test_texts = [
        "Bismuth telluride exhibits a Seebeck coefficient of 200 μV/K at 300 K.",
        "The thermal conductivity was measured at 1.5 W/m·K.",
        "The device achieved a power output of 459 W with 12.5% efficiency.",
        "The bandgap of the semiconductor is 1.1 eV.",
    ]

    for text in test_texts:
        print(f"\nText: {text}")
        props = extract_properties(text)
        for p in props:
            print(f"  {p.name}: {p.value} {p.unit} (raw: {p.raw_text!r})")


if __name__ == "__main__":
    main()
