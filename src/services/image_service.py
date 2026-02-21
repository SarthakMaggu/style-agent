"""Image validation, resizing, and base64 encoding service.

Handles all image pre-processing before Claude Vision or Replicate calls.
Enforces size, format, and resolution constraints.
"""

import base64
import io
import os
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

# Optional HEIC support
try:
    import pillow_heif  # type: ignore[import]
    pillow_heif.register_heif_opener()
    _HEIC_SUPPORTED = True
except ImportError:
    _HEIC_SUPPORTED = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024       # 15 MB
MIN_DIMENSION_PX = 400                        # minimum 400px on each side
MAX_DIMENSION_PX = 2048                       # cap before base64 to keep tokens down
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "HEIF", "HEIC"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
REJECTED_EXTENSIONS = {".gif", ".pdf", ".bmp", ".tiff", ".svg"}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ImageTooLargeError(ValueError):
    """Raised when the image file exceeds MAX_FILE_SIZE_BYTES."""


class ImageTooSmallError(ValueError):
    """Raised when either image dimension is below MIN_DIMENSION_PX."""


class UnsupportedFormatError(ValueError):
    """Raised when the image format is not in ALLOWED_FORMATS."""


class CorruptedImageError(ValueError):
    """Raised when the image file cannot be decoded."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_and_prepare(image_path: str | Path) -> dict[str, str | int]:
    """Validate, resize, and base64-encode an image for API submission.

    Performs the following steps:
    1. Check file exists and extension is allowed
    2. Check file size ≤ 15 MB
    3. Decode image and verify it's not corrupted
    4. Check minimum dimension 400 px
    5. Resize to MAX_DIMENSION_PX if larger
    6. Convert to JPEG in memory
    7. Return base64-encoded string + metadata

    Args:
        image_path: Path to the image file.

    Returns:
        Dict with keys: base64_data, media_type, width, height, original_path.

    Raises:
        FileNotFoundError: If the path does not exist.
        UnsupportedFormatError: If the file format is not allowed.
        ImageTooLargeError: If the file exceeds 15 MB.
        ImageTooSmallError: If either dimension is below 400 px.
        CorruptedImageError: If the image cannot be opened/decoded.
    """
    path = Path(image_path)

    # --- Existence check ---
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    # --- Extension check ---
    ext = path.suffix.lower()
    if ext in REJECTED_EXTENSIONS:
        raise UnsupportedFormatError(
            f"Format '{ext}' is not supported. Accepted: jpg, png, webp, heic."
        )
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFormatError(
            f"Format '{ext}' is not supported. Accepted: jpg, png, webp, heic."
        )

    # --- File size check ---
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ImageTooLargeError(
            f"Image is {file_size / 1_048_576:.1f} MB — maximum is 15 MB."
        )

    # --- Open and decode ---
    try:
        img = Image.open(path)
        img.verify()       # detects truncated / corrupted images
        img = Image.open(path)  # re-open after verify() (verify closes the file)
    except (UnidentifiedImageError, Exception) as exc:
        raise CorruptedImageError(f"Cannot decode image '{path.name}': {exc}") from exc

    # Check format
    fmt = (img.format or "").upper()
    if fmt not in ALLOWED_FORMATS:
        raise UnsupportedFormatError(f"Image format '{fmt}' is not supported.")

    # --- Auto-rotate per EXIF orientation (fixes sideways iPhone / HEIC photos) ---
    img = ImageOps.exif_transpose(img)

    # --- Dimension check ---
    width, height = img.size
    if width < MIN_DIMENSION_PX or height < MIN_DIMENSION_PX:
        raise ImageTooSmallError(
            f"Image dimensions {width}×{height} are below the minimum {MIN_DIMENSION_PX}×{MIN_DIMENSION_PX} px."
        )

    # --- Resize if too large ---
    img = img.convert("RGB")  # normalise to RGB (drops alpha for JPEG compat)
    if width > MAX_DIMENSION_PX or height > MAX_DIMENSION_PX:
        img.thumbnail((MAX_DIMENSION_PX, MAX_DIMENSION_PX), Image.LANCZOS)
        width, height = img.size

    # --- Encode to base64 ---
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "base64_data": b64,
        "media_type": "image/jpeg",
        "width": width,
        "height": height,
        "original_path": str(path.resolve()),
    }


def encode_pil_image(img: Image.Image) -> str:
    """Base64-encode a PIL Image object (for in-memory images).

    Args:
        img: PIL Image.

    Returns:
        Base64-encoded JPEG string.
    """
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def resize_preserving_ratio(img: Image.Image, max_dim: int = MAX_DIMENSION_PX) -> Image.Image:
    """Resize a PIL Image to fit within max_dim × max_dim, preserving aspect ratio.

    Args:
        img: PIL Image to resize.
        max_dim: Maximum dimension in pixels.

    Returns:
        Resized PIL Image.
    """
    img = img.copy()
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    return img
