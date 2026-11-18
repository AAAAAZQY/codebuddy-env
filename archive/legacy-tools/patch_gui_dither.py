# -*- coding: gbk -*-
"""把频域辨识(dither)并进 GUI: 多一个按钮, 直接出参数。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = r'D:\bProject\pid_tuner\pid_tuner.py'


def load(path):
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        txt = f.read()
    nl = '\r\n' if '\r\n' in txt else '\n'
    return txt, nl


def patch(txt, nl, old, new, tag):
    old = old.replace('\n', nl)
    new = new.replace('\n', nl)
    n = txt.count(old)
    if n != 1:
        print('  [FAIL] %-30s 命中 %d 次' % (tag, n))
        return txt, False
    print('  [ok]   %-30s +%d 行' % (tag, new.count(nl) - old.count(nl)))
    return txt.replace(old, new), True


txt, nl = load(P)
print('换行符=%s' % ('CRLF' if nl == '\r\n' else 'LF'))
ok = True

MODULE = '''_DIT_FREQS = [1.5, 3.0, 4.5, 9.0, 14.5, 20.0]


def _dit_dft(xs, dt, f):
    """Hann 窗单频 DFT, 返回复数峰值幅度。"""
    import cmath
    import math
    n = len(xs)
    s = 0j
    ws = 0.0
    for k, x in enumerate(xs):
        w = 0.5 - 0.5 * math.cos(2.0 * math.pi * k / max(1, n - 1))
        s += w * x * cmath.exp(-2j * math.pi * f * (k * dt))
        ws += w
    return 2.0 * s / ws if ws else 0j


def _dit_fit(P):
    """P 为各频点的复频响, 网格搜索 K/T/tau。"""
    import cmath
    import math
    ws = [2.0 * math.pi * f for f in _DIT_FREQS]
    best = None
    for i in range(38):
        T = 0.05 * (1.12 ** i)
        for j in range(33):
            tau = j * 0.0125
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


def _dit_pm(K, T, tau, Kc, Ti):
    """扫频求交越频率与相位余量。"""
    import cmath
    import math
    lo, hi = 0.01, 500.0
    for _ in range(80):
        wc = (lo * hi) ** 0.5
        C = Kc * (1.0 + 1.0 / (1j * wc * Ti))
        Pw = K * cmath.exp(-1j * wc * tau) / (1 + 1j * wc * T)
        if abs(C * Pw) > 1:
            lo = wc
        else:
            hi = wc
    wc = (lo * hi) ** 0.5
    C = Kc * (1.0 + 1.0 / (1j * wc * Ti))
    Pw = K * cmath.exp(-1j * wc * tau) / (1 + 1j * wc * T)
    ph = math.degrees(cmath.phase(C * Pw))
    return wc / (2.0 * math.pi), 180.0 + ph


def _dit_report(y, u, dt, ts):
    """dither 数据的频域辨识 + IMC 整定, 返回文本。"""
    import cmath
    import math
    # 只取激励生效段(速度 > 15000)
    seg = []
    started = False
    for k in range(len(y)):
        if y[k] > 15000:
            started = True
            seg.append(k)
        elif started and len(seg) > 50:
            break
    if len(seg) < 200:
        return ("数据里找不到足够长的匀速段(速度>15000). "
                "请确认采集时电机在正转高速, 且 MOTOR_IDENT_DITHER=1.")
    ys = [y[k] for k in seg]
    us = [u[k] for k in seg]
    ym = sum(ys) / len(ys)
    um = sum(us) / len(us)
    yn = [v - ym for v in ys]
    un = [v - um for v in us]

    lines = []
    lines.append("=" * 96)
    lines.append("  频域辨识 (dither)   %d 点  %.1f s  速度均值 %.0f" %
                 (len(seg), len(seg) * dt, ym))
    lines.append("=" * 96)
    lines.append("%-8s %10s %10s %8s %10s %9s" %
                 ("f(Hz)", "|U|(Uq)", "|Y|(vel)", "SNR(dB)", "|P|", "argP(deg)"))
    lines.append("-" * 62)
    Pv, bad = [], False
    for f in _DIT_FREQS:
        U = _dit_dft(un, dt, f)
        Y = _dit_dft(yn, dt, f)
        floor = max(abs(_dit_dft(un, dt, f + o)) for o in (-0.7, -0.5, 0.5, 0.7))
        snr = 20.0 * math.log10(max(1e-9, abs(U)) / max(1e-9, floor))
        pv = Y / U if abs(U) > 1e-9 else 0j
        lines.append("%-8.1f %10.1f %10.1f %8.1f %10.3f %9.1f"
                     % (f, abs(U), abs(Y), snr, abs(pv),
                        math.degrees(cmath.phase(pv))))
        if snr < 10:
            bad = True
        Pv.append(pv)
    if bad:
        lines.append("")
        lines.append("!! 有频点信噪比不足 10dB, 结果不可信。")
        lines.append("   请把 IDENT_DITHER_AMP 加大到 120 或延长采集时间。")
        return "\\n".join(lines)

    rel, K, T, tau = _dit_fit(Pv)
    lines.append("")
    lines.append("对象拟合  K=%.4f   T=%.4f s   tau=%.4f s   残差 %.1f%%"
                 % (K, T, tau, rel * 100.0))
    lam = max(tau, 0.1 * T)
    Kc = T / (K * (lam + tau)) if K * (lam + tau) else 0.0
    Ti = T
    fw_kp = Kc
    fw_ki = (Kc / Ti) * ts
    wc, pm = _dit_pm(K, T, tau, Kc, Ti)
    lines.append("")
    lines.append("IMC-PI 整定 (lambda=%.3f s)   交越 %.2f Hz   相位余量 %.1f deg"
                 % (lam, wc, pm))
    lines.append("-" * 62)
    lines.append("  可直接写进 PID_t:")
    lines.append("      .kp = %.4ff" % fw_kp)
    lines.append("      .ki = %.6ff" % fw_ki)
    lines.append("      .kd = 0.0f")
    if fw_ki > 0:
        lines.append("  积分限幅 integral_max >= %.0f" % (2272.0 / fw_ki))
    lines.append("")
    lines.append("  注: ki 已按固件每拍累加约定换算 (ki = Ki_cont * Ts, Ts=%g)" % ts)
    return "\\n".join(lines)


'''

txt, r = patch(txt, nl, 'def _fw_from_tool(pid, ts):\n', MODULE + 'def _fw_from_tool(pid, ts):\n',
               '1 模块级 dither 函数')
ok &= r

# 2. 按钮 + 处理器
txt, r = patch(txt, nl,
               '    ttk.Button(top, text="载入示例(有u)", command=load_sample).pack(side="right", padx=4)\n',
               '''    ttk.Button(top, text="载入示例(有u)", command=load_sample).pack(side="right", padx=4)

    def do_dither():
        """频域辨识: 用 dither 数据算对象频响并给固件参数。"""
        d = state.get("data")
        if not d:
            messagebox.showinfo("提示", "先载入数据: 需要 time,u,y 三列, 且带 dither 激励")
            return
        t, u, y, r = d
        _dt0 = 0.01
        if len(t) > 2:
            _dt0 = t[1] - t[0]
        try:
            _ts0 = float(ts_var.get().strip() or 0.0001)
        except (ValueError, AttributeError):
            _ts0 = 0.0001
        try:
            _txt = _dit_report(y, u, _dt0, _ts0)
        except Exception as e:                      # noqa: BLE001
            _fail("频域辨识失败", e)
            return
        set_text(_txt)

    ttk.Button(top, text="频域辨识(dither)", command=do_dither).pack(side="right", padx=4)
''', '2 按钮与处理器')
ok &= r

if ok:
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print('')
    print('已写入')
else:
    print('')
    print('!! 有失败, 未写入')
