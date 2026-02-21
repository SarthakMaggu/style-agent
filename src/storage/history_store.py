"""History store — append-only log of style analysis sessions.

History is stored as a JSON Lines file at:
  ~/.style-agent/history.jsonl

Each line is a full JSON object representing one analysis session.
This makes the log easy to append to, parse, and query.

History entry schema:
  {
    "timestamp": "2024-02-18T14:30:00+00:00",
    "occasion": "wedding_guest_indian",
    "overall_style_score": 7,
    "outfit_score": 6,
    "grooming_score": 7,
    "accessory_score": 5,
    "footwear_score": 4,
    "json_path": "./outputs/analysis_1708260600.json",
    "caricature_path": "./outputs/caricature_1708260600_caricature.png",
    "annotated_path": "./outputs/analysis_1708260600_annotated.png",
    "remark_count": 7,
    "critical_count": 2,
    "wardrobe_gaps": ["silk kurta", "mojaris"],
    "shopping_priorities": ["silk kurta", "mojaris"]
  }
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.models.recommendation import StyleRecommendation

logger = logging.getLogger(__name__)

_HISTORY_DIR = Path.home() / ".style-agent"
_HISTORY_PATH = _HISTORY_DIR / "history.jsonl"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def append_history(recommendation: StyleRecommendation, json_path: str = "") -> Path:
    """Append a completed analysis to the history log.

    Args:
        recommendation: The completed StyleRecommendation.
        json_path: Path to the saved JSON analysis file.

    Returns:
        Path to the history file.
    """
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    all_remarks = (
        recommendation.outfit_remarks
        + recommendation.footwear_remarks
        + recommendation.accessory_remarks
        + recommendation.grooming_remarks
    )

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "occasion": recommendation.outfit_breakdown.occasion_requested,
        "overall_style_score": recommendation.overall_style_score,
        "outfit_score": recommendation.outfit_score,
        "grooming_score": recommendation.grooming_score,
        "accessory_score": recommendation.accessory_score,
        "footwear_score": recommendation.footwear_score,
        "json_path": json_path,
        "caricature_path": recommendation.caricature_image_path,
        "annotated_path": recommendation.annotated_output_path,
        "remark_count": len(all_remarks),
        "critical_count": sum(1 for r in all_remarks if r.severity == "critical"),
        "wardrobe_gaps": recommendation.wardrobe_gaps,
        "shopping_priorities": recommendation.shopping_priorities,
    }

    with open(_HISTORY_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    logger.info("History updated: %s", _HISTORY_PATH)
    return _HISTORY_PATH


def load_history(last_n: int = 0) -> list[dict]:
    """Load analysis history entries.

    Args:
        last_n: If > 0, return only the last N entries. If 0, return all.

    Returns:
        List of history entry dicts, oldest first.
    """
    if not _HISTORY_PATH.exists():
        return []

    entries = []
    with open(_HISTORY_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    logger.warning("Skipping malformed history line: %s", exc)

    if last_n > 0:
        return entries[-last_n:]
    return entries


def history_count() -> int:
    """Return the total number of analysis sessions in history."""
    return len(load_history())


def clear_history() -> None:
    """Delete the history file. Used in tests.

    Does not raise if the file is absent.
    """
    if _HISTORY_PATH.exists():
        _HISTORY_PATH.unlink()
        logger.info("History cleared: %s", _HISTORY_PATH)


def history_path() -> Path:
    """Return the canonical history file path."""
    return _HISTORY_PATH
