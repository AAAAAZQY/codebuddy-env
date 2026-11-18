# -*- coding: gbk -*-
"""把 S17 总结页的概述句扩写为「过渡 + 能力收获 + 感谢」。"""
import sys

from pptx import Presentation
from pptx.util import Cm, Pt
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v9.pptx'
prs = Presentation(P)

s = prs.slides[16]
box = None
for sh in s.shapes:
    if sh.has_text_frame and '三个月' in sh.text_frame.text:
        box = sh
        break
assert box is not None, '未找到概述文本框'

L1 = ('三个月完成从协助到独立跟进项目的过渡：'
      '能独立定位问题、承接定制需求、完成新功能')
L2 = ('补上了电机控制基础，熟悉云台固件架构与调试手段，'
      '养成先复现、再查改动与时序、最后怀疑硬件的排查顺序；'
      '也学会了主动请教与协作，感谢带教和同事的帮助')

tf = box.text_frame
p1 = tf.paragraphs[0]
p1.runs[0].text = L1
for r in p1.runs[1:]:
    r.text = ''

p2 = tf.add_paragraph()
r2 = p2.add_run()
r2.text = L2
r2.font.size = Pt(17.0)
r2.font.bold = False
r2.font.color.rgb = RGBColor(0x24, 0x33, 0x3B)
r2.font.name = p1.runs[0].font.name

# 文本框加高（卡片从 10.0cm 开始，留出余量到 9.8）
box.height = Cm(3.0)
print('文本框高度改为 %.1f cm，底边 %.1f cm' % (box.height / 360000.0,
                                              (box.top + box.height) / 360000.0))

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v9.pptx', '_v10.pptx')
    prs.save(DST)
    print('v9 被占用，改存 v10')
print('已保存:', DST)
