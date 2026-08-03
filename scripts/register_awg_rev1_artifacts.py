#!/usr/bin/env python3
"""
Register the revised AWG package's tests (TR-017, TR-018) in P8 Test Registry.

PKG-AWG-002 is the revision of PKG-AWG-001 (which was REJECTED). The
revision doubles the adsorbent from 2 kg to 4 kg, raising yield from
1.6 to 3.2 L/day/m² (PASS R-001). This script registers the two new
analytical tests that verify the revised numbers.
"""
import sys
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "web" / "backend"))

from adapters.test_registry import TestRegistry

t = TestRegistry()

print("=" * 70)
print("REGISTERING TR-017, TR-018 in P8 Test Registry (PKG-AWG-002)")
print("=" * 70)

tr017 = t.register(
    test_name="R-001 yield check (revised, 4 kg adsorbent)",
    test_type="ANALYTICAL_ESTIMATE",
    claim_id="CL-058",
    validation_level_target="L2",
    expected_value=">= 3.0 L/day/m²",
    pass_criteria="corrected yield >= 3.0 L/day/m² (adsorbent-mass-limited)",
    evidence_id="EV-209",
    analytical_model="4kg × 2.8 L/kg/day × 0.57 / 2m² = 3.192 -> 3.2 L/day/m²",
    result_status="PASS",
    measured_value="3.2 L/day/m² (PASS R-001, margin 6.7%)",
)
print(f"  {tr017['id']} | {tr017['test_type']} | {tr017['result']['status']}")

tr018 = t.register(
    test_name="R-005 cost check (revised)",
    test_type="ANALYTICAL_ESTIMATE",
    claim_id="CL-059",
    validation_level_target="L2",
    expected_value="< $1,200",
    pass_criteria="total cost < $1,200 (DESIRABLE, not blocking)",
    evidence_id="EV-210",
    analytical_model="340+360+95+95+28+145+60+215+42+35+52 = 1267",
    result_status="PASS_WITH_CONDITIONS",
    measured_value="$1,267 (exceeds $1,200 by $67; R-005 is DESIRABLE so non-blocking)",
)
print(f"  {tr018['id']} | {tr018['test_type']} | {tr018['result']['status']}")

print()
print("=" * 70)
print("REGISTRY STATE AFTER REGISTRATION")
print("=" * 70)
s = t.summary()
print(f"  total: {s['total']}")
print(f"  by_type: {s['by_type']}")
print(f"  by_result: {s['by_result']}")
print(f"  failed_count: {s['failed_count']}")
print(f"  not_run_count: {s['not_run_count']}")
