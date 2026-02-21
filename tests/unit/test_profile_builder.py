"""Unit tests for agents/profile_builder.py — Step 13 (all mocked)."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.agents.profile_builder import (
    build_profile,
    save_profile,
    load_profile,
    refresh_profile,
    analyse_photo,
    categorise_photo,
    build_profile_from_folder,
    PhotoCategory,
    InsufficientPhotosError,
)
from src.models.user_profile import SkinUndertone, BodyShape, FaceShape, UserProfile


# ---------------------------------------------------------------------------
# Mock photo analysis data
# ---------------------------------------------------------------------------

def _photo_1_data(undertone: str = "deep_warm", face_shape: str = "square") -> dict:
    return {
        "skin_undertone": undertone,
        "skin_tone_depth": "deep",
        "skin_texture_visible": "smooth",
        "face_shape": face_shape,
        "jaw_type": "strong",
        "forehead": "average",
        "beard_style": "full",
        "beard_density": "dense",
        "beard_color": "black",
        "mustache_style": "natural",
        "beard_grooming_quality": "well groomed",
        "confidence_scores": {"skin_undertone": 0.9, "face_shape": 0.85},
    }


def _photo_3_data(body_shape: str = "inverted_triangle") -> dict:
    return {
        "body_shape": body_shape,
        "height_estimate": "tall",
        "build": "athletic",
        "shoulder_width": "broad",
        "torso_length": "average",
        "leg_proportion": "long",
        "current_outfit_style": "casual",
        "current_color_palette": ["navy", "white"],
        "fit_preference_observed": "slim",
        "confidence_scores": {"body_shape": 0.85},
    }


def _photo_5_data() -> dict:
    return {
        "style_vocabulary": "indian_traditional",
        "formality_default": "casual",
        "primary_colors_worn": ["navy", "white"],
        "accessory_habits": ["watch"],
        "footwear_type_seen": "sneakers",
        "fit_preference": "regular",
        "overall_grooming_impression": "well groomed",
        "hair_visible": {
            "hair_color": "black",
            "hair_texture": "straight",
            "hair_density": "medium",
            "current_haircut_style": "taper fade",
            "haircut_length": "short",
            "hair_visible_condition": "healthy",
        },
        "confidence_scores": {"style_vocabulary": 0.9},
    }


def _five_photos() -> list[dict]:
    return [
        _photo_1_data(),
        {"jaw_structure_depth": "prominent", "neck_proportions": "average",
         "facial_depth": "moderate", "beard_density_jawline": "dense", "nose_profile": "straight",
         "confidence_scores": {}},
        _photo_3_data(),
        {"posture": "upright", "belly_profile": "flat", "back_proportions": "straight",
         "build_depth": "average", "confidence_scores": {}},
        _photo_5_data(),
    ]


def _three_photos() -> list[dict]:
    return [_photo_1_data(), _photo_3_data(), _photo_5_data()]


# ---------------------------------------------------------------------------
# Build profile tests
# ---------------------------------------------------------------------------

def test_builds_profile_from_5_photos():
    profile = build_profile(_five_photos())
    assert isinstance(profile, UserProfile)
    assert profile.photos_used == 5


def test_accepts_3_photos_minimum():
    profile = build_profile(_three_photos())
    assert isinstance(profile, UserProfile)
    assert profile.photos_used == 3


def test_rejects_fewer_than_3():
    with pytest.raises(InsufficientPhotosError):
        build_profile([_photo_1_data(), _photo_3_data()])


def test_conflicting_undertone_majority_vote():
    """When 2 photos say deep_warm and 1 says cool, deep_warm should win."""
    analyses = [
        _photo_1_data(undertone="deep_warm"),
        {**_photo_3_data(), "skin_undertone": "deep_warm"},
        {**_photo_5_data(), "skin_undertone": "cool"},
    ]
    profile = build_profile(analyses)
    assert profile.skin_undertone == SkinUndertone.DEEP_WARM


def test_profile_has_correct_face_shape():
    profile = build_profile(_five_photos())
    assert profile.face_shape == FaceShape.SQUARE


def test_profile_has_correct_body_shape():
    profile = build_profile(_five_photos())
    assert profile.body_shape == BodyShape.INVERTED_TRIANGLE


def test_profile_has_confidence_scores():
    profile = build_profile(_five_photos())
    assert isinstance(profile.confidence_scores, dict)
    assert len(profile.confidence_scores) > 0


def test_profile_version_is_1_on_first_build():
    profile = build_profile(_five_photos())
    assert profile.profile_version == 1


def test_profile_hair_extracted():
    profile = build_profile(_five_photos())
    assert profile.current_haircut_style == "taper fade"
    assert profile.hair_color == "black"


# ---------------------------------------------------------------------------
# Save and load tests
# ---------------------------------------------------------------------------

def test_profile_saved_to_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "profile.json"
        profile = build_profile(_five_photos())
        save_profile(profile, path)
        assert path.exists()


def test_profile_loaded_matches_original():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "profile.json"
        profile = build_profile(_five_photos())
        save_profile(profile, path)
        loaded = load_profile(path)
        assert loaded.skin_undertone == profile.skin_undertone
        assert loaded.body_shape == profile.body_shape
        assert loaded.face_shape == profile.face_shape


def test_load_profile_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_profile(Path("/tmp/nonexistent_style_profile_xyz.json"))


# ---------------------------------------------------------------------------
# Refresh / version increment tests
# ---------------------------------------------------------------------------

def test_version_increments_on_refresh():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "profile.json"
        profile = build_profile(_five_photos())
        save_profile(profile, path)
        refreshed = refresh_profile(_five_photos(), path, existing_version=1)
        assert refreshed.profile_version == 2


def test_refresh_overwrites_existing():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "profile.json"

        # Build with square face
        profile = build_profile(_five_photos())
        save_profile(profile, path)

        # Refresh with round face majority
        round_analyses = [
            _photo_1_data(face_shape="round"),
            _photo_3_data(),
            {**_photo_5_data(), "face_shape": "round"},
        ]
        refresh_profile(round_analyses, path, existing_version=1)

        loaded = load_profile(path)
        assert loaded.face_shape == FaceShape.ROUND


# ---------------------------------------------------------------------------
# analyse_photo (mocked API)
# ---------------------------------------------------------------------------

def test_analyse_photo_calls_vision():
    mock_response = json.dumps(_photo_1_data())
    with patch("src.agents.profile_builder.call_vision", return_value=mock_response):
        result = analyse_photo(1, "fake_base64")
    assert result["skin_undertone"] == "deep_warm"


def test_analyse_photo_invalid_number():
    with pytest.raises(ValueError):
        from src.prompts.profile_analysis import get_photo_prompt
        get_photo_prompt(6)


# ---------------------------------------------------------------------------
# Phase A — categorise_photo and build_profile_from_folder (all mocked)
# ---------------------------------------------------------------------------


def test_categorise_photo_returns_valid_category():
    """categorise_photo must return a PhotoCategory enum value."""
    with patch("src.agents.profile_builder.call_vision", return_value="face_front"):
        result = categorise_photo("fake_base64", "image/jpeg")
    assert result == PhotoCategory.FACE_FRONT


def test_categorise_photo_skips_unclear():
    """categorise_photo must return UNCLEAR when vision returns an unknown label."""
    with patch("src.agents.profile_builder.call_vision", return_value="selfie"):
        result = categorise_photo("fake_base64", "image/jpeg")
    assert result == PhotoCategory.UNCLEAR


def test_categorise_photo_falls_back_on_error():
    """categorise_photo must return UNCLEAR on any API exception."""
    with patch(
        "src.agents.profile_builder.call_vision",
        side_effect=Exception("timeout"),
    ):
        result = categorise_photo("fake_base64", "image/jpeg")
    assert result == PhotoCategory.UNCLEAR


def test_build_profile_from_folder_raises_when_folder_missing():
    """build_profile_from_folder must raise FileNotFoundError for non-existent folder."""
    with pytest.raises(FileNotFoundError):
        build_profile_from_folder("/tmp/nonexistent_stylist_folder_xyz_123")


def test_build_profile_from_folder_raises_on_insufficient_photos(tmp_path):
    """build_profile_from_folder must raise InsufficientPhotosError when < 3 usable photos."""
    # Create 1 fake jpg so the folder isn't empty
    fake_img = tmp_path / "photo.jpg"
    fake_img.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # minimal JPEG header

    with (
        patch("src.agents.profile_builder.validate_and_prepare",
              return_value={"base64_data": "fake", "media_type": "image/jpeg"}),
        patch("src.agents.profile_builder.categorise_photo",
              return_value=PhotoCategory.UNCLEAR),
    ):
        with pytest.raises(InsufficientPhotosError):
            build_profile_from_folder(str(tmp_path))


def test_build_profile_from_folder_happy_path(tmp_path):
    """build_profile_from_folder must return a UserProfile on a mocked successful run."""
    # Create minimal fake image files
    for i in range(5):
        (tmp_path / f"photo{i}.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)

    face_resp   = json.dumps(_photo_1_data())
    body_resp   = json.dumps(_photo_3_data())
    outfit_resp = json.dumps(_photo_5_data())

    categories = [
        PhotoCategory.FACE_FRONT,
        PhotoCategory.FACE_SIDE,
        PhotoCategory.BODY_FRONT,
        PhotoCategory.BODY_SIDE,
        PhotoCategory.OUTFIT,
    ]

    call_count = 0
    def mock_call_vision(b64, mt, prompt):
        nonlocal call_count
        call_count += 1
        # 1st call per photo: categorisation, 2nd: analysis
        # But here categorise_photo is patched directly, so all calls are analysis
        if "body_front" in str(prompt) or "PHOTO_3" in str(prompt):
            return body_resp
        if "outfit" in str(prompt).lower() or "PHOTO_5" in str(prompt):
            return outfit_resp
        return face_resp

    with (
        patch("src.agents.profile_builder.validate_and_prepare",
              return_value={"base64_data": "fake", "media_type": "image/jpeg"}),
        patch("src.agents.profile_builder.categorise_photo",
              side_effect=categories),
        patch("src.agents.profile_builder.call_vision",
              side_effect=lambda b64, mt, prompt: (
                  body_resp if "body" in prompt.lower()
                  else outfit_resp if "outfit" in prompt.lower() or "style" in prompt.lower()
                  else face_resp
              )),
    ):
        profile = build_profile_from_folder(str(tmp_path), preferred_name="Arjun")

    assert isinstance(profile, UserProfile)
    assert profile.preferred_name == "Arjun"
    assert profile.seasonal_color_type is not None  # must be derived


def test_build_profile_from_folder_style_archetype_from_outfits(tmp_path):
    """style_archetype must be derived from outfit photo style_vocabulary."""
    (tmp_path / "outfit1.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)
    (tmp_path / "outfit2.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)
    (tmp_path / "face1.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)

    streetwear_outfit = {**_photo_5_data(), "style_vocabulary": "streetwear"}

    with (
        patch("src.agents.profile_builder.validate_and_prepare",
              return_value={"base64_data": "fake", "media_type": "image/jpeg"}),
        patch("src.agents.profile_builder.categorise_photo",
              side_effect=[
                  PhotoCategory.OUTFIT,
                  PhotoCategory.OUTFIT,
                  PhotoCategory.FACE_FRONT,
              ]),
        patch("src.agents.profile_builder.call_vision",
              return_value=json.dumps(streetwear_outfit)),
    ):
        profile = build_profile_from_folder(str(tmp_path))

    assert profile.style_archetype == "streetwear"


def test_build_profile_from_folder_preferred_name_stored(tmp_path):
    """preferred_name passed to build_profile_from_folder must appear on profile."""
    (tmp_path / "p1.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)
    (tmp_path / "p2.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)
    (tmp_path / "p3.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)

    with (
        patch("src.agents.profile_builder.validate_and_prepare",
              return_value={"base64_data": "fake", "media_type": "image/jpeg"}),
        patch("src.agents.profile_builder.categorise_photo",
              side_effect=[
                  PhotoCategory.FACE_FRONT,
                  PhotoCategory.BODY_FRONT,
                  PhotoCategory.OUTFIT,
              ]),
        patch("src.agents.profile_builder.call_vision",
              side_effect=[
                  json.dumps(_photo_1_data()),
                  json.dumps(_photo_3_data()),
                  json.dumps(_photo_5_data()),
              ]),
    ):
        profile = build_profile_from_folder(str(tmp_path), preferred_name="Dev")

    assert profile.preferred_name == "Dev"


def test_build_profile_from_folder_seasonal_type_is_derived(tmp_path):
    """seasonal_color_type must be a valid season string after folder build."""
    valid_seasons = {"spring", "summer", "autumn", "winter"}
    (tmp_path / "p1.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)
    (tmp_path / "p2.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)
    (tmp_path / "p3.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 20)

    with (
        patch("src.agents.profile_builder.validate_and_prepare",
              return_value={"base64_data": "fake", "media_type": "image/jpeg"}),
        patch("src.agents.profile_builder.categorise_photo",
              side_effect=[
                  PhotoCategory.FACE_FRONT,
                  PhotoCategory.BODY_FRONT,
                  PhotoCategory.OUTFIT,
              ]),
        patch("src.agents.profile_builder.call_vision",
              side_effect=[
                  json.dumps(_photo_1_data()),
                  json.dumps(_photo_3_data()),
                  json.dumps(_photo_5_data()),
              ]),
    ):
        profile = build_profile_from_folder(str(tmp_path))

    assert profile.seasonal_color_type in valid_seasons
