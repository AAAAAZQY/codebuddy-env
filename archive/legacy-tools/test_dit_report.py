# -*- coding: utf-8 -*-
"""Call the GUI's _dit_report with synthetic dither data to verify integration."""
import importlib.util
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

spec = importlib.util.spec_from_file_location(
    'pid_tuner', r'D:\bProject\pid_tuner\pid_tuner.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

rows = io.open(r'D:\Codebuddy\tmp\synth_dither.csv', encoding='utf-8').read().splitlines()[1:]
t, u, y = [], [], []
for ln in rows:
    p = ln.split(',')
    t.append(float(p[0]))
    u.append(float(p[1]))
    y.append(float(p[2]))

print(m._dit_report(y, u, t[1] - t[0], 0.0001))
