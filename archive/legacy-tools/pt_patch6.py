# -*- coding: cp936 -*-
"""第 6 步：窗口标题加标记，便于区分多份副本"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'


def L(s):
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()
old = L('    root.title(f"PID 自动整定器 v{__version__}")')
new = L('    root.title(f"PID 自动整定器 v{__version__}  [bProject · hex]")')

if src.count(old) != 1:
    print('anchor count =', src.count(old))
    sys.exit(1)

out = src.replace(old, new).encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('title tagged, bytes =', len(out))
