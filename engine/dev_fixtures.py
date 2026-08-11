"""
dev_fixtures.py — DEV_ONLY scientific challenges (Phase 15).

Rule 0: These fixtures are DEV_ONLY. They are NOT derived from Gate 2 cases.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class DevChallenge:
    challenge_id: str
    title: str
    source_domain: str
    target_domain: str
    source_documents: List[Dict[str, str]]
    target_problem: str
    target_constraints: List[str]
    expected_transfer_summary: str  # DEV-only eval aid; engine NEVER sees this
    entity_overlap_trap: List[str] = field(default_factory=list)
    plausible_competing_mechanisms: List[str] = field(default_factory=list)


# Challenge 4 — DELIBERATELY DIFFICULT (per reviewer's directive F):
# high domain distance, no shared terminology, multiple plausible mechanisms,
# non-trivial transfer mapping. This is the challenge the full real-LLM loop
# will run on.
CHALLENGE_4 = DevChallenge(
    challenge_id="DEV-CH-004",
    title="Slime mold foraging network optimization → urban traffic signal timing",
    source_domain="myxomycete biology / emergent computation",
    target_domain="urban transportation engineering",
    source_documents=[
        {
            "title": "Physarum polycephalum Network Adaptation: Adaptive Biologically-Inspired Transport Networks",
            "text": (
                "The slime mold Physarum polycephalum is a single-celled multinucleate "
                "organism that forages for food by growing a tubular cytoplasmic network "
                "connecting discovered food sources. The network adapts its morphology "
                "over time according to a self-organizing physiological feedback. "
                "\n\n"
                "The core adaptation mechanism is protoplasmic streaming driven by "
                "rhythmic contraction of the actin-myosin cytoskeleton along the tube "
                "walls. The contraction amplitude varies along the tube length, creating "
                "pressure differentials that drive shuttle-streaming of cytoplasm. "
                "Through-flow rate scales approximately with the fourth power of tube "
                "radius (Hagen-Poiseuille), so small radius differences produce large "
                "flow differences. "
                "\n\n"
                "When two paths connect the same two food sources, the organism "
                "preferentially routes flow through the thicker, shorter tube. The "
                "feedback is: high flow → tube thickens (actin polymerization, wall "
                "deposition); low flow → tube thins and eventually disappears (actin "
                "depolymerization, wall retraction). This is a positive feedback loop: "
                "the path that carries more flow becomes even more capable of carrying "
                "flow, while the path that carries less atrophies. "
                "\n\n"
                "The mechanism fails when: (1) flow is so low that the positive feedback "
                "cannot overcome baseline tube maintenance (the tube collapses everywhere); "
                "(2) flow is so high that the tube cannot thicken fast enough (rupture); "
                "(3) the network has cycles that allow flow to oscillate rather than "
                "converge (the feedback never stabilizes). The boundary condition is "
                "that the flow-to-radius feedback gain must be in a regime where "
                "perturbations damp out rather than amplify. "
                "\n\n"
                "The resulting networks exhibit shortest-path-like behavior without any "
                "global planner, and they self-repair when damaged. The organism "
                "effectively solves a distributed optimization problem using only local "
                "feedback rules."
            ),
        },
    ],
    target_problem=(
        "A mid-sized city (population 800,000) has a traffic signal network with 247 "
        "signalized intersections. The current signal timing plan is optimized centrally "
        "every 6 months using a macroscopic traffic model, but it cannot adapt to "
        "real-time conditions: incidents, weather, special events, and construction. "
        "Re-optimizing centrally every minute is computationally infeasible and would "
        "require expensive predictive models. The city wants a distributed, adaptive "
        "signal timing approach that uses only local traffic flow measurements "
        "(vehicle count and queue length at each intersection) to adjust green-split "
        "and offset in real time, without a central optimizer."
    ),
    target_constraints=[
        "No central optimizer — decisions must be made at each intersection using only local measurements",
        "Each intersection can communicate only with its immediate neighbors (adjacent intersections)",
        "Must converge to a stable timing plan within 15 minutes of a perturbation",
        "Must not oscillate indefinitely under cyclic topology (the downtown grid has many cycles)",
        "Must handle 247 intersections with heterogeneous degree (2-way to 6-way)",
        "Existing detection infrastructure: inductive loop detectors giving vehicle count + queue length per approach",
    ],
    expected_transfer_summary=(
        "A good transfer would map the slime mold's flow-to-radius feedback to a "
        "traffic flow-to-green-time feedback. The mechanism to transfer is: high flow "
        "→ increase capacity (longer green) → even more flow; low flow → decrease "
        "capacity → flow reroutes. The translation replaces tube radius with green "
        "split ratio, and protoplasmic flow with vehicle flow. The critical boundary "
        "condition is the feedback gain: too low and the network cannot adapt; too "
        "high and it oscillates. Competing mechanisms would include: (a) reinforcement "
        "learning at each intersection (model-based, requires training data); (b) "
        "model-predictive control with neighbor communication (computationally heavier); "
        "(c) fixed-time plans with library switching (not truly adaptive)."
    ),
    entity_overlap_trap=["network", "flow", "adaptation", "optimization", "feedback"],
    plausible_competing_mechanisms=[
        "Slime-mold flow-to-capacity positive feedback (the transfer)",
        "Reinforcement learning with neighbor communication",
        "Model-predictive control with distributed optimization",
        "Fixed-plan library with mode switching (SCATS-style)",
        "Back-pressure routing from queueing theory",
    ],
)


# Earlier challenges preserved for completeness (used in prior dev runs)
CHALLENGE_1 = DevChallenge(
    challenge_id="DEV-CH-001",
    title="Lotus-effect self-cleaning → solar panel efficiency retention",
    source_domain="botany / surface science",
    target_domain="photovoltaic engineering",
    source_documents=[{
        "title": "The Lotus Effect: Superhydrophobicity and Self-Cleaning",
        "text": (
            "The leaves of the lotus plant (Nelumbo nucifera) exhibit a remarkable "
            "self-cleaning property known as the Lotus Effect. The leaf surface is "
            "covered with microscopic papillae (epicuticular wax bumps) approximately "
            "10-20 micrometers in height, which themselves have a nano-scale wax "
            "crystal coating. This hierarchical micro/nano structure traps air "
            "pockets between water droplets and the leaf surface, dramatically "
            "reducing the contact area. The result is a superhydrophobic surface "
            "with a water contact angle greater than 150 degrees. "
            "\n\n"
            "When a water droplet lands on the lotus leaf, it remains nearly "
            "spherical and rolls off at a very small tilt angle (less than 5 "
            "degrees). As the droplet rolls, it picks up dust, pollen, and other "
            "particulate contaminants through capillary forces — the water "
            "envelopes the particles and carries them away. The critical mechanism "
            "is that the hierarchical roughness minimizes the adhesion between "
            "the contaminant and the surface, while the rolling droplet provides "
            "the transport force. The surface thus remains clean without any "
            "chemical cleaning agent or active energy input beyond gravity and "
            "the kinetic energy of falling water. "
            "\n\n"
            "The Lotus Effect fails when the hierarchical structure is damaged "
            "or when surfactants are present (which lower the surface tension and "
            "allow water to wet the surface). It also degrades when contaminants "
            "are smaller than the papillae spacing, because they can lodge within "
            "the structure and are not picked up by the rolling droplet. The "
            "boundary conditions are therefore: hierarchical micro/nano roughness, "
            "low-surface-tension contaminant-free water, and particle sizes "
            "larger than the nano-scale structure."
        ),
    }],
    target_problem=(
        "Solar panels installed in arid and semi-arid regions lose 15-30% of their "
        "power output within 6 months due to dust accumulation on the glass cover. "
        "Manual cleaning with water and brushes is labor-intensive, uses scarce water, "
        "and risks scratching the anti-reflective coating. Chemical coatings degrade "
        "under UV exposure. We need a passive, low-maintenance way to keep the panel "
        "surface clean so that transmittance stays high."
    ),
    target_constraints=[
        "No external water supply can be assumed (arid region)",
        "No moving parts or active power consumption",
        "Must survive UV exposure for 10+ years",
        "Must not reduce optical transmittance in the visible spectrum",
        "Dust particle sizes range from 1 to 100 micrometers",
    ],
    expected_transfer_summary="(see prior runs — this is the negative-science asset)",
    entity_overlap_trap=["surface", "water", "clean"],
    plausible_competing_mechanisms=[
        "Hierarchical roughness superhydrophobicity (lotus transfer)",
        "Electrostatic dust repulsion",
        "Photocatalytic TiO2 self-cleaning",
        "Aerodynamic shaping to prevent dust settling",
    ],
)


ALL_DEV_CHALLENGES: List[DevChallenge] = [CHALLENGE_1, CHALLENGE_4]


def get_challenge(challenge_id: str) -> DevChallenge:
    for c in ALL_DEV_CHALLENGES:
        if c.challenge_id == challenge_id:
            return c
    raise KeyError(f"Unknown DEV challenge: {challenge_id}")


__all__ = ["DevChallenge", "ALL_DEV_CHALLENGES", "get_challenge",
           "CHALLENGE_1", "CHALLENGE_4"]
