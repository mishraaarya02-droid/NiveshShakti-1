"""Unicode normalization and script-based language identification."""
import unicodedata


def normalize_extracted_text(text: str) -> tuple[str, str]:
    normalized = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    latin_letters = sum(char.isascii() and char.isalpha() for char in normalized)
    devanagari_letters = sum("\u0900" <= char <= "\u097f" and char.isalpha() for char in normalized)

    if latin_letters and devanagari_letters:
        language = "HINGLISH"
    elif devanagari_letters:
        language = "HI"
    elif latin_letters:
        language = "EN"
    else:
        language = "UNKNOWN"
    return normalized, language