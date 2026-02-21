"""Unit tests for agents/vision_agent.py — Step 12 (all mocked)."""

import json
import pytest
from unittest.mock import patch, MagicMock

from src.agents.vision_agent import analyse_outfit, _build_outfit_breakdown
from src.models.outfit import OutfitBreakdown


# ---------------------------------------------------------------------------
# Mock response factories
# ---------------------------------------------------------------------------

def _mock_indian_outfit_response(occasion_match: bool = False) -> dict:
    return {
        "occasion_detected": "indian_casual",
        "occasion_requested": "wedding_guest_indian",
        "occasion_match": occasion_match,
        "items": [
            {
                "category": "ethnic-top",
                "garment_type": "kurta",
                "color": "ivory",
                "pattern": "solid",
                "fabric_estimate": "cotton",
                "fit": "straight",
                "length": "hip",
                "collar_type": "mandarin",
                "sleeve_type": "full",
                "condition": "good",
                "occasion_appropriate": False,
                "issue": "Hip-length cotton kurta is under-dressed for a wedding",
                "fix": "Switch to mid-thigh silk-cotton blend kurta",
            }
        ],
        "accessory_analysis": {
            "items_detected": [
                {
                    "type": "watch",
                    "color": "silver/black",
                    "material_estimate": "rubber strap",
                    "style_category": "sport",
                    "condition": "good",
                    "occasion_appropriate": False,
                    "issue": "Sport watch at a wedding",
                    "fix": "Swap to leather strap",
                }
            ],
            "missing_accessories": ["pocket square"],
            "accessories_to_remove": [],
            "accessory_harmony": "Neutral",
            "overall_score": 4,
        },
        "footwear_analysis": {
            "visible": True,
            "type": "oxford",
            "color": "brown",
            "material_estimate": "leather",
            "condition": "scuffed",
            "style_category": "western formal",
            "occasion_match": False,
            "outfit_match": False,
            "issue": "Western oxfords with Indian ethnic wear",
            "recommended_instead": "Mojaris or juttis",
            "shoe_care_note": "Polish before next wear",
        },
        "overall_color_harmony": "Clashing",
        "color_clash_detected": True,
        "silhouette_assessment": "Top-heavy",
        "proportion_assessment": "Imbalanced",
        "formality_level": 6,
        "outfit_score": 4,
    }


def _mock_western_outfit_response() -> dict:
    return {
        "occasion_detected": "western_business_casual",
        "occasion_requested": "business_casual",
        "occasion_match": True,
        "items": [
            {
                "category": "top",
                "garment_type": "oxford shirt",
                "color": "light blue",
                "pattern": "solid",
                "fabric_estimate": "cotton poplin",
                "fit": "slim",
                "length": "hip",
                "collar_type": "button-down",
                "sleeve_type": "full",
                "condition": "excellent",
                "occasion_appropriate": True,
                "issue": "",
                "fix": "",
            },
            {
                "category": "bottom",
                "garment_type": "chinos",
                "color": "navy",
                "pattern": "solid",
                "fabric_estimate": "cotton",
                "fit": "slim",
                "length": "ankle",
                "collar_type": "n/a",
                "sleeve_type": "n/a",
                "condition": "good",
                "occasion_appropriate": True,
                "issue": "",
                "fix": "",
            },
        ],
        "accessory_analysis": {
            "items_detected": [],
            "missing_accessories": ["watch"],
            "accessories_to_remove": [],
            "accessory_harmony": "Minimal",
            "overall_score": 6,
        },
        "footwear_analysis": {
            "visible": True,
            "type": "loafers",
            "color": "tan",
            "material_estimate": "leather",
            "condition": "clean",
            "style_category": "business casual",
            "occasion_match": True,
            "outfit_match": True,
            "issue": "",
            "recommended_instead": "",
            "shoe_care_note": "",
        },
        "overall_color_harmony": "Harmonious",
        "color_clash_detected": False,
        "silhouette_assessment": "Well proportioned",
        "proportion_assessment": "Balanced",
        "formality_level": 6,
        "outfit_score": 7,
    }


def _no_footwear_response() -> dict:
    resp = _mock_western_outfit_response()
    resp["footwear_analysis"] = {
        "visible": False,
        "type": "",
        "color": "",
        "material_estimate": "",
        "condition": "",
        "style_category": "",
        "occasion_match": False,
        "outfit_match": False,
        "issue": "",
        "recommended_instead": "",
        "shoe_care_note": "",
    }
    return resp


# ---------------------------------------------------------------------------
# Tests using _build_outfit_breakdown directly (no API call)
# ---------------------------------------------------------------------------

def test_returns_valid_outfit_breakdown():
    breakdown = _build_outfit_breakdown(_mock_indian_outfit_response())
    assert isinstance(breakdown, OutfitBreakdown)


def test_detects_minimum_one_garment():
    breakdown = _build_outfit_breakdown(_mock_indian_outfit_response())
    assert len(breakdown.items) >= 1


def test_detects_accessories_when_visible():
    breakdown = _build_outfit_breakdown(_mock_indian_outfit_response())
    assert len(breakdown.accessory_analysis.items_detected) >= 1


def test_empty_accessory_list_when_none():
    breakdown = _build_outfit_breakdown(_mock_western_outfit_response())
    assert breakdown.accessory_analysis.items_detected == []


def test_footwear_visible_true_when_in_frame():
    breakdown = _build_outfit_breakdown(_mock_indian_outfit_response())
    assert breakdown.footwear_analysis.visible is True


def test_footwear_visible_false_when_not():
    breakdown = _build_outfit_breakdown(_no_footwear_response())
    assert breakdown.footwear_analysis.visible is False
    assert breakdown.footwear_analysis.type == ""


def test_indian_garment_detected():
    breakdown = _build_outfit_breakdown(_mock_indian_outfit_response())
    garment_types = [g.garment_type.lower() for g in breakdown.items]
    assert any("kurta" in g for g in garment_types)


def test_western_garment_detected():
    breakdown = _build_outfit_breakdown(_mock_western_outfit_response())
    garment_types = [g.garment_type.lower() for g in breakdown.items]
    assert any("shirt" in g or "chino" in g for g in garment_types)


def test_occasion_mismatch_flagged():
    breakdown = _build_outfit_breakdown(_mock_indian_outfit_response(occasion_match=False))
    assert breakdown.occasion_match is False


def test_color_clash_detected():
    breakdown = _build_outfit_breakdown(_mock_indian_outfit_response())
    assert breakdown.color_clash_detected is True


def test_outfit_score_range():
    breakdown = _build_outfit_breakdown(_mock_indian_outfit_response())
    assert 1 <= breakdown.outfit_score <= 10


# ---------------------------------------------------------------------------
# Tests using mocked API call (analyse_outfit)
# ---------------------------------------------------------------------------

def test_analyse_outfit_calls_vision_api():
    """analyse_outfit should call call_vision and return OutfitBreakdown."""
    mock_response = json.dumps(_mock_western_outfit_response())
    with patch("src.agents.vision_agent.call_vision", return_value=mock_response):
        breakdown = analyse_outfit("fake_base64", "image/jpeg", "business_casual")
    assert isinstance(breakdown, OutfitBreakdown)
    assert breakdown.occasion_requested == "business_casual"


def test_analyse_outfit_low_quality_handled():
    """Vision agent must not crash on minimal / sparse data."""
    sparse = {
        "occasion_detected": "casual",
        "occasion_requested": "auto",
        "occasion_match": True,
        "items": [],
        "accessory_analysis": {
            "items_detected": [],
            "missing_accessories": [],
            "accessories_to_remove": [],
            "accessory_harmony": "N/A",
            "overall_score": 5,
        },
        "footwear_analysis": {
            "visible": False,
            "type": "",
            "color": "",
            "material_estimate": "",
            "condition": "",
            "style_category": "",
            "occasion_match": False,
            "outfit_match": False,
            "issue": "",
            "recommended_instead": "",
            "shoe_care_note": "",
        },
        "overall_color_harmony": "Unknown",
        "color_clash_detected": False,
        "silhouette_assessment": "Not determined",
        "proportion_assessment": "Not determined",
        "formality_level": 5,
        "outfit_score": 5,
    }
    breakdown = _build_outfit_breakdown(sparse)
    assert isinstance(breakdown, OutfitBreakdown)
    assert breakdown.items == []


def test_vision_api_failure_raises_runtime_error():
    """analyse_outfit should raise RuntimeError on API failure."""
    with patch("src.agents.vision_agent.call_vision", side_effect=Exception("network error")):
        with pytest.raises(RuntimeError, match="Vision analysis failed"):
            analyse_outfit("fake_base64")


def test_fusion_detected():
    fusion_data = {
        **_mock_indian_outfit_response(),
        "occasion_detected": "ethnic_fusion",
        "items": [
            {
                "category": "ethnic-top",
                "garment_type": "kurta",
                "color": "navy",
                "pattern": "solid",
                "fabric_estimate": "cotton",
                "fit": "straight",
                "length": "mid-thigh",
                "collar_type": "mandarin",
                "sleeve_type": "full",
                "condition": "good",
                "occasion_appropriate": True,
                "issue": "",
                "fix": "",
            },
            {
                "category": "bottom",
                "garment_type": "dark slim jeans",
                "color": "dark blue",
                "pattern": "solid",
                "fabric_estimate": "denim",
                "fit": "slim",
                "length": "ankle",
                "collar_type": "n/a",
                "sleeve_type": "n/a",
                "condition": "good",
                "occasion_appropriate": True,
                "issue": "",
                "fix": "",
            },
        ],
    }
    breakdown = _build_outfit_breakdown(fusion_data)
    assert breakdown.occasion_detected == "ethnic_fusion"
    garment_types = [g.garment_type.lower() for g in breakdown.items]
    assert any("kurta" in g for g in garment_types)
    assert any("jeans" in g or "denim" in g for g in garment_types)
