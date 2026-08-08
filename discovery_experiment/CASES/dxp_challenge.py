"""
DXP-001 Discovery Experiment — frozen challenge fixture.

This fixture is created BEFORE the engine executes. The input documents
are frozen in INPUTS/ with a SHA-256 manifest. The engine will run against
these inputs using the checkpointed discovery loop.

The challenge: stomatal conductance regulation (plant physiology) →
adaptive fresh-air ventilation control (building HVAC).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class DXPChallenge:
    """The DXP-001 discovery challenge."""
    challenge_id: str = "DXP-001"
    title: str = "Stomatal conductance regulation → adaptive HVAC ventilation control"
    source_domain: str = "plant physiology"
    target_domain: str = "building HVAC control"
    source_documents: List[Dict[str, str]] = field(default_factory=list)
    target_problem: str = ""
    target_constraints: List[str] = field(default_factory=list)
    entity_overlap_trap: List[str] = field(default_factory=lambda: [
        "control", "feedback", "response", "system", "regulation"
    ])


def get_dxp_challenge() -> DXPChallenge:
    """Load the DXP-001 challenge from the frozen input documents."""
    from pathlib import Path
    repo = Path(__file__).resolve().parents[2]
    inputs_dir = repo / "discovery_experiment" / "INPUTS"

    doc_a = (inputs_dir / "DOCUMENT_A_STOMATAL_REGULATION.txt").read_text()
    doc_b = (inputs_dir / "DOCUMENT_B_HVAC_PROBLEM.txt").read_text()

    return DXPChallenge(
        source_documents=[{
            "title": "Stomatal Conductance Regulation in Vascular Plants",
            "text": doc_a,
        }],
        target_problem=(
            "A mid-size office building (200 occupants, 5 floors, mixed climate) "
            "uses a VAV HVAC system with outdoor air dampers. The current ventilation "
            "control uses fixed schedules and simple CO2 threshold logic, causing slow "
            "response, overshoot, oscillation, energy waste, and comfort complaints. "
            "A better control strategy is needed that responds faster, avoids overshoot, "
            "can anticipate changes, minimizes energy, works with existing sensors, and "
            "is implementable on the existing BAS within one month."
        ),
        target_constraints=[
            "Damper actuation rate: max 10% per minute",
            "CO2 sensor transport delay: 2-5 minutes",
            "ASHRAE 62.1: CO2 must not exceed 1000 ppm during occupied hours",
            "Energy target: reduce ventilation energy by at least 15%",
            "No new sensors can be installed",
            "Control logic runs at 1-minute intervals",
            "No cloud connectivity or ML infrastructure",
            "Tunable by a building engineer without control theory expertise",
        ],
    )
