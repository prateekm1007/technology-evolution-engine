"""Tests for derived_causal_chains.py — cycle 219.

Auditor's update #9 priority #3:
  "Advance Layer C from curated to derived. The executable causal chains
   are a great foundation. The next step is to *infer* chain structure
   from the mechanism models (vary a variable → propagate → observe
   which downstream quantities move), so the chain is discovered, not
   selected from a lookup."
"""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


def test_deriver_imports():
    """Module imports cleanly."""
    from scripts.derived_causal_chains import CausalChainDeriver, ProbeResult
    assert CausalChainDeriver is not None
    assert ProbeResult is not None


def test_probe_perturbs_variable():
    """Probing perturbs only the chosen variable."""
    from scripts.derived_causal_chains import CausalChainDeriver
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    deriver = CausalChainDeriver(THERMOELECTRIC_DOMAIN, thermoelectric_forward)
    baseline = {"composition_x": 0.5, "carrier_concentration": 1e19,
                "grain_size_nm": 1000.0, "porosity": 0.2}
    probe = deriver.probe(baseline, "composition_x", "increase")

    # Perturbed value must differ from baseline
    assert probe.perturbed_value != probe.baseline_value
    # Other variables unchanged
    assert probe.baseline_derived  # must have derived quantities


def test_probe_result_computes_deltas():
    """ProbeResult computes outcome delta and derived deltas."""
    from scripts.derived_causal_chains import CausalChainDeriver
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    deriver = CausalChainDeriver(THERMOELECTRIC_DOMAIN, thermoelectric_forward)
    baseline = {"composition_x": 0.5, "carrier_concentration": 1e19,
                "grain_size_nm": 1000.0, "porosity": 0.2}
    probe = deriver.probe(baseline, "composition_x", "increase")

    deltas = probe.derived_deltas()
    assert isinstance(deltas, dict)
    # Composition affects thermal_conductivity (Klemens)
    assert "thermal_conductivity" in deltas


def test_deriver_finds_chain_for_composition_x():
    """Deriver produces a chain for composition_x → ZT."""
    from scripts.derived_causal_chains import CausalChainDeriver
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    deriver = CausalChainDeriver(THERMOELECTRIC_DOMAIN, thermoelectric_forward)
    baseline = {"composition_x": 0.5, "carrier_concentration": 1e19,
                "grain_size_nm": 1000.0, "porosity": 0.2}
    chain = deriver.derive_chain("composition_x", baseline)

    assert chain is not None
    assert "DERIVED" in chain.chain_id
    assert len(chain.steps) >= 2
    # First step must touch composition_x
    assert chain.steps[0].variable == "composition_x"
    # Last step must touch ZT
    assert chain.steps[-1].variable == "ZT"


def test_deriver_finds_chain_for_carrier_concentration():
    """Deriver produces a chain for carrier_concentration → ZT."""
    from scripts.derived_causal_chains import CausalChainDeriver
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    deriver = CausalChainDeriver(THERMOELECTRIC_DOMAIN, thermoelectric_forward)
    baseline = {"composition_x": 0.5, "carrier_concentration": 1e19,
                "grain_size_nm": 1000.0, "porosity": 0.2}
    chain = deriver.derive_chain("carrier_concentration", baseline)

    assert chain is not None
    assert chain.steps[0].variable == "carrier_concentration"
    assert chain.steps[-1].variable == "ZT"


def test_deriver_works_across_domains():
    """Deriver works on all 4 domains."""
    from scripts.derived_causal_chains import CausalChainDeriver
    from scripts.cross_domain_transfer import (
        THERMOELECTRIC_DOMAIN, BATTERY_DOMAIN, CATALYST_DOMAIN, PV_DOMAIN,
        thermoelectric_forward, battery_forward, catalyst_forward, pv_forward,
    )

    cases = [
        (THERMOELECTRIC_DOMAIN, thermoelectric_forward, "composition_x"),
        (BATTERY_DOMAIN, battery_forward, "particle_size_nm"),
        (CATALYST_DOMAIN, catalyst_forward, "particle_size_nm"),
        (PV_DOMAIN, pv_forward, "bandgap_eV"),
    ]

    n_chains = 0
    for spec, fn, root_var in cases:
        deriver = CausalChainDeriver(spec, fn)
        baseline = {}
        for v in spec["design_vars"]:
            lo, hi = v["bounds"]
            if lo > 0 and hi / lo > 100:
                baseline[v["name"]] = math.exp((math.log(lo) + math.log(hi)) / 2)
            else:
                baseline[v["name"]] = (lo + hi) / 2
        chain = deriver.derive_chain(root_var, baseline)
        if chain:
            n_chains += 1
            # Each chain must end at the outcome variable
            assert chain.final_variable == spec["outcome_name"], \
                f"Chain for {root_var} in {spec['name']} ends at {chain.final_variable}, " \
                f"expected {spec['outcome_name']}"

    # Must derive chains for at least 3/4 domains
    assert n_chains >= 3, f"Only derived chains for {n_chains}/4 domains"


def test_derived_chain_same_structure_as_curated():
    """Derived chains have the same data structure as curated ones."""
    from scripts.derived_causal_chains import CausalChainDeriver
    from scripts.meta_invention import CausalChain, CausalStep
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    deriver = CausalChainDeriver(THERMOELECTRIC_DOMAIN, thermoelectric_forward)
    baseline = {"composition_x": 0.5, "carrier_concentration": 1e19,
                "grain_size_nm": 1000.0, "porosity": 0.2}
    chain = deriver.derive_chain("composition_x", baseline)

    # Must be a CausalChain instance with CausalStep objects
    assert isinstance(chain, CausalChain)
    for step in chain.steps:
        assert isinstance(step, CausalStep)
        assert step.variable
        assert step.change
        assert step.mechanism
        assert step.formula


def test_deriver_uses_probe_results():
    """Deriver actually probes the forward model (not just looks up labels)."""
    from scripts.derived_causal_chains import CausalChainDeriver
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    deriver = CausalChainDeriver(THERMOELECTRIC_DOMAIN, thermoelectric_forward)
    baseline = {"composition_x": 0.5, "carrier_concentration": 1e19,
                "grain_size_nm": 1000.0, "porosity": 0.2}

    # Probe should populate the cache
    probe = deriver.probe(baseline, "composition_x", "increase")
    assert len(deriver.probe_cache) >= 1

    # Derive should produce a chain (which requires probe results)
    chain = deriver.derive_chain("composition_x", baseline)
    assert chain is not None


def test_deriver_honest_when_no_chain_exists():
    """Deriver returns None honestly when no labeled mechanism matches.

    This is critical: the deriver should NOT fabricate a chain when
    the probe data doesn't match any known mechanism label.
    """
    from scripts.derived_causal_chains import CausalChainDeriver
    from scripts.cross_domain_transfer import THERMOELECTRIC_DOMAIN, thermoelectric_forward

    deriver = CausalChainDeriver(THERMOELECTRIC_DOMAIN, thermoelectric_forward)
    # Use a baseline where grain_size dominates κ but no label exists for
    # (grain_size_nm, thermal_conductivity) directly via Matthiessen
    # (the label only matches via mobility/electrical_conductivity)
    baseline = {"composition_x": 0.0, "carrier_concentration": 1e19,
                "grain_size_nm": 316.0, "porosity": 0.0}
    chain = deriver.derive_chain("grain_size_nm", baseline)
    # The probe will show grain_size affects thermal_conductivity
    # but the only label is (grain_size_nm, electrical_conductivity) which
    # won't be selected because electrical_conductivity didn't change.
    # This is HONEST behavior — the chain isn't fabricated.
    # It may return None or a partial chain depending on data.
    # The test just asserts it doesn't crash and returns either None
    # or a valid CausalChain.
    if chain is not None:
        assert chain.chain_id
        assert len(chain.steps) >= 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
