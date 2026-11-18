# -*- coding: gbk -*-
"""测一下降采样前后 analyze 的耗时。"""
import importlib.util
import io
import sys
import time

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
print('原始点数 %d' % len(t))

t2, u2, y2, _, k = m._decimate(t, u, y, None)
print('降采样 %d -> %d 点 (1/%d)' % (len(t), len(t2), k))
print('')

for tag, tt, uu, yy in (('原样', t, u, y), ('降采样', t2, u2, y2)):
    t0 = time.time()
    try:
        info, an = m.analyze(tt, uu, yy, mode='balanced',
                             do_optimize=True, do_robust=True, dt_ctrl=0.0001)
        kind = an.get('kind')
    except Exception as e:
        kind = 'ERR: %s' % e
    print('%-8s %6d 点  耗时 %6.2f s  路线=%s' % (tag, len(tt), time.time() - t0, kind))
