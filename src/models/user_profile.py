"""User profile data model."""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SkinUndertone(str, Enum):
    """Skin undertone categories with South Asian specifics."""

    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"
    DEEP_WARM = "deep_warm"      # warm undertone, deep skin — common South Asian
    DEEP_COOL = "deep_cool"
    OLIVE_WARM = "olive_warm"    # wheatish with warm base


class BodyShape(str, Enum):
    """Male body shape classifications."""

    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    INVERTED_TRIANGLE = "inverted_triangle"
    OVAL = "oval"
    TRAPEZOID = "trapezoid"


class FaceShape(str, Enum):
    """Face shape classifications."""

    OVAL = "oval"
    SQUARE = "square"
    ROUND = "round"
    OBLONG = "oblong"
    HEART = "heart"
    DIAMOND = "diamond"


class UserProfile(BaseModel):
    """Permanent user profile built from onboarding photos."""

    model_config = ConfigDict(strict=True, extra="forbid")

    # Skin
    skin_undertone: SkinUndertone
    skin_tone_depth: str           # light / medium / wheatish / tan / deep
    skin_texture_visible: str      # smooth / textured / oily / dry / combination

    # Body
    body_shape: BodyShape
    height_estimate: str           # tall / average / petite
    build: str                     # slim / lean / athletic / average / broad / stocky
    shoulder_width: str            # narrow / average / broad
    torso_length: str              # short / average / long
    leg_proportion: str            # short / average / long

    # Face
    face_shape: FaceShape
    jaw_type: str                  # strong / soft / angular / rounded
    forehead: str                  # broad / average / narrow

    # Hair
    hair_color: str
    hair_texture: str              # straight / wavy / curly / coily
    hair_density: str              # thin / medium / thick
    current_haircut_style: str
    haircut_length: str            # short / medium / long
    hair_visible_condition: str    # healthy / frizzy / oily / dry

    # Beard
    beard_style: str               # clean shaven / stubble / short / full / patchy
    beard_density: str             # none / patchy / medium / dense
    beard_color: str
    mustache_style: str            # none / natural / pencil / handlebar
    beard_grooming_quality: str    # well groomed / average / unkempt / not applicable

    # Meta
    confidence_scores: dict[str, float]
    photos_used: int
    profile_created_at: str
    profile_version: int

    # ── Extended Profile (v2) — all Optional for backward compatibility ──────
    style_archetype: Optional[str] = None
    # "classic" / "streetwear" / "ethnic_traditional" / "smart_casual"
    # "avant_garde" / "athletic" / "eclectic"

    seasonal_color_type: Optional[str] = None
    # "spring" / "summer" / "autumn" / "winter"

    fit_preference_default: Optional[str] = None
    # "slim" / "regular" / "relaxed" / "oversized"

    style_comfort_zones: Optional[list[str]] = None
    # e.g. ["indian_casual", "smart_casual"] — dominant occasions observed

    budget_tier: Optional[str] = None
    # "high_street" / "mid_range" / "designer" / "luxury"

    age_group: Optional[str] = None
    # "18-25" / "26-35" / "36-45" / "45+"

    lifestyle: Optional[str] = None
    # "corporate" / "creative" / "entrepreneur" / "student" / "freelance"

    style_goals: Optional[list[str]] = None
    # e.g. ["elevate work wardrobe", "build ethnic formal wardrobe"]

    preferred_name: Optional[str] = None
    # Personalises stylist address in recommendations

    posture: Optional[str] = None
    # "upright" / "slight forward lean" / "rounded shoulders" / "military straight"
    # Extracted from Photo 4 (body side) but previously discarded

    belly_profile: Optional[str] = None
    # "flat" / "slight" / "moderate" / "prominent"
    # Extracted from Photo 4 but previously discarded
