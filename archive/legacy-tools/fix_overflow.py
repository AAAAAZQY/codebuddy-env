# -*- coding: gbk -*-
"""S11/S12 压缩到 5 条、修复丢失的符号，避免压到页脚。"""
import sys

from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v11.pptx'
prs = Presentation(P)

BODY = RGBColor(0x24, 0x33, 0x3B)
DASH = RGBColor(0xE9, 0x61, 0x71)


def body_of(idx):
    for sh in prs.slides[idx].shapes:
        if sh.has_text_frame and sh.text_frame.text.strip().startswith('—'):
            return sh
    raise AssertionError('S%d 找不到正文' % (idx + 1))


def set_bullet(para, text):
    runs = para.runs
    runs[0].text = '—  '
    runs[0].font.size = Pt(15.0)
    runs[0].font.color.rgb = DASH
    runs[1].text = text
    runs[1].font.size = Pt(17.0)
    runs[1].font.bold = False
    runs[1].font.color.rgb = BODY
    for r in runs[2:]:
        r.text = ''


PLAN = {
    10: [
        '硬件条件：无充电管理芯片、无 CHRG/STDBY 引脚，只有一路电池电压进 ADC，'
        '充电状态只能由软件判定',
        '放电：厂家曲线按 5 格间隔取点建表，先查单调性再插值，越界取端点',
        '充电判定三段式：进入看端压净涨、维持看去抖、退出看回落，不能只看绝对电压',
        '充电积分：CC 段按 I/(C×60) 折算，CV 段按 K×(100-SOC)；上界钳位到电压法读数',
        '能力沉淀：无硬件电流检测时，用端压趋势 + 分段积分做出可用的电量估算',
    ],
    11: [
        '问题：关机后软件不运行，这段时间的电量变化没有任何记录',
        '做法：EEPROM 存关机时的电压法值当基线，开机与当前值比较，误差相减抵消',
        '关键坑：充电中关机不能写基线，端压虚高会让下次开机误判「没充过电」',
        '兜底：魔数不符或越界直接用电压值；≥12.55V 按满电；掉电重启用区间法',
        '能力沉淀：用 EEPROM 存基线、按误差相减，解决掉电期间状态不可观测',
    ],
}

for idx, lines in PLAN.items():
    body = body_of(idx)
    tf = body.text_frame
    paras = list(tf.paragraphs)
    for i, p in enumerate(paras):
        if i < len(lines):
            set_bullet(p, lines[i])
        else:
            p._p.getparent().remove(p._p)
            print('S%-2d 删除多余段落 %d' % (idx + 1, i))
    print('S%-2d 现有 %d 条' % (idx + 1, len(tf.paragraphs)))

# 修掉全文里被 GBK 吃掉后变成 ? 的符号
fixed = 0
for s in prs.slides:
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        for para in sh.text_frame.paragraphs:
            for r in para.runs:
                if '?' in r.text:
                    before = r.text
                    r.text = (r.text.replace('100?SOC', '100-SOC')
                                    .replace('I?C', 'IIC'))
                    if r.text != before:
                        fixed += 1
                        print('  修正: %r -> %r' % (before[:40], r.text[:40]))
print('符号修正 %d 处' % fixed)

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v11.pptx', '_v12.pptx')
    prs.save(DST)
    print('v11 被占用，改存 v12')
print('已保存:', DST)
