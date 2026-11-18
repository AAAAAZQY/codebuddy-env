# -*- coding: gbk -*-
"""工作计划重排：短期独立调参 / 中期模糊 PID / 长期 RTOS / 电流环作补充。"""
import sys

from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v12.pptx'
prs = Presentation(P)

BODY = RGBColor(0x24, 0x33, 0x3B)
DASH = RGBColor(0xE9, 0x61, 0x71)

LINES = [
    '短期（1~3 月）：独立完成限位、零点、速度曲线与 PID 的整定，沉淀一份可复用的调试步骤',
    '短期（1~3 月）：参与稳像调参，用阶跃响应与抖动 RMS 量化效果，留调参记录',
    '中期（3~6 月）：研究模糊 PID，先做离线仿真，对比固定参数方案在负载与装配差异下的表现',
    '长期（6~12 月）：学习 RTOS 任务调度与优先级设计，在控制模块尝试引入并评估收益',
    '补充：学习电流环控制原理，为后续伺服方向打基础（本工程未涉及）',
]

body = None
for sh in prs.slides[14].shapes:
    if sh.has_text_frame and sh.text_frame.text.strip().startswith('—'):
        body = sh
        break
assert body is not None

paras = list(body.text_frame.paragraphs)
assert len(paras) == len(LINES), '段落数不符 %d' % len(paras)

for p, txt in zip(paras, LINES):
    runs = p.runs
    runs[0].text = '—  '
    runs[0].font.size = Pt(15.0)
    runs[0].font.color.rgb = DASH
    runs[0].font.bold = False
    runs[1].text = txt
    runs[1].font.size = Pt(17.0)
    runs[1].font.bold = False
    runs[1].font.color.rgb = BODY
    for r in runs[2:]:
        r.text = ''
    print('  ' + txt)

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v12.pptx', '_v13.pptx')
    prs.save(DST)
    print('v12 被占用，改存 v13')
print('已保存:', DST)
