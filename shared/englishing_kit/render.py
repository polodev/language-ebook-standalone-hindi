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
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import PurePosixPath
from xml.etree import ElementTree as ET

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
    chapters: list[tuple[str, str, str]],
    stylesheet: str,
    cover_xhtml: str | None = None,
    cover_image: Path | None = None,
    extra_images: list[Path] | None = None,
    embed_fonts: bool = True,
    extra_fonts: list[Path] | None = None,
    identifier: str | None = None,
    modified: str | None = None,
) -> None:
    """Package EPUB 3, failing on missing assets and ambiguous archive paths.

    Pass an identifier and UTC modified timestamp from publication JSON for
    reproducible releases. With identical inputs these produce identical bytes.
    XHTML documents are complete documents, not body fragments.
    """
    if not chapters:
        raise ValueError("An EPUB requires at least one chapter")
    if not language.strip():
        raise ValueError("An EPUB requires a language")
    timestamp = modified or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    if date.strftime("%Y-%m-%dT%H:%M:%SZ") != timestamp:
        raise ValueError("modified must use YYYY-MM-DDTHH:MM:SSZ")
    if not 1980 <= date.year <= 2107:
        raise ValueError("modified year must fit ZIP timestamps (1980–2107)")
    book_id = identifier or "urn:sha256:" + sha256(
        json.dumps([title, author, language, chapters], ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    files: dict[str, bytes] = {}
    manifest, spine = [], []

    def add(name: str, data: bytes | str) -> None:
        path = PurePosixPath(name)
        if (path.is_absolute() or ".." in path.parts or "\\" in name or
                str(path) != name or name in files):
            raise ValueError(f"Unsafe or duplicate EPUB path: {name}")
        files[name] = data.encode("utf-8") if isinstance(data, str) else data

    def item(item_id: str, name: str, media: str, properties: str = "") -> None:
        extra = f' properties="{escape(properties)}"' if properties else ""
        manifest.append(f'<item id="{item_id}" href="{escape(name)}" media-type="{media}"{extra}/>')

    def xhtml(name: str, document: str) -> None:
        root = ET.fromstring(document)
        if root.tag != "{http://www.w3.org/1999/xhtml}html":
            raise ValueError(f"{name}: expected XHTML html root")
        if not root.get("lang") and not root.get("{http://www.w3.org/XML/1998/namespace}lang"):
            raise ValueError(f"{name}: language is missing")
        add("OEBPS/" + name, document)

    if cover_xhtml:
        xhtml("cover.xhtml", cover_xhtml)
        item("cover", "cover.xhtml", "application/xhtml+xml")
        spine.append('<itemref idref="cover"/>')
    seen: set[Path] = set()
    image_media = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".gif": "image/gif"}
    image_files = ([cover_image] if cover_image is not None else []) + list(extra_images or [])
    for index, image in enumerate(image_files):
        image = Path(image)
        if not image.is_file():
            raise FileNotFoundError(f"Missing EPUB image: {image}")
        if image.resolve() in seen:
            continue
        seen.add(image.resolve())
        if image.suffix.lower() not in image_media:
            raise ValueError(f"Unsupported EPUB image: {image}")
        name = "images/" + image.name
        add("OEBPS/" + name, image.read_bytes())
        is_cover = cover_image is not None and image.resolve() == Path(cover_image).resolve()
        item("cover-image" if is_cover else f"image{index}", name,
             image_media[image.suffix.lower()], "cover-image" if is_cover else "")

    for index, (filename, _title, body) in enumerate(chapters):
        if PurePosixPath(filename).parent != PurePosixPath(".") or not filename.endswith(".xhtml"):
            raise ValueError(f"Chapter filename must be a plain .xhtml name: {filename}")
        xhtml(filename, body)
        item(f"ch{index}", filename, "application/xhtml+xml")
        spine.append(f'<itemref idref="ch{index}"/>')

    font_files = list(fonts.epub_font_files()) if embed_fonts else []
    font_files.extend(extra_fonts or [])
    seen_fonts: set[Path] = set()
    font_media = {".ttf": "font/ttf", ".otf": "font/otf", ".woff": "font/woff", ".woff2": "font/woff2"}
    for index, font in enumerate(font_files):
        font = Path(font)
        if not font.is_file():
            raise FileNotFoundError(f"Missing EPUB font: {font}")
        if font.resolve() in seen_fonts:
            continue
        seen_fonts.add(font.resolve())
        if font.suffix.lower() not in font_media:
            raise ValueError(f"Unsupported EPUB font: {font}")
        name = "fonts/" + font.name
        add("OEBPS/" + name, font.read_bytes())
        item(f"font{index}", name, font_media[font.suffix.lower()])

    item("nav", "nav.xhtml", "application/xhtml+xml", "nav")
    item("style", "style.css", "text/css")
    opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="book-id">{escape(book_id)}</dc:identifier>
<dc:title>{escape(title)}</dc:title><dc:creator>{escape(author)}</dc:creator>
<dc:language>{escape(language)}</dc:language>
<meta property="dcterms:modified">{timestamp}</meta>
</metadata><manifest>{"".join(manifest)}</manifest><spine>{"".join(spine)}</spine></package>'''
    nav_items = "".join(f'<li><a href="{escape(name)}">{escape(label)}</a></li>' for name, label, _ in chapters)
    nav = f'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{escape(language)}" xml:lang="{escape(language)}">
<head><title>{escape(title)}</title><link rel="stylesheet" href="style.css"/></head>
<body><nav epub:type="toc" id="toc"><h1>{escape(title)}</h1><ol>{nav_items}</ol></nav></body></html>'''
    add("mimetype", "application/epub+zip")
    add("META-INF/container.xml", _CONTAINER_XML)
    add("OEBPS/content.opf", opf)
    xhtml("nav.xhtml", nav)
    add("OEBPS/style.css", stylesheet)
    epub_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = epub_path.with_suffix(epub_path.suffix + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w") as epub:
            for name in ["mimetype"] + sorted(n for n in files if n != "mimetype"):
                info = zipfile.ZipInfo(name, date.timetuple()[:6])
                info.compress_type = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                epub.writestr(info, files[name])
        temporary.replace(epub_path)
    finally:
        temporary.unlink(missing_ok=True)


def xhtml_page(title: str, body: str, language: str = "bn") -> str:
    """Wrap a body fragment in an EPUB-valid XHTML document."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{escape(language)}">
<head><title>{escape(title)}</title><link rel="stylesheet" href="style.css"/></head>
<body>{body}</body>
</html>"""
