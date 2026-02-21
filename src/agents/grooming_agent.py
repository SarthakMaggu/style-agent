"""Grooming agent — generates hair, beard, eyebrow, and skincare recommendations.

Combines rule-based knowledge from grooming_guide.py with an optional
Claude API call for additional nuance (mocked in tests).

The rule-based path is always executed and provides the core output.
The Claude API call enriches the output when available.
"""

import json
import logging
from typing import Any

from src.fashion_knowledge.grooming_guide import (
    get_beard_rules,
    get_eyebrow_recommendation,
    get_haircut_rules,
    score_beard_grooming,
)
from src.models.grooming import GroomingProfile
from src.models.remark import Remark, RemarkCategory
from src.models.user_profile import FaceShape, UserProfile
from src.prompts.recommendations import GROOMING_ANALYSIS_PROMPT
from src.services.anthropic_service import call_text, parse_json_response

logger = logging.getLogger(__name__)


def generate_grooming_profile(
    user_profile: UserProfile,
    use_api: bool = True,
) -> GroomingProfile:
    """Generate a GroomingProfile from user profile attributes.

    Uses rule-based knowledge as the primary source. If use_api=True, enriches
    the output with a Claude API call.

    Args:
        user_profile: The user's permanent profile.
        use_api: Whether to call Claude API for additional nuance.

    Returns:
        GroomingProfile with hair, beard, eyebrow, and skin recommendations.
    """
    face_shape = user_profile.face_shape
    beard_grooming_quality = user_profile.beard_grooming_quality

    haircut_rules = get_haircut_rules(face_shape)
    beard_rules = get_beard_rules(face_shape)
    eyebrow_rec = get_eyebrow_recommendation(face_shape)
    grooming_score = score_beard_grooming(beard_grooming_quality)

    # Build rule-based grooming profile
    current_haircut = user_profile.current_haircut_style
    recommended_haircut = (
        haircut_rules.recommended[0] if haircut_rules.recommended else "Standard cut"
    )
    haircut_to_avoid = (
        haircut_rules.avoid[0] if haircut_rules.avoid else "No specific cuts to avoid"
    )

    recommended_beard = (
        beard_rules.recommended[0] if beard_rules.recommended else "Maintain current style"
    )
    beard_to_avoid = (
        beard_rules.avoid[0] if beard_rules.avoid else "No specific styles to avoid"
    )

    # Generate grooming remarks
    grooming_remarks = _build_grooming_remarks(
        user_profile, haircut_rules, beard_rules, grooming_score
    )

    if use_api:
        try:
            grooming_profile = _enrich_with_api(
                user_profile=user_profile,
                current_haircut=current_haircut,
                recommended_haircut=recommended_haircut,
                haircut_to_avoid=haircut_to_avoid,
                recommended_beard=recommended_beard,
                beard_to_avoid=beard_to_avoid,
                eyebrow_rec=eyebrow_rec,
                grooming_score=grooming_score,
                grooming_remarks=grooming_remarks,
            )
            return grooming_profile
        except Exception as exc:
            logger.warning("API grooming enrichment failed — using rule-based output: %s", exc)

    # Rule-based fallback (also primary path when use_api=False)
    return GroomingProfile(
        current_haircut_assessment=(
            f"{current_haircut} — {haircut_rules.notes}"
            if haircut_rules.notes
            else current_haircut
        ),
        recommended_haircut=recommended_haircut,
        haircut_to_avoid=haircut_to_avoid,
        styling_product_recommendation=_default_styling_products(user_profile),
        hair_color_recommendation="Maintain natural color" if not user_profile.hair_color else f"Keep {user_profile.hair_color}",
        current_beard_assessment=(
            f"{user_profile.beard_style} beard — {beard_rules.notes}"
            if beard_rules.notes
            else user_profile.beard_style
        ),
        recommended_beard_style=recommended_beard,
        beard_grooming_tips=beard_rules.recommended[:3],
        beard_style_to_avoid=beard_to_avoid,
        eyebrow_assessment="Natural",
        eyebrow_recommendation=eyebrow_rec,
        visible_skin_concerns=[],
        skincare_categories_needed=["moisturiser", "SPF"],
        grooming_score=grooming_score,
        grooming_remarks=grooming_remarks,
    )


def _enrich_with_api(
    user_profile: UserProfile,
    current_haircut: str,
    recommended_haircut: str,
    haircut_to_avoid: str,
    recommended_beard: str,
    beard_to_avoid: str,
    eyebrow_rec: str,
    grooming_score: int,
    grooming_remarks: list[Remark],
) -> GroomingProfile:
    """Call Claude API to enrich the grooming profile with contextual nuance."""
    context = (
        f"Face shape: {user_profile.face_shape.value}\n"
        f"Current haircut: {current_haircut}\n"
        f"Beard style: {user_profile.beard_style}\n"
        f"Beard grooming quality: {user_profile.beard_grooming_quality}\n"
        f"Hair texture: {user_profile.hair_texture}\n"
        f"Hair density: {user_profile.hair_density}\n"
        f"Rule-based recommendation: {recommended_haircut}\n"
        f"Rule-based beard: {recommended_beard}"
    )

    prompt = f"USER CONTEXT:\n{context}\n\n{GROOMING_ANALYSIS_PROMPT}"
    raw = call_text(prompt)
    data = parse_json_response(raw)

    # Parse grooming_remarks from API response
    api_remarks = []
    for r in data.get("grooming_remarks", []):
        try:
            api_remarks.append(Remark(
                severity=r.get("severity", "minor"),
                category=RemarkCategory(r.get("category", "grooming_hair")),
                body_zone=r.get("body_zone", "head"),
                element=r.get("element", "hair"),
                issue=r.get("issue", ""),
                fix=r.get("fix", ""),
                why=r.get("why", ""),
                priority_order=int(r.get("priority_order", 99)),
            ))
        except (ValueError, KeyError):
            pass

    remarks = api_remarks if api_remarks else grooming_remarks

    return GroomingProfile(
        current_haircut_assessment=data.get("current_haircut_assessment", current_haircut),
        recommended_haircut=data.get("recommended_haircut", recommended_haircut),
        haircut_to_avoid=data.get("haircut_to_avoid", haircut_to_avoid),
        styling_product_recommendation=data.get("styling_product_recommendation", []),
        hair_color_recommendation=data.get("hair_color_recommendation", "Maintain natural"),
        current_beard_assessment=data.get("current_beard_assessment", user_profile.beard_style),
        recommended_beard_style=data.get("recommended_beard_style", recommended_beard),
        beard_grooming_tips=data.get("beard_grooming_tips", []),
        beard_style_to_avoid=data.get("beard_style_to_avoid", beard_to_avoid),
        eyebrow_assessment=data.get("eyebrow_assessment", "Natural"),
        eyebrow_recommendation=data.get("eyebrow_recommendation", eyebrow_rec),
        visible_skin_concerns=data.get("visible_skin_concerns", []),
        skincare_categories_needed=data.get("skincare_categories_needed", ["moisturiser", "SPF"]),
        grooming_score=int(data.get("grooming_score", grooming_score)),
        grooming_remarks=remarks,
    )


def _build_grooming_remarks(
    user_profile: UserProfile,
    haircut_rules: Any,
    beard_rules: Any,
    grooming_score: int,
) -> list[Remark]:
    """Build rule-based grooming remarks."""
    remarks: list[Remark] = []
    order = 1

    # Unkempt beard is always a moderate remark
    if user_profile.beard_grooming_quality == "unkempt":
        remarks.append(Remark(
            severity="moderate",
            category=RemarkCategory.GROOMING_BEARD,
            body_zone="face",
            element="beard",
            issue="Beard is unkempt — needs grooming before next public appearance",
            fix="Trim, shape, and moisturise beard. Use a beard comb.",
            why="Grooming quality affects overall perceived effort and professionalism.",
            priority_order=order,
        ))
        order += 1

    # Low grooming score generates a note
    if grooming_score <= 4:
        remarks.append(Remark(
            severity="moderate",
            category=RemarkCategory.GROOMING_HAIR,
            body_zone="head",
            element="hair",
            issue="Hair appears unmaintained — a fresh cut would significantly elevate the look",
            fix="Book a haircut this week. Ask for: " + (haircut_rules.recommended[0] if haircut_rules.recommended else "a style suited to your face shape"),
            why="Hair is the most noticed grooming element after the face.",
            priority_order=order,
        ))
        order += 1

    return remarks


def _default_styling_products(user_profile: UserProfile) -> list[str]:
    """Return default styling product recommendations based on hair texture."""
    texture = user_profile.hair_texture.lower()
    density = user_profile.hair_density.lower()

    products = []
    if "straight" in texture:
        products.append("matte clay" if "thick" in density else "light pomade")
    elif "wavy" in texture:
        products.append("curl-enhancing cream")
    elif "curly" in texture or "coily" in texture:
        products.extend(["curl cream", "leave-in conditioner"])

    products.append("SPF moisturiser for scalp")
    return products
