"""Unit tests for fashion_knowledge/grooming_guide.py — Step 4."""

import pytest

from src.models.user_profile import FaceShape
from src.fashion_knowledge.grooming_guide import (
    get_haircut_rules,
    get_beard_rules,
    get_eyebrow_recommendation,
    score_beard_grooming,
)


# ---------------------------------------------------------------------------
# Haircut rules
# ---------------------------------------------------------------------------

def test_oval_face_most_haircuts_valid():
    rules = get_haircut_rules(FaceShape.OVAL)
    assert any("most cuts" in r or "most" in r for r in rules.recommended)


def test_square_face_avoids_boxy():
    rules = get_haircut_rules(FaceShape.SQUARE)
    assert any("boxy" in a for a in rules.avoid)


def test_round_face_adds_height():
    rules = get_haircut_rules(FaceShape.ROUND)
    assert any("height" in r for r in rules.recommended)


def test_oblong_face_adds_width_not_height():
    rules = get_haircut_rules(FaceShape.OBLONG)
    assert any("width" in r or "side" in r for r in rules.recommended)
    assert any("height" in a for a in rules.avoid)


def test_heart_face_soft_fringe():
    rules = get_haircut_rules(FaceShape.HEART)
    assert any("fringe" in r or "side" in r for r in rules.recommended)


def test_diamond_face_maintains_width():
    rules = get_haircut_rules(FaceShape.DIAMOND)
    assert any("width" in r or "forehead" in r for r in rules.recommended)


def test_all_face_shapes_have_haircut_rules():
    for shape in FaceShape:
        rules = get_haircut_rules(shape)
        assert len(rules.recommended) >= 1, f"{shape} missing haircut recommendations"


# ---------------------------------------------------------------------------
# Beard rules
# ---------------------------------------------------------------------------

def test_beard_round_elongates_chin():
    rules = get_beard_rules(FaceShape.ROUND)
    assert any("chin" in r and ("extend" in r or "elongate" in r) for r in rules.recommended)


def test_beard_heart_fuller_chin():
    rules = get_beard_rules(FaceShape.HEART)
    assert any("chin" in r and "fuller" in r or "fuller chin" in r for r in rules.recommended)


def test_beard_square_longer_chin_shorter_sides():
    rules = get_beard_rules(FaceShape.SQUARE)
    combined = " ".join(rules.recommended).lower()
    assert "chin" in combined
    assert "shorter" in combined or "trimmed" in combined or "sides" in combined


def test_beard_diamond_full_jaw_clean_cheeks():
    rules = get_beard_rules(FaceShape.DIAMOND)
    assert any("jaw" in r or "full" in r for r in rules.recommended)
    assert any("cheek" in a for a in rules.avoid)


def test_beard_oblong_avoid_long_chin():
    rules = get_beard_rules(FaceShape.OBLONG)
    avoid_text = " ".join(rules.avoid).lower()
    assert "chin" in avoid_text or "elongates" in avoid_text or "long" in avoid_text


def test_oval_face_beard_any_style():
    rules = get_beard_rules(FaceShape.OVAL)
    combined = " ".join(rules.recommended).lower()
    assert "any style" in combined or "any" in combined


def test_all_face_shapes_have_beard_rules():
    for shape in FaceShape:
        rules = get_beard_rules(shape)
        assert len(rules.recommended) >= 1, f"{shape} missing beard recommendations"


# ---------------------------------------------------------------------------
# Eyebrow recommendations
# ---------------------------------------------------------------------------

def test_eyebrow_recommendation_not_empty():
    for shape in FaceShape:
        rec = get_eyebrow_recommendation(shape)
        assert isinstance(rec, str) and len(rec) > 5, f"{shape} has empty eyebrow rec"


def test_eyebrow_oval_mentions_arch():
    rec = get_eyebrow_recommendation(FaceShape.OVAL)
    assert "arch" in rec.lower()


def test_eyebrow_round_adds_height():
    rec = get_eyebrow_recommendation(FaceShape.ROUND)
    assert "arch" in rec.lower() or "length" in rec.lower()


# ---------------------------------------------------------------------------
# Grooming score
# ---------------------------------------------------------------------------

def test_grooming_score_1_to_10():
    for quality in ["well groomed", "average", "unkempt", "not applicable"]:
        score = score_beard_grooming(quality)
        assert 1 <= score <= 10, f"Score out of range for quality: {quality}"


def test_grooming_score_well_groomed_highest():
    assert score_beard_grooming("well groomed") > score_beard_grooming("unkempt")


def test_grooming_score_unknown_defaults_to_midrange():
    score = score_beard_grooming("unknown_quality")
    assert 1 <= score <= 10
