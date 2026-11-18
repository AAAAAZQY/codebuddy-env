# -*- coding: gbk -*-
"""在源码目录写一个测试文件，用于判断 Python 写入是否会被加密。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'd:\plain_view\66T\mis-t160-XH-ptz\application\_enc_test.txt'
io.open(P, 'w', encoding='ascii', newline='').write(
    '#include "test.h"\r\nint a = 1;\r\n')
print('python 已写入:', P)
