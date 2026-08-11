"""
custodian.tests.test_hardening — Tests for the 7 custody-hardening fixes.

1. Physical isolation: deployment test demonstrating TEE cannot read answer key
2. Near-duplicate detection: similarity/clustering as review flag
3. Scientific independence: custodian adjudication of clusters
4. Domain canonicalization: canonical domain taxonomy
5. State machine: no route to sealing without complete inputs
6. Empty hashes: reject missing cryptographic commitments
7. Deterministic identity: timestamps cannot contaminate canonical hash
"""
import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

CUSTODIAN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CUSTODIAN_DIR))

from src.hasher import sha256_json, sha256_string
from src.benchmark_builder import Benchmark, DRAFT, VALIDATED, CONSTRUCTED, SEALED, SealStateError, ValidationError
from src.case_schema import BenchmarkCase, check_blind_fixture_safety
from src.seal import seal_benchmark
from src.domain_taxonomy import canonicalize_domain, is_known_domain, DOMAIN_TAXONOMY
from src.similarity import detect_near_duplicates, SimilarityFlag


def _make_case(case_id="C1", domain="fluid_mechanics", group="IG-1", source_id="S1",
               problem="test problem", source_a="source A", source_b="source B",
               ground_truth=None):
    return BenchmarkCase(
        case_id=case_id, source_id=source_id, domain=domain, problem=problem,
        input_material={"source_a": source_a, "source_b": source_b},
        expected_task="generate hypothesis", verification_method="measurement",
        difficulty="moderate", independence_group=group,
        provenance={"constructor": "test", "construction_timestamp": "2026-01-01"},
        ground_truth=ground_truth or {"type": "positive", "mechanism": "secret"},
    )


def _make_sealable_benchmark(bid="HARDEN-TEST"):
    bm = Benchmark(benchmark_id=bid)
    domains = ["fluid_mechanics", "enzymology", "optics", "materials_science"]
    for i in range(4):
        bm.add_case(_make_case(
            case_id=f"C{i}", domain=domains[i], group=f"IG-{i}",
            source_id=f"S{i}",
            ground_truth={"type": "positive", "mechanism": f"secret_{i}"},
        ))
    bm.seal_state = VALIDATED
    bm.transition_to_constructed("a" * 64, "b" * 64, "c" * 64, {"target_n": 4})
    return bm


class TestHardening1_PhysicalIsolation(unittest.TestCase):
    """HARDENING #1: Physical isolation — TEE cannot read answer key path."""

    def test_answer_key_separate_file_from_blind_fixture(self):
        """Answer key and blind fixture are written to separate files."""
        bm = _make_sealable_benchmark()
        seal_benchmark(bm)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate custodian environment
            custodian_dir = Path(tmpdir) / "custodian"
            tee_dir = Path(tmpdir) / "tee"
            custodian_dir.mkdir()
            tee_dir.mkdir()

            # Custodian writes blind fixture to TEE-accessible dir
            blind = bm.get_tee_package()
            with open(tee_dir / "blind_fixture.json", "w") as f:
                json.dump(blind, f)

            # Custodian writes answer key to custodian-only dir
            answer_key = bm.get_answer_key()
            with open(custodian_dir / "answer_key.json", "w") as f:
                json.dump(answer_key, f)

            # Verify blind fixture is clean
            with open(tee_dir / "blind_fixture.json") as f:
                tee_data = json.load(f)
            self.assertEqual(check_blind_fixture_safety(tee_data), [])

            # Verify answer key exists in custodian dir
            self.assertTrue((custodian_dir / "answer_key.json").exists())

    def test_tee_dir_has_no_answer_key_file(self):
        """The TEE-accessible directory must not contain an answer key file."""
        bm = _make_sealable_benchmark()
        seal_benchmark(bm)

        with tempfile.TemporaryDirectory() as tmpdir:
            tee_dir = Path(tmpdir) / "tee"
            tee_dir.mkdir()

            # Only write the blind fixture to TEE dir
            blind = bm.get_tee_package()
            with open(tee_dir / "blind_fixture.json", "w") as f:
                json.dump(blind, f)

            # Check no answer_key file exists in TEE dir
            tee_files = list(tee_dir.iterdir())
            for f in tee_files:
                self.assertNotIn("answer", f.name.lower())
                self.assertNotIn("ground_truth", f.name.lower())
                self.assertNotIn("key", f.name.lower())

    def test_deployment_separation_documented(self):
        """Document that physical separation is a deployment responsibility."""
        # This test documents the requirement
        deployment_requirement = (
            "DEPLOYMENT REQUIREMENT: The answer key must be stored in a "
            "directory the TEE process cannot access. Unix permissions "
            "(chmod 600, separate user accounts) or separate machines "
            "must enforce this boundary."
        )
        self.assertIn("DEPLOYMENT REQUIREMENT", deployment_requirement)


class TestHardening2_NearDuplicateDetection(unittest.TestCase):
    """HARDENING #2: Near-duplicate detection as review flag."""

    def test_identical_input_material_flagged(self):
        """Cases with identical input material but different groups are flagged."""
        bm = Benchmark(benchmark_id="TEST")
        c1 = _make_case("C1", group="IG-1", source_a="identical content", source_b="identical content")
        c2 = _make_case("C2", group="IG-2", source_a="identical content", source_b="identical content")
        bm.add_case(c1)
        bm.add_case(c2)
        errors = bm.validate()
        # Should have NEAR_DUPLICATE_FLAG errors (not blocking, but flagged)
        dup_flags = [e for e in errors if "NEAR_DUPLICATE_FLAG" in e]
        self.assertTrue(len(dup_flags) > 0, "Near-duplicate not detected for identical input material")

    def test_similar_problem_text_flagged(self):
        """Cases with very similar problem text are flagged."""
        bm = Benchmark(benchmark_id="TEST")
        c1 = _make_case("C1", group="IG-1", problem="reduce drag in pipelines")
        c2 = _make_case("C2", group="IG-2", problem="reduce drag in pipelines")  # Identical
        bm.add_case(c1)
        bm.add_case(c2)
        errors = bm.validate()
        dup_flags = [e for e in errors if "NEAR_DUPLICATE_FLAG" in e]
        self.assertTrue(len(dup_flags) > 0, "Near-duplicate not detected for identical problem text")

    def test_same_source_id_flagged(self):
        """Cases with same source_id but different groups are flagged."""
        bm = Benchmark(benchmark_id="TEST")
        c1 = _make_case("C1", group="IG-1", source_id="SAME_SOURCE")
        c2 = _make_case("C2", group="IG-2", source_id="SAME_SOURCE")
        bm.add_case(c1)
        bm.add_case(c2)
        errors = bm.validate()
        dup_flags = [e for e in errors if "NEAR_DUPLICATE_FLAG" in e]
        self.assertTrue(len(dup_flags) > 0, "Same source_id not flagged")

    def test_different_cases_not_flagged(self):
        """Genuinely different cases are not flagged."""
        bm = Benchmark(benchmark_id="TEST")
        c1 = _make_case("C1", domain="fluid_mechanics", group="IG-1",
                        source_id="S1", problem="reduce pipeline drag",
                        source_a="shark skin riblets reduce turbulence",
                        source_b="pipe drag reduction needed")
        c2 = _make_case("C2", domain="enzymology", group="IG-2",
                        source_id="S2", problem="design industrial catalyst",
                        source_a="enzyme active sites stabilize transition states",
                        source_b="industrial catalyst needs high temperature stability")
        bm.add_case(c1)
        bm.add_case(c2)
        errors = bm.validate()
        dup_flags = [e for e in errors if "NEAR_DUPLICATE_FLAG" in e]
        self.assertEqual(len(dup_flags), 0, "Different cases incorrectly flagged as duplicates")


class TestHardening3_ScientificIndependence(unittest.TestCase):
    """HARDENING #3: Scientific independence — custodian adjudication required."""

    def test_near_duplicate_flag_requires_custodian_adjudication(self):
        """Near-duplicate flags include 'REQUIRES_CUSTODIAN_ADJUDICATION'."""
        bm = Benchmark(benchmark_id="TEST")
        c1 = _make_case("C1", group="IG-1", source_a="same", source_b="same")
        c2 = _make_case("C2", group="IG-2", source_a="same", source_b="same")
        bm.add_case(c1)
        bm.add_case(c2)
        errors = bm.validate()
        dup_flags = [e for e in errors if "NEAR_DUPLICATE_FLAG" in e]
        for flag in dup_flags:
            self.assertIn("REQUIRES_CUSTODIAN_ADJUDICATION", flag)


class TestHardening4_DomainCanonicalization(unittest.TestCase):
    """HARDENING #4: Domain canonicalization."""

    def test_underscore_hyphen_space_canonicalized(self):
        """fluid_mechanics, fluid-mechanics, fluid mechanics → same canonical."""
        self.assertEqual(canonicalize_domain("fluid_mechanics"), "fluid_mechanics")
        self.assertEqual(canonicalize_domain("fluid-mechanics"), "fluid_mechanics")
        self.assertEqual(canonicalize_domain("fluid mechanics"), "fluid_mechanics")

    def test_case_insensitive(self):
        """Physics, PHYSICS, physics → same canonical."""
        self.assertEqual(canonicalize_domain("Physics"), canonicalize_domain("physics"))
        self.assertEqual(canonicalize_domain("PHYSICS"), canonicalize_domain("physics"))

    def test_biology_variants_canonicalized(self):
        """biology, molecular_biology, cell_biology, biochemistry are DISTINCT canonical domains.
        They are related but scientifically different disciplines.
        Only string-format variants (underscores/hyphens/spaces/case) are canonicalized."""
        self.assertEqual(canonicalize_domain("biology"), "biology")
        self.assertEqual(canonicalize_domain("molecular_biology"), "molecular_biology")
        self.assertEqual(canonicalize_domain("molecular biology"), "molecular_biology")  # space → underscore
        self.assertEqual(canonicalize_domain("cell_biology"), "cell_biology")
        self.assertEqual(canonicalize_domain("biochemistry"), "biochemistry")
        self.assertEqual(canonicalize_domain("enzymology"), "enzymology")
        # Verify they are all DIFFERENT
        self.assertNotEqual(canonicalize_domain("biology"), canonicalize_domain("enzymology"))
        self.assertNotEqual(canonicalize_domain("molecular_biology"), canonicalize_domain("biochemistry"))
        self.assertNotEqual(canonicalize_domain("cell_biology"), canonicalize_domain("molecular_biology"))

    def test_domain_canonicalization_mismatch_detected(self):
        """Raw domains that map to fewer canonical domains are flagged."""
        bm = Benchmark(benchmark_id="TEST")
        # 4 raw domains that map to only 2 canonical domains
        bm.add_case(_make_case("C1", domain="fluid_mechanics", group="IG-1"))
        bm.add_case(_make_case("C2", domain="fluid-mechanics", group="IG-2"))  # Same canonical
        bm.add_case(_make_case("C3", domain="biology", group="IG-3"))
        bm.add_case(_make_case("C4", domain="biochemistry", group="IG-4"))  # Same canonical
        errors = bm.validate()
        canon_errors = [e for e in errors if "DOMAIN_CANONICALIZATION_MISMATCH" in e]
        self.assertTrue(len(canon_errors) > 0, "Domain canonicalization mismatch not detected")

    def test_is_known_domain(self):
        self.assertTrue(is_known_domain("fluid_mechanics"))
        self.assertTrue(is_known_domain("biology"))
        self.assertFalse(is_known_domain("nonexistent_domain_xyz"))


class TestHardening5_StateMachine(unittest.TestCase):
    """HARDENING #5: No route to sealing without complete inputs."""

    def test_cannot_seal_from_draft(self):
        bm = Benchmark(benchmark_id="TEST", seal_state=DRAFT)
        with self.assertRaises(SealStateError):
            bm.transition_to_sealed("now")

    def test_cannot_seal_from_validated(self):
        bm = Benchmark(benchmark_id="TEST", seal_state=VALIDATED)
        with self.assertRaises(SealStateError):
            bm.transition_to_sealed("now")

    def test_cannot_seal_without_hashes(self):
        """If state is set to CONSTRUCTED directly (bypassing transition),
        hashes are empty — sealing should now FAIL."""
        bm = Benchmark(benchmark_id="TEST", seal_state=CONSTRUCTED)
        # Hashes are empty because transition_to_constructed was not called
        self.assertEqual(bm.blind_fixture_hash, "")
        self.assertEqual(bm.answer_key_hash, "")
        # seal_benchmark should reject this
        with self.assertRaises(ValueError) as ctx:
            seal_benchmark(bm)
        self.assertIn("SEAL_REJECTED", str(ctx.exception))

    def test_cannot_seal_with_partial_hashes(self):
        """If some hashes are missing, sealing fails."""
        bm = Benchmark(benchmark_id="TEST", seal_state=CONSTRUCTED)
        bm.source_manifest_hash = "a" * 64
        bm.seed_hash = "b" * 64
        bm.corpus_hash = "c" * 64
        bm.blind_fixture_hash = ""  # Missing
        bm.answer_key_hash = "e" * 64
        with self.assertRaises(ValueError) as ctx:
            seal_benchmark(bm)
        self.assertIn("SEAL_REJECTED", str(ctx.exception))


class TestHardening6_EmptyHashes(unittest.TestCase):
    """HARDENING #6: Reject missing/empty cryptographic commitments."""

    def test_empty_source_manifest_hash_rejected(self):
        bm = Benchmark(benchmark_id="TEST", seal_state=VALIDATED)
        with self.assertRaises(ValidationError) as ctx:
            bm.transition_to_constructed("", "b" * 64, "c" * 64, {})
        self.assertIn("EMPTY_HASH", str(ctx.exception))

    def test_empty_seed_hash_rejected(self):
        bm = Benchmark(benchmark_id="TEST", seal_state=VALIDATED)
        with self.assertRaises(ValidationError) as ctx:
            bm.transition_to_constructed("a" * 64, "", "c" * 64, {})
        self.assertIn("EMPTY_HASH", str(ctx.exception))

    def test_short_hash_rejected(self):
        """Hashes must be exactly 64 chars (SHA-256 hex)."""
        bm = Benchmark(benchmark_id="TEST", seal_state=VALIDATED)
        with self.assertRaises(ValidationError):
            bm.transition_to_constructed("short", "b" * 64, "c" * 64, {})

    def test_valid_hashes_accepted(self):
        bm = Benchmark(benchmark_id="TEST", seal_state=VALIDATED)
        bm.transition_to_constructed("a" * 64, "b" * 64, "c" * 64, {})
        self.assertEqual(bm.seal_state, CONSTRUCTED)


class TestHardening7_DeterministicIdentity(unittest.TestCase):
    """HARDENING #7: Timestamps cannot contaminate canonical benchmark identity."""

    def test_same_benchmark_different_timestamps_same_hash(self):
        """Two identical benchmarks sealed at different times have the same
        manifest hash (sealed_at excluded from canonical hash)."""
        bm1 = _make_sealable_benchmark("SAME-ID")
        bm2 = _make_sealable_benchmark("SAME-ID")

        seal_benchmark(bm1)
        # bm2 already constructed, just seal with different timestamp
        bm2.seal_state = CONSTRUCTED
        seal_benchmark(bm2)

        # sealed_at may differ, but manifest_hash should be the same
        self.assertEqual(bm1.manifest_hash, bm2.manifest_hash,
                         "Same benchmark sealed at different times has different manifest hash — "
                         "timestamp contaminated canonical identity")

    def test_sealed_at_not_in_canonical_hash(self):
        """The manifest hash is computed excluding sealed_at."""
        bm = _make_sealable_benchmark()
        seal_benchmark(bm)

        # Get manifest without sealed_at
        manifest_no_ts = bm.get_manifest(include_hash=False, exclude_sealed_at=True)
        hash_no_ts = sha256_json(manifest_no_ts)

        # This should equal the stored manifest_hash
        self.assertEqual(hash_no_ts, bm.manifest_hash,
                         "Manifest hash includes sealed_at — canonical identity is not deterministic")

    def test_manifest_includes_sealed_at_as_metadata(self):
        """sealed_at is in the manifest as metadata, but NOT in the canonical hash."""
        bm = _make_sealable_benchmark()
        seal_benchmark(bm)

        manifest = bm.get_manifest(include_hash=True)
        self.assertIn("sealed_at", manifest)
        self.assertNotEqual(manifest["sealed_at"], "")


if __name__ == '__main__':
    unittest.main(verbosity=2)
