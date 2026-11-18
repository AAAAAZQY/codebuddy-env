# -*- coding: cp936 -*-
"""从 pptx 直接生成 HTML 预览，保证内容与 PPT 完全一致"""
import glob
import html
import os
import sys

from pptx import Presentation

desk = os.path.join(os.path.expanduser('~'), 'Desktop')
src = sys.argv[1] if len(sys.argv) > 1 else sorted(
    glob.glob(os.path.join(desk, '试用期述职报告*.pptx')), key=os.path.getmtime)[-1]
prs = Presentation(src)

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#dfe5ee;font-family:"微软雅黑","Microsoft YaHei",system-ui,sans-serif;color:#353c45}
.slide{position:relative;width:1280px;height:720px;margin:26px auto;background:#fff;
 box-shadow:0 10px 30px rgba(16,40,70,.16);padding:56px 66px;overflow:hidden;page-break-after:always}
.slide.dark{background:#0e2a47;color:#fff}
.slide h1{margin:0;font-size:30px;color:#0e2a47}
.slide.dark h1{color:#fff}
.slide .bar{position:absolute;left:66px;top:58px;width:7px;height:42px;background:#3e9add}
.slide .hd{margin-left:22px}
.slide .en{font-size:11px;color:#6b7481;letter-spacing:2px;margin-top:4px}
.slide.dark .en{color:#3e9add}
.slide .hr{height:1px;background:#d8dfe8;margin:24px 0 26px}
.slide.dark .hr{background:#2a4a6b}
.slide .pg{position:absolute;right:66px;top:56px;font-size:12px;color:#c3cdda}
.slide .foot{position:absolute;left:66px;bottom:22px;font-size:10px;color:#8b95a3;letter-spacing:1px}
.slide ul{list-style:none;margin:0;padding:0}
.slide li{position:relative;padding-left:26px;margin-bottom:14px;font-size:17px;line-height:1.65}
.slide li:before{content:"■";position:absolute;left:0;top:0;color:#1e6fba;font-size:13px}
.slide li.sub{color:#6b7481;font-size:15px;padding-left:46px}
.slide li.sub:before{content:"·";left:28px;color:#9aa6b5;font-size:17px}
.cover{background:#0e2a47;color:#fff;padding:0}
.cover .side{position:absolute;left:0;top:0;width:26px;height:100%;background:#1e6fba}
.cover .wrap{position:absolute;left:150px;top:250px}
.cover h2{margin:0;font-size:46px;letter-spacing:2px}
.cover .sub{margin-top:14px;font-size:13px;color:#3e9add;letter-spacing:4px}
.cover .meta{margin-top:40px;font-size:15px;line-height:2.1;color:#c9d6e4}
.end{background:#0e2a47;color:#fff;padding:0}
.end .wrap{position:absolute;left:150px;top:300px}
.end h2{margin:0;font-size:44px;letter-spacing:8px}
.end p{margin-top:26px;font-size:15px;color:#c9d6e4}
.nav{position:fixed;right:16px;bottom:12px;font-size:12px;color:#7b8492;background:rgba(255,255,255,.92);
 padding:6px 12px;border-radius:14px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
@media print{body{background:#fff}.slide{margin:0;box-shadow:none}.nav{display:none}}
"""

parts = []
for idx, slide in enumerate(prs.slides, 1):
    shapes = [sh for sh in slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    texts = []
    for sh in shapes:
        for p in sh.text_frame.paragraphs:
            t = ''.join(r.text for r in p.runs).strip()
            if t:
                texts.append(t)
    dark = idx in (1, 2, 8, 10, 12)

    if idx == 1:
        parts.append(
            '<section class="slide cover"><div class="side"></div><div class="wrap">'
            '<h2>' + html.escape(texts[0] if texts else '') + '</h2>'
            '<div class="sub">' + html.escape(texts[1] if len(texts) > 1 else '') + '</div>'
            '<div class="meta">' + '<br>'.join(html.escape(t) for t in texts[2:]) + '</div>'
            '</div></section>')
        continue
    if idx == len(prs.slides):
        parts.append(
            '<section class="slide end"><div class="side"></div><div class="wrap">'
            '<h2>' + html.escape(texts[0] if texts else '谢谢') + '</h2>'
            '<p>' + html.escape(texts[1] if len(texts) > 1 else '') + '</p>'
            '</div></section>')
        continue

    title = texts[0] if texts else ''
    en = texts[1] if len(texts) > 1 else ''
    body = texts[2:]
    lis = []
    for t in body:
        cls = ' class="sub"' if (t.startswith('·') or t.startswith('—')) else ''
        lis.append('<li%s>%s</li>' % (cls, html.escape(t)))
    parts.append(
        '<section class="slide%s">' % (' dark' if dark else '') +
        '<div class="bar"></div><div class="hd"><h1>%s</h1><div class="en">%s</div></div>'
        '<div class="pg">%02d / %d</div><div class="hr"></div><ul>%s</ul>'
        '<div class="foot">MYTECH 名扬时代  |  试用期述职报告</div></section>'
        % (html.escape(title), html.escape(en), idx, len(prs.slides), ''.join(lis)))

out = os.path.join(desk, '试用期述职报告_预览.html')
doc = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
       '<title>试用期述职报告 - 赵庆斌</title><style>' + CSS + '</style></head><body>'
       + ''.join(parts) +
       '<div class="nav">← → 翻页 ｜ F 全屏 ｜ Ctrl+P 导出 PDF</div>'
       '<script>var i=0,s=document.querySelectorAll(".slide");'
       'function go(n){i=Math.max(0,Math.min(s.length-1,n));s[i].scrollIntoView({behavior:"smooth",block:"center"})}'
       'document.addEventListener("keydown",function(e){'
       'if(e.key==="ArrowRight"||e.key===" "||e.key==="PageDown"){e.preventDefault();go(i+1)}'
       'if(e.key==="ArrowLeft"||e.key==="PageUp"){e.preventDefault();go(i-1)}'
       'if(e.key==="f"||e.key==="F"){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()}});'
       '</script></body></html>')

with open(out, 'w', encoding='utf-8') as f:
    f.write(doc)
print('SAVED ' + out)
print('slides', len(prs.slides), 'size', os.path.getsize(out))
