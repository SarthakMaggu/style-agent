"""Proportion theory — the complete height × body shape matrix.

Provides the authoritative 5×3 grid (5 body shapes × 3 heights = 15 entries)
for silhouette, trouser break, kurta length, jacket length, layering strategy,
pattern scale, and fabric texture guidance.

This module is the single source of truth for proportion-related rules used in
recommendation prompts. Existing body_types.py and western_wear.py functions
are kept intact for their own rule-based tests; this module powers the richer
prompt context injected into Claude.

Usage:
    from src.fashion_knowledge.proportion_theory import (
        get_proportion_rules,
        proportion_context_string,
        pattern_scale_recommendation,
    )

    rules = get_proportion_rules("tall", "inverted_triangle")
    context = proportion_context_string("average", "oval")
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class ProportionRules:
    """Full proportion guidance for one height × body shape combination."""

    height: str
    """"tall" / "average" / "petite"."""

    body_shape: str
    """BodyShape value string."""

    visual_goal: str
    """The single most important silhouette objective."""

    do: list[str] = field(default_factory=list)
    """Silhouette strategies to actively use."""

    avoid: list[str] = field(default_factory=list)
    """Silhouette mistakes to prevent."""

    trouser_break: str = ""
    """"none" / "slight" / "half" — hem landing on shoe."""

    kurta_length: str = ""
    """"hip" / "mid-thigh" / "below-knee" — ideal kurta/tunic length."""

    jacket_length: str = ""
    """Ideal jacket hem zone."""

    belt_use: str = ""
    """"emphasise" / "avoid" / "optional"."""

    layer_strategy: str = ""
    """How to handle layering for this combination."""


# ---------------------------------------------------------------------------
# The 15-entry matrix
# ---------------------------------------------------------------------------

_MATRIX: dict[tuple[str, str], ProportionRules] = {

    # ── TALL × each shape ──────────────────────────────────────────────────

    ("tall", "rectangle"): ProportionRules(
        height="tall",
        body_shape="rectangle",
        visual_goal="Add width definition and waist interest to a long, straight frame",
        do=[
            "Contrast top and bottom to create a visual break",
            "Belted silhouettes — nip the waist to create the illusion of shape",
            "Structured shoulders to add breadth",
            "Horizontal detailing at chest or hip level",
            "Bold patterns — your height carries them without feeling overwhelming",
        ],
        avoid=[
            "Boxy all-over with no definition — elongates without adding shape",
            "Monochromatic top-to-toe with no contrast — flattens the silhouette",
            "Overly long hemlines that emphasise the vertical line",
        ],
        trouser_break="slight",
        kurta_length="mid-thigh",
        jacket_length="hip-length",
        belt_use="emphasise",
        layer_strategy=(
            "Add a structured outer layer at hip length to create width contrast. "
            "Open front works well — adds frame without closing the silhouette."
        ),
    ),

    ("tall", "triangle"): ProportionRules(
        height="tall",
        body_shape="triangle",
        visual_goal="Build shoulder presence and draw the eye upward away from wider hips",
        do=[
            "Structured shoulders — padding or strong shoulder seam",
            "Bold top details: patterns, textures, interesting necklines",
            "Dark bottoms to visually narrow the hip zone",
            "Contrast in favour of the top half",
            "V-necks and open collars to broaden the upper chest visually",
        ],
        avoid=[
            "Tight bottoms with tight top — hip width is maximised",
            "Horizontal patterns at hip level",
            "Light or bright bottoms paired with dark tops",
            "Dropped shoulder tops — reduces already-narrow shoulder line",
        ],
        trouser_break="slight",
        kurta_length="hip",
        jacket_length="hip-length to mid-thigh",
        belt_use="avoid",
        layer_strategy=(
            "Layer structurally at the top — a blazer or structured shirt over a base layer "
            "adds shoulder mass. Keep bottoms clean and untextured."
        ),
    ),

    ("tall", "inverted_triangle"): ProportionRules(
        height="tall",
        body_shape="inverted_triangle",
        visual_goal="Balance wide shoulders by drawing volume and interest downward",
        do=[
            "Longer hemlines — mid-thigh to below-knee kurtas, longer jackets",
            "V-necks and vertical top lines to minimise chest breadth",
            "A-line or tapered bottoms for visual balance",
            "Muted, darker tones on top, more interesting textures below",
            "Straight-leg trousers — wide enough to balance the upper body",
        ],
        avoid=[
            "Shoulder pads or epaulettes",
            "Boat necks and wide horizontal collar lines",
            "Cropped tops or jackets — maximises shoulder-to-hip disparity",
            "Puffed sleeves or heavily textured upper arms",
            "Narrow, tapered trousers with a bulky top",
        ],
        trouser_break="none",
        kurta_length="mid-thigh to below-knee",
        jacket_length="mid-thigh or longer",
        belt_use="optional",
        layer_strategy=(
            "Keep layers minimal on top. A long open layer (longline cardigan, "
            "open bandhgala) elongates the torso and draws the eye down."
        ),
    ),

    ("tall", "oval"): ProportionRules(
        height="tall",
        body_shape="oval",
        visual_goal="Create vertical length through the midsection, define the silhouette",
        do=[
            "Vertical lines — pinstripes, long open layering, vertical seam details",
            "Open necklines — V-neck, open collar, mandarin without button closure",
            "Straight, unconstructed cuts that skim without clinging",
            "Longer hemlines to extend the vertical line past the midsection",
            "Monochromatic dressing for maximum elongation",
        ],
        avoid=[
            "Horizontal waist bands or belts",
            "Cropped tops — cuts the eye at the widest point",
            "Un-tucked shirts without structure — increases volume",
            "Hip-level horizontal patterns",
            "Boxy silhouettes all over",
        ],
        trouser_break="none",
        kurta_length="mid-thigh to below-knee",
        jacket_length="mid-thigh or longer",
        belt_use="avoid",
        layer_strategy=(
            "Single long vertical layer — longline blazer or kurta. "
            "Avoid short outer layers that break the line."
        ),
    ),

    ("tall", "trapezoid"): ProportionRules(
        height="tall",
        body_shape="trapezoid",
        visual_goal="Maintain proportional balance — your frame is naturally balanced; height does the rest",
        do=[
            "Most silhouettes work — focus on proportional balance",
            "Slightly tapered bottoms to keep the shape clean at height",
            "Structured outerwear to maintain presence",
        ],
        avoid=[
            "Excessive volume everywhere simultaneously",
            "Overly cropped tops — can look unbalanced at height",
        ],
        trouser_break="slight",
        kurta_length="mid-thigh",
        jacket_length="hip to mid-thigh",
        belt_use="optional",
        layer_strategy=(
            "Experiment freely — your proportions support most combinations. "
            "Watch that outer layers don't add unnecessary bulk."
        ),
    ),

    # ── AVERAGE × each shape ──────────────────────────────────────────────

    ("average", "rectangle"): ProportionRules(
        height="average",
        body_shape="rectangle",
        visual_goal="Add shape definition to a straight frame without adding unwanted height",
        do=[
            "Belted or waist-defining cuts",
            "Contrast between top and bottom colour",
            "Structured shoulders, slightly defined waist",
            "Mid-weight patterns — not overwhelming at average height",
            "Half-break trouser — safe default for a clean silhouette",
        ],
        avoid=[
            "Boxy cuts with no waist interest",
            "Very long hemlines that cut visual leg length",
        ],
        trouser_break="half",
        kurta_length="hip to mid-thigh",
        jacket_length="hip-length",
        belt_use="emphasise",
        layer_strategy=(
            "A structured jacket or bandhgala at hip length adds shape. "
            "Keep the inner layer fitted."
        ),
    ),

    ("average", "triangle"): ProportionRules(
        height="average",
        body_shape="triangle",
        visual_goal="Broaden the upper body and narrow the visual hip width",
        do=[
            "Wide or structured lapels to build shoulder frame",
            "Top details — patterns, textures, pockets at chest level",
            "Darker, plain bottoms",
            "Slight half-break on trousers — keeps the leg clean",
        ],
        avoid=[
            "Narrow collars that reduce the shoulder line",
            "Light or textured bottoms that draw attention to hips",
            "Horizontal patterns below the waist",
        ],
        trouser_break="half",
        kurta_length="hip",
        jacket_length="hip-length",
        belt_use="avoid",
        layer_strategy=(
            "Structured jacket or blazer is the single most effective tool — "
            "builds shoulder mass immediately. Keep the base slim."
        ),
    ),

    ("average", "inverted_triangle"): ProportionRules(
        height="average",
        body_shape="inverted_triangle",
        visual_goal="Soften broad shoulders and balance the lower half",
        do=[
            "Mid-thigh kurtas — elongate and balance at average height",
            "Vertical lines and V-neck openings",
            "Slightly wider trousers to balance upper body width",
            "Half-break — clean without shortening the leg",
        ],
        avoid=[
            "Boat necks, wide collars, shoulder emphasis",
            "Cropped jackets or short tops",
        ],
        trouser_break="half",
        kurta_length="mid-thigh",
        jacket_length="mid-thigh",
        belt_use="optional",
        layer_strategy=(
            "A longline outer layer (mid-thigh length) draws the eye down and "
            "balances the wide shoulder. Avoid short bomber-style jackets."
        ),
    ),

    ("average", "oval"): ProportionRules(
        height="average",
        body_shape="oval",
        visual_goal="Create vertical elongation through the midsection at average height",
        do=[
            "Long vertical layers — longline jacket, structured kurta",
            "Open necklines — V, mandarin, no collar",
            "Mid-thigh to below-knee hemlines to extend the vertical",
            "Monochromatic dressing in dark or neutral tones",
        ],
        avoid=[
            "Waist bands, belts, anything that marks the widest zone",
            "Cropped tops",
            "Horizontal waist-level details",
            "Clingy fabrics",
        ],
        trouser_break="none",
        kurta_length="mid-thigh to below-knee",
        jacket_length="mid-thigh",
        belt_use="avoid",
        layer_strategy=(
            "One clean vertical outer layer. Avoid multiple short layers "
            "that break the line and add horizontal interest."
        ),
    ),

    ("average", "trapezoid"): ProportionRules(
        height="average",
        body_shape="trapezoid",
        visual_goal="Maintain the natural balance — standard proportional rules apply",
        do=[
            "Most silhouettes work — concentrate on fit quality",
            "Half-break trouser is the safe default",
            "Slight waist definition in structured pieces",
        ],
        avoid=[
            "Excessive volume in both top and bottom simultaneously",
        ],
        trouser_break="half",
        kurta_length="hip to mid-thigh",
        jacket_length="hip-length",
        belt_use="optional",
        layer_strategy="Standard layering — heavier fabric on top, base slim.",
    ),

    # ── PETITE × each shape ──────────────────────────────────────────────

    ("petite", "rectangle"): ProportionRules(
        height="petite",
        body_shape="rectangle",
        visual_goal="Add length to the frame while creating shape definition",
        do=[
            "No trouser break — any break shortens the leg further",
            "Monochromatic or tonal dressing to add visual height",
            "Slim-fit cuts — excess volume overwhelms a petite frame",
            "Ankle-length or cropped trousers to show the shoe",
            "Subtle vertical details to elongate",
        ],
        avoid=[
            "Large prints that overwhelm the frame",
            "Mid-calf hemlines that chop the leg",
            "Heavy layering",
            "Wide-leg trousers without height",
        ],
        trouser_break="none",
        kurta_length="hip",
        jacket_length="hip-length (never longer — shortens further)",
        belt_use="emphasise",
        layer_strategy=(
            "Keep outer layers short — hip-length at maximum. "
            "Long layers are the fastest way to shorten a petite frame."
        ),
    ),

    ("petite", "triangle"): ProportionRules(
        height="petite",
        body_shape="triangle",
        visual_goal="Build shoulder presence without adding height-reducing volume",
        do=[
            "Structured shoulders to broaden and lift the eye upward",
            "No trouser break",
            "Short jackets — hip-length only — to avoid cutting the frame",
            "Ankle-length trousers to maximise leg length",
        ],
        avoid=[
            "Mid-calf or longer hemlines",
            "Very wide-leg trousers — disproportionate at petite height",
            "Dropped shoulders",
        ],
        trouser_break="none",
        kurta_length="hip",
        jacket_length="hip-length only",
        belt_use="avoid",
        layer_strategy=(
            "A structured blazer or bandhgala at hip length is ideal — "
            "adds shoulder and stops at the right point."
        ),
    ),

    ("petite", "inverted_triangle"): ProportionRules(
        height="petite",
        body_shape="inverted_triangle",
        visual_goal="Balance wide shoulders without losing precious frame height",
        do=[
            "No trouser break — adds maximum leg length",
            "V-neck to reduce chest breadth visually",
            "Slightly tapered trousers — shows the ankle, adds length",
            "Hip-length kurtas — any longer and height is lost",
            "Darker tones on top to reduce emphasis",
        ],
        avoid=[
            "Long kurtas or jackets — counter-productive at petite height",
            "Wide-leg trousers that shorten the leg",
            "Shoulder padding or epaulettes",
        ],
        trouser_break="none",
        kurta_length="hip",
        jacket_length="hip-length only",
        belt_use="optional",
        layer_strategy=(
            "Avoid extra layers on top. If layering is needed, keep it short "
            "and slim — a nehru jacket at hip length at most."
        ),
    ),

    ("petite", "oval"): ProportionRules(
        height="petite",
        body_shape="oval",
        visual_goal=(
            "Elongate the silhouette vertically while managing midsection volume — "
            "height is the primary tool"
        ),
        do=[
            "No trouser break — critical",
            "Monochromatic dressing from head to toe in dark or neutral tones",
            "Vertical lines wherever possible — placket, seam, stripe",
            "Long open layers — a longline open jacket elongates IF it ends no lower than knee",
            "Slim-leg trousers, not wide-leg",
        ],
        avoid=[
            "Any waist marking — belts, waist bands, cinching",
            "Cropped tops",
            "Large prints that visually expand",
            "Mid-calf hemlines that cut the leg at its widest",
        ],
        trouser_break="none",
        kurta_length="hip to mid-thigh (never below knee — shortens)",
        jacket_length="hip-length maximum",
        belt_use="avoid",
        layer_strategy=(
            "One vertical layer in the same tonal family. "
            "Nothing that breaks the line at the midsection."
        ),
    ),

    ("petite", "trapezoid"): ProportionRules(
        height="petite",
        body_shape="trapezoid",
        visual_goal="Use height-extending techniques to maximise the naturally balanced frame",
        do=[
            "No trouser break — every millimetre of leg counts",
            "Monochromatic or tonal dressing to add visual height",
            "Well-fitted cuts — petite height needs precision, not volume",
            "Ankle-length trousers with a slim shoe",
        ],
        avoid=[
            "Mid-calf hemlines",
            "Heavy layering that adds bulk",
            "Oversized silhouettes",
        ],
        trouser_break="none",
        kurta_length="hip",
        jacket_length="hip-length",
        belt_use="optional",
        layer_strategy=(
            "Short, fitted outer layer only. Height is the limiting constraint — "
            "any long layer costs visual leg length."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_proportion_rules(height: str, body_shape: str) -> ProportionRules:
    """Return the proportion rules for a height × body_shape combination.

    Args:
        height: "tall" / "average" / "petite" (case-insensitive).
        body_shape: BodyShape value string (case-insensitive).

    Returns:
        ProportionRules dataclass.

    Raises:
        ValueError: If the combination is not in the matrix.
    """
    key = (height.lower().strip(), body_shape.lower().strip())
    if key not in _MATRIX:
        raise ValueError(
            f"No proportion rules for height='{height}', body_shape='{body_shape}'. "
            f"Valid heights: tall, average, petite. "
            f"Valid shapes: rectangle, triangle, inverted_triangle, oval, trapezoid."
        )
    return _MATRIX[key]


def proportion_context_string(height: str, body_shape: str) -> str:
    """Return a formatted multi-line string for injection into the recommendation prompt.

    Returns an empty string rather than raising if inputs are invalid.

    Args:
        height: Height estimate.
        body_shape: Body shape value.

    Returns:
        Formatted proportion rules string.
    """
    try:
        rules = get_proportion_rules(height, body_shape)
    except ValueError:
        return ""

    do_lines   = "\n".join(f"    · {item}" for item in rules.do)
    avoid_lines = "\n".join(f"    · {item}" for item in rules.avoid)

    return (
        f"Goal: {rules.visual_goal}\n"
        f"  Do:\n{do_lines}\n"
        f"  Avoid:\n{avoid_lines}\n"
        f"  Trouser break  : {rules.trouser_break}\n"
        f"  Kurta length   : {rules.kurta_length}\n"
        f"  Jacket length  : {rules.jacket_length}\n"
        f"  Belt use       : {rules.belt_use}\n"
        f"  Layer strategy : {rules.layer_strategy}"
    )


def pattern_scale_recommendation(
    build: str,
    height: str,
    garment_zone: str = "upper",
) -> str:
    """Return print scale guidance based on physical frame.

    Args:
        build: "slim" / "lean" / "athletic" / "average" / "broad" / "stocky".
        height: "tall" / "average" / "petite".
        garment_zone: "upper" / "lower" / "full" — which garment zone the print is on.

    Returns:
        One of: "small_print" / "medium_print" / "large_print".
    """
    build  = build.lower().strip()
    height = height.lower().strip()

    broad_builds = {"broad", "stocky", "athletic"}
    slim_builds  = {"slim", "lean"}

    if height == "petite" or build in slim_builds:
        return "small_print"
    if height == "tall" and build in broad_builds:
        return "large_print"
    return "medium_print"


def fabric_texture_recommendation(
    body_shape: str,
    occasion: str = "",
) -> dict[str, str]:
    """Return fabric texture guidance for a body shape and occasion.

    Args:
        body_shape: BodyShape value string.
        occasion: Occasion string (informational only, used for commentary).

    Returns:
        Dict with keys: "recommended_texture", "avoid_texture", "why".
    """
    shape = body_shape.lower().strip()

    texture_map: dict[str, dict[str, str]] = {
        "rectangle": {
            "recommended_texture": "structured matte or subtle texture",
            "avoid_texture": "very shiny or reflective fabrics",
            "why": (
                "Textured and structured fabrics add visual interest and apparent definition "
                "to a straight frame. Shine adds width, which works if width is the goal, "
                "but can remove the shape illusion you're building."
            ),
        },
        "triangle": {
            "recommended_texture": "structured matte on top, plain matte below",
            "avoid_texture": "heavily textured or patterned bottoms",
            "why": (
                "Texture and pattern on the upper body builds visual mass where you need it "
                "(shoulders). Plain, matte bottoms reduce hip emphasis."
            ),
        },
        "inverted_triangle": {
            "recommended_texture": "matte top, soft texture or subtle pattern below",
            "avoid_texture": "heavy texture or embellishment on the shoulders and chest",
            "why": (
                "Textured or embellished uppers add visual mass to an already-wide shoulder. "
                "Softer texture below creates balance."
            ),
        },
        "oval": {
            "recommended_texture": "matte, structured fabrics with drape",
            "avoid_texture": "clingy, shiny, or heavily textured fabrics",
            "why": (
                "Matte and structured fabrics skim and drape — they don't cling or reflect "
                "light onto the midsection. Clingy or shiny fabrics emphasise volume."
            ),
        },
        "trapezoid": {
            "recommended_texture": "most textures work — choose for occasion",
            "avoid_texture": "excessive texture in both top and bottom simultaneously",
            "why": (
                "A balanced frame handles texture well. The caution is doubling up — "
                "heavy texture everywhere adds bulk without purpose."
            ),
        },
    }

    return texture_map.get(shape, {
        "recommended_texture": "structured matte",
        "avoid_texture": "clingy or overly shiny fabrics",
        "why": "Matte structured fabrics are the safest default across body types.",
    })
