"""Recommendation agent — generates full StyleRecommendation by cross-referencing
UserProfile, OutfitBreakdown, and all fashion knowledge modules.

Pipeline:
1. Apply rule-based checks (color theory, body type, footwear, accessories)
2. Call Claude API for narrative recommendation + remark generation
3. Parse response into StyleRecommendation
4. Sort all remarks by priority_order
"""

import json
import logging
from typing import Any

from src.fashion_knowledge.accessory_guide import (
    bag_appropriate,
    belt_shoe_match,
    suggest_missing_accessories,
    watch_strap_appropriate,
)
from src.fashion_knowledge.body_types import get_do, get_avoid
from src.fashion_knowledge.color_theory import palette_avoid, palette_do
from src.fashion_knowledge.footwear_guide import assess_condition, is_footwear_appropriate
from src.fashion_knowledge.grooming_guide import (
    get_beard_rules,
    get_haircut_rules,
    get_eyebrow_recommendation,
)
from src.fashion_knowledge.indian_wear import (
    collar_face_compatible as indian_collar_face_compatible,
    fabric_appropriate_for_occasion,
    is_valid_fusion,
    kurta_length_recommendation,
)
from src.fashion_knowledge.western_wear import (
    collar_face_compatible as western_collar_face_compatible,
    trouser_break,
    trouser_shoe_appropriate,
    validate_layering,
)
from src.models.grooming import GroomingProfile
from src.models.outfit import OutfitBreakdown
from src.models.recommendation import StyleRecommendation
from src.models.remark import Remark, RemarkCategory
from src.models.user_profile import UserProfile
from src.prompts.recommendations import build_recommendation_prompt
from src.services.anthropic_service import call_text, parse_json_response

logger = logging.getLogger(__name__)


def generate_recommendation(
    user_profile: UserProfile,
    grooming_profile: GroomingProfile,
    outfit_breakdown: OutfitBreakdown,
    occasion: str,
    caricature_path: str = "",
    annotated_path: str = "",
    json_path: str = "",
    use_api: bool = True,
) -> StyleRecommendation:
    """Generate a complete StyleRecommendation.

    Args:
        user_profile: The user's permanent profile.
        grooming_profile: Generated grooming recommendations.
        outfit_breakdown: Vision-analysed outfit.
        occasion: Target occasion string.
        caricature_path: Path to generated caricature image.
        annotated_path: Path to annotated output image.
        json_path: Path to JSON output file.
        use_api: Whether to call Claude API for recommendations.

    Returns:
        StyleRecommendation with all fields populated.
    """
    # Build rule-based remarks
    rule_outfit_remarks = _build_outfit_remarks(user_profile, outfit_breakdown, occasion)
    rule_footwear_remarks = _build_footwear_remarks(outfit_breakdown, occasion)
    rule_accessory_remarks = _build_accessory_remarks(user_profile, outfit_breakdown, occasion)
    rule_grooming_remarks = list(grooming_profile.grooming_remarks)

    # Color palettes
    color_do = palette_do(user_profile.skin_undertone)
    color_dont = palette_avoid(user_profile.skin_undertone)

    if use_api:
        try:
            return _enrich_with_api(
                user_profile=user_profile,
                grooming_profile=grooming_profile,
                outfit_breakdown=outfit_breakdown,
                occasion=occasion,
                color_do=color_do,
                color_dont=color_dont,
                rule_outfit_remarks=rule_outfit_remarks,
                rule_footwear_remarks=rule_footwear_remarks,
                rule_accessory_remarks=rule_accessory_remarks,
                rule_grooming_remarks=rule_grooming_remarks,
                caricature_path=caricature_path,
                annotated_path=annotated_path,
                json_path=json_path,
            )
        except Exception as exc:
            logger.warning("API recommendation failed — using rule-based output: %s", exc)

    return _build_rule_based_recommendation(
        user_profile=user_profile,
        grooming_profile=grooming_profile,
        outfit_breakdown=outfit_breakdown,
        color_do=color_do,
        color_dont=color_dont,
        outfit_remarks=rule_outfit_remarks,
        footwear_remarks=rule_footwear_remarks,
        accessory_remarks=rule_accessory_remarks,
        grooming_remarks=rule_grooming_remarks,
        caricature_path=caricature_path,
        annotated_path=annotated_path,
        json_path=json_path,
    )


def _build_outfit_remarks(
    user_profile: UserProfile,
    outfit_breakdown: OutfitBreakdown,
    occasion: str,
) -> list[Remark]:
    """Build rule-based outfit remarks from color clashes, occasion mismatch, etc."""
    remarks: list[Remark] = []
    order = 1

    # Color clash
    if outfit_breakdown.color_clash_detected:
        remarks.append(Remark(
            severity="critical",
            category=RemarkCategory.COLOR,
            body_zone="full-look",
            element="colour palette",
            issue=f"Colour clash detected: {outfit_breakdown.overall_color_harmony}",
            fix=f"Switch to colours from your palette: {', '.join(palette_do(user_profile.skin_undertone)[:4])}",
            why="Clashing colours create visual noise and undermine the overall look.",
            priority_order=order,
        ))
        order += 1

    # Occasion mismatch
    if not outfit_breakdown.occasion_match:
        remarks.append(Remark(
            severity="critical",
            category=RemarkCategory.OCCASION,
            body_zone="full-look",
            element="outfit",
            issue=f"Outfit is dressed for {outfit_breakdown.occasion_detected} — occasion requires {occasion}",
            fix="Upgrade garments to match the occasion's formality and dress code.",
            why="Occasion mismatch signals a lack of awareness of dress codes.",
            priority_order=order,
        ))
        order += 1

    # Per-garment issues
    is_indian_occasion = any(k in occasion.lower() for k in (
        "indian", "ethnic", "fusion", "wedding_guest", "festival",
    ))
    is_western_occasion = any(k in occasion.lower() for k in (
        "western", "business", "streetwear", "smart_casual", "party",
        "office", "gym", "travel", "beach", "lounge",
    ))

    for garment in outfit_breakdown.items:
        body_zone = "upper-body" if garment.category in (
            "top", "ethnic-top", "outerwear", "layer", "inner", "full-garment",
        ) else "lower-body"

        # Vision-flagged issue
        if not garment.occasion_appropriate and garment.issue:
            remarks.append(Remark(
                severity="moderate",
                category=RemarkCategory.FABRIC,
                body_zone=body_zone,
                element=garment.garment_type,
                issue=garment.issue,
                fix=garment.fix,
                why="Each garment must match the occasion's fabric and formality expectations.",
                priority_order=order,
            ))
            order += 1

        # Fabric appropriateness for Indian occasions
        if is_indian_occasion and garment.fabric_estimate:
            ok, fabric_issue = fabric_appropriate_for_occasion(
                garment.fabric_estimate, occasion
            )
            if not ok and fabric_issue:
                remarks.append(Remark(
                    severity="moderate",
                    category=RemarkCategory.FABRIC,
                    body_zone=body_zone,
                    element=garment.garment_type,
                    issue=fabric_issue,
                    fix="Upgrade to chanderi, silk-cotton blend, or raw silk for this occasion.",
                    why="Fabric weight signals formality in Indian wear as much as the silhouette.",
                    priority_order=order,
                ))
                order += 1

        # Indian collar vs face shape
        if is_indian_occasion and garment.collar_type not in ("n/a", "", "none"):
            ok, collar_issue = indian_collar_face_compatible(
                garment.collar_type, user_profile.face_shape
            )
            if not ok and collar_issue:
                remarks.append(Remark(
                    severity="minor",
                    category=RemarkCategory.FIT,
                    body_zone="neck",
                    element=f"{garment.collar_type} collar",
                    issue=collar_issue,
                    fix=collar_issue,
                    why="Collar shape frames the face — the wrong choice emphasises unflattering proportions.",
                    priority_order=order,
                ))
                order += 1

        # Western collar vs face shape
        if is_western_occasion and garment.collar_type not in ("n/a", "", "none"):
            ok, collar_issue = western_collar_face_compatible(
                garment.collar_type, user_profile.face_shape
            )
            if not ok and collar_issue:
                remarks.append(Remark(
                    severity="minor",
                    category=RemarkCategory.FIT,
                    body_zone="neck",
                    element=f"{garment.collar_type} collar",
                    issue=collar_issue,
                    fix=collar_issue,
                    why="Collar shape frames the face — the wrong choice emphasises unflattering proportions.",
                    priority_order=order,
                ))
                order += 1

    # Kurta length vs height + body shape (Indian occasions)
    if is_indian_occasion:
        tops = [g for g in outfit_breakdown.items if g.category in (
            "top", "ethnic-top", "full-garment",
        )]
        if tops:
            length_rec = kurta_length_recommendation(
                user_profile.height_estimate, user_profile.body_shape
            )
            top = tops[0]
            # Flag only if current length is "hip" and recommendation says longer
            if top.length and "hip" in top.length.lower() and "mid-thigh" in length_rec.lower():
                remarks.append(Remark(
                    severity="moderate",
                    category=RemarkCategory.LENGTH,
                    body_zone="upper-body",
                    element=top.garment_type,
                    issue=f"Hip-length kurta cuts the silhouette at the widest point for your proportions.",
                    fix=length_rec,
                    why="Kurta length dramatically affects perceived body proportions — longer hem elongates.",
                    priority_order=order,
                ))
                order += 1

    # Trouser break for Western occasions
    if is_western_occasion:
        trousers = [g for g in outfit_breakdown.items if g.category in (
            "bottom", "ethnic-bottom",
        )]
        if trousers:
            break_rec = trouser_break(user_profile.height_estimate)
            trouser = trousers[0]
            if trouser.length and "full break" in trouser.length.lower():
                remarks.append(Remark(
                    severity="minor",
                    category=RemarkCategory.LENGTH,
                    body_zone="lower-body",
                    element=trouser.garment_type,
                    issue=f"Full trouser break is excessive for your height.",
                    fix=break_rec,
                    why="Trouser break affects the leg line — too much break shortens and puddles.",
                    priority_order=order,
                ))
                order += 1

        # Layering validation
        layers = [g for g in outfit_breakdown.items if g.category in (
            "outerwear", "layer",
        )]
        bases  = [g for g in outfit_breakdown.items if g.category in ("top", "inner")]
        if layers and bases:
            layer_issues = validate_layering(
                bases[0].fabric_estimate,
                layers[0].fabric_estimate,
                bases[0].fit,
                layers[0].fit,
            )
            for issue_str in layer_issues[:1]:  # max 1 layering remark
                remarks.append(Remark(
                    severity="minor",
                    category=RemarkCategory.LAYERING,
                    body_zone="upper-body",
                    element="layering",
                    issue=issue_str,
                    fix="Ensure outer layer is heavier fabric than base; outer fit should be slightly more relaxed.",
                    why="Layering should taper inward — base slimmest, outer most relaxed.",
                    priority_order=order,
                ))
                order += 1

    # Trouser-shoe pairing for Western occasions
    if is_western_occasion and outfit_breakdown.footwear_analysis.visible:
        trousers = [g for g in outfit_breakdown.items if g.category in ("bottom", "ethnic-bottom")]
        if trousers:
            shoe_ok, shoe_issue = trouser_shoe_appropriate(
                trousers[0].fit, outfit_breakdown.footwear_analysis.type
            )
            if not shoe_ok and shoe_issue:
                remarks.append(Remark(
                    severity="minor",
                    category=RemarkCategory.FOOTWEAR,
                    body_zone="feet",
                    element=outfit_breakdown.footwear_analysis.type,
                    issue=shoe_issue,
                    fix=shoe_issue,
                    why="Trouser fit and shoe silhouette must harmonise — the wrong pairing breaks the leg line.",
                    priority_order=order,
                ))
                order += 1

    return remarks


def _build_footwear_remarks(outfit_breakdown: OutfitBreakdown, occasion: str) -> list[Remark]:
    """Build rule-based footwear remarks."""
    remarks: list[Remark] = []
    fw = outfit_breakdown.footwear_analysis

    if not fw.visible:
        return remarks

    order = 1

    # Condition check
    condition_assessment = assess_condition(fw.condition)
    if condition_assessment.severity != "none":
        remarks.append(Remark(
            severity=condition_assessment.severity,
            category=RemarkCategory.CONDITION,
            body_zone="feet",
            element=fw.type,
            issue=condition_assessment.issue,
            fix=condition_assessment.shoe_care_note,
            why="Shoe condition is noticed immediately — it anchors or undermines everything.",
            priority_order=order,
        ))
        order += 1

    # Occasion appropriateness
    if fw.issue:
        remarks.append(Remark(
            severity="moderate",
            category=RemarkCategory.FOOTWEAR,
            body_zone="feet",
            element=fw.type,
            issue=fw.issue,
            fix=fw.recommended_instead,
            why="Footwear must speak the same style language as the garment.",
            priority_order=order,
        ))

    return remarks


def _build_accessory_remarks(
    user_profile: UserProfile,
    outfit_breakdown: OutfitBreakdown,
    occasion: str,
) -> list[Remark]:
    """Build rule-based accessory remarks."""
    remarks: list[Remark] = []
    order = 1

    for item in outfit_breakdown.accessory_analysis.items_detected:
        if not item.occasion_appropriate and item.issue:
            remarks.append(Remark(
                severity="moderate",
                category=RemarkCategory.ACCESSORY,
                body_zone="upper-body",
                element=item.type.value,
                issue=item.issue,
                fix=item.fix,
                why="Accessories signal the formality level of an entire look.",
                priority_order=order,
            ))
            order += 1

    # Missing accessories
    detected_types = [item.type.value for item in outfit_breakdown.accessory_analysis.items_detected]
    suggestions = suggest_missing_accessories(occasion, detected_types)
    for suggestion in suggestions[:2]:  # max 2 missing accessory remarks
        remarks.append(Remark(
            severity="minor",
            category=RemarkCategory.ACCESSORY,
            body_zone="full-look",
            element="missing accessory",
            issue="Key accessory absent for this occasion",
            fix=suggestion,
            why="The right accessory elevates a good outfit to a complete look.",
            priority_order=order,
        ))
        order += 1

    return remarks


def _enrich_with_api(
    user_profile: UserProfile,
    grooming_profile: GroomingProfile,
    outfit_breakdown: OutfitBreakdown,
    occasion: str,
    color_do: list[str],
    color_dont: list[str],
    rule_outfit_remarks: list[Remark],
    rule_footwear_remarks: list[Remark],
    rule_accessory_remarks: list[Remark],
    rule_grooming_remarks: list[Remark],
    caricature_path: str,
    annotated_path: str,
    json_path: str,
) -> StyleRecommendation:
    """Call Claude API to generate rich narrative recommendations."""
    # ── Base body type rules (existing) ─────────────────────────────────────
    body_do = get_do(user_profile.body_shape)
    body_avoid = get_avoid(user_profile.body_shape)
    body_rules_str = (
        f"Body shape: {user_profile.body_shape.value}, Height: {user_profile.height_estimate}, "
        f"Build: {user_profile.build}\n"
        f"Do: {', '.join(body_do[:4])}\nAvoid: {', '.join(body_avoid[:3])}"
    )

    haircut_rules = get_haircut_rules(user_profile.face_shape)
    beard_rules   = get_beard_rules(user_profile.face_shape)
    eyebrow_rec   = get_eyebrow_recommendation(user_profile.face_shape)
    grooming_str  = (
        f"Face shape: {user_profile.face_shape.value}\n"
        f"Haircut recommended: {', '.join(haircut_rules.recommended[:2])}\n"
        f"Haircut avoid: {', '.join(haircut_rules.avoid[:2])}\n"
        f"Beard recommended: {', '.join(beard_rules.recommended[:2])}\n"
        f"Beard avoid: {', '.join(beard_rules.avoid[:2])}\n"
        f"Eyebrows: {eyebrow_rec}"
    )

    fw_visible = outfit_breakdown.footwear_analysis.visible
    lb_visible = any(
        g.category in ("bottom", "ethnic-bottom", "full-garment")
        for g in outfit_breakdown.items
    ) or outfit_breakdown.footwear_analysis.visible

    # ── v2 context — trend, seasonal, archetype, proportion ─────────────────
    try:
        from src.fashion_knowledge.trends import get_trend_context_string
        _is_indian = any(
            kw in occasion.lower()
            for kw in ("indian", "ethnic", "wedding", "festival", "fusion")
        )
        _region = "indian" if _is_indian else "western"
        trend_ctx = get_trend_context_string(
            occasion=occasion,
            body_shape=user_profile.body_shape.value,
            region=_region,
            max_items=5,
        )
    except Exception:
        trend_ctx = ""

    try:
        from src.fashion_knowledge.seasonal_color import (
            seasonal_palette_do,
            seasonal_palette_avoid,
        )
        _seasonal = user_profile.seasonal_color_type or ""
        s_do    = seasonal_palette_do(_seasonal)    if _seasonal else []
        s_avoid = seasonal_palette_avoid(_seasonal) if _seasonal else []
    except Exception:
        _seasonal = ""
        s_do    = []
        s_avoid = []

    try:
        from src.fashion_knowledge.style_archetypes import archetype_context_string
        arch_ctx = archetype_context_string(user_profile.style_archetype or "")
    except Exception:
        arch_ctx = ""

    try:
        from src.fashion_knowledge.proportion_theory import proportion_context_string
        prop_rules = proportion_context_string(
            user_profile.height_estimate,
            user_profile.body_shape.value,
        )
    except Exception:
        prop_rules = ""

    prompt = build_recommendation_prompt(
        user_profile_json=user_profile.model_dump_json(),
        outfit_breakdown_json=outfit_breakdown.model_dump_json(),
        occasion=occasion,
        color_do=color_do,
        color_dont=color_dont,
        body_type_rules=body_rules_str,
        grooming_rules=grooming_str,
        footwear_visible=fw_visible,
        lower_body_visible=lb_visible,
        # v2 parameters:
        trend_context=trend_ctx,
        seasonal_type=_seasonal,
        seasonal_do=s_do,
        seasonal_avoid=s_avoid,
        archetype_context=arch_ctx,
        proportion_rules=prop_rules,
        preferred_name=user_profile.preferred_name or "",
        style_goals=user_profile.style_goals or [],
        lifestyle=user_profile.lifestyle or "",
    )

    raw = call_text(prompt)
    data = parse_json_response(raw)

    # Parse API remarks
    def _parse_remarks(raw_list: list[dict[str, Any]], fallback: list[Remark]) -> list[Remark]:
        parsed = []
        for r in raw_list:
            try:
                parsed.append(Remark(
                    severity=r.get("severity", "minor"),
                    category=RemarkCategory(r.get("category", "occasion")),
                    body_zone=r.get("body_zone", "full-look"),
                    element=r.get("element", "outfit"),
                    issue=r.get("issue", ""),
                    fix=r.get("fix", ""),
                    why=r.get("why", ""),
                    priority_order=int(r.get("priority_order", 99)),
                ))
            except (ValueError, KeyError):
                pass
        return sorted(parsed, key=lambda x: x.priority_order) if parsed else fallback

    outfit_remarks   = _parse_remarks(data.get("outfit_remarks",   []), rule_outfit_remarks)
    grooming_remarks = _parse_remarks(data.get("grooming_remarks", []), rule_grooming_remarks)
    accessory_remarks= _parse_remarks(data.get("accessory_remarks",[]), rule_accessory_remarks)
    footwear_remarks = _parse_remarks(data.get("footwear_remarks", []), rule_footwear_remarks)

    # ── Hard filter: strip zones that aren't in frame ─────────────────────────
    # Even if Claude generates them, drop any feet/lower-body remarks when not visible.
    if not fw_visible:
        footwear_remarks = []
        outfit_remarks = [r for r in outfit_remarks if r.body_zone != "feet"]
        accessory_remarks = [r for r in accessory_remarks if r.body_zone != "feet"]
    if not lb_visible:
        outfit_remarks = [r for r in outfit_remarks if r.body_zone != "lower-body"]

    return StyleRecommendation(
        user_profile=user_profile,
        grooming_profile=grooming_profile,
        outfit_breakdown=outfit_breakdown,
        outfit_remarks=outfit_remarks,
        grooming_remarks=grooming_remarks,
        accessory_remarks=accessory_remarks,
        footwear_remarks=footwear_remarks,
        color_palette_do=data.get("color_palette_do", color_do[:6]),
        color_palette_dont=data.get("color_palette_dont", color_dont[:4]),
        color_palette_occasion_specific=data.get("color_palette_occasion_specific", []),
        recommended_outfit_instead=data.get("recommended_outfit_instead", ""),
        recommended_grooming_change=data.get("recommended_grooming_change", ""),
        recommended_accessories=data.get("recommended_accessories", ""),
        wardrobe_gaps=data.get("wardrobe_gaps", []),
        shopping_priorities=data.get("shopping_priorities", []),
        overall_style_score=int(data.get("overall_style_score", outfit_breakdown.outfit_score)),
        outfit_score=int(data.get("outfit_score", outfit_breakdown.outfit_score)),
        grooming_score=int(data.get("grooming_score", grooming_profile.grooming_score)),
        accessory_score=int(data.get("accessory_score", outfit_breakdown.accessory_analysis.overall_score)),
        footwear_score=_footwear_score(outfit_breakdown),
        caricature_image_path=caricature_path,
        annotated_output_path=annotated_path,
        analysis_json_path=json_path,
        # v2 stylist voice fields — Optional, may be None if Claude didn't return them
        whats_working=data.get("whats_working") or None,
        priority_fix_two=data.get("priority_fix_two") or None,
    )


def _build_rule_based_recommendation(
    user_profile: UserProfile,
    grooming_profile: GroomingProfile,
    outfit_breakdown: OutfitBreakdown,
    color_do: list[str],
    color_dont: list[str],
    outfit_remarks: list[Remark],
    footwear_remarks: list[Remark],
    accessory_remarks: list[Remark],
    grooming_remarks: list[Remark],
    caricature_path: str,
    annotated_path: str,
    json_path: str,
) -> StyleRecommendation:
    """Build a rule-based StyleRecommendation without API call."""
    all_remarks = outfit_remarks + footwear_remarks + accessory_remarks + grooming_remarks
    all_remarks.sort(key=lambda r: r.priority_order)

    return StyleRecommendation(
        user_profile=user_profile,
        grooming_profile=grooming_profile,
        outfit_breakdown=outfit_breakdown,
        outfit_remarks=sorted(outfit_remarks, key=lambda r: r.priority_order),
        grooming_remarks=sorted(grooming_remarks, key=lambda r: r.priority_order),
        accessory_remarks=sorted(accessory_remarks, key=lambda r: r.priority_order),
        footwear_remarks=sorted(footwear_remarks, key=lambda r: r.priority_order),
        color_palette_do=color_do[:8],
        color_palette_dont=color_dont[:6],
        color_palette_occasion_specific=[],
        recommended_outfit_instead="See detailed remarks above for specific garment swaps.",
        recommended_grooming_change=grooming_profile.recommended_beard_style,
        recommended_accessories="See accessory remarks for specific suggestions.",
        wardrobe_gaps=[],
        shopping_priorities=[],
        overall_style_score=outfit_breakdown.outfit_score,
        outfit_score=outfit_breakdown.outfit_score,
        grooming_score=grooming_profile.grooming_score,
        accessory_score=outfit_breakdown.accessory_analysis.overall_score,
        footwear_score=_footwear_score(outfit_breakdown),
        caricature_image_path=caricature_path,
        annotated_output_path=annotated_path,
        analysis_json_path=json_path,
    )


def _footwear_score(outfit_breakdown: OutfitBreakdown) -> int:
    """Derive a footwear score from the footwear analysis."""
    fw = outfit_breakdown.footwear_analysis
    if not fw.visible:
        return 5  # neutral when not visible
    if fw.condition in ("dirty", "worn out", "sole peeling"):
        return 2
    if fw.condition in ("scuffed", "yellowed sole"):
        return 5
    if fw.occasion_match and fw.outfit_match:
        return 8
    if fw.occasion_match or fw.outfit_match:
        return 6
    return 4
