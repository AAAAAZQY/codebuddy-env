# -*- coding: gbk -*-
"""修 S4 首条的红色整句，并精简 S12 的效果表述。"""
import sys

from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v11.pptx'
prs = Presentation(P)

BODY = RGBColor(0x24, 0x33, 0x3B)
DASH = RGBColor(0xE9, 0x61, 0x71)


def fix(para, text):
    runs = para.runs
    runs[0].text = '—  '
    runs[0].font.size = Pt(15.0)
    runs[0].font.color.rgb = DASH
    runs[0].font.bold = False
    runs[1].text = text
    runs[1].font.size = Pt(17.0)
    runs[1].font.bold = False
    runs[1].font.color.rgb = BODY
    for r in runs[2:]:
        r.text = ''


# S4 首条
for sh in prs.slides[3].shapes:
    if not sh.has_text_frame:
        continue
    for para in sh.text_frame.paragraphs:
        t = ''.join(r.text for r in para.runs)
        if '十余个项目' in t and len(para.runs) >= 2:
            fix(para, '十余个项目：问题修复、定制化项目、新功能开发三类并行')
            print('S4 首条已修正为常规配色')

# S12 效果表述
for sh in prs.slides[11].shapes:
    if not sh.has_text_frame:
        continue
    for para in sh.text_frame.paragraphs:
        t = ''.join(r.text for r in para.runs)
        if t.strip().startswith('—') and '效果' in t:
            fix(para, '效果：从「带载乱跳、充电虚高」到电量稳定，重启跳变由 ±20% 收敛到 ±5%')
            print('S12 效果表述已精简')

prs.save(P)
print('已保存:', P)
