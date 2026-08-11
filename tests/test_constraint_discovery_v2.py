"""Tests for constraint_discovery_v2.py — Constraint discovery 6→8."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.constraint_discovery_v2 import (
    discover_implicit_constraints,
    discover_conservation_constraints,
    discover_dimensional_constraints,
    discover_thermodynamic_constraints,
    discover_kinetic_constraints,
)
from scripts.constraint_from_equations import ConstraintDirection


def test_mass_conservation_from_reaction():
    """A + B → C produces a mass conservation constraint."""
    text = "Hydrogen and oxygen react to form water: H2 + O2 → H2O."
    constraints = discover_conservation_constraints(text)
    assert len(constraints) >= 1
    # The constraint should mention mass conservation
    found_mass = any("mass conservation" in c.relationship.lower() or "mass(" in c.relationship.lower()
                     for c in constraints)
    assert found_mass, f"No mass conservation constraint found: {[c.relationship for c in constraints]}"


def test_energy_conservation_from_heat_flow():
    """Heat flow from A to B produces an energy conservation constraint."""
    text = "Heat flow from the reactor to the cooling jacket was measured."
    constraints = discover_conservation_constraints(text)
    assert len(constraints) >= 1
    found_energy = any("energy" in c.relationship.lower() for c in constraints)
    assert found_energy, f"No energy conservation constraint found: {[c.relationship for c in constraints]}"


def test_efficiency_carnot_constraint():
    """An efficiency claim produces a Carnot bound constraint."""
    text = "The engine has an efficiency of 35%."
    constraints = discover_thermodynamic_constraints(text)
    assert len(constraints) >= 1
    # The constraint should mention Carnot
    found_carnot = any("carnot" in c.relationship.lower() for c in constraints)
    assert found_carnot, f"No Carnot constraint found: {[c.relationship for c in constraints]}"


def test_gibbs_energy_constraint_for_reaction():
    """A 'reaction' keyword produces a ΔG constraint."""
    text = "The reaction proceeded to completion overnight."
    constraints = discover_thermodynamic_constraints(text)
    # Should find both ΔG and ΔS constraints for "reaction"
    gibbs = any("δg" in c.relationship.lower() or "gibbs" in c.relationship.lower() for c in constraints)
    entropy = any("δs" in c.relationship.lower() or "entropy" in c.relationship.lower() for c in constraints)
    assert gibbs, f"No ΔG constraint found: {[c.relationship for c in constraints]}"
    assert entropy, f"No ΔS constraint found: {[c.relationship for c in constraints]}"


def test_arrhenius_kinetic_constraint():
    """Mentioning Arrhenius produces an E_a > 0 constraint."""
    text = "The rate constant follows the Arrhenius equation with E_a = 50 kJ/mol."
    constraints = discover_kinetic_constraints(text)
    assert len(constraints) >= 1
    found_ea = any("e_a" in c.relationship.lower() or "activation" in c.relationship.lower()
                   for c in constraints)
    assert found_ea, f"No activation energy constraint found: {[c.relationship for c in constraints]}"


def test_rate_law_constraint():
    """A rate law produces k > 0 constraint."""
    text = "The rate = k * [A]^2 was measured at 300K."
    constraints = discover_kinetic_constraints(text)
    assert len(constraints) >= 1
    found_k = any("rate constant k" in c.relationship.lower() for c in constraints)
    assert found_k, f"No rate constant constraint found: {[c.relationship for c in constraints]}"


def test_dimensional_constraint_from_equation():
    """An equation produces constraints for each unknown RHS variable."""
    eq = "Q = σAT⁴"
    constraints = discover_dimensional_constraints(eq)
    # σ and A appear on RHS but not LHS → they constrain Q
    assert len(constraints) >= 1
    # At least one constraint should mention σ or A
    found = any("σ" in c.constrained_variable or "A" in c.constrained_variable
                for c in constraints)
    assert found, f"No σ/A constraint found: {[c.constrained_variable for c in constraints]}"


def test_combined_implicit_constraints():
    """discover_implicit_constraints combines all four discovery methods."""
    text = "The combustion reaction CH4 + 2O2 → CO2 + 2H2O releases energy."
    constraints = discover_implicit_constraints(text)
    # Should have multiple constraints from conservation + thermodynamic
    assert len(constraints) >= 2


def test_no_constraints_on_empty_text():
    """Empty text yields no constraints."""
    assert discover_implicit_constraints("") == []
    assert discover_conservation_constraints("") == []
    assert discover_thermodynamic_constraints("") == []
    assert discover_kinetic_constraints("") == []


def test_constraints_have_valid_direction():
    """All constraints have a valid ConstraintDirection."""
    text = "The reaction A + B → C releases heat."
    constraints = discover_implicit_constraints(text)
    for c in constraints:
        assert isinstance(c.direction, ConstraintDirection), \
            f"Invalid direction: {c.direction}"


def test_constraints_have_confidence_in_range():
    """All constraints have confidence in [0, 1]."""
    text = "The engine has 30% efficiency. The reaction A + B → C is spontaneous."
    constraints = discover_implicit_constraints(text)
    for c in constraints:
        assert 0.0 <= c.confidence <= 1.0, \
            f"Confidence out of range: {c.confidence}"


def test_charge_conservation_from_redox():
    """A redox reaction with electrons produces a charge conservation constraint."""
    text = "Fe(3+) + e- → Fe(2+) is the reduction half-reaction."
    constraints = discover_conservation_constraints(text)
    # Charge conservation constraint should be present
    found_charge = any("charge" in c.relationship.lower() for c in constraints)
    assert found_charge, f"No charge conservation found: {[c.relationship for c in constraints]}"


def test_momentum_conservation_from_collision():
    """A collision description produces a momentum conservation constraint."""
    text = "The electron collides with the atom and transfers momentum."
    constraints = discover_conservation_constraints(text)
    found_momentum = any("momentum" in c.relationship.lower() for c in constraints)
    assert found_momentum, f"No momentum conservation found: {[c.relationship for c in constraints]}"


def test_constraints_have_source_equation():
    """Every constraint has a non-empty source_equation."""
    text = "The reaction A + B → C releases 100 J of energy."
    constraints = discover_implicit_constraints(text)
    for c in constraints:
        assert c.source_equation, f"Empty source_equation: {c}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
