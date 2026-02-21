"""Fabric guide — formality levels, weight, seasonal suitability, and care notes.

Integrated into indian_wear.py and western_wear.py tests rather than having its own
test file (per Build Order Step 9).
"""

from dataclasses import dataclass, field


@dataclass
class FabricProfile:
    """Full profile of a fabric type."""

    name: str
    formality_level: int          # 1 (casual) to 5 (formal)
    weight: str                   # light / medium / heavy
    seasonal_suitability: list[str]   # summer / winter / all-season / monsoon
    occasions: list[str]
    care_note: str
    texture: str                  # smooth / textured / sheer / structured
    drape: str                    # fluid / stiff / medium


_FABRICS: dict[str, FabricProfile] = {
    # --------------- Indian Fabrics ---------------
    "cotton": FabricProfile(
        name="cotton",
        formality_level=2,
        weight="light",
        seasonal_suitability=["summer", "all-season"],
        occasions=["casual", "indian_casual", "travel", "festival", "lounge"],
        care_note="Machine washable. Iron on medium heat.",
        texture="smooth",
        drape="medium",
    ),
    "linen": FabricProfile(
        name="linen",
        formality_level=2,
        weight="light",
        seasonal_suitability=["summer"],
        occasions=["casual", "indian_casual", "travel", "beach"],
        care_note="Hand wash or gentle machine. Wrinkles easily — embrace or steam.",
        texture="textured",
        drape="medium",
    ),
    "chanderi": FabricProfile(
        name="chanderi",
        formality_level=5,
        weight="light",
        seasonal_suitability=["all-season"],
        occasions=["indian_formal", "wedding_guest_indian", "party"],
        care_note="Dry clean recommended. Handle with care — delicate weave.",
        texture="sheer",
        drape="fluid",
    ),
    "raw silk": FabricProfile(
        name="raw silk",
        formality_level=4,
        weight="medium",
        seasonal_suitability=["all-season"],
        occasions=["indian_formal", "wedding_guest_indian", "party"],
        care_note="Dry clean only. Avoid direct sunlight — fades.",
        texture="textured",
        drape="medium",
    ),
    "silk": FabricProfile(
        name="silk",
        formality_level=5,
        weight="medium",
        seasonal_suitability=["all-season"],
        occasions=["indian_formal", "wedding_guest_indian", "party"],
        care_note="Dry clean only. Store away from light.",
        texture="smooth",
        drape="fluid",
    ),
    "brocade": FabricProfile(
        name="brocade",
        formality_level=5,
        weight="heavy",
        seasonal_suitability=["winter", "all-season"],
        occasions=["indian_formal", "wedding_guest_indian"],
        care_note="Dry clean only. Heavy — layer sparingly.",
        texture="textured",
        drape="stiff",
    ),
    "silk-cotton blend": FabricProfile(
        name="silk-cotton blend",
        formality_level=4,
        weight="medium",
        seasonal_suitability=["all-season"],
        occasions=["indian_formal", "wedding_guest_indian", "business_casual"],
        care_note="Dry clean or gentle hand wash in cold water.",
        texture="smooth",
        drape="medium",
    ),
    "linen-cotton blend": FabricProfile(
        name="linen-cotton blend",
        formality_level=3,
        weight="light",
        seasonal_suitability=["summer", "all-season"],
        occasions=["business_casual", "smart_casual", "indian_casual"],
        care_note="Machine washable. Light iron.",
        texture="textured",
        drape="medium",
    ),
    # --------------- Western Fabrics ---------------
    "wool": FabricProfile(
        name="wool",
        formality_level=5,
        weight="heavy",
        seasonal_suitability=["winter"],
        occasions=["western_formal", "business_casual", "smart_casual"],
        care_note="Dry clean or hand wash cold. Steam to remove wrinkles.",
        texture="textured",
        drape="structured",
    ),
    "wool blend": FabricProfile(
        name="wool blend",
        formality_level=4,
        weight="medium",
        seasonal_suitability=["winter", "all-season"],
        occasions=["western_formal", "business_casual"],
        care_note="Dry clean recommended.",
        texture="smooth",
        drape="structured",
    ),
    "denim": FabricProfile(
        name="denim",
        formality_level=2,
        weight="heavy",
        seasonal_suitability=["all-season"],
        occasions=["casual", "streetwear", "indian_casual"],
        care_note="Wash inside out. Cold wash to prevent fading.",
        texture="textured",
        drape="stiff",
    ),
    "cotton poplin": FabricProfile(
        name="cotton poplin",
        formality_level=3,
        weight="light",
        seasonal_suitability=["all-season"],
        occasions=["western_formal", "business_casual", "smart_casual"],
        care_note="Machine washable. Iron on medium heat — sharp collar important.",
        texture="smooth",
        drape="medium",
    ),
    "oxford cloth": FabricProfile(
        name="oxford cloth",
        formality_level=3,
        weight="medium",
        seasonal_suitability=["all-season"],
        occasions=["business_casual", "smart_casual", "casual"],
        care_note="Machine washable.",
        texture="textured",
        drape="medium",
    ),
    "velvet": FabricProfile(
        name="velvet",
        formality_level=5,
        weight="heavy",
        seasonal_suitability=["winter"],
        occasions=["party", "indian_formal", "wedding_guest_indian"],
        care_note="Dry clean only. Store on hanger — folding crushes pile.",
        texture="smooth",
        drape="structured",
    ),
    "jersey": FabricProfile(
        name="jersey",
        formality_level=1,
        weight="light",
        seasonal_suitability=["all-season"],
        occasions=["casual", "gym", "streetwear", "lounge"],
        care_note="Machine washable.",
        texture="smooth",
        drape="fluid",
    ),
}


def get_fabric(name: str) -> FabricProfile | None:
    """Return a FabricProfile by name.

    Args:
        name: Fabric name (case-insensitive).

    Returns:
        FabricProfile or None if not found.
    """
    return _FABRICS.get(name.lower().strip())


def fabric_formality(name: str) -> int:
    """Return the formality level of a fabric (1–5). Returns 3 for unknown fabrics.

    Args:
        name: Fabric name.

    Returns:
        Integer formality level.
    """
    profile = get_fabric(name)
    return profile.formality_level if profile else 3


def fabric_weight(name: str) -> str:
    """Return the fabric weight (light / medium / heavy).

    Args:
        name: Fabric name.

    Returns:
        Weight string, or "medium" for unknowns.
    """
    profile = get_fabric(name)
    return profile.weight if profile else "medium"


def fabrics_for_occasion(occasion: str) -> list[str]:
    """Return all fabrics appropriate for an occasion.

    Args:
        occasion: Occasion string.

    Returns:
        List of fabric names.
    """
    occ = occasion.lower().strip().replace(" ", "_")
    return [
        name for name, profile in _FABRICS.items()
        if occ in profile.occasions
    ]
