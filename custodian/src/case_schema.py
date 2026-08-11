"""
custodian.src.case_schema — Benchmark case schema and validation.

Each case has an independence_group field to prevent 20 questions
derived from one underlying problem masquerading as 20 independent
benchmark observations.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Fields that MUST NOT appear in the blind fixture
ANSWER_KEY_FIELDS = {
    "ground_truth",
    "expected_answer",
    "answer_key",
    "reference_solution",
    "verification_key",
    "expected_label",
    "expected_mechanism",
    "expected_direction",
    "expected_magnitude",
    "falsifier",
}

# Fields that ARE allowed in the blind fixture
BLIND_FIXTURE_ALLOWED_FIELDS = {
    "case_id",
    "source_id",
    "domain",
    "problem",
    "input_material",
    "expected_task",
    "verification_method",
    "difficulty",
    "independence_group",
    "provenance",
}

REQUIRED_CASE_FIELDS = {
    "case_id",
    "source_id",
    "domain",
    "problem",
    "input_material",
    "expected_task",
    "verification_method",
    "difficulty",
    "independence_group",
    "provenance",
}


@dataclass
class BenchmarkCase:
    case_id: str
    source_id: str
    domain: str
    problem: str
    input_material: dict  # {source_a, source_b}
    expected_task: str
    verification_method: str
    difficulty: str  # easy, moderate, hard
    independence_group: str
    provenance: dict
    ground_truth: Optional[dict] = None  # ANSWER KEY — not in blind fixture

    def to_dict(self) -> dict:
        d = {
            "case_id": self.case_id,
            "source_id": self.source_id,
            "domain": self.domain,
            "problem": self.problem,
            "input_material": self.input_material,
            "expected_task": self.expected_task,
            "verification_method": self.verification_method,
            "difficulty": self.difficulty,
            "independence_group": self.independence_group,
            "provenance": self.provenance,
        }
        if self.ground_truth is not None:
            d["ground_truth"] = self.ground_truth
        return d

    def to_blind_dict(self) -> dict:
        """Return ONLY fields safe for the blind fixture (no answer key)."""
        return {
            "case_id": self.case_id,
            "source_id": self.source_id,
            "domain": self.domain,
            "problem": self.problem,
            "input_material": self.input_material,
            "expected_task": self.expected_task,
            "verification_method": self.verification_method,
            "difficulty": self.difficulty,
            "independence_group": self.independence_group,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BenchmarkCase":
        return cls(
            case_id=d["case_id"],
            source_id=d["source_id"],
            domain=d["domain"],
            problem=d["problem"],
            input_material=d["input_material"],
            expected_task=d["expected_task"],
            verification_method=d["verification_method"],
            difficulty=d["difficulty"],
            independence_group=d["independence_group"],
            provenance=d["provenance"],
            ground_truth=d.get("ground_truth"),
        )


def validate_case(case: BenchmarkCase) -> List[str]:
    """Validate a single case. Returns list of errors (empty = valid)."""
    errors = []

    # Check required fields
    d = case.to_dict()
    for f in REQUIRED_CASE_FIELDS:
        if f not in d or d[f] is None or d[f] == "":
            errors.append(f"MISSING_REQUIRED_FIELD: {f}")

    # Check input_material structure
    if "input_material" in d:
        im = d["input_material"]
        if not isinstance(im, dict):
            errors.append("INVALID_INPUT_MATERIAL: must be dict")
        elif "source_a" not in im or "source_b" not in im:
            errors.append("INVALID_INPUT_MATERIAL: must have source_a and source_b")
        elif not im.get("source_a") or not im.get("source_b"):
            errors.append("INVALID_INPUT_MATERIAL: source_a and source_b must be non-empty")

    # Check difficulty
    if case.difficulty not in ("easy", "moderate", "hard"):
        errors.append(f"INVALID_DIFFICULTY: {case.difficulty}")

    # Check independence_group
    if not case.independence_group:
        errors.append("MISSING_INDEPENDENCE_GROUP")

    # Check provenance
    if not isinstance(case.provenance, dict):
        errors.append("INVALID_PROVENANCE: must be dict")
    elif "constructor" not in case.provenance:
        errors.append("MISSING_PROVENANCE: constructor")
    elif "construction_timestamp" not in case.provenance:
        errors.append("MISSING_PROVENANCE: construction_timestamp")

    return errors


def check_blind_fixture_safety(data: dict) -> List[str]:
    """Check that a blind fixture dict contains NO answer-key fields.
    Returns list of violations (empty = safe)."""
    violations = []

    def check_recursive(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ANSWER_KEY_FIELDS:
                    violations.append(f"ANSWER_KEY_LEAK: {path}.{key}")
                check_recursive(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_recursive(item, f"{path}[{i}]")

    check_recursive(data)
    return violations
