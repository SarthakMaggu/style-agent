"""Unit tests for seasonal_color.py — Step 3 (Phase C1)."""

import pytest

from src.fashion_knowledge.seasonal_color import (
    derive_seasonal_type,
    get_seasonal_palette,
    seasonal_palette_do,
    seasonal_palette_avoid,
    seasonal_context_string,
)
from src.models.user_profile import SkinUndertone


# ---------------------------------------------------------------------------
# derive_seasonal_type — decision matrix
# ---------------------------------------------------------------------------


def test_derive_seasonal_type_warm_light_hair_is_spring():
    """WARM undertone + light depth + light hair → spring."""
    result = derive_seasonal_type(SkinUndertone.WARM, "light", "golden brown")
    assert result == "spring"


def test_derive_seasonal_type_warm_medium_light_hair_is_spring():
    """WARM undertone + medium depth + light hair → spring."""
    result = derive_seasonal_type(SkinUndertone.WARM, "medium", "auburn")
    assert result == "spring"


def test_derive_seasonal_type_warm_deep_is_autumn():
    """WARM undertone + deep skin → autumn regardless of hair."""
    result = derive_seasonal_type(SkinUndertone.WARM, "deep", "black")
    assert result == "autumn"


def test_derive_seasonal_type_warm_tan_is_autumn():
    """WARM undertone + tan → autumn."""
    result = derive_seasonal_type(SkinUndertone.WARM, "tan", "black")
    assert result == "autumn"


def test_derive_seasonal_type_deep_warm_is_autumn():
    """DEEP_WARM always maps to autumn."""
    result = derive_seasonal_type(SkinUndertone.DEEP_WARM, "deep", "black")
    assert result == "autumn"


def test_derive_seasonal_type_olive_warm_is_autumn():
    """OLIVE_WARM always maps to autumn."""
    result = derive_seasonal_type(SkinUndertone.OLIVE_WARM, "wheatish", "dark brown")
    assert result == "autumn"


def test_derive_seasonal_type_cool_light_is_summer():
    """COOL undertone + light depth → summer."""
    result = derive_seasonal_type(SkinUndertone.COOL, "light", "light brown")
    assert result == "summer"


def test_derive_seasonal_type_cool_medium_is_summer():
    """COOL undertone + medium depth → summer."""
    result = derive_seasonal_type(SkinUndertone.COOL, "medium", "brown")
    assert result == "summer"


def test_derive_seasonal_type_cool_deep_is_winter():
    """COOL undertone + deep skin → winter."""
    result = derive_seasonal_type(SkinUndertone.COOL, "deep", "black")
    assert result == "winter"


def test_derive_seasonal_type_deep_cool_is_winter():
    """DEEP_COOL always maps to winter."""
    result = derive_seasonal_type(SkinUndertone.DEEP_COOL, "deep", "black")
    assert result == "winter"


def test_derive_seasonal_type_neutral_light_is_summer():
    """NEUTRAL + light → summer."""
    result = derive_seasonal_type(SkinUndertone.NEUTRAL, "light", "brown")
    assert result == "summer"


def test_derive_seasonal_type_neutral_tan_is_autumn():
    """NEUTRAL + tan → autumn."""
    result = derive_seasonal_type(SkinUndertone.NEUTRAL, "tan", "dark brown")
    assert result == "autumn"


def test_all_undertones_map_to_a_valid_season():
    """Every SkinUndertone must map to one of the 4 valid seasons."""
    valid = {"spring", "summer", "autumn", "winter"}
    for undertone in SkinUndertone:
        result = derive_seasonal_type(undertone, "medium", "black")
        assert result in valid, f"{undertone} mapped to unexpected '{result}'"


# ---------------------------------------------------------------------------
# get_seasonal_palette / palette helpers
# ---------------------------------------------------------------------------


def test_get_seasonal_palette_spring_not_empty():
    """Spring palette must have entries in both do and avoid."""
    sp = get_seasonal_palette("spring")
    assert sp.season == "spring"
    assert len(sp.palette_do) > 0
    assert len(sp.palette_avoid) > 0


def test_get_seasonal_palette_autumn_contains_earth_tones():
    """Autumn palette should contain signature earth tones."""
    sp = get_seasonal_palette("autumn")
    do = [c.lower() for c in sp.palette_do]
    assert any("rust" in c or "terracotta" in c or "burnt" in c for c in do)


def test_get_seasonal_palette_winter_contains_jewel_tones():
    """Winter palette must include high-contrast jewel tones."""
    sp = get_seasonal_palette("winter")
    do = [c.lower() for c in sp.palette_do]
    assert any(c in do for c in ["emerald", "sapphire", "royal blue", "navy"])


def test_get_seasonal_palette_summer_contains_muted_cool():
    """Summer palette must include muted cool tones."""
    sp = get_seasonal_palette("summer")
    do = [c.lower() for c in sp.palette_do]
    assert any("mauve" in c or "dusty" in c or "lavender" in c or "slate" in c for c in do)


def test_get_seasonal_palette_invalid_raises():
    """Invalid season string must raise ValueError."""
    with pytest.raises(ValueError, match="Unknown season"):
        get_seasonal_palette("monsoon")


def test_seasonal_palette_do_returns_list():
    """seasonal_palette_do must return a non-empty list."""
    result = seasonal_palette_do("autumn")
    assert isinstance(result, list)
    assert len(result) > 0


def test_seasonal_palette_avoid_returns_list():
    """seasonal_palette_avoid must return a non-empty list."""
    result = seasonal_palette_avoid("winter")
    assert isinstance(result, list)
    assert len(result) > 0


def test_seasonal_fabric_finish_present():
    """Each season must have at least one fabric_finish entry."""
    for season in ("spring", "summer", "autumn", "winter"):
        sp = get_seasonal_palette(season)
        assert len(sp.fabric_finishes) > 0, f"{season} has no fabric_finishes"


def test_seasonal_context_string_not_empty_for_valid_season():
    """seasonal_context_string must return a non-empty string for known seasons."""
    result = seasonal_context_string("autumn")
    assert isinstance(result, str)
    assert len(result) > 20
    assert "autumn" in result.lower() or "Autumn" in result


def test_seasonal_context_string_empty_for_blank():
    """seasonal_context_string must return empty string when season is empty."""
    result = seasonal_context_string("")
    assert result == ""


def test_seasonal_context_string_empty_for_invalid():
    """seasonal_context_string must return empty string for an unknown season."""
    result = seasonal_context_string("monsoon")
    assert result == ""
