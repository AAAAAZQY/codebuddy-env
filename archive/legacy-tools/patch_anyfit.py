# -*- coding: gbk -*-
"""修 _dit_report 的 u=None 崩溃, 并新增"任意激励仿真拟合"路线(不需要阶跃)。"""
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
        print('  [FAIL] %-32s 命中 %d 次' % (tag, n))
        return txt, False
    print('  [ok]   %-32s +%d 行' % (tag, new.count(nl) - old.count(nl)))
    return txt.replace(old, new), True


txt, nl = load(P)
print('换行符=%s' % ('CRLF' if nl == '\r\n' else 'LF'))
ok = True

# 1. u/y 为 None 的防护
txt, r = patch(txt, nl, '''def _dit_report(y, u, dt, ts):
    """dither 数据的频域辨识 + IMC 整定, 返回文本。"""
    import cmath
    import math
''', '''def _dit_report(y, u, dt, ts):
    """dither 数据的频域辨识 + IMC 整定, 返回文本。"""
    import cmath
    import math
    if y is None or u is None:
        return ("这份数据没有控制器输出 u, 无法做频域辨识。\\n"
                "请用 time,u,y 三列(或 vofa 里 u=ch3) 重新载入。")
    if len(u) != len(y):
        return "u 与 y 长度不一致, 请检查数据列映射。"
''', '1 u=None 防护')
ok &= r

# 2. 任意激励仿真拟合 + 自动分派
NEWFN = '''def _fit_sim(y, u, dt):
    """任意激励下的 FOPDT 拟合: 用实测 u 驱动模型, 最小化与实测 y 的误差。

    不需要阶跃 —— 只要有足够激励(输入有变化)即可。返回 (rmse_rel, K, T, tau)。
    """
    n = len(y)
    ym = sum(y) / n
    um = sum(u) / n
    yd = [v - ym for v in y]
    ud = [v - um for v in u]
    syy = sum(v * v for v in yd)
    if syy <= 0:
        return None
    best = None
    for i in range(34):
        T = 0.03 * (1.15 ** i)
        a = dt / T
        if a > 1.0:
            continue
        for j in range(0, 25):
            d = int(round((j * 0.01) / dt))
            if d >= n // 3:
                break
            # K=1 时的模型响应(用实测 u 驱动, 去掉输入均值)
            hs = [0.0] * n
            prev = 0.0
            for k in range(n):
                src = ud[k - d] if k - d >= 0 else 0.0
                prev = prev + a * (src - prev)
                hs[k] = prev
            shh = sum(v * v for v in hs)
            if shh <= 1e-12:
                continue
            K = sum(hs[k] * yd[k] for k in range(n)) / shh
            err = sum((yd[k] - K * hs[k]) ** 2 for k in range(n))
            rel = err / syy
            if best is None or rel < best[0]:
                best = (rel, K, T, j * 0.01)
            if K > 0:
                pass
    return best


def _fit_report(y, u, dt, ts):
    """把任意激励拟合结果整理成可读文本 + 固件参数。"""
    import math
    if y is None or u is None:
        return ("这份数据没有控制器输出 u, 无法拟合。\\n"
                "请载入 time,u,y 三列(或 vofa 里 u=ch3)。")
    n = len(y)
    if n < 100:
        return "数据太短(少于 100 点), 请至少采 2 秒。"
    best = _fit_sim(y, u, dt)
    if best is None:
        return "输入 u 几乎没有变化, 没有激励就辨识不出对象。"
    rel, K, T, tau = best
    lines = []
    lines.append("=" * 96)
    lines.append("  任意激励拟合 (仿真误差最小化, 不需要阶跃)")
    lines.append("=" * 96)
    lines.append("  点数 %d   dt=%.4g s" % (n, dt))
    lines.append("  拟合 K=%.4f   T=%.4f s   tau=%.4f s   相对残差 %.1f%%"
                 % (K, T, tau, rel * 100.0))
    if rel > 0.35:
        lines.append("  !! 残差偏大, 模型与数据吻合度低, 下列参数仅供参考")
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
    return "\\n".join(lines)


def _auto_report(y, u, dt, ts):
    """有 dither 就走频域; 否则退回任意激励拟合。"""
    t = _dit_report(y, u, dt, ts)
    bad = ("信噪比不足" in t) or ("找不到足够长" in t) or ("没有控制器输出" in t)
    if not bad:
        return t
    return t + "\\n\\n" + _fit_report(y, u, dt, ts)


'''
txt, r = patch(txt, nl, 'def _fw_from_tool(pid, ts):\n', NEWFN + 'def _fw_from_tool(pid, ts):\n',
               '2 任意激励拟合')
ok &= r

# 3. 按钮改为自动分派
txt, r = patch(txt, nl, '''            _txt = _dit_report(y, u, _dt0, _ts0)''',
               '''            _txt = _auto_report(y, u, _dt0, _ts0)''', '3 按钮走自动分派')
ok &= r

if ok:
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print('')
    print('已写入')
else:
    print('')
    print('!! 有失败, 未写入')
