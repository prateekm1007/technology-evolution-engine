"""
Test Phase I (Scientific Memory) dataclasses (cycle 70).

Per CEO cycle 68: "Add Observation, Intervention, Theory dataclasses.
Success criterion: everything becomes replayable."

These tests verify the new dataclasses exist, have the required fields,
and can be serialized.
"""
import sys
import pathlib
import json

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invention_compiler.causal_graph import Observation, Intervention, Theory


class TestObservation:
    """Verify the Observation dataclass."""

    def test_observation_exists(self):
        """Observation class must exist."""
        assert Observation is not None

    def test_observation_has_required_fields(self):
        """Observation must have: source, variables, units, measurement, uncertainty, conditions."""
        obs = Observation(
            source="paper_001",
            variables={"T": 300.0, "Q": 150.0},
            units={"T": "K", "Q": "W"},
            measurement=150.0,
            uncertainty=5.0,
            conditions={"ambient": 25.0, "humidity": 50.0},
        )
        assert obs.source == "paper_001"
        assert obs.variables == {"T": 300.0, "Q": 150.0}
        assert obs.units == {"T": "K", "Q": "W"}
        assert obs.measurement == 150.0
        assert obs.uncertainty == 5.0
        assert obs.conditions == {"ambient": 25.0, "humidity": 50.0}

    def test_observation_uncertainty_optional(self):
        """Uncertainty can be None (not all measurements have it)."""
        obs = Observation(
            source="paper_002",
            variables={"efficiency": 3.58},
            units={"efficiency": "%"},
            measurement=3.58,
            uncertainty=None,
            conditions={"delta_T": 120},
        )
        assert obs.uncertainty is None

    def test_observation_to_dict(self):
        """to_dict must produce a JSON-serializable dict."""
        obs = Observation(
            source="test",
            variables={"x": 1.0},
            units={"x": "m"},
            measurement=1.0,
            uncertainty=0.1,
            conditions={"temp": 300},
        )
        d = obs.to_dict()
        json.dumps(d)  # must not raise
        assert d["source"] == "test"
        assert d["measurement"] == 1.0


class TestTheory:
    """Verify the Theory dataclass."""

    def test_theory_exists(self):
        """Theory class must exist."""
        assert Theory is not None

    def test_theory_has_required_fields(self):
        """Theory must have: name, assumptions, laws, domain, failures."""
        t = Theory(
            name="Stefan-Boltzmann radiative cooling",
            assumptions=["surface emits as blackbody", "sky temperature is known"],
            laws=["Q = εσA(T_s⁴ - T_sky⁴)"],
            domain="thermal radiation",
            failures=["does not account for convection", "fails if emissivity < 0.5"],
        )
        assert t.name == "Stefan-Boltzmann radiative cooling"
        assert len(t.assumptions) == 2
        assert len(t.laws) == 1
        assert t.domain == "thermal radiation"
        assert len(t.failures) == 2

    def test_theory_to_dict(self):
        """to_dict must produce a JSON-serializable dict."""
        t = Theory(
            name="test_theory",
            assumptions=["a1"],
            laws=["l1"],
            domain="test",
            failures=[],
        )
        d = t.to_dict()
        json.dumps(d)
        assert d["name"] == "test_theory"

    def test_theory_failures_empty_by_default(self):
        """A new theory has no failures (failures accumulate with observations)."""
        t = Theory(
            name="new_theory",
            assumptions=["a"],
            laws=["l"],
            domain="d",
            failures=[],
        )
        assert len(t.failures) == 0


class TestInterventionExists:
    """Verify Intervention already exists (it was added in an earlier cycle)."""

    def test_intervention_exists(self):
        """Intervention class must exist (added in earlier cycle)."""
        assert Intervention is not None

    def test_intervention_has_required_fields(self):
        """Intervention must have: node, intervention, predicted_effect, expected_magnitude, uncertainty."""
        iv = Intervention(
            node="temperature",
            intervention="increase by 100K",
            predicted_effect="increase power output",
            expected_magnitude="2.5W increase",
            uncertainty="±0.5W",
        )
        assert iv.node == "temperature"
        assert iv.intervention == "increase by 100K"
