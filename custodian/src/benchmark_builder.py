"""
custodian.src.benchmark_builder — Build, validate, and seal benchmarks.

State machine:
    DRAFT → VALIDATED → CONSTRUCTED → SEALED

Once SEALED:
- cases cannot be added/removed
- sampling cannot change
- answer key cannot change
- blind fixture cannot change
- manifest cannot change

Any modification must produce a new benchmark version.
Never mutate a sealed benchmark in place.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .case_schema import (
    BenchmarkCase,
    validate_case,
    check_blind_fixture_safety,
    ANSWER_KEY_FIELDS,
)
from .hasher import sha256_json
from .sampler import construct_benchmark, SAMPLER_VERSION
from .domain_taxonomy import canonicalize_domain, DOMAIN_TAXONOMY
from .similarity import detect_near_duplicates, SimilarityFlag


class SealStateError(Exception):
    """Raised when attempting to modify a sealed benchmark."""
    pass


class ValidationError(Exception):
    """Raised when benchmark validation fails."""
    pass


# State machine states
DRAFT = "DRAFT"
VALIDATED = "VALIDATED"
CONSTRUCTED = "CONSTRUCTED"
SEALED = "SEALED"

VALID_TRANSITIONS = {
    DRAFT: {VALIDATED},
    VALIDATED: {CONSTRUCTED},
    CONSTRUCTED: {SEALED},
    SEALED: set(),  # Terminal state — no transitions
}


@dataclass
class Benchmark:
    benchmark_id: str
    benchmark_version: str = "1"
    seal_state: str = DRAFT
    cases: List[BenchmarkCase] = field(default_factory=list)
    source_manifest_hash: str = ""
    seed_hash: str = ""
    corpus_hash: str = ""
    construction_parameters: dict = field(default_factory=dict)
    blind_fixture_hash: str = ""
    answer_key_hash: str = ""
    manifest_hash: str = ""
    sealed_at: str = ""
    construction_timestamp: str = ""

    def _assert_state(self, allowed_states: set, operation: str):
        if self.seal_state not in allowed_states:
            raise SealStateError(
                f"ILLEGAL_OPERATION: {operation} requires state in {allowed_states}, "
                f"but benchmark is in state {self.seal_state}. "
                f"Sealed benchmarks are immutable."
            )

    def add_case(self, case: BenchmarkCase):
        """Add a case. Only allowed in DRAFT state."""
        self._assert_state({DRAFT}, "add_case")
        errors = validate_case(case)
        if errors:
            raise ValidationError(f"INVALID_CASE: {errors}")
        self.cases.append(case)

    def validate(self) -> List[str]:
        """Validate the benchmark. Returns list of errors."""
        errors = []
        seen_ids = set()
        seen_groups: Dict[str, int] = {}

        for case in self.cases:
            # Check for duplicates
            if case.case_id in seen_ids:
                errors.append(f"DUPLICATE_CASE: {case.case_id}")
            seen_ids.add(case.case_id)

            # Validate case
            case_errors = validate_case(case)
            errors.extend(case_errors)

            # Track independence groups
            group = case.independence_group
            seen_groups[group] = seen_groups.get(group, 0) + 1

        # Check independence (max 1 case per group by default)
        for group, count in seen_groups.items():
            if count > 1:
                errors.append(
                    f"DEPENDENT_CASE_CLUSTER: independence_group '{group}' "
                    f"has {count} cases (max 1 allowed)"
                )

        # Check minimum case count
        if len(self.cases) < 100:
            errors.append(
                f"INSUFFICIENT_CORPUS: {len(self.cases)} cases (need >= 100)"
            )

        # Check minimum domain count (using canonicalized domains)
        canonical_domains = set(canonicalize_domain(c.domain) for c in self.cases)
        if len(canonical_domains) < 4:
            errors.append(
                f"INSUFFICIENT_DOMAINS: {len(canonical_domains)} canonical domains "
                f"(need >= 4). Raw domains: {sorted(set(c.domain for c in self.cases))}"
            )

        # Check for domain label manipulation (non-canonical labels)
        raw_domains = set(c.domain for c in self.cases)
        if len(raw_domains) != len(canonical_domains):
            errors.append(
                f"DOMAIN_CANONICALIZATION_MISMATCH: {len(raw_domains)} raw domains "
                f"map to {len(canonical_domains)} canonical domains. "
                f"Possible label manipulation. Raw: {sorted(raw_domains)}, "
                f"Canonical: {sorted(canonical_domains)}"
            )

        # Near-duplicate detection (review flags, not blocking)
        dup_flags = detect_near_duplicates(self.cases)
        for flag in dup_flags:
            errors.append(
                f"NEAR_DUPLICATE_FLAG: cases {flag.case_a} and {flag.case_b} "
                f"have {flag.similarity_type} similarity (score={flag.score:.2f}). "
                f"REQUIRES_CUSTODIAN_ADJUDICATION."
            )

        return errors

    def transition_to_validated(self):
        """DRAFT → VALIDATED. Runs full validation."""
        self._assert_state({DRAFT}, "transition_to_validated")
        errors = self.validate()
        if errors:
            raise ValidationError(f"VALIDATION_FAILED: {errors}")
        self.seal_state = VALIDATED

    def transition_to_constructed(
        self,
        source_manifest_hash: str,
        seed_hash: str,
        corpus_hash: str,
        construction_parameters: dict,
    ):
        """VALIDATED → CONSTRUCTED. Locks construction metadata.

        HARDENING: All hash inputs must be non-empty. Rejects empty commitments.
        """
        self._assert_state({VALIDATED}, "transition_to_constructed")

        # HARDENING #6: Reject empty/missing cryptographic commitments
        if not source_manifest_hash or len(source_manifest_hash) != 64:
            raise ValidationError(
                f"EMPTY_HASH: source_manifest_hash must be a 64-char SHA-256 hex, "
                f"got '{source_manifest_hash}'"
            )
        if not seed_hash or len(seed_hash) != 64:
            raise ValidationError(
                f"EMPTY_HASH: seed_hash must be a 64-char SHA-256 hex, "
                f"got '{seed_hash}'"
            )
        if not corpus_hash or len(corpus_hash) != 64:
            raise ValidationError(
                f"EMPTY_HASH: corpus_hash must be a 64-char SHA-256 hex, "
                f"got '{corpus_hash}'"
            )

        self.source_manifest_hash = source_manifest_hash
        self.seed_hash = seed_hash
        self.corpus_hash = corpus_hash
        self.construction_parameters = construction_parameters
        self.seal_state = CONSTRUCTED

        # Compute blind fixture and answer key hashes
        blind = self.get_blind_fixture()
        answer_key = self.get_answer_key()
        self.blind_fixture_hash = sha256_json(blind)
        self.answer_key_hash = sha256_json(answer_key)

    def transition_to_sealed(self, sealed_at: str):
        """CONSTRUCTED → SEALED. Immutable after this.

        HARDENING:
        #5: Verify all required inputs are present before sealing.
        #6: Verify hashes are non-empty.
        #7: sealed_at is NOT included in the canonical manifest hash (deterministic identity).
        """
        self._assert_state({CONSTRUCTED}, "transition_to_sealed")

        # HARDENING #5: Verify all required inputs are present
        required_inputs = {
            "source_manifest_hash": self.source_manifest_hash,
            "seed_hash": self.seed_hash,
            "corpus_hash": self.corpus_hash,
            "blind_fixture_hash": self.blind_fixture_hash,
            "answer_key_hash": self.answer_key_hash,
        }
        for name, value in required_inputs.items():
            if not value or len(value) != 64:
                raise ValidationError(
                    f"SEAL_REJECTED: {name} is empty or invalid (got '{value}'). "
                    f"Cannot seal without all required cryptographic commitments."
                )

        self.sealed_at = sealed_at
        self.seal_state = SEALED

        # HARDENING #7: Compute manifest hash EXCLUDING sealed_at
        # (sealed_at is metadata, not canonical identity)
        manifest = self.get_manifest(include_hash=False, exclude_sealed_at=True)
        self.manifest_hash = sha256_json(manifest)

    def get_blind_fixture(self) -> dict:
        """Return the blind fixture (NO answer key).

        FIX #5: Uses canonical domain count for consistency with manifest.
        """
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "case_count": len(self.cases),
            "domain_count": len(set(canonicalize_domain(c.domain) for c in self.cases)),  # FIX: canonical
            "cases": [c.to_blind_dict() for c in self.cases],
        }

    def get_answer_key(self) -> dict:
        """Return the answer key (separate from blind fixture)."""
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "answer_key": {
                c.case_id: c.ground_truth for c in self.cases if c.ground_truth
            },
        }

    def get_manifest(self, include_hash: bool = True, exclude_sealed_at: bool = False) -> dict:
        """Return the benchmark manifest.

        HARDENING #7: exclude_sealed_at=True removes sealed_at from the manifest
        dict before hashing, ensuring deterministic canonical identity.
        """
        manifest = {
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "custodian_version": "1.0.0",
            "construction_timestamp": self.construction_timestamp,
            "source_manifest_hash": self.source_manifest_hash,
            "sampling_seed_hash": self.seed_hash,
            "case_count": len(self.cases),
            "domain_count": len(set(canonicalize_domain(c.domain) for c in self.cases)),
            "case_ids": [c.case_id for c in self.cases],
            "domain_distribution": {
                d: sum(1 for c in self.cases if canonicalize_domain(c.domain) == d)
                for d in sorted(set(canonicalize_domain(c.domain) for c in self.cases))
            },
            "blind_fixture_hash": self.blind_fixture_hash,
            "answer_key_hash": self.answer_key_hash,
            "construction_parameters": self.construction_parameters,
            "software_version": "1.0.0",
            "sampler_version": SAMPLER_VERSION,
            "seal_state": self.seal_state,
        }
        if include_hash:
            manifest["manifest_hash"] = self.manifest_hash
        if self.sealed_at and not exclude_sealed_at:
            manifest["sealed_at"] = self.sealed_at
        return manifest

    def get_tee_package(self) -> dict:
        """Return the package TEE receives (blind fixture + metadata)."""
        self._assert_state({SEALED}, "get_tee_package")
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "blind_fixture": self.get_blind_fixture(),
            "fixture_hash": self.blind_fixture_hash,
            "evaluation_protocol_version": "NORTH_STAR_GATE_A_V1",
        }

    def verify_blind_fixture_safety(self) -> List[str]:
        """Verify the blind fixture contains NO answer-key fields."""
        blind = self.get_blind_fixture()
        return check_blind_fixture_safety(blind)

    def to_dict(self) -> dict:
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "seal_state": self.seal_state,
            "cases": [c.to_dict() for c in self.cases],
            "source_manifest_hash": self.source_manifest_hash,
            "seed_hash": self.seed_hash,
            "corpus_hash": self.corpus_hash,
            "construction_parameters": self.construction_parameters,
            "blind_fixture_hash": self.blind_fixture_hash,
            "answer_key_hash": self.answer_key_hash,
            "manifest_hash": self.manifest_hash,
            "sealed_at": self.sealed_at,
            "construction_timestamp": self.construction_timestamp,
        }
