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
    "canvas_bg":    (14,  14,  16),   # near-black, very slight blue tint
    "header_bg":    (8,   8,   10),   # true black header
    "panel_bg":     (20,  20,  22),   # slightly lighter panel
    "card_bg":      (26,  26,  30),   # card background
    "divider":      (40,  40,  44),   # subtle divider — not too visible
    "text_primary": (242, 240, 235),  # warm near-white
    "text_muted":   (148, 144, 138),  # warm mid-grey
    "text_caption": (80,  78,  74),   # very muted caption
    "accent_gold":  (210, 172, 95),   # warm editorial gold
    "critical":     (186, 50,  50),   # desaturated red — not garish
    "moderate":     (204, 128, 38),   # warm amber
    "minor":        (62,  148, 80),   # muted green
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
    # Product catalogue entries for SHOP section — optional
    product_entries: list[Any] | None = None,
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
        product_entries:    List of ProductEntry objects for the SHOP section (optional).

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
                product_entries or [],
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
    product_entries: list[Any] | None = None,
) -> Any:
    """Render the new editorial layout.

    NO header. Recommendations left, cartoon right, shop at bottom.

      ┌──────────────────────────┬───────────────────────┐
      │                          │                       │
      │  RECOMMENDATIONS (48%)   │  CARICATURE  (52%)    │
      │                          │                       │
      │  1  Fix action bold      │  full cartoon image   │
      │     Issue context grey   │  clean, no overlays   │
      │                          │                       │
      │  2  Fix action bold      │  score gauge          │
      │     Issue context grey   │  bottom-right corner  │
      │                          │                       │
      ├──────────────────────────┴───────────────────────┤
      │  SHOP THIS LOOK  (optional, only if entries)      │
      └──────────────────────────────────────────────────┘
    """
    from PIL import Image, ImageDraw

    E     = _EDITORIAL
    fonts = _ensure_editorial_fonts()
    fw, fh = fig.size

    # Ensure minimum height
    TARGET_H = max(fh, 700)
    if fh < TARGET_H:
        scale = TARGET_H / fh
        fig   = fig.resize((int(fw * scale), TARGET_H))
        fw, fh = fig.size

    # Columns: recs 48%, cartoon 52%
    card_col = max(int(fw * 0.92), 660)
    img_col  = fw
    total_w  = card_col + img_col

    # SHOP section height
    n_shop = min(3, len(product_entries)) if product_entries else 0
    SHOP_H = (52 + n_shop * 110) if n_shop else 0

    total_h = fh + SHOP_H

    canvas = Image.new("RGB", (total_w, total_h), E["canvas_bg"])
    draw   = ImageDraw.Draw(canvas)

    # ── 1. Cartoon — RIGHT panel ───────────────────────────────────────────────
    canvas.paste(fig, (card_col, 0))

    # Score gauge — bottom-right corner of cartoon
    if overall_score is not None:
        GAUGE_R  = 48
        GAUGE_CX = card_col + fw - GAUGE_R - 20
        GAUGE_CY = fh - GAUGE_R - 20
        # Dark circle backing
        r_pad = GAUGE_R + 10
        draw.ellipse(
            [GAUGE_CX - r_pad, GAUGE_CY - r_pad,
             GAUGE_CX + r_pad, GAUGE_CY + r_pad],
            fill=(8, 8, 10),
        )
        _draw_score_gauge(
            draw, GAUGE_CX, GAUGE_CY, overall_score,
            radius=GAUGE_R,
            font_num=_ef(fonts, "playfair_bold",    28),
            font_lbl=_ef(fonts, "montserrat_light",  9),
            colors=E,
        )

    # Thin vertical divider
    draw.line([(card_col, 0), (card_col, fh)], fill=E["divider"], width=1)

    # ── 2. Recommendation cards — LEFT panel ───────────────────────────────────
    chosen = _select(remarks, max_remarks)
    _draw_remark_cards(
        draw, chosen,
        rx=0,
        ry=0,
        col_w=card_col,
        avail_h=fh,
        fonts=fonts,
        E=E,
        occasion=occasion,
        overall_score=overall_score,
    )

    # ── 3. SHOP section ────────────────────────────────────────────────────────
    if product_entries and n_shop > 0:
        shop_entries = _filter_shop_entries(product_entries, occasion, remarks, max_items=3)
        if shop_entries:
            _draw_shop_section(draw, canvas, fh, total_w, shop_entries, fonts, E)

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
    occasion: str = "",
    overall_score: int | None = None,
) -> None:
    """Draw luxury-magazine-style recommendation cards.

    Layout — left panel, top to bottom:

      ┌────────────────────────────────────┐
      │  INDIAN FORMAL  ·  5 / 10          │  ← occasion + score header (32px)
      ├────────────────────────────────────┤
      │                                    │
      │▌  Upgrade to chanderi or raw       │  ← fix: large bold white (18pt)
      │   silk-cotton blend, mid-thigh     │
      │                                    │
      │   The kurta fabric reads casual    │  ← issue: small muted grey (11pt)
      │                                    │
      ├────────────────────────────────────┤
      │                                    │
      │▌  Swap to embellished mojaris      │
      │   or juttis in tan or gold.        │
      │                                    │
      │   Leather oxfords don't match      │
      │   Indian traditional garments.     │
      │                                    │
      └────────────────────────────────────┘

    Fix is BIG. Issue is small and below. Lots of whitespace. Clean numbered bar.
    """
    PAD_X   = 36    # left/right padding
    PAD_T   = 28    # top padding inside card
    PAD_B   = 20    # bottom padding inside card
    BAR_W   = 4     # severity bar width
    HDR_H   = 36    # occasion+score strip at top
    CARD_SEP = 1    # 1px separator between cards

    f_hdr   = _ef(fonts, "montserrat_semibold", 10)
    f_num   = _ef(fonts, "playfair_bold",       20)
    f_fix   = _ef(fonts, "playfair_bold",       18)
    f_issue = _ef(fonts, "montserrat_light",    11)

    n = len(remarks)
    if n == 0:
        return

    # ── Occasion + score strip at very top of panel ───────────────────────────
    draw.rectangle([rx, ry, rx + col_w, ry + HDR_H], fill=E["header_bg"])
    draw.line([(rx, ry + HDR_H - 1), (rx + col_w, ry + HDR_H - 1)],
              fill=E["divider"], width=1)

    hdr_parts: list[str] = []
    if occasion:
        hdr_parts.append(_fmt_occasion(occasion).upper())
    if overall_score is not None:
        hdr_parts.append(f"{overall_score} / 10")
    hdr_text = "   ·   ".join(hdr_parts) if hdr_parts else "STYLE ANALYSIS"
    draw.text((rx + PAD_X, ry + 11), hdr_text, font=f_hdr, fill=E["text_caption"])

    # ── Cards fill remaining space below header ────────────────────────────────
    cards_ry    = ry + HDR_H
    cards_avail = avail_h - HDR_H

    text_w = col_w - PAD_X - 24    # text wrapping width

    # Pre-compute natural card heights
    card_specs: list[dict] = []
    for r in remarks:
        fix_text   = (getattr(r, "fix",   "") or "").strip()
        issue_text = (getattr(r, "issue", "") or "").strip()

        fix_lines   = _wrap_px(fix_text,   text_w, f_fix,   max_lines=4) if fix_text   else []
        issue_lines = _wrap_px(issue_text, text_w, f_issue, max_lines=2) if issue_text else []

        # Number height + fix lines + issue lines
        content_h = (
            32                                     # number + spacing
            + len(fix_lines) * 26                  # fix line height 26px
            + (12 if issue_lines else 0)           # gap before issue
            + len(issue_lines) * 16                # issue line height 16px
        )
        natural_h = PAD_T + content_h + PAD_B
        card_specs.append({
            "r":           r,
            "fix_lines":   fix_lines,
            "issue_lines": issue_lines,
            "content_h":   content_h,
            "natural_h":   natural_h,
        })

    # Fit to available space
    total_natural = sum(s["natural_h"] for s in card_specs) + CARD_SEP * (n - 1)
    if total_natural > cards_avail:
        scale = cards_avail / total_natural
        for s in card_specs:
            s["card_h"] = max(60, int(s["natural_h"] * scale))
    else:
        # Equal extra breathing room per card (capped at 40px each)
        extra_each = min(40, (cards_avail - total_natural) // max(1, n))
        for s in card_specs:
            s["card_h"] = s["natural_h"] + extra_each

    # Draw each card
    cy = cards_ry
    for idx, spec in enumerate(card_specs):
        r       = spec["r"]
        card_h  = spec["card_h"]
        cy2     = cy + card_h
        sev_col = E.get(r.severity, E["minor"])

        # Card background — pure canvas_bg, no panel colour tint
        draw.rectangle([rx, cy, rx + col_w - 1, cy2], fill=E["canvas_bg"])

        # Left severity bar
        draw.rectangle([rx, cy, rx + BAR_W, cy2], fill=sev_col)

        tx = rx + PAD_X
        ty = cy + PAD_T

        # Priority number — large playfair, gold
        num_str = str(r.priority_order)
        draw.text((tx, ty), num_str, font=f_num, fill=E["accent_gold"])
        try:
            num_w = f_num.getbbox(num_str)[2]
        except Exception:
            num_w = 20
        ty += 32   # fixed gap after number

        # Fix text — large, bold, white
        for line in spec["fix_lines"]:
            if ty + 26 > cy2 - 8:
                break
            draw.text((tx, ty), line, font=f_fix, fill=E["text_primary"])
            ty += 26

        # Issue text — small, muted, below fix
        if spec["issue_lines"] and ty + 12 < cy2 - 8:
            ty += 12   # gap between fix and issue
            for line in spec["issue_lines"]:
                if ty + 16 > cy2 - 4:
                    break
                draw.text((tx, ty), line, font=f_issue, fill=E["text_muted"])
                ty += 16

        # Thin separator
        if idx < n - 1:
            draw.rectangle(
                [rx, cy2, rx + col_w - 1, cy2 + CARD_SEP],
                fill=E["divider"],
            )

        cy = cy2 + CARD_SEP


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
    """Draw footer: circular colour dots left, Wear Instead text right.

    Minimalist — thin gold top line, circular swatches, clean label.
    """
    DOT_R    = 14     # radius of circular colour dot
    DOT_GAP  = 10     # gap between dots
    PAD      = 18

    draw.rectangle([0, fy, total_w, fy + footer_h], fill=E["header_bg"])
    draw.line([(0, fy), (total_w, fy)], fill=E["accent_gold"], width=1)

    f_lbl  = _ef(fonts, "montserrat_semibold", 9)
    f_text = _ef(fonts, "montserrat_light",   12)

    # Split: 55% for palette, 45% for wear instead
    split_x = int(total_w * 0.55)
    cy_mid  = fy + footer_h // 2  # vertical centre of footer

    # ── YOUR PALETTE label ────────────────────────────────────────────────────
    draw.text((PAD, fy + 10), "YOUR PALETTE", font=f_lbl, fill=E["accent_gold"])

    # ── DO swatches — circular dots, centred vertically ──────────────────────
    do_colours = color_palette_do[:8] if color_palette_do else []
    sx = PAD
    dot_y = fy + footer_h // 2 + 4  # slightly below centre (allow label above)
    for colour in do_colours:
        rgb = _NAME_TO_RGB.get(colour.lower().strip())
        if rgb is None:
            continue
        cx = sx + DOT_R
        if cx + DOT_R > split_x - 20:
            break
        draw.ellipse([cx - DOT_R, dot_y - DOT_R, cx + DOT_R, dot_y + DOT_R], fill=rgb)
        sx += DOT_R * 2 + DOT_GAP

    # ── AVOID swatches — smaller, faded, with cross overlay ──────────────────
    AVOID_R = 10
    avoid_colours = color_palette_dont[:5] if color_palette_dont else []
    if avoid_colours:
        draw.text((PAD, fy + footer_h - AVOID_R * 2 - 16), "AVOID", font=f_lbl, fill=E["critical"])
        ax = PAD + 52
        ay = fy + footer_h - AVOID_R - 10
        for colour in avoid_colours:
            rgb = _NAME_TO_RGB.get(colour.lower().strip())
            if rgb is None:
                continue
            if ax + AVOID_R > split_x - 10:
                break
            faded = tuple(max(0, int(c * 0.55)) for c in rgb)
            draw.ellipse(
                [ax - AVOID_R, ay - AVOID_R, ax + AVOID_R, ay + AVOID_R],
                fill=faded,
            )
            # Small ✕ overlay
            d = AVOID_R - 3
            draw.line([(ax - d, ay - d), (ax + d, ay + d)], fill=E["critical"], width=1)
            draw.line([(ax + d, ay - d), (ax - d, ay + d)], fill=E["critical"], width=1)
            ax += AVOID_R * 2 + 8

    # ── Vertical divider ─────────────────────────────────────────────────────
    draw.line(
        [(split_x, fy + 10), (split_x, fy + footer_h - 10)],
        fill=E["divider"], width=1,
    )

    # ── WEAR INSTEAD ─────────────────────────────────────────────────────────
    wx = split_x + PAD
    draw.text((wx, fy + 10), "WEAR INSTEAD", font=f_lbl, fill=E["accent_gold"])
    if recommended_outfit:
        avail_w = total_w - wx - PAD
        wo_lines = _wrap_px(recommended_outfit, avail_w, f_text, max_lines=4)
        wy = fy + 26
        for line in wo_lines:
            if wy + 14 > fy + footer_h - 4:
                break
            draw.text((wx, wy), line, font=f_text, fill=E["text_muted"])
            wy += 17


def _filter_shop_entries(
    entries: list[Any],
    occasion: str,
    remarks: list[Any],
    max_items: int = 4,
) -> list[Any]:
    """Select the most relevant product entries for the current occasion + remarks.

    Scoring:
    - +2 if the entry's occasion_relevance contains the current occasion
    - +1 for each remark whose category keyword appears in the entry's category name
    Ties are broken by list order (original priority). Returns up to max_items.
    """
    # Categories mentioned in remarks
    remark_categories: set[str] = set()
    for r in remarks:
        cat = (getattr(r, "category", "") or "").lower()
        if cat:
            remark_categories.add(cat)
        zone = (getattr(r, "body_zone", "") or "").lower()
        if zone:
            remark_categories.add(zone.replace("-", " "))

    scored: list[tuple[int, int, Any]] = []
    for idx, entry in enumerate(entries):
        score = 0
        occ_relevance = getattr(entry, "occasion_relevance", []) or []
        if occasion in occ_relevance:
            score += 2
        # Partial match: any occasion keyword appears
        for occ_part in (occasion or "").split("_"):
            if occ_part and any(occ_part in o for o in occ_relevance):
                score += 1
                break
        # Remark category boost
        entry_cat = (getattr(entry, "category", "") or "").lower()
        for cat in remark_categories:
            if cat in entry_cat or entry_cat in cat:
                score += 1
        scored.append((score, idx, entry))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return [e for _, _, e in scored[:max_items]]


def _draw_shop_section(
    draw: Any,
    canvas: Any,
    sy: int,
    total_w: int,
    entries: list[Any],
    fonts: dict,
    E: dict,
) -> None:
    """Draw SHOP THIS LOOK — clean, minimal 4-column grid.

    Each row (100px):
    ┌──────────────┬────────────────┬────────────────┬────────────────┐
    │ CATEGORY     │ HIGH STREET    │ DESIGNER       │ LUXURY         │
    │ reason       │ Brand · Price  │ Brand · Price  │ Brand · Price  │
    │              │ Product name   │ Product name   │ Product name   │
    └──────────────┴────────────────┴────────────────┴────────────────┘

    Minimal: uniform backgrounds, thin 1px dividers, no heavy borders.
    """
    SHOP_H_HDR = 52   # section header height
    ROW_H      = 100  # per product row
    PAD        = 16

    # Tier column backgrounds — subtle, barely different from canvas
    _TIER_BG: dict[str, tuple[int, int, int]] = {
        "high_street": (22, 22, 26),
        "designer":    (20, 22, 32),
        "luxury":      (18, 16, 14),
    }
    _TIER_LABELS: dict[str, str] = {
        "high_street": "HIGH STREET",
        "designer":    "DESIGNER",
        "luxury":      "LUXURY",
    }

    # ── Section header ────────────────────────────────────────────────────────
    draw.rectangle([0, sy, total_w, sy + SHOP_H_HDR], fill=E["header_bg"])
    draw.line([(0, sy), (total_w, sy)], fill=E["accent_gold"], width=1)

    f_header   = _ef(fonts, "playfair_bold",      18)
    f_tier_lbl = _ef(fonts, "montserrat_semibold", 8)
    f_brand    = _ef(fonts, "montserrat_semibold", 12)
    f_product  = _ef(fonts, "montserrat_light",    10)
    f_price    = _ef(fonts, "playfair_bold",        11)
    f_cat      = _ef(fonts, "montserrat_semibold", 10)
    f_reason   = _ef(fonts, "montserrat_light",     9)
    f_search   = _ef(fonts, "montserrat_light",     8)

    draw.text((PAD, sy + 16), "SHOP THIS LOOK", font=f_header, fill=E["accent_gold"])

    col_w     = total_w // 4
    tier_keys = ["high_street", "designer", "luxury"]

    # ── Product rows ──────────────────────────────────────────────────────────
    for row_idx, entry in enumerate(entries):
        row_y  = sy + SHOP_H_HDR + row_idx * ROW_H
        row_y2 = row_y + ROW_H

        # Thin row divider
        draw.line([(0, row_y), (total_w, row_y)], fill=E["divider"], width=1)

        # ── Category column ────────────────────────────────────────────────
        draw.rectangle([0, row_y, col_w - 1, row_y2], fill=E["canvas_bg"])

        category = str(getattr(entry, "category", "") or "")
        reason   = str(getattr(entry, "profile_reason", "") or "")

        cat_trunc = _fit_text(category, col_w - PAD * 2, f_cat)
        draw.text((PAD, row_y + PAD), cat_trunc, font=f_cat, fill=E["text_primary"])

        reason_lines = _wrap_px(reason, col_w - PAD * 2, f_reason, max_lines=4)
        ty = row_y + PAD + 18
        for line in reason_lines:
            if ty + 13 > row_y2 - 4:
                break
            draw.text((PAD, ty), line, font=f_reason, fill=E["text_muted"])
            ty += 13

        # ── Tier columns ────────────────────────────────────────────────────
        for t_idx, tier_key in enumerate(tier_keys):
            cx0 = col_w * (t_idx + 1)
            cx1 = cx0 + col_w - 1

            tier_obj = getattr(entry, tier_key, None)
            bg_col   = _TIER_BG.get(tier_key, E["canvas_bg"])
            draw.rectangle([cx0, row_y, cx1, row_y2], fill=bg_col)

            # Thin left divider between tier columns
            draw.line([(cx0, row_y), (cx0, row_y2)], fill=E["divider"], width=1)

            # Thin gold top accent for luxury only
            if tier_key == "luxury":
                draw.line([(cx0, row_y), (cx1, row_y)], fill=E["accent_gold"], width=1)

            # Tier label (small caps, gold)
            lbl = _TIER_LABELS.get(tier_key, tier_key.upper())
            draw.text((cx0 + PAD, row_y + 8), lbl, font=f_tier_lbl, fill=E["accent_gold"])

            if tier_obj is None:
                continue

            brand   = str(getattr(tier_obj, "brand", "") or "")
            product = str(getattr(tier_obj, "product_name", "") or "")
            price   = str(getattr(tier_obj, "price_range", "") or "")
            search  = str(getattr(tier_obj, "search_query", "") or "")
            tw      = col_w - PAD * 2

            ty = row_y + 22
            # Brand — semibold white
            draw.text((cx0 + PAD, ty), _fit_text(brand, tw, f_brand),
                      font=f_brand, fill=E["text_primary"])
            ty += 17
            # Price — gold
            draw.text((cx0 + PAD, ty), price, font=f_price, fill=E["accent_gold"])
            ty += 16
            # Product name — light grey, wrapped
            for line in _wrap_px(product, tw, f_product, max_lines=2):
                if ty + 13 > row_y2 - 16:
                    break
                draw.text((cx0 + PAD, ty), line, font=f_product, fill=E["text_muted"])
                ty += 13
            # Search hint — very muted caption at bottom
            if search and ty + 10 <= row_y2 - 4:
                draw.text((cx0 + PAD, row_y2 - 14),
                          f"↗ {search[:26]}",
                          font=f_search, fill=E["text_caption"])

    # Final bottom line
    bottom_y = sy + SHOP_H_HDR + len(entries) * ROW_H
    draw.line([(0, bottom_y - 1), (total_w, bottom_y - 1)], fill=E["divider"], width=1)


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
