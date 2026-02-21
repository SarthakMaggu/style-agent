"""Renderer — fashion editorial annotation.

Layout
------
Two modes:

  editorial (default, v2):
    Dark-mode magazine layout — near-black canvas, gold accents.
    Left panel : caricature (50% width) — clean, no dots, no clutter.
    Right panel: stacked remark cards, large readable text.
                 Each card: coloured left bar | [N] SEV — ZONE
                                              | Issue (grey, 13pt)
                                              | Fix   (white, 15pt, bold)
    Header (72px): STYLE ANALYSIS · USER NAME  |  occasion  |  N/10
    Footer (96px): colour swatches DO / AVOID  |  WEAR INSTEAD text

  sidebar (legacy):
    Two white sidebar panels flank the cartoon figure with angled dot lines.
    Preserved for backward compat.

Fonts
-----
Downloads Playfair Display Bold + Montserrat variants from GitHub on first
run to ~/.style-agent/fonts/. Falls back to system fonts silently.
"""

from __future__ import annotations

import logging
import re
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Google Font download URLs ──────────────────────────────────────────────────
_FONT_CACHE_DIR = Path.home() / ".style-agent" / "fonts"
_EDITORIAL_FONTS: dict[str, str] = {
    "PlayfairDisplay-Bold.ttf": (
        "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/"
        "PlayfairDisplay%5Bwght%5D.ttf"
    ),
    "Montserrat-Regular.ttf": (
        "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/"
        "Montserrat-Regular.ttf"
    ),
    "Montserrat-SemiBold.ttf": (
        "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/"
        "Montserrat-SemiBold.ttf"
    ),
    "Montserrat-Light.ttf": (
        "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/"
        "Montserrat-Light.ttf"
    ),
}

# ── Legacy sidebar constants ───────────────────────────────────────────────────
_SIDEBAR_FRAC = 0.52
_CANVAS_BG    = (250, 250, 250)
_DIVIDER_CLR  = (215, 215, 215)
_ZONE_SZ  = 12
_FIX_SZ   = 17
_BADGE_SZ = 26
_FIX_CLR  = (18,  18,  18)
_LINE_CLR = (190, 190, 190)
_DOT_RING = (255, 255, 255)
_BADGE_BG = (22,  22,  22)
_BADGE_FG = (80,  205, 255)
_PAD_X   = 18
_V_GAP   = 30
_DOT_R   = 9
_LINE_W  = 2
_BADGE_W = 112
_BADGE_H = 60
_BADGE_M = 14
_SEV: dict[str, tuple[int, int, int]] = {
    "critical": (210, 45,  45),
    "moderate": (215, 135, 0),
    "minor":    (45,  165, 75),
}
_FALLBACK_Y_FRAC: dict[str, float] = {
    "head":       0.05,
    "face":       0.13,
    "neck":       0.22,
    "upper-body": 0.35,
    "lower-body": 0.62,
    "feet":       0.78,
    "full-look":  0.48,
}
_SIDE_OVERRIDE: dict[str, str] = {
    "head":       "left",
    "lower-body": "left",
}

# ── Editorial colour palette ───────────────────────────────────────────────────
_EDITORIAL: dict[str, tuple[int, int, int]] = {
    "canvas_bg":    (18,  18,  18),
    "header_bg":    (10,  10,  10),
    "panel_bg":     (24,  24,  26),
    "card_bg":      (34,  34,  38),
    "divider":      (58,  58,  62),
    "text_primary": (238, 238, 232),
    "text_muted":   (155, 150, 142),
    "text_caption": (95,  92,  87),
    "accent_gold":  (212, 175, 100),
    "critical":     (192, 55,  55),
    "moderate":     (208, 132, 42),
    "minor":        (68,  155, 86),
}

# ── Colour name → RGB lookup for palette swatches ────────────────────────────
_NAME_TO_RGB: dict[str, tuple[int, int, int]] = {
    "rust":           (180, 85,  50),
    "terracotta":     (195, 100, 70),
    "mustard":        (210, 165, 40),
    "warm cream":     (245, 235, 215),
    "champagne":      (212, 195, 150),
    "warm champagne": (212, 195, 150),
    "deep teal":      (30,  100, 110),
    "teal":           (30,  110, 110),
    "burnt orange":   (195, 100, 30),
    "forest green":   (50,  90,  60),
    "forest":         (50,  90,  60),
    "navy":           (25,  40,  100),
    "navy blue":      (25,  40,  100),
    "burgundy":       (120, 30,  55),
    "deep burgundy":  (100, 25,  45),
    "emerald":        (25,  115, 75),
    "cobalt":         (30,  60,  180),
    "cobalt blue":    (30,  60,  180),
    "ivory":          (245, 242, 230),
    "warm white":     (245, 242, 230),
    "off-white":      (240, 237, 225),
    "charcoal":       (55,  55,  60),
    "olive":          (100, 105, 50),
    "olive green":    (90,  100, 45),
    "camel":          (190, 150, 90),
    "coral":          (220, 105, 90),
    "peach":          (235, 175, 145),
    "gold":           (200, 170, 60),
    "warm beige":     (215, 195, 165),
    "rose":           (200, 130, 130),
    "mauve":          (170, 120, 140),
    "lavender":       (180, 160, 210),
    "cool grey":      (155, 155, 165),
    "grey":           (140, 140, 140),
    "silver":         (190, 190, 195),
    "black":          (30,  30,  30),
    "white":          (240, 240, 240),
    "brown":          (120, 80,  50),
    "dark brown":     (80,  50,  30),
    "tan":            (175, 135, 90),
    "cognac":         (155, 80,  40),
    "warm red":       (195, 60,  50),
    "red":            (195, 50,  50),
    "blue":           (60,  100, 180),
    "pink":           (210, 150, 160),
    "purple":         (120, 70,  150),
    "royal purple":   (85,  40,  130),
    "cream":          (245, 235, 210),
    "sapphire":       (20,  65,  165),
    "warm brown":     (130, 85,  55),
    "sand":           (210, 190, 155),
    "stone":          (185, 175, 160),
    "khaki":          (170, 155, 100),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def annotate_caricature(
    caricature_path: str,
    remarks: list[Any],
    output_path: str,
    max_remarks: int = 7,
    overall_score: int | None = None,
    use_vision_locate: bool = True,
    layout_mode: str = "editorial",
    export_pdf: bool = False,
    scale_factor: float = 1.0,
    # Rich data for editorial layout — all optional, default to None/empty
    color_palette_do: list[str] | None = None,
    color_palette_dont: list[str] | None = None,
    occasion: str = "",
    user_name: str = "",
    whats_working: str = "",
    recommended_outfit: str = "",
) -> str:
    """Generate a fashion-editorial annotated image.

    Args:
        caricature_path:    Source cartoon / caricature image path.
        remarks:            Remark objects (.severity, .body_zone, .issue, .fix, .priority_order).
        output_path:        Destination JPEG path.
        max_remarks:        Max remark cards to draw.
        overall_score:      1–10 score for the gauge.
        use_vision_locate:  Call Claude Vision to locate zones (sidebar mode only).
        layout_mode:        "editorial" (dark magazine, default) or "sidebar" (legacy).
        export_pdf:         Also save a PDF alongside the JPEG.
        scale_factor:       Resolution multiplier (2.0 = hi-res).
        color_palette_do:   User's actual DO colour list from recommendation.
        color_palette_dont: User's actual AVOID colour list from recommendation.
        occasion:           Detected/requested occasion string for header.
        user_name:          User's preferred name for header personalisation.
        whats_working:      One-line positive from recommendation.
        recommended_outfit: "Wear Instead" text for footer.

    Returns:
        Path to saved annotated image, or caricature_path on failure.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError:
        logger.error("Pillow not installed")
        return caricature_path

    if not Path(caricature_path).exists():
        logger.warning("Image not found: %s", caricature_path)
        return caricature_path

    try:
        # Load & orient
        fig = Image.open(caricature_path).convert("RGB")
        fig = ImageOps.exif_transpose(fig)
        if fig.width > fig.height * 1.15:
            fig = fig.rotate(-90, expand=True)

        # Route to layout
        if layout_mode == "editorial":
            canvas = _editorial_layout(
                fig, remarks, max_remarks, overall_score,
                color_palette_do or [], color_palette_dont or [],
                occasion, user_name, whats_working, recommended_outfit,
            )
        else:
            canvas = _sidebar_layout(
                fig, remarks, max_remarks, overall_score,
                use_vision_locate, caricature_path,
            )

        # Scale up for hi-res
        if scale_factor > 1.0:
            new_w = int(canvas.width  * scale_factor)
            new_h = int(canvas.height * scale_factor)
            try:
                from PIL import Image as _Img
                canvas = canvas.resize((new_w, new_h), _Img.LANCZOS)
            except AttributeError:
                canvas = canvas.resize((new_w, new_h))

        # Save JPEG
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, "JPEG", quality=95)
        logger.info("Annotated → %s", output_path)

        # Optionally export PDF
        if export_pdf:
            pdf_path = re.sub(r"\.(jpe?g|png|webp)$", ".pdf", output_path,
                              flags=re.IGNORECASE)
            if pdf_path == output_path:
                pdf_path = output_path + ".pdf"
            try:
                canvas.save(pdf_path, "PDF", resolution=150)
                logger.info("PDF exported → %s", pdf_path)
            except Exception as pdf_exc:
                logger.warning("PDF export failed: %s", pdf_exc)

        return output_path

    except Exception as exc:
        logger.error("Render failed: %s", exc, exc_info=True)
        return caricature_path


# ═══════════════════════════════════════════════════════════════════════════════
# Editorial layout — dark magazine aesthetic
# ═══════════════════════════════════════════════════════════════════════════════

def _editorial_layout(
    fig: Any,
    remarks: list[Any],
    max_remarks: int,
    overall_score: int | None,
    color_palette_do: list[str],
    color_palette_dont: list[str],
    occasion: str,
    user_name: str,
    whats_working: str,
    recommended_outfit: str,
) -> Any:
    """Render the dark-mode editorial magazine layout.

    Structure:
      ┌──────────────────────────────────────────────────────────────┐
      │ HEADER (72px) — STYLE ANALYSIS  ·  USER  |  Occasion | N/10 │
      ├──────────────────────┬───────────────────────────────────────┤
      │  caricature (50%)    │  Remark cards (50%)                  │
      │  clean, full-size    │  [N] SEV — ZONE  large text          │
      │                      │  Issue text (grey 13pt)              │
      │                      │  Fix text (white 15pt)               │
      ├──────────────────────┴───────────────────────────────────────┤
      │ FOOTER (96px) — colour swatches  |  Wear Instead text        │
      └──────────────────────────────────────────────────────────────┘
    """
    from PIL import Image, ImageDraw

    E      = _EDITORIAL
    fonts  = _ensure_editorial_fonts()
    fw, fh = fig.size

    HEADER_H = 72
    FOOTER_H = 96

    # Canvas: caricature half + cards half, minimum 1400px wide
    # Scale caricature to a standard height for readability
    TARGET_FIG_H = max(fh, 600)   # at least 600px tall
    if fh < TARGET_FIG_H:
        scale    = TARGET_FIG_H / fh
        new_fw   = int(fw * scale)
        fig      = fig.resize((new_fw, TARGET_FIG_H))
        fw, fh   = fig.size

    img_col  = fw                      # caricature column = figure width
    card_col = max(img_col, 680)       # card column, at least 680px
    total_w  = img_col + card_col
    total_h  = fh + HEADER_H + FOOTER_H

    canvas = Image.new("RGB", (total_w, total_h), E["canvas_bg"])
    draw   = ImageDraw.Draw(canvas)

    # ── 1. Header ─────────────────────────────────────────────────────────────
    draw.rectangle([0, 0, total_w, HEADER_H], fill=E["header_bg"])
    # Gold accent bar (4px) on left edge
    draw.rectangle([0, 0, 4, HEADER_H], fill=E["accent_gold"])
    # Gold divider under header
    draw.line([(0, HEADER_H - 1), (total_w, HEADER_H - 1)],
              fill=E["accent_gold"], width=1)

    f_title = _ef(fonts, "playfair_bold",       28)
    f_occ   = _ef(fonts, "montserrat_light",     14)
    f_cap   = _ef(fonts, "montserrat_light",     10)
    f_score = _ef(fonts, "playfair_bold",         22)

    title = "STYLE ANALYSIS"
    if user_name:
        title = f"STYLE ANALYSIS  ·  {user_name.upper()}"
    draw.text((16, 12), title, font=f_title, fill=E["accent_gold"])

    if occasion:
        draw.text((16, 46), _fmt_occasion(occasion), font=f_occ, fill=E["text_muted"])

    draw.text((16, 62), "StyleAgent  ·  Fashion Intelligence",
              font=f_cap, fill=E["text_caption"])

    # Score top-right — large, clear
    if overall_score is not None:
        score_str = f"{overall_score} / 10"
        try:
            sw_px = f_score.getbbox(score_str)[2]
        except Exception:
            sw_px = len(score_str) * 14
        draw.text((total_w - sw_px - 20, 24), score_str,
                  font=f_score, fill=E["accent_gold"])

    # ── 2. Caricature panel (left) ────────────────────────────────────────────
    canvas.paste(fig, (0, HEADER_H))

    # Score gauge — 60px radius, bottom-left corner of caricature
    GAUGE_R  = 60
    GAUGE_CX = GAUGE_R + 14
    GAUGE_CY = HEADER_H + fh - GAUGE_R - 14
    # Dark backing so gauge reads over caricature
    draw.rectangle(
        [GAUGE_CX - GAUGE_R - 10, GAUGE_CY - GAUGE_R - 10,
         GAUGE_CX + GAUGE_R + 10, GAUGE_CY + GAUGE_R + 10],
        fill=(16, 16, 16),
    )
    if overall_score is not None:
        _draw_score_gauge(
            draw, GAUGE_CX, GAUGE_CY, overall_score,
            radius=GAUGE_R,
            font_num=_ef(fonts, "playfair_bold",    34),
            font_lbl=_ef(fonts, "montserrat_light", 12),
            colors=E,
        )

    # ── 3. Vertical divider ────────────────────────────────────────────────────
    draw.line([(img_col, HEADER_H), (img_col, HEADER_H + fh)],
              fill=E["divider"], width=1)

    # ── 4. Remark cards (right panel) ─────────────────────────────────────────
    chosen = _select(remarks, max_remarks)
    _draw_remark_cards(
        draw, chosen,
        rx=img_col + 1,
        ry=HEADER_H,
        col_w=card_col,
        avail_h=fh,
        fonts=fonts,
        E=E,
    )

    # ── 5. Footer ─────────────────────────────────────────────────────────────
    fy = HEADER_H + fh
    _draw_palette_footer(
        draw, fy, total_w, FOOTER_H,
        color_palette_do, color_palette_dont,
        recommended_outfit, fonts, E,
    )

    return canvas


def _draw_remark_cards(
    draw: Any,
    remarks: list[Any],
    rx: int,
    ry: int,
    col_w: int,
    avail_h: int,
    fonts: dict,
    E: dict,
) -> None:
    """Draw stacked remark cards — content-height, no wasted space.

    Each card layout:
      ┌─────────────────────────────────────────────────────┐
      │▌ [1] CRITICAL  ·  UPPER BODY                        │  ← meta bar (11pt semibold, severity colour)
      │  The kurta reads two levels below wedding standard.  │  ← issue text (13pt light, grey)
      │  Upgrade to chanderi silk or raw silk blend.         │  ← fix text (15pt semibold, white)
      └─────────────────────────────────────────────────────┘

    Card height = exactly what content needs (meta + issue lines + fix lines + padding).
    Cards are stacked compactly top-to-bottom. If total cards overflow avail_h, scale
    uniformly so they all fit.
    """
    BAR_W  = 8    # coloured left bar width
    PAD_L  = BAR_W + 16
    PAD_R  = 24
    PAD_T  = 12   # top padding inside card
    PAD_B  = 14   # bottom padding inside card
    LINE_I = 18   # issue line height
    LINE_F = 22   # fix line height
    META_H = 22   # meta line height
    GAP    = 3    # gap between cards

    f_meta  = _ef(fonts, "montserrat_semibold", 11)
    f_issue = _ef(fonts, "montserrat_light",    13)
    f_fix   = _ef(fonts, "montserrat_semibold", 15)

    n = len(remarks)
    if n == 0:
        return

    text_w = col_w - PAD_L - PAD_R

    # ── Pre-compute each card's natural height ─────────────────────────────────
    card_specs: list[dict] = []
    for r in remarks:
        issue_text = (getattr(r, "issue", "") or "").strip()
        fix_text   = (getattr(r, "fix",   "") or "").strip()

        issue_lines = _wrap_px(issue_text, text_w, f_issue, max_lines=2) if issue_text else []
        fix_lines   = _wrap_px(fix_text,   text_w, f_fix,   max_lines=3) if fix_text   else []

        natural_h = (PAD_T
                     + META_H
                     + len(issue_lines) * LINE_I
                     + (4 if issue_lines and fix_lines else 0)   # gap between issue and fix
                     + len(fix_lines)   * LINE_F
                     + PAD_B)
        card_specs.append({
            "r":           r,
            "issue_lines": issue_lines,
            "fix_lines":   fix_lines,
            "natural_h":   natural_h,
        })

    # ── Compute final card heights ─────────────────────────────────────────────
    # GAP between cards is drawn as a solid divider stripe (3px), not blank space
    GAP = 3
    total_natural = sum(s["natural_h"] for s in card_specs) + GAP * (n - 1)
    if total_natural > avail_h:
        # Scale all cards down proportionally so they all fit
        scale = avail_h / total_natural
        for s in card_specs:
            s["card_h"] = max(50, int(s["natural_h"] * scale))
    else:
        # Spread leftover evenly as extra bottom breathing room per card
        leftover    = avail_h - total_natural
        extra_each  = leftover // n
        for s in card_specs:
            s["card_h"] = s["natural_h"] + extra_each

    # ── Draw cards ────────────────────────────────────────────────────────────
    cy = ry
    for idx, spec in enumerate(card_specs):
        r       = spec["r"]
        card_h  = spec["card_h"]
        cy2     = cy + card_h
        sev_col = E.get(r.severity, E["minor"])

        # Card background (alternating for scannability)
        bg = E["card_bg"] if idx % 2 == 0 else E["panel_bg"]
        draw.rectangle([rx, cy, rx + col_w - 1, cy2], fill=bg)

        # Severity left bar
        draw.rectangle([rx, cy, rx + BAR_W, cy2], fill=sev_col)

        # ── Compute content height to vertically centre inside card ───────────
        n_issue  = len(spec["issue_lines"])
        n_fix    = len(spec["fix_lines"])
        gap_if   = 6 if (n_issue > 0 and n_fix > 0) else 0
        content_h = META_H + n_issue * LINE_I + gap_if + n_fix * LINE_F
        # Centre: start drawing at vertical midpoint minus half content height
        top_space = (card_h - content_h) // 2
        ty_start  = cy + max(PAD_T, top_space)

        # ── Meta line: [N] CRITICAL  ·  UPPER BODY ────────────────────────────
        tx = rx + PAD_L
        ty = ty_start

        num        = f"[{r.priority_order}]"
        sev        = r.severity.upper()
        zone_label = r.body_zone.replace("-", " ").upper()
        meta       = f"{num}  {sev}  ·  {zone_label}"
        draw.text((tx, ty), meta, font=f_meta, fill=sev_col)
        ty += META_H

        # ── Issue text ────────────────────────────────────────────────────────
        for line in spec["issue_lines"]:
            if ty + LINE_I > cy2 - 4:
                break
            draw.text((tx, ty), line, font=f_issue, fill=E["text_muted"])
            ty += LINE_I
        if spec["issue_lines"] and spec["fix_lines"]:
            ty += gap_if

        # ── Fix text ──────────────────────────────────────────────────────────
        for i, line in enumerate(spec["fix_lines"]):
            if ty + LINE_F > cy2 - 4:
                trunc = _fit_text(line, text_w, f_fix)
                draw.text((tx, ty), trunc, font=f_fix, fill=E["text_primary"])
                break
            draw.text((tx, ty), line, font=f_fix, fill=E["text_primary"])
            ty += LINE_F

        # Solid divider strip between cards (canvas_bg colour — clearly separates cards)
        if idx < n - 1:
            draw.rectangle(
                [rx, cy2, rx + col_w - 1, cy2 + GAP],
                fill=E["canvas_bg"],
            )

        cy = cy2 + GAP


def _draw_score_gauge(
    draw: Any,
    cx: int,
    cy: int,
    score: int,
    radius: int = 60,
    font_num: Any = None,
    font_lbl: Any = None,
    colors: dict | None = None,
) -> None:
    """Draw a circular arc score gauge with gold ring.

    Arc spans 270° (from bottom-left going clockwise). Filled proportionally
    to score/10 in gold. Score number centred inside in Playfair Bold.
    """
    E       = colors or _EDITORIAL
    score   = max(0, min(10, score))
    START   = 135     # degrees — bottom-left start
    TOTAL   = 270     # total arc degrees
    THICK   = max(8, radius // 7)

    bb = [cx - radius, cy - radius, cx + radius, cy + radius]

    # Background track
    draw.arc(bb, start=START, end=START + TOTAL,
             fill=E["divider"], width=THICK)
    # Gold fill proportional to score
    fill_deg = int(TOTAL * score / 10)
    if fill_deg > 0:
        draw.arc(bb, start=START, end=START + fill_deg,
                 fill=E["accent_gold"], width=THICK)

    # Score number centred
    if font_num:
        _ctext(draw, cx, cy - 6, str(score), font_num, E["text_primary"])
    if font_lbl:
        _ctext(draw, cx, cy + radius - THICK - 6, "/10", font_lbl, E["text_muted"])


def _draw_palette_footer(
    draw: Any,
    fy: int,
    total_w: int,
    footer_h: int,
    color_palette_do: list[str],
    color_palette_dont: list[str],
    recommended_outfit: str,
    fonts: dict,
    E: dict,
) -> None:
    """Draw footer: colour swatches left, Wear Instead text right."""
    SWATCH_SZ   = 44    # DO swatch size
    AVOID_SZ    = 32    # AVOID swatch size
    SWATCH_GAP  = 10
    PAD         = 18

    draw.rectangle([0, fy, total_w, fy + footer_h], fill=E["panel_bg"])
    draw.line([(0, fy), (total_w, fy)], fill=E["accent_gold"], width=1)

    f_lbl  = _ef(fonts, "montserrat_semibold", 10)
    f_name = _ef(fonts, "montserrat_light",     9)
    f_text = _ef(fonts, "montserrat_regular",  12)

    split_x = int(total_w * 0.60)

    # ── YOUR PALETTE label ─────────────────────────────────────────────────────
    draw.text((PAD, fy + 10), "YOUR PALETTE", font=f_lbl, fill=E["accent_gold"])

    # ── DO swatches ────────────────────────────────────────────────────────────
    swatch_y  = fy + 28
    name_y    = swatch_y + SWATCH_SZ + 3
    sx        = PAD
    do_colours = color_palette_do[:8] if color_palette_do else []
    for colour in do_colours:
        rgb = _NAME_TO_RGB.get(colour.lower().strip())
        if rgb is None:
            continue
        if sx + SWATCH_SZ > split_x - 20:
            break
        # Swatch square
        draw.rectangle(
            [sx, swatch_y, sx + SWATCH_SZ, swatch_y + SWATCH_SZ],
            fill=rgb,
        )
        draw.rectangle(
            [sx, swatch_y, sx + SWATCH_SZ, swatch_y + SWATCH_SZ],
            outline=E["divider"], width=1,
        )
        # Colour name below — abbreviated to 9 chars
        label = colour[:9] if len(colour) <= 9 else colour[:8] + "."
        draw.text((sx + 1, name_y), label, font=f_name, fill=E["text_caption"])
        sx += SWATCH_SZ + SWATCH_GAP

    # ── AVOID swatches ─────────────────────────────────────────────────────────
    avoid_colours = color_palette_dont[:5] if color_palette_dont else []
    if avoid_colours:
        avoid_row_y = fy + footer_h - AVOID_SZ - 16
        draw.text((PAD, avoid_row_y - 14), "AVOID", font=f_lbl, fill=E["critical"])
        ax = PAD + 56
        for colour in avoid_colours:
            rgb = _NAME_TO_RGB.get(colour.lower().strip())
            if rgb is None:
                continue
            if ax + AVOID_SZ > split_x - 10:
                break
            faded = tuple(int(c * 0.60) for c in rgb)
            draw.rectangle(
                [ax, avoid_row_y, ax + AVOID_SZ, avoid_row_y + AVOID_SZ],
                fill=faded,
            )
            draw.rectangle(
                [ax, avoid_row_y, ax + AVOID_SZ, avoid_row_y + AVOID_SZ],
                outline=E["critical"], width=1,
            )
            ax += AVOID_SZ + 8

    # ── Vertical divider ───────────────────────────────────────────────────────
    draw.line(
        [(split_x, fy + 8), (split_x, fy + footer_h - 8)],
        fill=E["divider"], width=1,
    )

    # ── WEAR INSTEAD ──────────────────────────────────────────────────────────
    wx = split_x + PAD
    draw.text((wx, fy + 10), "WEAR INSTEAD", font=f_lbl, fill=E["accent_gold"])
    if recommended_outfit:
        wo_lines = _wrap_px(recommended_outfit, total_w - wx - PAD, f_text, max_lines=5)
        wy = fy + 28
        for line in wo_lines:
            if wy + 15 > fy + footer_h - 4:
                break
            draw.text((wx, wy), line, font=f_text, fill=E["text_muted"])
            wy += 18


def _fmt_occasion(occ: str) -> str:
    """Format occasion slug for display.

    'wedding_guest_indian' → 'Wedding Guest — Indian'
    """
    parts       = occ.replace("_", " ").split()
    region_words = {"indian", "western", "ethnic"}
    out: list[str] = []
    for i, p in enumerate(parts):
        if i > 0 and p.lower() in region_words and out:
            out.append("—")
        out.append(p.capitalize())
    return " ".join(out)


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy sidebar layout — unchanged from v1
# ═══════════════════════════════════════════════════════════════════════════════

def _sidebar_layout(
    fig: Any,
    remarks: list[Any],
    max_remarks: int,
    overall_score: int | None,
    use_vision_locate: bool,
    caricature_path: str,
) -> Any:
    """Original two-panel sidebar layout (v1). Preserved for backward compat."""
    from PIL import Image, ImageDraw

    fw, fh = fig.size

    zone_locs: dict[str, dict] = {}
    if use_vision_locate:
        zone_locs = _locate_zones_for_image(caricature_path)

    sw      = int(fw * _SIDEBAR_FRAC)
    total_w = fw + 2 * sw
    canvas  = Image.new("RGB", (total_w, fh), _CANVAS_BG)
    fig_x   = sw
    canvas.paste(fig, (fig_x, 0))
    draw    = ImageDraw.Draw(canvas)

    f_zone  = _font(_ZONE_SZ)
    f_fix   = _font(_FIX_SZ)
    f_badge = _font(_BADGE_SZ)
    f_blbl  = _font(11)
    text_w  = sw - _PAD_X * 2

    chosen = _select(remarks, max_remarks)

    if zone_locs:
        visible_zones = {z for z, info in zone_locs.items() if info.get("visible")}
        chosen = [
            r for r in chosen
            if r.body_zone not in zone_locs or r.body_zone in visible_zones
        ]
        logger.debug("Visible zones: %s  |  Kept: %d", visible_zones, len(chosen))

    blocks: list[dict] = []
    for r in chosen:
        label = _clean(r.fix)
        lines = _wrap(_clean(r.fix), text_w, f_fix)
        blk_h = (_ZONE_SZ + 5) + len(lines) * (_FIX_SZ + 5)
        blk_h = max(blk_h, 50)
        blocks.append(dict(r=r, label=label, lines=lines, h=blk_h))

    if zone_locs:
        fig_top, fig_bottom, fig_cx = 0, fh, fw // 2
    else:
        fig_top, fig_bottom, fig_cx = _detect_figure_bounds(fig)

    fig_h_span = fig_bottom - fig_top
    used_l: list[int] = []
    used_r: list[int] = []
    badge_reserve = _BADGE_M + _BADGE_H + 10

    for blk in blocks:
        r    = blk["r"]
        zone = r.body_zone

        if zone_locs and zone in zone_locs:
            loc          = zone_locs[zone]
            dot_x_in_fig = int(loc["x_pct"] / 100.0 * fw)
            dot_y        = int(loc["y_pct"] / 100.0 * fh)
        else:
            y_frac       = _FALLBACK_Y_FRAC.get(zone, 0.48)
            dot_y        = int(fig_top + y_frac * fig_h_span)
            x_off        = _zone_x_offset(zone)
            dot_x_in_fig = int(fig_cx + x_off * fw)

        dot_x_in_fig = max(_DOT_R, min(dot_x_in_fig, fw - _DOT_R))
        dot_y        = max(0, min(dot_y, fh - 1))

        if zone_locs and zone in zone_locs:
            x_pct = zone_locs[zone]["x_pct"]
            side  = _SIDE_OVERRIDE.get(zone, "left" if x_pct < 50 else "right")
        else:
            x_off = _zone_x_offset(zone)
            side  = _SIDE_OVERRIDE.get(zone, "left" if x_off < -0.05 else "right")

        used    = used_r if side == "right" else used_l
        min_y   = badge_reserve if side == "right" else _V_GAP
        ideal   = dot_y - blk["h"] // 2
        placed  = _place(ideal, blk["h"], used, fh, min_y)
        used.append(placed)

        blk["dot_x"] = fig_x + dot_x_in_fig
        blk["dot_y"] = dot_y
        blk["side"]  = side
        blk["y"]     = placed

    for blk in blocks:
        r    = blk["r"]
        col  = _SEV.get(r.severity, _SEV["minor"])
        dx   = blk["dot_x"]
        dy   = blk["dot_y"]
        side = blk["side"]
        by   = blk["y"]
        bh   = blk["h"]
        bcy  = by + bh // 2

        if side == "left":
            tx      = _PAD_X
            line_sx = sw - 10
        else:
            tx      = fig_x + fw + _PAD_X
            line_sx = fig_x + fw + 10

        draw.line([(line_sx, bcy), (dx, dy)], fill=_LINE_CLR, width=_LINE_W)
        draw.ellipse(
            [dx - _DOT_R, dy - _DOT_R, dx + _DOT_R, dy + _DOT_R],
            fill=col, outline=_DOT_RING, width=2,
        )
        r5 = 5
        draw.ellipse(
            [line_sx - r5, bcy - r5, line_sx + r5, bcy + r5],
            fill=col,
        )
        zone_label = r.body_zone.replace("-", " ").upper()
        draw.text((tx, by), zone_label, font=f_zone, fill=col)
        ty = by + _ZONE_SZ + 6
        for line in blk["lines"]:
            draw.text((tx, ty), line, font=f_fix, fill=_FIX_CLR)
            ty += _FIX_SZ + 5

    if overall_score is not None:
        bx  = total_w - _BADGE_W - _BADGE_M
        by_ = _BADGE_M
        try:
            draw.rounded_rectangle(
                [bx, by_, bx + _BADGE_W, by_ + _BADGE_H],
                radius=10, fill=_BADGE_BG,
            )
        except AttributeError:
            draw.rectangle([bx, by_, bx + _BADGE_W, by_ + _BADGE_H], fill=_BADGE_BG)
        _ctext(draw, bx + _BADGE_W // 2, by_ + 16, "STYLE SCORE", f_blbl, (155, 155, 155))
        _ctext(draw, bx + _BADGE_W // 2, by_ + 42, f"{overall_score}/10", f_badge, _BADGE_FG)

    draw.line([(fig_x, 0),      (fig_x, fh)],      fill=_DIVIDER_CLR, width=1)
    draw.line([(fig_x + fw, 0), (fig_x + fw, fh)], fill=_DIVIDER_CLR, width=1)

    return canvas


# ═══════════════════════════════════════════════════════════════════════════════
# Vision zone locator
# ═══════════════════════════════════════════════════════════════════════════════

def _locate_zones_for_image(image_path: str) -> dict[str, dict]:
    """Call Claude Vision to locate body zones. Returns {} on failure."""
    try:
        from src.services.image_service import validate_and_prepare
        from src.services.anthropic_service import locate_zones

        prepared   = validate_and_prepare(image_path)
        b64        = prepared["base64_data"]
        media_type = prepared["media_type"]
        zones      = locate_zones(b64, media_type)
        logger.debug("Vision zone locate: %s",
                     {z: (v["visible"], v.get("x_pct"), v.get("y_pct"))
                      for z, v in zones.items()})
        return zones
    except Exception as exc:
        logger.warning("Vision zone locate failed (%s) — using heuristics", exc)
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
# Pixel heuristic fallback (sidebar mode, offline)
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_figure_bounds(img: Any) -> tuple[int, int, int]:
    """Fallback: detect figure top/bottom/centre using pixel brightness."""
    try:
        import numpy as np
        arr = np.array(img, dtype=np.int32)
        h, w = arr.shape[:2]

        cx_lo  = int(w * 0.30)
        cx_hi  = int(w * 0.70)
        center = arr[:, cx_lo:cx_hi]
        row_bright = center.mean(axis=(1, 2))

        dark_rows = np.where(row_bright < 90)[0]
        if len(dark_rows) > 0 and dark_rows[0] < int(h * 0.45):
            fig_top = int(dark_rows[0])
        else:
            grad    = np.abs(np.diff(row_bright))
            top_h   = grad[: h // 2]
            fig_top = int(np.argmax(top_h)) if top_h.max() > 5 else int(h * 0.10)

        fig_bottom = h - 1
        for y in range(h - 1, int(h * 0.50), -1):
            row = center[y]
            if row.mean() < 135 or row.std() > 25:
                fig_bottom = y
                break

        if (fig_bottom - fig_top) < int(0.20 * h):
            fig_top, fig_bottom = 0, h

        mid_top = fig_top + int((fig_bottom - fig_top) * 0.20)
        mid_bot = fig_top + int((fig_bottom - fig_top) * 0.80)
        patch   = 12
        corners = [arr[:patch, :patch], arr[:patch, w - patch:],
                   arr[h - patch:, :patch], arr[h - patch:, w - patch:]]
        bg_rgb  = np.median(
            np.concatenate([c.reshape(-1, 3) for c in corners], axis=0), axis=0)
        diff    = np.abs(arr - bg_rgb[None, None, :]).sum(axis=2)
        mid_mask = (diff > 40)[mid_top:mid_bot, :]
        col_sums = mid_mask.sum(axis=0).astype(float)
        fig_cx   = (int(np.average(np.arange(w, dtype=float), weights=col_sums))
                    if col_sums.sum() > 0 else w // 2)

        return fig_top, fig_bottom, fig_cx

    except Exception as exc:
        logger.debug("Figure heuristic failed (%s)", exc)
        return 0, img.height, img.width // 2


def _zone_x_offset(zone: str) -> float:
    """Fallback x-offset from figure centre (fraction of fig width)."""
    offsets: dict[str, float] = {
        "head":       0.00,
        "face":       0.10,
        "neck":       -0.06,
        "upper-body": 0.00,
        "lower-body": 0.00,
        "feet":       -0.04,
        "full-look":  0.02,
    }
    return offsets.get(zone, 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# Shared helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _select(remarks: list[Any], max_n: int) -> list[Any]:
    """One remark per body zone, sorted by priority_order."""
    by_pri = sorted(remarks, key=lambda r: r.priority_order)
    seen:   set[str]  = set()
    chosen: list[Any] = []
    for r in by_pri:
        zone = r.body_zone
        if zone in seen:
            continue
        seen.add(zone)
        chosen.append(r)
        if len(chosen) >= max_n:
            break
    return chosen


def _clean(text: str) -> str:
    """Extract first clean imperative sentence from fix text (≤60 chars).

    Used only in legacy sidebar mode.
    """
    if not text:
        return ""
    text = re.sub(
        r"^(Primary recommendation|Secondary option|Tertiary option|"
        r"Option \d+|Step \d+|\(\d+\)):\s*",
        "", text, flags=re.IGNORECASE,
    ).strip()
    first = re.split(r"\.\s+(?=[A-Z])|—|\n", text, maxsplit=1)[0]
    first = first.strip(" .,;:—")
    if len(first) > 52:
        best = -1
        for m in re.finditer(r",", first):
            if m.start() <= 54:
                best = m.start()
        if best >= 20:
            first = first[:best].strip()
    if len(first) > 60:
        first = first[:60].rsplit(" ", 1)[0].rstrip(" .,;:")
    return (first[0].upper() + first[1:]) if first else ""


def _wrap_px(text: str, max_px: int, font: Any, max_lines: int = 4) -> list[str]:
    """Word-wrap text to max_px width, returning up to max_lines lines.

    Does NOT truncate — returns all lines that fit up to max_lines.
    """
    if not text:
        return []

    def W(s: str) -> int:
        try:
            return font.getbbox(s)[2]
        except Exception:
            return len(s) * 8

    words  = text.split()
    lines: list[str] = []
    current: list[str] = []

    for word in words:
        candidate = " ".join(current + [word])
        if W(candidate) <= max_px:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
                if len(lines) >= max_lines:
                    break
            current = [word]

    if current and len(lines) < max_lines:
        lines.append(" ".join(current))

    return lines or [text[:40]]


def _wrap(text: str, max_px: int, font: Any) -> list[str]:
    """Legacy word-wrap for sidebar mode. Returns up to 3 lines."""
    return _wrap_px(text, max_px, font, max_lines=3)


def _fit_text(text: str, max_px: int, font: Any) -> str:
    """Truncate text to fit max_px, appending '…'."""
    def W(s: str) -> int:
        try:
            return font.getbbox(s)[2]
        except Exception:
            return len(s) * 8

    if W(text) <= max_px:
        return text

    lo, hi = 0, len(text)
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if W(text[:mid] + "…") <= max_px:
            lo = mid
        else:
            hi = mid
    return text[:lo].rstrip() + "…"


def _truncate_to_width(text: str, max_px: int, font: Any) -> str:
    """Alias for _fit_text — backward compat."""
    return _fit_text(text, max_px, font)


def _place(ideal: int, h: int, used: list[int], img_h: int,
           min_y: int = 0) -> int:
    """Non-overlapping vertical placement for a label block."""
    pos = max(min_y, min(ideal, img_h - h - 4))
    for _ in range(100):
        clash = next((u for u in used if abs(pos - u) < h + _V_GAP), None)
        if clash is None:
            break
        down = clash + h + _V_GAP
        up   = clash - h - _V_GAP
        if down + h <= img_h - 4:
            pos = down
        elif up >= min_y:
            pos = up
        else:
            pos = down
        pos = max(min_y, min(pos, img_h - h - 4))
    return pos


def _ensure_editorial_fonts() -> dict[str, str]:
    """Download Google Fonts to ~/.style-agent/fonts/ on first run.

    Returns a dict mapping role names to TTF file paths.
    Falls back silently to system fonts if download fails.

    Roles: playfair_bold, montserrat_regular, montserrat_semibold, montserrat_light
    """
    _FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    for filename, url in _EDITORIAL_FONTS.items():
        dest = _FONT_CACHE_DIR / filename
        # Delete corrupt / zero-byte files before re-downloading
        if dest.exists() and dest.stat().st_size < 10_000:
            dest.unlink()
            logger.debug("Removed corrupt font: %s", filename)
        if dest.exists():
            continue
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            dest.write_bytes(data)
            logger.debug("Downloaded font: %s  (%d bytes)", filename, len(data))
        except Exception as exc:
            logger.debug("Font download skipped (%s): %s", filename, exc)

    def _try(name: str) -> str:
        p = _FONT_CACHE_DIR / name
        return str(p) if (p.exists() and p.stat().st_size > 10_000) else ""

    _SYSTEM_SANS = next(
        (p for p in [
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ] if Path(p).exists()),
        "",
    )

    return {
        "playfair_bold":       _try("PlayfairDisplay-Bold.ttf")  or _SYSTEM_SANS,
        "montserrat_regular":  _try("Montserrat-Regular.ttf")    or _SYSTEM_SANS,
        "montserrat_semibold": _try("Montserrat-SemiBold.ttf")   or _SYSTEM_SANS,
        "montserrat_light":    _try("Montserrat-Light.ttf")       or _SYSTEM_SANS,
    }


def _ef(fonts: dict[str, str], role: str, size: int) -> Any:
    """Load editorial font by role at given size, fallback to system sans."""
    from PIL import ImageFont
    path = fonts.get(role, "")
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return _font(size)


def _font(size: int) -> Any:
    """Load best available system TrueType font at given size."""
    from PIL import ImageFont
    for p in [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFCompact.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _ctext(draw: Any, cx: int, cy: int, text: str, font: Any,
           color: tuple) -> None:
    """Draw text centred at (cx, cy)."""
    try:
        bb = font.getbbox(text)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
    except Exception:
        tw, th = len(text) * 8, 16
    draw.text((cx - tw // 2, cy - th // 2), text, font=font, fill=color)
