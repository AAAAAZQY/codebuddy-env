# -*- coding: cp936 -*-
"""对比两次稳态段：波动幅度、Uq 是否仍顶限幅"""
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


for name, path in (('Kp=0.7 (旧)', r'D:\Codebuddy\tmp\vofa_hex6.txt'),
                   ('Kp=0.56 (新)', r'D:\Codebuddy\tmp\vofa_hex7.txt')):
    fr = load(path)
    if not fr:
        print(name, 'no frames')
        continue
    n = len(fr)
    y = [f[0] for f in fr]
    r = [f[1] for f in fr]
    u = [f[3] for f in fr]

    # 取后半段（稳态）统计
    half = fr[n // 2:]
    yh = [f[0] for f in half]
    rh = [f[1] for f in half]
    uh = [f[3] for f in half]

    r0 = statistics.median(rh)
    span = max(yh) - min(yh)
    sd = statistics.pstdev(yh)
    sat = sum(1 for v in uh if abs(v) >= 3990) / len(uh) * 100

    print('=== %s ===' % name)
    print('  frames=%d  r_median=%.0f' % (n, r0))
    print('  稳态 y: min=%.0f max=%.0f  span=%.0f (%.1f%% of r)  std=%.0f'
          % (min(yh), max(yh), span, span / abs(r0) * 100 if r0 else 0, sd))
    print('  稳态 u: min=%.0f max=%.0f  |u|>=3990 占比 %.1f%%'
          % (min(uh), max(uh), sat))
