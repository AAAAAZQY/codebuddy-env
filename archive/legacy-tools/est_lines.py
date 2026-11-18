# -*- coding: gbk -*-
"""估算正文段落在不同字号下的行数, 判断能否统一到 17pt 而不溢出。"""
import math
import sys

from pptx import Presentation
from pptx.util import Emu

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v8.pptx'
prs = Presentation(SRC)


def width_units(txt):
    """中文/全角记 1.0，ASCII 记 0.55。"""
    u = 0.0
    for ch in txt:
        u += 1.0 if ord(ch) > 0x2E80 else 0.55
    return u


def est_lines(txt, box_cm, size_pt):
    per_line = box_cm / (size_pt * 0.03528)
    return max(1, math.ceil(width_units(txt) / max(1.0, per_line)))


print('%-5s %-6s %-7s %-6s %-18s' % ('页', '框宽cm', '框高cm', '段数', '行数@16 -> @17'))
print('-' * 56)
for si, slide in enumerate(prs.slides, 1):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        paras = [''.join(r.text for r in p.runs)
                 for p in sh.text_frame.paragraphs]
        paras = [t for t in paras if t.strip().startswith(('—', '·'))]
        if not paras:
            continue
        w = sh.width / 360000.0
        h = sh.height / 360000.0
        n16 = sum(est_lines(t, w, 16) for t in paras)
        n17 = sum(est_lines(t, w, 17) for t in paras)
        cap16 = h / (16 * 0.03528 * 1.35)
        flag = ''
        if n17 > n16:
            flag = '  <== 17pt 多出 %d 行' % (n17 - n16)
        if n16 > cap16:
            flag += '  (16pt 已超框 %.1f 行)' % (n16 - cap16)
        print('S%-4d %-7.1f %-8.1f %-7d %d -> %d   容量约%.1f行%s'
              % (si, w, h, len(paras), n16, n17, cap16, flag))
