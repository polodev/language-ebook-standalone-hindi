"""Offline PDF/EPUB fonts declared in assets/fonts/fonts.json.

PDF CSS embeds exact bundled binaries as data URIs to prevent asynchronous font
loading from producing invisible text. EPUB CSS uses archive-relative paths.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from .config import FONT_DIR

def load_font_config(font_dir: Path | None = None) -> dict:
    """Load the bundled font choices; no font family is hard-coded in Python."""
    directory = font_dir or FONT_DIR
    config = json.loads((directory / "fonts.json").read_text(encoding="utf-8"))
    for face in config["faces"]:
        filename = face["filename"]
        if Path(filename).name != filename:
            raise ValueError(f"Font filename must be local: {filename}")
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Missing bundled font: {path}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != face["sha256"]:
            raise ValueError(f"Bundled font hash mismatch: {path}")
    return config


def _faces(config: dict) -> list[tuple[str, str, int, str]]:
    return [(f["family"], f["filename"], f["weight"], f["style"])
            for f in config["faces"]]


def _stack(names: list[str]) -> str:
    generic = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"}
    return ", ".join(name if name in generic else "'" + name + "'" for name in names)


_CONFIG = load_font_config()
FACES = _faces(_CONFIG)
STACK = _stack(_CONFIG["stacks"]["default"])
STACK_BN = _stack(_CONFIG["stacks"]["bangla"])
STACK_TARGET = _stack(_CONFIG["stacks"]["target"])


def font_face_css(font_dir: Path | None = None, embed: bool = True) -> str:
    """@font-face rules for the PDF HTML.

    `embed=True` (the default) inlines each .ttf as a base64 `data:` URI, and this is
    NOT an optimisation — it is a correctness fix. Do not "improve" it back to file://.

    With `url(file://…)`, Chrome fetches the font asynchronously. `--print-to-pdf` does not
    reliably wait for that fetch, and `font-display: block` renders pending text as
    *nothing*. The result is a race: the same HTML sometimes produces a perfect book and
    sometimes a book with **invisible text** — Bengali first, since those faces load last.
    It was observed failing in the wild, and re-running appeared to "fix" it, which is
    exactly what makes it dangerous: a silently corrupt PDF that passes a casual glance.

    A data: URI has nothing to fetch. The font is part of the stylesheet, so it cannot lose
    a race with the printer. The generated HTML gets ~1.3 MB bigger; the PDF does not.
    """
    directory = font_dir or FONT_DIR
    rules = []
    for family, filename, weight, style in _faces(load_font_config(directory)):
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing font {path}. Fonts live in assets/fonts/ at the repo root; "
                f"consult the source and license manifest in fonts.json."
            )
        if embed:
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            src = f"url(data:font/ttf;base64,{b64}) format('truetype')"
        else:
            src = f"url('{path.resolve().as_uri()}') format('truetype')"
        rules.append(
            f"@font-face{{font-family:'{family}';src:{src};"
            f"font-weight:{weight};font-style:{style};font-display:block;}}"
        )
    return "\n".join(rules)


def epub_font_faces() -> str:
    """Same rules, but pointing at the relative paths used inside the EPUB zip."""
    rules = []
    for family, filename, weight, style in FACES:
        rules.append(
            f"@font-face{{font-family:'{family}';"
            f"src:url('fonts/{filename}') format('truetype');"
            f"font-weight:{weight};font-style:{style};}}"
        )
    return "\n".join(rules)


def epub_font_files(font_dir: Path | None = None) -> list[Path]:
    """The .ttf files an EPUB must carry so it renders offline on any e-reader."""
    directory = font_dir or FONT_DIR
    return [directory / filename for _, filename, _, _ in _faces(load_font_config(directory))]
