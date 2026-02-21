"""Profile store — persist and retrieve UserProfile and ProductCatalogue.

Files stored at:
  ~/.style-agent/profile.json           — user profile
  ~/.style-agent/product_catalogue.json — per-user curated product catalogue

The directory is created on first save. Objects are saved with
model_dump_json() and loaded with model_validate_json() for full
Pydantic v2 validation on read.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from src.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

_PROFILE_DIR = Path.home() / ".style-agent"
_PROFILE_PATH = _PROFILE_DIR / "profile.json"
_CATALOGUE_PATH = _PROFILE_DIR / "product_catalogue.json"


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


# ---------------------------------------------------------------------------
# Product catalogue persistence
# ---------------------------------------------------------------------------


def save_catalogue(catalogue: "ProductCatalogue") -> Path:  # type: ignore[name-defined]
    """Save a ProductCatalogue to ~/.style-agent/product_catalogue.json.

    Args:
        catalogue: The ProductCatalogue to persist.

    Returns:
        Path to the saved catalogue file.
    """
    from src.models.product import ProductCatalogue  # local import avoids circular dep

    _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(catalogue.model_dump_json())
    _CATALOGUE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Product catalogue saved: %s (%d entries)", _CATALOGUE_PATH, len(catalogue.entries))
    return _CATALOGUE_PATH


def load_catalogue() -> Optional["ProductCatalogue"]:  # type: ignore[name-defined]
    """Load the ProductCatalogue from disk. Returns None if not found.

    Returns:
        ProductCatalogue or None if no catalogue has been generated yet.
    """
    from src.models.product import ProductCatalogue  # local import

    if not _CATALOGUE_PATH.exists():
        logger.debug("No product catalogue found at %s", _CATALOGUE_PATH)
        return None
    try:
        raw = _CATALOGUE_PATH.read_text(encoding="utf-8")
        return ProductCatalogue.model_validate_json(raw)
    except Exception as exc:
        logger.warning("Product catalogue file is corrupted (%s) — returning None", exc)
        return None


def catalogue_exists() -> bool:
    """Return True if a product catalogue file exists on disk."""
    return _CATALOGUE_PATH.exists()


def catalogue_path() -> Path:
    """Return the canonical catalogue file path."""
    return _CATALOGUE_PATH
