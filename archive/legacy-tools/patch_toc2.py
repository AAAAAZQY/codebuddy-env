# -*- coding: cp936 -*-
"""同步目录描述与新结构"""
import io
import sys

PAIRS = [
    ("'产品线 / 电机控制 / 云台功能 / 电源与显示 / 配件移植'",
     "'17 个项目 / 五个方向 / 模块移植 / 调试排障'"),
    ("'技术能力 / 排查方法 / 工程习惯'",
     "'技术 / 架构 / 方法 / 协作'"),
]

for p in sys.argv[1:]:
    s = io.open(p, encoding='cp936', newline='').read()
    hit = 0
    for old, new in PAIRS:
        if old in s:
            s = s.replace(old, new)
            hit += 1
        else:
            print('MISS %s : %s' % (p, old[:20]))
    io.open(p, 'w', encoding='cp936', newline='').write(s)
    print('%s  toc_replaced=%d' % (p, hit))
