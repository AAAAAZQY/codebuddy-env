# -*- coding: gbk -*-
"""打印待修改段落的精确文本与其 run 拆分情况。"""
import sys

from pptx import Presentation

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v7.pptx'
prs = Presentation(SRC)

TARGETS = [
    (2, '电机 / 显示 / 电源 / 光敏 / 方法'),
    (5, 'IRCUT画面异常'),
    (8, '收获 · 显示与电源'),
    (8, 'DISPLAY'),
    (9, '收获 · 光敏与协议'),
    (9, 'LIGHT'),
    (9, '软硬光敏切换'),
]

for sno, key in TARGETS:
    slide = prs.slides[sno - 1]
    for shi, sh in enumerate(slide.shapes):
        if not sh.has_text_frame:
            continue
        for pi, p in enumerate(sh.text_frame.paragraphs):
            txt = ''.join(r.text for r in p.runs)
            if key in txt:
                print('S%-2d shape%-2d para%-2d  %r' % (sno, shi, pi, txt))
                print('        runs = %r' % [r.text for r in p.runs])
                print('')
