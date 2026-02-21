"""Western wear rules — trouser break, collar types, layering, and belt/shoe pairing.

Used by recommendation_agent for Western formal, business casual, smart casual,
streetwear, and party analysis.
"""

from src.models.user_profile import FaceShape


# ---------------------------------------------------------------------------
# Trouser break by height
# ---------------------------------------------------------------------------

def trouser_break(height: str) -> str:
    """Return the recommended trouser break for a height.

    Args:
        height: Height estimate — "tall" / "average" / "petite".

    Returns:
        Recommendation string.
    """
    h = height.lower().strip()
    if h == "tall":
        return "no break or slight break — full break puddles and shortens the leg line"
    if h == "petite":
        return "no break always — consider ankle-length trousers for maximum leg length"
    return "half break is the safe default for average height"


# ---------------------------------------------------------------------------
# Shirt collar compatibility with face shape
# ---------------------------------------------------------------------------

_COLLAR_FACE_COMPATIBILITY: dict[str, list[FaceShape]] = {
    "spread collar": [FaceShape.SQUARE, FaceShape.OVAL, FaceShape.OBLONG],
    "button-down": [FaceShape.OVAL, FaceShape.HEART, FaceShape.OBLONG],
    "band collar": [FaceShape.OVAL, FaceShape.OBLONG],
    "point collar": list(FaceShape),     # generally versatile
    "cutaway collar": [FaceShape.SQUARE, FaceShape.OVAL],
    "club collar": [FaceShape.OVAL, FaceShape.HEART],
}

_COLLAR_AVOID: dict[str, list[FaceShape]] = {
    "spread collar": [FaceShape.ROUND],  # spread collar on round face widens further
}


def collar_face_compatible(collar_type: str, face_shape: FaceShape) -> tuple[bool, str]:
    """Return whether a western shirt collar type suits a face shape.

    Args:
        collar_type: Collar type string.
        face_shape: User's face shape.

    Returns:
        Tuple of (is_compatible, issue_description).
    """
    ct = collar_type.lower().strip()

    # Check explicit avoid rules first
    avoid_shapes = _COLLAR_AVOID.get(ct, [])
    if face_shape in avoid_shapes:
        return False, (
            f"'{collar_type}' collar is not recommended for {face_shape.value} face — "
            "it adds width at the collar which amplifies the face's roundness. "
            "Try button-down or point collar instead."
        )

    compatible = _COLLAR_FACE_COMPATIBILITY.get(ct)
    if compatible is None:
        return True, ""  # Unknown collar — no ruling

    if face_shape not in compatible:
        better = [
            c for c, shapes in _COLLAR_FACE_COMPATIBILITY.items()
            if face_shape in shapes and c != ct
        ]
        rec = f"Better collars for {face_shape.value}: {', '.join(better[:3])}" if better else ""
        return False, f"'{collar_type}' is not ideal for {face_shape.value} face. {rec}"

    return True, ""


# ---------------------------------------------------------------------------
# Layering rules
# ---------------------------------------------------------------------------

def validate_layering(
    base_fabric_weight: str,
    outer_fabric_weight: str,
    base_fit: str,
    outer_fit: str,
) -> list[str]:
    """Return a list of layering issues (empty if all is well).

    Rules:
    - Heavier fabric must be on the outside
    - Fit tapers inward: base layer slimmest, outer most relaxed

    Args:
        base_fabric_weight: Fabric weight of base layer (light / medium / heavy).
        outer_fabric_weight: Fabric weight of outer layer.
        base_fit: Fit of base layer (slim / regular / relaxed / oversized).
        outer_fit: Fit of outer layer.

    Returns:
        List of issue strings.
    """
    issues: list[str] = []
    weight_order = {"light": 1, "medium": 2, "heavy": 3}
    fit_order = {"slim": 1, "fitted": 1, "regular": 2, "relaxed": 3, "oversized": 4}

    base_w = weight_order.get(base_fabric_weight.lower().strip(), 2)
    outer_w = weight_order.get(outer_fabric_weight.lower().strip(), 2)
    base_f = fit_order.get(base_fit.lower().strip(), 2)
    outer_f = fit_order.get(outer_fit.lower().strip(), 2)

    if outer_w < base_w:
        issues.append(
            "Outer layer is lighter than base layer — reverse the order. "
            "Heavier fabrics always go on the outside."
        )
    if outer_f < base_f:
        issues.append(
            "Outer layer is slimmer than base layer — layering should taper inward. "
            "Base layer slimmest, outer layer most relaxed."
        )
    return issues


# ---------------------------------------------------------------------------
# Trouser and shoe pairing
# ---------------------------------------------------------------------------

_TROUSER_SHOE_PAIRS: dict[str, list[str]] = {
    "slim": ["loafers", "derbies", "clean sneakers", "chelsea boots"],
    "tapered": ["loafers", "derbies", "clean sneakers", "chelsea boots"],
    "regular": ["loafers", "brogues", "clean sneakers", "oxford", "derby"],
    "wide": ["chunky sneakers", "chelsea boots", "brogues"],
    "relaxed": ["chunky sneakers", "chelsea boots", "brogues"],
    "formal tailored": ["oxford", "derby"],
}

_TROUSER_SHOE_FORBIDDEN: dict[str, list[str]] = {
    "formal tailored": ["loafers", "sneakers"],
}


def trouser_shoe_appropriate(trouser_fit: str, shoe_type: str) -> tuple[bool, str]:
    """Return whether a shoe type pairs well with a trouser fit.

    Args:
        trouser_fit: Trouser fit string (slim / tapered / regular / wide / formal tailored).
        shoe_type: Shoe type string.

    Returns:
        Tuple of (is_appropriate, issue_description).
    """
    fit = trouser_fit.lower().strip()
    shoe = shoe_type.lower().strip()

    forbidden = _TROUSER_SHOE_FORBIDDEN.get(fit, [])
    for f in forbidden:
        if f in shoe:
            recommended = _TROUSER_SHOE_PAIRS.get(fit, [])
            return False, (
                f"'{shoe_type}' is not appropriate with {trouser_fit} trousers. "
                f"Recommended: {', '.join(recommended[:3])}."
            )

    return True, ""


# ---------------------------------------------------------------------------
# Belt and shoe colour rules (re-exported convenience — canonical in accessory_guide.py)
# ---------------------------------------------------------------------------

def belt_shoe_compatible(belt_color: str, shoe_color: str) -> tuple[bool, str]:
    """Delegate to accessory_guide.belt_shoe_match for consistency."""
    from src.fashion_knowledge.accessory_guide import belt_shoe_match
    return belt_shoe_match(belt_color, shoe_color)


def no_belt_needed(garment_type: str, style: str) -> bool:
    """Return True when a belt is unnecessary or incorrect for the combination.

    Args:
        garment_type: Bottom garment type (e.g. "chinos", "denim", "jeans").
        style: Style context (e.g. "untucked shirt", "suspenders", "formal suit").

    Returns:
        True if no belt is needed.
    """
    gt = garment_type.lower().strip()
    s = style.lower().strip()
    no_belt_cases = [
        ("denim", "untucked"),
        ("jeans", "untucked"),
        ("chinos", "untucked"),
        ("suit", "suspenders"),
        ("tailored suit", "suspenders"),
    ]
    for garment, sty in no_belt_cases:
        if garment in gt and sty in s:
            return True
    return False
