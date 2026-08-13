"""
Domain Map — 30 domains across 6 technological universes (Issue #5).

Per CEO directive: optimize for the maximum number of INDEPENDENT evidence
systems that can constrain one another — NOT the maximum number of domains.

Universes:
  MATTER      — materials, chemistry, metallurgy, polymers, textiles, packaging, nanotechnology
  ENERGY      — batteries, electrochemistry, nuclear, renewables, power electronics, combustion
  LIFE        — biotechnology, pharmaceuticals, medicine, medical devices, agriculture, food
  MACHINE     — mechanical, robotics, manufacturing, aerospace, transportation, civil
  INFORMATION — computing, AI, semiconductors, electronics, photonics, telecom, quantum
  PLANET      — climate, environmental, water, ocean, geoscience, atmospheric

The killer graph is the cross-product of these 6 universes.
"""
from __future__ import annotations
from dataclasses import dataclass


UNIVERSES = ["matter", "energy", "life", "machine", "information", "planet"]


@dataclass(frozen=True)
class Domain:
    domain_id: str
    name: str
    universe: str
    description: str
    cross_universe_bridges: tuple[str, ...]  # other universes it commonly bridges to


DOMAINS: list[Domain] = [
    # --- MATTER (7 domains) ---
    Domain("materials", "Materials Science", "matter",
           "Materials synthesis, characterization, properties",
           ("energy", "machine", "information")),
    Domain("chemistry", "Chemistry", "matter",
           "Synthesis, reactions, catalysis, computational chemistry",
           ("life", "energy", "planet")),
    Domain("metallurgy", "Metallurgy", "matter",
           "Ore processing, alloy design, metal forming",
           ("machine", "energy")),
    Domain("polymers", "Polymers", "matter",
           "Polymer synthesis, characterization, processing",
           ("life", "machine", "information")),
    Domain("textiles", "Textiles & Fibers", "matter",
           "Fiber chemistry, biomaterials, smart textiles, wearables",
           ("life", "information", "machine")),
    Domain("packaging", "Packaging", "matter",
           "Barrier materials, food science, active packaging",
           ("life", "energy", "machine")),
    Domain("nanotechnology", "Nanotechnology", "matter",
           "Nanomaterials, quantum dots, nanostructures",
           ("information", "energy", "life")),

    # --- ENERGY (6 domains) ---
    Domain("batteries", "Battery & Electrochemical Systems", "energy",
           "Batteries, supercapacitors, electrochemistry",
           ("matter", "machine", "planet")),
    Domain("nuclear", "Nuclear Science & Engineering", "energy",
           "Reactor engineering, materials, radiation, isotopes",
           ("matter", "machine", "life")),
    Domain("renewables", "Renewables", "energy",
           "Solar, wind, geothermal, hydro",
           ("matter", "planet", "information")),
    Domain("power_electronics", "Power Electronics", "energy",
           "Converters, inverters, wide-bandgap devices",
           ("information", "machine")),
    Domain("combustion", "Combustion & Fire Science", "energy",
           "Combustion chemistry, fire safety, propulsion",
           ("matter", "machine", "planet")),
    Domain("hydrogen", "Hydrogen & Fuel Cells", "energy",
           "Electrolysis, storage, fuel cells",
           ("matter", "machine", "planet")),

    # --- LIFE (6 domains) ---
    Domain("biotechnology", "Biotechnology", "life",
           "Genetic engineering, fermentation, biosynthesis",
           ("matter", "information")),
    Domain("pharmaceuticals", "Pharmaceuticals", "life",
           "Drug discovery, formulation, delivery",
           ("matter", "information")),
    Domain("medicine", "Medicine", "life",
           "Clinical medicine, diagnostics, therapeutics",
           ("information", "machine")),
    Domain("medical_devices", "Medical Devices", "life",
           "Implants, instruments, diagnostics devices",
           ("matter", "machine", "information")),
    Domain("agriculture", "Agriculture & AgTech", "life",
           "Crops, livestock, precision agriculture",
           ("planet", "information", "machine")),
    Domain("food_science", "Food Science", "life",
           "Food chemistry, processing, safety, fermentation",
           ("matter", "machine")),

    # --- MACHINE (6 domains) ---
    Domain("mechanical", "Mechanical Engineering", "machine",
           "Mechanics, structures, tribology, corrosion",
           ("matter", "energy")),
    Domain("robotics", "Robotics", "machine",
           "Manipulation, locomotion, control, sensors",
           ("information", "life")),
    Domain("manufacturing", "Advanced Manufacturing", "machine",
           "Additive, subtractive, forming, assembly",
           ("matter", "information")),
    Domain("aerospace", "Aerospace", "machine",
           "Propulsion, structures, controls, materials",
           ("energy", "information", "matter")),
    Domain("transportation", "Transportation", "machine",
           "Automotive, rail, aviation, maritime, autonomous",
           ("information", "energy", "planet")),
    Domain("civil_engineering", "Civil & Construction", "machine",
           "Structures, materials, geotechnical, energy",
           ("matter", "energy", "planet")),

    # --- INFORMATION (7 domains) ---
    Domain("computing", "Computational Science", "information",
           "Numerical methods, simulation, scientific ML",
           ("matter", "energy", "life", "planet")),
    Domain("ai", "Artificial Intelligence", "information",
           "ML, deep learning, NLP, computer vision",
           ("life", "machine")),
    Domain("semiconductors", "Semiconductors", "information",
           "Device physics, fabrication, packaging",
           ("matter", "energy", "machine")),
    Domain("electronics", "Electronics", "information",
           "Printed/flexible electronics, MEMS, sensors",
           ("matter", "machine")),
    Domain("photonics", "Photonics & Optics", "information",
           "Lasers, waveguides, metamaterials, sensing",
           ("matter", "energy", "machine")),
    Domain("telecom", "Telecommunications", "information",
           "RF, antennas, optical comm, networking",
           ("machine", "planet")),
    Domain("quantum", "Quantum Technology", "information",
           "Quantum materials, sensing, computing, comms",
           ("matter", "energy", "machine")),

    # --- PLANET (6 domains) ---
    Domain("climate", "Climate & Atmospheric Science", "planet",
           "Atmospheric chemistry, climate modeling, carbon",
           ("energy", "life")),
    Domain("environmental", "Environmental Science", "planet",
           "Pollution, ecology, sustainability, remediation",
           ("life", "matter", "energy")),
    Domain("water", "Water Technology", "planet",
           "Desalination, membranes, filtration, treatment",
           ("matter", "energy", "life")),
    Domain("ocean", "Ocean & Marine Technology", "planet",
           "Hydrodynamics, corrosion, marine vehicles, sensing",
           ("machine", "matter", "life")),
    Domain("geoscience", "Geoscience", "planet",
           "Mineralogy, geology, geophysics, subsurface",
           ("matter", "energy")),
    Domain("atmospheric", "Atmospheric Science", "planet",
           "Weather, atmospheric chemistry, remote sensing",
           ("energy", "information")),
]


def get_all_domains() -> list[Domain]:
    return DOMAINS


def get_domains_by_universe(universe: str) -> list[Domain]:
    return [d for d in DOMAINS if d.universe == universe]


def get_universe_of_domain(domain_id: str) -> str | None:
    for d in DOMAINS:
        if d.domain_id == domain_id:
            return d.universe
    return None


def universe_distance(u1: str, u2: str) -> int:
    """Distance between two universes (0=same, 5=max).

    Used for knowledge-distance scoring (search prioritization only,
    NOT evidence of truth)."""
    if u1 == u2:
        return 0
    # 6 universes -> max distance is 5
    return 5  # any non-same is treated as max distance for the simple metric


def domain_distance(d1: str, d2: str) -> int:
    """Distance between two domains. 0=same domain, 1=same universe different
    domain, 5=different universe."""
    if d1 == d2:
        return 0
    u1 = get_universe_of_domain(d1)
    u2 = get_universe_of_domain(d2)
    if u1 == u2:
        return 1
    return 5


def domain_map_summary() -> dict:
    by_universe: dict[str, int] = {}
    for d in DOMAINS:
        by_universe[d.universe] = by_universe.get(d.universe, 0) + 1
    return {
        "total_domains": len(DOMAINS),
        "total_universes": len(UNIVERSES),
        "domains_by_universe": by_universe,
        "universes": UNIVERSES,
    }
