# -*- coding: gbk -*-
"""把源码导出到一个 .csv 中转文件（该扩展名不触发加密）。"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
MID = r'D:\Codebuddy\tmp\mb_mid.csv'

raw = open(SRC, 'rb').read()
print('python 读源: %d 字节' % len(raw))
print('  头: %r' % raw[:44])
ctrl = sum(1 for b in raw if b < 0x09 or (0x0E <= b <= 0x1F))
print('  控制字符: %d' % ctrl)
print('  含 uq_comp_18x: %s' % (b'uq_comp_18x' in raw))

open(MID, 'wb').write(raw)
print('已写出中转文件:', MID, os.path.getsize(MID), '字节')
