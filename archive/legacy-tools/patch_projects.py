# -*- coding: cp936 -*-
"""把第 4 页从「产品线」改成「参与项目（按问题类型）」，网格布局 3x2"""
import io

# ================= pptx =================
P1 = r'D:\Codebuddy\tools\gen_pptx.py'
s = io.open(P1, encoding='cp936', newline='').read().replace('\r\n', '\n')

NEW_FUNC = '''def cards_slide(title, en, cards, page):
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

'''

i0 = s.find('def cards_slide')
i1 = s.find('# ---------------- 1 封面 ----------------')
if i0 < 0 or i1 < 0 or i1 < i0:
    raise SystemExit('pptx: anchor for cards_slide not found')
s = s[:i0] + NEW_FUNC + s[i1:]

NEW_CALL = '''# ---------------- 3.5 参与项目 ----------------
cards_slide('参与项目 · 按问题类型', 'PROJECTS   (17)', [
    ('电机与云台', [
        '申盛 T160：电机参数整定，解决丢步与撞头',
        'PM 球机：自检撞头、角度不准',
        '20H U 款：电机调参、零位机芯对接',
        '5D670：精度与速度测试',
    ]),
    ('画面与显示', [
        '海洋王 6126b：电源板屏幕、主板反转',
        '海洋王 60D：画面异常（全系共性问题）',
        '球芯：电源板开机花屏',
        'k13 T160：画面异常',
    ]),
    ('电源与电量', [
        '5100 森曼：电量来回跳',
        '5100 森曼：OLED 开机花屏、缺键',
    ]),
    ('光敏与灯光', [
        'LMD B1105C：软 / 硬光敏切换逻辑',
        '国信 B130：白光灯自动切换',
        '5SKS / BS7：光敏切换阈值调整',
    ]),
    ('协议与功能定制', [
        '标配 5 寸：特殊预置位、云台报警查询',
        'k13 T160：MTK 查询协议、垂直电机跟焦',
        '赣鸿 B130：双串口改单串口',
    ]),
    ('定位与其他', [
        '66D：尾线查询异常，判定为硬件问题',
        '锐明 IRC4t、B3AA P8L2：问题修复',
        '5SKS / BS7：虚标与自动翻转异常',
    ]),
], 4)

'''

j0 = s.find('# ---------------- 3.5 产品线覆盖 ----------------')
j1 = s.find('# ---------------- 4 电机控制 ----------------')
if j0 < 0 or j1 < 0 or j1 < j0:
    raise SystemExit('pptx: anchor for cards call not found')
s = s[:j0] + NEW_CALL + s[j1:]

io.open(P1, 'w', encoding='cp936', newline='').write(s.replace('\n', '\r\n'))
print('pptx done: cards_slide=%d projects=%d' % (s.count('def cards_slide'), s.count('参与项目')))

# ================= html =================
P2 = r'D:\Codebuddy\tools\gen_html.py'
h = io.open(P2, encoding='cp936', newline='').read().replace('\r\n', '\n')

OLD_CSS = """.cards .grid { display:flex; gap:18px; margin-top:8px; }
.cards .card { flex:1; background:#f4f7fb; border-top:5px solid #1e6fba; padding:22px 18px; min-height:330px; }
.cards .card h3 { margin:0 0 14px; font-size:17px; color:#0e2a47; }
.cards .card p { margin:0; font-size:13px; line-height:2.0; color:#6b7481; }"""

NEW_CSS = """.cards .grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:20px 22px; margin-top:6px; }
.cards .card { background:#f4f7fb; border-top:5px solid #1e6fba; padding:18px 18px; min-height:196px; }
.cards .card h3 { margin:0 0 12px; font-size:15px; color:#0e2a47; }
.cards .card p { margin:0; font-size:12.5px; line-height:1.95; color:#6b7481; }"""

h = h.replace(OLD_CSS, NEW_CSS, 1)

CARDS_OLD_START = h.find('CARDS_HTML = (')
CARDS_OLD_END = h.find('for t, en, items, pg in body:')
if CARDS_OLD_START < 0 or CARDS_OLD_END < 0:
    raise SystemExit('html: CARDS_HTML block not found')

CARDS_NEW = '''CARDS_HTML = (
    '<section class="slide cards">'
    '<div class="bar"></div>'
    '<h1>参与项目 · 按问题类型</h1>'
    '<div class="en">PROJECTS (17)</div>'
    '<div class="pg">04</div>'
    '<div class="hr"></div>'
    '<div class="grid">'
    '<div class="card"><h3>电机与云台</h3><p>'
    '申盛 T160：电机参数整定，解决丢步与撞头<br>'
    'PM 球机：自检撞头、角度不准<br>'
    '20H U 款：电机调参、零位机芯对接<br>'
    '5D670：精度与速度测试</p></div>'
    '<div class="card"><h3>画面与显示</h3><p>'
    '海洋王 6126b：电源板屏幕、主板反转<br>'
    '海洋王 60D：画面异常（全系共性问题）<br>'
    '球芯：电源板开机花屏<br>'
    'k13 T160：画面异常</p></div>'
    '<div class="card"><h3>电源与电量</h3><p>'
    '5100 森曼：电量来回跳<br>'
    '5100 森曼：OLED 开机花屏、缺键</p></div>'
    '<div class="card"><h3>光敏与灯光</h3><p>'
    'LMD B1105C：软 / 硬光敏切换逻辑<br>'
    '国信 B130：白光灯自动切换<br>'
    '5SKS / BS7：光敏切换阈值调整</p></div>'
    '<div class="card"><h3>协议与功能定制</h3><p>'
    '标配 5 寸：特殊预置位、云台报警查询<br>'
    'k13 T160：MTK 查询协议、垂直电机跟焦<br>'
    '赣鸿 B130：双串口改单串口</p></div>'
    '<div class="card"><h3>定位与其他</h3><p>'
    '66D：尾线查询异常，判定为硬件问题<br>'
    '锐明 IRC4t、B3AA P8L2：问题修复<br>'
    '5SKS / BS7：虚标与自动翻转异常</p></div>'
    '</div>'
    '<div class="foot">MYTECH 名扬时代  |  试用期述职报告</div>'
    '</section>'
)

'''
h = h[:CARDS_OLD_START] + CARDS_NEW + h[CARDS_OLD_END:]

io.open(P2, 'w', encoding='cp936', newline='').write(h.replace('\n', '\r\n'))
print('html done: cards=%d projects=%d' % (h.count('CARDS_HTML'), h.count('参与项目')))
