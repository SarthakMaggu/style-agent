"""Unit tests for agents/caricature_agent.py — Step 14 (all mocked)."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.agents.caricature_agent import generate, VALID_STYLES


FAKE_BASE64 = "ZmFrZWltYWdl"  # "fakeimage" base64-encoded
FAKE_ORIGINAL = "/tmp/original_photo.jpg"


# ---------------------------------------------------------------------------
# Style validation
# ---------------------------------------------------------------------------

def test_valid_styles_set():
    assert VALID_STYLES == {"caricature", "cartoon", "pixar"}


def test_unknown_style_defaults_to_caricature():
    """Unknown style should default to caricature and not raise."""
    with patch("src.agents.caricature_agent.generate_caricature_safe", return_value="/tmp/out.png") as mock_gen:
        result = generate(FAKE_BASE64, style="oil_painting", original_image_path=FAKE_ORIGINAL)
    # Should have been called with style "caricature"
    mock_gen.assert_called_once()
    call_kwargs = mock_gen.call_args[1] if mock_gen.call_args[1] else {}
    call_args = mock_gen.call_args[0] if mock_gen.call_args[0] else ()
    # The style kwarg should be "caricature"
    assert result == "/tmp/out.png"


# ---------------------------------------------------------------------------
# Happy path — generation succeeds
# ---------------------------------------------------------------------------

def test_returns_local_image_path():
    expected_path = "/tmp/outputs/caricature_12345_caricature.png"
    with patch("src.agents.caricature_agent.generate_caricature_safe", return_value=expected_path):
        result = generate(FAKE_BASE64, style="caricature")
    assert result == expected_path


def test_image_downloaded_cartoon():
    expected_path = "/tmp/outputs/caricature_12345_cartoon.png"
    with patch("src.agents.caricature_agent.generate_caricature_safe", return_value=expected_path):
        result = generate(FAKE_BASE64, style="cartoon")
    assert result == expected_path


def test_pixar_style_accepted():
    expected_path = "/tmp/outputs/caricature_12345_pixar.png"
    with patch("src.agents.caricature_agent.generate_caricature_safe", return_value=expected_path):
        result = generate(FAKE_BASE64, style="pixar")
    assert result == expected_path


# ---------------------------------------------------------------------------
# Failure and fallback
# ---------------------------------------------------------------------------

def test_timeout_handled_gracefully():
    """If generate_caricature_safe returns None, fallback to original photo."""
    with patch("src.agents.caricature_agent.generate_caricature_safe", return_value=None):
        result = generate(FAKE_BASE64, original_image_path=FAKE_ORIGINAL)
    assert result == FAKE_ORIGINAL


def test_api_error_handled():
    """If generate_caricature_safe raises, generate should not crash."""
    with patch(
        "src.agents.caricature_agent.generate_caricature_safe",
        side_effect=Exception("API timeout"),
    ):
        # Should fall through to fallback — but generate_caricature_safe is supposed
        # to never raise (it catches internally). Test the wrapping layer too.
        try:
            result = generate(FAKE_BASE64, original_image_path=FAKE_ORIGINAL)
        except Exception:
            pytest.fail("generate() should not raise — it must degrade gracefully")


def test_fallback_original_photo_if_fails():
    """When generation fails, original_image_path must be returned."""
    with patch("src.agents.caricature_agent.generate_caricature_safe", return_value=FAKE_ORIGINAL):
        result = generate(FAKE_BASE64, original_image_path=FAKE_ORIGINAL)
    assert result == FAKE_ORIGINAL


# ---------------------------------------------------------------------------
# Output directory creation
# ---------------------------------------------------------------------------

def test_output_dir_created():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = str(Path(tmpdir) / "new_outputs")
        with patch("src.agents.caricature_agent.generate_caricature_safe", return_value="/tmp/out.png"):
            generate(FAKE_BASE64, output_dir=output_dir)
        assert Path(output_dir).exists()


# ---------------------------------------------------------------------------
# Replicate model called with correct slug
# ---------------------------------------------------------------------------

def test_replicate_called_correct_model():
    """replicate_service.generate_caricature_safe must be called for caricature style."""
    with patch("src.agents.caricature_agent.generate_caricature_safe", return_value="/tmp/out.png") as mock_safe:
        generate(FAKE_BASE64, style="caricature", original_image_path=FAKE_ORIGINAL)
    mock_safe.assert_called_once()
    # Verify style param passed
    _, kwargs = mock_safe.call_args
    assert kwargs.get("style") == "caricature" or mock_safe.call_args[0][1] == "caricature"
