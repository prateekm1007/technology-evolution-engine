"""P46 served-instrument verification tests — FAIL-CLOSED.

Per audit round 63 / P46 GOVERNANCE DECISION:
    The frozen P46 specification (ANTI_ENTROPY.md) requires:
        "Read response.model on every call, assert it equals the
         expected instrument, fail loudly on any mismatch."

    SUCCESS requires:
        served_model is present (not None)
        AND served_model == requested_model

    served_provider is OPTIONAL metadata:
        - When present, it is recorded.
        - When absent, it does NOT cause failure.
        - It is NOT used to determine served_instrument_verified.

    Per P6 (fail closed): if served_model is absent or mismatches,
    the call FAILS. No warning-only path. No fallback.

Test matrix (5 cases):
    1. correct model + missing provider → SUCCESS (P46 model-only)
    2. correct model + provider present → SUCCESS
    3. wrong model + missing provider → FAIL
    4. wrong model + provider present → FAIL
    5. missing model → FAIL
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
    """Run provider.generate() with a mocked z-ai CLI that returns
    the given response file."""
    def mock_run(args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        # Copy our response to the provider's temp output file
        if "-o" in args:
            o_idx = args.index("-o")
            if o_idx + 1 < len(args):
                import shutil
                shutil.copy2(response_path, args[o_idx + 1])
        return result
    with patch("subprocess.run", side_effect=mock_run):
        content, manifest = provider.generate("test prompt")
    return content, manifest


# ===== CASE 1: correct model + missing provider → SUCCESS =====

def test_p46_case1_correct_model_missing_provider_success():
    """Per audit round 63: correct served_model + missing served_provider
    → SUCCESS. P46 requires model verification only.

    This is the actual z-ai CLI behavior (reports model but not provider).
    """
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="glm-4-plus", provider=None)
    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert manifest.success is True
    assert manifest.served_instrument_verified is True
    assert manifest.served_model == "glm-4-plus"
    assert manifest.served_provider is None  # absent, but not a failure
    assert content == "OK"


# ===== CASE 2: correct model + provider present → SUCCESS =====

def test_p46_case2_correct_model_provider_present_success():
    """Correct model + provider present → SUCCESS.
    Provider is recorded as optional metadata."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="glm-4-plus", provider="zai")
    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert manifest.success is True
    assert manifest.served_instrument_verified is True
    assert manifest.served_model == "glm-4-plus"
    assert manifest.served_provider == "zai"  # recorded as metadata
    assert content == "OK"


# ===== CASE 3: wrong model + missing provider → FAIL =====

def test_p46_case3_wrong_model_missing_provider_fails():
    """Wrong served_model → FAIL regardless of provider presence."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="gpt-4", provider=None)
    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert content == ""
    assert manifest.success is False
    assert manifest.served_instrument_verified is False
    assert manifest.served_model == "gpt-4"
    assert "P46_SERVED_INSTRUMENT_MISMATCH" in manifest.error


# ===== CASE 4: wrong model + provider present → FAIL =====

def test_p46_case4_wrong_model_provider_present_fails():
    """Wrong served_model → FAIL even when provider is present.
    Model mismatch is a hard failure regardless of provider metadata."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="gpt-4", provider="zai")
    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    assert content == ""
    assert manifest.success is False
    assert manifest.served_instrument_verified is False
    assert manifest.served_model == "gpt-4"
    assert "P46_SERVED_INSTRUMENT_MISMATCH" in manifest.error


# ===== CASE 5: missing model → FAIL =====

def test_p46_case5_missing_model_fails():
    """Missing served_model → FAIL. P46 requires model to be present."""
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
    assert "P46_SERVED_INSTRUMENT_UNVERIFIED" in manifest.error


# ===== METADATA TESTS =====

def test_manifest_records_all_available_response_metadata():
    """The manifest records all available response metadata:
    model, provider (when present), and other fields."""
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="glm-4-plus", provider=None)
    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    d = manifest.to_dict()
    assert d["served_model"] == "glm-4-plus"
    assert d["served_provider"] is None  # absent but recorded
    assert d["served_instrument_verified"] is True


def test_manifest_scientific_boundary_documented():
    """The manifest distinguishes:
    - served_model = observed (attested by response)
    - served_provider = NOT attested by this interface
    """
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)
    response_path = _make_zai_response(model="glm-4-plus", provider=None)
    try:
        content, manifest = _run_provider_with_mocked_cli(provider, response_path)
    finally:
        os.unlink(response_path)

    # served_model is observed
    assert manifest.served_model is not None
    assert manifest.served_model == "glm-4-plus"
    # served_provider is NOT attested by this interface
    assert manifest.served_provider is None
    # But P46 still passes because model is verified
    assert manifest.served_instrument_verified is True
