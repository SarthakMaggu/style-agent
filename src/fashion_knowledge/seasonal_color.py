"""Seasonal color analysis — Spring / Summer / Autumn / Winter.

Extends the undertone-based color theory in color_theory.py with a second layer
of refinement. Each seasonal type carries its own curated palette, fabric finish
guidance, and intensity descriptor.

Usage:
    from src.fashion_knowledge.seasonal_color import derive_seasonal_type, seasonal_palette_do

    season = derive_seasonal_type(SkinUndertone.DEEP_WARM, "tan", "black")
    colours = seasonal_palette_do(season)  # → ["rust", "burnt orange", ...]
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.user_profile import SkinUndertone


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class SeasonalType:
    """Complete descriptor for a seasonal color type."""

    season: str
    """One of: "spring" / "summer" / "autumn" / "winter"."""

    description: str
    """Short human-readable label, e.g. "Warm, clear, light"."""

    characteristics: str
    """Typical skin + hair + tone combination for this season."""

    intensity: str
    """e.g. "light and clear" / "deep and muted" / "deep and rich" / "cool and soft"."""

    palette_do: list[str] = field(default_factory=list)
    """Colors this season wears best."""

    palette_avoid: list[str] = field(default_factory=list)
    """Colors that fight this season's natural coloring."""

    fabric_finishes: list[str] = field(default_factory=list)
    """Recommended fabric surface qualities: "matte" / "soft sheen" / "jewel sheen" / "clear"."""


# ---------------------------------------------------------------------------
# Seasonal definitions
# ---------------------------------------------------------------------------

_SEASONS: dict[str, SeasonalType] = {
    "spring": SeasonalType(
        season="spring",
        description="Warm, clear, light",
        characteristics=(
            "Warm or neutral undertone with light to medium skin depth. "
            "Hair typically medium to light brown, golden, or warm black."
        ),
        intensity="light and clear",
        palette_do=[
            "peach", "coral", "warm ivory", "golden yellow", "warm turquoise",
            "bright coral red", "camel", "warm salmon", "light warm brown",
            "golden tan", "grass green", "warm sky blue", "clear orange",
        ],
        palette_avoid=[
            "cool grey", "muted navy", "dark burgundy", "cool white", "black",
            "mauve", "dusty rose", "forest green", "icy lavender",
        ],
        fabric_finishes=["soft sheen", "clear", "lightweight matte"],
    ),

    "summer": SeasonalType(
        season="summer",
        description="Cool, muted, light",
        characteristics=(
            "Cool or neutral undertone with light to medium skin depth. "
            "Hair often light to medium ash or cool brown."
        ),
        intensity="cool and soft",
        palette_do=[
            "dusty rose", "mauve", "powder blue", "soft lavender", "cool grey",
            "slate blue", "dusty teal", "soft white", "muted pink", "periwinkle",
            "cool taupe", "light sage", "cool beige",
        ],
        palette_avoid=[
            "warm orange", "rust", "camel", "warm gold", "bright coral",
            "warm brown", "mustard", "tomato red", "warm olive",
        ],
        fabric_finishes=["matte", "soft sheen", "jersey"],
    ),

    "autumn": SeasonalType(
        season="autumn",
        description="Warm, muted, deep",
        characteristics=(
            "Warm undertone (warm, deep_warm, or olive_warm) with medium to deep skin. "
            "Hair dark brown, warm black, or deep auburn. Common in South Asian coloring."
        ),
        intensity="deep and muted",
        palette_do=[
            "rust", "terracotta", "burnt orange", "deep olive", "warm brown",
            "camel", "mustard", "warm khaki", "forest green", "warm teal",
            "brick red", "warm burgundy", "cognac", "dark chocolate",
            "gold", "deep peach",
        ],
        palette_avoid=[
            "icy white", "cool grey", "pastel blue", "cool pink", "lavender",
            "bright cobalt", "cool silver", "stark black",
        ],
        fabric_finishes=["matte", "textured matte", "soft nap"],
    ),

    "winter": SeasonalType(
        season="winter",
        description="Cool, clear, deep",
        characteristics=(
            "Cool undertone (cool or deep_cool) with medium to deep skin. "
            "Hair dark, often jet black or very dark brown. High contrast overall."
        ),
        intensity="deep and rich",
        palette_do=[
            "true black", "bright white", "navy", "royal blue", "emerald",
            "deep burgundy", "fuchsia", "sapphire", "cool red", "charcoal",
            "icy pink", "cobalt", "deep purple", "cool magenta",
        ],
        palette_avoid=[
            "warm orange", "camel", "rust", "warm beige", "warm gold",
            "muted earth tones", "warm olive", "peach",
        ],
        fabric_finishes=["jewel sheen", "clear", "structured matte"],
    ),
}


# ---------------------------------------------------------------------------
# Decision matrix
# ---------------------------------------------------------------------------

def derive_seasonal_type(
    undertone: SkinUndertone,
    skin_tone_depth: str,
    hair_color: str,
) -> str:
    """Map undertone + skin depth + hair color to a seasonal type string.

    Decision matrix:
    ─────────────────────────────────────────────────────────────────
    DEEP_WARM (any depth, any hair)   → autumn
    OLIVE_WARM (any depth, any hair)  → autumn
    DEEP_COOL (any depth, any hair)   → winter
    WARM + light/medium + light hair  → spring
    WARM + deep/tan/wheatish          → autumn
    COOL + light/medium               → summer
    COOL + deep/tan/wheatish          → winter
    NEUTRAL + light                   → summer
    NEUTRAL + medium/deep/tan         → autumn
    ─────────────────────────────────────────────────────────────────

    Args:
        undertone: SkinUndertone enum value.
        skin_tone_depth: "light" / "medium" / "wheatish" / "tan" / "deep"
        hair_color: Free-form string — checked for warm vs dark/cool keywords.

    Returns:
        Season string: "spring" / "summer" / "autumn" / "winter".
    """
    depth = skin_tone_depth.lower().strip()
    deep_depths = {"tan", "deep", "wheatish"}
    light_depths = {"light", "medium"}

    hair_lower = hair_color.lower()
    light_hair_keywords = ("blonde", "light", "golden", "auburn", "red", "brown")
    is_light_hair = any(kw in hair_lower for kw in light_hair_keywords)

    match undertone:
        case SkinUndertone.DEEP_WARM:
            return "autumn"
        case SkinUndertone.OLIVE_WARM:
            return "autumn"
        case SkinUndertone.DEEP_COOL:
            return "winter"
        case SkinUndertone.WARM:
            if depth in light_depths and is_light_hair:
                return "spring"
            return "autumn"
        case SkinUndertone.COOL:
            if depth in light_depths:
                return "summer"
            return "winter"
        case SkinUndertone.NEUTRAL:
            if depth in light_depths:
                return "summer"
            return "autumn"
        case _:
            # Unknown undertone — default to autumn (most common in South Asian)
            return "autumn"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_seasonal_palette(season: str) -> SeasonalType:
    """Return the SeasonalType dataclass for the given season string.

    Args:
        season: "spring" / "summer" / "autumn" / "winter" (case-insensitive).

    Returns:
        SeasonalType with full palette and descriptor.

    Raises:
        ValueError: If season is not a recognised value.
    """
    key = season.lower().strip()
    if key not in _SEASONS:
        raise ValueError(
            f"Unknown season '{season}'. "
            "Must be one of: spring, summer, autumn, winter."
        )
    return _SEASONS[key]


def seasonal_palette_do(season: str) -> list[str]:
    """Return the recommended color list for the given seasonal type.

    Args:
        season: Season string.

    Returns:
        List of recommended color names.
    """
    return get_seasonal_palette(season).palette_do


def seasonal_palette_avoid(season: str) -> list[str]:
    """Return the colors to avoid for the given seasonal type.

    Args:
        season: Season string.

    Returns:
        List of color names to avoid.
    """
    return get_seasonal_palette(season).palette_avoid


def seasonal_context_string(season: str) -> str:
    """Return a formatted string block for injection into the recommendation prompt.

    Args:
        season: Season string.

    Returns:
        Multi-line string describing the seasonal type and its palette.
    """
    if not season:
        return ""
    try:
        st = get_seasonal_palette(season)
    except ValueError:
        return ""

    do_str   = "  ·  ".join(c.capitalize() for c in st.palette_do[:8])
    avoid_str = "  ·  ".join(c.capitalize() for c in st.palette_avoid[:6])
    return (
        f"Seasonal type: {st.season.capitalize()} ({st.description})\n"
        f"  Wear : {do_str}\n"
        f"  Avoid: {avoid_str}\n"
        f"  Fabric finish: {', '.join(st.fabric_finishes)}"
    )
