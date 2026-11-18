# -*- coding: cp936 -*-
"""按等角度重采样后做 FFT，求每圈振荡次数（比找极值可靠）"""
import io
import struct

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TAIL = b'\x00\x00\x80\x7f'
DT = 0.05


def load(path):
    raw = io.open(path, encoding='utf-8').read()
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
    return fr


def analyze(path, tag):
    fr = load(path)
    # 累积角度
    ang = [0.0]
    for f in fr[:-1]:
        ang.append(ang[-1] + (f[0] / 100.0) * DT)
    total = ang[-1]
    print('=== %s ===' % tag)
    print('  frames=%d  total=%.0f deg = %.2f turns' % (len(fr), total, total / 360.0))

    # 按每 2 度重采样
    step = 2.0
    grid = []
    a = 0.0
    k = 0
    while a <= total and k < len(fr):
        while k + 1 < len(fr) and ang[k + 1] < a:
            k += 1
        grid.append(fr[k][3])          # Uq
        a += step
    n = len(grid)
    if n < 32:
        print('  too few samples')
        return
    mean = sum(grid) / n
    x = [v - mean for v in grid]

    # 简单 DFT，扫描"每圈次数" 0.5 ~ 40
    turns = total / 360.0
    best = []
    f = 0.5
    while f <= 40:
        # 频率 f 次/圈 -> 每步角度 = 360/(f*step) 步
        omega = 2.0 * 3.141592653589793 * f * (step / 360.0)
        re = 0.0
        im = 0.0
        for i, v in enumerate(x):
            re += v * __import__('math').cos(omega * i)
            im -= v * __import__('math').sin(omega * i)
        mag = (re * re + im * im) ** 0.5
        best.append((f, mag))
        f += 0.1
    best.sort(key=lambda t: -t[1])
    print('  top peaks (cycles per turn):')
    for f, m in best[:6]:
        print('    %.1f /turn   mag=%.0f' % (f, m))
    print()


analyze(r'D:\Codebuddy\tmp\vofa_hex12.txt', '25107 (4.16 turns)')
analyze(r'D:\Codebuddy\tmp\vofa_hex11.txt', '7146 (1.5 turns)')
