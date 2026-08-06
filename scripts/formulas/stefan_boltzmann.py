"""
Stefan-Boltzmann radiative cooling formula (DR-7 formula execution).

Per F-051: the vaccine fridge package cited the Stefan-Boltzmann
equation but hand-typed the result. This formula executes it as
a callable function, diffed against the package's stated output.

Q = ε * σ * A * (T_surface^4 - T_sky^4)

Where:
  ε = emissivity of surface (0-1)
  σ = Stefan-Boltzmann constant = 5.67 × 10^-8 W/m²·K⁴
  A = radiating surface area (m²)
  T_surface = surface temperature (K)
  T_sky = effective sky temperature (K)

Negative Q means the surface is LOSING heat (cooling).
"""
import math
from typing import Dict, Any, Tuple

STEFAN_BOLTZMANN = 5.67e-8  # W/m²·K⁴


def stefan_boltzmann_radiative_cooling(
    epsilon: float, A: float, T_surface: float, T_sky: float
) -> float:
    """Compute radiative heat transfer (W).

    Negative = net cooling (surface loses heat to sky).
    Positive = net heating (sky heats surface).

    Args:
        epsilon: emissivity (0-1)
        A: surface area (m²)
        T_surface: surface temperature (K)
        T_sky: effective sky temperature (K)

    Returns:
        Q: radiative heat transfer in Watts (negative = cooling)
    """
    if not 0 < epsilon <= 1:
        raise ValueError(f"epsilon={epsilon} outside (0, 1]")
    if A <= 0:
        raise ValueError(f"A={A} must be positive")
    if T_surface <= 0 or T_sky <= 0:
        raise ValueError(f"Temperatures must be positive Kelvin: T_surface={T_surface}, T_sky={T_sky}")

    Q = epsilon * STEFAN_BOLTZMANN * A * (T_surface ** 4 - T_sky ** 4)
    return round(Q, 1)


def verify(inputs: Dict[str, Any], expected_output: float,
           tolerance: float = 10.0) -> Tuple[bool, float, str]:
    """Verify the Stefan-Boltzmann formula against a stated output.

    Args:
        inputs: {"epsilon": 0.95, "A": 1.0, "T_surface": 278, "T_sky": 282}
        expected_output: the package's stated Q value (W)
        tolerance: acceptable diff (W)

    Returns:
        (passed, computed_value, message)
    """
    try:
        computed = stefan_boltzmann_radiative_cooling(
            float(inputs["epsilon"]),
            float(inputs["A"]),
            float(inputs["T_surface"]),
            float(inputs["T_sky"]),
        )
    except (KeyError, ValueError) as e:
        return False, 0.0, f"Input error: {e}"

    diff = abs(computed - expected_output)
    if diff <= tolerance:
        return True, computed, f"MATCH: computed={computed}W, expected={expected_output}W, diff={diff:.1f}W"
    else:
        return False, computed, f"MISMATCH: computed={computed}W, expected={expected_output}W, diff={diff:.1f}W (tolerance={tolerance}W)"
