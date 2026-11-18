# -*- coding: gbk -*-
"""给 pid_tuner.py / mc_sim_verify.py 增加 integral_max 参数。每次替换都断言命中次数。"""
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TUNER = r'D:\bProject\pid_tuner\pid_tuner.py'
VERIFY = r'D:\bProject\pid_tuner\mc_sim_verify.py'


def load(path):
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        txt = f.read()
    nl = '\r\n' if '\r\n' in txt else '\n'
    return txt, nl


def save(path, txt):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)


def patch(txt, nl, old, new, tag):
    old = old.replace('\n', nl)
    new = new.replace('\n', nl)
    n = txt.count(old)
    if n != 1:
        print('  [FAIL] %-34s 命中 %d 次 (需要 1)' % (tag, n))
        return txt, False
    print('  [ok]   %-34s +%d 行' % (tag, new.count(nl) - old.count(nl)))
    return txt.replace(old, new), True


ok = True
txt, nl = load(TUNER)
print('pid_tuner.py  换行符=%s  长度=%d' % ('CRLF' if nl == '\r\n' else 'LF', len(txt)))
print('')

# 1. 模块级全局
txt, r = patch(txt, nl, '''_VOFA_DIAG = [None]
''', '''_VOFA_DIAG = [None]

# 积分限幅(控制量单位)。None = 不限幅, 即保持历史行为。
# CLI 用 --integral-max 设置, 界面用「积分限幅 Imax」输入框设置;
# simulate() 未显式传入时会读取它。设了它, 仿真中的积分才会像真机那样被
# 封顶(integral_max), 否则工具会给出"积分可以无限累积"的过于乐观的结论。
_INTEGRAL_MAX = None
''', '1 模块级 _INTEGRAL_MAX')
ok &= r

# 2. simulate 签名
txt, r = patch(txt, nl, '''             u_min=None, u_max=None, T_end=None, sp0=None, y0=0.0,
             dt_ctrl=None):''', '''             u_min=None, u_max=None, T_end=None, sp0=None, y0=0.0,
             dt_ctrl=None, integral_max=None):''', '2 simulate 增加入参')
ok &= r

# 3. 解析默认值
txt, r = patch(txt, nl, '''    if u_min is None:
        u_min = -u_max

    blow = 1e6 * (1.0 + abs(sp))''', '''    if u_min is None:
        u_min = -u_max
    if integral_max is None:
        integral_max = _INTEGRAL_MAX

    blow = 1e6 * (1.0 + abs(sp))''', '3 解析 integral_max 默认值')
ok &= r

# 4. 积分钳位(核心)
txt, r = patch(txt, nl, '''            e = sp - y
            integ += Ki * e * dt_ctrl
            D = Kd * (e - e_prev) / dt_ctrl''', '''            e = sp - y
            integ += Ki * e * dt_ctrl
            if integral_max is not None:
                # 真机的积分限幅: 超了就钉住, 与输出限幅的抗饱和是两回事。
                if integ > integral_max:
                    integ = integral_max
                elif integ < -integral_max:
                    integ = -integral_max
            D = Kd * (e - e_prev) / dt_ctrl''', '4 积分钳位(核心)')
ok &= r

# 5. CLI 用法串
txt, r = patch(txt, nl, '''                  '[--dt <采样周期>] [--current-pid "Kp,Ki,Kd"] [--plain]')''',
               '''                  '[--dt <采样周期>] [--ts <控制周期>] '
                  '[--integral-max <积分限幅>] '
                  '[--current-pid "Kp,Ki,Kd"] [--plain]')''', '5 CLI 用法串')
ok &= r

# 6. CLI 解析
txt, r = patch(txt, nl, '''            if dt_ctrl <= 0:
                print("--ts 必须大于 0")
                return 2
''', '''            if dt_ctrl <= 0:
                print("--ts 必须大于 0")
                return 2

        # --integral-max: 真机的积分限幅(控制量单位), 如 --integral-max 2000。
        # 不填 = 不限幅(历史行为)。填了之后仿真才会反映"积分被钉住"。
        global _INTEGRAL_MAX
        _INTEGRAL_MAX = None
        if "--integral-max" in args:
            try:
                _imax = float(args[args.index("--integral-max") + 1])
            except (IndexError, ValueError):
                print("--integral-max 需要是一个正数, 例如 --integral-max 2000")
                return 2
            if _imax <= 0:
                print("--integral-max 必须大于 0")
                return 2
            _INTEGRAL_MAX = _imax
            print("积分限幅 Imax = %g (仿真中积分超过它会被钉住)" % _imax)
''', '6 CLI --integral-max 解析')
ok &= r

# 7. GUI 输入框
txt, r = patch(txt, nl, '''    ttk.Button(pid_holder, text="重新计算",
               command=lambda: reanalyze()).pack(side="left", padx=10)''',
               '''    # 积分限幅: 真机的 integral_max(控制量单位)。留空 = 不限幅。
    ttk.Label(pid_holder, text="  积分限幅 Imax:").pack(side="left")
    imax_var = tk.StringVar(value="")
    ttk.Entry(pid_holder, textvariable=imax_var, width=9).pack(side="left")
    ttk.Label(pid_holder, text="(留空=不限幅)").pack(side="left", padx=(4, 0))
    ttk.Button(pid_holder, text="重新计算",
               command=lambda: reanalyze()).pack(side="left", padx=10)''', '7 GUI 增加 Imax 输入框')
ok &= r

# 8. GUI 解析
txt, r = patch(txt, nl, '''        except (ValueError, AttributeError):
            _ts = None
        try:
            info, an = analyze(t, u, y, r=r, mode=current_mode(),''',
               '''        except (ValueError, AttributeError):
            _ts = None
        global _INTEGRAL_MAX
        _INTEGRAL_MAX = None
        try:
            _raw_imax = imax_var.get().strip()
            if _raw_imax:
                _imax = float(_raw_imax)
                if _imax > 0:
                    _INTEGRAL_MAX = _imax
        except (ValueError, AttributeError):
            _INTEGRAL_MAX = None
        try:
            info, an = analyze(t, u, y, r=r, mode=current_mode(),''', '8 GUI 解析 Imax')
ok &= r

if ok:
    save(TUNER, txt)
    print('')
    print('pid_tuner.py 已写入')
else:
    print('')
    print('!! 有替换失败, 未写入 pid_tuner.py')

# ---- mc_sim_verify.py ----
ok2 = True
txt2, nl2 = load(VERIFY)
print('')
print('mc_sim_verify.py  换行符=%s' % ('CRLF' if nl2 == '\r\n' else 'LF'))
txt2, r = patch(txt2, nl2, '''U_MAX, U_MIN = 10.0, -10.0''',
                '''U_MAX, U_MIN = 10.0, -10.0
# 积分限幅(PID_SIM_INTEGRAL_MAX)。None = 不限幅, 与旧版行为一致。
INTEGRAL_MAX = None''', '7b 增加 INTEGRAL_MAX 常量')
ok2 &= r
txt2, r = patch(txt2, nl2, '''        integ += KI * e * dt
        deriv = (e - e_prev) / dt''',
                '''        integ += KI * e * dt
        if INTEGRAL_MAX is not None:
            integ = max(-INTEGRAL_MAX, min(INTEGRAL_MAX, integ))
        deriv = (e - e_prev) / dt''', '8b 积分钳位')
ok2 &= r
if ok2:
    save(VERIFY, txt2)
    print('mc_sim_verify.py 已写入')
else:
    print('!! 有替换失败, 未写入 mc_sim_verify.py')
