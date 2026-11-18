# -*- coding: gbk -*-
"""VOFA JustFloat frame stats: segment split, ch0/ch5 noise, correlation, Uq clipping.

Frame: 6 x float32 le + tail 00 00 80 7F (28 bytes).
Default channel meaning (PAN, encoder-speed loop, ch5 = raw gyro):
  ch0 encoder velocity  ch1 plan velocity  ch2 position error
  ch3 target Uq         ch4 target velocity  ch5 IMU gyro (YAW=gz)*100

usage:
  python vofa_stats.py <hexfile>
  python vofa_stats.py <hexfile> --steady-th 24000
  python vofa_stats.py <hexfile> --csvout out.csv

Segments (from ch4 target velocity, the loop setpoint):
  accel   0 -> near max
  steady  ch4 >= th (default 0.95*max)
  decel   near max -> 0
"""
import io
import struct
import sys
import statistics as st


def load(path):
    raw = io.open(path, encoding='utf-8', errors='ignore').read()
    toks = [t for t in raw.replace('0x', ' ').replace('0X', ' ').split() if len(t) == 2]
    data = bytes(int(t, 16) for t in toks)
    frames = []
    i, n = 0, len(data)
    while i + 28 <= n:
        if data[i + 24:i + 28] == b'\x00\x00\x80\x7f':
            frames.append(struct.unpack('<6f', data[i:i + 24]))
            i += 28
        else:
            i += 1
    return frames, n


def corr(a, b):
    if len(a) < 2:
        return 0.0
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a)
    db = sum((y - mb) ** 2 for y in b)
    return num / ((da * db) ** 0.5) if da * db > 0 else 0.0


def djump(v):
    return [abs(v[k + 1] - v[k]) for k in range(len(v) - 1)]


def seg_report(frames, idx, name):
    if len(idx) < 3:
        print('[%s] too few frames (%d)' % (name, len(idx)))
        return
    ch = [[frames[i][k] for i in idx] for k in range(6)]
    c0, c5, uq = ch[0], ch[5], ch[3]
    d0, d5 = djump(c0), djump(c5)
    nz5 = sum(1 for x in d5 if x > 0)
    print('[%s] n=%d (%.2f s)' % (name, len(idx), len(idx) * 0.01))
    print('  ch0 enc : mean=%9.1f  std=%7.1f  pp=%7.0f  djump_med=%6.1f' %
          (st.mean(c0), st.pstdev(c0), max(c0) - min(c0), st.median(d0)))
    print('  ch5 gyro: mean=%9.1f  std=%7.1f  pp=%7.0f  djump_med=%6.1f' %
          (st.mean(c5), st.pstdev(c5), max(c5) - min(c5), st.median(d5)))
    print('  mean diff (ch5-ch0) = %.1f' % (st.mean(c5) - st.mean(c0)))
    print('  corr(ch0,ch5) = %.4f' % corr(c0, c5))
    print('  ch5 nonzero djump = %d/%d' % (nz5, len(d5)))
    print('  uq: max=%.0f mean=%.0f std=%.1f  clip(|uq|>=3999)=%d' %
          (max(uq), st.mean(uq), st.pstdev(uq), sum(1 for x in uq if abs(x) >= 3999)))
    print('')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        return
    path = args[0]

    th = None
    for a in sys.argv[1:]:
        if a.startswith('--steady-th'):
            th = float(a.split('=', 1)[1]) if '=' in a else None

    frames, nbytes = load(path)
    n = len(frames)
    if n == 0:
        print('ERROR: 0 frames from %s (%d bytes)' % (path, nbytes))
        return

    print('file   : %s' % path)
    print('frames : %d  bytes=%d  (frames*28=%d)' % (n, nbytes, n * 28))
    print('')

    ch4 = [f[4] for f in frames]
    mx = max(ch4)
    if th is None:
        th = 0.95 * mx
    print('ch4 setpoint max=%.0f  steady threshold=%.0f' % (mx, th))

    steady = [i for i in range(n) if ch4[i] >= th]
    # longest continuous steady run
    best, cur = [], []
    for i in steady:
        if cur and i == cur[-1] + 1:
            cur.append(i)
        else:
            cur = [i]
        if len(cur) > len(best):
            best = cur
    steady = best
    print('steady segment: %s' % ('[%d..%d] len=%d' % (steady[0], steady[-1], len(steady))
                                  if steady else 'none'))
    print('')

    seg_report(frames, list(range(n)), 'ALL')
    if steady:
        seg_report(frames, steady, 'STEADY')
        pre = [i for i in range(steady[0]) if ch4[i] > 500]
        post = [i for i in range(steady[-1] + 1, n) if ch4[i] > 500]
        seg_report(frames, pre, 'ACCEL')
        seg_report(frames, post, 'DECEL')

    # low-speed tail (near zero) as a noise floor probe
    tail = [i for i in range(n) if abs(ch4[i]) < 500]
    if len(tail) >= 20:
        seg_report(frames, tail, 'IDLE(ch4<500)')


if __name__ == '__main__':
    main()
