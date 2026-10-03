"""Shared validation and bounded reads for untrusted multipart uploads."""
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Mapping, Set

from fastapi import UploadFile


IMAGE_MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
AUDIO_MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

IMAGE_UPLOAD_TYPES: dict[str, Set[str]] = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "image/tiff": {".tif", ".tiff"},
}
AUDIO_UPLOAD_TYPES: dict[str, Set[str]] = {
    "audio/mpeg": {".mp3"},
    "audio/wav": {".wav"},
    "audio/x-wav": {".wav"},
    "audio/mp4": {".m4a"},
    "audio/x-m4a": {".m4a"},
    "audio/ogg": {".ogg"},
    "audio/flac": {".flac"},
    "audio/x-flac": {".flac"},
}


class UploadValidationError(ValueError):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def validate_upload_metadata(
    filename: str | None,
    mime_type: str | None,
    allowed_types: Mapping[str, Set[str]],
) -> None:
    normalized_name = (filename or "").replace("\\", "/")
    extensions = allowed_types.get(mime_type or "")
    if not extensions or PurePosixPath(normalized_name).suffix.lower() not in extensions:
        raise UploadValidationError(
            415,
            "Upload MIME type and file extension must match a supported format.",
        )


async def read_limited_upload(file: UploadFile, max_size: int) -> bytes:
    if file.size is not None and file.size > max_size:
        raise UploadValidationError(413, "Upload exceeds the permitted size limit.")
    contents = await file.read(max_size + 1)
    if len(contents) > max_size:
        raise UploadValidationError(413, "Upload exceeds the permitted size limit.")
    return contents