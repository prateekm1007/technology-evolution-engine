"""DXP-004 challenge fixture — shark skin denticles → pipe drag reduction."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path


@dataclass
class DXP004Challenge:
    challenge_id: str = "DXP-004"
    title: str = "Shark skin denticle morphology → drag reduction surface for water pipes"
    source_domain: str = "ichthyology"
    target_domain: str = "fluid mechanics"
    source_documents: List[Dict[str, str]] = field(default_factory=list)
    target_problem: str = ""
    target_constraints: List[str] = field(default_factory=list)
    entity_overlap_trap: List[str] = field(default_factory=lambda: [
        "surface", "flow", "reduction", "friction"
    ])


def get_dxp004_challenge() -> DXP004Challenge:
    repo = Path(__file__).resolve().parents[2]
    inputs_dir = repo / "discovery_experiment" / "INPUTS"
    doc_a = (inputs_dir / "DXP-004_DOCUMENT_A_SHARK_SKIN.txt").read_text()
    doc_b = (inputs_dir / "DXP-004_DOCUMENT_B_PIPE_DRAG.txt").read_text()
    return DXP004Challenge(
        source_documents=[{
            "title": "Shark Skin Denticle Morphology and Hydrodynamic Function",
            "text": doc_a,
        }],
        target_problem=(
            "A municipal water pipeline (10 km, 0.5 m diameter, Re=500,000) uses "
            "smooth HDPE pipe with friction factor f=0.013. Chemical drag reducers "
            "are prohibited. A passive surface treatment is needed that reduces "
            "pressure drop by at least 5%, is food-grade, survives 20 years, and "
            "can be retrofitted to existing pipes."
        ),
        target_constraints=[
            "No chemical additives",
            "Surface modification only (internal lining or texture)",
            "Food-grade certified (NSF/ANSI 61)",
            "20-year design lifetime",
            "Maximum surface feature height: 200 micrometers",
            "Must remain cleanable (pigging)",
            "Temperature: 5-25°C",
            "Cost: ≤ $100/meter",
            "Retrofit to existing pipes",
        ],
    )
