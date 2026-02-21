"""Unit tests for fashion_knowledge/body_types.py — Step 3."""

import pytest

from src.models.user_profile import BodyShape
from src.fashion_knowledge.body_types import (
    get_rules,
    get_do,
    get_avoid,
    kurta_length,
    all_shapes_covered,
)


# ---------------------------------------------------------------------------
# Rectangle
# ---------------------------------------------------------------------------

def test_rectangle_belted_silhouette_in_do():
    do = get_do(BodyShape.RECTANGLE)
    assert any("belted" in item for item in do)


def test_rectangle_avoids_boxy():
    avoid = get_avoid(BodyShape.RECTANGLE)
    assert any("boxy" in item for item in avoid)


# ---------------------------------------------------------------------------
# Inverted Triangle
# ---------------------------------------------------------------------------

def test_inverted_triangle_no_shoulder_padding():
    avoid = get_avoid(BodyShape.INVERTED_TRIANGLE)
    assert any("shoulder padding" in item for item in avoid)


def test_inverted_triangle_longer_hemline_recommended():
    do = get_do(BodyShape.INVERTED_TRIANGLE)
    assert any("longer" in item or "mid-thigh" in item for item in do)


def test_inverted_triangle_no_horizontal_stripes_on_chest():
    avoid = get_avoid(BodyShape.INVERTED_TRIANGLE)
    assert any("horizontal" in item for item in avoid)


# ---------------------------------------------------------------------------
# Triangle
# ---------------------------------------------------------------------------

def test_triangle_darker_bottom_in_do():
    do = get_do(BodyShape.TRIANGLE)
    assert any("darker bottom" in item for item in do)


def test_triangle_avoids_hip_horizontal():
    avoid = get_avoid(BodyShape.TRIANGLE)
    assert any("hip" in item for item in avoid)


# ---------------------------------------------------------------------------
# Oval
# ---------------------------------------------------------------------------

def test_oval_vertical_lines_in_do():
    do = get_do(BodyShape.OVAL)
    assert any("vertical" in item for item in do)


def test_oval_avoids_horizontal_waist_band():
    avoid = get_avoid(BodyShape.OVAL)
    assert any("horizontal" in item for item in avoid)


# ---------------------------------------------------------------------------
# Trapezoid
# ---------------------------------------------------------------------------

def test_trapezoid_balanced_proportion():
    do = get_do(BodyShape.TRAPEZOID)
    assert any("proportion" in item or "most silhouettes" in item for item in do)


def test_trapezoid_avoids_bulk_everywhere():
    avoid = get_avoid(BodyShape.TRAPEZOID)
    assert any("bulk" in item for item in avoid)


# ---------------------------------------------------------------------------
# Completeness
# ---------------------------------------------------------------------------

def test_every_type_has_do_and_dont():
    for shape in BodyShape:
        rules = get_rules(shape)
        assert len(rules.do) >= 2, f"{shape} missing do items"
        assert len(rules.avoid) >= 1, f"{shape} missing avoid items"


def test_all_shapes_covered():
    assert all_shapes_covered() is True


# ---------------------------------------------------------------------------
# Kurta length
# ---------------------------------------------------------------------------

def test_kurta_length_tall_mid_thigh():
    result = kurta_length("tall", BodyShape.RECTANGLE)
    assert "mid-thigh" in result or "below" in result


def test_kurta_length_petite_hip_only():
    result = kurta_length("petite", BodyShape.OVAL)
    assert "hip" in result
    # Must warn against going longer
    assert "never" in result or "shorter" in result or "shortens" in result


def test_kurta_length_tall_inverted_triangle():
    result = kurta_length("tall", BodyShape.INVERTED_TRIANGLE)
    assert "mid-thigh" in result


def test_kurta_length_petite_inverted_triangle():
    # Petite always wins over inverted triangle body rule
    result = kurta_length("petite", BodyShape.INVERTED_TRIANGLE)
    assert "hip" in result


def test_kurta_length_average_rectangle():
    result = kurta_length("average", BodyShape.RECTANGLE)
    assert "hip" in result or "mid-thigh" in result
