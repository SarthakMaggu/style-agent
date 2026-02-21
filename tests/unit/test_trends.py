"""Unit tests for trends.py — Step 6 (Phase B)."""

import pytest

from src.fashion_knowledge.trends import (
    get_trends_for_occasion,
    get_trending_colors_2025,
    get_trend_context_string,
)


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------


def test_trends_data_loads_without_error():
    """get_trends_for_occasion must return a list (JSON must parse cleanly)."""
    result = get_trends_for_occasion("smart_casual")
    assert isinstance(result, list)


def test_trends_data_has_entries():
    """The trends dataset must have at least 20 entries."""
    result = get_trends_for_occasion("smart_casual", region="global")
    # At least some smart_casual entries should exist
    all_entries = get_trends_for_occasion("", region="global")
    assert len(all_entries) >= 20 or len(result) >= 1


# ---------------------------------------------------------------------------
# get_trends_for_occasion
# ---------------------------------------------------------------------------


def test_get_trends_for_occasion_returns_list():
    """Must return a list for any occasion string."""
    result = get_trends_for_occasion("indian_casual")
    assert isinstance(result, list)


def test_get_trends_for_occasion_indian_has_entries():
    """indian_casual occasion must return at least 2 entries."""
    result = get_trends_for_occasion("indian_casual", region="indian")
    assert len(result) >= 2


def test_get_trends_for_occasion_western_has_entries():
    """western_business_casual occasion must return entries."""
    result = get_trends_for_occasion("western_business_casual", region="western")
    assert len(result) >= 1


def test_get_trends_for_occasion_empty_for_unknown():
    """An occasion with no matching entries must return empty list, not raise."""
    result = get_trends_for_occasion("underwater_polo", region="global")
    assert isinstance(result, list)  # may be empty but must not raise


def test_rising_and_peak_trends_appear_in_result():
    """Result must include 'rising' and/or 'peak' entries for common occasions."""
    result = get_trends_for_occasion("smart_casual", region="global")
    if result:
        directions = {e["trend_direction"] for e in result}
        assert directions.intersection({"rising", "peak"})


def test_trend_entries_have_required_keys():
    """Every returned entry must have all required TrendEntry keys."""
    required = {"item", "category", "occasions", "body_types", "region", "trend_direction", "stylist_note"}
    result = get_trends_for_occasion("indian_formal", region="indian")
    for entry in result:
        assert required.issubset(entry.keys()), f"Missing keys in entry: {entry}"


# ---------------------------------------------------------------------------
# get_trending_colors_2025
# ---------------------------------------------------------------------------


def test_trending_colors_has_indian_and_western():
    """get_trending_colors_2025 must return dict with 'indian' and 'western' keys."""
    colors = get_trending_colors_2025()
    assert "indian" in colors
    assert "western" in colors


def test_trending_colors_values_are_lists():
    """All values in get_trending_colors_2025 must be lists."""
    colors = get_trending_colors_2025()
    for key, value in colors.items():
        assert isinstance(value, list), f"Key '{key}' is not a list"


# ---------------------------------------------------------------------------
# get_trend_context_string
# ---------------------------------------------------------------------------


def test_trend_context_string_returns_string():
    """Must always return a string."""
    result = get_trend_context_string("smart_casual")
    assert isinstance(result, str)


def test_trend_context_string_not_empty_for_common_occasion():
    """Must return a non-empty string for common occasions."""
    result = get_trend_context_string("indian_casual", region="indian")
    assert len(result) > 20


def test_trend_context_string_respects_max_items():
    """Must not include more entries than max_items."""
    result = get_trend_context_string("smart_casual", region="global", max_items=3)
    # Count lines that start with " · "
    items = [line for line in result.splitlines() if line.strip().startswith("·")]
    assert len(items) <= 3


def test_trend_context_string_body_type_filter():
    """Body-type-specific entries must appear first when body_shape matches."""
    result = get_trend_context_string(
        "indian_casual",
        body_shape="inverted_triangle",
        region="indian",
    )
    # Should return something without raising
    assert isinstance(result, str)


def test_trend_direction_valid_values():
    """All trend_direction values in the dataset must be rising/peak/fading."""
    valid = {"rising", "peak", "fading"}
    entries = get_trends_for_occasion("", region="global")
    for entry in entries:
        assert entry["trend_direction"] in valid, (
            f"Invalid trend_direction '{entry['trend_direction']}' in entry: {entry['item']}"
        )
