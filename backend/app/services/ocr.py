"""
OCR service for NiveshShakti.

Uses Tesseract via pytesseract to extract text from uploaded images.
When the Tesseract binary is not installed on the system, returns an honest
PROVIDER_UNAVAILABLE result — never a fabricated or mock extraction.
"""
from __future__ import annotations

import io
import warnings
from typing import Literal, Optional, Protocol, TypedDict

try:
    from PIL import Image, UnidentifiedImageError
    _PIL_AVAILABLE = True
except ImportError:
    Image = None
    UnidentifiedImageError = OSError
    _PIL_AVAILABLE = False

try:
    import pytesseract
except ImportError:
    pytesseract = None

from .uploads import IMAGE_MAX_FILE_SIZE_BYTES, IMAGE_UPLOAD_TYPES, UploadValidationError, validate_upload_metadata


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ALLOWED_MIME_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
}

MAX_FILE_SIZE_BYTES = IMAGE_MAX_FILE_SIZE_BYTES


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
class OCRResult(TypedDict):
    status: Literal["SUCCESS", "PROVIDER_UNAVAILABLE", "INVALID_INPUT", "ERROR"]
    text: Optional[str]
    message: str


class OCRProvider(Protocol):
    def extract_text(self, image: Image.Image) -> str:
        """Return text recognized from a validated image."""


class TesseractOCRProvider:
    def extract_text(self, image: Image.Image) -> str:
        if pytesseract is None:
            raise RuntimeError("pytesseract is not installed")
        try:
            return pytesseract.image_to_string(image, lang="eng+hin")
        except pytesseract.pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError("Tesseract binary is not installed") from exc
        except pytesseract.pytesseract.TesseractError:
            try:
                return pytesseract.image_to_string(image, lang="eng")
            except pytesseract.pytesseract.TesseractNotFoundError as exc:
                raise RuntimeError("Tesseract binary is not installed") from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def extract_text_from_image(
    file_bytes: bytes,
    mime_type: str,
    filename: str = "upload.png",
    provider: Optional[OCRProvider] = None,
) -> OCRResult:
    """
    Extract text from an image using Tesseract OCR.

    Returns an OCRResult dict with:
        status  - one of SUCCESS | PROVIDER_UNAVAILABLE | INVALID_INPUT | ERROR
        text    - extracted string (None when status != SUCCESS)
        message - human-readable explanation

    This function NEVER returns fabricated text.
    """
    try:
        validate_upload_metadata(filename, mime_type, IMAGE_UPLOAD_TYPES)
    except UploadValidationError as exc:
        return OCRResult(
            status="INVALID_INPUT",
            text=None,
            message=str(exc),
        )

    if not file_bytes:
        return OCRResult(status="INVALID_INPUT", text=None, message="The uploaded image is empty.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return OCRResult(
            status="INVALID_INPUT",
            text=None,
            message=f"File too large ({len(file_bytes) // 1024} KB). Maximum allowed is 5 MB."
        )

    if not _PIL_AVAILABLE:
        return OCRResult(
            status="PROVIDER_UNAVAILABLE",
            text=None,
            message="Image OCR is unavailable because Pillow is not installed.",
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(file_bytes))
            expected_format = {
                "image/jpeg": "JPEG",
                "image/png": "PNG",
                "image/webp": "WEBP",
                "image/tiff": "TIFF",
            }[mime_type]
            if image.format != expected_format:
                return OCRResult(status="INVALID_INPUT", text=None, message="Image content does not match its declared type.")
            image.verify()
            image = Image.open(io.BytesIO(file_bytes))
            if image.width * image.height > 40_000_000:
                return OCRResult(status="INVALID_INPUT", text=None, message="Image dimensions exceed the processing limit.")
            image.load()

        active_provider = provider or TesseractOCRProvider()
        extracted = active_provider.extract_text(image)

        extracted = extracted.strip()
        if not extracted:
            return OCRResult(
                status="SUCCESS",
                text="",
                message="OCR completed but no text was detected in the image."
            )
        return OCRResult(status="SUCCESS", text=extracted, message="OCR completed successfully.")

    except RuntimeError as exc:
        if str(exc) == "pytesseract is not installed" or str(exc) == "Tesseract binary is not installed":
            return OCRResult(
                status="PROVIDER_UNAVAILABLE",
                text=None,
                message="Tesseract OCR is unavailable. Install Tesseract and its English/Hindi language data.",
            )
        return OCRResult(status="ERROR", text=None, message="Image OCR provider failed to process the image.")
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        return OCRResult(
            status="INVALID_INPUT",
            text=None,
            message="The uploaded file could not be decoded as a safe image.",
        )
    except Exception:
        return OCRResult(
            status="ERROR",
            text=None,
            message="Image OCR provider failed to process the image.",
        )
