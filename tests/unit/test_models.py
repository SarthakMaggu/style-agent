"""Unit tests for all data models — Step 1."""

import json
import pytest
from pydantic import ValidationError

from src.models.user_profile import SkinUndertone, BodyShape, FaceShape, UserProfile
from src.models.remark import RemarkCategory, Remark
from src.models.grooming import GroomingProfile
from src.models.accessories import AccessoryType, AccessoryItem, AccessoryAnalysis
from src.models.footwear import FootwearAnalysis
from src.models.outfit import GarmentItem, OutfitBreakdown
from src.models.recommendation import StyleRecommendation


# ---------------------------------------------------------------------------
# UserProfile — enums
# ---------------------------------------------------------------------------

def test_user_profile_rejects_invalid_undertone():
    """strict=True must reject an unknown undertone string."""
    with pytest.raises(ValidationError):
        UserProfile(
            skin_undertone="yellow",  # not in SkinUndertone enum
            skin_tone_depth="medium",
            skin_texture_visible="smooth",
            body_shape=BodyShape.RECTANGLE,
            height_estimate="average",
            build="average",
            shoulder_width="average",
            torso_length="average",
            leg_proportion="average",
            face_shape=FaceShape.OVAL,
            jaw_type="soft",
            forehead="average",
            hair_color="black",
            hair_texture="straight",
            hair_density="medium",
            current_haircut_style="buzz",
            haircut_length="short",
            hair_visible_condition="healthy",
            beard_style="stubble",
            beard_density="patchy",
            beard_color="black",
            mustache_style="none",
            beard_grooming_quality="average",
            confidence_scores={},
            photos_used=3,
            profile_created_at="2024-01-01T00:00:00",
            profile_version=1,
        )


def test_face_shape_enum_all_values():
    """All six face shapes must be present in the enum."""
    values = {e.value for e in FaceShape}
    assert values == {"oval", "square", "round", "oblong", "heart", "diamond"}


def test_body_shape_enum_all_values():
    """All five body shapes must be present in the enum."""
    values = {e.value for e in BodyShape}
    assert values == {"rectangle", "triangle", "inverted_triangle", "oval", "trapezoid"}


def test_skin_undertone_enum_all_values():
    """All six undertone values must be present."""
    values = {e.value for e in SkinUndertone}
    assert values == {"warm", "cool", "neutral", "deep_warm", "deep_cool", "olive_warm"}


# ---------------------------------------------------------------------------
# AccessoryType enum completeness
# ---------------------------------------------------------------------------

def test_accessory_type_enum_complete():
    """AccessoryType must cover all specified items."""
    required = {
        "watch", "ring", "bracelet", "necklace", "chain", "pendant",
        "belt", "bag", "sunglasses", "hat", "cap", "turban", "pagdi",
        "pocket_square", "tie", "tie_pin", "cufflinks", "earring",
    }
    values = {e.value for e in AccessoryType}
    assert required.issubset(values)


# ---------------------------------------------------------------------------
# GarmentItem — requires issue and fix
# ---------------------------------------------------------------------------

def test_garment_item_requires_issue_and_fix():
    """GarmentItem must always carry an issue and fix string."""
    item = GarmentItem(
        category="top",
        garment_type="t-shirt",
        color="white",
        pattern="solid",
        fabric_estimate="cotton",
        fit="regular",
        length="hip",
        collar_type="crew",
        sleeve_type="short",
        condition="good",
        occasion_appropriate=True,
        issue="No issue",
        fix="No fix needed",
    )
    assert item.issue == "No issue"
    assert item.fix == "No fix needed"


# ---------------------------------------------------------------------------
# Remark — severity and priority
# ---------------------------------------------------------------------------

def test_remark_severity_valid_values(sample_remark: Remark):
    """Severity must be one of critical/moderate/minor."""
    assert sample_remark.severity in {"critical", "moderate", "minor"}


def test_remark_priority_order_positive_int(sample_remark: Remark):
    """Priority order must be a positive integer."""
    assert isinstance(sample_remark.priority_order, int)
    assert sample_remark.priority_order > 0


def test_remark_category_enum_complete():
    """RemarkCategory must cover all specified categories."""
    required = {
        "color", "fit", "fabric", "occasion", "proportion",
        "accessory", "footwear", "grooming_hair", "grooming_beard",
        "grooming_skin", "layering", "pattern", "length", "condition", "posture",
    }
    values = {e.value for e in RemarkCategory}
    assert required == values


# ---------------------------------------------------------------------------
# FootwearAnalysis — visible=False behaviour
# ---------------------------------------------------------------------------

def test_footwear_visible_false_returns_empty():
    """When visible=False, type/color can be empty strings (not-applicable)."""
    fw = FootwearAnalysis(
        visible=False,
        type="",
        color="",
        material_estimate="",
        condition="",
        style_category="",
        occasion_match=False,
        outfit_match=False,
        issue="",
        recommended_instead="",
        shoe_care_note="",
    )
    assert fw.visible is False
    assert fw.type == ""


# ---------------------------------------------------------------------------
# StyleRecommendation — JSON round-trip
# ---------------------------------------------------------------------------

def test_style_recommendation_json_roundtrip(sample_style_recommendation: StyleRecommendation):
    """Serialising to JSON and back must produce an identical object."""
    json_str = sample_style_recommendation.model_dump_json()
    restored = StyleRecommendation.model_validate_json(json_str)
    assert restored == sample_style_recommendation


# ---------------------------------------------------------------------------
# strict=True — rejects extra fields
# ---------------------------------------------------------------------------

def test_strict_mode_rejects_extra_fields():
    """Pydantic strict mode must reject extra (unknown) fields."""
    with pytest.raises(ValidationError):
        FootwearAnalysis(
            visible=True,
            type="sneakers",
            color="white",
            material_estimate="canvas",
            condition="clean",
            style_category="casual",
            occasion_match=True,
            outfit_match=True,
            issue="",
            recommended_instead="",
            shoe_care_note="",
            extra_unknown_field="should_fail",  # type: ignore[call-arg]
        )


# ---------------------------------------------------------------------------
# OutfitBreakdown — score ranges
# ---------------------------------------------------------------------------

def test_outfit_breakdown_scores_are_ints(sample_outfit_breakdown: OutfitBreakdown):
    """formality_level and outfit_score must be integers."""
    assert isinstance(sample_outfit_breakdown.formality_level, int)
    assert isinstance(sample_outfit_breakdown.outfit_score, int)


# ---------------------------------------------------------------------------
# AccessoryAnalysis — model construction
# ---------------------------------------------------------------------------

def test_accessory_analysis_empty_items():
    """AccessoryAnalysis with no detected items must still be valid."""
    analysis = AccessoryAnalysis(
        items_detected=[],
        missing_accessories=[],
        accessories_to_remove=[],
        accessory_harmony="N/A",
        overall_score=5,
    )
    assert analysis.items_detected == []


def test_accessory_item_occasion_appropriate_flag():
    """AccessoryItem.occasion_appropriate must be a bool."""
    item = AccessoryItem(
        type=AccessoryType.BELT,
        color="black",
        material_estimate="leather",
        style_category="formal",
        condition="good",
        occasion_appropriate=True,
        issue="",
        fix="",
    )
    assert item.occasion_appropriate is True


# ---------------------------------------------------------------------------
# UserProfile v2 — Optional extended fields (Phase F)
# ---------------------------------------------------------------------------

def _make_base_profile(**overrides) -> UserProfile:
    """Helper: build a minimal valid UserProfile, with optional overrides."""
    defaults = dict(
        skin_undertone=SkinUndertone.WARM,
        skin_tone_depth="medium",
        skin_texture_visible="smooth",
        body_shape=BodyShape.RECTANGLE,
        height_estimate="average",
        build="average",
        shoulder_width="average",
        torso_length="average",
        leg_proportion="average",
        face_shape=FaceShape.OVAL,
        jaw_type="soft",
        forehead="average",
        hair_color="black",
        hair_texture="straight",
        hair_density="medium",
        current_haircut_style="buzz",
        haircut_length="short",
        hair_visible_condition="healthy",
        beard_style="stubble",
        beard_density="patchy",
        beard_color="black",
        mustache_style="none",
        beard_grooming_quality="average",
        confidence_scores={},
        photos_used=3,
        profile_created_at="2024-01-01T00:00:00",
        profile_version=1,
    )
    defaults.update(overrides)
    return UserProfile(**defaults)


def test_user_profile_optional_fields_default_none():
    """All v2 Optional fields must default to None when not supplied."""
    p = _make_base_profile()
    assert p.style_archetype is None
    assert p.seasonal_color_type is None
    assert p.fit_preference_default is None
    assert p.style_comfort_zones is None
    assert p.budget_tier is None
    assert p.age_group is None
    assert p.lifestyle is None
    assert p.style_goals is None
    assert p.preferred_name is None
    assert p.posture is None
    assert p.belly_profile is None


def test_user_profile_style_archetype_valid_string():
    """style_archetype must accept any string value without raising."""
    p = _make_base_profile(style_archetype="smart_casual")
    assert p.style_archetype == "smart_casual"


def test_user_profile_backward_compat_without_new_fields():
    """A profile built without v2 fields must still validate (defaults fill None)."""
    p = _make_base_profile()
    assert p.profile_version == 1
    assert p.style_archetype is None   # new field defaults correctly


def test_user_profile_json_roundtrip_with_optional_fields():
    """A profile with v2 fields populated round-trips through JSON unchanged."""
    p = _make_base_profile(
        style_archetype="classic",
        seasonal_color_type="autumn",
        preferred_name="Arjun",
        style_goals=["elevate work wardrobe"],
        style_comfort_zones=["smart_casual", "indian_casual"],
    )
    restored = UserProfile.model_validate_json(p.model_dump_json())
    assert restored.style_archetype == "classic"
    assert restored.preferred_name == "Arjun"
    assert restored.style_goals == ["elevate work wardrobe"]


def test_user_profile_none_fields_excluded_from_json_dump():
    """model_dump_json(exclude_none=True) must omit None fields."""
    p = _make_base_profile()
    data = p.model_dump(exclude_none=True)
    assert "style_archetype" not in data
    assert "preferred_name" not in data
    # But required fields must still be present
    assert "skin_undertone" in data
    assert "body_shape" in data
