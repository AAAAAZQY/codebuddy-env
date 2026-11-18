# -*- coding: gbk -*-
"""拆分 S9：日夜与灯光 / 外设与模块；更新方向命名；重编页码。"""
import copy
import sys

from pptx import Presentation
from pptx.util import Pt

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v8.pptx'
prs = Presentation(P)

# ---------- 1. 复制 S9 作为新页，插到 S9 之后 ----------
src = prs.slides[8]
new = prs.slides.add_slide(src.slide_layout)
for sh in list(new.shapes):
    sh._element.getparent().remove(sh._element)
for sh in src.shapes:
    new.shapes._spTree.append(copy.deepcopy(sh._element))

ids = list(prs.slides._sldIdLst)
el = ids[-1]
prs.slides._sldIdLst.remove(el)
prs.slides._sldIdLst.insert(9, el)
print('已插入新页，当前总页数 %d' % len(prs.slides))


# ---------- 2. 改写正文（保留 run0 破折号格式） ----------
def set_body(slide_idx, lines):
    body = prs.slides[slide_idx].shapes[5]
    paras = body.text_frame.paragraphs
    assert len(paras) == len(lines), '段落数不符: %d vs %d' % (len(paras), len(lines))
    for p, txt in zip(paras, lines):
        assert len(p.runs) >= 2, 'run 结构异常'
        p.runs[1].text = txt
        for r in p.runs[2:]:
            r.text = ''


def set_title(slide_idx, cn, en):
    s = prs.slides[slide_idx]
    s.shapes[2].text_frame.paragraphs[0].runs[0].text = cn
    s.shapes[3].text_frame.paragraphs[0].runs[0].text = en


set_title(8, '收获 · 日夜与灯光', 'DAY-NIGHT   &   LIGHTING')
set_body(8, [
    'LMD B110 / 国信 B130：软/硬光敏切换与日夜状态判定',
    '国信 B130：白光灯自动切换',
    'ir-cut 状态误判是普遍问题：状态上报错导致机芯切错滤光片，网页端画面异常',
    '光敏阈值必须现场实测，否则白天误切黑夜',
])

set_title(9, '收获 · 外设与模块', 'PERIPHERALS   &   MODULES')
set_body(9, [
    'XH T160：红外补光灯、激光测距两个模块对接移植',
    'KB T160：新增外设查询协议',
    '馥鸿 B130：双串口改单串口；抓机芯数据时发现对方下发数据异常，定位后推动修正',
    '协议类问题两步：先对齐帧，再补解析分支',
])

# ---------- 3. 更新方向命名 ----------
def replace_text(slide_idx, old, new):
    s = prs.slides[slide_idx]
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            txt = ''.join(r.text for r in p.runs)
            if old in txt:
                p.runs[0].text = txt.replace(old, new)
                for r in p.runs[1:]:
                    r.text = ''
                print('  S%-2d %r -> %r' % (slide_idx + 1, old, new))
                return True
    return False


replace_text(1, '电机 / OLED / 电池 / 日夜 / 方法',
             '电机 / OLED / 电池 / 日夜 / 外设')
replace_text(3, '日夜与灯光、协议定制', '日夜与灯光、外设与模块')
replace_text(4, '协议与定制：KB T160 查询协议、激光测距红外灯模块对接、馥鸿 B130 串口改造',
             '外设与模块：XH T160 红外补光灯 / 激光测距对接、KB T160 查询协议、馥鸿 B130 串口改造')

# ---------- 4. 重编页码 ----------
total = len(prs.slides)
fixed = 0
for i, sl in enumerate(prs.slides, 1):
    for sh in sl.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        if '/' in t and len(t) < 12 and t.replace('/', '').replace(' ', '').isdigit():
            p = sh.text_frame.paragraphs[0]
            p.runs[0].text = '%02d / %d' % (i, total)
            for r in p.runs[1:]:
                r.text = ''
            fixed += 1
print('页码已重编 %d 处，共 %d 页' % (fixed, total))

import os
DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v8.pptx', '_v9.pptx')
    prs.save(DST)
    print('v8 被占用(可能在 PowerPoint 里打开)，已改存为 v9')
print('已保存:', DST)
