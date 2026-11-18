# -*- coding: gbk -*-
"""统计全篇字体/字号，按“角色”归类，找出不统一的地方。"""
import re
import sys
from collections import Counter, defaultdict

from pptx import Presentation

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'C:\Users\myages2026\Desktop\试用期述职报告_赵庆斌_v8.pptx'
prs = Presentation(SRC)


def role_of(txt):
    t = txt.strip()
    if re.match(r'^\d+\s*/\s*17$', t):
        return 'pagenum'
    if 'MYTECH' in t:
        return 'footer'
    if re.match(r'^\d{2}$', t):
        return 'section_num'
    if re.match(r'^\d+$', t):
        return 'bignum'
    if re.fullmatch(r'[A-Z0-9 &\.\-]+', t):
        return 'english'
    if t.startswith('—') or t.startswith('·'):
        return 'body'
    return 'title'


stats = defaultdict(Counter)
detail = defaultdict(list)

for si, slide in enumerate(prs.slides, 1):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            txt = ''.join(r.text for r in p.runs)
            if not txt.strip():
                continue
            role = role_of(txt)
            for r in p.runs:
                if not r.text.strip():
                    continue
                key = (r.font.name, r.font.size.pt if r.font.size else None,
                       bool(r.font.bold))
                stats[role][key] += 1
                detail[role].append((si, key, txt.strip()[:40]))

for role in ('title', 'body', 'english', 'footer', 'pagenum',
             'section_num', 'bignum'):
    if role not in stats:
        continue
    print('=' * 70)
    print('角色: %s' % role)
    print('=' * 70)
    for key, cnt in stats[role].most_common():
        name, size, bold = key
        print('   %-16s %-6s bold=%-5s  x%d' % (name, size, bold, cnt))
    print('   -- 明细(仅列出与最常见组合不同的) --')
    top = stats[role].most_common(1)[0][0]
    for si, key, txt in detail[role]:
        if key != top:
            print('     S%-2d %-16s %-6s  %s'
                  % (si, key[0], key[1], txt))
    print('')
