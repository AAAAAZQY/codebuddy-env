# -*- coding: gbk -*-
"""第二轮: 机型名/空格修正 + 全篇字号统一。"""
import sys

from pptx import Presentation
from pptx.util import Pt

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v8.pptx'
prs = Presentation(SRC)

BODY_SIZE = 17.0     # 正文内容
DASH_SIZE = 15.0     # 段首破折号
TITLE_SIZE = 32.0    # 页面标题

changes = {'body': 0, 'dash': 0, 'title': 0, 'other': 0}


def pt(r):
    return round(r.font.size.pt, 1) if r.font.size else None


# ---------- 1. 文本修正 ----------
def fix_run(sno, shi, pi, ridx, expect, new):
    p = prs.slides[sno - 1].shapes[shi].text_frame.paragraphs[pi]
    assert p.runs[ridx].text == expect, \
        'S%d 期望 %r 实际 %r' % (sno, expect, p.runs[ridx].text)
    p.runs[ridx].text = new
    print('  文本 S%-2d run%d: %r -> %r' % (sno, ridx, expect, new))


# S8: 森曼 S100 -> SM S100, 并去掉冒号后的多余空格
fix_run(8, 5, 1, 1, '森曼 S100： OLED ', 'SM S100：OLED ')
# S5: OLED显示 -> OLED 显示
fix_run(5, 5, 1, 2, '显示：海洋王 6126b / 60d、球芯全系的开机花屏',
        ' 显示：海洋王 6126b / 60d、球芯全系的开机花屏')

# ---------- 2. 字号统一 ----------
for si, slide in enumerate(prs.slides, 1):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            txt = ''.join(r.text for r in p.runs)
            if not txt.strip():
                continue

            # 页面标题: 目前 34pt 的只有 4 个章节页标题
            if all(pt(r) == 34.0 for r in p.runs if r.text.strip()):
                for r in p.runs:
                    if r.text.strip():
                        r.font.size = Pt(TITLE_SIZE)
                changes['title'] += 1
                continue

            # 正文条目: 只处理以破折号开头的(以 · 开头的是补充说明, 保持原样)
            if txt.strip().startswith('—'):
                runs = [r for r in p.runs if r.text.strip()]
                for r in runs:
                    if r.text.strip() in ('—',):
                        r.font.size = Pt(DASH_SIZE)
                        changes['dash'] += 1
                    else:
                        r.font.size = Pt(BODY_SIZE)
                        changes['body'] += 1

# ---------- 3. 首页零散项 ----------
for sh in prs.slides[0].shapes:
    if not sh.has_text_frame:
        continue
    for p in sh.text_frame.paragraphs:
        for r in p.runs:
            if r.text.strip() == 'PROBATION   WORK   REVIEW':
                r.font.size = Pt(12.0)
                changes['other'] += 1
                print('  字号 S1 英文副标题 -> 12pt')
            elif r.text.strip().startswith('MYTECH 名扬时代电子'):
                r.font.size = Pt(9.5)
                changes['other'] += 1
                print('  字号 S1 公司名 -> 9.5pt')

prs.save(SRC)
print('')
print('已保存:', SRC)
print('字号调整: 标题 %d 段, 正文内容 %d 个 run, 破折号 %d 个 run, 其它 %d'
      % (changes['title'], changes['body'], changes['dash'], changes['other']))
