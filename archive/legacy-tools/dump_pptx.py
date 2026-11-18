# -*- coding: gbk -*-
"""把 pptx 里所有文字按 幻灯片/形状 打印出来，供通读。"""
import sys

from pptx import Presentation
from pptx.util import Emu

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

if len(sys.argv) > 1:
    SRC = sys.argv[1]
else:
    SRC = (r'C:\Users\MYAGES~1\AppData\Local\Temp\codebuddy-dropped-files'
           r'\dc32098d-c2ea-4840-83e7-fd892ee559ab\试用期述职报告_赵庆斌_v7.pptx')

prs = Presentation(SRC)
print('幻灯片总数: %d   尺寸: %.1f x %.1f cm'
      % (len(prs.slides), prs.slide_width / 360000.0, prs.slide_height / 360000.0))


def dump_shape(sh, indent='    '):
    lines = []
    if not sh.has_text_frame:
        return lines
    for p in sh.text_frame.paragraphs:
        txt = ''.join(r.text for r in p.runs)
        if txt.strip():
            lines.append('%s%s' % (indent, txt))
    return lines


for si, slide in enumerate(prs.slides, 1):
    print('')
    print('=' * 78)
    print('### 第 %d 页' % si)
    print('=' * 78)
    for shi, sh in enumerate(slide.shapes):
        if sh.has_table:
            print('  [shape %d] 表格 %d行 x %d列  name=%s'
                  % (shi, len(sh.table.rows), len(sh.table.columns), sh.name))
            for r in sh.table.rows:
                cells = [c.text.replace('\n', ' / ') for c in r.cells]
                print('      | ' + ' | '.join(cells))
            continue
        if sh.has_text_frame and sh.text_frame.text.strip():
            print('  [shape %d] name=%s  pos=(%.1f,%.1f)cm'
                  % (shi, sh.name, sh.left / 360000.0, sh.top / 360000.0))
            for ln in dump_shape(sh):
                print('      ' + ln)
