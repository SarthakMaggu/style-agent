"""Body type rules for silhouette, proportion, and garment recommendations.

Covers all five male body shapes and cross-references with kurta length rules
for Indian wear.
"""

from dataclasses import dataclass, field

from src.models.user_profile import BodyShape


# ---------------------------------------------------------------------------
# Silhouette rules by body shape
# ---------------------------------------------------------------------------

@dataclass
class BodyTypeRules:
    """Do and avoid rules for a body shape."""

    shape: BodyShape
    do: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    notes: str = ""


_RULES: dict[BodyShape, BodyTypeRules] = {
    BodyShape.RECTANGLE: BodyTypeRules(
        shape=BodyShape.RECTANGLE,
        do=[
            "structured shoulders",
            "belted silhouettes",
            "contrast top/bottom",
            "double-breasted jackets",
            "layering to add visual depth",
            "horizontal stripe on top to add perceived width",
        ],
        avoid=[
            "boxy all-over with no definition",
            "single-colour head-to-toe without any waist emphasis",
        ],
        notes="Goal: create the illusion of a defined waist.",
    ),
    BodyShape.TRIANGLE: BodyTypeRules(
        shape=BodyShape.TRIANGLE,
        do=[
            "structured shoulders",
            "top details (lapels, pockets, patterns on chest)",
            "darker bottoms",
            "wider-collar shirts",
            "horizontal stripes or bold prints on top",
            "lighter colours on top",
        ],
        avoid=[
            "tight bottom + tight top together",
            "hip-level horizontal patterns",
            "cargo or wide-leg trousers without structure on top",
        ],
        notes="Goal: balance narrower shoulders vs wider hips by drawing attention upward.",
    ),
    BodyShape.INVERTED_TRIANGLE: BodyTypeRules(
        shape=BodyShape.INVERTED_TRIANGLE,
        do=[
            "longer hemlines",
            "V-necks and open necklines (draw eye inward and down)",
            "vertical top lines",
            "A-line or tapered bottoms",
            "mid-thigh or longer kurtas",
            "solid or small-pattern tops",
        ],
        avoid=[
            "shoulder padding",
            "chest horizontal stripes",
            "puffed sleeves",
            "epaulettes or wide lapels",
            "bold top patterns that amplify shoulder width",
        ],
        notes="Goal: minimise perceived shoulder width; elongate downward.",
    ),
    BodyShape.OVAL: BodyTypeRules(
        shape=BodyShape.OVAL,
        do=[
            "vertical lines and pinstripes",
            "open necklines (V-neck, open collar)",
            "straight cuts",
            "longer lengths",
            "dark monochromatic palette",
            "structured outer layer",
        ],
        avoid=[
            "horizontal waist bands",
            "cropped tops",
            "un-tucked shirts without structure",
            "clingy fabrics",
            "bold horizontal patterns at the midsection",
        ],
        notes="Goal: create a vertical, elongating line through the silhouette.",
    ),
    BodyShape.TRAPEZOID: BodyTypeRules(
        shape=BodyShape.TRAPEZOID,
        do=[
            "most silhouettes work",
            "maintain proportional balance between top and bottom",
            "fitted garments that follow the natural taper",
            "both casual and formal cuts",
        ],
        avoid=[
            "excessive bulk everywhere",
            "oversized top + oversized bottom simultaneously",
        ],
        notes="Trapezoid is considered the most versatile male body shape.",
    ),
}


# ---------------------------------------------------------------------------
# Kurta length rules (Indian wear cross-reference)
# ---------------------------------------------------------------------------

def kurta_length(height: str, body_shape: BodyShape) -> str:
    """Return the recommended kurta length based on height and body shape.

    Args:
        height: User height estimate — "tall" / "average" / "petite".
        body_shape: User body shape.

    Returns:
        Recommended kurta length string.
    """
    h = height.lower().strip()

    # Petite always hip or just above — longer drags down and shortens further
    if h == "petite":
        return "at or just above hip — never lower (shortens the frame further)"

    # Inverted triangle always needs mid-thigh+ to offset shoulder width
    if body_shape == BodyShape.INVERTED_TRIANGLE:
        return "mid-thigh or longer — balances broad shoulders by drawing the eye down"

    if h == "tall":
        return "mid-thigh or below"

    # Average height + rectangle
    if body_shape == BodyShape.RECTANGLE:
        return "hip to mid-thigh"

    # Average height + other shapes
    return "mid-thigh is the safest choice for most occasions"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_rules(shape: BodyShape) -> BodyTypeRules:
    """Return do/avoid rules for a body shape.

    Args:
        shape: The user's body shape.

    Returns:
        BodyTypeRules dataclass.
    """
    return _RULES[shape]


def get_do(shape: BodyShape) -> list[str]:
    """Return recommended styling actions for this body shape."""
    return list(_RULES[shape].do)


def get_avoid(shape: BodyShape) -> list[str]:
    """Return styling actions to avoid for this body shape."""
    return list(_RULES[shape].avoid)


def all_shapes_covered() -> bool:
    """Return True if every BodyShape has a rule entry (completeness check)."""
    return all(shape in _RULES for shape in BodyShape)
