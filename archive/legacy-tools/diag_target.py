# -*- coding: gbk -*-
"""检查编译目录那份文件是否被加密软件改写，并对比两份字节。"""
import hashlib
import io
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

M = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
T = (r'd:\aMyProject\Project\MIS-T160\XH\mis-t160\ptz_source_code'
     r'\source_code\application\motor_bldc.c')

for tag, p in (('mirror', M), ('target', T)):
    raw = open(p, 'rb').read()
    st = os.stat(p)
    ctrl = sum(1 for b in raw if b < 0x09 or (0x0E <= b <= 0x1F) or b == 0x7F)
    print('%-7s %6d 字节  %s  控制字符 %d' %
          (tag, len(raw), time.strftime('%H:%M:%S', time.localtime(st.st_mtime)), ctrl))
    print('        头 64 字节 : %r' % raw[:64])
    print('        sha256     : %s' % hashlib.sha256(raw).hexdigest()[:16])
    for mark in (b'%TSD-Header-', b'\x00\x00\x00\x00' * 2):
        if mark in raw[:512]:
            print('        !! 发现加密标记: %r' % mark[:16])
    print('')

a = open(M, 'rb').read()
b = open(T, 'rb').read()
print('两份相同: %s' % (a == b))
if a != b:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            print('首个差异在偏移 %d: mirror=%r target=%r'
                  % (i, a[max(0, i - 8):i + 8], b[max(0, i - 8):i + 8]))
            break
