"""Phase 7 Round 7: Isolated temporary-repository filesystem adversarial tests.

Per audit round 21:
    "Build an actual isolated fixture: Temporary repository with .git/,
     frozen artifacts, and a real Git commit. Point the freeze module's
     repository root at that temporary repo WITHOUT mocking the integrity
     mechanism itself."

Per P3:
    "Mocking the thing you're trying to verify verifies nothing.
     Use real fixtures for security/correctness-critical paths."

Per P4:
    "State files are a claim about reality, not a diary of intentions."

SCIENTIFIC SCOPE (per audit round 22):
    These tests prove: "The freeze MECHANISM rejects filesystem mutations
    relative to an independently committed Git HEAD in an isolated real
    repository."

    These tests do NOT prove: "The production frozen artifacts are
    independently trustworthy." That latter claim depends on the
    provenance work already audited (Phases 3-6).

MUTATION SURFACES (per audit round 22):
    BRIDGE_SYNONYMS is defined INSIDE discovery_capability_benchmark.py,
    not as a separately protected file. The synonym test modifies that
    same benchmark-source surface. The accurate statement is:

    "All identified mutation classes tested at filesystem level, including
     synonym mutation within the benchmark-source surface."

    NOT: "All 5 independently protected filesystem surfaces tested."

Protected mutation classes:
    1. benchmark-source content (includes GOLD_DISCOVERIES, BRIDGE_SYNONYMS,
       matcher logic, F1 formula, thresholds)
    2. score artifact
    3. manifest
    4. coordinated manifest + score attack
    5. coordinated multi-artifact attack
    6. synonym mutation (within the benchmark-source surface, exercised
       as a distinct semantic mutation class)

These tests:
    1. Create a TEMPORARY directory (not the real working tree)
    2. Copy the exact frozen artifacts into it
    3. Initialize a real git repo and commit the pristine fixture
    4. Load the freeze module from the temp repo (NOT by mocking the
       integrity mechanism)
    5. Run the gate on pristine → PASS
    6. Physically mutate each artifact → direct invocation → FAIL
    7. Restore → PASS
    8. Mutate manifest + artifact together → FAIL
    9. Mutate all artifacts → FAIL
    10. Verify SHA-256 equality with original after restoration
    11. Delete the temporary repository
    12. Confirm the real project working tree was NEVER touched

The real project working tree is NEVER modified. All mutations happen
in the temporary fixture. The freeze gate runs against the temporary
repo's git HEAD, not the real repo's HEAD.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REAL_REPO = Path(__file__).resolve().parents[1]


class TempFreezeFixture:
    """An isolated temporary repository for freeze-gate testing.

    Creates a real git repo with the frozen artifacts, allows physical
    mutation, and cleans up automatically. The real project working
    tree is NEVER touched.
    """

    def __init__(self):
        self.temp_dir = None
        self.repo_dir = None
        self.original_cwd = None

        # Paths within the temp repo
        self.benchmark_path = None
        self.score_path = None
        self.manifest_path = None
        self.bootstrap_path = None

        # Original hashes for verification
        self.original_hashes = {}

    def setup(self):
        """Create the temporary repository with frozen artifacts."""
        self.temp_dir = tempfile.mkdtemp(prefix="freeze_test_")
        self.repo_dir = Path(self.temp_dir)
        self.original_cwd = os.getcwd()

        # Create directory structure
        (self.repo_dir / "benchmarks" / "reports").mkdir(parents=True, exist_ok=True)
        (self.repo_dir / "reports" / "phase7").mkdir(parents=True, exist_ok=True)
        (self.repo_dir / "engine").mkdir(parents=True, exist_ok=True)
        (self.repo_dir / "programs" / "A_metrology").mkdir(parents=True, exist_ok=True)

        # Copy frozen artifacts from the real repo
        real_benchmark = REAL_REPO / "benchmarks" / "discovery_capability_benchmark.py"
        real_score = REAL_REPO / "benchmarks" / "reports" / "discovery_capability_score.json"
        real_manifest = REAL_REPO / "reports" / "phase7" / "frozen_f1_manifest.json"
        real_freeze_module = REAL_REPO / "engine" / "f1_optimization_freeze.py"
        real_enforcer = REAL_REPO / "engine" / "epistemic_state_enforcer.py"
        real_bootstrap = REAL_REPO / "programs" / "A_metrology" / "bootstrap_statistics.py"

        self.benchmark_path = self.repo_dir / "benchmarks" / "discovery_capability_benchmark.py"
        self.score_path = self.repo_dir / "benchmarks" / "reports" / "discovery_capability_score.json"
        self.manifest_path = self.repo_dir / "reports" / "phase7" / "frozen_f1_manifest.json"
        self.bootstrap_path = self.repo_dir / "programs" / "A_metrology" / "bootstrap_statistics.py"

        shutil.copy2(real_benchmark, self.benchmark_path)
        shutil.copy2(real_score, self.score_path)
        shutil.copy2(real_manifest, self.manifest_path)
        shutil.copy2(real_freeze_module, self.repo_dir / "engine" / "f1_optimization_freeze.py")
        shutil.copy2(real_enforcer, self.repo_dir / "engine" / "epistemic_state_enforcer.py")
        shutil.copy2(real_bootstrap, self.bootstrap_path)

        # Copy the quarantine manifest (needed by epistemic_state_enforcer)
        real_quarantine = REAL_REPO / "reports" / "phase5" / "forbidden_metrics_quarantine.json"
        if real_quarantine.exists():
            (self.repo_dir / "reports" / "phase5").mkdir(parents=True, exist_ok=True)
            shutil.copy2(real_quarantine, self.repo_dir / "reports" / "phase5" / "forbidden_metrics_quarantine.json")

        # Copy the phase4 inventory (also needed by enforcer)
        real_inventory = REAL_REPO / "reports" / "phase4" / "metric_inventory.json"
        if real_inventory.exists():
            (self.repo_dir / "reports" / "phase4").mkdir(parents=True, exist_ok=True)
            shutil.copy2(real_inventory, self.repo_dir / "reports" / "phase4" / "metric_inventory.json")

        # Create __init__.py files for packages
        (self.repo_dir / "engine" / "__init__.py").touch()
        (self.repo_dir / "benchmarks" / "__init__.py").touch()
        (self.repo_dir / "programs" / "__init__.py").touch()
        (self.repo_dir / "programs" / "A_metrology" / "__init__.py").touch()

        # Record original hashes
        self.original_hashes = {
            "benchmark": self._sha256(self.benchmark_path),
            "score": self._sha256(self.score_path),
            "manifest": self._sha256(self.manifest_path),
        }

        # Initialize git repo and commit
        os.chdir(self.repo_dir)
        subprocess.run(["git", "init"], capture_output=True, check=True)
        subprocess.run(["git", "add", "-A"], capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "freeze test fixture"], capture_output=True, check=True)

    def teardown(self):
        """Clean up the temporary repository and restore CWD."""
        if self.original_cwd:
            os.chdir(self.original_cwd)
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _sha256(self, path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def save_artifact(self, path):
        """Save artifact content for later restoration."""
        return path.read_bytes()

    def restore_artifact(self, path, content):
        """Restore artifact to saved content."""
        path.write_bytes(content)

    def modify_file(self, path, modification_func):
        """Physically modify a file on disk."""
        content = path.read_bytes()
        modified = modification_func(content)
        path.write_bytes(modified)

    def invoke_gate(self):
        """Invoke the freeze gate against the temporary repo.

        This loads the freeze module directly from the temp repo's file
        path (not via package import), so it resolves REPO to the temp
        directory. The integrity mechanism itself is NOT mocked.
        """
        import importlib.util

        # Clear ALL cached engine modules to force fresh load
        mods_to_clear = [k for k in list(sys.modules)
                         if "f1_optimization_freeze" in k
                         or "epistemic_state_enforcer" in k
                         or k == "engine"
                         or (k.startswith("engine.") and "." not in k[7:])]
        for mod in mods_to_clear:
            del sys.modules[mod]

        # Load the freeze module from the temp repo's file path
        freeze_path = self.repo_dir / "engine" / "f1_optimization_freeze.py"
        spec = importlib.util.spec_from_file_location(
            "f1_optimization_freeze_isolated", freeze_path
        )
        module = importlib.util.module_from_spec(spec)

        # We need the engine package to be resolvable for the enforcer import
        # inside the freeze module. Add the temp repo to sys.path.
        sys.path.insert(0, str(self.repo_dir))

        # Also need to make 'engine' resolvable as a package from temp repo
        # Create a minimal engine package
        engine_init = self.repo_dir / "engine" / "__init__.py"
        engine_init.touch(exist_ok=True)

        spec.loader.exec_module(module)

        # Clean up sys.path
        sys.path.remove(str(self.repo_dir))

        return module.assert_frozen_data_unchanged()


@pytest.fixture
def freeze_fixture():
    """Create and tear down an isolated temporary freeze fixture."""
    fixture = TempFreezeFixture()
    fixture.setup()
    yield fixture
    fixture.teardown()


class TestIsolatedFilesystemAdversarial:
    """Filesystem-level adversarial tests in an ISOLATED temporary repository.

    Per audit round 21:
    > "Build an actual isolated fixture. The real project working tree
    >  is NEVER touched."
    """

    def test_pristine_fixture_passes_gate(self, freeze_fixture):
        """Step 5: Run the gate on the pristine fixture → PASS."""
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

    def test_modify_benchmark_source_detected(self, freeze_fixture):
        """Physically modify the benchmark source file (which contains
        GOLD_DISCOVERIES, BRIDGE_SYNONYMS, matcher logic, F1 formula)
        in the TEMPORARY repo and verify rejection.

        Note: GOLD_DISCOVERIES is defined INSIDE discovery_capability_benchmark.py
        (not a separate data file). Modifying this source file changes
        both the gold data and the benchmark logic. The benchmark_source_sha256
        in the manifest detects any modification to this file.
        """
        # Pristine passes
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

        # Physically modify the benchmark source
        orig = freeze_fixture.save_artifact(freeze_fixture.benchmark_path)
        freeze_fixture.modify_file(
            freeze_fixture.benchmark_path,
            lambda c: c + b"\n# ADVERSARIAL INJECTION\n"
        )

        # Gate must reject
        with pytest.raises(Exception, match="BENCHMARK SOURCE MODIFIED"):
            freeze_fixture.invoke_gate()

        # Restore
        freeze_fixture.restore_artifact(freeze_fixture.benchmark_path, orig)

        # Gate passes again
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

    def test_modify_score_artifact_detected(self, freeze_fixture):
        """Physically modify discovery_capability_score.json → REJECT."""
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

        orig = freeze_fixture.save_artifact(freeze_fixture.score_path)
        data = json.loads(orig)
        data["f1"] = 0.9999
        freeze_fixture.score_path.write_text(json.dumps(data, indent=2))

        with pytest.raises(Exception, match="COMMITTED SCORE MODIFIED"):
            freeze_fixture.invoke_gate()

        freeze_fixture.restore_artifact(freeze_fixture.score_path, orig)

        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

    def test_modify_manifest_detected(self, freeze_fixture):
        """Physically modify frozen_f1_manifest.json on disk → REJECT
        (manifest substitution: disk != git HEAD)."""
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

        orig = freeze_fixture.save_artifact(freeze_fixture.manifest_path)
        data = json.loads(orig)
        data["baseline_f1"] = 0.9999
        freeze_fixture.manifest_path.write_text(json.dumps(data, indent=2))

        with pytest.raises(Exception, match="MANIFEST SUBSTITUTION"):
            freeze_fixture.invoke_gate()

        freeze_fixture.restore_artifact(freeze_fixture.manifest_path, orig)

        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

    def test_modify_synonyms_detected(self, freeze_fixture):
        """Physically modify BRIDGE_SYNONYMS (inside the benchmark source)
        → REJECT.

        BRIDGE_SYNONYMS is defined at line 68 of discovery_capability_benchmark.py
        as `BRIDGE_SYNONYMS = {}`. Modifying it (e.g., adding an entry)
        changes the benchmark source hash, which the freeze gate detects.

        This test specifically targets the synonym mutation surface that
        was missing from Round 6 (audit round 21).
        """
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

        orig = freeze_fixture.save_artifact(freeze_fixture.benchmark_path)
        content = orig.decode("utf-8")

        # Modify BRIDGE_SYNONYMS from {} to {"test": {"synonym"}}
        modified_content = content.replace(
            "BRIDGE_SYNONYMS = {}",
            'BRIDGE_SYNONYMS = {"test": {"synonym"}}',
        )
        # If the replacement didn't work (formatting difference), try alternatives
        if modified_content == content:
            modified_content = content.replace(
                "BRIDGE_SYNONYMS={}",
                'BRIDGE_SYNONYMS={"test": {"synonym"}}',
            )

        freeze_fixture.benchmark_path.write_bytes(modified_content.encode("utf-8"))

        with pytest.raises(Exception, match="BENCHMARK SOURCE MODIFIED|SYNONYM"):
            freeze_fixture.invoke_gate()

        freeze_fixture.restore_artifact(freeze_fixture.benchmark_path, orig)

        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

    def test_modify_manifest_and_artifact_together(self, freeze_fixture):
        """CRITICAL: Modify BOTH manifest AND score artifact simultaneously
        in the temporary repo.

        An attacker who rewrites both the manifest (with new hash) and the
        score artifact (to match) should STILL be caught because the
        on-disk manifest doesn't match the git-committed version at HEAD.
        """
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

        orig_manifest = freeze_fixture.save_artifact(freeze_fixture.manifest_path)
        orig_score = freeze_fixture.save_artifact(freeze_fixture.score_path)

        # Rewrite manifest with new score hash + new baseline
        manifest_data = json.loads(orig_manifest)
        score_data = json.loads(orig_score)
        score_data["f1"] = 0.9999
        new_score_json = json.dumps(score_data, indent=2)
        new_score_hash = hashlib.sha256(new_score_json.encode()).hexdigest()
        manifest_data["score_artifact_sha256"] = new_score_hash
        manifest_data["baseline_f1"] = 0.9999

        # Write both modified versions
        freeze_fixture.manifest_path.write_text(json.dumps(manifest_data, indent=2))
        freeze_fixture.score_path.write_text(new_score_json)

        with pytest.raises(Exception, match="MANIFEST SUBSTITUTION|BASELINE MISMATCH"):
            freeze_fixture.invoke_gate()

        # Restore both
        freeze_fixture.restore_artifact(freeze_fixture.manifest_path, orig_manifest)
        freeze_fixture.restore_artifact(freeze_fixture.score_path, orig_score)

        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

    def test_modify_all_artifacts_together(self, freeze_fixture):
        """CRITICAL: Modify ALL protected artifacts simultaneously
        in the temporary repo."""
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

        orig_benchmark = freeze_fixture.save_artifact(freeze_fixture.benchmark_path)
        orig_score = freeze_fixture.save_artifact(freeze_fixture.score_path)
        orig_manifest = freeze_fixture.save_artifact(freeze_fixture.manifest_path)

        # Modify ALL
        freeze_fixture.benchmark_path.write_bytes(orig_benchmark + b"\n# ADVERSARIAL\n")
        score_data = json.loads(orig_score)
        score_data["f1"] = 0.9999
        freeze_fixture.score_path.write_text(json.dumps(score_data, indent=2))
        manifest_data = json.loads(orig_manifest)
        manifest_data["baseline_f1"] = 0.9999
        freeze_fixture.manifest_path.write_text(json.dumps(manifest_data, indent=2))

        with pytest.raises(Exception, match="MANIFEST SUBSTITUTION|MODIFIED"):
            freeze_fixture.invoke_gate()

        # Restore ALL
        freeze_fixture.restore_artifact(freeze_fixture.benchmark_path, orig_benchmark)
        freeze_fixture.restore_artifact(freeze_fixture.score_path, orig_score)
        freeze_fixture.restore_artifact(freeze_fixture.manifest_path, orig_manifest)

        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

    def test_sha256_equality_after_restoration(self, freeze_fixture):
        """Verify exact SHA-256 equality with original fixture after
        all mutation+restoration cycles."""
        # Run gate on pristine
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

        # Mutate and restore each artifact
        for path, name in [
            (freeze_fixture.benchmark_path, "benchmark"),
            (freeze_fixture.score_path, "score"),
            (freeze_fixture.manifest_path, "manifest"),
        ]:
            orig = freeze_fixture.save_artifact(path)
            orig_hash = freeze_fixture._sha256(path)

            # Mutate
            path.write_bytes(orig + b"\n# TEMP MUTATION\n")

            # Restore
            freeze_fixture.restore_artifact(path, orig)

            # Verify exact SHA-256 equality
            restored_hash = freeze_fixture._sha256(path)
            assert restored_hash == orig_hash, (
                f"{name}: SHA-256 mismatch after restoration. "
                f"Original: {orig_hash[:16]}..., Restored: {restored_hash[:16]}..."
            )

        # Gate passes after all restorations
        result = freeze_fixture.invoke_gate()
        assert result["all_unchanged"] is True

    def test_real_working_tree_never_touched(self, freeze_fixture):
        """Verify the real project working tree was NEVER modified.

        This test records the SHA-256 of real repo files at the start,
        performs mutations in the temp fixture, then verifies the real
        repo files are unchanged.
        """
        # Record real repo file hashes BEFORE temp fixture operations
        real_files = {
            "benchmark": REAL_REPO / "benchmarks" / "discovery_capability_benchmark.py",
            "score": REAL_REPO / "benchmarks" / "reports" / "discovery_capability_score.json",
            "manifest": REAL_REPO / "reports" / "phase7" / "frozen_f1_manifest.json",
        }
        real_hashes_before = {}
        for name, path in real_files.items():
            h = hashlib.sha256()
            with open(path, "rb") as f:
                h.update(f.read())
            real_hashes_before[name] = h.hexdigest()

        # Perform mutations in the temp fixture
        orig = freeze_fixture.save_artifact(freeze_fixture.benchmark_path)
        freeze_fixture.benchmark_path.write_bytes(orig + b"\n# TEMP\n")
        try:
            freeze_fixture.invoke_gate()  # will raise — that's expected
        except Exception:
            pass  # The gate correctly rejected the mutation
        freeze_fixture.restore_artifact(freeze_fixture.benchmark_path, orig)

        # Verify real repo files are UNCHANGED
        for name, path in real_files.items():
            h = hashlib.sha256()
            with open(path, "rb") as f:
                h.update(f.read())
            real_hash_after = h.hexdigest()
            assert real_hash_after == real_hashes_before[name], (
                f"Real repo file {name} was modified! "
                f"Before: {real_hashes_before[name][:16]}..., "
                f"After: {real_hash_after[:16]}... "
                f"The test must NEVER touch the real working tree."
            )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
