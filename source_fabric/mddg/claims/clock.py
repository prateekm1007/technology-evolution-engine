"""
Clock provider for deterministic vs production timestamps (CTO V17 #3).

Per CTO: "Inject a clock. Production: SystemClock.now(). Replay: ReplayClock.
The extraction algorithm stays identical. Do not globally freeze time in
production logic."
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


class Clock(Protocol):
    """Clock protocol for timestamp injection."""
    def now(self) -> str:
        """Return current ISO timestamp."""
        ...


@dataclass(frozen=True)
class SystemClock:
    """Production clock — uses real system time."""
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ReplayClock:
    """Replay clock — uses a fixed timestamp for determinism."""
    fixed_timestamp: str = "2026-08-13T06:00:00Z"

    def now(self) -> str:
        return self.fixed_timestamp


# Default clock for production use
DEFAULT_CLOCK: Clock = SystemClock()
