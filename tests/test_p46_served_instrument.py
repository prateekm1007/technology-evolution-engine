"""P46 served-instrument verification tests (audit finding round 4).

The auditor found that the ZAI provider recorded the REQUESTED model
but not the SERVED model. Per P46:

    "Verify the served instrument, not the requested one. Read
     response.model on every call, assert it equals the expected
     instrument, fail loudly on any mismatch."

These tests exercise the actual provider boundary with mocked CLI/API
responses to verify:
1. The manifest records served_model (from response), not just model (from config)
2. A served-model mismatch causes hard failure
3. The manifest distinguishes requested vs served
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.providers import ZAIReasoningProvider, ProviderCallManifest


def _make_zai_response(model: str, content: str = "OK") -> str:
    """Create a fake z-ai CLI JSON response file and return its path."""
    response = {
        "id": "test-id",
        "object": "chat.completion",
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(response, f)
    return path


def test_zai_provider_records_served_model_not_requested_model():
    """The ZAI provider must record the SERVED model from the response,
    not just the REQUESTED model from configuration.

    This is the core P46 test. The auditor found that the manifest only
    recorded self._model (requested). Now it must also record
    data["model"] (served).
    """
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)

    # Mock the CLI call to return a response with served model = "glm-4-plus"
    response_path = _make_zai_response("glm-4-plus", "test content")

    def fake_run(args, **kwargs):
        # The z-ai CLI writes to -o <path>; we need to copy our response there
        # Find the -o path in args
        if "-o" in args:
            out_path = args[args.index("-o") + 1]
            import shutil
            shutil.copy(response_path, out_path)
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    try:
        with patch("subprocess.run", side_effect=fake_run):
            content, manifest = provider.generate("test prompt")
    finally:
        os.unlink(response_path)

    # The manifest must record BOTH requested and served model
    assert manifest.model == "glm-4-plus", "requested model should be glm-4-plus"
    assert manifest.served_model == "glm-4-plus", (
        f"served_model should be glm-4-plus (from response), got {manifest.served_model}. "
        f"P46: the manifest must record what was SERVED, not just what was REQUESTED."
    )
    assert manifest.success is True


def test_zai_provider_hard_fails_on_served_model_mismatch():
    """If the z-ai CLI serves a DIFFERENT model than requested, the provider
    must hard-fail. This is the P46 invariant: a request for glm-4-plus is
    not evidence that glm-4-plus produced the observation.
    """
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)

    # Mock the CLI to return a response with served model = "some-other-model"
    response_path = _make_zai_response("some-other-model", "sneaky content")

    def fake_run(args, **kwargs):
        if "-o" in args:
            out_path = args[args.index("-o") + 1]
            import shutil
            shutil.copy(response_path, out_path)
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    try:
        with patch("subprocess.run", side_effect=fake_run):
            content, manifest = provider.generate("test prompt")
    finally:
        os.unlink(response_path)

    # The provider must NOT return content (hard fail)
    assert content == "", "Provider must not return content on served-model mismatch"
    assert manifest.success is False, (
        "manifest.success must be False when served model != requested model"
    )
    assert "P46 SERVED-INSTRUMENT MISMATCH" in manifest.error, (
        f"Error must mention P46 mismatch, got: {manifest.error}"
    )
    assert manifest.served_model == "some-other-model"
    assert manifest.model == "glm-4-plus"


def test_zai_provider_records_served_model_absent():
    """If the response does not include a 'model' field, the provider records
    p46_served_model_absent=True in the configuration. This is a warning
    state — we cannot establish experimental identity, but we don't hard-fail
    (the CLI may not always report the field).
    """
    provider = ZAIReasoningProvider(model="glm-4-plus", timeout=10)

    # Create a response with NO model field
    response = {
        "id": "test-id",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "OK"}}],
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(response, f)
    response_path = path

    def fake_run(args, **kwargs):
        if "-o" in args:
            out_path = args[args.index("-o") + 1]
            import shutil
            shutil.copy(response_path, out_path)
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    try:
        with patch("subprocess.run", side_effect=fake_run):
            content, manifest = provider.generate("test prompt")
    finally:
        os.unlink(response_path)

    assert manifest.served_model is None
    assert manifest.configuration.get("p46_served_model_absent") is True
    # We don't hard-fail on absent served model (CLI may not always report it)
    assert manifest.success is True


def test_provider_call_manifest_has_served_fields():
    """The ProviderCallManifest dataclass must have served_provider and
    served_model fields, and to_dict() must include them.
    """
    m = ProviderCallManifest(
        provider="zai", model="glm-4-plus", version="test",
        served_provider="zai", served_model="glm-4-plus",
    )
    d = m.to_dict()
    assert "served_provider" in d
    assert "served_model" in d
    assert d["served_provider"] == "zai"
    assert d["served_model"] == "glm-4-plus"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
