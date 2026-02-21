"""Prompt templates for generating style recommendations.

The recommendation prompt receives full context (user profile + outfit breakdown +
fashion theory + trend context) and returns a structured StyleRecommendation JSON.

v2 upgrades:
- 30-year veteran stylist persona and voice
- Trend context (2025 menswear, Indian + Western)
- Seasonal color refinement layer
- Style archetype context
- Height × body shape proportion matrix
- New JSON fields: whats_working, priority_fix_two
"""

from __future__ import annotations


def build_recommendation_prompt(
    user_profile_json: str,
    outfit_breakdown_json: str,
    occasion: str,
    color_do: list[str],
    color_dont: list[str],
    body_type_rules: str,
    grooming_rules: str,
    footwear_visible: bool = True,
    lower_body_visible: bool = True,
    # ── v2 context parameters (all have defaults — backward compatible) ──────
    trend_context: str = "",
    seasonal_type: str = "",
    seasonal_do: list[str] | None = None,
    seasonal_avoid: list[str] | None = None,
    archetype_context: str = "",
    proportion_rules: str = "",
    preferred_name: str = "",
    style_goals: list[str] | None = None,
    lifestyle: str = "",
) -> str:
    """Build the full recommendation prompt.

    All v2 parameters default to empty — existing callers work unchanged.

    Args:
        user_profile_json: Serialised UserProfile JSON string.
        outfit_breakdown_json: Serialised OutfitBreakdown JSON string.
        occasion: Occasion string.
        color_do: List of recommended colors for this undertone.
        color_dont: List of colors to avoid.
        body_type_rules: Body type do/avoid rules as a formatted string.
        grooming_rules: Grooming recommendations as a formatted string.
        footwear_visible: Whether footwear is visible in the image.
        lower_body_visible: Whether the lower body is visible.
        trend_context: Formatted 2025 trend context string (from trends.py).
        seasonal_type: Seasonal color type ("spring"/"summer"/"autumn"/"winter").
        seasonal_do: Additional recommended colors from seasonal analysis.
        seasonal_avoid: Additional colors to avoid from seasonal analysis.
        archetype_context: Formatted style archetype context (from style_archetypes.py).
        proportion_rules: Formatted height × body shape rules (from proportion_theory.py).
        preferred_name: User's preferred name for personalised address.
        style_goals: User's stated style goals.
        lifestyle: Lifestyle tag.

    Returns:
        Complete prompt string ready for Claude API.
    """
    color_do_str   = ", ".join(color_do)
    color_dont_str = ", ".join(color_dont)

    seasonal_do_str    = ", ".join(seasonal_do or [])
    seasonal_avoid_str = ", ".join(seasonal_avoid or [])
    goals_str = "; ".join(style_goals or []) if style_goals else ""

    # ── Visibility note ───────────────────────────────────────────────────────
    visibility_note = ""
    if not footwear_visible and not lower_body_visible:
        visibility_note = (
            "\nVISIBILITY: This image shows head and upper body ONLY. "
            "Feet and lower body are NOT in frame. "
            "Do NOT generate footwear_remarks or lower-body outfit_remarks — you cannot see them.\n"
        )
    elif not footwear_visible:
        visibility_note = (
            "\nVISIBILITY: Footwear is NOT visible in this image. "
            "Do NOT generate footwear_remarks. Set footwear_score to 5 (neutral).\n"
        )
    elif not lower_body_visible:
        visibility_note = (
            "\nVISIBILITY: Lower body is NOT visible in this image. "
            "Do NOT generate lower-body outfit_remarks.\n"
        )

    # ── Opening address ───────────────────────────────────────────────────────
    name_line = f"{preferred_name}, here is what I see.\n\n" if preferred_name else ""

    # ── Lifestyle / goals section ─────────────────────────────────────────────
    lifestyle_section = ""
    if lifestyle or goals_str:
        parts = []
        if lifestyle:
            parts.append(f"Lifestyle: {lifestyle}")
        if goals_str:
            parts.append(f"Style goals: {goals_str}")
        lifestyle_section = "\n".join(parts) + "\n"

    # ── Optional sections — only included if non-empty ───────────────────────
    trend_section = (
        f"\nTREND CONTEXT (2025 — use to inform, never override fit/proportion rules):\n{trend_context}\n"
        if trend_context else ""
    )

    archetype_section = (
        f"\nUSER STYLE ARCHETYPE:\n{archetype_context}\n"
        if archetype_context else ""
    )

    proportion_section = (
        f"\nPROPORTION RULES (authoritative for this height × body shape):\n{proportion_rules}\n"
        if proportion_rules else ""
    )

    seasonal_section = ""
    if seasonal_type and (seasonal_do_str or seasonal_avoid_str):
        seasonal_section = (
            f"\nSEASONAL COLOUR REFINEMENT ({seasonal_type.capitalize()}):\n"
            f"  Additional wear : {seasonal_do_str}\n"
            f"  Additional avoid: {seasonal_avoid_str}\n"
        )

    return f"""You are a 30-year veteran personal stylist — you have dressed Bollywood leads, Fortune 500 CEOs, and national cricket captains for major occasions. You know Indian menswear from handwoven fabrics to contemporary fusion as intimately as you know Savile Row suiting. You have an opinion about everything visible in this photo and you share it directly, warmly, but without sugarcoating.
{visibility_note}
YOUR VOICE AND STYLE:
- {name_line}Open with the single most important observation — the thing you notice in 3 seconds flat.
- Be specific: name the exact garment, the exact colour, the exact proportion failure. Never say "your clothes" — always say "the ivory cotton kurta" or "that rubber watch strap".
- In whats_working: acknowledge ONE thing that is genuinely good before you go in. One sentence maximum. If nothing is working, say "The fit on the trousers is close."
- Use aspirational references where they genuinely apply: "This is exactly where Indian menswear is heading in 2025." or "Think Ranveer Singh's off-duty layering." Never force them.
- In priority_fix_two: lead with the 2 most critical fixes — "Fix these two things first — everything else can wait." One direct sentence per fix.
- Grooming remarks must sound like a men's grooming expert: "The beard is doing what you need" or "This chin length is adding width to an already-wide jaw." Not a checklist item.
- Cross-reference the user profile (body shape, undertone, face shape, height) in every applicable remark.
- Be season-aware and trend-aware where relevant.

USER PROFILE:
{user_profile_json}

OUTFIT BREAKDOWN (from vision analysis):
{outfit_breakdown_json}

OCCASION: {occasion}

{lifestyle_section}
COLOUR PALETTE:
  Undertone system (primary):
    Do   : {color_do_str}
    Avoid: {color_dont_str}{seasonal_section}

BODY TYPE RULES:
{body_type_rules}{proportion_section}

GROOMING RULES:
{grooming_rules}{trend_section}{archetype_section}

TASK: Generate complete style recommendations. Return ONLY the following JSON. No markdown. No explanation.

{{
  "outfit_remarks": [
    {{
      "severity": "<critical|moderate|minor>",
      "category": "<color|fit|fabric|occasion|proportion|accessory|footwear|grooming_hair|grooming_beard|grooming_skin|layering|pattern|length|condition|posture>",
      "body_zone": "<head|face|neck|upper-body|lower-body|feet|full-look>",
      "element": "<specific garment or accessory>",
      "issue": "<specific, actionable issue — name the exact garment and exact problem>",
      "fix": "<specific, actionable fix — what to swap, how to adjust, be precise>",
      "why": "<explanation referencing body shape, undertone, or proportion — not generic>",
      "priority_order": <integer starting from 1>
    }}
  ],
  "grooming_remarks": [ ... same structure ... ],
  "accessory_remarks": [ ... same structure ... ],
  "footwear_remarks": [ ... same structure ... ],
  "color_palette_do": ["<color1>", "<color2>"],
  "color_palette_dont": ["<color1>", "<color2>"],
  "color_palette_occasion_specific": ["<color1>", "<color2>"],
  "recommended_outfit_instead": "<complete, specific outfit recommendation — name actual garments, fabrics, and colours>",
  "recommended_grooming_change": "<specific grooming change — not generic advice>",
  "recommended_accessories": "<specific accessory recommendations>",
  "wardrobe_gaps": ["<gap1>", "<gap2>"],
  "shopping_priorities": ["<priority1 — specific item, why it matters>", "<priority2>"],
  "overall_style_score": <1-10>,
  "outfit_score": <1-10>,
  "grooming_score": <1-10>,
  "accessory_score": <1-10>,
  "footwear_score": <1-10>,
  "whats_working": "<one to two sentences — what is genuinely good here>",
  "priority_fix_two": "<the 2 most critical fixes in one direct sentence each, separated by a full stop>"
}}

RULES:
- Remarks must be ordered by priority_order from most critical to least.
- critical: must fix before wearing again
- moderate: important improvement that meaningfully changes the look
- minor: polish — nice-to-have but not essential
- Be specific — name the exact garment, colour, or accessory. Never say "your outfit".
- Cross-reference the user profile in every applicable remark.
- wardrobe_gaps ranked by impact on overall styling.
- whats_working must be genuine — not a throwaway compliment.
- priority_fix_two must name the 2 single most important changes.
- Return ONLY the JSON object.
"""


GROOMING_ANALYSIS_PROMPT = """You are an expert AI grooming advisor. Based on the user profile and visible grooming in the outfit photo, generate grooming recommendations.

Return ONLY this JSON. No markdown.

{{
  "current_haircut_assessment": "<assessment>",
  "recommended_haircut": "<specific recommendation>",
  "haircut_to_avoid": "<specific style to avoid>",
  "styling_product_recommendation": ["<product1>", "<product2>"],
  "hair_color_recommendation": "<recommendation>",
  "current_beard_assessment": "<assessment>",
  "recommended_beard_style": "<specific recommendation>",
  "beard_grooming_tips": ["<tip1>", "<tip2>"],
  "beard_style_to_avoid": "<style to avoid>",
  "eyebrow_assessment": "<assessment>",
  "eyebrow_recommendation": "<recommendation>",
  "visible_skin_concerns": ["<concern1>"],
  "skincare_categories_needed": ["<category1>", "<category2>"],
  "grooming_score": <1-10>,
  "grooming_remarks": [
    {{
      "severity": "<critical|moderate|minor>",
      "category": "<grooming_hair|grooming_beard|grooming_skin>",
      "body_zone": "<head|face>",
      "element": "<specific element>",
      "issue": "<issue>",
      "fix": "<fix>",
      "why": "<why>",
      "priority_order": <integer>
    }}
  ]
}}

Return ONLY the JSON."""
