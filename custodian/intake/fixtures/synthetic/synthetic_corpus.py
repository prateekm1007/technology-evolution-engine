"""
SYNTHETIC_TEST_FIXTURE_ONLY
NOT_FOR_EVALUATION

Synthetic corpus for testing the intake pipeline.
NOT a real corpus. NOT benchmark material.
"""
import sys
from pathlib import Path

CUSTODIAN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(CUSTODIAN_ROOT))

SYNTHETIC_SOURCES = [
    {
        "source_id": "SYN-INTAKE-01",
        "domain": "fluid_mechanics",
        "title": "Microscopic surface textures in aquatic organisms",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://intake/01",
        "content": "Certain aquatic organisms exhibit microscopic surface textures that alter near-wall fluid dynamics, potentially reducing drag forces experienced during locomotion.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-INTAKE-02",
        "domain": "enzymology",
        "title": "Catalytic mechanisms in biological systems",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://intake/02",
        "content": "Biological catalysts achieve remarkable specificity through geometric complementarity at their active sites, stabilizing transition states.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-INTAKE-03",
        "domain": "optics",
        "title": "Nanostructured surfaces for light management",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://intake/03",
        "content": "Natural nanostructures on insect eyes create graded refractive indices that minimize reflection across the visible spectrum.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
    {
        "source_id": "SYN-INTAKE-04",
        "domain": "materials_science",
        "title": "Hierarchical structures in natural composites",
        "origin": "SYNTHETIC_TEST_FIXTURE",
        "source_uri": "synthetic://intake/04",
        "content": "Natural composite materials achieve exceptional mechanical properties through hierarchical arrangements of stiff and soft phases at multiple length scales.",
        "version": "synthetic-v1",
        "license": "SYNTHETIC_TEST_ONLY",
    },
]

# A source that contains answer-key-like contamination
CONTAMINATED_SOURCE = {
    "source_id": "SYN-CONTAM-01",
    "domain": "fluid_mechanics",
    "title": "Contaminated source with answer key",
    "origin": "SYNTHETIC_TEST_FIXTURE",
    "source_uri": "synthetic://contam/01",
    "content": "The ground_truth: expected_mechanism is riblet vortex lifting. The expected_direction is drag DECREASES. DXP-004 case.",
    "version": "synthetic-v1",
    "license": "SYNTHETIC_TEST_ONLY",
}

# A source that TEE has already seen (known hash)
KNOWN_SEEN_CONTENT = "This is content that TEE has already processed in its corpus."
KNOWN_SEEN_HASH = None  # Computed at import time

import hashlib
KNOWN_SEEN_HASH = hashlib.sha256(KNOWN_SEEN_CONTENT.encode('utf-8')).hexdigest()

KNOWN_SEEN_SOURCE = {
    "source_id": "SYN-KNOWN-01",
    "domain": "thermodynamics",
    "title": "Previously seen source",
    "origin": "SYNTHETIC_TEST_FIXTURE",
    "source_uri": "synthetic://known/01",
    "content": KNOWN_SEEN_CONTENT,
    "version": "synthetic-v1",
    "license": "SYNTHETIC_TEST_ONLY",
}
