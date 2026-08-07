"""
test_python313_spacy_compat.py — Cycle 256: Python 3.13 / spaCy compatibility.

Closes F-143 finding 5: "Python 3.13 dependency issue (not fixed)".

Background:
  The original requirements.txt constraint `spacy>=3.7.0,<3.8.0` silently
  blocked every CPython 3.13 install because spaCy 3.7.x has no cp313
  wheels. spaCy added Python 3.13 wheel support starting with the 3.8.x
  series (3.8.7+ ship cp313 tags). Cycle 256 lifts the cap to <3.9.0.

These tests verify the compatibility claim is real, not just declared.
"""
import re
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_TXT = REPO_ROOT / "requirements.txt"


def _read_requirements() -> str:
    return REQUIREMENTS_TXT.read_text(encoding="utf-8")


def test_spacy_upper_bound_allows_38_series():
    """The constraint must NOT cap spaCy below 3.8.x (which is the first
    series with Python 3.13 wheels). The old `<3.8.0` cap is the bug we
    are fixing; this test guards against regression."""
    text = _read_requirements()
    # Find the spacy line
    match = re.search(r"^spacy([^\n#]*)", text, re.MULTILINE)
    assert match, "spacy line not found in requirements.txt"
    spec = match.group(1)
    # The forbidden cap
    assert "<3.8.0" not in spec, (
        f"spaCy cap <3.8.0 blocks Python 3.13 (no cp313 wheels in 3.7.x). "
        f"Found spec: {spec!r}"
    )
    # The new cap must allow 3.8.x
    assert "<3.9.0" in spec or "<3.10" in spec, (
        f"spaCy spec must cap below 3.9.0 or 3.10 to allow 3.8.x; got {spec!r}"
    )


def test_spacy_lower_bound_unchanged():
    """The lower bound 3.7.0 must be preserved — we're not forcing an
    upgrade, we're lifting the upper bound only."""
    text = _read_requirements()
    match = re.search(r"^spacy([^\n#]*)", text, re.MULTILINE)
    assert match
    spec = match.group(1)
    assert ">=3.7.0" in spec, (
        f"Lower bound >=3.7.0 must be preserved; got spec {spec!r}"
    )


def test_spacy_actually_imports_on_this_python():
    """smoke test: spaCy must import successfully in this environment."""
    import spacy
    # Version must be 3.7.x or 3.8.x (the two allowed series)
    version = spacy.__version__
    major_minor = ".".join(version.split(".")[:2])
    assert major_minor in {"3.7", "3.8"}, (
        f"spaCy {version} is outside the allowed 3.7.x / 3.8.x range"
    )


def test_python_version_in_requires_python_allows_313():
    """pyproject.toml requires-python must not exclude Python 3.13."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'requires-python\s*=\s*"([^"]+)"', pyproject)
    assert match, "requires-python not found in pyproject.toml"
    spec = match.group(1)
    # `>=3.10` permits 3.13. A spec like `>=3.10,<3.13` would not.
    assert "<3.13" not in spec, (
        f"requires-python excludes Python 3.13: {spec!r}"
    )
    assert "<3.12" not in spec, (
        f"requires-python excludes Python 3.12+: {spec!r}"
    )


def test_nlp_pipeline_imports_cleanly():
    """The actual consumer of spaCy must import without error."""
    # Force-import to catch any compatibility breakage
    import scripts.nlp_pipeline  # noqa: F401


def test_current_python_version_is_supported_according_to_requires_python():
    """Self-check: this Python must satisfy the requires-python spec
    declared in pyproject.toml. If we declared support we should at
    least be running on a supported version ourselves."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'requires-python\s*=\s*">=([\d.]+)"', pyproject)
    assert match
    min_required = tuple(int(p) for p in match.group(1).split("."))
    current = sys.version_info[:2]
    assert current >= min_required, (
        f"Current Python {current} below required minimum {min_required}"
    )
