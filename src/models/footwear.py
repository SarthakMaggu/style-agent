"""Footwear analysis data model."""

from pydantic import BaseModel, ConfigDict


class FootwearAnalysis(BaseModel):
    """Footwear detection and assessment."""

    model_config = ConfigDict(strict=True, extra="forbid")

    visible: bool
    type: str                      # sneakers / oxford / loafers / boots / sandals /
                                   # chappals / mojaris / juttis / kolhapuris / etc.
    color: str
    material_estimate: str
    condition: str                 # clean / scuffed / dirty / worn out / sole peeling
    style_category: str
    occasion_match: bool
    outfit_match: bool
    issue: str
    recommended_instead: str
    shoe_care_note: str
