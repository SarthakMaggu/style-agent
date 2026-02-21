"""Grooming rules for haircut, beard, and eyebrows by face shape.

Provides lookup functions used by grooming_agent to generate specific
hair and beard recommendations.
"""

from dataclasses import dataclass, field

from src.models.user_profile import FaceShape


# ---------------------------------------------------------------------------
# Haircut rules by face shape
# ---------------------------------------------------------------------------

@dataclass
class HaircutRules:
    """Recommended and avoided haircuts for a face shape."""

    face_shape: FaceShape
    recommended: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    notes: str = ""


_HAIRCUT_RULES: dict[FaceShape, HaircutRules] = {
    FaceShape.OVAL: HaircutRules(
        face_shape=FaceShape.OVAL,
        recommended=[
            "most cuts work",
            "classic taper fade",
            "side part",
            "quiff",
            "textured crop",
            "slicked back",
        ],
        avoid=[
            "excessive height that further elongates the face",
            "very tall quiff without side volume",
        ],
        notes="Oval is the most versatile face shape for haircuts.",
    ),
    FaceShape.SQUARE: HaircutRules(
        face_shape=FaceShape.SQUARE,
        recommended=[
            "textured crops",
            "side parts",
            "tapered sides with texture on top",
            "fades with soft top styling",
            "modern quiff with movement",
        ],
        avoid=[
            "boxy cuts",
            "bowl cuts",
            "blunt fringes that emphasise the jaw width",
            "all-one-length cuts with no fade",
        ],
        notes="Soften the angular jaw — avoid anything that adds squareness.",
    ),
    FaceShape.ROUND: HaircutRules(
        face_shape=FaceShape.ROUND,
        recommended=[
            "height on top (pompadour, quiff, faux hawk)",
            "tight sides (high fade, undercut)",
            "angular or geometric styling on top",
            "textured crop with height",
        ],
        avoid=[
            "bowl cuts",
            "unstyled curtains",
            "side sweeps without any height",
            "full volume on sides",
        ],
        notes="Add height to elongate; keep sides tight to reduce perceived width.",
    ),
    FaceShape.OBLONG: HaircutRules(
        face_shape=FaceShape.OBLONG,
        recommended=[
            "side sweeps",
            "volume on sides",
            "medium-length styles with width",
            "curtains or fringe",
            "tousled texture at the sides",
        ],
        avoid=[
            "height — elongates the face further",
            "very short sides with tall top",
            "slicked-back styles with no side volume",
        ],
        notes="Add width, never height — the face is already long.",
    ),
    FaceShape.HEART: HaircutRules(
        face_shape=FaceShape.HEART,
        recommended=[
            "medium length with soft fringe",
            "side parts that break forehead width",
            "styles with volume at the jaw level",
            "textured mid-length",
        ],
        avoid=[
            "heavy top-heavy volume",
            "very short sides that emphasise the wide forehead",
            "high fades with no top coverage",
        ],
        notes="Balance wide forehead with volume lower down.",
    ),
    FaceShape.DIAMOND: HaircutRules(
        face_shape=FaceShape.DIAMOND,
        recommended=[
            "styles that maintain width at forehead and jaw",
            "short to medium length",
            "textured fringe",
            "soft side parts",
        ],
        avoid=[
            "narrow side profiles",
            "very slicked-back styles",
            "styles that taper at both forehead and jaw simultaneously",
        ],
        notes="Keep width visible at forehead and jaw to soften narrow cheekbones.",
    ),
}


# ---------------------------------------------------------------------------
# Beard rules by face shape
# ---------------------------------------------------------------------------

@dataclass
class BeardRules:
    """Recommended and avoided beard styles for a face shape."""

    face_shape: FaceShape
    recommended: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    notes: str = ""


_BEARD_RULES: dict[FaceShape, BeardRules] = {
    FaceShape.OVAL: BeardRules(
        face_shape=FaceShape.OVAL,
        recommended=[
            "any style",
            "classic full beard recommended",
            "short stubble",
            "groomed medium beard",
        ],
        avoid=[],
        notes="Oval suits all beard styles.",
    ),
    FaceShape.SQUARE: BeardRules(
        face_shape=FaceShape.SQUARE,
        recommended=[
            "longer on chin to soften jaw",
            "cheeks and sides trimmed shorter",
            "chin-extended goatee",
            "rounded full beard with longer chin",
        ],
        avoid=[
            "wide full cheek coverage that adds jaw width",
            "square-cut beard that mirrors the jaw shape",
        ],
        notes="Soften the jaw: length on chin, shorter on sides.",
    ),
    FaceShape.ROUND: BeardRules(
        face_shape=FaceShape.ROUND,
        recommended=[
            "extended chin beard to elongate",
            "sides kept tight or clean",
            "short goatee",
            "chin strap with chin extension",
        ],
        avoid=[
            "full round beard that adds width",
            "mutton chops",
            "heavy cheek coverage",
        ],
        notes="Elongate the face: length at chin is critical, tight sides.",
    ),
    FaceShape.OBLONG: BeardRules(
        face_shape=FaceShape.OBLONG,
        recommended=[
            "full and wide to add width",
            "boxed beard",
            "mutton chops or extended sideburns",
        ],
        avoid=[
            "long chin extension (elongates further)",
            "narrow chin-only styles",
        ],
        notes="Add width, not length. Full beard adds needed width to the face.",
    ),
    FaceShape.HEART: BeardRules(
        face_shape=FaceShape.HEART,
        recommended=[
            "fuller chin to balance narrower jaw",
            "light cheek coverage",
            "rounded full beard",
            "extended chin with kept sides",
        ],
        avoid=[
            "bare chin with heavy sideburns",
            "styles that widen the already-wide forehead area",
        ],
        notes="Balance wide forehead with chin fullness.",
    ),
    FaceShape.DIAMOND: BeardRules(
        face_shape=FaceShape.DIAMOND,
        recommended=[
            "full at jaw",
            "cheeks clean — avoids width at cheekbones",
            "chin-focused full beard",
        ],
        avoid=[
            "heavy cheek coverage (widens cheekbones)",
            "narrow chin-only styles",
        ],
        notes="Full jaw and clean cheeks balance the narrow forehead and chin.",
    ),
}


# ---------------------------------------------------------------------------
# Eyebrow recommendations (universal + face-shape specific)
# ---------------------------------------------------------------------------

_EYEBROW_RECOMMENDATIONS: dict[FaceShape, str] = {
    FaceShape.OVAL: "Well-groomed natural arch. Slight angle complements balance.",
    FaceShape.SQUARE: "Soft arch to counterbalance the angular jaw. Avoid flat brows.",
    FaceShape.ROUND: "High arch to add vertical length. Avoid flat or round brows.",
    FaceShape.OBLONG: "Flat to slightly arched — avoids adding more perceived length.",
    FaceShape.HEART: "Soft natural arch. Avoid overly thin or heavily shaped brows.",
    FaceShape.DIAMOND: "Curved arch to balance the angular cheekbones.",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_haircut_rules(face_shape: FaceShape) -> HaircutRules:
    """Return haircut do/avoid rules for a face shape.

    Args:
        face_shape: The user's face shape.

    Returns:
        HaircutRules dataclass.
    """
    return _HAIRCUT_RULES[face_shape]


def get_beard_rules(face_shape: FaceShape) -> BeardRules:
    """Return beard do/avoid rules for a face shape.

    Args:
        face_shape: The user's face shape.

    Returns:
        BeardRules dataclass.
    """
    return _BEARD_RULES[face_shape]


def get_eyebrow_recommendation(face_shape: FaceShape) -> str:
    """Return eyebrow grooming recommendation for a face shape.

    Args:
        face_shape: The user's face shape.

    Returns:
        Recommendation string (never empty).
    """
    return _EYEBROW_RECOMMENDATIONS[face_shape]


def score_beard_grooming(grooming_quality: str) -> int:
    """Return a grooming score contribution (1–10) based on beard grooming quality.

    Args:
        grooming_quality: Observed grooming quality string.

    Returns:
        Integer score 1–10.
    """
    mapping = {
        "well groomed": 9,
        "average": 6,
        "unkempt": 3,
        "not applicable": 8,  # clean shaven counts as well maintained
    }
    return mapping.get(grooming_quality.lower().strip(), 5)
