#!/usr/bin/env python3
"""Build review PDFs and EPUBs from validated chapter JSON and local artwork for Book 4."""
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


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class BookRenderer:
    def __init__(self):
        assembled_path = BOOK / "generated/assembled.json"
        if not assembled_path.exists():
            subprocess.run([sys.executable, str(ROOT / "scripts/manage.py"), "assemble", "--book", BOOK.name], cwd=ROOT, check=True)
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
        required = {"cover", "banner"} | {i["key"] for c in self.chapters for i in c.get("image_prompts", [])}
        directory = BOOK / "generated/publication-images"
        directory.mkdir(parents=True, exist_ok=True)
        result = {}
        for key in sorted(required):
            dest = directory / f"{key}.jpg"
            src = (BOOK / manifest[key]["path"]).resolve() if (key in manifest and "path" in manifest[key]) else (BOOK / f"assets/images/{key}.png")
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

    def synthesize_image(self, key, dest):
        palettes = self.design["palettes"]
        if key == "cover":
            w, h = 1024, 1536
            img = Image.new("RGB", (w, h), "#FAF8F5")
            draw = ImageDraw.Draw(img)
            # Upper third calm with delicate tint
            draw.rectangle([0, 0, w, int(h * 0.35)], fill="#F4EFEA")
            draw.rectangle([int(w * 0.08), int(h * 0.36), int(w * 0.92), int(h * 0.365)], fill="#175B72")
            # Lower two-thirds: balanced abstract editorial shapes
            draw.arc([int(w * 0.15), int(h * 0.42), int(w * 0.85), int(h * 0.92)], 0, 180, fill="#175B72", width=8)
            draw.ellipse([int(w * 0.28), int(h * 0.52), int(w * 0.72), int(h * 0.78)], fill="#277657")
            draw.ellipse([int(w * 0.38), int(h * 0.58), int(w * 0.62), int(h * 0.72)], fill="#EAF5FA")
            draw.rounded_rectangle([int(w * 0.18), int(h * 0.82), int(w * 0.82), int(h * 0.94)], radius=24, fill="#97552A")
            draw.rounded_rectangle([int(w * 0.25), int(h * 0.85), int(w * 0.75), int(h * 0.91)], radius=16, fill="#FFF3E8")
        elif key == "banner":
            w, h = 1152, 768
            img = Image.new("RGB", (w, h), "#FAF8F5")
            draw = ImageDraw.Draw(img)
            # Left third calm
            draw.rectangle([0, 0, int(w * 0.35), h], fill="#F4EFEA")
            draw.rectangle([int(w * 0.35), 0, int(w * 0.355), h], fill="#175B72")
            # Right two-thirds
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
            if "bridge" in key:
                draw.rounded_rectangle([int(w * 0.08), int(h * 0.12), int(w * 0.92), int(h * 0.88)], radius=20, outline=pal["ink"], width=4)
                draw.arc([int(w * 0.15), int(h * 0.2), int(w * 0.85), int(h * 0.85)], 180, 360, fill=pal["ink"], width=6)
                draw.ellipse([int(w * 0.35), int(h * 0.35), int(w * 0.65), int(h * 0.75)], fill=pal2["background"], outline=pal2["ink"], width=4)
            else:
                draw.rounded_rectangle([int(w * 0.08), int(h * 0.12), int(w * 0.92), int(h * 0.88)], radius=20, outline=pal2["ink"], width=4)
                draw.ellipse([int(w * 0.25), int(h * 0.2), int(w * 0.75), int(h * 0.8)], fill=pal["ink"])
                draw.ellipse([int(w * 0.35), int(h * 0.32), int(w * 0.65), int(h * 0.68)], fill=pal["background"])
                draw.arc([int(w * 0.18), int(h * 0.15), int(w * 0.82), int(h * 0.85)], 0, 180, fill=pal2["ink"], width=5)
        img.save(dest, "JPEG", quality=self.design["ui"]["image_jpeg_quality"], optimize=True)

    def words(self, items):
        return "".join(
            '<span class="word-cue"><span class="native" lang="'+esc(self.pub["target_language"])+'">'+esc(w["target"])+
            '</span> <span class="cue" lang="bn">('+esc(w["bangla_pronunciation"])+', '+esc(w["romanization"])+')</span></span>'+esc(w["separator_after"])
            for w in items
        )

    def annotated(self, item, model=False):
        prefix = "model_" if model else ""
        return '<div class="annotated">'+self.words(item[prefix+"word_pronunciations"])+"</div>"

    def ordered_entry(self, item):
        body = (self.row('meaning', item['meaning_bengali_md'], True)
                + self.row('pronunciation', item['bangla_pronunciation'])
                + self.row('romanization', item['romanization'])
                + '<div class="label">'+esc(self.copy['word_breakdown'])+'</div>'
                + self.annotated(item))
        if item.get('example_target'):
            body += ('<div class="example-box">'
                     + '<div class="label">'+esc(self.copy.get('example', 'উদাহরণ বাক্য'))+': </div>'
                     + self.row('meaning', item['example_meaning_bengali_md'], True)
                     + self.row('pronunciation', item['example_bangla_pronunciation'])
                     + self.row('romanization', item['example_romanization'])
                     + '<div class="annotated">'+self.words(item['example_word_pronunciations'])+'</div>'
                     + '</div>')
        return body

    def row(self, label, value, markdown=False):
        return '<div class="detail"><span class="label">'+esc(self.copy[label])+': </span>'+(render_inline(value) if markdown else esc(value))+'</div>'

    def palette(self, number):
        p = self.design["palettes"][number % len(self.design["palettes"])]
        return f'--accent:{p["ink"]};--tint:{p["background"]}'

    def card(self, body, number=0):
        return '<div class="card" style="'+self.palette(number)+'">'+body+'</div>'

    def picture(self, key, alt, epub=False):
        path = 'images/'+self.images[key].name if epub else self.images[key].resolve().as_uri()
        return '<img class="reading-image" src="'+esc(path)+'" alt="'+esc(alt)+'" />'

    def cover(self, mode, epub=False):
        note = self.copy.get('edition_note', 'সম্পূর্ণ শব্দভাণ্ডার সংস্করণ')
        return '<section class="cover '+mode+'">'+self.picture('cover', self.copy['title_bengali'], epub)+ '<div class="cover-copy"><div class="eyebrow">'+esc(note)+'</div><h1>'+esc(self.copy['title'])+'</h1><h2>'+esc(self.copy['title_bengali'])+'</h2><p>'+esc(self.copy['subtitle'])+'</p><p class="publisher">'+esc(self.copy['publisher'])+'</p></div></section>'

    def contents(self, chapters, epub=False):
        prefix = 'chapter-'
        items = ''.join('<li><a href="'+(prefix+c['chapter_id']+'.xhtml' if epub else '#'+c['chapter_id'])+'">'+esc(c['title_bengali'])+'</a></li>' for c in chapters)
        return '<section class="contents"><h1>'+esc(self.copy['contents'])+'</h1><p>'+esc(self.copy['review_note'])+'</p><ol>'+items+'</ol></section>'

    def chapter(self, chapter, number, epub=False, mode="mobile"):
        c = chapter
        parts = [
            '<article class="chapter" id="'+esc(c['chapter_id'])+'" style="'+self.palette(number)+'">',
            '<header class="chapter-head"><div class="eyebrow">'+esc(self.copy['chapter_label'])+' '+str(number+1).zfill(3)+'</div>',
            '<h1>'+esc(c['title_bengali'])+'</h1>',
            '<div class="chapter-native">'+self.words(c['title_word_pronunciations'])+'</div>',
            self.row('pronunciation', c['title_bangla_pronunciation']),
            self.row('romanization', c['title_romanization']),
            render_block(c['goal_bengali_md']),
            '</header>'
        ]
        for section in self.design['reading_layout']['section_order']:
            parts.append('<section class="lesson-section"><h2>'+esc(self.copy[section])+'</h2>')
            if section == 'sentences' and mode == 'desktop':
                headings = self.copy['sentence_table_columns']
                parts.append('<table class="learning-table"><colgroup><col class="index-col"/><col class="meaning-col"/><col class="target-col"/><col class="pron-col"/></colgroup><thead><tr>'+''.join('<th scope="col">'+esc(h)+'</th>' for h in headings)+'</tr></thead><tbody>')
                for i, item in enumerate(c['sentences']):
                    target = self.annotated(item)
                    hindi = self.row('pronunciation', item['bangla_pronunciation'])+self.row('romanization', item['romanization'])
                    parts.append('<tr style="'+self.palette((number*30+i)//self.design['palette_rotation_every_items'])+'"><td>'+str(i+1).zfill(2)+'</td><td>'+render_inline(item['meaning_bengali_md'])+'</td><td>'+hindi+'</td><td>'+target+'</td></tr>')
                parts.append('</tbody></table>')
            elif section == 'vocabulary' and mode == 'desktop':
                headings = self.copy['vocabulary_table_columns']
                parts.append('<table class="learning-table vocab-3col"><colgroup><col class="vocab-bangla-col"/><col class="vocab-hindi-col"/><col class="vocab-sentence-col"/></colgroup><thead><tr>'+''.join('<th scope="col">'+esc(h)+'</th>' for h in headings)+'</tr></thead><tbody>')
                for i, item in enumerate(c['vocabulary']):
                    bangla = f'<div class="item-number">{str(i+1).zfill(2)}</div><div class="meaning-text"><strong>{render_inline(item["meaning_bengali_md"])}</strong></div>'
                    hindi = (f'<div class="native vocab-target">{esc(item["target"])}</div>'
                             + f'<div class="pron-rom">{esc(item["bangla_pronunciation"])} ({esc(item["romanization"])})</div>')
                    sentence = ''
                    if item.get('example_target'):
                        sentence = (f'<div class="native sentence-target">{esc(item["example_target"])}</div>'
                                    + f'<div class="pron-rom">{esc(item["example_bangla_pronunciation"])} ({esc(item["example_romanization"])})</div>')
                    parts.append('<tr style="'+self.palette((number*30+i)//self.design['palette_rotation_every_items'])+'"><td>'+bangla+'</td><td>'+hindi+'</td><td>'+sentence+'</td></tr>')
                parts.append('</tbody></table>')
            elif section == 'sentences':
                cards = []
                for i, s in enumerate(c['sentences']):
                    body = '<div class="item-number">'+str(i+1).zfill(2)+'</div>'+self.ordered_entry(s)
                    cards.append(self.card(body, (number*30+i)//self.design['palette_rotation_every_items']))
                parts.append('<div class="cards">'+''.join(cards)+'</div>')
            elif section == 'vocabulary':
                cards = []
                for i, v in enumerate(c['vocabulary']):
                    body = (f'<div class="item-number">{str(i+1).zfill(2)}</div>'
                            + f'<div class="meaning-text"><strong>{render_inline(v["meaning_bengali_md"])}</strong></div>'
                            + f'<div class="native vocab-target" style="margin-top:1.5mm;">{esc(v["target"])}</div>'
                            + f'<div class="pron-rom">{esc(v["bangla_pronunciation"])} ({esc(v["romanization"])})</div>')
                    cards.append(self.card(body, (number*30+i)//self.design['palette_rotation_every_items']))
                parts.append('<div class="cards vocabulary">'+''.join(cards)+'</div>')
            elif section in ('bridge_reading', 'target_reading'):
                r = c[section]
                key = next(x['key'] for x in c['image_prompts'] if x['reading'] == section)
                parts.append('<h3>'+esc(r['title_bengali'])+'</h3>'+self.picture(key, r['scene_summary'], epub))
                if section == 'bridge_reading':
                    prose = ''.join(esc(s['text']) if s['kind'] == 'bangla' else self.words(s['word_pronunciations']) for s in r['segments'])
                    parts.append('<div class="bridge prose">'+prose+'</div>')
                else:
                    parts.append('<div class="complete-target-reading" lang="bn"><p>'+esc(r['bangla_pronunciation'])+'</p><p class="cue">'+esc(r['romanization'])+'</p></div>')
                    parts.append('<div class="reading-meaning"><h3>'+esc(self.copy['reading_meaning'])+'</h3>'+render_block(r['meaning_bengali_md'])+'</div>')
                    parts.append('<h3>'+esc(self.copy['reading_breakdown'])+'</h3><div class="pure-reading">'+''.join('<div class="reading-line">'+self.annotated(line)+'<div class="detail">'+esc(line['bangla_pronunciation'])+', '+esc(line['romanization'])+'</div></div>' for line in r['lines'])+'</div>')
            elif section == 'script_and_numbers':
                parts.append('<h3>'+esc(self.copy['script'])+'</h3><div class="cards">')
                for s in c['script_practice']:
                    body = '<div class="script-symbol"><span class="native" lang="'+esc(self.pub['target_language'])+'">'+esc(s['target'])+'</span> <span class="cue">('+esc(s['bangla_pronunciation'])+', '+esc(s['romanization'])+')</span></div><div class="label">'+esc(self.copy['script_modes'][s['mode']])+'</div>'+render_block(s['explanation_bengali_md'])+render_block(s['practice_bengali_md'])
                    parts.append(self.card(body, number))
                parts.append('</div>')
                if c.get('number_practice'):
                    parts.append('<h3>'+esc(self.copy['numbers'])+'</h3><div class="cards">')
                    for n in c['number_practice']:
                        parts.append(self.card('<div class="number-symbol">'+esc(n['display'])+'</div>'+self.annotated(n)+self.row('pronunciation',n['bangla_pronunciation'])+self.row('romanization',n['romanization'])+self.row('meaning',n['meaning_bengali_md'],True), number))
                    parts.append('</div>')
            parts.append('</section>')
        if c.get('additional_practice'):
            parts.append('<section class="lesson-section"><h2>'+esc(self.copy['additional_practice'])+'</h2>')
            for item in c['additional_practice']:
                parts.append(render_block(item['explanation_bengali_md']))
                for prefix in ['base', 'expanded', 'polished']:
                    parts.append('<h3>'+esc(self.copy[prefix])+'</h3>'+self.words(item[prefix+'_word_pronunciations'])+self.row('pronunciation',item[prefix+'_bangla_pronunciation'])+self.row('romanization',item[prefix+'_romanization']))
            parts.append('</section>')
        parts.append('</article>')
        return ''.join(parts)

    def tracker(self, color):
        pages = []
        for start in range(0, len(self.chapters), 30):
            rows = []
            for i, c in enumerate(self.chapters[start:start+30], start):
                style = self.palette(i // 5) if color else ''
                rows.append('<tr style="'+style+'"><td>'+str(i+1).zfill(3)+'</td><td>'+esc(c['title_bengali'])+'</td>'+('<td><span class="check-box"></span></td>'*3)+'</tr>')
            pages.append('<section class="tracker"><h1>'+esc(self.copy['tracker'])+'</h1><p>'+esc(self.copy['title_bengali'])+' · '+esc(self.copy['tracker_subtitle'])+'</p><table><thead><tr>'+''.join('<th>'+esc(s)+'</th>' for s in self.copy['tracker_columns'])+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></section>')
        return ''.join(pages)

    def css(self, mode, epub=False):
        ui = self.design['ui']
        mobile = 'mobile' in mode
        tracker = mode.startswith('tracker')
        size = self.design['tracker_page_mm'] if tracker else self.design['mobile_page_mm'] if mobile else self.design['desktop_page_mm']
        margin = ui['mobile_margin_mm'] if mobile else ui['desktop_margin_mm']
        pt = ui['mobile_font_pt'] if mobile else ui['desktop_font_pt']
        face = fonts.epub_font_faces() if epub else fonts.font_face_css()
        page = '' if epub else f'''@page {{size:{size[0]}mm {size[1]}mm;margin:{margin}mm;@bottom-left{{content:"{self.copy['publisher']}";font-family:{fonts.STACK};font-size:8pt;color:{ui['muted']};}}@bottom-right{{content:counter(page);font-family:{fonts.STACK};font-size:8pt;}}}}'''
        css = face + page + f'''
        *{{box-sizing:border-box}}html,body{{margin:0;padding:0}}body{{font-family:{fonts.STACK};font-size:{pt}pt;line-height:1.55;color:{ui['text']};background:{ui['paper']};font-synthesis:none}}a{{color:inherit;text-decoration:none}}h1,h2,h3,p{{margin:0 0 3mm}}h1{{font-size:22pt;line-height:1.4}}h2{{font-size:17pt;color:var(--accent,{ui['cover_ink']});border-bottom:1px solid {ui['rule']};padding-bottom:2mm;margin-top:5mm;break-after:avoid}}h3{{font-size:13pt;margin-top:4mm;break-after:avoid}}p{{orphans:2;widows:2}}.native{{font-family:'{self.design['target_font']}',{fonts.STACK};font-weight:700;font-size:1.16em}}.cue{{color:{ui['muted']};font-size:.85em;font-weight:400}}.word-cue{{display:inline-block;white-space:nowrap;max-width:100%}}.annotated{{line-height:1.9;margin-bottom:2mm}}.detail{{font-size:.93em;margin:1mm 0;overflow-wrap:anywhere}}.label{{font-size:.82em;color:{ui['muted']};font-weight:700}}.item-number{{font-family:'Miriam Libre';font-size:10pt;color:var(--accent);font-weight:700;margin-bottom:1mm}}.badge{{display:inline-block;font-size:0.75em;padding:1px 5px;background:var(--accent);color:#ffffff;border-radius:3px;margin-left:4px;vertical-align:middle;font-weight:600}}.cards{{display:grid;grid-template-columns:1fr 1fr;gap:3mm;align-items:start}}.card{{break-inside:avoid;border-left:1mm solid var(--accent);border-radius:{ui['card_radius_mm']}mm;background:var(--tint);padding:3mm 4mm;min-width:0}}.card p{{margin:1mm 0}}.example-box{{margin-top:2mm;padding:2mm;background:rgba(255,255,255,0.7);border-radius:2mm;font-size:0.92em;border-left:2px solid var(--accent)}}.chapter{{break-before:page}}.chapter-head{{break-inside:avoid;border-top:2mm solid var(--accent);padding-top:5mm;margin-bottom:4mm}}.eyebrow{{font-size:10pt;font-weight:700;letter-spacing:.05em;color:{ui['muted']};margin-bottom:3mm}}.chapter-native{{font-size:13pt;margin:2mm 0}}.reading-image{{display:block;width:100%;height:auto;max-height:92mm;object-fit:contain;margin:3mm auto 5mm;break-inside:avoid}}.prose{{line-height:2.05;margin:2mm 0 6mm}}.bridge .native{{font-weight:700}}.reading-line{{padding:2mm 0;border-bottom:1px solid {ui['rule']};break-inside:avoid}}.script-symbol{{font-size:22pt;line-height:1.7}}.number-symbol{{font-size:20pt;font-weight:700}}.cover{{position:relative;break-after:page;height:{size[1]-2*margin-2}mm;overflow:hidden;background:var(--tint,{ui['paper']})}}.cover>.reading-image{{position:absolute;right:0;top:0;width:54%;height:100%;max-height:none;object-fit:contain;margin:0}}.cover-copy{{position:absolute;top:22%;left:2%;width:43%;color:{ui['cover_ink']}}}.cover h1{{font-size:28pt;line-height:1.15;margin:3mm 0}}.cover h2{{border:0;font-size:20pt;margin:2mm 0}}.cover .publisher{{margin-top:5mm;font-size:10pt}}.contents{{break-after:page}}.contents ol{{column-count:2;column-gap:10mm;margin:4mm 0;padding-left:8mm}}.contents li{{break-inside:avoid;margin-bottom:2mm;padding-left:1mm}}.tracker{{break-after:page}}.tracker:last-child{{break-after:auto}}table{{border-collapse:collapse;width:100%;font-size:10pt}}th{{text-align:left;padding:2mm;border-bottom:1px solid {ui['rule']}}}td{{padding:1.5mm 2mm;border-bottom:1px solid {ui['rule']};background:var(--tint,{ui['paper']})}}td:first-child{{width:13mm}}td:nth-child(n+3){{text-align:center;width:20mm}}tr{{break-inside:avoid}}.check-box{{display:inline-block;width:3mm;height:3mm;border:1px solid {ui['muted']}}}
        '''
        if not mobile:
            css += f""".learning-table{{table-layout:fixed;font-size:10pt;margin:3mm 0 5mm}}.learning-table .index-col{{width:6%}}.learning-table .target-col{{width:28%}}.learning-table .pron-col{{width:38%}}.learning-table .meaning-col{{width:28%}}.learning-table th{{background:{ui['rule']};font-size:9.5pt;padding:2mm;vertical-align:top}}.learning-table td{{width:auto;text-align:left;vertical-align:top;padding:2.5mm 2mm;border:1px solid {ui['rule']};overflow-wrap:anywhere}}.learning-table td:first-child{{font-family:'Miriam Libre';font-size:9.5pt;color:var(--accent)}}.learning-table thead{{display:table-header-group}}.learning-table .annotated{{margin:0;line-height:1.8}}.learning-table tr{{break-inside:avoid}}.learning-table.vocab-3col .vocab-bangla-col{{width:22%}}.learning-table.vocab-3col .vocab-hindi-col{{width:32%}}.learning-table.vocab-3col .vocab-sentence-col{{width:46%}}.learning-table.vocab-3col td{{padding:2mm 2.5mm;vertical-align:top}}.learning-table.vocab-3col td:first-child{{font-family:{fonts.STACK};font-size:10pt;color:{ui['text']}}}.vocab-target{{font-size:1.22em;line-height:1.3;margin-bottom:0.8mm}}.sentence-target{{font-size:1.15em;line-height:1.35;margin-bottom:0.8mm}}.pron-rom{{font-size:0.92em;line-height:1.35;color:{ui['text']}}}.meaning-text{{font-family:{fonts.STACK};font-size:1.05em;color:{ui['text']};line-height:1.35}}.compact-example{{margin-top:2mm;padding:2mm 2.5mm;background:rgba(255,255,255,0.65);border-radius:2mm;border-left:2px solid var(--accent)}}"""
        if not mobile and size[0] < size[1] and not epub:
            css += '''.cover>.reading-image{width:100%;height:100%;object-fit:cover}.cover-copy{left:5%;top:3%;width:90%}.cover h1{font-size:26pt;line-height:1.15;margin:3mm 0}.cover h2{font-size:19pt;margin:2mm 0}.cover .publisher{margin-top:3mm}.cover .eyebrow{margin-bottom:2mm}'''
        if tracker:
            css += f"table{{font-size:{ui['tracker_font_pt']}pt}}td{{padding:{ui['tracker_cell_padding_mm']}mm 2mm}}"
        if mobile:
            css += '''.cards{display:block}.card{margin-bottom:3mm}.contents ol{column-count:1}.cover>.reading-image{width:100%;height:100%;object-fit:cover}.cover-copy{left:5%;top:3%;width:90%}.cover h1{font-size:18pt;line-height:1.15;margin:2mm 0}.cover h2{font-size:13pt;margin:1mm 0}.cover-copy p{font-size:8.5pt;margin:1mm 0}.cover .publisher{margin-top:2mm;font-size:8pt}.cover .eyebrow{font-size:8pt;margin-bottom:1mm}.reading-image{max-height:68mm}h1{font-size:18pt}h2{font-size:14pt}.chapter-native{font-size:11pt}.card{padding:3mm}.script-symbol{font-size:20pt}'''
        if epub:
            css += '''.cover{height:auto;min-height:0;overflow:visible;page-break-after:always}.cover>.reading-image{position:static;width:100%;height:auto;max-height:none}.cover-copy{position:static;width:auto;margin:1em}.cover h1{font-size:2em}.cover h2{font-size:1.4em}.cards{display:block}.card{margin-bottom:1em}.reading-image{max-height:none}.contents ol{column-count:1}.chapter{page-break-before:always}.word-cue{max-width:100%}@media(max-width:600px){body{font-size:1em}.card{padding:.7em}.native{font-size:1.1em}.cue{font-size:.85em}}'''
        return css

    def build(self, only=None):
        output = BOOK / 'output'
        output.mkdir(exist_ok=True)
        generated = BOOK / 'generated/publication'
        generated.mkdir(exist_ok=True)
        outputs = self.book['expected_output_files']
        selected = [f for f in outputs if not only or f == only or Path(f).stem == only]
        if not selected:
            raise ValueError('Unknown output selection: ' + str(only))
        chrome = render.find_chrome()
        for filename in selected:
            path = output / filename
            mobile = 'mobile' in filename
            sample = 'sample' in filename
            tracker = 'tracker' in filename
            chapters = self.chapters[:2] if sample else self.chapters

            if filename.endswith('.pdf'):
                if tracker:
                    mode = 'tracker_color' if 'color' in filename else 'tracker'
                    body = self.tracker('color' in filename)
                    required = ['MiriamLibre', 'NotoSerifBengali']
                else:
                    mode = 'mobile' if mobile else 'desktop'
                    body = self.cover(mode) + self.contents(chapters) + ''.join(self.chapter(c, i, mode=mode) for i, c in enumerate(chapters))
                    required = ['MiriamLibre', 'NotoSerifBengali', 'NotoSansDevanagari']

                html = generated / (path.stem + '.html')
                html.write_text('<!doctype html><html lang="bn"><head><meta charset="utf-8"/><title>'+esc(self.copy['title'])+'</title><style>'+self.css(mode)+'</style></head><body>'+body+'</body></html>', encoding="utf-8")
                if not tracker:
                    # Assert no clipping on the cover
                    cover_html = generated / (path.stem + '.cover-probe.html')
                    cover_html.write_text('<!doctype html><html lang="bn"><head><meta charset="utf-8"/><title>'+esc(self.copy['title'])+'</title><style>'+self.css(mode)+'</style></head><body>'+self.cover(mode)+'</body></html>', encoding="utf-8")
                    try:
                        render.assert_no_clipping(chrome, cover_html, selector='.cover')
                    finally:
                        cover_html.unlink(missing_ok=True)
                render.render_pdf(chrome, html, path, require_fonts=required)
            else:
                mode = 'mobile' if mobile else 'desktop'
                entries = [('contents.xhtml', self.copy['contents'], render.xhtml_page(self.copy['contents'], self.contents(chapters, True), 'bn'))]
                entries += [('chapter-'+c['chapter_id']+'.xhtml', c['title_bengali'], render.xhtml_page(c['title_bengali'], self.chapter(c, i, True, mode=mode), 'bn')) for i, c in enumerate(chapters)]
                render.write_epub(
                    path,
                    title=self.copy['title_bengali'],
                    author=self.pub['publisher_name'],
                    language=self.pub['language'],
                    chapters=entries,
                    stylesheet=self.css(mode, True),
                    cover_xhtml=render.xhtml_page(self.copy['title_bengali'], self.cover(mode, True), 'bn'),
                    cover_image=self.images['cover'],
                    extra_images=[v for k, v in self.images.items() if k not in ('cover', 'banner')],
                    identifier=self.pub['identifier'] + ':' + mode,
                    modified=self.pub['modified']
                )
            print(f'Built {path.name} ({path.stat().st_size/1024/1024:.2f} MiB)', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only')
    args = parser.parse_args()
    BookRenderer().build(args.only)
