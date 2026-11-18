# -*- coding: gbk -*-
"""第三轮: 电源 -> 电池, 并把 S8 的“与电源”去掉(该页无电池内容)。"""
import sys

from pptx import Presentation

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v8.pptx'
prs = Presentation(P)


def replace_in_para(para, old, new):
    """在段落内跨 run 安全替换: 拼成整串后若命中, 全部写回第一个 run。"""
    txt = ''.join(r.text for r in para.runs)
    if old not in txt:
        return False
    newtxt = txt.replace(old, new)
    para.runs[0].text = newtxt
    for r in para.runs[1:]:
        r.text = ''
    return True


TARGETS = [
    ('电源与电量', '电池与电量'),      # S4 / S5
    ('电机 / OLED / 电源 / 日夜 / 方法', '电机 / OLED / 电池 / 日夜 / 方法'),   # S2 目录
    ('收获 · OLED 与电源', '收获 · OLED 显示'),                                  # S8 标题
    ('OLED   &   POWER', 'OLED   DISPLAY'),                                     # S8 英文
]

count = 0
for si, slide in enumerate(prs.slides, 1):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        for para in sh.text_frame.paragraphs:
            for old, new in TARGETS:
                if replace_in_para(para, old, new):
                    print('S%-2d  %r -> %r' % (si, old, new))
                    count += 1

prs.save(P)
print('')
print('共修改 %d 处，已保存' % count)
