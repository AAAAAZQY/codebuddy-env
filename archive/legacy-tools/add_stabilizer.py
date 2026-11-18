# -*- coding: gbk -*-
"""模块数改 3 个、补稳像移植与软件限位。"""
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


# ---------- S4：2 个模块 -> 3 个模块 ----------
for sh in prs.slides[3].shapes:
    if not sh.has_text_frame:
        continue
    for para in sh.text_frame.paragraphs:
        t = ''.join(r.text for r in para.runs)
        if '2 个模块移植' in t and len(para.runs) >= 2:
            fix(para, '3 个模块移植：激光测距、红外补光灯、稳像（纯软件，无新增硬件）')
            print('S4 模块口径 -> 3 个')
        elif t.strip() == '2' and sh.left / 360000.0 > 24:
            para.runs[0].text = '3'
            for r in para.runs[1:]:
                r.text = ''
            print('S4 KPI 数字 2 -> 3')

# ---------- S5：外设方向补稳像 ----------
for sh in prs.slides[4].shapes:
    if not sh.has_text_frame:
        continue
    for para in sh.text_frame.paragraphs:
        t = ''.join(r.text for r in para.runs)
        if '外设与模块' in t and '激光测距' in t:
            fix(para, '外设与模块：XH T160 红外补光灯 / 激光测距 / 稳像移植、'
                      'KB T160 查询协议、馥鸿 B130 串口改造')
            print('S5 外设方向已补稳像')

# ---------- S10：重写 4 条 ----------
body = None
for sh in prs.slides[9].shapes:
    if sh.has_text_frame and sh.text_frame.text.strip().startswith('—'):
        body = sh
        break
assert body is not None

LINES = [
    '三个模块移植：激光测距、红外补光灯、稳像（稳像为纯软件实现，无新增硬件）',
    '稳像软件限位：新增软件限位函数，限制稳像摆动范围，避免越界撞头，实测好用',
    '外设协议：KB T160 新增查询协议；馥鸿 B130 双串口改单串口，'
    '定位对方下发异常并推动修正',
    '能力沉淀：熟悉串口协议解析与模块移植流程；协议问题先对齐帧、再补解析分支',
]
tf = body.text_frame
paras = list(tf.paragraphs)
for i, p in enumerate(paras):
    if i < len(LINES):
        fix(p, LINES[i])
    else:
        p._p.getparent().remove(p._p)
print('S10 现有 %d 条' % len(tf.paragraphs))

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v11.pptx', '_v12.pptx')
    prs.save(DST)
    print('v11 被占用，改存 v12')
print('已保存:', DST)
