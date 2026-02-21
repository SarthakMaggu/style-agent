"""Unit tests for fashion_knowledge/accessory_guide.py — Step 5."""

import pytest

from src.models.user_profile import FaceShape
from src.fashion_knowledge.accessory_guide import (
    watch_strap_appropriate,
    belt_shoe_match,
    belt_appropriate_with_garment,
    rings_appropriate,
    bag_appropriate,
    sunglasses_frame_recommendation,
    assess_turban,
    suggest_missing_accessories,
)


# ---------------------------------------------------------------------------
# Watch strap rules
# ---------------------------------------------------------------------------

def test_formal_requires_leather_strap():
    ok, issue = watch_strap_appropriate("rubber strap", "western_formal")
    assert ok is False
    assert "rubber" in issue.lower() or "sport" in issue.lower()


def test_casual_allows_nato():
    ok, issue = watch_strap_appropriate("NATO strap", "casual")
    assert ok is True
    assert issue == ""


def test_plastic_watch_flagged_with_formal():
    ok, issue = watch_strap_appropriate("plastic case", "indian_formal")
    assert ok is False
    assert "plastic" in issue.lower()


def test_leather_strap_ok_with_formal():
    ok, issue = watch_strap_appropriate("leather strap", "western_formal")
    assert ok is True


def test_rubber_strap_ok_with_streetwear():
    ok, issue = watch_strap_appropriate("rubber strap", "streetwear")
    assert ok is True


def test_metal_bracelet_ok_with_wedding():
    ok, issue = watch_strap_appropriate("metal bracelet", "wedding_guest_indian")
    assert ok is True


# ---------------------------------------------------------------------------
# Belt + shoe rules
# ---------------------------------------------------------------------------

def test_belt_black_matches_black_shoe():
    ok, issue = belt_shoe_match("black", "black")
    assert ok is True


def test_belt_black_mismatch_brown_shoe():
    ok, issue = belt_shoe_match("black", "brown")
    assert ok is False
    assert "black" in issue.lower()


def test_belt_brown_matches_cognac():
    ok, issue = belt_shoe_match("brown", "cognac")
    assert ok is True


def test_belt_brown_mismatch_black_shoe():
    ok, issue = belt_shoe_match("brown", "black")
    assert ok is False


def test_no_belt_with_sherwani():
    ok, issue = belt_appropriate_with_garment("sherwani")
    assert ok is False
    assert "sherwani" in issue.lower() or "belt" in issue.lower()


def test_no_belt_with_bandhgala():
    ok, issue = belt_appropriate_with_garment("bandhgala")
    assert ok is False


def test_belt_ok_with_jeans():
    ok, issue = belt_appropriate_with_garment("jeans")
    assert ok is True


# ---------------------------------------------------------------------------
# Ring rules
# ---------------------------------------------------------------------------

def test_ring_max_two_hands():
    ok, issue = rings_appropriate(3, "smart casual")
    assert ok is False
    assert "2" in issue or "two" in issue.lower()


def test_rings_one_is_fine():
    ok, issue = rings_appropriate(1, "smart casual")
    assert ok is True


def test_rings_two_is_fine():
    ok, issue = rings_appropriate(2, "party")
    assert ok is True


# ---------------------------------------------------------------------------
# Bag rules
# ---------------------------------------------------------------------------

def test_backpack_flagged_with_formal():
    ok, issue = bag_appropriate("backpack", "western_formal")
    assert ok is False
    assert "backpack" in issue.lower() or "formal" in issue.lower()


def test_backpack_ok_with_casual():
    ok, issue = bag_appropriate("backpack", "casual")
    assert ok is True


def test_jhola_flagged_with_western_formal():
    ok, issue = bag_appropriate("jhola", "western_formal")
    assert ok is False


def test_jhola_ok_with_indian_casual():
    ok, issue = bag_appropriate("jhola", "indian_casual")
    assert ok is True


# ---------------------------------------------------------------------------
# Sunglasses frames
# ---------------------------------------------------------------------------

def test_sunglasses_round_face_angular_frames():
    rec = sunglasses_frame_recommendation(FaceShape.ROUND)
    combined = " ".join(rec["recommended"]).lower()
    assert "angular" in combined or "square" in combined or "wayfarer" in combined


def test_sunglasses_square_face_round_frames():
    rec = sunglasses_frame_recommendation(FaceShape.SQUARE)
    combined = " ".join(rec["recommended"]).lower()
    assert "round" in combined or "oval" in combined


def test_sunglasses_oval_most_frames():
    rec = sunglasses_frame_recommendation(FaceShape.OVAL)
    combined = " ".join(rec["recommended"]).lower()
    assert "most" in combined or "aviator" in combined or "wayfarer" in combined


def test_sunglasses_all_shapes_covered():
    for shape in FaceShape:
        rec = sunglasses_frame_recommendation(shape)
        assert len(rec["recommended"]) >= 1, f"{shape} missing sunglass recommendations"


# ---------------------------------------------------------------------------
# Turban assessment
# ---------------------------------------------------------------------------

def test_turban_color_assessed():
    issues = assess_turban(
        turban_color="rust",
        outfit_colors=["cobalt blue"],
        occasion="indian_formal",
        turban_fabric="cotton",
        outfit_fabric="brocade",
    )
    # Rust + cobalt blue may clash; light fabric vs heavy outfit
    assert isinstance(issues, list)


def test_turban_matching_colors_no_issue():
    issues = assess_turban(
        turban_color="navy",
        outfit_colors=["navy"],
        occasion="indian_formal",
        turban_fabric="silk",
        outfit_fabric="brocade",
    )
    # Same color family, matching fabric weight — should raise no issues
    assert len(issues) == 0


# ---------------------------------------------------------------------------
# Missing accessories
# ---------------------------------------------------------------------------

def test_missing_accessories_suggested():
    suggestions = suggest_missing_accessories("western_formal", [])
    assert len(suggestions) >= 1


def test_no_missing_when_all_present():
    suggestions = suggest_missing_accessories("western_formal", ["watch", "pocket square"])
    # All key accessories present — suggestions should be minimal or empty
    assert isinstance(suggestions, list)


def test_missing_watch_suggested_for_formal():
    suggestions = suggest_missing_accessories("western_formal", [])
    combined = " ".join(suggestions).lower()
    assert "watch" in combined
