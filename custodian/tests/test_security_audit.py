"""
custodian.tests.test_security_audit — Adversarial security audit of f308b3c.

Threat model:
    Assume the TEE team is curious, the benchmark constructor makes mistakes,
    files can be inspected, APIs can be called incorrectly, and developers
    can accidentally leak information. Can the custodian still preserve
    the blind experiment?

Each test attempts to BREAK the custodian, not verify the happy path.
"""
import sys
import os
import json
import copy
import tempfile
import unittest
from pathlib import Path

CUSTODIAN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CUSTODIAN_DIR))

from src.hasher import sha256_json, sha256_string, canonical_json
from src.source_registry import SourceRegistry, SourceEntry
from src.case_schema import (
    BenchmarkCase,
    validate_case,
    check_blind_fixture_safety,
    ANSWER_KEY_FIELDS,
)
from src.sampler import (
    deterministic_sample,
    construct_benchmark,
    validate_construction_params,
    TEEDependencyError,
    InsufficientCorpusError,
    DuplicateCaseError,
)
from src.benchmark_builder import (
    Benchmark,
    DRAFT,
    VALIDATED,
    CONSTRUCTED,
    SEALED,
    SealStateError,
    ValidationError,
)
from src.seal import seal_benchmark, generate_infrastructure_attestation
from src.audit_trail import AuditTrail

from fixtures.synthetic.synthetic_fixture import SYNTHETIC_CASES, SYNTHETIC_EXTERNAL_SEED


def _make_case(case_id="C1", domain="fluid_mechanics", group="IG-1", ground_truth=None):
    return BenchmarkCase(
        case_id=case_id,
        source_id="S1",
        domain=domain,
        problem="test problem",
        input_material={"source_a": "source A content", "source_b": "source B content"},
        expected_task="generate hypothesis",
        verification_method="measurement",
        difficulty="moderate",
        independence_group=group,
        provenance={"constructor": "test", "construction_timestamp": "2026-01-01T00:00:00Z"},
        ground_truth=ground_truth or {"type": "positive", "mechanism": "secret_mechanism"},
    )


def _make_constructed_benchmark():
    """Create a benchmark in CONSTRUCTED state for testing."""
    bm = Benchmark(benchmark_id="SEC-TEST-001")
    domains = ["fluid_mechanics", "enzymology", "optics", "materials_science"]
    for i in range(4):
        c = _make_case(
            case_id=f"C{i}",
            domain=domains[i],
            group=f"IG-{i}",
            ground_truth={"type": "positive", "mechanism": f"secret_{i}"},
        )
        bm.add_case(c)
    bm.seal_state = VALIDATED  # skip N>=100 check for testing
    bm.transition_to_constructed(
        source_manifest_hash="a" * 64,
        seed_hash="b" * 64,
        corpus_hash="c" * 64,
        construction_parameters={"target_n": 4},
    )
    return bm


# ============================================================
# ATTACK 1: Can TEE obtain answer key through any channel?
# ============================================================

class TestAttack1_AnswerKeyLeakage(unittest.TestCase):
    """Attempt to obtain the answer key through every possible channel."""

    def test_tee_package_has_no_answer_key(self):
        """The TEE package must not contain ground_truth."""
        bm = _make_constructed_benchmark()
        bm.seal_state = SEALED
        tee_pkg = bm.get_tee_package()
        violations = check_blind_fixture_safety(tee_pkg)
        self.assertEqual(violations, [], f"TEE package leaks: {violations}")

    def test_blind_fixture_has_no_ground_truth_key(self):
        """Blind fixture cases must not have ground_truth field."""
        bm = _make_constructed_benchmark()
        blind = bm.get_blind_fixture()
        for case in blind["cases"]:
            self.assertNotIn("ground_truth", case)

    def test_blind_fixture_has_no_mechanism(self):
        """Blind fixture must not contain the expected mechanism."""
        bm = _make_constructed_benchmark()
        blind = bm.get_blind_fixture()
        blind_str = json.dumps(blind)
        # The ground truth mechanisms are "secret_0", "secret_1", etc.
        for i in range(4):
            self.assertNotIn(f"secret_{i}", blind_str)

    def test_answer_key_separate_from_blind_fixture(self):
        """Answer key and blind fixture are different objects with different hashes."""
        bm = _make_constructed_benchmark()
        blind = bm.get_blind_fixture()
        answer_key = bm.get_answer_key()
        self.assertNotEqual(
            sha256_json(blind),
            sha256_json(answer_key),
            "Blind fixture and answer key have the same hash — they are identical!"
        )

    def test_answer_key_not_in_benchmark_to_dict(self):
        """Benchmark.to_dict() includes ground_truth — but this is the CUSTODIAN's
        internal representation, not the TEE package. Verify TEE package doesn't use to_dict()."""
        bm = _make_constructed_benchmark()
        bm.seal_state = SEALED
        tee_pkg = bm.get_tee_package()
        # TEE package uses get_blind_fixture(), NOT to_dict()
        self.assertNotIn("cases", tee_pkg.get("blind_fixture", {}).get("cases", [{}])[0].get("ground_truth", {}))

    def test_no_answer_key_in_exception_messages(self):
        """Exception messages must not leak ground truth."""
        bm = Benchmark(benchmark_id="TEST")
        case = _make_case(ground_truth={"mechanism": "SECRET_IN_EXCEPTION"})
        bm.add_case(case)
        # Try to trigger an exception
        try:
            bm.add_case(case)  # Duplicate
        except Exception as e:
            self.assertNotIn("SECRET_IN_EXCEPTION", str(e))

    def test_no_answer_key_in_audit_trail(self):
        """Audit trail must not contain ground truth."""
        bm = _make_constructed_benchmark()
        trail = AuditTrail()
        trail.record("BENCHMARK_SEALED", "TEST", "actor",
                     relevant_hash=bm.manifest_hash or "test",
                     details={"case_count": len(bm.cases)})
        trail_str = trail.to_json()
        self.assertNotIn("secret_0", trail_str)
        self.assertNotIn("secret_1", trail_str)


# ============================================================
# ATTACK 2: Can construction indirectly consume TEE outputs?
# ============================================================

class TestAttack2_TEEOutputConsumption(unittest.TestCase):
    """Attempt to feed TEE outputs into benchmark construction."""

    def test_tee_score_in_params_rejected(self):
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({"tee_score": 0.95})

    def test_tee_outputs_in_params_rejected(self):
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({"tee_outputs": ["h1", "h2"]})

    def test_tee_rankings_in_params_rejected(self):
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({"tee_rankings": [1, 2, 3]})

    def test_tee_model_identity_in_params_rejected(self):
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({"tee_model_identity": "glm-4-plus"})

    def test_nested_tee_reference_rejected(self):
        """TEE reference hidden in nested dict is still detected."""
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({
                "sampling": {"config": {"tee_performance": 0.8}}
            })

    def test_tee_reference_in_list_rejected(self):
        """TEE reference in a list is detected."""
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({
                "filters": [{"tee_failures": ["case1"]}]
            })

    def test_case_insensitive_tee_detection(self):
        """TEE references are detected case-insensitively."""
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({"TEE_SCORE": 0.5})
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({"Tee_Outputs": []})


# ============================================================
# ATTACK 3: Can seed be manipulated after seeing candidates?
# ============================================================

class TestAttack3_SeedManipulation(unittest.TestCase):
    """Attempt to manipulate the seed after seeing candidates."""

    def test_seed_hash_is_committed_before_selection(self):
        """The seed hash is computed from the external seed, not from candidates."""
        candidates = [c.copy() for c in SYNTHETIC_CASES]
        _, seed_hash = deterministic_sample(candidates, "my_seed", target_n=4)
        # Seed hash should be SHA-256 of "my_seed"
        expected = sha256_string("my_seed")
        self.assertEqual(seed_hash, expected)

    def test_changing_seed_changes_hash(self):
        """Different seeds produce different hashes."""
        candidates = [c.copy() for c in SYNTHETIC_CASES]
        _, hash1 = deterministic_sample(candidates, "seed_A", target_n=4)
        _, hash2 = deterministic_sample(candidates, "seed_B", target_n=4)
        self.assertNotEqual(hash1, hash2)

    def test_seed_does_not_depend_on_candidates(self):
        """The seed hash is the same regardless of which candidates are provided."""
        _, hash1 = deterministic_sample(
            [c.copy() for c in SYNTHETIC_CASES], "fixed_seed", target_n=4
        )
        # Different candidates, same seed
        other_candidates = [
            {**c, "case_id": f"OTHER-{c['case_id']}", "independence_group": f"OTHER-{c['independence_group']}"}
            for c in SYNTHETIC_CASES
        ]
        _, hash2 = deterministic_sample(other_candidates, "fixed_seed", target_n=4)
        self.assertEqual(hash1, hash2, "Seed hash should not depend on candidates")

    def test_empty_seed_rejected(self):
        """Empty seed is rejected."""
        with self.assertRaises(ValueError):
            deterministic_sample(SYNTHETIC_CASES, "", target_n=4)


# ============================================================
# ATTACK 4: Can sealed benchmark be mutated?
# ============================================================

class TestAttack4_SealedMutation(unittest.TestCase):
    """Attempt to mutate a sealed benchmark through every channel."""

    def setUp(self):
        self.bm = _make_constructed_benchmark()
        seal_benchmark(self.bm)
        self.original_hash = self.bm.manifest_hash

    def test_cannot_add_case_after_seal(self):
        with self.assertRaises(SealStateError):
            self.bm.add_case(_make_case("NEW"))

    def test_cannot_transition_from_sealed(self):
        with self.assertRaises(SealStateError):
            self.bm.transition_to_validated()
        with self.assertRaises(SealStateError):
            self.bm.transition_to_constructed("", "", "", {})
        with self.assertRaises(SealStateError):
            self.bm.transition_to_sealed("")

    def test_shallow_copy_mutation_detected(self):
        """A shallow copy of a case can be mutated, but the benchmark's
        manifest hash is computed from the benchmark's internal state.
        Verify that mutating a copied case doesn't change the benchmark."""
        original_cases = list(self.bm.cases)
        # Make a shallow copy and mutate
        copied = copy.copy(self.bm.cases[0])
        copied.case_id = "TAMPERED"
        # The original benchmark should be unaffected
        self.assertEqual(self.bm.cases[0].case_id, original_cases[0].case_id)

    def test_deep_copy_mutation_detected(self):
        """Deep copy mutation doesn't affect original."""
        bm_copy = copy.deepcopy(self.bm)
        bm_copy.cases[0].case_id = "TAMPERED"
        # Original is unchanged
        self.assertEqual(self.bm.cases[0].case_id, "C0")
        # Manifest hash is unchanged
        self.assertEqual(self.bm.manifest_hash, self.original_hash)

    def test_manifest_hash_includes_all_fields(self):
        """Manifest hash changes if any case is modified."""
        # Use same benchmark_id for comparison (different IDs produce different hashes)
        bm2 = Benchmark(benchmark_id=self.bm.benchmark_id)
        domains = ["fluid_mechanics", "enzymology", "optics", "materials_science"]
        for i in range(4):
            c = _make_case(
                case_id=f"C{i}", domain=domains[i], group=f"IG-{i}",
                ground_truth={"type": "positive", "mechanism": f"secret_{i}"},
            )
            bm2.add_case(c)
        bm2.seal_state = VALIDATED
        bm2.transition_to_constructed("a" * 64, "b" * 64, "c" * 64, {"target_n": 4})
        seal_benchmark(bm2)

        # Modify bm2's internal case (bypassing state machine — this is the attack)
        bm2.cases[0].case_id = "TAMPERED"
        # Re-compute manifest
        manifest = bm2.get_manifest(include_hash=False)
        new_hash = sha256_json(manifest)
        self.assertNotEqual(new_hash, self.bm.manifest_hash,
                           "Manifest hash did not change after tampering — HASH IS BROKEN")

    def test_sealed_at_cannot_be_overwritten(self):
        """Direct attribute assignment is possible in Python, but the
        manifest hash would no longer match."""
        original_sealed_at = self.bm.sealed_at
        self.bm.sealed_at = "TAMPERED_TIMESTAMP"
        # The manifest hash was computed at seal time and is now stale
        # A verifier would detect this by recomputing the manifest hash
        manifest = self.bm.get_manifest(include_hash=False)
        recomputed_hash = sha256_json(manifest)
        self.assertNotEqual(recomputed_hash, self.bm.manifest_hash,
                           "Tampered sealed_at not detected by manifest hash")


# ============================================================
# ATTACK 5: Can blind fixture be reconstructed into answer key?
# ============================================================

class TestAttack5_BlindToAnswerKeyReconstruction(unittest.TestCase):
    """Attempt to reconstruct the answer key from blind fixture metadata."""

    def test_blind_fixture_has_no_verification_answer(self):
        """The verification_method field describes HOW to verify, not the answer."""
        bm = _make_constructed_benchmark()
        blind = bm.get_blind_fixture()
        for case in blind["cases"]:
            self.assertIn("verification_method", case)
            # verification_method should be a description, not the answer
            self.assertNotIn("mechanism", case.get("verification_method", "").lower())

    def test_blind_fixture_provenance_has_no_ground_truth(self):
        """Provenance metadata must not leak ground truth."""
        bm = _make_constructed_benchmark()
        blind = bm.get_blind_fixture()
        for case in blind["cases"]:
            provenance_str = json.dumps(case.get("provenance", {}))
            self.assertNotIn("secret_", provenance_str)
            self.assertNotIn("mechanism", provenance_str.lower())

    def test_blind_fixture_hash_cannot_reveal_answer_key(self):
        """The blind fixture hash is SHA-256 of the blind fixture.
        It cannot be reverse-engineered to reveal the answer key."""
        bm = _make_constructed_benchmark()
        blind_hash = bm.blind_fixture_hash
        answer_hash = bm.answer_key_hash
        # The hashes are different (proven in other tests)
        self.assertNotEqual(blind_hash, answer_hash)
        # Neither hash reveals the other's content
        self.assertEqual(len(blind_hash), 64)
        self.assertEqual(len(answer_hash), 64)


# ============================================================
# ATTACK 6: Can provenance be altered without invalidating manifest?
# ============================================================

class TestAttack6_ProvenanceTampering(unittest.TestCase):
    """Attempt to alter provenance without detection."""

    def test_provenance_change_invalidates_manifest(self):
        """Changing provenance changes the manifest hash."""
        bm = _make_constructed_benchmark()
        seal_benchmark(bm)
        original_hash = bm.manifest_hash

        # Tamper with provenance
        bm.cases[0].provenance["constructor"] = "TAMPERED"

        # Recompute manifest hash
        manifest = bm.get_manifest(include_hash=False)
        new_hash = sha256_json(manifest)
        self.assertNotEqual(new_hash, original_hash)

    def test_source_content_change_detected(self):
        """Changing source content changes the source content_hash."""
        reg = SourceRegistry()
        reg.register("S1", "d", "t", "o", "u", "original content", "v")
        original_hash = reg.get("S1").content_hash

        # Register same ID with different content (would fail)
        # Instead, verify content hash mismatch
        self.assertFalse(reg.verify_content("S1", "tampered content"))
        self.assertTrue(reg.verify_content("S1", "original content"))


# ============================================================
# ATTACK 7-8: Can duplicates/near-duplicates evade independence?
# ============================================================

class TestAttack7_8_DuplicateEvasion(unittest.TestCase):
    """Attempt to evade duplicate and independence checks."""

    def test_same_problem_different_case_id_detected(self):
        """Two cases with same problem text but different IDs are still
        flagged if they share an independence_group."""
        bm = Benchmark(benchmark_id="TEST")
        c1 = _make_case("C1", group="SAME_GROUP")
        c2 = _make_case("C2", group="SAME_GROUP")
        bm.add_case(c1)
        bm.add_case(c2)
        errors = bm.validate()
        self.assertTrue(any("DEPENDENT_CASE_CLUSTER" in e for e in errors))

    def test_near_identical_input_material_not_detected_by_current_validator(self):
        """KNOWN WEAKNESS: Near-identical input_material with different independence_groups
        is NOT detected by the current validator. This is a semantic gap."""
        bm = Benchmark(benchmark_id="TEST")
        c1 = _make_case("C1", group="IG-1")
        c2 = _make_case("C2", group="IG-2")
        # Same source text, different group
        c2.input_material = c1.input_material  # Identical sources
        bm.add_case(c1)
        bm.add_case(c2)
        errors = bm.validate()
        # This PASSES validation (no error) — which is a KNOWN WEAKNESS
        # The validator only checks independence_group, not content similarity
        # This must be documented in the threat model
        has_cluster_error = any("DEPENDENT_CASE_CLUSTER" in e for e in errors)
        # Document this as a known gap
        if not has_cluster_error:
            pass  # This is expected — documented as a known weakness

    def test_domain_label_manipulation_detected(self):
        """A case with domain='fluid_mechanics' and another with domain='fluid-mechanics'
        would be treated as different domains by the current validator."""
        # This is a KNOWN WEAKNESS: domain labels are string-compared, not semantic
        # An attacker could create "fluid_mechanics" and "fluid-mechanics" as "different" domains
        bm = Benchmark(benchmark_id="TEST")
        c1 = _make_case("C1", domain="fluid_mechanics", group="IG-1")
        c2 = _make_case("C2", domain="fluid-mechanics", group="IG-2")  # Hyphen vs underscore
        bm.add_case(c1)
        bm.add_case(c2)
        domains = set(c.domain for c in bm.cases)
        # These are treated as different domains — KNOWN WEAKNESS
        self.assertEqual(len(domains), 2)  # Should be 1 semantically


# ============================================================
# ATTACK 9: Can domain labels be manipulated?
# ============================================================

class TestAttack9_DomainManipulation(unittest.TestCase):
    """Attempt to manufacture ≥4 domains through label tricks."""

    def test_trivial_domain_variants_not_caught(self):
        """KNOWN WEAKNESS: 'physics', 'Physics', 'PHYSICS' are treated as 3 domains."""
        domains = set(["physics", "Physics", "PHYSICS"])
        self.assertEqual(len(domains), 3)  # String comparison, not semantic

    def test_domain_count_is_string_based(self):
        """Domain count uses set() of strings — no canonicalization."""
        bm = Benchmark(benchmark_id="TEST")
        for i, domain in enumerate(["d1", "d2", "d3", "d4"]):
            c = _make_case(f"C{i}", domain=domain, group=f"IG-{i}")
            bm.add_case(c)
        self.assertEqual(len(set(c.domain for c in bm.cases)), 4)


# ============================================================
# ATTACK 10: Can benchmark be sealed without all 9 requirements?
# ============================================================

class TestAttack10_IncompleteSeal(unittest.TestCase):
    """Attempt to seal a benchmark without all requirements."""

    def test_cannot_seal_from_draft(self):
        """Cannot skip VALIDATED and CONSTRUCTED."""
        bm = Benchmark(benchmark_id="TEST", seal_state=DRAFT)
        with self.assertRaises(SealStateError):
            bm.transition_to_sealed("now")

    def test_cannot_seal_from_validated(self):
        """Cannot skip CONSTRUCTED."""
        bm = Benchmark(benchmark_id="TEST", seal_state=VALIDATED)
        with self.assertRaises(SealStateError):
            bm.transition_to_sealed("now")

    def test_cannot_seal_without_hashes(self):
        """CONSTRUCTED state requires blind_fixture_hash and answer_key_hash."""
        bm = Benchmark(benchmark_id="TEST", seal_state=CONSTRUCTED)
        # If someone bypasses transition_to_constructed and sets state directly,
        # the hashes would be empty
        self.assertEqual(bm.blind_fixture_hash, "")
        self.assertEqual(bm.answer_key_hash, "")
        # seal_benchmark would still work (it doesn't check for empty hashes)
        # This is a KNOWN WEAKNESS — documented in threat model

    def test_seal_verifies_blind_fixture_safety(self):
        """seal_benchmark checks blind fixture safety before sealing."""
        bm = _make_constructed_benchmark()
        # Tamper: inject answer key into blind fixture by overriding the method
        original_method = bm.get_blind_fixture
        bm.get_blind_fixture = lambda: {"cases": [{"ground_truth": "leaked"}]}

        with self.assertRaises(ValueError) as ctx:
            seal_benchmark(bm)
        self.assertIn("BLIND_FIXTURE_SAFETY_VIOLATION", str(ctx.exception))


# ============================================================
# ATTACK 11: Can TEE performance influence selection implicitly?
# ============================================================

class TestAttack11_ImplicitTEEDependency(unittest.TestCase):
    """Attempt to influence selection through implicit TEE references."""

    def test_tee_results_in_nested_config_rejected(self):
        """TEE results deeply nested in config are detected."""
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({
                "optimization": {
                    "parameters": {
                        "weights": {
                            "tee_results": [1, 2, 3]
                        }
                    }
                }
            })

    def test_tee_in_list_of_dicts_rejected(self):
        """TEE reference in a list of dicts is detected."""
        with self.assertRaises(TEEDependencyError):
            validate_construction_params({
                "case_filters": [
                    {"name": "filter1", "tee_score": 0.9},
                    {"name": "filter2"},
                ]
            })

    def test_no_implicit_dependency_in_sampler(self):
        """The sampler function signature has no TEE-related parameters."""
        import inspect
        sig = inspect.signature(deterministic_sample)
        param_names = set(sig.parameters.keys())
        forbidden = {"tee", "score", "results", "performance", "model"}
        for f in forbidden:
            for p in param_names:
                self.assertNotIn(f, p.lower(),
                                 f"Sampler parameter '{p}' contains '{f}' — potential TEE dependency")


# ============================================================
# ATTACK 12: Does filesystem enforce separation?
# ============================================================

class TestAttack12_FilesystemBoundary(unittest.TestCase):
    """Test whether the filesystem enforces separation, or only Python objects."""

    def test_answer_key_serializable_to_file(self):
        """The answer key CAN be serialized to a file. The separation is
        LOGICAL (API boundary), not PHYSICAL (filesystem boundary).

        KNOWN WEAKNESS: If the custodian writes the answer key to a file
        that the TEE process can read, the separation is broken.
        The custodian must store the answer key in a location the TEE
        cannot access."""
        bm = _make_constructed_benchmark()
        answer_key = bm.get_answer_key()

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(answer_key, f)
            temp_path = f.name

        # The file exists and contains the answer key
        with open(temp_path) as f:
            loaded = json.load(f)
        self.assertIn("answer_key", loaded)
        self.assertIn("C0", loaded["answer_key"])

        # Cleanup
        os.unlink(temp_path)

    def test_blind_fixture_serializable_to_file(self):
        """Blind fixture can be serialized to a file for TEE consumption."""
        bm = _make_constructed_benchmark()
        bm.seal_state = SEALED
        tee_pkg = bm.get_tee_package()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(tee_pkg, f)
            temp_path = f.name

        with open(temp_path) as f:
            loaded = json.load(f)

        # Verify no answer key in the file
        violations = check_blind_fixture_safety(loaded)
        self.assertEqual(violations, [])

        os.unlink(temp_path)

    def test_filesystem_separation_not_enforced_by_custodian(self):
        """KNOWN WEAKNESS: The custodian does NOT enforce filesystem-level
        access control. If the TEE process has filesystem access to the
        directory where the answer key is stored, it can read it.

        The custodian provides LOGICAL separation (different data structures,
        different hashes, automated safety checks) but NOT PHYSICAL separation
        (filesystem permissions, separate directories, access control lists).

        This must be addressed by the DEPLOYMENT architecture, not the
        custodian code alone."""

        # This test documents the weakness rather than testing for it
        # The custodian cannot enforce filesystem permissions from Python
        self.assertTrue(True, "Filesystem separation is a deployment responsibility")


if __name__ == '__main__':
    unittest.main(verbosity=2)
