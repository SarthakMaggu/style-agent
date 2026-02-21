"""Unit tests for fashion_knowledge/footwear_guide.py — Step 6."""

import pytest

from src.fashion_knowledge.footwear_guide import (
    get_footwear_rules,
    is_footwear_appropriate,
    assess_condition,
    all_occasions_covered,
)


# ---------------------------------------------------------------------------
# Occasion-appropriate footwear
# ---------------------------------------------------------------------------

def test_sherwani_requires_mojari():
    """Indian formal occasion allows mojaris."""
    rules = get_footwear_rules("indian_formal")
    assert rules is not None
    allowed_flat = " ".join(rules.allowed).lower()
    assert "mojaris" in allowed_flat or "juttis" in allowed_flat


def test_sneakers_critical_with_sherwani():
    """Sneakers must be flagged for indian_formal."""
    ok, issue = is_footwear_appropriate("sneakers", "indian_formal")
    assert ok is False
    assert len(issue) > 0


def test_western_formal_requires_oxford_derby_monk():
    rules = get_footwear_rules("western_formal")
    assert rules is not None
    allowed_flat = " ".join(rules.allowed).lower()
    assert "oxford" in allowed_flat or "derby" in allowed_flat or "monk" in allowed_flat


def test_sneakers_flagged_western_formal():
    ok, issue = is_footwear_appropriate("sneakers", "western_formal")
    assert ok is False


def test_streetwear_allows_clean_sneakers():
    ok, issue = is_footwear_appropriate("sneakers", "streetwear")
    assert ok is True


def test_mojaris_ok_indian_formal():
    ok, issue = is_footwear_appropriate("mojaris", "indian_formal")
    assert ok is True


def test_loafers_ok_business_casual():
    ok, issue = is_footwear_appropriate("loafers", "business_casual")
    assert ok is True


# ---------------------------------------------------------------------------
# Condition severity
# ---------------------------------------------------------------------------

def test_dirty_sneakers_critical():
    assessment = assess_condition("dirty")
    assert assessment.severity == "critical"


def test_scuffed_leather_moderate():
    assessment = assess_condition("scuffed")
    assert assessment.severity == "moderate"


def test_sole_peeling_critical():
    assessment = assess_condition("sole peeling")
    assert assessment.severity == "critical"


def test_yellowed_sole_moderate():
    assessment = assess_condition("yellowed sole")
    assert assessment.severity == "moderate"


def test_clean_no_severity():
    assessment = assess_condition("clean")
    assert assessment.severity == "none"
    assert assessment.issue == ""


def test_worn_out_critical():
    assessment = assess_condition("worn out")
    assert assessment.severity == "critical"


# ---------------------------------------------------------------------------
# Shoe care notes
# ---------------------------------------------------------------------------

def test_shoe_care_note_populated_when_bad():
    for condition in ["scuffed", "dirty", "sole peeling", "yellowed sole", "worn out"]:
        assessment = assess_condition(condition)
        assert len(assessment.shoe_care_note) > 0, f"No care note for: {condition}"


def test_clean_has_no_care_note():
    assessment = assess_condition("clean")
    assert assessment.shoe_care_note == ""


# ---------------------------------------------------------------------------
# Completeness
# ---------------------------------------------------------------------------

def test_all_occasions_covered():
    assert all_occasions_covered() is True


def test_unknown_occasion_returns_none():
    rules = get_footwear_rules("nonexistent_occasion")
    assert rules is None


def test_unknown_footwear_unknown_occasion_defaults_appropriate():
    ok, issue = is_footwear_appropriate("sneakers", "nonexistent_occasion")
    assert ok is True  # No ruling → no penalty
