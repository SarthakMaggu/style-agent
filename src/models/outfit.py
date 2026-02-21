"""Outfit breakdown data models."""

from pydantic import BaseModel, ConfigDict

from src.models.accessories import AccessoryAnalysis
from src.models.footwear import FootwearAnalysis


class GarmentItem(BaseModel):
    """A single garment detected in the outfit photo."""

    model_config = ConfigDict(strict=True, extra="forbid")

    category: str                  # top / bottom / outerwear / layer / inner /
                                   # ethnic-top / ethnic-bottom / full-garment
    garment_type: str
    color: str
    pattern: str                   # solid / stripes / checks / floral / geometric /
                                   # embroidered / printed / textured
    fabric_estimate: str
    fit: str
    length: str
    collar_type: str               # "n/a" if not applicable
    sleeve_type: str               # "n/a" if not applicable
    condition: str
    occasion_appropriate: bool
    issue: str
    fix: str


class OutfitBreakdown(BaseModel):
    """Complete outfit analysis including garments, accessories, and footwear."""

    model_config = ConfigDict(strict=True, extra="forbid")

    occasion_detected: str
    occasion_requested: str
    occasion_match: bool
    items: list[GarmentItem]
    accessory_analysis: AccessoryAnalysis
    footwear_analysis: FootwearAnalysis
    overall_color_harmony: str
    color_clash_detected: bool
    silhouette_assessment: str
    proportion_assessment: str
    formality_level: int           # 1–10
    outfit_score: int              # 1–10
