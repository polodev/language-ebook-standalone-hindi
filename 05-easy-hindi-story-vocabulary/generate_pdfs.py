#!/usr/bin/env python3
"""Build review PDFs and EPUBs from validated chapter JSON and local artwork for Book 5 (Story Vocabulary)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageOps

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent
sys.path.insert(0, str(ROOT / "shared"))
from englishing_kit import fonts, render
from englishing_kit.markdown_render import escape as esc, render_inline, render_block


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class BookRenderer:
    def __init__(self):
        assembled_path = BOOK / "generated/assembled.json"
        if not assembled_path.exists():
            subprocess.run(
                [sys.executable, str(ROOT / "scripts/manage.py"), "assemble", "--book", BOOK.name],
                cwd=ROOT,
                check=True,
            )
        data = load(assembled_path)
        self.book = load(BOOK / "book.json")
        self.chapters = data["chapters"]
        self.supp = load(BOOK / "supplementary.json")
        self.copy = self.supp["copy"]
        self.design = self.supp["design"]
        self.pub = self.supp["publication"]
        self.images = self.prepare_images()

    def prepare_images(self):
        manifest_path = BOOK / "assets/images.json"
        manifest = load(manifest_path).get("images", {}) if manifest_path.exists() else {}
        required = {"cover", "banner"} | {
            c.get("image_prompt", {}).get("key") or f"{c['chapter_id']}_story_hero_01"
            for c in self.chapters
        }
        directory = BOOK / "generated/publication-images"
        directory.mkdir(parents=True, exist_ok=True)
        result = {}
        for key in sorted(required):
            dest = directory / f"{key}.jpg"
            src = (
                (BOOK / manifest[key]["path"]).resolve()
                if (key in manifest and "path" in manifest[key])
                else (BOOK / f"assets/images/{key}.png")
            )
            if src.is_file():
                with Image.open(src) as image:
                    image = ImageOps.exif_transpose(image).convert("RGB")
                    limit = self.design["ui"]["image_width_px"]
                    image.thumbnail((limit, limit * 2), Image.Resampling.LANCZOS)
                    image.save(dest, "JPEG", quality=self.design["ui"]["image_jpeg_quality"], optimize=True)
            elif not dest.is_file():
                self.synthesize_image(key, dest)
            result[key] = dest
        return result

    def synthesize_image(self, key: str, dest: Path):
        palettes = self.design["palettes"]
        if key == "cover":
            w, h = 1024, 1536
            img = Image.new("RGB", (w, h), "#FAF8F5")
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, w, int(h * 0.35)], fill="#F4EFEA")
            draw.rectangle([int(w * 0.08), int(h * 0.36), int(w * 0.92), int(h * 0.365)], fill="#175B72")
            draw.arc([int(w * 0.15), int(h * 0.42), int(w * 0.85), int(h * 0.92)], 0, 180, fill="#175B72", width=8)
            draw.ellipse([int(w * 0.28), int(h * 0.52), int(w * 0.72), int(h * 0.78)], fill="#277657")
            draw.ellipse([int(w * 0.38), int(h * 0.58), int(w * 0.62), int(h * 0.72)], fill="#EAF5FA")
            draw.rounded_rectangle([int(w * 0.18), int(h * 0.82), int(w * 0.82), int(h * 0.94)], radius=24, fill="#97552A")
            draw.rounded_rectangle([int(w * 0.25), int(h * 0.85), int(w * 0.75), int(h * 0.91)], radius=16, fill="#FFF3E8")
        elif key == "banner":
            w, h = 1152, 768
            img = Image.new("RGB", (w, h), "#FAF8F5")
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, int(w * 0.35), h], fill="#F4EFEA")
            draw.rectangle([int(w * 0.35), 0, int(w * 0.355), h], fill="#175B72")
            draw.ellipse([int(w * 0.5), int(h * 0.15), int(w * 0.85), int(h * 0.65)], fill="#277657")
            draw.arc([int(w * 0.4), int(h * 0.3), int(w * 0.95), int(h * 0.85)], 180, 360, fill="#175B72", width=6)
            draw.rounded_rectangle([int(w * 0.55), int(h * 0.65), int(w * 0.9), int(h * 0.85)], radius=18, fill="#6A4388")
        else:
            w, h = 1152, 768
            ch_num = 0
            if key.startswith("ch"):
                try:
                    ch_num = int(key.split("_")[0][2:]) - 1
                except Exception:
                    pass
            pal = palettes[ch_num % len(palettes)]
            pal2 = palettes[(ch_num + 3) % len(palettes)]
            img = Image.new("RGB", (w, h), pal["background"])
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([int(w * 0.06), int(h * 0.08), int(w * 0.94), int(h * 0.92)], radius=20, outline=pal["ink"], width=4)
            draw.ellipse([int(w * 0.2), int(h * 0.18), int(w * 0.8), int(h * 0.82)], fill=pal2["background"], outline=pal2["ink"], width=3)
            draw.arc([int(w * 0.12), int(h * 0.15), int(w * 0.88), int(h * 0.85)], 0, 180, fill=pal["ink"], width=5)
            draw.rounded_rectangle([int(w * 0.28), int(h * 0.62), int(w * 0.72), int(h * 0.82)], radius=14, fill=pal["ink"])
        img.save(dest, "JPEG", quality=self.design["ui"]["image_jpeg_quality"], optimize=True)

    def blend_color(self, c1: str, c2: str, ratio: float) -> str:
        h1 = c1.lstrip("#")
        h2 = c2.lstrip("#")
        rgb1 = tuple(int(h1[i:i+2], 16) for i in (0, 2, 4))
        rgb2 = tuple(int(h2[i:i+2], 16) for i in (0, 2, 4))
        blended = tuple(rgb1[j] * (1 - ratio) + rgb2[j] * ratio for j in range(3))
        return "#" + "".join(f"{max(0, min(255, round(v))):02X}" for v in blended)

    def palette(self, number: int) -> str:
        p = self.design["palettes"][number % len(self.design["palettes"])]
        return f'--accent:{p["ink"]};--tint:{p["background"]}'

    def palette_row(self, group: int, is_odd: bool) -> tuple[str, str]:
        p = self.design["palettes"][group % len(self.design["palettes"])]
        bg = self.blend_color(p["background"], p["ink"], 0.065) if is_odd else p["background"]
        style = f'--accent:{p["ink"]};--tint:{bg};background-color:{bg}'
        return style, bg

    def picture(self, key: str, alt: str, epub: bool = False) -> str:
        path = "images/" + self.images[key].name if epub else self.images[key].resolve().as_uri()
        return f'<img class="reading-image" src="{esc(path)}" alt="{esc(alt)}" />'

    def cover(self, mode: str, epub: bool = False) -> str:
        note = self.copy.get("edition_note", "পর্যালোচনা ও সম্পাদনা সংস্করণ")
        return (
            f'<section class="cover {mode}">'
            f'{self.picture("cover", self.copy["title_bengali"], epub)}'
            f'<div class="cover-copy">'
            f'<div class="eyebrow">{esc(note)}</div>'
            f'<h1>{esc(self.copy["title"])}</h1>'
            f'<h2>{esc(self.copy["title_bengali"])}</h2>'
            f'<p>{esc(self.copy["subtitle"])}</p>'
            f'<p class="publisher">{esc(self.copy["publisher"])}</p>'
            f'</div></section>'
        )

    def contents(self, chapters: list[dict], epub: bool = False) -> str:
        prefix = "chapter-"
        items = "".join(
            f'<li><a href="{(prefix + c["chapter_id"] + ".xhtml" if epub else "#" + c["chapter_id"])}">'
            f'<span class="toc-num">{str(i+1).zfill(2)}.</span> {esc(c["title_bengali"])}</a></li>'
            for i, c in enumerate(chapters)
        )
        return (
            f'<section class="contents">'
            f'<h1>{esc(self.copy["contents"])}</h1>'
            f'<p>{esc(self.copy.get("review_note", ""))}</p>'
            f'<ol>{items}</ol>'
            f'</section>'
        )

    def tracker(self, color: bool) -> str:
        pages = []
        for start in range(0, len(self.chapters), 30):
            rows = []
            for i, c in enumerate(self.chapters[start : start + 30], start):
                style = self.palette(i // 5) if color else ""
                rows.append(
                    f'<tr style="{style}">'
                    f'<td>{str(i+1).zfill(2)}</td>'
                    f'<td>{esc(c["title_bengali"])}</td>'
                    + ("<td><span class='check-box'></span></td>" * 3)
                    + "</tr>"
                )
            pages.append(
                f'<section class="tracker">'
                f'<h1>{esc(self.copy["tracker"])}</h1>'
                f'<p>{esc(self.copy["title_bengali"])} · {esc(self.copy["tracker_subtitle"])}</p>'
                f'<table><thead><tr>'
                + "".join(f"<th>{esc(col)}</th>" for col in self.copy["tracker_columns"])
                + f'</tr></thead><tbody>{"".join(rows)}</tbody></table>'
                f"</section>"
            )
        return "".join(pages)

    def chapter(self, chapter: dict, number: int, epub: bool = False, mode: str = "desktop") -> str:
        c = chapter
        theme = esc(c.get("theme") or c.get("theme_bengali") or "")
        target_lang = esc(self.pub.get("target_language", "hi-IN"))
        target_key = "hindi" if "hi" in target_lang else "japanese"
        img_key = c.get("image_prompt", {}).get("key") or f"{c['chapter_id']}_story_hero_01"

        parts = [
            f'<article class="chapter" id="{esc(c["chapter_id"])}" style="{self.palette(number)}">',
            '<header class="chapter-head">',
            f'<div class="eyebrow">{esc(self.copy["chapter_label"])} {str(number+1).zfill(2)} · {theme}</div>',
            f'<h1>{esc(c["title_bengali"])}</h1>',
            f'<div class="chapter-native"><span class="native" lang="{target_lang}">{esc(c["title_target"])}</span> '
            f'<span class="cue">({esc(c["title_bangla_pronunciation"])} - {esc(c["title_romanization"])})</span></div>',
            '</header>',
            self.picture(img_key, c["title_bengali"], epub),
            f'<section class="story-section"><h2>{esc(self.copy["story_heading"])}</h2>',
            f'<div class="story-prose">{render_block(c["story_bengali_md"])}</div>',
            '</section>',
            f'<section class="vocab-section"><h2>{esc(self.copy["vocabulary_heading"])} ({len(c["vocabulary_table"])}টি শব্দ)</h2>'
        ]

        vocab = c.get("vocabulary_table", [])
        if mode == "desktop":
            parts.append('<table class="vocab-table"><colgroup><col class="col-vocab"/><col class="col-meaning"/></colgroup>')
            parts.append(f'<thead><tr><th scope="col">{esc(self.copy["vocabulary_column"])}</th><th scope="col">{esc(self.copy["meaning_column"])}</th></tr></thead><tbody>')
            for i, item in enumerate(vocab):
                target_word = item.get(target_key) or item.get("hindi") or item.get("japanese") or ""
                pron = esc(item.get("bangla_pronunciation", ""))
                rom = esc(item.get("romanization", ""))
                meaning = render_inline(item.get("meaning_bengali", ""))
                group = (number * 50 + i) // self.design.get("palette_rotation_every_items", 5)
                row_style, bg = self.palette_row(group, is_odd=(i % 2 == 1))
                parts.append(
                    f'<tr style="{row_style}">'
                    f'<td style="background-color:{bg}"><span class="item-badge">{str(i+1).zfill(2)}</span> '
                    f'<span class="native" lang="{target_lang}">{esc(target_word)}</span> '
                    f'<span class="pron-cue">({pron} - {rom})</span></td>'
                    f'<td style="background-color:{bg}"><span class="meaning-text">{meaning}</span></td></tr>'
                )
            parts.append('</tbody></table>')
        else:
            parts.append('<table class="vocab-table-mobile"><colgroup><col class="col-mob-vocab"/><col class="col-mob-meaning"/></colgroup>')
            parts.append(f'<thead><tr><th scope="col">{esc(self.copy["vocabulary_column"])}</th><th scope="col">{esc(self.copy["meaning_column"])}</th></tr></thead><tbody>')
            for i, item in enumerate(vocab):
                target_word = item.get(target_key) or item.get("hindi") or item.get("japanese") or ""
                pron = esc(item.get("bangla_pronunciation", ""))
                rom = esc(item.get("romanization", ""))
                meaning = render_inline(item.get("meaning_bengali", ""))
                group = (number * 50 + i) // self.design.get("palette_rotation_every_items", 5)
                row_style, bg = self.palette_row(group, is_odd=(i % 2 == 1))
                parts.append(
                    f'<tr style="{row_style}">'
                    f'<td style="background-color:{bg}"><span class="item-badge">{str(i+1).zfill(2)}</span> '
                    f'<span class="native" lang="{target_lang}">{esc(target_word)}</span> '
                    f'<span class="pron-cue">({pron} - {rom})</span></td>'
                    f'<td style="background-color:{bg}"><div class="meaning-text">{meaning}</div></td></tr>'
                )
            parts.append('</tbody></table>')

        parts.append('</section>')
        parts.append('</article>')
        return "".join(parts)

    def css(self, mode: str, epub: bool = False) -> str:
        ui = self.design["ui"]
        mobile = "mobile" in mode
        tracker = mode.startswith("tracker")
        size = (
            self.design["tracker_page_mm"]
            if tracker
            else self.design["mobile_page_mm"]
            if mobile
            else self.design["desktop_page_mm"]
        )
        margin = ui["mobile_margin_mm"] if mobile else ui["desktop_margin_mm"]
        pt = ui["mobile_font_pt"] if mobile else ui["desktop_font_pt"]
        face = fonts.epub_font_faces() if epub else fonts.font_face_css()
        page = (
            ""
            if epub
            else f"""@page {{
                size: {size[0]}mm {size[1]}mm;
                margin: {margin}mm;
                @bottom-left {{
                    content: "{self.copy['publisher']}";
                    font-family: {fonts.STACK};
                    font-size: 8pt;
                    color: {ui['muted']};
                }}
                @bottom-right {{
                    content: counter(page);
                    font-family: {fonts.STACK};
                    font-size: 8pt;
                }}
            }}"""
        )
        css = (
            face
            + page
            + f"""
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; padding: 0; }}
        body {{
            font-family: {fonts.STACK};
            font-size: {pt}pt;
            line-height: 1.55;
            color: {ui['text']};
            background: {ui['paper']};
            font-synthesis: none;
        }}
        a {{ color: inherit; text-decoration: none; }}
        h1, h2, h3, p {{ margin: 0 0 3mm; }}
        h1 {{ font-size: 22pt; line-height: 1.35; }}
        h2 {{
            font-size: 16pt;
            color: var(--accent, {ui['cover_ink']});
            border-bottom: 1px solid {ui['rule']};
            padding-bottom: 2mm;
            margin-top: 5mm;
            break-after: avoid;
        }}
        h3 {{ font-size: 13pt; margin-top: 4mm; break-after: avoid; }}
        p {{ orphans: 2; widows: 2; }}
        .native {{
            font-family: '{self.design['target_font']}', {fonts.STACK};
            font-weight: 700;
            font-size: 1.15em;
        }}
        .cue {{
            color: {ui['muted']};
            font-size: 0.88em;
            font-weight: 400;
        }}
        .chapter {{ break-before: page; }}
        .chapter-head {{
            break-inside: avoid;
            border-top: 2.5mm solid var(--accent);
            padding-top: 5mm;
            margin-bottom: 4mm;
        }}
        .eyebrow {{
            font-size: 10pt;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: {ui['muted']};
            margin-bottom: 2mm;
        }}
        .chapter-native {{
            font-size: 13pt;
            margin: 2mm 0;
            line-height: 1.4;
        }}
        .reading-image {{
            display: block;
            width: 100%;
            height: auto;
            max-height: 90mm;
            object-fit: contain;
            margin: 3mm auto 5mm;
            break-inside: avoid;
        }}
        .story-section {{
            margin: 4mm 0 6mm;
            break-inside: auto;
        }}
        .story-prose {{
            line-height: 1.95;
            font-size: 1.05em;
            margin: 2mm 0 4mm;
        }}
        .story-prose p {{
            margin-bottom: 3.5mm;
            text-align: justify;
        }}
        .story-prose strong {{
            font-weight: 700;
            color: var(--accent);
            background: rgba(0, 0, 0, 0.04);
            padding: 0.5px 3px;
            border-radius: 3px;
        }}
        .vocab-section {{
            margin-top: 6mm;
            break-inside: auto;
        }}
        .vocab-table {{
            table-layout: fixed;
            width: 100%;
            margin: 3mm 0 6mm;
            font-size: 9.8pt;
            border-collapse: collapse;
        }}
        .vocab-table .col-vocab {{ width: 55%; }}
        .vocab-table .col-meaning {{ width: 45%; }}
        .vocab-table th {{
            background: {ui['rule']};
            padding: 2.5mm 3mm;
            font-size: 9.5pt;
            font-weight: 700;
            border: 1px solid {ui['rule']};
            text-align: left;
        }}
        .vocab-table td {{
            padding: 2.2mm 3mm;
            border: 1px solid {ui['rule']};
            background: var(--tint, #FFFFFF);
            vertical-align: middle;
            word-break: break-word;
        }}
        .vocab-table tr {{ break-inside: avoid; }}
        .vocab-table-mobile {{
            table-layout: fixed;
            width: 100%;
            margin: 2mm 0 4mm;
            font-size: 8.5pt;
            border-collapse: collapse;
        }}
        .vocab-table-mobile .col-mob-vocab {{ width: 55%; }}
        .vocab-table-mobile .col-mob-meaning {{ width: 45%; }}
        .vocab-table-mobile th {{
            background: {ui['rule']};
            padding: 1.5mm;
            font-size: 8.5pt;
            font-weight: 700;
            border: 1px solid {ui['rule']};
            text-align: left;
        }}
        .vocab-table-mobile td {{
            padding: 1.8mm 1.5mm;
            border: 1px solid {ui['rule']};
            background: var(--tint, #FFFFFF);
            vertical-align: top;
            word-break: break-word;
        }}
        .vocab-table-mobile tr {{ break-inside: avoid; }}
        .item-badge, .item-num {{
            display: inline-block;
            font-family: 'Miriam Libre', sans-serif;
            font-size: 7.5pt;
            font-weight: 700;
            line-height: 1.15;
            color: var(--accent);
            background: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 3px;
            padding: 0.5px 3.5px;
            margin-right: 1.5mm;
            vertical-align: 0.5px;
            letter-spacing: 0.02em;
        }}
        .pron-cue {{
            color: {ui['muted']};
            font-size: 0.88em;
            white-space: normal;
        }}
        .meaning-text {{
            font-weight: 600;
            color: {ui['text']};
            line-height: 1.35;
        }}
        .cover {{
            position: relative;
            break-after: page;
            height: {size[1] - 2 * margin - 2}mm;
            overflow: hidden;
            background: var(--tint, {ui['paper']});
        }}
        .cover > .reading-image {{
            position: absolute;
            right: 0;
            top: 0;
            width: 54%;
            height: 100%;
            max-height: none;
            object-fit: contain;
            margin: 0;
        }}
        .cover-copy {{
            position: absolute;
            top: 22%;
            left: 2%;
            width: 43%;
            color: {ui['cover_ink']};
        }}
        .cover h1 {{
            font-size: 26pt;
            line-height: 1.15;
            margin: 3mm 0;
        }}
        .cover h2 {{
            border: 0;
            font-size: 19pt;
            margin: 2mm 0;
        }}
        .cover .publisher {{
            margin-top: 5mm;
            font-size: 10pt;
        }}
        .contents {{
            break-after: page;
        }}
        .contents ol {{
            list-style: none;
            column-count: 2;
            column-gap: 8mm;
            margin: 4mm 0;
            padding-left: 0;
            font-size: 9.5pt;
        }}
        .contents li {{
            list-style: none;
            break-inside: avoid;
            margin-bottom: 2mm;
            padding-left: 0;
        }}
        .toc-num {{
            font-family: 'Miriam Libre';
            font-weight: 700;
            color: {ui['cover_ink']};
            margin-right: 1mm;
        }}
        .tracker {{ break-after: page; }}
        .tracker:last-child {{ break-after: auto; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 10pt;
        }}
        th {{
            text-align: left;
            padding: 2mm;
            border-bottom: 1px solid {ui['rule']};
        }}
        td {{
            padding: 1.5mm 2mm;
            border-bottom: 1px solid {ui['rule']};
            background: var(--tint, {ui['paper']});
        }}
        td:first-child {{ width: 13mm; }}
        td:nth-child(n+3) {{
            text-align: center;
            width: 20mm;
        }}
        tr {{ break-inside: avoid; }}
        .check-box {{
            display: inline-block;
            width: 3mm;
            height: 3mm;
            border: 1px solid {ui['muted']};
        }}
        """
        )
        if not mobile and size[0] < size[1] and not epub:
            css += """
            .cover > .reading-image { width: 100%; height: 100%; object-fit: cover; }
            .cover-copy { left: 5%; top: 3%; width: 90%; }
            .cover h1 { font-size: 24pt; line-height: 1.15; margin: 3mm 0; }
            .cover h2 { font-size: 18pt; margin: 2mm 0; }
            .cover .publisher { margin-top: 3mm; }
            .cover .eyebrow { margin-bottom: 2mm; }
            """
        if tracker:
            css += f"""
            table {{ font-size: {ui['tracker_font_pt']}pt; }}
            td {{ padding: {ui['tracker_cell_padding_mm']}mm 2mm; }}
            """
        if mobile:
            css += f"""
            .contents ol {{ column-count: 1; list-style: none; padding-left: 0; }}
            .contents li {{ list-style: none; padding-left: 0; }}
            .cover > .reading-image {{ width: 100%; height: 100%; object-fit: cover; }}
            .cover-copy {{ left: 5%; top: 3%; width: 90%; }}
            .cover h1 {{ font-size: 18pt; line-height: 1.15; margin: 2mm 0; }}
            .cover h2 {{ font-size: 13pt; margin: 1mm 0; }}
            .cover-copy p {{ font-size: 8.5pt; margin: 1mm 0; }}
            .cover .publisher {{ margin-top: 2mm; font-size: 8pt; }}
            .cover .eyebrow {{ font-size: 8pt; margin-bottom: 1mm; }}
            .reading-image {{ max-height: 60mm; }}
            h1 {{ font-size: 18pt; }}
            h2 {{ font-size: 13pt; }}
            .chapter-native {{ font-size: 11pt; }}
            .story-prose {{ font-size: 9.5pt; line-height: 1.8; }}
            .item-badge, .item-num {{
                font-size: 6.8pt;
                padding: 0.4px 3px;
                margin-right: 1mm;
                border-radius: 2.5px;
            }}
            """
        if epub:
            css += """
            .cover { height: auto; min-height: 0; overflow: visible; page-break-after: always; }
            .cover > .reading-image { position: static; width: 100%; height: auto; max-height: none; }
            .cover-copy { position: static; width: auto; margin: 1em; }
            .cover h1 { font-size: 2em; }
            .cover h2 { font-size: 1.4em; }
            .reading-image { max-height: none; }
            .contents ol { column-count: 1; list-style: none; padding-left: 0; }
            .contents li { list-style: none; padding-left: 0; }
            .chapter { page-break-before: always; }
            """
        return css

    def build(self, only: str | None = None):
        output = BOOK / "output"
        output.mkdir(exist_ok=True)
        generated = BOOK / "generated/publication"
        generated.mkdir(exist_ok=True)
        outputs = self.book["expected_output_files"]
        selected = [f for f in outputs if not only or f == only or Path(f).stem == only]
        if not selected:
            raise ValueError("Unknown output selection: " + str(only))
        chrome = render.find_chrome()
        target_lang = self.pub.get("target_language", "hi-IN")
        is_hindi = "hi" in target_lang

        for filename in selected:
            path = output / filename
            mobile = "mobile" in filename
            sample = "sample" in filename
            tracker = "tracker" in filename
            chapters = self.chapters[:2] if sample else self.chapters

            if filename.endswith(".pdf"):
                if tracker:
                    mode = "tracker_color" if "color" in filename else "tracker"
                    body = self.tracker("color" in filename)
                    required = ["MiriamLibre", "NotoSerifBengali"]
                else:
                    mode = "mobile" if mobile else "desktop"
                    body = (
                        self.cover(mode)
                        + self.contents(chapters)
                        + "".join(self.chapter(c, i, mode=mode) for i, c in enumerate(chapters))
                    )
                    required = (
                        ["MiriamLibre", "NotoSerifBengali", "NotoSansDevanagari"]
                        if is_hindi
                        else ["MiriamLibre", "NotoSerifBengali"]
                    )

                html = generated / (path.stem + ".html")
                html.write_text(
                    '<!doctype html><html lang="bn"><head><meta charset="utf-8"/><title>'
                    + esc(self.copy["title"])
                    + "</title><style>"
                    + self.css(mode)
                    + "</style></head><body>"
                    + body
                    + "</body></html>",
                    encoding="utf-8",
                )
                if not tracker:
                    cover_html = generated / (path.stem + ".cover-probe.html")
                    cover_html.write_text(
                        '<!doctype html><html lang="bn"><head><meta charset="utf-8"/><title>'
                        + esc(self.copy["title"])
                        + "</title><style>"
                        + self.css(mode)
                        + "</style></head><body>"
                        + self.cover(mode)
                        + "</body></html>",
                        encoding="utf-8",
                    )
                    try:
                        render.assert_no_clipping(chrome, cover_html, selector=".cover")
                    finally:
                        cover_html.unlink(missing_ok=True)
                render.render_pdf(chrome, html, path, require_fonts=required)
            else:
                mode = "mobile" if mobile else "desktop"
                entries = [
                    (
                        "contents.xhtml",
                        self.copy["contents"],
                        render.xhtml_page(self.copy["contents"], self.contents(chapters, True), "bn"),
                    )
                ]
                entries += [
                    (
                        "chapter-" + c["chapter_id"] + ".xhtml",
                        c["title_bengali"],
                        render.xhtml_page(c["title_bengali"], self.chapter(c, i, True, mode=mode), "bn"),
                    )
                    for i, c in enumerate(chapters)
                ]
                render.write_epub(
                    path,
                    title=self.copy["title_bengali"],
                    author=self.pub["publisher_name"],
                    language=self.pub["language"],
                    chapters=entries,
                    stylesheet=self.css(mode, True),
                    cover_xhtml=render.xhtml_page(self.copy["title_bengali"], self.cover(mode, True), "bn"),
                    cover_image=self.images["cover"],
                    extra_images=[v for k, v in self.images.items() if k not in ("cover", "banner")],
                    identifier=self.pub["identifier"] + ":" + mode,
                    modified=self.pub["modified"],
                )
            print(f"Built {path.name} ({path.stat().st_size/1024/1024:.2f} MiB)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only")
    args = parser.parse_args()
    BookRenderer().build(args.only)
