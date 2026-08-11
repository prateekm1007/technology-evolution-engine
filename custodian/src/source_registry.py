"""
custodian.src.source_registry — Registry of source documents.

Records provenance for every source: where it came from, when it was
retrieved, its content hash, and its version.

The registry must allow the custodian to prove:
1. where every case originated
2. which exact source version was used
3. that source material was not silently changed after construction

Do NOT put private credentials or secrets into the registry.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .hasher import sha256_string


@dataclass
class SourceEntry:
    source_id: str
    domain: str
    title: str
    origin: str
    source_uri: str
    retrieval_timestamp: str
    content_hash: str
    version: str
    license: str = ""
    provenance_metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "domain": self.domain,
            "title": self.title,
            "origin": self.origin,
            "source_uri": self.source_uri,
            "retrieval_timestamp": self.retrieval_timestamp,
            "content_hash": self.content_hash,
            "license": self.license,
            "provenance_metadata": self.provenance_metadata,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SourceEntry":
        return cls(**d)


class SourceRegistry:
    """Registry of source documents with provenance tracking."""

    def __init__(self):
        self._sources: Dict[str, SourceEntry] = {}

    def register(
        self,
        source_id: str,
        domain: str,
        title: str,
        origin: str,
        source_uri: str,
        content: str,
        version: str,
        license: str = "",
        provenance_metadata: Optional[dict] = None,
    ) -> SourceEntry:
        """Register a new source. Content is hashed but NOT stored."""
        if source_id in self._sources:
            raise ValueError(f"DUPLICATE_SOURCE_ID: {source_id} already registered")

        entry = SourceEntry(
            source_id=source_id,
            domain=domain,
            title=title,
            origin=origin,
            source_uri=source_uri,
            retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
            content_hash=sha256_string(content),
            version=version,
            license=license,
            provenance_metadata=provenance_metadata or {},
        )
        self._sources[source_id] = entry
        return entry

    def get(self, source_id: str) -> SourceEntry:
        if source_id not in self._sources:
            raise KeyError(f"Source not found: {source_id}")
        return self._sources[source_id]

    def list_sources(self) -> List[SourceEntry]:
        return list(self._sources.values())

    def list_domains(self) -> List[str]:
        return sorted(set(s.domain for s in self._sources.values()))

    def verify_content(self, source_id: str, content: str) -> bool:
        """Verify that content matches the registered hash."""
        entry = self.get(source_id)
        return sha256_string(content) == entry.content_hash

    def to_dict(self) -> dict:
        return {
            "sources": {sid: s.to_dict() for sid, s in self._sources.items()},
            "source_count": len(self._sources),
            "domain_count": len(self.list_domains()),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SourceRegistry":
        reg = cls()
        for sid, sd in d.get("sources", {}).items():
            reg._sources[sid] = SourceEntry.from_dict(sd)
        return reg

    def manifest_hash(self) -> str:
        """Hash of the entire registry (for manifest)."""
        from .hasher import sha256_json
        return sha256_json(self.to_dict())
