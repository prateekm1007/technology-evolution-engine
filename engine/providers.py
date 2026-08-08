"""
providers.py — Model-agnostic provider interfaces (Phase 20).

The reasoning model is a COMPONENT, not the engine. The scientific state,
evidence, provenance, validation, and failure machinery live in the
engine, not in the providers.

Provider protocols:
    ReasoningProvider   — generate text from a prompt (the LLM)
    EmbeddingProvider   — vectorize text
    RetrievalProvider   — retrieve documents
    LiteratureProvider  — search external literature (DEV_ONLY mock)
    ScientificToolProvider — run scientific tools (stub)

Every provider call records a ProviderCallManifest for reproducibility.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class ProviderCallManifest:
    """Reproducibility record for a single provider call.

    P46 (verify the served instrument, not the requested one):
        The `provider` and `model` fields record what was REQUESTED.
        The `served_provider` and `served_model` fields record what was
        actually SERVED, as reported by the provider's response metadata.

        If served_provider/served_model are None, the provider did not
        report served-instrument metadata and the manifest cannot
        establish experimental identity. If they are set and differ from
        the requested values, the provider call is marked failed
        (success=False, error describes the mismatch).

        This is the machine-enforced P46 invariant: a request for the
        preregistered instrument is not evidence that the preregistered
        instrument actually produced the observation.
    """
    provider: str                        # requested provider
    model: str                           # requested model
    version: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    prompt_sha: str = ""
    seed: Optional[int] = None
    tool_versions: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    latency_ms: Optional[int] = None
    success: bool = True
    error: str = ""
    # P46 served-instrument fields (audit finding round 4)
    served_provider: Optional[str] = None  # provider as reported by response
    served_model: Optional[str] = None     # model as reported by response

    def to_dict(self) -> Dict:
        return {
            "provider": self.provider, "model": self.model, "version": self.version,
            "configuration": self.configuration, "prompt_sha": self.prompt_sha,
            "seed": self.seed, "tool_versions": self.tool_versions,
            "timestamp": self.timestamp, "latency_ms": self.latency_ms,
            "success": self.success, "error": self.error,
            "served_provider": self.served_provider,
            "served_model": self.served_model,
        }


def _prompt_sha(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class ReasoningProvider(Protocol):
    def generate(self, prompt: str, *, system: str = "",
                 temperature: float = 0.2, max_tokens: int = 4096,
                 seed: Optional[int] = None) -> tuple[str, ProviderCallManifest]: ...
    @property
    def provider_name(self) -> str: ...
    @property
    def model_name(self) -> str: ...
    @property
    def version(self) -> str: ...


class LiteratureProvider(Protocol):
    def search(self, query: str, cutoff: str = "",
               k: int = 10) -> tuple[List[Dict], ProviderCallManifest]: ...


class ZAIReasoningProvider:
    """ReasoningProvider backed by the z-ai CLI (glm-4-plus)."""

    def __init__(self, *, model: str = "glm-4-plus",
                 default_temperature: float = 0.2,
                 default_max_tokens: int = 4096,
                 cli_path: str = "z-ai",
                 timeout: int = 120):
        self._model = model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._cli_path = cli_path
        self._timeout = timeout

    @property
    def provider_name(self) -> str: return "zai"
    @property
    def model_name(self) -> str: return self._model
    @property
    def version(self) -> str: return "z-ai-web-dev-sdk"

    def generate(self, prompt: str, *, system: str = "",
                 temperature: float = None,
                 max_tokens: int = None,
                 seed: Optional[int] = None) -> tuple[str, ProviderCallManifest]:
        if temperature is None: temperature = self._default_temperature
        if max_tokens is None: max_tokens = self._default_max_tokens
        psha = _prompt_sha(prompt)
        manifest = ProviderCallManifest(
            provider=self.provider_name, model=self._model, version=self.version,
            configuration={"temperature": temperature, "max_tokens": max_tokens,
                           "system_sha": _prompt_sha(system) if system else ""},
            prompt_sha=psha, seed=seed,
            tool_versions={"z_ai_cli": self._cli_path},
        )
        start = time.time()
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                tmp_path = tmp.name
            args = [self._cli_path, "chat", "--prompt", prompt, "-o", tmp_path]
            if system:
                args.extend(["--system", system])
            proc = subprocess.run(args, capture_output=True, text=True, timeout=self._timeout)
            manifest.latency_ms = int((time.time() - start) * 1000)
            if proc.returncode != 0:
                manifest.success = False
                manifest.error = f"CLI exit {proc.returncode}: {proc.stderr[:500]}"
                return "", manifest
            with open(tmp_path) as f:
                data = json.load(f)

            # ===== P46: Verify the served instrument, not the requested one =====
            # (audit finding round 4)
            # Read the served model from the response metadata. The z-ai CLI
            # returns an OpenAI-compatible response with a top-level "model"
            # field. If the served model differs from the requested model,
            # the provider call is marked FAILED.
            served_model = data.get("model")
            manifest.served_model = served_model
            manifest.served_provider = self.provider_name  # z-ai CLI always serves via ZAI
            if served_model is not None and served_model != self._model:
                manifest.success = False
                manifest.error = (
                    f"P46 SERVED-INSTRUMENT MISMATCH: requested model={self._model} "
                    f"but response served model={served_model}. The provider routed "
                    f"the request to a different instrument. This is an experimental "
                    f"identity violation — the preregistered instrument did not "
                    f"produce this observation."
                )
                return "", manifest
            if served_model is None:
                # The response did not include served-model metadata. This is
                # a P46 warning — we cannot establish experimental identity.
                # We do NOT hard-fail (the z-ai CLI may not always report the
                # model field), but we record the absence in the manifest.
                manifest.configuration["p46_served_model_absent"] = True

            response = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not response.strip():
                manifest.success = False
                manifest.error = "empty response"
                return "", manifest
            return response, manifest
        except subprocess.TimeoutExpired:
            manifest.latency_ms = int((time.time() - start) * 1000)
            manifest.success = False
            manifest.error = f"timeout after {self._timeout}s"
            return "", manifest
        except Exception as e:
            manifest.latency_ms = int((time.time() - start) * 1000)
            manifest.success = False
            manifest.error = f"{type(e).__name__}: {e}"
            return "", manifest
        finally:
            if tmp_path:
                try: os.unlink(tmp_path)
                except OSError: pass


class MockReasoningProvider:
    """Deterministic mock for tests."""
    def __init__(self, responses: Optional[Dict[str, str]] = None,
                 default_response: str = ""):
        self._responses = responses or {}
        self._default = default_response

    @property
    def provider_name(self) -> str: return "mock"
    @property
    def model_name(self) -> str: return "mock-reasoner-v0"
    @property
    def version(self) -> str: return "test"

    def generate(self, prompt: str, *, system: str = "",
                 temperature: float = 0.2, max_tokens: int = 4096,
                 seed: Optional[int] = None) -> tuple[str, ProviderCallManifest]:
        psha = _prompt_sha(prompt)
        manifest = ProviderCallManifest(
            provider=self.provider_name, model=self.model_name, version=self.version,
            configuration={"temperature": temperature, "max_tokens": max_tokens},
            prompt_sha=psha, seed=seed,
        )
        for prefix, resp in self._responses.items():
            if prompt.startswith(prefix):
                return resp, manifest
        return self._default, manifest


class MockLiteratureProvider:
    """DEV_ONLY literature provider. Returns from a fixed corpus."""
    def __init__(self, corpus: List[Dict]):
        self._corpus = corpus

    def search(self, query: str, cutoff: str = "",
               k: int = 10) -> tuple[List[Dict], ProviderCallManifest]:
        manifest = ProviderCallManifest(
            provider="mock-literature", model="dev-corpus-v0", version="test",
            configuration={"corpus_size": len(self._corpus), "cutoff": cutoff},
            prompt_sha=_prompt_sha(query),
        )
        query_lower = query.lower()
        results = []
        for doc in self._corpus:
            text = (doc.get("title", "") + " " + doc.get("abstract", "")).lower()
            if any(term in text for term in query_lower.split()[:5]):
                results.append(doc)
            if len(results) >= k:
                break
        return results, manifest


__all__ = [
    "ProviderCallManifest", "ReasoningProvider", "LiteratureProvider",
    "ZAIReasoningProvider", "MockReasoningProvider", "MockLiteratureProvider",
]
