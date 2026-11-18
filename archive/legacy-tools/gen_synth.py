# -*- coding: gbk -*-
"""生成一份带 6 频激励的合成数据, 用来验证 dither_id.py 能否还原已知对象。"""
import cmath
import io
import math
import random
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FREQS = [1.5, 3.0, 4.5, 9.0, 14.5, 20.0]
AMP = 80.0
K, T, TAU = 6.45, 0.181, 0.012
UMEAN, YMEAN = 2272.0, 25107.0
DT, DUR = 0.01, 20.0

random.seed(7)
n = int(DUR / DT)
rows = []
for i in range(n):
    t = i * DT
    u = 0.0
    y = 0.0
    for f in FREQS:
        u += AMP * math.sin(2 * math.pi * f * t)
        P = K * cmath.exp(-1j * 2 * math.pi * f * TAU) / (1 + 1j * 2 * math.pi * f * T)
        y += abs(P) * AMP * math.sin(2 * math.pi * f * t + math.atan2(P.imag, P.real))
    u += UMEAN + random.uniform(-15, 15)
    y += YMEAN + random.uniform(-40, 40)
    rows.append('%.4f,%.4f,%.4f' % (t, u, y))

out = r'D:\Codebuddy\tmp\synth_dither.csv'
with io.open(out, 'w', encoding='utf-8', newline='') as fh:
    fh.write('time,u,y\n')
    fh.write('\n'.join(rows) + '\n')

print('truth: K=%.4f T=%.4f tau=%.4f' % (K, T, TAU))
print('written', out, len(rows), 'rows')
