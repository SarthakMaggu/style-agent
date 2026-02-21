"""Remark data model — shared across grooming, outfit, and recommendation models."""

from enum import Enum
from pydantic import BaseModel, ConfigDict


class RemarkCategory(str, Enum):
    """Categories for style remarks."""

    COLOR = "color"
    FIT = "fit"
    FABRIC = "fabric"
    OCCASION = "occasion"
    PROPORTION = "proportion"
    ACCESSORY = "accessory"
    FOOTWEAR = "footwear"
    GROOMING_HAIR = "grooming_hair"
    GROOMING_BEARD = "grooming_beard"
    GROOMING_SKIN = "grooming_skin"
    LAYERING = "layering"
    PATTERN = "pattern"
    LENGTH = "length"
    CONDITION = "condition"
    POSTURE = "posture"


class Remark(BaseModel):
    """A single actionable style remark."""

    model_config = ConfigDict(strict=True, extra="forbid")

    severity: str                  # critical / moderate / minor
    category: RemarkCategory
    body_zone: str                 # head / face / neck / upper-body / lower-body / feet / full-look
    element: str
    issue: str
    fix: str
    why: str
    priority_order: int
