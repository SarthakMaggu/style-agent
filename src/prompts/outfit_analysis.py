"""Prompt templates for outfit vision analysis.

Returns structured JSON matching OutfitBreakdown, AccessoryAnalysis, and FootwearAnalysis models.
"""

OUTFIT_ANALYSIS_PROMPT = """You are an expert AI personal stylist. Analyse this outfit photo with extreme precision.

Return a JSON object that EXACTLY matches this structure. No additional keys. No markdown.

{
  "occasion_detected": "<auto-detected occasion from the outfit>",
  "occasion_requested": "<OCCASION_PLACEHOLDER>",
  "occasion_match": <true|false>,
  "items": [
    {
      "category": "<top|bottom|outerwear|layer|inner|ethnic-top|ethnic-bottom|full-garment>",
      "garment_type": "<specific garment name, e.g. kurta, oxford shirt, chinos>",
      "color": "<specific color name>",
      "pattern": "<solid|stripes|checks|floral|geometric|embroidered|printed|textured>",
      "fabric_estimate": "<estimated fabric, e.g. cotton, linen, silk>",
      "fit": "<slim|regular|relaxed|oversized|straight|tailored>",
      "length": "<e.g. hip|mid-thigh|below-knee|ankle|cropped|full-length>",
      "collar_type": "<collar type or n/a>",
      "sleeve_type": "<sleeve type or n/a>",
      "condition": "<excellent|good|worn|scuffed|creased>",
      "occasion_appropriate": <true|false>,
      "issue": "<specific issue or empty string if none>",
      "fix": "<specific fix or empty string if none>"
    }
  ],
  "accessory_analysis": {
    "items_detected": [
      {
        "type": "<watch|ring|bracelet|necklace|chain|pendant|belt|bag|sunglasses|hat|cap|turban|pagdi|pocket_square|tie|tie_pin|cufflinks|earring>",
        "color": "<color>",
        "material_estimate": "<estimated material>",
        "style_category": "<casual|formal|traditional|statement|sport>",
        "condition": "<condition>",
        "occasion_appropriate": <true|false>,
        "issue": "<issue or empty string>",
        "fix": "<fix or empty string>"
      }
    ],
    "missing_accessories": ["<list of accessories that would improve this look>"],
    "accessories_to_remove": ["<list of accessories that should be removed>"],
    "accessory_harmony": "<assessment of accessory harmony>",
    "overall_score": <1-10>
  },
  "footwear_analysis": {
    "visible": <true|false>,
    "type": "<footwear type or empty string if not visible>",
    "color": "<color or empty string>",
    "material_estimate": "<material or empty string>",
    "condition": "<clean|scuffed|dirty|worn out|sole peeling|yellowed sole or empty string>",
    "style_category": "<style or empty string>",
    "occasion_match": <true|false>,
    "outfit_match": <true|false>,
    "issue": "<issue or empty string>",
    "recommended_instead": "<alternative or empty string>",
    "shoe_care_note": "<care note or empty string>"
  },
  "overall_color_harmony": "<assessment>",
  "color_clash_detected": <true|false>,
  "silhouette_assessment": "<assessment>",
  "proportion_assessment": "<assessment>",
  "formality_level": <1-10>,
  "outfit_score": <1-10>
}

RULES:
- Detect EVERY visible garment, layer, and accessory. Miss nothing.
- For footwear: if feet are not visible, set visible=false and leave other footwear fields empty.
- Be specific about colors — not "blue" but "navy blue" or "cobalt blue".
- occasion_detected: pick from: indian_formal, indian_casual, ethnic_fusion, western_business_formal, western_business_casual, western_streetwear, smart_casual, party, wedding_guest_indian, festival, travel, gym, beach, lounge
- Return ONLY the JSON object. No explanation. No markdown fences.
"""


def build_outfit_prompt(occasion: str = "auto") -> str:
    """Build the outfit analysis prompt with the requested occasion.

    Args:
        occasion: Occasion string or "auto" for auto-detection.

    Returns:
        Complete prompt string.
    """
    return OUTFIT_ANALYSIS_PROMPT.replace("OCCASION_PLACEHOLDER", occasion)
