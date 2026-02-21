"""Product catalogue models — per-user curated product recommendations.

Generated once at onboarding time by the ProductCatalogueAgent using the
completed UserProfile. Stored at ~/.style-agent/product_catalogue.json and
loaded at analysis time to populate the SHOP section of the editorial image.

Tier levels
-----------
  high_street  — accessible brands, mass market, ₹1k–8k / $20–120
  designer     — premium / mid-luxury brands, ₹8k–40k / $120–600
  luxury       — luxury / bespoke, ₹40k+ / $600+
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductTier(BaseModel):
    """One tier (High Street / Designer / Luxury) within a product entry."""

    model_config = ConfigDict(strict=True)

    tier: str
    """Tier identifier: "high_street" | "designer" | "luxury"."""

    brand: str
    """Brand name, e.g. "Manyavar", "Sabyasachi", "Ermenegildo Zegna"."""

    product_name: str
    """Specific product description, e.g. "Silk blend kurta set in rust"."""

    price_range: str
    """Localised price range, e.g. "₹3,000–6,000" or "$80–150"."""

    search_query: str
    """Search string the user can paste into Amazon / Myntra / ASOS."""

    why_for_you: str
    """One sentence explaining why this specific product suits this user's profile."""


class ProductEntry(BaseModel):
    """A product category with three tier options."""

    model_config = ConfigDict(strict=True)

    category: str
    """Human-readable category label, e.g. "Indian Formal Kurta", "Leather Watch Strap"."""

    occasion_relevance: list[str]
    """Occasion slugs this product helps with, e.g. ["indian_formal", "wedding_guest_indian"]."""

    profile_reason: str
    """Why this category is a priority for this user (based on profile gaps / remarks)."""

    high_street: ProductTier
    designer: ProductTier
    luxury: ProductTier


class ProductCatalogue(BaseModel):
    """Full per-user product catalogue generated at onboarding."""

    model_config = ConfigDict(strict=True)

    profile_undertone: str
    """Undertone of the user when the catalogue was generated."""

    profile_body_shape: str
    """Body shape of the user when the catalogue was generated."""

    entries: list[ProductEntry]
    """12–15 curated product entries covering all wardrobe / grooming / skincare categories."""

    generated_at: str
    """ISO-8601 timestamp of catalogue generation."""

    catalogue_version: int = 1
