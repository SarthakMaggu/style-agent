"""StyleAgent CLI entry point.

Usage:
  python src/main.py onboard                             # First time setup
  python src/main.py onboard --refresh-profile           # Rebuild profile
  python src/main.py analyze --image ./photo.jpg         # Analyze outfit
  python src/main.py analyze --image ./photo.jpg --occasion wedding_guest_indian
  python src/main.py analyze --image ./photo.jpg --style cartoon
  python src/main.py profile --show                      # View your profile
  python src/main.py history --last 5                    # View past analyses
"""

import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: ensure project root is on sys.path so `from src.x` always works,
# regardless of how this file is invoked (python src/main.py vs python -m src.main)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Load .env FIRST — before any src imports that read os.environ.
# override=True ensures .env values win even if the var is already set to ""
# in the shell environment (e.g. from a stale export).
try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env", override=True)
except ImportError:
    pass  # python-dotenv not installed; keys must be set in shell environment

import click

# ---------------------------------------------------------------------------
# Logging setup — info to stdout, errors to stderr
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("style-agent")

# ---------------------------------------------------------------------------
# Photo request copy (per CLAUDE.md)
# ---------------------------------------------------------------------------

_PHOTO_PROMPT = """\
Let's build your style profile. I need 5 photos — grab them from
your camera roll or take them now. Here's what works best:

Photo 1 — A close-up of your face, looking straight at the camera.
           Natural light, indoors is fine.

Photo 2 — Your face from the side (either side).

Photo 3 — Full body, front-facing. Stand naturally, whatever you'd
           normally wear heading out — jeans, kurta, anything real.

Photo 4 — Full body, side profile. Same everyday look.

Photo 5 — One of your recent outfits you actually went somewhere in.
           Office, dinner, casual day out — just a real one.

Once I have these I'll know enough about you to give useful feedback
every single time.
"""

_VALID_OCCASIONS = [
    "indian_formal",
    "indian_casual",
    "ethnic_fusion",
    "western_business_formal",
    "western_business_casual",
    "western_streetwear",
    "smart_casual",
    "party",
    "wedding_guest_indian",
    "festival",
    "travel",
    "gym",
    "beach",
    "lounge",
]

_VALID_STYLES = ["caricature", "cartoon", "pixar"]


# ---------------------------------------------------------------------------
# Main group
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """StyleAgent — your AI personal stylist."""
    _validate_env()


# ---------------------------------------------------------------------------
# onboard
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--refresh-profile", is_flag=True, default=False,
              help="Rebuild your profile even if one already exists.")
@click.option("--save-photos", is_flag=True, default=False,
              help="Keep copies of your onboarding photos.")
@click.option("--folder", default="", type=click.Path(),
              help="Path to a folder of photos (any type, 3–30+). Auto-categorises all images.")
@click.option("--name", default="", help="Your preferred name (used in personalised recommendations).")
@click.option("--age-group", default="", type=click.Choice(["", "18-25", "26-35", "36-45", "45+"]),
              help="Your age group (optional).")
@click.option("--lifestyle", default="",
              type=click.Choice(["", "corporate", "creative", "entrepreneur", "student", "freelance"]),
              help="Your lifestyle (optional).")
@click.option("--budget", default="",
              type=click.Choice(["", "high_street", "mid_range", "designer", "luxury"]),
              help="Your budget tier (optional).")
def onboard(
    refresh_profile: bool,
    save_photos: bool,
    folder: str,
    name: str,
    age_group: str,
    lifestyle: str,
    budget: str,
) -> None:
    """Build your permanent style profile from photos.

    Two modes:

    \b
    SEQUENTIAL (default): Provide 3–5 photos in order.
      python src/main.py onboard

    \b
    FOLDER MODE: Drop any photos in a folder — StyleAgent auto-categorises them.
      python src/main.py onboard --folder ./my_photos/
      python src/main.py onboard --folder ./my_photos/ --name "Arjun" --age-group 26-35
    """
    from src.storage.profile_store import profile_exists
    from src.agents.style_agent import run_onboarding, StyleAgentError

    if profile_exists() and not refresh_profile:
        click.echo(
            "\nYou already have a profile. Run `python src/main.py profile --show` to view it.\n"
            "To rebuild it, pass --refresh-profile.\n"
        )
        return

    # ── Folder mode ──────────────────────────────────────────────────────────
    if folder:
        from pathlib import Path as _Path
        if not _Path(folder).is_dir():
            click.echo(f"\n✗  Folder not found: {folder}", err=True)
            sys.exit(1)

        # Count images in folder for user feedback
        _exts = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
        img_count = sum(
            1 for p in _Path(folder).iterdir()
            if p.is_file() and p.suffix.lower() in _exts
        )
        click.echo(
            f"\nFound {img_count} image(s) in {folder}.\n"
            "Categorising and analysing — this may take a few minutes for large folders…\n"
        )

        try:
            profile = run_onboarding(
                photo_paths=[],
                refresh=refresh_profile,
                folder_mode=True,
                folder_path=folder,
                preferred_name=name,
                lifestyle=lifestyle,
                age_group=age_group,
                budget_tier=budget,
            )
            click.echo("\n✓  Profile built from folder successfully.\n")
            _print_profile(profile)
        except StyleAgentError as exc:
            click.echo(f"\n✗  {exc}", err=True)
            sys.exit(1)
        except Exception as exc:
            logger.exception("Folder onboarding failed")
            click.echo(f"\n✗  Unexpected error: {exc}", err=True)
            sys.exit(1)
        return

    # ── Sequential mode (existing behaviour) ─────────────────────────────────
    click.echo(_PHOTO_PROMPT)

    photo_paths: list[str] = []
    for i in range(1, 6):
        while True:
            path = click.prompt(f"Photo {i} path (or press Enter to skip)").strip()
            if not path:
                if i <= 3:
                    click.echo(f"  ✗  Photo {i} is required (minimum 3 photos needed).")
                    continue
                break  # optional photo skipped
            from pathlib import Path as _Path
            if not _Path(path).exists():
                click.echo(f"  ✗  File not found: {path}")
                continue
            photo_paths.append(path)
            click.echo(f"  ✓  Photo {i} added.")
            break

    if len(photo_paths) < 3:
        click.echo("\n✗  Not enough photos — need at least 3. Run onboard again.", err=True)
        sys.exit(1)

    click.echo(f"\nAnalysing {len(photo_paths)} photo(s) — this takes about 30 seconds…")

    try:
        profile = run_onboarding(photo_paths, refresh=refresh_profile, save_photos=save_photos)
        click.echo("\n✓  Profile built successfully.\n")
        _print_profile(profile)
    except StyleAgentError as exc:
        click.echo(f"\n✗  {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Onboarding failed")
        click.echo(f"\n✗  Unexpected error: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--image", required=True, type=click.Path(exists=True),
              help="Path to the outfit photo to analyse.")
@click.option("--occasion", default="", type=click.Choice(_VALID_OCCASIONS + [""]),
              help="Target occasion (auto-detected if not supplied).")
@click.option("--style", default="caricature", type=click.Choice(_VALID_STYLES),
              help="Caricature render style.")
@click.option("--output-dir", default="./outputs",
              help="Directory for output files (default: ./outputs).")
@click.option("--no-api", is_flag=True, default=False,
              help="Run rule-based only — no API calls.")
@click.option("--save-photos", is_flag=True, default=False,
              help="Save the input photo alongside analysis outputs.")
@click.option("--cartoon-input", is_flag=True, default=False,
              help="Treat the input image as an already-styled cartoon — annotate directly, skip Replicate.")
@click.option("--layout", default="editorial", type=click.Choice(["editorial", "sidebar"]),
              help="Annotated image layout: editorial (dark magazine, default) or sidebar (classic).")
@click.option("--hires", is_flag=True, default=False,
              help="Export annotated image at 2× resolution.")
@click.option("--export-pdf", is_flag=True, default=False,
              help="Also export a PDF alongside the annotated JPEG.")
def analyze(
    image: str,
    occasion: str,
    style: str,
    output_dir: str,
    no_api: bool,
    save_photos: bool,
    cartoon_input: bool,
    layout: str,
    hires: bool,
    export_pdf: bool,
) -> None:
    """Analyse an outfit photo and print a full style report."""
    from src.agents.style_agent import run_analysis, StyleAgentError
    from src.output.formatter import print_recommendation

    click.echo("\nAnalysing your outfit…\n")

    try:
        result = run_analysis(
            image_path=image,
            occasion=occasion,
            caricature_style=style,
            output_dir=output_dir,
            use_api=not no_api,
            save_photos=save_photos,
            cartoon_input=cartoon_input,
            layout_mode=layout,
            scale_factor=2.0 if hires else 1.0,
            export_pdf=export_pdf,
        )

        for warning in result.warnings:
            click.echo(f"  ⚠  {warning}")

        print_recommendation(result.recommendation, occasion=occasion)
        click.echo(f"\nCompleted in {result.elapsed_seconds:.1f}s")

    except StyleAgentError as exc:
        click.echo(f"\n✗  {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Analysis failed")
        click.echo(f"\n✗  Unexpected error: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--show", is_flag=True, default=True, help="Print your current profile.")
def profile(show: bool) -> None:
    """View your stored style profile."""
    from src.storage.profile_store import load_profile, ProfileNotFoundError

    try:
        up = load_profile()
        _print_profile(up)
    except ProfileNotFoundError:
        click.echo(
            "\n✗  No profile found. Run `python src/main.py onboard` first.\n", err=True
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# history
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--last", default=5, show_default=True,
              help="Number of past analyses to show.")
def history(last: int) -> None:
    """View past style analyses."""
    from src.storage.history_store import load_history

    entries = load_history(last_n=last)
    if not entries:
        click.echo("\nNo analysis history found. Run `python src/main.py analyze` first.\n")
        return

    click.echo(f"\n{'─' * 60}")
    click.echo(f"  LAST {len(entries)} ANALYSES")
    click.echo(f"{'─' * 60}")
    for i, entry in enumerate(reversed(entries), 1):
        ts = entry.get("timestamp", "")[:19].replace("T", " ")
        occasion = entry.get("occasion", "unknown").replace("_", " ").title()
        score = entry.get("overall_style_score", "?")
        remarks = entry.get("remark_count", 0)
        critical = entry.get("critical_count", 0)
        click.echo(
            f"  {i}. [{ts}]  {occasion}  —  Score {score}/10  "
            f"({remarks} remarks, {critical} critical)"
        )
    click.echo(f"{'─' * 60}\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_env() -> None:
    """Warn if required API keys are missing (non-fatal)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        click.echo(
            "  ⚠  ANTHROPIC_API_KEY not set. Add it to your .env file.",
            err=True,
        )


def _print_profile(profile: "UserProfile") -> None:  # type: ignore[name-defined]
    """Print a formatted profile summary to terminal."""
    up = profile
    w = 60
    click.echo("═" * w)
    click.echo("  YOUR STYLE PROFILE")
    click.echo("═" * w)
    click.echo(f"  Undertone   : {up.skin_undertone.value.replace('_', ' ').title()}")
    click.echo(f"  Skin depth  : {up.skin_tone_depth.capitalize()}")
    click.echo(f"  Body shape  : {up.body_shape.value.replace('_', ' ').title()}")
    click.echo(f"  Build       : {up.build.capitalize()}, {up.shoulder_width} shoulders")
    click.echo(f"  Height      : {up.height_estimate.capitalize()}")
    click.echo(f"  Face shape  : {up.face_shape.value.capitalize()}")
    click.echo(f"  Hair        : {up.haircut_length.capitalize()} {up.current_haircut_style}, "
               f"{up.hair_texture}, {up.hair_density} density")
    click.echo(f"  Beard       : {up.beard_style.capitalize()}, {up.beard_grooming_quality}")
    if up.confidence_scores:
        avg = sum(up.confidence_scores.values()) / len(up.confidence_scores)
        click.echo(f"  Confidence  : {avg:.0%} average across {len(up.confidence_scores)} attributes")
    click.echo(f"  Photos used : {up.photos_used}")
    click.echo(f"  Version     : {up.profile_version}")
    click.echo("═" * w)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    cli()
