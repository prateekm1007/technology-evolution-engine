"""
openrouter_provider.py — OpenRouter ReasoningProvider implementation.

Provides access to LLM models via the OpenRouter API.
Used as an alternative when the ZAI API is unavailable.

Protocol amendment for DXP-005:
  DXP-005 was preregistered with ZAI (glm-4-plus). The ZAI API is
  rate-limited (HTTP 429). The CEO directed use of OpenRouter with
  Kimi K3. The A/B/C ablation comparison remains valid within a single
  provider (all three conditions use the same model). Cross-experiment
  comparisons with DXP-001/002/003/004 (which used ZAI) are NOT valid.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from engine.providers import ReasoningProvider, ProviderCallManifest


class OpenRouterProvider:
    """ReasoningProvider backed by the OpenRouter API.

    Supports any model available on OpenRouter (Kimi K3, Muse Spark, etc.)
    """

    def __init__(self, *, api_key: str, model: str = "moonshotai/kimi-k3",
                 default_temperature: float = 0.2,
                 default_max_tokens: int = 4096,
                 timeout: int = 120):
        self._api_key = api_key
        self._model = model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._timeout = timeout
        self._base_url = "https://openrouter.ai/api/v1/chat/completions"

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def version(self) -> str:
        return "openrouter-api-v1"

    def generate(self, prompt: str, *, system: str = "",
                 temperature: float = None,
                 max_tokens: int = None,
                 seed: Optional[int] = None) -> tuple[str, ProviderCallManifest]:
        if temperature is None:
            temperature = self._default_temperature
        if max_tokens is None:
            max_tokens = self._default_max_tokens

        psha = _prompt_sha(prompt)
        manifest = ProviderCallManifest(
            provider=self.provider_name,
            model=self._model,
            version=self.version,
            configuration={
                "temperature": temperature,
                "max_tokens": max_tokens,
                "system_sha": _prompt_sha(system) if system else "",
            },
            prompt_sha=psha,
            seed=seed,
            tool_versions={"openrouter_api": "v1"},
        )

        # Build messages
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = time.time()
        try:
            resp = requests.post(
                self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=self._timeout,
            )
            manifest.latency_ms = int((time.time() - start) * 1000)

            if resp.status_code != 200:
                manifest.success = False
                manifest.error = f"HTTP {resp.status_code}: {resp.text[:500]}"
                return "", manifest

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not content or not content.strip():
                manifest.success = False
                manifest.error = "empty response"
                return "", manifest

            # Record usage if available
            usage = data.get("usage", {})
            manifest.configuration["prompt_tokens"] = usage.get("prompt_tokens", 0)
            manifest.configuration["completion_tokens"] = usage.get("completion_tokens", 0)
            manifest.configuration["cost"] = usage.get("cost", 0)

            return content, manifest

        except requests.exceptions.Timeout:
            manifest.latency_ms = int((time.time() - start) * 1000)
            manifest.success = False
            manifest.error = f"timeout after {self._timeout}s"
            return "", manifest
        except Exception as e:
            manifest.latency_ms = int((time.time() - start) * 1000)
            manifest.success = False
            manifest.error = f"{type(e).__name__}: {e}"
            return "", manifest


def _prompt_sha(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


__all__ = ["OpenRouterProvider"]
