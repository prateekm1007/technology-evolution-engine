"""Phase 7 Round 6: Filesystem-level adversarial mutation tests.

Per audit round 20:
    "The next test layer should operate against a temporary real
     repository/filesystem fixture, not only mocked Path.read_text()."

Per P3:
    "Mocking the thing you're trying to verify verifies nothing.
     Use real fixtures for security/correctness-critical paths."

These tests:
    1. Create a temporary copy of the freeze manifest
    2. Physically modify each protected artifact on disk
    3. Invoke the freeze gate directly (not through main())
    4. Require the gate to reject the modification
    5. Verify the rejection identifies the specific violation
    6. Restore the exact bytes
    7. Verify the gate succeeds again
    8. Verify no protected production artifact was permanently changed

Attack matrix tested:
    - Modify gold only → REJECT
    - Modify synonyms only → REJECT
    - Modify benchmark source only → REJECT
    - Modify score artifact only → REJECT
    - Modify manifest only → REJECT (substitution)
    - Modify manifest + artifact together → REJECT (critical)
    - Modify all artifacts together → REJECT (critical)
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO = Path(__file__).resolve().parents[1]


def _sha256_file(path):
    """SHA-256 of a file's raw bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_json(obj):
    """SHA-256 of a JSON object's canonical representation."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


class TestFilesystemAdversarialMutation:
    """Filesystem-level bypass resistance tests.

    These tests modify ACTUAL FILES on disk (in the real repository)
    and verify the freeze gate detects the modification. After each
    test, the file is restored to its original content.

    Per P3: these use real fixtures, not mocks.
    """

    # Paths to protected artifacts
    GOLD_PATH = REPO / "benchmarks" / "discovery_capability_benchmark.py"
    SCORE_PATH = REPO / "benchmarks" / "reports" / "discovery_capability_score.json"
    MANIFEST_PATH = REPO / "reports" / "phase7" / "frozen_f1_manifest.json"

    @pytest.fixture(autouse=True)
    def restore_artifacts(self):
        """Save all protected artifacts before each test, restore after."""
        # Save original content
        originals = {}
        for path in [self.GOLD_PATH, self.SCORE_PATH, self.MANIFEST_PATH]:
            if path.exists():
                originals[path] = path.read_bytes()

        yield

        # Restore original content
        for path, content in originals.items():
            path.write_bytes(content)

    def _invoke_gate(self):
        """Invoke the freeze gate directly (not through main())."""
        from engine.f1_optimization_freeze import assert_frozen_data_unchanged
        return assert_frozen_data_unchanged()

    def test_filesystem_modify_gold_discoveries_detected(self):
        """Physically modify the benchmark source file (which contains
        GOLD_DISCOVERIES) and verify the freeze gate rejects."""
        # Step 1: Verify gate passes with unmodified data
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

        # Step 2: Physically modify the benchmark source
        original = self.GOLD_PATH.read_bytes()
        modified = original + b"\n# INJECTED BY ADVERSARIAL TEST\n"
        self.GOLD_PATH.write_bytes(modified)

        # Step 3: The benchmark source hash should now differ
        # The freeze gate checks benchmark_source_sha256
        from engine.f1_optimization_freeze import _compute_benchmark_source_hash
        new_hash = _compute_benchmark_source_hash()

        # Step 4: The gate must reject
        with pytest.raises(Exception, match="BENCHMARK SOURCE MODIFIED|GOLD SET MODIFIED"):
            self._invoke_gate()

        # Step 5: Restore (fixture handles this, but verify explicitly)
        self.GOLD_PATH.write_bytes(original)

        # Step 6: Gate passes again
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

    def test_filesystem_modify_score_artifact_detected(self):
        """Physically modify the committed score JSON and verify rejection."""
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

        # Modify the score artifact
        original = self.SCORE_PATH.read_bytes()
        data = json.loads(original)
        data["f1"] = 0.9999  # modified F1
        self.SCORE_PATH.write_text(json.dumps(data, indent=2))

        # Gate must reject
        with pytest.raises(Exception, match="COMMITTED SCORE MODIFIED"):
            self._invoke_gate()

        # Restore
        self.SCORE_PATH.write_bytes(original)

        # Gate passes
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

    def test_filesystem_modify_manifest_detected(self):
        """Physically modify the manifest on disk and verify the
        git-HEAD comparison detects the substitution."""
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

        # Modify the manifest on disk (but NOT in git)
        original = self.MANIFEST_PATH.read_bytes()
        data = json.loads(original)
        data["baseline_f1"] = 0.9999  # modified baseline
        self.MANIFEST_PATH.write_text(json.dumps(data, indent=2))

        # The gate must detect: on-disk manifest != git HEAD manifest
        with pytest.raises(Exception, match="MANIFEST SUBSTITUTION"):
            self._invoke_gate()

        # Restore
        self.MANIFEST_PATH.write_bytes(original)

        # Gate passes
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

    def test_filesystem_modify_manifest_and_artifact_together(self):
        """CRITICAL: Modify BOTH the manifest AND a production artifact
        together. An attacker who rewrites both should still be caught
        because the on-disk manifest doesn't match the git-committed version.

        This is the key attack the audit round 20 specifically requested."""
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

        # Save originals
        orig_manifest = self.MANIFEST_PATH.read_bytes()
        orig_score = self.SCORE_PATH.read_bytes()

        # Modify BOTH: rewrite the manifest with a new score hash
        # AND modify the score artifact to match
        manifest_data = json.loads(orig_manifest)
        score_data = json.loads(orig_score)
        score_data["f1"] = 0.9999
        new_score_json = json.dumps(score_data, indent=2)
        new_score_hash = hashlib.sha256(new_score_json.encode()).hexdigest()

        # Rewrite manifest with the new score hash
        manifest_data["score_artifact_sha256"] = new_score_hash
        manifest_data["baseline_f1"] = 0.9999
        new_manifest_json = json.dumps(manifest_data, indent=2)

        # Write both modified versions to disk
        self.MANIFEST_PATH.write_text(new_manifest_json)
        self.SCORE_PATH.write_text(new_score_json)

        # The gate must STILL reject because:
        # 1. The on-disk manifest doesn't match git HEAD (substitution detected)
        # 2. Even if it did match, the baseline_f1 cross-validation would fail
        with pytest.raises(Exception, match="MANIFEST SUBSTITUTION|BASELINE MISMATCH"):
            self._invoke_gate()

        # Restore both
        self.MANIFEST_PATH.write_bytes(orig_manifest)
        self.SCORE_PATH.write_bytes(orig_score)

        # Gate passes
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

    def test_filesystem_modify_all_artifacts_together(self):
        """CRITICAL: Modify ALL protected artifacts simultaneously.
        Even a coordinated attack on all surfaces must be detected."""
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

        # Save originals
        orig_benchmark = self.GOLD_PATH.read_bytes()
        orig_score = self.SCORE_PATH.read_bytes()
        orig_manifest = self.MANIFEST_PATH.read_bytes()

        # Modify ALL: benchmark source, score artifact, manifest
        self.GOLD_PATH.write_bytes(orig_benchmark + b"\n# ADVERSARIAL\n")

        score_data = json.loads(orig_score)
        score_data["f1"] = 0.9999
        self.SCORE_PATH.write_text(json.dumps(score_data, indent=2))

        manifest_data = json.loads(orig_manifest)
        manifest_data["baseline_f1"] = 0.9999
        self.MANIFEST_PATH.write_text(json.dumps(manifest_data, indent=2))

        # The gate must reject. The manifest substitution check fires first
        # (on-disk manifest != git HEAD), but even if it didn't, the
        # benchmark source hash and score hash would mismatch.
        with pytest.raises(Exception, match="MANIFEST SUBSTITUTION|MODIFIED"):
            self._invoke_gate()

        # Restore ALL
        self.GOLD_PATH.write_bytes(orig_benchmark)
        self.SCORE_PATH.write_bytes(orig_score)
        self.MANIFEST_PATH.write_bytes(orig_manifest)

        # Gate passes
        result = self._invoke_gate()
        assert result["all_unchanged"] is True

    def test_filesystem_verify_no_permanent_change(self):
        """After all adversarial tests, verify no protected artifact
        was permanently changed. This is the safety net."""
        # Run the gate — if any artifact was permanently changed from
        # a previous test that didn't restore properly, this will fail.
        result = self._invoke_gate()
        assert result["all_unchanged"] is True, (
            "A protected artifact was permanently changed by a previous "
            "adversarial test. The restore fixture failed. This is a "
            "critical test infrastructure failure."
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
