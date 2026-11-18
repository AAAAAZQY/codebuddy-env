# -*- coding: gbk -*-
"""Run the new no-step fitting on the real data that failed step identification."""
import importlib.util
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location(
    'pid_tuner', r'D:\bProject\pid_tuner\pid_tuner.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

rows = io.open(r'D:\Codebuddy\tmp\fw_uy.csv', encoding='utf-8').read().splitlines()[1:]
t, u, y = [], [], []
for ln in rows:
    p = ln.split(',')
    t.append(float(p[0]))
    u.append(float(p[1]))
    y.append(float(p[2]))

print('数据: %d 点, u %.0f..%.0f, y %.0f..%.0f' % (len(t), min(u), max(u), min(y), max(y)))
print('')
print(m._fit_report(y, u, t[1] - t[0], 0.0001))
