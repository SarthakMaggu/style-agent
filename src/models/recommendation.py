"""Style recommendation data model."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict

from src.models.remark import Remark, RemarkCategory  # noqa: F401 — re-exported
from src.models.user_profile import UserProfile
from src.models.grooming import GroomingProfile
from src.models.outfit import OutfitBreakdown


class StyleRecommendation(BaseModel):
    """Complete style recommendation output for one analysis session."""

    model_config = ConfigDict(strict=True, extra="forbid")

    user_profile: UserProfile
    grooming_profile: GroomingProfile
    outfit_breakdown: OutfitBreakdown

    outfit_remarks: list[Remark]
    grooming_remarks: list[Remark]
    accessory_remarks: list[Remark]
    footwear_remarks: list[Remark]

    color_palette_do: list[str]
    color_palette_dont: list[str]
    color_palette_occasion_specific: list[str]

    recommended_outfit_instead: str
    recommended_grooming_change: str
    recommended_accessories: str

    wardrobe_gaps: list[str]
    shopping_priorities: list[str]

    overall_style_score: int       # 1–10
    outfit_score: int
    grooming_score: int
    accessory_score: int
    footwear_score: int

    caricature_image_path: str
    annotated_output_path: str
    analysis_json_path: str

    # ── v2 stylist voice fields (Optional for backward compat) ───────────────
    whats_working: Optional[str] = None
    """One to two sentences acknowledging what is genuinely good in this look."""

    priority_fix_two: Optional[str] = None
    """The 2 most critical fixes, each stated in one direct sentence."""
