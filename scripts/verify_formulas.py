#!/usr/bin/env python3
"""
verify_formulas.py — Formula execution verifier (DR-7 / Layer 2).

Per DR-7: "Every package that derives a pass/fail threshold from a named
equation must ship that equation as a callable function alongside the
package, and the verifier calls it with the stated inputs and diffs
against the stated output."

Per DR-15: edges with mechanism_status=ASSERTED and a formula field
can be promoted to VERIFIED if the formula's computed output matches
the stated output within tolerance.

This is the single highest-leverage build: it converts the causal graph
from a schema into a reasoning engine. Without formula execution, the
graph is a knowledge store. With formula execution, the graph produces
verified predictions.

Usage:
    python scripts/verify_formulas.py                    # verify all registered formulas
    python scripts/verify_formulas.py --json             # JSON output
    python scripts/verify_formulas.py --promote          # promote ASSERTED → VERIFIED on match

Exit codes:
    0 = all formulas verified (PASS)
    1 = one or more formulas fail (FAIL)
"""
import sys
import pathlib
import argparse
import importlib
from typing import Dict, Any, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Import the formula modules
from scripts.formulas.stull_wet_bulb import stull_wet_bulb, verify as verify_stull
from scripts.formulas.stefan_boltzmann import (
    stefan_boltzmann_radiative_cooling, verify as verify_stefan
)
from scripts.formulas.pcm_latent_heat import (
    pcm_latent_heat_sizing, verify as verify_pcm
)


# Registry of all formulas the verifier can execute.
# Each entry: (formula_name, verify_function, test_cases)
# Test cases are (inputs, expected_output, tolerance, description)
FORMULA_REGISTRY = {
    "stull_wet_bulb": {
        "verify_fn": verify_stull,
        "callable": stull_wet_bulb,
        "test_cases": [
            # Stull's own reference case: T=20°C, RH=50% → T_wb≈13.7°C
            ({"T": 20, "RH": 50}, 13.7, 0.5, "Stull reference case (T=20, RH=50)"),
            # The vaccine fridge package's Arid case: T=42, RH=25
            # Package stated T_wb=19°C. Actual (radians): ~25.8°C.
            # This SHOULD FAIL — the package's hand-typed value was wrong.
            ({"T": 42, "RH": 25}, 19.0, 0.5, "Vaccine fridge Arid case (T=42, RH=25, stated T_wb=19)"),
            # Correct Arid case (computed)
            ({"T": 42, "RH": 25}, 25.8, 1.0, "Vaccine fridge Arid case (corrected T_wb=25.8)"),
            # Tropical wet case: T=32, RH=85
            ({"T": 32, "RH": 85}, 29.0, 1.0, "Tropical wet case (T=32, RH=85)"),
        ],
    },
    "stefan_boltzmann": {
        "verify_fn": verify_stefan,
        "callable": stefan_boltzmann_radiative_cooling,
        "test_cases": [
            # Vaccine fridge: ε=0.95, A=1.0, T_surface=278K(5°C), T_sky=282K(9°C)
            # Package stated Q_rad = -190 W/m²
            ({"epsilon": 0.95, "A": 1.0, "T_surface": 278, "T_sky": 282}, -190.0, 10.0,
             "Vaccine fridge radiant cooling (ε=0.95, T=5°C, Tsky=9°C)"),
        ],
    },
    "pcm_latent_heat": {
        "verify_fn": verify_pcm,
        "callable": pcm_latent_heat_sizing,
        "test_cases": [
            # Vaccine fridge: Q=14.4W, t=14h, L=180000 J/kg
            # Package stated m_pcm = 0.7 kg (initial, later corrected to 1.8)
            ({"Q_daily": 14.4, "t_hours": 14, "L_pcm": 180000}, 0.7, 0.1,
             "Vaccine fridge PCM initial (Q=14.4W, t=14h, L=180kJ/kg, stated 0.7kg)"),
            # Corrected value
            ({"Q_daily": 14.4, "t_hours": 14, "L_pcm": 180000}, 4.032, 0.1,
             "Vaccine fridge PCM corrected (Q=14.4W, t=14h, L=180kJ/kg, actual 4.032kg)"),
        ],
    },
}


def run_all_verifications() -> List[Dict[str, Any]]:
    """Run all formula verifications and return results.

    Each result is a dict with:
      formula_name, test_description, inputs, expected, computed,
      diff, tolerance, passed, message
    """
    results = []

    for formula_name, spec in FORMULA_REGISTRY.items():
        verify_fn = spec["verify_fn"]

        for inputs, expected, tolerance, description in spec["test_cases"]:
            passed, computed, message = verify_fn(inputs, expected, tolerance)
            results.append({
                "formula_name": formula_name,
                "test_description": description,
                "inputs": inputs,
                "expected_output": expected,
                "computed_output": computed,
                "diff": abs(computed - expected) if computed else None,
                "tolerance": tolerance,
                "passed": passed,
                "message": message,
            })

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Formula execution verifier (DR-7). Executes physics formulas and diffs against stated outputs."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--promote", action="store_true",
                        help="Promote ASSERTED edges to VERIFIED on match (future: update causal graph)")
    args = parser.parse_args()

    results = run_all_verifications()
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])

    if args.json:
        import json
        output = {
            "verifier": "scripts/verify_formulas.py",
            "total_formulas": len(results),
            "passed": passed,
            "failed": failed,
            "results": results,
            "status": "PASS" if failed == 0 else "FAIL",
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print("=" * 70)
        print("FORMULA EXECUTION VERIFIER (DR-7 / Layer 2)")
        print("=" * 70)
        print()

        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"  {status} | {r['formula_name']} | {r['test_description']}")
            print(f"    Inputs: {r['inputs']}")
            print(f"    Expected: {r['expected_output']}, Computed: {r['computed_output']}")
            print(f"    Diff: {r['diff']}, Tolerance: {r['tolerance']}")
            print(f"    Message: {r['message']}")
            print()

        print("=" * 70)
        if failed == 0:
            print(f"OVERALL STATUS: PASS ({passed}/{len(results)} formulas verified)")
        else:
            print(f"OVERALL STATUS: FAIL ({passed}/{len(results)} passed, {failed} failed)")
            print()
            print("  Failed formulas indicate hand-typed values that don't match")
            print("  the computed physics. Per DR-7, these must be corrected")
            print("  before the package can ship.")
        print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
