"""Tests for src/agents/product_catalogue_agent.py.

All tests use mocked Anthropic API responses — no real API calls.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.models.product import ProductCatalogue, ProductEntry, ProductTier
from src.models.user_profile import BodyShape, FaceShape, SkinUndertone, UserProfile


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_profile() -> UserProfile:
    """Return a minimal but valid UserProfile for testing."""
    return UserProfile(
        skin_undertone=SkinUndertone.DEEP_WARM,
        skin_tone_depth="deep",
        skin_texture_visible="smooth",
        body_shape=BodyShape.INVERTED_TRIANGLE,
        height_estimate="tall",
        build="athletic",
        shoulder_width="broad",
        torso_length="average",
        leg_proportion="average",
        face_shape=FaceShape.SQUARE,
        jaw_type="strong",
        forehead="average",
        hair_color="black",
        hair_texture="straight",
        hair_density="medium",
        current_haircut_style="taper fade",
        haircut_length="short",
        hair_visible_condition="healthy",
        beard_style="full",
        beard_density="dense",
        beard_color="black",
        mustache_style="natural",
        beard_grooming_quality="well groomed",
        confidence_scores={"skin_undertone": 0.9, "body_shape": 0.85},
        photos_used=5,
        profile_created_at="2025-01-01T00:00:00+00:00",
        profile_version=1,
    )


def _make_mock_catalogue_json() -> str:
    """Return a minimal valid product catalogue JSON array."""
    return json.dumps([
        {
            "category": "Indian Formal Kurta",
            "occasion_relevance": ["indian_formal", "wedding_guest_indian"],
            "profile_reason": "No silk-blend kurta — highest gap.",
            "high_street": {
                "tier": "high_street",
                "brand": "Manyavar",
                "product_name": "Silk blend kurta in rust",
                "price_range": "₹3,000–6,000",
                "search_query": "manyavar silk kurta rust",
                "why_for_you": "Warm rust suits your deep warm undertone.",
            },
            "designer": {
                "tier": "designer",
                "brand": "FabIndia",
                "product_name": "Chanderi kurta in champagne",
                "price_range": "₹8,000–14,000",
                "search_query": "fabindia chanderi champagne",
                "why_for_you": "Chanderi reads formal for your occasion.",
            },
            "luxury": {
                "tier": "luxury",
                "brand": "Sabyasachi",
                "product_name": "Bespoke raw silk kurta",
                "price_range": "₹45,000+",
                "search_query": "sabyasachi silk kurta bespoke",
                "why_for_you": "Bespoke mid-thigh balances inverted triangle.",
            },
        },
        {
            "category": "Leather Strap Watch",
            "occasion_relevance": ["indian_formal", "smart_casual"],
            "profile_reason": "Rubber strap noted as critical issue.",
            "high_street": {
                "tier": "high_street",
                "brand": "Casio Edifice",
                "product_name": "Tan leather strap dress watch",
                "price_range": "₹4,000–7,000",
                "search_query": "casio edifice tan leather strap",
                "why_for_you": "Tan leather reads formal at this occasion.",
            },
            "designer": {
                "tier": "designer",
                "brand": "Fossil",
                "product_name": "Minimalist field watch cognac strap",
                "price_range": "₹12,000–18,000",
                "search_query": "fossil watch cognac leather",
                "why_for_you": "Cognac reads warm — matches your undertone.",
            },
            "luxury": {
                "tier": "luxury",
                "brand": "Tissot",
                "product_name": "Le Locle automatic tan strap",
                "price_range": "₹35,000+",
                "search_query": "tissot le locle leather",
                "why_for_you": "Swiss movement, dress proportions for formal.",
            },
        },
    ])


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_generate_returns_product_catalogue_on_success():
    """generate_product_catalogue must return a ProductCatalogue on valid Claude response."""
    from src.agents.product_catalogue_agent import generate_product_catalogue

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=_make_mock_catalogue_json())]

    with patch("src.agents.product_catalogue_agent.anthropic") as mock_anthropic_mod:
        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_message

        result = generate_product_catalogue(_make_profile(), anthropic_api_key="test-key")

    assert result is not None
    assert isinstance(result, ProductCatalogue)
    assert len(result.entries) == 2
    assert result.entries[0].category == "Indian Formal Kurta"


def test_generate_returns_none_when_no_api_key():
    """generate_product_catalogue must return None and log error when API key missing."""
    from src.agents.product_catalogue_agent import generate_product_catalogue

    with patch.dict("os.environ", {}, clear=True):
        # Remove ANTHROPIC_API_KEY from env
        import os
        env_backup = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            result = generate_product_catalogue(_make_profile(), anthropic_api_key="")
        finally:
            if env_backup:
                os.environ["ANTHROPIC_API_KEY"] = env_backup

    assert result is None


def test_generate_returns_none_on_api_failure():
    """generate_product_catalogue must return None (not raise) when API call fails."""
    from src.agents.product_catalogue_agent import generate_product_catalogue

    with patch("src.agents.product_catalogue_agent.anthropic") as mock_anthropic_mod:
        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = RuntimeError("API error")

        result = generate_product_catalogue(_make_profile(), anthropic_api_key="test-key")

    assert result is None


def test_generate_returns_none_on_bad_json():
    """generate_product_catalogue must return None if Claude returns invalid JSON."""
    from src.agents.product_catalogue_agent import generate_product_catalogue

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="This is not JSON at all!")]

    with patch("src.agents.product_catalogue_agent.anthropic") as mock_anthropic_mod:
        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_message

        result = generate_product_catalogue(_make_profile(), anthropic_api_key="test-key")

    assert result is None


def test_generate_strips_markdown_fences():
    """generate_product_catalogue must strip ``` markdown fences from Claude response."""
    from src.agents.product_catalogue_agent import generate_product_catalogue

    raw_with_fences = "```json\n" + _make_mock_catalogue_json() + "\n```"
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=raw_with_fences)]

    with patch("src.agents.product_catalogue_agent.anthropic") as mock_anthropic_mod:
        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_message

        result = generate_product_catalogue(_make_profile(), anthropic_api_key="test-key")

    assert result is not None
    assert len(result.entries) == 2


def test_catalogue_has_correct_tier_structure():
    """Every ProductEntry must have all three tiers with non-empty brand names."""
    from src.agents.product_catalogue_agent import generate_product_catalogue

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=_make_mock_catalogue_json())]

    with patch("src.agents.product_catalogue_agent.anthropic") as mock_anthropic_mod:
        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_message

        result = generate_product_catalogue(_make_profile(), anthropic_api_key="test-key")

    assert result is not None
    for entry in result.entries:
        assert entry.high_street.brand != ""
        assert entry.designer.brand != ""
        assert entry.luxury.brand != ""
        assert entry.high_street.tier == "high_street"
        assert entry.designer.tier == "designer"
        assert entry.luxury.tier == "luxury"


def test_catalogue_stores_profile_metadata():
    """ProductCatalogue must record profile_undertone and profile_body_shape."""
    from src.agents.product_catalogue_agent import generate_product_catalogue

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=_make_mock_catalogue_json())]

    with patch("src.agents.product_catalogue_agent.anthropic") as mock_anthropic_mod:
        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_message

        profile = _make_profile()
        result = generate_product_catalogue(profile, anthropic_api_key="test-key")

    assert result is not None
    assert result.profile_undertone == profile.skin_undertone.value
    assert result.profile_body_shape == profile.body_shape.value


def test_malformed_entry_skipped_gracefully():
    """Malformed entries in Claude response must be skipped; valid ones kept."""
    from src.agents.product_catalogue_agent import generate_product_catalogue

    # Mix one valid and one missing-key entry
    data = json.loads(_make_mock_catalogue_json())
    data.append({"category": "Broken Entry"})  # missing high_street, designer, luxury
    broken_json = json.dumps(data)

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=broken_json)]

    with patch("src.agents.product_catalogue_agent.anthropic") as mock_anthropic_mod:
        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = mock_message

        result = generate_product_catalogue(_make_profile(), anthropic_api_key="test-key")

    assert result is not None
    # Only the 2 valid entries should be included; malformed one is skipped
    assert len(result.entries) == 2


# ── Product model tests ────────────────────────────────────────────────────────

def test_product_tier_pydantic_valid():
    """ProductTier must accept all required fields."""
    tier = ProductTier(
        tier="high_street",
        brand="Manyavar",
        product_name="Silk blend kurta",
        price_range="₹3,000–6,000",
        search_query="manyavar silk kurta",
        why_for_you="Suits your warm undertone.",
    )
    assert tier.tier == "high_street"
    assert tier.brand == "Manyavar"


def test_product_entry_pydantic_valid():
    """ProductEntry must accept all required fields including three tiers."""
    tier = ProductTier(
        tier="high_street", brand="Brand", product_name="Product",
        price_range="₹1,000", search_query="brand product", why_for_you="Reason.",
    )
    entry = ProductEntry(
        category="Test Category",
        occasion_relevance=["indian_formal"],
        profile_reason="Test reason.",
        high_street=tier,
        designer=tier,
        luxury=tier,
    )
    assert entry.category == "Test Category"
    assert len(entry.occasion_relevance) == 1


def test_product_catalogue_pydantic_valid():
    """ProductCatalogue must accept entries list and metadata fields."""
    tier = ProductTier(
        tier="high_street", brand="Brand", product_name="Product",
        price_range="₹1,000", search_query="brand product", why_for_you="Reason.",
    )
    entry = ProductEntry(
        category="Test", occasion_relevance=["indian_formal"],
        profile_reason="Reason.", high_street=tier, designer=tier, luxury=tier,
    )
    catalogue = ProductCatalogue(
        profile_undertone="deep_warm",
        profile_body_shape="inverted_triangle",
        entries=[entry],
        generated_at="2025-01-01T00:00:00+00:00",
    )
    assert len(catalogue.entries) == 1
    assert catalogue.catalogue_version == 1
