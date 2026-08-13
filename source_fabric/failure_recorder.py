"""
Failure recorder (Issue #5).

Append-only log of source failures: API blocks, schema changes, licensing
issues, rate limits, deprecated sources. NEVER silently dropped.

Per CEO directive: "Source failures, API blocks, licensing problems and
schema changes are recorded rather than hidden."
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import hashlib


FAILURE_TYPES = {
    "API_BLOCKED",            # 403/401/captcha
    "RATE_LIMITED",           # 429
    "LICENSE_BLOCKED",        # license check failed
    "SCHEMA_CHANGED",         # response shape differs from expected
    "AUTH_REQUIRED",          # credentials missing or expired
    "SOURCE_DEPRECATED",      # source announced deprecation
    "NETWORK_ERROR",          # timeout, DNS, connection refused
    "PARSE_ERROR",            # response unparseable
    "PARTIAL_HARVEST",        # some records harvested, some failed
    "UNAVAILABLE",            # 5xx or maintenance
    "UNKNOWN",
}


@dataclass
class FailureRecord:
    failure_id: str
    source_id: str
    failure_type: str
    occurred_at: str           # ISO timestamp
    details: str
    http_status: int = 0
    record_count_affected: int = 0
    recovery_action: str = ""  # what should be done to recover
    recovered: bool = False

    def __post_init__(self):
        if self.failure_type not in FAILURE_TYPES:
            raise ValueError(f"Unknown failure_type: {self.failure_type!r}")

    def canonical_dict(self) -> dict:
        return asdict(self)


class FailureLog:
    """Append-only failure log. Writes JSONL. Never overwrites."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # touch the file
        self.path.touch(exist_ok=True)

    def record(self, source_id: str, failure_type: str, details: str,
               http_status: int = 0, record_count_affected: int = 0,
               recovery_action: str = "") -> FailureRecord:
        now = datetime.now(timezone.utc).isoformat()
        # Deterministic failure_id from source + timestamp + details hash
        h = hashlib.sha256(f"{source_id}|{now}|{details}".encode()).hexdigest()[:12]
        rec = FailureRecord(
            failure_id=f"fail:{h}",
            source_id=source_id,
            failure_type=failure_type,
            occurred_at=now,
            details=details,
            http_status=http_status,
            record_count_affected=record_count_affected,
            recovery_action=recovery_action,
        )
        with self.path.open("a") as f:
            f.write(json.dumps(rec.canonical_dict(), sort_keys=True) + "\n")
        return rec

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def failures_for_source(self, source_id: str) -> list[dict]:
        return [r for r in self.read_all() if r.get("source_id") == source_id]

    def summary(self) -> dict:
        records = self.read_all()
        by_type: dict[str, int] = {}
        by_source: dict[str, int] = {}
        for r in records:
            by_type[r["failure_type"]] = by_type.get(r["failure_type"], 0) + 1
            by_source[r["source_id"]] = by_source.get(r["source_id"], 0) + 1
        return {
            "total_failures": len(records),
            "by_type": by_type,
            "by_source": by_source,
            "log_path": str(self.path),
        }
