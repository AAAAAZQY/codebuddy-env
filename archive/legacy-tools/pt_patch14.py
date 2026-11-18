# -*- coding: cp936 -*-
"""第 14 步：vofa 帧长自动识别（支持 5 通道 24 字节 / 6 通道 28 字节）"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'

src = io.open(TARGET, encoding='latin-1', newline='').read()

old = '''    n = 5
    step = n * 4 + 4'''

new = '''    n = 5
    # 帧长自动识别: 找前两个帧尾之间的距离, 推算通道数
    _t1 = data.find(_VOFA_TAIL)
    if _t1 >= 0:
        _t2 = data.find(_VOFA_TAIL, _t1 + 4)
        if _t2 > _t1:
            _nc = (_t2 - _t1 - 4) // 4
            if 1 <= _nc <= 16:
                n = _nc
    step = n * 4 + 4'''

if src.count(old) != 1:
    print('anchor count =', src.count(old))
    sys.exit(1)

src = src.replace(old, new)
out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('patched, bytes =', len(out))
