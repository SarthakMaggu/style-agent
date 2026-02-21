"""Style archetypes — 7 categories covering Indian and Western menswear.

Each archetype carries signature pieces, color approach, fit preference, upgrade
moves, pitfalls, celebrity references, and grooming alignment. This knowledge is
injected into the recommendation prompt to make Claude's advice archetype-aware.

Usage:
    from src.fashion_knowledge.style_archetypes import get_archetype, archetype_context_string

    arch = get_archetype("ethnic_traditional")
    context = archetype_context_string("smart_casual")
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class StyleArchetype:
    """Complete descriptor for one style archetype."""

    name: str
    """Archetype identifier string."""

    description: str
    """One-sentence description of this archetype's philosophy."""

    signature_pieces: list[str] = field(default_factory=list)
    """Indian and Western pieces central to this archetype."""

    color_approach: str = ""
    """How this archetype handles color — muted / bold / monochromatic / tonal."""

    fit_default: str = ""
    """Typical fit preference: slim / regular / relaxed / oversized."""

    occasions_natural_fit: list[str] = field(default_factory=list)
    """Occasions this archetype dresses effortlessly."""

    upgrade_moves: list[str] = field(default_factory=list)
    """Specific actions to elevate this archetype without losing its identity."""

    pitfalls: list[str] = field(default_factory=list)
    """Where this archetype typically goes wrong."""

    celebrity_reference: str = ""
    """A named Indian or global figure who embodies this archetype well."""

    grooming_alignment: str = ""
    """How grooming should reinforce this archetype."""


# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------

_ARCHETYPES: dict[str, StyleArchetype] = {

    "classic": StyleArchetype(
        name="classic",
        description=(
            "Timeless, conservative, and precise — quality over trend, "
            "fit over flash."
        ),
        signature_pieces=[
            "Well-tailored suit (navy, charcoal, mid-grey)",
            "Crisp oxford shirt",
            "Bandhgala suit for Indian formal occasions",
            "Slim-cut dark chinos",
            "Leather Oxford or Derby shoe (polished)",
            "Simple leather watch with a classic case",
            "Silk pocket square (white or muted)",
        ],
        color_approach=(
            "Muted, restrained palette — navy, charcoal, camel, cream, white. "
            "No more than 2-3 colors in any outfit. Patterns minimal and classic "
            "(fine stripe, fine check)."
        ),
        fit_default="slim to tailored",
        occasions_natural_fit=[
            "western_business_formal", "western_business_casual",
            "indian_formal", "smart_casual",
        ],
        upgrade_moves=[
            "Invest in one suit that is made-to-measure — fit is where classic wins",
            "A tan or cognac leather watch strap elevates without shouting",
            "Move from polyester to wool or wool-blend for suiting",
            "Add a silk pocket square in a muted tone — not a printed one",
            "Upgrade shoe quality before any other piece — classic lives in the details",
        ],
        pitfalls=[
            "Wearing classic pieces in bad fit — defeats the entire purpose",
            "Overdoing the formality for the occasion — classic should be appropriate, not costumey",
            "Forgetting that classic needs regular grooming — stubble, neat hair, clean shoes are non-negotiable",
            "Playing it so safe it becomes boring — one considered accent piece lifts it",
        ],
        celebrity_reference=(
            "Think Rahul Dravid's off-duty look — precise, understated, confident. "
            "Or Anil Kapoor's formal appearances — never overdressed, always exactly right."
        ),
        grooming_alignment=(
            "Clean shave or very short, well-maintained stubble. "
            "Classic short haircut — taper, side part, or neat crop. "
            "Grooming must match the precision of the clothing."
        ),
    ),

    "streetwear": StyleArchetype(
        name="streetwear",
        description=(
            "Culture-led, expressive, and brand-aware — drawing from music, sport, "
            "and youth subculture."
        ),
        signature_pieces=[
            "Graphic tee (quality print, not fast-fashion)",
            "Cargo trousers or utility pants",
            "Clean, well-maintained sneakers (condition is critical)",
            "Oversized hoodies or tech fleece",
            "Statement outerwear — bomber, MA-1 jacket",
            "Streetwear-appropriate accessories: caps, chains, crossbody",
            "Jordans, Dunks, or clean technical runners",
        ],
        color_approach=(
            "Bold color blocking or careful monochromatic. "
            "Neutrals (black, white, grey, tan) as base; "
            "one color accent worn deliberately — not accidentally."
        ),
        fit_default="relaxed to oversized",
        occasions_natural_fit=[
            "western_streetwear", "casual", "travel", "party",
        ],
        upgrade_moves=[
            "Sneaker condition is non-negotiable — dirty sneakers undermine everything else",
            "Move from printed logos to clean, design-led pieces",
            "Proportion matters even in streetwear — oversized top + slim/tapered base",
            "One statement piece per outfit — not three simultaneously",
            "Invest in one piece at a time: better one quality sneaker than five mediocre",
        ],
        pitfalls=[
            "Wearing too many statement pieces at once — the eye has nowhere to rest",
            "Ignoring fit entirely — relaxed is intentional, sloppy is not",
            "Dirty or scuffed sneakers — this is the fastest credibility killer in streetwear",
            "Wearing heavy graphics with heavy graphics — clashing visual noise",
            "Treating the Indian weather as an afterthought — layering needs heat management",
        ],
        celebrity_reference=(
            "Think Ranveer Singh's off-duty — fearless with color and proportion, "
            "but always considered. Or A$AP Rocky's editorial streetwear — intentional at every level."
        ),
        grooming_alignment=(
            "Grooming is part of the look here. "
            "Fade, textured crop, or a defined shape — nothing accidental. "
            "Beard: short and precise, or clean shaven. "
            "Jewellery is part of the grooming: rings, chains are intentional accessories."
        ),
    ),

    "ethnic_traditional": StyleArchetype(
        name="ethnic_traditional",
        description=(
            "Rooted in Indian craft and tradition — prioritising fabric quality, "
            "artisan techniques, and occasion appropriateness."
        ),
        signature_pieces=[
            "Chanderi or silk-cotton kurta",
            "Raw silk or brocade sherwani for wedding occasions",
            "Churidar or straight-cut salwar",
            "Mojaris, juttis, or kolhapuris",
            "Bandhgala jacket as smart ethnic formal",
            "Handblock print or handloom kurta for casual ethnic",
            "Classic pagdi or safa for wedding occasions",
        ],
        color_approach=(
            "Rich, warm jewel tones for formal — emerald, burgundy, sapphire, deep gold. "
            "Earthy, handwoven tones for casual — natural dyes, block print palettes. "
            "Avoid Western-style pastels and neons in traditional pieces."
        ),
        fit_default="regular to relaxed",
        occasions_natural_fit=[
            "indian_formal", "indian_casual", "wedding_guest_indian",
            "festival", "ethnic_fusion",
        ],
        upgrade_moves=[
            "Fabric quality is the single biggest upgrade — move from polyester to cotton, chanderi, or silk-blend",
            "Invest in one quality pair of footwear (mojaris or juttis) — they transform any kurta",
            "Understand which collar style suits your face shape (bandhgala, nehru, mandarin)",
            "Appropriate kurta length for your height and body shape is non-negotiable",
            "One quality piece of Indian jewellery or a classic watch elevates the look",
        ],
        pitfalls=[
            "Mismatching fabric weights within an outfit — silk kurta with cotton churidar reads cheap",
            "Ignoring kurta length for your height and body shape",
            "Wrong footwear language — leather oxford with sherwani, rubber chappal with wedding kurta",
            "Formality mismatch — cotton casual kurta at a formal occasion",
            "Over-embellishment — more embroidery is not always more formal",
        ],
        celebrity_reference=(
            "Think Virat Kohli at BCCI events — understated, well-fitted, fabric-first. "
            "Or Nawazuddin Siddiqui at award functions — quality kurtas, precise fit, quiet confidence."
        ),
        grooming_alignment=(
            "Clean, well-maintained beard or clean shave. "
            "Ethnic formal demands neat grooming — stubble should be defined, not accidental. "
            "Hair: well-set and clean. Avoid very modern cuts with traditional formal — "
            "a classic cut or slicked-back look suits the occasion better."
        ),
    ),

    "smart_casual": StyleArchetype(
        name="smart_casual",
        description=(
            "The most versatile archetype — elevated enough for professional settings, "
            "relaxed enough to feel human."
        ),
        signature_pieces=[
            "Clean chinos (olive, navy, stone, tan)",
            "Oxford or OCBD shirt — solid or fine check",
            "Loafers (leather or suede — no rubber sport soles)",
            "Structured polo or high-quality jersey",
            "Slim-fit dark jeans (no distressing for smart end)",
            "Leather or suede Chelsea boots",
            "Unstructured linen or cotton blazer",
        ],
        color_approach=(
            "Tonal, muted, but not dull. "
            "Navy + white, olive + beige, grey + cream — "
            "two complementary colors. Accent with one muted tone."
        ),
        fit_default="slim to regular",
        occasions_natural_fit=[
            "smart_casual", "western_business_casual",
            "indian_casual", "ethnic_fusion", "travel",
        ],
        upgrade_moves=[
            "Move from generic brands to quality basics — the fabric shows",
            "Introduce one interesting texture per outfit: a linen blazer, a suede loafer",
            "Well-fitted chinos are the backbone — invest in two pairs that fit perfectly",
            "A leather watch strap over a rubber one immediately raises the formality dial",
            "Shoes: the one place to spend more — they anchor the entire smart-casual look",
        ],
        pitfalls=[
            "Mixing too many casual signals at once — denim + hoodie + trainers is casual, not smart-casual",
            "Ignoring shoe quality — scuffed shoes undermine everything above them",
            "Treating smart-casual as an excuse for poor fit",
            "Over-ironed or stiff-looking pieces — smart-casual should feel effortless",
        ],
        celebrity_reference=(
            "Think Mahendra Singh Dhoni's airport look — relaxed, quality fabrics, "
            "no unnecessary logos. Or Benedict Cumberbatch's press-day casualwear — "
            "it always looks considered, never overdone."
        ),
        grooming_alignment=(
            "This archetype needs tidy, well-maintained grooming — "
            "not formal, but certainly not neglected. "
            "A medium beard is fine if well-shaped. "
            "Hair should look intentional, not accidental."
        ),
    ),

    "avant_garde": StyleArchetype(
        name="avant_garde",
        description=(
            "Experimental, design-led, and convention-defying — "
            "wears ideas as much as garments."
        ),
        signature_pieces=[
            "Deconstructed or asymmetric silhouettes",
            "Strong, unexpected color combinations",
            "Oversized or exaggerated proportions",
            "Statement outerwear as the centrepiece",
            "Unusual textures: bonded, raw-edged, washed",
            "Minimal or no visible branding",
            "Fashion-forward ethnic fusion: dhoti pants with structured jackets",
        ],
        color_approach=(
            "Bold and intentional — monochromatic all-black, "
            "unexpected complementary pairs, or deliberate tonal clashing. "
            "Color is always a decision, never an accident."
        ),
        fit_default="oversized to experimental",
        occasions_natural_fit=[
            "party", "creative_professional", "fashion_events", "travel",
        ],
        upgrade_moves=[
            "Ground experimental pieces with one anchor — clean shoes, a simple base",
            "Understand proportion before you break it — rules exist before they can be subverted",
            "One statement piece per outfit — let it be the conversation, not a chorus",
            "Invest in quality even in experimental pieces — construction shows",
        ],
        pitfalls=[
            "Looking chaotic rather than considered — avant-garde requires more thought, not less",
            "Wrong occasion — this archetype is context-dependent",
            "Prioritising the look over comfort and function at inappropriate moments",
            "Ignoring grooming — avant-garde style with accidental grooming reads as neglect",
        ],
        celebrity_reference=(
            "Think Ranveer Singh's award-season looks — deliberate provocation, "
            "always a point of view. Or Billy Porter — nothing accidental, every element intentional."
        ),
        grooming_alignment=(
            "Grooming is part of the statement here. "
            "A long, styled beard or a bold haircut reinforces the archetype. "
            "Or a completely clean look as contrast to the clothing — the juxtaposition is the point."
        ),
    ),

    "athletic": StyleArchetype(
        name="athletic",
        description=(
            "Function-first, performance-aware, and increasingly elevated — "
            "athleisure done with intention."
        ),
        signature_pieces=[
            "Performance joggers or track trousers (tailored, not boxy)",
            "Clean technical runners or court shoes",
            "Quality jersey or fleece in neutral tones",
            "Structured athletic jacket (not a cheap windbreaker)",
            "Compression or fitted base layers under casual layers",
            "Quarter-zip or half-zip technical top",
            "Minimal accessories — clean watch, no-logo cap",
        ],
        color_approach=(
            "Tonal neutrals — black, grey, white, navy. "
            "One color accent: a single clean color in the shoe or outer layer."
        ),
        fit_default="regular to slim",
        occasions_natural_fit=[
            "gym", "travel", "casual", "western_streetwear",
        ],
        upgrade_moves=[
            "Move from sports brands to performance-lifestyle brands for elevated pieces",
            "Tailored track trousers over baggy gym shorts — the single biggest upgrade",
            "Shoe condition is everything in athletic — clean shoes, every time",
            "One quality technical jacket over a hoodie for the gym-to-street transition",
        ],
        pitfalls=[
            "Wearing gym wear to non-gym settings without elevation",
            "Logos and branding everywhere simultaneously",
            "Dirty shoes — the fastest way to look unintentional",
            "Wearing athletic exclusively when the occasion calls for more formality",
        ],
        celebrity_reference=(
            "Think Kohli's training-day outfits — clean, quality athleisure, minimal logos. "
            "Or David Beckham's sportswear — elevated basics with excellent fit."
        ),
        grooming_alignment=(
            "Short, maintained haircut — fade or crop. "
            "Beard: short and defined, or clean shaven. "
            "Athletic archetype and long unkempt grooming are at odds. "
            "The physical appearance of the face should match the deliberateness of the look."
        ),
    ),

    "eclectic": StyleArchetype(
        name="eclectic",
        description=(
            "Genre-fluid and culturally layered — mixing Indian and Western, "
            "vintage and contemporary, with deliberate confidence."
        ),
        signature_pieces=[
            "Kurta over slim Western trousers",
            "Ethnic print shirt with tailored chinos",
            "Bandhgala jacket over a Western shirt and denim",
            "Vintage-inspired piece as the hero of an otherwise modern look",
            "Mix of Indian and Western accessories",
        ],
        color_approach=(
            "Bold but cohesive — the tonal story still needs to be told across the mix. "
            "Ethnic colours paired with Western neutrals to prevent visual chaos."
        ),
        fit_default="regular — varied by piece",
        occasions_natural_fit=[
            "ethnic_fusion", "smart_casual", "party", "festival",
        ],
        upgrade_moves=[
            "Anchor each outfit with one neutral piece to ground the mix",
            "Ensure there is a clear tonal story even across different styles",
            "Footwear must make a language decision — Indian or Western, not both simultaneously",
            "Resist adding too many elements — three considered pieces, not six",
        ],
        pitfalls=[
            "Mixing styles without a coherent tonal or visual story",
            "Wearing three statement pieces simultaneously — too much",
            "Ethnic top with sportswear bottoms — this fusion doesn't work",
            "Not considering footwear language — shoes must commit to one register",
        ],
        celebrity_reference=(
            "Think Saif Ali Khan's casual appearances — easy fusion that looks effortless. "
            "Or Farhan Akhtar's festival outfits — Indian and Western elements in genuine dialogue."
        ),
        grooming_alignment=(
            "Medium length, well-maintained styling. "
            "Eclectic archetype can support a more distinctive hair or beard choice — "
            "but it must be maintained, not accidental."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_archetype(archetype: str) -> StyleArchetype | None:
    """Return the StyleArchetype for the given archetype name.

    Args:
        archetype: Archetype name string (case-insensitive).

    Returns:
        StyleArchetype dataclass, or None if not found.
    """
    return _ARCHETYPES.get(archetype.lower().strip())


def all_archetype_names() -> list[str]:
    """Return all defined archetype name strings."""
    return list(_ARCHETYPES.keys())


def archetype_context_string(archetype: str) -> str:
    """Return a formatted multi-line string for injection into the recommendation prompt.

    Returns an empty string if the archetype is unknown or empty.

    Args:
        archetype: Archetype name string.

    Returns:
        Formatted archetype context block.
    """
    if not archetype:
        return ""

    arch = get_archetype(archetype)
    if arch is None:
        return ""

    upgrade_lines = "\n".join(f"    · {u}" for u in arch.upgrade_moves[:4])
    pitfall_lines = "\n".join(f"    · {p}" for p in arch.pitfalls[:3])

    return (
        f"Archetype: {arch.name.replace('_', ' ').title()}\n"
        f"  {arch.description}\n\n"
        f"  Color approach : {arch.color_approach}\n"
        f"  Fit default    : {arch.fit_default}\n\n"
        f"  Upgrade moves:\n{upgrade_lines}\n\n"
        f"  Watch out for:\n{pitfall_lines}\n\n"
        f"  Reference     : {arch.celebrity_reference}\n"
        f"  Grooming      : {arch.grooming_alignment}"
    )
