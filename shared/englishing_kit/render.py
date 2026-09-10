"""PDF rendering and EPUB packaging.

PDF: we shell out to headless Google Chrome (`--print-to-pdf`) rather than use a
Python PDF library. Chrome is the only engine that renders our CSS (grid, custom
fonts, print page-breaks, Bengali shaping) exactly as designed, and it is what the
reference project used. Chrome or Chromium must be installed.

EPUB: hand-built with the standard-library `zipfile`. An EPUB is a zip with a fixed
internal shape, and doing it directly avoids a dependency and gives us full control
over the embedded fonts.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from . import fonts
from .markdown_render import escape


@dataclass(frozen=True)
class Edition:
    """One output file. Courses declare these in their supplementary JSON."""
    name: str
    mode: str                      # desktop | mobile | compact_desktop | compact_mobile | tracker | tracker_color
    sample_lessons: int | None = None

    @property
    def is_sample(self) -> bool:
        return self.sample_lessons is not None


def editions_from(supplementary: dict) -> list[Edition]:
    return [
        Edition(name=str(e["name"]), mode=str(e["mode"]), sample_lessons=e.get("sample_lessons"))
        for e in supplementary.get("pdf_editions", [])
    ]


# ───────────────────────────────────────────────────────────────── PDF

def find_chrome(explicit: str | None = None) -> Path:
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return path
        raise FileNotFoundError(f"Chrome was not found at {path}")
    candidates = [
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    ]
    for command in ("google-chrome", "chromium", "chromium-browser"):
        resolved = shutil.which(command)
        if resolved:
            candidates.append(Path(resolved))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Google Chrome or Chromium is required to render PDFs. Install Chrome, or pass --chrome <path>."
    )


def embedded_fonts(pdf_path: Path) -> set[str]:
    """Font names embedded in a PDF, via `pdffonts` (poppler). Empty set if unavailable."""
    if not shutil.which("pdffonts"):
        return set()
    out = subprocess.run(["pdffonts", str(pdf_path)], capture_output=True, text=True, check=False)
    names = set()
    for line in out.stdout.splitlines()[2:]:
        if line.strip():
            # "AAAAAA+NotoSerifBengali-Regular" -> "NotoSerifBengali-Regular"
            names.add(line.split()[0].split("+")[-1])
    return names


def verify_fonts(pdf_path: Path, require: list[str]) -> None:
    """Fail loudly if an expected font is missing from the rendered PDF.

    This exists because of a real, observed failure. When fonts were fetched with
    `url(file://…)`, Chrome sometimes printed *before* they finished loading, and
    `font-display: block` painted the pending text as nothing — producing a PDF with
    **invisible Bengali**. It was nondeterministic: the same HTML would render fine on
    the next run. A book with missing text that looks fine to a spot-check is exactly the
    thing that must never reach a paying reader, so we assert instead of hoping.

    `fonts.font_face_css(embed=True)` removes the race. This check makes sure it stays gone.
    """
    found = embedded_fonts(pdf_path)
    if not found:
        return   # pdffonts not installed; nothing to assert against
    missing = [f for f in require if not any(f in name for name in found)]
    if missing:
        raise RuntimeError(
            f"{pdf_path.name}: expected font(s) {missing} are NOT embedded — text using them "
            f"will be INVISIBLE in the PDF.\nEmbedded: {sorted(found)}\n"
            f"Cause is almost always a font that failed to load before printing. "
            f"Ensure the HTML uses fonts.font_face_css(embed=True)."
        )


def assert_no_clipping(chrome: Path, html_path: Path, selector: str = ".sheet") -> None:
    """Fail the build if any FIXED-height page is overflowing its box.

    Fixed-height pages use `overflow:hidden`, which does not warn — it just silently
    guillotines whatever did not fit. That shipped a contents table cut off mid-title and
    a lesson list cut off mid-sentence, and neither was visible from the build log.

    Flowing pages cannot clip by construction, so only fixed sheets (cover, unit dividers)
    need this check. It measures scrollHeight vs clientHeight in the real browser.
    """
    probe = """<script>
    window.addEventListener('load', async () => {
      await document.fonts.ready;
      const bad = [];
      document.querySelectorAll('SELECTOR').forEach((el, i) => {
        const over = el.scrollHeight - el.clientHeight;
        if (over > 2) bad.push((el.className || 'sheet') + '#' + i + ' overflows by ' + over + 'px');
      });
      document.title = JSON.stringify(bad);
    });
    </script>""".replace("SELECTOR", selector)

    probe_path = html_path.with_suffix(".probe.html")
    probe_path.write_text(html_path.read_text(encoding="utf-8").replace("</body>", probe + "</body>"),
                          encoding="utf-8")
    try:
        out = subprocess.run(
            [str(chrome), "--headless=new", "--disable-gpu", "--no-sandbox",
             "--allow-file-access-from-files", "--virtual-time-budget=20000", "--dump-dom",
             probe_path.resolve().as_uri()],
            capture_output=True, text=True, check=False, timeout=300,
        ).stdout
        match = re.search(r"<title>(.*?)</title>", out, re.S)
        if not match:
            return
        import html as _html
        bad = json.loads(_html.unescape(match.group(1)) or "[]")
        if bad:
            raise RuntimeError(
                f"{html_path.name}: {len(bad)} fixed page(s) are CLIPPED — content is being cut off "
                f"and would ship invisible:\n  " + "\n  ".join(bad[:10])
            )
    finally:
        probe_path.unlink(missing_ok=True)


def render_pdf(
    chrome: Path,
    html_path: Path,
    pdf_path: Path,
    timeout: int = 900,
    require_fonts: list[str] | None = None,
) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--allow-file-access-from-files",   # images are file:// URIs (fonts are inlined)
        "--no-pdf-header-footer",
        "--disable-pdf-tagging",
        "--run-all-compositor-stages-before-draw",
        # THE flag that makes the render deterministic. Without it, Chrome prints before
        # the @font-face faces finish loading, and `font-display: block` paints pending
        # text as NOTHING — producing a PDF with invisible Bengali. Measured: 1/6 runs
        # embedded the Bengali font without this flag, 6/6 with it. Do not remove.
        "--virtual-time-budget=20000",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_path.resolve().as_uri(),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
    if completed.returncode != 0 or not pdf_path.is_file():
        raise RuntimeError(
            f"Chrome failed to render {html_path.name}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    if require_fonts:
        verify_fonts(pdf_path, require_fonts)


# ───────────────────────────────────────────────────────────────── EPUB

_CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""


def write_epub(
    epub_path: Path,
    *,
    title: str,
    author: str,
    language: str,
    chapters: list[tuple[str, str, str]],   # (filename, chapter_title, xhtml_body)
    stylesheet: str,
    cover_xhtml: str | None = None,
    cover_image: Path | None = None,
    extra_images: list[Path] | None = None,
    embed_fonts: bool = True,
    extra_fonts: list[Path] | None = None,
) -> None:
    """Write a valid EPUB 3.

    `chapters` is a list of (filename, title, body-xhtml). The body must be
    XHTML-clean — which it will be, because markdown_render emits xhtml output.
    """
    epub_path.parent.mkdir(parents=True, exist_ok=True)
    book_id = f"urn:uuid:{uuid4()}"

    manifest, spine = [], []
    if cover_xhtml:
        manifest.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
        spine.append('<itemref idref="cover"/>')
    if cover_image and cover_image.is_file():
        media = "image/png" if cover_image.suffix.lower() == ".png" else "image/jpeg"
        manifest.append(f'<item id="cover-image" href="images/{cover_image.name}" media-type="{media}" properties="cover-image"/>')

    epub_images: list[Path] = []
    seen_image_paths: set[Path] = set()
    if cover_image and cover_image.is_file():
        seen_image_paths.add(cover_image.resolve())
    for image in extra_images or []:
        if not image.is_file():
            continue
        resolved = image.resolve()
        if resolved in seen_image_paths:
            continue
        seen_image_paths.add(resolved)
        epub_images.append(image)
    for i, image in enumerate(epub_images):
        media = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
        manifest.append(f'<item id="image{i}" href="images/{escape(image.name)}" media-type="{media}"/>')

    for i, (filename, _title, _body) in enumerate(chapters):
        manifest.append(f'<item id="ch{i}" href="{filename}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="ch{i}"/>')

    manifest.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
    manifest.append('<item id="style" href="style.css" media-type="text/css"/>')

    font_files = fonts.epub_font_files() if embed_fonts else []
    for font in extra_fonts or []:
        if font.is_file() and font not in font_files:
            font_files.append(font)
    for i, font in enumerate(font_files):
        manifest.append(f'<item id="font{i}" href="fonts/{font.name}" media-type="font/ttf"/>')

    opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{book_id}</dc:identifier>
    <dc:title>{escape(title)}</dc:title>
    <dc:creator>{escape(author)}</dc:creator>
    <dc:language>{escape(language)}</dc:language>
    <meta property="dcterms:modified">2026-07-12T00:00:00Z</meta>
  </metadata>
  <manifest>{"".join(manifest)}</manifest>
  <spine>{"".join(spine)}</spine>
</package>"""

    nav_items = "".join(
        f'<li><a href="{filename}">{escape(chapter_title)}</a></li>'
        for filename, chapter_title, _ in chapters
    )
    nav = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{escape(language)}">
<head><title>{escape(title)}</title><link rel="stylesheet" href="style.css"/></head>
<body><nav epub:type="toc" id="toc"><h1>{escape(title)}</h1><ol>{nav_items}</ol></nav></body>
</html>"""

    with zipfile.ZipFile(epub_path, "w") as epub:
        # `mimetype` must be first and STORED, uncompressed. This is a hard spec
        # requirement; a deflated mimetype produces an EPUB that readers reject.
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        epub.writestr("META-INF/container.xml", _CONTAINER_XML)
        epub.writestr("OEBPS/content.opf", opf)
        epub.writestr("OEBPS/nav.xhtml", nav)
        epub.writestr("OEBPS/style.css", stylesheet)
        if cover_xhtml:
            epub.writestr("OEBPS/cover.xhtml", cover_xhtml)
        if cover_image and cover_image.is_file():
            epub.write(cover_image, f"OEBPS/images/{cover_image.name}")
        for image in epub_images:
            epub.write(image, f"OEBPS/images/{image.name}")
        for filename, _title, body in chapters:
            epub.writestr(f"OEBPS/{filename}", body)
        for font in font_files:
            if font.is_file():
                epub.write(font, f"OEBPS/fonts/{font.name}")


def xhtml_page(title: str, body: str, language: str = "bn") -> str:
    """Wrap a body fragment in an EPUB-valid XHTML document."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{escape(language)}">
<head><title>{escape(title)}</title><link rel="stylesheet" href="style.css"/></head>
<body>{body}</body>
</html>"""
