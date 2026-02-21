"""Unit tests for agents/grooming_agent.py — Step 15 (all mocked)."""

import json
import pytest
from unittest.mock import patch

from src.agents.grooming_agent import generate_grooming_profile
from src.models.grooming import GroomingProfile
from src.models.user_profile import FaceShape, SkinUndertone, BodyShape, UserProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_profile(**overrides) -> UserProfile:
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


# ---------------------------------------------------------------------------
# Rule-based path (use_api=False)
# ---------------------------------------------------------------------------

def test_returns_grooming_profile():
    profile = _make_profile()
    result = generate_grooming_profile(profile, use_api=False)
    assert isinstance(result, GroomingProfile)


def test_recommended_haircut_not_empty():
    profile = _make_profile()
    result = generate_grooming_profile(profile, use_api=False)
    assert len(result.recommended_haircut) > 0


def test_beard_style_to_avoid_not_empty():
    profile = _make_profile()
    result = generate_grooming_profile(profile, use_api=False)
    assert isinstance(result.beard_style_to_avoid, str)


def test_eyebrow_recommendation_not_empty():
    profile = _make_profile()
    result = generate_grooming_profile(profile, use_api=False)
    assert len(result.eyebrow_recommendation) > 0


def test_grooming_score_1_to_10():
    profile = _make_profile()
    result = generate_grooming_profile(profile, use_api=False)
    assert 1 <= result.grooming_score <= 10


def test_unkempt_beard_generates_remark():
    profile = _make_profile(beard_grooming_quality="unkempt")
    result = generate_grooming_profile(profile, use_api=False)
    assert any("beard" in r.element.lower() or "beard" in r.issue.lower() for r in result.grooming_remarks)


def test_well_groomed_beard_score_higher_than_unkempt():
    well = generate_grooming_profile(_make_profile(beard_grooming_quality="well groomed"), use_api=False)
    unkempt = generate_grooming_profile(_make_profile(beard_grooming_quality="unkempt"), use_api=False)
    assert well.grooming_score > unkempt.grooming_score


def test_styling_products_populated():
    profile = _make_profile()
    result = generate_grooming_profile(profile, use_api=False)
    assert len(result.styling_product_recommendation) >= 1


def test_skincare_categories_populated():
    profile = _make_profile()
    result = generate_grooming_profile(profile, use_api=False)
    assert len(result.skincare_categories_needed) >= 1


# ---------------------------------------------------------------------------
# API path (mocked)
# ---------------------------------------------------------------------------

def _mock_api_response() -> str:
    return json.dumps({
        "current_haircut_assessment": "Taper fade — well suited to square face",
        "recommended_haircut": "Keep taper fade with soft texture on top",
        "haircut_to_avoid": "Bowl cut or boxy styles",
        "styling_product_recommendation": ["matte clay", "light pomade"],
        "hair_color_recommendation": "Keep natural black",
        "current_beard_assessment": "Full dense beard, well groomed",
        "recommended_beard_style": "Trim cheek line, extend chin",
        "beard_grooming_tips": ["Trim sides shorter", "Let chin grow"],
        "beard_style_to_avoid": "Wide cheek coverage",
        "eyebrow_assessment": "Natural, proportional",
        "eyebrow_recommendation": "Maintain natural arch",
        "visible_skin_concerns": [],
        "skincare_categories_needed": ["moisturiser", "SPF"],
        "grooming_score": 8,
        "grooming_remarks": [
            {
                "severity": "minor",
                "category": "grooming_beard",
                "body_zone": "face",
                "element": "beard",
                "issue": "Beard sides add width to square jaw",
                "fix": "Trim cheek line 0.5cm higher",
                "why": "Reduces jaw width emphasis",
                "priority_order": 1,
            }
        ],
    })


def test_api_enrichment_returns_profile():
    with patch("src.agents.grooming_agent.call_text", return_value=_mock_api_response()):
        profile = _make_profile()
        result = generate_grooming_profile(profile, use_api=True)
    assert isinstance(result, GroomingProfile)
    assert result.grooming_score == 8


def test_api_failure_falls_back_to_rule_based():
    with patch("src.agents.grooming_agent.call_text", side_effect=Exception("API down")):
        profile = _make_profile()
        result = generate_grooming_profile(profile, use_api=True)
    assert isinstance(result, GroomingProfile)
    assert 1 <= result.grooming_score <= 10


def test_grooming_remarks_in_api_output():
    with patch("src.agents.grooming_agent.call_text", return_value=_mock_api_response()):
        profile = _make_profile()
        result = generate_grooming_profile(profile, use_api=True)
    assert len(result.grooming_remarks) >= 1


def test_beard_grooming_tips_not_empty_api():
    with patch("src.agents.grooming_agent.call_text", return_value=_mock_api_response()):
        profile = _make_profile()
        result = generate_grooming_profile(profile, use_api=True)
    assert len(result.beard_grooming_tips) >= 1
