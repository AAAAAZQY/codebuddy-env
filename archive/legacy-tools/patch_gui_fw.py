# -*- coding: gbk -*-
"""GUI 增加「固件单位」勾选：PID 与积分限幅按固件语义解释。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TUNER = r'D:\bProject\pid_tuner\pid_tuner.py'


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
        print('  [FAIL] %-28s 命中 %d 次' % (tag, n))
        return txt, False
    print('  [ok]   %-28s +%d 行' % (tag, new.count(nl) - old.count(nl)))
    return txt.replace(old, new), True


txt, nl = load(TUNER)
print('换行符=%s' % ('CRLF' if nl == '\r\n' else 'LF'))
ok = True

# 1. 勾选框
txt, r = patch(txt, nl, '''    ttk.Label(pid_holder, text="(留空=不限幅)").pack(side="left", padx=(4, 0))
''', '''    ttk.Label(pid_holder, text="(留空=不限幅)").pack(side="left", padx=(4, 0))
    # 固件单位: 勾上后上面的 Kp/Ki/Kd 与 Imax 按固件语义解释 ——
    # 固件是 integral += error(每拍累加), 工具是 Ki*e*dt, 二者差 1/Ts。
    # 勾上还必须填 Ts, 否则积分/微分无法换算。
    fw_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(pid_holder, text="固件单位", variable=fw_var).pack(
        side="left", padx=(8, 0))
''', '1 固件单位勾选框')
ok &= r

# 2. do_analyze 里换算输入
txt, r = patch(txt, nl, '''        try:
            info, an = analyze(t, u, y, r=r, mode=current_mode(),
                               current_pid=read_current_pid(),
''', '''        global _FW_UNITS
        _FW_UNITS = None
        _cur_pid = read_current_pid()
        try:
            if fw_var.get():
                if not _ts:
                    raise ValueError(
                        "勾选「固件单位」必须填控制周期 Ts。"
                        "本机速度环 10kHz, Ts = 0.0001 秒")
                _rp = read_current_pid() or {}
                _fkp = _rp.get("Kp", 0.0)
                _fki = _rp.get("Ki", 0.0)
                _fkd = _rp.get("Kd", 0.0)
                _FW_UNITS = {"kp": _fkp, "ki": _fki, "kd": _fkd,
                             "imax": _INTEGRAL_MAX, "ts": _ts}
                _cur_pid = {"Kp": _fkp, "Ki": _fki / _ts, "Kd": _fkd * _ts}
                if _INTEGRAL_MAX is not None and _fki:
                    _INTEGRAL_MAX = _fki * _INTEGRAL_MAX
        except Exception as e:                      # noqa: BLE001
            _fail("固件单位换算失败", e)
            return
        try:
            info, an = analyze(t, u, y, r=r, mode=current_mode(),
                               current_pid=_cur_pid,
''', '2 do_analyze 输入换算')
ok &= r

# 3. 结果文本里追加固件换算
txt, r = patch(txt, nl, '''        set_text("\\n".join(lines))
''', '''        if _FW_UNITS:
            _bp = ((an.get("best") or {}).get("pid")) or {}
            if not _bp:
                _bp = ((an.get("rule_fallback") or {}).get("adjusted")) or {}
            if _bp:
                _ckp, _cki, _ckd = _fw_from_tool(_bp, _FW_UNITS["ts"])
                lines.append("")
                lines.append("=" * 118)
                lines.append("★ 换算回固件单位 (Ts=%g s, ki=Ki*Ts, kd=Kd/Ts)"
                             % _FW_UNITS["ts"])
                lines.append("=" * 118)
                lines.append("   建议 kp = %.4f      ki = %.6f      kd = %.6f"
                             % (_ckp, _cki, _ckd))
                lines.append("   以上可直接写进 PID_t; 积分限幅按固件累加器填即可")
        set_text("\\n".join(lines))
''', '3 结果文本追加固件换算')
ok &= r

if ok:
    with io.open(TUNER, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    print('')
    print('已写入')
else:
    print('')
    print('!! 有失败, 未写入')
