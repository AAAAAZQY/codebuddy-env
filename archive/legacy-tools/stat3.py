# -*- coding: cp936 -*-
"""只统计 r 恒定的稳态段"""
import io
import statistics
import struct

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TAIL = b'\x00\x00\x80\x7f'


def load(path):
    raw = io.open(path, encoding='utf-8').read()
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
    return frames


for name, path in (('Kp=0.7 (旧, r=25107)', r'D:\Codebuddy\tmp\vofa_hex6.txt'),
                   ('Kp=0.56 (新, r=20039)', r'D:\Codebuddy\tmp\vofa_hex7.txt')):
    fr = load(path)
    rm = statistics.median([f[1] for f in fr])
    steady = [f for f in fr if abs(f[1] - rm) < max(1.0, abs(rm) * 1e-4)]
    if len(steady) < 10:
        print(name, '稳态帧太少', len(steady))
        continue
    y = [f[0] for f in steady]
    u = [f[3] for f in steady]
    span = max(y) - min(y)
    sd = statistics.pstdev(y)
    sat = sum(1 for v in u if abs(v) >= 3990) / len(u) * 100
    print('=== %s ===' % name)
    print('  稳态帧=%d / 总帧=%d' % (len(steady), len(fr)))
    print('  y: min=%.0f max=%.0f  span=%.0f (%.1f%%)  std=%.0f (%.2f%%)'
          % (min(y), max(y), span, span / abs(rm) * 100, sd, sd / abs(rm) * 100))
    print('  u: min=%.0f max=%.0f  |u|>=3990: %.1f%%'
          % (min(u), max(u), sat))
    print()
