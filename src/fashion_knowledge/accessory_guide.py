"""Accessory rules covering watches, rings, belts, bags, sunglasses, and turbans.

Used by recommendation_agent to flag accessory issues and suggest improvements.
"""

from dataclasses import dataclass, field

from src.models.user_profile import FaceShape


# ---------------------------------------------------------------------------
# Watch rules
# ---------------------------------------------------------------------------

# Occasion formality levels (1=most casual, 5=most formal)
_FORMALITY_LEVELS: dict[str, int] = {
    "gym": 1,
    "beach": 1,
    "casual": 2,
    "streetwear": 2,
    "travel": 2,
    "smart casual": 3,
    "party": 3,
    "business casual": 4,
    "western formal": 5,
    "indian formal": 5,
    "wedding guest indian": 5,
    "indian casual": 2,
    "ethnic fusion": 3,
    "festival": 2,
    "lounge": 2,
}

FORMAL_OCCASIONS = {k for k, v in _FORMALITY_LEVELS.items() if v >= 4}
CASUAL_OCCASIONS = {k for k, v in _FORMALITY_LEVELS.items() if v <= 2}


def watch_strap_appropriate(strap_material: str, occasion: str) -> tuple[bool, str]:
    """Return whether a watch strap is appropriate for an occasion.

    Args:
        strap_material: Detected strap material (e.g. "rubber", "leather", "NATO").
        occasion: Occasion string (lowercase).

    Returns:
        Tuple of (is_appropriate, issue_description). If appropriate, issue is empty.
    """
    occ = occasion.lower().strip().replace("_", " ")
    strap = strap_material.lower().strip()
    is_formal = occ in FORMAL_OCCASIONS or _FORMALITY_LEVELS.get(occ, 3) >= 4

    rubber_straps = {"rubber", "silicone", "sport strap", "rubber strap"}
    formal_straps = {"leather", "leather strap", "tan leather", "metal bracelet", "metal strap", "mesh"}
    plastic_watch = {"plastic", "plastic case", "casio plastic"}

    if is_formal:
        if any(p in strap for p in plastic_watch):
            return False, "Plastic or Casio-style watch is never appropriate for formal occasions"
        if any(r in strap for r in rubber_straps):
            return False, (
                f"Rubber/sport strap signals casual energy — swap to leather strap "
                f"(tan, black, or dark brown) or simple metal bracelet for {occ}"
            )
    return True, ""


# ---------------------------------------------------------------------------
# Belt rules
# ---------------------------------------------------------------------------

def belt_shoe_match(belt_color: str, shoe_color: str) -> tuple[bool, str]:
    """Return whether belt and shoe colors are compatible.

    Rule: black belt = black shoes; brown belt = any shade of brown/tan/cognac.
    Not an exact-match requirement — family match is sufficient.

    Args:
        belt_color: Belt color string.
        shoe_color: Shoe color string.

    Returns:
        Tuple of (is_compatible, issue_description).
    """
    b = belt_color.lower().strip()
    s = shoe_color.lower().strip()

    black_family = {"black", "dark black", "charcoal"}
    brown_family = {"brown", "tan", "cognac", "dark brown", "light brown", "caramel", "chestnut"}

    if any(c in b for c in black_family):
        if not any(c in s for c in black_family):
            return False, f"Black belt should pair with black shoes — detected {shoe_color}"
    elif any(c in b for c in brown_family):
        if not any(c in s for c in brown_family):
            return False, (
                f"Brown-family belt ({belt_color}) should pair with brown/tan/cognac shoes — "
                f"detected {shoe_color}"
            )
    return True, ""


def belt_appropriate_with_garment(garment_type: str) -> tuple[bool, str]:
    """Return whether a belt is appropriate with this garment.

    Sherwanis, formal kurtas, and bandhgalas should never have belts.

    Args:
        garment_type: Garment type string (lowercase).

    Returns:
        Tuple of (is_appropriate, issue_description).
    """
    no_belt_garments = {"sherwani", "bandhgala", "formal kurta", "achkan", "angrakha"}
    g = garment_type.lower().strip()
    if any(ng in g for ng in no_belt_garments):
        return False, (
            f"Never wear a belt with {garment_type} — these garments have self-closing "
            "silhouettes and belts disrupt the drape"
        )
    return True, ""


# ---------------------------------------------------------------------------
# Ring rules
# ---------------------------------------------------------------------------

def rings_appropriate(ring_count: int, occasion: str) -> tuple[bool, str]:
    """Return whether the number of visible rings is appropriate.

    Rule: max 2 rings visible across both hands.

    Args:
        ring_count: Total number of rings detected.
        occasion: Occasion string.

    Returns:
        Tuple of (is_appropriate, issue_description).
    """
    if ring_count > 2:
        return False, (
            f"More than 2 rings visible across both hands — reduces visual intentionality. "
            f"Edit to maximum 2 for {occasion}."
        )
    return True, ""


# ---------------------------------------------------------------------------
# Bag rules
# ---------------------------------------------------------------------------

def bag_appropriate(bag_type: str, occasion: str) -> tuple[bool, str]:
    """Return whether a bag type is appropriate for the occasion.

    Args:
        bag_type: Bag type string (e.g. "backpack", "clutch", "jhola").
        occasion: Occasion string.

    Returns:
        Tuple of (is_appropriate, issue_description).
    """
    occ = occasion.lower().strip().replace("_", " ")
    bag = bag_type.lower().strip()

    backpack_ok = {"casual", "travel", "streetwear", "business casual", "gym", "beach"}
    jhola_ok = {"indian casual", "casual", "festival", "ethnic fusion"}

    if "backpack" in bag:
        if occ not in backpack_ok and _FORMALITY_LEVELS.get(occ, 3) >= 4:
            return False, (
                "Backpack is casual/travel only — never with formal or ethnic formal. "
                "Swap to structured tote or clutch."
            )
    elif "jhola" in bag or "cloth bag" in bag:
        if occ not in jhola_ok:
            return False, f"Jhola/cloth bag suits casual ethnic only — not appropriate for {occ}"

    return True, ""


# ---------------------------------------------------------------------------
# Sunglasses rules
# ---------------------------------------------------------------------------

_FRAME_RECOMMENDATIONS: dict[FaceShape, dict[str, list[str]]] = {
    FaceShape.ROUND: {
        "recommended": ["angular frames", "wayfarer", "square frames", "rectangular frames"],
        "avoid": ["round frames", "oval frames"],
    },
    FaceShape.SQUARE: {
        "recommended": ["round frames", "oval frames", "soft curves"],
        "avoid": ["angular square frames", "rectangular frames that mirror the jaw"],
    },
    FaceShape.OVAL: {
        "recommended": ["most frames work", "wayfarer", "aviator", "cat-eye", "square"],
        "avoid": ["frames that are too wide for the face"],
    },
    FaceShape.OBLONG: {
        "recommended": ["oversized frames", "round or square", "frames with decorative temples"],
        "avoid": ["narrow frames", "small frames that elongate further"],
    },
    FaceShape.HEART: {
        "recommended": ["bottom-heavy frames", "round", "aviator", "rimless"],
        "avoid": ["cat-eye", "heavily decorated top rim"],
    },
    FaceShape.DIAMOND: {
        "recommended": ["oval frames", "rimless", "frames that are as wide as cheekbones"],
        "avoid": ["narrow rectangular", "very small frames"],
    },
}


def sunglasses_frame_recommendation(face_shape: FaceShape) -> dict[str, list[str]]:
    """Return sunglass frame recommendations for a face shape.

    Args:
        face_shape: User's face shape.

    Returns:
        Dict with 'recommended' and 'avoid' frame style lists.
    """
    return {
        "recommended": list(_FRAME_RECOMMENDATIONS[face_shape]["recommended"]),
        "avoid": list(_FRAME_RECOMMENDATIONS[face_shape]["avoid"]),
    }


# ---------------------------------------------------------------------------
# Turban / Pagdi rules
# ---------------------------------------------------------------------------

def assess_turban(
    turban_color: str,
    outfit_colors: list[str],
    occasion: str,
    turban_fabric: str,
    outfit_fabric: str,
) -> list[str]:
    """Assess turban/pagdi colour match, fabric, and occasion appropriateness.

    Args:
        turban_color: Turban color string.
        outfit_colors: List of outfit color strings.
        occasion: Occasion string.
        turban_fabric: Turban fabric description.
        outfit_fabric: Outfit fabric description.

    Returns:
        List of issue strings (empty if no issues).
    """
    issues: list[str] = []
    tc = turban_color.lower().strip()
    occ = occasion.lower().strip()

    # Check color harmony — turban must not clash with outfit
    from src.fashion_knowledge.color_theory import is_clash
    for oc in outfit_colors:
        if is_clash(tc, oc.lower().strip()):
            issues.append(
                f"Turban color '{turban_color}' clashes with '{oc}' in the outfit — "
                "choose a complementary or tonal match"
            )

    # Fabric weight match check (simple heuristic)
    heavy_fabrics = {"brocade", "silk", "velvet", "raw silk", "chanderi"}
    light_fabrics = {"cotton", "linen", "muslin"}
    turban_f = turban_fabric.lower()
    outfit_f = outfit_fabric.lower()

    turban_heavy = any(f in turban_f for f in heavy_fabrics)
    outfit_heavy = any(f in outfit_f for f in heavy_fabrics)
    turban_light = any(f in turban_f for f in light_fabrics)
    outfit_heavy_bool = outfit_heavy

    if turban_heavy and not outfit_heavy_bool:
        issues.append(
            "Turban fabric weight is heavier than the outfit — creates imbalance. "
            "Match fabric formality levels."
        )
    elif turban_light and outfit_heavy_bool:
        issues.append(
            "Turban fabric is too light for a formal/heavy outfit — upgrade to silk or brocade pagdi."
        )

    return issues


# ---------------------------------------------------------------------------
# Missing accessory suggestions
# ---------------------------------------------------------------------------

def suggest_missing_accessories(
    occasion: str,
    detected_types: list[str],
) -> list[str]:
    """Suggest accessories that are commonly missing for an occasion.

    Args:
        occasion: Occasion string.
        detected_types: List of already-detected accessory type strings.

    Returns:
        List of suggested missing accessories.
    """
    occ = occasion.lower().strip().replace("_", " ")
    detected = {d.lower() for d in detected_types}
    suggestions: list[str] = []

    if "western formal" in occ or "business" in occ:
        if "pocket square" not in detected:
            suggestions.append("Pocket square — adds intentionality to a formal jacket")
        if "watch" not in detected:
            suggestions.append("Dress watch with leather strap — anchors the formal look")

    if "indian formal" in occ or "wedding" in occ:
        if "watch" not in detected:
            suggestions.append("Simple metal bracelet or dress watch on tan leather strap")

    if "party" in occ or "smart casual" in occ:
        if "watch" not in detected:
            suggestions.append("Watch — even a minimal piece elevates smart casual")

    return suggestions
