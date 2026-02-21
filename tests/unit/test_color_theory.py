"""Unit tests for fashion_knowledge/color_theory.py — Step 2."""

import pytest

from src.models.user_profile import SkinUndertone
from src.fashion_knowledge.color_theory import (
    get_palette,
    palette_do,
    palette_avoid,
    is_clash,
    detect_clashes,
    is_undertone_color_appropriate,
    recommended_print_scale,
)


# ---------------------------------------------------------------------------
# Warm undertone palette
# ---------------------------------------------------------------------------

def test_warm_palette_contains_rust_terracotta():
    do = palette_do(SkinUndertone.WARM)
    assert "rust" in do
    assert "terracotta" in do


def test_warm_avoids_cobalt():
    avoid = palette_avoid(SkinUndertone.WARM)
    assert "cobalt blue" in avoid


def test_warm_palette_contains_mustard_and_gold():
    do = palette_do(SkinUndertone.WARM)
    assert "mustard" in do
    assert "gold" in do


# ---------------------------------------------------------------------------
# Cool undertone palette
# ---------------------------------------------------------------------------

def test_cool_palette_contains_navy_emerald():
    do = palette_do(SkinUndertone.COOL)
    assert "navy" in do
    assert "emerald" in do


def test_cool_avoids_warm_yellows():
    avoid = palette_avoid(SkinUndertone.COOL)
    assert "warm yellows" in avoid


def test_cool_avoids_rust_and_gold():
    avoid = palette_avoid(SkinUndertone.COOL)
    assert "rust" in avoid
    assert "gold" in avoid


# ---------------------------------------------------------------------------
# Deep warm undertone palette
# ---------------------------------------------------------------------------

def test_deep_warm_includes_jewel_tones():
    do = palette_do(SkinUndertone.DEEP_WARM)
    # Must include sapphire, emerald, or deep burgundy
    jewel = {"sapphire", "emerald", "deep burgundy", "royal purple"}
    assert jewel & set(do), "Deep warm palette must include jewel tones"


def test_deep_warm_excludes_pastels():
    avoid = palette_avoid(SkinUndertone.DEEP_WARM)
    pastel_present = [c for c in avoid if "pastel" in c]
    assert len(pastel_present) >= 1, "Deep warm must avoid pastels"


def test_deep_warm_includes_gold_and_rust():
    do = palette_do(SkinUndertone.DEEP_WARM)
    assert "gold" in do
    assert "rust" in do


# ---------------------------------------------------------------------------
# Olive warm undertone palette
# ---------------------------------------------------------------------------

def test_olive_warm_palette_correct():
    do = palette_do(SkinUndertone.OLIVE_WARM)
    avoid = palette_avoid(SkinUndertone.OLIVE_WARM)
    assert "terracotta" in do
    assert "warm earth tones" in do
    assert "stark white" in avoid or "cool pastels" in avoid


# ---------------------------------------------------------------------------
# Clash detection
# ---------------------------------------------------------------------------

def test_clash_detected_correctly():
    assert is_clash("rust", "cool grey") is True


def test_clash_bidirectional():
    assert is_clash("cobalt blue", "terracotta") is True


def test_monochromatic_not_flagged_as_clash():
    # Both within the blue family
    assert is_clash("navy", "cobalt") is False


def test_same_color_never_clashes():
    assert is_clash("rust", "rust") is False


def test_detect_clashes_returns_pairs():
    colors = ["rust", "cool grey", "ivory"]
    clashes = detect_clashes(colors)
    assert ("rust", "cool grey") in clashes or ("cool grey", "rust") in clashes


def test_detect_clashes_empty_on_harmonious():
    colors = ["navy", "cobalt", "icy blue"]
    assert detect_clashes(colors) == []


def test_detect_clashes_multiple():
    colors = ["rust", "cool grey", "orange", "pink"]
    clashes = detect_clashes(colors)
    assert len(clashes) >= 2


# ---------------------------------------------------------------------------
# Undertone appropriateness
# ---------------------------------------------------------------------------

def test_undertone_appropriate_rust_warm():
    assert is_undertone_color_appropriate("rust", SkinUndertone.WARM) is True


def test_undertone_appropriate_cobalt_cool():
    assert is_undertone_color_appropriate("cobalt", SkinUndertone.COOL) is True


def test_undertone_inappropriate_rust_cool():
    # Rust is in COOL's avoid list, so not in do-list
    assert is_undertone_color_appropriate("rust", SkinUndertone.COOL) is False


# ---------------------------------------------------------------------------
# Print scale recommendation
# ---------------------------------------------------------------------------

def test_pattern_scale_small_frame_small_print():
    result = recommended_print_scale("slim")
    assert "small" in result.lower()


def test_pattern_scale_broad_frame():
    result = recommended_print_scale("broad")
    assert "medium" in result.lower() or "large" in result.lower()


def test_pattern_scale_average():
    result = recommended_print_scale("average")
    assert isinstance(result, str) and len(result) > 0


# ---------------------------------------------------------------------------
# Full palette object
# ---------------------------------------------------------------------------

def test_get_palette_returns_correct_undertone():
    palette = get_palette(SkinUndertone.DEEP_WARM)
    assert palette.undertone == SkinUndertone.DEEP_WARM


def test_all_undertones_have_do_and_avoid():
    for undertone in SkinUndertone:
        do = palette_do(undertone)
        avoid = palette_avoid(undertone)
        assert len(do) >= 3, f"{undertone} has too few do-colors"
        assert len(avoid) >= 2, f"{undertone} has too few avoid-colors"
