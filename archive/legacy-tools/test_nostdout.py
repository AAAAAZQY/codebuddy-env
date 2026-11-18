# -*- coding: cp936 -*-
"""模拟 GUI 无控制台环境（sys.stdout = None）下粘贴 vofa 文本"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, r'D:\bProject\pid_tuner')
import pid_tuner as pt

raw = io.open(r'D:\Codebuddy\tmp\vofa_hex4.txt', encoding='utf-8').read()
oneline = " ".join(raw.split())

real = sys.stdout
result = []
sys.stdout = None          # 模拟 pythonw / 无控制台
try:
    t, u, y, r = pt.parse_data(oneline, dt=0.05)
    result.append('OK n=%d u_is_none=%s' % (len(t), u is None))
except Exception as exc:
    result.append('FAIL %s: %s' % (type(exc).__name__, exc))
finally:
    sys.stdout = real

print('stdout=None ->', result[0])
