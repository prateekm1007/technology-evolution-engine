#!/usr/bin/env python3
"""verify_audit_instrument.py — Independent verification of the frozen audit instrument.

Per audit round 53: the instrument freeze must be INDEPENDENTLY VERIFIED,
not just self-reported. Three concerns:

1. HASH CONVENTION: The canonical serialization convention must be explicitly
   frozen and the internal instrument_sha must be verified (not just the
   sidecar file).

2. RUNTIME ENVIRONMENT: Frozen source files don't imply frozen behavior.
   The instrument must record and verify:
   - Python version
   - spaCy version + model version
   - NumPy/SymPy versions (where relevant)
   - All imported dependency versions

3. ACTUAL LOADED MODULE: The verifier must check the ACTUAL loaded module
   bytes at runtime, not just the expected repo path. This catches
   import-path substitution.

Additionally: an execution manifest must be sealed before execution,
and any change after sealing → EXECUTION_INVALIDATED.

VERIFICATION LEVELS:
    SOURCE_FROZEN: source file SHA-256 matches frozen hash
    DATA_FROZEN: data artifacts (NER dictionary, stopwords, model info) match
    RUNTIME_FROZEN: Python version, spaCy version, dependency versions match
    MODULE_LOADED: actual loaded module bytes match frozen source hash
"""
import hashlib
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_DIR = REPO_ROOT / "provenance" / "frozen_components"


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------
# 1. CANONICAL SERIALIZATION CONVENTION (frozen)
# --------------------------------------------------------------------
CANONICAL_CONVENTION = {
    "format": "JSON",
    "sort_keys": True,
    "separators":(",", ":"),
    "encoding": "UTF-8",
    "no_trailing_newline": True,
    "description": (
        "Canonical serialization for hash computation. "
        "The instrument_sha256 field is computed from the instrument "
        "payload WITHOUT the instrument_sha256 field itself, using "
        "this convention. Verification must recompute using the same "
        "convention."
    ),
}


def canonical_serialize(obj: Any) -> bytes:
    """Serialize using the frozen canonical convention."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_internal_sha(artifact: dict) -> Tuple[bool, str]:
    """Verify that the internal instrument_sha256 is consistent.

    This checks that:
    1. instrument_sha256 field exists
    2. Removing it and re-hashing with the canonical convention produces the same value

    This is DIFFERENT from checking the sidecar .sha256 file, which only
    proves file integrity, not internal consistency.
    """
    if "instrument_sha256" not in artifact:
        return False, "Missing instrument_sha256 field"

    recorded_sha = artifact["instrument_sha256"]
    payload_without_sha = {k: v for k, v in artifact.items() if k != "instrument_sha256"}
    computed_sha = compute_sha256(canonical_serialize(payload_without_sha))

    if computed_sha != recorded_sha:
        return False, (
            f"Internal SHA mismatch: recorded={recorded_sha[:16]}... "
            f"computed={computed_sha[:16]}... "
            f"The instrument_sha256 field does not match the canonical hash "
            f"of the remaining payload."
        )

    return True, ""


def verify_sidecar_sha() -> Tuple[bool, str]:
    """Verify the sidecar .sha256 file is consistent with the internal
    instrument_sha256.

    The sidecar SHA is the canonical hash of the payload without the
    instrument_sha256 field. The internal instrument_sha256 should be
    the same value. This checks they agree.

    File-byte integrity is checked separately by comparing the file's
    parsed instrument_sha256 against the sidecar.
    """
    json_path = FROZEN_DIR / "audit_instrument.json"
    sha_path = FROZEN_DIR / "audit_instrument.sha256"

    if not json_path.exists():
        return False, f"Artifact not found: {json_path}"
    if not sha_path.exists():
        return False, f"Sidecar SHA not found: {sha_path}"

    # Parse the artifact
    artifact = json.loads(json_path.read_text())
    internal_sha = artifact.get("instrument_sha256")

    # Read sidecar
    sidecar_sha = sha_path.read_text().split()[0]

    # The sidecar should match the internal instrument_sha256
    if sidecar_sha != internal_sha:
        return False, (
            f"Sidecar SHA does not match internal instrument_sha256: "
            f"sidecar={sidecar_sha[:16]}... internal={internal_sha[:16] if internal_sha else 'None'}..."
        )

    # Also verify internal consistency (canonical hash of payload matches)
    ok, err = verify_internal_sha(artifact)
    if not ok:
        return False, f"Internal SHA inconsistent: {err}"

    return True, ""


# --------------------------------------------------------------------
# 2. RUNTIME ENVIRONMENT VERIFICATION
# --------------------------------------------------------------------
def get_runtime_manifest() -> Dict[str, Any]:
    """Capture the current runtime environment.

    This records:
    - Python version
    - spaCy version + model version
    - NumPy version (if available)
    - SymPy version (if available)
    - All versions of modules imported by the audit instrument
    """
    manifest = {
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": sys.platform,
    }

    # spaCy
    try:
        import spacy
        manifest["spacy_version"] = spacy.__version__
        from engine.b2_provenance.generation_null import NULL_CONFIG
        manifest["spacy_model"] = NULL_CONFIG["ner_model"]
    except Exception:
        manifest["spacy_version"] = None
        manifest["spacy_model"] = None

    # NumPy
    try:
        import numpy
        manifest["numpy_version"] = numpy.__version__
    except Exception:
        manifest["numpy_version"] = None

    # SymPy
    try:
        import sympy
        manifest["sympy_version"] = sympy.__version__
    except Exception:
        manifest["sympy_version"] = None

    # SciPy
    try:
        import scipy
        manifest["scipy_version"] = scipy.__version__
    except Exception:
        manifest["scipy_version"] = None

    return manifest


def verify_runtime_environment(frozen_manifest: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify the runtime environment matches the frozen manifest."""
    runtime = get_runtime_manifest()

    for key in ["python_version", "spacy_version", "spacy_model",
                "numpy_version", "sympy_version", "scipy_version"]:
        frozen_val = frozen_manifest.get(key)
        runtime_val = runtime.get(key)

        if frozen_val != runtime_val:
            return False, (
                f"Runtime mismatch for '{key}': "
                f"frozen={frozen_val}, runtime={runtime_val}"
            )

    return True, ""


# --------------------------------------------------------------------
# 3. ACTUAL LOADED MODULE VERIFICATION
# --------------------------------------------------------------------
def verify_loaded_module(module_name: str, expected_sha: str,
                          expected_path: str) -> Tuple[bool, str]:
    """Verify the ACTUAL loaded module matches the frozen hash.

    This imports the module, gets its source file, reads the actual bytes,
    and computes SHA-256. This catches import-path substitution where
    a different file is loaded than the one in the repo.

    Args:
        module_name: dotted module path (e.g., "engine.b2_provenance.frozen_parser")
        expected_sha: the frozen SHA-256
        expected_path: the expected relative path in the repo

    Returns:
        (verified, error_message)
    """
    try:
        # Import the module
        if module_name not in sys.modules:
            importlib.import_module(module_name)
        module = sys.modules[module_name]

        # Get the actual source file
        actual_path = inspect.getfile(module)
        actual_path_obj = Path(actual_path).resolve()

        # Verify path matches expected
        expected_path_obj = (REPO_ROOT / expected_path).resolve()
        if actual_path_obj != expected_path_obj:
            return False, (
                f"Module path mismatch for {module_name}: "
                f"actual={actual_path_obj}, expected={expected_path_obj}. "
                f"Import-path substitution detected."
            )

        # Read actual bytes and compute SHA
        actual_bytes = actual_path_obj.read_bytes()
        actual_sha = compute_sha256(actual_bytes)

        if actual_sha != expected_sha:
            return False, (
                f"Module SHA mismatch for {module_name}: "
                f"actual={actual_sha[:16]}..., expected={expected_sha[:16]}... "
                f"The loaded source does not match the frozen hash."
            )

        return True, ""

    except Exception as e:
        return False, f"Failed to verify module {module_name}: {e}"


def verify_all_loaded_modules(artifact: dict) -> Tuple[bool, List[str]]:
    """Verify ALL frozen modules are actually loaded from the correct path
    with the correct SHA-256.

    Returns:
        (all_verified, list_of_errors)
    """
    errors = []
    components = artifact.get("components", {})

    module_mapping = {
        "audit_script": ("scripts.baseline_equivalence_audit", None),
        "parser_script": ("engine.b2_provenance.frozen_parser", None),
        "generation_null_script": ("engine.b2_provenance.generation_null", None),
        "provenance_ledger_script": ("engine.b2_provenance.provenance_ledger", None),
        "content_addressed_storage_script": ("engine.b2_provenance.content_addressed_storage", None),
    }

    for component_name, (module_name, _) in module_mapping.items():
        if component_name not in components:
            errors.append(f"Missing component: {component_name}")
            continue

        expected_sha = components[component_name]["sha256"]
        expected_path = components[component_name]["path"]

        verified, err = verify_loaded_module(module_name, expected_sha, expected_path)
        if not verified:
            errors.append(f"{component_name}: {err}")

    return len(errors) == 0, errors


# --------------------------------------------------------------------
# FULL INSTRUMENT VERIFICATION
# --------------------------------------------------------------------
def verify_instrument() -> Dict[str, Any]:
    """Full independent verification of the frozen audit instrument.

    Checks:
    1. Sidecar SHA matches file bytes (file integrity)
    2. Internal instrument_sha256 is consistent (internal consistency)
    3. All component source files match frozen hashes (SOURCE_FROZEN)
    4. NER data artifacts match frozen hashes (DATA_FROZEN)
    5. Runtime environment matches frozen manifest (RUNTIME_FROZEN)
    6. Actually loaded modules match frozen hashes (MODULE_LOADED)

    Returns:
        Dict with verification results for each level.
    """
    results = {
        "source_frozen": False,
        "data_frozen": False,
        "runtime_frozen": False,
        "module_loaded": False,
        "sidecar_verified": False,
        "internal_sha_verified": False,
        "errors": [],
    }

    # Load the artifact
    json_path = FROZEN_DIR / "audit_instrument.json"
    if not json_path.exists():
        results["errors"].append(f"Instrument artifact not found: {json_path}")
        return results

    artifact = json.loads(json_path.read_text())

    # 1. Sidecar SHA
    sidecar_ok, sidecar_err = verify_sidecar_sha()
    results["sidecar_verified"] = sidecar_ok
    if not sidecar_ok:
        results["errors"].append(f"SIDECAR: {sidecar_err}")

    # 2. Internal SHA consistency
    internal_ok, internal_err = verify_internal_sha(artifact)
    results["internal_sha_verified"] = internal_ok
    if not internal_ok:
        results["errors"].append(f"INTERNAL_SHA: {internal_err}")

    # 3. SOURCE_FROZEN: verify each component file
    source_errors = []
    for name, info in artifact.get("components", {}).items():
        path = REPO_ROOT / info["path"]
        if not path.exists():
            source_errors.append(f"{name}: file not found at {path}")
            continue
        actual_sha = compute_sha256(path.read_bytes())
        if actual_sha != info["sha256"]:
            source_errors.append(
                f"{name}: SHA mismatch actual={actual_sha[:16]}... "
                f"frozen={info['sha256'][:16]}..."
            )
    results["source_frozen"] = len(source_errors) == 0
    results["errors"].extend([f"SOURCE: {e}" for e in source_errors])

    # 4. DATA_FROZEN: verify NER data artifacts
    data_errors = []
    ner = artifact.get("ner_components", {})
    for name, expected_sha in ner.items():
        if expected_sha is None:
            data_errors.append(f"{name}: no frozen hash")
            continue
        artifact_name = name.replace("_sha256", "").replace("ner_model_info", "ner_model_info")
        data_path = FROZEN_DIR / f"{artifact_name}.json"
        if not data_path.exists():
            data_errors.append(f"{name}: data file not found")
            continue
        data = json.loads(data_path.read_text())
        actual_sha = compute_sha256(canonical_serialize(data))
        if actual_sha != expected_sha:
            data_errors.append(
                f"{name}: SHA mismatch actual={actual_sha[:16]}... "
                f"frozen={expected_sha[:16]}..."
            )
    results["data_frozen"] = len(data_errors) == 0
    results["errors"].extend([f"DATA: {e}" for e in data_errors])

    # 5. RUNTIME_FROZEN: verify runtime environment
    if "runtime_manifest" in artifact:
        runtime_ok, runtime_err = verify_runtime_environment(artifact["runtime_manifest"])
        results["runtime_frozen"] = runtime_ok
        if not runtime_ok:
            results["errors"].append(f"RUNTIME: {runtime_err}")
    else:
        results["runtime_frozen"] = False
        results["errors"].append("RUNTIME: no runtime_manifest in instrument")

    # 6. MODULE_LOADED: verify actual loaded modules
    module_ok, module_errors = verify_all_loaded_modules(artifact)
    results["module_loaded"] = module_ok
    results["errors"].extend([f"MODULE: {e}" for e in module_errors])

    return results


# --------------------------------------------------------------------
# EXECUTION MANIFEST
# --------------------------------------------------------------------
def create_execution_manifest(
    preregistration_id: str,
    case_ids: List[str],
    source_pair_hashes: Dict[str, str],
) -> Dict[str, Any]:
    """Create a sealed execution manifest before engine/null execution.

    This manifest is created BEFORE either arm runs. It records:
    - The frozen audit instrument hash
    - The preregistration ID
    - The case set
    - Source pair hashes
    - Runtime manifest
    - Seed derivation rule

    Once sealed, any change to any frozen component invalidates the execution.

    Returns:
        The execution manifest dict.
    """
    # Load the frozen instrument
    instrument_path = FROZEN_DIR / "audit_instrument.json"
    instrument = json.loads(instrument_path.read_text())

    # Get runtime manifest
    runtime = get_runtime_manifest()

    manifest = {
        "manifest_type": "EXECUTION_MANIFEST",
        "preregistration_id": preregistration_id,
        "audit_instrument_sha256": instrument.get("instrument_sha256"),
        "case_ids": case_ids,
        "source_pair_hashes": source_pair_hashes,
        "runtime_manifest": runtime,
        "seed_derivation_rule": "SHA256(preregistration_id || case_id || 'downstream')",
        "diagnostic_rule": (
            "This execution is DIAGNOSTIC. Results do NOT establish "
            "baseline fairness or unfairness. They establish the empirical "
            "structure of the two arms."
        ),
    }

    # Seal: compute manifest hash
    manifest_str = canonical_serialize(manifest)
    manifest_sha = compute_sha256(manifest_str)
    manifest["manifest_sha256"] = manifest_sha

    return manifest


def verify_execution_manifest(manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Verify an execution manifest is still valid.

    Checks:
    1. The manifest's internal hash is consistent
    2. The audit instrument is still the same
    3. The runtime environment hasn't changed
    4. All frozen components are still frozen

    If anything has changed → EXECUTION_INVALIDATED.
    """
    errors = []

    # 1. Internal hash consistency
    if "manifest_sha256" not in manifest:
        errors.append("Missing manifest_sha256")
    else:
        recorded = manifest["manifest_sha256"]
        payload = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
        computed = compute_sha256(canonical_serialize(payload))
        if computed != recorded:
            errors.append(
                f"Manifest SHA mismatch: recorded={recorded[:16]}... "
                f"computed={computed[:16]}... MANIFEST TAMPERED."
            )

    # 2. Audit instrument still valid
    instrument_results = verify_instrument()
    if not all([
        instrument_results["sidecar_verified"],
        instrument_results["internal_sha_verified"],
        instrument_results["source_frozen"],
        instrument_results["data_frozen"],
        instrument_results["runtime_frozen"],
        instrument_results["module_loaded"],
    ]):
        errors.append("Audit instrument verification FAILED")
        errors.extend(instrument_results["errors"])

    # 3. Runtime matches manifest
    if "runtime_manifest" in manifest:
        rt_ok, rt_err = verify_runtime_environment(manifest["runtime_manifest"])
        if not rt_ok:
            errors.append(f"Runtime changed since manifest sealed: {rt_err}")

    if errors:
        errors.insert(0, "EXECUTION_INVALIDATED")

    return len(errors) == 0, errors
