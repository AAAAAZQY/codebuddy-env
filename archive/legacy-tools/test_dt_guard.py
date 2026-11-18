# -*- coding: gbk -*-
"""Verify the dt guard and that dt=0.01 produces sane P values."""
import importlib.util
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location(
    'pid_tuner', r'D:\bProject\pid_tuner\pid_tuner.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

rows = io.open(r'D:\Codebuddy\tmp\synth_dither.csv', encoding='utf-8').read().splitlines()[1:]
u, y = [], []
for ln in rows:
    p = ln.split(',')
    u.append(float(p[1]))
    y.append(float(p[2]))

print('=== dt = 1.0 (旧默认, 应当被拒绝) ===')
print(m._dit_report(y, u, 1.0, 0.0001)[:300])
print('')
print('=== dt = 0.01 (正确) ===')
print(m._dit_report(y, u, 0.01, 0.0001))
