# -*- coding: cp936 -*-
"""验证 7.4Hz 是否为齿槽转矩：按电角度分箱统计 Uq"""
import io
import statistics
import struct
import sys

DATA = r'D:\Codebuddy\tmp\vofa_hex29.txt'
POLE_PAIRS = 10


def load(path):
    raw = io.open(path, encoding='utf-8').read()
    toks = [t for t in raw.split() if len(t) == 2]
    data = bytes(int(t, 16) for t in toks)
    tail = b'\x00\x00\x80\x7f'
    fr = []
    i = 0
    while i + 28 <= len(data):
        c = data[i:i + 28]
        if c[24:28] == tail:
            fr.append(struct.unpack('<6f', c[:24]))
            i += 28
        else:
            i += 1
    return fr


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    fr = load(DATA)
    st = [f for f in fr if abs(f[1] - 25107) < 2 and f[0] > 15000]
    print('steady frames:', len(st))

    nb = 72
    bins = [[] for _ in range(nb)]
    for f in st:
        ea = (f[5] * POLE_PAIRS) % 36000.0
        b = int(ea / (36000.0 / nb)) % nb
        bins[b].append(f[3])

    means = [statistics.mean(b) if b else None for b in bins]
    valid = [m for m in means if m is not None]
    avg = statistics.mean(valid)
    print('electrical-angle Uq: min=%.0f max=%.0f span=%.0f' % (min(valid), max(valid), max(valid) - min(valid)))
    print()
    print(' bin  elec_deg   Uq_mean   n   deviation')
    for b in range(nb):
        if means[b] is None:
            continue
        v = means[b] - avg
        bar = '#' * min(50, int(abs(v) / 10))
        sign = '+' if v >= 0 else '-'
        print(' %3d  %6.1f   %7.0f  %2d   %s%4.0f %s' % (b, b * 5.0, means[b], len(bins[b]), sign, abs(v), bar))

    # 机械角分箱对比
    bins2 = [[] for _ in range(36)]
    for f in st:
        bins2[int((f[5] % 36000) / 1000)].append(f[3])
    m2 = [statistics.mean(x) for x in bins2 if x]
    print()
    print('mechanical-angle(36 bins) Uq: min=%.0f max=%.0f span=%.0f' % (min(m2), max(m2), max(m2) - min(m2)))


if __name__ == '__main__':
    main()
