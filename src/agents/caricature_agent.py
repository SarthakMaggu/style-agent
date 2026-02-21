"""Caricature agent — orchestrates stylised portrait generation via Replicate.

Wraps replicate_service with caricature-specific logic:
- Validates style parameter
- Manages output directory creation
- Provides safe fallback to original image on failure
- Logs all outcomes for debugging
"""

import logging
from pathlib import Path

from src.services.replicate_service import generate_caricature_safe

logger = logging.getLogger(__name__)

VALID_STYLES = {"caricature", "cartoon", "pixar"}
DEFAULT_OUTPUT_DIR = "./outputs"


def generate(
    image_base64: str,
    style: str = "caricature",
    output_dir: str = DEFAULT_OUTPUT_DIR,
    original_image_path: str = "",
) -> str:
    """Generate a stylised portrait and return the local path.

    Falls back to original_image_path if generation fails entirely.

    Args:
        image_base64: Base64-encoded source photo.
        style: One of "caricature", "cartoon", "pixar".
        output_dir: Directory to save the generated image.
        original_image_path: Path to original photo (fallback if generation fails).

    Returns:
        Local file path of the caricature (or original photo if fallback used).
    """
    style = style.lower().strip()
    if style not in VALID_STYLES:
        logger.warning(
            "Unknown style '%s' — defaulting to 'caricature'. Valid: %s",
            style,
            VALID_STYLES,
        )
        style = "caricature"

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        result = generate_caricature_safe(
            image_base64=image_base64,
            style=style,
            output_dir=output_dir,
            original_image_path=original_image_path,
        )
    except Exception as exc:
        logger.error("Unexpected error in caricature generation: %s", exc)
        result = original_image_path or ""

    if result == original_image_path and original_image_path:
        logger.warning(
            "Caricature generation failed — using original photo as fallback: %s",
            original_image_path,
        )
    elif result:
        logger.info("Caricature generated: %s", result)
    else:
        logger.error("Caricature generation failed and no fallback available.")

    return result or original_image_path
