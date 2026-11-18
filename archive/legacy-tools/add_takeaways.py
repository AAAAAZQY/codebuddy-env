# -*- coding: gbk -*-
"""在 S7、S13 末尾补一条「·」小结，落 ① 和 ② 两条收获。"""
import copy
import sys

from pptx import Presentation

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v9.pptx'
prs = Presentation(P)


def find_body(slide_idx):
    """找到以 — 开头的正文文本框。"""
    for sh in prs.slides[slide_idx].shapes:
        if sh.has_text_frame and sh.text_frame.text.strip().startswith('—'):
            return sh
    return None


# 用 S9 的「·」小结段落做模板（14pt 破折号 + 11pt 正文）
template = None
for sh in prs.slides[8].shapes:
    if not sh.has_text_frame:
        continue
    for p in sh.text_frame.paragraphs:
        if p.runs and p.runs[0].text.strip().startswith('·'):
            template = copy.deepcopy(p._p)
            break
    if template is not None:
        break
assert template is not None, '未找到「·」模板段落'
print('已取得「·」模板')

TASKS = [
    (6,  '掌握伺服与步进电机的控制原理和调试方法，能独立做参数整定与问题定位'),
    (12, '熟悉云台固件整体架构与调试手段：在线调试、串口数据、示波器'),
]

for idx, text in TASKS:
    body = find_body(idx)
    assert body is not None, 'S%d 未找到正文' % (idx + 1)
    new_p = copy.deepcopy(template)
    body.text_frame._txBody.append(new_p)
    # 取新加的段落（最后一个）
    from pptx.text.text import _Paragraph
    para = _Paragraph(new_p, body.text_frame)
    assert len(para.runs) >= 2
    para.runs[1].text = text
    for r in para.runs[2:]:
        r.text = ''
    print('S%-2d 已追加: ·  %s' % (idx + 1, text))

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v9.pptx', '_v10.pptx')
    prs.save(DST)
    print('v9 被占用，改存 v10')
print('已保存:', DST)
