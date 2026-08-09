#!/usr/bin/env python3
"""freeze_ner_components.py — Freeze NER components for provenance verification.

Per audit round 49: NER identity must be frozen, not just reported.
This script generates:
    provenance/frozen_components/entity_dictionary.json
    provenance/frozen_components/entity_dictionary.sha256
    provenance/frozen_components/stopword_set.json
    provenance/frozen_components/stopword_set.sha256
    provenance/frozen_components/ner_model_info.json
    provenance/frozen_components/ner_model_info.sha256

The runtime verification (in generation_null.py) will reject any mismatch
between these frozen artifacts and the actual runtime components.

This is the same principle that hardened the Phase 7 freeze:
    disk content != frozen content → substitution detected.
"""
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "provenance" / "frozen_components"


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_artifact(name: str, data: dict) -> str:
    """Write a JSON artifact and its SHA-256.

    Returns the SHA-256.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Canonical JSON: sorted keys, compact separators
    json_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sha = compute_sha256(json_bytes)

    # Write JSON (pretty-printed for readability)
    json_path = OUTPUT_DIR / f"{name}.json"
    json_path.write_text(json.dumps(data, indent=2))

    # Write SHA-256
    sha_path = OUTPUT_DIR / f"{name}.sha256"
    sha_path.write_text(f"{sha}  {name}.json\n")

    # Verify reproducibility
    reloaded = json.loads(json_path.read_text())
    reloaded_bytes = json.dumps(reloaded, sort_keys=True, separators=(",", ":")).encode("utf-8")
    reloaded_sha = compute_sha256(reloaded_bytes)
    assert reloaded_sha == sha, (
        f"REPRODUCIBILITY FAILED for {name}: "
        f"original={sha[:16]}..., reloaded={reloaded_sha[:16]}..."
    )

    print(f"  {name}.json: {len(json_bytes)} bytes, SHA-256: {sha[:16]}...")
    return sha


def get_entity_dictionary():
    """Get the frozen entity dictionary.

    This is the preregistered set of valid scientific concepts.
    Only entities in this dictionary are considered as shared entities.
    """
    return sorted([
        # General scientific terms
        "crystal", "crystallization", "nucleation", "growth", "dissolution",
        "precipitation", "mineral", "mineralization", "biomineralization",
        "calcium", "phosphate", "carbonate", "silica", "silicate",
        "protein", "enzyme", "cell", "tissue", "membrane",
        "transport", "diffusion", "osmosis", "cavitation", "acoustic",
        "ultrasound", "frequency", "wavelength", "amplitude",
        "thermal", "temperature", "heat", "energy", "kinetic",
        "thermodynamic", "entropy", "enthalpy", "free",
        "chemical", "reaction", "catalyst", "kinetics", "equilibrium",
        "phase", "transition", "polymorph", "stable", "metastable",
        "solution", "solvent", "solute", "concentration", "saturation",
        "supersaturated", "interface", "surface", "boundary", "layer",
        "molecular", "atomic", "ion", "ionic", "charge",
        "electric", "magnetic", "field", "force", "pressure",
        "stress", "strain", "elastic", "plastic", "deformation",
        "fracture", "crack", "defect", "lattice", "structure",
        "material", "composite", "polymer", "ceramic", "metal",
        "alloy", "oxide", "hydroxide", "acid", "base",
        "oxidation", "reduction", "electron", "proton", "neutron",
        "photon", "quantum", "wave", "particle", "interaction",
        "binding", "adsorption", "absorption", "desorption", "release",
        "mechanism", "pathway", "process", "phenomenon", "effect",
        "formation", "transformation", "conversion", "synthesis",
        "degradation", "stability", "instability",
        # Domain-specific terms
        "bone", "shell", "skeleton", "biological",
        "marine", "diatom", "osteoblast", "collagen",
        "sonocrystallization", "sonochemical",
        "radiative", "cooling", "emission",
        "desalination", "purification", "filtration", "separation",
        "battery", "electrode", "electrolyte", "cathode", "anode",
        "capacitor", "conductor", "insulator", "semiconductor",
    ])


def get_stopword_set():
    """Get the frozen stopword set.

    This is a fixed set of English stopwords.
    """
    return sorted([
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "must", "shall",
        "can", "need", "dare", "ought", "used", "this", "that", "these",
        "those", "they", "what", "which", "who", "when", "where", "why",
        "how", "all", "each", "every", "both", "few", "more", "most",
        "other", "some", "such", "not", "only", "own", "same", "than",
        "too", "very", "just", "also", "through", "into", "out", "up",
        "down", "about", "above", "below", "over", "under", "again",
        "further", "then", "once", "here", "there",
        "its", "their", "his", "her", "our", "your", "them",
    ])


def get_ner_model_info():
    """Get the frozen NER model information."""
    import spacy
    return {
        "ner_library": "spacy",
        "ner_model": "en_core_web_sm",
        "spacy_version": spacy.__version__,
        "python_version": sys.version.split()[0],
        "model_source": "spaCy model package",
        "model_capabilities": ["ner", "noun_chunks", "lemmatization", "pos_tagging"],
        "canonicalization_rule": "lowercase → strip punctuation → lemmatize (first non-stop token lemma)",
        "min_token_length": 4,
    }


def main():
    print("Freezing NER components for provenance verification...")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Write entity dictionary
    print("Entity dictionary:")
    entity_dict = get_entity_dictionary()
    dict_artifact = {
        "artifact_type": "FROZEN_ENTITY_DICTIONARY",
        "description": "Preregistered set of valid scientific concepts for shared-entity extraction",
        "n_entries": len(entity_dict),
        "entries": entity_dict,
    }
    dict_sha = write_artifact("entity_dictionary", dict_artifact)

    # Write stopword set
    print("Stopword set:")
    stopwords = get_stopword_set()
    stopword_artifact = {
        "artifact_type": "FROZEN_STOPWORD_SET",
        "description": "Fixed English stopword set for entity filtering",
        "n_entries": len(stopwords),
        "entries": stopwords,
    }
    stopword_sha = write_artifact("stopword_set", stopword_artifact)

    # Write NER model info
    print("NER model info:")
    ner_info = get_ner_model_info()
    ner_artifact = {
        "artifact_type": "FROZEN_NER_MODEL_INFO",
        "description": "Frozen NER model identity for provenance verification",
        "model_info": ner_info,
    }
    ner_sha = write_artifact("ner_model_info", ner_artifact)

    print()
    print("Freeze summary:")
    print(f"  entity_dictionary.sha256: {dict_sha[:16]}...")
    print(f"  stopword_set.sha256:      {stopword_sha[:16]}...")
    print(f"  ner_model_info.sha256:    {ner_sha[:16]}...")
    print()
    print("Runtime verification will reject any mismatch between these")
    print("frozen artifacts and the actual runtime components.")


if __name__ == "__main__":
    main()
