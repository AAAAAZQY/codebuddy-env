# -*- coding: cp936 -*-
"""仅当存在 _v2 文件时才把桌面主文件替换掉；否则什么都不做"""
import os

desk = os.path.join(os.path.expanduser('~'), 'Desktop')
old = os.path.join(desk, '试用期述职报告_赵庆斌_2026-10.pptx')
new = os.path.join(desk, '试用期述职报告_赵庆斌_2026-10_v2.pptx')

if not os.path.exists(new):
    print('no v2 file, nothing to do')
else:
    os.remove(old) if os.path.exists(old) else None
    os.rename(new, old)
    print('REPLACED -> %s (%d bytes)' % (old, os.path.getsize(old)))

for f in os.listdir(desk):
    if f.startswith('试用期述职报告'):
        print('  %s  %d bytes' % (f, os.path.getsize(os.path.join(desk, f))))
