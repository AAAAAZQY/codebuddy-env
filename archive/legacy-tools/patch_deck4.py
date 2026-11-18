# -*- coding: cp936 -*-
"""清掉目录页与注释里残留的稳像字样"""
import io
import sys

PAIRS = [
    ('电机控制 / 云台功能 / 稳像与配件 / 调试排障',
     '电机控制 / 云台功能 / 配件模块移植 / 调试排障'),
    ('# ---------------- 6 稳像与配件 ----------------',
     '# ---------------- 6 配件模块移植 ----------------'),
]

for p in sys.argv[1:]:
    s = io.open(p, encoding='cp936', newline='').read()
    for old, new in PAIRS:
        s = s.replace(old, new)
    io.open(p, 'w', encoding='cp936', newline='').write(s)
    print('%s  remain_wenxiang=%d' % (p, s.count('稳像')))
