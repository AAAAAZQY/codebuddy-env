# -*- coding: cp936 -*-
"""在总览与云台页补上电源/电量内容（只占一条，不单开页）"""
import io
import sys

PAIRS = [
    ('四条主线：电机控制、云台功能与逻辑、配件模块移植、调试与排障',
     '四条主线：电机控制、云台功能与逻辑、电源与显示、配件模块移植、调试与排障'),
    ('电源相关：电池电量检测与低电保护逻辑',
     '电源与电量：电量计算与低电保护逻辑，处理电量跳变与电源板开机花屏'),
]

for p in sys.argv[1:]:
    s = io.open(p, encoding='cp936', newline='').read()
    hit = 0
    for old, new in PAIRS:
        if old in s:
            s = s.replace(old, new)
            hit += 1
        else:
            print('MISS in %s : %s' % (p, old[:26]))
    io.open(p, 'w', encoding='cp936', newline='').write(s)
    print('%s  replaced=%d  has_power=%d' % (p, hit, s.count('电量')))
