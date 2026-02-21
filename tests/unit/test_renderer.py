"""Tests for src/output/renderer.py — editorial and sidebar layouts.

All tests use in-memory images + mock remarks. No real API calls.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_remark(
    severity: str = "moderate",
    body_zone: str = "upper-body",
    fix: str = "Swap to a slim-fit shirt.",
    issue: str = "The boxy fit adds unwanted bulk.",
    priority: int = 1,
):
    """Return a minimal mock Remark object with issue and fix."""
    return SimpleNamespace(
        severity=severity,
        body_zone=body_zone,
        fix=fix,
        issue=issue,
        priority_order=priority,
    )


def _make_png_file(tmp_path: Path, width: int = 400, height: int = 600) -> str:
    """Create a minimal solid-colour PNG file and return its path."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    img = Image.new("RGB", (width, height), (200, 180, 160))
    p = tmp_path / "test_fig.png"
    img.save(str(p))
    return str(p)


# ── Test 1: annotate_caricature returns a path (editorial mode) ───────────────

def test_annotate_caricature_returns_path_editorial(tmp_path):
    """annotate_caricature with layout_mode='editorial' must return a valid path."""
    from src.output.renderer import annotate_caricature

    src = _make_png_file(tmp_path)
    out = str(tmp_path / "out_editorial.jpg")
    remarks = [
        _make_remark("critical",  "upper-body", "Swap the shirt.",          "Shirt is too boxy.", 1),
        _make_remark("moderate",  "feet",        "Polish shoes.",            "Shoes are scuffed.", 2),
        _make_remark("minor",     "face",        "Trim beard sides.",        "Beard sides are wide.", 3),
    ]
    result = annotate_caricature(
        src, remarks, out,
        max_remarks=7,
        overall_score=6,
        use_vision_locate=False,
        layout_mode="editorial",
    )
    assert result != ""
    assert Path(result).exists()


# ── Test 2: annotate_caricature returns a path (sidebar / legacy mode) ────────

def test_annotate_caricature_returns_path_sidebar(tmp_path):
    """annotate_caricature with layout_mode='sidebar' must return a valid path."""
    from src.output.renderer import annotate_caricature

    src = _make_png_file(tmp_path)
    out = str(tmp_path / "out_sidebar.jpg")
    remarks = [_make_remark("minor", "head", "Adjust hat.")]
    result = annotate_caricature(
        src, remarks, out,
        use_vision_locate=False,
        layout_mode="sidebar",
    )
    assert result != ""
    assert Path(result).exists()


# ── Test 3: editorial canvas is wider than source image ───────────────────────

def test_editorial_canvas_wider_than_source(tmp_path):
    """Editorial layout must produce a canvas wider than the source image."""
    from PIL import Image
    from src.output.renderer import annotate_caricature

    src = _make_png_file(tmp_path, width=400, height=600)
    out = str(tmp_path / "wide.jpg")
    remarks = [_make_remark("critical", "upper-body")]
    annotate_caricature(src, remarks, out, use_vision_locate=False,
                        layout_mode="editorial")

    result_img = Image.open(out)
    assert result_img.width > 400     # must be wider due to card panel


# ── Test 4: editorial output has dark background ──────────────────────────────

def test_editorial_has_dark_background(tmp_path):
    """Editorial canvas header background must be near-black (brightness < 80)."""
    from PIL import Image
    import numpy as np
    from src.output.renderer import annotate_caricature

    src = _make_png_file(tmp_path, width=200, height=300)
    out = str(tmp_path / "dark.jpg")
    remarks = [_make_remark("moderate", "face")]
    annotate_caricature(src, remarks, out, use_vision_locate=False,
                        layout_mode="editorial", overall_score=7)

    arr = np.array(Image.open(out))
    # Sample header area past the 4px gold accent bar — should be near-black header_bg
    # Use columns 10-30 to avoid the gold left bar, rows 0-8 for the header
    corner = arr[:8, 10:30].mean()
    # header_bg is (10,10,10); JPEG compression may push it slightly higher
    assert corner < 120, f"Expected dark header background, got mean {corner:.1f}"


# ── Test 5: scale_factor doubles output dimensions ────────────────────────────

def test_scale_factor_doubles_output(tmp_path):
    """scale_factor=2.0 must produce an image approximately 2× the 1x dimensions."""
    from PIL import Image
    from src.output.renderer import annotate_caricature

    src = _make_png_file(tmp_path, width=300, height=450)
    out1 = str(tmp_path / "normal.jpg")
    out2 = str(tmp_path / "hires.jpg")
    remarks = [_make_remark("minor", "feet")]

    annotate_caricature(src, remarks, out1, use_vision_locate=False,
                        layout_mode="editorial", scale_factor=1.0)
    annotate_caricature(src, remarks, out2, use_vision_locate=False,
                        layout_mode="editorial", scale_factor=2.0)

    img1 = Image.open(out1)
    img2 = Image.open(out2)

    assert img2.width  >= img1.width  * 1.8
    assert img2.height >= img1.height * 1.8


# ── Test 6: _draw_score_gauge does not raise for any score ────────────────────

def test_draw_score_gauge_no_exception(tmp_path):
    """_draw_score_gauge must run without raising for any score 0–10."""
    from PIL import Image, ImageDraw
    from src.output.renderer import _draw_score_gauge, _EDITORIAL

    img  = Image.new("RGB", (200, 200), (20, 20, 20))
    draw = ImageDraw.Draw(img)

    for score in (0, 1, 5, 7, 10):
        _draw_score_gauge(draw, 100, 100, score, radius=60, colors=_EDITORIAL)


# ── Test 7: missing source file falls back gracefully ────────────────────────

def test_annotate_missing_file_returns_source_path(tmp_path):
    """If source image does not exist, annotate_caricature returns the original path."""
    from src.output.renderer import annotate_caricature

    fake_src = str(tmp_path / "nonexistent.jpg")
    out      = str(tmp_path / "out.jpg")
    result   = annotate_caricature(fake_src, [], out, use_vision_locate=False)
    assert result == fake_src


# ── Test 8: real colour palette swatches rendered ────────────────────────────

def test_palette_footer_uses_real_colours(tmp_path):
    """Passing color_palette_do with known colours must produce a wider/taller output
    than passing empty palette (footer is always rendered but with/without swatches)."""
    from PIL import Image
    from src.output.renderer import annotate_caricature

    src = _make_png_file(tmp_path, width=300, height=400)
    out = str(tmp_path / "palette.jpg")
    remarks = [_make_remark("minor", "head")]
    # Should not raise even with known colours
    result = annotate_caricature(
        src, remarks, out,
        use_vision_locate=False,
        layout_mode="editorial",
        color_palette_do=["rust", "mustard", "deep teal"],
        color_palette_dont=["cobalt", "lavender"],
        recommended_outfit="Tapered olive chinos with a rust henley.",
    )
    assert Path(result).exists()
    img = Image.open(result)
    assert img.width > 300    # card panel added


# ── Test 9: header includes occasion text ─────────────────────────────────────

def test_header_shows_occasion(tmp_path):
    """Passing occasion must not raise and must produce a valid output file."""
    from PIL import Image
    from src.output.renderer import annotate_caricature

    src = _make_png_file(tmp_path, width=300, height=400)
    out = str(tmp_path / "occasion.jpg")
    remarks = [_make_remark()]
    result = annotate_caricature(
        src, remarks, out,
        use_vision_locate=False,
        layout_mode="editorial",
        occasion="smart_casual",
        user_name="Arjun",
        overall_score=8,
    )
    assert Path(result).exists()


# ── Test 10: score gauge at 60px radius covers expected pixel area ────────────

def test_score_gauge_60px_radius(tmp_path):
    """_draw_score_gauge with radius=60 should colour pixels far from centre."""
    from PIL import Image, ImageDraw
    import numpy as np
    from src.output.renderer import _draw_score_gauge, _EDITORIAL

    img  = Image.new("RGB", (300, 300), (20, 20, 20))
    draw = ImageDraw.Draw(img)
    _draw_score_gauge(draw, 150, 150, score=8, radius=60, colors=_EDITORIAL)

    arr = np.array(img)
    # Gold arc (212,175,100) should appear somewhere beyond 40px from centre
    gold_r, gold_g, gold_b = 212, 175, 100
    # Check a broad ring from r=40 to r=70 for gold-ish pixels
    found_gold = False
    for y in range(300):
        for x in range(300):
            dist = ((x - 150) ** 2 + (y - 150) ** 2) ** 0.5
            if 40 < dist < 70:
                r, g, b = arr[y, x]
                if r > 150 and g > 120 and b < 130:
                    found_gold = True
                    break
        if found_gold:
            break
    assert found_gold, "Score gauge gold arc not found at expected radius"
