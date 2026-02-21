"""Anthropic API service with retry logic, timeouts, and error handling.

Wraps the Anthropic client for both vision and text-only calls with:
- Exponential backoff retries (3 attempts: 2s / 4s / 8s)
- 30s timeout for vision calls
- Structured JSON response parsing
- User-friendly error messages (no raw stack traces)
"""

import json
import logging
import os
import time
from typing import Any

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# Model identifiers
VISION_MODEL = "claude-opus-4-6"
RECOMMENDATION_MODEL = "claude-opus-4-6"

VISION_TIMEOUT_SECONDS = 60
RECOMMENDATION_TIMEOUT_SECONDS = 120
MAX_TOKENS_VISION = 4096
MAX_TOKENS_RECOMMENDATION = 8192


def _load_env() -> None:
    """Load .env from project root if dotenv is available."""
    try:
        from pathlib import Path
        from dotenv import load_dotenv
        root = Path(__file__).resolve().parent.parent.parent
        load_dotenv(root / ".env", override=True)
    except ImportError:
        pass


def _get_client() -> anthropic.Anthropic:
    """Instantiate Anthropic client from environment variable.

    Raises:
        EnvironmentError: If ANTHROPIC_API_KEY is not set.
    """
    _load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file and run scripts/validate_env.py."
        )
    return anthropic.Anthropic(api_key=api_key)


@retry(
    retry=retry_if_exception_type((
        anthropic.APIConnectionError,
        anthropic.RateLimitError,
        anthropic.APITimeoutError,
    )),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def call_vision(
    image_base64: str,
    media_type: str,
    prompt: str,
) -> str:
    """Send an image + prompt to Claude Vision and return the raw text response.

    Args:
        image_base64: Base64-encoded image string.
        media_type: MIME type string (e.g. "image/jpeg").
        prompt: Instruction prompt.

    Returns:
        Raw text content from Claude's response.

    Raises:
        anthropic.APIError: After 3 retries on transient failures.
        TimeoutError: If response exceeds VISION_TIMEOUT_SECONDS.
        EnvironmentError: If API key is not configured.
    """
    client = _get_client()

    message = client.messages.create(
        model=VISION_MODEL,
        max_tokens=MAX_TOKENS_VISION,
        timeout=VISION_TIMEOUT_SECONDS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return message.content[0].text


@retry(
    retry=retry_if_exception_type((
        anthropic.APIConnectionError,
        anthropic.RateLimitError,
        anthropic.APITimeoutError,
    )),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def call_text(prompt: str, system_prompt: str = "") -> str:
    """Send a text prompt to Claude and return the raw text response.

    Args:
        prompt: User message content.
        system_prompt: Optional system-level instructions.

    Returns:
        Raw text content from Claude's response.

    Raises:
        anthropic.APIError: After 3 retries on transient failures.
        EnvironmentError: If API key is not configured.
    """
    client = _get_client()

    kwargs: dict[str, Any] = {
        "model": RECOMMENDATION_MODEL,
        "max_tokens": MAX_TOKENS_RECOMMENDATION,
        "timeout": RECOMMENDATION_TIMEOUT_SECONDS,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    message = client.messages.create(**kwargs)
    return message.content[0].text


_ZONE_LOCATE_PROMPT = """\
Look at this image carefully. For each body zone listed below, tell me:
1. Is it VISIBLE in the image? (yes/no)
2. If visible, what are the approximate pixel coordinates of the best dot placement point?
   Express as x_pct and y_pct — percentage of image width/height (0–100).

Zones to locate:
- head        (top of hair / hair crown)
- face        (jawline / cheek area)
- neck        (collar / neck area)
- upper-body  (chest / upper garment centre)
- lower-body  (trouser / skirt midpoint)
- feet        (shoes / bare feet / ankle area)
- full-look   (waist / belt level)

Rules:
- If a zone is NOT in the frame at all (e.g. feet cut off, no legs shown), set visible=false
- x_pct: 0=left edge, 100=right edge of the IMAGE (not the figure)
- y_pct: 0=top edge, 100=bottom edge of the IMAGE
- Place the dot ON the body part, not in the background
- For half-body images (head+torso only), feet and lower-body must be visible=false

Return ONLY valid JSON, no other text:
{
  "head":        {"visible": true,  "x_pct": 45, "y_pct": 12},
  "face":        {"visible": true,  "x_pct": 47, "y_pct": 22},
  "neck":        {"visible": true,  "x_pct": 46, "y_pct": 30},
  "upper-body":  {"visible": true,  "x_pct": 48, "y_pct": 45},
  "lower-body":  {"visible": false, "x_pct": 0,  "y_pct": 0},
  "feet":        {"visible": false, "x_pct": 0,  "y_pct": 0},
  "full-look":   {"visible": true,  "x_pct": 48, "y_pct": 55}
}
"""


def locate_zones(image_base64: str, media_type: str) -> dict[str, dict]:
    """Use Claude Vision to locate body zones in image with exact coordinates.

    Returns a dict like:
        {
          "head":       {"visible": True,  "x_pct": 45, "y_pct": 12},
          "face":       {"visible": True,  "x_pct": 47, "y_pct": 22},
          "feet":       {"visible": False, "x_pct": 0,  "y_pct": 0},
          ...
        }

    Falls back to empty dict on any failure — renderer uses pixel heuristics.
    """
    try:
        raw = call_vision(image_base64, media_type, _ZONE_LOCATE_PROMPT)
        data = parse_json_response(raw)
        # Validate + normalise
        result: dict[str, dict] = {}
        for zone in ("head", "face", "neck", "upper-body", "lower-body", "feet", "full-look"):
            entry = data.get(zone, {})
            result[zone] = {
                "visible": bool(entry.get("visible", False)),
                "x_pct":   float(entry.get("x_pct", 50)),
                "y_pct":   float(entry.get("y_pct", 50)),
            }
        logger.debug("Zone locations from Vision: %s", result)
        return result
    except Exception as exc:
        logger.warning("Zone location failed (%s) — renderer will use heuristics", exc)
        return {}


def parse_json_response(text: str) -> dict[str, Any]:
    """Extract and parse the first JSON object from a Claude response.

    Claude sometimes wraps JSON in markdown code fences — this strips them.

    Args:
        text: Raw response text from Claude.

    Returns:
        Parsed Python dictionary.

    Raises:
        ValueError: If no valid JSON object is found in the response.
    """
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Drop first line (```json or ```) and last line (```)
        inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        cleaned = inner.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Try to extract JSON substring
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass
        raise ValueError(
            f"Could not parse JSON from Claude response. "
            f"Response preview: {text[:200]}"
        ) from exc
