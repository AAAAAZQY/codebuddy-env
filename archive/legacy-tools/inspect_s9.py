# -*- coding: gbk -*-
"""检查 S9 的版式与形状，为拆分做准备；同时列出所有页码形状。"""
import sys

from pptx import Presentation

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v8.pptx'
prs = Presentation(P)
print('总页数 %d' % len(prs.slides))

s = prs.slides[8]
print('S9 版式: %s' % s.slide_layout.name)
print('S9 形状:')
for i, sh in enumerate(s.shapes):
    txt = ''
    if sh.has_text_frame:
        txt = sh.text_frame.text.replace('\n', ' / ')[:50]
    print('  [%d] %-14s type=%-12s pos=(%.1f,%.1f) size=(%.1fx%.1f)  %s'
          % (i, sh.name, sh.shape_type, sh.left / 360000.0, sh.top / 360000.0,
             sh.width / 360000.0, sh.height / 360000.0, txt))

print('')
print('各页页码文本:')
for i, sl in enumerate(prs.slides, 1):
    for sh in sl.shapes:
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if '/' in t and len(t) < 12 and any(ch.isdigit() for ch in t):
                print('  S%-2d %r  (shape=%s)' % (i, t, sh.name))
