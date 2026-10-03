"""
Speech-to-text service for NiveshShakti.

Uses OpenAI Whisper (open-source, CPU) for audio transcription.
Requires PyTorch to be installed. When torch or whisper are unavailable,
returns an honest PROVIDER_UNAVAILABLE result — never a fabricated transcript.
"""
from __future__ import annotations

import io
import shutil
import tempfile
import wave
from pathlib import Path
from typing import Literal, Optional, Protocol, TypedDict

from .uploads import AUDIO_MAX_FILE_SIZE_BYTES, AUDIO_UPLOAD_TYPES, UploadValidationError, validate_upload_metadata


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ALLOWED_MIME_TYPES: set[str] = {
    "audio/mpeg",       # .mp3
    "audio/wav",        # .wav
    "audio/x-wav",      # .wav (alt)
    "audio/mp4",        # .m4a (some browsers)
    "audio/x-m4a",     # .m4a
    "audio/ogg",        # .ogg
    "audio/flac",       # .flac
    "audio/x-flac",    # .flac (alt)
}

MIME_TO_EXT: dict[str, str] = {
    mime_type: next(iter(extensions))
    for mime_type, extensions in AUDIO_UPLOAD_TYPES.items()
}
MAX_FILE_SIZE_BYTES = AUDIO_MAX_FILE_SIZE_BYTES


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
class SpeechResult(TypedDict):
    status: Literal["SUCCESS", "PROVIDER_UNAVAILABLE", "INVALID_INPUT", "ERROR"]
    text: Optional[str]
    message: str


class SpeechProvider(Protocol):
    def transcribe(self, audio_path: str) -> str:
        """Return a transcript from a validated temporary audio file."""


class WhisperSpeechProvider:
    def transcribe(self, audio_path: str) -> str:
        try:
            import torch  # noqa: F401
            import whisper
        except ImportError as exc:
            raise RuntimeError("Whisper dependencies are not installed") from exc
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("FFmpeg is not installed")

        model = whisper.load_model("tiny", device="cpu")
        result = model.transcribe(audio_path)
        return str(result.get("text", ""))


def _has_valid_audio_signature(file_bytes: bytes, mime_type: str) -> bool:
    if mime_type in {"audio/wav", "audio/x-wav"}:
        try:
            with wave.open(io.BytesIO(file_bytes), "rb") as audio:
                return audio.getnframes() > 0 and audio.getnchannels() > 0 and audio.getframerate() > 0
        except (wave.Error, EOFError):
            return False
    if mime_type == "audio/mpeg":
        return file_bytes.startswith(b"ID3") or (
            len(file_bytes) >= 2 and file_bytes[0] == 0xFF and file_bytes[1] & 0xE0 == 0xE0
        )
    if mime_type in {"audio/mp4", "audio/x-m4a"}:
        return len(file_bytes) >= 12 and file_bytes[4:8] == b"ftyp"
    if mime_type == "audio/ogg":
        return file_bytes.startswith(b"OggS")
    if mime_type in {"audio/flac", "audio/x-flac"}:
        return file_bytes.startswith(b"fLaC")
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def transcribe_audio(
    file_bytes: bytes,
    mime_type: str,
    original_filename: str = "upload.wav",
    provider: Optional[SpeechProvider] = None,
) -> SpeechResult:
    """
    Transcribe audio using OpenAI Whisper (tiny model, CPU).

    Returns a SpeechResult dict with:
        status  - one of SUCCESS | PROVIDER_UNAVAILABLE | INVALID_INPUT | ERROR
        text    - transcription string (None when status != SUCCESS)
        message - human-readable explanation

    This function NEVER returns fabricated transcriptions.
    """
    try:
        validate_upload_metadata(original_filename, mime_type, AUDIO_UPLOAD_TYPES)
    except UploadValidationError as exc:
        return SpeechResult(
            status="INVALID_INPUT",
            text=None,
            message=str(exc),
        )

    if not file_bytes or not _has_valid_audio_signature(file_bytes, mime_type):
        return SpeechResult(status="INVALID_INPUT", text=None, message="The uploaded file is not valid audio.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return SpeechResult(
            status="INVALID_INPUT",
            text=None,
            message=f"File too large ({len(file_bytes) // (1024 * 1024)} MB). Maximum allowed is 25 MB."
        )

    ext = MIME_TO_EXT.get(mime_type, ".audio")
    try:
        active_provider = provider or WhisperSpeechProvider()
        with tempfile.TemporaryDirectory(prefix="niveshshakti-audio-") as temp_dir:
            audio_path = Path(temp_dir) / f"upload{ext}"
            audio_path.write_bytes(file_bytes)
            transcript = active_provider.transcribe(str(audio_path)).strip()

        if not transcript:
            return SpeechResult(
                status="SUCCESS",
                text="",
                message="Transcription completed but no speech was detected in the audio."
            )
        return SpeechResult(status="SUCCESS", text=transcript, message="Transcription completed successfully.")

    except RuntimeError as exc:
        if "dependencies are not installed" in str(exc) or "FFmpeg is not installed" in str(exc):
            return SpeechResult(
                status="PROVIDER_UNAVAILABLE",
                text=None,
                message="Audio transcription is unavailable. Install PyTorch, openai-whisper, and FFmpeg.",
            )
        return SpeechResult(
            status="ERROR",
            text=None,
            message="Whisper failed to process the uploaded audio.",
        )
    except Exception:
        return SpeechResult(status="ERROR", text=None, message="Whisper failed to process the uploaded audio.")
