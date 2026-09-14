"""Repo paths, .env loading, and brand constants.

The API key is read from the root `.env` and nowhere else. Never hard-code it.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# shared/englishing_kit/config.py -> shared/englishing_kit -> shared -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

SHARED_DIR = REPO_ROOT / "shared"
ASSETS_DIR = REPO_ROOT / "assets"
FONT_DIR = ASSETS_DIR / "fonts"
BRAND_DIR = ASSETS_DIR / "brand"
DOCS_DIR = REPO_ROOT / "docs"
ENV_FILE = REPO_ROOT / ".env"

load_dotenv(ENV_FILE)

BRAND = {
    "name": "Bidyazo.com",
    "parent_brand": "Englishing.app",
    "site_url": "https://bidyazo.com",
    "parent_site_url": "https://englishing.app",
    "ebook_selling_url": "https://bidyazo.com/ebook/bangladesh",
    "tagline": "Learn deeply. Remember longer.",
}


def require_openai_key() -> str:
    """Return OPENAI_API_KEY, or fail loudly with instructions.

    Only the image pipeline needs this. PDF and EPUB generation must work with no
    key at all, so that a future agent can rebuild every output offline.
    """
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key.startswith("sk-proj-xxxx"):
        raise RuntimeError(
            f"OPENAI_API_KEY is missing from {ENV_FILE}.\n"
            f"Fix: cp {REPO_ROOT / '.env.example'} {ENV_FILE} and paste the real key."
        )
    return key


def image_model() -> str:
    return os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")


def image_quality() -> str:
    """Default gpt-image quality. `low` on purpose — see .env.example."""
    return os.getenv("OPENAI_IMAGE_QUALITY", "low")


def max_workers() -> int:
    return int(os.getenv("IMAGEGEN_MAX_WORKERS", "6"))


def course_dir(country: str, language: str, slug: str) -> Path:
    return REPO_ROOT / country / language / slug
