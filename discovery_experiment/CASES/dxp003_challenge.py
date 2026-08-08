"""DXP-003 challenge fixture — bat echolocation → maritime radar clutter rejection."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path


@dataclass
class DXP003Challenge:
    challenge_id: str = "DXP-003"
    title: str = "Bat echolocation signal processing → adaptive radar waveform design"
    source_domain: str = "bioacoustics"
    target_domain: str = "radar signal processing"
    source_documents: List[Dict[str, str]] = field(default_factory=list)
    target_problem: str = ""
    target_constraints: List[str] = field(default_factory=list)
    entity_overlap_trap: List[str] = field(default_factory=lambda: [
        "frequency", "range", "resolution", "detection", "clutter"
    ])


def get_dxp003_challenge() -> DXP003Challenge:
    repo = Path(__file__).resolve().parents[2]
    inputs_dir = repo / "discovery_experiment" / "INPUTS"
    doc_a = (inputs_dir / "DXP-003_DOCUMENT_A_BAT_ECHOLOCATION.txt").read_text()
    doc_b = (inputs_dir / "DXP-003_DOCUMENT_B_RADAR.txt").read_text()
    return DXP003Challenge(
        source_documents=[{
            "title": "Bat Echolocation Signal Processing and Adaptive Call Design",
            "text": doc_a,
        }],
        target_problem=(
            "A maritime surveillance radar uses fixed LFM waveforms and suffers from "
            "excessive sea clutter false alarms. An adaptive waveform strategy is needed "
            "that adapts pulse duration to target range, reduces clutter false alarms, "
            "maintains resolution, and addresses range-Doppler coupling — all within "
            "real-time processing constraints on existing FPGA hardware."
        ),
        target_constraints=[
            "Real-time processing within 500 microseconds",
            "Limited FPGA computational resources",
            "Maximum bandwidth 20 MHz",
            "Waveform switching takes 1 ms (two pulse intervals)",
            "Detection probability >= 0.9 for 1 m² targets at 15 km in sea state 4",
            "False alarm rate <= 10⁻⁶ per resolution cell per scan",
        ],
    )
