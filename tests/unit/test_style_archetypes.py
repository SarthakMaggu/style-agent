"""Unit tests for style_archetypes.py — Step 5 (Phase C3)."""

import pytest

from src.fashion_knowledge.style_archetypes import (
    get_archetype,
    all_archetype_names,
    archetype_context_string,
)


_VALID_ARCHETYPES = [
    "classic", "streetwear", "ethnic_traditional",
    "smart_casual", "avant_garde", "athletic", "eclectic",
]


def test_all_archetypes_have_entries():
    """Every defined archetype must be retrievable."""
    for name in _VALID_ARCHETYPES:
        arch = get_archetype(name)
        assert arch is not None, f"Archetype '{name}' returned None"
        assert arch.name == name


def test_all_archetypes_names_function():
    """all_archetype_names() must return all 7 archetypes."""
    names = all_archetype_names()
    for name in _VALID_ARCHETYPES:
        assert name in names


def test_classic_archetype_has_signature_pieces():
    """Classic archetype must list specific garment/accessory pieces."""
    arch = get_archetype("classic")
    assert arch is not None
    assert len(arch.signature_pieces) >= 3
    # Must mention a suit or tailored piece
    all_pieces = " ".join(arch.signature_pieces).lower()
    assert "suit" in all_pieces or "bandhgala" in all_pieces


def test_streetwear_archetype_has_celebrity_reference():
    """Streetwear archetype must provide a celebrity reference."""
    arch = get_archetype("streetwear")
    assert arch is not None
    assert len(arch.celebrity_reference) > 10


def test_ethnic_archetype_has_indian_pieces():
    """ethnic_traditional archetype must reference Indian garments."""
    arch = get_archetype("ethnic_traditional")
    assert arch is not None
    all_pieces = " ".join(arch.signature_pieces).lower()
    assert any(
        term in all_pieces
        for term in ["kurta", "sherwani", "mojari", "jutti", "bandhgala", "churidar"]
    )


def test_all_archetypes_have_upgrade_moves_and_pitfalls():
    """Every archetype must have at least 2 upgrade moves and 2 pitfalls."""
    for name in _VALID_ARCHETYPES:
        arch = get_archetype(name)
        assert arch is not None
        assert len(arch.upgrade_moves) >= 2, f"{name}: not enough upgrade_moves"
        assert len(arch.pitfalls) >= 2, f"{name}: not enough pitfalls"


def test_get_archetype_unknown_returns_none():
    """An unknown archetype name must return None, not raise."""
    result = get_archetype("grunge")
    assert result is None


def test_archetype_context_string_not_empty():
    """archetype_context_string must return a non-empty string for valid archetypes."""
    for name in _VALID_ARCHETYPES:
        result = archetype_context_string(name)
        assert isinstance(result, str), f"{name}: not a string"
        assert len(result) > 50, f"{name}: context string too short"


def test_archetype_context_string_empty_for_unknown():
    """archetype_context_string must return '' for unknown or empty archetype."""
    assert archetype_context_string("grunge") == ""
    assert archetype_context_string("") == ""


def test_archetype_context_string_contains_description():
    """The context string must include the archetype's description."""
    arch = get_archetype("smart_casual")
    ctx = archetype_context_string("smart_casual")
    # Description should appear somewhere in the context
    assert arch is not None
    assert arch.description[:30] in ctx


def test_all_archetypes_have_grooming_alignment():
    """Every archetype must have a grooming_alignment string."""
    for name in _VALID_ARCHETYPES:
        arch = get_archetype(name)
        assert arch is not None
        assert len(arch.grooming_alignment) > 10, f"{name}: grooming_alignment too short"
