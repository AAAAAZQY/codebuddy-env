# -*- coding: cp936 -*-
"""增加「业务覆盖 · 产品线」卡片页；修正五条主线；补步进+伺服表述"""
import io

# ================= pptx =================
P1 = r'D:\Codebuddy\tools\gen_pptx.py'
s = io.open(P1, encoding='cp936', newline='').read().replace('\r\n', '\n')

FUNC = '''def cards_slide(title, en, cards, page):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, prs.slide_width, prs.slide_height, C_WHITE)
    rect(s, Inches(0.85), Inches(0.72), Inches(0.075), Inches(0.44), C_BLUE)
    textbox(s, Inches(1.05), Inches(0.66), Inches(9.0), Inches(0.55), title, 27, True, C_DARK)
    textbox(s, Inches(1.06), Inches(1.14), Inches(6.0), Inches(0.3), en, 11, False, C_SUB)
    textbox(s, Inches(11.2), Inches(0.72), Inches(1.3), Inches(0.4), '%02d' % page, 20, True, RGBColor(0xC3, 0xCD, 0xDA), PP_ALIGN.RIGHT)
    rect(s, Inches(0.85), Inches(1.52), Inches(11.63), Inches(0.012), C_LINE)
    n = len(cards)
    cw = Inches(2.16)
    gap = Inches(0.18)
    total = int(cw * n + gap * (n - 1))
    x0 = int((prs.slide_width - total) / 2)
    y0 = Inches(1.95)
    ch = Inches(3.6)
    for i, item in enumerate(cards):
        x = x0 + i * (cw + gap)
        rect(s, x, y0, cw, ch, C_BG)
        rect(s, x, y0, cw, Inches(0.07), C_BLUE)
        textbox(s, x + Inches(0.2), y0 + Inches(0.34), cw - Inches(0.4), Inches(0.45), item[0], 16, True, C_DARK)
        textbox(s, x + Inches(0.2), y0 + Inches(0.95), cw - Inches(0.4), ch - Inches(1.1), item[1], 11, False, C_SUB, spacing=1.7)
    rect(s, Inches(0.85), Inches(6.92), Inches(11.63), Inches(0.008), C_LINE)
    textbox(s, Inches(0.85), Inches(7.0), Inches(7.0), Inches(0.28), 'MYTECH 名扬时代  |  试用期述职报告', 10, False, C_SUB)
    return s

'''

A1 = '# ---------------- 1 封面 ----------------'
if 'def cards_slide' not in s:
    s = s.replace(A1, FUNC + A1, 1)

# 原有页 4~11 后移一位
for n in range(11, 3, -1):
    s = s.replace('], %d)' % n, '], @@%d@@)' % (n + 1))
s = s.replace('@@', '')

CALL = '''# ---------------- 3.5 产品线覆盖 ----------------
cards_slide('业务覆盖 · 产品线', 'PRODUCT   LINES', [
    ('光电转台', '电机参数整定、自检撞头与角度偏差、限位与回零'),
    ('布控球', '画面异常与开机花屏、电量显示与低电保护、光敏切换'),
    ('车载球机', '翻转异常、角度不准、协议适配'),
    ('T 型云台', '电机调参、零位机芯对接、运动平稳性'),
    ('安防球机', '预置位与巡航调用、云台报警查询、协议解析'),
], 4)

'''
A4 = '# ---------------- 4 电机控制 ----------------'
if '业务覆盖 · 产品线' not in s:
    s = s.replace(A4, CALL + A4, 1)

s = s.replace('四条主线：电机控制、云台功能与逻辑、电源与显示、配件模块移植、调试与排障',
              '五条主线：电机控制、云台功能与逻辑、电源与显示、配件模块移植、调试与排障')
s = s.replace("'BLDC 的 FOC：Clarke / Park 变换、SVPWM 调制、电流采样与反 Park、电角度对齐',",
              "'伺服与步进两套传动：BLDC 的 FOC（Clarke / Park、SVPWM、电流采样与反 Park、电角度对齐）',")

io.open(P1, 'w', encoding='cp936', newline='').write(s.replace('\n', '\r\n'))
print('pptx: cards_func=%d cards_call=%d wutiao=%d servo=%d'
      % (s.count('def cards_slide'), s.count('业务覆盖 · 产品线'), s.count('五条主线'), s.count('两套传动')))

# ================= html =================
P2 = r'D:\Codebuddy\tools\gen_html.py'
h = io.open(P2, encoding='cp936', newline='').read().replace('\r\n', '\n')

CSS_ADD = """\
.cards .grid { display:flex; gap:18px; margin-top:8px; }
.cards .card { flex:1; background:#f4f7fb; border-top:5px solid #1e6fba; padding:22px 18px; min-height:330px; }
.cards .card h3 { margin:0 0 14px; font-size:17px; color:#0e2a47; }
.cards .card p { margin:0; font-size:13px; line-height:2.0; color:#6b7481; }
"""
if '.cards .grid' not in h:
    h = h.replace('@media print {', CSS_ADD + '\n@media print {', 1)

CARDS = """CARDS_HTML = (
    '<section class="slide cards">'
    '<div class="bar"></div>'
    '<h1>业务覆盖 · 产品线</h1>'
    '<div class="en">PRODUCT LINES</div>'
    '<div class="pg">04</div>'
    '<div class="hr"></div>'
    '<div class="grid">'
    '<div class="card"><h3>光电转台</h3><p>电机参数整定<br>自检撞头与角度偏差<br>限位与回零</p></div>'
    '<div class="card"><h3>布控球</h3><p>画面异常与开机花屏<br>电量显示与低电保护<br>光敏切换</p></div>'
    '<div class="card"><h3>车载球机</h3><p>翻转异常<br>角度不准<br>协议适配</p></div>'
    '<div class="card"><h3>T 型云台</h3><p>电机调参<br>零位机芯对接<br>运动平稳性</p></div>'
    '<div class="card"><h3>安防球机</h3><p>预置位与巡航调用<br>云台报警查询<br>协议解析</p></div>'
    '</div>'
    '<div class="foot">MYTECH 名扬时代  |  试用期述职报告</div>'
    '</section>'
)

"""

OLD_LOOP = """for t, en, items, pg in body:
    parts.append(slide(t, en, items, pg))"""
NEW_LOOP = """for t, en, items, pg in body:
    parts.append(slide(t, en, items, pg if pg < 4 else pg + 1))
    if pg == 3:
        parts.append(CARDS_HTML)"""

if 'CARDS_HTML' not in h:
    h = h.replace('for t, en, items, pg in body:', CARDS + 'for t, en, items, pg in body:', 1)
    h = h.replace(OLD_LOOP, NEW_LOOP, 1)

h = h.replace('四条主线：电机控制、云台功能与逻辑、电源与显示、配件模块移植、调试与排障',
              '五条主线：电机控制、云台功能与逻辑、电源与显示、配件模块移植、调试与排障')
h = h.replace("'BLDC 的 FOC：Clarke / Park 变换、SVPWM 调制、电流采样与反 Park、电角度对齐',",
              "'伺服与步进两套传动：BLDC 的 FOC（Clarke / Park、SVPWM、电流采样与反 Park、电角度对齐）',")

io.open(P2, 'w', encoding='cp936', newline='').write(h.replace('\n', '\r\n'))
print('html: cards=%d wutiao=%d servo=%d loop=%d'
      % (h.count('CARDS_HTML'), h.count('五条主线'), h.count('两套传动'), h.count('if pg == 3')))
