"""
SYNTHETIC_TEST_FIXTURE_ONLY
NOT_FOR_EVALUATION

This file contains a small synthetic corpus solely for testing the custodian
machinery. It is NOT the benchmark. It must NOT be used for evaluation.
It must NOT be reported as benchmark evidence.

It exists to prove:
- deterministic sampling works
- duplicate detection works
- independence-group detection works
- blind/answer-key separation works
- hashing works
- manifest generation works
- sealing works
- immutability works
- reproducibility works
"""

# 6 synthetic sources across 4 domains (minimum for testing)
SYNTHETIC_SOURCES = [
    {
        "source_id": "SYN-A1",
        "domain": "fluid_mechanics",
        "title": "Shark skin riblet hydrodynamics",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://fluid_mechanics/riblet",
        "content": "Shark skin denticles feature microscopic riblets that lift streamwise vortices away from the surface, reducing turbulent skin friction drag by 5-10%.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-B1",
        "domain": "fluid_mechanics",
        "title": "Pipe drag reduction surface treatment",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://fluid_mechanics/pipe_drag",
        "content": "Pipeline drag reduction can be achieved through surface modifications that alter near-wall turbulence structure.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-A2",
        "domain": "enzymology",
        "title": "Enzyme active site catalysis",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://enzymology/active_site",
        "content": "Enzyme active sites stabilize transition states through precise geometric and electrostatic complementarity, lowering activation energy by 10-20 kJ/mol.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-B2",
        "domain": "enzymology",
        "title": "Industrial catalyst design",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://enzymology/catalyst",
        "content": "Industrial catalysts seek to replicate enzyme efficiency at high temperatures and pressures.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-A3",
        "domain": "optics",
        "title": "Moth eye anti-reflection structure",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://optics/moth_eye",
        "content": "Moth eyes feature nanostructured surfaces that create a graded refractive index, reducing reflection to less than 1% across visible wavelengths.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-B3",
        "domain": "optics",
        "title": "Solar cell efficiency improvement",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://optics/solar_cell",
        "content": "Solar cell efficiency is limited by reflection losses at the air-semiconductor interface.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-A4",
        "domain": "materials_science",
        "title": "Nacre structural toughness",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://materials/nacre",
        "content": "Nacre achieves exceptional toughness through a brick-and-mortar arrangement of aragonite platelets and biopolymer, deflecting cracks at multiple length scales.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-B4",
        "domain": "materials_science",
        "title": "Composite armor design",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://materials/armor",
        "content": "Lightweight composite armor requires high fracture toughness and crack deflection capability.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
]

# 8 synthetic cases (4 domains × 2 per domain) — NOT 100, for testing only
SYNTHETIC_CASES = [
    {
        "case_id": "SYN-CASE-01",
        "source_id": "SYN-A1",
        "domain": "fluid_mechanics",
        "problem": "Reduce pipeline pumping energy costs",
        "input_material": {
            "source_a": SYNTHETIC_SOURCES[0]["content"],
            "source_b": SYNTHETIC_SOURCES[1]["content"],
        },
        "expected_task": "Generate a hypothesis for how the shark skin mechanism could reduce pipe drag",
        "verification_method": "Quantitative drag reduction measurement",
        "difficulty": "moderate",
        "independence_group": "IG-01",
        "provenance": {
            "constructor": "synthetic_fixture_generator",
            "construction_timestamp": "2026-08-10T00:00:00Z",
            "construction_method": "synthetic",
            "source_version": "synthetic-v1",
        },
        "ground_truth": {
            "type": "positive",
            "mechanism": "riblet geometry lifts streamwise vortices",
            "causal_variable": "riblet spacing",
            "direction": "drag DECREASES",
            "magnitude": "5-10% reduction",
            "falsifier": "riblets outside 5-25 wall units produce no reduction",
        },
    },
    {
        "case_id": "SYN-CASE-02",
        "source_id": "SYN-A2",
        "domain": "enzymology",
        "problem": "Design a high-temperature industrial catalyst",
        "input_material": {
            "source_a": SYNTHETIC_SOURCES[2]["content"],
            "source_b": SYNTHETIC_SOURCES[3]["content"],
        },
        "expected_task": "Generate a hypothesis for enzyme-inspired catalyst design",
        "verification_method": "Catalytic efficiency measurement",
        "difficulty": "hard",
        "independence_group": "IG-02",
        "provenance": {
            "constructor": "synthetic_fixture_generator",
            "construction_timestamp": "2026-08-10T00:00:00Z",
            "construction_method": "synthetic",
            "source_version": "synthetic-v1",
        },
        "ground_truth": {
            "type": "positive",
            "mechanism": "transition state stabilization",
            "causal_variable": "active site geometry",
            "direction": "activation energy DECREASES",
            "magnitude": "10-20 kJ/mol reduction",
            "falsifier": "catalysts without geometric complementarity show no improvement",
        },
    },
    {
        "case_id": "SYN-CASE-03",
        "source_id": "SYN-A3",
        "domain": "optics",
        "problem": "Improve solar cell efficiency",
        "input_material": {
            "source_a": SYNTHETIC_SOURCES[4]["content"],
            "source_b": SYNTHETIC_SOURCES[5]["content"],
        },
        "expected_task": "Generate a hypothesis for moth-eye-inspired anti-reflection coating",
        "verification_method": "Reflectance measurement",
        "difficulty": "moderate",
        "independence_group": "IG-03",
        "provenance": {
            "constructor": "synthetic_fixture_generator",
            "construction_timestamp": "2026-08-10T00:00:00Z",
            "construction_method": "synthetic",
            "source_version": "synthetic-v1",
        },
        "ground_truth": {
            "type": "positive",
            "mechanism": "graded refractive index",
            "causal_variable": "nanostructure spacing",
            "direction": "reflectance DECREASES",
            "magnitude": "<1% reflection",
            "falsifier": "smooth surfaces show >4% reflection",
        },
    },
    {
        "case_id": "SYN-CASE-04",
        "source_id": "SYN-A4",
        "domain": "materials_science",
        "problem": "Design lightweight composite armor",
        "input_material": {
            "source_a": SYNTHETIC_SOURCES[6]["content"],
            "source_b": SYNTHETIC_SOURCES[7]["content"],
        },
        "expected_task": "Generate a hypothesis for nacre-inspired tough composite",
        "verification_method": "Fracture toughness measurement",
        "difficulty": "hard",
        "independence_group": "IG-04",
        "provenance": {
            "constructor": "synthetic_fixture_generator",
            "construction_timestamp": "2026-08-10T00:00:00Z",
            "construction_method": "synthetic",
            "source_version": "synthetic-v1",
        },
        "ground_truth": {
            "type": "positive",
            "mechanism": "crack deflection at platelet interfaces",
            "causal_variable": "platelet aspect ratio",
            "direction": "toughness INCREASES",
            "magnitude": "3-5x improvement",
            "falsifier": "random platelet orientation shows no improvement",
        },
    },
]

SYNTHETIC_EXTERNAL_SEED = "synthetic-test-seed-not-for-evaluation"
