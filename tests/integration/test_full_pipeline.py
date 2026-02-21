"""Integration tests for the full StyleAgent pipeline — all external calls mocked.

Tests cover:
  - Different skin undertone / body shape / occasion combinations
  - Onboarding (5 photos mocked)
  - Returning user loads profile
  - Caricature failure still returns text analysis
  - Vision failure raises clear error
  - Annotated output file created (renderer mocked)
  - JSON saved to outputs directory
  - History log updated after analysis

All Claude Vision, Claude Text, and Replicate API calls are mocked.
Filesystem reads (profile, image) use temp directories.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.models.user_profile import SkinUndertone, BodyShape, FaceShape, UserProfile
from src.models.grooming import GroomingProfile
from src.models.remark import RemarkCategory, Remark
from src.models.accessories import AccessoryType, AccessoryItem, AccessoryAnalysis
from src.models.footwear import FootwearAnalysis
from src.models.outfit import GarmentItem, OutfitBreakdown
from src.models.recommendation import StyleRecommendation


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    """Temporary directory for output files."""
    return tmp_path


@pytest.fixture()
def sample_image_path(tmp_dir: Path) -> str:
    """A tiny valid JPEG written to a temp file."""
    from PIL import Image
    img = Image.new("RGB", (800, 600), color=(100, 150, 200))
    path = tmp_dir / "outfit.jpg"
    img.save(str(path), "JPEG")
    return str(path)


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------


def _make_user_profile(
    undertone: SkinUndertone = SkinUndertone.DEEP_WARM,
    body_shape: BodyShape = BodyShape.INVERTED_TRIANGLE,
) -> UserProfile:
    return UserProfile(
        skin_undertone=undertone,
        skin_tone_depth="deep",
        skin_texture_visible="smooth",
        body_shape=body_shape,
        height_estimate="tall",
        build="athletic",
        shoulder_width="broad",
        torso_length="average",
        leg_proportion="long",
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
        confidence_scores={"skin_undertone": 0.89, "body_shape": 0.82},
        photos_used=5,
        profile_created_at="2024-01-01T00:00:00+00:00",
        profile_version=1,
    )


def _make_grooming_profile() -> GroomingProfile:
    return GroomingProfile(
        current_haircut_assessment="Taper fade",
        recommended_haircut="Keep taper fade",
        haircut_to_avoid="Bowl cut",
        styling_product_recommendation=["matte clay"],
        hair_color_recommendation="Keep natural black",
        current_beard_assessment="Full beard",
        recommended_beard_style="Trim cheek line",
        beard_grooming_tips=["Trim sides"],
        beard_style_to_avoid="Wide coverage",
        eyebrow_assessment="Natural",
        eyebrow_recommendation="Maintain",
        visible_skin_concerns=[],
        skincare_categories_needed=["moisturiser"],
        grooming_score=7,
        grooming_remarks=[],
    )


def _make_outfit_breakdown(
    occasion: str = "wedding_guest_indian",
    color_clash: bool = False,
    occasion_match: bool = True,
) -> OutfitBreakdown:
    return OutfitBreakdown(
        occasion_detected=occasion,
        occasion_requested=occasion,
        occasion_match=occasion_match,
        items=[GarmentItem(
            category="ethnic-top",
            garment_type="kurta",
            color="rust",
            pattern="solid",
            fabric_estimate="silk-cotton",
            fit="straight",
            length="mid-thigh",
            collar_type="mandarin",
            sleeve_type="full",
            condition="good",
            occasion_appropriate=True,
            issue="",
            fix="",
        )],
        accessory_analysis=AccessoryAnalysis(
            items_detected=[],
            missing_accessories=[],
            accessories_to_remove=[],
            accessory_harmony="good",
            overall_score=7,
        ),
        footwear_analysis=FootwearAnalysis(
            visible=True,
            type="mojaris",
            color="tan",
            material_estimate="leather",
            condition="clean",
            style_category="indian formal",
            occasion_match=True,
            outfit_match=True,
            issue="",
            recommended_instead="",
            shoe_care_note="",
        ),
        overall_color_harmony="harmonious" if not color_clash else "clashing",
        color_clash_detected=color_clash,
        silhouette_assessment="balanced",
        proportion_assessment="good",
        formality_level=8,
        outfit_score=7,
    )


def _make_recommendation(
    profile: UserProfile,
    outfit: OutfitBreakdown,
    overall_score: int = 7,
    gaps: list | None = None,
    priorities: list | None = None,
    caricature_path: str = "",
    annotated_path: str = "",
    json_path: str = "",
) -> StyleRecommendation:
    return StyleRecommendation(
        user_profile=profile,
        grooming_profile=_make_grooming_profile(),
        outfit_breakdown=outfit,
        outfit_remarks=[],
        grooming_remarks=[],
        accessory_remarks=[],
        footwear_remarks=[],
        color_palette_do=["rust", "terracotta"],
        color_palette_dont=["icy white"],
        color_palette_occasion_specific=[],
        recommended_outfit_instead="Rust silk kurta, mid-thigh",
        recommended_grooming_change="Trim cheek line",
        recommended_accessories="Tan leather strap",
        wardrobe_gaps=gaps or ["silk kurta"],
        shopping_priorities=priorities or ["silk kurta"],
        overall_style_score=overall_score,
        outfit_score=7,
        grooming_score=7,
        accessory_score=7,
        footwear_score=7,
        caricature_image_path=caricature_path,
        annotated_output_path=annotated_path,
        analysis_json_path=json_path,
    )


def _full_patch(
    profile: UserProfile,
    outfit: OutfitBreakdown,
    recommendation: StyleRecommendation,
    caricature_return: tuple = ("", ""),
    annotate_side_effect=None,
):
    """Patch ALL external calls in the pipeline at module level."""
    if annotate_side_effect is None:
        annotate_side_effect = lambda rec, src, dst: dst  # noqa: E731
    return patch.multiple(
        "src.agents.style_agent",
        _load_profile=MagicMock(return_value=profile),
        _prepare_image=MagicMock(return_value=("base64data", "image/jpeg")),
        _run_vision=MagicMock(return_value=outfit),
        _run_grooming=MagicMock(return_value=_make_grooming_profile()),
        _run_caricature=MagicMock(return_value=caricature_return),
        _run_recommendation=MagicMock(return_value=recommendation),
        _annotate=MagicMock(side_effect=annotate_side_effect),
        _save_json=MagicMock(),
        _append_history=MagicMock(),
    )


# ---------------------------------------------------------------------------
# Full pipeline — scenario tests
# ---------------------------------------------------------------------------


def test_warm_indian_casual_mocked(sample_image_path, tmp_dir):
    """Deep Warm profile + Indian casual outfit — pipeline completes."""
    from src.agents.style_agent import run_analysis

    profile = _make_user_profile(undertone=SkinUndertone.DEEP_WARM)
    outfit = _make_outfit_breakdown(occasion="indian_casual")
    rec = _make_recommendation(profile, outfit)

    with _full_patch(profile, outfit, rec):
        result = run_analysis(
            image_path=sample_image_path,
            occasion="indian_casual",
            output_dir=str(tmp_dir),
            use_api=False,
        )

    assert result.recommendation.overall_style_score == 7
    assert result.recommendation.user_profile.skin_undertone == SkinUndertone.DEEP_WARM


def test_cool_western_business_mocked(sample_image_path, tmp_dir):
    """Cool undertone + Western business formal — pipeline completes."""
    from src.agents.style_agent import run_analysis

    profile = _make_user_profile(undertone=SkinUndertone.COOL)
    outfit = _make_outfit_breakdown(occasion="western_business_formal")
    rec = _make_recommendation(profile, outfit, overall_score=8)

    with _full_patch(profile, outfit, rec):
        result = run_analysis(
            image_path=sample_image_path,
            occasion="western_business_formal",
            output_dir=str(tmp_dir),
            use_api=False,
        )

    assert result.recommendation.overall_style_score == 8


def test_deep_warm_wedding_guest_mocked(sample_image_path, tmp_dir):
    """Deep Warm + Wedding guest Indian — pipeline completes."""
    from src.agents.style_agent import run_analysis

    profile = _make_user_profile(undertone=SkinUndertone.DEEP_WARM)
    outfit = _make_outfit_breakdown(occasion="wedding_guest_indian")
    rec = _make_recommendation(profile, outfit)

    with _full_patch(profile, outfit, rec):
        result = run_analysis(
            image_path=sample_image_path,
            occasion="wedding_guest_indian",
            output_dir=str(tmp_dir),
            use_api=False,
        )

    assert isinstance(result.recommendation, StyleRecommendation)
    assert result.recommendation.outfit_breakdown.occasion_requested == "wedding_guest_indian"


def test_onboarding_5_photos_mocked(tmp_dir):
    """Onboarding builds a valid UserProfile from 5 mocked photos."""
    from src.agents.style_agent import run_onboarding

    from PIL import Image
    photo_paths = []
    for i in range(5):
        img = Image.new("RGB", (600, 800), color=(i * 40, 100, 150))
        p = tmp_dir / f"photo_{i+1}.jpg"
        img.save(str(p), "JPEG")
        photo_paths.append(str(p))

    built_profile = _make_user_profile()
    # Fake per-photo analysis dict that build_profile can consume
    fake_analysis = {
        "skin_undertone": "deep_warm", "skin_tone_depth": "deep",
        "skin_texture_visible": "smooth", "body_shape": "inverted_triangle",
        "height_estimate": "tall", "build": "athletic", "shoulder_width": "broad",
        "torso_length": "average", "leg_proportion": "long", "face_shape": "square",
        "jaw_type": "strong", "forehead": "average", "hair_color": "black",
        "hair_texture": "straight", "hair_density": "medium",
        "current_haircut_style": "taper fade", "haircut_length": "short",
        "hair_visible_condition": "healthy", "beard_style": "full",
        "beard_density": "dense", "beard_color": "black",
        "mustache_style": "natural", "beard_grooming_quality": "well groomed",
    }

    with (
        patch("src.services.image_service.validate_and_prepare",
              return_value={"base64_data": "b64", "media_type": "image/jpeg",
                            "width": 600, "height": 800, "original_path": "x"}),
        patch("src.agents.profile_builder.analyse_photo", return_value=fake_analysis),
        patch("src.agents.profile_builder.build_profile", return_value=built_profile),
        patch("src.agents.profile_builder.save_profile"),
    ):
        result = run_onboarding(photo_paths, refresh=False)

    assert isinstance(result, UserProfile)
    assert result.photos_used == 5


def test_returning_user_loads_profile_mocked(sample_image_path, tmp_dir):
    """Returning user profile is loaded from storage without re-onboarding."""
    from src.agents.style_agent import run_analysis

    profile = _make_user_profile()
    outfit = _make_outfit_breakdown()
    rec = _make_recommendation(profile, outfit)

    load_calls = []

    def _fake_load():
        load_calls.append(1)
        return profile

    with patch.multiple(
        "src.agents.style_agent",
        _load_profile=_fake_load,
        _prepare_image=MagicMock(return_value=("b64", "image/jpeg")),
        _run_vision=MagicMock(return_value=outfit),
        _run_grooming=MagicMock(return_value=_make_grooming_profile()),
        _run_caricature=MagicMock(return_value=("", "")),
        _run_recommendation=MagicMock(return_value=rec),
        _annotate=MagicMock(side_effect=lambda rec, src, dst: dst),
        _save_json=MagicMock(),
        _append_history=MagicMock(),
    ):
        run_analysis(image_path=sample_image_path, output_dir=str(tmp_dir), use_api=False)

    assert len(load_calls) == 1, "Profile should be loaded exactly once per run"


def test_caricature_fail_still_returns_text(sample_image_path, tmp_dir):
    """Caricature failure produces a warning but the text report is still complete."""
    from src.agents.style_agent import run_analysis

    profile = _make_user_profile()
    outfit = _make_outfit_breakdown()
    rec = _make_recommendation(profile, outfit)

    with _full_patch(
        profile, outfit, rec,
        caricature_return=("", "Caricature generation failed — text analysis still complete."),
    ):
        result = run_analysis(
            image_path=sample_image_path,
            output_dir=str(tmp_dir),
            use_api=True,
        )

    assert isinstance(result.recommendation, StyleRecommendation)
    assert any("Caricature" in w for w in result.warnings)
    assert result.caricature_path == ""


def test_vision_fail_clear_error(sample_image_path, tmp_dir):
    """Vision failure raises StyleAgentError with a readable message."""
    from src.agents.style_agent import run_analysis, StyleAgentError

    profile = _make_user_profile()

    with patch.multiple(
        "src.agents.style_agent",
        _load_profile=MagicMock(return_value=profile),
        _prepare_image=MagicMock(return_value=("b64", "image/jpeg")),
        _run_vision=MagicMock(side_effect=StyleAgentError("Vision analysis failed: timeout")),
    ):
        with pytest.raises(StyleAgentError, match="Vision analysis failed"):
            run_analysis(image_path=sample_image_path, output_dir=str(tmp_dir))


def test_annotated_output_created(sample_image_path, tmp_dir):
    """When caricature succeeds, annotate is called and annotated_path is set."""
    from src.agents.style_agent import run_analysis

    profile = _make_user_profile()
    outfit = _make_outfit_breakdown()
    fake_caricature = str(tmp_dir / "caric.png")
    fake_annotated = str(tmp_dir / "annotated.png")

    # Create a dummy caricature file so the pipeline sees it as "present"
    Path(fake_caricature).write_bytes(b"fake")

    rec = _make_recommendation(profile, outfit)
    annotate_calls = []

    def _fake_annotate(rec_arg, src, dst, **kwargs):
        annotate_calls.append(dst)
        return fake_annotated

    with patch.multiple(
        "src.agents.style_agent",
        _load_profile=MagicMock(return_value=profile),
        _prepare_image=MagicMock(return_value=("b64", "image/jpeg")),
        _run_vision=MagicMock(return_value=outfit),
        _run_grooming=MagicMock(return_value=_make_grooming_profile()),
        _run_caricature=MagicMock(return_value=(fake_caricature, "")),
        _run_recommendation=MagicMock(return_value=rec),
        _annotate=_fake_annotate,
        _save_json=MagicMock(),
        _append_history=MagicMock(),
    ):
        result = run_analysis(image_path=sample_image_path, output_dir=str(tmp_dir))

    assert len(annotate_calls) == 1
    assert result.annotated_path == fake_annotated


def test_json_saved_to_outputs(sample_image_path, tmp_dir):
    """_save_json is called once per analysis run."""
    from src.agents.style_agent import run_analysis

    profile = _make_user_profile()
    outfit = _make_outfit_breakdown()
    rec = _make_recommendation(profile, outfit)

    save_calls = []

    def _fake_save(rec_arg, path):
        save_calls.append(path)

    with patch.multiple(
        "src.agents.style_agent",
        _load_profile=MagicMock(return_value=profile),
        _prepare_image=MagicMock(return_value=("b64", "image/jpeg")),
        _run_vision=MagicMock(return_value=outfit),
        _run_grooming=MagicMock(return_value=_make_grooming_profile()),
        _run_caricature=MagicMock(return_value=("", "")),
        _run_recommendation=MagicMock(return_value=rec),
        _annotate=MagicMock(side_effect=lambda r, s, d: d),
        _save_json=_fake_save,
        _append_history=MagicMock(),
    ):
        run_analysis(image_path=sample_image_path, output_dir=str(tmp_dir))

    assert len(save_calls) == 1
    assert save_calls[0].endswith(".json")


def test_history_log_updated(sample_image_path, tmp_dir):
    """_append_history is called once per analysis run."""
    from src.agents.style_agent import run_analysis

    profile = _make_user_profile()
    outfit = _make_outfit_breakdown()
    rec = _make_recommendation(profile, outfit)

    history_calls = []

    def _fake_history(rec_arg, path):
        history_calls.append(rec_arg)

    with patch.multiple(
        "src.agents.style_agent",
        _load_profile=MagicMock(return_value=profile),
        _prepare_image=MagicMock(return_value=("b64", "image/jpeg")),
        _run_vision=MagicMock(return_value=outfit),
        _run_grooming=MagicMock(return_value=_make_grooming_profile()),
        _run_caricature=MagicMock(return_value=("", "")),
        _run_recommendation=MagicMock(return_value=rec),
        _annotate=MagicMock(side_effect=lambda r, s, d: d),
        _save_json=MagicMock(),
        _append_history=_fake_history,
    ):
        run_analysis(image_path=sample_image_path, output_dir=str(tmp_dir))

    assert len(history_calls) == 1
    assert isinstance(history_calls[0], StyleRecommendation)
