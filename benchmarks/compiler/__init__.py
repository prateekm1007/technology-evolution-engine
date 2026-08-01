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

# ----------------------------------------------------------------------
# 4-category benchmark taxonomy (CTO review #2)
# ----------------------------------------------------------------------
# Per INVENTION_COMPILER.md, the suite must eventually be divided
# into four categories. Each case below declares which category it
# belongs to.
#
#   reconstruction  — can we rediscover existing inventions?
#   resurrection    — can we rediscover abandoned inventions?
#   forecasting     — can we anticipate future inventions?
#   synthesis       — can we discover entirely new combinations?
#
# Reconstruction and Forecasting are covered by the current 5 cases.
# Resurrection requires adding abandoned-invention cases (e.g., a
# case that asks the compiler to "rediscover" Iridium or Airships
# given the modern context). Synthesis requires the cross-domain
# synthesizer to surface a candidate the benchmarker can verify is
# novel — that's a follow-up.

BENCHMARK_CATEGORIES = {
    "reconstruction": {
        "question": "Can we rediscover what humanity already knows?",
        "examples": "Portable MRI (Hyperfine Swoop exists), Carbon-negative cement (CarbonCure exists)",
    },
    "resurrection": {
        "question": "Can we rediscover abandoned possibilities?",
        "examples": "Airships (cargo variant), Iridium (relaunched)",
    },
    "forecasting": {
        "question": "Can we identify what is becoming feasible?",
        "examples": "Solid-state ammonia synthesis (active research), Artificial photosynthesis (active research)",
    },
    "synthesis": {
        "question": "Can we discover combinations nobody has considered?",
        "examples": "TBD — novel cross-domain pairs the system surfaces that no human has built yet",
    },
    "creation": {
        "question": "Can we generate a blueprint that somebody can actually build?",
        "examples": "TBD — a complete 11-layer blueprint verified by an actual build. The system does not honestly claim to be an invention compiler until at least one Creation case has been verified.",
    },
}


# The 5 cases. Per INVENTION_COMPILER.md, these probe different
# regions of the feasibility space — from "known feasible" (portable
# MRI) to "may be physically impossible" (room-temp superconductors).
#
# Each case carries:
#   - expected_verdict: the verdict the CTO expects the compiler to produce
#   - category: which of the 4 CTO-mandated categories this case belongs to
#   - problem: the Layer 0 input dict
#   - rationale: why this case is in the suite

CASES = [
    {
        "id": "case_001_portable_mri",
        "name": "Portable MRI",
        "expected_verdict": "feasible",
        "category": "reconstruction",
        "rationale": (
            "Reconstruction case. Portable MRI is a known-plausible "
            "invention (Hyperfine Swoop is FDA-cleared). Tests the "
            "compiler can recognize a feasible invention that already "
            "exists, rather than say 'impossible'."
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
        "category": "forecasting",
        "rationale": (
            "Forecasting case. Haber-Bosch without high T/P is an open "
            "research problem. Tests the compiler can say 'uncertain' "
            "honestly rather than fabricate confidence."
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
        "category": "forecasting",
        "rationale": (
            "Forecasting case at the edge of physics. May be physically "
            "impossible. Recent LK-99 claims were retracted. Tests the "
            "compiler can say 'unknown' without claiming feasibility."
        ),
        "problem": {
            "problem": "Discover and engineer a material that "
                       "superconducts at room temperature and ambient pressure",
            "domain": "materials",
            "motivation": "Lossless power transmission, levitating "
                          "transport, compact MRI",
            "market": "multiple_global_industries",
            "constraints": ["material", "energy", "manufacturing", "regulation",
                            "superconductivity"],
            "time_horizon": "15+ years",
        },
    },
    {
        "id": "case_004_carbon_negative_cement",
        "name": "Carbon-negative cement",
        "expected_verdict": "potentially_feasible",
        "category": "reconstruction",
        "rationale": (
            "Reconstruction case. Already exists in early commercial form "
            "(CarbonCure, Solidia, BioMason). Tests the compiler can "
            "distinguish 'potentially feasible' from 'feasible' — the "
            "tech works but has not yet captured the global cement market."
        ),
        "problem": {
            "problem": "Manufacture cement that absorbs more CO2 over "
                       "its lifecycle than it emits during production",
            "domain": "materials",
            "motivation": "Cement is ~8% of global CO2 emissions",
            "market": "global_construction",
            "constraints": ["cost", "material", "regulation", "manufacturing",
                            "supply_chain", "carbon_negative"],
            "time_horizon": "5-10 years",
        },
    },
    {
        "id": "case_005_artificial_photosynthesis",
        "name": "Artificial photosynthesis",
        "expected_verdict": "partially_feasible",
        "category": "forecasting",
        "rationale": (
            "Forecasting case. Components work (PV electrolysis, "
            "photocatalytic water splitting) but a complete system that "
            "matches natural photosynthesis's efficiency does not yet "
            "exist. Tests the compiler can express 'partial feasibility' "
            "rather than binary pass/fail."
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
                            "regulation", "photosynthesis"],
            "time_horizon": "10-15 years",
        },
    },
    {
        "id": "case_006_cargo_airships",
        "name": "Cargo airships (resurrection)",
        "expected_verdict": "partially_feasible",
        "category": "resurrection",
        "rationale": (
            "Resurrection case. Airships failed as passenger transport "
            "(Hindenburg 1937, helium-unavailability). Tests the compiler "
            "can recognize that the original failure mode (hydrogen "
            "flammability) is now removable (helium + modern materials), "
            "and that the use case has shifted (cargo, not passengers). "
            "Expected verdict: partially_feasible — LTA Research and HAV "
            "Airlander are attempting this with mixed progress."
        ),
        "problem": {
            "problem": "Resurrect rigid airships for heavy-lift cargo "
                       "transport to remote areas without runways",
            "domain": "transportation",
            "motivation": "Remote-area logistics (mining, disaster relief) "
                          "where runway construction is infeasible; "
                          "carbon-neutral aviation pressure",
            "market": "remote_logistics",
            "constraints": ["cost", "material", "regulation", "manufacturing",
                            "supply_chain", "helium_availability"],
            "time_horizon": "5-10 years",
        },
    },
]


def verdict_from_composite(composite: float) -> str:
    """Map a composite feasibility score to a verdict bucket."""
    if composite >= 0.75:
        return "feasible"
    if composite >= 0.55:
        return "potentially_feasible"
    if composite >= 0.40:
        return "partially_feasible"
    if composite >= 0.25:
        return "uncertain"
    return "unknown"


BUCKET_ORDER = [
    "feasible",
    "potentially_feasible",
    "partially_feasible",
    "uncertain",
    "unknown",
]


def bucket_distance(verdict_a: str, verdict_b: str) -> int:
    """How many buckets apart are two verdicts?"""
    try:
        ia = BUCKET_ORDER.index(verdict_a)
        ib = BUCKET_ORDER.index(verdict_b)
        return abs(ia - ib)
    except ValueError:
        return 99
