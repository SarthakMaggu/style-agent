"""Replicate API service for caricature / stylised portrait generation.

Supports three styles using black-forest-labs/flux-kontext-pro:
  - pixar:      Pixar 3D animated character (face stylised, outfit stays real)
  - cartoon:    2D anime/cartoon illustration (full scene)
  - caricature: Watercolour editorial illustration (full scene)

Wraps Replicate client with:
- 120s timeout (generation is slow)
- 3-attempt retry with exponential backoff
- Graceful failure — returns None instead of raising, so caller can fall back
"""

import base64
import io
import logging
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

CARICATURE_TIMEOUT_SECONDS = 120

# ---------------------------------------------------------------------------
# Model — flux-kontext-pro (image-in / image-out, no versioned hash needed)
# ---------------------------------------------------------------------------

_FLUX_MODEL = "black-forest-labs/flux-kontext-pro"

# Per-style prompts — tuned from live tests
_STYLE_PROMPTS: dict[str, str] = {
    "pixar": (
        "Transform ONLY the face and head of this person into a Pixar 3D animated "
        "character — large expressive eyes, smooth skin, warm cinematic lighting, "
        "high quality render. Keep the outfit, body, and background completely "
        "photorealistic and unchanged."
    ),
    "cartoon": (
        "Convert this person into a 2D cartoon illustration style — bold clean outlines, "
        "flat vibrant colors, anime-inspired, expressive face. Keep the outfit details "
        "visible and the pose identical."
    ),
    "caricature": (
        "Convert this person into an exaggerated caricature — watercolour editorial "
        "illustration style, slightly enlarged expressive eyes and features, artistic "
        "linework, warm palette. Preserve outfit and pose."
    ),
}


def _load_env() -> None:
    """Load .env from project root if dotenv is available."""
    try:
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent.parent
        load_dotenv(root / ".env", override=True)
    except ImportError:
        pass


def _get_token() -> str | None:
    """Return the Replicate API token from environment."""
    _load_env()
    return os.environ.get("REPLICATE_API_TOKEN") or None


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=False,
)
def generate_caricature(
    image_base64: str,
    style: str = "pixar",
    output_dir: str = "./outputs",
) -> str | None:
    """Generate a stylised portrait via flux-kontext-pro and save it locally.

    Args:
        image_base64: Base64-encoded source photo (JPEG).
        style: One of "pixar", "cartoon", "caricature".
        output_dir: Directory to save the output image.

    Returns:
        Local file path of the saved image, or None if generation failed.
    """
    import replicate

    token = _get_token()
    if not token:
        logger.error("REPLICATE_API_TOKEN not set — skipping caricature generation")
        return None

    style = style.lower().strip()
    if style not in _STYLE_PROMPTS:
        logger.warning("Unknown style '%s' — defaulting to 'pixar'", style)
        style = "pixar"

    prompt = _STYLE_PROMPTS[style]

    try:
        image_bytes = base64.b64decode(image_base64)
        image_file = io.BytesIO(image_bytes)
        image_file.name = "input.jpg"

        output = replicate.run(
            _FLUX_MODEL,
            input={
                "prompt": prompt,
                "input_image": image_file,
                "output_format": "jpg",
            },
        )

        if not output:
            logger.warning("Replicate returned empty output for style '%s'", style)
            return None

        # flux-kontext-pro returns a FileOutput object — str() gives the URL
        image_url = str(output[0]) if isinstance(output, list) else str(output)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())
        out_path = Path(output_dir) / f"caricature_{timestamp}_{style}.jpg"

        urllib.request.urlretrieve(image_url, str(out_path))
        logger.info("Caricature saved: %s", out_path)
        return str(out_path)

    except Exception as exc:
        logger.error("Caricature generation failed: %s", exc)
        return None


def generate_caricature_safe(
    image_base64: str,
    style: str = "pixar",
    output_dir: str = "./outputs",
    original_image_path: str = "",
) -> str:
    """Generate caricature with guaranteed non-None return.

    Falls back to the original image path if generation fails entirely.

    Args:
        image_base64: Base64-encoded source photo.
        style: One of "pixar", "cartoon", "caricature".
        output_dir: Output directory.
        original_image_path: Path to original photo (used as fallback).

    Returns:
        Path to the caricature (or original photo on failure).
    """
    result = generate_caricature(image_base64, style, output_dir)
    if result:
        return result
    logger.warning("Falling back to original image path: %s", original_image_path)
    return original_image_path
