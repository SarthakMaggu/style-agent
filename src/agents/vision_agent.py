"""Vision agent — analyses outfit photos using Claude Vision.

Takes a base64-encoded image and returns a fully structured OutfitBreakdown
(including AccessoryAnalysis and FootwearAnalysis).
"""

import logging
from typing import Any

from src.models.accessories import AccessoryAnalysis, AccessoryItem, AccessoryType
from src.models.footwear import FootwearAnalysis
from src.models.outfit import GarmentItem, OutfitBreakdown
from src.prompts.outfit_analysis import build_outfit_prompt
from src.services.anthropic_service import call_vision, parse_json_response

logger = logging.getLogger(__name__)


def analyse_outfit(
    image_base64: str,
    media_type: str = "image/jpeg",
    occasion: str = "auto",
) -> OutfitBreakdown:
    """Analyse an outfit photo and return a structured OutfitBreakdown.

    Args:
        image_base64: Base64-encoded image string.
        media_type: MIME type (default "image/jpeg").
        occasion: Requested occasion string, or "auto" for auto-detection.

    Returns:
        OutfitBreakdown populated from Claude Vision's analysis.

    Raises:
        ValueError: If the response cannot be parsed into OutfitBreakdown.
        RuntimeError: If vision API call fails after retries.
    """
    prompt = build_outfit_prompt(occasion)

    try:
        raw_response = call_vision(image_base64, media_type, prompt)
    except Exception as exc:
        raise RuntimeError(
            f"Vision analysis failed: {exc}. "
            "Check your ANTHROPIC_API_KEY and network connection."
        ) from exc

    try:
        data = parse_json_response(raw_response)
    except ValueError as exc:
        raise ValueError(f"Could not parse outfit analysis response: {exc}") from exc

    return _build_outfit_breakdown(data)


def _build_outfit_breakdown(data: dict[str, Any]) -> OutfitBreakdown:
    """Convert a raw API response dict into an OutfitBreakdown model.

    Args:
        data: Parsed JSON dict from Claude Vision response.

    Returns:
        Validated OutfitBreakdown instance.
    """
    items = [_build_garment(g) for g in data.get("items", [])]
    accessory_analysis = _build_accessory_analysis(data.get("accessory_analysis", {}))
    footwear_analysis = _build_footwear_analysis(data.get("footwear_analysis", {}))

    return OutfitBreakdown(
        occasion_detected=data.get("occasion_detected", "unknown"),
        occasion_requested=data.get("occasion_requested", "auto"),
        occasion_match=bool(data.get("occasion_match", False)),
        items=items,
        accessory_analysis=accessory_analysis,
        footwear_analysis=footwear_analysis,
        overall_color_harmony=data.get("overall_color_harmony", ""),
        color_clash_detected=bool(data.get("color_clash_detected", False)),
        silhouette_assessment=data.get("silhouette_assessment", ""),
        proportion_assessment=data.get("proportion_assessment", ""),
        formality_level=int(data.get("formality_level", 5)),
        outfit_score=int(data.get("outfit_score", 5)),
    )


def _build_garment(g: dict[str, Any]) -> GarmentItem:
    """Build a GarmentItem from a raw dict."""
    return GarmentItem(
        category=g.get("category", "top"),
        garment_type=g.get("garment_type", "unknown"),
        color=g.get("color", "unknown"),
        pattern=g.get("pattern", "solid"),
        fabric_estimate=g.get("fabric_estimate", "unknown"),
        fit=g.get("fit", "regular"),
        length=g.get("length", "unknown"),
        collar_type=g.get("collar_type", "n/a"),
        sleeve_type=g.get("sleeve_type", "n/a"),
        condition=g.get("condition", "good"),
        occasion_appropriate=bool(g.get("occasion_appropriate", True)),
        issue=g.get("issue", ""),
        fix=g.get("fix", ""),
    )


def _build_accessory_analysis(data: dict[str, Any]) -> AccessoryAnalysis:
    """Build an AccessoryAnalysis from a raw dict."""
    items = []
    for item_data in data.get("items_detected", []):
        try:
            accessory_type = AccessoryType(item_data.get("type", "watch"))
        except ValueError:
            accessory_type = AccessoryType.WATCH

        items.append(
            AccessoryItem(
                type=accessory_type,
                color=item_data.get("color", "unknown"),
                material_estimate=item_data.get("material_estimate", "unknown"),
                style_category=item_data.get("style_category", "casual"),
                condition=item_data.get("condition", "good"),
                occasion_appropriate=bool(item_data.get("occasion_appropriate", True)),
                issue=item_data.get("issue", ""),
                fix=item_data.get("fix", ""),
            )
        )

    return AccessoryAnalysis(
        items_detected=items,
        missing_accessories=data.get("missing_accessories", []),
        accessories_to_remove=data.get("accessories_to_remove", []),
        accessory_harmony=data.get("accessory_harmony", ""),
        overall_score=int(data.get("overall_score", 5)),
    )


def _build_footwear_analysis(data: dict[str, Any]) -> FootwearAnalysis:
    """Build a FootwearAnalysis from a raw dict."""
    visible = bool(data.get("visible", False))
    return FootwearAnalysis(
        visible=visible,
        type=data.get("type", ""),
        color=data.get("color", ""),
        material_estimate=data.get("material_estimate", ""),
        condition=data.get("condition", ""),
        style_category=data.get("style_category", ""),
        occasion_match=bool(data.get("occasion_match", False)),
        outfit_match=bool(data.get("outfit_match", False)),
        issue=data.get("issue", ""),
        recommended_instead=data.get("recommended_instead", ""),
        shoe_care_note=data.get("shoe_care_note", ""),
    )
