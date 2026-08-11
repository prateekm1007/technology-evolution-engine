"""
custodian.src.seal — Sealing state machine and attestation.

State machine:
    DRAFT → VALIDATED → CONSTRUCTED → SEALED

Once SEALED, the benchmark is immutable. Any modification must produce
a new benchmark version.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .benchmark_builder import Benchmark, SEALED, CONSTRUCTED


@dataclass
class CustodianAttestation:
    """Machine-readable and human-readable attestation of benchmark state."""

    benchmark_id: str
    benchmark_version: str
    custodian_version: str
    construction_status: str
    case_count: int
    domain_count: int
    source_count: int
    sampling_method: str
    seed_commitment: str
    source_manifest_hash: str
    blind_fixture_hash: str
    answer_key_hash: str
    manifest_hash: str
    validation_result: str
    sealed_at: str

    def to_dict(self) -> dict:
        return {
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "custodian_version": self.custodian_version,
            "construction_status": self.construction_status,
            "case_count": self.case_count,
            "domain_count": self.domain_count,
            "source_count": self.source_count,
            "sampling_method": self.sampling_method,
            "seed_commitment": self.seed_commitment,
            "source_manifest_hash": self.source_manifest_hash,
            "blind_fixture_hash": self.blind_fixture_hash,
            "answer_key_hash": self.answer_key_hash,
            "manifest_hash": self.manifest_hash,
            "validation_result": self.validation_result,
            "sealed_at": self.sealed_at,
        }

    def to_human_readable(self) -> str:
        lines = [
            "=== CUSTODIAN ATTESTATION ===",
            f"Benchmark ID: {self.benchmark_id}",
            f"Benchmark Version: {self.benchmark_version}",
            f"Custodian Version: {self.custodian_version}",
            f"Construction Status: {self.construction_status}",
            f"Case Count: {self.case_count}",
            f"Domain Count: {self.domain_count}",
            f"Source Count: {self.source_count}",
            f"Sampling Method: {self.sampling_method}",
            f"Seed Commitment: {self.seed_commitment}",
            f"Source Manifest Hash: {self.source_manifest_hash}",
            f"Blind Fixture Hash: {self.blind_fixture_hash}",
            f"Answer Key Hash: {self.answer_key_hash}",
            f"Manifest Hash: {self.manifest_hash}",
            f"Validation Result: {self.validation_result}",
            f"Sealed At: {self.sealed_at or 'NOT SEALED'}",
        ]

        if self.construction_status == "INFRASTRUCTURE_READY":
            lines.append("")
            lines.append("STATUS: INFRASTRUCTURE READY")
            lines.append("BENCHMARK STATUS: NOT SEALED")
            lines.append("REASON: CORPUS NOT YET AVAILABLE")
            lines.append("")
            lines.append("NOTE: Do not confuse 'infrastructure ready' with 'benchmark validated'.")
            lines.append("      The custodian machinery is built and tested, but no real")
            lines.append("      benchmark has been constructed or sealed.")

        return "\n".join(lines)


def generate_infrastructure_attestation() -> CustodianAttestation:
    """Generate attestation for infrastructure-ready state (no benchmark)."""
    return CustodianAttestation(
        benchmark_id="NOT_ASSIGNED",
        benchmark_version="NOT_ASSIGNED",
        custodian_version="1.0.0",
        construction_status="INFRASTRUCTURE_READY",
        case_count=0,
        domain_count=0,
        source_count=0,
        sampling_method="deterministic_seeded (not yet executed)",
        seed_commitment="NOT_COMMITTED",
        source_manifest_hash="NOT_COMPUTED",
        blind_fixture_hash="NOT_COMPUTED",
        answer_key_hash="NOT_COMPUTED",
        manifest_hash="NOT_COMPUTED",
        validation_result="NOT_RUN (no benchmark to validate)",
        sealed_at="NOT_SEALED",
    )


def seal_benchmark(benchmark: Benchmark) -> CustodianAttestation:
    """Seal a constructed benchmark. Returns attestation.

    HARDENING #5-6: Verifies all required inputs and non-empty hashes before sealing.
    """
    if benchmark.seal_state != CONSTRUCTED:
        raise ValueError(
            f"Cannot seal: benchmark must be in CONSTRUCTED state, "
            f"got {benchmark.seal_state}. Use transition_to_constructed() first."
        )

    # HARDENING #6: Verify all hashes are non-empty before sealing
    required_hashes = {
        "source_manifest_hash": benchmark.source_manifest_hash,
        "seed_hash": benchmark.seed_hash,
        "corpus_hash": benchmark.corpus_hash,
        "blind_fixture_hash": benchmark.blind_fixture_hash,
        "answer_key_hash": benchmark.answer_key_hash,
    }
    for name, value in required_hashes.items():
        if not value or len(value) != 64:
            raise ValueError(
                f"SEAL_REJECTED: {name} is empty or invalid (got '{value}'). "
                f"Cannot seal without all required cryptographic commitments. "
                f"Use transition_to_constructed() to set all hashes."
            )

    # Verify blind fixture safety before sealing
    violations = benchmark.verify_blind_fixture_safety()
    if violations:
        raise ValueError(f"BLIND_FIXTURE_SAFETY_VIOLATION: {violations}")

    # Seal
    sealed_at = datetime.now(timezone.utc).isoformat()
    benchmark.transition_to_sealed(sealed_at)

    # FIX #5: Use canonical domain count for consistency
    from .domain_taxonomy import canonicalize_domain
    canonical_domains = set(canonicalize_domain(c.domain) for c in benchmark.cases)

    return CustodianAttestation(
        benchmark_id=benchmark.benchmark_id,
        benchmark_version=benchmark.benchmark_version,
        custodian_version="1.0.0",
        construction_status="BENCHMARK_SEALED",
        case_count=len(benchmark.cases),
        domain_count=len(canonical_domains),  # FIX: canonical, not raw
        source_count=len(set(c.source_id for c in benchmark.cases)),
        sampling_method="deterministic_seeded",
        seed_commitment=benchmark.seed_hash,
        source_manifest_hash=benchmark.source_manifest_hash,
        blind_fixture_hash=benchmark.blind_fixture_hash,
        answer_key_hash=benchmark.answer_key_hash,
        manifest_hash=benchmark.manifest_hash,
        validation_result="PASS",
        sealed_at=sealed_at,
    )
