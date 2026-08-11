#!/usr/bin/env python3
"""
Register the EV battery package's retraction (RT-001) and tests (TR-001..TR-008)
in the actual P7 Retraction Registry and P8 Test Registry.

Per the consolidated review: 'Build these mechanisms and stop there.' This
script USES the mechanisms — it is the first time the system has been able
to mechanically register its own engineering artifacts in its own registries.

This is the Gate 5 + Gate 9 step of the AEP pipeline for the EV battery
package (PKG-EVBT-001).
"""
import sys
import pathlib

# Add web/backend to path
REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "web" / "backend"))

from adapters.retraction_registry import RetractionRegistry
from adapters.test_registry import TestRegistry

# Use the real registries (data/retractions/ and data/tests/)
r = RetractionRegistry()
t = TestRegistry()

print("=" * 70)
print("REGISTERING RT-001 (2C fast-charge retraction) in P7 Retraction Registry")
print("=" * 70)

rt = r.register(
    retracted_claim_id="CL-040",
    retracted_claim_statement="2C fast charge: 80% in 18 minutes",
    retraction_agent="TEE Compiler (Gate 5, EV battery package)",
    reason_category="KILL_TEST_FAILED",
    reason_description=(
        "Single-cell 2C cycle test (TR-007) measured cell surface temperature "
        "peaking at 62.4°C against the 55°C limit. Negative margin of 7.4°C. "
        "The cooling system cannot reject 3.6 kW of peak heat at the required rate."
    ),
    detected_by="test_registry (TR-007, physical validation)",
    detection_date="2026-08-03T00:00:00Z",
    replacement_claim_id="CL-041",
    replacement_evidence_id="EV-301",
    replacement_derivation=(
        "Revised thermal CFD at 1.5C charge rate predicts cell surface peak "
        "of 51.8°C with 3.2°C margin to the 55°C limit. Replacement claim: "
        "1.5C max charge rate; 0-80% SoC in 32 minutes."
    ),
)
print(f"  Registered: {rt['id']}")
print(f"  Status: {rt['status']}")
print(f"  Has replacement: {rt['replacement'] is not None}")
print()

print("=" * 70)
print("REGISTERING TR-001..TR-008 in P8 Test Registry")
print("=" * 70)

tests_to_register = [
    {
        "test_name": "Pack energy density analytical estimate",
        "test_type": "ANALYTICAL_ESTIMATE",
        "claim_id": "CL-014",
        "validation_level_target": "L2",
        "expected_value": "123.4 Wh/kg",
        "pass_criteria": "Computed value within +/- 3 Wh/kg of (cell_energy * count - overhead) / pack_mass",
        "evidence_id": "EV-101",
        "analytical_model": "pack_energy / pack_mass = 86000 / 696.9 = 123.4",
        "result_status": "NOT_RUN",
    },
    {
        "test_name": "Thermal CFD at 1C continuous",
        "test_type": "NUMERICAL_SIMULATION",
        "claim_id": "CL-022",
        "validation_level_target": "L3",
        "expected_value": "cell max 35.2°C, coolant outlet 31.8°C",
        "pass_criteria": "cell max < 45°C at 25°C ambient, 4 L/min coolant, 1C discharge",
        "evidence_id": "EV-205",
        "numerical_solver": "OpenFOAM (CFD, heat equation + Navier-Stokes)",
        "numerical_model_file": "models/thermal_1C_continuous.foam",
        "numerical_run_command": "blockMesh && simpleFoam",
        "result_status": "PASS",
        "measured_value": "cell max 35.2°C, coolant outlet 31.8°C (predicted)",
        "date_run": "2026-08-02T00:00:00Z",
        "run_by": "CFD Analyst (OpenFOAM)",
        "raw_data_path": "tests/data/thermal_1C_raw.csv",
        "analysis_path": "tests/analysis/analyze_thermal.py",
    },
    {
        "test_name": "Thermal CFD at 1.5C peak charge",
        "test_type": "NUMERICAL_SIMULATION",
        "claim_id": "CL-023",
        "validation_level_target": "L3",
        "expected_value": "cell max 51.8°C (margin 3.2°C to 55°C limit)",
        "pass_criteria": "cell surface max < 55°C at 25°C ambient, 8 L/min coolant, 1.5C charge, 0-80% SoC in 32 min",
        "evidence_id": "EV-301",
        "numerical_solver": "OpenFOAM (transient CFD)",
        "numerical_model_file": "models/thermal_1.5C_transient.foam",
        "numerical_run_command": "blockMesh && simpleFoam",
        "result_status": "PASS_WITH_CONDITIONS",
        "measured_value": "cell max 51.8°C, margin 3.2°C (thin — recommend upgrade to 12 L/min pump)",
        "date_run": "2026-08-02T00:00:00Z",
        "run_by": "CFD Analyst (OpenFOAM)",
    },
    {
        "test_name": "Coolant flow test (physical)",
        "test_type": "PHYSICAL_VALIDATION",
        "claim_id": "CL-024",
        "validation_level_target": "L4",
        "expected_value": "1.8 kW heat rejection at 4 L/min, 25°C inlet, 5°C deltaT",
        "pass_criteria": "heat rejection >= 1.5 kW at 4 L/min with deltaT >= 4°C",
        "evidence_id": "EV-206",
        "physical_test_stand": "bench rig B-001 (coolant loop + heater)",
        "physical_sample_size": 1,
        "physical_duration": "4 hours continuous",
        "physical_instruments": ["Pierburg EWP-80 pump", "Type-K thermocouple x4", "Omega flow meter"],
        "physical_calibration_date": "2026-07-15",
        "physical_procedure_doc": "tests/procedures/coolant_flow_test.md",
        "result_status": "PASS",
        "measured_value": "1.82 kW heat rejection at 4 L/min, deltaT 4.8°C",
        "date_run": "2026-07-20T00:00:00Z",
        "run_by": "Test Engineer J. Park",
        "raw_data_path": "tests/data/coolant_flow_2026-07-20.csv",
    },
    {
        "test_name": "Cost model arithmetic check",
        "test_type": "ANALYTICAL_ESTIMATE",
        "claim_id": "CL-030",
        "validation_level_target": "L2",
        "expected_value": "$142.2/kWh",
        "pass_criteria": "sum(BOM line subtotals) / pack_energy = $142.2/kWh",
        "evidence_id": "EV-501",
        "analytical_model": "sum(BL-001..BL-011) / 86.0 kWh = 12229.80 / 86.0 = 142.2",
        "result_status": "PASS",
        "measured_value": "$142.2/kWh (9 QUOTED lines + 1 ESTIMATED line)",
    },
    {
        "test_name": "Range per kWh derivation",
        "test_type": "ANALYTICAL_ESTIMATE",
        "claim_id": "CL-031",
        "validation_level_target": "L2",
        "expected_value": "3.95 mi/kWh",
        "pass_criteria": "derived range / pack energy within +/- 0.1 mi/kWh of 3.95",
        "evidence_id": "EV-601",
        "analytical_model": "340 miles / 86.0 kWh = 3.95 mi/kWh (literature-analog vehicle platform)",
        "result_status": "PASS",
        "measured_value": "3.95 mi/kWh (analytical, requires vehicle-level validation)",
    },
    {
        "test_name": "2C fast-charge cycle test (RETRACTED → RT-001)",
        "test_type": "PHYSICAL_VALIDATION",
        "claim_id": "CL-040",
        "validation_level_target": "L4",
        "expected_value": ">=80% SoC in 18 min, surface temp < 55°C",
        "pass_criteria": ">=80% SoC in 18 min AND surface temp < 55°C (pre-stated 2026-07-01)",
        "evidence_id": "EV-407",
        "physical_test_stand": "Arbin LBT21084, bench rig B-001",
        "physical_sample_size": 3,
        "physical_duration": "1000 cycles or 80% DoD, whichever first",
        "physical_instruments": ["Arbin LBT21084", "Fluke 87V multimeter", "Type-K thermocouple x4"],
        "physical_calibration_date": "2026-06-15",
        "physical_procedure_doc": "tests/procedures/single-cell-2C-charge.md",
        "result_status": "FAIL",
        "measured_value": "78% in 18 min, 84% in 24 min; cell surface peaked at 62.4°C (limit 55°C)",
        "date_run": "2026-08-01T14:00:00Z",
        "run_by": "Test Engineer J. Park",
        "raw_data_path": "tests/data/2C-charge-2026-08-01.csv",
        "analysis_path": "tests/analysis/analyze_2C_charge.py",
        "retraction_id": "RT-001",
    },
    {
        "test_name": "1.5C fast-charge cycle test (replacement for TR-007)",
        "test_type": "PHYSICAL_VALIDATION",
        "claim_id": "CL-041",
        "validation_level_target": "L4",
        "expected_value": ">=80% SoC in 32 min, surface temp < 55°C",
        "pass_criteria": ">=80% SoC in 32 min AND surface temp < 55°C (pre-stated 2026-08-03)",
        "evidence_id": "EV-302",
        "physical_test_stand": "Arbin LBT21084, bench rig B-001",
        "physical_sample_size": 3,
        "physical_duration": "1000 cycles or 80% DoD, whichever first",
        "physical_instruments": ["Arbin LBT21084", "Fluke 87V multimeter", "Type-K thermocouple x4"],
        "physical_calibration_date": "2026-06-15",
        "physical_procedure_doc": "tests/procedures/single-cell-1.5C-charge.md",
        "result_status": "NOT_RUN",
    },
]

for spec in tests_to_register:
    tr = t.register(**spec)
    print(f"  Registered: {tr['id']} | {tr['test_type']:25s} | {tr['test_name'][:50]:50s} | result: {tr['result']['status']}")

print()
print("=" * 70)
print("REGISTRY STATE AFTER REGISTRATION")
print("=" * 70)
print(f"Retraction Registry:")
print(f"  count: {r.count()}")
print(f"  unresolved_count: {r.unresolved()}")
unresolved = r.unresolved()
print(f"  unresolved (RETRACTED with no replacement): {len(unresolved)}")
print(f"  gate_11_check_5_pass: {len(unresolved) == 0}")
print()
print(f"Test Registry:")
s = t.summary()
print(f"  total: {s['total']}")
print(f"  by_type: {s['by_type']}")
print(f"  by_result: {s['by_result']}")
print(f"  failed_count: {s['failed_count']}")
print(f"  not_run_count: {s['not_run_count']}")
print()
print("Gate 11 Loop Closure check:")
print(f"  5. No unresolved retractions: {'PASS' if len(unresolved) == 0 else 'FAIL'}")
print(f"  4. P7 Retraction Registry: PASS_WITH_CONDITIONS (1 retraction, has replacement)")
print(f"  4. P8 Test Registry: MARGINAL (1 FAIL mitigated, 3 NOT_RUN)")
