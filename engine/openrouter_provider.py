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
                 default_max_tokens: int = 8192,
                 timeout: int = 180,
                 max_retries: int = 3,
                 retry_backoff: float = 5.0):
        """ReasoningProvider backed by OpenRouter.

        Operational parameters (not science):
          max_retries     — number of retries on empty response or 429/5xx
          retry_backoff   — seconds to wait between retries (multiplied by attempt #)
        Nemotron 3 Ultra is a reasoning model whose free tier intermittently
        returns an empty `content` (when reasoning tokens saturate max_tokens
        before answer text is produced). Retrying with a higher max_tokens
        on the next attempt usually recovers a non-empty response.
        """
        self._api_key = api_key
        self._model = model
        self._default_temperature = default_temperature
        self._default_max_tokens = default_max_tokens
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
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

        # Retry loop: Nemotron free tier intermittently returns empty content
        # when reasoning_tokens saturate max_tokens before answer text.
        # On each retry, double max_tokens (up to 32768) to give the model
        # more room for the answer after its reasoning.
        attempt_max_tokens = max_tokens
        last_error = ""
        for attempt in range(1, self._max_retries + 1):
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
                        "max_tokens": attempt_max_tokens,
                    },
                    timeout=self._timeout,
                )
                manifest.latency_ms = int((time.time() - start) * 1000)

                if resp.status_code == 429:
                    last_error = f"HTTP 429: {resp.text[:200]}"
                    manifest.configuration[f"attempt_{attempt}_status"] = "429"
                    # backoff and retry
                    time.sleep(self._retry_backoff * attempt)
                    continue
                if resp.status_code >= 500:
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    manifest.configuration[f"attempt_{attempt}_status"] = str(resp.status_code)
                    time.sleep(self._retry_backoff * attempt)
                    continue
                if resp.status_code != 200:
                    manifest.success = False
                    manifest.error = f"HTTP {resp.status_code}: {resp.text[:500]}"
                    return "", manifest

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                if not content or not content.strip():
                    # Empty content — reasoning model saturated max_tokens
                    # with reasoning before producing answer. Retry with more.
                    last_error = "empty response (reasoning saturated max_tokens)"
                    manifest.configuration[f"attempt_{attempt}_status"] = "empty"
                    manifest.configuration[f"attempt_{attempt}_max_tokens"] = attempt_max_tokens
                    # Double max_tokens for next attempt (cap at 32768)
                    attempt_max_tokens = min(attempt_max_tokens * 2, 32768)
                    time.sleep(self._retry_backoff * 0.5 * attempt)
                    continue

                # Success — record usage and return
                usage = data.get("usage", {})
                manifest.configuration["prompt_tokens"] = usage.get("prompt_tokens", 0)
                manifest.configuration["completion_tokens"] = usage.get("completion_tokens", 0)
                manifest.configuration["cost"] = usage.get("cost", 0)
                manifest.configuration["attempts"] = attempt
                manifest.configuration["final_max_tokens"] = attempt_max_tokens

                # ===== P46: Verify the served instrument (audit finding round 4) =====
                # OpenRouter returns the served model in the top-level "model"
                # field and the upstream provider in the "provider" field.
                served_model = data.get("model")
                served_provider = data.get("provider")
                manifest.served_model = served_model
                manifest.served_provider = served_provider
                if served_model is not None and served_model != self._model:
                    manifest.success = False
                    manifest.error = (
                        f"P46 SERVED-INSTRUMENT MISMATCH: requested model={self._model} "
                        f"but response served model={served_model} "
                        f"(served_provider={served_provider}). OpenRouter routed "
                        f"the request to a different instrument. This is an "
                        f"experimental identity violation."
                    )
                    return "", manifest
                if served_model is None:
                    manifest.configuration["p46_served_model_absent"] = True

                return content, manifest

            except requests.exceptions.Timeout:
                manifest.latency_ms = int((time.time() - start) * 1000)
                last_error = f"timeout after {self._timeout}s (attempt {attempt})"
                manifest.configuration[f"attempt_{attempt}_status"] = "timeout"
                time.sleep(self._retry_backoff * attempt)
                continue
            except Exception as e:
                manifest.latency_ms = int((time.time() - start) * 1000)
                last_error = f"{type(e).__name__}: {e} (attempt {attempt})"
                manifest.configuration[f"attempt_{attempt}_status"] = "exception"
                time.sleep(self._retry_backoff * attempt)
                continue

        # All retries exhausted
        manifest.success = False
        manifest.error = f"all {self._max_retries} retries failed; last_error={last_error}"
        return "", manifest


def _prompt_sha(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


__all__ = ["OpenRouterProvider"]
