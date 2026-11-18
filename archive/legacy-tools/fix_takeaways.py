# -*- coding: gbk -*-
"""把 S7/S13 那条 11pt 的「·」小结换成 17pt 正式条目，并润色措辞。"""
import copy
import sys

from pptx import Presentation
from pptx.util import Pt

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v9.pptx'
prs = Presentation(P)


def find_body(idx):
    for sh in prs.slides[idx].shapes:
        if sh.has_text_frame and sh.text_frame.text.strip().startswith('—'):
            return sh
    return None


NEW = {
    6:  '能力沉淀：掌握伺服与步进电机的控制原理与调试方法，能独立完成参数整定与问题定位',
    12: '调试手段：在线调试、串口数据、示波器，先把现象量化，再判断是软件还是硬件',
}

for idx, text in NEW.items():
    body = find_body(idx)
    assert body is not None, 'S%d 未找到正文' % (idx + 1)
    tf = body.text_frame

    # 1) 删掉之前加的「·」小结段落
    removed = 0
    for p in list(tf.paragraphs):
        if p.runs and p.runs[0].text.strip().startswith('·'):
            p._p.getparent().remove(p._p)
            removed += 1

    # 2) 克隆一个正常的「—」条目作为模板，改文字
    tpl = None
    for p in tf.paragraphs:
        if p.runs and p.runs[0].text.strip().startswith('—') and len(p.runs) >= 2:
            tpl = copy.deepcopy(p._p)
    assert tpl is not None

    tf._txBody.append(tpl)
    from pptx.text.text import _Paragraph
    para = _Paragraph(tpl, tf)
    para.runs[0].text = '—  '
    para.runs[1].text = text
    for r in para.runs[2:]:
        r.text = ''
    print('S%-2d 删除 %d 条小结，新增 17pt 条目: %s' % (idx + 1, removed, text))

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v9.pptx', '_v10.pptx')
    prs.save(DST)
    print('v9 被占用，改存 v10')
print('已保存:', DST)
