# -*- coding: cp936 -*-
"""第 5 步：默认通道映射改为只取 r,y（粘贴时走规则整定）"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'

src = io.open(TARGET, encoding='latin-1', newline='').read()
old = '_VOFA_MAP = "y=0,r=1,u=3"'
new = '_VOFA_MAP = "y=0,r=1"'

if src.count(old) != 1:
    print('anchor count =', src.count(old))
    sys.exit(1)

out = src.replace(old, new).encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('default map -> y=0,r=1   (bytes %d)' % len(out))
