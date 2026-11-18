# -*- coding: gbk -*-
"""校验生成的口播稿 docx：段落数、字体、字号、乱码。用法: python chk_speech_doc.py <路径>"""
import sys

from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

path = sys.argv[1]
doc = Document(path)

bad = 0
total = 0
for p in doc.paragraphs:
    txt = p.text
    total += len(txt)
    if '?' in txt:
        bad += txt.count('?')
    if not p.runs:
        print('(empty)')
        continue
    r = p.runs[0]
    rpr = r._element.rPr
    ea = ''
    if rpr is not None and rpr.rFonts is not None:
        ea = rpr.rFonts.get(qn('w:eastAsia')) or ''
    size = r.font.size.pt if r.font.size else 0
    indent = p.paragraph_format.first_line_indent
    ind_txt = '%.0fpt' % (indent.pt if indent else 0)
    print('%5.1fpt %-5s indent%-6s %s' % (size, ea, ind_txt, txt[:30]))

print('---')
print('paras=%d chars=%d badChars=%d' % (len(doc.paragraphs), total, bad))
