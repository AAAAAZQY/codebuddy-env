# -*- coding: cp936 -*-
"""从 25107 匀速数据生成 36 点角度前馈补偿表"""
import io
import struct

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TAIL = b'\x00\x00\x80\x7f'
DT = 0.05
BINS = 36

raw = io.open(r'D:\Codebuddy\tmp\vofa_hex12.txt', encoding='utf-8').read()
toks = [t for t in raw.split() if len(t) == 2]
data = bytes(int(t, 16) for t in toks)
fr = []
i = 0
while i + 24 <= len(data):
    c = data[i:i + 24]
    if c[20:24] == TAIL:
        fr.append(struct.unpack('<5f', c[:20]))
        i += 24
    else:
        i += 1

rm = sorted(f[1] for f in fr)[len(fr) // 2]
sel = [f for f in fr if abs(f[1] - rm) < max(1.0, abs(rm) * 5e-3)]
print('total=%d  steady=%d  r=%.0f (%.1f deg/s)' % (len(fr), len(sel), rm, rm / 100.0))

ang = 0.0
buckets = [[] for _ in range(BINS)]
for f in sel:
    idx = int((ang % 360.0) // (360.0 / BINS))
    buckets[idx].append(f[3])
    ang += (f[0] / 100.0) * DT

print('steady angle = %.0f deg = %.2f turns' % (ang, ang / 360.0))

means = []
for b in range(BINS):
    v = buckets[b]
    means.append(sum(v) / len(v) if v else None)
    print('  bin %2d (%3d-%3d deg): mean=%7.1f  n=%d'
          % (b, b * 10, b * 10 + 10, means[-1] if v else -1, len(v)))

valid = [m for m in means if m is not None]
overall = sum(valid) / len(valid)
print('overall mean Uq = %.1f' % overall)

comp = [round(m - overall) for m in means]

# 3 点循环平滑
sm = []
for b in range(BINS):
    sm.append(round((comp[(b - 1) % BINS] + comp[b] + comp[(b + 1) % BINS]) / 3.0))

print()
print('补偿表 (每 10 度, 单位同 target_Uq):')
print('static const int16_t uq_comp_36[36] = {')
for row in range(0, 36, 6):
    vals = ', '.join('%4d' % v for v in sm[row:row + 6])
    print('    ' + vals + ',   /* %3d - %3d deg */' % (row * 10, (row + 6) * 10))
print('};')
print()
print('raw range: %d ~ %d,  smoothed range: %d ~ %d'
      % (min(comp), max(comp), min(sm), max(sm)))
