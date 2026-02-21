"""Prompt templates for per-photo profile analysis during onboarding.

Each photo type gets a specific prompt optimised to extract the most useful
attributes from that angle and subject matter.
"""

PHOTO_1_FACE_FRONT = """You are an expert AI stylist and physiognomist. Analyse this face photo (front-facing, close-up).

Extract and return ONLY this JSON. No markdown. No explanations.

{
  "skin_undertone": "<warm|cool|neutral|deep_warm|deep_cool|olive_warm>",
  "skin_tone_depth": "<light|medium|wheatish|tan|deep>",
  "skin_texture_visible": "<smooth|textured|oily|dry|combination>",
  "face_shape": "<oval|square|round|oblong|heart|diamond>",
  "jaw_type": "<strong|soft|angular|rounded>",
  "forehead": "<broad|average|narrow>",
  "beard_style": "<clean shaven|stubble|short|full|patchy>",
  "beard_density": "<none|patchy|medium|dense>",
  "beard_color": "<color>",
  "mustache_style": "<none|natural|pencil|handlebar>",
  "beard_grooming_quality": "<well groomed|average|unkempt|not applicable>",
  "eyebrow_shape": "<natural|thick|thin|arched|flat>",
  "confidence_scores": {
    "skin_undertone": <0.0-1.0>,
    "face_shape": <0.0-1.0>,
    "skin_tone_depth": <0.0-1.0>
  }
}

SKIN UNDERTONE GUIDE:
- warm: golden/yellow base, looks good in earth tones
- cool: pink/blue base, looks good in jewel tones
- neutral: balanced — suits both
- deep_warm: warm undertone with deep skin (common South Asian)
- deep_cool: cool undertone with deep skin
- olive_warm: wheatish with warm base (common South Asian)

Be confident and specific. Return ONLY the JSON."""

PHOTO_2_FACE_SIDE = """You are an expert AI stylist. Analyse this side-profile face photo.

Extract and return ONLY this JSON. No markdown.

{
  "jaw_structure_depth": "<prominent|moderate|subtle>",
  "facial_depth": "<deep|moderate|flat>",
  "beard_density_jawline": "<none|sparse|medium|dense>",
  "neck_proportions": "<long|average|short>",
  "nose_profile": "<straight|aquiline|upturned|rounded>",
  "confidence_scores": {
    "jaw_structure_depth": <0.0-1.0>,
    "neck_proportions": <0.0-1.0>
  }
}

Return ONLY the JSON."""

PHOTO_3_BODY_FRONT = """You are an expert AI stylist. Analyse this full-body front-facing photo.

Extract and return ONLY this JSON. No markdown.

{
  "body_shape": "<rectangle|triangle|inverted_triangle|oval|trapezoid>",
  "height_estimate": "<tall|average|petite>",
  "build": "<slim|lean|athletic|average|broad|stocky>",
  "shoulder_width": "<narrow|average|broad>",
  "torso_length": "<short|average|long>",
  "leg_proportion": "<short|average|long>",
  "current_outfit_style": "<casual|smart casual|formal|ethnic|streetwear|athletic>",
  "current_color_palette": ["<color1>", "<color2>"],
  "fit_preference_observed": "<slim|regular|relaxed|oversized>",
  "confidence_scores": {
    "body_shape": <0.0-1.0>,
    "height_estimate": <0.0-1.0>,
    "build": <0.0-1.0>
  }
}

BODY SHAPE GUIDE:
- rectangle: shoulders ≈ hips, no defined waist
- triangle: hips wider than shoulders
- inverted_triangle: shoulders wider than hips
- oval: midsection widest point
- trapezoid: slightly wider shoulders, slight taper — most common male shape

Return ONLY the JSON."""

PHOTO_4_BODY_SIDE = """You are an expert AI stylist. Analyse this full-body side-profile photo.

Extract and return ONLY this JSON. No markdown.

{
  "posture": "<upright|slight forward lean|rounded shoulders|military straight>",
  "belly_profile": "<flat|slight|moderate|prominent>",
  "back_proportions": "<straight|curved|athletic>",
  "build_depth": "<slim|average|broad>",
  "confidence_scores": {
    "posture": <0.0-1.0>,
    "belly_profile": <0.0-1.0>
  }
}

Return ONLY the JSON."""

PHOTO_5_REAL_OUTFIT = """You are an expert AI stylist. Analyse this real-world outfit photo.

Extract and return ONLY this JSON. No markdown.

{
  "style_vocabulary": "<the dominant style: indian_traditional|western_casual|western_formal|ethnic_fusion|streetwear|smart_casual|athletic>",
  "formality_default": "<casual|smart casual|formal|very formal>",
  "primary_colors_worn": ["<color1>", "<color2>", "<color3>"],
  "accessory_habits": ["<accessory type the person wears>"],
  "footwear_type_seen": "<type of shoe visible>",
  "fit_preference": "<slim|regular|relaxed|oversized>",
  "overall_grooming_impression": "<well groomed|average|needs improvement>",
  "hair_visible": {
    "hair_color": "<color>",
    "hair_texture": "<straight|wavy|curly|coily>",
    "hair_density": "<thin|medium|thick>",
    "current_haircut_style": "<description>",
    "haircut_length": "<short|medium|long>",
    "hair_visible_condition": "<healthy|frizzy|oily|dry>"
  },
  "confidence_scores": {
    "style_vocabulary": <0.0-1.0>,
    "formality_default": <0.0-1.0>
  }
}

Return ONLY the JSON."""


PHOTO_CATEGORISATION_PROMPT = """Look at this image carefully.

What type of photo is this?

Return exactly ONE word from the list below — no other text, no punctuation, no explanation:

face_front    — close-up of a face looking directly at the camera
face_side     — face photographed from the side (profile view)
body_front    — full or half body shown from the front
body_side     — full or half body shown from the side
outfit        — a real-world outfit photo (indoor/outdoor, any angle, any formality)
unclear       — none of the above, or unable to determine

Return only the single word."""


def get_photo_prompt(photo_number: int) -> str:
    """Return the vision prompt for a given onboarding photo number (1–5).

    Args:
        photo_number: Photo index 1–5.

    Returns:
        Prompt string.

    Raises:
        ValueError: If photo_number is not 1–5.
    """
    prompts = {
        1: PHOTO_1_FACE_FRONT,
        2: PHOTO_2_FACE_SIDE,
        3: PHOTO_3_BODY_FRONT,
        4: PHOTO_4_BODY_SIDE,
        5: PHOTO_5_REAL_OUTFIT,
    }
    if photo_number not in prompts:
        raise ValueError(f"Photo number must be 1–5, got {photo_number}")
    return prompts[photo_number]
