# -*- coding: gbk -*-
"""恢复 motor_bldc.c 的 CRLF 行尾（此前被 python 写成了 LF）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = r'd:\plain_view\66T\mis-t160-XH-ptz\application\motor_bldc.c'
MID = r'D:\Codebuddy\tmp\mb_crlf.csv'

raw = open(SRC, 'rb').read()
crlf = raw.count(b'\r\n')
lf_only = raw.count(b'\n') - crlf
print('当前: %d 字节, CRLF=%d, 裸 LF=%d' % (len(raw), crlf, lf_only))

# 统一成 LF 再按 CRLF 写出
txt = raw.decode('gbk', 'replace').replace('\r\n', '\n')
out = txt.replace('\n', '\r\n').encode('gbk', 'replace')
io.open(MID, 'wb').write(out)
print('已生成 CRLF 版本: %d 字节 (%d 行)' % (len(out), txt.count('\n')))
