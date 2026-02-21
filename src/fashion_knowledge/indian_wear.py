"""Indian wear rules — kurta length, collar types, fabric, fusion validity, and skin palettes.

Used by recommendation_agent for all Indian and ethnic fusion occasion analysis.
"""

from src.models.user_profile import BodyShape, FaceShape, SkinUndertone


# ---------------------------------------------------------------------------
# Collar type compatibility with face shapes
# ---------------------------------------------------------------------------

_COLLAR_FACE_COMPATIBILITY: dict[str, list[FaceShape]] = {
    "bandhgala": [FaceShape.SQUARE, FaceShape.OVAL, FaceShape.OBLONG],
    "nehru": [FaceShape.OVAL, FaceShape.HEART, FaceShape.DIAMOND],
    "mandarin": list(FaceShape),  # versatile — most face shapes
    "angrakha": [FaceShape.OVAL, FaceShape.HEART],
}


def collar_face_compatible(collar_type: str, face_shape: FaceShape) -> tuple[bool, str]:
    """Return whether an Indian collar type suits a face shape.

    Args:
        collar_type: Collar type string (e.g. "bandhgala", "nehru").
        occasion: Occasion string.

    Returns:
        Tuple of (is_compatible, recommendation).
    """
    ct = collar_type.lower().strip()
    compatible_shapes = _COLLAR_FACE_COMPATIBILITY.get(ct)
    if compatible_shapes is None:
        return True, ""  # Unknown collar — no ruling

    if face_shape not in compatible_shapes:
        better = [c for c, shapes in _COLLAR_FACE_COMPATIBILITY.items() if face_shape in shapes]
        rec = f"Better collar choices for {face_shape.value} face: {', '.join(better)}" if better else ""
        return False, (
            f"{collar_type.title()} collar is not ideal for {face_shape.value} face. {rec}"
        )
    return True, ""


# ---------------------------------------------------------------------------
# Fabric by occasion
# ---------------------------------------------------------------------------

_FABRIC_OCCASION: dict[str, list[str]] = {
    "wedding_guest_indian": ["chanderi", "silk-cotton blend", "raw silk", "brocade"],
    "indian_formal": ["chanderi", "silk-cotton blend", "raw silk", "brocade"],
    "business_casual": ["cotton-silk blend", "linen-cotton", "structured cotton"],
    "smart_casual": ["cotton-silk blend", "linen-cotton", "structured cotton"],
    "indian_casual": ["plain cotton", "block print", "linen"],
    "casual": ["plain cotton", "block print", "linen"],
    "festival": ["any — colour and print are more important than fabric at festivals"],
    "ethnic_fusion": ["cotton-silk blend", "structured cotton", "linen-cotton"],
    "party": ["silk", "raw silk", "chanderi", "velvet"],
}


def fabric_appropriate_for_occasion(fabric: str, occasion: str) -> tuple[bool, str]:
    """Return whether fabric is appropriate for the occasion.

    Args:
        fabric: Fabric string (e.g. "plain cotton", "silk").
        occasion: Occasion string.

    Returns:
        Tuple of (is_appropriate, issue_description).
    """
    occ = occasion.lower().strip().replace(" ", "_")
    appropriate = _FABRIC_OCCASION.get(occ)

    if appropriate is None:
        return True, ""  # Unknown occasion — no ruling

    if "any" in appropriate[0]:
        return True, ""  # Festival — anything goes

    fab = fabric.lower().strip()
    for suitable in appropriate:
        if suitable in fab or fab in suitable:
            return True, ""

    # Cotton at a wedding is the most common failure case
    is_formal_occasion = occ in {"wedding_guest_indian", "indian_formal", "party"}
    if is_formal_occasion and ("cotton" in fab and "silk" not in fab):
        return False, (
            f"'{fabric}' reads two formality levels below what {occ.replace('_', ' ')} requires. "
            f"Upgrade to: {', '.join(appropriate[:2])}."
        )

    return False, (
        f"'{fabric}' is not ideal for {occ.replace('_', ' ')}. "
        f"Recommended fabrics: {', '.join(appropriate[:3])}."
    )


# ---------------------------------------------------------------------------
# Ethnic fusion validity
# ---------------------------------------------------------------------------

_VALID_FUSIONS = [
    ("kurta", "tailored trousers"),
    ("kurta", "dark slim jeans"),
    ("kurta", "dark jeans"),
    ("bandhgala jacket", "western trousers"),
    ("nehru jacket", "shirt"),
]

_INVALID_FUSIONS = [
    ("sherwani", "jeans"),
    ("ethnic top", "track pants"),
    ("ethnic top", "gym bottoms"),
    ("formal kurta", "cargo shorts"),
    ("mojaris", "western formal suit"),
]


def is_valid_fusion(top_garment: str, bottom_garment: str) -> tuple[bool, str]:
    """Return whether an ethnic + western fusion combination is valid.

    Args:
        top_garment: Top/upper garment description.
        bottom_garment: Bottom garment description.

    Returns:
        Tuple of (is_valid, issue_description).
    """
    top = top_garment.lower().strip()
    bottom = bottom_garment.lower().strip()

    # Check invalid combinations first
    for inv_top, inv_bottom in _INVALID_FUSIONS:
        if inv_top in top and inv_bottom in bottom:
            return False, (
                f"'{top_garment}' + '{bottom_garment}' is an invalid ethnic fusion — "
                f"this combination undermines both garments."
            )

    # Check valid combinations
    for val_top, val_bottom in _VALID_FUSIONS:
        if val_top in top and val_bottom in bottom:
            return True, ""

    # Unknown combination — return neutral
    return True, ""


# ---------------------------------------------------------------------------
# South Asian skin palettes
# ---------------------------------------------------------------------------

_SOUTH_ASIAN_PALETTES: dict[str, list[str]] = {
    "warm_olive": ["mustard", "rust", "deep teal", "warm navy", "ivory", "earthy browns"],
    "deep_warm": ["jewel tones", "gold", "warm burgundy", "deep orange", "forest green"],
    "medium_warm": [
        "wide range — avoid nude too close to skin tone",
        "terracotta", "warm navy", "rust", "olive green",
    ],
}


def south_asian_palette(undertone: SkinUndertone) -> list[str]:
    """Return South Asian occasion-aware colour palette for an undertone.

    Args:
        undertone: The user's skin undertone.

    Returns:
        List of recommended colours.
    """
    if undertone == SkinUndertone.DEEP_WARM:
        return list(_SOUTH_ASIAN_PALETTES["deep_warm"])
    if undertone in (SkinUndertone.OLIVE_WARM, SkinUndertone.WARM):
        return list(_SOUTH_ASIAN_PALETTES["warm_olive"])
    return list(_SOUTH_ASIAN_PALETTES["medium_warm"])


# ---------------------------------------------------------------------------
# Kurta length (re-exported here for convenience — canonical in body_types.py)
# ---------------------------------------------------------------------------

def kurta_length_recommendation(height: str, body_shape: BodyShape) -> str:
    """Convenience wrapper — delegates to body_types.kurta_length."""
    from src.fashion_knowledge.body_types import kurta_length
    return kurta_length(height, body_shape)
