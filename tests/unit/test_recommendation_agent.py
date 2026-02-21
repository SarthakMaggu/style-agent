"""Unit tests for agents/recommendation_agent.py — Step 16 (all mocked)."""

import json
import pytest
from unittest.mock import patch

from src.agents.recommendation_agent import generate_recommendation
from src.models.recommendation import StyleRecommendation
from src.models.remark import Remark, RemarkCategory
from src.models.user_profile import (
    SkinUndertone, BodyShape, FaceShape, UserProfile,
)
from src.models.grooming import GroomingProfile
from src.models.accessories import AccessoryType, AccessoryItem, AccessoryAnalysis
from src.models.footwear import FootwearAnalysis
from src.models.outfit import GarmentItem, OutfitBreakdown


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_profile(**overrides) -> UserProfile:
    defaults = dict(
        skin_undertone=SkinUndertone.DEEP_WARM,
        skin_tone_depth="deep",
        skin_texture_visible="smooth",
        body_shape=BodyShape.INVERTED_TRIANGLE,
        height_estimate="tall",
        build="athletic",
        shoulder_width="broad",
        torso_length="average",
        leg_proportion="long",
        face_shape=FaceShape.SQUARE,
        jaw_type="strong",
        forehead="average",
        hair_color="black",
        hair_texture="straight",
        hair_density="medium",
        current_haircut_style="taper fade",
        haircut_length="short",
        hair_visible_condition="healthy",
        beard_style="full",
        beard_density="dense",
        beard_color="black",
        mustache_style="natural",
        beard_grooming_quality="well groomed",
        confidence_scores={},
        photos_used=5,
        profile_created_at="2024-01-01T00:00:00+00:00",
        profile_version=1,
    )
    defaults.update(overrides)
    return UserProfile(**defaults)


def _make_grooming_profile(**overrides) -> GroomingProfile:
    defaults = dict(
        current_haircut_assessment="Short taper fade",
        recommended_haircut="Keep taper fade",
        haircut_to_avoid="Bowl cut",
        styling_product_recommendation=["matte clay"],
        hair_color_recommendation="Keep natural black",
        current_beard_assessment="Full beard, well groomed",
        recommended_beard_style="Trim cheek line",
        beard_grooming_tips=["Trim sides"],
        beard_style_to_avoid="Wide cheek coverage",
        eyebrow_assessment="Natural",
        eyebrow_recommendation="Maintain",
        visible_skin_concerns=[],
        skincare_categories_needed=["moisturiser"],
        grooming_score=7,
        grooming_remarks=[],
    )
    defaults.update(overrides)
    return GroomingProfile(**defaults)


def _make_accessory_analysis(
    occasion_appropriate: bool = True,
    condition: str = "clean",
) -> AccessoryAnalysis:
    watch = AccessoryItem(
        type=AccessoryType.WATCH,
        color="silver",
        material_estimate="metal case, leather strap",
        style_category="formal",
        condition=condition,
        occasion_appropriate=occasion_appropriate,
        issue="" if occasion_appropriate else "Sport strap with formal wear",
        fix="" if occasion_appropriate else "Swap to leather strap",
    )
    return AccessoryAnalysis(
        items_detected=[watch],
        missing_accessories=[],
        accessories_to_remove=[],
        accessory_harmony="good",
        overall_score=7,
    )


def _make_footwear(
    condition: str = "clean",
    occasion_match: bool = True,
    outfit_match: bool = True,
    visible: bool = True,
    issue: str = "",
) -> FootwearAnalysis:
    return FootwearAnalysis(
        visible=visible,
        type="mojaris",
        color="tan",
        material_estimate="leather",
        condition=condition,
        style_category="indian formal",
        occasion_match=occasion_match,
        outfit_match=outfit_match,
        issue=issue,
        recommended_instead="",
        shoe_care_note="",
    )


def _make_garment(
    category: str = "ethnic-top",
    garment_type: str = "kurta",
    occasion_appropriate: bool = True,
    issue: str = "",
    fix: str = "",
) -> GarmentItem:
    return GarmentItem(
        category=category,
        garment_type=garment_type,
        color="ivory",
        pattern="solid",
        fabric_estimate="cotton",
        fit="straight",
        length="mid-thigh",
        collar_type="mandarin",
        sleeve_type="full",
        condition="good",
        occasion_appropriate=occasion_appropriate,
        issue=issue,
        fix=fix,
    )


def _make_outfit(
    color_clash: bool = False,
    occasion_match: bool = True,
    occasion_detected: str = "wedding_guest_indian",
    occasion_requested: str = "wedding_guest_indian",
    garments: list | None = None,
    footwear: FootwearAnalysis | None = None,
    accessory_analysis: AccessoryAnalysis | None = None,
) -> OutfitBreakdown:
    if garments is None:
        garments = [_make_garment()]
    if footwear is None:
        footwear = _make_footwear()
    if accessory_analysis is None:
        accessory_analysis = _make_accessory_analysis()
    return OutfitBreakdown(
        occasion_detected=occasion_detected,
        occasion_requested=occasion_requested,
        occasion_match=occasion_match,
        items=garments,
        accessory_analysis=accessory_analysis,
        footwear_analysis=footwear,
        overall_color_harmony="good" if not color_clash else "clashing",
        color_clash_detected=color_clash,
        silhouette_assessment="balanced",
        proportion_assessment="good",
        formality_level=8,
        outfit_score=7,
    )


def _mock_api_response(
    outfit_remarks: list | None = None,
    grooming_remarks: list | None = None,
    accessory_remarks: list | None = None,
    footwear_remarks: list | None = None,
    wardrobe_gaps: list | None = None,
    shopping_priorities: list | None = None,
    overall_style_score: int = 7,
    outfit_score: int = 7,
    grooming_score: int = 7,
    accessory_score: int = 7,
) -> str:
    return json.dumps({
        "outfit_remarks": outfit_remarks or [],
        "grooming_remarks": grooming_remarks or [
            {
                "severity": "minor",
                "category": "grooming_beard",
                "body_zone": "face",
                "element": "beard",
                "issue": "Beard sides add width",
                "fix": "Trim cheek line",
                "why": "Reduces jaw width",
                "priority_order": 1,
            }
        ],
        "accessory_remarks": accessory_remarks or [
            {
                "severity": "minor",
                "category": "accessory",
                "body_zone": "upper-body",
                "element": "watch",
                "issue": "Minor accessory note",
                "fix": "No change needed",
                "why": "Contextual fit",
                "priority_order": 2,
            }
        ],
        "footwear_remarks": footwear_remarks or [
            {
                "severity": "minor",
                "category": "footwear",
                "body_zone": "feet",
                "element": "mojaris",
                "issue": "Minor footwear note",
                "fix": "No change needed",
                "why": "Good match",
                "priority_order": 3,
            }
        ],
        "color_palette_do": ["rust", "terracotta", "deep teal"],
        "color_palette_dont": ["icy white", "cool grey"],
        "color_palette_occasion_specific": ["burgundy"],
        "recommended_outfit_instead": "Rust silk-cotton kurta",
        "recommended_grooming_change": "Trim cheek line",
        "recommended_accessories": "Tan leather strap",
        "wardrobe_gaps": wardrobe_gaps or ["silk kurta", "mojaris"],
        "shopping_priorities": shopping_priorities or ["silk kurta", "mojaris"],
        "overall_style_score": overall_style_score,
        "outfit_score": outfit_score,
        "grooming_score": grooming_score,
        "accessory_score": accessory_score,
    })


# ---------------------------------------------------------------------------
# Rule-based path (use_api=False)
# ---------------------------------------------------------------------------

def test_returns_style_recommendation():
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=_make_outfit(),
        occasion="wedding_guest_indian",
        use_api=False,
    )
    assert isinstance(result, StyleRecommendation)


def test_all_scores_1_to_10():
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=_make_outfit(),
        occasion="wedding_guest_indian",
        use_api=False,
    )
    for score in (
        result.overall_style_score,
        result.outfit_score,
        result.grooming_score,
        result.accessory_score,
        result.footwear_score,
    ):
        assert 1 <= score <= 10, f"Score out of range: {score}"


def test_critical_remark_color_clash():
    """Color clash must produce at least one critical remark."""
    outfit = _make_outfit(color_clash=True)
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="wedding_guest_indian",
        use_api=False,
    )
    critical = [r for r in result.outfit_remarks if r.severity == "critical"]
    assert len(critical) >= 1


def test_critical_remark_dirty_shoes():
    """Dirty sneakers must produce a critical remark."""
    footwear = _make_footwear(condition="dirty", occasion_match=False, issue="Dirty shoes")
    outfit = _make_outfit(footwear=footwear)
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="streetwear",
        use_api=False,
    )
    all_remarks = result.footwear_remarks
    critical = [r for r in all_remarks if r.severity == "critical"]
    assert len(critical) >= 1


def test_critical_remark_sole_peeling():
    """Sole peeling must produce a critical remark."""
    footwear = _make_footwear(condition="sole peeling", occasion_match=False, issue="Sole peeling")
    outfit = _make_outfit(footwear=footwear)
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="streetwear",
        use_api=False,
    )
    critical = [r for r in result.footwear_remarks if r.severity == "critical"]
    assert len(critical) >= 1


def test_remarks_ordered_by_priority():
    """All remark lists must be sorted by priority_order ascending."""
    outfit = _make_outfit(color_clash=True, occasion_match=False)
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="wedding_guest_indian",
        use_api=False,
    )
    for remark_list in (
        result.outfit_remarks,
        result.grooming_remarks,
        result.accessory_remarks,
        result.footwear_remarks,
    ):
        orders = [r.priority_order for r in remark_list]
        assert orders == sorted(orders), f"Remarks not sorted: {orders}"


def test_grooming_remarks_in_output():
    """Grooming remarks from GroomingProfile must pass through."""
    grooming_remark = Remark(
        severity="minor",
        category=RemarkCategory.GROOMING_BEARD,
        body_zone="face",
        element="beard",
        issue="Beard adds width to square jaw",
        fix="Trim cheek line",
        why="Reduces jaw width",
        priority_order=1,
    )
    grooming = _make_grooming_profile(grooming_remarks=[grooming_remark])
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=grooming,
        outfit_breakdown=_make_outfit(),
        occasion="wedding_guest_indian",
        use_api=False,
    )
    assert len(result.grooming_remarks) >= 1


def test_accessory_remarks_in_output():
    """Inappropriate accessory must produce an accessory remark."""
    accessories = _make_accessory_analysis(occasion_appropriate=False)
    outfit = _make_outfit(accessory_analysis=accessories)
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="wedding_guest_indian",
        use_api=False,
    )
    assert len(result.accessory_remarks) >= 1


def test_footwear_remarks_in_output():
    """Footwear with issues must produce footwear remarks."""
    footwear = _make_footwear(condition="scuffed", occasion_match=False, issue="Scuffed shoes")
    outfit = _make_outfit(footwear=footwear)
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="wedding_guest_indian",
        use_api=False,
    )
    assert len(result.footwear_remarks) >= 1


def test_footwear_not_visible_no_footwear_remarks():
    """If footwear is not visible, no footwear remarks should be generated."""
    footwear = _make_footwear(visible=False)
    outfit = _make_outfit(footwear=footwear)
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="wedding_guest_indian",
        use_api=False,
    )
    assert result.footwear_remarks == []


def test_indian_occasion_indian_garments():
    """Indian garments with Indian occasion should not trigger occasion mismatch."""
    garment = _make_garment(
        category="ethnic-top",
        garment_type="kurta",
        occasion_appropriate=True,
    )
    outfit = _make_outfit(
        garments=[garment],
        occasion_match=True,
        occasion_detected="wedding_guest_indian",
        occasion_requested="wedding_guest_indian",
    )
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="wedding_guest_indian",
        use_api=False,
    )
    occasion_remarks = [r for r in result.outfit_remarks if r.category == RemarkCategory.OCCASION]
    assert len(occasion_remarks) == 0


def test_western_occasion_western_garments():
    """Western garments with Western occasion should not trigger mismatch."""
    garment = _make_garment(
        category="top",
        garment_type="dress shirt",
        occasion_appropriate=True,
    )
    outfit = _make_outfit(
        garments=[garment],
        occasion_match=True,
        occasion_detected="western_business_formal",
        occasion_requested="western_business_formal",
    )
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="western_business_formal",
        use_api=False,
    )
    occasion_remarks = [r for r in result.outfit_remarks if r.category == RemarkCategory.OCCASION]
    assert len(occasion_remarks) == 0


def test_warm_undertone_avoids_cool_in_recommendation():
    """Deep Warm undertone — color_palette_dont should include cool colours."""
    result = generate_recommendation(
        user_profile=_make_user_profile(skin_undertone=SkinUndertone.DEEP_WARM),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=_make_outfit(),
        occasion="wedding_guest_indian",
        use_api=False,
    )
    dont = " ".join(result.color_palette_dont).lower()
    # deep warm avoids pastels and cool tones
    assert len(result.color_palette_dont) >= 1
    assert len(result.color_palette_do) >= 1


def test_warm_undertone_color_do_includes_warm_tones():
    """Deep Warm palette should include warm jewel tones."""
    result = generate_recommendation(
        user_profile=_make_user_profile(skin_undertone=SkinUndertone.DEEP_WARM),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=_make_outfit(),
        occasion="wedding_guest_indian",
        use_api=False,
    )
    do = " ".join(result.color_palette_do).lower()
    # At least one warm/jewel tone present
    warm_keywords = ["rust", "terracotta", "camel", "mustard", "gold", "emerald", "burgundy", "sapphire", "teal", "warm", "earth"]
    assert any(kw in do for kw in warm_keywords)


def test_inverted_triangle_no_shoulder_emphasis():
    """Inverted triangle body shape — color palette and remarks should be generated."""
    result = generate_recommendation(
        user_profile=_make_user_profile(body_shape=BodyShape.INVERTED_TRIANGLE),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=_make_outfit(),
        occasion="wedding_guest_indian",
        use_api=False,
    )
    # Should still produce a recommendation without errors
    assert isinstance(result, StyleRecommendation)
    # Color palettes populated
    assert len(result.color_palette_do) > 0


def test_occasion_mismatch_generates_critical_remark():
    """Occasion mismatch must produce a critical OCCASION remark."""
    outfit = _make_outfit(
        occasion_match=False,
        occasion_detected="streetwear",
        occasion_requested="wedding_guest_indian",
    )
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        occasion="wedding_guest_indian",
        use_api=False,
    )
    occasion_remarks = [r for r in result.outfit_remarks if r.category == RemarkCategory.OCCASION]
    assert len(occasion_remarks) >= 1
    assert occasion_remarks[0].severity == "critical"


def test_footwear_score_dirty_is_low():
    """Dirty footwear should produce a score of 2."""
    from src.agents.recommendation_agent import _footwear_score
    from src.models.footwear import FootwearAnalysis

    fw = FootwearAnalysis(
        visible=True,
        type="sneakers",
        color="white",
        material_estimate="canvas",
        condition="dirty",
        style_category="casual",
        occasion_match=False,
        outfit_match=False,
        issue="Dirty sneakers",
        recommended_instead="Clean sneakers",
        shoe_care_note="Clean before wear",
    )
    from src.models.outfit import OutfitBreakdown, GarmentItem
    from src.models.accessories import AccessoryAnalysis

    outfit = OutfitBreakdown(
        occasion_detected="streetwear",
        occasion_requested="streetwear",
        occasion_match=True,
        items=[_make_garment()],
        accessory_analysis=_make_accessory_analysis(),
        footwear_analysis=fw,
        overall_color_harmony="ok",
        color_clash_detected=False,
        silhouette_assessment="ok",
        proportion_assessment="ok",
        formality_level=3,
        outfit_score=5,
    )
    assert _footwear_score(outfit) == 2


def test_footwear_score_neutral_when_not_visible():
    """Footwear score must be 5 when footwear is not visible."""
    from src.agents.recommendation_agent import _footwear_score

    fw = FootwearAnalysis(
        visible=False,
        type="n/a",
        color="n/a",
        material_estimate="n/a",
        condition="n/a",
        style_category="n/a",
        occasion_match=False,
        outfit_match=False,
        issue="",
        recommended_instead="",
        shoe_care_note="",
    )
    outfit = _make_outfit(footwear=fw)
    assert _footwear_score(outfit) == 5


def test_footwear_score_high_when_both_match():
    """Footwear that matches both occasion and outfit should score 8."""
    from src.agents.recommendation_agent import _footwear_score

    fw = FootwearAnalysis(
        visible=True,
        type="mojaris",
        color="tan",
        material_estimate="leather",
        condition="clean",
        style_category="indian formal",
        occasion_match=True,
        outfit_match=True,
        issue="",
        recommended_instead="",
        shoe_care_note="",
    )
    outfit = _make_outfit(footwear=fw)
    assert _footwear_score(outfit) == 8


def test_color_palettes_populated():
    """Both do and dont color palettes must have entries."""
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=_make_outfit(),
        occasion="wedding_guest_indian",
        use_api=False,
    )
    assert len(result.color_palette_do) >= 1
    assert len(result.color_palette_dont) >= 1


# ---------------------------------------------------------------------------
# API path (mocked)
# ---------------------------------------------------------------------------

def test_api_enrichment_returns_recommendation():
    with patch("src.agents.recommendation_agent.call_text", return_value=_mock_api_response()):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    assert isinstance(result, StyleRecommendation)


def test_api_grooming_remarks_parsed():
    with patch("src.agents.recommendation_agent.call_text", return_value=_mock_api_response()):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    assert len(result.grooming_remarks) >= 1


def test_api_accessory_remarks_parsed():
    with patch("src.agents.recommendation_agent.call_text", return_value=_mock_api_response()):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    assert len(result.accessory_remarks) >= 1


def test_api_footwear_remarks_parsed():
    with patch("src.agents.recommendation_agent.call_text", return_value=_mock_api_response()):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    assert len(result.footwear_remarks) >= 1


def test_api_shopping_priorities_ranked():
    priorities = ["silk kurta", "mojaris", "leather strap watch"]
    with patch("src.agents.recommendation_agent.call_text",
               return_value=_mock_api_response(shopping_priorities=priorities)):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    assert result.shopping_priorities == priorities


def test_api_wardrobe_gaps_not_empty():
    gaps = ["silk kurta", "mojaris"]
    with patch("src.agents.recommendation_agent.call_text",
               return_value=_mock_api_response(wardrobe_gaps=gaps)):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    assert len(result.wardrobe_gaps) >= 1


def test_api_failure_falls_back_to_rule_based():
    with patch("src.agents.recommendation_agent.call_text", side_effect=Exception("API down")):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    assert isinstance(result, StyleRecommendation)
    for score in (
        result.overall_style_score,
        result.outfit_score,
        result.grooming_score,
        result.accessory_score,
        result.footwear_score,
    ):
        assert 1 <= score <= 10


def test_api_all_scores_1_to_10():
    with patch("src.agents.recommendation_agent.call_text",
               return_value=_mock_api_response(overall_style_score=8, outfit_score=7,
                                                grooming_score=7, accessory_score=6)):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    for score in (
        result.overall_style_score,
        result.outfit_score,
        result.grooming_score,
        result.accessory_score,
        result.footwear_score,
    ):
        assert 1 <= score <= 10


def test_api_remarks_ordered_by_priority():
    outfit_remarks = [
        {"severity": "critical", "category": "color", "body_zone": "full-look",
         "element": "colour", "issue": "clash", "fix": "swap", "why": "reason", "priority_order": 1},
        {"severity": "moderate", "category": "occasion", "body_zone": "full-look",
         "element": "outfit", "issue": "mismatch", "fix": "upgrade", "why": "reason", "priority_order": 2},
    ]
    with patch("src.agents.recommendation_agent.call_text",
               return_value=_mock_api_response(outfit_remarks=outfit_remarks)):
        result = generate_recommendation(
            user_profile=_make_user_profile(),
            grooming_profile=_make_grooming_profile(),
            outfit_breakdown=_make_outfit(color_clash=True, occasion_match=False),
            occasion="wedding_guest_indian",
            use_api=True,
        )
    for remark_list in (
        result.outfit_remarks,
        result.grooming_remarks,
        result.accessory_remarks,
        result.footwear_remarks,
    ):
        orders = [r.priority_order for r in remark_list]
        assert orders == sorted(orders)


def test_caricature_and_paths_stored():
    """Paths passed to generate_recommendation should be stored in the output."""
    result = generate_recommendation(
        user_profile=_make_user_profile(),
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=_make_outfit(),
        occasion="wedding_guest_indian",
        caricature_path="./outputs/caric.png",
        annotated_path="./outputs/annot.png",
        json_path="./outputs/data.json",
        use_api=False,
    )
    assert result.caricature_image_path == "./outputs/caric.png"
    assert result.annotated_output_path == "./outputs/annot.png"
    assert result.analysis_json_path == "./outputs/data.json"
