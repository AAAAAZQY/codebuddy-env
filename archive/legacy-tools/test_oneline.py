# -*- coding: cp936 -*-
"""模拟 GUI 粘贴：整段 hex 压成一行的极端情况"""
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
print('oneline chars =', len(oneline), ' tokens =', len(oneline.split()))

t, u, y, r = pt.parse_data(oneline, dt=0.05)
print('parse ok: n=%d  u_is_none=%s  r_is_none=%s  vofa=%s'
      % (len(t), u is None, r is None, pt._VOFA_USED[0]))
