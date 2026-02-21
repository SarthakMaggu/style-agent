"""Grooming profile data model."""

from pydantic import BaseModel, ConfigDict

from src.models.remark import Remark


class GroomingProfile(BaseModel):
    """Hair, beard, and skin grooming analysis and recommendations."""

    model_config = ConfigDict(strict=True, extra="forbid")

    # Hair
    current_haircut_assessment: str
    recommended_haircut: str
    haircut_to_avoid: str
    styling_product_recommendation: list[str]
    hair_color_recommendation: str

    # Beard
    current_beard_assessment: str
    recommended_beard_style: str
    beard_grooming_tips: list[str]
    beard_style_to_avoid: str

    # Eyebrows
    eyebrow_assessment: str
    eyebrow_recommendation: str

    # Skin
    visible_skin_concerns: list[str]
    skincare_categories_needed: list[str]

    grooming_score: int            # 1–10
    grooming_remarks: list[Remark]
