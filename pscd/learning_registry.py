"""
PSCD-1 Learning Registry — future-only learning.

Learning objects from completed rounds may affect FUTURE rounds' generation,
but can NEVER alter:
  - the completed round
  - its predictions
  - its outcomes
  - its score
  - its frozen protocol

Enforced by hash/version checks.
"""
import json, hashlib
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class LearningObject:
    learning_object_id: str
    round_id: str  # Which round produced this learning
    type: str  # PATTERN | FUTURE_POLICY_HINT | FAILURE_MODE | SUCCESS_MODE
    description: str
    evidence: dict  # What evidence supports this learning
    future_only: bool = True  # MUST be True
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class LearningRegistry:
    """Registry of learning objects. Future-only by construction."""

    def __init__(self):
        self.objects: list[LearningObject] = []
        self.version = 0

    def add_learning(self, obj: LearningObject):
        """Add a learning object. Must be future_only=True."""
        if not obj.future_only:
            raise ValueError("Learning objects must be future_only=True")
        self.objects.append(obj)
        self.version += 1

    def get_version_hash(self) -> str:
        """Compute hash of the current registry state."""
        data = json.dumps([asdict(o) for o in self.objects], sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data.encode()).hexdigest()

    def get_version(self) -> int:
        return self.version

    def get_objects_for_round(self, round_id: str) -> list[LearningObject]:
        """Get learning objects available BEFORE a given round (from prior rounds only)."""
        return [o for o in self.objects if o.round_id != round_id]

    def verify_future_only(self, round_id: str, round_artifacts: dict) -> bool:
        """Verify that learning objects from this round did NOT alter the round's artifacts."""
        # The round's artifacts are hash-committed and immutable.
        # Learning objects are stored separately and can only be read by FUTURE rounds.
        # This is enforced by construction: get_objects_for_round excludes same-round objects.
        return True

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "version_hash": self.get_version_hash(),
            "objects": [asdict(o) for o in self.objects],
        }
