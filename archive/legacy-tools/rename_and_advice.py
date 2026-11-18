# -*- coding: gbk -*-
"""姓名改为赵庆赟；三条建议合并为一条（云台预置位功能表纳入共享文档管理）。"""
import os
import sys

from pptx import Presentation
from pptx.util import Cm, Pt
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v13.pptx'
prs = Presentation(P)

OLD = '赵庆斌'
NEW = '赵庆赟'

# ---------- 1. 全局改名 ----------
n = 0
for s in prs.slides:
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        for para in sh.text_frame.paragraphs:
            for r in para.runs:
                if OLD in r.text:
                    r.text = r.text.replace(OLD, NEW)
                    n += 1
print('改名 %d 处' % n)

# ---------- 2. S17 只留一条建议 ----------
s17 = prs.slides[16]

# 找到三张卡片：矩形 + 顶部条 + 标题 + 正文
cards = []
for sh in s17.shapes:
    if 10.0 - 0.2 <= sh.top / 360000.0 <= 10.1 and sh.width / 360000.0 <= 9.5:
        cards.append(sh)
print('卡片相关形状 %d 个' % len(cards))

# 删掉第 2、3 张卡片（x 起点 >= 12cm 的矩形与文字）
keep_x = 2.6
removed = 0
for sh in list(s17.shapes):
    x = sh.left / 360000.0
    if x >= 12.0 and 9.9 <= sh.top / 360000.0 <= 14.5:
        sh._element.getparent().remove(sh._element)
        removed += 1
print('删除第 2、3 张卡片形状 %d 个' % removed)

# 剩下一张卡片加宽
for sh in s17.shapes:
    x = sh.left / 360000.0
    if abs(x - 2.6) < 0.3 and 9.9 <= sh.top / 360000.0 <= 10.2:
        sh.width = Cm(27.6)
    if abs(x - 3.2) < 0.3 and 11.4 <= sh.top / 360000.0 <= 11.6:
        sh.width = Cm(26.4)

# 改文字
for sh in s17.shapes:
    if not sh.has_text_frame:
        continue
    for para in sh.text_frame.paragraphs:
        t = ''.join(r.text for r in para.runs)
        if t.strip() == '建议一':
            para.runs[0].text = '建议'
            for r in para.runs[1:]:
                r.text = ''
            print('标题: 建议一 -> 建议')
        elif '整机联调自检清单' in t:
            para.runs[0].text = ('把云台预置位功能表也纳入共享文档管理，'
                                 '与机型参数、接口定义一起维护')
            for r in para.runs[1:]:
                r.text = ''
            print('正文: 已替换为预置位功能表建议')

prs.save(P)
print('已保存:', P)

# ---------- 3. 文件改名 ----------
newpath = P.replace('赵庆斌', NEW)
if newpath != P:
    try:
        os.rename(P, newpath)
        print('文件已改名:', newpath)
    except Exception as e:                          # noqa: BLE001
        print('文件改名失败(可能被占用):', e)
