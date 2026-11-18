# -*- coding: cp936 -*-
"""验证：粘贴 vofa hex 文本能识别；普通 CSV 不被误判"""
import io
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

sys.path.insert(0, r'D:\bProject\pid_tuner')
import pid_tuner as pt

print('--- case 1: paste vofa hex text ---')
raw = io.open(r'D:\Codebuddy\tmp\vofa_hex4.txt', encoding='utf-8').read()
t, u, y, r = pt.parse_data(raw, dt=0.05)
print('  n=%d  u_is_none=%s  r_is_none=%s  vofa_used=%s'
      % (len(t), u is None, r is None, pt._VOFA_USED[0]))
if r is not None:
    print('  r[0],r[50],r[100] = %.0f %.0f %.0f' % (r[0], r[50], r[100]))

print('--- case 2: normal csv must NOT be mistaken ---')
rows = ["time,u,y"]
for i in range(20):
    rows.append("%.2f,%.2f,%.3f" % (i * 0.02, 0.2 if i < 9 else 0.7, 0.5 + 0.01 * i))
t2, u2, y2, r2 = pt.parse_data("\n".join(rows), dt=0.02)
print('  n=%d  u_is_none=%s  r_is_none=%s  u[0]=%s'
      % (len(t2), u2 is None, r2 is None, u2[0] if u2 else None))

print('--- case 3: two-column r,y csv ---')
rows3 = ["time,r,y"]
for i in range(20):
    rows3.append("%.1f,25107,%d" % (i * 0.1, 24000 + (i % 5) * 500))
t3, u3, y3, r3 = pt.parse_data("\n".join(rows3), dt=0.1)
print('  n=%d  u_is_none=%s  r[0]=%s' % (len(t3), u3 is None, r3[0] if r3 else None))
