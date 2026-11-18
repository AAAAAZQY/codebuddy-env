# -*- coding: gbk -*-
"""把源码目录里被加密的 motor_bldc.c 还原成明文：先导出到 tmp（明文区）。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
DST = r'D:\Codebuddy\tmp\motor_bldc_plain.c'

raw = open(SRC, 'rb').read()          # python 读到的是明文
print('源(明文视图) %d 字节' % len(raw))
print('控制字符: %d' % sum(1 for b in raw if b < 0x09 or (0x0E <= b <= 0x1F)))
print('头: %r' % raw[:40])

os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, 'wb').write(raw)
print('已导出明文副本:', DST)
