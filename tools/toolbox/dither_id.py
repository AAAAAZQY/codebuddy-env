# -*- coding: gbk -*-
"""从 vofa 数据中提取对象频响并给出固件 PID。

用法:
    python dither_id.py <数据文件> [--dt 0.01] [--ts 0.0001] [--lam 0.3]

数据文件可以是
  1) vofa hex 文本(6 路 float, 每帧以 00 00 80 7F 结尾): u=通道3, y=通道0
  2) CSV, 表头含 time,u,y

激励频率(固件 MOTOR_IDENT_DITHER 注入, 必须与此处一致):
    1.5  3.0  4.5  9.0  14.5  20.0 Hz
"""
import cmath
import io
import math
import struct
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FREQS = [1.5, 3.0, 4.5, 9.0, 14.5, 20.0]
U_CH, Y_CH = 3, 0          # vofa 通道: u=target_Uq, y=current_velocity


def load_hex(path):
    raw = io.open(path, encoding='utf-8', errors='replace').read()
    toks = [t for t in raw.split() if len(t) == 2]
    data = bytes(int(t, 16) for t in toks)
    fr, i = [], 0
    while i + 28 <= len(data):
        c = data[i:i + 28]
        if c[24:28] == b'\x00\x00\x80\x7f':
            fr.append(struct.unpack('<6f', c[:24]))
            i += 28
        else:
            i += 1
    return [(f[Y_CH], f[U_CH]) for f in fr]


def load_csv(path):
    lines = io.open(path, encoding='utf-8', errors='replace').read().splitlines()
    head = [c.strip().lower() for c in lines[0].split(',')]
    iu, iy = head.index('u'), head.index('y')
    out = []
    for ln in lines[1:]:
        p = ln.split(',')
        if len(p) <= max(iu, iy):
            continue
        out.append((float(p[iy]), float(p[iu])))
    return out


def dft(xs, dt, f, t0=0.0):
    """Hann 窗单频 DFT, 返回幅度为峰值(幅值)的复数。"""
    n = len(xs)
    s = 0j
    ws = 0.0
    for k, x in enumerate(xs):
        w = 0.5 - 0.5 * math.cos(2.0 * math.pi * k / max(1, n - 1))
        s += w * x * cmath.exp(-2j * math.pi * f * (t0 + k * dt))
        ws += w
    return 2.0 * s / ws if ws else 0j


def fit_fopdt(P, ws):
    """P = K e^{-j w tau} / (1 + j w T), 网格搜索 T/tau, K 最小二乘。"""
    best = None
    Tgs = [0.05 * (1.12 ** i) for i in range(38)]        # 0.05 .. ~3.9
    for T in Tgs:
        for j in range(0, 33):
            tau = j * 0.0125                             # 0 .. 0.4
            G = [cmath.exp(-1j * w * tau) / (1 + 1j * w * T) for w in ws]
            num = sum((P[k] * G[k].conjugate()).real for k in range(len(P)))
            den = sum(abs(g) ** 2 for g in G)
            if den <= 0:
                continue
            K = num / den
            err = sum(abs(P[k] - K * G[k]) ** 2 for k in range(len(P)))
            rel = err / max(1e-12, sum(abs(p) ** 2 for p in P))
            if best is None or rel < best[0]:
                best = (rel, K, T, tau)
    return best


def loop_pm(K, T, tau, Kc, Ti, ws):
    """扫描频率求增益交越与相位余量。"""
    lo, hi = 0.01, 500.0
    for _ in range(80):
        wc = (lo * hi) ** 0.5
        C = Kc * (1.0 + 1.0 / (1j * wc * Ti))
        P = K * cmath.exp(-1j * wc * tau) / (1 + 1j * wc * T)
        if abs(C * P) > 1:
            lo = wc
        else:
            hi = wc
    wc = (lo * hi) ** 0.5
    C = Kc * (1.0 + 1.0 / (1j * wc * Ti))
    P = K * cmath.exp(-1j * wc * tau) / (1 + 1j * wc * T)
    L = C * P
    return wc / (2 * math.pi), 180 + math.degrees(cmath.phase(L))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    dt = 0.01
    ts = 0.0001
    lam = None
    a = sys.argv[2:]
    for i, x in enumerate(a):
        if x == '--dt' and i + 1 < len(a):
            dt = float(a[i + 1])
        if x == '--ts' and i + 1 < len(a):
            ts = float(a[i + 1])
        if x == '--lam' and i + 1 < len(a):
            lam = float(a[i + 1])

    data = load_csv(path) if path.lower().endswith('.csv') else load_hex(path)
    print('总帧数 %d' % len(data))

    # 只取激励生效段(速度 > 15000)
    seg, t0 = [], None
    for k, (y, u) in enumerate(data):
        if y > 15000:
            if t0 is None:
                t0 = k
            seg.append((y, u))
        elif t0 is not None and len(seg) > 50:
            break
    print('取激励段 %d 帧 (%.1f s), 速度均值 %.0f'
          % (len(seg), len(seg) * dt, sum(s[0] for s in seg) / max(1, len(seg))))
    if len(seg) < 200:
        print('数据太短, 至少需要 200 帧(2 秒)匀速段')
        return 1

    ys = [s[0] for s in seg]
    us = [s[1] for s in seg]
    Ym = sum(ys) / len(ys)
    Um = sum(us) / len(us)
    yn = [v - Ym for v in ys]
    un = [v - Um for v in us]

    print('')
    print('%-8s %10s %10s %8s %10s %9s' %
          ('f(Hz)', '|U|(Uq)', '|Y|(vel)', 'SNR(dB)', '|P|', 'argP(deg)'))
    print('-' * 62)
    P, ws, ok = [], [], True
    for f in FREQS:
        U = dft(un, dt, f)
        Y = dft(yn, dt, f)
        floor = max(abs(dft(un, dt, f + o)) for o in (-0.7, -0.5, 0.5, 0.7))
        snr = 20 * math.log10(max(1e-9, abs(U)) / max(1e-9, floor))
        p = Y / U if abs(U) > 1e-9 else 0j
        print('%-8.1f %10.1f %10.1f %8.1f %10.3f %9.1f'
              % (f, abs(U), abs(Y), snr, abs(p), math.degrees(cmath.phase(p))))
        if snr < 10:
            ok = False
        P.append(p)
        ws.append(2 * math.pi * f)

    if not ok:
        print('')
        print('!! 有频点信噪比不足 10dB, 结果不可信。请加大 IDENT_DITHER_AMP 或延长采集。')
        return 1

    rel, K, T, tau = fit_fopdt(P, ws)
    print('')
    print('对象拟合  K=%.4f   T=%.4f s   tau=%.4f s   相对残差 %.1f%%'
          % (K, T, tau, rel * 100))

    if lam is None:
        lam = max(tau, 0.1 * T)
    Kc = T / (K * (lam + tau)) if K * (lam + tau) else 0.0
    Ti = T
    ki_cont = Kc / Ti
    fw_kp = Kc
    fw_ki = ki_cont * ts
    wc, pm = loop_pm(K, T, tau, Kc, Ti, ws)

    print('')
    print('IMC-PI 整定 (lambda=%.3f s)' % lam)
    print('=' * 62)
    print('  交越频率   %.2f Hz' % wc)
    print('  相位余量   %.1f deg   %s' % (pm, '(偏低)' if pm < 40 else ''))
    print('')
    print('  ---- 直接写进 PID_t ----')
    print('  .kp = %.4ff' % fw_kp)
    print('  .ki = %.6ff' % fw_ki)
    print('  .kd = 0.0f')
    if fw_ki > 0:
        need = 2272.0 / fw_ki
        print('')
        print('  积分限幅建议 >= %.0f  (让积分项能出到 2272 Uq 的工作点)' % need)
    print('')
    print('  说明: ki 已按固件"每拍累加"约定换算 (ki = Ki_cont * Ts, Ts=%g)' % ts)
    return 0


if __name__ == '__main__':
    sys.exit(main())
