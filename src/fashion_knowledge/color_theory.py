"""Color theory rules for South Asian and Western skin undertones.

Provides palette lookups and clash detection used by the recommendation engine.
"""

from dataclasses import dataclass, field

from src.models.user_profile import SkinUndertone


# ---------------------------------------------------------------------------
# Palette definitions
# ---------------------------------------------------------------------------

_PALETTES: dict[SkinUndertone, dict[str, list[str]]] = {
    SkinUndertone.WARM: {
        "do": [
            "rust", "terracotta", "camel", "warm beige", "mustard", "peach",
            "coral", "warm red", "burnt orange", "olive green", "warm brown",
            "cream", "gold",
        ],
        "avoid": [
            "cool grey", "icy white", "lavender", "cobalt blue", "cool pink", "silver",
        ],
    },
    SkinUndertone.COOL: {
        "do": [
            "navy", "burgundy", "cool grey", "emerald", "cobalt", "cool white",
            "rose", "mauve", "icy blue", "charcoal", "silver", "cool teal",
        ],
        "avoid": [
            "warm yellows", "orange", "rust", "warm beige", "gold",
        ],
    },
    SkinUndertone.NEUTRAL: {
        "do": [
            "muted rust", "muted navy", "soft grey", "dusty rose", "warm taupe",
            "desaturated teal", "soft burgundy", "stone", "sage", "blush",
        ],
        "avoid": [
            "neon yellow", "neon orange", "electric blue", "hot pink",
        ],
    },
    SkinUndertone.DEEP_WARM: {
        "do": [
            "sapphire", "emerald", "deep burgundy", "royal purple", "warm earth tones",
            "gold", "rust", "deep teal", "forest green", "rich burgundy",
        ],
        "avoid": [
            "pastel pink", "pastel yellow", "pastel blue", "pastel lavender",
            "neon", "very light neutrals", "cream",
        ],
    },
    SkinUndertone.DEEP_COOL: {
        "do": [
            "jewel tones", "cobalt blue", "fuchsia", "royal purple", "silver",
            "cool emerald", "icy white", "deep teal", "charcoal",
        ],
        "avoid": [
            "rust", "warm earth tones", "gold", "warm orange", "camel",
        ],
    },
    SkinUndertone.OLIVE_WARM: {
        "do": [
            "warm earth tones", "muted greens", "warm tans", "terracotta",
            "deep blues", "mustard", "rust", "forest green", "warm navy",
        ],
        "avoid": [
            "nude beige", "cool pastels", "stark white", "icy pink",
        ],
    },
}

# Colors that commonly clash when combined (bidirectional pairs)
_CLASH_PAIRS: list[frozenset[str]] = [
    frozenset({"rust", "cool grey"}),
    frozenset({"terracotta", "cobalt blue"}),
    frozenset({"mustard", "lavender"}),
    frozenset({"orange", "pink"}),
    frozenset({"red", "green"}),  # unless deliberate Christmas-style contrast
    frozenset({"yellow", "purple"}),
    frozenset({"icy white", "warm beige"}),
    frozenset({"neon yellow", "neon pink"}),
    frozenset({"royal purple", "warm orange"}),
]

# Monochromatic family groupings — same family = no clash
_MONO_FAMILIES: list[set[str]] = [
    {"navy", "cobalt", "icy blue", "denim blue", "deep blue"},
    {"rust", "terracotta", "burnt orange", "warm orange", "coral"},
    {"burgundy", "deep burgundy", "wine", "maroon"},
    {"emerald", "forest green", "olive green", "sage"},
    {"charcoal", "cool grey", "slate", "silver"},
    {"camel", "warm beige", "warm tan", "sand"},
    {"ivory", "cream", "warm cream", "off-white"},
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class ColorPalette:
    """Resolved palette for a given undertone."""

    undertone: SkinUndertone
    do: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)


def get_palette(undertone: SkinUndertone) -> ColorPalette:
    """Return the do/avoid color palette for a given skin undertone.

    Args:
        undertone: The user's skin undertone enum value.

    Returns:
        ColorPalette with do and avoid lists.
    """
    entry = _PALETTES[undertone]
    return ColorPalette(
        undertone=undertone,
        do=list(entry["do"]),
        avoid=list(entry["avoid"]),
    )


def palette_do(undertone: SkinUndertone) -> list[str]:
    """Return the recommended colors for the given undertone."""
    return list(_PALETTES[undertone]["do"])


def palette_avoid(undertone: SkinUndertone) -> list[str]:
    """Return the colors to avoid for the given undertone."""
    return list(_PALETTES[undertone]["avoid"])


def is_clash(color_a: str, color_b: str) -> bool:
    """Return True if the two colors are a known clashing pair.

    Monochromatic pairings within the same color family are never flagged as
    clashes even if their raw strings differ.

    Args:
        color_a: First color (lowercase, descriptive string).
        color_b: Second color (lowercase, descriptive string).

    Returns:
        True if this is a clashing combination.
    """
    a, b = color_a.lower().strip(), color_b.lower().strip()
    if a == b:
        return False

    # Monochromatic — same family never clashes
    for family in _MONO_FAMILIES:
        if a in family and b in family:
            return False

    return frozenset({a, b}) in {p for p in _CLASH_PAIRS}


def detect_clashes(colors: list[str]) -> list[tuple[str, str]]:
    """Return all clashing color pairs from a list of outfit colors.

    Args:
        colors: List of color strings present in the outfit.

    Returns:
        List of (color_a, color_b) tuples that clash.
    """
    clashes: list[tuple[str, str]] = []
    normalized = [c.lower().strip() for c in colors]
    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            if is_clash(normalized[i], normalized[j]):
                clashes.append((normalized[i], normalized[j]))
    return clashes


def is_undertone_color_appropriate(color: str, undertone: SkinUndertone) -> bool:
    """Return True if a color is in the do-list for the given undertone.

    Args:
        color: The color to evaluate (lowercase).
        undertone: The user's skin undertone.

    Returns:
        True if the color is recommended for this undertone.
    """
    return color.lower().strip() in _PALETTES[undertone]["do"]


def recommended_print_scale(build: str) -> str:
    """Return print scale recommendation based on build/frame size.

    Small frame = small prints; large frame = larger prints.

    Args:
        build: User build string (slim / lean / athletic / average / broad / stocky).

    Returns:
        Recommendation string.
    """
    small_builds = {"slim", "lean", "petite"}
    large_builds = {"broad", "stocky", "athletic"}
    b = build.lower().strip()
    if b in small_builds:
        return "small-scale prints only — large patterns overwhelm the frame"
    if b in large_builds:
        return "medium to large prints work well — avoid micro-prints that read as texture"
    return "medium-scale prints are safest — most proportions work"
