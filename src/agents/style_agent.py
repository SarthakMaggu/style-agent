"""StyleAgent — master orchestrator.

Runs the complete analysis pipeline in sequence:
  1. Load UserProfile from storage
  2. Validate and prepare the outfit image
  3. Run vision agent (OutfitBreakdown)
  4. Run grooming agent (GroomingProfile from photo)
  5. Run caricature agent (Replicate → local PNG)
  6. Run recommendation agent (full StyleRecommendation)
  7. Annotate caricature with remarks (renderer)
  8. Print terminal report (formatter)
  9. Save JSON output (formatter)
  10. Append to history log

Failure modes:
  - Missing profile → prompts user to run `onboard` first
  - Vision failure → raised as StyleAgentError with clear message
  - Caricature failure → continues without caricature (text report still produced)
  - Any other step failure → logged, report printed with available data
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.models.grooming import GroomingProfile
from src.models.outfit import OutfitBreakdown
from src.models.recommendation import StyleRecommendation
from src.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class StyleAgentError(Exception):
    """Raised when a non-recoverable error occurs in the pipeline."""


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class AnalysisResult:
    """Container for a completed style analysis run.

    Attributes:
        recommendation: The full StyleRecommendation.
        caricature_path: Path to caricature image (may be empty string).
        annotated_path: Path to annotated output image (may be empty string).
        json_path: Path to the saved JSON analysis file.
        elapsed_seconds: Wall-clock time for the entire run.
    """

    recommendation: StyleRecommendation
    caricature_path: str = ""
    annotated_path: str = ""
    json_path: str = ""
    elapsed_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_analysis(
    image_path: str,
    occasion: str = "",
    caricature_style: str = "caricature",
    output_dir: str = "./outputs",
    use_api: bool = True,
    save_photos: bool = False,
    cartoon_input: bool = False,
    layout_mode: str = "editorial",
    scale_factor: float = 1.0,
    export_pdf: bool = False,
) -> AnalysisResult:
    """Run the full style analysis pipeline.

    Args:
        image_path: Path to the outfit photo (real or pre-styled cartoon).
        occasion: Target occasion string (auto-detected if empty).
        caricature_style: One of "caricature", "cartoon", "pixar".
        output_dir: Directory to write output files.
        use_api: Whether to call Claude/Replicate APIs.
        save_photos: If True, copy the source photo to output_dir.
        cartoon_input: If True, treat the input image as an already-styled
                       cartoon and annotate it directly (skip Replicate).
        layout_mode: "editorial" (dark magazine, v2 default) or "sidebar" (legacy).
        scale_factor: Resolution multiplier for annotated image (2.0 = hi-res).
        export_pdf: If True, also save a PDF alongside the annotated JPEG.

    Returns:
        AnalysisResult containing recommendation and output paths.

    Raises:
        StyleAgentError: If profile is missing or vision analysis fails.
    """
    t_start = time.time()
    warnings: list[str] = []

    # 1. Load profile
    user_profile = _load_profile()

    # 2. Prepare image
    image_base64, media_type = _prepare_image(image_path)

    # If the image is landscape (sideways cartoon / Flux output), rotate it upright
    # so Vision receives the correct orientation — same rotation the renderer applies.
    vision_base64 = _maybe_rotate_base64(image_base64, media_type)

    # 3. Vision analysis
    outfit_breakdown = _run_vision(vision_base64, media_type, occasion, use_api)
    if not occasion:
        occasion = outfit_breakdown.occasion_detected

    # 4. Grooming from the same photo
    grooming_profile = _run_grooming(user_profile, use_api)

    # 5. Caricature — skip Replicate if user passed a pre-styled cartoon image
    if cartoon_input:
        # Annotate directly on the cartoon the user provided
        caricature_path = image_path
        caric_warning = ""
    else:
        caricature_path, caric_warning = _run_caricature(
            vision_base64, caricature_style, output_dir, image_path, use_api
        )
    if caric_warning:
        warnings.append(caric_warning)

    # 6. Recommendation
    ts = int(t_start)
    annotated_path = str(Path(output_dir) / f"analysis_{ts}_annotated.jpg")
    json_path = str(Path(output_dir) / f"analysis_{ts}.json")

    recommendation = _run_recommendation(
        user_profile=user_profile,
        grooming_profile=grooming_profile,
        outfit_breakdown=outfit_breakdown,
        occasion=occasion,
        caricature_path=caricature_path,
        annotated_path=annotated_path,
        json_path=json_path,
        use_api=use_api,
    )

    # 7. Annotate caricature / cartoon
    if caricature_path:
        annotated_path = _annotate(
            recommendation, caricature_path, annotated_path,
            occasion=occasion,
            layout_mode=layout_mode,
            scale_factor=scale_factor,
            export_pdf=export_pdf,
        )
    else:
        annotated_path = ""

    # 8. Save JSON
    _save_json(recommendation, json_path)

    # 9. Append to history
    _append_history(recommendation, json_path)

    elapsed = time.time() - t_start

    return AnalysisResult(
        recommendation=recommendation,
        caricature_path=caricature_path,
        annotated_path=annotated_path,
        json_path=json_path,
        elapsed_seconds=elapsed,
        warnings=warnings,
    )


def run_onboarding(
    photo_paths: list[str],
    refresh: bool = False,
    save_photos: bool = False,
    folder_mode: bool = False,
    folder_path: str = "",
    preferred_name: str = "",
    lifestyle: str = "",
    age_group: str = "",
    budget_tier: str = "",
) -> UserProfile:
    """Build or refresh the user profile from photos.

    Two modes:
    1. Sequential mode (default): ordered list of 3–5 photos (face front,
       face side, body front, body side, real outfit).
    2. Folder mode (folder_mode=True): auto-categorises all images in a
       folder and merges results — supports 30+ photos.

    Args:
        photo_paths: Ordered photo paths for sequential mode (ignored in folder mode).
        refresh: If True, overwrite an existing profile.
        save_photos: If True, copy photos to ~/.style-agent/photos/.
        folder_mode: If True, use build_profile_from_folder instead.
        folder_path: Folder path for folder mode.
        preferred_name: User's preferred name for personalised recommendations.
        lifestyle: Lifestyle tag (optional, folder mode only).
        age_group: Age group (optional, folder mode only).
        budget_tier: Budget tier (optional, folder mode only).

    Returns:
        The built UserProfile.

    Raises:
        StyleAgentError: On any build or validation failure.
    """
    from src.agents.profile_builder import (
        analyse_photo,
        build_profile,
        build_profile_from_folder,
        save_profile as _builder_save_profile,
        refresh_profile,
        InsufficientPhotosError,
        DEFAULT_PROFILE_PATH,
    )
    from src.services.image_service import validate_and_prepare

    # ── Folder mode ──────────────────────────────────────────────────────────
    if folder_mode:
        if not folder_path:
            raise StyleAgentError("folder_mode requires --folder to be specified.")
        try:
            profile = build_profile_from_folder(
                folder_path=folder_path,
                preferred_name=preferred_name,
                lifestyle=lifestyle,
                age_group=age_group,
                budget_tier=budget_tier,
                refresh=refresh,
            )
            _builder_save_profile(profile)
        except InsufficientPhotosError as exc:
            raise StyleAgentError(str(exc)) from exc
        except Exception as exc:
            raise StyleAgentError(f"Folder profile build failed: {exc}") from exc
        return profile

    if len(photo_paths) < 3:
        raise StyleAgentError(
            f"Need at least 3 photos to build your profile — you provided {len(photo_paths)}."
        )

    # Step 1: validate + encode each image
    prepared: list[tuple[str, str]] = []
    for path in photo_paths:
        try:
            result = validate_and_prepare(path)
            prepared.append((result["base64_data"], result["media_type"]))
        except Exception as exc:
            raise StyleAgentError(f"Could not read photo {path}: {exc}") from exc

    # Step 2: run per-photo vision analysis (photo_number is 1-indexed)
    analyses: list[dict] = []
    for idx, (b64, mime) in enumerate(prepared, start=1):
        try:
            analysis = analyse_photo(idx, b64, mime)
            analyses.append(analysis)
        except Exception as exc:
            raise StyleAgentError(f"Vision analysis failed for photo {idx}: {exc}") from exc

    # Step 3: merge into UserProfile via majority vote, then persist
    try:
        if refresh and DEFAULT_PROFILE_PATH.exists():
            # refresh_profile increments version and saves internally
            from src.agents.profile_builder import load_profile as _load_existing
            try:
                existing = _load_existing()
                profile = refresh_profile(analyses, existing_version=existing.profile_version)
            except Exception:
                # Existing profile unreadable — treat as fresh build
                profile = build_profile(analyses, photos_used=len(analyses))
                _builder_save_profile(profile)
        else:
            profile = build_profile(analyses, photos_used=len(analyses))
            _builder_save_profile(profile)
    except InsufficientPhotosError as exc:
        raise StyleAgentError(str(exc)) from exc
    except Exception as exc:
        raise StyleAgentError(f"Profile build failed: {exc}") from exc

    return profile


# ---------------------------------------------------------------------------
# Private pipeline steps
# ---------------------------------------------------------------------------


def _load_profile() -> UserProfile:
    """Load user profile from storage, raising StyleAgentError if missing."""
    from src.storage.profile_store import load_profile, ProfileNotFoundError

    try:
        return load_profile()
    except ProfileNotFoundError:
        raise StyleAgentError(
            "No profile found. Run `python src/main.py onboard` first to build your profile."
        )


def _prepare_image(image_path: str) -> tuple[str, str]:
    """Validate and base64-encode the outfit image.

    Returns:
        (base64_data, media_type) tuple.
    """
    from src.services.image_service import (
        validate_and_prepare,
        ImageTooLargeError,
        UnsupportedFormatError,
    )

    try:
        result = validate_and_prepare(image_path)
        return result["base64_data"], result["media_type"]
    except ImageTooLargeError as exc:
        raise StyleAgentError(f"Image too large: {exc}") from exc
    except UnsupportedFormatError as exc:
        raise StyleAgentError(f"Unsupported image format: {exc}") from exc
    except Exception as exc:
        raise StyleAgentError(f"Could not read image at {image_path}: {exc}") from exc


def _run_vision(
    image_base64: str,
    media_type: str,
    occasion: str,
    use_api: bool,
) -> OutfitBreakdown:
    """Run vision analysis to get OutfitBreakdown."""
    from src.agents.vision_agent import analyse_outfit

    try:
        return analyse_outfit(image_base64, media_type, occasion=occasion)
    except Exception as exc:
        raise StyleAgentError(f"Vision analysis failed: {exc}") from exc


def _run_grooming(user_profile: UserProfile, use_api: bool) -> GroomingProfile:
    """Generate grooming recommendations for the user profile."""
    from src.agents.grooming_agent import generate_grooming_profile

    try:
        return generate_grooming_profile(user_profile, use_api=use_api)
    except Exception as exc:
        logger.warning("Grooming agent failed, using defaults: %s", exc)
        # Return a minimal grooming profile so pipeline can continue
        from src.fashion_knowledge.grooming_guide import get_haircut_rules, get_beard_rules
        haircut = get_haircut_rules(user_profile.face_shape)
        beard = get_beard_rules(user_profile.face_shape)
        return GroomingProfile(
            current_haircut_assessment="Unable to assess",
            recommended_haircut=", ".join(haircut.recommended[:2]),
            haircut_to_avoid=", ".join(haircut.to_avoid[:2]),
            styling_product_recommendation=["matte clay"],
            hair_color_recommendation="Maintain current colour",
            current_beard_assessment="Unable to assess",
            recommended_beard_style=", ".join(beard.recommended[:2]),
            beard_grooming_tips=beard.tips[:2],
            beard_style_to_avoid=", ".join(beard.to_avoid[:1]),
            eyebrow_assessment="",
            eyebrow_recommendation="Maintain natural shape",
            visible_skin_concerns=[],
            skincare_categories_needed=["moisturiser"],
            grooming_score=5,
            grooming_remarks=[],
        )


def _run_caricature(
    image_base64: str,
    style: str,
    output_dir: str,
    original_path: str,
    use_api: bool,
) -> tuple[str, str]:
    """Generate caricature via Replicate. Returns (path, warning_or_empty)."""
    if not use_api:
        return "", ""

    from src.agents.caricature_agent import generate

    try:
        path = generate(image_base64, style=style, output_dir=output_dir)
        if path and path != original_path:
            return path, ""
        return "", "Caricature generation failed — text analysis still complete."
    except Exception as exc:
        logger.warning("Caricature skipped: %s", exc)
        return "", f"Caricature skipped: {exc}"


def _run_recommendation(
    user_profile: UserProfile,
    grooming_profile: GroomingProfile,
    outfit_breakdown: OutfitBreakdown,
    occasion: str,
    caricature_path: str,
    annotated_path: str,
    json_path: str,
    use_api: bool,
) -> StyleRecommendation:
    """Generate full StyleRecommendation."""
    from src.agents.recommendation_agent import generate_recommendation

    return generate_recommendation(
        user_profile=user_profile,
        grooming_profile=grooming_profile,
        outfit_breakdown=outfit_breakdown,
        occasion=occasion,
        caricature_path=caricature_path,
        annotated_path=annotated_path,
        json_path=json_path,
        use_api=use_api,
    )


def _annotate(
    recommendation: StyleRecommendation,
    caricature_path: str,
    output_path: str,
    occasion: str = "",
    layout_mode: str = "editorial",
    scale_factor: float = 1.0,
    export_pdf: bool = False,
) -> str:
    """Overlay remarks onto caricature image.

    Args:
        recommendation: Full StyleRecommendation with all remark lists.
        caricature_path: Source cartoon / caricature image path.
        output_path: Destination JPEG path.
        occasion: Occasion string for header display.
        layout_mode: "editorial" (v2 default) or "sidebar" (legacy).
        scale_factor: Resolution multiplier (2.0 = hi-res).
        export_pdf: Also export a PDF alongside the JPEG.
    """
    from src.output.renderer import annotate_caricature

    all_remarks = (
        recommendation.outfit_remarks
        + recommendation.footwear_remarks
        + recommendation.accessory_remarks
        + recommendation.grooming_remarks
    )
    return annotate_caricature(
        caricature_path,
        all_remarks,
        output_path,
        max_remarks=10,
        overall_score=recommendation.overall_style_score,
        layout_mode=layout_mode,
        scale_factor=scale_factor,
        export_pdf=export_pdf,
        # Rich editorial data
        color_palette_do=recommendation.color_palette_do,
        color_palette_dont=recommendation.color_palette_dont,
        occasion=occasion,
        user_name=recommendation.user_profile.preferred_name or "",
        whats_working=recommendation.whats_working or "",
        recommended_outfit=recommendation.recommended_outfit_instead or "",
    )


def _maybe_rotate_base64(image_base64: str, media_type: str) -> str:
    """If the image is landscape (width > height * 1.15), rotate 90° CW and re-encode.

    This ensures Claude Vision and Replicate both receive an upright portrait,
    matching the orientation the renderer will display. No-op for portrait images.

    Args:
        image_base64: Base64-encoded JPEG image.
        media_type: MIME type (e.g. "image/jpeg").

    Returns:
        Base64-encoded JPEG, rotated if needed, otherwise the original string.
    """
    import base64
    import io

    try:
        from PIL import Image

        raw = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(raw))
        if img.width > img.height * 1.15:
            img = img.rotate(-90, expand=True)
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=92)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8")
    except Exception as exc:
        logger.warning("Could not auto-rotate image for vision: %s", exc)

    return image_base64


def _save_json(recommendation: StyleRecommendation, json_path: str) -> None:
    """Write analysis JSON to disk."""
    from src.output.formatter import save_json

    try:
        save_json(recommendation, json_path)
    except Exception as exc:
        logger.error("JSON save failed: %s", exc)


def _append_history(recommendation: StyleRecommendation, json_path: str) -> None:
    """Append this analysis to the history log."""
    from src.storage.history_store import append_history

    try:
        append_history(recommendation, json_path)
    except Exception as exc:
        logger.warning("History log update failed: %s", exc)
