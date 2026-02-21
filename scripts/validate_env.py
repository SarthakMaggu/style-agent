"""Validate required environment variables at startup.

Run directly to check your setup:
  python scripts/validate_env.py

Called automatically by main.py on every invocation.
"""

import os
import sys
from pathlib import Path


_REQUIRED = {
    "ANTHROPIC_API_KEY": "Required for outfit analysis and recommendations.",
    "REPLICATE_API_TOKEN": "Required for caricature generation (optional feature).",
}

_OPTIONAL = {
    "REPLICATE_API_TOKEN": True,  # caricature is optional; pipeline continues without it
}


def validate(raise_on_missing: bool = True) -> list[str]:
    """Check that required environment variables are set.

    Loads .env if present (via python-dotenv if available).

    Args:
        raise_on_missing: If True and any required vars are unset, raise
                          EnvironmentError. If False, print warnings only.

    Returns:
        List of missing required variable names.
    """
    _load_dotenv()

    missing = []
    for var, description in _REQUIRED.items():
        if not os.environ.get(var):
            if _OPTIONAL.get(var):
                print(f"  ⚠  {var} not set — {description}", file=sys.stderr)
            else:
                print(f"  ✗  {var} not set — {description}", file=sys.stderr)
                missing.append(var)

    if missing and raise_on_missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}\n"
            "Add them to your .env file and re-run."
        )

    return missing


def _load_dotenv() -> None:
    """Load .env file using python-dotenv if available."""
    env_path = Path(".env")
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # dotenv not installed — fall through; env vars may be set externally
        pass


if __name__ == "__main__":
    print("Validating environment…")
    missing = validate(raise_on_missing=False)
    if not missing:
        print("✓  All required environment variables are set.")
    else:
        print(f"\n✗  {len(missing)} required variable(s) missing. Add them to your .env file.")
        sys.exit(1)
