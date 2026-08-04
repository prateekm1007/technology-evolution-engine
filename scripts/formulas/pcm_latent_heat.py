"""
PCM latent heat sizing formula (DR-7 formula execution).

Per F-051: the vaccine fridge package hand-typed PCM mass values
that drifted (0.7→1.2→1.8 kg). This formula executes the latent
heat sizing equation as a callable function.

m_pcm = Q_daily * t / L_pcm

Where:
  Q_daily = daily heat load (W)
  t = duration that PCM must buffer (seconds)
  L_pcm = latent heat of fusion (J/kg)

Returns: required PCM mass (kg) to buffer the heat load for the duration.
"""
from typing import Dict, Any, Tuple


def pcm_latent_heat_sizing(Q_daily: float, t_hours: float, L_pcm: float) -> float:
    """Compute required PCM mass to buffer a heat load.

    Args:
        Q_daily: daily heat load in Watts
        t_hours: hours the PCM must buffer
        L_pcm: latent heat of fusion in J/kg

    Returns:
        m_pcm: required PCM mass in kg
    """
    if Q_daily <= 0:
        raise ValueError(f"Q_daily={Q_daily} must be positive")
    if t_hours <= 0:
        raise ValueError(f"t_hours={t_hours} must be positive")
    if L_pcm <= 0:
        raise ValueError(f"L_pcm={L_pcm} must be positive")

    t_seconds = t_hours * 3600
    Q_total = Q_daily * t_seconds
    m_pcm = Q_total / L_pcm
    return round(m_pcm, 3)


def verify(inputs: Dict[str, Any], expected_output: float,
           tolerance: float = 0.1) -> Tuple[bool, float, str]:
    """Verify the PCM sizing formula against a stated output.

    Args:
        inputs: {"Q_daily": 14.4, "t_hours": 14, "L_pcm": 180000}
        expected_output: the package's stated m_pcm value (kg)
        tolerance: acceptable diff (kg)

    Returns:
        (passed, computed_value, message)
    """
    try:
        computed = pcm_latent_heat_sizing(
            float(inputs["Q_daily"]),
            float(inputs["t_hours"]),
            float(inputs["L_pcm"]),
        )
    except (KeyError, ValueError) as e:
        return False, 0.0, f"Input error: {e}"

    diff = abs(computed - expected_output)
    if diff <= tolerance:
        return True, computed, f"MATCH: computed={computed}kg, expected={expected_output}kg, diff={diff:.3f}kg"
    else:
        return False, computed, f"MISMATCH: computed={computed}kg, expected={expected_output}kg, diff={diff:.3f}kg (tolerance={tolerance}kg)"
