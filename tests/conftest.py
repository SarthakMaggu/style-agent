"""Shared test fixtures for StyleAgent test suite."""

import pytest

from src.models.user_profile import SkinUndertone, BodyShape, FaceShape, UserProfile
from src.models.remark import RemarkCategory, Remark
from src.models.grooming import GroomingProfile
from src.models.accessories import AccessoryType, AccessoryItem, AccessoryAnalysis
from src.models.footwear import FootwearAnalysis
from src.models.outfit import GarmentItem, OutfitBreakdown
from src.models.recommendation import StyleRecommendation


@pytest.fixture
def sample_user_profile() -> UserProfile:
    """A valid UserProfile for use in tests."""
    return UserProfile(
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
        confidence_scores={"skin_undertone": 0.89, "body_shape": 0.82},
        photos_used=5,
        profile_created_at="2024-01-01T00:00:00",
        profile_version=1,
    )


@pytest.fixture
def sample_remark() -> Remark:
    """A valid Remark for use in tests."""
    return Remark(
        severity="critical",
        category=RemarkCategory.COLOR,
        body_zone="upper-body",
        element="kurta",
        issue="Ivory has cool undertones — grey cast against warm complexion.",
        fix="Swap to warm cream or off-white with yellow base.",
        why="Cool whites fight warm undertones — the face reads tired.",
        priority_order=1,
    )


@pytest.fixture
def sample_grooming_profile(sample_remark: Remark) -> GroomingProfile:
    """A valid GroomingProfile for use in tests."""
    return GroomingProfile(
        current_haircut_assessment="Short taper fade, well maintained",
        recommended_haircut="Keep taper fade — works for square face",
        haircut_to_avoid="Bowl cut, boxy cuts",
        styling_product_recommendation=["matte clay", "light pomade"],
        hair_color_recommendation="Keep natural black",
        current_beard_assessment="Full dense beard, well groomed",
        recommended_beard_style="Trim cheek line higher, extend chin length",
        beard_grooming_tips=["Trim sides shorter", "Let chin grow 1-2 weeks"],
        beard_style_to_avoid="Wide full cheek coverage",
        eyebrow_assessment="Natural, proportional",
        eyebrow_recommendation="Maintain shape, no major change needed",
        visible_skin_concerns=[],
        skincare_categories_needed=["moisturiser", "SPF"],
        grooming_score=7,
        grooming_remarks=[sample_remark],
    )


@pytest.fixture
def sample_accessory_analysis() -> AccessoryAnalysis:
    """A valid AccessoryAnalysis for use in tests."""
    watch = AccessoryItem(
        type=AccessoryType.WATCH,
        color="silver/black",
        material_estimate="metal case, rubber strap",
        style_category="sport",
        condition="good",
        occasion_appropriate=False,
        issue="Rubber sport strap with formal wear",
        fix="Swap to tan leather strap",
    )
    return AccessoryAnalysis(
        items_detected=[watch],
        missing_accessories=["pocket square"],
        accessories_to_remove=[],
        accessory_harmony="Neutral — watch clashes with formality level",
        overall_score=5,
    )


@pytest.fixture
def sample_footwear_analysis() -> FootwearAnalysis:
    """A valid FootwearAnalysis for use in tests."""
    return FootwearAnalysis(
        visible=True,
        type="oxford",
        color="brown",
        material_estimate="leather",
        condition="scuffed",
        style_category="western formal",
        occasion_match=False,
        outfit_match=False,
        issue="Western oxfords with Indian ethnic wear",
        recommended_instead="Mojaris or embellished juttis",
        shoe_care_note="Polish before next wear or take to cobbler",
    )


@pytest.fixture
def sample_garment_item() -> GarmentItem:
    """A valid GarmentItem for use in tests."""
    return GarmentItem(
        category="ethnic-top",
        garment_type="kurta",
        color="ivory",
        pattern="solid",
        fabric_estimate="cotton",
        fit="straight",
        length="hip",
        collar_type="mandarin",
        sleeve_type="full",
        condition="good",
        occasion_appropriate=False,
        issue="Hip-length kurta ends at broadest point",
        fix="Switch to mid-thigh or longer kurta",
    )


@pytest.fixture
def sample_outfit_breakdown(
    sample_garment_item: GarmentItem,
    sample_accessory_analysis: AccessoryAnalysis,
    sample_footwear_analysis: FootwearAnalysis,
) -> OutfitBreakdown:
    """A valid OutfitBreakdown for use in tests."""
    return OutfitBreakdown(
        occasion_detected="indian_casual",
        occasion_requested="wedding_guest_indian",
        occasion_match=False,
        items=[sample_garment_item],
        accessory_analysis=sample_accessory_analysis,
        footwear_analysis=sample_footwear_analysis,
        overall_color_harmony="Clashing — ivory cool-toned vs warm undertone",
        color_clash_detected=True,
        silhouette_assessment="Top-heavy — kurta ends at widest point",
        proportion_assessment="Imbalanced — broad shoulders not offset by length",
        formality_level=6,
        outfit_score=4,
    )


@pytest.fixture
def sample_style_recommendation(
    sample_user_profile: UserProfile,
    sample_grooming_profile: GroomingProfile,
    sample_outfit_breakdown: OutfitBreakdown,
    sample_remark: Remark,
) -> StyleRecommendation:
    """A valid StyleRecommendation for use in tests."""
    footwear_remark = Remark(
        severity="moderate",
        category=RemarkCategory.FOOTWEAR,
        body_zone="feet",
        element="oxford shoes",
        issue="Western oxfords with Indian ethnic wear",
        fix="Swap to mojaris or embellished juttis",
        why="Footwear must speak the same style language as the garment",
        priority_order=2,
    )
    return StyleRecommendation(
        user_profile=sample_user_profile,
        grooming_profile=sample_grooming_profile,
        outfit_breakdown=sample_outfit_breakdown,
        outfit_remarks=[sample_remark],
        grooming_remarks=[],
        accessory_remarks=[],
        footwear_remarks=[footwear_remark],
        color_palette_do=["rust", "terracotta", "warm champagne"],
        color_palette_dont=["icy white", "cool grey", "lavender"],
        color_palette_occasion_specific=["deep teal", "burgundy"],
        recommended_outfit_instead="Rust silk-cotton kurta, mid-thigh, with ivory churidar",
        recommended_grooming_change="Trim cheek beard higher, extend chin length",
        recommended_accessories="Tan leather strap watch or simple gold-tone bracelet",
        wardrobe_gaps=["silk-blend kurta", "mojaris/juttis"],
        shopping_priorities=["silk-blend kurta in rust or champagne"],
        overall_style_score=5,
        outfit_score=4,
        grooming_score=7,
        accessory_score=5,
        footwear_score=4,
        caricature_image_path="./outputs/caricature_20240215.png",
        annotated_output_path="./outputs/analysis_20240215_annotated.png",
        analysis_json_path="./outputs/analysis_20240215.json",
    )
