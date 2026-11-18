# -*- coding: gbk -*-
"""给 pid_tuner.py 增加 --fw-units(固件单位换算)。每次替换都断言命中次数。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TUNER = r'D:\bProject\pid_tuner\pid_tuner.py'


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
        print('  [FAIL] %-32s 命中 %d 次' % (tag, n))
        return txt, False
    print('  [ok]   %-32s +%d 行' % (tag, new.count(nl) - old.count(nl)))
    return txt.replace(old, new), True


txt, nl = load(TUNER)
print('pid_tuner.py 换行符=%s' % ('CRLF' if nl == '\r\n' else 'LF'))
ok = True

# A. 模块级全局
txt, r = patch(txt, nl, '''_INTEGRAL_MAX = None


def _vofa_tokens(raw, limit=None):
''', '''_INTEGRAL_MAX = None

# 固件单位换算上下文。None = 未启用 --fw-units。
# 固件 PID 是"每拍累加积分"(integral += error), 工具的 Ki 是每秒积分增益,
# 二者差 1/Ts; 微分同理差 Ts。启用后输入/输出都在固件单位下进行。
_FW_UNITS = None
''', 'A 模块级 _FW_UNITS')
ok &= r

# B. 辅助函数(放在 main 之前)
txt, r = patch(txt, nl, '''def main():
''', '''def _fw_from_tool(pid, ts):
    """工具单位 (Kp,Ki,Kd) -> 固件单位 (kp,ki,kd)。"""
    return (pid.get("Kp"), pid.get("Ki", 0.0) * ts, pid.get("Kd", 0.0) / ts)


def _print_fw_suggestion(analysis, fw):
    """把工具算出的建议参数换算回固件单位并打印。"""
    ts = fw["ts"]
    analysis = analysis or {}
    pid = ((analysis.get("best") or {}).get("pid")) or {}
    if not pid:
        pid = ((analysis.get("rule_fallback") or {}).get("adjusted")) or {}
    if not pid:
        return
    kp, ki, kd = _fw_from_tool(pid, ts)
    print("")
    print("=" * 78)
    print("  ★ 换算回固件单位 (Ts=%g s)" % ts)
    print("=" * 78)
    print("  固件 kp = %.4f" % kp)
    print("  固件 ki = %.6f" % ki)
    print("  固件 kd = %.6f" % kd)
    if fw.get("imax") is not None and fw.get("ki"):
        print("  积分限幅 imax: 现用 %g -> ki*imax = %.4g (工具侧积分上限)"
              % (fw["imax"], fw["ki"] * fw["imax"]))
        print("                稳态需要多少 Uq 就填多少, 超过它才会饱和")
    print("")
    print("  说明: 以上可直接写进 PID_t, 前提是 CSV 的 u 是 Uq、y 是速度同单位。")


def main():
''', 'B 辅助函数')
ok &= r

# C. CLI 用法串
txt, r = patch(txt, nl, '''                  '[--integral-max <积分限幅>] '
''', '''                  '[--integral-max <积分限幅>] '
                  '[--fw-units "kp=..,ki=..,kd=..,imax=.."] '
''', 'C 用法串')
ok &= r

# D. CLI 解析: 放在 --current-pid 之后, 覆盖它
txt, r = patch(txt, nl, '''        do_optimize = "--plain" not in args
''', '''        # --fw-units: 按固件约定给参数。固件是"每拍累加积分"(integral +=
        # error), 与工具的"每秒积分"差 1/Ts; 微分差 Ts。没有 --ts 就没法换算。
        global _FW_UNITS
        _FW_UNITS = None
        if "--fw-units" in args:
            try:
                _spec = args[args.index("--fw-units") + 1]
            except IndexError:
                print('--fw-units 需要形如 "kp=0.85,ki=0.01,kd=0.05,imax=200000"')
                return 2
            _fw = {}
            for _part in _spec.replace(" ", "").split(","):
                if not _part:
                    continue
                if "=" not in _part:
                    print("--fw-units 片段格式错误:", _part)
                    return 2
                _k, _v = _part.split("=", 1)
                try:
                    _fw[_k.strip().lower()] = float(_v)
                except ValueError:
                    print("--fw-units 的值必须是数字:", _part)
                    return 2
            if dt_ctrl is None:
                print("--fw-units 必须同时给 --ts <控制周期(秒)>, 否则无法换算积分/微分")
                return 2
            _fw_kp = _fw.get("kp", 0.0)
            _fw_ki = _fw.get("ki", 0.0)
            _fw_kd = _fw.get("kd", 0.0)
            _fw_imax = _fw.get("imax")
            _FW_UNITS = {"kp": _fw_kp, "ki": _fw_ki, "kd": _fw_kd,
                         "imax": _fw_imax, "ts": dt_ctrl}
            current_pid = {"Kp": _fw_kp, "Ki": _fw_ki / dt_ctrl,
                           "Kd": _fw_kd * dt_ctrl}
            if _fw_imax is not None and _fw_ki:
                _INTEGRAL_MAX = _fw_ki * _fw_imax
            print("已按固件约定换算 (Ts=%g s):" % dt_ctrl)
            print("   固件: kp=%.4g  ki=%.4g  kd=%.4g  imax=%.6g"
                  % (_fw_kp, _fw_ki, _fw_kd, _fw_imax if _fw_imax is not None else 0))
            print("   工具: Kp=%.4g  Ki=%.4g  Kd=%.4g  Imax=%s"
                  % (current_pid["Kp"], current_pid["Ki"], current_pid["Kd"],
                     ("%.4g" % _INTEGRAL_MAX) if _INTEGRAL_MAX is not None else "(不限)"))

        do_optimize = "--plain" not in args
''', 'D CLI --fw-units 解析')
ok &= r

# E. 报告后打印固件换算
txt, r = patch(txt, nl, '''        print(report(info, analysis))
''', '''        print(report(info, analysis))
        if _FW_UNITS:
            _print_fw_suggestion(analysis, _FW_UNITS)
''', 'E 打印固件换算')
ok &= r

if ok:
    save(TUNER, txt)
    print('')
    print('已写入 pid_tuner.py')
else:
    print('')
    print('!! 有替换失败, 未写入')
