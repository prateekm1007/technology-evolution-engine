"""P46 served-instrument verification tests — FAIL-CLOSED (audit finding round 5).

Per P6 (fail closed, not open) and P46 (verify the served instrument):
    SUCCESS requires:
        served_provider is present (not None)
        AND served_model is present (not None)
        AND served_provider == requested_provider
        AND served_model == requested_model
    Otherwise: hard failure (success=False, content="")

No warning-only path. No fallback. No inference from client configuration.

Test matrix (7 cases):
    1. correct served model + correct served provider → SUCCESS
    2. wrong served model → FAIL
    3. missing served model → FAIL
    4. correct model but missing served provider → FAIL
    5. wrong served provider → FAIL
    6. both missing → FAIL
    7. malformed response → FAIL
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.providers import ZAIReasoningProvider, ProviderCallManifest


def _make_zai_response(model=None, provider=None, content="OK"):
    """Create a fake z-ai CLI JSON response file and return its path.

    If model is None, the 'model' key is omitted entirely.
    If provider is None, the 'provider' key is omitted entirely.
    """
    response = {
        "id": "test-id",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
    }
    if model is not None:
        response["model"] = model
    if provider is not None:
        response["provider"] = provider
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(response, f)
    return path


def _run_provider_with_mocked_cli(provider, response_path):
    """Run provider.generate() with a mocked z-ai CLI that returns the given response."""
    def fake_run(args, **kwargs):
        if "-o" in args:
            out_path = args[args.index("-o") + 1]
            import shutil
            shutil.copy(response_path, out_path)
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    with patch("subprocess.run", side_effect=fake_run):
        return provider.generate("test prompt")


# ===== CASE 1: correct served model + correct served provider → SUCCESS =====

def test_p46_case1_correct_served_model_and_provider_succeeds():
    """When the response reports served_model=glm-4-plus AND served_provider=zai,
    and both match the requested values, the call succeeds."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="glm-4-plus", provider="zai", content="test")

    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert manifest.success is True
    assert manifest.served_model == "glm-4-plus"
    assert manifest.served_provider == "zai"
    assert manifest.served_instrument_verified is True
    assert content == "test"


# ===== CASE 2: wrong served model → FAIL =====

def test_p46_case2_wrong_served_model_fails():
    """When the response reports a different served_model, the call hard-fails."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="different-model", provider="zai")

    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert content == "", "Provider must not return content on served-model mismatch"
    assert manifest.success is False
    assert manifest.served_instrument_verified is False
    assert "P46_SERVED_INSTRUMENT_MISMATCH" in manifest.error


# ===== CASE 3: missing served model → FAIL (FAIL-CLOSED, round 5) =====

def test_p46_case3_missing_served_model_fails():
    """When the response has no 'model' field, the call MUST hard-fail.

    This is the case that was previously a warning → success. Per P6 and
    the round-5 audit: unknown instrument identity is a hard failure.
    """
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    # Response with provider=zai but NO model field
    response_path = _make_zai_response(model=None, provider="zai")

    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert content == "", "Provider must not return content when served_model is missing"
    assert manifest.success is False, (
        "missing served_model must cause hard failure, not warning (P6: fail closed)"
    )
    assert manifest.served_instrument_verified is False
    assert manifest.served_model is None
    assert "P46_SERVED_INSTRUMENT_UNVERIFIED" in manifest.error


# ===== CASE 4: correct model but missing served provider → FAIL =====

def test_p46_case4_missing_served_provider_fails():
    """When the response has served_model=glm-4-plus but no served_provider,
    the call MUST hard-fail. The provider identity cannot be inferred from
    the client configuration — it must come from the response."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    # Response with model=glm-4-plus but NO provider field
    # This is the actual z-ai CLI behavior (it reports model but not provider)
    response_path = _make_zai_response(model="glm-4-plus", provider=None)

    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert content == "", (
        "Provider must not return content when served_provider is missing. "
        "The z-ai CLI does not report provider identity, so provider identity "
        "cannot be verified. This is a hard failure per P46 round 5."
    )
    assert manifest.success is False
    assert manifest.served_instrument_verified is False
    assert manifest.served_provider is None
    assert manifest.served_model == "glm-4-plus"  # model IS present
    assert "P46_SERVED_INSTRUMENT_UNVERIFIED" in manifest.error
    assert "served-provider" in manifest.error or "provider" in manifest.error.lower()


# ===== CASE 5: wrong served provider → FAIL =====

def test_p46_case5_wrong_served_provider_fails():
    """When the response reports a different served_provider, the call hard-fails."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="glm-4-plus", provider="wrong-provider")

    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert content == ""
    assert manifest.success is False
    assert manifest.served_instrument_verified is False
    assert "P46_SERVED_INSTRUMENT_MISMATCH" in manifest.error
    assert "provider" in manifest.error.lower()


# ===== CASE 6: both missing → FAIL =====

def test_p46_case6_both_missing_fails():
    """When the response has neither model nor provider, the call hard-fails."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model=None, provider=None)

    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert content == ""
    assert manifest.success is False
    assert manifest.served_instrument_verified is False
    assert manifest.served_model is None
    assert manifest.served_provider is None
    assert "P46_SERVED_INSTRUMENT_UNVERIFIED" in manifest.error


# ===== CASE 7: malformed response → FAIL =====

def test_p46_case7_malformed_response_fails():
    """When the response is malformed (not valid JSON), the call hard-fails.
    This is already handled by the existing exception handling, but we verify
    it doesn't accidentally succeed."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)

    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        f.write("this is not valid JSON {{{")

    def fake_run(args, **kwargs):
        if "-o" in args:
            out_path = args[args.index("-o") + 1]
            import shutil
            shutil.copy(path, out_path)
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    try:
        with patch("subprocess.run", side_effect=fake_run):
            content, manifest = provider.generate("test prompt")
    finally:
        os.unlink(path)

    assert content == ""
    assert manifest.success is False
    assert manifest.served_instrument_verified is False


# ===== ADDITIONAL: manifest dataclass has the right fields =====

def test_provider_call_manifest_has_served_instrument_verified_field():
    """The ProviderCallManifest must have a served_instrument_verified boolean
    field, and to_dict() must include it."""
    m = ProviderCallManifest(
        provider="zai", model="glm-4-plus", version="test",
        served_provider="zai", served_model="glm-4-plus",
        served_instrument_verified=True,
    )
    d = m.to_dict()
    assert "served_instrument_verified" in d
    assert d["served_instrument_verified"] is True
    assert "served_provider" in d
    assert "served_model" in d


def test_mock_provider_does_not_verify_instrument_identity():
    """The MockReasoningProvider must NOT set served_instrument_verified=True.
    A mock cannot establish real experimental identity."""
    from engine.providers import MockReasoningProvider
    mock = MockReasoningProvider(default_response="test")
    content, manifest = mock.generate("test prompt")
    assert manifest.served_instrument_verified is False, (
        "Mock provider must not claim to verify instrument identity. "
        "It has no served_provider or served_model from a real response."
    )
    assert manifest.served_provider is None
    assert manifest.served_model is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
