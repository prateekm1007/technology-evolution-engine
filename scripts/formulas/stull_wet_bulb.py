"""
Stull wet-bulb formula (DR-7 formula execution).

Per F-051: the vaccine fridge package hand-typed T_wb values that
were wrong by ~7°C. This formula executes the Stull 2011 equation
as a callable function, diffed against the package's stated output.

Reference: Stull, R. (2011). "Wet-Bulb Temperature from Relative
Humidity and Air Temperature." Journal of Applied Meteorology and
Climatology, 50(11), 2267-2269. doi:10.1175/JAMC-D-11-0143.1

The formula (all trig in RADIANS):
  T_wb = T * atan(0.151977 * (RH + 8.313659)^0.5)
        + atan(T + RH)
        - atan(RH - 1.676331)
        + 0.00391838 * RH^1.5 * atan(0.023101 * RH)
        - 4.686035

Where:
  T = dry-bulb temperature in °C
  RH = relative humidity in %
  T_wb = wet-bulb temperature in °C

Valid range: T ∈ [-20°C, 50°C], RH ∈ [5%, 99%]
"""
import math
from typing import Dict, Any, Tuple


def stull_wet_bulb(T: float, RH: float) -> float:
    """Compute wet-bulb temperature from dry-bulb T (°C) and RH (%).

    All trigonometric functions are in RADIANS (this is the critical
    detail — the F-051 error was likely a degrees/radians confusion).

    Args:
        T: dry-bulb temperature in °C
        RH: relative humidity in % (0-100)

    Returns:
        T_wb: wet-bulb temperature in °C

    Raises:
        ValueError: if inputs are outside valid range
    """
    if T < -20 or T > 50:
        raise ValueError(f"T={T}°C outside valid range [-20, 50]")
    if RH < 5 or RH > 99:
        raise ValueError(f"RH={RH}% outside valid range [5, 99]")

    term1 = T * math.atan(0.151977 * (RH + 8.313659) ** 0.5)
    term2 = math.atan(T + RH)
    term3 = math.atan(RH - 1.676331)
    term4 = 0.00391838 * (RH ** 1.5) * math.atan(0.023101 * RH)
    term5 = 4.686035

    T_wb = term1 + term2 - term3 + term4 - term5
    return round(T_wb, 1)


def verify(inputs: Dict[str, Any], expected_output: float,
           tolerance: float = 0.5) -> Tuple[bool, float, str]:
    """Verify the Stull formula against a stated output.

    Args:
        inputs: {"T": 42, "RH": 25}
        expected_output: the package's stated T_wb value
        tolerance: acceptable diff (°C)

    Returns:
        (passed, computed_value, message)
    """
    T = inputs.get("T")
    RH = inputs.get("RH")
    if T is None or RH is None:
        return False, 0.0, f"Missing inputs: T={T}, RH={RH}"

    try:
        computed = stull_wet_bulb(float(T), float(RH))
    except ValueError as e:
        return False, 0.0, f"Input validation error: {e}"

    diff = abs(computed - expected_output)
    if diff <= tolerance:
        return True, computed, f"MATCH: computed={computed}°C, expected={expected_output}°C, diff={diff:.1f}°C"
    else:
        return False, computed, f"MISMATCH: computed={computed}°C, expected={expected_output}°C, diff={diff:.1f}°C (tolerance={tolerance}°C)"
