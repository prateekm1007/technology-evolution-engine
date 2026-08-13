"""
Multilingual handler (Issue #5).

RULES:
  - The original-language text is ALWAYS retained. Never overwritten.
  - A translation is stored as a separate record linked via `translation_of`.
  - Every record carries language (ISO 639-1) and original_language.
  - A record that has been translated has language != original_language.
  - Translations are never equated with originals for content-hashing —
    the same text in two languages is two distinct content hashes, with a
    typed `translation_of` edge connecting them.

This module does NOT perform translation (that requires an LLM or translation
API). It provides the data structures and validation for retaining originals
alongside translations.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import hashlib


@dataclass(frozen=True)
class MultilingualText:
    """A text in a specific language, with optional link to its original."""
    text: str
    language: str              # ISO 639-1 (en, zh, ja, de, fr, ...)
    original_record_id: Optional[str] = None  # None if this IS the original
    translation_engine: Optional[str] = None  # "deepl" | "google" | "human" | None
    translation_confidence: Optional[float] = None

    def is_original(self) -> bool:
        return self.original_record_id is None

    def content_hash(self) -> str:
        return hashlib.sha256(f"{self.language}:{self.text}".encode()).hexdigest()


def make_translation(original_text: str, original_lang: str,
                     translated_text: str, translated_lang: str,
                     original_record_id: str,
                     engine: str = "unknown",
                     confidence: Optional[float] = None) -> tuple[MultilingualText, MultilingualText]:
    """Returns (original, translation) — both as MultilingualText objects.

    The original carries original_record_id=None (it IS the original).
    The translation carries original_record_id=original_record_id.
    """
    original = MultilingualText(
        text=original_text,
        language=original_lang,
        original_record_id=None,
    )
    translation = MultilingualText(
        text=translated_text,
        language=translated_lang,
        original_record_id=original_record_id,
        translation_engine=engine,
        translation_confidence=confidence,
    )
    return original, translation


def validate_multilingual_pair(original: MultilingualText,
                                translation: MultilingualText) -> list[str]:
    """Validate that (original, translation) form a consistent pair."""
    errors = []
    if not original.is_original():
        errors.append("original.is_original() must be True")
    if translation.is_original():
        errors.append("translation.is_original() must be False (needs original_record_id)")
    if original.language == translation.language:
        errors.append(f"original and translation have the same language: {original.language}")
    if translation.translation_engine is None:
        errors.append("translation must declare translation_engine")
    if translation.translation_confidence is not None:
        if not (0.0 <= translation.translation_confidence <= 1.0):
            errors.append(f"translation_confidence out of range: {translation.translation_confidence}")
    return errors


# Common ISO 639-1 codes for cross-corpus work
SUPPORTED_LANGUAGES = {
    "en", "zh", "ja", "ko", "de", "fr", "es", "it", "pt", "ru",
    "ar", "hi", "fa", "tr", "nl", "sv", "no", "da", "fi", "pl",
    "cs", "hu", "ro", "el", "he", "th", "vi", "id", "ms",
}


def is_supported_language(code: str) -> bool:
    return code in SUPPORTED_LANGUAGES
