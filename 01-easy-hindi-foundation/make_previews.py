#!/usr/bin/env python3
"""Compose promotional banner and reading screenshots from local build assets."""
import fitz
from generate_pdfs import BOOK, BookRenderer, fonts, render, esc

r = BookRenderer()
out = BOOK / 'output/previews'
out.mkdir(exist_ok=True)
for mode, prefix in [('desktop', '05'), ('mobile', '06')]:
    source = next((BOOK / 'output').glob(prefix + '-*.pdf'))
    with fitz.open(source) as doc:
        for index in [0, 2, len(doc)//2]:
            doc[index].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(out / f'{mode}-page-{index+1}.png')
ui = r.design['ui']
css = fonts.font_face_css() + f"""@page{{size:288mm 192mm;margin:0}}*{{box-sizing:border-box}}body{{margin:0;font-family:{fonts.STACK};color:{ui['cover_ink']}}}.art{{position:absolute;width:288mm;height:192mm}}.copy{{position:absolute;left:12mm;top:22mm;width:110mm;padding:5mm;background:{ui['paper']}E8}}h1{{font-size:32pt;line-height:1.2}}h2{{font-size:22pt}}p{{font-size:13pt}}"""
html = '<!doctype html><html lang="bn"><meta charset="utf-8"><style>'+css+'</style><body><img class="art" src="'+r.images['banner'].as_uri()+'"><div class="copy"><p>'+esc(r.copy['edition_note'])+'</p><h1>'+esc(r.copy['title'])+'</h1><h2>'+esc(r.copy['title_bengali'])+'</h2><p>'+esc(r.copy['subtitle'])+'</p><p>'+esc(r.copy['publisher'])+'</p></div></body></html>'
p = BOOK / 'generated/publication/banner.html'
p.write_text(html)
pdf = BOOK / 'generated/publication/banner.pdf'
render.render_pdf(render.find_chrome(), p, pdf, require_fonts=['MiriamLibre', 'NotoSerifBengali'])
with fitz.open(pdf) as doc:
    assert len(doc) == 1
    doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(out / 'banner.png')
print(out)
