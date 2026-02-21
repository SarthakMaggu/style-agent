"""Profile builder — constructs a UserProfile from onboarding photos.

Handles:
- Per-photo vision analysis (different prompt per photo type)
- Auto-categorisation for folder-mode ingestion (30 photos from a folder)
- Attribute extraction from each photo
- Majority-vote conflict resolution across photos
- Confidence score tracking
- Profile JSON persistence
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from src.fashion_knowledge.seasonal_color import derive_seasonal_type
from src.models.user_profile import (
    BodyShape,
    FaceShape,
    SkinUndertone,
    UserProfile,
)
from src.prompts.profile_analysis import (
    PHOTO_CATEGORISATION_PROMPT,
    PHOTO_1_FACE_FRONT,
    PHOTO_2_FACE_SIDE,
    PHOTO_3_BODY_FRONT,
    PHOTO_4_BODY_SIDE,
    PHOTO_5_REAL_OUTFIT,
    get_photo_prompt,
)
from src.services.anthropic_service import call_vision, parse_json_response
from src.services.image_service import validate_and_prepare

logger = logging.getLogger(__name__)

DEFAULT_PROFILE_PATH = Path.home() / ".style-agent" / "profile.json"
MIN_PHOTOS = 3


class InsufficientPhotosError(ValueError):
    """Raised when fewer than MIN_PHOTOS are provided."""


def analyse_photo(
    photo_number: int,
    image_base64: str,
    media_type: str = "image/jpeg",
) -> dict[str, Any]:
    """Run vision analysis on a single onboarding photo.

    Args:
        photo_number: 1–5 indicating which onboarding photo this is.
        image_base64: Base64-encoded image.
        media_type: MIME type.

    Returns:
        Parsed dict of attributes extracted from this photo.
    """
    prompt = get_photo_prompt(photo_number)
    raw = call_vision(image_base64, media_type, prompt)
    return parse_json_response(raw)


def _majority_vote(values: list[str]) -> tuple[str, float]:
    """Return the most common value and its confidence (frequency / total).

    Args:
        values: List of string values from multiple photos.

    Returns:
        Tuple of (winning_value, confidence_score).
    """
    if not values:
        return ("unknown", 0.0)
    counts = Counter(values)
    winner, freq = counts.most_common(1)[0]
    confidence = round(freq / len(values), 2)
    return (winner, confidence)


def build_profile(
    photo_analyses: list[dict[str, Any]],
    photos_used: int | None = None,
) -> UserProfile:
    """Merge attributes from multiple photo analyses into a UserProfile.

    Uses majority vote for conflicting readings and tracks confidence scores.

    Args:
        photo_analyses: List of parsed dicts from analyse_photo (one per photo).
        photos_used: Actual number of photos submitted (may differ from len if sparse).

    Returns:
        Validated UserProfile.

    Raises:
        InsufficientPhotosError: If fewer than MIN_PHOTOS analyses are provided.
    """
    if len(photo_analyses) < MIN_PHOTOS:
        raise InsufficientPhotosError(
            f"Minimum {MIN_PHOTOS} photos required — got {len(photo_analyses)}. "
            "Please provide at least 3 photos to proceed."
        )

    confidence: dict[str, float] = {}

    def _vote(key: str, valid_type: type | None = None) -> tuple[str, float]:
        """Collect all non-null values for key and majority-vote."""
        vals = [
            str(a[key]) for a in photo_analyses
            if key in a and a[key] not in (None, "", "unknown")
        ]
        val, conf = _majority_vote(vals)
        confidence[key] = conf
        return val, conf

    # Skin
    skin_undertone_str, _ = _vote("skin_undertone")
    try:
        skin_undertone = SkinUndertone(skin_undertone_str)
    except ValueError:
        skin_undertone = SkinUndertone.NEUTRAL
        confidence["skin_undertone"] = 0.4

    skin_tone_depth, _ = _vote("skin_tone_depth")
    skin_texture, _ = _vote("skin_texture_visible")

    # Body
    body_shape_str, _ = _vote("body_shape")
    try:
        body_shape = BodyShape(body_shape_str)
    except ValueError:
        body_shape = BodyShape.RECTANGLE
        confidence["body_shape"] = 0.4

    height, _ = _vote("height_estimate")
    build, _ = _vote("build")
    shoulder_width, _ = _vote("shoulder_width")
    torso_length, _ = _vote("torso_length")
    leg_proportion, _ = _vote("leg_proportion")

    # Face
    face_shape_str, _ = _vote("face_shape")
    try:
        face_shape = FaceShape(face_shape_str)
    except ValueError:
        face_shape = FaceShape.OVAL
        confidence["face_shape"] = 0.4

    jaw_type, _ = _vote("jaw_type")
    forehead, _ = _vote("forehead")

    # Hair (from photo 5 primarily, falls back to other photos)
    hair_data = _collect_hair_data(photo_analyses)
    hair_color = hair_data.get("hair_color", "black")
    hair_texture = hair_data.get("hair_texture", "straight")
    hair_density = hair_data.get("hair_density", "medium")
    haircut_style = hair_data.get("current_haircut_style", "standard")
    haircut_length = hair_data.get("haircut_length", "short")
    hair_condition = hair_data.get("hair_visible_condition", "healthy")

    # Beard
    beard_style, _ = _vote("beard_style")
    beard_density, _ = _vote("beard_density")
    beard_color, _ = _vote("beard_color")
    mustache_style, _ = _vote("mustache_style")
    beard_grooming, _ = _vote("beard_grooming_quality")

    # Defaults for unknown/empty values
    def _default(val: str, fallback: str) -> str:
        return val if val and val != "unknown" else fallback

    return UserProfile(
        skin_undertone=skin_undertone,
        skin_tone_depth=_default(skin_tone_depth, "medium"),
        skin_texture_visible=_default(skin_texture, "smooth"),
        body_shape=body_shape,
        height_estimate=_default(height, "average"),
        build=_default(build, "average"),
        shoulder_width=_default(shoulder_width, "average"),
        torso_length=_default(torso_length, "average"),
        leg_proportion=_default(leg_proportion, "average"),
        face_shape=face_shape,
        jaw_type=_default(jaw_type, "soft"),
        forehead=_default(forehead, "average"),
        hair_color=_default(hair_color, "black"),
        hair_texture=_default(hair_texture, "straight"),
        hair_density=_default(hair_density, "medium"),
        current_haircut_style=_default(haircut_style, "standard"),
        haircut_length=_default(haircut_length, "short"),
        hair_visible_condition=_default(hair_condition, "healthy"),
        beard_style=_default(beard_style, "stubble"),
        beard_density=_default(beard_density, "medium"),
        beard_color=_default(beard_color, "black"),
        mustache_style=_default(mustache_style, "none"),
        beard_grooming_quality=_default(beard_grooming, "average"),
        confidence_scores=confidence,
        photos_used=photos_used if photos_used is not None else len(photo_analyses),
        profile_created_at=datetime.now(timezone.utc).isoformat(),
        profile_version=1,
    )


def _collect_hair_data(photo_analyses: list[dict[str, Any]]) -> dict[str, str]:
    """Extract hair data preferring photo 5 (real outfit), then other photos."""
    # Photo 5 stores hair data nested under "hair_visible"
    for analysis in reversed(photo_analyses):
        hair = analysis.get("hair_visible", {})
        if hair and any(hair.values()):
            return {k: str(v) for k, v in hair.items() if v}
    # Fall back to flat keys
    for analysis in reversed(photo_analyses):
        if "hair_color" in analysis:
            return {
                k: str(analysis.get(k, ""))
                for k in [
                    "hair_color", "hair_texture", "hair_density",
                    "current_haircut_style", "haircut_length", "hair_visible_condition",
                ]
            }
    return {}


# ---------------------------------------------------------------------------
# Archetype mapping — style_vocabulary → style_archetype
# ---------------------------------------------------------------------------

_ARCHETYPE_MAP: dict[str, str] = {
    "indian_traditional": "ethnic_traditional",
    "western_casual":     "smart_casual",
    "western_formal":     "classic",
    "ethnic_fusion":      "eclectic",
    "streetwear":         "streetwear",
    "smart_casual":       "smart_casual",
    "athletic":           "athletic",
}


# ---------------------------------------------------------------------------
# Photo category enum
# ---------------------------------------------------------------------------


class PhotoCategory(str, Enum):
    """Photo types for folder-mode auto-categorisation."""

    FACE_FRONT = "face_front"
    FACE_SIDE  = "face_side"
    BODY_FRONT = "body_front"
    BODY_SIDE  = "body_side"
    OUTFIT     = "outfit"
    UNCLEAR    = "unclear"


# Map category → photo prompt
_CATEGORY_PROMPT: dict[PhotoCategory, str] = {
    PhotoCategory.FACE_FRONT: PHOTO_1_FACE_FRONT,
    PhotoCategory.FACE_SIDE:  PHOTO_2_FACE_SIDE,
    PhotoCategory.BODY_FRONT: PHOTO_3_BODY_FRONT,
    PhotoCategory.BODY_SIDE:  PHOTO_4_BODY_SIDE,
    PhotoCategory.OUTFIT:     PHOTO_5_REAL_OUTFIT,
}


def categorise_photo(image_base64: str, media_type: str = "image/jpeg") -> PhotoCategory:
    """Ask Claude Vision to classify a photo into one of the 6 PhotoCategory values.

    Args:
        image_base64: Base64-encoded image data.
        media_type: MIME type string.

    Returns:
        PhotoCategory enum value. Falls back to UNCLEAR on any error.
    """
    try:
        raw = call_vision(
            image_base64,
            media_type,
            PHOTO_CATEGORISATION_PROMPT,
        )
        label = raw.strip().lower().split()[0]  # take only the first word
        return PhotoCategory(label)
    except Exception as exc:
        logger.warning("Photo categorisation failed: %s — treating as unclear", exc)
        return PhotoCategory.UNCLEAR


def build_profile_from_folder(
    folder_path: str,
    preferred_name: str = "",
    lifestyle: str = "",
    age_group: str = "",
    budget_tier: str = "",
    refresh: bool = False,
) -> UserProfile:
    """Build a UserProfile by ingesting all images from a folder.

    Supports up to 30+ photos of any type. Auto-categorises each image and
    runs the appropriate analysis prompt. Multiple photos of the same category
    are majority-voted to increase confidence.

    Args:
        folder_path: Path to the folder containing the photos.
        preferred_name: User's preferred name for personalised recommendations.
        lifestyle: Optional lifestyle tag ("corporate" / "creative" / etc.).
        age_group: Optional age group string ("18-25" / "26-35" / etc.).
        budget_tier: Optional budget tier ("high_street" / "designer" / etc.).
        refresh: If True, treats this as a profile refresh (increments version).

    Returns:
        UserProfile with all available fields populated.

    Raises:
        InsufficientPhotosError: If fewer than MIN_PHOTOS usable photos found.
        FileNotFoundError: If the folder does not exist.
    """
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # Supported image extensions
    _IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
    image_paths = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS
    ]

    if not image_paths:
        raise InsufficientPhotosError(
            f"No image files found in {folder_path}. "
            "Supported formats: jpg, jpeg, png, webp, heic."
        )

    logger.info("Found %d image files in folder — categorising...", len(image_paths))

    # --- Categorise all photos ---
    categorised: dict[PhotoCategory, list[dict[str, Any]]] = {
        cat: [] for cat in PhotoCategory if cat != PhotoCategory.UNCLEAR
    }
    unclear_count = 0

    for img_path in sorted(image_paths):
        try:
            prepared = validate_and_prepare(str(img_path))
        except Exception as exc:
            logger.warning("Skipping %s — invalid image: %s", img_path.name, exc)
            unclear_count += 1
            continue

        category = categorise_photo(prepared["base64_data"], prepared["media_type"])
        logger.info("  %s → %s", img_path.name, category.value)

        if category == PhotoCategory.UNCLEAR:
            unclear_count += 1
            continue

        # Run the appropriate analysis prompt
        prompt = _CATEGORY_PROMPT.get(category)
        if prompt is None:
            unclear_count += 1
            continue

        try:
            raw = call_vision(prepared["base64_data"], prepared["media_type"], prompt)
            analysis = parse_json_response(raw)
            analysis["_source_category"] = category.value
            categorised[category].append(analysis)
        except Exception as exc:
            logger.warning("Analysis failed for %s: %s", img_path.name, exc)

    total_usable = sum(len(v) for v in categorised.values())
    logger.info(
        "Categorisation complete: %d usable, %d unclear/skipped",
        total_usable, unclear_count,
    )

    if total_usable < MIN_PHOTOS:
        raise InsufficientPhotosError(
            f"Only {total_usable} usable photos found (minimum {MIN_PHOTOS}). "
            "Please add more clear photos of your face and body."
        )

    # --- Build flat analysis list from all categorised results ---
    all_analyses: list[dict[str, Any]] = []
    for cat_list in categorised.values():
        all_analyses.extend(cat_list)

    # --- Build base profile from merged analyses ---
    profile = build_profile(all_analyses, photos_used=total_usable)

    # --- Enrich with folder-specific insights ---

    # 1. Style archetype from outfit photos
    outfit_analyses = categorised[PhotoCategory.OUTFIT]
    style_vocabs = [
        a.get("style_vocabulary", "")
        for a in outfit_analyses
        if a.get("style_vocabulary")
    ]
    style_archetype = None
    style_comfort_zones: list[str] = []
    fit_preference_default = None

    if style_vocabs:
        # style_comfort_zones = all unique styles seen
        style_comfort_zones = list(dict.fromkeys(style_vocabs))  # unique, ordered
        # style_archetype = most frequent vocabulary → archetype mapping
        most_common_vocab, _ = _majority_vote(style_vocabs)
        style_archetype = _ARCHETYPE_MAP.get(most_common_vocab.lower(), most_common_vocab)

        # fit_preference from outfit analyses
        fit_prefs = [a.get("fit_preference", "") for a in outfit_analyses if a.get("fit_preference")]
        if fit_prefs:
            fit_preference_default, _ = _majority_vote(fit_prefs)

    # 2. Posture and belly_profile from body-side photos
    body_side_analyses = categorised[PhotoCategory.BODY_SIDE]
    posture = None
    belly_profile = None
    if body_side_analyses:
        postures = [a.get("posture", "") for a in body_side_analyses if a.get("posture")]
        bellies = [a.get("belly_profile", "") for a in body_side_analyses if a.get("belly_profile")]
        if postures:
            posture, _ = _majority_vote(postures)
        if bellies:
            belly_profile, _ = _majority_vote(bellies)

    # 3. Seasonal color type from base profile attributes
    seasonal_type = derive_seasonal_type(
        undertone=profile.skin_undertone,
        skin_tone_depth=profile.skin_tone_depth,
        hair_color=profile.hair_color,
    )

    # --- Assemble extended profile ---
    profile = profile.model_copy(update={
        k: v for k, v in {
            "style_archetype":       style_archetype,
            "seasonal_color_type":   seasonal_type,
            "fit_preference_default": fit_preference_default,
            "style_comfort_zones":   style_comfort_zones or None,
            "preferred_name":        preferred_name or None,
            "lifestyle":             lifestyle or None,
            "age_group":             age_group or None,
            "budget_tier":           budget_tier or None,
            "posture":               posture or None,
            "belly_profile":         belly_profile or None,
        }.items() if v is not None
    })

    logger.info(
        "Profile built from folder: %d photos, archetype=%s, seasonal=%s",
        total_usable,
        profile.style_archetype,
        profile.seasonal_color_type,
    )
    return profile


def save_profile(profile: UserProfile, path: Path = DEFAULT_PROFILE_PATH) -> None:
    """Save a UserProfile to JSON at the given path.

    Args:
        profile: The UserProfile to save.
        path: Destination path (creates parent directories if needed).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(profile.model_dump_json(indent=2))
    logger.info("Profile saved to %s", path)


def load_profile(path: Path = DEFAULT_PROFILE_PATH) -> UserProfile:
    """Load a UserProfile from JSON.

    Args:
        path: Path to the profile JSON file.

    Returns:
        UserProfile loaded from the file.

    Raises:
        FileNotFoundError: If the profile file does not exist.
        ValueError: If the JSON cannot be parsed into UserProfile.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"No profile found at {path}. "
            "Run 'python src/main.py onboard' to create your profile."
        )
    with open(path) as f:
        return UserProfile.model_validate_json(f.read())


def refresh_profile(
    photo_analyses: list[dict[str, Any]],
    path: Path = DEFAULT_PROFILE_PATH,
    existing_version: int = 1,
) -> UserProfile:
    """Build a new profile from fresh photos and increment version.

    Args:
        photo_analyses: Fresh photo analyses.
        path: Profile file path.
        existing_version: Current version to increment.

    Returns:
        Updated UserProfile with incremented version.
    """
    profile = build_profile(photo_analyses)
    # Increment version
    updated = profile.model_copy(
        update={"profile_version": existing_version + 1}
    )
    save_profile(updated, path)
    return updated
