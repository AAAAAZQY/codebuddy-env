# -*- coding: gbk -*-
"""口径改十余个 / 电量三层与效果 / 补一次失误 / 计划专业化 / 修多余空格。"""
import copy
import sys

from pptx import Presentation
from pptx.text.text import _Paragraph
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


def clone_para(para):
    return copy.deepcopy(para._p)


def append_bullet(tf, text, tpl_para):
    el = clone_para(tpl_para)
    tf._txBody.append(el)
    set_bullet(_Paragraph(el, tf), text)


def insert_bullet_after(para, text):
    el = clone_para(para)
    para._p.addnext(el)
    set_bullet(_Paragraph(el, para._parent), text)


def rewrite(idx, lines, where='append'):
    body = body_of(idx)
    tf = body.text_frame
    paras = list(tf.paragraphs)

    if where == 'insert1' and len(paras) >= 2:
        # 在第 2 条位置插入一条
        insert_bullet_after(paras[0], lines[1])
        rest = list(tf.paragraphs)[2:]
        for p, txt in zip(rest, lines[2:]):
            set_bullet(p, txt)
        print('S%-2d 插入后共 %d 条' % (idx + 1, len(tf.paragraphs)))
        return

    for i, p in enumerate(paras):
        if i < len(lines):
            set_bullet(p, lines[i])
        else:
            p._p.getparent().remove(p._p)
    tpl = tf.paragraphs[-1]
    for extra in lines[len(paras):]:
        append_bullet(tf, extra, tpl)
    print('S%-2d 现有 %d 条' % (idx + 1, len(tf.paragraphs)))


# ---------- 1. S4 口径与 KPI ----------
s4 = prs.slides[3]
for sh in s4.shapes:
    if not sh.has_text_frame:
        continue
    for para in sh.text_frame.paragraphs:
        txt = ''.join(r.text for r in para.runs)
        if '17个项目' in txt:
            para.runs[0].text = txt.replace('17个项目', '十余个项目')
            for r in para.runs[1:]:
                r.text = ''
            print('S4 项目口径 -> 十余个')
        elif txt.strip() == '17':
            para.runs[0].text = '十余'
            for r in para.runs[1:]:
                r.text = ''
            print('S4 KPI 数字 17 -> 十余')

# ---------- 2. 修多余空格（— 后面三个空格）----------
n = 0
for s in prs.slides:
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        for para in sh.text_frame.paragraphs:
            for r in para.runs:
                if r.text and r.text.startswith('—') and r.text.lstrip('—') != r.text:
                    lead = r.text[:len(r.text) - len(r.text.lstrip('—'))]
                    body_txt = r.text.lstrip('—')
                    spaces = len(body_txt) - len(body_txt.lstrip(' '))
                    if spaces > 2:
                        r.text = '—' + '  ' + body_txt.lstrip(' ')
                        n += 1
print('多余空格修正 %d 处' % n)

# ---------- 3. S11 电量：三层处理 ----------
rewrite(10, [
    '硬件条件：无充电管理芯片、无 CHRG/STDBY 引脚，只有一路电池电压进 ADC',
    '整体分三层：放电靠电压查表，充电靠分段积分，掉电靠 EEPROM 记账',
    '放电：厂家曲线按 5 格间隔取点建表，先查单调性再插值，越界取端点',
    '充电判定三段式：进入看端压净涨、维持看去抖、退出看回落',
    '充电积分：CC 段按 I/(C×60) 折算，CV 段按 K×(100-SOC)；上界钳位到电压法读数',
    '能力沉淀：无硬件电流检测时，用端压趋势 + 分段积分做出可用的电量估算',
])

# ---------- 4. S12 关机记账 + 效果量化 ----------
rewrite(11, [
    '问题：关机后软件不运行，这段时间的电量变化没有任何记录',
    '做法：EEPROM 存关机时的电压法值当基线，开机与当前值比较，误差相减抵消',
    '关键坑：充电中关机不能写基线，端压虚高会让下次开机误判「没充过电」',
    '兜底：魔数不符或越界直接用电压值；≥12.55V 按满电；掉电重启用区间法',
    '效果：从「带载乱跳、充电虚高」到误差收敛到 ±5% 以内，重启跳变由 ±20% 压到 ±5%',
    '能力沉淀：用 EEPROM 存基线、按误差相减，解决掉电期间状态不可观测',
])

# ---------- 5. S13 补一次判断失误 ----------
rewrite(12, [
    '排查顺序：复现现象 → 查最近改动 → 查逻辑与时序 → 查标定 → 最后怀疑硬件',
    '一次判断失误：申威 T160 最初判为限位问题，周报时组长提醒后复查，实为自检找不到光耦',
    '不懂就问：协议与时序拿不准，先和硬件、测试同事对齐再动手',
    '交付习惯：最小改动、可回退、不碰安全阈值与协议码',
    '调试手段：在线调试、串口数据、示波器，先把现象量化，再判断是软件还是硬件',
], where='insert1')

# ---------- 6. S15 工作计划专业化 ----------
rewrite(14, [
    '短期（1~3 月）：完成电流环带宽标定，输出可复用的整定步骤，先在 1~2 个机型验证',
    '短期（1~3 月）：参与稳像调参，量化抖动指标（阶跃响应、抖动 RMS），留调参记录',
    '中期（3~6 月）：在控制模块引入 RTOS 任务划分，给出优先级与时序预算的可移植方案',
    '中期（3~6 月）：完成模糊 PID 的离线仿真与台架验证，与固定参数方案做量化对比',
    '长期（6~12 月）：自检、标定、参数版本化沉淀为平台模块，支持新机型快速导入',
])

DST = P
try:
    prs.save(DST)
except PermissionError:
    DST = P.replace('_v11.pptx', '_v12.pptx')
    prs.save(DST)
    print('v11 被占用，改存 v12')
print('已保存:', DST)
