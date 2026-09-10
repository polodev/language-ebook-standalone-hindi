"""The embedded font stack, as @font-face CSS.

Font policy, inherited from the reference project and non-negotiable:

    English text   Miriam Libre
    Bengali text   Noto Serif Bengali
    IPA text       Noto Serif Bengali

Miriam Libre carries no Bengali glyphs, so it goes FIRST in every font stack.
Pure-English fragments ("Day 01") render in Miriam Libre; Bengali characters fall
through to Noto Serif Bengali. That fall-through is the whole trick, and it is why
mixed Bangla/English sentences render correctly without any markup around them.

Fonts are embedded from assets/fonts/ as file:// URIs. Never link Google Fonts —
a PDF render must not depend on the network.
"""
from __future__ import annotations

import base64
from pathlib import Path

from .config import FONT_DIR

FACES = [
    ("Miriam Libre", "MiriamLibre-Regular.ttf", 400, "normal"),
    ("Miriam Libre", "MiriamLibre-Bold.ttf", 700, "normal"),
    ("Noto Serif Bengali", "NotoSerifBengali-Regular.ttf", 400, "normal"),
    ("Noto Serif Bengali", "NotoSerifBengali-Medium.ttf", 500, "normal"),
    ("Noto Serif Bengali", "NotoSerifBengali-SemiBold.ttf", 600, "normal"),
    ("Noto Serif Bengali", "NotoSerifBengali-Bold.ttf", 700, "normal"),
]

# English first, Bengali as fall-through. Use this everywhere.
STACK = "'Miriam Libre', 'Noto Serif Bengali', sans-serif"
# For a Bangla-dominant block where Latin fragments are incidental.
STACK_BN = "'Noto Serif Bengali', 'Miriam Libre', serif"


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
    for family, filename, weight, style in FACES:
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing font {path}. Fonts live in assets/fonts/ at the repo root; "
                f"they were copied from the reference project."
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
    return [directory / filename for _, filename, _, _ in FACES]
