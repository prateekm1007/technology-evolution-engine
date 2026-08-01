"""
5-benchmark suite for the invention compiler.

Each case is a YAML-style problem definition. The benchmark runner
(`scripts/run_compiler_benchmarks.py`) compiles each case through the
full 11-layer pipeline and compares the verdict to the expected
verdict specified by the CTO review (see INVENTION_COMPILER.md).

Verdict buckets (composite feasibility → verdict):
    composite >= 0.75     -> feasible
    0.55 <= c < 0.75      -> potentially_feasible
    0.40 <= c < 0.55      -> partially_feasible
    0.25 <= c < 0.40      -> uncertain
    c < 0.25              -> unknown
"""

# The 5 cases. Per INVENTION_COMPILER.md, these probe different
# regions of the feasibility space — from "known feasible" (portable
# MRI) to "may be physically impossible" (room-temp superconductors).
#
# Each case carries:
#   - expected_verdict: the verdict the CTO expects the compiler to produce
#   - problem: the Layer 0 input dict
#   - rationale: why this case is in the suite

CASES = [
    {
        "id": "case_001_portable_mri",
        "name": "Portable MRI",
        "expected_verdict": "feasible",
        "rationale": (
            "Control case. Portable MRI is a known-plausible invention "
            "(Hyperfine Swoop is FDA-cleared). Tests the compiler does "
            "not say 'impossible' on a real invention."
        ),
        "problem": {
            "problem": "Build a portable MRI scanner suitable for rural "
                       "clinics without cryogenic helium",
            "domain": "medical_imaging",
            "motivation": "Conventional MRI requires $100K+ helium and "
                          "shielded rooms; rural clinics cannot afford either",
            "market": "global_radiology",
            "constraints": ["cost", "weight", "power", "regulation", "manufacturing"],
            "time_horizon": "5-10 years",
        },
    },
    {
        "id": "case_002_ammonia_synthesis",
        "name": "Solid-state ammonia synthesis",
        "expected_verdict": "uncertain",
        "rationale": (
            "Active research area. Haber-Bosch without high T/P is an "
            "open problem — the honest answer is 'we don't know yet.' "
            "Tests the compiler can say 'uncertain' honestly rather than "
            "fabricate confidence."
        ),
        "problem": {
            "problem": "Synthesize ammonia from nitrogen and water at "
                       "ambient temperature and pressure using electrochemistry",
            "domain": "chemistry",
            "motivation": "Haber-Bosch consumes 1-2% of world energy; a "
                          "low-energy route would decarbonize fertilizer",
            "market": "global_agriculture",
            "constraints": ["energy", "catalyst", "manufacturing", "regulation"],
            "time_horizon": "10-15 years",
        },
    },
    {
        "id": "case_003_rt_superconductors",
        "name": "Room-temperature superconductors",
        "expected_verdict": "unknown",
        "rationale": (
            "May be physically impossible. Recent LK-99 claims were "
            "retracted; no known material superconducts above ~250K at "
            "ambient pressure. Tests the compiler can say 'unknown' "
            "without claiming feasibility."
        ),
        "problem": {
            "problem": "Discover and engineer a material that "
                       "superconducts at room temperature and ambient pressure",
            "domain": "materials",
            "motivation": "Lossless power transmission, levitating "
                          "transport, compact MRI",
            "market": "multiple_global_industries",
            "constraints": ["material", "energy", "manufacturing", "regulation",
                            "scientific_unknown"],
            "time_horizon": "15+ years",
        },
    },
    {
        "id": "case_004_carbon_negative_cement",
        "name": "Carbon-negative cement",
        "expected_verdict": "potentially_feasible",
        "rationale": (
            "Already exists in early commercial form (CarbonCure, "
            "Solidia, BioMason). Tests the compiler can distinguish "
            "'potentially feasible' from 'feasible' — the tech works "
            "but has not yet captured the global cement market."
        ),
        "problem": {
            "problem": "Manufacture cement that absorbs more CO2 over "
                       "its lifecycle than it emits during production",
            "domain": "materials",
            "motivation": "Cement is ~8% of global CO2 emissions",
            "market": "global_construction",
            "constraints": ["cost", "material", "regulation", "manufacturing",
                            "supply_chain"],
            "time_horizon": "5-10 years",
        },
    },
    {
        "id": "case_005_artificial_photosynthesis",
        "name": "Artificial photosynthesis",
        "expected_verdict": "partially_feasible",
        "rationale": (
            "Components work (PV electrolysis, photocatalytic water "
            "splitting) but a complete system that matches natural "
            "photosynthesis's efficiency does not yet exist. Tests "
            "the compiler can express 'partial feasibility' rather than "
            "binary pass/fail."
        ),
        "problem": {
            "problem": "Build a system that converts sunlight, CO2, and "
                       "water into storable chemical fuel with efficiency "
                       "exceeding natural photosynthesis",
            "domain": "energy",
            "motivation": "Carbon-neutral liquid fuel for hard-to-electrify "
                          "sectors (aviation, shipping)",
            "market": "global_energy",
            "constraints": ["energy", "material", "catalyst", "manufacturing",
                            "regulation", "scientific_unknown"],
            "time_horizon": "10-15 years",
        },
    },
]


def verdict_from_composite(composite: float) -> str:
    """Map a composite feasibility score to a verdict bucket.

    Per INVENTION_COMPILER.md, the buckets are priors, not
    calibrations. They should be recalibrated as the verification
    cycle accumulates outcomes.
    """
    if composite >= 0.75:
        return "feasible"
    if composite >= 0.55:
        return "potentially_feasible"
    if composite >= 0.40:
        return "partially_feasible"
    if composite >= 0.25:
        return "uncertain"
    return "unknown"


# Ordered list of buckets, from most to least feasible.
BUCKET_ORDER = [
    "feasible",
    "potentially_feasible",
    "partially_feasible",
    "uncertain",
    "unknown",
]


def bucket_distance(verdict_a: str, verdict_b: str) -> int:
    """How many buckets apart are two verdicts? 0 = same bucket,
    1 = adjacent bucket, etc. Used to decide PASS (within 1) vs
    FAIL (more than 1 apart)."""
    try:
        ia = BUCKET_ORDER.index(verdict_a)
        ib = BUCKET_ORDER.index(verdict_b)
        return abs(ia - ib)
    except ValueError:
        return 99  # unknown verdict -> large distance
