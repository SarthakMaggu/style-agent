"""Profile store — persist and retrieve UserProfile.

Profiles are stored as JSON at:
  ~/.style-agent/profile.json

The directory is created on first save. Profiles are saved with
model_dump_json() and loaded with model_validate_json() for full
Pydantic v2 validation on read.
"""

import json
import logging
from pathlib import Path

from src.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

_PROFILE_DIR = Path.home() / ".style-agent"
_PROFILE_PATH = _PROFILE_DIR / "profile.json"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ProfileNotFoundError(FileNotFoundError):
    """Raised when no profile exists on disk."""


class ProfileAlreadyExistsError(FileExistsError):
    """Raised when a profile exists and overwrite=False."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def save_profile(profile: UserProfile, overwrite: bool = False) -> Path:
    """Save a UserProfile to ~/.style-agent/profile.json.

    Args:
        profile: The UserProfile to persist.
        overwrite: If False and a profile already exists, raise
                   ProfileAlreadyExistsError.

    Returns:
        Path to the saved profile file.

    Raises:
        ProfileAlreadyExistsError: If a profile exists and overwrite is False.
    """
    _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    if _PROFILE_PATH.exists() and not overwrite:
        raise ProfileAlreadyExistsError(
            f"Profile already exists at {_PROFILE_PATH}. "
            "Use --refresh-profile to overwrite."
        )
    # exclude_none keeps the JSON clean — v2 Optional fields omitted when not set
    data = json.loads(profile.model_dump_json(exclude_none=True))
    _PROFILE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Profile saved: %s", _PROFILE_PATH)
    return _PROFILE_PATH


def load_profile() -> UserProfile:
    """Load the UserProfile from ~/.style-agent/profile.json.

    Returns:
        The deserialized UserProfile.

    Raises:
        ProfileNotFoundError: If no profile file exists.
        ValueError: If the profile file is invalid or corrupted.
    """
    if not _PROFILE_PATH.exists():
        raise ProfileNotFoundError(
            f"No profile found at {_PROFILE_PATH}. "
            "Run `python src/main.py onboard` to create one."
        )
    try:
        raw = _PROFILE_PATH.read_text(encoding="utf-8")
        return UserProfile.model_validate_json(raw)
    except Exception as exc:
        raise ValueError(f"Profile file is corrupted: {exc}") from exc


def profile_exists() -> bool:
    """Return True if a profile file exists on disk."""
    return _PROFILE_PATH.exists()


def delete_profile() -> None:
    """Delete the profile file if it exists.

    Used in tests and for account reset. Does not raise if file is absent.
    """
    if _PROFILE_PATH.exists():
        _PROFILE_PATH.unlink()
        logger.info("Profile deleted: %s", _PROFILE_PATH)


def profile_path() -> Path:
    """Return the canonical profile file path."""
    return _PROFILE_PATH
