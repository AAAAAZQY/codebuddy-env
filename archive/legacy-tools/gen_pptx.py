# -*- coding: cp936 -*-
"""生成《试用期述职报告》PPT（16:9，简约商务风）"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

FONT = '微软雅黑'
C_DARK = RGBColor(0x0E, 0x2A, 0x47)
C_BLUE = RGBColor(0x1E, 0x6F, 0xBA)
C_ACC = RGBColor(0x3E, 0x9A, 0xDD)
C_TEXT = RGBColor(0x3A, 0x41, 0x4A)
C_SUB = RGBColor(0x6B, 0x74, 0x81)
C_LINE = RGBColor(0xD8, 0xDF, 0xE8)
C_BG = RGBColor(0xF4, 0xF7, 0xFB)
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def set_font(run, size, bold=False, color=C_TEXT, name=FONT):
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


def rect(slide, x, y, w, h, color, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = color
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    s.shadow.inherit = False
    s.text_frame.text = ''
    return s


def textbox(slide, x, y, w, h, text, size, bold=False, color=C_TEXT,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.25):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = spacing
    r = p.add_run()
    r.text = text
    set_font(r, size, bold, color)
    return tb


def bullets(slide, x, y, w, h, items, size=19, gap=16, spacing=1.3):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    first = True
    for it in items:
        level = 0
        text = it
        if isinstance(it, tuple):
            text, level = it
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(gap)
        p.line_spacing = spacing
        bs = 16 if level == 0 else 13
        rb = p.add_run()
        rb.text = ('■   ' if level == 0 else '·   ')
        set_font(rb, bs, False, C_BLUE if level == 0 else C_SUB)
        rt = p.add_run()
        rt.text = text
        set_font(rt, size if level == 0 else size - 3,
                 False, C_TEXT if level == 0 else C_SUB)
    return tb


def content_slide(title, en, items, page, size=19):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, prs.slide_width, prs.slide_height, C_WHITE)
    rect(s, Inches(0.85), Inches(0.72), Inches(0.075), Inches(0.44), C_BLUE)
    textbox(s, Inches(1.05), Inches(0.66), Inches(9.0), Inches(0.55),
            title, 27, True, C_DARK)
    textbox(s, Inches(1.06), Inches(1.14), Inches(6.0), Inches(0.3),
            en, 11, False, C_SUB)
    textbox(s, Inches(11.2), Inches(0.72), Inches(1.3), Inches(0.4),
            '%02d' % page, 20, True, RGBColor(0xC3, 0xCD, 0xDA), PP_ALIGN.RIGHT)
    rect(s, Inches(0.85), Inches(1.52), Inches(11.63), Inches(0.012), C_LINE)
    bullets(s, Inches(0.95), Inches(1.85), Inches(11.4), Inches(4.6), items, size=size)
    rect(s, Inches(0.85), Inches(6.92), Inches(11.63), Inches(0.008), C_LINE)
    textbox(s, Inches(0.85), Inches(7.0), Inches(7.0), Inches(0.28),
            'MYTECH 名扬时代  |  试用期述职报告', 10, False, C_SUB)
    return s


def cards_slide(title, en, cards, page):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, prs.slide_width, prs.slide_height, C_WHITE)
    rect(s, Inches(0.85), Inches(0.72), Inches(0.075), Inches(0.44), C_BLUE)
    textbox(s, Inches(1.05), Inches(0.66), Inches(9.5), Inches(0.55), title, 27, True, C_DARK)
    textbox(s, Inches(1.06), Inches(1.14), Inches(7.0), Inches(0.3), en, 11, False, C_SUB)
    textbox(s, Inches(11.2), Inches(0.72), Inches(1.3), Inches(0.4), '%02d' % page, 20, True, RGBColor(0xC3, 0xCD, 0xDA), PP_ALIGN.RIGHT)
    rect(s, Inches(0.85), Inches(1.52), Inches(11.63), Inches(0.012), C_LINE)

    cols = 3
    cw = Inches(3.56)
    ch = Inches(2.24)
    gx = Inches(0.27)
    gy = Inches(0.26)
    total_w = int(cw * cols + gx * (cols - 1))
    x0 = int((prs.slide_width - total_w) / 2)
    y0 = Inches(1.82)
    for i, item in enumerate(cards):
        r = i // cols
        c = i % cols
        x = x0 + c * (cw + gx)
        y = y0 + r * (ch + gy)
        rect(s, x, y, cw, ch, C_BG)
        rect(s, x, y, cw, Inches(0.06), C_BLUE)
        textbox(s, x + Inches(0.22), y + Inches(0.24), cw - Inches(0.44), Inches(0.32), item[0], 14, True, C_DARK)
        lines = item[1]
        tb = s.shapes.add_textbox(x + Inches(0.22), y + Inches(0.68), cw - Inches(0.44), ch - Inches(0.82))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = 0
        tf.margin_right = 0
        tf.margin_top = 0
        tf.margin_bottom = 0
        first = True
        for ln in lines:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.space_after = Pt(5)
            p.line_spacing = 1.3
            run = p.add_run()
            run.text = ln
            set_font(run, 10.5, False, C_SUB)
    rect(s, Inches(0.85), Inches(6.92), Inches(11.63), Inches(0.008), C_LINE)
    textbox(s, Inches(0.85), Inches(7.0), Inches(9.0), Inches(0.28), 'MYTECH 名扬时代  |  试用期述职报告', 10, False, C_SUB)
    return s

# ---------------- 1 封面 ----------------
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, prs.slide_width, prs.slide_height, C_DARK)
rect(s, 0, 0, Inches(0.28), prs.slide_height, C_BLUE)
rect(s, Inches(1.5), Inches(2.55), Inches(1.1), Inches(0.06), C_ACC)
textbox(s, Inches(1.5), Inches(2.85), Inches(9.0), Inches(1.1),
        '试用期述职报告', 46, True, C_WHITE)
textbox(s, Inches(1.52), Inches(4.02), Inches(8.0), Inches(0.4),
        'PROBATION   WORK   REVIEW', 13, False, C_ACC)
textbox(s, Inches(1.52), Inches(4.75), Inches(9.0), Inches(1.4),
        '汇报人：赵庆斌      研发部 · 单片机软件\n入职日期：2026.8.3      汇报日期：2026.10',
        15, False, RGBColor(0xC9, 0xD6, 0xE4), spacing=1.7)

# ---------------- 2 目录 ----------------
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, prs.slide_width, prs.slide_height, C_WHITE)
rect(s, 0, 0, Inches(4.55), prs.slide_height, C_BG)
rect(s, 0, 0, Inches(0.25), prs.slide_height, C_BLUE)
textbox(s, Inches(1.0), Inches(2.55), Inches(3.2), Inches(0.9),
        'CONTENTS', 34, True, C_DARK)
textbox(s, Inches(1.02), Inches(3.45), Inches(3.2), Inches(0.4),
        '目 录', 16, False, C_SUB)

menu = [
    ('01', '试用期回顾', '17 个项目 / 五个方向 / 模块移植 / 调试排障'),
    ('02', '工作收获', '技术 / 架构 / 方法 / 协作'),
    ('03', '工作计划', '短期 / 中期 / 长期'),
    ('04', '总结与建议', '总体总结 / 对团队的建议'),
]
y = Inches(1.35)
for num, t, d in menu:
    textbox(s, Inches(5.35), y, Inches(0.9), Inches(0.5), num, 24, True, C_ACC)
    textbox(s, Inches(6.25), y - Inches(0.02), Inches(4.0), Inches(0.42), t, 21, True, C_DARK)
    textbox(s, Inches(6.27), y + Inches(0.42), Inches(6.2), Inches(0.32), d, 12, False, C_SUB)
    rect(s, Inches(5.35), y + Inches(0.92), Inches(7.0), Inches(0.008), C_LINE)
    y += Inches(1.35)

# ---------------- 3 回顾总览 ----------------
content_slide('试用期回顾 · 总览', 'OVERVIEW', [
    '入职三个月跟进 17 个项目，覆盖电机、显示、电源、光敏、协议五个方向',
    '三类工作：问题修复、定制化项目（U 款球机对接零位机芯等）、新功能开发（电量管理、模块移植）',
    '讲法：每条按「现象 → 判断依据 → 处理」展开，重点在怎么定位，而不是改了什么',
    ('项目名按实际型号写，不做改写', 1),
], 3, 18)

# ---------------- 4 收获：电机与云台 ----------------
content_slide('收获 · 电机与云台', 'MOTOR   &   GIMBAL', [
    'U 款球机定制对接：第三方零位机芯（VBM-5100）报文对不上，先抓串口逐帧对齐格式与时序，再按零位脉冲修正电机零点，实现上电自动找零',
    '申盛 T160：低速丢步与自检撞头，定位到限位与零点偏差使行程被提前截断，调整电机参数与加减速曲线后恢复',
    'PM 球机：自检撞头与角度不准，重新核对行程与零点后修正',
    '5d6750：完成精度与速度测试，形成可复现的测试方法',
    ('共性：运动类问题先查限位、零点、加减速曲线，再怀疑电机本身', 1),
], 4, 16)

# ---------------- 5 收获：显示与电源 ----------------
content_slide('收获 · 显示与电源', 'DISPLAY   &   POWER', [
    '电量管理：按充电曲线积分累计电量，识别充放电状态并在 OSD 层输出百分比；5100 森美 电量来回跳，靠采样滤波 + 刷新节流解决',
    '5100 森美：OLED 开机花屏与缺 CU 键，定位为初始化顺序与按键扫描时序问题',
    '海洋王 6126b：电源板屏幕 y 板反转，修正初始化与显示方向配置',
    '球芯全系、海洋王 60d：电源板开机花屏与画面异常，判断为共性问题后统一处理',
    ('共性：花屏与异常多出在初始化顺序和刷新节流，不在图像链路', 1),
], 5, 16)

# ---------------- 6 收获：光敏与协议 ----------------
content_slide('收获 · 光敏与协议', 'LIGHT   &   PROTOCOL', [
    'k13 T160：新增 my 查询协议（帧格式、超时重发），并增加垂直电机跟随，解决变倍后画面上下偏移',
    '标配 5 寸：特殊预置位（巡航等）无法调用、云台报警信息查不到，补齐协议解析分支',
    'LMD B1105C：新增软 / 硬光敏切换逻辑',
    '国传信 B130：增加白光灯自动切换模式',
    '5SKS / BS7：修复虚标与自动翻转异常，并按现场光照调整光敏切换阈值',
], 6, 16)

# ---------------- 7 收获：排查方法与协作 ----------------
content_slide('收获 · 排查方法与协作', 'METHOD   &   TEAMWORK', [
    '66d：尾线不能查询数据，逐层排除后确认为硬件问题，没有在软件上反复试；锐明 IRC4t、B3AA P8L2 同样先定位再动手',
    '固定顺序：复现现象 → 查最近改动 → 查逻辑与时序 → 查标定 → 最后怀疑硬件',
    '遇到不懂的先问，和硬件、测试同事把信息对齐再动手',
    '交付习惯：最小改动、可回退、可追溯，不擅自改安全阈值与协议码',
], 7, 17)

# ---------------- 8 配件模块移植 ----------------
content_slide('配件模块移植', 'MODULE   PORTING', [
    '激光测距：55AA 帧解析、单次 / 连续测距、命令透传与应答回显',
    '红外补光灯：开关、亮度、角度随变倍联动、上电强制关灯保护',
    '移植原则：不改动原工程控制逻辑，按最小改动接入并逐项联调验证',
    ('接线与协议按目标机型核对：串口占用、引脚定义、方向控制脚', 1),
], 8)

# ---------------- 9 工作计划 ----------------
content_slide('工作计划', 'PLAN', [
    '短期：深入研究伺服电机控制，从电流环响应、参数自整定入手，提升低速平稳性',
    '短期：参与稳像功能的调参与优化，改善抖动抑制效果与异常工况稳定性',
    '中期：学习 RTOS 的任务调度与优先级设计，尝试引入工程，改善多任务实时性',
    '中期：研究模糊 PID，针对负载变化、装配差异等不确定因素做自适应补偿',
    '长期：把重复问题沉淀成自检清单与案例库，参与控制模块平台化',
], 9)

# ---------------- 10 总结与建议 ----------------
content_slide('总结与建议', 'SUMMARY   &   SUGGESTIONS', [
    '总结：三个月完成从协助到独立跟进项目的过渡，问题覆盖电机、显示、电源、光敏与协议',
    '建议一：建立整机联调自检清单与常见问题案例库，新机型可直接复用',
    '建议二：限位值、标定值、PID 与电机参数按机型版本化记录，避免换机后参数错配',
    '建议三：软硬件接口（串口分配、协议码、引脚定义）统一维护一份，减少联调沟通成本',
], 10)

# ---------------- 12 结束 ----------------
s = prs.slides.add_slide(BLANK)
rect(s, 0, 0, prs.slide_width, prs.slide_height, C_DARK)
rect(s, 0, 0, Inches(0.28), prs.slide_height, C_BLUE)
textbox(s, Inches(1.5), Inches(3.0), Inches(8.0), Inches(1.0), '谢 谢', 44, True, C_WHITE)
rect(s, Inches(1.52), Inches(4.05), Inches(1.1), Inches(0.06), C_ACC)
textbox(s, Inches(1.52), Inches(4.3), Inches(9.0), Inches(0.4),
        '请各位领导批评指正', 16, False, RGBColor(0xC9, 0xD6, 0xE4))

# ---------------- 保存 ----------------
desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
if not os.path.isdir(desktop):
    desktop = 'D:\\Codebuddy\\output'
    os.makedirs(desktop, exist_ok=True)
out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10-28.pptx')
try:
    if os.path.exists(out):
        os.remove(out)
    prs.save(out)
except Exception as e:
    print('primary save failed: %s' % e)
    out = os.path.join(desktop, '试用期述职报告_赵庆斌_2026-10_v2.pptx')
    prs.save(out)
print('SAVED ' + out)
print('size ' + str(os.path.getsize(out)) + ' bytes')
