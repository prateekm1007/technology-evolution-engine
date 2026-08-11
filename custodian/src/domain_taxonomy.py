"""
custodian.src.domain_taxonomy — Canonical domain taxonomy.

Prevents domain label manipulation by mapping variant labels
to canonical forms. The taxonomy is frozen before benchmark
construction.

HARDENING #4: Domain canonicalization.
"""
import re
from typing import Optional


# Frozen domain taxonomy: maps variant labels to canonical forms.
# This taxonomy ONLY normalizes string formatting (case, underscores/hyphens/spaces).
# It does NOT collapse scientifically distinct disciplines.
# "biology", "molecular_biology", "cell_biology", "biochemistry", and "enzymology"
# are DIFFERENT canonical domains — they are related but not identical.
#
# This taxonomy MUST be defined before benchmark construction.
# New domains can only be added by updating this file and re-freezing.
DOMAIN_TAXONOMY = {
    # Fluid mechanics — only string-format variants of the SAME discipline
    "fluid_mechanics": "fluid_mechanics",
    "fluid-mechanics": "fluid_mechanics",
    "fluid mechanics": "fluid_mechanics",
    "fluidmechanics": "fluid_mechanics",
    # fluid_dynamics is a closely related but distinct subfield; keep separate
    "fluid_dynamics": "fluid_dynamics",
    "fluid-dynamics": "fluid_dynamics",
    "fluid dynamics": "fluid_dynamics",
    "fluiddynamics": "fluid_dynamics",
    # hydrodynamics and aerodynamics are distinct subfields
    "hydrodynamics": "hydrodynamics",
    "aerodynamics": "aerodynamics",

    # Enzymology — only string-format variants
    "enzymology": "enzymology",

    # Biochemistry — distinct from enzymology
    "biochemistry": "biochemistry",
    "biochemical": "biochemistry",

    # Molecular biology — distinct from enzymology and biochemistry
    "molecular_biology": "molecular_biology",
    "molecular biology": "molecular_biology",
    "molecularbiology": "molecular_biology",

    # Cell biology — distinct from molecular biology
    "cell_biology": "cell_biology",
    "cell biology": "cell_biology",
    "cellbiology": "cell_biology",

    # Biology (general) — distinct from all subfields above
    "biology": "biology",

    # Optics variants
    "optics": "optics",
    "optical": "optics",
    # photonics and optoelectronics are distinct subfields
    "photonics": "photonics",
    "optoelectronics": "optoelectronics",

    # Materials science variants
    "materials_science": "materials_science",
    "materials-science": "materials_science",
    "materials science": "materials_science",
    "materialsscience": "materials_science",
    # metallurgy and polymer_science are distinct subfields
    "metallurgy": "metallurgy",
    "polymer_science": "polymer_science",
    "polymer science": "polymer_science",

    # Thermodynamics variants
    "thermodynamics": "thermodynamics",
    # heat_transfer is a distinct subfield
    "heat_transfer": "heat_transfer",
    "heat-transfer": "heat_transfer",
    "heat transfer": "heat_transfer",

    # Electromagnetics variants
    "electromagnetics": "electromagnetics",
    "electromagnetic": "electromagnetics",

    # Chemistry variants
    "chemistry": "chemistry",
    # chemical_engineering is distinct from chemistry
    "chemical_engineering": "chemical_engineering",
    "chemical engineering": "chemical_engineering",

    # Mechanical engineering variants
    "mechanical_engineering": "mechanical_engineering",
    "mechanical engineering": "mechanical_engineering",

    # Electrical engineering variants
    "electrical_engineering": "electrical_engineering",
    "electrical engineering": "electrical_engineering",
    # electronics is a distinct subfield
    "electronics": "electronics",
    "electronic": "electronics",

    # Computer science variants
    "computer_science": "computer_science",
    "computer science": "computer_science",
    "computerscience": "computer_science",
}


def canonicalize_domain(domain: str) -> str:
    """Map a domain label to its canonical form.

    - Case-insensitive
    - Handles underscores, hyphens, spaces
    - Returns canonical form from taxonomy
    - If domain is not in taxonomy, returns the lowercased normalized form
      (this will be flagged by the validator as a potential issue)
    """
    if not domain:
        return ""

    # Normalize: lowercase, strip, collapse whitespace
    normalized = re.sub(r'\s+', ' ', domain.lower().strip())

    # Replace underscores and hyphens with underscores for lookup
    lookup_key = normalized.replace('-', '_').replace(' ', '_')

    # Try exact lookup
    if lookup_key in DOMAIN_TAXONOMY:
        return DOMAIN_TAXONOMY[lookup_key]

    # Try with spaces
    if normalized in DOMAIN_TAXONOMY:
        return DOMAIN_TAXONOMY[normalized]

    # Try with hyphens
    hyphen_key = normalized.replace('_', '-').replace(' ', '-')
    if hyphen_key in DOMAIN_TAXONOMY:
        return DOMAIN_TAXONOMY[hyphen_key]

    # Not in taxonomy — return normalized form (will be flagged by validator)
    return lookup_key


def is_known_domain(domain: str) -> bool:
    """Check if a domain is in the frozen taxonomy."""
    canonical = canonicalize_domain(domain)
    return canonical in set(DOMAIN_TAXONOMY.values())
