# -*- coding: gbk -*-
"""测试: python 写临时文件 -> cmd copy 覆盖目标, 是否仍被加密。"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

D = r'd:\plain_view\66T\mis-t160-XH-ptz\application'
SRC = os.path.join(D, '_t_src.txt')
DST = os.path.join(D, '_t_dst.txt')

io.open(SRC, 'w', encoding='ascii', newline='').write(
    '#include "t.h"\r\nint b = 2;\r\n')
if os.path.exists(DST):
    os.remove(DST)
r = subprocess.run(['cmd', '/c', 'copy', '/b', SRC, DST],
                   capture_output=True, text=True)
print('cmd copy 返回:', r.returncode, r.stdout.strip()[:60])
print('目标存在:', os.path.exists(DST))
print('SRC=%s' % SRC)
print('DST=%s' % DST)
