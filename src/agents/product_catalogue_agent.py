"""ProductCatalogueAgent — generates a per-user curated product catalogue.

Called once at onboarding time (after the UserProfile is complete). Sends the
full profile to Claude and receives back 12–15 ``ProductEntry`` objects covering
every wardrobe, footwear, accessory, grooming, and skincare category relevant to
this specific user.

The catalogue is stored at ``~/.style-agent/product_catalogue.json`` and loaded
at analysis time to populate the SHOP section of the editorial output image.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

from src.models.product import ProductCatalogue, ProductEntry, ProductTier
from src.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

_CATALOGUE_SYSTEM = """You are a 30-year veteran personal stylist and wardrobe consultant.
You know Indian menswear, Western menswear, grooming, skincare, and accessories in depth.
You return only valid JSON. No markdown, no explanation, no extra text."""

_CATALOGUE_PROMPT_TEMPLATE = """Given the user profile below, generate a curated product catalogue
with 12–15 entries covering the highest-impact categories for this specific person.

USER PROFILE:
{profile_json}

INSTRUCTIONS:
- Cover ALL of these category types: Indian garments, Western garments, footwear,
  watches, jewellery/accessories, grooming products (hair + beard), skincare.
- For every category, provide THREE tiers: high_street, designer, luxury.
- Use real Indian and international brand names relevant to the user's profile.
- Make recommendations specific to their undertone, body shape, face shape, build, and beard type.
- "search_query" must be a short (3–6 word) string the user can paste into Myntra/Amazon/ASOS.
- "why_for_you" must be ONE sentence, specific to their profile data (e.g. "Suits your warm
  undertone and inverted triangle shape — mid-thigh length balances shoulder width.").
- "price_range" in Indian Rupees (₹) for Indian brands, USD ($) for international.
- "occasion_relevance" should list relevant occasion slugs from:
  indian_formal, indian_casual, ethnic_fusion, office_western, smart_casual,
  party, wedding_guest_indian, festival, travel, gym, streetwear, beach, lounge.

Return a JSON array of 12–15 objects, each matching this schema exactly:
[
  {{
    "category": "Indian Formal Kurta",
    "occasion_relevance": ["indian_formal", "wedding_guest_indian"],
    "profile_reason": "No silk-blend kurta in wardrobe — highest single impact gap.",
    "high_street": {{
      "tier": "high_street",
      "brand": "Manyavar",
      "product_name": "Silk blend straight kurta in rust",
      "price_range": "₹3,000–6,000",
      "search_query": "manyavar silk kurta rust",
      "why_for_you": "Warm rust suits your deep warm undertone and reads correct formality."
    }},
    "designer": {{
      "tier": "designer",
      "brand": "FabIndia",
      "product_name": "Handwoven chanderi kurta in warm champagne",
      "price_range": "₹7,000–14,000",
      "search_query": "fabindia chanderi kurta champagne",
      "why_for_you": "Chanderi drape adds formality without heaviness — right for your athletic build."
    }},
    "luxury": {{
      "tier": "luxury",
      "brand": "Sabyasachi",
      "product_name": "Raw silk embroidered kurta, mid-thigh, custom fit",
      "price_range": "₹45,000–90,000",
      "search_query": "sabyasachi silk kurta bespoke",
      "why_for_you": "Bespoke mid-thigh length is essential for your inverted triangle — off-rack rarely fits correctly."
    }}
  }}
]

Return ONLY the JSON array. No markdown fences, no extra keys, no explanation."""


# ── Agent ─────────────────────────────────────────────────────────────────────

def generate_product_catalogue(
    profile: UserProfile,
    anthropic_api_key: str = "",
) -> ProductCatalogue | None:
    """Generate a personalised product catalogue from a completed UserProfile.

    Args:
        profile:          Completed user profile from onboarding.
        anthropic_api_key: API key. Falls back to ANTHROPIC_API_KEY env var.

    Returns:
        ProductCatalogue on success, None on failure (logs error).
    """
    import os
    key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        logger.error("ANTHROPIC_API_KEY not set — cannot generate product catalogue")
        return None

    if anthropic is None:
        logger.error("anthropic package not installed — cannot generate product catalogue")
        return None

    # Serialise profile (exclude None fields for cleaner prompt)
    profile_json = profile.model_dump_json(exclude_none=True)

    prompt = _CATALOGUE_PROMPT_TEMPLATE.format(profile_json=profile_json)

    try:
        client = anthropic.Anthropic(api_key=key)
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=_CATALOGUE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
    except Exception as exc:
        logger.error("Claude API call failed in ProductCatalogueAgent: %s", exc)
        return None

    # Parse JSON
    try:
        # Strip markdown fences if Claude wraps them anyway
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Product catalogue JSON parse failed: %s\nRaw: %s", exc, raw[:500])
        return None

    # Validate and construct models
    entries: list[ProductEntry] = []
    for item in data:
        try:
            entry = _parse_entry(item)
            if entry:
                entries.append(entry)
        except Exception as exc:
            logger.warning("Skipping malformed product entry: %s — %s", item.get("category"), exc)

    if not entries:
        logger.error("No valid product entries parsed from Claude response")
        return None

    catalogue = ProductCatalogue(
        profile_undertone=profile.skin_undertone.value,
        profile_body_shape=profile.body_shape.value,
        entries=entries,
        generated_at=datetime.now(timezone.utc).isoformat(),
        catalogue_version=1,
    )
    logger.info("Product catalogue generated: %d entries", len(entries))
    return catalogue


def _parse_entry(data: dict) -> ProductEntry | None:
    """Parse one raw dict into a ProductEntry. Returns None if invalid."""
    required = ("category", "occasion_relevance", "profile_reason",
                "high_street", "designer", "luxury")
    for key in required:
        if key not in data:
            logger.warning("ProductEntry missing key '%s'", key)
            return None

    def _parse_tier(td: dict) -> ProductTier:
        return ProductTier(
            tier=str(td.get("tier", "")),
            brand=str(td.get("brand", "")),
            product_name=str(td.get("product_name", "")),
            price_range=str(td.get("price_range", "")),
            search_query=str(td.get("search_query", "")),
            why_for_you=str(td.get("why_for_you", "")),
        )

    return ProductEntry(
        category=str(data["category"]),
        occasion_relevance=[str(o) for o in data["occasion_relevance"]],
        profile_reason=str(data["profile_reason"]),
        high_street=_parse_tier(data["high_street"]),
        designer=_parse_tier(data["designer"]),
        luxury=_parse_tier(data["luxury"]),
    )
