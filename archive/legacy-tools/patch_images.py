# -*- coding: cp936 -*-
"""第 3 页、第 6 页改为左文右图，插入 H260 / T50 产品图"""
import io

# ================= pptx =================
P1 = r'D:\Codebuddy\tools\gen_pptx.py'
s = io.open(P1, encoding='cp936', newline='').read().replace('\r\n', '\n')

FUNC = '''IMG_DIR = r'D:\\Codebuddy\\tools\\media'


def add_pic(slide, name, x, y, max_w, max_h):
    from PIL import Image
    p = os.path.join(IMG_DIR, name)
    iw, ih = Image.open(p).size
    r = min(float(max_w) / iw, float(max_h) / ih)
    w = int(iw * r)
    h = int(ih * r)
    left = int(x + (max_w - w) / 2)
    top = int(y + (max_h - h) / 2)
    return slide.shapes.add_picture(p, left, top, width=w, height=h)


def content_img_slide(title, en, items, page, img):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, prs.slide_width, prs.slide_height, C_WHITE)
    rect(s, Inches(0.85), Inches(0.72), Inches(0.075), Inches(0.44), C_BLUE)
    textbox(s, Inches(1.05), Inches(0.66), Inches(9.0), Inches(0.55), title, 27, True, C_DARK)
    textbox(s, Inches(1.06), Inches(1.14), Inches(6.0), Inches(0.3), en, 11, False, C_SUB)
    textbox(s, Inches(11.2), Inches(0.72), Inches(1.3), Inches(0.4), '%02d' % page, 20, True, RGBColor(0xC3, 0xCD, 0xDA), PP_ALIGN.RIGHT)
    rect(s, Inches(0.85), Inches(1.52), Inches(11.63), Inches(0.012), C_LINE)
    bullets(s, Inches(0.95), Inches(1.88), Inches(7.05), Inches(4.55), items, size=17, gap=13)
    add_pic(s, img, Inches(8.3), Inches(1.8), Inches(4.15), Inches(4.55))
    rect(s, Inches(0.85), Inches(6.92), Inches(11.63), Inches(0.008), C_LINE)
    textbox(s, Inches(0.85), Inches(7.0), Inches(7.0), Inches(0.28), 'MYTECH 名扬时代  |  试用期述职报告', 10, False, C_SUB)
    return s


'''

A = 'def cards_slide(title, en, cards, page):'
if 'content_img_slide' not in s:
    s = s.replace(A, FUNC + A, 1)

# 第 3 页
s = s.replace("content_slide('试用期回顾 · 总览', 'OVERVIEW', [",
              "content_img_slide('试用期回顾 · 总览', 'OVERVIEW', [", 1)
s = s.replace('], 3)', "], 3, 'h260.png')", 1)

# 第 6 页
s = s.replace("content_slide('云台功能与逻辑', 'GIMBAL   FEATURES', [",
              "content_img_slide('云台功能与逻辑', 'GIMBAL   FEATURES', [", 1)
s = s.replace('], 6)', "], 6, 't50.png')", 1)

io.open(P1, 'w', encoding='cp936', newline='').write(s.replace('\n', '\r\n'))
print('pptx: img_slide=%d h260=%d t50=%d' % (s.count('content_img_slide'), s.count('h260.png'), s.count('t50.png')))

# ================= html =================
P2 = r'D:\Codebuddy\tools\gen_html.py'
h = io.open(P2, encoding='cp936', newline='').read().replace('\r\n', '\n')

CSS_ADD = """\
.split { display:flex; gap:26px; align-items:flex-start; }
.split .txt { flex:0 0 690px; }
.split .pic { flex:1; text-align:center; }
.split .pic img { max-width:100%; max-height:430px; }
"""
if '.split .pic' not in h:
    h = h.replace('.toc .left {', CSS_ADD + '.toc .left {', 1)

# slide() 支持 img
OLD_SIG = "def slide(title, en, items, page):"
NEW_SIG = "def slide(title, en, items, page, img=None):"
h = h.replace(OLD_SIG, NEW_SIG, 1)

OLD_RET = """    return (
        '<section class="slide">\\n'
        '  <div class="bar"></div>\\n'
        '  <h1>%s</h1>\\n'
        '  <div class="en">%s</div>\\n'
        '  <div class="pg">%02d</div>\\n'
        '  <div class="hr"></div>\\n'
        '  <ul>\\n    %s\\n  </ul>\\n'
        '  <div class="foot">MYTECH 名扬时代  |  试用期述职报告</div>\\n'
        '</section>\\n' % (esc(title), esc(en), page, '\\n    '.join(lis))
    )"""
NEW_RET = """    body = '<ul>\\n    %s\\n  </ul>' % ('\\n    '.join(lis))
    if img:
        body = ('<div class="split"><div class="txt">' + body +
                '</div><div class="pic"><img src="' + img + '"></div></div>')
    return (
        '<section class="slide">\\n'
        '  <div class="bar"></div>\\n'
        '  <h1>%s</h1>\\n'
        '  <div class="en">%s</div>\\n'
        '  <div class="pg">%02d</div>\\n'
        '  <div class="hr"></div>\\n'
        '  %s\\n'
        '  <div class="foot">MYTECH 名扬时代  |  试用期述职报告</div>\\n'
        '</section>\\n' % (esc(title), esc(en), page, body)
    )"""
if 'class="split"' not in h:
    h = h.replace(OLD_RET, NEW_RET, 1)

OLD_LOOP = """for t, en, items, pg in body:
    parts.append(slide(t, en, items, pg if pg < 4 else pg + 1))
    if pg == 3:
        parts.append(CARDS_HTML)"""
NEW_LOOP = """IMGS = {3: 'media/h260.png', 6: 'media/t50.png'}
for item in body:
    t, en, items, pg = item[0], item[1], item[2], item[3]
    parts.append(slide(t, en, items, pg if pg < 4 else pg + 1, IMGS.get(pg)))
    if pg == 3:
        parts.append(CARDS_HTML)"""
if 'IMGS = {' not in h:
    h = h.replace(OLD_LOOP, NEW_LOOP, 1)

io.open(P2, 'w', encoding='cp936', newline='').write(h.replace('\n', '\r\n'))
print('html: split_css=%d imgs=%d' % (h.count('.split .pic'), h.count('IMGS = {')))
