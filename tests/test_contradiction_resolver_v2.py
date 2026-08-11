"""Tests for contradiction_resolver_v2.py — Contradiction resolution 7→9."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.contradiction_resolver_v2 import (
    PhysicalDomainResolver,
    PhysicalDomain,
    ParameterizedSolution,
    PARAMETER_DOMAINS,
    PRINCIPLE_DOMAINS,
)


def test_classify_mechanical_parameter():
    """Mechanical parameters are classified correctly."""
    resolver = PhysicalDomainResolver()
    assert resolver.classify_parameter("strength") == PhysicalDomain.MECHANICAL
    assert resolver.classify_parameter("weight") == PhysicalDomain.MECHANICAL
    assert resolver.classify_parameter("stiffness") == PhysicalDomain.MECHANICAL
    assert resolver.classify_parameter("fatigue") == PhysicalDomain.MECHANICAL


def test_classify_thermal_parameter():
    """Thermal parameters are classified correctly."""
    resolver = PhysicalDomainResolver()
    assert resolver.classify_parameter("temperature") == PhysicalDomain.THERMAL
    assert resolver.classify_parameter("heat") == PhysicalDomain.THERMAL


def test_classify_electrical_parameter():
    """Electrical parameters are classified correctly."""
    resolver = PhysicalDomainResolver()
    assert resolver.classify_parameter("conductivity") == PhysicalDomain.ELECTRICAL
    assert resolver.classify_parameter("voltage") == PhysicalDomain.ELECTRICAL


def test_classify_unknown_returns_general():
    """Unknown parameters return GENERAL domain."""
    resolver = PhysicalDomainResolver()
    assert resolver.classify_parameter("purple") == PhysicalDomain.GENERAL
    assert resolver.classify_parameter("snorkle") == PhysicalDomain.GENERAL


def test_classify_case_insensitive():
    """Classification is case-insensitive."""
    resolver = PhysicalDomainResolver()
    assert resolver.classify_parameter("STRENGTH") == PhysicalDomain.MECHANICAL
    assert resolver.classify_parameter("Temperature") == PhysicalDomain.THERMAL


def test_resolve_returns_solutions():
    """resolve() returns a list of ParameterizedSolution objects."""
    resolver = PhysicalDomainResolver()
    solutions = resolver.resolve("strength", "weight", top_k=3)
    assert len(solutions) == 3
    for s in solutions:
        assert isinstance(s, ParameterizedSolution)
        assert s.principle_number >= 1
        assert s.principle_number <= 40
        assert 0.0 <= s.compatibility_score <= 1.0


def test_resolve_mechanical_favors_mechanical_principles():
    """A purely mechanical contradiction favors mechanical-domain principles."""
    resolver = PhysicalDomainResolver()
    solutions = resolver.resolve("strength", "weight", top_k=5)
    # The top solution should have mechanical in its domains
    assert "mechanical" in solutions[0].physical_domains


def test_resolve_thermal_contradiction():
    """A thermal contradiction scores thermal principles highly."""
    resolver = PhysicalDomainResolver()
    solutions = resolver.resolve("temperature", "energy", top_k=10)
    # At least one of the top 10 should be a thermal-domain principle
    thermal_found = any("thermal" in s.physical_domains for s in solutions)
    assert thermal_found


def test_parameterized_sketch_includes_placeholders():
    """Solution sketches include <<placeholder>> syntax."""
    resolver = PhysicalDomainResolver()
    solutions = resolver.resolve("strength", "weight", top_k=3)
    # At least one solution should have <<...>> placeholders
    found_placeholder = any("<<" in s.parameterized_sketch for s in solutions)
    assert found_placeholder


def test_parameterized_sketch_includes_improve_worsen():
    """Solution sketches include the improve and worsen parameters."""
    resolver = PhysicalDomainResolver()
    solutions = resolver.resolve("strength", "weight", top_k=3)
    for s in solutions:
        if "<<" in s.parameterized_sketch:
            # The template should have substituted {improve} and {worsen}
            assert "strength" in s.parameterized_sketch or "weight" in s.parameterized_sketch


def test_compatibility_score_higher_for_matching_domains():
    """Principles matching the contradiction's domains score higher."""
    resolver = PhysicalDomainResolver()
    # Mechanical contradiction
    score_mech = resolver.principle_compatibility(
        1,  # Segmentation (mechanical)
        {PhysicalDomain.MECHANICAL},
    )
    score_thermal = resolver.principle_compatibility(
        36,  # Phase transitions (thermal)
        {PhysicalDomain.MECHANICAL},
    )
    assert score_mech > score_thermal, \
        f"Mechanical principle ({score_mech}) should outscore thermal ({score_thermal}) on a mechanical contradiction"


def test_general_principle_compat_neutral():
    """General principles have neutral (0.5) compatibility."""
    resolver = PhysicalDomainResolver()
    # Principle 6 (Universality) is GENERAL-only
    score = resolver.principle_compatibility(
        6,
        {PhysicalDomain.MECHANICAL, PhysicalDomain.THERMAL},
    )
    assert score == 0.5


def test_compat_zero_for_non_overlapping():
    """Principles with zero domain overlap have low (0.2) compatibility."""
    resolver = PhysicalDomainResolver()
    # Principle 32 (Color changes) is OPTICAL only
    score = resolver.principle_compatibility(
        32,
        {PhysicalDomain.MECHANICAL},
    )
    assert score == 0.2


def test_reasoning_mentions_domains():
    """Each solution's reasoning mentions the physical domains."""
    resolver = PhysicalDomainResolver()
    solutions = resolver.resolve("strength", "weight", top_k=3)
    for s in solutions:
        assert "domain" in s.reasoning.lower() or "mechanical" in s.reasoning.lower()


def test_principle_domains_covers_all_40():
    """Every TRIZ principle (1-40) has a domain classification."""
    for pnum in range(1, 41):
        assert pnum in PRINCIPLE_DOMAINS, f"Principle {pnum} missing from PRINCIPLE_DOMAINS"


def test_parameter_domains_covers_main_engineering_params():
    """Main engineering parameters are classified."""
    expected = {"strength", "weight", "temperature", "conductivity",
                "corrosion", "cost", "efficiency", "speed"}
    found = set(PARAMETER_DOMAINS.keys())
    missing = expected - found
    assert not missing, f"Missing parameters: {missing}"


def test_concrete_examples_for_top_principles():
    """Principles 40, 35, 1 have concrete examples."""
    resolver = PhysicalDomainResolver()
    for pnum in [40, 35, 1]:
        examples = resolver.CONCRETE_EXAMPLES.get(pnum, [])
        assert len(examples) >= 1, f"Principle {pnum} missing concrete examples"


def test_resolve_handles_unknown_parameter():
    """resolve() works even with unknown parameters (returns GENERAL)."""
    resolver = PhysicalDomainResolver()
    solutions = resolver.resolve("unknown_param", "weight", top_k=3)
    assert len(solutions) == 3


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
