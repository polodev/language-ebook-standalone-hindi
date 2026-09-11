#!/usr/bin/env python3
"""Build review PDFs and EPUBs from validated chapter JSON and local artwork."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageOps

BOOK = Path(__file__).resolve().parent
ROOT = BOOK.parent
sys.path.insert(0, str(ROOT / "shared"))
from englishing_kit import fonts, render
from englishing_kit.markdown_render import escape as esc, render_inline, render_block


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class BookRenderer:
    def __init__(self):
        subprocess.run([sys.executable, str(ROOT / "scripts/manage.py"), "assemble", "--book", BOOK.name], cwd=ROOT, check=True)
        data = load(BOOK / "generated/assembled.json")
        self.book, self.chapters = data["book"], data["chapters"]
        self.supp = load(BOOK / "supplementary.json")
        self.copy = self.supp["copy"]
        self.design = self.supp["design"]
        self.pub = self.supp["publication"]
        self.images = self.prepare_images()

    def prepare_images(self):
        manifest = load(BOOK / "assets/images.json")["images"]
        required = {"cover", "banner"} | {i["key"] for c in self.chapters for i in c["image_prompts"]}
        if required - set(manifest):
            raise ValueError(f"Missing image records: {sorted(required - set(manifest))}")
        directory = BOOK / "generated/publication-images"
        directory.mkdir(parents=True, exist_ok=True)
        result = {}
        for key in sorted(required):
            src = (BOOK / manifest[key]["path"]).resolve()
            if not src.is_relative_to(BOOK) or not src.is_file():
                raise ValueError(f"Missing or unsafe artwork: {key}")
            dest = directory / f"{key}.jpg"
            # Publication derivatives keep the lossless, tracked originals untouched.
            with Image.open(src) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                limit = self.design["ui"]["image_width_px"]
                image.thumbnail((limit, limit * 2), Image.Resampling.LANCZOS)
                image.save(dest, "JPEG", quality=self.design["ui"]["image_jpeg_quality"], optimize=True)
            result[key] = dest
        return result

    def words(self, items):
        return "".join(
            '<span class="word-cue"><span class="native" lang="'+esc(self.pub["target_language"])+'">'+esc(w["target"])+
            '</span> <span class="cue" lang="bn">('+esc(w["bangla_pronunciation"])+')</span></span>'+esc(w["separator_after"])
            for w in items
        )

    def annotated(self, item, model=False):
        prefix = "model_" if model else ""
        return '<div class="annotated">'+self.words(item[prefix+"word_pronunciations"])+"</div>"

    def ordered_entry(self, item):
        return (self.row('meaning', item['meaning_bengali_md'], True)
                + '<div class="native" lang="'+esc(self.pub['target_language'])+'">'+esc(item['target'])+'</div>'
                + self.row('pronunciation', item['bangla_pronunciation'])
                + self.row('romanization', item['romanization'])
                + '<div class="label">'+esc(self.copy['word_breakdown'])+'</div>'
                + self.annotated(item))

    def row(self, label, value, markdown=False):
        return '<div class="detail"><span class="label">'+esc(self.copy[label])+': </span>'+(render_inline(value) if markdown else esc(value))+'</div>'

    def palette(self, number):
        p = self.design["palettes"][number % len(self.design["palettes"])];return f'--accent:{p["ink"]};--tint:{p["background"]}'

    def card(self, body, number=0):
        return '<div class="card" style="'+self.palette(number)+'">'+body+'</div>'

    def picture(self, key, alt, epub=False):
        path = 'images/'+self.images[key].name if epub else self.images[key].resolve().as_uri()
        return '<img class="reading-image" src="'+esc(path)+'" alt="'+esc(alt)+'" />'

    def cover(self, mode, epub=False):
        return '<section class="cover '+mode+'">'+self.picture('cover',self.copy['title_bengali'],epub)+ '<div class="cover-copy"><div class="eyebrow">'+esc(self.copy['edition_note'])+'</div><h1>'+esc(self.copy['title'])+'</h1><h2>'+esc(self.copy['title_bengali'])+'</h2><p>'+esc(self.copy['subtitle'])+'</p><p class="publisher">'+esc(self.copy['publisher'])+'</p></div></section>'

    def contents(self, chapters, epub=False):
        items=''.join('<li><a href="'+('chapter-'+c['chapter_id']+'.xhtml' if epub else '#'+c['chapter_id'])+'">'+esc(c['title_bengali'])+'</a></li>' for c in chapters)
        return '<section class="contents"><h1>'+esc(self.copy['contents'])+'</h1><p>'+esc(self.copy['review_note'])+'</p><ol>'+items+'</ol></section>'

    def chapter(self, chapter, number, epub=False, mode="mobile"):
        c=chapter
        parts=['<article class="chapter" id="'+esc(c['chapter_id'])+'" style="'+self.palette(number)+'">', '<header class="chapter-head"><div class="eyebrow">'+esc(self.copy['chapter_label'])+' '+str(number+1).zfill(2)+'</div><h1>'+esc(c['title_bengali'])+'</h1><div class="chapter-native">'+self.words(c['title_word_pronunciations'])+'</div>'+self.row('pronunciation',c['title_bangla_pronunciation'])+render_block(c['goal_bengali_md'])+'</header>']
        for section in self.design['reading_layout']['section_order']:
            parts.append('<section class="lesson-section"><h2>'+esc(self.copy[section])+'</h2>')
            if section in ('sentences', 'vocabulary') and mode == 'desktop' and not epub:
                headings = self.copy['sentence_table_columns' if section == 'sentences' else 'vocabulary_table_columns']
                parts.append('<table class="learning-table"><colgroup><col class="index-col"/><col class="meaning-col"/><col class="target-col"/><col class="pron-col"/></colgroup><thead><tr>'+''.join('<th scope="col">'+esc(h)+'</th>' for h in headings)+'</tr></thead><tbody>')
                for i, item in enumerate(c[section]):
                    target = self.annotated(item)
                    for field in ['synonyms', 'collocations']:
                        if item.get(field):
                            target += '<div class="label">'+esc(self.copy[field])+'</div>'+''.join(self.annotated(x)+self.row('pronunciation',x['bangla_pronunciation']) for x in item[field])
                    hindi = '<div class="native" lang="'+esc(self.pub['target_language'])+'">'+esc(item['target'])+'</div>'+self.row('pronunciation', item['bangla_pronunciation'])+self.row('romanization', item['romanization'])
                    parts.append('<tr style="'+self.palette((number*20+i)//self.design['palette_rotation_every_items'])+'"><td>'+str(i+1).zfill(2)+'</td><td>'+render_inline(item['meaning_bengali_md'])+'</td><td>'+hindi+'</td><td>'+target+'</td></tr>')
                parts.append('</tbody></table>')
            elif section=='sentences':
                cards=[]
                for i,s in enumerate(c['sentences']):
                    body='<div class="item-number">'+str(i+1).zfill(2)+'</div>'+self.ordered_entry(s)
                    cards.append(self.card(body,(number*20+i)//self.design['palette_rotation_every_items']))
                parts.append('<div class="cards">'+''.join(cards)+'</div>')
            elif section=='vocabulary':
                cards=[]
                for i,v in enumerate(c['vocabulary']):
                    body=self.ordered_entry(v)
                    for field in ['synonyms','collocations']:
                        if v.get(field):
                            body+='<div class="label">'+esc(self.copy[field])+'</div>'+''.join(self.annotated(x)+self.row('pronunciation',x['bangla_pronunciation']) for x in v[field])
                    cards.append(self.card(body,(number*20+i)//self.design['palette_rotation_every_items']))
                parts.append('<div class="cards vocabulary">'+''.join(cards)+'</div>')
            elif section in ('bridge_reading','target_reading'):
                r=c[section];key=next(x['key'] for x in c['image_prompts'] if x['reading']==section)
                parts.append('<h3>'+esc(r['title_bengali'])+'</h3>'+self.picture(key,r['scene_summary'],epub))
                if section=='bridge_reading':
                    # Validate the Markdown mirror during assembly; render canonical segments
                    # so each bold native word remains attached to its pronunciation cue.
                    prose=''.join(esc(s['text']) if s['kind']=='bangla' else self.words(s['word_pronunciations']) for s in r['segments'])
                    parts.append('<div class="bridge prose">'+prose+'</div>')
                else:
                    parts.append('<h3>'+esc(self.copy['complete_target_reading'])+'</h3><div class="complete-target-reading" lang="'+esc(self.pub['target_language'])+'">'+''.join('<p class="native">'+esc(line['target'])+'</p>' for line in r['lines'])+'</div><h3>'+esc(self.copy['reading_breakdown'])+'</h3>')
                    parts.append('<div class="pure-reading">'+''.join('<div class="reading-line">'+self.annotated(line)+self.row('pronunciation',line['bangla_pronunciation'])+'</div>' for line in r['lines'])+'</div>')
                    parts.append('<h3>'+esc(self.copy['reading_pronunciation'])+'</h3><p>'+esc(r['bangla_pronunciation'])+'</p><h3>'+esc(self.copy['reading_meaning'])+'</h3>'+render_block(r['meaning_bengali_md']))
            elif section=='script_and_numbers':
                parts.append('<h3>'+esc(self.copy['script'])+'</h3><div class="cards">')
                for s in c['script_practice']:
                    body='<div class="script-symbol"><span class="native" lang="'+esc(self.pub['target_language'])+'">'+esc(s['target'])+'</span> <span class="cue">('+esc(s['bangla_pronunciation'])+')</span></div><div class="label">'+esc(self.copy['script_modes'][s['mode']])+'</div>'+render_block(s['explanation_bengali_md'])+render_block(s['practice_bengali_md'])
                    parts.append(self.card(body,number))
                parts.append('</div>')
                if c['number_practice']:
                    parts.append('<h3>'+esc(self.copy['numbers'])+'</h3><div class="cards">')
                    for n in c['number_practice']:
                        parts.append(self.card('<div class="number-symbol">'+esc(n['display'])+'</div>'+self.annotated(n)+self.row('pronunciation',n['bangla_pronunciation'])+self.row('meaning',n['meaning_bengali_md'],True),number))
                    parts.append('</div>')
            elif section=='speaking_practice':
                parts.append('<div class="cards">')
                for i,s in enumerate(c['speaking_practice']):
                    parts.append(self.card('<div class="item-number">'+str(i+1).zfill(2)+'</div>'+render_block(s['prompt_bengali_md'])+'<div class="label">'+esc(self.copy['answer'])+'</div>'+self.annotated(s,True)+self.row('pronunciation',s['model_bangla_pronunciation'])+self.row('meaning',s['model_meaning_bengali_md'],True),number))
                parts.append('</div>')
            parts.append('</section>')
        if c.get('additional_practice'):
            parts.append('<section class="lesson-section"><h2>'+esc(self.copy['additional_practice'])+'</h2>')
            for item in c['additional_practice']:
                parts.append(render_block(item['explanation_bengali_md']))
                for prefix in ['base','expanded','polished']:
                    parts.append('<h3>'+esc(self.copy[prefix])+'</h3>'+self.words(item[prefix+'_word_pronunciations'])+self.row('pronunciation',item[prefix+'_bangla_pronunciation']))
            parts.append('</section>')
        parts.append('</article>');return ''.join(parts)

    def tracker(self, color):
        pages=[]
        for start in range(0,len(self.chapters),30):
            rows=[]
            for i,c in enumerate(self.chapters[start:start+30],start):
                style=self.palette(i//5) if color else ''
                rows.append('<tr style="'+style+'"><td>'+str(i+1).zfill(2)+'</td><td>'+esc(c['title_bengali'])+'</td>'+('<td><span class="check-box"></span></td>'*3)+'</tr>')
            pages.append('<section class="tracker"><h1>'+esc(self.copy['tracker'])+'</h1><p>'+esc(self.copy['title_bengali'])+' · '+esc(self.copy['tracker_subtitle'])+'</p><table><thead><tr>'+''.join('<th>'+esc(s)+'</th>' for s in self.copy['tracker_columns'])+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></section>')
        return ''.join(pages)

    def css(self,mode,epub=False):
        ui=self.design['ui'];mobile=mode=='mobile';tracker=mode.startswith('tracker');size=self.design['tracker_page_mm'] if tracker else self.design['mobile_page_mm'] if mobile else self.design['desktop_page_mm'];margin=ui['mobile_margin_mm'] if mobile else ui['desktop_margin_mm'];pt=ui['mobile_font_pt'] if mobile else ui['desktop_font_pt']
        face=fonts.epub_font_faces() if epub else fonts.font_face_css()
        page='' if epub else f'''@page {{size:{size[0]}mm {size[1]}mm;margin:{margin}mm;@bottom-left{{content:"{self.copy['publisher']}";font-family:{fonts.STACK};font-size:8pt;color:{ui['muted']};}}@bottom-right{{content:counter(page);font-family:{fonts.STACK};font-size:8pt;}}}}'''
        css=face+page+f'''
        *{{box-sizing:border-box}}html,body{{margin:0;padding:0}}body{{font-family:{fonts.STACK};font-size:{pt}pt;line-height:1.55;color:{ui['text']};background:{ui['paper']};font-synthesis:none}}a{{color:inherit;text-decoration:none}}h1,h2,h3,p{{margin:0 0 3mm}}h1{{font-size:22pt;line-height:1.4}}h2{{font-size:17pt;color:var(--accent,{ui['cover_ink']});border-bottom:1px solid {ui['rule']};padding-bottom:2mm;margin-top:5mm;break-after:avoid}}h3{{font-size:13pt;margin-top:4mm;break-after:avoid}}p{{orphans:2;widows:2}}.native{{font-family:'{self.design['target_font']}',{fonts.STACK};font-weight:700;font-size:1.16em}}.cue{{color:{ui['muted']};font-size:.85em;font-weight:400}}.word-cue{{display:inline-block;white-space:nowrap;max-width:100%}}.annotated{{line-height:1.9;margin-bottom:2mm}}.detail{{font-size:.93em;margin:1mm 0;overflow-wrap:anywhere}}.label{{font-size:.82em;color:{ui['muted']};font-weight:700}}.item-number{{font-family:'Miriam Libre';font-size:10pt;color:var(--accent);font-weight:700;margin-bottom:1mm}}.cards{{display:grid;grid-template-columns:1fr 1fr;gap:3mm;align-items:start}}.card{{break-inside:avoid;border-left:1mm solid var(--accent);border-radius:{ui['card_radius_mm']}mm;background:var(--tint);padding:3mm 4mm;min-width:0}}.card p{{margin:1mm 0}}.chapter{{break-before:page}}.chapter-head{{break-inside:avoid;border-top:2mm solid var(--accent);padding-top:5mm;margin-bottom:4mm}}.eyebrow{{font-size:10pt;font-weight:700;letter-spacing:.05em;color:{ui['muted']};margin-bottom:3mm}}.chapter-native{{font-size:13pt;margin:2mm 0}}.reading-image{{display:block;width:100%;height:auto;max-height:92mm;object-fit:contain;margin:3mm auto 5mm;break-inside:avoid}}.prose{{line-height:2.05;margin:2mm 0 6mm}}.bridge .native{{font-weight:700}}.reading-line{{padding:2mm 0;border-bottom:1px solid {ui['rule']};break-inside:avoid}}.script-symbol{{font-size:22pt;line-height:1.7}}.number-symbol{{font-size:20pt;font-weight:700}}.cover{{position:relative;break-after:page;height:{size[1]-2*margin-2}mm;overflow:hidden;background:var(--tint,{ui['paper']})}}.cover>.reading-image{{position:absolute;right:0;top:0;width:54%;height:100%;max-height:none;object-fit:contain;margin:0}}.cover-copy{{position:absolute;top:22%;left:2%;width:43%;color:{ui['cover_ink']}}}.cover h1{{font-size:37pt;line-height:1.12;margin:4mm 0}}.cover h2{{border:0;font-size:23pt;margin:4mm 0}}.cover .publisher{{margin-top:10mm;font-size:10pt}}.contents{{break-after:page}}.contents ol{{column-count:2;column-gap:10mm;margin:4mm 0;padding-left:8mm}}.contents li{{break-inside:avoid;margin-bottom:2mm;padding-left:1mm}}.tracker{{break-after:page}}.tracker:last-child{{break-after:auto}}table{{border-collapse:collapse;width:100%;font-size:10pt}}th{{text-align:left;padding:2mm;border-bottom:1px solid {ui['rule']}}}td{{padding:1.5mm 2mm;border-bottom:1px solid {ui['rule']};background:var(--tint,{ui['paper']})}}td:first-child{{width:13mm}}td:nth-child(n+3){{text-align:center;width:20mm}}tr{{break-inside:avoid}}.check-box{{display:inline-block;width:3mm;height:3mm;border:1px solid {ui['muted']}}}
        '''
        if mode == 'desktop' and not epub:
            css+=f""".learning-table{{table-layout:fixed;font-size:10pt;margin:3mm 0 5mm}}.learning-table .index-col{{width:6%}}.learning-table .target-col{{width:28%}}.learning-table .pron-col{{width:38%}}.learning-table .meaning-col{{width:28%}}.learning-table th{{background:{ui['rule']};font-size:9pt;padding:2mm;vertical-align:top}}.learning-table td{{width:auto;text-align:left;vertical-align:top;padding:2.5mm 2mm;border:1px solid {ui['rule']};overflow-wrap:anywhere}}.learning-table td:first-child{{font-family:'Miriam Libre';font-size:9pt;color:var(--accent)}}.learning-table thead{{display:table-header-group}}.learning-table .annotated{{margin:0;line-height:1.8}}.learning-table tr{{break-inside:avoid}}"""
        if mode == 'desktop' and size[0] < size[1] and not epub:
            css+='''.cover>.reading-image{width:100%;height:100%;object-fit:cover}.cover-copy{left:5%;top:3%;width:90%}.cover h1{font-size:32pt}.cover h2{font-size:24pt;margin:2mm 0}.cover .publisher{margin-top:3mm}.cover .eyebrow{margin-bottom:2mm}'''
        if tracker:
            css+=f"table{{font-size:{ui['tracker_font_pt']}pt}}td{{padding:{ui['tracker_cell_padding_mm']}mm 2mm}}"
        if mobile:
            css+='''.cards{display:block}.card{margin-bottom:3mm}.contents ol{column-count:1}.cover>.reading-image{width:100%;height:100%;object-fit:cover}.cover-copy{left:5%;top:3%;width:90%}.cover h1{font-size:23pt}.cover h2{font-size:16pt;margin:1mm 0}.cover-copy p{font-size:9pt}.cover .publisher{margin-top:2mm}.cover .eyebrow{font-size:8pt;margin-bottom:1mm}.reading-image{max-height:68mm}h1{font-size:19pt}h2{font-size:15pt}.chapter-native{font-size:11pt}.card{padding:3mm}.script-symbol{font-size:20pt}'''
        if epub:
            css+='''.cover{height:auto;min-height:0;overflow:visible;page-break-after:always}.cover>.reading-image{position:static;width:100%;height:auto;max-height:none}.cover-copy{position:static;width:auto;margin:1em}.cover h1{font-size:2em}.cover h2{font-size:1.4em}.cards{display:block}.card{margin-bottom:1em}.reading-image{max-height:none}.contents ol{column-count:1}.chapter{page-break-before:always}.word-cue{max-width:100%}@media(max-width:600px){body{font-size:1em}.card{padding:.7em}.native{font-size:1.1em}.cue{font-size:.85em}}'''
        return css

    def build(self,only=None):
        output=BOOK/'output';output.mkdir(exist_ok=True);generated=BOOK/'generated/publication';generated.mkdir(exist_ok=True)
        outputs=self.book['expected_output_files']
        selected=[f for f in outputs if not only or f==only or Path(f).stem==only]
        if not selected:raise ValueError('Unknown output selection: '+str(only))
        chrome=render.find_chrome()
        for filename in selected:
            path=output/filename;mobile='mobile' in filename;mode='mobile' if mobile else 'desktop';sample='sample' in filename;chapters=self.chapters[:2] if sample else self.chapters
            if filename.endswith('.pdf'):
                if 'tracker' in filename:
                    mode='tracker_color' if 'color' in filename else 'tracker';body=self.tracker('color' in filename);required=['MiriamLibre','NotoSerifBengali']
                else:
                    body=self.cover(mode)+self.contents(chapters)+''.join(self.chapter(c,i,mode=mode) for i,c in enumerate(chapters));required=['MiriamLibre','NotoSerifBengali','NotoSansDevanagari']
                html=generated/(path.stem+'.html');html.write_text('<!doctype html><html lang="bn"><head><meta charset="utf-8"/><title>'+esc(self.copy['title'])+'</title><style>'+self.css(mode)+'</style></head><body>'+body+'</body></html>')
                render.assert_no_clipping(chrome,html,selector='.cover')
                render.render_pdf(chrome,html,path,require_fonts=required)
            else:
                entries=[('contents.xhtml',self.copy['contents'],render.xhtml_page(self.copy['contents'],self.contents(chapters,True),'bn'))]
                entries += [('chapter-'+c['chapter_id']+'.xhtml',c['title_bengali'],render.xhtml_page(c['title_bengali'],self.chapter(c,i,True),'bn')) for i,c in enumerate(chapters)]
                render.write_epub(path,title=self.copy['title_bengali'],author=self.pub['publisher_name'],language=self.pub['language'],chapters=entries,stylesheet=self.css(mode,True),cover_xhtml=render.xhtml_page(self.copy['title_bengali'],self.cover(mode,True),'bn'),cover_image=self.images['cover'],extra_images=[v for k,v in self.images.items() if k not in ('cover','banner')],identifier=self.pub['identifier']+':'+mode,modified=self.pub['modified'])
            print(f'Built {path.name} ({path.stat().st_size/1024/1024:.1f} MiB)',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only');args=parser.parse_args()
    BookRenderer().build(args.only)
