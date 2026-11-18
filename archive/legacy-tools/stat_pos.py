# -*- coding: cp936 -*-
"""分析位置环表现：稳态段 pos_err 与 target_velocity 的波动"""
import io
import statistics
import struct

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TAIL = b'\x00\x00\x80\x7f'

raw = io.open(r'D:\Codebuddy\tmp\vofa_hex9.txt', encoding='utf-8').read()
toks = [t for t in raw.split() if len(t) == 2]
data = bytes(int(t, 16) for t in toks)
frames = []
i = 0
while i + 24 <= len(data):
    c = data[i:i + 24]
    if c[20:24] == TAIL:
        frames.append(struct.unpack('<5f', c[:20]))
        i += 24
    else:
        i += 1

print('frames =', len(frames))
print('列: y(实际速度) r(规划速度) pos_err(位置误差) u(Uq) tgt_vel(位置环输出)')

rm = statistics.median([f[1] for f in frames])
steady = [f for f in frames if abs(f[1] - rm) < max(1.0, abs(rm) * 1e-4)]
print('r_median=%.0f  稳态帧=%d / %d' % (rm, len(steady), len(frames)))

if len(steady) >= 10:
    for idx, name in ((0, 'y  实际速度'), (2, 'pos_err'), (3, 'u  Uq'),
                      (4, 'tgt_vel')):
        v = [f[idx] for f in steady]
        print('  %-12s min=%9.0f  max=%9.0f  span=%8.0f  std=%7.1f'
              % (name, min(v), max(v), max(v) - min(v), statistics.pstdev(v)))

    # 相邻帧变化量（看是否高频抖动）
    pe = [f[2] for f in steady]
    tv = [f[4] for f in steady]
    d_pe = [abs(pe[k + 1] - pe[k]) for k in range(len(pe) - 1)]
    d_tv = [abs(tv[k + 1] - tv[k]) for k in range(len(tv) - 1)]
    print('  相邻帧变化: pos_err 平均 %.0f 最大 %.0f'
          % (statistics.mean(d_pe), max(d_pe)))
    print('              tgt_vel 平均 %.0f 最大 %.0f'
          % (statistics.mean(d_tv), max(d_tv)))

    # 打印一段明细
    print()
    print('  帧   y       r      pos_err   u     tgt_vel')
    for k in range(0, min(24, len(steady))):
        f = steady[k]
        print('  %3d %7.0f %7.0f %8.0f %7.0f %8.0f'
              % (k, f[0], f[1], f[2], f[3], f[4]))
