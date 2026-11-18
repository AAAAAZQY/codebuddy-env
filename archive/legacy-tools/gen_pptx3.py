# -*- coding: cp936 -*-
"""试用期述职报告 v3：按公司课题分享模板风格（深青蓝 + 珊瑚红、大字、章节页）"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

FONT = '微软雅黑'
BLUE = RGBColor(0x0F, 0x84, 0xAD)      # 主色（同步进/FOC 模板）
BLUE_D = RGBColor(0x0B, 0x5F, 0x7E)
CORAL = RGBColor(0xE9, 0x61, 0x71)     # 强调色
INK = RGBColor(0x24, 0x33, 0x3B)
GREY = RGBColor(0x6E, 0x7F, 0x8C)
LGREY = RGBColor(0xF4, 0xF7, 0xF9)
LINE = RGBColor(0xDD, 0xE5, 0xEA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 17


def set_font(run, size, bold=False, color=INK, name=FONT):
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


def rect(slide, x, y, w, h, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1)
    sh.shadow.inherit = False
    return sh


def text(slide, x, y, w, h, s, size, bold=False, color=INK,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.3):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, ln in enumerate(s.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        r = p.add_run()
        r.text = ln
        set_font(r, size, bold, color)
    return tb


def items_list(slide, x, y, w, h, items, size=20, gap=20, spacing=1.55,
               bullet=CORAL, color=INK):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    for i, it in enumerate(items):
        sub = False
        s = it
        if isinstance(it, tuple):
            s, sub = it[0], True
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap if not sub else 10)
        p.line_spacing = spacing
        rb = p.add_run()
        rb.text = '—  ' if not sub else '·  '
        set_font(rb, size - 2, True, bullet if not sub else GREY)
        rt = p.add_run()
        rt.text = s
        set_font(rt, size if not sub else size - 5, False, color if not sub else GREY)
    return tb


def blank(fill=WHITE):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, prs.slide_width, prs.slide_height, fill)
    return s


def content(title, en, page, items, size=20, gap=20):
    s = blank(WHITE)
    rect(s, 0, 0, Inches(0.22), prs.slide_height, BLUE)
    text(s, Inches(1.0), Inches(0.85), Inches(10.5), Inches(0.7), title, 32, True, INK)
    text(s, Inches(1.02), Inches(1.55), Inches(8.0), Inches(0.35), en, 12, False, GREY)
    rect(s, Inches(1.0), Inches(1.98), Inches(1.0), Inches(0.055), CORAL)
    items_list(s, Inches(1.02), Inches(2.45), Inches(11.2), Inches(3.9), items,
               size=size, gap=gap)
    text(s, Inches(11.0), Inches(6.85), Inches(1.5), Inches(0.3),
         '%02d / %d' % (page, TOTAL), 11, False, RGBColor(0xB8, 0xC4, 0xCC), PP_ALIGN.RIGHT)
    text(s, Inches(1.02), Inches(6.85), Inches(7.0), Inches(0.3),
         'MYTECH 名扬时代 ｜ 试用期述职报告 ｜ 赵庆斌', 9.5, False, RGBColor(0xB8, 0xC4, 0xCC))
    return s


def section(num, title, en, page):
    s = blank(BLUE)
    rect(s, 0, 0, Inches(0.22), prs.slide_height, CORAL)
    text(s, Inches(1.5), Inches(2.25), Inches(4.0), Inches(1.8), num, 96, True,
         RGBColor(0xFF, 0xFF, 0xFF))
    rect(s, Inches(1.62), Inches(4.25), Inches(1.3), Inches(0.06), CORAL)
    text(s, Inches(1.62), Inches(4.55), Inches(8.0), Inches(0.7), title, 34, True, WHITE)
    text(s, Inches(1.64), Inches(5.25), Inches(8.0), Inches(0.4), en, 12, False,
         RGBColor(0xA8, 0xD4, 0xE4))
    text(s, Inches(11.0), Inches(6.85), Inches(1.5), Inches(0.3),
         '%02d / %d' % (page, TOTAL), 11, False, RGBColor(0x7F, 0xB6, 0xCB), PP_ALIGN.RIGHT)
    return s


# ================= 01 封面 =================
s = blank(WHITE)
rect(s, 0, 0, prs.slide_width, Inches(0.42), BLUE)
rect(s, Inches(1.2), Inches(2.35), Inches(1.4), Inches(0.07), CORAL)
text(s, Inches(1.18), Inches(2.7), Inches(9.5), Inches(1.1), '试用期述职报告', 54, True, INK)
text(s, Inches(1.2), Inches(3.95), Inches(9.0), Inches(0.4), 'PROBATION   WORK   REVIEW', 13, False, BLUE)
text(s, Inches(1.2), Inches(4.75), Inches(9.0), Inches(1.5),
     '汇报人：赵庆斌\n研发部 · 单片机软件\n汇报日期：2026.10.28', 15, False, GREY, spacing=1.9)
rect(s, 0, Inches(7.08), prs.slide_width, Inches(0.42), BLUE)
text(s, Inches(1.2), Inches(7.14), Inches(9.0), Inches(0.3), 'MYTECH 名扬时代电子有限公司', 10, False,
     RGBColor(0xD5, 0xEA, 0xF2))

# ================= 02 目录 =================
s = blank(WHITE)
rect(s, 0, 0, Inches(0.22), prs.slide_height, BLUE)
text(s, Inches(1.0), Inches(0.9), Inches(6.0), Inches(0.7), '目 录', 32, True, INK)
text(s, Inches(1.02), Inches(1.6), Inches(6.0), Inches(0.35), 'CONTENTS', 12, False, GREY)
rect(s, Inches(1.0), Inches(2.02), Inches(1.0), Inches(0.055), CORAL)
toc = [('01', '试用期回顾', '做了什么 · 覆盖哪些方向'),
       ('02', '工作收获', '电机 / 显示 / 电源 / 光敏 / 方法'),
       ('03', '工作计划', '伺服 · 稳像 · RTOS · 模糊 PID'),
       ('04', '总结与建议', '总体总结与三点建议')]
for i, (n, t, d) in enumerate(toc):
    y = Inches(2.5 + i * 1.15)
    text(s, Inches(1.05), y, Inches(1.0), Inches(0.55), n, 30, True, RGBColor(0xC8, 0xD8, 0xE0))
    text(s, Inches(2.0), y + Inches(0.02), Inches(6.6), Inches(0.45), t, 22, True, INK)
    text(s, Inches(2.02), y + Inches(0.52), Inches(7.0), Inches(0.35), d, 12, False, GREY)
    if i < 3:
        rect(s, Inches(2.0), y + Inches(0.92), Inches(9.4), Inches(0.008), LINE)

# ================= 03 章节 01 =================
section('01', '试用期回顾', 'WHAT   I   DID', 3)

# ================= 04 工作概览 =================
s = content('工作概览', 'AT   A   GLANCE', 4, [
    '17 个项目：问题修复、定制化项目、新功能开发三类并行',
    '5 个方向：电机与云台、显示、电源与电量、光敏与灯光、协议定制',
    '2 个模块移植：激光测距、红外补光灯',
], size=21, gap=24)
for i, (num, label) in enumerate([('17', '个项目'), ('5', '个方向'),
                                  ('3', '类工作'), ('2', '个模块')]):
    x = Inches(1.02 + i * 3.0)
    rect(s, x, Inches(4.95), Inches(2.7), Inches(1.35), LGREY)
    rect(s, x, Inches(4.95), Inches(0.07), Inches(1.35), CORAL)
    text(s, x + Inches(0.25), Inches(5.1), Inches(1.6), Inches(0.6), num, 30, True, BLUE)
    text(s, x + Inches(0.25), Inches(5.72), Inches(2.2), Inches(0.3), label, 11, False, GREY)

# ================= 05 参与方向 =================
content('参与方向与典型问题', 'DIRECTIONS   &   CASES', 5, [
    '电机与云台：申威 T160 丢步撞头、U 款球机速度曲线与电机调参、PM 球机角度偏差',
    '显示：海洋王 6126b / 60d、球芯全系的开机花屏、屏幕反转、画面异常',
    '电源与电量：无充电检测硬件，靠端压趋势判充电，曲线查表 + 分段积分 + 关机记账',
    '光敏与灯光：LMD B1105C 软硬光敏切换、国信 B130 白光灯自动切换',
    '协议与定制：KB T160 查询协议、BM S100 特殊预置位、馥鸿 B130 串口改造',
], size=17, gap=14)

# ================= 06 章节 02 =================
section('02', '工作收获', 'WHAT   I   LEARNED', 6)

# ================= 07 收获电机 =================
content('收获 · 电机与云台', 'MOTOR   &   GIMBAL', 7, [
    'U 款球机：独立完成速度曲线调整，把机械参数（行程、负载）映射到速度曲线，实现不丢步、不撞头、速度适中',
    '申威 T160：丢步是头太重、电机力矩不够，增大常态力矩解决；撞头是行程太大、自检没找到光耦，增大自检行程后解决',
    '22B2 SST：结构特殊导致找不到光耦，新增绕过限制直接发脉冲的函数，确保能找到光耦',
    'PM 球机 / 5d6750：修正自检撞头与角度偏差，完成精度与速度测试',
    '运动类问题先查限位、零点、加减速曲线，再怀疑电机本体',
], size=17, gap=12)

# ================= 08 收获显示电源 =================
content('收获 · 显示与电源', 'DISPLAY   &   POWER', 8, [
    '海洋王 6126b、球芯全系：屏幕反转与开机花屏，根因是初始化顺序与上电时序',
    '海洋王 60d：画面异常判断为全系共性问题，统一处理而不是逐台当个案修',
    '森曼 S100：修复 OLED 开机花屏（初始化与按键扫描时序）与 ircut 潜在问题',
    '花屏与反显三类根因：初始化顺序、刷新节流、显示方向配置',
], size=18, gap=16)

# ================= 09 收获光敏协议 =================
content('收获 · 光敏与协议', 'LIGHT   &   PROTOCOL', 9, [
    'KB T160：新增查询协议（帧格式、超时重发）与垂直电机跟随，解决变倍后画面偏移',
    'BM S100：特殊预置位无法调用，修复状态机 bug 后解决',
    '馥鸿 B130：双串口改单串口；抓机芯数据时发现对方下发数据异常，定位后推动修正',
    'LMD B1105C / 国信 B130 / 5SKS·BS7：光敏切换逻辑与阈值按现场光照调整',
    ('协议类问题两步：先对齐帧，再补解析分支；阈值必须现场实测', 1),
], size=16, gap=12)

# ================= 10 专项 电量管理（方案） =================
content('专项 · 电量管理 ｜ SM S100', 'POWER   MANAGEMENT', 10, [
    '硬件条件：整板无充电管理芯片、无 CHRG/STDBY 引脚，只有一路电池电压进 ADC —— 充电状态只能由软件判定',
    '放电：厂家曲线按 5 格间隔取点建表，先查单调性再插值，越界取端点',
    '充电判定三段式：进入看端压净涨、维持看去抖、退出看回落；不能只看绝对电压，满电静置也在恒压点之上',
    '充电积分：CC 段按 I/(C×60) 折算（3A/4.5Ah ≈ 1.1 格/分），CV 段按 K×(100-SOC)（τ ≈ 23 分），再乘 1.1~1.2 补偿',
    ('上界钳位到电压法读数，防止积分跑飞', 1),
], size=16, gap=13)

# ================= 11 专项 关机充电记账 =================
content('专项 · 关机充电记账 ｜ SM S100', 'CHARGING   WHILE   POWERED   OFF', 11, [
    '问题：关机后软件不运行，这段时间的电量变化没有任何记录 —— 可能被补电、自放电，也可能拆下充满再装回',
    '做法：EEPROM 存「关机时的电压法值」当基线，开机与当前电压法值比较；存电压法值而非积分值，误差相减抵消',
    '关键坑：充电中关机不能写电压基线 —— 端压虚高会抬高基线，下次开机误判「没充过电」，充进去的电全丢',
    '兜底：魔数不符或越界直接用电压值；开机端压 ≥12.55V 按满电；充电中掉电重启，存值作下界、电压值作上界',
    ('效果：关机充电引起的重启跳变从 ±20 格压到 ±5 格以内', 1),
], size=16, gap=13)

# ================= 11 收获方法协作 =================
content('收获 · 排查方法与协作', 'METHOD   &   TEAMWORK', 12, [
    '排查顺序：复现现象 → 查最近改动 → 查逻辑与时序 → 查标定 → 最后怀疑硬件',
    '给结论不给猜测：66d 尾线查询异常，逐层排除后确认是硬件问题',
    '不懂就问：协议与时序拿不准，先和硬件、测试同事对齐再动手',
    '交付习惯：最小改动、可回退、不碰安全阈值与协议码',
], size=19, gap=18)

# ================= 12 章节 03 =================
section('03', '工作计划', 'WHAT   I   WILL   DO', 13)

# ================= 13 计划 =================
s = content('工作计划', 'PLAN', 14, [
    '短期：深入研究伺服电机控制 —— 电流环响应、参数自整定',
    '短期：参与稳像功能调参与优化，改善抖动抑制',
    '中期：学习 RTOS 任务调度与优先级设计，尝试引入工程',
    '中期：研究模糊 PID，应对负载变化与装配差异',
    '长期：沉淀自检清单与案例库，参与控制模块平台化',
], size=20, gap=16)

# ================= 14 章节 04 =================
section('04', '总结与建议', 'SUMMARY   &   SUGGESTIONS', 15)

# ================= 15 总结建议 =================
s = blank(WHITE)
rect(s, 0, 0, Inches(0.22), prs.slide_height, BLUE)
text(s, Inches(1.0), Inches(0.85), Inches(10.0), Inches(0.7), '总结与建议', 32, True, INK)
text(s, Inches(1.02), Inches(1.55), Inches(8.0), Inches(0.35), 'SUMMARY   &   SUGGESTIONS', 12, False, GREY)
rect(s, Inches(1.0), Inches(1.98), Inches(1.0), Inches(0.055), CORAL)
rect(s, Inches(1.02), Inches(2.45), Inches(11.3), Inches(1.15), LGREY)
rect(s, Inches(1.02), Inches(2.45), Inches(0.07), Inches(1.15), BLUE)
text(s, Inches(1.32), Inches(2.62), Inches(10.7), Inches(0.85),
     '三个月完成从协助到独立跟进项目的过渡：能独立定位问题、独立承接定制需求、独立完成一块新功能',
     17, True, INK, spacing=1.5)
sug = [('建议一', '建立整机联调自检清单与常见问题案例库'),
       ('建议二', '限位、零点、PID、电机参数按机型版本化记录'),
       ('建议三', '软硬件接口（串口、协议码、引脚）统一维护')]
for i, (tag, s1) in enumerate(sug):
    x = Inches(1.02 + i * 3.78)
    rect(s, x, Inches(3.95), Inches(3.55), Inches(1.75), WHITE, LINE)
    rect(s, x, Inches(3.95), Inches(3.55), Inches(0.07), CORAL)
    text(s, x + Inches(0.24), Inches(4.18), Inches(3.0), Inches(0.3), tag, 11, True, CORAL)
    text(s, x + Inches(0.24), Inches(4.52), Inches(3.1), Inches(1.0), s1, 13, False, INK, spacing=1.5)
text(s, Inches(11.0), Inches(6.85), Inches(1.5), Inches(0.3), '16 / %d' % TOTAL, 11, False,
     RGBColor(0xB8, 0xC4, 0xCC), PP_ALIGN.RIGHT)

# ================= 16 THANKS =================
s = blank(BLUE)
rect(s, 0, 0, Inches(0.22), prs.slide_height, CORAL)
text(s, Inches(1.5), Inches(2.9), Inches(6.0), Inches(1.0), 'THANKS', 54, True, WHITE)
rect(s, Inches(1.55), Inches(4.15), Inches(1.3), Inches(0.06), CORAL)
text(s, Inches(1.55), Inches(4.45), Inches(7.0), Inches(0.4), '感谢聆听 · 请各位领导批评指正', 15, False,
     RGBColor(0xA8, 0xD4, 0xE4))

# ================= 保存 =================
desk = os.path.join(os.path.expanduser('~'), 'Desktop')
if not os.path.isdir(desk):
    desk = r'D:\Codebuddy\output'
    os.makedirs(desk, exist_ok=True)
out = os.path.join(desk, '试用期述职报告_赵庆斌_v7.pptx')
prs.save(out)
print('SAVED ' + out)
print('size', os.path.getsize(out), 'slides', len(prs.slides))
