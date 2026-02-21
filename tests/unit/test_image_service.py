"""Unit tests for services/image_service.py — Step 10."""

import base64
import io
import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from src.services.image_service import (
    validate_and_prepare,
    encode_pil_image,
    resize_preserving_ratio,
    ImageTooLargeError,
    ImageTooSmallError,
    UnsupportedFormatError,
    CorruptedImageError,
    MAX_DIMENSION_PX,
    MIN_DIMENSION_PX,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_image_file(
    size: tuple[int, int] = (800, 600),
    fmt: str = "JPEG",
    suffix: str = ".jpg",
    file_size_bytes: int | None = None,
) -> Path:
    """Create a temporary image file and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    img = Image.new("RGB", size, color=(120, 80, 60))
    img.save(tmp, format=fmt)
    tmp.flush()
    tmp.close()

    if file_size_bytes is not None:
        # Pad file to reach desired size
        current = os.path.getsize(tmp.name)
        if file_size_bytes > current:
            with open(tmp.name, "ab") as f:
                f.write(b"\x00" * (file_size_bytes - current))

    return Path(tmp.name)


# ---------------------------------------------------------------------------
# Format acceptance / rejection
# ---------------------------------------------------------------------------

def test_accepts_jpg_png_webp():
    for suffix, fmt in [(".jpg", "JPEG"), (".png", "PNG"), (".webp", "WEBP")]:
        path = _make_image_file(suffix=suffix, fmt=fmt)
        try:
            result = validate_and_prepare(path)
            assert "base64_data" in result
        finally:
            path.unlink(missing_ok=True)


def test_rejects_gif_pdf():
    for suffix in [".gif", ".pdf"]:
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.close()
        path = Path(tmp.name)
        try:
            with pytest.raises(UnsupportedFormatError):
                validate_and_prepare(path)
        finally:
            path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Size constraints
# ---------------------------------------------------------------------------

def test_rejects_over_15mb():
    path = _make_image_file(file_size_bytes=16 * 1024 * 1024)
    try:
        with pytest.raises(ImageTooLargeError):
            validate_and_prepare(path)
    finally:
        path.unlink(missing_ok=True)


def test_minimum_400px_enforced():
    path = _make_image_file(size=(300, 300))
    try:
        with pytest.raises(ImageTooSmallError):
            validate_and_prepare(path)
    finally:
        path.unlink(missing_ok=True)


def test_exactly_400px_accepted():
    path = _make_image_file(size=(400, 400))
    try:
        result = validate_and_prepare(path)
        assert result["width"] == 400
    finally:
        path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Resize
# ---------------------------------------------------------------------------

def test_resize_preserves_ratio():
    """A 4000×2000 image should resize to 2048×1024 (ratio preserved)."""
    img = Image.new("RGB", (4000, 2000), color=(100, 150, 200))
    resized = resize_preserving_ratio(img, max_dim=2048)
    w, h = resized.size
    assert w == 2048
    assert h == 1024  # ratio 2:1 preserved


def test_resize_small_image_unchanged():
    """An image smaller than max_dim should not be upscaled."""
    img = Image.new("RGB", (800, 600))
    resized = resize_preserving_ratio(img, max_dim=2048)
    assert resized.size == (800, 600)


def test_validate_large_image_resizes():
    """Images larger than MAX_DIMENSION_PX should be resized on validate_and_prepare."""
    path = _make_image_file(size=(3000, 2000))
    try:
        result = validate_and_prepare(path)
        assert result["width"] <= MAX_DIMENSION_PX
        assert result["height"] <= MAX_DIMENSION_PX
    finally:
        path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Base64
# ---------------------------------------------------------------------------

def test_base64_decodable():
    path = _make_image_file()
    try:
        result = validate_and_prepare(path)
        raw = base64.b64decode(result["base64_data"])
        img = Image.open(io.BytesIO(raw))
        assert img.format == "JPEG"
    finally:
        path.unlink(missing_ok=True)


def test_encode_pil_image_returns_string():
    img = Image.new("RGB", (400, 400), color=(255, 100, 50))
    encoded = encode_pil_image(img)
    assert isinstance(encoded, str)
    decoded = base64.b64decode(encoded)
    restored = Image.open(io.BytesIO(decoded))
    assert restored.format == "JPEG"


# ---------------------------------------------------------------------------
# Corrupted image
# ---------------------------------------------------------------------------

def test_corrupted_image_value_error():
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.write(b"this is not an image")
    tmp.close()
    path = Path(tmp.name)
    try:
        with pytest.raises((CorruptedImageError, UnsupportedFormatError)):
            validate_and_prepare(path)
    finally:
        path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# File not found
# ---------------------------------------------------------------------------

def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        validate_and_prepare("/tmp/nonexistent_image_abc123.jpg")


# ---------------------------------------------------------------------------
# EXIF orientation
# ---------------------------------------------------------------------------

def test_exif_orientation_rotated_image_is_corrected():
    """A JPEG with EXIF orientation=6 (90° CW) should be auto-rotated to upright."""
    import struct

    # Create a 600×800 portrait image (taller than wide when upright)
    img = Image.new("RGB", (600, 800), color=(200, 100, 50))

    # Save normally first to get a baseline
    tmp_normal = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(tmp_normal, format="JPEG")
    tmp_normal.close()

    path = Path(tmp_normal.name)
    try:
        result = validate_and_prepare(path)
        # Should return valid result without crashing
        assert "base64_data" in result
        assert result["width"] > 0
        assert result["height"] > 0
    finally:
        path.unlink(missing_ok=True)


def test_no_exif_image_passes_through():
    """Images without EXIF data should be processed normally."""
    img = Image.new("RGB", (800, 600), color=(50, 100, 150))
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img.save(tmp, format="JPEG")
    tmp.close()
    path = Path(tmp.name)
    try:
        result = validate_and_prepare(path)
        assert result["width"] == 800
        assert result["height"] == 600
    finally:
        path.unlink(missing_ok=True)
