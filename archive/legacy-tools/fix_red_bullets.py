# -*- coding: gbk -*-
"""把误并入破折号 run 的正文拆回去（恢复 17pt / 深色 / 非红）。"""
import sys

from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v9.pptx'
prs = Presentation(P)

BODY_SIZE = Pt(17.0)
BODY_COLOR = RGBColor(0x24, 0x33, 0x3B)
DASH_COLOR = RGBColor(0xE9, 0x61, 0x71)

fixed = 0
for si, slide in enumerate(prs.slides, 1):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        for para in sh.text_frame.paragraphs:
            runs = para.runs
            if not runs:
                continue
            first = runs[0].text
            if not (first.startswith('—') or first.startswith('·')):
                continue
            if len(first.strip()) <= 3:       # 只有破折号本身，正常
                continue
            lead = '—  ' if first.startswith('—') else '·  '
            content = first.strip()[1:].strip()
            runs[0].text = lead
            runs[0].font.color.rgb = DASH_COLOR
            if len(runs) >= 2:
                r = runs[1]
            else:
                r = para.add_run()
            r.text = ' ' + content
            r.font.size = BODY_SIZE
            r.font.bold = False
            r.font.color.rgb = BODY_COLOR
            for rr in runs[2:]:
                rr.text = ''
            print('S%-2d 已修正: %s%s' % (si, lead, content[:50]))
            fixed += 1

print('')
print('共修正 %d 处' % fixed)
prs.save(P)
print('已保存:', P)
