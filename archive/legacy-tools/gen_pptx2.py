# -*- coding: cp936 -*-
"""试用期述职报告 v2：多版式、深浅交替、内容加厚（13 页）"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

FONT = '微软雅黑'
DARK = RGBColor(0x0E, 0x2A, 0x47)
DARK2 = RGBColor(0x16, 0x3B, 0x60)
BLUE = RGBColor(0x1E, 0x6F, 0xBA)
SKY = RGBColor(0x3E, 0x9A, 0xDD)
ORANGE = RGBColor(0xE0, 0x7A, 0x2F)
TEXT = RGBColor(0x35, 0x3C, 0x45)
SUB = RGBColor(0x6B, 0x74, 0x81)
LINE = RGBColor(0xD8, 0xDF, 0xE8)
BG = RGBColor(0xF4, 0xF7, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 12


def set_font(run, size, bold=False, color=TEXT, name=FONT):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.color.rgb = color
    f.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', name)


def shape(slide, kind, x, y, w, h, fill, line=None, lw=0.75, radius=0.08):
    sh = slide.shapes.add_shape(kind, x, y, w, h)
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    return sh


def text(slide, x, y, w, h, s, size, bold=False, color=TEXT,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.25):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    lines = s.split('\n')
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run()
        r.text = ln
        set_font(r, size, bold, color)
    return tb


def bullets(slide, x, y, w, h, items, size=17, gap=12, spacing=1.35, bullet_color=BLUE):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, it in enumerate(items):
        level = 0
        s = it
        if isinstance(it, tuple):
            s, level = it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.line_spacing = spacing
        rb = p.add_run()
        rb.text = '■   ' if level == 0 else '·   '
        set_font(rb, 13 if level == 0 else 12, False,
                 bullet_color if level == 0 else SUB)
        rt = p.add_run()
        rt.text = s
        set_font(rt, size if level == 0 else size - 3,
                 False, TEXT if level == 0 else SUB)
    return tb


def header(slide, title, en, page, dark=False):
    c_title = WHITE if dark else DARK
    c_en = SKY if dark else SUB
    c_pg = RGBColor(0x55, 0x6B, 0x82) if dark else RGBColor(0xC3, 0xCD, 0xDA)
    shape(slide, MSO_SHAPE.RECTANGLE, Inches(0.82), Inches(0.72), Inches(0.07), Inches(0.44), SKY)
    text(slide, Inches(1.02), Inches(0.64), Inches(9.0), Inches(0.55), title, 26, True, c_title)
    text(slide, Inches(1.03), Inches(1.12), Inches(7.0), Inches(0.3), en, 10.5, False, c_en)
    text(slide, Inches(11.0), Inches(0.7), Inches(1.5), Inches(0.4),
         '%02d / %d' % (page, TOTAL), 11, False, c_pg, PP_ALIGN.RIGHT)
    shape(slide, MSO_SHAPE.RECTANGLE, Inches(0.82), Inches(1.5), Inches(11.7),
          Inches(0.01), RGBColor(0x2A, 0x4A, 0x6B) if dark else LINE)


def footer(slide, dark=False):
    text(slide, Inches(0.82), Inches(7.0), Inches(8.0), Inches(0.28),
         'MYTECH 名扬时代  |  试用期述职报告  |  赵庆斌', 9.5, False,
         RGBColor(0x55, 0x6B, 0x82) if dark else SUB)


def page(dark=False):
    s = prs.slides.add_slide(BLANK)
    shape(s, MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height,
          DARK if dark else WHITE)
    return s


# ================= 1 封面 =================
s = page(True)
shape(s, MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.3), prs.slide_height, BLUE)
shape(s, MSO_SHAPE.RECTANGLE, Inches(7.9), 0, Inches(5.44), prs.slide_height, DARK2)
text(s, Inches(8.5), Inches(2.3), Inches(4.4), Inches(0.4), 'CONTENTS  OVERVIEW', 10.5, False, SKY)
for i, (n, t) in enumerate([('01', '试用期回顾'), ('02', '工作收获'), ('03', '工作计划'), ('04', '总结与建议')]):
    yy = Inches(2.85 + i * 0.82)
    text(s, Inches(8.5), yy, Inches(0.7), Inches(0.4), n, 17, True, ORANGE)
    text(s, Inches(9.1), yy, Inches(3.4), Inches(0.4), t, 17, True, WHITE)
shape(s, MSO_SHAPE.RECTANGLE, Inches(1.4), Inches(2.5), Inches(1.1), Inches(0.06), SKY)
text(s, Inches(1.4), Inches(2.8), Inches(6.0), Inches(1.0), '试用期述职报告', 44, True, WHITE)
text(s, Inches(1.42), Inches(3.92), Inches(6.0), Inches(0.4), 'PROBATION   WORK   REVIEW', 12, False, SKY)
text(s, Inches(1.42), Inches(4.6), Inches(6.0), Inches(1.4),
     '汇报人：赵庆斌\n研发部 · 单片机软件\n入职日期：2026.8.3      汇报日期：2026.10.28', 13, False,
     RGBColor(0xC9, 0xD6, 0xE4), spacing=1.9)

# ================= 2 关键数字 =================
s = page(True)
header(s, '三个月的工作量', 'AT   A   GLANCE', 2, dark=True)
stats = [('17', '个项目', '问题修复与定制开发'), ('5', '个方向', '电机 / 显示 / 电源 / 光敏 / 协议'),
         ('3', '类工作', '修复 · 定制 · 新功能'), ('2', '个模块', '激光测距 / 补光灯移植')]
for i, (num, label, desc) in enumerate(stats):
    x = Inches(0.85 + i * 3.02)
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.15), Inches(2.82), Inches(2.75), DARK2)
    text(s, x + Inches(0.3), Inches(2.45), Inches(2.2), Inches(0.9), num, 44, True, ORANGE)
    text(s, x + Inches(0.3), Inches(3.42), Inches(2.2), Inches(0.4), label, 16, True, WHITE)
    text(s, x + Inches(0.3), Inches(3.92), Inches(2.25), Inches(0.8), desc, 10.5, False,
         RGBColor(0xA8, 0xBC, 0xD2), spacing=1.45)
text(s, Inches(0.85), Inches(5.35), Inches(11.6), Inches(0.9),
     '时间跨度 2026.8.3 — 2026.10.28　｜　工作方式：接需求 → 理清方案 → 定位或实现 → 自测交付', 12.5, False,
     RGBColor(0xA8, 0xBC, 0xD2))
footer(s, dark=True)

# ================= 3 三类工作 =================
s = page(False)
header(s, '三类工作', 'THREE   TYPES   OF   WORK', 3)
cols = [
    ('问题修复', '占大多数', ['申盛 T160：低速丢步、自检撞头',
                          '海洋王 60d：画面异常（全系共性）',
                          '球芯：电源板开机花屏',
                          '5100 森美：电量来回跳'], BLUE),
    ('定制化项目', '客户/机型差异', ['U 款球机：对接第三方零位机芯',
                                 '赣鸿 B130：双串口改单串口',
                                 'k13 T160：新增查询协议 + 垂直电机跟随',
                                 '国传信 B130：白光灯自动切换'], SKY),
    ('新功能开发', '从零到可用', ['电量管理：充电曲线积分 + 充电检测 + OSD 显示',
                             '激光测距模块接入',
                             '红外补光灯模块接入'], ORANGE),
]
for i, (t, sub, items, color) in enumerate(cols):
    x = Inches(0.85 + i * 3.95)
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.85), Inches(3.7), Inches(4.7), BG)
    shape(s, MSO_SHAPE.RECTANGLE, x, Inches(1.85), Inches(3.7), Inches(0.08), color)
    text(s, x + Inches(0.28), Inches(2.1), Inches(3.2), Inches(0.4), t, 17, True, DARK)
    text(s, x + Inches(0.28), Inches(2.52), Inches(3.2), Inches(0.3), sub, 10, False, SUB)
    shape(s, MSO_SHAPE.RECTANGLE, x + Inches(0.28), Inches(2.9), Inches(3.1), Inches(0.008), LINE)
    bb = s.shapes.add_textbox(x + Inches(0.28), Inches(3.05), Inches(3.15), Inches(3.3))
    tf = bb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for j, it in enumerate(items):
        p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        p.space_after = Pt(11)
        p.line_spacing = 1.35
        rb = p.add_run()
        rb.text = '· '
        set_font(rb, 12, False, color)
        rt = p.add_run()
        rt.text = it
        set_font(rt, 11.5, False, TEXT)
footer(s)

# ================= 4 收获·电机与云台 =================
s = page(False)
header(s, '收获 · 电机与云台', 'MOTOR   &   GIMBAL', 4)
bullets(s, Inches(0.85), Inches(1.82), Inches(7.5), Inches(4.9), [
    'U 款球机定制对接：第三方零位机芯（VBM-5100）报文对不上，先抓串口逐帧对齐格式与时序，再按零位脉冲修正电机零点，实现上电自动找零',
    '申盛 T160：低速丢步与自检撞头，定位到限位与零点偏差使行程被提前截断，调整电机参数与加减速曲线后恢复',
    'PM 球机：自检撞头与角度不准，重新核对行程与零点后修正',
    '5d6750：完成精度与速度测试，形成可复现的测试方法',
], size=15.5, gap=14)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.62), Inches(1.85), Inches(3.9), Inches(4.6), BG)
shape(s, MSO_SHAPE.RECTANGLE, Inches(8.62), Inches(1.85), Inches(3.9), Inches(0.08), ORANGE)
text(s, Inches(8.9), Inches(2.12), Inches(3.3), Inches(0.35), '运动类问题的排查顺序', 13, True, DARK)
steps = ['先看限位：行程是否被夹紧提前截断',
         '再看零点：回零是否准确、是否被滑行影响',
         '最后看曲线：加减速与刹车距离是否匹配负载',
         '三步排除后才怀疑电机本体或驱动']
for i, st in enumerate(steps):
    y = Inches(2.62 + i * 0.85)
    shape(s, MSO_SHAPE.OVAL, Inches(8.92), y + Inches(0.04), Inches(0.28), Inches(0.28), SKY)
    text(s, Inches(8.92), y + Inches(0.05), Inches(0.28), Inches(0.28), str(i + 1), 9.5, True, WHITE, PP_ALIGN.CENTER)
    text(s, Inches(9.32), y, Inches(3.0), Inches(0.75), st, 10.5, False, TEXT, spacing=1.4)
footer(s)

# ================= 5 收获·显示与电源 =================
s = page(False)
header(s, '收获 · 显示与电源', 'DISPLAY   &   POWER', 5)
bullets(s, Inches(0.85), Inches(1.82), Inches(7.5), Inches(4.9), [
    '海洋王 6126b：电源板屏幕 y 板反转，定位为初始化顺序问题，调整上电与显示方向配置后恢复',
    '球芯全系：电源板开机花屏，判断为上电时序与刷新顺序问题，统一处理后全系回归正常',
    '海洋王 60d：画面异常，先判断为全系共性问题再统一解决，避免逐台当个案修',
    '5100 森美：OLED 开机花屏与缺 CU 键，定位到初始化顺序与按键扫描时序冲突',
], size=15.5, gap=14)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.62), Inches(1.85), Inches(3.9), Inches(4.6), BG)
shape(s, MSO_SHAPE.RECTANGLE, Inches(8.62), Inches(1.85), Inches(3.9), Inches(0.08), SKY)
text(s, Inches(8.9), Inches(2.12), Inches(3.3), Inches(0.35), '花屏 / 反显的三类根因', 13, True, DARK)
causes = [('初始化顺序', '上电初始化没完成就刷新'),
          ('刷新节流', '刷新过快或与写显存冲突'),
          ('方向与配置', '显示方向、y 板配置错位')]
for i, (h1, d1) in enumerate(causes):
    y = Inches(2.62 + i * 1.05)
    text(s, Inches(8.92), y, Inches(3.2), Inches(0.3), h1, 11.5, True, BLUE)
    text(s, Inches(8.92), y + Inches(0.32), Inches(3.2), Inches(0.5), d1, 10, False, SUB, spacing=1.4)
text(s, Inches(8.92), Inches(5.78), Inches(3.2), Inches(0.5),
     '共性优先：一个现象出现在多台，先按系统性问题查', 10, False, ORANGE, spacing=1.4)
footer(s)

# ================= 6 电量管理 =================
s = page(False)
header(s, '专项 · 电量管理', 'POWER   MANAGEMENT', 6)
flow = [('充电曲线', '按曲线拟合电压-电量关系'), ('积分累计', '对充电过程积分算剩余电量'),
        ('充放电检测', '识别插入/拔出与充放电状态'), ('OSD 输出', '在 OSD 层显示百分比与充电指示')]
for i, (h1, d1) in enumerate(flow):
    x = Inches(0.85 + i * 3.02)
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.9), Inches(2.6), Inches(1.55), BG)
    shape(s, MSO_SHAPE.RECTANGLE, x, Inches(1.9), Inches(2.6), Inches(0.07), BLUE)
    text(s, x + Inches(0.22), Inches(2.12), Inches(2.2), Inches(0.35), h1, 13, True, DARK)
    text(s, x + Inches(0.22), Inches(2.55), Inches(2.2), Inches(0.8), d1, 9.5, False, SUB, spacing=1.4)
    if i < 3:
        text(s, x + Inches(2.66), Inches(2.45), Inches(0.35), Inches(0.4), '→', 16, True, SKY)
bullets(s, Inches(0.85), Inches(3.85), Inches(11.6), Inches(2.6), [
    '难点：电量来回跳 —— 采样端做滤波、显示端做刷新节流，避免读数抖动直接反映到 OSD',
    '覆盖：低电保护阈值、充电指示灯状态、关机前电量保存',
    '验证：满充 → 放电 → 边充边用 三种场景分别记录曲线，与实测容量对比',
], size=15, gap=13)
footer(s)

# ================= 7 收获·光敏与协议 =================
s = page(False)
header(s, '收获 · 光敏与协议', 'LIGHT   &   PROTOCOL', 7)
bullets(s, Inches(0.85), Inches(1.82), Inches(7.5), Inches(4.9), [
    'k13 T160：新增 my 查询协议（帧格式、超时重发），并增加垂直电机跟随，解决变倍后画面上下偏移',
    '标配 5 寸：特殊预置位（巡航等）无法调用、云台报警信息查不到，补齐协议解析分支',
    'LMD B1105C：新增软 / 硬光敏切换逻辑，两种判据可切',
    '国传信 B130：增加白光灯自动切换模式',
    '5SKS / BS7：修复虚标与自动翻转异常，并按现场光照调整光敏切换阈值',
], size=15, gap=12)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.62), Inches(1.85), Inches(3.9), Inches(4.6), BG)
shape(s, MSO_SHAPE.RECTANGLE, Inches(8.62), Inches(1.85), Inches(3.9), Inches(0.08), ORANGE)
text(s, Inches(8.9), Inches(2.12), Inches(3.3), Inches(0.35), '协议类问题的两步', 13, True, DARK)
text(s, Inches(8.92), Inches(2.68), Inches(3.2), Inches(0.3), '第一步 · 对齐帧', 11.5, True, BLUE)
text(s, Inches(8.92), Inches(3.0), Inches(3.2), Inches(0.9),
     '抓原始报文，确认帧头、长度、校验与字节序，先能稳定收全一帧', 10, False, SUB, spacing=1.45)
text(s, Inches(8.92), Inches(3.95), Inches(3.2), Inches(0.3), '第二步 · 补分支', 11.5, True, BLUE)
text(s, Inches(8.92), Inches(4.27), Inches(3.2), Inches(0.9),
     '在解析状态机里补齐命令分支与应答，逐条命令单独验证', 10, False, SUB, spacing=1.45)
text(s, Inches(8.92), Inches(5.45), Inches(3.2), Inches(0.8),
     '阈值类问题：必须按现场光照实测，曲线达标不代表现场不误切', 10, False, ORANGE, spacing=1.45)
footer(s)

# ================= 8 收获·方法与协作 =================
s = page(True)
header(s, '收获 · 方法与协作', 'METHOD   &   TEAMWORK', 8, dark=True)
text(s, Inches(0.85), Inches(1.75), Inches(5.6), Inches(0.35), '排查方法', 14, True, SKY)
bullets(s, Inches(0.85), Inches(2.2), Inches(5.5), Inches(3.9), [
    '固定顺序：复现 → 查最近改动 → 查逻辑与时序 → 查标定 → 最后怀疑硬件',
    '给结论而不是给猜测：66d 尾线不能查询数据，逐层排除后确认是硬件问题',
    '误差先分类：成比例查标定，随次数累积查丢步，随速度变化查触发延迟',
    '补救有边界：限定触发条件、记录风险、留回退手段',
], size=12, gap=10)
shape(s, MSO_SHAPE.RECTANGLE, Inches(6.72), Inches(1.85), Inches(0.01), Inches(4.5), RGBColor(0x2A, 0x4A, 0x6B))
text(s, Inches(7.0), Inches(1.75), Inches(5.5), Inches(0.35), '协作与习惯', 14, True, SKY)
bullets(s, Inches(7.0), Inches(2.2), Inches(5.45), Inches(3.9), [
    '不懂就问：拿不准的协议与时序，先和硬件、测试同事对齐再动手',
    '动手前先确认边界：哪些能改、哪些是安全阈值不能碰',
    '交付前自测：关键场景（上电、断电、边界值）自己先跑一遍',
    '最小改动、可回退、可追溯，改动留对比记录',
], size=12, gap=10)
footer(s, dark=True)

# ================= 9 配件模块移植 =================
s = page(False)
header(s, '配件模块移植', 'MODULE   PORTING', 9)
bullets(s, Inches(0.85), Inches(1.82), Inches(7.4), Inches(2.6), [
    '激光测距：55AA 帧解析、单次 / 连续测距、命令透传与应答回显',
    '红外补光灯：开关、亮度、角度随变倍联动、上电强制关灯保护',
], size=15.5, gap=13)
text(s, Inches(0.85), Inches(3.35), Inches(7.4), Inches(0.35), '移植五步', 14, True, BLUE)
steps5 = ['读懂原工程的控制流程与状态机', '找到接入点：串口、命令端口、上电流程',
          '只加不改：配置项追加、不改现有索引与逻辑', '逐项联调：单命令验证后再串起来',
          '自测交付：断电重启、异常拔插、边界值']
for i, st in enumerate(steps5):
    y = Inches(3.8 + i * 0.6)
    shape(s, MSO_SHAPE.OVAL, Inches(0.86), y + Inches(0.03), Inches(0.26), Inches(0.26), BLUE)
    text(s, Inches(0.86), y + Inches(0.04), Inches(0.26), Inches(0.26), str(i + 1), 9, True, WHITE, PP_ALIGN.CENTER)
    text(s, Inches(1.24), y, Inches(7.0), Inches(0.35), st, 11.5, False, TEXT)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.62), Inches(1.85), Inches(3.9), Inches(4.5), BG)
shape(s, MSO_SHAPE.RECTANGLE, Inches(8.62), Inches(1.85), Inches(3.9), Inches(0.08), ORANGE)
text(s, Inches(8.9), Inches(2.12), Inches(3.3), Inches(0.35), '原则', 13, True, DARK)
rules = ['不改动原工程的控制逻辑与安全阈值', '接线与协议按目标机型重新核对',
         '串口占用、引脚定义、方向控制脚逐个确认', '每个模块单独可验证后再合并']
for i, r in enumerate(rules):
    text(s, Inches(8.92), Inches(2.62 + i * 0.8), Inches(3.2), Inches(0.7),
         '·  ' + r, 10.5, False, TEXT, spacing=1.4)
footer(s)

# ================= 10 工作计划 =================
s = page(True)
header(s, '工作计划', 'PLAN', 10, dark=True)
shape(s, MSO_SHAPE.RECTANGLE, Inches(1.05), Inches(2.05), Inches(0.02), Inches(4.1), RGBColor(0x2A, 0x4A, 0x6B))
plan = [('短期', '1 — 3 个月', ['深入研究伺服电机控制：电流环响应、参数自整定',
                              '参与稳像功能调参与优化，改善抖动抑制']),
        ('中期', '3 — 6 个月', ['学习 RTOS 任务调度与优先级设计，尝试引入工程',
                              '研究模糊 PID，应对负载变化与装配差异']),
        ('长期', '6 个月以上', ['把重复问题沉淀成自检清单与案例库',
                             '参与控制模块平台化，减少新机型重复开发'])]
for i, (phase, span, items) in enumerate(plan):
    y = Inches(2.15 + i * 1.4)
    shape(s, MSO_SHAPE.OVAL, Inches(1.0), y + Inches(0.06), Inches(0.3), Inches(0.3), ORANGE)
    text(s, Inches(1.32), y, Inches(1.2), Inches(0.35), phase, 15, True, WHITE)
    text(s, Inches(1.32), y + Inches(0.36), Inches(1.4), Inches(0.3), span, 9.5, False, SKY)
    for j, it in enumerate(items):
        text(s, Inches(2.95), y + Inches(j * 0.42), Inches(9.4), Inches(0.4),
             '·  ' + it, 12.5, False, RGBColor(0xD5, 0xE0, 0xEC))
footer(s, dark=True)

# ================= 11 总结与建议 =================
s = page(False)
header(s, '总结与建议', 'SUMMARY   &   SUGGESTIONS', 11)
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.85), Inches(1.8), Inches(11.65), Inches(1.5), BG)
shape(s, MSO_SHAPE.RECTANGLE, Inches(0.85), Inches(1.8), Inches(0.08), Inches(1.5), BLUE)
text(s, Inches(1.15), Inches(2.0), Inches(11.1), Inches(1.1),
     '三个月完成从协助到独立跟进项目的过渡：能独立定位问题、独立承接定制需求、独立完成一块新功能开发',
     15.5, True, DARK, spacing=1.5)
sug = [('建议一', '建立整机联调自检清单与常见问题案例库', '新机型可直接复用，缩短上手时间'),
       ('建议二', '关键参数按机型版本化记录', '限位、零点、PID、电机参数，避免换机后错配'),
       ('建议三', '软硬件接口文档统一维护', '串口分配、协议码、引脚定义，减少联调沟通成本')]
for i, (tag, h1, d1) in enumerate(sug):
    x = Inches(0.85 + i * 3.98)
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(3.55), Inches(3.72), Inches(2.5), WHITE, LINE)
    shape(s, MSO_SHAPE.RECTANGLE, x, Inches(3.55), Inches(3.72), Inches(0.07), ORANGE)
    text(s, x + Inches(0.25), Inches(3.78), Inches(3.2), Inches(0.3), tag, 10.5, True, ORANGE)
    text(s, x + Inches(0.25), Inches(4.12), Inches(3.25), Inches(0.8), h1, 12.5, True, DARK, spacing=1.4)
    text(s, x + Inches(0.25), Inches(5.0), Inches(3.25), Inches(0.9), d1, 10, False, SUB, spacing=1.45)
footer(s)

# ================= 12 结束 =================
s = page(True)
shape(s, MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.3), prs.slide_height, BLUE)
text(s, Inches(1.4), Inches(2.9), Inches(6.0), Inches(1.0), '谢  谢', 42, True, WHITE)
shape(s, MSO_SHAPE.RECTANGLE, Inches(1.42), Inches(3.95), Inches(1.1), Inches(0.06), SKY)
text(s, Inches(1.42), Inches(4.2), Inches(7.0), Inches(0.4), '请各位领导批评指正', 14, False,
     RGBColor(0xC9, 0xD6, 0xE4))

# ================= 保存 =================
desk = os.path.join(os.path.expanduser('~'), 'Desktop')
if not os.path.isdir(desk):
    desk = r'D:\Codebuddy\output'
    os.makedirs(desk, exist_ok=True)
out = os.path.join(desk, '试用期述职报告_赵庆斌_2026-10-28_v2.pptx')
prs.save(out)
print('SAVED ' + out)
print('size', os.path.getsize(out), 'slides', len(prs.slides))
