"""Unit tests for fashion_knowledge/western_wear.py — Step 8."""

import pytest

from src.models.user_profile import FaceShape
from src.fashion_knowledge.western_wear import (
    trouser_break,
    collar_face_compatible,
    validate_layering,
    trouser_shoe_appropriate,
    belt_shoe_compatible,
    no_belt_needed,
)


# ---------------------------------------------------------------------------
# Trouser break
# ---------------------------------------------------------------------------

def test_tall_no_break():
    result = trouser_break("tall")
    assert "no break" in result.lower() or "slight" in result.lower()


def test_petite_no_break_always():
    result = trouser_break("petite")
    assert "no break" in result.lower()


def test_average_half_break():
    result = trouser_break("average")
    assert "half" in result.lower() or "break" in result.lower()


# ---------------------------------------------------------------------------
# Collar + face shape
# ---------------------------------------------------------------------------

def test_spread_collar_not_round_face():
    ok, issue = collar_face_compatible("spread collar", FaceShape.ROUND)
    assert ok is False
    assert len(issue) > 0


def test_button_down_oval_ok():
    ok, _ = collar_face_compatible("button-down", FaceShape.OVAL)
    assert ok is True


def test_spread_collar_square_ok():
    ok, _ = collar_face_compatible("spread collar", FaceShape.SQUARE)
    assert ok is True


def test_band_collar_oval_ok():
    ok, _ = collar_face_compatible("band collar", FaceShape.OVAL)
    assert ok is True


def test_unknown_collar_no_ruling():
    ok, issue = collar_face_compatible("polo collar", FaceShape.ROUND)
    assert ok is True
    assert issue == ""


# ---------------------------------------------------------------------------
# Layering
# ---------------------------------------------------------------------------

def test_layering_heavier_outer():
    """Heavier outer is correct — should return no issues."""
    issues = validate_layering("light", "heavy", "slim", "relaxed")
    assert len(issues) == 0


def test_layering_lighter_outer_flagged():
    issues = validate_layering("heavy", "light", "regular", "slim")
    assert len(issues) >= 1
    combined = " ".join(issues).lower()
    assert "heavier" in combined or "outer" in combined


def test_layering_slimmer_outer_flagged():
    """Outer layer slimmer than base is wrong."""
    issues = validate_layering("light", "medium", "relaxed", "slim")
    assert len(issues) >= 1


def test_layering_correct_no_issues():
    issues = validate_layering("light", "heavy", "slim", "relaxed")
    assert issues == []


# ---------------------------------------------------------------------------
# Trouser + shoe pairing
# ---------------------------------------------------------------------------

def test_slim_trouser_loafer_derby():
    ok, _ = trouser_shoe_appropriate("slim", "loafers")
    assert ok is True
    ok2, _ = trouser_shoe_appropriate("slim", "derbies")
    assert ok2 is True


def test_formal_tailored_no_loafers():
    ok, issue = trouser_shoe_appropriate("formal tailored", "loafers")
    assert ok is False


def test_formal_tailored_oxford_ok():
    ok, _ = trouser_shoe_appropriate("formal tailored", "oxford")
    assert ok is True


def test_wide_trouser_chunky_sneakers_ok():
    ok, _ = trouser_shoe_appropriate("wide", "chunky sneakers")
    assert ok is True


# ---------------------------------------------------------------------------
# Belt + shoe colour
# ---------------------------------------------------------------------------

def test_black_belt_black_shoe():
    ok, _ = belt_shoe_compatible("black", "black")
    assert ok is True


def test_brown_belt_cognac_ok():
    ok, _ = belt_shoe_compatible("brown", "cognac")
    assert ok is True


def test_black_belt_brown_shoe_fail():
    ok, issue = belt_shoe_compatible("black", "brown")
    assert ok is False


# ---------------------------------------------------------------------------
# No belt situations
# ---------------------------------------------------------------------------

def test_no_belt_denim_ok():
    assert no_belt_needed("denim", "untucked shirt") is True


def test_no_belt_jeans_untucked():
    assert no_belt_needed("jeans", "untucked") is True


def test_belt_needed_for_chinos_tucked():
    assert no_belt_needed("chinos", "tucked shirt") is False


def test_no_belt_suit_suspenders():
    assert no_belt_needed("tailored suit", "suspenders") is True
