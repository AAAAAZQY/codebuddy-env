# -*- coding: cp936 -*-
"""目录页第一项描述补上电源与显示 / 配件移植"""
import io
import sys

OLD = "'电机控制 / 云台功能 / 配件模块移植 / 调试排障'"
NEW = "'产品线 / 电机控制 / 云台功能 / 电源与显示 / 配件移植'"

for p in sys.argv[1:]:
    s = io.open(p, encoding='cp936', newline='').read()
    if OLD in s:
        s = s.replace(OLD, NEW)
        io.open(p, 'w', encoding='cp936', newline='').write(s)
        print('updated ' + p)
    else:
        print('MISS ' + p)
