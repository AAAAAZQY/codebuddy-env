# -*- coding: gbk -*-
"""按修订意见修改述职 PPT，另存为 v8（保留 v7 原件）。"""
import io
import sys

from pptx import Presentation

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v7.pptx'
DST = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v8.pptx'

prs = Presentation(SRC)


def para(sno, shape_idx, para_idx):
    return prs.slides[sno - 1].shapes[shape_idx].text_frame.paragraphs[para_idx]


def set_para(sno, shi, pi, expect, new):
    """整段替换: 文本全部放在第一个 run 上, 其余 run 清空(保留首个 run 的格式)。"""
    p = para(sno, shi, pi)
    cur = ''.join(r.text for r in p.runs)
    assert cur == expect, 'S%d sh%d p%d 期望 %r 实际 %r' % (sno, shi, pi, expect, cur)
    p.runs[0].text = new
    for r in p.runs[1:]:
        r.text = ''
    print('S%-2d sh%-2d p%-2d  OK  %s' % (sno, shi, pi, new))


def set_run(sno, shi, pi, ridx, expect, new):
    p = para(sno, shi, pi)
    assert p.runs[ridx].text == expect, \
        'S%d sh%d p%d run%d 期望 %r 实际 %r' % (sno, shi, pi, ridx, expect, p.runs[ridx].text)
    p.runs[ridx].text = new


# ---- 1. 目录: 显示 -> OLED, 光敏 -> 日夜 ----
set_para(2, 11, 0, '电机 / 显示 / 电源 / 光敏 / 方法',
         '电机 / OLED / 电源 / 日夜 / 方法')

# ---- 2. 第5页: IRCUT画面异常 -> 网页端画面异常(ir-cut 状态机) ----
set_run(5, 5, 3, 2,
        '与灯光：LMD B110软硬光敏切换、国信 B130 白光灯自动切换',
        '与灯光：LMD B110 软/硬光敏切换、国信 B130 白光灯自动切换')
set_run(5, 5, 3, 3, '、', '、网页端画面异常（')
set_run(5, 5, 3, 4, 'IRCUT', 'ir-cut')
set_run(5, 5, 3, 5, '画面异常', ' 状态机）')
print('S5  sh5  p3    OK  ' + ''.join(r.text for r in para(5, 5, 3).runs))

# ---- 3. 第8页: 显示 -> OLED ----
set_para(8, 2, 0, '收获 · 显示与电源', '收获 · OLED 与电源')
set_para(8, 3, 0, 'DISPLAY   &   POWER', 'OLED   &   POWER')

# ---- 4. 第9页: 光敏 -> 日夜, 并补上 ir-cut 的机理 ----
set_para(9, 2, 0, '收获 · 光敏与协议', '收获 · 日夜与协议')
set_para(9, 3, 0, 'LIGHT   &   PROTOCOL', 'DAY-NIGHT   &   PROTOCOL')
set_run(9, 5, 2, 1, 'LMD B110 / 国信 B130 ：', 'LMD B110 / 国信 B130：')
set_run(9, 5, 2, 2, '软硬', '软/硬')
set_run(9, 5, 2, 3, '光敏切换逻辑', '光敏切换、日夜状态判定、ir-cut 状态误报致网页端画面异常')
print('S9  sh5  p2    OK  ' + ''.join(r.text for r in para(9, 5, 2).runs))

prs.save(DST)
print('')
print('已保存:', DST)
