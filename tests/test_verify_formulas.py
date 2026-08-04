"""
Tests for the formula execution verifier (DR-7 / Layer 2).

Per DR-7: "Every package that derives a pass/fail threshold from a named
equation must ship that equation as a callable function alongside the
package, and the verifier calls it with the stated inputs and diffs
against the stated output."

These tests verify:
  1. The Stull wet-bulb formula computes correctly
  2. The Stefan-Boltzmann formula computes correctly
  3. The PCM latent heat formula computes correctly
  4. The verifier catches the F-051 errors (hand-typed values that were wrong)
  5. The verifier passes when values match
"""
import sys
import math
import pathlib
import subprocess
import json

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.formulas.stull_wet_bulb import stull_wet_bulb, verify as verify_stull
from scripts.formulas.stefan_boltzmann import (
    stefan_boltzmann_radiative_cooling, verify as verify_stefan
)
from scripts.formulas.pcm_latent_heat import (
    pcm_latent_heat_sizing, verify as verify_pcm
)


# ----------------------------------------------------------------------
# 1. Stull wet-bulb formula
# ----------------------------------------------------------------------

class TestStullWetBulb:
    def test_stull_reference_case(self):
        """Stull's own reference: T=20°C, RH=50% → T_wb≈13.7°C."""
        T_wb = stull_wet_bulb(20, 50)
        assert abs(T_wb - 13.7) < 0.5, f"Expected ~13.7°C, got {T_wb}°C"

    def test_stull_arid_case(self):
        """Arid case: T=42°C, RH=25% → T_wb≈25.8°C (NOT 19°C as the package stated)."""
        T_wb = stull_wet_bulb(42, 25)
        assert abs(T_wb - 25.8) < 1.0, f"Expected ~25.8°C, got {T_wb}°C"

    def test_stull_tropical_wet(self):
        """Tropical wet: T=32°C, RH=85% → T_wb≈29.8°C."""
        T_wb = stull_wet_bulb(32, 85)
        assert 28 < T_wb < 31, f"Expected ~29°C, got {T_wb}°C"

    def test_stull_catches_package_error(self):
        """The F-051 error: package stated T_wb=19°C for T=42, RH=25.
        Actual is ~25.8°C. The verifier should FAIL on the stated value."""
        passed, computed, msg = verify_stull({"T": 42, "RH": 25}, 19.0, 0.5)
        assert not passed, (
            f"Verifier should FAIL on the package's stated T_wb=19°C. "
            f"Computed={computed}°C, diff=6.8°C. Message: {msg}"
        )

    def test_stull_passes_corrected_value(self):
        """The corrected value (25.8°C) should pass verification."""
        passed, computed, msg = verify_stull({"T": 42, "RH": 25}, 25.8, 1.0)
        assert passed, f"Verifier should PASS on corrected T_wb=25.8°C. Message: {msg}"

    def test_stull_uses_radians_not_degrees(self):
        """The formula must use RADIANS for all trig functions.
        If degrees were used, the result would be completely wrong."""
        T_wb_radians = stull_wet_bulb(20, 50)
        # If someone used degrees, the result would be wildly different
        assert 10 < T_wb_radians < 18, (
            f"T_wb={T_wb_radians} — if this is outside 10-18, "
            f"trig functions may be in degrees instead of radians"
        )

    def test_stull_validates_inputs(self):
        """The formula should reject inputs outside valid range."""
        with pytest.raises(ValueError):
            stull_wet_bulb(60, 50)  # T > 50
        with pytest.raises(ValueError):
            stull_wet_bulb(20, 1)   # RH < 5


# ----------------------------------------------------------------------
# 2. Stefan-Boltzmann formula
# ----------------------------------------------------------------------

class TestStefanBoltzmann:
    def test_radiative_cooling_at_small_deltaT(self):
        """Small ΔT (4K) produces small cooling (~19W)."""
        Q = stefan_boltzmann_radiative_cooling(0.95, 1.0, 278, 282)
        assert Q < 0, f"Expected negative (cooling), got {Q}W"
        assert abs(Q - (-18.9)) < 1.0, f"Expected ~-19W, got {Q}W"

    def test_radiative_cooling_at_large_deltaT(self):
        """Large ΔT (20K, e.g., surface 5°C, sky -15°C) produces strong heat loss.
        T_surface=278K (5°C), T_sky=258K (-15°C). Surface is warmer than sky
        so it radiates energy outward — Q should be negative (net cooling)."""
        Q = stefan_boltzmann_radiative_cooling(0.95, 1.0, 278, 258)
        # Q = ε*σ*A*(T_surface^4 - T_sky^4). T_surface > T_sky means T_surface^4 > T_sky^4
        # so Q is POSITIVE (surface radiates MORE than it absorbs).
        # Wait — that's the physics convention: positive Q = net heat transfer FROM surface.
        # The sign convention in the formula: Q = ε*σ*A*(T_surface^4 - T_sky^4)
        # If T_surface > T_sky, Q is POSITIVE = surface is NET RADIATING (cooling).
        # If T_surface < T_sky, Q is NEGATIVE = surface is NET ABSORBING (heating).
        # So for cooling, we want Q > 0 (surface loses energy).
        assert Q > 0, f"Expected positive (surface cooling), got {Q}W"
        assert abs(Q) > 50, f"Expected >50W cooling, got {Q}W"

    def test_stefan_boltzmann_catches_package_error(self):
        """The package stated Q_rad=-190W for ΔT=4K. Actual is -18.9W.
        The verifier should FAIL on the stated value."""
        passed, computed, msg = verify_stefan(
            {"epsilon": 0.95, "A": 1.0, "T_surface": 278, "T_sky": 282},
            -190.0, 10.0
        )
        assert not passed, (
            f"Verifier should FAIL on the package's stated Q=-190W. "
            f"Computed={computed}W. Message: {msg}"
        )

    def test_stefan_boltzmann_validates_inputs(self):
        """The formula should reject invalid inputs."""
        with pytest.raises(ValueError):
            stefan_boltzmann_radiative_cooling(1.5, 1.0, 278, 282)  # ε > 1
        with pytest.raises(ValueError):
            stefan_boltzmann_radiative_cooling(0.95, -1, 278, 282)  # A < 0
        with pytest.raises(ValueError):
            stefan_boltzmann_radiative_cooling(0.95, 1.0, -278, 282)  # T < 0


# ----------------------------------------------------------------------
# 3. PCM latent heat formula
# ----------------------------------------------------------------------

class TestPCMLatentHeat:
    def test_pcm_sizing_basic(self):
        """Q=14.4W, t=14h, L=180000 J/kg → m=4.032 kg."""
        m = pcm_latent_heat_sizing(14.4, 14, 180000)
        assert abs(m - 4.032) < 0.01, f"Expected 4.032 kg, got {m} kg"

    def test_pcm_catches_package_error(self):
        """The package initially stated m_pcm=0.7 kg. Actual is 4.032 kg.
        The verifier should FAIL on the stated value."""
        passed, computed, msg = verify_pcm(
            {"Q_daily": 14.4, "t_hours": 14, "L_pcm": 180000},
            0.7, 0.1
        )
        assert not passed, (
            f"Verifier should FAIL on the package's stated m=0.7kg. "
            f"Computed={computed}kg. Message: {msg}"
        )

    def test_pcm_passes_corrected_value(self):
        """The corrected value (4.032 kg) should pass verification."""
        passed, computed, msg = verify_pcm(
            {"Q_daily": 14.4, "t_hours": 14, "L_pcm": 180000},
            4.032, 0.1
        )
        assert passed, f"Verifier should PASS on corrected m=4.032kg. Message: {msg}"

    def test_pcm_scales_linearly_with_heat_load(self):
        """Double the heat load → double the PCM mass."""
        m1 = pcm_latent_heat_sizing(10, 14, 180000)
        m2 = pcm_latent_heat_sizing(20, 14, 180000)
        assert abs(m2 - 2 * m1) < 0.01, f"Doubling Q should double m: {m1} vs {m2}"


# ----------------------------------------------------------------------
# 4. Formula verifier CLI
# ----------------------------------------------------------------------

class TestFormulaVerifierCLI:
    def test_cli_runs_and_reports_results(self):
        """The CLI should run and report pass/fail counts."""
        result = subprocess.run(
            [sys.executable, "scripts/verify_formulas.py"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        # Exit code 1 because some test cases intentionally fail
        assert result.returncode == 1, f"Expected exit 1 (some failures), got {result.returncode}"
        assert "FORMULA EXECUTION VERIFIER" in result.stdout
        assert "PASS" in result.stdout
        assert "FAIL" in result.stdout

    def test_cli_json_output(self):
        """The --json flag should emit valid JSON."""
        result = subprocess.run(
            [sys.executable, "scripts/verify_formulas.py", "--json"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        output = json.loads(result.stdout)
        assert output["verifier"] == "scripts/verify_formulas.py"
        assert output["total_formulas"] == 7
        assert output["passed"] == 4
        assert output["failed"] == 3
        assert output["status"] == "FAIL"

    def test_cli_catches_stull_error(self):
        """The CLI should report the Stull wet-bulb error (6.8°C diff)."""
        result = subprocess.run(
            [sys.executable, "scripts/verify_formulas.py"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert "stull_wet_bulb" in result.stdout
        assert "6.8" in result.stdout or "6.80" in result.stdout

    def test_cli_catches_pcm_error(self):
        """The CLI should report the PCM mass error (3.3kg diff)."""
        result = subprocess.run(
            [sys.executable, "scripts/verify_formulas.py"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert "pcm_latent_heat" in result.stdout
        assert "3.332" in result.stdout or "3.3" in result.stdout
