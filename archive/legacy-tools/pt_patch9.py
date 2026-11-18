# -*- coding: cp936 -*-
"""第 9 步：采样不足时，模型路径自动补算规则整定，并作为主推荐输出"""
import io
import sys

TARGET = r'D:\bProject\pid_tuner\pid_tuner.py'


def L(s):
    return s.encode('utf-8').decode('latin-1')


src = io.open(TARGET, encoding='latin-1', newline='').read()

# ---------- A: _model_route 里补算规则整定 ----------
a_old = '''            an["iter_note"] = _note
        except Exception:       # noqa: BLE001
            pass
        return info, an'''

a_new = '''            an["iter_note"] = _note
        except Exception:       # noqa: BLE001
            pass
        # 采样不足时, 同时算一份"经验规则整定"挂到结果上。
        # 模型整定在这种数据上不可信(对象滞后只有 1~2 个采样点),
        # 但振荡特征(波动幅度/衰减比)是可靠的, 规则整定给的调整
        # 方向可以直接上机用。报告里会把它放在最前面作为主推荐。
        if pid_used is not None and r is not None:
            try:
                _rec = recommended_sample_time(ident["K"], ident["T"], ident["tau"])
                _now = (t[1] - t[0]) if len(t) > 1 else (dt_ctrl or 1.0)
                if _now > _rec * 2.0:
                    _f2 = closed_loop_feature_const(t, r, y)
                    an["rule_fallback"] = build_closed_analysis(
                        _f2, pid_used, mode, pref)
            except Exception:       # noqa: BLE001
                pass
        return info, an'''

if src.count(a_old) != 1:
    print('anchor A count =', src.count(a_old))
    sys.exit(1)
src = src.replace(a_old, L(a_new))

# ---------- B: 报告里把规则整定提到表格之前 ----------
b_old = L('''    _pref = normalize_pref(analysis.get("pref"))
    _ptxt = (f"   调参偏好: {PREF_LABEL[_pref]}" if _pref != "balanced" else "")
    add("=" * 78)
    add(f"  PID 方案对比    (约束模式: {MODE_LABEL[mode]}){_ptxt}")''')

b_new = L('''    _fb = analysis.get("rule_fallback")
    if _fb:
        _fbc = _fb.get("current") or {}
        _fba = _fb.get("adjusted") or {}
        add("=" * 78)
        add("  ★ 经验规则整定 (采样不足, 以这条为准)")
        add("=" * 78)
        if _fbc:
            add(f"  当前参数 : Kp = {_fmt_pid(_fbc.get('Kp')):>10}"
                f"   Ki = {_fmt_pid(_fbc.get('Ki')):>10}"
                f"   Kd = {_fmt_pid(_fbc.get('Kd')):>10}")
        if _fb.get("action"):
            add(f"  调整动作 : {_fb['action']}")
        if _fba:
            add(f"  建议参数 : Kp = {_fmt_pid(_fba.get('Kp')):>10}"
                f"   Ki = {_fmt_pid(_fba.get('Ki')):>10}"
                f"   Kd = {_fmt_pid(_fba.get('Kd')):>10}")
        for _n in (_fb.get("notes") or [])[:3]:
            add(f"    - {_n}")
        add("")
        add("=" * 78)
        add("  以下是模型整定结果, 仅供趋势参考 (采样不足, 请勿直接上机)")
        add("=" * 78)

    _pref = normalize_pref(analysis.get("pref"))
    _ptxt = (f"   调参偏好: {PREF_LABEL[_pref]}" if _pref != "balanced" else "")
    add("=" * 78)
    add(f"  PID 方案对比    (约束模式: {MODE_LABEL[mode]}){_ptxt}")''')

if src.count(b_old) != 1:
    print('anchor B count =', src.count(b_old))
    sys.exit(1)
src = src.replace(b_old, b_new)

out = src.encode('latin-1')
io.open(TARGET, 'wb').write(out)
print('patched, bytes =', len(out))
