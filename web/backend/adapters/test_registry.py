"""
Test Registry — Honesty Loop Priority 8 engine (code implementation).

Per TEST_REGISTRY_ENGINE.md (specification):
- Append-only ledger of every test run against a Blueprint claim.
- Three test types: ANALYTICAL_ESTIMATE, NUMERICAL_SIMULATION,
  PHYSICAL_VALIDATION. Per Law 28d, these cannot be conflated.
- Each test has pre-stated pass criteria (EP-6 — committed before
  the test runs, not alongside the results).
- FAIL is a valid result (Law 4 — failure is an asset). FAIL is not
  hidden; the affected claim is retracted via P7.
- Every test links to evidence (P1 Evidence Lineage).

Per CONSTITUTION.md Law 7 (Historical Permanence):
- The registry is append-only. A test record, once written, cannot be
  edited. If a test is re-run, a new TR-XXX is created; the old one is
  marked SUPERSEDED with a reference to the new one.

Per Law 27 (Honesty Loop):
- Each test record carries a typed epistemic_status block, not a
  numerical confidence. Tests are facts about what was measured; their
  validation level depends on the test type:
    ANALYTICAL_ESTIMATE -> L2 (analytical estimate from first principles)
    NUMERICAL_SIMULATION -> L3 (numerical model, governing equations solved)
    PHYSICAL_VALIDATION -> L4-L9 (depending on test scale)

Schema (per TEST_REGISTRY_ENGINE.md §Schema):
    interface TestRecord {
        id: string                    # TR-XXX, immutable
        testType: enum
        testName: string
        claimId: string               # CL-XXX
        validationLevelTarget: enum
        method: {
            analyticalModel?: string
            numericalModel?: {...}
            physicalTest?: {...}
        }
        result: {
            status: enum
            measuredValue?: string
            expectedValue: string
            passCriteria: string       # pre-stated (EP-6)
            dateRun?: string
            runBy?: string
            rawDataPath?: string
            analysisPath?: string
        }
        evidenceId: string            # EV-XXX (P1)
        retractionId?: string         # if result retracted (P7)
        status: enum                  # overall record status
        immutable: true
        epistemic_status: {...}       # typed block (Law 27)
    }

Storage:
- JSONL at data/tests/tests.jsonl (append-only, mirrors P7 Retraction
  Registry and the prediction ledger pattern).
"""
from __future__ import annotations

import json
import pathlib
import re
import datetime
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "data" / "tests" / "tests.jsonl"

# Test types per spec (Law 28d — cannot be conflated)
TEST_TYPES = frozenset({
    "ANALYTICAL_ESTIMATE",
    "NUMERICAL_SIMULATION",
    "PHYSICAL_VALIDATION",
})

# Result status per test (Law 29a verdict enum + NOT_RUN for planned tests)
RESULT_STATUS_VALUES = frozenset({
    "PASS",
    "PASS_WITH_CONDITIONS",
    "MARGINAL",
    "FAIL",
    "BLOCKED",
    "NOT_RUN",
})

# Overall record status
RECORD_STATUS_VALUES = frozenset({
    "PASS",
    "PASS_WITH_CONDITIONS",
    "MARGINAL",
    "BLOCKED",
    "REJECTED",
    "SUPERSEDED",
})

# Validation level targets per test type (per TEST_REGISTRY_ENGINE.md)
VALIDATION_LEVEL_TARGETS = frozenset({
    "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"
})

# Map test type to the validation level it can support.
# Per TEST_REGISTRY_ENGINE.md:
#   ANALYTICAL_ESTIMATE -> L2
#   NUMERICAL_SIMULATION -> L3
#   PHYSICAL_VALIDATION -> L4-L9 (depending on scale)
TEST_TYPE_TO_VALIDATION_LEVEL = {
    "ANALYTICAL_ESTIMATE": "L2",
    "NUMERICAL_SIMULATION": "L3",
    # PHYSICAL_VALIDATION varies (L4-L9) — caller specifies
}

# Map test type to evidence strength (per Law 29c)
# Analytical estimates: WEAK (no external evidence, just the model)
# Numerical simulations: MODERATE (governing equations, but unvalidated)
# Physical validations: STRONG or VERY_STRONG (depends on scale)
TEST_TYPE_TO_EVIDENCE_STRENGTH = {
    "ANALYTICAL_ESTIMATE": "WEAK",
    "NUMERICAL_SIMULATION": "MODERATE",
    # PHYSICAL_VALIDATION: caller specifies (STRONG or VERY_STRONG)
}

# ID format: TR-XXX where XXX is a zero-padded sequential number
ID_PATTERN = re.compile(r"^TR-(\d{3,})$")


class TestRegistry:
    """Append-only registry of tests run against Blueprint claims.

    Per Law 7 (Historical Permanence): once written, a test record
    cannot be edited or deleted. The only valid mutation is appending
    a new record that supersedes an existing one (with the existing
    record's status updated to SUPERSEDED in memory — the file record
    is unchanged, append-only).
    """

    def __init__(self, registry_path: pathlib.Path = REGISTRY_PATH):
        self.path = pathlib.Path(registry_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def list_tests(self) -> list[dict]:
        """Return all test records, oldest first."""
        if not self.path.exists():
            return []
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def count(self) -> int:
        """Return the number of test records."""
        return len(self.list_tests())

    def get(self, test_id: str) -> Optional[dict]:
        """Return a single test by ID, or None if not found."""
        for t in self.list_tests():
            if t.get("id") == test_id:
                return t
        return None

    def by_claim(self, claim_id: str) -> list[dict]:
        """Return all tests for a given claim ID."""
        return [t for t in self.list_tests() if t.get("claim_id") == claim_id]

    def by_type(self, test_type: str) -> list[dict]:
        """Return all tests of a given type."""
        return [t for t in self.list_tests() if t.get("test_type") == test_type]

    def failed(self) -> list[dict]:
        """Return all tests with result.status == FAIL.

        Per Law 4 (failure is an asset): FAIL is not hidden. The
        affected claim should be retracted via P7 Retraction Registry.
        """
        return [t for t in self.list_tests()
                if t.get("result", {}).get("status") == "FAIL"]

    def not_run(self) -> list[dict]:
        """Return all tests with result.status == NOT_RUN.

        These are planned tests that have not yet been executed. Makes
        the test plan visible — prevents the 'we forgot to test that'
        failure.
        """
        return [t for t in self.list_tests()
                if t.get("result", {}).get("status") == "NOT_RUN"]

    def summary(self) -> dict:
        """Return a summary of the registry for the API endpoint."""
        tests = self.list_tests()
        by_type = {}
        by_result = {}
        for t in tests:
            tt = t.get("test_type", "UNKNOWN")
            by_type[tt] = by_type.get(tt, 0) + 1
            rs = t.get("result", {}).get("status", "UNKNOWN")
            by_result[rs] = by_result.get(rs, 0) + 1
        return {
            "total": len(tests),
            "by_type": by_type,
            "by_result": by_result,
            "failed_count": len(self.failed()),
            "not_run_count": len(self.not_run()),
        }

    # ------------------------------------------------------------------
    # Write operations (append-only)
    # ------------------------------------------------------------------

    def register(self, *, test_name: str, test_type: str,
                 claim_id: str, validation_level_target: str,
                 expected_value: str, pass_criteria: str,
                 evidence_id: str,
                 # Optional method fields
                 analytical_model: Optional[str] = None,
                 numerical_solver: Optional[str] = None,
                 numerical_model_file: Optional[str] = None,
                 numerical_run_command: Optional[str] = None,
                 physical_test_stand: Optional[str] = None,
                 physical_sample_size: Optional[int] = None,
                 physical_duration: Optional[str] = None,
                 physical_instruments: Optional[list[str]] = None,
                 physical_calibration_date: Optional[str] = None,
                 physical_procedure_doc: Optional[str] = None,
                 # Optional result fields (if test already run)
                 result_status: str = "NOT_RUN",
                 measured_value: Optional[str] = None,
                 date_run: Optional[str] = None,
                 run_by: Optional[str] = None,
                 raw_data_path: Optional[str] = None,
                 analysis_path: Optional[str] = None,
                 # Optional relations
                 retraction_id: Optional[str] = None,
                 related_test_ids: Optional[list[str]] = None) -> dict:
        """Register a new test record. Returns the record that was written.

        Per Law 7: the registry is append-only.
        Per EP-6: pass_criteria must be supplied at registration
        (before the test runs), not alongside the results.
        Per Law 27: the record carries a typed epistemic_status block.
        """
        # Validate test type
        if test_type not in TEST_TYPES:
            raise ValueError(
                f"test_type `{test_type}` not in allowed set. "
                f"Allowed: {sorted(TEST_TYPES)}"
            )
        # Validate validation level target
        if validation_level_target not in VALIDATION_LEVEL_TARGETS:
            raise ValueError(
                f"validation_level_target `{validation_level_target}` not in "
                f"allowed set. Allowed: {sorted(VALIDATION_LEVEL_TARGETS)}"
            )
        # Validate test type / validation level consistency.
        # Per TEST_REGISTRY_ENGINE.md:
        #   ANALYTICAL_ESTIMATE -> L2 only
        #   NUMERICAL_SIMULATION -> L3 only
        #   PHYSICAL_VALIDATION -> L4-L9 (any scale)
        if test_type == "ANALYTICAL_ESTIMATE":
            if validation_level_target != "L2":
                raise ValueError(
                    f"ANALYTICAL_ESTIMATE requires validation_level_target "
                    f"`L2`, got `{validation_level_target}`."
                )
        elif test_type == "NUMERICAL_SIMULATION":
            if validation_level_target != "L3":
                raise ValueError(
                    f"NUMERICAL_SIMULATION requires validation_level_target "
                    f"`L3`, got `{validation_level_target}`."
                )
        elif test_type == "PHYSICAL_VALIDATION":
            if validation_level_target not in {"L4", "L5", "L6", "L7", "L8", "L9"}:
                raise ValueError(
                    f"PHYSICAL_VALIDATION requires validation_level_target "
                    f"L4-L9, got `{validation_level_target}`."
                )
        # Validate result status
        if result_status not in RESULT_STATUS_VALUES:
            raise ValueError(
                f"result_status `{result_status}` not in allowed set. "
                f"Allowed: {sorted(RESULT_STATUS_VALUES)}"
            )
        # Validate physical test fields consistency
        if test_type == "PHYSICAL_VALIDATION":
            if not physical_test_stand or physical_sample_size is None:
                raise ValueError(
                    "PHYSICAL_VALIDATION requires physical_test_stand and "
                    "physical_sample_size."
                )
        if test_type == "NUMERICAL_SIMULATION":
            if not numerical_solver or not numerical_model_file:
                raise ValueError(
                    "NUMERICAL_SIMULATION requires numerical_solver and "
                    "numerical_model_file."
                )

        # Generate the next test ID
        next_id = self._next_id()

        # Build the method block
        method = {}
        if test_type == "ANALYTICAL_ESTIMATE":
            method["analytical_model"] = analytical_model or "unspecified"
        elif test_type == "NUMERICAL_SIMULATION":
            method["numerical_model"] = {
                "solver": numerical_solver,
                "model_file": numerical_model_file,
                "run_command": numerical_run_command or "",
            }
        elif test_type == "PHYSICAL_VALIDATION":
            method["physical_test"] = {
                "test_stand": physical_test_stand,
                "sample_size": physical_sample_size,
                "test_duration": physical_duration or "unspecified",
                "measurement_instruments": physical_instruments or [],
                "calibration_date": physical_calibration_date or "",
                "procedure_document": physical_procedure_doc or "",
            }

        # Build the result block
        result = {
            "status": result_status,
            "measured_value": measured_value,
            "expected_value": expected_value,
            "pass_criteria": pass_criteria,  # pre-stated per EP-6
            "date_run": date_run,
            "run_by": run_by,
            "raw_data_path": raw_data_path,
            "analysis_path": analysis_path,
        }

        # Build the typed epistemic_status block (Law 27)
        es = self._epistemic_status_for(test_type, validation_level_target)

        # Determine overall record status from result status
        if result_status == "FAIL":
            record_status = "REJECTED"
        elif result_status == "BLOCKED":
            record_status = "BLOCKED"
        elif result_status == "NOT_RUN":
            record_status = "BLOCKED"  # planned but not run yet
        elif result_status == "MARGINAL":
            record_status = "MARGINAL"
        elif result_status == "PASS_WITH_CONDITIONS":
            record_status = "PASS_WITH_CONDITIONS"
        else:  # PASS
            record_status = "PASS"

        record = {
            "id": next_id,
            "test_type": test_type,
            "test_name": test_name,
            "claim_id": claim_id,
            "validation_level_target": validation_level_target,
            "method": method,
            "result": result,
            "evidence_id": evidence_id,
            "retraction_id": retraction_id,
            "related_test_ids": related_test_ids or [],
            "status": record_status,
            "immutable": True,
            "epistemic_status": es,
        }

        # Append to the registry file. Per Law 7: append-only.
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _next_id(self) -> str:
        """Return the next test ID (TR-001, TR-002, ...)."""
        existing = self.list_tests()
        max_num = 0
        for t in existing:
            tid = t.get("id", "")
            m = ID_PATTERN.match(tid)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
        return f"TR-{max_num + 1:03d}"

    def _epistemic_status_for(self, test_type: str,
                               validation_level_target: str) -> dict:
        """Return the typed epistemic_status block for a test record.

        Per Law 27: no numerical confidence. The block declares the
        test's epistemic level honestly based on its type.
        """
        evidence_strength = TEST_TYPE_TO_EVIDENCE_STRENGTH.get(test_type, "WEAK")
        if test_type == "PHYSICAL_VALIDATION":
            # Physical validations with L7+ are VERY_STRONG; L4-L6 are STRONG
            if validation_level_target in {"L7", "L8", "L9"}:
                evidence_strength = "VERY_STRONG"
            else:
                evidence_strength = "STRONG"

        # Experimental validation: only PHYSICAL_VALIDATION has it
        if test_type == "PHYSICAL_VALIDATION":
            ev_map = {"L4": "BENCH", "L5": "SUBSYSTEM", "L6": "PROTOTYPE",
                      "L7": "PILOT", "L8": "PRODUCTION", "L9": "PRODUCTION"}
            experimental_validation = ev_map.get(validation_level_target, "BENCH")
        else:
            experimental_validation = "ABSENT"

        rationale = (
            f"Test record of type {test_type}. Per Law 28d, test types "
            f"cannot be conflated: analytical estimates are not simulations, "
            f"simulations are not measurements. This record's validation "
            f"level target is {validation_level_target} — the claim it "
            f"validates may be promoted to that level if the test PASSES. "
            f"Per Law 27, no numerical confidence is assigned."
        )

        return {
            "validation_level": validation_level_target,
            "evidence_strength": evidence_strength,
            "experimental_validation": experimental_validation,
            "status": "PASS",  # the record itself is valid (the test ran/was planned)
            "rationale": rationale,
        }


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format with Z suffix."""
    return datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
