# -*- coding: gbk -*-
"""生成述职报告口播稿 docx。用法: python gen_speech_doc.py [输出路径]"""
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = (sys.argv[1] if len(sys.argv) > 1
       else r'C:\Users\myages2026\Desktop\试用期述职报告_口播稿_赵庆赟.docx')

TITLE = '试用期述职报告 · 口播稿'
SUBTITLE = '汇报人：赵庆赟    研发部 · 单片机软件    汇报对象：组长、人事部'
NOTE = '全文约 4 分钟，按 PPT 页码顺序讲；页码仅为对应位置，不必念出。'

SECTIONS = [
    ('一、开场（第 1 页，约 15 秒）',
     '组长、人事老师好，我是研发部单片机软件的赵庆赟。这三个月我主要做云台固件相关的工作，'
     '下面分四块汇报。'),

    ('二、工作概览（第 4~5 页，约 30 秒）',
     '三个月跟了十余个项目，涉及五个方向：电机与云台、OLED 显示、电池电量、日夜灯光、外设模块。'
     '工作分三类：老产品问题修复、客户定制、新功能开发。代表性问题是云台的丢步撞头、'
     '球芯全系开机花屏、SM S100 的电量显示、ir-cut 误切导致的画面异常，以及三个模块的移植。'
     '下面挑重点说结果。'),

    ('三、电机与云台（第 7 页，约 45 秒）',
     '这是我投入最多的一块，主要是云台丢步和撞头两类老问题。几个主力机型上分别定位到根因：'
     '有的是云台头部负载偏重、电机力矩不足，有的是机械行程标定偏大、自检扫不到光耦；'
     '还有结构特殊扫不到光耦的，我加了一个直接发脉冲的函数解决。'
     'U 款球机独立完成了速度曲线整定，做到不丢步、不撞头、转速平稳。'
     '这类问题现在我可以独立定位，不用人带。'),

    ('四、其余三个方向（第 8~10 页，约 30 秒）',
     'OLED 主要是球芯全系的开机花屏和个别开机 Y 轴反转，根因在初始化顺序和上电时序。'
     '日夜灯光做了软硬光敏切换和白光灯自动切换。'
     '外设完成了三个模块移植，另外把一台机型的双串口改成单串口，'
     '解决了客供机芯下发数据导致云台异常的问题。'),

    ('五、电量专项（第 11 页，约 35 秒）',
     'SM S100 这块硬件上没有充电检测，只有一路电压进 ADC，电量只能靠软件估。'
     '我用电压查表做放电、分段积分做充电、EEPROM 记账解决掉电丢失，'
     '另外加了数据异常时回退电压法的兜底。'
     '结论是没有电流采样，也能做出可交付的电量估算。'),

    ('六、方法与协作（第 12 页，约 35 秒）',
     '排查上我现在固定按“复现现象、查最近改动、查逻辑与时序、查标定、最后怀疑硬件”的顺序走。'
     '也讲一次失误：申威 T160 最初我判成限位问题，是组长在周报时提醒我复查，实际是自检没找到光耦。'
     '从那以后我要求结论必须带证据。交付上坚持最小改动、可回退、不碰安全阈值和协议码。'),

    ('七、工作计划（第 14 页，约 35 秒）',
     '短期一到三个月，把伺服参数整定吃透，整机问题能独立排查；'
     '中期三到六个月，做模糊 PID，让云台在变负载下速度环保持稳定；'
     '长期六到十二个月，学 RTOS 的任务调度与优先级设计，先在控制模块试点，用实测数据评估收益。'),

    ('八、小结与建议（第 16 页，约 40 秒）',
     '三个月，我完成了从协助到独立跟进项目的过渡，能独立定位问题、承接定制需求、完成新功能。'
     '不足是硬件底层理解还不够，跨软硬边界的问题还得先找人确认，这块后面补。'
     '建议把云台预置位功能表放进共享文档统一管理，新同事接手和跨项目复用时能省很多事。'
     '感谢组长带教和人事老师的支持。'),

    ('九、结尾（第 17 页，约 10 秒）',
     '汇报到这里，请两位批评指正，谢谢。'),
]

BLACK = RGBColor(0x00, 0x00, 0x00)
GREY = RGBColor(0x59, 0x59, 0x59)


def set_run_font(run, cn_font, size_pt, bold=False, color=BLACK):
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = rpr.makeelement(qn('w:rFonts'), {})
        rpr.append(rf)
    rf.set(qn('w:eastAsia'), cn_font)
    rf.set(qn('w:ascii'), 'Times New Roman')
    rf.set(qn('w:hAnsi'), 'Times New Roman')


def first_line_chars(par, chars=200):
    par.paragraph_format.first_line_indent = Pt(24)
    ppr = par._element.get_or_add_pPr()
    ind = ppr.find(qn('w:ind'))
    if ind is None:
        ind = ppr.makeelement(qn('w:ind'), {})
        ppr.append(ind)
    ind.set(qn('w:firstLineChars'), str(chars))


doc = Document()

sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(1.27)
sec.right_margin = Cm(1.27)
sec.top_margin = Cm(2.54)
sec.bottom_margin = Cm(2.54)

normal = doc.styles['Normal']
normal.font.name = 'Times New Roman'
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

# 标题
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(6)
set_run_font(p.add_run(TITLE), '黑体', 22, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
set_run_font(p.add_run(SUBTITLE), '宋体', 10.5, color=GREY)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(18)
set_run_font(p.add_run(NOTE), '宋体', 10.5, color=GREY)

for head, body in SECTIONS:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    set_run_font(p.add_run(head), '黑体', 14, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    first_line_chars(p)
    set_run_font(p.add_run(body), '宋体', 12)

doc.save(OUT)
print('saved: %s' % OUT)
