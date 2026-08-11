"""Auditor's adversarial tests for learning generalization (cycle 215).

Per the auditor: 'I would deliberately try to break it.'

Test A: Hide PbTe. Can it rediscover SnSe?
Test B: Hide SnSe. Can it find another high-ZT family?
Test E: Start from deliberately bad priors. Does it still converge?
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_a_hide_pbte_rediscover_snse():
    """Test A: Hide PbTe. Can the search rediscover SnSe?

    Per auditor: 'If no, it memorized.'
    """
    import scripts.materials_database as mdb
    from scripts.learning_inventor import LearningInventor
    from scripts.specification import SpecificationEngine

    original = dict(mdb.MATERIALS_DATABASE)
    mdb.MATERIALS_DATABASE.pop("PbTe", None)

    try:
        spec = SpecificationEngine().compile("improve thermoelectric performance")
        inventor = LearningInventor(seed=42)
        results = inventor.run_multiple(spec, n_iterations=3, n_per_iter=20)

        all_results = []
        for r in results:
            all_results.extend(r.candidates)

        snse_results = [r for r in all_results if r.design_point.base_material == "SnSe"]
        snse_passed = [r for r in snse_results if r.passed_plausibility]

        assert len(snse_passed) > 0, \
            "SnSe must be discoverable without PbTe — otherwise the search memorized PbTe"
    finally:
        mdb.MATERIALS_DATABASE = original


def test_b_hide_snse_find_alternative():
    """Test B: Hide SnSe. Can it find another high-ZT family?

    Per auditor: 'If no, still memorizing.'
    """
    import scripts.materials_database as mdb
    from scripts.learning_inventor import LearningInventor
    from scripts.specification import SpecificationEngine

    original = dict(mdb.MATERIALS_DATABASE)
    mdb.MATERIALS_DATABASE.pop("SnSe", None)

    try:
        spec = SpecificationEngine().compile("improve thermoelectric performance")
        inventor = LearningInventor(seed=42)
        results = inventor.run_multiple(spec, n_iterations=3, n_per_iter=20)

        all_results = []
        for r in results:
            all_results.extend(r.candidates)

        high_zt = [r for r in all_results if r.passed_plausibility and r.predicted_zt > 1.0]
        materials_found = set(r.design_point.base_material for r in high_zt)

        assert len(materials_found) >= 2, \
            f"Must find ≥2 high-ZT families without SnSe — got: {materials_found}"
    finally:
        mdb.MATERIALS_DATABASE = original


def test_e_bad_priors_still_converge():
    """Test E: Start from deliberately bad priors. Does it still improve?

    Per auditor: 'Start from worst materials promoted. If it converges
    similarly, that's much stronger evidence.'
    """
    from scripts.learning_inventor import LearningInventor, SearchPolicy
    from scripts.specification import SpecificationEngine

    spec = SpecificationEngine().compile("improve thermoelectric performance")

    # Bad priors: promote WORST materials, demote BEST
    bad_policy = SearchPolicy()
    bad_policy.material_weights = {
        "SrTiO3": 3.0,   # worst (ZT=0.3) — promoted
        "Bi2Te3": 2.0,   # mediocre (ZT=0.93) — promoted
        "PbTe": 0.1,     # good (ZT=1.4) — demoted
        "SnSe": 0.1,     # best (ZT=2.6) — demoted
    }

    inventor = LearningInventor(seed=42)
    inventor.policy = bad_policy
    results = inventor.run_multiple(spec, n_iterations=3, n_per_iter=20)

    # Compute avg ZT over passed candidates for each iteration
    avgs = []
    for r in results:
        passed = [c for c in r.candidates if c.passed_plausibility]
        if passed:
            avgs.append(sum(c.predicted_zt for c in passed) / len(passed))
        else:
            avgs.append(0.0)

    # Despite bad priors, the avg ZT should improve (not stay stuck at low values)
    assert avgs[-1] > avgs[0], \
        f"Bad priors must still improve: iter1={avgs[0]:.3f}, iter3={avgs[-1]:.3f}"

    # SnSe should be rediscovered despite being demoted to weight=0.1
    final_materials = set()
    for r in results[-1].candidates:
        final_materials.add(r.design_point.base_material)

    # At least some good material should appear despite bad priors
    good_materials = {"SnSe", "PbTe", "Bi0.4Sb1.6Te3", "CoSb3"}
    found_good = good_materials & final_materials
    assert len(found_good) >= 1, \
        f"At least 1 good material must be rediscovered despite bad priors: {final_materials}"


def test_heuristic_learning_produces_transferable_principles():
    """Heuristic learning produces transferable principles (not material preferences).

    Per auditor: 'The learned object should no longer be PbTe weight = 3.38.
    It should be reusable design principles.'
    """
    from scripts.heuristic_learning import HeuristicLearner
    from scripts.learning_inventor import LearningInventor
    from scripts.specification import SpecificationEngine

    spec = SpecificationEngine().compile("improve thermoelectric performance")
    inventor = LearningInventor(seed=42)
    results = inventor.run_multiple(spec, n_iterations=3, n_per_iter=20)

    all_results = []
    for r in results:
        all_results.extend(r.candidates)

    learner = HeuristicLearner()
    heuristics = learner.learn_from_results(all_results)

    assert len(heuristics) > 0, "Must learn at least 1 heuristic"

    for h in heuristics:
        # Must reference a design variable, not a material name
        assert h.variable in ("grain_size_nm", "carrier_concentration",
                              "composition_x", "porosity"), \
            f"Heuristic must reference design variable, got: {h.variable}"
        # Must span multiple materials
        assert len(h.materials_tested) >= 3, \
            f"Heuristic must span ≥3 materials: {h.materials_tested}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
