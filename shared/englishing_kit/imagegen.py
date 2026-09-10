"""Multi-threaded OpenAI image pipeline (gpt-image-2).

JSON in, images out. Every prompt is DECLARED IN JSON, never in Python — so the entire
art direction of a book is recoverable from the repo's JSON alone, forever, even if this
file is rewritten.

Two JSON files per course, and the distinction matters:

  bn-<slug>-images.json     THE DECLARATION. Committed. Every image's key, role, size,
                            quality, and prompt subject. This is the source of truth and
                            the thing you edit. Re-running the pipeline from this file
                            reproduces the whole book's art.

  assets/images.json        THE MANIFEST. Committed. What was ACTUALLY generated: the
                            final composed prompt (including the style and no-text
                            clauses), filename, path, model, size, quality, timestamp.
                            This is the recovery record.

Content JSON refers to an image by its `key`, never by a path.

Usage in a course's generate_images.py:

    from englishing_kit import imagegen
    specs = imagegen.specs_from_json(COURSE_DIR / "bn-<slug>-images.json")
    imagegen.generate_all(specs, course_dir=COURSE_DIR)
"""
from __future__ import annotations

import base64
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config

# ───────────────────────────────────────────────────────── the rules

# Appended to EVERY prompt. Not optional, not removable, not overridable.
NO_TEXT_CLAUSE = (
    "ABSOLUTELY NO TEXT of any kind in the image: no letters, no words, no numbers, "
    "no captions, no labels, no signage, no book titles, no handwriting, no logos, "
    "no watermarks, no QR codes, no UI text. Any writing on any surface must be "
    "omitted entirely rather than rendered as shapes or scribbles. Pure imagery only."
)

# The house look. Every book inherits it, so all 14 read as one series.
BRAND_STYLE = (
    "Premium, colourful, modern editorial illustration. Rich saturated palette built on "
    "warm orange (#f35816), deep navy (#0f172a), teal, royal blue, and magenta accents on a "
    "warm cream background. Clean vector-adjacent shapes, generous negative space, soft depth, "
    "confident and optimistic mood. Adult audience, not childish. Flat lighting, no photorealism"
)

# Covers and banners carry a title — but the title is drawn by the PDF/web layer in real
# embedded fonts, ON TOP of a text-free image. Titled artwork, zero typo risk. For that to
# look composed rather than pasted, the art must leave room for the type.
COVER_COMPOSITION = (
    "Composition: leave the upper third calm, uncluttered, and visually quiet — a soft, "
    "near-empty area of background where a title will later be placed. Concentrate all visual "
    "weight and detail in the lower two-thirds. Do not centre the subject vertically"
)
BANNER_COMPOSITION = (
    "Composition: a wide horizontal banner. Keep the left third calm, uncluttered, and nearly "
    "empty — a quiet area of background where a headline will later be placed. Concentrate the "
    "subject matter and visual weight in the right two-thirds. Balanced, editorial, spacious"
)

ROLE_COMPOSITION = {"cover": COVER_COMPOSITION, "banner": BANNER_COMPOSITION}


def composition_for(role: str, size: str) -> str | None:
    """Where the type will sit — decided by SHAPE, not just role.

    A `banner` is normally wide, so the headline sits in the clear LEFT third. But a
    book-ratio banner (portrait, for a website thumbnail) is shaped like a cover, so its
    title sits in the clear UPPER third. Getting this wrong is what sheared the subject's
    head off the first desktop cover.
    """
    if role not in ROLE_COMPOSITION:
        return None
    if size != "auto":
        w, h = (int(n) for n in size.lower().split("x"))
        if h > w:                       # portrait -> title goes on top
            return COVER_COMPOSITION
    return ROLE_COMPOSITION[role]

# ───────────────────────────────────────────────────────── sizes

# gpt-image-2 is flexible about size, but every dimension MUST divide by 8 — that is a hard
# constraint of the model's latent grid. `validate()` enforces it, so a bad size fails before
# it costs money. Prefer these named constants: they are common, safe, and also valid on
# gpt-image-1 if we ever have to fall back.
SQUARE = "1024x1024"       # spot art, exercise and dialogue illustrations
PORTRAIT = "1024x1536"     # covers, full-page lesson dividers
LANDSCAPE = "1536x1024"    # unit headers, wide hero art
BANNER = "1536x1024"       # the course banner (3:2). Widest size valid on BOTH image models.

# Valid on gpt-image-2 only. Use when a wider banner is genuinely wanted.
BANNER_WIDE = "1792x1024"  # 7:4

COMMON_SIZES = {SQUARE, PORTRAIT, LANDSCAPE, BANNER_WIDE, "auto"}
VALID_QUALITIES = {"low", "medium", "high", "auto"}

# Every course ships at least these two. Enforced by `check_required_roles()`.
REQUIRED_ROLES = ("cover", "banner")

# Where each role is written. Banners get their own folder because they are *website*
# assets — thumbnails and share cards — not illustrations buried among 30 lesson heroes.
ROLE_DIRS = {"banner": "assets/banner/art"}   # raw art; composed banners land in assets/banner/
DEFAULT_IMAGE_DIR = "assets/images"


def image_dir_for(course_dir: Path, role: str) -> Path:
    return course_dir / ROLE_DIRS.get(role, DEFAULT_IMAGE_DIR)


@dataclass
class ImageSpec:
    """One image. Normally built from JSON via `specs_from_json()`, not by hand."""
    key: str
    subject: str
    role: str = "spot"                 # cover | banner | unit-header | lesson-hero | spot
    style: str = BRAND_STYLE
    size: str = SQUARE
    quality: str | None = None         # None -> OPENAI_IMAGE_QUALITY from .env (which is `low`)
    filename: str | None = None
    context: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def resolved_filename(self) -> str:
        return self.filename or f"{self.key}.png"

    def resolved_quality(self) -> str:
        return self.quality or config.image_quality()

    def validate(self) -> None:
        if self.size != "auto":
            try:
                width, height = (int(n) for n in self.size.lower().split("x"))
            except ValueError as exc:
                raise ValueError(f"{self.key}: size {self.size!r} must look like '1024x1536'.") from exc
            # The hard one. Divisible by 8, both dimensions.
            if width % 8 or height % 8:
                raise ValueError(
                    f"{self.key}: size {self.size} is invalid — width and height must BOTH divide by 8. "
                    f"({width}%8={width % 8}, {height}%8={height % 8})"
                )
            if not (256 <= width <= 4096 and 256 <= height <= 4096):
                raise ValueError(f"{self.key}: size {self.size} is outside the sane 256–4096 range.")
            if self.size not in COMMON_SIZES:
                # Allowed, but say so — uncommon sizes cost more and render less predictably.
                _log(f"  note   {self.key}: {self.size} is not one of the common sizes {sorted(COMMON_SIZES)}")
        if self.resolved_quality() not in VALID_QUALITIES:
            raise ValueError(f"{self.key}: quality {self.resolved_quality()!r} not in {sorted(VALID_QUALITIES)}.")


def build_prompt(spec: ImageSpec) -> str:
    """Compose the final prompt: subject + style + role composition + the no-text clause.

    The no-text clause is welded on here, mechanically. Nobody writes it and nobody can
    forget it. A typo baked into an illustration in a language-learning book destroys trust
    in the whole product, so this is enforced in code rather than left to the prompt author.
    """
    parts = [spec.subject.strip().rstrip("."), spec.style.strip().rstrip(".")]
    composition = composition_for(spec.role, spec.size)
    if composition:
        parts.append(composition)
    parts.append(NO_TEXT_CLAUSE)
    return ". ".join(p for p in parts if p)


# ───────────────────────────────────────────────────────── JSON in

def specs_from_json(path: Path) -> list[ImageSpec]:
    """Load the image DECLARATION file. This is how prompts enter the pipeline.

    Expected shape — see docs/JSON-CONTENT-GUIDE.md §7:

        {
          "schema_version": "1.0",
          "course_slug": "english-foundations-a1",
          "default_quality": "low",
          "images": [
            {
              "key": "cover",
              "role": "cover",
              "size": "1024x1536",
              "subject": "an open notebook, floating study cards, a pencil, on a warm desk",
              "context": "Book cover. Title is overlaid by the PDF layer in real fonts."
            }
          ]
        }
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    default_quality = data.get("default_quality")
    default_style = data.get("default_style", BRAND_STYLE)

    specs: list[ImageSpec] = []
    for entry in data["images"]:
        specs.append(
            ImageSpec(
                key=entry["key"],
                subject=entry["subject"],
                role=entry.get("role", "spot"),
                style=entry.get("style", default_style),
                size=entry.get("size", SQUARE),
                quality=entry.get("quality", default_quality),
                filename=entry.get("filename"),
                context=entry.get("context", ""),
                extra=entry.get("extra", {}),
            )
        )

    check_required_roles(specs, source=str(path))
    keys = [s.key for s in specs]
    duplicates = {k for k in keys if keys.count(k) > 1}
    if duplicates:
        raise ValueError(f"{path}: duplicate image keys {sorted(duplicates)} — keys must be unique.")
    return specs


def check_required_roles(specs: list[ImageSpec], source: str = "") -> None:
    """Every course must ship a cover AND a banner."""
    roles = {s.role for s in specs}
    missing = [r for r in REQUIRED_ROLES if r not in roles]
    if missing:
        raise ValueError(
            f"{source}: every course must declare a {' and a '.join(REQUIRED_ROLES)} image. "
            f"Missing role(s): {missing}. Add an entry with \"role\": \"{missing[0]}\"."
        )


# ───────────────────────────────────────────────────────── generate

_print_lock = threading.Lock()


def _log(message: str) -> None:
    with _print_lock:
        print(message, flush=True)


def _generate_one(client: Any, spec: ImageSpec, course_dir: Path, force: bool) -> dict[str, Any]:
    spec.validate()
    path = image_dir_for(course_dir, spec.role) / spec.resolved_filename()
    path.parent.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(spec)

    record = {
        "key": spec.key,
        "role": spec.role,
        "filename": spec.resolved_filename(),
        "path": f"{image_dir_for(course_dir, spec.role).relative_to(course_dir)}/{spec.resolved_filename()}",
        "prompt": prompt,                 # the FULL composed prompt — the recovery record
        "subject": spec.subject,
        "style": spec.style,
        "size": spec.size,
        "quality": spec.resolved_quality(),
        "context": spec.context,
        "model": config.image_model(),
        "generated_at": None,
        **spec.extra,
    }

    if path.is_file() and not force:
        _log(f"  skip   {spec.key}  (on disk; --force to regenerate)")
        record["generated_at"] = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
        record["reused"] = True
        record["bytes"] = path.stat().st_size
        return record

    _log(f"  start  {spec.key}  [{spec.role}] {spec.size} q={spec.resolved_quality()}")
    response = client.images.generate(
        model=config.image_model(),
        prompt=prompt,
        size=spec.size,
        quality=spec.resolved_quality(),
        n=1,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(response.data[0].b64_json))

    record["generated_at"] = datetime.now(timezone.utc).isoformat()
    record["reused"] = False
    record["bytes"] = path.stat().st_size
    _log(f"  done   {spec.key}  ({record['bytes'] / 1024:.0f} KB)")
    return record


def generate_all(
    specs: list[ImageSpec],
    course_dir: Path,
    *,
    force: bool = False,
    max_workers: int | None = None,
) -> dict[str, Any]:
    """Generate every spec in parallel; write `assets/images.json`.

    Threads, not processes — this is entirely network-bound. Worker count comes from
    IMAGEGEN_MAX_WORKERS in .env. Raise it carefully: the image endpoint rate-limits per
    minute, and a 429 storm is slower than six threads.

    Images already on disk are skipped, so a re-run after a partial failure only retries
    what failed.
    """
    from openai import OpenAI  # lazy: a PDF-only build must not need the openai package

    check_required_roles(specs, source="generate_all()")
    for spec in specs:
        spec.validate()   # fail on ALL bad specs before spending a cent on the good ones

    client = OpenAI(api_key=config.require_openai_key())
    workers = max_workers or config.max_workers()

    _log(f"{len(specs)} images · model={config.image_model()} · {workers} threads")

    records: dict[str, dict[str, Any]] = {}
    failures: list[tuple[str, str]] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_generate_one, client, spec, course_dir, force): spec for spec in specs}
        for future in as_completed(futures):
            spec = futures[future]
            try:
                records[spec.key] = future.result()
            except Exception as exc:                      # noqa: BLE001
                failures.append((spec.key, str(exc)))
                _log(f"  FAIL   {spec.key}: {exc}")

    manifest = {
        "schema_version": "1.0",
        "purpose": (
            "Recovery record of every image actually generated for this course. Content JSON refers "
            "to an image by its `key`. The `prompt` field is the full composed prompt, so the art is "
            "reproducible from this file alone."
        ),
        "declared_in": f"bn-{course_dir.name}-images.json",
        "no_text_policy": NO_TEXT_CLAUSE,
        "model": config.image_model(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "image_count": len(records),
        "images": dict(sorted(records.items())),
    }
    manifest_path = course_dir / "assets" / "images.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"Wrote {manifest_path.name}  ({len(records)} images)")

    if failures:
        raise RuntimeError(
            "Some images failed:\n" + "\n".join(f"  {k}: {e}" for k, e in failures)
            + "\nRe-run to retry only the failures — images already on disk are skipped."
        )
    return manifest


# ───────────────────────────────────────────────────────── read back

def load_manifest(course_dir: Path) -> dict[str, Any]:
    path = course_dir / "assets" / "images.json"
    if not path.is_file():
        raise FileNotFoundError(f"No image manifest at {path}. Run this course's generate_images.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def image_path(course_dir: Path, key: str) -> Path:
    """Resolve a manifest key to a real file.

    Raises loudly if it is missing — a broken illustration must fail the build, never render
    as an empty box inside a PDF someone paid for.
    """
    manifest = load_manifest(course_dir)
    entry = manifest["images"].get(key)
    if not entry:
        available = ", ".join(sorted(manifest["images"])) or "(none)"
        raise KeyError(f"Image key {key!r} is not in the manifest. Available: {available}")
    path = course_dir / entry["path"]
    if not path.is_file():
        raise FileNotFoundError(f"Manifest lists {key!r} at {path}, but the file is not there.")
    return path
