"""DXP-002 challenge fixture — beetle fog harvesting → dew condenser design."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path


@dataclass
class DXP002Challenge:
    challenge_id: str = "DXP-002"
    title: str = "Namib beetle fog harvesting → dew condenser surface design"
    source_domain: str = "entomology"
    target_domain: str = "materials engineering"
    source_documents: List[Dict[str, str]] = field(default_factory=list)
    target_problem: str = ""
    target_constraints: List[str] = field(default_factory=list)
    entity_overlap_trap: List[str] = field(default_factory=lambda: [
        "water", "surface", "collection", "efficiency"
    ])


def get_dxp002_challenge() -> DXP002Challenge:
    repo = Path(__file__).resolve().parents[2]
    inputs_dir = repo / "discovery_experiment" / "INPUTS"
    doc_a = (inputs_dir / "DXP-002_DOCUMENT_A_BEETLE_FOG.txt").read_text()
    doc_b = (inputs_dir / "DXP-002_DOCUMENT_B_CONDENSER.txt").read_text()
    return DXP002Challenge(
        source_documents=[{
            "title": "Fog-Harvesting Mechanism of the Namib Desert Fog-Basking Beetle",
            "text": doc_a,
        }],
        target_problem=(
            "Arid coastal regions experience regular fog events but almost no rain. "
            "Passive dew condensers using flat foil sheets achieve only 0.1-0.3 L/m²/night. "
            "A better surface design is needed that promotes dropwise condensation, "
            "nucleates droplets efficiently, transports them to drainage rapidly, "
            "is durable, low-cost, and requires no energy input."
        ),
        target_constraints=[
            "Passive system only — no energy input",
            "Surface area ≤ 10 m² per unit",
            "Must survive 5+ years outdoors",
            "Collection rate ≥ 1.0 L/m²/night (3x improvement)",
            "Materials cost ≤ $50/m²",
            "Tolerance ±0.1 mm maximum",
            "Must drain to a single collection point",
            "Food-grade materials (no contamination)",
        ],
    )
