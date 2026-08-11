#!/usr/bin/env python3
"""
Test: Honesty Loop enforcement (Law 27, 28, 29).

Per the consolidated review post-BP-2:
    "gate score ≠ engineering truth"
    "confidence = 58% should disappear"
    "85.7% PASS should disappear"
    "complete blueprint should disappear"
    "Add Law 27: The Blueprint shall not assign numerical
     certainty to claims that lack repeated experimental
     validation."

This test verifies:
1. Law 27, 28, 29 are present in BLUEPRINT_CONSTITUTION.md
2. HONESTY_LOOP.md exists and defines the loop
3. All 10 priority engine .md files exist
4. AEP_PROTOCOL.md includes Gate 11 (Loop Closure)
5. scripts/enforce_law27.py exists and runs
6. The scanner detects forbidden language in a fixture file
7. The scanner accepts a clean fixture file
8. CI workflow includes the Law 27 gate
9. remember_governance.py includes HONESTY_LOOP.md in the read list
10. ENGINEERING_PRINCIPLES.md Principle 4 was amended
11. CODER_DIRECTIONS.md mentions the 18 required engines
"""

import json
import pathlib
import subprocess
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
FIXTURES_DIR = ROOT / "tests" / "fixtures"


# --------------------------------------------------------------------------
# Governance document tests
# --------------------------------------------------------------------------

class TestGovernanceDocuments:
    """Verify the Honesty Loop governance documents exist and contain the required content."""

    def test_blueprint_constitution_has_law_27(self):
        """BLUEPRINT_CONSTITUTION.md must contain Law 27."""
        content = (ROOT / "BLUEPRINT_CONSTITUTION.md").read_text()
        assert "LAW 27" in content, (
            "BLUEPRINT_CONSTITUTION.md does not contain Law 27. "
            "Law 27 forbids numerical certainty without experimental validation."
        )
        # Must mention the weather-forecast rationale
        assert "weather" in content.lower() or "rain" in content.lower(), (
            "Law 27 should cite the weather-forecast rationale: a forecast "
            "has decades of data; the Blueprint does not."
        )

    def test_blueprint_constitution_has_law_28(self):
        """BLUEPRINT_CONSTITUTION.md must contain Law 28 (forbidden language)."""
        content = (ROOT / "BLUEPRINT_CONSTITUTION.md").read_text()
        assert "LAW 28" in content, "BLUEPRINT_CONSTITUTION.md does not contain Law 28."
        # Must forbid "complete blueprint"
        assert "complete blueprint" in content.lower(), (
            "Law 28 should explicitly forbid 'complete blueprint'."
        )
        # Must forbid PASS / FAIL percentages
        assert "PASS" in content and "%" in content, (
            "Law 28 should explicitly forbid PASS/FAIL percentages."
        )

    def test_blueprint_constitution_has_law_29(self):
        """BLUEPRINT_CONSTITUTION.md must contain Law 29 (required typed enums)."""
        content = (ROOT / "BLUEPRINT_CONSTITUTION.md").read_text()
        assert "LAW 29" in content, "BLUEPRINT_CONSTITUTION.md does not contain Law 29."
        # Must define the 5 status values
        for status in ["PASS", "PASS_WITH_CONDITIONS", "MARGINAL", "BLOCKED", "REJECTED"]:
            assert status in content, f"Law 29 must define status: {status}"
        # Must define validation levels L0-L9
        for level in ["L0", "L4", "L9"]:
            assert level in content, f"Law 29 must define validation level: {level}"

    def test_honesty_loop_md_exists(self):
        """HONESTY_LOOP.md must exist at repo root."""
        path = ROOT / "HONESTY_LOOP.md"
        assert path.exists(), "HONESTY_LOOP.md does not exist at repo root."

    def test_honesty_loop_md_defines_loop_stages(self):
        """HONESTY_LOOP.md must define the 5 loop stages."""
        content = (ROOT / "HONESTY_LOOP.md").read_text()
        # The 5 stages
        for stage in ["READ", "SCAN", "REPLACE", "CLOSE", "RE-ENTER"]:
            assert stage in content, (
                f"HONESTY_LOOP.md must define loop stage: {stage}"
            )

    def test_honesty_loop_md_lists_10_engines(self):
        """HONESTY_LOOP.md must list all 10 priority engines."""
        content = (ROOT / "HONESTY_LOOP.md").read_text()
        # All 10 engine names should appear
        engines = [
            "Evidence Lineage",
            "Mass Stack-up",
            "Interface Control",
            "Procurement",
            "Validation Level",
            "Requirement Reconciliation",
            "Retraction Registry",
            "Test Registry",
            "Economic Reality",
            "Thermal Envelope",
        ]
        for engine in engines:
            assert engine in content, (
                f"HONESTY_LOOP.md must list the '{engine}' engine"
            )

    def test_engineering_principles_principle_4_amended(self):
        """Principle 4 in ENGINEERING_PRINCIPLES.md must be amended to forbid numerical certainty."""
        content = (ROOT / "ENGINEERING_PRINCIPLES.md").read_text()
        # Original Principle 4 said "Confidence is never 1.0"
        # Amended version should say "Numerical certainty is never assigned"
        assert "Numerical certainty is never assigned" in content, (
            "Principle 4 has not been amended. "
            "Original: 'Confidence is never 1.0'. "
            "Amended: 'Numerical certainty is never assigned to claims "
            "without repeated experimental validation.'"
        )

    def test_coder_directions_lists_18_engines(self):
        """CODER_DIRECTIONS.md must list 18 engines (8 original + 10 Honesty Loop)."""
        content = (ROOT / "CODER_DIRECTIONS.md").read_text()
        assert "18 required engines" in content, (
            "CODER_DIRECTIONS.md does not list 18 required engines. "
            "Should be 8 original + 10 Honesty Loop priority engines."
        )

    def test_coder_directions_removes_complete_blueprint(self):
        """CODER_DIRECTIONS.md must not contain 'complete blueprint' (forbidden by Law 28a)."""
        content = (ROOT / "CODER_DIRECTIONS.md").read_text()
        # Allowable: 'complete blueprint' inside fenced code blocks or as part of "Bad:" example
        # The scanner already enforces this; here we do a basic check.
        # Look for "complete blueprint" outside fenced code blocks
        lines = content.split("\n")
        in_code_block = False
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if stripped.startswith("Bad:"):
                continue
            assert "complete blueprint" not in line.lower(), (
                f"CODER_DIRECTIONS.md contains 'complete blueprint' outside "
                f"exempt contexts: {line!r}"
            )


# --------------------------------------------------------------------------
# 10 priority engine files
# --------------------------------------------------------------------------

class TestTenPriorityEngines:
    """Verify all 10 priority engine .md files exist."""

    REQUIRED_ENGINES = [
        ("EVIDENCE_LINEAGE_ENGINE.md", "Evidence Lineage", "P1"),
        ("MASS_STACKUP_ENGINE.md", "Mass Stack-up", "P2"),
        ("INTERFACE_CONTROL_ENGINE.md", "Interface Control", "P3"),
        ("PROCUREMENT_ENGINE.md", "Procurement", "P4"),
        ("VALIDATION_LEVEL_ENGINE.md", "Validation Level", "P5"),
        ("REQUIREMENT_RECONCILIATION_ENGINE.md", "Requirement Reconciliation", "P6"),
        ("RETRACTION_REGISTRY_ENGINE.md", "Retraction Registry", "P7"),
        ("TEST_REGISTRY_ENGINE.md", "Test Registry", "P8"),
        ("ECONOMIC_REALITY_ENGINE.md", "Economic Reality", "P9"),
        ("THERMAL_ENVELOPE_ENGINE.md", "Thermal Envelope", "P10"),
    ]

    @pytest.mark.parametrize("filename,name,priority", REQUIRED_ENGINES)
    def test_engine_file_exists(self, filename, name, priority):
        """Each priority engine must have its .md file at repo root."""
        path = ROOT / filename
        assert path.exists(), f"{filename} does not exist at repo root."

    @pytest.mark.parametrize("filename,name,priority", REQUIRED_ENGINES)
    def test_engine_file_has_schema(self, filename, name, priority):
        """Each engine file must include a TypeScript schema or interface block."""
        content = (ROOT / filename).read_text()
        # Look for either "interface" (TypeScript) or a "Schema" section
        assert "interface" in content or "Schema" in content or "schema" in content.lower(), (
            f"{filename} does not include a schema definition."
        )

    @pytest.mark.parametrize("filename,name,priority", REQUIRED_ENGINES)
    def test_engine_file_has_falsifier(self, filename, name, priority):
        """Each engine file must include a pre-stated falsifier (EP-4)."""
        content = (ROOT / filename).read_text()
        assert "falsifier" in content.lower(), (
            f"{filename} does not include a pre-stated falsifier (per EP-4)."
        )

    @pytest.mark.parametrize("filename,name,priority", REQUIRED_ENGINES)
    def test_engine_file_references_law_27(self, filename, name, priority):
        """Each engine file should reference Law 27 or the Honesty Loop."""
        content = (ROOT / filename).read_text()
        # Either Law 27, Law 28, Law 29, or HONESTY_LOOP
        references = ["Law 27", "Law 28", "Law 29", "HONESTY_LOOP"]
        assert any(ref in content for ref in references), (
            f"{filename} does not reference Law 27/28/29 or HONESTY_LOOP. "
            f"Each engine must ground itself in the Honesty Loop governance."
        )


# --------------------------------------------------------------------------
# AEP_PROTOCOL Gate 11
# --------------------------------------------------------------------------

class TestAEPGate11:
    """Verify AEP_PROTOCOL.md includes Gate 11 (Loop Closure)."""

    def test_aep_protocol_has_gate_11(self):
        """AEP_PROTOCOL.md must define Gate 11 (Loop Closure)."""
        content = (ROOT / "AEP_PROTOCOL.md").read_text()
        assert "Gate 11" in content, (
            "AEP_PROTOCOL.md does not define Gate 11 (Loop Closure Gate)."
        )
        assert "Loop Closure" in content, "Gate 11 must be named 'Loop Closure'."

    def test_aep_pipeline_lists_gate_11(self):
        """The pipeline diagram must include Gate 11."""
        content = (ROOT / "AEP_PROTOCOL.md").read_text()
        # The pipeline diagram should mention Gate 11
        assert "Gate 11" in content, "Pipeline diagram must list Gate 11."

    def test_aep_excellence_formula_updated(self):
        """The Excellence Formula must reference 11/11 gates, not 10/10."""
        content = (ROOT / "AEP_PROTOCOL.md").read_text()
        assert "11/11" in content, (
            "Excellence Formula must reference 11/11 gates passed (was 10/10)."
        )


# --------------------------------------------------------------------------
# Scanner tests
# --------------------------------------------------------------------------

class TestScanner:
    """Verify the forbidden-language scanner works correctly."""

    def test_scanner_script_exists(self):
        """scripts/enforce_law27.py must exist."""
        path = SCRIPTS_DIR / "enforce_law27.py"
        assert path.exists(), "scripts/enforce_law27.py does not exist."

    def test_scanner_runs_default_mode(self):
        """Scanner must run in default mode and exit 0 (no violations in non-grandfathered artifacts)."""
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "enforce_law27.py")],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        assert result.returncode == 0, (
            f"Scanner failed in default mode (exit {result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
        assert "STATUS: PASS" in result.stdout or "STATUS: REJECTED" in result.stdout, (
            "Scanner must print STATUS line."
        )

    def test_scanner_detects_forbidden_fixture(self):
        """Scanner must detect violations in the forbidden-language fixture file."""
        fixture = FIXTURES_DIR / "forbidden_language_blueprint.json"
        assert fixture.exists(), (
            f"Test fixture missing: {fixture}. "
            "Required to verify scanner detects forbidden patterns."
        )
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "enforce_law27.py"), str(fixture)],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        assert result.returncode == 1, (
            f"Scanner should exit 1 on forbidden-language fixture, got {result.returncode}:\n{result.stdout}"
        )
        # The fixture contains: "complete engineering blueprint", "85.7% PASS",
        # "confidence: 58%", "reliability: 92%", etc.
        # Verify at least 3 distinct pattern IDs were detected
        pattern_ids_detected = set()
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("[") and "]" in line:
                pid = line[1:line.index("]")]
                pattern_ids_detected.add(pid)
        assert len(pattern_ids_detected) >= 3, (
            f"Scanner detected only {len(pattern_ids_detected)} distinct patterns; "
            f"expected at least 3 from the fixture. Detected: {pattern_ids_detected}"
        )

    def test_scanner_accepts_clean_fixture(self):
        """Scanner must accept (exit 0) on a clean fixture file."""
        fixture = FIXTURES_DIR / "clean_language_blueprint.json"
        assert fixture.exists(), (
            f"Test fixture missing: {fixture}. "
            "Required to verify scanner accepts compliant artifacts."
        )
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "enforce_law27.py"), str(fixture)],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        assert result.returncode == 0, (
            f"Scanner should accept clean fixture (exit 0), got {result.returncode}:\n{result.stdout}"
        )

    def test_scanner_supports_json_output(self):
        """Scanner must support --json output for programmatic consumers."""
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "enforce_law27.py"), "--json"],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        # Default mode should produce valid JSON (possibly empty array)
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, list), "JSON output must be a list."
        except json.JSONDecodeError as e:
            pytest.fail(f"Scanner --json output is not valid JSON: {e}\nstdout: {result.stdout}")

    def test_scanner_supports_full_mode(self):
        """Scanner must support --full mode for honest audit of the entire repo."""
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "enforce_law27.py"), "--full"],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        # --full mode without --strict should exit 0 (informational)
        assert result.returncode == 0, (
            f"--full mode should exit 0 (informational), got {result.returncode}"
        )
        assert "FULL" in result.stdout, "Scanner must label output as FULL mode."

    def test_scanner_detects_each_pattern_class(self):
        """Scanner must detect at least one of each pattern class (A, B, C, E)."""
        fixture = FIXTURES_DIR / "forbidden_language_blueprint.json"
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "enforce_law27.py"), "--json", str(fixture)],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"JSON parse failed: {result.stdout}")
        pattern_classes = {v["pattern_id"][0] for v in data}
        # The fixture contains A (complete blueprint), B (confidence), C (PASS%), E (probability)
        for cls in ["A", "B", "C", "E"]:
            assert cls in pattern_classes, (
                f"Scanner failed to detect pattern class {cls}. "
                f"Detected classes: {pattern_classes}. "
                f"Violations: {data}"
            )


# --------------------------------------------------------------------------
# CI workflow tests
# --------------------------------------------------------------------------

class TestCIWorkflow:
    """Verify the CI workflow enforces the Honesty Loop."""

    def test_ci_workflow_exists(self):
        """.github/workflows/ci.yml must exist."""
        path = ROOT / ".github" / "workflows" / "ci.yml"
        assert path.exists(), "CI workflow does not exist."

    def test_ci_includes_honesty_loop_gate(self):
        """CI must include the enforce_law27.py gate."""
        content = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        assert "enforce_law27.py" in content, (
            "CI workflow must run scripts/enforce_law27.py as a gate."
        )
        assert "Honesty Loop" in content, (
            "CI workflow must reference the Honesty Loop gate by name."
        )

    def test_ci_includes_remember_governance_with_honesty_loop(self):
        """remember_governance.py must include HONESTY_LOOP.md in the read list."""
        content = (SCRIPTS_DIR / "remember_governance.py").read_text()
        assert "HONESTY_LOOP.md" in content, (
            "remember_governance.py must list HONESTY_LOOP.md in the read list."
        )


# --------------------------------------------------------------------------
# Honesty Loop closure simulation
# --------------------------------------------------------------------------

class TestHonestyLoopClosure:
    """End-to-end test: simulate the loop closing on a clean artifact."""

    def test_clean_artifact_passes_all_loop_checks(self):
        """A clean artifact should pass all 5 Gate 11 checks."""
        # Check 1: scanner runs clean on the clean fixture
        fixture = FIXTURES_DIR / "clean_language_blueprint.json"
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "enforce_law27.py"), str(fixture)],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        assert result.returncode == 0, (
            f"Check 1 (scanner) failed on clean fixture:\n{result.stdout}"
        )

        # Check 2: clean fixture has typed claim wrappers (Law 29e)
        data = json.loads(fixture.read_text())
        artifact = data["cleanBlueprintArtifact"]
        assert "packageMaturity" in artifact, (
            "Check 3 (package maturity) failed: clean artifact must declare packageMaturity."
        )
        for claim in artifact.get("claims", []):
            for field in ["validationLevel", "evidenceStrength", "experimentalValidation", "status", "evidenceIds"]:
                assert field in claim, (
                    f"Check 2 (typed wrappers) failed: claim missing required field '{field}': {claim}"
                )

    def test_forbidden_artifact_fails_loop_closure(self):
        """A forbidden artifact should fail Gate 11."""
        fixture = FIXTURES_DIR / "forbidden_language_blueprint.json"
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "enforce_law27.py"), str(fixture)],
            capture_output=True, text=True, cwd=str(ROOT)
        )
        assert result.returncode == 1, (
            "Forbidden artifact should fail Gate 11 (scanner should exit 1)."
        )


# --------------------------------------------------------------------------
# Document cross-references
# --------------------------------------------------------------------------

class TestCrossReferences:
    """Verify documents reference each other correctly."""

    def test_honesty_loop_references_all_engines(self):
        """HONESTY_LOOP.md must reference all 10 engine files by name."""
        content = (ROOT / "HONESTY_LOOP.md").read_text()
        for engine_file in [
            "EVIDENCE_LINEAGE_ENGINE.md",
            "MASS_STACKUP_ENGINE.md",
            "INTERFACE_CONTROL_ENGINE.md",
            "PROCUREMENT_ENGINE.md",
            "VALIDATION_LEVEL_ENGINE.md",
            "REQUIREMENT_RECONCILIATION_ENGINE.md",
            "RETRACTION_REGISTRY_ENGINE.md",
            "TEST_REGISTRY_ENGINE.md",
            "ECONOMIC_REALITY_ENGINE.md",
            "THERMAL_ENVELOPE_ENGINE.md",
        ]:
            assert engine_file in content, (
                f"HONESTY_LOOP.md must reference {engine_file}."
            )

    def test_aep_protocol_references_honesty_loop(self):
        """AEP_PROTOCOL.md must reference HONESTY_LOOP.md."""
        content = (ROOT / "AEP_PROTOCOL.md").read_text()
        assert "HONESTY_LOOP.md" in content or "HONESTY_LOOP" in content, (
            "AEP_PROTOCOL.md must reference HONESTY_LOOP.md (Gate 11 depends on it)."
        )

    def test_coder_directions_references_honesty_loop(self):
        """CODER_DIRECTIONS.md must reference HONESTY_LOOP.md."""
        content = (ROOT / "CODER_DIRECTIONS.md").read_text()
        assert "HONESTY_LOOP.md" in content or "HONESTY_LOOP" in content, (
            "CODER_DIRECTIONS.md must reference HONESTY_LOOP.md."
        )

    def test_blueprint_constitution_references_law_27_in_honesty_loop(self):
        """HONESTY_LOOP.md must reference Law 27, 28, 29."""
        content = (ROOT / "HONESTY_LOOP.md").read_text()
        for law in ["Law 27", "Law 28", "Law 29"]:
            assert law in content, (
                f"HONESTY_LOOP.md must reference {law}."
            )
