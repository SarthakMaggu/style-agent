"""Accessory data models."""

from enum import Enum
from pydantic import BaseModel, ConfigDict


class AccessoryType(str, Enum):
    """Types of accessories that can be detected."""

    WATCH = "watch"
    RING = "ring"
    BRACELET = "bracelet"
    NECKLACE = "necklace"
    CHAIN = "chain"
    PENDANT = "pendant"
    BELT = "belt"
    BAG = "bag"
    SUNGLASSES = "sunglasses"
    HAT = "hat"
    CAP = "cap"
    TURBAN = "turban"
    PAGDI = "pagdi"
    POCKET_SQUARE = "pocket_square"
    TIE = "tie"
    TIE_PIN = "tie_pin"
    CUFFLINKS = "cufflinks"
    EARRING = "earring"


class AccessoryItem(BaseModel):
    """A single detected accessory with assessment."""

    model_config = ConfigDict(strict=True, extra="forbid")

    type: AccessoryType
    color: str
    material_estimate: str
    style_category: str            # casual / formal / traditional / statement / sport
    condition: str
    occasion_appropriate: bool
    issue: str
    fix: str


class AccessoryAnalysis(BaseModel):
    """Complete accessory analysis for an outfit."""

    model_config = ConfigDict(strict=True, extra="forbid")

    items_detected: list[AccessoryItem]
    missing_accessories: list[str]
    accessories_to_remove: list[str]
    accessory_harmony: str
    overall_score: int             # 1–10
