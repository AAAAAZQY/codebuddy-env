# -*- coding: gbk -*-
"""在 XH 工程里找 0x51/0x53/0x59/0x5B 这几个指令码的处理位置。"""
import glob
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r'd:\plain_view\66T\mis-t160-XH-ptz'
files = glob.glob(ROOT + r'\**\*.c', recursive=True) + \
        glob.glob(ROOT + r'\**\*.h', recursive=True)

pat_code = re.compile(r'0x0*(51|53|59|5B|59u|5Bu)\b', re.I)
pat_name = re.compile(r'(ANGLE|angle|query_angle|QUERY)', re.I)

print('=== 含 0x51/0x53/0x59/0x5B 的行 ===')
for f in files:
    try:
        s = io.open(f, encoding='gbk', errors='replace').read()
    except Exception:                               # noqa: BLE001
        continue
    lines = s.splitlines()
    hit = []
    for i, l in enumerate(lines, 1):
        if re.search(r'0x5[13]\b|0x5[9bB]\b', l) or '0X5' in l.upper():
            if pat_code.search(l.replace(' ', '')) or re.search(r'0x5[139bB]', l, re.I):
                hit.append((i, l.strip()))
    if hit:
        print('')
        print('--- %s ---' % f.replace(ROOT, '...'))
        for i, l in hit[:12]:
            print('  %4d| %s' % (i, l[:110]))
