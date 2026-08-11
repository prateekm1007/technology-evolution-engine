"""Tests for cycle 206: materials database + independent measurement."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_materials_database_has_real_data():
    """Materials database has real published thermoelectric data."""
    from scripts.materials_database import MATERIALS_DATABASE, get_material
    assert len(MATERIALS_DATABASE) >= 5
    bi2te3 = get_material("Bi2Te3")
    assert bi2te3 is not None
    assert 100e-6 < bi2te3.seebeck_coefficient < 500e-6  # 100-500 µV/K
    assert 0.5 < bi2te3.zt < 2.0  # realistic ZT


def test_materials_database_has_multiple_families():
    """Database covers multiple thermoelectric families."""
    from scripts.materials_database import MATERIALS_DATABASE
    families = set(m.family for m in MATERIALS_DATABASE.values())
    assert len(families) >= 4  # at least 4 families


def test_material_parameters_match_published():
    """Bi2Te3 parameters match Snyder & Toberer 2008."""
    from scripts.materials_database import get_material
    m = get_material("Bi2Te3")
    assert abs(m.seebeck_coefficient - 200e-6) < 10e-6  # ~200 µV/K
    assert abs(m.electrical_conductivity - 1e5) < 0.5e5  # ~1e5 S/m
    assert abs(m.thermal_conductivity - 1.5) < 0.5  # ~1.5 W/(m·K)
    assert 0.5 < m.zt < 1.5  # ~0.93


def test_independent_measurement_is_independent():
    """Independent measurement uses a different code path from forward model."""
    from scripts.independent_measurement import IndependentMeasurement
    from scripts.forward_model import ForwardModel
    from scripts.materials_database import get_material_parameters
    from scripts.artifact_generator import Configuration, Component

    params = get_material_parameters("Bi2Te3")
    comp = Component(material="Bi2Te3", role="thermoelectric", parameters=params)
    config = Configuration(config_id="TEST", spec_objective="test",
                           domain="thermoelectric", components=[comp])

    fm = ForwardModel()
    im = IndependentMeasurement()

    pred = fm.predict(config)
    meas = im.measure(config, "Bi2Te3")

    # The measurement must be from a DIFFERENT code path
    assert meas.independent_of_forward_model
    # The values must DIFFER (different physics)
    assert pred.predicted_properties["ZT"] != meas.measured_zt
    # Both must be in physical range
    assert 0 < pred.predicted_properties["ZT"] < 5
    assert 0 < meas.measured_zt < 5


def test_independent_measurement_residual_is_nonzero():
    """The predicted-vs-measured residual is non-zero (real physics differences)."""
    from scripts.independent_measurement import IndependentMeasurement
    from scripts.forward_model import ForwardModel
    from scripts.materials_database import get_material_parameters
    from scripts.artifact_generator import Configuration, Component

    params = get_material_parameters("Bi2Te3")
    comp = Component(material="Bi2Te3", role="thermoelectric", parameters=params)
    config = Configuration(config_id="TEST", spec_objective="test",
                           domain="thermoelectric", components=[comp])

    fm = ForwardModel()
    im = IndependentMeasurement()

    pred = fm.predict(config)
    meas = im.measure(config, "Bi2Te3")

    residual = pred.predicted_properties["ZT"] - meas.measured_zt
    assert abs(residual) > 0.01, \
        f"Residual must be non-zero (different physics). Got: {residual}"


def test_independent_measurement_includes_corrections():
    """Independent measurement includes contact resistance, grain boundary, temp corrections."""
    from scripts.independent_measurement import IndependentMeasurement
    from scripts.materials_database import get_material_parameters
    from scripts.artifact_generator import Configuration, Component

    params = get_material_parameters("Bi2Te3")
    comp = Component(material="Bi2Te3", role="thermoelectric", parameters=params)
    config = Configuration(config_id="TEST", spec_objective="test",
                           domain="thermoelectric", components=[comp])

    im = IndependentMeasurement()
    meas = im.measure(config, "Bi2Te3")

    assert meas.contact_resistance_ohm > 0, "Contact resistance must be applied"
    assert meas.grain_boundary_factor > 1.0, "Grain boundary factor must increase κ"
    assert "contact" in meas.method.lower(), "Method must mention contact resistance"
    assert "grain" in meas.method.lower(), "Method must mention grain boundary"


def test_vertical_slice_uses_independent_measurement():
    """The vertical slice uses IndependentMeasurement (not MeasurementInstrument)."""
    # Read the source to verify
    source = Path(__file__).resolve().parents[1] / "scripts" / "vertical_slice_thermal.py"
    content = source.read_text()
    assert "IndependentMeasurement" in content, \
        "Vertical slice must use IndependentMeasurement (not MeasurementInstrument)"
    assert "independent_measurement" in content, \
        "Vertical slice must import from independent_measurement"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))


def test_all_materials_zt_consistent():
    """Every material's stored S, σ, κ must reproduce its stated ZT within 0.5 at stated T.

    Per auditor finding (cycle 206): SnSe stored values gave ZT=26 (not 2.6),
    which locked out the best real material via the F-100 veto. This test
    prevents data provenance bugs.
    """
    from scripts.materials_database import MATERIALS_DATABASE
    for name, m in MATERIALS_DATABASE.items():
        computed_zt = m.seebeck_coefficient**2 * m.electrical_conductivity * m.temperature / m.thermal_conductivity
        diff = abs(computed_zt - m.zt)
        assert diff < 0.5, \
            f"{name}: computed ZT={computed_zt:.2f} but published ZT={m.zt:.2f} (diff={diff:.2f}). " \
            f"Stored S, σ, κ, T must reproduce the published ZT."


def test_snse_not_locked_out_by_veto():
    """SnSe (ZT=2.6) must NOT be vetoed by the physical plausibility checker.

    Per auditor finding: SnSe is the record-holding thermoelectric. If its
    stored parameters produce ZT > 5, the F-100 veto locks it out — a real
    high-performing material rejected by the system.
    """
    from scripts.materials_database import get_material_parameters
    from scripts.forward_model import ForwardModel
    from scripts.physical_plausibility import PhysicalPlausibilityChecker
    from scripts.artifact_generator import Configuration, Component

    params = get_material_parameters("SnSe")
    comp = Component(material="SnSe", role="thermoelectric", parameters=params)
    config = Configuration(config_id="TEST-SNSE", spec_objective="test",
                           domain="thermoelectric", components=[comp])

    fm = ForwardModel()
    pred = fm.predict(config)
    ZT = pred.predicted_properties.get("ZT", 0)

    checker = PhysicalPlausibilityChecker()
    result = checker.check_prediction(pred.predicted_properties)

    assert ZT <= 5.0, f"SnSe ZT={ZT:.2f} exceeds physical max — would be vetoed"
    assert not result.vetoed, f"SnSe vetoed by plausibility checker — best real material locked out"


def test_search_space_includes_all_thermoelectric_materials():
    """The search space must include ALL thermoelectric materials from the DB.

    Per auditor (cycle 208): 'add a test asserting the generator can actually
    produce a SnSe/PbTe candidate when the spec targets high-temperature
    thermoelectrics, not just evaluate them if hand-selected.'
    """
    from scripts.artifact_generator import ArtifactGenerator
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec_engine = SpecificationEngine()
    spec = spec_engine.compile("improve thermoelectric performance of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth_telluride", "generates", "voltage")])

    gen = ArtifactGenerator(seed=42)
    materials = gen._find_materials(spec, cg)

    # Must include at least 3 thermoelectric materials
    assert len(materials) >= 3, f"Expected ≥3 materials in search space, got {materials}"
    # Must include tin_selenide (SnSe — the record holder)
    assert "tin_selenide" in materials, f"SnSe not in search space: {materials}"
    # Must include lead_telluride (PbTe)
    assert "lead_telluride" in materials, f"PbTe not in search space: {materials}"


def test_generator_can_produce_snse_candidate():
    """The generator can actually PRODUCE a SnSe candidate, not just evaluate it.

    Per auditor: 'prove the generator can actually produce a SnSe/PbTe candidate
    when the spec targets high-temperature thermoelectrics.'
    """
    from scripts.artifact_generator import ArtifactGenerator
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph

    spec_engine = SpecificationEngine()
    spec = spec_engine.compile("improve thermoelectric performance of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth_telluride", "generates", "voltage")])

    # Generate many candidates with different seeds to find SnSe
    snse_found = False
    for seed in range(100):
        gen = ArtifactGenerator(seed=seed)
        configs = gen.generate(spec, cg, n=5)
        for c in configs:
            for comp in c.components:
                if comp.material == "tin_selenide":
                    snse_found = True
                    break
            if snse_found:
                break
        if snse_found:
            break

    assert snse_found, "Generator never produced a SnSe candidate in 100 seeds × 5 configs"


def test_snse_candidate_evaluated_at_correct_temperature():
    """A SnSe candidate is evaluated at ~923K, not 350K."""
    from scripts.artifact_generator import ArtifactGenerator
    from scripts.specification import SpecificationEngine
    from scripts.capability_graph import CapabilityGraph
    from scripts.forward_model import ForwardModel

    spec_engine = SpecificationEngine()
    spec = spec_engine.compile("improve thermoelectric performance of bismuth telluride")
    cg = CapabilityGraph()
    cg.from_relations([("bismuth_telluride", "generates", "voltage")])

    # Find a SnSe candidate
    fm = ForwardModel()
    for seed in range(100):
        gen = ArtifactGenerator(seed=seed)
        configs = gen.generate(spec, cg, n=5)
        for c in configs:
            for comp in c.components:
                if comp.material == "tin_selenide":
                    pred = fm.predict(c)
                    T_avg = pred.predicted_properties.get("T_avg_K", 0)
                    ZT = pred.predicted_properties.get("ZT", 0)
                    # SnSe should be evaluated near 923K
                    assert T_avg > 800, \
                        f"SnSe evaluated at T_avg={T_avg}K — should be >800K"
                    # ZT should be near 2.6
                    assert ZT > 1.5, \
                        f"SnSe ZT={ZT:.2f} at T={T_avg}K — should be >1.5 (near published 2.6)"
                    return

    # If we get here, SnSe was never found — that's a failure
    assert False, "SnSe candidate never found in 100 seeds"
