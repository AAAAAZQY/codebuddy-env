# -*- coding: cp936 -*-
"""用实测数据反推真实摩擦表：friction = 实测Uq - 当前补偿表"""
import io
import statistics
import struct

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TAIL = b'\x00\x00\x80\x7f'
BINS = 36

CUR = [402, 590, 529, 439, 391, 369,
       407, 304, 232, 201, 231, 152,
        41, -51, -66, -98, -223, -330,
      -425, -388, -463, -425, -466, -309,
      -300, -318, -350, -307, -152, -160,
       -88, -58, 89, 155, 140, 307]

raw = io.open(r'D:\Codebuddy\tmp\vofa_hex13.txt', encoding='utf-8').read()
toks = [t for t in raw.split() if len(t) == 2]
data = bytes(int(t, 16) for t in toks)
fr = []
i = 0
while i + 28 <= len(data):
    c = data[i:i + 28]
    if c[24:28] == TAIL:
        fr.append(struct.unpack('<6f', c[:24]))
        i += 28
    else:
        i += 1

rm = statistics.median(f[1] for f in fr)
steady = [f for f in fr if abs(f[1] - rm) < max(1.0, abs(rm) * 5e-3)]
print('steady frames =', len(steady), ' at r=%.0f' % rm)

buckets = [[] for _ in range(BINS)]
for f in steady:
    b = int((f[5] % 36000) / 1000)
    if 0 <= b < BINS:
        buckets[b].append(f[3])

meas = []
for b in range(BINS):
    v = buckets[b]
    meas.append(sum(v) / len(v) if v else None)

# friction = 实测Uq - 当前表补偿量  (只对补偿生效的帧成立, 速度>15000)
fric = []
for b in range(BINS):
    fric.append(meas[b] - CUR[b] if meas[b] is not None else None)

valid = [x for x in fric if x is not None]
mean_f = sum(valid) / len(valid)
print('mean friction level = %.0f' % mean_f)

new = []
for b in range(BINS):
    new.append(round(fric[b] - mean_f) if fric[b] is not None else 0)

# 3 点循环平滑
sm = [round((new[(b - 1) % BINS] + new[b] + new[(b + 1) % BINS]) / 3.0) for b in range(BINS)]

print()
print('物理含义: 正数=该角度阻力大(需要多加Uq), 负数=阻力小')
print('新补偿表:')
print('static const int16_t uq_comp_36[36] =')
print('{')
for row in range(0, 36, 6):
    print('    ' + ', '.join('%5d' % v for v in sm[row:row + 6]) + ',   /* %3d-%3d deg */'
          % (row * 10, (row + 6) * 10))
print('};')
print()
print('新表范围: %d ~ %d (峰峰 %d)' % (min(sm), max(sm), max(sm) - min(sm)))
print('旧表范围: %d ~ %d (峰峰 %d)' % (min(CUR), max(CUR), max(CUR) - min(CUR)))
