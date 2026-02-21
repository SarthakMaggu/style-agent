"""Formatter — terminal output and JSON file export for StyleRecommendation.

Terminal output uses the canonical format defined in CLAUDE.md.
Every text field is word-wrapped to a clean column width so nothing
is ever truncated, half-shown, or cut mid-sentence.
"""

import json
import logging
import textwrap
from pathlib import Path

from src.models.recommendation import StyleRecommendation

logger = logging.getLogger(__name__)

_WIDTH       = 70          # total print width
_TEXT_WIDTH  = 66          # wrap width for body text
_DIVIDER     = "═" * _WIDTH
_THIN        = "─" * _WIDTH
_INDENT      = "    "      # 4-space indent for body content
_CONT        = "      "    # 6-space continuation indent (for Fix/Issue/Why labels)


# ─────────────────────────────────────────────────────────────────────────────
def print_recommendation(recommendation: StyleRecommendation, occasion: str = "") -> None:
    """Print the complete style analysis report to terminal.

    Every field is fully displayed — no truncation, no half-brackets.
    Long text is word-wrapped with a clean continuation indent.
    """
    rec = recommendation
    up  = rec.user_profile
    gp  = rec.grooming_profile
    ob  = rec.outfit_breakdown

    # ── Header ────────────────────────────────────────────────────────────────
    _out(_DIVIDER)
    occ = _fmt_occasion(occasion or ob.occasion_requested)
    _out(f"  STYLE ANALYSIS  |  {occ}")
    _out(f"  Overall Score   : {rec.overall_style_score} / 10")
    _out(_DIVIDER)

    # ── Score bars ────────────────────────────────────────────────────────────
    _blank()
    _out(_score_bar("Outfit",    rec.outfit_score))
    _out(_score_bar("Grooming",  rec.grooming_score))
    _out(_score_bar("Accessory", rec.accessory_score))
    if ob.footwear_analysis.visible:
        _out(_score_bar("Footwear",  rec.footwear_score))

    # ── Profile ───────────────────────────────────────────────────────────────
    _blank()
    _out(_THIN)
    _out("YOUR PROFILE")
    _out(_THIN)
    _out(f"  Undertone   : {_fmt_undertone(up.skin_undertone.value)}")
    _out(f"  Skin depth  : {up.skin_tone_depth.capitalize()}")
    _out(f"  Body Shape  : {_fmt_val(up.body_shape.value)}")
    _out(f"  Build       : {up.build.capitalize()}, {up.shoulder_width} shoulders")
    _out(f"  Height      : {up.height_estimate.capitalize()}")
    _out(f"  Face Shape  : {up.face_shape.value.capitalize()}")
    _out(f"  Hair        : {up.haircut_length.capitalize()} {up.current_haircut_style}, "
         f"{up.hair_texture}, {up.hair_density} density")
    _out(f"  Beard       : {up.beard_style.capitalize()} beard, {up.beard_grooming_quality}")

    # ── Outfit breakdown ──────────────────────────────────────────────────────
    _blank()
    _out(_THIN)
    _out("OUTFIT BREAKDOWN")
    _out(_THIN)
    for item in ob.items:
        label = item.garment_type.replace("_", " ").capitalize()
        desc  = (f"{item.color.capitalize()} {item.fabric_estimate}, "
                 f"{item.fit} fit, {item.length} length")
        _out(f"  {label:<14}: {desc}")
    for acc in ob.accessory_analysis.items_detected:
        label = acc.type.value.capitalize()
        _out(f"  {label:<14}: {acc.color.capitalize()} — {acc.style_category}")
    fw = ob.footwear_analysis
    if fw.visible:
        _out(f"  {'Footwear':<14}: {fw.type.capitalize()}, {fw.color}, {fw.condition}")
    else:
        _out(f"  {'Footwear':<14}: Not visible in frame")
    _blank()
    _wrap_field("Color Harmony", ob.overall_color_harmony)
    _wrap_field("Silhouette",    ob.silhouette_assessment)
    _out(f"  Formality      : {ob.formality_level} / 10")
    _out(f"  Occasion match : {'✓' if ob.occasion_match else '✗'}")

    # ── What's working (v2 stylist voice) ────────────────────────────────────
    if rec.whats_working:
        _blank()
        _out(_THIN)
        _out("WHAT'S WORKING")
        _out(_THIN)
        _multiline_wrap(rec.whats_working, indent="  ")

    # ── Priority fix (v2 stylist voice) ──────────────────────────────────────
    if rec.priority_fix_two:
        _blank()
        _out(_THIN)
        _out("FIX THESE TWO THINGS FIRST")
        _out(_THIN)
        _multiline_wrap(rec.priority_fix_two, indent="  ")

    # ── Remarks ───────────────────────────────────────────────────────────────
    all_remarks = (
        rec.outfit_remarks
        + rec.footwear_remarks
        + rec.accessory_remarks
        + rec.grooming_remarks
    )
    all_remarks.sort(key=lambda r: r.priority_order)

    if all_remarks:
        _blank()
        _out(_THIN)
        _out("REMARKS  (fix in this order)")
        _out(_THIN)

        for idx, r in enumerate(all_remarks, 1):
            _blank()
            cat   = r.category.value.upper().replace("_", " ")
            zone  = r.body_zone.upper().replace("-", " ")
            _out(f"  [{idx}] {r.severity.upper()}  |  {cat}  |  {zone}")
            _blank()
            _labeled_wrap("Issue", r.issue)
            _blank()
            _labeled_wrap("Fix",   r.fix)
            _blank()
            _labeled_wrap("Why",   r.why)

    # ── Color palette ─────────────────────────────────────────────────────────
    _blank()
    _out(_THIN)
    _out("YOUR COLOR PALETTE")
    _out(_THIN)
    if rec.color_palette_do:
        do_chunks = _chunk_list(rec.color_palette_do, per_line=4)
        _out("  ✓  Wear  :")
        for chunk in do_chunks:
            _out("             " + "  ·  ".join(c.capitalize() for c in chunk))
    if rec.color_palette_dont:
        _out("  ✗  Avoid :")
        dont_chunks = _chunk_list(rec.color_palette_dont, per_line=4)
        for chunk in dont_chunks:
            _out("             " + "  ·  ".join(c.capitalize() for c in chunk))
    if rec.color_palette_occasion_specific:
        _out("  ★  For this occasion :")
        occ_chunks = _chunk_list(rec.color_palette_occasion_specific, per_line=4)
        for chunk in occ_chunks:
            _out("             " + "  ·  ".join(c.capitalize() for c in chunk))

    # ── Wear this instead ─────────────────────────────────────────────────────
    if rec.recommended_outfit_instead:
        _blank()
        _out(_THIN)
        _out("WEAR THIS INSTEAD")
        _out(_THIN)
        _multiline_wrap(rec.recommended_outfit_instead, indent="  ")

    if rec.recommended_accessories:
        _blank()
        _out("  ACCESSORIES")
        _multiline_wrap(rec.recommended_accessories, indent="  ")

    # ── Grooming ──────────────────────────────────────────────────────────────
    _blank()
    _out(_THIN)
    _out("GROOMING")
    _out(_THIN)
    if gp.recommended_haircut:
        _labeled_wrap("Hair",   gp.recommended_haircut)
    if gp.recommended_beard_style:
        _blank()
        _labeled_wrap("Beard",  gp.recommended_beard_style)
    if gp.beard_grooming_tips:
        _blank()
        _out("  Beard tips:")
        for tip in gp.beard_grooming_tips:
            _multiline_wrap(tip, indent="    • ")
    if gp.eyebrow_recommendation:
        _blank()
        _labeled_wrap("Brows",  gp.eyebrow_recommendation)
    if gp.skincare_categories_needed:
        _blank()
        _out("  Skin care needed  : " + "  ·  ".join(gp.skincare_categories_needed))
    if gp.recommended_grooming_change if hasattr(gp, "recommended_grooming_change") else False:
        _blank()
        _labeled_wrap("Change", rec.recommended_grooming_change)
    elif rec.recommended_grooming_change:
        _blank()
        _labeled_wrap("Overall change", rec.recommended_grooming_change)

    # ── Wardrobe gaps ─────────────────────────────────────────────────────────
    if rec.wardrobe_gaps:
        _blank()
        _out(_THIN)
        _out("WARDROBE GAPS  (ranked by impact)")
        _out(_THIN)
        for i, gap in enumerate(rec.wardrobe_gaps, 1):
            _multiline_wrap(f"{i}. {gap}", indent="   ",
                            subsequent_indent="      ")

    # ── Shopping priorities ───────────────────────────────────────────────────
    if rec.shopping_priorities:
        _blank()
        _out(_THIN)
        _out("SHOPPING PRIORITIES")
        _out(_THIN)
        for i, item in enumerate(rec.shopping_priorities, 1):
            _multiline_wrap(f"{i}. {item}", indent="   ",
                            subsequent_indent="      ")

    # ── Output paths ──────────────────────────────────────────────────────────
    _blank()
    _out(_THIN)
    if rec.caricature_image_path:
        _out(f"  Caricature  →  {rec.caricature_image_path}")
    if rec.annotated_output_path:
        _out(f"  Annotated   →  {rec.annotated_output_path}")
    if rec.analysis_json_path:
        _out(f"  JSON        →  {rec.analysis_json_path}")
    _out(_DIVIDER)


# ─────────────────────────────────────────────────────────────────────────────
def save_json(recommendation: StyleRecommendation, output_path: str) -> str:
    """Serialize the StyleRecommendation to a pretty-printed JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(recommendation.model_dump_json())
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    logger.info("Analysis JSON saved: %s", output_path)
    return output_path


def format_score_bar(score: int, label: str, width: int = 20) -> str:
    """Format a score as a simple ASCII bar."""
    filled = int((score / 10) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{label:<10} [{bar}]  {score}/10"


def format_profile_summary(recommendation: StyleRecommendation) -> str:
    """Return a compact one-line profile summary string."""
    up = recommendation.user_profile
    return (
        f"{_fmt_undertone(up.skin_undertone.value)} · "
        f"{_fmt_val(up.body_shape.value)} · "
        f"{up.height_estimate.capitalize()} · "
        f"{up.face_shape.value.capitalize()} face"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _out(text: str) -> None:
    print(text)


def _blank() -> None:
    print()


def _score_bar(label: str, score: int, bar_width: int = 20) -> str:
    filled = max(0, min(bar_width, int(score / 10 * bar_width)))
    bar    = "█" * filled + "░" * (bar_width - filled)
    return f"  {label:<10}  [{bar}]  {score}/10"


def _fmt_occasion(raw: str) -> str:
    return raw.replace("_", " ").title()


def _fmt_undertone(raw: str) -> str:
    return raw.replace("_", " ").title()


def _fmt_val(raw: str) -> str:
    return raw.replace("_", " ").title()


def _wrap_field(label: str, text: str) -> None:
    """Print a short labelled field, wrapping the value if needed."""
    prefix = f"  {label:<14}: "
    cont   = " " * len(prefix)
    lines  = textwrap.wrap(text or "—", width=_TEXT_WIDTH - len(prefix))
    if not lines:
        _out(prefix + "—")
        return
    _out(prefix + lines[0])
    for l in lines[1:]:
        _out(cont + l)


def _labeled_wrap(label: str, text: str) -> None:
    """Print a labelled block (Issue / Fix / Why) with full word-wrap.

    Format:
        Issue : First line of text here, continuing naturally
                across multiple lines with a clean indent so
                nothing is ever cut off.
    """
    if not text:
        return
    prefix   = f"  {label:<5} : "
    cont     = " " * len(prefix)
    wrap_w   = _TEXT_WIDTH
    lines    = textwrap.wrap(text.strip(), width=wrap_w)
    if not lines:
        return
    _out(prefix + lines[0])
    for l in lines[1:]:
        _out(cont + l)


def _multiline_wrap(text: str, indent: str = "  ",
                    subsequent_indent: str | None = None) -> None:
    """Wrap a paragraph with a given indent, preserving natural sentence flow."""
    if not text:
        return
    si = subsequent_indent if subsequent_indent is not None else indent + "  "
    lines = textwrap.wrap(
        text.strip(),
        width=_TEXT_WIDTH,
        initial_indent=indent,
        subsequent_indent=si,
    )
    for l in lines:
        _out(l)


def _chunk_list(items: list, per_line: int = 4) -> list[list]:
    """Split a list into sublists of at most per_line items."""
    return [items[i: i + per_line] for i in range(0, len(items), per_line)]
