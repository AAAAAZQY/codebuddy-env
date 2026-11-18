# -*- coding: gbk -*-
"""在 02 工作收获 章节开头插入「收获 · 能力与成长」一页。"""
import copy
import sys

from pptx import Presentation

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v9.pptx'
prs = Presentation(P)

# S6 是章节页「02 工作收获」，复制内容页 S7 作为新页，插在其后
src = prs.slides[6]
new = prs.slides.add_slide(src.slide_layout)
for sh in list(new.shapes):
    sh._element.getparent().remove(sh._element)
for sh in src.shapes:
    new.shapes._spTree.append(copy.deepcopy(sh._element))

ids = list(prs.slides._sldIdLst)
el = ids[-1]
prs.slides._sldIdLst.remove(el)
prs.slides._sldIdLst.insert(6, el)
print('已插入新页，总页数 %d' % len(prs.slides))

s = prs.slides[6]
# 标题
s.shapes[2].text_frame.paragraphs[0].runs[0].text = '收获 · 能力与成长'
s.shapes[3].text_frame.paragraphs[0].runs[0].text = 'GROWTH   &   CAPABILITY'

LINES = [
    '掌握伺服与步进电机的控制原理和调试方法，能独立做参数整定与问题定位',
    '熟悉云台固件整体架构与调试手段：在线调试、串口数据、示波器',
    '养成「先复现 → 查最近改动与逻辑时序 → 最后怀疑硬件」的排查顺序，能区分软硬件问题',
    '遇到不懂的主动请教，学会与同事沟通协作，问题推进更顺',
]

body = s.shapes[5]
paras = body.text_frame.paragraphs
print('正文原有段落 %d' % len(paras))

for i, txt in enumerate(LINES):
    p = paras[i]
    assert len(p.runs) >= 2
    p.runs[1].text = txt
    for r in p.runs[2:]:
        r.text = ''

# 多余段落整段删掉
for p in list(paras[len(LINES):]):
    p._p.getparent().remove(p._p)
print('正文现有段落 %d' % len(body.text_frame.paragraphs))

# 重编页码
total = len(prs.slides)
for i, sl in enumerate(prs.slides, 1):
    for sh in sl.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        if '/' in t and len(t) < 12 and t.replace('/', '').replace(' ', '').isdigit():
            para = sh.text_frame.paragraphs[0]
            para.runs[0].text = '%02d / %d' % (i, total)
            for r in para.runs[1:]:
                r.text = ''

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v9.pptx', '_v10.pptx')
    prs.save(DST)
    print('v9 被占用，改存 v10')
print('已保存:', DST, '共 %d 页' % total)
