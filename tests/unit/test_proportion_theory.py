"""Unit tests for proportion_theory.py — Step 4 (Phase C2)."""

import pytest

from src.fashion_knowledge.proportion_theory import (
    get_proportion_rules,
    proportion_context_string,
    pattern_scale_recommendation,
    fabric_texture_recommendation,
)


# ---------------------------------------------------------------------------
# Matrix completeness — all 15 combinations must exist
# ---------------------------------------------------------------------------

_HEIGHTS = ("tall", "average", "petite")
_SHAPES  = ("rectangle", "triangle", "inverted_triangle", "oval", "trapezoid")


def test_all_15_combinations_covered():
    """Every height × shape combination must return a ProportionRules object."""
    for height in _HEIGHTS:
        for shape in _SHAPES:
            rules = get_proportion_rules(height, shape)
            assert rules.height == height
            assert rules.body_shape == shape


def test_invalid_combination_raises():
    """Unknown height or shape must raise ValueError."""
    with pytest.raises(ValueError, match="No proportion rules"):
        get_proportion_rules("giant", "rectangle")

    with pytest.raises(ValueError, match="No proportion rules"):
        get_proportion_rules("tall", "hourglass")


# ---------------------------------------------------------------------------
# Trouser break rules
# ---------------------------------------------------------------------------


def test_trouser_break_tall_is_slight_or_none():
    """Tall frames should have 'none' or 'slight' break — never 'half' or more."""
    for shape in _SHAPES:
        rules = get_proportion_rules("tall", shape)
        assert rules.trouser_break in {"none", "slight"}, (
            f"tall/{shape}: unexpected break '{rules.trouser_break}'"
        )


def test_trouser_break_petite_is_always_none():
    """Every petite combination must have no trouser break — critical for height."""
    for shape in _SHAPES:
        rules = get_proportion_rules("petite", shape)
        assert rules.trouser_break == "none", (
            f"petite/{shape}: expected 'none', got '{rules.trouser_break}'"
        )


def test_trouser_break_average_is_half_or_slight():
    """Average height gets half or slight break as the safe default."""
    for shape in _SHAPES:
        rules = get_proportion_rules("average", shape)
        assert rules.trouser_break in {"half", "slight", "none"}, (
            f"average/{shape}: unexpected break '{rules.trouser_break}'"
        )


# ---------------------------------------------------------------------------
# Kurta length rules
# ---------------------------------------------------------------------------


def test_kurta_length_petite_oval_not_below_knee():
    """Petite oval: kurta must not go below knee — shortens too much."""
    rules = get_proportion_rules("petite", "oval")
    assert "below" not in rules.kurta_length.lower() or "never" in rules.kurta_length.lower()


def test_kurta_length_tall_inverted_triangle_mid_thigh_or_longer():
    """Tall inverted triangle needs mid-thigh or longer to balance wide shoulders."""
    rules = get_proportion_rules("tall", "inverted_triangle")
    assert "mid-thigh" in rules.kurta_length.lower() or "below" in rules.kurta_length.lower()


def test_kurta_length_petite_all_shapes_hip():
    """Every petite combination should have 'hip' in the kurta_length."""
    for shape in _SHAPES:
        rules = get_proportion_rules("petite", shape)
        assert "hip" in rules.kurta_length.lower(), (
            f"petite/{shape}: expected 'hip' in kurta_length, got '{rules.kurta_length}'"
        )


# ---------------------------------------------------------------------------
# Belt use rules
# ---------------------------------------------------------------------------


def test_belt_use_oval_is_avoid():
    """Oval body shape: belt marks the widest zone — must be avoided."""
    for height in _HEIGHTS:
        rules = get_proportion_rules(height, "oval")
        assert rules.belt_use == "avoid", (
            f"{height}/oval: belt_use should be 'avoid', got '{rules.belt_use}'"
        )


def test_belt_use_rectangle_emphasises():
    """Rectangle body shape: belt creates waist definition — must be emphasised."""
    for height in _HEIGHTS:
        rules = get_proportion_rules(height, "rectangle")
        assert rules.belt_use == "emphasise", (
            f"{height}/rectangle: belt_use should be 'emphasise', got '{rules.belt_use}'"
        )


# ---------------------------------------------------------------------------
# All rules have required non-empty fields
# ---------------------------------------------------------------------------


def test_all_rules_have_do_and_avoid_items():
    """Every ProportionRules entry must have at least one do and one avoid item."""
    for height in _HEIGHTS:
        for shape in _SHAPES:
            rules = get_proportion_rules(height, shape)
            assert len(rules.do) > 0, f"{height}/{shape}: empty 'do' list"
            assert len(rules.avoid) > 0, f"{height}/{shape}: empty 'avoid' list"


def test_all_rules_have_layer_strategy():
    """Every combination must have a non-empty layer strategy."""
    for height in _HEIGHTS:
        for shape in _SHAPES:
            rules = get_proportion_rules(height, shape)
            assert rules.layer_strategy, f"{height}/{shape}: empty layer_strategy"


# ---------------------------------------------------------------------------
# proportion_context_string
# ---------------------------------------------------------------------------


def test_proportion_context_string_not_empty():
    """Context string for a valid combination must be non-empty."""
    result = proportion_context_string("average", "inverted_triangle")
    assert isinstance(result, str)
    assert len(result) > 50


def test_proportion_context_string_empty_for_invalid():
    """Invalid inputs must return empty string (not raise)."""
    result = proportion_context_string("giant", "hourglass")
    assert result == ""


def test_proportion_context_string_contains_visual_goal():
    """The context string must include the visual goal text."""
    rules = get_proportion_rules("tall", "oval")
    ctx = proportion_context_string("tall", "oval")
    assert rules.visual_goal in ctx


# ---------------------------------------------------------------------------
# pattern_scale_recommendation
# ---------------------------------------------------------------------------


def test_pattern_scale_slim_frame_small_print():
    """Slim build at petite height should get small_print."""
    result = pattern_scale_recommendation("slim", "petite")
    assert result == "small_print"


def test_pattern_scale_broad_tall_frame_large_print():
    """Broad build at tall height should get large_print."""
    result = pattern_scale_recommendation("broad", "tall")
    assert result == "large_print"


def test_pattern_scale_average_returns_medium():
    """Average build at average height should return medium_print."""
    result = pattern_scale_recommendation("average", "average")
    assert result == "medium_print"


def test_pattern_scale_returns_valid_value():
    """All inputs must return one of the 3 valid strings."""
    valid = {"small_print", "medium_print", "large_print"}
    for build in ("slim", "lean", "athletic", "average", "broad", "stocky"):
        for height in _HEIGHTS:
            result = pattern_scale_recommendation(build, height)
            assert result in valid, f"build={build}, height={height} → '{result}'"


# ---------------------------------------------------------------------------
# fabric_texture_recommendation
# ---------------------------------------------------------------------------


def test_fabric_texture_oval_matte_recommended():
    """Oval body shape should always recommend matte fabric."""
    result = fabric_texture_recommendation("oval")
    assert "matte" in result["recommended_texture"].lower()


def test_fabric_texture_inverted_triangle_avoid_shoulder_texture():
    """Inverted triangle: avoid texture on upper body."""
    result = fabric_texture_recommendation("inverted_triangle")
    assert len(result["avoid_texture"]) > 0


def test_fabric_texture_all_shapes_have_required_keys():
    """All shapes must return all three keys."""
    required_keys = {"recommended_texture", "avoid_texture", "why"}
    for shape in _SHAPES:
        result = fabric_texture_recommendation(shape)
        assert required_keys.issubset(result.keys()), f"{shape} missing keys"
        assert len(result["why"]) > 0


def test_fabric_texture_unknown_shape_returns_default():
    """Unknown shape must return a default dict, not raise."""
    result = fabric_texture_recommendation("hourglass")
    assert "recommended_texture" in result
